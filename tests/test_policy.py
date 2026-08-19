from __future__ import annotations

import unittest

from pontius.evaluation import collect_information_sets
from pontius.kuhn import KuhnPoker
from pontius.policy import interpolate_policy


class PolicyInterpolationTests(unittest.TestCase):
    def setUp(self) -> None:
        game = KuhnPoker()
        self.information_sets = {
            key: actions
            for player in range(game.num_players)
            for key, actions in collect_information_sets(game, player).items()
        }
        self.key, self.actions = next(iter(self.information_sets.items()))
        first, second = self.actions
        self.blueprint = {self.key: {first: 0.8, second: 0.2}}
        self.candidate = {self.key: {first: 0.1, second: 0.9}}

    def test_zero_weight_is_no_op_and_one_is_replacement(self) -> None:
        no_op = interpolate_policy(
            self.blueprint,
            self.candidate,
            self.information_sets,
            candidate_weight=0.0,
        )
        replacement = interpolate_policy(
            self.blueprint,
            self.candidate,
            self.information_sets,
            candidate_weight=1.0,
        )
        self.assertEqual(no_op[self.key], self.blueprint[self.key])
        self.assertEqual(replacement[self.key], self.candidate[self.key])

    def test_partial_weight_is_linear_interpolation(self) -> None:
        result = interpolate_policy(
            self.blueprint,
            self.candidate,
            self.information_sets,
            candidate_weight=0.25,
        )
        first, second = self.actions
        self.assertAlmostEqual(result[self.key][first], 0.625)
        self.assertAlmostEqual(result[self.key][second], 0.375)

    def test_invalid_weight_and_unknown_information_set_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            interpolate_policy(
                self.blueprint,
                self.candidate,
                self.information_sets,
                candidate_weight=-0.1,
            )
        with self.assertRaises(ValueError):
            interpolate_policy(
                self.blueprint,
                {"unknown": {"a": 1.0}},
                self.information_sets,
                candidate_weight=0.5,
            )


if __name__ == "__main__":
    unittest.main()
