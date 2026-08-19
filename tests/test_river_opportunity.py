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
        self.assertEqual(self.result["schema_version"], 2)
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
        self.assertGreater(
            first["labels"][
                "best_future_normalized_reduction_per_thousand_state_visits"
            ],
            0.0,
        )
        self.assertGreater(
            first["labels"][
                "best_future_normalized_reduction_per_solver_millisecond"
            ],
            0.0,
        )
        self.assertEqual(
            rows[-1]["labels"][
                "best_future_normalized_reduction_per_thousand_state_visits"
            ],
            0.0,
        )
        self.assertIsNone(
            rows[-1]["labels"]["next_checkpoint_additional_state_visits"]
        )

    def test_exact_teacher_is_independent_of_solver_trace(self) -> None:
        context = self.result["contexts"][0]
        self.assertLessEqual(context["oracle_labels"]["nash_conv"], 1e-8)
        self.assertLessEqual(context["oracle_labels"]["duality_gap"], 1e-8)
        self.assertNotIn("policy", context["oracle_labels"])
        self.assertEqual(len(self.result["summary"]), 8)

    def test_sequential_trace_counts_the_larger_tree_and_keeps_local_regret_a_label(
        self,
    ) -> None:
        result = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "hands_per_player": 2,
                "families": ["balanced"],
                "solvers": ["cfr"],
                "checkpoints": [0, 1, 2],
                "sequential_raise": True,
            }
        )

        context = result["contexts"][0]
        expected_states = 1 + 8 * len(context["joint_range"])
        self.assertTrue(result["config"]["sequential_raise"])
        self.assertIsNotNone(context["raise_to"])
        for record in result["records"]:
            self.assertEqual(
                record["online_features"]["tree_states_per_full_traversal"],
                expected_states,
            )
            self.assertNotIn(
                "local_one_step_positive_regret",
                record["online_features"],
            )
            self.assertIn(
                "local_one_step_positive_regret",
                record["labels"],
            )
            self.assertIn(
                "best_future_normalized_reduction_per_thousand_state_visits",
                record["labels"],
            )
        self.assertTrue(
            any(
                abs(
                    record["labels"]["local_one_step_positive_regret"]
                    - record["labels"]["nash_conv"]
                )
                > 1e-10
                for record in result["records"]
            )
        )

    def test_trace_records_configured_shadow_regret_as_an_online_feature(self) -> None:
        result = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "hands_per_player": 2,
                "families": ["balanced"],
                "solvers": ["dcfr"],
                "shadow_regret_variants": {"dcfr": ["cfr_plus"]},
                "checkpoints": [0, 1, 2],
                "sequential_raise": True,
            }
        )

        self.assertEqual(
            result["config"]["shadow_regret_variants"],
            {"dcfr": ["cfr_plus"]},
        )
        checkpoint_two = next(
            record for record in result["records"] if record["checkpoint"] == 2
        )
        features = checkpoint_two["online_features"]
        self.assertGreater(
            features["shadow_cfr_plus_normalized_positive_regret_mass"],
            0.0,
        )
        self.assertGreater(
            features["shadow_cfr_plus_materialized_information_sets"],
            0,
        )

    def test_trace_can_charge_a_minimal_active_regret_summary(self) -> None:
        result = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "hands_per_player": 2,
                "families": ["balanced"],
                "solvers": ["dcfr"],
                "checkpoints": [0, 1, 2],
                "sequential_raise": True,
                "measure_active_regret_summary_cost": True,
            }
        )

        self.assertTrue(result["config"]["measure_active_regret_summary_cost"])
        self.assertGreaterEqual(
            result["timing"]["active_regret_summary_seconds"],
            0.0,
        )
        for record in result["records"]:
            self.assertGreaterEqual(
                record["online_features"][
                    "active_regret_summary_milliseconds"
                ],
                0.0,
            )

    def test_active_regret_cost_flag_must_be_boolean(self) -> None:
        with self.assertRaisesRegex(TypeError, "measure_active"):
            run_river_opportunity_experiment(
                {"groups": 1, "measure_active_regret_summary_cost": "yes"}
            )

    def test_trace_rejects_invalid_shadow_regret_configuration(self) -> None:
        base = {
            "groups": 1,
            "seed": 5,
            "families": ["balanced"],
            "solvers": ["dcfr"],
            "checkpoints": [0, 1, 2],
        }
        with self.assertRaises(ValueError):
            run_river_opportunity_experiment(
                {**base, "shadow_regret_variants": {"cfr": ["cfr_plus"]}}
            )
        with self.assertRaises(ValueError):
            run_river_opportunity_experiment(
                {**base, "shadow_regret_variants": {"dcfr": ["dcfr"]}}
            )
        with self.assertRaises(TypeError):
            run_river_opportunity_experiment(
                {**base, "shadow_regret_variants": {"dcfr": "cfr_plus"}}
            )

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

    def test_post_probe_oracle_charges_every_context_for_feature_acquisition(
        self,
    ) -> None:
        def row(checkpoint: int, exploitability: float) -> dict:
            return {
                "checkpoint": checkpoint,
                "labels": {"exploitability": exploitability},
            }

        easy = [row(0, 10.0), row(2, 9.0), row(4, 9.0)]
        hard = [row(0, 10.0), row(2, 10.0), row(4, 0.0)]

        result = _pooled_iteration_oracle(
            [easy, hard],
            average_budget=3,
            minimum_checkpoint=2,
        )

        self.assertEqual(result["minimum_checkpoint"], 2)
        self.assertEqual(result["aggregate_iteration_budget"], 6)
        self.assertEqual(result["aggregate_additional_iteration_budget"], 2)
        self.assertEqual(result["fixed_checkpoint"], 2)
        self.assertEqual(result["fixed_checkpoint_total_reduction"], 1.0)
        self.assertEqual(result["pooled_perfect_information_total_reduction"], 11.0)
        self.assertEqual(result["pooled_selection_counts"], {"2": 1, "4": 1})
        with self.assertRaisesRegex(ValueError, "minimum checkpoint"):
            _pooled_iteration_oracle(
                [easy, hard],
                average_budget=1,
                minimum_checkpoint=2,
            )

    def test_invalid_solver_and_checkpoint_configs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported solvers"):
            run_river_opportunity_experiment(
                {"groups": 1, "solvers": ["magic"], "checkpoints": [0]}
            )
        with self.assertRaisesRegex(ValueError, "checkpoints"):
            run_river_opportunity_experiment(
                {"groups": 1, "solvers": ["cfr"], "checkpoints": [1, 2]}
            )
        with self.assertRaisesRegex(TypeError, "boolean"):
            run_river_opportunity_experiment(
                {"groups": 1, "sequential_raise": "yes"}
            )
        with self.assertRaisesRegex(ValueError, "at most five"):
            run_river_opportunity_experiment(
                {
                    "groups": 1,
                    "hands_per_player": 6,
                    "sequential_raise": True,
                }
            )


if __name__ == "__main__":
    unittest.main()
