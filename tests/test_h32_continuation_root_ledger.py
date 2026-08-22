import math
import unittest

from pontius.h32_continuation_root_ledger import derive_continuation_capacities


class ContinuationRootLedgerTests(unittest.TestCase):
    def test_worst_case_and_profiled_prefix_capacities_are_distinct(self) -> None:
        result = derive_continuation_capacities(
            (100.0, 200.0, 300.0),
            warm_step_ms=1000.0,
            street_budget_ms=2000.0,
            emission_reserve_ms=200.0,
            tier_c_reserve_ms=10.0,
        )
        self.assertEqual(result["available_candidate_ms"], 790.0)
        self.assertEqual(result["maximum_candidate_ms"], 300.0)
        self.assertEqual(result["worst_case_safe_k"], 2)
        self.assertEqual(result["profiled_cumulative_k"], 3)
        self.assertTrue(result["profiled_cumulative_library_limited"])
        self.assertTrue(
            result[
                "profiled_cumulative_is_development_capacity_not_live_deadline_guarantee"
            ]
        )

    def test_profiled_rule_stops_at_first_nonfitting_prefix_row(self) -> None:
        result = derive_continuation_capacities(
            (400.0, 400.0, 1.0),
            warm_step_ms=100.0,
            street_budget_ms=750.0,
            emission_reserve_ms=100.0,
            tier_c_reserve_ms=10.0,
        )
        self.assertEqual(result["available_candidate_ms"], 540.0)
        self.assertEqual(result["worst_case_safe_k"], 1)
        self.assertEqual(result["profiled_cumulative_k"], 1)
        self.assertEqual(len(result["prefix_rows"]), 2)
        self.assertFalse(result["prefix_rows"][-1]["fits"])

    def test_exhausted_budget_cannot_admit_zero_cost_rows(self) -> None:
        result = derive_continuation_capacities(
            (0.0, 0.0),
            warm_step_ms=100.0,
            street_budget_ms=100.0,
            emission_reserve_ms=1.0,
            tier_c_reserve_ms=0.0,
        )
        self.assertEqual(result["worst_case_safe_k"], 0)
        self.assertEqual(result["profiled_cumulative_k"], 0)

    def test_invalid_costs_and_ledger_inputs_fail_closed(self) -> None:
        common = {
            "warm_step_ms": 100.0,
            "street_budget_ms": 1000.0,
            "emission_reserve_ms": 100.0,
            "tier_c_reserve_ms": 10.0,
        }
        for costs in ((), (-1.0,), (math.inf,), (math.nan,)):
            with self.subTest(costs=costs), self.assertRaises(ValueError):
                derive_continuation_capacities(costs, **common)
        with self.assertRaises(ValueError):
            derive_continuation_capacities(
                (1.0,),
                **{**common, "warm_step_ms": math.nan},
            )
        with self.assertRaises(ValueError):
            derive_continuation_capacities(
                (1.0,),
                **{**common, "street_budget_ms": 0.0},
            )


if __name__ == "__main__":
    unittest.main()
