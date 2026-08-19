from __future__ import annotations

import unittest

from pontius.safe_composition_matrix import run_safe_composition_matrix


class SafeCompositionMatrixTests(unittest.TestCase):
    def test_matrix_caches_blueprints_and_aggregates_certificates(self) -> None:
        result = run_safe_composition_matrix(
            {
                "base": {
                    "blueprint_iterations": 10,
                    "search_iterations": 5,
                },
                "axes": {"search_solver": ["lcfr", "cfr_plus"]},
            }
        )

        self.assertEqual(result["run_count"], 2)
        self.assertEqual(result["prepared_blueprints"], 1)
        self.assertEqual(result["single_boundary_summary"]["cases"], 8)
        self.assertEqual(result["single_boundary_summary"]["bound_failures"], 0)
        self.assertEqual(
            result["architecture_summary"]["safe_continual"][
                "residual_adjusted_bound_failures"
            ],
            0,
        )

    def test_invalid_matrix_is_rejected_before_running(self) -> None:
        with self.assertRaisesRegex(ValueError, "axes cannot be empty"):
            run_safe_composition_matrix({"axes": {}})
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_safe_composition_matrix({"axes": {"mystery": [1]}})


if __name__ == "__main__":
    unittest.main()
