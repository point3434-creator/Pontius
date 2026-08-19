from __future__ import annotations

import unittest

from pontius.leaf_experiment import prepare_blueprint
from pontius.safe_oracle_experiment import run_safe_oracle_experiment


class SafeOracleExperimentTests(unittest.TestCase):
    def test_reports_target_free_and_hidden_objectives_separately(self) -> None:
        result = run_safe_oracle_experiment(
            {
                "blueprint_iterations": 20,
            },
            environment={"test": True},
        )
        max_min = result["max_min"]
        summed = result["sum_margin"]
        hidden = result["hidden_best_response_greedy"]

        self.assertFalse(max_min["full_game_target_used"])
        self.assertFalse(summed["full_game_target_used"])
        self.assertTrue(hidden["full_game_target_used"])
        self.assertTrue(result["protocol"]["hidden_control_is_greedy_across_public_boundaries"])
        self.assertGreater(
            summed["candidate"]["nash_conv_improvement_over_blueprint"],
            max_min["candidate"]["nash_conv_improvement_over_blueprint"],
        )
        self.assertGreater(
            result["paired"]["sum_margin_fraction_of_hidden_improvement"],
            0.9,
        )
        for architecture in (max_min, summed, hidden):
            self.assertTrue(
                architecture["candidate"]["residual_adjusted_bound_holds"]
            )

    def test_invalid_and_mismatched_configurations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires kuhn2"):
            run_safe_oracle_experiment({"game": "kuhn3"})
        prepared = prepare_blueprint("kuhn2", "lcfr", 10)
        with self.assertRaisesRegex(ValueError, "does not match"):
            run_safe_oracle_experiment(
                {"blueprint_iterations": 20},
                prepared_blueprint=prepared,
            )


if __name__ == "__main__":
    unittest.main()
