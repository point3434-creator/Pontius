from __future__ import annotations

import unittest

from pontius.exact_oracle_assessment import assess_exact_oracle_gains


class ExactOracleAssessmentTests(unittest.TestCase):
    def test_cap_and_epigraph_allowances_are_semantically_distinct(self) -> None:
        assessed = assess_exact_oracle_gains(
            (0.5 + 5e-10, 0.25),
            (0.5, 0.5),
            cap_allowance=2e-11,
            epigraph=(0.5, 0.25),
            epigraph_allowance=1e-9,
        )
        self.assertFalse(assessed.cap_feasible)
        self.assertTrue(assessed.epigraph_closed)
        self.assertEqual(assessed.epigraph_violating_players, ())

    def test_optional_epigraph_and_numerical_negative_gain(self) -> None:
        assessed = assess_exact_oracle_gains(
            (-1e-15, 0.1),
            (0.0, 0.2),
            cap_allowance=2e-11,
        )
        self.assertEqual(assessed.gains, (0.0, 0.1))
        self.assertTrue(assessed.cap_feasible)
        self.assertIsNone(assessed.epigraph_closed)
        self.assertIsNone(assessed.maximum_epigraph_violation)

    def test_malformed_axes_and_allowances_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "different player axes"):
            assess_exact_oracle_gains((0.1,), (0.1, 0.2), cap_allowance=0.0)
        with self.assertRaisesRegex(ValueError, "requires epigraph"):
            assess_exact_oracle_gains(
                (0.1,),
                (0.2,),
                cap_allowance=0.0,
                epigraph_allowance=1e-9,
            )
        with self.assertRaisesRegex(ValueError, "epigraph allowance"):
            assess_exact_oracle_gains(
                (0.1,),
                (0.2,),
                cap_allowance=0.0,
                epigraph=(0.1,),
            )


if __name__ == "__main__":
    unittest.main()
