from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import unittest

from pontius.evaluation import best_response
from pontius.exact_selector_fan import (
    map_exact_selector_fan_section,
    reachable_response_tape,
    realization_interpolated_policy,
)
from pontius.exact_selector_window_oracle import (
    exact_best_response_trace,
    exact_fixed_response_trace,
)
from pontius.game import TERMINAL_PLAYER
from pontius.selector_window import (
    conservative_affine_selector_window,
    fixed_response_selector_scores,
)


LEFT = "left"
RIGHT = "right"
FIRST = "first"
SECOND = "second"
STOP = "stop"
GO = "go"


@dataclass(frozen=True)
class _CrossingState:
    history: tuple[str, ...] = ()
    tied: bool = False

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if len(self.history) == 2 else len(self.history)

    def legal_actions(self) -> tuple[str, ...]:
        return (LEFT, RIGHT) if not self.history else (FIRST, SECOND)

    def chance_outcomes(self) -> tuple[()]:
        return ()

    def apply_action(self, action: str) -> _CrossingState:
        if action not in self.legal_actions():
            raise ValueError("invalid crossing action")
        return _CrossingState((*self.history, action), self.tied)

    def information_state_key(self, player: int) -> str:
        if player != self.current_player:
            raise ValueError("crossing information player mismatch")
        return "crossing-p0" if player == 0 else "crossing-p1"

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("crossing return requested before terminal")
        if self.tied:
            target = 0.0
        else:
            target = float(
                (self.history == (LEFT, FIRST))
                or (self.history == (RIGHT, SECOND))
            )
        return -target, target


@dataclass(frozen=True)
class _CrossingGame:
    tied: bool = False
    num_players: int = 2

    def initial_state(self) -> _CrossingState:
        return _CrossingState(tied=self.tied)


