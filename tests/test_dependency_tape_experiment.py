from __future__ import annotations

import unittest

from pontius.dependency_tape_experiment import run_dependency_tape_experiment


class DependencyTapeExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = {
            "groups": 4,
            "seed": 5,
            "hands_per_player": 3,
            "families": ["balanced"],
            "included_splits": ["development"],
            "sequential_raise_shapes": [False, True],
            "solver": "dcfr",
            "source_policy_checkpoints": [1, 2],
            "root_tv_budget": 0.01,
            "maximum_donor_fraction": 0.75,
            "factorized_likelihood_minimum": 0.5,
            "factorized_likelihood_maximum": 1.5,
            "dense_threshold": 0.35,
            "gates": {
                "maximum_absolute_evaluation_error": 1e-10,
                "minimum_sparse_auto_fraction": 0.0,
                "minimum_dense_auto_fraction": 0.0,
            },
        }
        cls.result = run_dependency_tape_experiment(cls.config)

    def test_all_exactness_and_topology_gates_pass(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "generic_dependency_tape_differential_matrix",
        )
        self.assertTrue(self.result["gates"]["passed"])
        self.assertTrue(all(self.result["gates"]["results"].values()))
        self.assertLessEqual(
            self.result["aggregate"]["maximum_absolute_evaluation_error"],
            1e-10,
        )
        self.assertEqual(
            self.result["aggregate"]["best_response_action_mismatches"],
            0,
        )
        self.assertEqual(
            self.result["counts"]["target_records"],
            self.result["counts"]["source_policy_tapes"] * 5,
        )
        self.assertEqual(
            {row["sequential_raise"] for row in self.result["sources"]},
            {False, True},
        )

    def test_sparse_support_and_dense_likelihood_axes_are_auditable(self) -> None:
        support = [
            row
            for row in self.result["records"]
            if row["target_kind"] == "sparse_support"
        ]
        dense = [
            row
            for row in self.result["records"]
            if row["target_kind"] == "factorized_dense"
        ]
        self.assertTrue(support)
        self.assertTrue(dense)
        for row in support:
            self.assertEqual(row["changed_deals"], 2)
            self.assertTrue(row["target_metadata"]["new_private_hand_was_absent"])
            self.assertEqual(row["target_metadata"]["added_deals"], 1)
            self.assertEqual(row["target_metadata"]["removed_deals"], 1)
        for row in dense:
            self.assertTrue(row["target_metadata"]["support_preserved"])
            self.assertEqual(
                row["automatic_diagnostics"]["execution_mode"],
                "dense",
            )

    def test_reserved_split_tree_axis_and_unknown_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "development-only"):
            run_dependency_tape_experiment(
                {**self.config, "included_splits": ["validation"]}
            )
        with self.assertRaisesRegex(ValueError, "exactly"):
            run_dependency_tape_experiment(
                {**self.config, "sequential_raise_shapes": [True]}
            )
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_dependency_tape_experiment({**self.config, "future_axis": 1})


if __name__ == "__main__":
    unittest.main()
