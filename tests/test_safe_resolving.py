from __future__ import annotations

import unittest

from pontius.evaluation import (
    Policy,
    best_response,
    best_response_enumerated,
    evaluate_profile,
    expected_utilities,
)
from pontius.kuhn import BET, CALL, CHECK, FOLD, KuhnPoker
from pontius.safe_resolving import (
    FOLLOW,
    TERMINATE,
    ResolvingGadgetGame,
    build_counterfactual_frontier,
    resolve_all_public_histories_safely,
    resolve_subgame_safely,
)


def _policy_with_player_one_bet(probability: float) -> Policy:
    policy: Policy = {}
    for card in range(3):
        policy[f"p0|card={card}|history=root"] = {CHECK: 0.6, BET: 0.4}
        policy[f"p1|card={card}|history=p0:check"] = {
            CHECK: 1.0 - probability,
            BET: probability,
        }
        policy[f"p1|card={card}|history=p0:bet"] = {FOLD: 0.5, CALL: 0.5}
        policy[
            f"p0|card={card}|history=p0:check/p1:bet"
        ] = {FOLD: 0.5, CALL: 0.5}
    return policy


class SafeResolvingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = KuhnPoker(2)
        self.boundary = ((0, CHECK), (1, BET))

    def test_root_reach_excludes_the_opponents_prior_strategy(self) -> None:
        low_bet = build_counterfactual_frontier(
            self.game,
            _policy_with_player_one_bet(0.1),
            self.boundary,
            resolver_player=0,
        )
        high_bet = build_counterfactual_frontier(
            self.game,
            _policy_with_player_one_bet(0.9),
            self.boundary,
            resolver_player=0,
        )

        self.assertEqual(low_bet.roots, high_bet.roots)
        self.assertAlmostEqual(low_bet.total_counterfactual_reach, 0.6)
        self.assertEqual(len(low_bet.entries), 3)

    def test_terminate_policy_reproduces_the_blueprint_frontier_value(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        frontier = build_counterfactual_frontier(
            self.game,
            blueprint,
            self.boundary,
            resolver_player=0,
        )
        gadget = ResolvingGadgetGame(frontier)
        terminate_policy: Policy = {
            entry.key: {TERMINATE: 1.0, FOLLOW: 0.0}
            for entry in frontier.entries
        }

        opponent_value = expected_utilities(gadget, terminate_policy)[1]
        self.assertAlmostEqual(opponent_value, frontier.opponent_gadget_value)

    def test_blueprint_is_a_feasible_gadget_security_strategy(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        frontier = build_counterfactual_frontier(
            self.game,
            blueprint,
            self.boundary,
            resolver_player=0,
        )
        gadget = ResolvingGadgetGame(frontier)

        opponent_best_response, _ = best_response(gadget, blueprint, player=1)
        self.assertAlmostEqual(
            opponent_best_response,
            frontier.opponent_gadget_value,
        )

    def test_gadget_dynamic_best_response_matches_enumeration(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        frontier = build_counterfactual_frontier(
            self.game,
            blueprint,
            self.boundary,
            resolver_player=0,
        )
        gadget = ResolvingGadgetGame(frontier)

        dynamic_value, _ = best_response(gadget, blueprint, player=1)
        enumerated_value, _ = best_response_enumerated(
            gadget,
            blueprint,
            player=1,
        )
        self.assertAlmostEqual(dynamic_value, enumerated_value)

    def test_finite_solver_residual_equals_positive_frontier_violation(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        result = resolve_subgame_safely(
            self.game,
            blueprint,
            self.boundary,
            resolver_player=0,
            search_iterations=100,
        )

        self.assertAlmostEqual(
            result.gadget_opponent_security_residual,
            result.total_positive_frontier_violation,
        )
        self.assertGreaterEqual(result.gadget_evaluation.nash_conv, 0.0)

    def test_full_game_exploitability_respects_the_residual_bound(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        result = resolve_subgame_safely(
            self.game,
            blueprint,
            self.boundary,
            resolver_player=0,
            search_iterations=100,
        )
        blueprint_exploitability = evaluate_profile(
            self.game,
            blueprint,
        ).exploitability
        candidate_exploitability = evaluate_profile(
            self.game,
            result.policy,
        ).exploitability
        assert blueprint_exploitability is not None
        assert candidate_exploitability is not None

        self.assertLessEqual(
            candidate_exploitability,
            blueprint_exploitability
            + result.full_game_exploitability_increase_bound
            + 1e-10,
        )

    def test_root_forward_composition_has_an_additive_residual_bound(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        result = resolve_all_public_histories_safely(
            self.game,
            blueprint,
            search_iterations=100,
        )
        blueprint_exploitability = evaluate_profile(
            self.game,
            blueprint,
        ).exploitability
        candidate_exploitability = evaluate_profile(
            self.game,
            result.policy,
        ).exploitability
        assert blueprint_exploitability is not None
        assert candidate_exploitability is not None

        self.assertEqual(result.structural_public_histories, 4)
        self.assertEqual(result.searched_public_histories, 4)
        self.assertLessEqual(
            candidate_exploitability,
            blueprint_exploitability
            + result.cumulative_exploitability_increase_bound
            + 1e-10,
        )

    def test_strict_frontier_gate_rejects_uncertified_replacements(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        result = resolve_all_public_histories_safely(
            self.game,
            blueprint,
            search_iterations=1,
            max_deployed_frontier_violation=0.0,
        )

        self.assertTrue(any(not record.candidate_deployed for record in result.records))
        self.assertTrue(
            all(
                record.exploitability_increase_bound == 0.0
                for record in result.records
                if not record.candidate_deployed
            )
        )

    def test_invalid_configuration_is_rejected(self) -> None:
        blueprint = _policy_with_player_one_bet(0.5)
        with self.assertRaisesRegex(ValueError, "two-player"):
            build_counterfactual_frontier(
                KuhnPoker(3),
                blueprint,
                (),
                resolver_player=0,
            )
        with self.assertRaisesRegex(ValueError, "unknown public"):
            build_counterfactual_frontier(
                self.game,
                blueprint,
                ((1, BET),),
                resolver_player=0,
            )
        with self.assertRaisesRegex(ValueError, "unsupported search solver"):
            resolve_subgame_safely(
                self.game,
                blueprint,
                self.boundary,
                resolver_player=0,
                solver_name="imaginary",
            )
        with self.assertRaisesRegex(ValueError, "positive"):
            resolve_subgame_safely(
                self.game,
                blueprint,
                self.boundary,
                resolver_player=0,
                search_iterations=0,
            )


if __name__ == "__main__":
    unittest.main()
