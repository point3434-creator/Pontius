from __future__ import annotations

import unittest

from pontius.constrained_generation import solve_sum_margin_with_generation
from pontius.continual import public_belief, public_histories
from pontius.evaluation import evaluate_profile
from pontius.leaf_experiment import prepare_blueprint


class ConstrainedGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.blueprint = prepare_blueprint("kuhn2", "lcfr", 20)

    def test_dynamic_row_and_column_generation_reaches_exact_root_optimum(self) -> None:
        result = solve_sum_margin_with_generation(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
        )

        self.assertTrue(result.converged)
        self.assertAlmostEqual(
            result.incumbent_sum_margin,
            result.exact_sum_margin_optimum,
        )
        self.assertLess(result.final_columns, result.resolver_normal_form_plans)
        self.assertAlmostEqual(result.updates[-1].best_reduced_cost, 0.0)
        self.assertLessEqual(
            result.updates[-1].realization_equivalence_max_error,
            1e-10,
        )
        self.assertTrue(any(update.added_column for update in result.updates))
        self.assertTrue(
            any(update.added_response_constraints for update in result.updates)
        )
        for update in result.updates:
            self.assertAlmostEqual(
                update.cumulative_candidate_compute_seconds
                + update.pricing_seconds,
                update.cumulative_decision_compute_seconds,
            )
            self.assertGreater(update.candidate_max_column_weight, 0.0)
            self.assertLessEqual(update.candidate_max_column_weight, 1.0)
            self.assertGreater(update.candidate_column_weight_concentration, 0.0)
            self.assertLessEqual(update.candidate_column_weight_concentration, 1.0)
            self.assertGreaterEqual(update.candidate_column_weight_entropy, 0.0)
            self.assertLessEqual(update.candidate_column_weight_entropy, 1.0)
            self.assertLessEqual(
                update.response_dual_active_count,
                update.response_constraints_before_update,
            )
            self.assertGreaterEqual(update.response_dual_max_share, 0.0)
            self.assertLessEqual(update.response_dual_max_share, 1.0)

    def test_every_public_boundary_matches_the_normal_form_teacher(self) -> None:
        for history in public_histories(self.blueprint.game):
            belief = public_belief(
                self.blueprint.game,
                self.blueprint.policy,
                history,
            )
            assert belief is not None
            with self.subTest(history=history, resolver_player=belief.acting_player):
                result = solve_sum_margin_with_generation(
                    self.blueprint.game,
                    self.blueprint.policy,
                    history,
                    resolver_player=belief.acting_player,
                )
                self.assertTrue(result.converged)
                self.assertAlmostEqual(
                    result.incumbent_sum_margin,
                    result.exact_sum_margin_optimum,
                )
                self.assertTrue(result.updates[-1].safe_candidate)
                self.assertLessEqual(
                    result.updates[-1].master_duality_gap,
                    1e-10,
                )

    def test_truncated_generation_retains_the_safe_blueprint_incumbent(self) -> None:
        result = solve_sum_margin_with_generation(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
            max_updates=1,
        )

        self.assertFalse(result.converged)
        self.assertEqual(result.incumbent_sum_margin, 0.0)
        self.assertTrue(result.updates[0].safe_candidate)
        self.assertFalse(result.updates[0].incumbent_updated)
        self.assertEqual(result.updates[0].candidate_support_size, 1)
        self.assertIsNotNone(result.updates[0].added_column)
        self.assertEqual(result.policy, self.blueprint.policy)

    def test_phase_aware_terminal_checkpoint_skips_future_only_pricing(self) -> None:
        result = solve_sum_margin_with_generation(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
            max_updates=1,
            verify_generated_responses=False,
            verify_realization_equivalence=False,
            price_after_last_update=False,
        )
        update = result.updates[0]

        self.assertFalse(result.converged)
        self.assertFalse(update.pricing_performed)
        self.assertEqual(update.pricing_seconds, 0.0)
        self.assertIsNone(update.best_pricing_score)
        self.assertIsNone(update.best_reduced_cost)
        self.assertIsNone(update.added_column)
        self.assertIsNone(update.realization_equivalence_max_error)
        self.assertEqual(result.final_columns, 1)
        self.assertEqual(
            update.cumulative_candidate_compute_seconds,
            update.cumulative_decision_compute_seconds,
        )

    def test_one_pass_response_oracle_still_matches_exact_teacher(self) -> None:
        result = solve_sum_margin_with_generation(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
            verify_generated_responses=False,
            verify_realization_equivalence=False,
        )

        self.assertTrue(result.converged)
        self.assertAlmostEqual(
            result.incumbent_sum_margin,
            result.exact_sum_margin_optimum,
        )
        self.assertTrue(
            all(
                update.realization_equivalence_max_error is None
                for update in result.updates
            )
        )

    def test_safe_generated_replacement_cannot_increase_exploitability(self) -> None:
        result = solve_sum_margin_with_generation(
            self.blueprint.game,
            self.blueprint.policy,
            (),
            resolver_player=0,
        )
        evaluation = evaluate_profile(self.blueprint.game, result.policy)
        assert evaluation.exploitability is not None
        assert self.blueprint.evaluation.exploitability is not None

        self.assertLessEqual(
            evaluation.exploitability,
            self.blueprint.evaluation.exploitability + 1e-10,
        )

    def test_invalid_limits_and_tolerance_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_updates must be positive"):
            solve_sum_margin_with_generation(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                max_updates=0,
            )
        with self.assertRaisesRegex(ValueError, "max_pure_plans must be positive"):
            solve_sum_margin_with_generation(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                max_pure_plans=0,
            )
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            solve_sum_margin_with_generation(
                self.blueprint.game,
                self.blueprint.policy,
                (),
                resolver_player=0,
                tolerance=float("nan"),
            )


if __name__ == "__main__":
    unittest.main()
