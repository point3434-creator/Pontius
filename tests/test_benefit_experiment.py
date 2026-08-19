from __future__ import annotations

import unittest

from pontius.benefit_experiment import run_benefit_experiment
from pontius.leaf_experiment import prepare_blueprint


class BenefitExperimentTests(unittest.TestCase):
    def test_signals_use_model_and_target_uses_full_game(self) -> None:
        result = run_benefit_experiment(
            {
                "blueprint_iterations": 10,
                "probe_iterations": 2,
                "search_iterations": 4,
                "depth_limit": 2,
            }
        )

        self.assertEqual(result["schema_version"], 1)
        self.assertTrue(
            result["protocol"][
                "full_game_target_never_enters_signal_calculation"
            ]
        )
        self.assertEqual(result["model"]["information_sets"], 9)
        self.assertAlmostEqual(
            result["targets"]["max_model_full_utility_mismatch"],
            0.0,
        )
        self.assertGreater(result["timing"]["probe_search_seconds"], 0.0)
        self.assertGreater(result["timing"]["full_search_seconds"], 0.0)
        self.assertIn(
            "probe_local_nash_conv_improvement",
            result["signals"],
        )
        self.assertIn(
            "full_game_nash_conv_improvement",
            result["targets"],
        )
        self.assertIn(
            "full_local_improvement_per_mean_policy_tv",
            result["signals"],
        )

    def test_prepared_blueprint_must_match(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 5)
        result = run_benefit_experiment(
            {
                "blueprint_iterations": 5,
                "probe_iterations": 1,
                "search_iterations": 2,
            },
            prepared_blueprint=prepared,
        )
        self.assertFalse(result["timing"]["blueprint_prepared_in_run"])

        with self.assertRaises(ValueError):
            run_benefit_experiment(
                {
                    "blueprint_iterations": 6,
                    "probe_iterations": 1,
                    "search_iterations": 2,
                },
                prepared_blueprint=prepared,
            )

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_benefit_experiment({"probe_iterations": 0})
        with self.assertRaises(ValueError):
            run_benefit_experiment({"in_search_blueprint_weight": 1.1})
        with self.assertRaises(ValueError):
            run_benefit_experiment({"search_solver": "imaginary"})


if __name__ == "__main__":
    unittest.main()
