from __future__ import annotations

import unittest

from pontius.continual import (
    PublicBeliefGame,
    public_belief,
    public_histories,
    resolve_all_public_histories,
)
from pontius.evaluation import (
    collect_information_sets,
    evaluate_profile,
    policy_distribution,
)
from pontius.kuhn import CHECK, FOLD, KuhnPoker
from pontius.leaf_experiment import prepare_blueprint


class ContinualResolvingTests(unittest.TestCase):
    def test_root_belief_is_uniform_and_public_tree_has_four_decisions(self) -> None:
        game = KuhnPoker()
        belief = public_belief(game, {}, ())

        self.assertIsNotNone(belief)
        assert belief is not None
        self.assertEqual(len(public_histories(game)), 4)
        self.assertEqual(len(belief.states), 6)
        self.assertAlmostEqual(belief.public_reach_probability, 1.0)
        self.assertTrue(
            all(abs(probability - 1.0 / 6.0) < 1e-12 for _, probability in belief.states)
        )
        rooted = PublicBeliefGame(2, belief)
        self.assertEqual(len(rooted.initial_state().chance_outcomes()), 6)

    def test_belief_applies_bayes_rule_to_card_dependent_action(self) -> None:
        game = KuhnPoker()
        policy = {
            f"p0|card={card}|history=root": {
                CHECK: probability,
                "bet": 1.0 - probability,
            }
            for card, probability in ((0, 0.2), (1, 0.5), (2, 0.8))
        }
        history = ((0, CHECK),)
        belief = public_belief(game, policy, history)

        self.assertIsNotNone(belief)
        assert belief is not None
        self.assertAlmostEqual(belief.public_reach_probability, 0.5)
        probability_by_card = {0: 0.0, 1: 0.0, 2: 0.0}
        for state, probability in belief.states:
            assert state.cards is not None
            probability_by_card[state.cards[0]] += probability
        self.assertAlmostEqual(probability_by_card[0], 0.2 / 1.5)
        self.assertAlmostEqual(probability_by_card[1], 0.5 / 1.5)
        self.assertAlmostEqual(probability_by_card[2], 0.8 / 1.5)

    def test_full_anchor_composes_exact_blueprint_once_per_information_set(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 10)
        result = resolve_all_public_histories(
            prepared.game,
            prepared.policy,
            search_iterations=2,
            depth_limit=2,
            in_search_blueprint_weight=1.0,
        )

        information_set_count = sum(
            len(collect_information_sets(prepared.game, player))
            for player in range(prepared.game.num_players)
        )
        self.assertEqual(result.structural_public_histories, 4)
        self.assertEqual(result.searched_public_histories, 4)
        self.assertEqual(result.deployed_public_histories, 4)
        self.assertEqual(result.searched_information_sets, information_set_count)
        self.assertEqual(result.deployed_information_sets, information_set_count)
        self.assertFalse(result.skipped_zero_reach_histories)
        for player in range(prepared.game.num_players):
            for key, actions in collect_information_sets(prepared.game, player).items():
                expected = policy_distribution(prepared.policy, key, actions)
                actual = policy_distribution(result.policy, key, actions)
                for action in actions:
                    self.assertAlmostEqual(actual[action], expected[action])
        self.assertAlmostEqual(
            evaluate_profile(prepared.game, result.policy).nash_conv,
            prepared.evaluation.nash_conv,
        )
        self.assertTrue(
            all(
                record.root_candidate_max_policy_tv < 1e-15
                for record in result.records
            )
        )
        self.assertGreater(result.expected_public_decisions_per_hand, 1.0)

    def test_zero_reach_public_histories_keep_blueprint_fallback(self) -> None:
        game = KuhnPoker()
        passive = {}
        for player in range(game.num_players):
            for key, actions in collect_information_sets(game, player).items():
                selected = CHECK if CHECK in actions else FOLD
                passive[key] = {
                    action: float(action == selected) for action in actions
                }
        result = resolve_all_public_histories(
            game,
            passive,
            search_iterations=1,
            in_search_blueprint_weight=1.0,
        )

        self.assertEqual(result.searched_public_histories, 2)
        self.assertEqual(len(result.skipped_zero_reach_histories), 2)
        self.assertEqual(result.policy, passive)

    def test_recorded_posteriors_match_final_composed_prefix(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 20)
        result = resolve_all_public_histories(
            prepared.game,
            prepared.policy,
            search_iterations=3,
            depth_limit=2,
            in_search_blueprint_weight=0.99,
        )

        for record in result.records:
            final_belief = public_belief(
                prepared.game,
                result.policy,
                record.history,
            )
            self.assertIsNotNone(final_belief)
            assert final_belief is not None
            self.assertAlmostEqual(
                final_belief.public_reach_probability,
                record.public_reach_probability,
            )
            self.assertAlmostEqual(
                final_belief.effective_state_count,
                record.posterior_effective_states,
            )
            self.assertAlmostEqual(
                final_belief.entropy_nats,
                record.posterior_entropy_nats,
            )

    def test_local_gate_never_deploys_a_nonpositive_candidate(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 20)
        result = resolve_all_public_histories(
            prepared.game,
            prepared.policy,
            search_iterations=3,
            depth_limit=2,
            in_search_blueprint_weight=0.99,
            deployment_gate="positive_local_model_gain",
        )

        self.assertTrue(
            all(
                record.root_candidate_model_nash_conv_improvement > 0.0
                for record in result.records
                if record.candidate_deployed
            )
        )

    def test_invalid_resolver_configuration_is_rejected(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 2)
        with self.assertRaises(ValueError):
            resolve_all_public_histories(
                prepared.game,
                prepared.policy,
                search_iterations=0,
            )
        with self.assertRaises(ValueError):
            resolve_all_public_histories(
                prepared.game,
                prepared.policy,
                solver_name="imaginary",
            )
        with self.assertRaises(ValueError):
            resolve_all_public_histories(
                prepared.game,
                prepared.policy,
                deployment_gate="oracle",
            )


if __name__ == "__main__":
    unittest.main()
