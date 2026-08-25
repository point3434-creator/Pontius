from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from pathlib import Path
import unittest

from pontius.exact_directional_face_oracle import (
    compose_exact_directional_face_fan_section,
    exact_directional_best_response_face,
)
from pontius.exact_selector_fan import (
    reachable_response_tape,
    realization_interpolated_policy,
)
from pontius.exact_selector_window_oracle import (
    exact_best_response_trace,
    exact_fixed_response_trace,
    exact_policy_utilities,
)
from pontius.game import CHANCE_PLAYER, TERMINAL_PLAYER
from tests.test_exact_tie_aware_affine_envelope import (
    _CrossingGame,
    _policies,
)


STOP = "stop"
GO = "go"


@dataclass(frozen=True, slots=True)
class _ChainState:
    levels: int
    depth: int = 0
    terminal: bool = False

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if self.terminal else 0

    def legal_actions(self) -> tuple[str, ...]:
        return (STOP, GO)

    def chance_outcomes(self) -> tuple[()]:
        return ()

    def apply_action(self, action: str) -> _ChainState:
        if action not in self.legal_actions() or self.terminal:
            raise ValueError("invalid directional-face chain action")
        finished = action == STOP or self.depth + 1 == self.levels
        return _ChainState(self.levels, self.depth + 1, finished)

    def information_state_key(self, player: int) -> str:
        if player != 0 or self.terminal:
            raise ValueError("directional-face chain player mismatch")
        return f"directional-face-chain-{self.depth}"

    def returns(self) -> tuple[float]:
        if not self.terminal:
            raise ValueError("directional-face chain return before terminal")
        return (0.0,)


@dataclass(frozen=True, slots=True)
class _ChainGame:
    levels: int
    num_players: int = 1

    def initial_state(self) -> _ChainState:
        return _ChainState(self.levels)


@dataclass(frozen=True, slots=True)
class _RepeatedSlopeState:
    history: tuple[str, ...] = ()

    @property
    def current_player(self) -> int:
        if not self.history:
            return 0
        if len(self.history) in (1, 2) and self.history[-1] != STOP:
            return 1
        return TERMINAL_PLAYER

    def legal_actions(self) -> tuple[str, ...]:
        if not self.history:
            return ("left", "right")
        if len(self.history) == 1:
            return (STOP, GO)
        return ("first", "second")

    def chance_outcomes(self) -> tuple[()]:
        return ()

    def apply_action(self, action: str) -> _RepeatedSlopeState:
        if action not in self.legal_actions():
            raise ValueError("invalid repeated-slope action")
        return _RepeatedSlopeState((*self.history, action))

    def information_state_key(self, player: int) -> str:
        if player != self.current_player:
            raise ValueError("repeated-slope player mismatch")
        if player == 0:
            return "repeated-slope-p0"
        return "repeated-slope-root" if len(self.history) == 1 else "repeated-slope-child"

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("repeated-slope return before terminal")
        if self.history[-1] == STOP:
            target = 0.5
        else:
            target = float(
                (self.history[0], self.history[-1])
                in (("left", "first"), ("right", "second"))
            )
        return -target, target


@dataclass(frozen=True, slots=True)
class _RepeatedSlopeGame:
    num_players: int = 2

    def initial_state(self) -> _RepeatedSlopeState:
        return _RepeatedSlopeState()


