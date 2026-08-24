from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import unittest

from pontius.exact_selector_fan import reachable_response_tape
from pontius.exact_selector_window_oracle import exact_best_response_trace
from pontius.exact_tie_aware_affine_envelope import (
    build_exact_tie_aware_affine_section,
    enumerate_exact_local_maximizer_tapes,
)
from pontius.game import TERMINAL_PLAYER
from pontius.selector_window import fixed_response_selector_scores
from pontius.tie_aware_affine_adapter import choose_tie_aware_affine_mode


LEFT = "left"
RIGHT = "right"
FIRST = "first"
SECOND = "second"
STOP = "stop"
GO = "go"


@dataclass(frozen=True, slots=True)
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
            raise ValueError("invalid tie-aware control action")
        return _CrossingState((*self.history, action), self.tied)

    def information_state_key(self, player: int) -> str:
        if player != self.current_player:
            raise ValueError("tie-aware control player mismatch")
        return "tie-aware-p0" if player == 0 else "tie-aware-p1"

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("tie-aware return requested before terminal")
        target = (
            0.0
            if self.tied
            else float(
                self.history in ((LEFT, FIRST), (RIGHT, SECOND))
            )
        )
        return -target, target


@dataclass(frozen=True, slots=True)
class _CrossingGame:
    tied: bool = False
    num_players: int = 2

    def initial_state(self) -> _CrossingState:
        return _CrossingState(tied=self.tied)


@dataclass(frozen=True, slots=True)
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
            raise ValueError("invalid repeated-actor control action")
        return _RepeatedState((*self.history, action))

    def information_state_key(self, player: int) -> str:
        if player != 0 or self.current_player != 0:
            raise ValueError("repeated-actor control player mismatch")
        return "repeated-root" if not self.history else "repeated-child"

    def returns(self) -> tuple[float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("repeated-actor return requested before terminal")
        return (0.0,)


@dataclass(frozen=True, slots=True)
class _RepeatedGame:
    num_players: int = 1

    def initial_state(self) -> _RepeatedState:
        return _RepeatedState()


def _policies() -> tuple[dict[str, dict[str, Fraction]], ...]:
    source = {
        "tie-aware-p0": {LEFT: Fraction(3, 4), RIGHT: Fraction(1, 4)},
        "tie-aware-p1": {FIRST: Fraction(1, 2), SECOND: Fraction(1, 2)},
    }
    endpoint = {
        **source,
        "tie-aware-p0": {LEFT: Fraction(1, 4), RIGHT: Fraction(3, 4)},
    }
    return source, endpoint


class ExactTieAwareAffineEnvelopeTests(unittest.TestCase):
    def test_crossing_retains_both_rows_and_exact_tie_closure(self) -> None:
        source, endpoint = _policies()
        section = build_exact_tie_aware_affine_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        boundary = next(
            row for row in section.samples if row.scale == Fraction(1, 2)
        )
        self.assertTrue(section.single_tape_exact_eligible)
        self.assertEqual(len(section.source_active_tapes), 1)
        self.assertEqual(len(boundary.active_tapes), 2)
        self.assertEqual(len(section.rows), 2)
        for sample in section.samples:
            values = tuple(
                row.deviation_gain(sample.scale) for row in section.rows
            )
            self.assertEqual(max(values), sample.deviation_gain)
            self.assertTrue(all(value <= sample.deviation_gain for value in values))

    def test_positive_measure_tie_retains_every_equivalent_active_row(self) -> None:
        source, endpoint = _policies()
        section = build_exact_tie_aware_affine_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertFalse(section.single_tape_exact_eligible)
        self.assertEqual(len(section.source_active_tapes), 2)
        self.assertEqual(len(section.rows), 2)
        self.assertEqual(len(section.affine_equivalence_classes), 1)
        self.assertEqual(len(section.affine_equivalence_classes[0]), 2)
        self.assertTrue(
            all(len(sample.active_tapes) == 2 for sample in section.samples)
        )
        source_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in source.items()
        }
        endpoint_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in endpoint.items()
        }
        score_endpoints = {
            tape: (
                fixed_response_selector_scores(
                    _CrossingGame(tied=True),
                    source_float,
                    1,
                    dict(tape),
                ),
                fixed_response_selector_scores(
                    _CrossingGame(tied=True),
                    endpoint_float,
                    1,
                    dict(tape),
                ),
            )
            for tape in section.source_active_tapes
        }
        adapter = choose_tie_aware_affine_mode(
            section,
            score_endpoints,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(adapter.mode, "tie_aware_maximum_envelope")
        self.assertEqual(adapter.single_tape_scale_limit, 0.0)
        self.assertEqual(len(adapter.v2_windows), 2)
        self.assertTrue(
            all(window.scale_limit == 0.0 for _, window in adapter.v2_windows)
        )

    def test_repeated_actor_cartesian_ties_remain_total_tapes(self) -> None:
        game = _RepeatedGame()
        policy = {
            "repeated-root": {STOP: Fraction(1, 2), GO: Fraction(1, 2)},
            "repeated-child": {FIRST: Fraction(1, 2), SECOND: Fraction(1, 2)},
        }
        trace = exact_best_response_trace(game, policy, 0)
        tapes = enumerate_exact_local_maximizer_tapes(trace, maximum_tapes=4)
        self.assertEqual(len(tapes), 4)
        reachable = {
            reachable_response_tape(game, policy, 0, dict(tape))
            for tape in tapes
        }
        self.assertEqual(len(reachable), 3)
        with self.assertRaises(RuntimeError):
            enumerate_exact_local_maximizer_tapes(trace, maximum_tapes=3)

    def test_invalid_bounds_fail_closed(self) -> None:
        game = _RepeatedGame()
        policy = {
            "repeated-root": {STOP: Fraction(1), GO: Fraction(0)},
            "repeated-child": {FIRST: Fraction(1), SECOND: Fraction(0)},
        }
        trace = exact_best_response_trace(game, policy, 0)
        with self.assertRaises(ValueError):
            enumerate_exact_local_maximizer_tapes(trace, maximum_tapes=0)
        with self.assertRaises(ValueError):
            enumerate_exact_local_maximizer_tapes(
                trace,
                maximum_tapes=1.5,  # type: ignore[arg-type]
            )
        source, endpoint = _policies()
        with self.assertRaises(ValueError):
            build_exact_tie_aware_affine_section(
                _CrossingGame(),
                source,
                endpoint,
                acting_player=0,
                target_player=1,
                maximum_affine_rows=0,
            )


if __name__ == "__main__":
    unittest.main()
