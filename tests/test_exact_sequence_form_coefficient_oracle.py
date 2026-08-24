from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
import unittest

from pontius.evaluation import collect_information_sets, expected_utilities
from pontius.exact_sequence_form_coefficient_oracle import (
    exact_expected_utilities,
    exact_open_axis_payoff_coefficients,
    exact_sequence_axis,
)
from pontius.legal_river_continuation import LegalHeadsUpRiverContinuation
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from pontius.one_seat_convex_generation import (
    _sequence_axis,
    open_axis_payoff_coefficients,
)
from pontius.river import RiverDeal, make_hole, parse_cards


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/exact_sequence_form_coefficient_oracle.py"


def _checked_to_river() -> NoLimitBettingState:
    state = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(6,) * 6,
        small_blind=1,
        big_blind=2,
    )
    for seat, action in (
        (3, FOLD),
        (4, FOLD),
        (5, FOLD),
        (0, FOLD),
        (1, CALL),
        (2, CHECK),
    ):
        if state.acting_seat != seat:
            raise AssertionError("oracle fixture preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    return state.apply_action(CHECK)


def _game() -> LegalHeadsUpRiverContinuation:
    return LegalHeadsUpRiverContinuation(
        board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
        base_state=_checked_to_river(),
        deals=((RiverDeal(make_hole("As", "Ad"), make_hole("Kh", "Kd")), 1.0),),
    )


def _policy(game: LegalHeadsUpRiverContinuation) -> dict:
    policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            if len(actions) == 4:
                probabilities = (0.125, 0.25, 0.125, 0.5)
            elif len(actions) == 3:
                probabilities = (0.25, 0.25, 0.5)
            elif len(actions) == 2:
                probabilities = (0.25, 0.75)
            else:
                raise AssertionError("oracle fixture action width drifted")
            policy[key] = dict(zip(actions, probabilities, strict=True))
    return policy


class ExactSequenceFormCoefficientOracleTests(unittest.TestCase):
    def test_exact_rows_match_float_subject_and_direct_utility(self) -> None:
        game = _game()
        policy = _policy(game)
        exact_axis = exact_sequence_axis(game, 0)
        float_axis = _sequence_axis(game, 0)
        self.assertEqual(len(exact_axis.information_sets), 3)
        self.assertEqual(len(exact_axis.variables), 8)
        self.assertEqual(set(exact_axis.variables), set(float_axis.variables))

        exact_realization = exact_axis.realization(policy)
        float_realization = float_axis.realization_from_policy(policy)
        for token, value in zip(
            float_axis.variables,
            float_realization,
            strict=True,
        ):
            self.assertLessEqual(abs(value - float(exact_realization[token])), 1e-15)

        exact_utilities = exact_expected_utilities(game, policy)
        float_utilities = expected_utilities(game, policy)
        self.assertEqual(sum(exact_utilities, Fraction(0)), 0)
        for payoff_player in range(game.num_players):
            exact = exact_open_axis_payoff_coefficients(
                game,
                policy,
                acting_player=0,
                payoff_player=payoff_player,
            )
            subject = open_axis_payoff_coefficients(
                game,
                policy,
                acting_player=0,
                payoff_player=payoff_player,
            )
            self.assertEqual(exact.value(exact_realization), exact_utilities[payoff_player])
            self.assertLessEqual(
                abs(subject.constant - float(exact.constant)),
                1e-15,
            )
            for token, coefficient in zip(
                float_axis.variables,
                subject.coefficients,
                strict=True,
            ):
                self.assertLessEqual(
                    abs(coefficient - float(exact.coefficients[token])),
                    1e-15,
                )
            self.assertLessEqual(
                abs(subject.value(float_realization) - float_utilities[payoff_player]),
                1e-15,
            )

    def test_fixed_raise_response_exercises_both_repeated_actor_sequences(self) -> None:
        game = _game()
        policy = _policy(game)
        responder = collect_information_sets(game, 1)
        for key, actions in responder.items():
            selected = raise_to(4) if raise_to(4) in actions else CALL
            policy[key] = {
                action: float(action == selected) for action in actions
            }
        row = exact_open_axis_payoff_coefficients(
            game,
            policy,
            acting_player=0,
            payoff_player=1,
        )
        histories = {
            key.rsplit("history=", 1)[-1]
            for (key, _), coefficient in row.coefficients.items()
            if "p1:raise-to-4" in key and coefficient != 0
        }
        self.assertTrue(any("raise-to-2" in history for history in histories))
        self.assertTrue(any("raise-to-3" in history for history in histories))

    def test_invalid_axis_policy_and_realization_fail_closed(self) -> None:
        game = _game()
        with self.assertRaises(ValueError):
            exact_sequence_axis(game, True)
        policy = _policy(game)
        key, actions = next(
            (key, actions)
            for key, actions in collect_information_sets(game, 0).items()
            if key.endswith("history=root")
        )
        policy[key] = {raise_to(999): 1.0}
        with self.assertRaisesRegex(ValueError, "unavailable"):
            exact_expected_utilities(game, policy)

        valid = _policy(game)
        axis = exact_sequence_axis(game, 0)
        row = exact_open_axis_payoff_coefficients(
            game,
            valid,
            acting_player=0,
            payoff_player=0,
        )
        realization = dict(axis.realization(valid))
        realization.pop(next(iter(realization)))
        with self.assertRaisesRegex(ValueError, "axes differ"):
            row.value(realization)
        self.assertIn(CHECK, actions)

    def test_oracle_source_has_no_subject_or_evaluator_dependency(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(
            any(
                "one_seat_convex_generation" in name
                or name.endswith("evaluation")
                for name in imports
            )
        )
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("open_axis_payoff_coefficients", called)
        self.assertNotIn("expected_utilities", called)


if __name__ == "__main__":
    unittest.main()
