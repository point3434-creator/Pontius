from __future__ import annotations

import ast
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_qualification as qualification
from pontius.certified_reduced_sizing_consumer_v2 import (
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    KernelRaiseToTotal,
    LegalRaiseSetScope,
    ReducedSizingResponseModel,
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
)
from pontius.fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    ADR0323_OPPORTUNITY_FLOOR,
    ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
    ADR0323_QUALIFICATION_TARGET,
    ActionWidthQualificationArm,
    ActionWidthQualificationCampaignResult,
    ActionWidthQualificationClassification,
    ActionWidthQualificationConsumerFailure,
    ActionWidthQualificationObservation,
    ActionWidthQualificationRunnerRejected,
    ActionWidthQualificationSchedule,
    ActionWidthQualificationStopReason,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    NestedValueReversalAllowance,
    NormalizedOpportunityFloor,
    QualificationAmbiguityGuard,
    QualifiedActionWidthDevelopmentPanel,
    build_adr0323_qualification_schedule,
    certified_full_minus_subset_regret,
    classify_action_width_opportunity,
    qualification_protocol_sha256,
    qualification_requests_for_context,
    run_adr0323_development_qualification,
    verify_adr0323_qualification_source_and_dependencies,
    verify_adr0324_structure_source_and_pool,
)
from pontius.fresh_action_width_qualification_seal import (
    ADR0323_QUALIFICATION_PROTOCOL_SHA256,
    ADR0323_QUALIFICATION_SCHEDULE_SHA256,
    ADR0323_QUALIFICATION_SOURCE_MANIFEST,
    ADR0323_QUALIFICATION_TASK_COUNT,
)
from pontius.fresh_action_width_structures_seal import (
    ADR0323_DEVELOPMENT_POOL_SHA256,
)
from pontius.no_limit_betting import BettingStreet, NoLimitBettingState


_PROBABILITIES = (
    (Fraction(1, 4), Fraction(1, 4)),
    (Fraction(1, 4), Fraction(1, 4)),
)
_SIGNS = ((1, 1), (-1, -1))


def _two_live_toy_state() -> NoLimitBettingState:
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(9, 9, 2, 2, 2, 2),
        stacks=(4, 4, 2, 2, 2, 2),
        total_contributions=(5, 5, 0, 0, 0, 0),
        street_contributions=(0, 0, 0, 0, 0, 0),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=2,
        acted_at_bet=(None, None, None, None, None, None),
    )


def _toy_request(
    *,
    scope: LegalRaiseSetScope,
    amounts: tuple[int, ...],
    label: str,
) -> CertifiedReducedSizingRequestV2:
    return CertifiedReducedSizingRequestV2(
        context_id=label,
        betting=_two_live_toy_state(),
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=scope,
        legal_raise_to_totals=tuple(KernelRaiseToTotal(value) for value in amounts),
        joint_probabilities=_PROBABILITIES,
        showdown_signs=_SIGNS,
    )


