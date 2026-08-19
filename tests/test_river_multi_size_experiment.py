from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from pontius.river_multi_size_experiment import run_multi_size_river_experiment


def _tape_sha256() -> str:
    path = Path(__file__).parents[1] / "src" / "pontius" / "dependency_tape.py"
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MultiSizeRiverExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = {
            "groups": 4,
            "seed": 5,
            "hands_per_player": 3,
            "families": ["balanced"],
            "included_splits": ["development"],
            "tree_shapes": ["fixed_single", "multi_size_3x2"],
            "baseline_bet_pot_fraction": 0.5,
            "baseline_raise_to_pot_fraction": 1.5,
            "bet_pot_fractions": [0.25, 0.5, 0.75],
            "raise_to_pot_fractions": [1.5, 2.0],
            "solver": "dcfr",
            "source_policy_checkpoints": [1, 2],
            "root_tv_budget": 0.01,
            "maximum_donor_fraction": 0.75,
            "factorized_likelihood_minimum": 0.5,
            "factorized_likelihood_maximum": 1.5,
            "dense_threshold": 0.35,
            "expected_dependency_tape_sha256": _tape_sha256(),
            "gates": {
                "maximum_absolute_evaluation_error": 1e-10,
                "maximum_best_response_action_value_loss": 1e-10,
                "maximum_payoff_audit_error": 0.0,
                "maximum_sparse_dirty_fraction": 1.0,
                "minimum_sparse_auto_fraction": 0.0,
                "minimum_dense_auto_fraction": 0.0,
            },
        }
        cls.result = run_multi_size_river_experiment(cls.config)

    def test_exactness_payoff_topology_and_unchanged_tape_gates_pass(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "multi_size_river_dependency_tape_transfer",
        )
        self.assertTrue(self.result["gates"]["passed"])
        self.assertTrue(all(self.result["gates"]["results"].values()))
        self.assertEqual(
            self.result["aggregate"]["maximum_best_response_action_value_loss"],
            0,
        )
        self.assertEqual(
            self.result["aggregate"]["maximum_payoff_audit_error"],
            0.0,
        )
        self.assertEqual(
            self.result["counts"]["target_records"],
            self.result["counts"]["source_policy_tapes"] * 5,
        )
        self.assertEqual(
            self.result["counts"]["payoff_audits"],
            self.result["counts"]["contexts"] * 6,
        )
        self.assertTrue(
            all(
                row["terminal_histories"] == row["expected_terminal_histories"]
                for row in self.result["payoff_audits"]
            )
        )

    def test_wide_topology_and_matched_dirty_transfer_are_reported(self) -> None:
        self.assertGreater(
            self.result["paired_transfer"]["mean_numeric_node_ratio"],
            1.0,
        )
        self.assertGreater(
            self.result["paired_transfer"]["mean_tree_state_ratio"],
            1.0,
        )
        self.assertEqual(
            {row["shape"] for row in self.result["summaries"]},
            {"fixed_single", "multi_size_3x2"},
        )
        self.assertEqual(
            {
                row["target_kind"]
                for row in self.result["paired_transfer"]["dirty_transfer"]
            },
            {"sparse_reweight", "sparse_support", "factorized_dense"},
        )
        fixed = [
            row for row in self.result["records"] if row["shape"] == "fixed_single"
        ]
        wide = [
            row for row in self.result["records"] if row["shape"] == "multi_size_3x2"
        ]
        self.assertTrue(all(row["specialized_evaluation_error"] is not None for row in fixed))
        self.assertTrue(all(row["specialized_evaluation_error"] is None for row in wide))

    def test_reserved_shape_hash_and_unknown_fields_cannot_pass_silently(self) -> None:
        with self.assertRaisesRegex(ValueError, "development-only"):
            run_multi_size_river_experiment(
                {**self.config, "included_splits": ["validation"]}
            )
        with self.assertRaisesRegex(ValueError, "tree_shapes"):
            run_multi_size_river_experiment(
                {**self.config, "tree_shapes": ["multi_size_3x2"]}
            )
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_multi_size_river_experiment({**self.config, "future_axis": 1})

        wrong_hash = run_multi_size_river_experiment(
            {**self.config, "expected_dependency_tape_sha256": "0" * 64}
        )
        self.assertFalse(
            wrong_hash["gates"]["results"]["dependency_tape_is_unchanged"]
        )
        self.assertFalse(wrong_hash["gates"]["passed"])


if __name__ == "__main__":
    unittest.main()
