from __future__ import annotations

import copy
import unittest

from pontius.river_opportunity import run_river_opportunity_experiment
from pontius.river_trace_analysis import analyze_river_trace


class RiverTraceAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = run_river_opportunity_experiment(
            {
                "groups": 2,
                "seed": 31,
                "families": ["balanced", "blocker_stress"],
                "solvers": ["cfr", "dcfr"],
                "checkpoints": [0, 1, 2, 4],
            }
        )

    def test_reports_unfitted_path_and_signal_diagnostics(self) -> None:
        result = analyze_river_trace(self.artifact, folds=2)

        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["status"], "unfitted_diagnostics_only")
        self.assertEqual(result["source_counts"]["contexts"], 4)
        self.assertEqual(len(result["solver_path_diagnostics"]), 2)
        self.assertEqual(len(result["primary_signal"]["by_solver"]), 2)
        for solver in result["solver_path_diagnostics"]:
            self.assertEqual(solver["runs"], 4)
            self.assertEqual(sum(solver["first_improvement_counts"].values()), 4)
        self.assertTrue(
            any("acts at most once" in warning for warning in result["interpretation_warnings"])
        )
        self.assertTrue(result["local_regret_vs_nash_conv"]["available"])
        self.assertEqual(result["local_regret_vs_nash_conv"]["nonidentity_records"], 0)

    def test_sequential_analysis_reports_that_local_regret_identity_is_broken(
        self,
    ) -> None:
        artifact = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "hands_per_player": 2,
                "families": ["balanced"],
                "solvers": ["cfr"],
                "checkpoints": [0, 1, 2, 4],
                "sequential_raise": True,
            }
        )

        result = analyze_river_trace(
            artifact,
            primary_checkpoint=1,
            primary_target="state_visit_efficiency",
            allocation_probe_checkpoint=2,
            folds=2,
        )

        self.assertTrue(
            any(
                "opener acts twice" in warning
                for warning in result["interpretation_warnings"]
            )
        )
        self.assertGreater(
            result["local_regret_vs_nash_conv"]["nonidentity_records"],
            0,
        )
        self.assertEqual(
            result["primary_signal"]["target"],
            "state_visit_efficiency",
        )
        self.assertTrue(
            result["post_probe_allocation_oracles"]["feature_acquisition_paid"]
        )
        self.assertEqual(
            result["post_probe_allocation_oracles"]["minimum_checkpoint"],
            2,
        )

    def test_analysis_reads_labels_but_does_not_mutate_source(self) -> None:
        source = copy.deepcopy(self.artifact)
        analyze_river_trace(source, folds=2)
        self.assertEqual(source, self.artifact)

    def test_analysis_remains_compatible_with_pre_diagnostic_artifacts(self) -> None:
        legacy = copy.deepcopy(self.artifact)
        legacy["config"].pop("sequential_raise")
        for record in legacy["records"]:
            record["online_features"].pop("payoff_span")
            record["labels"].pop("local_one_step_positive_regret")

        result = analyze_river_trace(legacy, folds=2)

        self.assertFalse(result["local_regret_vs_nash_conv"]["available"])
        self.assertTrue(
            any(
                "acts at most once" in warning
                for warning in result["interpretation_warnings"]
            )
        )

    def test_invalid_artifact_feature_and_folds_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not an exact river"):
            analyze_river_trace({"experiment_type": "other"})
        with self.assertRaisesRegex(ValueError, "unknown primary"):
            analyze_river_trace(self.artifact, primary_feature="oracle_future")
        with self.assertRaisesRegex(ValueError, "unknown primary target"):
            analyze_river_trace(self.artifact, primary_target="wishful_efficiency")
        with self.assertRaisesRegex(ValueError, "probe checkpoint"):
            analyze_river_trace(self.artifact, allocation_probe_checkpoint=3)
        with self.assertRaisesRegex(ValueError, "folds"):
            analyze_river_trace(self.artifact, folds=1)


if __name__ == "__main__":
    unittest.main()