def _forbidden_consumer(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("fresh qualification consumer must remain unopened")


class FreshActionWidthQualificationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = verify_adr0324_structure_source_and_pool()
        cls.schedule = build_adr0323_qualification_schedule()
        full = consume_certified_reduced_sizing_v2(
            _toy_request(
                scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
                amounts=(2, 3, 4),
                label="adr0323-unsealed-qualification-schema-full-toy",
            )
        )
        width_two = consume_certified_reduced_sizing_v2(
            _toy_request(
                scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
                amounts=(2, 4),
                label="adr0323-unsealed-qualification-schema-width2-toy",
            )
        )
        if not isinstance(full, CertifiedReducedSizingAcceptedV2) or not isinstance(
            width_two,
            CertifiedReducedSizingAcceptedV2,
        ):
            raise AssertionError("unsealed qualification schema toys must be accepted")
        cls.full_toy = full
        cls.width_two_toy = width_two

    def test_source_manifest_protocol_and_import_boundary_are_exact(self) -> None:
        root = Path(qualification.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0323_QUALIFICATION_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0323_QUALIFICATION_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_qualification.py"],
            verify_adr0323_qualification_source_and_dependencies(),
        )
        self.assertEqual(
            ADR0323_QUALIFICATION_PROTOCOL_SHA256,
            qualification_protocol_sha256(),
        )
        with self.assertRaises(TypeError):
            ADR0323_QUALIFICATION_SOURCE_MANIFEST[  # type: ignore[index]
                "fresh_action_width_qualification.py"
            ] = "0" * 64

        source_path = Path(qualification.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        consumer_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "consume_certified_reduced_sizing_v2"
            ):
                consumer_calls += 1
        forbidden_modules = {
            "capacity_filling_action_abstraction",
            "collision_repair_action_abstraction",
            "fresh_capacity_filling_qualification",
            "fresh_collision_repair_qualification",
            "legal_action_abstraction",
            "linear_program",
            "reduced_river_sizing_oracle",
            "sizing_power_diagnostic",
            "width_four_sizing_power_evaluation",
        }
        self.assertTrue(imported.isdisjoint(forbidden_modules))
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("raise_to", names)
        self.assertNotIn("apply_action", attributes)
        self.assertEqual(2, consumer_calls)

        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "qualification.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                actual["fresh_action_width_qualification.py"],
                canonical_lf_source_sha256(copy),
            )

    def test_value_free_schedule_is_complete_ordered_and_sealed(self) -> None:
        with patch.object(
            qualification,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            schedule = build_adr0323_qualification_schedule()
        self.assertEqual(ADR0323_DEVELOPMENT_POOL_SHA256, schedule.pool_sha256)
        self.assertEqual(ADR0323_QUALIFICATION_TASK_COUNT, len(schedule.tasks))
        self.assertEqual(ADR0323_QUALIFICATION_SCHEDULE_SHA256, schedule.digest)
        for index, context in enumerate(self.pool.contexts):
            full, width_two = schedule.tasks[2 * index : 2 * index + 2]
            expected_full, expected_width_two = qualification_requests_for_context(
                context=context,
                context_index=index,
            )
            self.assertEqual(expected_full, full)
            self.assertEqual(expected_width_two, width_two)
            self.assertEqual(full.request.betting, context.betting)
            self.assertEqual(context.complete_raise_to_totals, full.request.legal_raise_to_totals)
            self.assertEqual(
                (
                    context.complete_raise_to_totals[0],
                    context.complete_raise_to_totals[-1],
                ),
                width_two.request.legal_raise_to_totals,
            )
            self.assertEqual(
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                full.arm,
            )
            self.assertEqual(
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
                width_two.arm,
            )

    def test_regret_interval_uses_conservative_endpoint_directions(self) -> None:
        regret = certified_full_minus_subset_regret(
            full=CertifiedChipValueInterval(1.0, 1.1),
            subset=CertifiedChipValueInterval(0.8, 0.9),
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        self.assertAlmostEqual(0.1, regret.signed_lower_chips)
        self.assertAlmostEqual(0.3, regret.signed_upper_chips)
        self.assertAlmostEqual(0.1, regret.nonnegative_lower_chips)
        self.assertAlmostEqual(0.3, regret.nonnegative_upper_chips)

        overlap = certified_full_minus_subset_regret(
            full=CertifiedChipValueInterval(0.999999999, 1.0),
            subset=CertifiedChipValueInterval(1.0, 1.000000001),
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        self.assertEqual(0.0, overlap.nonnegative_lower_chips)
        self.assertEqual(0.0, overlap.nonnegative_upper_chips)
        with self.assertRaisesRegex(ValueError, "reverse"):
            certified_full_minus_subset_regret(
                full=CertifiedChipValueInterval(0.8, 0.9),
                subset=CertifiedChipValueInterval(1.0, 1.1),
                reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
            )

    def test_classification_keeps_normalized_floor_and_chip_guard_distinct(self) -> None:
        qualifying = CertifiedChipRegretInterval(0.011, 0.012, 0.011, 0.012)
        nonqualifying = CertifiedChipRegretInterval(0.005, 0.006, 0.005, 0.006)
        ambiguous = CertifiedChipRegretInterval(0.009999999, 0.010000001, 0.009999999, 0.010000001)
        self.assertIs(
            ActionWidthQualificationClassification.QUALIFYING,
            classify_action_width_opportunity(
                regret=qualifying,
                payoff_span_chips=100,
                opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
                ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
            ),
        )
        self.assertIs(
            ActionWidthQualificationClassification.NONQUALIFYING,
            classify_action_width_opportunity(
                regret=nonqualifying,
                payoff_span_chips=100,
                opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
                ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
            ),
        )
        self.assertIs(
            ActionWidthQualificationClassification.AMBIGUOUS,
            classify_action_width_opportunity(
                regret=ambiguous,
                payoff_span_chips=100,
                opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
                ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
            ),
        )
        payoff_span_control = CertifiedChipRegretInterval(0.0015, 0.0016, 0.0015, 0.0016)
        self.assertIs(
            ActionWidthQualificationClassification.NONQUALIFYING,
            classify_action_width_opportunity(
                regret=payoff_span_control,
                payoff_span_chips=22,
                opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
                ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
            ),
        )
        self.assertNotEqual(
            NormalizedOpportunityFloor(1e-4),
            QualificationAmbiguityGuard(1e-4),
        )
        self.assertNotEqual(
            NestedValueReversalAllowance(1e-8),
            QualificationAmbiguityGuard(1e-8),
        )

    def test_campaign_stop_state_and_digest_bind_values(self) -> None:
        regret = CertifiedChipRegretInterval(0.1, 0.2, 0.1, 0.2)
        observations = tuple(
            ActionWidthQualificationObservation(
                context_index=index,
                context_semantic_digest=sha256(f"context-{index}".encode()).hexdigest(),
                full=self.full_toy,
                width_two=self.width_two_toy,
                regret=regret,
                classification=ActionWidthQualificationClassification.QUALIFYING,
            )
            for index in range(ADR0323_QUALIFICATION_TARGET)
        )
        result = ActionWidthQualificationCampaignResult(
            pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
            schedule_sha256=ADR0323_QUALIFICATION_SCHEDULE_SHA256,
            qualification_source_sha256="1" * 64,
            observations=observations,
            qualified_indices=tuple(range(ADR0323_QUALIFICATION_TARGET)),
            stop_reason=ActionWidthQualificationStopReason.TARGET_REACHED,
        )
        self.assertEqual(32, result.public_highs_ds_invocation_count)
        changed_observations = (
            replace(
                observations[0],
                regret=CertifiedChipRegretInterval(0.11, 0.21, 0.11, 0.21),
            ),
            *observations[1:],
        )
        changed = replace(result, observations=changed_observations)
        self.assertNotEqual(result.digest, changed.digest)
        with self.assertRaises(ValueError):
            replace(result, qualified_indices=result.qualified_indices[:-1])

        ambiguous = replace(
            observations[0],
            classification=ActionWidthQualificationClassification.AMBIGUOUS,
        )
        ambiguous_result = ActionWidthQualificationCampaignResult(
            pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
            schedule_sha256=ADR0323_QUALIFICATION_SCHEDULE_SHA256,
            qualification_source_sha256="2" * 64,
            observations=(ambiguous,),
            qualified_indices=(),
            stop_reason=ActionWidthQualificationStopReason.AMBIGUOUS,
        )
        self.assertEqual(2, ambiguous_result.public_highs_ds_invocation_count)
        with self.assertRaises(ValueError):
            replace(
                ambiguous_result,
                stop_reason=ActionWidthQualificationStopReason.POOL_EXHAUSTED,
            )

    def test_consumer_rejection_is_retained_without_retry(self) -> None:
        rejected = consume_certified_reduced_sizing_v2(
            _toy_request(
                scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
                amounts=(2, 4),
                label="adr0323-unsealed-qualification-rejection-toy",
            ),
            linprog_function=_forbidden_consumer,
        )
        self.assertIsInstance(rejected, CertifiedReducedSizingRejectedV2)
        assert isinstance(rejected, CertifiedReducedSizingRejectedV2)
        failure = ActionWidthQualificationConsumerFailure(
            context_index=0,
            context_semantic_digest="3" * 64,
            arm=ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
            rejected=rejected,
        )
        result = ActionWidthQualificationCampaignResult(
            pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
            schedule_sha256=ADR0323_QUALIFICATION_SCHEDULE_SHA256,
            qualification_source_sha256="4" * 64,
            observations=(),
            qualified_indices=(),
            stop_reason=ActionWidthQualificationStopReason.CONSUMER_REJECTED,
            consumer_failure=failure,
        )
        self.assertEqual(0, result.public_highs_ds_invocation_count)
        self.assertEqual(0, rejected.public_highs_ds_invocation_count)

    def test_preflight_rejection_makes_no_consumer_call(self) -> None:
        with (
            patch.object(
                qualification,
                "verify_adr0323_qualification_source_and_dependencies",
                side_effect=RuntimeError("synthetic source drift"),
            ),
            patch.object(
                qualification,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_consumer,
            ),
        ):
            result = run_adr0323_development_qualification()
        self.assertIsInstance(result, ActionWidthQualificationRunnerRejected)
        assert isinstance(result, ActionWidthQualificationRunnerRejected)
        self.assertEqual(0, result.known_public_highs_ds_invocation_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertIn("synthetic source drift", result.exception_chain[0].message)

    def test_unexpected_execution_failure_retains_prefix_and_unknown_count(self) -> None:
        with patch.object(
            qualification,
            "consume_certified_reduced_sizing_v2",
            return_value=object(),
        ):
            result = run_adr0323_development_qualification()
        self.assertIsInstance(result, ActionWidthQualificationRunnerRejected)
        assert isinstance(result, ActionWidthQualificationRunnerRejected)
        self.assertEqual("execution", result.stage.value)
        self.assertEqual(ADR0323_DEVELOPMENT_POOL_SHA256, result.pool_sha256)
        self.assertEqual(ADR0323_QUALIFICATION_SCHEDULE_SHA256, result.schedule_sha256)
        self.assertEqual((), result.completed_observations)
        self.assertEqual((), result.qualified_indices)
        self.assertEqual(0, result.current_context_index)
        self.assertIs(
            ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
            result.current_arm,
        )
        self.assertEqual(0, result.known_public_highs_ds_invocation_count)
        self.assertFalse(result.invocation_count_complete)
        self.assertEqual(64, len(result.digest))

    def test_structure_drift_rejects_before_pool_use(self) -> None:
        with patch.object(
            qualification,
            "canonical_lf_source_sha256",
            return_value="0" * 64,
        ):
            with self.assertRaisesRegex(RuntimeError, "structure source"):
                verify_adr0324_structure_source_and_pool()

    def test_panel_and_schedule_corruption_fail_closed(self) -> None:
        panel = QualifiedActionWidthDevelopmentPanel(
            pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
            qualification_result_sha256="5" * 64,
            pool_indices=tuple(range(ADR0323_QUALIFICATION_TARGET)),
            context_semantic_digests=tuple(
                sha256(f"panel-{index}".encode()).hexdigest()
                for index in range(ADR0323_QUALIFICATION_TARGET)
            ),
        )
        self.assertEqual(64, len(panel.digest))
        with self.assertRaises(ValueError):
            replace(panel, pool_indices=tuple(reversed(panel.pool_indices)))
        with self.assertRaises(ValueError):
            replace(
                self.schedule,
                tasks=(self.schedule.tasks[1], self.schedule.tasks[0], *self.schedule.tasks[2:]),
            )


if __name__ == "__main__":
    unittest.main()