@dataclass(frozen=True)
class _RepeatedState:
    history: tuple[str, ...] = ()

    @property
    def current_player(self) -> int:
        if not self.history or self.history == (GO,):
            return 0
        return TERMINAL_PLAYER

    def legal_actions(self) -> tuple[str, ...]:
        return (STOP, GO) if not self.history else (FIRST, SECOND)

    def chance_outcomes(self) -> tuple[()]:
        return ()

    def apply_action(self, action: str) -> _RepeatedState:
        if action not in self.legal_actions():
            raise ValueError("invalid repeated-actor action")
        return _RepeatedState((*self.history, action))

    def information_state_key(self, player: int) -> str:
        if player != 0 or self.current_player != 0:
            raise ValueError("repeated-actor information player mismatch")
        return "repeated-root" if not self.history else "repeated-child"

    def returns(self) -> tuple[float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("repeated-actor return requested before terminal")
        return (0.0,)


@dataclass(frozen=True)
class _RepeatedGame:
    num_players: int = 1

    def initial_state(self) -> _RepeatedState:
        return _RepeatedState()


class ExactSelectorFanTests(unittest.TestCase):
    def test_exact_selector_matches_production_tapes_and_values(self) -> None:
        game = _CrossingGame()
        policy = {
            "crossing-p0": {LEFT: Fraction(3, 4), RIGHT: Fraction(1, 4)},
            "crossing-p1": {FIRST: Fraction(1, 2), SECOND: Fraction(1, 2)},
        }
        for player in range(game.num_players):
            value, tape = best_response(game, policy, player)
            exact = exact_best_response_trace(game, policy, player)
            fixed = exact_fixed_response_trace(
                game,
                policy,
                player,
                exact.selected_actions,
            )
            self.assertEqual(dict(exact.selected_actions), tape)
            self.assertEqual(float(exact.value), value)
            self.assertEqual(fixed.value, exact.value)
            self.assertTrue(
                all(row.selected_is_maximal for row in fixed.information_sets)
            )

    def test_crossing_section_is_exactly_fixed_tie_switched(self) -> None:
        game = _CrossingGame()
        source = {
            "crossing-p0": {LEFT: Fraction(3, 4), RIGHT: Fraction(1, 4)},
            "crossing-p1": {FIRST: Fraction(1, 2), SECOND: Fraction(1, 2)},
        }
        endpoint = {
            **source,
            "crossing-p0": {LEFT: Fraction(1, 4), RIGHT: Fraction(3, 4)},
        }
        fan = map_exact_selector_fan_section(
            game,
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )

        self.assertEqual(fan.source_cell_upper, Fraction(1, 2))
        self.assertEqual(fan.legacy_source_breakpoint, Fraction(1, 2))
        self.assertEqual(fan.total_fixed_measure, Fraction(1, 2))
        self.assertEqual(fan.total_tie_unresolved_measure, 0)
        self.assertEqual(fan.total_switched_measure, Fraction(1, 2))
        self.assertIn(Fraction(1, 2), fan.total_tie_points)
        boundary = next(point for point in fan.points if point.scale == Fraction(1, 2))
        self.assertEqual(boundary.total_state, "tie_unresolved")

        source_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in source.items()
        }
        endpoint_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in endpoint.items()
        }
        tape = dict(fan.source_tape)
        left = fixed_response_selector_scores(game, source_float, 1, tape)
        right = fixed_response_selector_scores(game, endpoint_float, 1, tape)
        exact_window = conservative_affine_selector_window(
            left,
            right,
            selector_margin_allowance=0.0,
        )
        conservative = conservative_affine_selector_window(
            left,
            right,
            selector_margin_allowance=0.01,
        )
        self.assertEqual(exact_window.scale_limit, 0.5)
        self.assertLess(conservative.scale_limit, exact_window.scale_limit)

    def test_degenerate_tie_interval_has_full_measure(self) -> None:
        game = _CrossingGame(tied=True)
        source = {
            "crossing-p0": {LEFT: Fraction(3, 4), RIGHT: Fraction(1, 4)},
            "crossing-p1": {FIRST: Fraction(1, 2), SECOND: Fraction(1, 2)},
        }
        endpoint = {
            **source,
            "crossing-p0": {LEFT: Fraction(1, 4), RIGHT: Fraction(3, 4)},
        }
        fan = map_exact_selector_fan_section(
            game,
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertEqual(fan.total_tie_unresolved_measure, 1)
        self.assertEqual(fan.reachable_tie_unresolved_measure, 1)
        self.assertEqual(fan.total_fixed_measure, 0)
        self.assertTrue(
            all(segment.total_state == "tie_unresolved" for segment in fan.segments)
        )

    def test_total_and_reachable_tape_semantics_are_not_conflated(self) -> None:
        game = _RepeatedGame()
        policy = {
            "repeated-root": {STOP: Fraction(1), GO: Fraction(0)},
            "repeated-child": {FIRST: Fraction(1), SECOND: Fraction(0)},
        }
        first = {"repeated-root": STOP, "repeated-child": FIRST}
        second = {"repeated-root": STOP, "repeated-child": SECOND}
        self.assertNotEqual(tuple(sorted(first.items())), tuple(sorted(second.items())))
        self.assertEqual(
            reachable_response_tape(game, policy, 0, first),
            reachable_response_tape(game, policy, 0, second),
        )
        self.assertEqual(
            reachable_response_tape(game, policy, 0, first),
            (("repeated-root", STOP),),
        )

    def test_realization_interpolation_preserves_repeated_actor_flow(self) -> None:
        game = _RepeatedGame()
        source = {
            "repeated-root": {STOP: Fraction(1, 2), GO: Fraction(1, 2)},
            "repeated-child": {FIRST: Fraction(3, 4), SECOND: Fraction(1, 4)},
        }
        endpoint = {
            "repeated-root": {STOP: Fraction(1, 4), GO: Fraction(3, 4)},
            "repeated-child": {FIRST: Fraction(1, 4), SECOND: Fraction(3, 4)},
        }
        middle = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=0,
            scale=Fraction(1, 2),
        )
        self.assertEqual(sum(middle["repeated-root"].values()), 1)
        self.assertEqual(sum(middle["repeated-child"].values()), 1)
        root_go = middle["repeated-root"][GO]
        child_first_realization = root_go * middle["repeated-child"][FIRST]
        self.assertEqual(
            child_first_realization,
            Fraction(1, 2) * Fraction(1, 2) * Fraction(3, 4)
            + Fraction(1, 2) * Fraction(3, 4) * Fraction(1, 4),
        )


if __name__ == "__main__":
    unittest.main()
