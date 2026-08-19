from __future__ import annotations

import unittest

from pontius.safe_oracle_matrix import run_safe_oracle_matrix


class SafeOracleMatrixTests(unittest.TestCase):
    def test_compacts_runs_and_reports_paired_capture(self) -> None:
        result = run_safe_oracle_matrix(
            {
                "base": {
                    "blueprint_iterations": 20,
                },
                "axes": {
                    "blueprint_solver": ["lcfr"],
                },
                "store_full_runs": False,
            }
        )

        self.assertEqual(result["run_count"], 1)
        self.assertEqual(result["prepared_blueprints"], 1)
        self.assertNotIn("full_runs", result)
        self.assertEqual(result["paired_summary"]["sum_margin_beats_max_min"], 1)
        self.assertGreater(
            result["paired_summary"][
                "aggregate_sum_margin_fraction_of_hidden_improvement"
            ],
            0.9,
        )

    def test_invalid_matrix_is_rejected_before_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown safe-oracle"):
            run_safe_oracle_matrix(
                {
                    "base": {"mystery": 1},
                    "axes": {"blueprint_iterations": [20]},
                }
            )


if __name__ == "__main__":
    unittest.main()
