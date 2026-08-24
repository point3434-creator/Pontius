"""Candidate-blind ADR-0323 development qualification owner.

The source can build the frozen request schedule without opening a sizing
value.  Its public runner is eligible only after the adjacent source seal is
committed; it owns both consumer calls, interval classification, and stop state
for each opened context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from pathlib import Path

from .certified_reduced_sizing_consumer_v2 import (
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    LegalRaiseSetScope,
    ReducedSizingResponseModel,
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
)
from .fresh_action_width_structures import (
    ADR0323_RAISE_WIDTHS,
    FreshActionWidthContext,
    FreshActionWidthDevelopmentPool,
    RaiseActionWidth,
    anchored_raise_subset_family,
    build_adr0323_development_pool,
)


ADR0323_QUALIFICATION_TARGET = 16


def _require_positive_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class NormalizedOpportunityFloor:
    """Dimensionless material-opportunity threshold."""

    value: float

    def __post_init__(self) -> None:
        value = _require_positive_finite(
            self.value,
            label="normalized opportunity floor",
        )
        if value >= 1.0:
            raise ValueError("normalized opportunity floor must be below one")


@dataclass(frozen=True, slots=True)
class NestedValueReversalAllowance:
    """Chip allowance for certified nested-action interval reversal."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(
            self.chips,
            label="nested-value reversal allowance",
        )


