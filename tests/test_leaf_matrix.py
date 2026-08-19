from __future__ import annotations

import unittest

from pontius.leaf_matrix import run_leaf_matrix


class LeafMatrixTests(unittest.TestCase):
    def test_matrix_expands_axes_and_aggregates_replicates(self) -> None:
        result = run_leaf_matrix(
            {
                "base": {
                    "game": "kuhn2",
                    "blueprint_iterations": 5,
                    "search_iterations": 2,
                    "depth_limit": 1,
                },
                "axes": {
                    "leaf_error_scale": [0.0, 0.1],
                    "leaf_error_seed": [0, 1],
                },
                "replicate_axes": ["leaf_error_seed"],
            }
        )

        self.assertEqual(result["schema_version"], 3)
        self.assertEqual(result["run_count"], 4)
        self.assertEqual(result["prepared_blueprints"], 1)
        self.assertEqual(len(result["runs"]), 4)
        self.assertEqual(len(result["summaries"]), 2)
        self.assertTrue(all(summary["replicates"] == 2 for summary in result["summaries"]))
        self.assertNotIn("full_runs", result)
        for summary in result["summaries"]:
            self.assertEqual(summary["metrics"]["leaf_rmse"]["count"], 2)
            self.assertEqual(summary["metrics"]["leaf_rmse"]["defined_count"], 2)

    def test_matrix_can_retain_full_runs(self) -> None:
        result = run_leaf_matrix(
            {
                "base": {
                    "blueprint_iterations": 2,
                    "search_iterations": 1,
                },
                "axes": {"leaf_error_seed": [0]},
                "store_full_runs": True,
            }
        )
        self.assertEqual(len(result["full_runs"]), 1)
        self.assertFalse(
            result["full_runs"][0]["timing"]["blueprint_prepared_in_run"]
        )

    def test_invalid_matrix_is_rejected_before_running(self) -> None:
        with self.assertRaises(ValueError):
            run_leaf_matrix({"axes": {}})
        with self.assertRaises(ValueError):
            run_leaf_matrix({"axes": {"typo": [1]}})
        with self.assertRaises(ValueError):
            run_leaf_matrix(
                {
                    "axes": {"leaf_error_seed": [0, 1]},
                    "max_runs": 1,
                }
            )


if __name__ == "__main__":
    unittest.main()
