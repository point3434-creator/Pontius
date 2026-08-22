import math
import unittest

from pontius.h32_continuation_root_strategy_trial import (
    may_start_continuation_candidate,
    select_full_affine_winner,
)


def _row(index: int, value: float, *, complete: bool = True) -> dict[str, object]:
    return {
        "candidate_id": f"candidate_{index}",
        "schedule_index": index,
        "envelope": {
            "complete": complete,
            "selected_scale": 0.5 if complete else None,
            "positive_certified_value": value,
        },
    }


class ContinuationRootStrategyTrialTests(unittest.TestCase):
    def test_candidate_guard_reserves_tail_and_accepts_boundary(self) -> None:
        common = {
            "prior_maximum_candidate_ms": 1000.0,
            "decision_budget_ms": 15000.0,
            "emission_reserve_ms": 1000.0,
            "certificate_start_reserve_ms": 1250.0,
            "envelope_reserve_ms": 10.0,
        }
        self.assertTrue(
            may_start_continuation_candidate(elapsed_ms=11740.0, **common)
        )
        self.assertFalse(
            may_start_continuation_candidate(elapsed_ms=11740.000001, **common)
        )

    def test_candidate_guard_rejects_invalid_inputs(self) -> None:
        common = {
            "elapsed_ms": 0.0,
            "prior_maximum_candidate_ms": 1.0,
            "decision_budget_ms": 15000.0,
            "emission_reserve_ms": 1000.0,
            "certificate_start_reserve_ms": 1250.0,
            "envelope_reserve_ms": 10.0,
        }
        for field, value in (
            ("elapsed_ms", -1.0),
            ("prior_maximum_candidate_ms", math.inf),
            ("certificate_start_reserve_ms", math.nan),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                may_start_continuation_candidate(**{**common, field: value})
        with self.assertRaises(ValueError):
            may_start_continuation_candidate(
                **{**common, "decision_budget_ms": 1000.0, "emission_reserve_ms": 1000.0}
            )

    def test_full_affine_winner_uses_value_then_structural_tie_break(self) -> None:
        winner = select_full_affine_winner(
            (_row(3, 0.2), _row(1, 0.2), _row(0, 0.1))
        )
        self.assertIsNotNone(winner)
        self.assertEqual(winner["candidate_id"], "candidate_1")

    def test_full_affine_winner_abstains_without_positive_complete_row(self) -> None:
        self.assertIsNone(
            select_full_affine_winner((_row(0, 0.0), _row(1, 1.0, complete=False)))
        )


if __name__ == "__main__":
    unittest.main()