@dataclass(frozen=True, slots=True)
class _ZeroSupportChanceState:
    history: tuple[str, ...] = ()

    @property
    def current_player(self) -> int:
        if not self.history:
            return CHANCE_PLAYER
        return 0 if len(self.history) == 1 else TERMINAL_PLAYER

    def legal_actions(self) -> tuple[str, ...]:
        return ("first", "second")

    def chance_outcomes(self) -> tuple[tuple[str, float], ...]:
        return (("live", 1.0), ("dead", 0.0))

    def apply_action(self, action: str) -> _ZeroSupportChanceState:
        legal = (
            tuple(item[0] for item in self.chance_outcomes())
            if not self.history
            else self.legal_actions()
        )
        if action not in legal:
            raise ValueError("invalid zero-support chance action")
        return _ZeroSupportChanceState((*self.history, action))

    def information_state_key(self, player: int) -> str:
        if player != 0 or self.current_player != 0:
            raise ValueError("zero-support chance player mismatch")
        return f"zero-support-{self.history[0]}"

    def returns(self) -> tuple[float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("zero-support chance return before terminal")
        return (0.0,)


@dataclass(frozen=True, slots=True)
class _ZeroSupportChanceGame:
    num_players: int = 1

    def initial_state(self) -> _ZeroSupportChanceState:
        return _ZeroSupportChanceState()


def _chain_policy(levels: int) -> dict[str, dict[str, Fraction]]:
    return {
        f"directional-face-chain-{depth}": {
            STOP: Fraction(1, 2),
            GO: Fraction(1, 2),
        }
        for depth in range(levels)
    }


def _exhaustive_active_tapes(
    game: object,
    policy: dict[str, dict[str, Fraction]],
    target_player: int,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    trace = exact_best_response_trace(game, policy, target_player)
    keys = tuple(row.key for row in trace.information_sets)
    choices = tuple(row.maximizing_actions for row in trace.information_sets)
    return tuple(
        tuple(sorted(zip(keys, selected, strict=True)))
        for selected in product(*choices)
    )


def _all_response_tapes(
    game: object,
    policy: dict[str, dict[str, Fraction]],
    target_player: int,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    trace = exact_best_response_trace(game, policy, target_player)
    keys = tuple(row.key for row in trace.information_sets)
    choices = tuple(row.actions for row in trace.information_sets)
    return tuple(
        tuple(sorted(zip(keys, selected, strict=True)))
        for selected in product(*choices)
    )


class ExactDirectionalFaceOracleTests(unittest.TestCase):
    def test_future_crossing_is_preserved_by_the_composed_ray_instrument(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertEqual(section.crossing_scales, (Fraction(1, 2),))
        boundary = next(
            sample
            for sample in section.samples
            if sample.sample_kind == "fan_boundary"
            and sample.scale == Fraction(1, 2)
        )
        self.assertEqual(boundary.total_state, "tie_unresolved")
        self.assertEqual(boundary.reachable_state, "tie_unresolved")
        self.assertEqual(boundary.face.total_function_cardinality, 2)
        self.assertEqual(boundary.face.reachable_support_cardinality, 2)
        self.assertEqual(boundary.face.minimum_gain_slope, Fraction(-1, 2))
        self.assertEqual(boundary.face.maximum_gain_slope, Fraction(1, 2))
        self.assertNotEqual(
            boundary.face.minimum_slope_tape,
            boundary.face.maximum_slope_tape,
        )
        self.assertEqual(boundary.face.work.lexicographic_passes, 2)
        self.assertEqual(boundary.face.work.materialized_response_tapes, 0)

    def test_face_extrema_equal_exhaustive_fixed_tape_slopes(self) -> None:
        source, endpoint = _policies()
        game = _CrossingGame()
        scale = Fraction(1, 2)
        current = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=scale,
        )
        tapes = _exhaustive_active_tapes(game, current, 1)
        source_exact = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(0),
        )
        endpoint_exact = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(1),
        )
        slopes = tuple(
            exact_fixed_response_trace(game, endpoint_exact, 1, dict(tape)).value
            - exact_fixed_response_trace(game, source_exact, 1, dict(tape)).value
            for tape in tapes
        )
        face = exact_directional_best_response_face(
            game,
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            scale=scale,
        )
        self.assertEqual(face.minimum_response_slope, min(slopes))
        self.assertEqual(face.maximum_response_slope, max(slopes))
        self.assertEqual(face.total_function_cardinality, len(tapes))
        reachable = {
            reachable_response_tape(game, current, 1, dict(tape)) for tape in tapes
        }
        self.assertEqual(face.reachable_support_cardinality, len(reachable))

    def test_billion_voice_shape_uses_no_cartesian_materialization(self) -> None:
        levels = 30
        game = _ChainGame(levels)
        policy = _chain_policy(levels)
        face = exact_directional_best_response_face(
            game,
            policy,
            policy,
            acting_player=0,
            target_player=0,
            scale=Fraction(0),
        )
        self.assertEqual(face.total_function_cardinality, 2**levels)
        self.assertEqual(face.reachable_support_cardinality, levels + 1)
        self.assertEqual(face.minimum_response_slope, 0)
        self.assertEqual(face.maximum_response_slope, 0)
        self.assertEqual(face.work.tree_nodes, 2 * levels + 1)
        self.assertEqual(face.work.target_action_edges, 2 * levels)
        self.assertEqual(face.work.sequence_variables, 2 * levels)
        self.assertEqual(face.work.materialized_response_tapes, 0)
        expected_per_pass = (
            face.work.tree_nodes
            + face.work.target_action_edges
            + face.work.sequence_variables
        )
        self.assertEqual(face.work.per_pass_linear_work_ceiling, expected_per_pass)
        self.assertEqual(
            face.work.total_logical_work_units,
            2 * expected_per_pass
            + face.work.total_cardinality_multiplications
            + face.work.reachable_cardinality_additions
            + face.work.reachable_cardinality_multiplications,
        )
        self.assertLessEqual(
            face.work.total_cardinality_multiplications
            + face.work.reachable_cardinality_additions
            + face.work.reachable_cardinality_multiplications,
            face.work.cardinality_linear_work_ceiling,
        )
        self.assertEqual(face.work.total_cardinality_bit_length, levels + 1)

    def test_oracle_source_contains_no_cartesian_enumerator(self) -> None:
        source = (
            Path(__file__).parents[1]
            / "src/pontius/exact_directional_face_oracle.py"
        )
        tree = ast.parse(source.read_text(encoding="utf-8"))
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        self.assertNotIn("itertools", imports)
        self.assertTrue(
            {
                "enumerate_exact_local_maximizer_tapes",
                "product",
            }.isdisjoint(calls)
        )

    def test_work_growth_is_linear_while_face_growth_is_exponential(self) -> None:
        faces = []
        for levels in (4, 10):
            game = _ChainGame(levels)
            policy = _chain_policy(levels)
            faces.append(
                exact_directional_best_response_face(
                    game,
                    policy,
                    policy,
                    acting_player=0,
                    target_player=0,
                    scale=Fraction(1, 2),
                )
            )
        small, large = faces
        self.assertEqual(
            large.total_function_cardinality // small.total_function_cardinality,
            64,
        )
        self.assertLess(
            large.work.total_logical_work_units,
            3 * small.work.total_logical_work_units,
        )

    def test_reachable_cardinality_equals_exhaustive_pruned_tape_quotient(self) -> None:
        levels = 4
        game = _ChainGame(levels)
        policy = _chain_policy(levels)
        tapes = _exhaustive_active_tapes(game, policy, 0)
        reachable = {
            reachable_response_tape(game, policy, 0, dict(tape)) for tape in tapes
        }
        face = exact_directional_best_response_face(
            game,
            policy,
            policy,
            acting_player=0,
            target_player=0,
            scale=Fraction(0),
        )
        self.assertEqual(len(tapes), 16)
        self.assertEqual(len(reachable), 5)
        self.assertEqual(face.total_function_cardinality, len(tapes))
        self.assertEqual(face.reachable_support_cardinality, len(reachable))

    def test_zero_support_chance_branch_is_retained_only_in_total_cardinality(self) -> None:
        game = _ZeroSupportChanceGame()
        policy = {
            "zero-support-live": {
                "first": Fraction(1, 2),
                "second": Fraction(1, 2),
            },
            "zero-support-dead": {
                "first": Fraction(1, 2),
                "second": Fraction(1, 2),
            },
        }
        face = exact_directional_best_response_face(
            game,
            policy,
            policy,
            acting_player=0,
            target_player=0,
            scale=Fraction(0),
        )
        self.assertEqual(face.total_function_cardinality, 4)
        self.assertEqual(face.reachable_support_cardinality, 2)
        support = {
            row.key: row.positive_counterfactual_support
            for row in face.information_sets
        }
        self.assertEqual(
            support,
            {"zero-support-dead": False, "zero-support-live": True},
        )

    def test_repeated_actor_extrema_use_independent_lexicographic_tapes(self) -> None:
        game = _RepeatedSlopeGame()
        source = {
            "repeated-slope-p0": {
                "left": Fraction(1, 2),
                "right": Fraction(1, 2),
            },
            "repeated-slope-root": {STOP: Fraction(1, 2), GO: Fraction(1, 2)},
            "repeated-slope-child": {
                "first": Fraction(1, 2),
                "second": Fraction(1, 2),
            },
        }
        endpoint = {
            **source,
            "repeated-slope-p0": {
                "left": Fraction(3, 4),
                "right": Fraction(1, 4),
            },
        }
        face = exact_directional_best_response_face(
            game,
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            scale=Fraction(0),
        )
        self.assertEqual(face.total_function_cardinality, 4)
        self.assertEqual(face.reachable_support_cardinality, 3)
        self.assertEqual(face.minimum_response_slope, Fraction(-1, 4))
        self.assertEqual(face.maximum_response_slope, Fraction(1, 4))
        self.assertNotEqual(face.minimum_slope_tape, face.maximum_slope_tape)
        current = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(0),
        )
        tapes = _exhaustive_active_tapes(game, current, 1)
        reachable = {
            reachable_response_tape(game, current, 1, dict(tape)) for tape in tapes
        }
        self.assertEqual(len(tapes), face.total_function_cardinality)
        self.assertEqual(len(reachable), face.reachable_support_cardinality)

    def test_repeated_actor_face_matches_all_pure_tapes_at_five_scales(self) -> None:
        game = _RepeatedSlopeGame()
        source = {
            "repeated-slope-p0": {
                "left": Fraction(1, 2),
                "right": Fraction(1, 2),
            },
            "repeated-slope-root": {STOP: Fraction(1, 2), GO: Fraction(1, 2)},
            "repeated-slope-child": {
                "first": Fraction(1, 2),
                "second": Fraction(1, 2),
            },
        }
        endpoint = {
            **source,
            "repeated-slope-p0": {
                "left": Fraction(3, 4),
                "right": Fraction(1, 4),
            },
        }
        source_exact = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(0),
        )
        endpoint_exact = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(1),
        )
        all_tapes = _all_response_tapes(game, source_exact, 1)
        endpoints = {
            tape: (
                exact_fixed_response_trace(
                    game, source_exact, 1, dict(tape)
                ).value,
                exact_fixed_response_trace(
                    game, endpoint_exact, 1, dict(tape)
                ).value,
            )
            for tape in all_tapes
        }
        for scale in (
            Fraction(0),
            Fraction(1, 4),
            Fraction(1, 2),
            Fraction(3, 4),
            Fraction(1),
        ):
            with self.subTest(scale=scale):
                current = realization_interpolated_policy(
                    game,
                    source,
                    endpoint,
                    acting_player=0,
                    scale=scale,
                )
                values = {
                    tape: (Fraction(1) - scale) * pair[0] + scale * pair[1]
                    for tape, pair in endpoints.items()
                }
                best = max(values.values())
                active = tuple(tape for tape, value in values.items() if value == best)
                slopes = tuple(
                    endpoints[tape][1] - endpoints[tape][0] for tape in active
                )
                reachable = {
                    reachable_response_tape(game, current, 1, dict(tape))
                    for tape in active
                }
                face = exact_directional_best_response_face(
                    game,
                    source,
                    endpoint,
                    acting_player=0,
                    target_player=1,
                    scale=scale,
                )
                self.assertEqual(face.response_value, best)
                self.assertEqual(face.total_function_cardinality, len(active))
                self.assertEqual(
                    face.reachable_support_cardinality,
                    len(reachable),
                )
                self.assertEqual(face.minimum_response_slope, min(slopes))
                self.assertEqual(face.maximum_response_slope, max(slopes))

    def test_positive_measure_tie_remains_unresolved_with_one_slope(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertEqual(section.crossing_scales, ())
        self.assertEqual(section.fan.total_tie_unresolved_measure, 1)
        self.assertTrue(
            all(sample.face.total_function_cardinality == 2 for sample in section.samples)
        )
        self.assertTrue(
            all(
                sample.face.minimum_gain_slope
                == sample.face.maximum_gain_slope
                == 0
                for sample in section.samples
            )
        )

    def test_compact_state_and_fan_piece_bounds_fail_closed(self) -> None:
        game = _ChainGame(10)
        policy = _chain_policy(10)
        with self.assertRaises(RuntimeError):
            exact_directional_best_response_face(
                game,
                policy,
                policy,
                acting_player=0,
                target_player=0,
                scale=Fraction(0),
                maximum_tree_nodes=20,
            )
        source, endpoint = _policies()
        with self.assertRaises(RuntimeError):
            compose_exact_directional_face_fan_section(
                _CrossingGame(),
                source,
                endpoint,
                acting_player=0,
                target_player=1,
                maximum_fan_tapes=1,
            )

    def test_profile_gain_slope_is_separate_from_response_slope(self) -> None:
        source, endpoint = _policies()
        face = exact_directional_best_response_face(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            scale=Fraction(1, 2),
        )
        source_profile = exact_policy_utilities(_CrossingGame(), source)[1]
        endpoint_profile = exact_policy_utilities(_CrossingGame(), endpoint)[1]
        self.assertEqual(
            face.profile_utility_slope,
            endpoint_profile - source_profile,
        )
        self.assertEqual(
            face.minimum_gain_slope,
            face.minimum_response_slope - face.profile_utility_slope,
        )

    def test_invalid_scale_and_bounds_fail_closed(self) -> None:
        source, endpoint = _policies()
        for scale in (Fraction(-1, 2), Fraction(3, 2), 0.5):
            with self.subTest(scale=scale):
                with self.assertRaises(ValueError):
                    exact_directional_best_response_face(
                        _CrossingGame(),
                        source,
                        endpoint,
                        acting_player=0,
                        target_player=1,
                        scale=scale,  # type: ignore[arg-type]
                    )
        with self.assertRaises(ValueError):
            exact_directional_best_response_face(
                _CrossingGame(),
                source,
                endpoint,
                acting_player=0,
                target_player=1,
                scale=Fraction(0),
                maximum_tree_nodes=0,
            )


if __name__ == "__main__":
    unittest.main()
