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

    def test_analysis_reads_labels_but_does_not_mutate_source(self) -> None:
        source = copy.deepcopy(self.artifact)
        analyze_river_trace(source, folds=2)
        self.assertEqual(source, self.artifact)

    def test_invalid_artifact_feature_and_folds_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not an exact river"):
            analyze_river_trace({"experiment_type": "other"})
        with self.assertRaisesRegex(ValueError, "unknown primary"):
            analyze_river_trace(self.artifact, primary_feature="oracle_future")
        with self.assertRaisesRegex(ValueError, "folds"):
            analyze_river_trace(self.artifact, folds=1)


if __name__ == "__main__":
    unittest.main()
