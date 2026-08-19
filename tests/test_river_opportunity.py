from __future__ import annotations

import unittest

from pontius.river_opportunity import (
    FORBIDDEN_ONLINE_FEATURE_FRAGMENTS,
    _pooled_iteration_oracle,
    run_river_opportunity_experiment,
)


class RiverOpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "families": ["balanced"],
                "solvers": ["cfr", "lcfr"],
                "checkpoints": [0, 1, 2, 4],
            }
        )

    def test_builds_grouped_exact_traces_with_causal_features(self) -> None:
        self.assertEqual(self.result["status"], "measurement_only_no_scheduler_fit")
        self.assertEqual(
            self.result["counts"],
            {
                "groups": 1,
                "contexts": 1,
                "solver_runs": 2,
                "trace_records": 8,
            },
        )
        for record in self.result["records"]:
            for name in record["online_features"]:
                self.assertFalse(
                    any(
                        fragment in name
                        for fragment in FORBIDDEN_ONLINE_FEATURE_FRAGMENTS
                    ),
                    name,
                )
            self.assertIn("exploitability", record["labels"])
            self.assertIn("future_best_additional_reduction", record["labels"])

    def test_future_labels_are_computed_from_later_checkpoints_only(self) -> None:
        rows = [row for row in self.result["records"] if row["solver"] == "cfr"]
        first = rows[0]
        second = rows[1]
        expected_next_reduction = (
            first["labels"]["exploitability"]
            - second["labels"]["exploitability"]
        )
        self.assertAlmostEqual(
            first["labels"]["next_checkpoint_reduction"],
            expected_next_reduction,
        )
        self.assertEqual(rows[-1]["labels"]["future_best_additional_reduction"], 0.0)
        self.assertIsNone(rows[-1]["labels"]["first_future_improvement_checkpoint"])

    def test_exact_teacher_is_independent_of_solver_trace(self) -> None:
        context = self.result["contexts"][0]
        self.assertLessEqual(context["oracle_labels"]["nash_conv"], 1e-8)
        self.assertLessEqual(context["oracle_labels"]["duality_gap"], 1e-8)
        self.assertNotIn("policy", context["oracle_labels"])
        self.assertEqual(len(self.result["summary"]), 8)

    def test_pooled_oracle_can_move_an_easy_context_budget(self) -> None:
        def row(checkpoint: int, exploitability: float) -> dict:
            return {
                "checkpoint": checkpoint,
                "labels": {"exploitability": exploitability},
            }

        easy = [row(0, 10.0), row(2, 9.0), row(4, 9.0)]
        hard = [row(0, 10.0), row(2, 10.0), row(4, 0.0)]

        result = _pooled_iteration_oracle([easy, hard], average_budget=2)

        self.assertEqual(result["fixed_checkpoint_total_reduction"], 1.0)
        self.assertEqual(result["independent_hard_cap_oracle_total_reduction"], 1.0)
        self.assertEqual(result["pooled_perfect_information_total_reduction"], 10.0)
        self.assertEqual(result["pooled_selection_counts"], {"0": 1, "4": 1})

    def test_invalid_solver_and_checkpoint_configs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported solvers"):
            run_river_opportunity_experiment(
                {"groups": 1, "solvers": ["magic"], "checkpoints": [0]}
            )
        with self.assertRaisesRegex(ValueError, "checkpoints"):
            run_river_opportunity_experiment(
                {"groups": 1, "solvers": ["cfr"], "checkpoints": [1, 2]}
            )


if __name__ == "__main__":
    unittest.main()
