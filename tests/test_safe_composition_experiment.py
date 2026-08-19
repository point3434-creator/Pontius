from __future__ import annotations

import unittest

from pontius.leaf_experiment import prepare_blueprint
from pontius.safe_composition_experiment import run_safe_composition_experiment


class SafeCompositionExperimentTests(unittest.TestCase):
    def test_reports_target_blind_single_and_continual_certificates(self) -> None:
        result = run_safe_composition_experiment(
            {
                "blueprint_iterations": 20,
                "search_iterations": 20,
            },
            environment={"test": True},
        )

        self.assertTrue(
            result["protocol"]["full_game_target_never_enters_policy_construction"]
        )
        self.assertEqual(len(result["single_boundary"]["records"]), 4)
        self.assertTrue(
            all(
                record["candidate"]["residual_adjusted_bound_holds"]
                for record in result["single_boundary"]["records"]
            )
        )
        self.assertTrue(
            result["safe_continual"]["candidate"][
                "residual_adjusted_bound_holds"
            ]
        )
        self.assertTrue(
            result["strict_safe_continual"]["candidate"][
                "residual_adjusted_bound_holds"
            ]
        )
        self.assertIsNone(
            result["global_control"]["candidate"][
                "residual_adjusted_bound_holds"
            ]
        )

    def test_strict_zero_residual_gate_cannot_worsen_beyond_tolerance(self) -> None:
        result = run_safe_composition_experiment(
            {
                "blueprint_iterations": 20,
                "search_iterations": 5,
                "strict_frontier_tolerance": 0.0,
            },
            environment={"test": True},
        )

        self.assertGreaterEqual(
            result["strict_safe_continual"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ],
            -2e-10,
        )

    def test_invalid_and_mismatched_configurations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires kuhn2"):
            run_safe_composition_experiment({"game": "kuhn3"})
        prepared = prepare_blueprint("kuhn2", "lcfr", 10)
        with self.assertRaisesRegex(ValueError, "does not match"):
            run_safe_composition_experiment(
                {"blueprint_iterations": 20},
                prepared_blueprint=prepared,
            )


if __name__ == "__main__":
    unittest.main()
