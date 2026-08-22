from __future__ import annotations

import unittest

from pontius.h32_one_round_convex_master import (
    bounded_gap,
    corrected_one_round_reserve,
)


class H32OneRoundConvexMasterTests(unittest.TestCase):
    def test_corrected_reserve_charges_both_master_solves(self) -> None:
        result = corrected_one_round_reserve(
            {
                "one_round_complete_ledger_ms": 13467.6157,
                "fixed_before_cut_rounds_ms": 8452.3813,
                "complete_cut_round_ms": 5015.2344,
            },
            initial_master_reserve_ms=500.0,
        )
        self.assertAlmostEqual(result["corrected_one_round_ledger_ms"], 13967.6157)
        self.assertEqual(result["correction_ms"], 500.0)
        self.assertTrue(result["fits_15000_ms"])
        with self.assertRaisesRegex(ValueError, "arithmetic is inconsistent"):
            corrected_one_round_reserve(
                {
                    "one_round_complete_ledger_ms": 1.0,
                    "fixed_before_cut_rounds_ms": 2.0,
                    "complete_cut_round_ms": 3.0,
                },
                initial_master_reserve_ms=500.0,
            )

    def test_gap_orientation_is_upper_minus_lower(self) -> None:
        self.assertAlmostEqual(bounded_gap(5.0, 3.0, tolerance=1e-9), 2.0)
        self.assertEqual(bounded_gap(3.0, 3.0 + 1e-10, tolerance=1e-9), 0.0)
        with self.assertRaisesRegex(ArithmeticError, "exceeds incumbent"):
            bounded_gap(3.0, 3.1, tolerance=1e-9)


if __name__ == "__main__":
    unittest.main()
