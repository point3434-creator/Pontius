from __future__ import annotations

import copy
import unittest

from pontius.river_opportunity import run_river_opportunity_experiment
from pontius.river_trace_comparison import compare_river_traces


class RiverTraceComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = {
            "groups": 2,
            "seed": 31,
            "hands_per_player": 2,
            "families": ["balanced", "blocker_stress"],
            "solvers": ["cfr", "dcfr"],
            "checkpoints": [0, 1, 2, 4],
        }
        cls.baseline = run_river_opportunity_experiment(config)
        cls.target = run_river_opportunity_experiment(
            {**config, "sequential_raise": True}
        )

    def test_compares_exactly_paired_ranges_across_different_trees(self) -> None:
        result = compare_river_traces(self.baseline, self.target)

        self.assertEqual(result["status"], "paired_diagnostics_only")
        self.assertEqual(result["contexts"], 4)
        self.assertTrue(result["exact_context_pairing"])
        self.assertEqual(len(result["solver_correlations"]), 2)
        self.assertEqual(len(result["allocation_comparison"]), 2)
        for row in result["solver_correlations"]:
            self.assertIn("feature_rank_stability", row)
            self.assertIn("target_feature_vs_target_state_efficiency", row)

    def test_rejects_context_or_feature_mismatches(self) -> None:
        changed = copy.deepcopy(self.target)
        changed["contexts"][0]["bet_size"] += 1.0
        with self.assertRaisesRegex(ValueError, "changed cards, bet, or joint range"):
            compare_river_traces(self.baseline, changed)
        with self.assertRaisesRegex(ValueError, "feature"):
            compare_river_traces(
                self.baseline,
                self.target,
                feature="clairvoyance",
            )


if __name__ == "__main__":
    unittest.main()
