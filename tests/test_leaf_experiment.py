from __future__ import annotations

import unittest

from pontius.leaf_experiment import run_leaf_experiment


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

        self.assertEqual(result["experiment_type"], "paired_leaf_error")
        self.assertEqual(
            result["leaf_protocol"]["cache_mode"],
            "precomputed_before_search",
        )
        self.assertEqual(result["leaf_error"]["leaf_states"], 12)
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


if __name__ == "__main__":
    unittest.main()
