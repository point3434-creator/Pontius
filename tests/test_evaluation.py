from __future__ import annotations

import unittest

from pontius.evaluation import (
    best_response,
    best_response_enumerated,
    collect_information_sets,
    counterfactual_regret_profile,
    evaluate_profile,
    expected_utilities,
)
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

    def test_counterfactual_regret_profile_has_known_kuhn_values(self) -> None:
        uniform = counterfactual_regret_profile(KuhnPoker(), {})
        passive = counterfactual_regret_profile(KuhnPoker(), passive_policy())

        self.assertEqual(uniform.information_sets, 12)
        self.assertAlmostEqual(uniform.total_positive_regret, 4.0 / 3.0)
        self.assertAlmostEqual(uniform.per_player_positive_regret[0], 19.0 / 24.0)
        self.assertAlmostEqual(uniform.per_player_positive_regret[1], 13.0 / 24.0)
        self.assertAlmostEqual(
            uniform.total_positive_regret,
            sum(uniform.per_player_positive_regret),
        )
        self.assertAlmostEqual(uniform.max_information_set_positive_regret, 0.25)
        self.assertAlmostEqual(passive.total_positive_regret, 2.0)
        self.assertAlmostEqual(passive.max_information_set_positive_regret, 2.0 / 3.0)

    def test_every_player_has_six_information_sets(self) -> None:
        game = KuhnPoker()
        self.assertEqual(len(collect_information_sets(game, 0)), 6)
        self.assertEqual(len(collect_information_sets(game, 1)), 6)

    def test_dynamic_best_response_matches_policy_enumeration(self) -> None:
        game = KuhnPoker()
        for policy in ({}, passive_policy()):
            for player in range(game.num_players):
                dynamic_value, _ = best_response(game, policy, player)
                enumerated_value, _ = best_response_enumerated(game, policy, player)
                self.assertAlmostEqual(dynamic_value, enumerated_value)

    def test_three_player_uniform_profile_has_exact_deviation_metrics(self) -> None:
        game = KuhnPoker(3)
        evaluation = evaluate_profile(game, {})
        self.assertEqual(len(evaluation.utilities), 3)
        self.assertAlmostEqual(sum(evaluation.utilities), 0.0)
        self.assertEqual(len(evaluation.deviation_gains), 3)
        self.assertGreater(evaluation.nash_conv, 0.0)
        self.assertIsNone(evaluation.exploitability)

    def test_three_player_best_response_is_locally_undominated(self) -> None:
        game = KuhnPoker(3)
        player = 0
        best_value, selected = best_response(game, {}, player)
        information_sets = collect_information_sets(game, player)
        best_policy = {
            key: {candidate: float(candidate == action) for candidate in information_sets[key]}
            for key, action in selected.items()
        }
        self.assertAlmostEqual(expected_utilities(game, best_policy)[player], best_value)

        for key, chosen in selected.items():
            alternative = next(action for action in information_sets[key] if action != chosen)
            deviated = {policy_key: dict(distribution) for policy_key, distribution in best_policy.items()}
            deviated[key] = {
                action: float(action == alternative) for action in information_sets[key]
            }
            self.assertLessEqual(expected_utilities(game, deviated)[player], best_value + 1e-12)

    def test_three_player_information_set_counts_are_symmetric(self) -> None:
        game = KuhnPoker(3)
        self.assertEqual(
            [len(collect_information_sets(game, player)) for player in range(3)],
            [16, 16, 16],
        )


if __name__ == "__main__":
    unittest.main()
