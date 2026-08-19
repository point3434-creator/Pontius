from __future__ import annotations

import unittest

from pontius.evaluation import collect_information_sets, evaluate_profile, expected_utilities
from pontius.kuhn import BET, CALL, CHECK, FOLD, KuhnPoker


def passive_policy() -> dict[str, dict[str, float]]:
    game = KuhnPoker()
    policy: dict[str, dict[str, float]] = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            if CHECK in actions:
                chosen = CHECK
            elif FOLD in actions:
                chosen = FOLD
            else:
                raise AssertionError(actions)
            policy[key] = {action: float(action == chosen) for action in actions}
    return policy


class ExactEvaluationTests(unittest.TestCase):
    def test_passive_profile_is_zero_sum_and_zero_value(self) -> None:
        utilities = expected_utilities(KuhnPoker(), passive_policy())
        self.assertAlmostEqual(sum(utilities), 0.0)
        self.assertAlmostEqual(utilities[0], 0.0)

    def test_passive_profile_is_exploitable(self) -> None:
        evaluation = evaluate_profile(KuhnPoker(), passive_policy())
        self.assertGreater(evaluation.nash_conv, 0.5)
        self.assertAlmostEqual(evaluation.exploitability or 0.0, evaluation.nash_conv / 2.0)

    def test_uniform_profile_is_evaluable(self) -> None:
        evaluation = evaluate_profile(KuhnPoker(), {})
        self.assertAlmostEqual(sum(evaluation.utilities), 0.0)
        self.assertGreater(evaluation.nash_conv, 0.0)
        self.assertEqual(len(evaluation.best_response_values), 2)

    def test_every_player_has_six_information_sets(self) -> None:
        game = KuhnPoker()
        self.assertEqual(len(collect_information_sets(game, 0)), 6)
        self.assertEqual(len(collect_information_sets(game, 1)), 6)


if __name__ == "__main__":
    unittest.main()

