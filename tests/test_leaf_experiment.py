from __future__ import annotations

import unittest

from pontius.leaf_experiment import prepare_blueprint, run_leaf_experiment


class LeafExperimentTests(unittest.TestCase):
    def test_zero_error_treatment_exactly_matches_paired_control(self) -> None:
        result = run_leaf_experiment(
            {
                "game": "kuhn2",
                "blueprint_solver": "lcfr",
                "blueprint_iterations": 20,
                "search_solver": "cfr_plus",
                "search_iterations": 10,
                "depth_limit": 1,
                "leaf_error_scale": 0.0,
                "leaf_error_seed": 8,
            }
        )

        self.assertEqual(result["schema_version"], 3)
        self.assertEqual(result["experiment_type"], "paired_leaf_error")
        self.assertEqual(
            result["leaf_protocol"]["cache_mode"],
            "precomputed_before_search",
        )
        self.assertEqual(result["leaf_error"]["leaf_states"], 12)
        self.assertIn("on_policy_root_l2", result["leaf_error_reach_weighted"])
        self.assertEqual(result["leaf_error"]["rmse"], 0.0)
        self.assertEqual(result["causal_effect"]["average"]["nash_conv_delta"], 0.0)
        self.assertEqual(
            result["causal_effect"]["average"][
                "mean_information_set_total_variation"
            ],
            0.0,
        )
        self.assertEqual(
            result["exact_control"]["average"]["policy"],
            result["perturbed"]["average"]["policy"],
        )

    def test_nonzero_error_records_full_game_effect_and_warm_start(self) -> None:
        result = run_leaf_experiment(
            {
                "game": "kuhn2",
                "blueprint_iterations": 20,
                "search_iterations": 10,
                "leaf_error_scale": 0.2,
                "leaf_error_seed": 3,
                "warm_start_regret_mass": 5.0,
            }
        )

        self.assertEqual(result["config"]["warm_start_regret_mass"], 5.0)
        self.assertGreater(result["leaf_error"]["rmse"], 0.0)
        self.assertIn("nash_conv", result["blueprint"])
        self.assertIn("nash_conv_delta", result["causal_effect"]["average"])
        self.assertGreaterEqual(
            result["causal_effect"]["average"][
                "mean_information_set_total_variation"
            ],
            0.0,
        )
        self.assertGreater(result["timing"]["exact_control_search_seconds"], 0.0)
        self.assertGreater(result["timing"]["exact_control_initialization_seconds"], 0.0)

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_leaf_experiment({"leaf_error_scale": -1.0})
        with self.assertRaises(ValueError):
            run_leaf_experiment({"warm_start_regret_mass": 0.0})
        with self.assertRaises(ValueError):
            run_leaf_experiment({"search_solver": "imaginary"})
        with self.assertRaises(ValueError):
            run_leaf_experiment({"in_search_blueprint_weight": 1.1})
        with self.assertRaises(ValueError):
            run_leaf_experiment({"output_candidate_weight": -0.1})
        with self.assertRaises(ValueError):
            run_leaf_experiment(
                {"leaf_error_target_on_policy_root_l2": 0.1}
            )
        with self.assertRaises(ValueError):
            run_leaf_experiment(
                {
                    "leaf_error_scale": 1.0,
                    "leaf_error_target_on_policy_root_l2": 0.1,
                    "leaf_error_bias": [0.1, -0.1],
                }
            )

    def test_zero_output_weight_is_explicit_no_op_despite_leaf_error(self) -> None:
        result = run_leaf_experiment(
            {
                "blueprint_iterations": 20,
                "search_iterations": 10,
                "leaf_error_scale": 0.5,
                "output_candidate_weight": 0.0,
            }
        )

        blueprint_nash_conv = result["blueprint"]["nash_conv"]
        self.assertEqual(
            result["exact_control"]["average"]["nash_conv"],
            blueprint_nash_conv,
        )
        self.assertEqual(
            result["perturbed"]["average"]["nash_conv"],
            blueprint_nash_conv,
        )
        self.assertEqual(
            result["causal_effect"]["average"][
                "mean_information_set_total_variation"
            ],
            0.0,
        )
        self.assertFalse(
            result["oracle_no_op_selection"]["perturbed_average"][
                "candidate_selected"
            ]
        )

    def test_full_in_search_anchor_returns_blueprint(self) -> None:
        result = run_leaf_experiment(
            {
                "blueprint_iterations": 20,
                "search_iterations": 10,
                "leaf_error_scale": 0.5,
                "in_search_blueprint_weight": 1.0,
            }
        )
        self.assertAlmostEqual(
            result["perturbed"]["average"]["nash_conv"],
            result["blueprint"]["nash_conv"],
        )
        self.assertEqual(
            result["strategy_protocol"][
                "maximum_unanchored_candidate_component"
            ],
            0.0,
        )
        self.assertAlmostEqual(
            result["perturbed"]["average"][
                "resolved_policy_distance_from_blueprint"
            ]["mean_information_set_total_variation"],
            0.0,
        )

    def test_prepared_blueprint_is_reused_and_must_match(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 5)
        result = run_leaf_experiment(
            {
                "game": "kuhn2",
                "blueprint_solver": "lcfr",
                "blueprint_iterations": 5,
                "search_iterations": 2,
            },
            prepared_blueprint=prepared,
        )
        self.assertFalse(result["timing"]["blueprint_prepared_in_run"])

        with self.assertRaises(ValueError):
            run_leaf_experiment(
                {
                    "game": "kuhn2",
                    "blueprint_solver": "lcfr",
                    "blueprint_iterations": 6,
                    "search_iterations": 2,
                },
                prepared_blueprint=prepared,
            )

    def test_structured_leaf_error_controls_are_recorded(self) -> None:
        result = run_leaf_experiment(
            {
                "blueprint_iterations": 10,
                "search_iterations": 2,
                "depth_limit": 1,
                "leaf_error_scale": 0.0,
                "leaf_error_grouping": "public_history",
                "leaf_error_scope": "public_actions",
                "leaf_error_scope_actions": ["check"],
                "leaf_error_bias": [0.1, -0.1],
            }
        )

        protocol = result["structured_error_protocol"]
        self.assertEqual(protocol["grouping"], "public_history")
        self.assertEqual(protocol["scope"], "public_actions")
        self.assertEqual(protocol["active_leaf_states"], 6)
        self.assertEqual(protocol["active_error_groups"], 1)
        self.assertEqual(
            protocol["effective_bias_after_zero_sum_projection"],
            [0.1, -0.1],
        )
        self.assertGreater(protocol["active_on_policy_reach_fraction"], 0.0)
        self.assertLess(protocol["active_on_policy_reach_fraction"], 1.0)
        self.assertEqual(result["leaf_error"]["active_leaf_states"], 6)
        self.assertEqual(result["leaf_error"]["nonzero_leaf_states"], 6)
        self.assertGreater(protocol["active_on_policy_reach_mass"], 0.0)

    def test_random_error_can_be_calibrated_to_root_l2(self) -> None:
        result = run_leaf_experiment(
            {
                "blueprint_iterations": 10,
                "search_iterations": 2,
                "depth_limit": 2,
                "leaf_error_scale": 1.0,
                "leaf_error_target_on_policy_root_l2": 0.02,
                "leaf_error_grouping": "public_history",
            }
        )

        self.assertAlmostEqual(
            result["leaf_error_reach_weighted"]["on_policy_root_l2"],
            0.02,
        )
        self.assertGreater(
            result["structured_error_protocol"]["effective_leaf_error_scale"],
            0.0,
        )
        self.assertEqual(
            result["config"]["leaf_error_target_on_policy_root_l2"],
            0.02,
        )


if __name__ == "__main__":
    unittest.main()