@dataclass(frozen=True, slots=True)
class QualificationAmbiguityGuard:
    """Chip guard around the normalized qualification threshold."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(
            self.chips,
            label="qualification ambiguity guard",
        )


ADR0323_OPPORTUNITY_FLOOR = NormalizedOpportunityFloor(1e-4)
ADR0323_NESTED_REVERSAL_ALLOWANCE = NestedValueReversalAllowance(1e-8)
ADR0323_QUALIFICATION_AMBIGUITY_GUARD = QualificationAmbiguityGuard(1e-8)


@dataclass(frozen=True, slots=True)
class CertifiedChipValueInterval:
    lower_chips: float
    upper_chips: float

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, float) and isfinite(value)
            for value in (self.lower_chips, self.upper_chips)
        ):
            raise ValueError("certified chip-value endpoints must be finite floats")
        if self.lower_chips > self.upper_chips:
            raise ValueError("certified chip-value interval is inverted")


@dataclass(frozen=True, slots=True)
class CertifiedChipRegretInterval:
    signed_lower_chips: float
    signed_upper_chips: float
    nonnegative_lower_chips: float
    nonnegative_upper_chips: float

    def __post_init__(self) -> None:
        values = (
            self.signed_lower_chips,
            self.signed_upper_chips,
            self.nonnegative_lower_chips,
            self.nonnegative_upper_chips,
        )
        if not all(isinstance(value, float) and isfinite(value) for value in values):
            raise ValueError("certified chip-regret endpoints must be finite floats")
        if self.signed_lower_chips > self.signed_upper_chips:
            raise ValueError("signed certified chip-regret interval is inverted")
        if (
            self.nonnegative_lower_chips
            != max(0.0, self.signed_lower_chips)
            or self.nonnegative_upper_chips
            != max(0.0, self.signed_upper_chips)
        ):
            raise ValueError("nonnegative chip regret differs from signed endpoints")
        if self.nonnegative_lower_chips > self.nonnegative_upper_chips:
            raise ValueError("nonnegative certified chip-regret interval is inverted")


def certified_full_minus_subset_regret(
    *,
    full: CertifiedChipValueInterval,
    subset: CertifiedChipValueInterval,
    reversal_allowance: NestedValueReversalAllowance,
) -> CertifiedChipRegretInterval:
    """Subtract certified endpoints in the conservative nested-game direction."""

    if not isinstance(full, CertifiedChipValueInterval) or not isinstance(
        subset,
        CertifiedChipValueInterval,
    ):
        raise TypeError("certified regret requires two chip-value intervals")
    if not isinstance(reversal_allowance, NestedValueReversalAllowance):
        raise TypeError("certified regret requires a nested-value allowance")
    signed_lower = full.lower_chips - subset.upper_chips
    signed_upper = full.upper_chips - subset.lower_chips
    if signed_upper < -reversal_allowance.chips:
        raise ValueError("nested action sets reverse beyond the chip allowance")
    return CertifiedChipRegretInterval(
        signed_lower_chips=signed_lower,
        signed_upper_chips=signed_upper,
        nonnegative_lower_chips=max(0.0, signed_lower),
        nonnegative_upper_chips=max(0.0, signed_upper),
    )


class ActionWidthQualificationClassification(StrEnum):
    QUALIFYING = "qualifying"
    NONQUALIFYING = "nonqualifying"
    AMBIGUOUS = "ambiguous"


def classify_action_width_opportunity(
    *,
    regret: CertifiedChipRegretInterval,
    payoff_span_chips: int,
    opportunity_floor: NormalizedOpportunityFloor,
    ambiguity_guard: QualificationAmbiguityGuard,
) -> ActionWidthQualificationClassification:
    if not isinstance(regret, CertifiedChipRegretInterval):
        raise TypeError("action-width classification requires certified chip regret")
    if (
        isinstance(payoff_span_chips, bool)
        or not isinstance(payoff_span_chips, int)
        or payoff_span_chips <= 0
    ):
        raise ValueError("action-width payoff span must be a positive chip count")
    if not isinstance(opportunity_floor, NormalizedOpportunityFloor):
        raise TypeError("action-width classification requires its normalized floor")
    if not isinstance(ambiguity_guard, QualificationAmbiguityGuard):
        raise TypeError("action-width classification requires its chip guard")
    threshold = opportunity_floor.value * payoff_span_chips
    if regret.nonnegative_lower_chips > threshold + ambiguity_guard.chips:
        return ActionWidthQualificationClassification.QUALIFYING
    if regret.nonnegative_upper_chips < threshold - ambiguity_guard.chips:
        return ActionWidthQualificationClassification.NONQUALIFYING
    return ActionWidthQualificationClassification.AMBIGUOUS


class ActionWidthQualificationArm(StrEnum):
    COMPLETE_INTEGER_UNIVERSE = "complete_integer_universe"
    ANCHORED_RAISE_WIDTH_TWO = "anchored_raise_width_two"


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationTask:
    context_index: int
    context_semantic_digest: str
    arm: ActionWidthQualificationArm
    request: CertifiedReducedSizingRequestV2

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index < 0
        ):
            raise ValueError("qualification task context index must be nonnegative")
        _require_digest(
            self.context_semantic_digest,
            label="qualification task context",
        )
        if not isinstance(self.arm, ActionWidthQualificationArm):
            raise TypeError("qualification task arm must be semantic")
        if not isinstance(self.request, CertifiedReducedSizingRequestV2):
            raise TypeError("qualification task requires an exact consumer request")
        if self.arm is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE:
            if self.request.legal_raise_scope is not LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE:
                raise ValueError("complete qualification arm has restricted scope")
        else:
            if (
                self.request.legal_raise_scope
                is not LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET
                or len(self.request.legal_raise_to_totals) != 2
            ):
                raise ValueError("width-two qualification arm has the wrong scope")

    @property
    def digest(self) -> str:
        return _canonical_sha256({
            "arm": self.arm.value,
            "context_index": self.context_index,
            "context_semantic_digest": self.context_semantic_digest,
            "context_label": self.request.context_id,
            "raise_to_totals": tuple(
                value.chips for value in self.request.legal_raise_to_totals
            ),
            "scope": self.request.legal_raise_scope.value,
            "version": "adr0323-action-width-qualification-task-v1",
        })


def qualification_requests_for_context(
    *,
    context: FreshActionWidthContext,
    context_index: int,
) -> tuple[ActionWidthQualificationTask, ActionWidthQualificationTask]:
    if not isinstance(context, FreshActionWidthContext):
        raise TypeError("qualification request construction requires a fresh context")
    if (
        isinstance(context_index, bool)
        or not isinstance(context_index, int)
        or context_index < 0
    ):
        raise ValueError("qualification request context index must be nonnegative")
    width_two = anchored_raise_subset_family(
        context.complete_raise_to_totals,
        RaiseActionWidth(2),
    ).subsets[0]
    shared = {
        "betting": context.betting,
        "response_model": ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        "joint_probabilities": context.joint_probabilities,
        "showdown_signs": context.showdown_signs,
    }
    full_request = CertifiedReducedSizingRequestV2(
        context_id=f"{context.context_id}|qualification|full",
        legal_raise_scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
        legal_raise_to_totals=context.complete_raise_to_totals,
        **shared,
    )
    width_two_request = CertifiedReducedSizingRequestV2(
        context_id=f"{context.context_id}|qualification|raise-width-2",
        legal_raise_scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
        legal_raise_to_totals=width_two,
        **shared,
    )
    return (
        ActionWidthQualificationTask(
            context_index=context_index,
            context_semantic_digest=context.semantic_digest,
            arm=ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
            request=full_request,
        ),
        ActionWidthQualificationTask(
            context_index=context_index,
            context_semantic_digest=context.semantic_digest,
            arm=ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
            request=width_two_request,
        ),
    )


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationSchedule:
    pool_sha256: str
    tasks: tuple[ActionWidthQualificationTask, ...]

    def __post_init__(self) -> None:
        _require_digest(self.pool_sha256, label="qualification schedule pool")
        if not isinstance(self.tasks, tuple) or len(self.tasks) != 192:
            raise TypeError("qualification schedule requires 192 immutable tasks")
        if any(not isinstance(task, ActionWidthQualificationTask) for task in self.tasks):
            raise TypeError("qualification schedule contains a nonsemantic task")
        expected_order = tuple(
            (index, arm)
            for index in range(96)
            for arm in (
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
            )
        )
        if tuple((task.context_index, task.arm) for task in self.tasks) != expected_order:
            raise ValueError("qualification task order differs from ADR-0323")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("qualification schedule repeats a task")

    @property
    def digest(self) -> str:
        return _canonical_sha256({
            "pool_sha256": self.pool_sha256,
            "task_digests": tuple(task.digest for task in self.tasks),
            "version": "adr0323-action-width-qualification-schedule-v1",
        })


def verify_adr0324_structure_source_and_pool() -> FreshActionWidthDevelopmentPool:
    from .fresh_action_width_structures_seal import (
        ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS,
        ADR0323_DEVELOPMENT_POOL_SHA256,
        ADR0323_STRUCTURE_PROTOCOL_SHA256,
        ADR0323_STRUCTURE_SOURCE_MANIFEST,
        ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH,
        ADR0323_TOTAL_SUBSET_COUNT,
    )
    from .fresh_action_width_structures import (
        ADR0323_STRUCTURE_PROTOCOL_SHA256 as actual_protocol,
    )

    root = Path(__file__).resolve().parent
    actual_manifest = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0323_STRUCTURE_SOURCE_MANIFEST
    }
    if actual_manifest != ADR0323_STRUCTURE_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0324 structure source or dependency differs from its seal")
    if actual_protocol != ADR0323_STRUCTURE_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0324 structure protocol differs from its seal")
    pool = build_adr0323_development_pool()
    if (
        pool.digest != ADR0323_DEVELOPMENT_POOL_SHA256
        or pool.candidate_attempts != ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS
        or tuple(
            (width.count, count)
            for width, count in pool.subset_work_ledger.subset_counts_by_raise_width
        )
        != ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH
        or pool.subset_work_ledger.total_subset_count != ADR0323_TOTAL_SUBSET_COUNT
    ):
        raise RuntimeError("ADR-0324 development pool differs from its seal")
    return pool


def build_adr0323_qualification_schedule() -> ActionWidthQualificationSchedule:
    """Build the complete value-free schedule after verifying ADR-0324."""

    pool = verify_adr0324_structure_source_and_pool()
    return ActionWidthQualificationSchedule(
        pool_sha256=pool.digest,
        tasks=tuple(
            task
            for index, context in enumerate(pool.contexts)
            for task in qualification_requests_for_context(
                context=context,
                context_index=index,
            )
        ),
    )


def verify_adr0323_qualification_source_and_dependencies() -> str:
    """Verify the qualification source seal before a fresh consumer call."""

    from .fresh_action_width_qualification_seal import (
        ADR0323_QUALIFICATION_SOURCE_MANIFEST,
        ADR0323_QUALIFICATION_PROTOCOL_SHA256,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0323_QUALIFICATION_SOURCE_MANIFEST
    }
    if actual != ADR0323_QUALIFICATION_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0323 qualification source differs from its seal")
    if ADR0323_QUALIFICATION_PROTOCOL_SHA256 != qualification_protocol_sha256():
        raise RuntimeError("ADR-0323 qualification protocol differs from its seal")
    return actual["fresh_action_width_qualification.py"]


def qualification_protocol_sha256() -> str:
    return _canonical_sha256({
        "ambiguity_guard_chips": ADR0323_QUALIFICATION_AMBIGUITY_GUARD.chips,
        "arm_order": tuple(arm.value for arm in ActionWidthQualificationArm),
        "classification_order": tuple(
            classification.value for classification in ActionWidthQualificationClassification
        ),
        "nested_reversal_allowance_chips": ADR0323_NESTED_REVERSAL_ALLOWANCE.chips,
        "opportunity_floor": ADR0323_OPPORTUNITY_FLOOR.value,
        "private_range_width": 4,
        "raise_width_two": ADR0323_RAISE_WIDTHS[0].count,
        "regret_interval": "[L_full-U_subset,U_full-L_subset]",
        "target": ADR0323_QUALIFICATION_TARGET,
        "version": "adr0323-action-width-qualification-protocol-v1",
    })


def _accepted_interval(
    result: CertifiedReducedSizingAcceptedV2,
) -> CertifiedChipValueInterval:
    if not isinstance(result, CertifiedReducedSizingAcceptedV2):
        raise TypeError("qualification value interval requires accepted evidence")
    if result.public_highs_ds_invocation_count != 1:
        raise ValueError("qualification accepted arm must make exactly one public call")
    return CertifiedChipValueInterval(
        lower_chips=result.feasible_behavioral_lower_bound_chips,
        upper_chips=result.certified_upper_bound_chips,
    )


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationObservation:
    context_index: int
    context_semantic_digest: str
    full: CertifiedReducedSizingAcceptedV2
    width_two: CertifiedReducedSizingAcceptedV2
    regret: CertifiedChipRegretInterval
    classification: ActionWidthQualificationClassification

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index < 0
        ):
            raise ValueError("qualification observation index must be nonnegative")
        _require_digest(
            self.context_semantic_digest,
            label="qualification observation context",
        )
        if not isinstance(self.full, CertifiedReducedSizingAcceptedV2) or not isinstance(
            self.width_two,
            CertifiedReducedSizingAcceptedV2,
        ):
            raise TypeError("qualification observation requires two accepted arms")
        if not isinstance(self.regret, CertifiedChipRegretInterval):
            raise TypeError("qualification observation requires certified regret")
        if not isinstance(self.classification, ActionWidthQualificationClassification):
            raise TypeError("qualification observation classification must be semantic")

    def verify_against_context(self, context: FreshActionWidthContext) -> None:
        expected_full, expected_width_two = qualification_requests_for_context(
            context=context,
            context_index=self.context_index,
        )
        if (
            self.context_semantic_digest != context.semantic_digest
            or self.full.request != expected_full.request
            or self.width_two.request != expected_width_two.request
        ):
            raise ValueError("qualification observation differs from its exact context")
        expected_regret = certified_full_minus_subset_regret(
            full=_accepted_interval(self.full),
            subset=_accepted_interval(self.width_two),
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_classification = classify_action_width_opportunity(
            regret=expected_regret,
            payoff_span_chips=context.payoff_span_chips,
            opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
            ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
        )
        if self.regret != expected_regret or self.classification is not expected_classification:
            raise ValueError("qualification observation interval or class drifted")


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationConsumerFailure:
    context_index: int
    context_semantic_digest: str
    arm: ActionWidthQualificationArm
    rejected: CertifiedReducedSizingRejectedV2
    completed_full: CertifiedReducedSizingAcceptedV2 | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index < 0
        ):
            raise ValueError("qualification failure index must be nonnegative")
        _require_digest(self.context_semantic_digest, label="qualification failure context")
        if not isinstance(self.arm, ActionWidthQualificationArm):
            raise TypeError("qualification failure arm must be semantic")
        if not isinstance(self.rejected, CertifiedReducedSizingRejectedV2):
            raise TypeError("qualification failure must retain a consumer rejection")
        if self.arm is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE:
            if self.completed_full is not None:
                raise ValueError("full-arm rejection cannot retain a completed full arm")
        elif not isinstance(self.completed_full, CertifiedReducedSizingAcceptedV2):
            raise TypeError("width-two rejection must retain its accepted full arm")


class ActionWidthQualificationStopReason(StrEnum):
    TARGET_REACHED = "target_reached"
    POOL_EXHAUSTED = "pool_exhausted"
    AMBIGUOUS = "ambiguous"
    CONSUMER_REJECTED = "consumer_rejected"


@dataclass(frozen=True, slots=True)
class QualifiedActionWidthDevelopmentPanel:
    pool_sha256: str
    qualification_result_sha256: str
    pool_indices: tuple[int, ...]
    context_semantic_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_digest(self.pool_sha256, label="qualified panel pool")
        _require_digest(
            self.qualification_result_sha256,
            label="qualified panel result",
        )
        if not isinstance(self.pool_indices, tuple) or len(
            self.pool_indices
        ) != ADR0323_QUALIFICATION_TARGET:
            raise TypeError("qualified panel requires 16 immutable indices")
        if tuple(sorted(self.pool_indices)) != self.pool_indices or len(
            set(self.pool_indices)
        ) != len(self.pool_indices):
            raise ValueError("qualified panel indices must increase uniquely")
        if not isinstance(self.context_semantic_digests, tuple) or len(
            self.context_semantic_digests
        ) != len(self.pool_indices):
            raise TypeError("qualified panel context digests must align with indices")
        for digest in self.context_semantic_digests:
            _require_digest(digest, label="qualified panel context")

    @property
    def digest(self) -> str:
        return _canonical_sha256({
            "context_semantic_digests": self.context_semantic_digests,
            "pool_indices": self.pool_indices,
            "pool_sha256": self.pool_sha256,
            "qualification_result_sha256": self.qualification_result_sha256,
            "version": "adr0323-qualified-action-width-development-panel-v1",
        })


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationCampaignResult:
    pool_sha256: str
    schedule_sha256: str
    qualification_source_sha256: str
    observations: tuple[ActionWidthQualificationObservation, ...]
    qualified_indices: tuple[int, ...]
    stop_reason: ActionWidthQualificationStopReason
    consumer_failure: ActionWidthQualificationConsumerFailure | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("qualification result pool", self.pool_sha256),
            ("qualification result schedule", self.schedule_sha256),
            ("qualification result source", self.qualification_source_sha256),
        ):
            _require_digest(value, label=label)
        if not isinstance(self.observations, tuple) or any(
            not isinstance(value, ActionWidthQualificationObservation)
            for value in self.observations
        ):
            raise TypeError("qualification result observations must be semantic")
        if not isinstance(self.stop_reason, ActionWidthQualificationStopReason):
            raise TypeError("qualification stop reason must be semantic")
        if tuple(value.context_index for value in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("qualification observations must be a contiguous prefix")
        expected_qualified = tuple(
            value.context_index
            for value in self.observations
            if value.classification is ActionWidthQualificationClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("qualification indices differ from observations")
        ambiguous = tuple(
            value
            for value in self.observations
            if value.classification is ActionWidthQualificationClassification.AMBIGUOUS
        )
        if self.stop_reason is ActionWidthQualificationStopReason.TARGET_REACHED:
            if len(self.qualified_indices) != ADR0323_QUALIFICATION_TARGET or ambiguous:
                raise ValueError("target qualification result has wrong stop state")
            if self.consumer_failure is not None:
                raise ValueError("target qualification result cannot retain a failure")
        elif self.stop_reason is ActionWidthQualificationStopReason.POOL_EXHAUSTED:
            if (
                len(self.observations) != 96
                or len(self.qualified_indices) >= ADR0323_QUALIFICATION_TARGET
                or ambiguous
                or self.consumer_failure is not None
            ):
                raise ValueError("exhausted qualification result has wrong stop state")
        elif self.stop_reason is ActionWidthQualificationStopReason.AMBIGUOUS:
            if (
                len(ambiguous) != 1
                or ambiguous[0] is not self.observations[-1]
                or self.consumer_failure is not None
            ):
                raise ValueError("ambiguous qualification result has wrong stop state")
        else:
            if not isinstance(self.consumer_failure, ActionWidthQualificationConsumerFailure):
                raise TypeError("consumer-rejected result must retain its failure")
            if self.consumer_failure.context_index != len(self.observations):
                raise ValueError("consumer failure does not follow completed observations")
            if ambiguous:
                raise ValueError("consumer-rejected result continued past ambiguity")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        count = 2 * len(self.observations)
        if self.consumer_failure is not None:
            if self.consumer_failure.completed_full is not None:
                count += self.consumer_failure.completed_full.public_highs_ds_invocation_count
            count += self.consumer_failure.rejected.public_highs_ds_invocation_count
        return count

    @property
    def digest(self) -> str:
        def accepted_payload(
            value: CertifiedReducedSizingAcceptedV2,
        ) -> dict[str, object]:
            return {
                "bet_increments": tuple(
                    amount.chips for amount in value.reduced_bet_increments
                ),
                "certified_gap_hex": value.certified_gap_chips.hex(),
                "certified_upper_hex": value.certified_upper_bound_chips.hex(),
                "consumer_protocol_sha256": value.consumer_protocol_sha256,
                "consumer_source_sha256": value.consumer_source_sha256,
                "feasible_lower_hex": (
                    value.feasible_behavioral_lower_bound_chips.hex()
                ),
                "legal_raise_set_sha256": value.legal_raise_set_sha256,
                "linear_program_sha256": value.solution.linear_program_sha256,
                "public_call_count": value.public_highs_ds_invocation_count,
                "public_state_sha256": value.public_state_sha256,
                "raise_to_totals": tuple(
                    amount.chips for amount in value.legal_raise_to_totals
                ),
                "request_sha256": value.request_sha256,
                "signed_gap_hex": value.signed_certificate_gap_chips.hex(),
            }

        def observation_payload(
            value: ActionWidthQualificationObservation,
        ) -> dict[str, object]:
            return {
                "classification": value.classification.value,
                "context_index": value.context_index,
                "context_semantic_digest": value.context_semantic_digest,
                "full": accepted_payload(value.full),
                "regret": {
                    "nonnegative_lower_hex": (
                        value.regret.nonnegative_lower_chips.hex()
                    ),
                    "nonnegative_upper_hex": (
                        value.regret.nonnegative_upper_chips.hex()
                    ),
                    "signed_lower_hex": value.regret.signed_lower_chips.hex(),
                    "signed_upper_hex": value.regret.signed_upper_chips.hex(),
                },
                "width_two": accepted_payload(value.width_two),
            }

        failure_payload: dict[str, object] | None = None
        if self.consumer_failure is not None:
            rejected = self.consumer_failure.rejected
            failure_payload = {
                "arm": self.consumer_failure.arm.value,
                "completed_full": (
                    None
                    if self.consumer_failure.completed_full is None
                    else accepted_payload(self.consumer_failure.completed_full)
                ),
                "context_index": self.consumer_failure.context_index,
                "context_semantic_digest": (
                    self.consumer_failure.context_semantic_digest
                ),
                "rejected": {
                    "consumer_protocol_sha256": rejected.consumer_protocol_sha256,
                    "consumer_source_sha256": rejected.consumer_source_sha256,
                    "exception_chain": tuple(
                        (item.module, item.type_name, item.message)
                        for item in rejected.exception_chain
                    ),
                    "legal_raise_set_sha256": rejected.legal_raise_set_sha256,
                    "public_call_count": rejected.public_highs_ds_invocation_count,
                    "public_state_sha256": rejected.public_state_sha256,
                    "reason": rejected.reason.value,
                    "request_sha256": rejected.request_sha256,
                    "stage": rejected.stage.value,
                },
            }
        return _canonical_sha256({
            "consumer_failure": failure_payload,
            "observations": tuple(
                observation_payload(value) for value in self.observations
            ),
            "pool_sha256": self.pool_sha256,
            "qualified_indices": self.qualified_indices,
            "qualification_source_sha256": self.qualification_source_sha256,
            "schedule_sha256": self.schedule_sha256,
            "stop_reason": self.stop_reason.value,
            "version": "adr0323-action-width-qualification-result-v1",
        })

    def verify_against_pool(self, pool: FreshActionWidthDevelopmentPool) -> None:
        if not isinstance(pool, FreshActionWidthDevelopmentPool):
            raise TypeError("qualification result verification requires its pool")
        schedule = ActionWidthQualificationSchedule(
            pool_sha256=pool.digest,
            tasks=tuple(
                task
                for index, context in enumerate(pool.contexts)
                for task in qualification_requests_for_context(
                    context=context,
                    context_index=index,
                )
            ),
        )
        if self.pool_sha256 != pool.digest or self.schedule_sha256 != schedule.digest:
            raise ValueError("qualification result pool or schedule drifted")
        for observation in self.observations:
            observation.verify_against_context(pool.contexts[observation.context_index])
        if self.consumer_failure is not None:
            failure = self.consumer_failure
            context = pool.contexts[failure.context_index]
            full_task, width_task = qualification_requests_for_context(
                context=context,
                context_index=failure.context_index,
            )
            expected = (
                full_task
                if failure.arm
                is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE
                else width_task
            )
            if (
                failure.context_semantic_digest != context.semantic_digest
                or failure.rejected.request != expected.request
            ):
                raise ValueError("qualification failure differs from its exact task")
            if (
                failure.completed_full is not None
                and failure.completed_full.request != full_task.request
            ):
                raise ValueError("qualification failure full evidence drifted")

    def qualified_panel(
        self,
        pool: FreshActionWidthDevelopmentPool,
    ) -> QualifiedActionWidthDevelopmentPanel:
        if self.stop_reason is not ActionWidthQualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached qualification has a panel")
        self.verify_against_pool(pool)
        return QualifiedActionWidthDevelopmentPanel(
            pool_sha256=pool.digest,
            qualification_result_sha256=self.digest,
            pool_indices=self.qualified_indices,
            context_semantic_digests=tuple(
                pool.contexts[index].semantic_digest for index in self.qualified_indices
            ),
        )


class QualificationRunnerStage(StrEnum):
    SOURCE_PREFLIGHT = "source_preflight"
    EXECUTION = "execution"


@dataclass(frozen=True, slots=True)
class QualificationRunnerException:
    module: str
    type_name: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.module, str) or not self.module:
            raise ValueError("qualification exception module must be nonempty")
        if not isinstance(self.type_name, str) or not self.type_name:
            raise ValueError("qualification exception type must be nonempty")
        if not isinstance(self.message, str):
            raise TypeError("qualification exception message must be text")


def _exception_chain(error: Exception) -> tuple[QualificationRunnerException, ...]:
    records: list[QualificationRunnerException] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        records.append(QualificationRunnerException(
            module=type(current).__module__,
            type_name=type(current).__qualname__,
            message=str(current),
        ))
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return tuple(records)


@dataclass(frozen=True, slots=True)
class ActionWidthQualificationRunnerRejected:
    stage: QualificationRunnerStage
    reason: str
    pool_sha256: str | None
    schedule_sha256: str | None
    qualification_source_sha256: str | None
    completed_observations: tuple[ActionWidthQualificationObservation, ...]
    qualified_indices: tuple[int, ...]
    current_context_index: int | None
    current_arm: ActionWidthQualificationArm | None
    known_public_highs_ds_invocation_count: int
    invocation_count_complete: bool
    exception_chain: tuple[QualificationRunnerException, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.stage, QualificationRunnerStage):
            raise TypeError("qualification runner rejection stage must be semantic")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("qualification runner rejection reason must be nonempty")
        if not isinstance(self.completed_observations, tuple) or any(
            not isinstance(value, ActionWidthQualificationObservation)
            for value in self.completed_observations
        ):
            raise TypeError("qualification runner rejection observations must be semantic")
        if tuple(
            value.context_index for value in self.completed_observations
        ) != tuple(range(len(self.completed_observations))):
            raise ValueError("qualification runner rejection observations are not a prefix")
        expected_qualified = tuple(
            value.context_index
            for value in self.completed_observations
            if value.classification is ActionWidthQualificationClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("qualification runner rejection indices drifted")
        if (
            isinstance(self.known_public_highs_ds_invocation_count, bool)
            or not isinstance(self.known_public_highs_ds_invocation_count, int)
            or self.known_public_highs_ds_invocation_count < 0
        ):
            raise ValueError("known qualification public-call count is invalid")
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("qualification call-count completeness must be boolean")
        if not isinstance(self.exception_chain, tuple) or not self.exception_chain:
            raise TypeError("qualification runner rejection requires an exception chain")
        if self.stage is QualificationRunnerStage.SOURCE_PREFLIGHT:
            if any(
                value is not None
                for value in (
                    self.pool_sha256,
                    self.schedule_sha256,
                    self.qualification_source_sha256,
                    self.current_context_index,
                    self.current_arm,
                )
            ):
                raise ValueError("qualification preflight rejection cannot claim run state")
            if (
                self.completed_observations
                or self.qualified_indices
                or self.known_public_highs_ds_invocation_count != 0
                or not self.invocation_count_complete
            ):
                raise ValueError("qualification preflight rejection has execution evidence")
        else:
            for label, value in (
                ("qualification runner pool", self.pool_sha256),
                ("qualification runner schedule", self.schedule_sha256),
                ("qualification runner source", self.qualification_source_sha256),
            ):
                _require_digest(value, label=label)
            if (
                isinstance(self.current_context_index, bool)
                or not isinstance(self.current_context_index, int)
                or self.current_context_index
                not in {
                    len(self.completed_observations),
                    max(0, len(self.completed_observations) - 1),
                }
            ):
                raise ValueError("qualification runner current context is invalid")
            if not isinstance(self.current_arm, ActionWidthQualificationArm):
                raise TypeError("qualification runner current arm must be semantic")
            if self.invocation_count_complete:
                raise ValueError("unexpected execution rejection cannot claim complete calls")

    @property
    def digest(self) -> str:
        return _canonical_sha256({
            "completed_observations": tuple(
                {
                    "classification": value.classification.value,
                    "context_index": value.context_index,
                    "context_semantic_digest": value.context_semantic_digest,
                    "full_request_sha256": value.full.request_sha256,
                    "regret_hex": (
                        value.regret.signed_lower_chips.hex(),
                        value.regret.signed_upper_chips.hex(),
                        value.regret.nonnegative_lower_chips.hex(),
                        value.regret.nonnegative_upper_chips.hex(),
                    ),
                    "width_two_request_sha256": value.width_two.request_sha256,
                }
                for value in self.completed_observations
            ),
            "current_arm": None if self.current_arm is None else self.current_arm.value,
            "current_context_index": self.current_context_index,
            "exception_chain": tuple(
                (value.module, value.type_name, value.message)
                for value in self.exception_chain
            ),
            "invocation_count_complete": self.invocation_count_complete,
            "known_public_call_count": self.known_public_highs_ds_invocation_count,
            "pool_sha256": self.pool_sha256,
            "qualification_source_sha256": self.qualification_source_sha256,
            "qualified_indices": self.qualified_indices,
            "reason": self.reason,
            "schedule_sha256": self.schedule_sha256,
            "stage": self.stage.value,
            "version": "adr0323-action-width-qualification-runner-rejection-v1",
        })


ActionWidthQualificationResult = (
    ActionWidthQualificationCampaignResult | ActionWidthQualificationRunnerRejected
)


def run_adr0323_development_qualification() -> ActionWidthQualificationResult:
    """Own the first fresh sizing values after the committed source seal."""

    try:
        qualification_source = verify_adr0323_qualification_source_and_dependencies()
        pool = verify_adr0324_structure_source_and_pool()
        schedule = build_adr0323_qualification_schedule()
    except Exception as error:
        return ActionWidthQualificationRunnerRejected(
            stage=QualificationRunnerStage.SOURCE_PREFLIGHT,
            reason="qualification source, structure, or schedule drift",
            pool_sha256=None,
            schedule_sha256=None,
            qualification_source_sha256=None,
            completed_observations=(),
            qualified_indices=(),
            current_context_index=None,
            current_arm=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=_exception_chain(error),
        )

    observations: list[ActionWidthQualificationObservation] = []
    qualified: list[int] = []
    known_calls = 0
    current_index = 0
    current_arm = ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE
    try:
        for index, context in enumerate(pool.contexts):
            current_index = index
            full_task = schedule.tasks[2 * index]
            width_task = schedule.tasks[2 * index + 1]
            current_arm = full_task.arm
            full_result = consume_certified_reduced_sizing_v2(full_task.request)
            known_calls += full_result.public_highs_ds_invocation_count
            if isinstance(full_result, CertifiedReducedSizingRejectedV2):
                return ActionWidthQualificationCampaignResult(
                    pool_sha256=pool.digest,
                    schedule_sha256=schedule.digest,
                    qualification_source_sha256=qualification_source,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified),
                    stop_reason=ActionWidthQualificationStopReason.CONSUMER_REJECTED,
                    consumer_failure=ActionWidthQualificationConsumerFailure(
                        context_index=index,
                        context_semantic_digest=context.semantic_digest,
                        arm=full_task.arm,
                        rejected=full_result,
                    ),
                )
            if not isinstance(full_result, CertifiedReducedSizingAcceptedV2):
                raise TypeError("qualification full arm returned a nonsemantic result")

            current_arm = width_task.arm
            width_result = consume_certified_reduced_sizing_v2(width_task.request)
            known_calls += width_result.public_highs_ds_invocation_count
            if isinstance(width_result, CertifiedReducedSizingRejectedV2):
                return ActionWidthQualificationCampaignResult(
                    pool_sha256=pool.digest,
                    schedule_sha256=schedule.digest,
                    qualification_source_sha256=qualification_source,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified),
                    stop_reason=ActionWidthQualificationStopReason.CONSUMER_REJECTED,
                    consumer_failure=ActionWidthQualificationConsumerFailure(
                        context_index=index,
                        context_semantic_digest=context.semantic_digest,
                        arm=width_task.arm,
                        rejected=width_result,
                        completed_full=full_result,
                    ),
                )
            if not isinstance(width_result, CertifiedReducedSizingAcceptedV2):
                raise TypeError("qualification width-two arm returned a nonsemantic result")

            regret = certified_full_minus_subset_regret(
                full=_accepted_interval(full_result),
                subset=_accepted_interval(width_result),
                reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
            )
            classification = classify_action_width_opportunity(
                regret=regret,
                payoff_span_chips=context.payoff_span_chips,
                opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
                ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
            )
            observation = ActionWidthQualificationObservation(
                context_index=index,
                context_semantic_digest=context.semantic_digest,
                full=full_result,
                width_two=width_result,
                regret=regret,
                classification=classification,
            )
            observation.verify_against_context(context)
            observations.append(observation)
            if classification is ActionWidthQualificationClassification.AMBIGUOUS:
                return ActionWidthQualificationCampaignResult(
                    pool_sha256=pool.digest,
                    schedule_sha256=schedule.digest,
                    qualification_source_sha256=qualification_source,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified),
                    stop_reason=ActionWidthQualificationStopReason.AMBIGUOUS,
                )
            if classification is ActionWidthQualificationClassification.QUALIFYING:
                qualified.append(index)
                if len(qualified) == ADR0323_QUALIFICATION_TARGET:
                    return ActionWidthQualificationCampaignResult(
                        pool_sha256=pool.digest,
                        schedule_sha256=schedule.digest,
                        qualification_source_sha256=qualification_source,
                        observations=tuple(observations),
                        qualified_indices=tuple(qualified),
                        stop_reason=ActionWidthQualificationStopReason.TARGET_REACHED,
                    )
        return ActionWidthQualificationCampaignResult(
            pool_sha256=pool.digest,
            schedule_sha256=schedule.digest,
            qualification_source_sha256=qualification_source,
            observations=tuple(observations),
            qualified_indices=tuple(qualified),
            stop_reason=ActionWidthQualificationStopReason.POOL_EXHAUSTED,
        )
    except Exception as error:
        return ActionWidthQualificationRunnerRejected(
            stage=QualificationRunnerStage.EXECUTION,
            reason="qualification runner failed outside a typed consumer rejection",
            pool_sha256=pool.digest,
            schedule_sha256=schedule.digest,
            qualification_source_sha256=qualification_source,
            completed_observations=tuple(observations),
            qualified_indices=tuple(qualified),
            current_context_index=current_index,
            current_arm=current_arm,
            known_public_highs_ds_invocation_count=known_calls,
            invocation_count_complete=False,
            exception_chain=_exception_chain(error),
        )


__all__ = [
    "ADR0323_NESTED_REVERSAL_ALLOWANCE",
    "ADR0323_OPPORTUNITY_FLOOR",
    "ADR0323_QUALIFICATION_AMBIGUITY_GUARD",
    "ADR0323_QUALIFICATION_TARGET",
    "ActionWidthQualificationArm",
    "ActionWidthQualificationCampaignResult",
    "ActionWidthQualificationClassification",
    "ActionWidthQualificationConsumerFailure",
    "ActionWidthQualificationObservation",
    "ActionWidthQualificationResult",
    "ActionWidthQualificationRunnerRejected",
    "ActionWidthQualificationSchedule",
    "ActionWidthQualificationStopReason",
    "ActionWidthQualificationTask",
    "CertifiedChipRegretInterval",
    "CertifiedChipValueInterval",
    "NestedValueReversalAllowance",
    "NormalizedOpportunityFloor",
    "QualificationAmbiguityGuard",
    "QualificationRunnerException",
    "QualificationRunnerStage",
    "QualifiedActionWidthDevelopmentPanel",
    "build_adr0323_qualification_schedule",
    "certified_full_minus_subset_regret",
    "classify_action_width_opportunity",
    "qualification_protocol_sha256",
    "qualification_requests_for_context",
    "run_adr0323_development_qualification",
    "verify_adr0323_qualification_source_and_dependencies",
    "verify_adr0324_structure_source_and_pool",
]
