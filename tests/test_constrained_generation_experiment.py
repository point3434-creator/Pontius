from __future__ import annotations

import unittest

from pontius.constrained_generation_experiment import (
    run_constrained_generation_experiment,
)
from pontius.leaf_experiment import prepare_blueprint


class ConstrainedGenerationExperimentTests(unittest.TestCase):
    def test_reports_anytime_updates_and_excludes_teacher_costs(self) -> None:
        result = run_constrained_generation_experiment(
            {
                "blueprint_iterations": 20,
                "max_updates": 3,
                "verify_generated_responses": False,
                "verify_realization_equivalence": False,
                "price_after_last_update": False,
            },
            environment={"test": True},
        )

        self.assertEqual(len(result["boundaries"]), 4)
        self.assertFalse(
            result["protocol"]["full_game_target_used_for_construction"]
        )
        self.assertFalse(
            result["protocol"]["exact_normal_form_used_for_construction"]
        )
        self.assertFalse(
            result["protocol"]["row_oracle_reverified_with_duplicate_traversal"]
        )
        self.assertFalse(
            result["protocol"]["mixture_realization_reverified_on_active_rows"]
        )
        for boundary in result["boundaries"]:
            self.assertEqual(boundary["updates_executed"], 3)
            self.assertGreater(boundary["exact_oracle_seconds_excluded"], 0.0)
            self.assertGreater(boundary["decision_compute_seconds"], 0.0)
            self.assertEqual(boundary["updates"][0]["update"], 1)
            self.assertFalse(boundary["updates"][-1]["pricing_performed"])

    def test_unknown_and_mismatched_configurations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown constrained-generation"):
            run_constrained_generation_experiment({"mystery": 1})
        with self.assertRaisesRegex(ValueError, "phase controls must be boolean"):
            run_constrained_generation_experiment(
                {"verify_generated_responses": "false"}
            )
        prepared = prepare_blueprint("kuhn2", "lcfr", 10)
        with self.assertRaisesRegex(ValueError, "does not match"):
            run_constrained_generation_experiment(
                {"blueprint_iterations": 20},
                prepared_blueprint=prepared,
            )


if __name__ == "__main__":
    unittest.main()
