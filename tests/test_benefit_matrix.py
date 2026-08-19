from __future__ import annotations

import unittest

from pontius.benefit_matrix import run_benefit_matrix


class BenefitMatrixTests(unittest.TestCase):
    def test_matrix_caches_blueprints_and_reports_signal_diagnostics(self) -> None:
        result = run_benefit_matrix(
            {
                "base": {
                    "probe_iterations": 1,
                    "search_iterations": 2,
                },
                "axes": {
                    "blueprint_iterations": [3, 4],
                    "depth_limit": [1, 2],
                },
                "max_runs": 4,
            }
        )

        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["run_count"], 4)
        self.assertEqual(result["prepared_blueprints"], 2)
        diagnostics = result["signal_diagnostics"]
        self.assertEqual(diagnostics["cases"], 4)
        self.assertIn(
            "probe_local_nash_conv_improvement",
            diagnostics["signals"],
        )
        self.assertTrue(
            all(
                run["targets"]["max_model_full_utility_mismatch"] < 1e-12
                for run in result["runs"]
            )
        )

    def test_invalid_matrix_is_rejected_before_running(self) -> None:
        with self.assertRaises(ValueError):
            run_benefit_matrix({"axes": {}})
        with self.assertRaises(ValueError):
            run_benefit_matrix({"axes": {"typo": [1]}})
        with self.assertRaises(ValueError):
            run_benefit_matrix(
                {
                    "axes": {"depth_limit": [1, 2]},
                    "max_runs": 1,
                }
            )


if __name__ == "__main__":
    unittest.main()
