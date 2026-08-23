from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import pontius.collision_repair_v3_evaluation as evaluation_module
from pontius.collision_repair_v3_evaluation import (
    ADR0300_AGGREGATE_RECOVERY_FLOOR,
    ADR0300_EVALUATION_CAMPAIGN_SHA256,
    ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT,
    ADR0300_MAXIMUM_V3_ACTIONS,
    ADR0300_MAXIMUM_V3_RAISES,
    ADR0300_MEAN_NORMALIZED_LOSS_LIMIT,
    ADR0300_QUALIFIED_RESULT_SHA256,
    ADR0300_REPRESENTATIVE_RESULT_SHA256,
    V3AggregateRecoveryFloor,
    V3ArmKind,
    V3CampaignStopReason,
    V3MaximumNormalizedLossLimit,
    V3MeanNormalizedLossLimit,
    V3OrderingAllowance,
    run_adr0300_collision_repair_v3_evaluation,
)
from pontius.fresh_collision_repair_qualification import (
    ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
    ADR0302_ENVELOPE_ALLOWANCE,
    ADR0302_LP_DUALITY_ALLOWANCE,
    ADR0302_PROBABILITY_ALLOWANCE,
    ADR0302_QUALIFIED_INDICES,
    ADR0302_SIMPLEX_PIVOT_CAP,
)
from pontius.fresh_collision_repair_structures import (
    ADR0301_REPRESENTATIVE_CONTEXT_COUNT,
    FreshStructureKind,
    build_adr0301_fresh_structure,
)

_ROOT = Path(__file__).parents[1]


def _round_half_up(value: Fraction) -> int:
    """Independently round a nonnegative exact rational, with ties upward."""

    if value < 0:
        raise ValueError("manual sizing formula requires a nonnegative value")
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + int(2 * remainder >= value.denominator)


def _manual_v3_sizes(*, pot: int, stack: int, minimum_bet: int) -> tuple[tuple[int, ...], bool]:
    """Reconstruct ADR-0300 without importing production sizing helpers."""

    def projected(raw: int) -> int:
        return min(stack, max(minimum_bet, raw))

    primary = projected(2 * pot)
    collision = primary in (minimum_bet, stack)
    adaptive = Fraction(3, 2) if collision else Fraction(2, 1)
    raw_sizes = (
        minimum_bet,
        _round_half_up(Fraction(1, 4) * pot),
        _round_half_up(Fraction(1, 2) * pot),
        pot,
        _round_half_up(adaptive * pot),
        stack,
        stack,
    )
    return tuple(sorted({projected(size) for size in raw_sizes})), collision


