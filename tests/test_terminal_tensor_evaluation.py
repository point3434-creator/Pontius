from __future__ import annotations

import unittest

import numpy as np

from pontius.evaluation import Policy, collect_information_sets
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem
from pontius.terminal_tensor_evaluation import evaluate_with_terminal_values


def _game() -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    ranges: list[dict[HoleCards, float]] = []
    cursor = 0
    for _ in range(3):
        weights = {}
        for hand_index in range(2):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(hand_index + 1)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=12.0,
        stacks=(30.0,) * 3,
        bet_size=3.0,
        player_weights=tuple(ranges),
    )


def _dense_policy(game: MultiwayRiverHoldem) -> Policy:
    result: Policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            result[key] = {
                action: float(index + 1) / 3.0
                for index, action in enumerate(actions)
            }
    return result


class TerminalTensorEvaluationTests(unittest.TestCase):
    def test_literal_terminal_tensor_reproduces_layout_result_and_actions(self) -> None:
        game = _game()
        layout = PublicTreeTensorEvaluator(game)
        policy = _dense_policy(game)
        expected = layout.evaluate(policy)
        actual = evaluate_with_terminal_values(layout, policy, layout.terminal_values)
        self.assertEqual(actual.best_response_actions, expected.best_response_actions)
        self.assertLessEqual(
            max(
                abs(left - right)
                for left, right in zip(
                    (
                        *actual.evaluation.utilities,
                        *actual.evaluation.best_response_values,
                        *actual.evaluation.deviation_gains,
                        actual.evaluation.nash_conv,
                    ),
                    (
                        *expected.evaluation.utilities,
                        *expected.evaluation.best_response_values,
                        *expected.evaluation.deviation_gains,
                        expected.evaluation.nash_conv,
                    ),
                    strict=True,
                )
            ),
            1e-14,
        )

    def test_terminal_override_changes_values_without_changing_layout(self) -> None:
        game = _game()
        layout = PublicTreeTensorEvaluator(game)
        terminal = layout.terminal_values.copy()
        terminal[:, :, 0] += 0.25
        original = layout.evaluate({}).evaluation
        changed = evaluate_with_terminal_values(layout, {}, terminal).evaluation
        self.assertNotEqual(changed.utilities[0], original.utilities[0])
        self.assertEqual(layout.evaluate({}).evaluation, original)

    def test_invalid_terminal_shape_and_nonfinite_values_are_rejected(self) -> None:
        layout = PublicTreeTensorEvaluator(_game())
        with self.assertRaisesRegex(ValueError, "shape"):
            evaluate_with_terminal_values(layout, {}, np.zeros((1, 1, 1)))
        invalid = layout.terminal_values.copy()
        invalid[0, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_with_terminal_values(layout, {}, invalid)


if __name__ == "__main__":
    unittest.main()
