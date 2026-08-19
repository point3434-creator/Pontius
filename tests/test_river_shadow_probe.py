from __future__ import annotations

import unittest

from pontius.river_opportunity import run_river_opportunity_experiment
from pontius.river_shadow_probe import run_river_shadow_probe


class RiverShadowProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = run_river_opportunity_experiment(
            {
                "groups": 1,
                "seed": 5,
                "hands_per_player": 2,
                "families": ["balanced"],
                "included_splits": ["development"],
                "solvers": ["dcfr"],
                "checkpoints": [0, 1, 2, 4],
                "sequential_raise": True,
            }
        )

    def test_probe_reproduces_context_and_does_not_change_active_dcfr(self) -> None:
        result = run_river_shadow_probe(self.source)

        self.assertEqual(result["counts"]["contexts"], 1)
        self.assertEqual(result["counts"]["extra_shadow_tree_traversals"], 0)
        self.assertEqual(
            result["correctness"]["maximum_active_accumulator_difference"],
            0.0,
        )
        self.assertTrue(
            result["correctness"]["all_source_active_features_reproduced"]
        )
        self.assertFalse(
            result["correctness"]["standalone_cfr_plus_equivalence_claimed"]
        )
        row = result["records"][0]
        self.assertGreater(
            row["online_features"][
                "shadow_cfr_plus_normalized_positive_regret_mass"
            ],
            0.0,
        )
        self.assertGreaterEqual(
            row["timing"][
                "conservative_instrumentation_overhead_milliseconds"
            ],
            row["timing"]["charged_feature_summary_milliseconds"],
        )

    def test_probe_rejects_nonsequential_or_nondevelopment_sources(self) -> None:
        nonsequential = {**self.source, "config": dict(self.source["config"])}
        nonsequential["config"]["sequential_raise"] = False
        with self.assertRaisesRegex(ValueError, "sequential"):
            run_river_shadow_probe(nonsequential)

        reserved = {**self.source, "config": dict(self.source["config"])}
        reserved["config"]["included_splits"] = ["validation"]
        with self.assertRaisesRegex(ValueError, "development"):
            run_river_shadow_probe(reserved)


if __name__ == "__main__":
    unittest.main()