class CollisionRepairV3EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.campaign = run_adr0300_collision_repair_v3_evaluation()

    def test_frozen_campaign_rejects_only_qualified_raw_chip_recovery(self) -> None:
        campaign = self.campaign
        self.assertIs(campaign.stop_reason, V3CampaignStopReason.QUALIFIED_REJECTED)
        self.assertFalse(campaign.passed)
        self.assertGreater(campaign.elapsed_seconds, 0.0)
        self.assertEqual(campaign.digest, ADR0300_EVALUATION_CAMPAIGN_SHA256)

        representative = campaign.representative
        qualified = campaign.qualified
        assert qualified is not None
        self.assertTrue(representative.passed)
        self.assertFalse(qualified.passed)
        self.assertEqual(representative.digest, ADR0300_REPRESENTATIVE_RESULT_SHA256)
        self.assertEqual(qualified.digest, ADR0300_QUALIFIED_RESULT_SHA256)

        self.assertEqual(
            representative.maximum_normalized_loss,
            0.0006146721799333525,
        )
        self.assertEqual(
            representative.mean_normalized_loss,
            7.113215970853139e-05,
        )
        self.assertLessEqual(
            representative.maximum_normalized_loss,
            ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT.value,
        )
        self.assertLessEqual(
            representative.mean_normalized_loss,
            ADR0300_MEAN_NORMALIZED_LOSS_LIMIT.value,
        )

        self.assertEqual(qualified.maximum_normalized_loss, 0.0010646792653687953)
        self.assertEqual(qualified.mean_normalized_loss, 0.00025946068709217334)
        self.assertLessEqual(
            qualified.maximum_normalized_loss,
            ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT.value,
        )
        self.assertLessEqual(
            qualified.mean_normalized_loss,
            ADR0300_MEAN_NORMALIZED_LOSS_LIMIT.value,
        )
        self.assertEqual(qualified.recovery_numerator_chips, 1.299630985953442)
        self.assertEqual(qualified.recovery_denominator_chips, 1.623427607863377)
        self.assertEqual(qualified.aggregate_recovery, 0.800547544995807)
        assert qualified.aggregate_recovery is not None
        self.assertLess(
            qualified.aggregate_recovery,
            ADR0300_AGGREGATE_RECOVERY_FLOOR.value,
        )

        manual_numerator = sum(
            observation.arms[1].value_chips - observation.arms[2].value_chips
            for observation in qualified.observations
        )
        manual_denominator = sum(
            observation.arms[0].value_chips - observation.arms[2].value_chips
            for observation in qualified.observations
        )
        self.assertEqual(manual_numerator, qualified.recovery_numerator_chips)
        self.assertEqual(manual_denominator, qualified.recovery_denominator_chips)
        self.assertEqual(
            manual_numerator / manual_denominator,
            qualified.aggregate_recovery,
        )

    def test_all_72_contexts_bind_exact_sources_widths_and_manual_v3_formula(self) -> None:
        representative_structure = build_adr0301_fresh_structure(
            kind=FreshStructureKind.REPRESENTATIVE
        )
        qualified_structure = build_adr0301_fresh_structure(
            kind=FreshStructureKind.QUALIFIED_POOL
        )
        qualified = self.campaign.qualified
        assert qualified is not None
        families = (
            (
                self.campaign.representative,
                representative_structure,
                tuple(range(ADR0301_REPRESENTATIVE_CONTEXT_COUNT)),
                40,
            ),
            (qualified, qualified_structure, ADR0302_QUALIFIED_INDICES, 20),
        )

        for family, structure, indices, expected_collision_count in families:
            family.verify_against_structure(structure=structure, pool_indices=indices)
            collision_count = 0
            for observation, context_index in zip(
                family.observations,
                indices,
                strict=True,
            ):
                context = structure.contexts[context_index]
                manual_sizes, collided = _manual_v3_sizes(
                    pot=context.pot,
                    stack=context.stack,
                    minimum_bet=context.minimum_bet,
                )
                collision_count += int(collided)
                full, candidate, narrow = observation.arms
                self.assertEqual(
                    tuple(arm.kind for arm in observation.arms),
                    tuple(V3ArmKind),
                )
                self.assertEqual(
                    full.bet_sizes,
                    tuple(range(context.minimum_bet, context.stack + 1)),
                )
                self.assertEqual(candidate.bet_sizes, manual_sizes)
                self.assertEqual(
                    narrow.bet_sizes,
                    (context.minimum_bet, context.stack),
                )
                self.assertGreaterEqual(
                    full.value_chips + 1e-9,
                    candidate.value_chips,
                )
                self.assertGreaterEqual(
                    candidate.value_chips + 1e-9,
                    narrow.value_chips,
                )
                self.assertEqual(observation.v3_raise_count, len(manual_sizes))
                self.assertEqual(observation.v3_action_count, len(manual_sizes) + 1)
                self.assertLessEqual(
                    observation.v3_raise_count,
                    ADR0300_MAXIMUM_V3_RAISES,
                )
                self.assertLessEqual(
                    observation.v3_action_count,
                    ADR0300_MAXIMUM_V3_ACTIONS,
                )
                self.assertLess(
                    observation.v3_action_count,
                    observation.exact_legal_action_count,
                )
                for arm in observation.arms:
                    self.assertEqual(
                        arm.dimensions.variable_count,
                        8 * len(arm.bet_sizes) + 4,
                    )
                    self.assertEqual(
                        arm.dimensions.inequality_count,
                        8 * len(arm.bet_sizes) + 8,
                    )
                    self.assertLessEqual(
                        arm.probability_residual,
                        ADR0302_PROBABILITY_ALLOWANCE.value,
                    )
                    self.assertLessEqual(
                        arm.chip_objective_error,
                        ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips,
                    )
                    self.assertLessEqual(
                        arm.lp_duality_gap_chips,
                        ADR0302_LP_DUALITY_ALLOWANCE.chips,
                    )
                    self.assertLessEqual(
                        arm.envelope_violation_chips,
                        ADR0302_ENVELOPE_ALLOWANCE.chips,
                    )
                    self.assertLessEqual(arm.simplex_pivots, ADR0302_SIMPLEX_PIVOT_CAP)
            self.assertEqual(collision_count, expected_collision_count)

    def test_every_context_has_an_independent_bounded_teacher_certificate(self) -> None:
        qualified = self.campaign.qualified
        assert qualified is not None
        teachers = (
            *self.campaign.representative.teacher_observations,
            *qualified.teacher_observations,
        )
        self.assertEqual(len(teachers), 72)
        for teacher in teachers:
            self.assertLessEqual(teacher.value_difference_chips, 1e-9)
            self.assertLessEqual(teacher.teacher_duality_gap_chips, 1e-9)
            self.assertLessEqual(
                teacher.compact_probability_residual,
                ADR0302_PROBABILITY_ALLOWANCE.value,
            )
            self.assertLessEqual(
                teacher.compact_chip_objective_error,
                ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                teacher.compact_lp_duality_gap_chips,
                ADR0302_LP_DUALITY_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                teacher.compact_envelope_violation_chips,
                ADR0302_ENVELOPE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                teacher.compact_simplex_pivots,
                ADR0302_SIMPLEX_PIVOT_CAP,
            )
            self.assertEqual(teacher.teacher_opener_pure_plan_count, 9)
            self.assertEqual(teacher.teacher_responder_pure_plan_count, 16)

    def test_schema_mutations_and_representative_first_stop_fail_closed(self) -> None:
        representative = self.campaign.representative
        first = representative.observations[0]
        with self.assertRaisesRegex(ValueError, "normalized loss"):
            replace(first, normalized_full_loss=first.normalized_full_loss + 1e-8)
        zero_loss = next(
            observation
            for observation in representative.observations
            if observation.normalized_full_loss == 0.0
        )
        with self.assertRaisesRegex(ValueError, "normalized loss"):
            replace(zero_loss, normalized_full_loss=False)  # type: ignore[arg-type]

        changed_span = replace(
            first,
            payoff_span=first.payoff_span + 1,
            normalized_full_loss=(
                max(0.0, first.arms[0].value_chips - first.arms[1].value_chips)
                / (first.payoff_span + 1)
            ),
        )
        changed_span_family = replace(
            representative,
            observations=(changed_span, *representative.observations[1:]),
        )
        with self.assertRaisesRegex(ValueError, "payoff span"):
            changed_span_family.verify_against_structure(
                structure=build_adr0301_fresh_structure(
                    kind=FreshStructureKind.REPRESENTATIVE
                ),
                pool_indices=tuple(range(ADR0301_REPRESENTATIVE_CONTEXT_COUNT)),
            )

        full, candidate, narrow = first.arms
        reversed_full = replace(
            full,
            value_chips=candidate.value_chips - 2e-9,
        )
        with self.assertRaisesRegex(ValueError, "reverses full and candidate"):
            replace(first, arms=(reversed_full, candidate, narrow))

        wrong_index = replace(first, pool_context_index=1)
        with self.assertRaisesRegex(ValueError, "pool indices"):
            replace(
                representative,
                observations=(wrong_index, *representative.observations[1:]),
            )

        changed_elapsed = replace(
            self.campaign,
            elapsed_seconds=self.campaign.elapsed_seconds + 1000.0,
        )
        self.assertEqual(changed_elapsed.digest, self.campaign.digest)

        victim_position = max(
            range(len(representative.observations)),
            key=lambda position: (
                representative.observations[position].arms[0].value_chips
                - representative.observations[position].arms[2].value_chips
            )
            / representative.observations[position].payoff_span,
        )
        victim = representative.observations[victim_position]
        victim_full, victim_candidate, victim_narrow = victim.arms
        failed_candidate = replace(
            victim_candidate,
            value_chips=victim_narrow.value_chips,
        )
        failed_victim = replace(
            victim,
            arms=(victim_full, failed_candidate, victim_narrow),
            normalized_full_loss=(
                victim_full.value_chips - failed_candidate.value_chips
            )
            / victim.payoff_span,
        )
        failed_observations = list(representative.observations)
        failed_observations[victim_position] = failed_victim
        failed_representative = replace(
            representative,
            observations=tuple(failed_observations),
        )
        self.assertFalse(failed_representative.passed)
        with patch.object(
            evaluation_module,
            "_evaluate_family",
            return_value=failed_representative,
        ) as evaluator:
            stopped = evaluation_module.run_adr0300_collision_repair_v3_evaluation()
        self.assertEqual(evaluator.call_count, 1)
        self.assertIs(
            stopped.stop_reason,
            V3CampaignStopReason.REPRESENTATIVE_REJECTED,
        )
        self.assertIsNone(stopped.qualified)

    def test_gate_quantities_are_distinct_types_and_source_has_no_integration_hook(self) -> None:
        gate_types = {
            type(V3OrderingAllowance(1e-9)),
            type(V3MaximumNormalizedLossLimit(0.005)),
            type(V3MeanNormalizedLossLimit(0.001)),
            type(V3AggregateRecoveryFloor(0.90)),
        }
        self.assertEqual(len(gate_types), 4)
        with self.assertRaises(ValueError):
            V3OrderingAllowance(0.0)
        with self.assertRaises(ValueError):
            V3MaximumNormalizedLossLimit(0.0)
        with self.assertRaises(ValueError):
            V3MeanNormalizedLossLimit(0.0)
        with self.assertRaises(ValueError):
            V3AggregateRecoveryFloor(0.0)

        path = _ROOT / "src/pontius/collision_repair_v3_evaluation.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        forbidden_fragments = ("blueprint", "convex", "replay", "resolver", "strategy")
        for module in imported_modules:
            self.assertFalse(
                any(fragment in module for fragment in forbidden_fragments),
                module,
            )


if __name__ == "__main__":
    unittest.main()
