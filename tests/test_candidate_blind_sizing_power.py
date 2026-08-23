from __future__ import annotations

import unittest

from pontius.reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ProbabilitySimplexAllowance,
    solve_bounded_normal_form_sizing_teacher,
    solve_reduced_river_sizing,
)
from pontius.sizing_power_diagnostic import (
    ChipClassificationGuard,
    NormalizedSizingOpportunityFloor,
    QualificationStopReason,
    build_adr0295_sizing_power_pool,
    run_candidate_blind_sizing_power_qualification,
)


class CandidateBlindSizingPowerDiagnosticTests(unittest.TestCase):
    def test_second_replication_rejects_candidate_blind_power_diagnostic(self) -> None:
        probability_allowance = ProbabilitySimplexAllowance(1e-9)
        chip_allowance = ChipObjectiveAllowance(1e-9)
        opportunity_floor = NormalizedSizingOpportunityFloor(1e-4)
        classification_guard = ChipClassificationGuard(1e-8)
        first_pool = build_adr0295_sizing_power_pool(batch_index=0)
        first = run_candidate_blind_sizing_power_qualification(
            pool=first_pool,
            opportunity_floor=opportunity_floor,
            classification_guard=classification_guard,
            probability_allowance=probability_allowance,
            chip_allowance=chip_allowance,
        )
        self.assertIs(first.stop_reason, QualificationStopReason.TARGET_REACHED)
        self.assertEqual(first.opened_context_count, 40)
        self.assertEqual(
            first.qualified_indices,
            (8, 11, 13, 15, 16, 21, 22, 23, 26, 28, 33, 39),
        )
        self.assertEqual(
            first.digest,
            "7f4d9e6df70e489bbc5325f1fbf87a4d6ba071c14389be961d68fd96524ddd17",
        )
        selected = tuple(first_pool.contexts[index] for index in first.qualified_indices)
        self.assertGreaterEqual(len({context.pot for context in selected}), 3)
        self.assertGreaterEqual(len({context.stack for context in selected}), 3)
        self.assertGreaterEqual(len({context.showdown_signs for context in selected}), 6)
        panel = first.qualified_panel(pool=first_pool)
        self.assertEqual(
            panel.digest,
            "e40102cfaeff0a682be78b6628bd415d2c43daacf9a37e65434a1fba9fa8b4ce",
        )
        for context in selected:
            bounded = context.bounded_two_by_two()
            sizes = (bounded.minimum_bet, bounded.stack)
            compact = solve_reduced_river_sizing(
                bounded,
                sizes,
                probability_allowance=probability_allowance,
                chip_allowance=chip_allowance,
            )
            teacher = solve_bounded_normal_form_sizing_teacher(bounded, sizes)
            self.assertAlmostEqual(compact.value_chips, teacher.value_chips, delta=1e-9)
            self.assertLessEqual(teacher.duality_gap, 1e-9)

        second_pool = build_adr0295_sizing_power_pool(batch_index=1)
        second = run_candidate_blind_sizing_power_qualification(
            pool=second_pool,
            opportunity_floor=opportunity_floor,
            classification_guard=classification_guard,
            probability_allowance=probability_allowance,
            chip_allowance=chip_allowance,
        )
        self.assertIs(second.stop_reason, QualificationStopReason.POOL_EXHAUSTED)
        self.assertEqual(second.opened_context_count, 96)
        self.assertEqual(
            second.qualified_indices,
            (5, 13, 39, 44, 46, 47, 63, 69, 71, 74, 92),
        )
        self.assertEqual(
            second.digest,
            "7574ba9fc1adaf4c3d8546514179630499633bbc07289d1af505917d4b4c05f5",
        )
        with self.assertRaisesRegex(ValueError, "target-reached"):
            second.qualified_panel(pool=second_pool)
        self.assertFalse(len(second.qualified_indices) >= 12)


if __name__ == "__main__":
    unittest.main()
