from __future__ import annotations

import unittest

from pontius.river_incremental_experiment import run_river_incremental_experiment


class RiverIncrementalExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = {
            "groups": 4,
            "seed": 5,
            "hands_per_player": 3,
            "families": ["balanced"],
            "included_splits": ["development"],
            "sequential_raise": True,
            "perturbations": [
                {
                    "name": "reweight_p0",
                    "kind": "blocker_reweight",
                    "player": 0,
                    "root_tv_budget": 0.01,
                    "maximum_donor_fraction": 0.75,
                },
                {
                    "name": "swap_p1",
                    "kind": "support_swap",
                    "player": 1,
                },
            ],
            "solver": "dcfr",
            "source_policy_checkpoints": [1, 2],
            "normalized_exploitability_thresholds": [0.01, 0.02],
            "timing": {
                "batches": 1,
                "cache_inner_repetitions": 1,
                "delta_inner_repetitions": 1,
                "full_inner_repetitions": 1,
                "incremental_inner_repetitions": 1,
                "bound_inner_repetitions": 1,
            },
            "gates": {
                "maximum_absolute_evaluation_error": 1e-10,
                "minimum_aggregate_hot_speedup": 0.0,
                "minimum_shared_delta_speedup": 0.0,
                "minimum_fraction_incremental_faster": 0.0,
            },
        }
        cls.result = run_river_incremental_experiment(cls.config)

    def test_finite_policy_exactness_and_cost_boundaries_are_reported(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "finite_policy_exact_delta_river_recertification",
        )
        self.assertTrue(self.result["gates"]["results"]["exact_identity"])
        self.assertTrue(self.result["gates"]["passed"])
        self.assertGreater(self.result["counts"]["source_contexts"], 0)
        self.assertEqual(
            self.result["counts"]["recertification_records"],
            self.result["counts"]["range_pairs"] * 2,
        )
        for record in self.result["records"]:
            self.assertTrue(record["source_policy_is_finite_dcfr"])
            self.assertLessEqual(record["maximum_absolute_evaluation_error"], 1e-10)
            self.assertGreaterEqual(
                record["incremental_recertification_timing"]["median_milliseconds"],
                0.0,
            )
            self.assertGreaterEqual(
                record["full_recertification_timing"]["median_milliseconds"],
                0.0,
            )

    def test_support_swap_stays_sparse_and_compiles_unseen_deal(self) -> None:
        support_pairs = [
            pair
            for pair in self.result["pairs"]
            if pair["perturbation"]["kind"] == "support_swap"
        ]
        self.assertTrue(support_pairs)
        for pair in support_pairs:
            self.assertEqual(pair["changed_deals"], 2)
            self.assertEqual(pair["added_deals"], 1)
            self.assertEqual(pair["removed_deals"], 1)
            self.assertEqual(pair["reweighted_deals"], 0)
            self.assertTrue(pair["metadata"]["new_private_hand_was_absent"])
        for record in self.result["records"]:
            if record["perturbation_kind"] == "support_swap":
                self.assertEqual(record["diagnostics"]["newly_compiled_deals"], 1)

    def test_tv_bound_never_false_accepts_in_exact_cross_check(self) -> None:
        self.assertTrue(
            all(
                row["bound_false_positives"] == 0
                for row in self.result["tv_certificate_summary"]
            )
        )

    def test_reserved_splits_missing_axis_and_unknown_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "development-only"):
            run_river_incremental_experiment(
                {**self.config, "included_splits": ["validation"]}
            )
        with self.assertRaisesRegex(ValueError, "both reweight and support-swap"):
            run_river_incremental_experiment(
                {**self.config, "perturbations": [self.config["perturbations"][0]]}
            )
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_river_incremental_experiment({**self.config, "future_label": 1})


if __name__ == "__main__":
    unittest.main()
