from __future__ import annotations

import unittest

from pontius.h32_cross_payoff_adjoint_feasibility import (
    reverse_adjoint_feasibility_decision,
)


class H32CrossPayoffAdjointFeasibilityTests(unittest.TestCase):
    def test_complete_ledger_prices_every_reserved_stage(self) -> None:
        result = reverse_adjoint_feasibility_decision(
            warm_step_ms=1000.0,
            cross_matrix_ms=9000.0,
            street_budget_ms=15000.0,
            certificate_reserve_ms=1250.0,
            envelope_reserve_ms=10.0,
            optimizer_reserve_ms=10.0,
            emission_reserve_ms=1000.0,
        )
        self.assertEqual(result["complete_generated_direction_ledger_ms"], 12270.0)
        self.assertEqual(result["headroom_ms"], 2730.0)
        self.assertTrue(result["fits_street"])

    def test_over_budget_result_fails_without_changing_validity(self) -> None:
        result = reverse_adjoint_feasibility_decision(
            warm_step_ms=1500.0,
            cross_matrix_ms=13000.0,
            street_budget_ms=15000.0,
            certificate_reserve_ms=1250.0,
            envelope_reserve_ms=10.0,
            optimizer_reserve_ms=10.0,
            emission_reserve_ms=1000.0,
        )
        self.assertFalse(result["fits_street"])
        self.assertLess(result["headroom_ms"], 0.0)

    def test_invalid_time_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite and nonnegative"):
            reverse_adjoint_feasibility_decision(
                warm_step_ms=-1.0,
                cross_matrix_ms=1.0,
                street_budget_ms=15000.0,
                certificate_reserve_ms=1250.0,
                envelope_reserve_ms=10.0,
                optimizer_reserve_ms=10.0,
                emission_reserve_ms=1000.0,
            )


if __name__ == "__main__":
    unittest.main()
