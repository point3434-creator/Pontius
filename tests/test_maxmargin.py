from __future__ import annotations

import unittest

from pontius.evaluation import evaluate_profile
from pontius.leaf_experiment import prepare_blueprint
from pontius.maxmargin import (
    resolve_all_public_histories_best_response,
    resolve_all_public_histories_maxmargin,
    resolve_all_public_histories_sum_margin,
    solve_safe_best_response_subgame,
    solve_safe_sum_margin_subgame,
    solve_maxmargin_subgame,
)
from pontius.safe_resolving import resolve_subgame_safely


class MaxMarginOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.blueprint = prepare_blueprint("kuhn2", "lcfr", 20)

    def test_oracle_is_frontier_feasible_and_realization_equivalent(self) -> None:
        result = solve_maxmargin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
        )

        self.assertGreaterEqual(result.max_margin, -1e-10)
        self.assertLessEqual(result.total_positive_frontier_violation, 1e-10)
        self.assertLessEqual(result.matrix_duality_gap, 1e-10)
        self.assertLessEqual(result.realization_equivalence_max_error, 1e-10)
        self.assertAlmostEqual(result.max_margin, result.verified_min_margin)

    def test_oracle_dominates_an_under_solved_cfr_candidate_margin(self) -> None:
        history = ((0, "bet"),)
        oracle = solve_maxmargin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            history,
            resolver_player=1,
        )
        cfr = resolve_subgame_safely(
            self.blueprint.game,
            self.blueprint.policy,
            history,
            resolver_player=1,
            search_iterations=5,
        )
        cfr_min_margin = min(
            item.blueprint_cbr_value - item.candidate_cbr_value
            for item in cfr.comparisons
        )

        self.assertGreaterEqual(oracle.max_margin + 1e-10, cfr_min_margin)

    def test_oracle_replacement_cannot_increase_exploitability(self) -> None:
        result = solve_maxmargin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            ((0, "check"), (1, "bet")),
            resolver_player=0,
        )
        candidate = evaluate_profile(self.blueprint.game, result.policy)
        assert candidate.exploitability is not None
        assert self.blueprint.evaluation.exploitability is not None

        self.assertLessEqual(
            candidate.exploitability,
            self.blueprint.evaluation.exploitability + 1e-10,
        )

    def test_sum_margin_breaks_a_degenerate_max_min_tie_safely(self) -> None:
        max_min = solve_maxmargin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
        )
        summed = solve_safe_sum_margin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
        )

        self.assertAlmostEqual(max_min.max_margin, 0.0)
        self.assertGreater(summed.objective_value, 0.01)
        self.assertGreater(
            summed.verified_sum_margin,
            sum(record.margin for record in max_min.frontier_records),
        )
        self.assertFalse(summed.full_game_target_used)
        self.assertLessEqual(summed.total_positive_frontier_violation, 1e-10)
        self.assertLessEqual(summed.realization_equivalence_max_error, 1e-10)

    def test_hidden_best_response_oracle_measures_boundary_optimum(self) -> None:
        history = ((0, "bet"),)
        summed = solve_safe_sum_margin_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            history,
            resolver_player=1,
        )
        oracle = solve_safe_best_response_subgame(
            self.blueprint.game,
            self.blueprint.policy,
            history,
            resolver_player=1,
        )
        summed_evaluation = evaluate_profile(self.blueprint.game, summed.policy)
        oracle_evaluation = evaluate_profile(self.blueprint.game, oracle.policy)
        summed_gain = (
            self.blueprint.evaluation.nash_conv - summed_evaluation.nash_conv
        )
        oracle_gain = (
            self.blueprint.evaluation.nash_conv - oracle_evaluation.nash_conv
        )

        self.assertAlmostEqual(summed_gain, 0.0)
        self.assertGreater(oracle_gain, 0.0007)
        self.assertAlmostEqual(oracle.objective_value, oracle_gain)
        self.assertTrue(oracle.full_game_target_used)
        self.assertGreater(oracle.objective_response_constraints, 0)
        self.assertLessEqual(oracle.total_positive_frontier_violation, 1e-10)
        self.assertLessEqual(oracle.realization_equivalence_max_error, 1e-10)

    def test_nested_oracle_composition_cannot_increase_exploitability(self) -> None:
        result = resolve_all_public_histories_maxmargin(
            self.blueprint.game,
            self.blueprint.policy,
        )
        candidate = evaluate_profile(self.blueprint.game, result.policy)
        assert candidate.exploitability is not None
        assert self.blueprint.evaluation.exploitability is not None

        self.assertEqual(result.structural_public_histories, 4)
        self.assertEqual(result.searched_public_histories, 4)
        self.assertLessEqual(
            candidate.exploitability,
            self.blueprint.evaluation.exploitability
            + result.cumulative_exploitability_increase_bound
            + 1e-10,
        )

    def test_sum_margin_composition_tracks_hidden_greedy_control(self) -> None:
        summed = resolve_all_public_histories_sum_margin(
            self.blueprint.game,
            self.blueprint.policy,
        )
        oracle = resolve_all_public_histories_best_response(
            self.blueprint.game,
            self.blueprint.policy,
        )
        summed_evaluation = evaluate_profile(self.blueprint.game, summed.policy)
        oracle_evaluation = evaluate_profile(self.blueprint.game, oracle.policy)
        summed_gain = (
            self.blueprint.evaluation.nash_conv - summed_evaluation.nash_conv
        )
        oracle_gain = (
            self.blueprint.evaluation.nash_conv - oracle_evaluation.nash_conv
        )

        self.assertEqual(summed.searched_public_histories, 4)
        self.assertEqual(oracle.searched_public_histories, 4)
        self.assertFalse(summed.full_game_target_used)
        self.assertTrue(oracle.full_game_target_used)
        self.assertGreaterEqual(summed_gain, 0.9 * oracle_gain)
        self.assertLessEqual(summed_gain, oracle_gain + 1e-10)
        self.assertAlmostEqual(oracle_gain, oracle.total_verified_objective_value)
        self.assertLessEqual(
            summed.cumulative_exploitability_increase_bound,
            1e-10,
        )
        self.assertLessEqual(
            oracle.cumulative_exploitability_increase_bound,
            1e-10,
        )

    def test_plan_limit_and_invalid_tolerance_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "pure plans"):
            solve_maxmargin_subgame(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                max_pure_plans=10,
            )
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            solve_maxmargin_subgame(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                tolerance=float("nan"),
            )
        with self.assertRaisesRegex(ValueError, "must be positive"):
            solve_safe_sum_margin_subgame(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                max_pure_plans=0,
            )


if __name__ == "__main__":
    unittest.main()
