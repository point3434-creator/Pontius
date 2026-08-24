"""Prospective width-three transfer-confirmation owner for ADR-0342.

The owner binds ADR-0338's already-selected context-local mechanism to
ADR-0341's exact untouched target panel.  The retained complete-universe and
anchored-width-two arms are immutable prior evidence; only the possible third
raise arms are prospective calls.  Importing, building, or synthetically
exercising this module opens no real confirmation value.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    CallerFallbackDispositionV2,
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    CertifiedSizingConsumerRejectionReasonV2,
    CertifiedSizingConsumerStageV2,
    KernelRaiseToTotal,
    LegalRaiseSetScope,
    ReducedSizingResponseModel,
    _bind_request,
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
)
from .certified_reduced_sizing_consumer_v2_seal import (
    ADR0321_CONSUMER_SOURCE_MANIFEST,
)
from .certified_reduced_sizing_highs import ADR0318_CERTIFIED_SIZING_ALLOWANCES
from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    JournalRecovery,
    canonical_journal_json_bytes,
    parse_journal_record_line,
    recover_journal_bytes,
)
from .fresh_action_width_greedy import (
    ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
    ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
    CertifiedGreedyTeacherExcessInterval,
    ClosedFiniteBlockCandidateEvidence,
    ClosedFiniteBlockTransition,
    ConservativeAggregateRecoveryInterval,
    GreedyCertifiedValueEvidence,
    GreedySubsetTask,
    GreedyWidthGateResult,
    NormalizedGreedyTeacherExcessInterval,
    OwnRaiseBlockIdentity,
    _expected_response_rows,
    _response_row_set_for_request,
    build_closed_finite_block_candidate,
    certified_greedy_teacher_excess,
    conservative_aggregate_recovery,
    normalize_full_regret,
    normalize_greedy_teacher_excess,
    select_greedy_candidate,
)
from .fresh_action_width_nonreplay_greedy_result import (
    ADR0338_GREEDY_RESULT_SHA256,
    ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH,
    verify_adr0338_greedy_result_source_and_dependencies,
)
from .fresh_action_width_nonreplay_qualification import (
    QualificationArmEvidence,
    QualificationEvidenceKind,
    _ACCEPTED_RESULT_KEYS,
    _REJECTED_RESULT_KEYS,
    _UNEXPECTED_RESULT_KEYS,
    _accepted_result_payload,
    _exception_payload,
    _fraction_policy_payload,
    _rebind_real_accepted_value_witness,
    _rejected_result_payload,
    _require_exact_keys,
    _require_float_hex,
    _validate_exception_chain,
    _validate_fraction_policy,
)
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    certified_full_minus_subset_regret,
)
from .fresh_action_width_teacher import (
    ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    NormalizedTeacherRegretInterval,
    TeacherSubsetCandidate,
    TeacherWidthEnvelope,
    reduce_teacher_width,
)
from .fresh_action_width_transfer_qualification import (
    build_adr0340_transfer_qualification_schedule,
)
from .fresh_action_width_transfer_qualification_result import (
    ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
    ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
    verify_adr0341_transfer_qualification_result_artifact,
)
from .fresh_action_width_transfer_structures import (
    FreshActionWidthTransferPool,
    build_adr0339_transfer_pool,
)
from .fresh_action_width_transfer_structures_seal import (
    ADR0339_TRANSFER_POOL_SHA256,
)
from .fresh_action_width_structures import (
    ADR0323_PRIVATE_RANGE_WIDTH,
    FreshActionWidthContext,
    RaiseActionWidth,
)


ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-transfer-confirmation-v1.jsonl"
)
ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH = RaiseActionWidth(3)
ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT = 16
ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT = 32
ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT = 16
ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT = 126
ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT = 142
ADR0342_TRANSFER_CONFIRMATION_TRANSITION_COUNT = 126
ADR0342_TRANSFER_CONFIRMATION_COMPLETED_RECORD_COUNT = 128

_SCHEDULE_VERSION = "adr0342-transfer-confirmation-schedule-v1"
_EVIDENCE_VERSION = "adr0342-transfer-confirmation-evidence-v1"
_CAMPAIGN_VERSION = "adr0342-transfer-confirmation-campaign-v1"
_HEADER_VERSION = "adr0342-transfer-confirmation-header-v1"
_TERMINAL_VERSION = "adr0342-transfer-confirmation-terminal-v1"


def _require_digest(
    value: object,
    *,
    label: str,
    optional: bool = False,
) -> str | None:
    if optional and value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_count(
    value: object,
    *,
    label: str,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f"{label} lies outside its frozen range")
    return value


def _sealed_payload(
    core: Mapping[str, object],
    *,
    digest_field: str,
) -> dict[str, object]:
    if digest_field in core:
        raise ValueError("self-free core already contains its digest")
    return {
        **core,
        digest_field: sha256(canonical_journal_json_bytes(core)).hexdigest(),
    }


def _verify_sealed_payload(
    value: object,
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or digest_field not in value:
        raise ValueError(f"{label} lacks its digest")
    claimed = _require_digest(value[digest_field], label=f"{label} digest")
    core = {key: item for key, item in value.items() if key != digest_field}
    if sha256(canonical_journal_json_bytes(core)).hexdigest() != claimed:
        raise ValueError(f"{label} digest differs from its self-free core")
    return core


def _candidate_request(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    candidate_position: int,
    amounts: tuple[KernelRaiseToTotal, ...],
) -> CertifiedReducedSizingRequestV2:
    return CertifiedReducedSizingRequestV2(
        context_id=(
            f"{context.context_id}|transfer-confirmation|panel-{panel_position:02d}|"
            f"raise-width-3|candidate-{candidate_position:02d}"
        ),
        betting=context.betting,
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
        legal_raise_to_totals=amounts,
        joint_probabilities=context.joint_probabilities,
        showdown_signs=context.showdown_signs,
    )


def _candidate_task(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    pool_index: int,
    ordinal: int,
    candidate_position: int,
    amounts: tuple[KernelRaiseToTotal, ...],
) -> GreedySubsetTask:
    request = _candidate_request(
        context=context,
        panel_position=panel_position,
        candidate_position=candidate_position,
        amounts=amounts,
    )
    return GreedySubsetTask(
        ordinal=ordinal,
        panel_position=panel_position,
        pool_index=pool_index,
        context_semantic_digest=context.semantic_digest,
        raise_width=ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH,
        subset_index=candidate_position,
        request=request,
        response_row_set=_response_row_set_for_request(
            context_semantic_digest=context.semantic_digest,
            request=request,
        ),
    )


def _baseline_task(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    pool_index: int,
    request: CertifiedReducedSizingRequestV2,
) -> GreedySubsetTask:
    return GreedySubsetTask(
        ordinal=panel_position,
        panel_position=panel_position,
        pool_index=pool_index,
        context_semantic_digest=context.semantic_digest,
        raise_width=RaiseActionWidth(2),
        subset_index=0,
        request=request,
        response_row_set=_response_row_set_for_request(
            context_semantic_digest=context.semantic_digest,
            request=request,
        ),
    )


def _greedy_value_from_qualification(
    *,
    task: GreedySubsetTask,
    evidence: QualificationArmEvidence,
) -> GreedyCertifiedValueEvidence:
    if (
        evidence.kind is not QualificationEvidenceKind.ACCEPTED
        or evidence.synthetic
    ):
        raise ValueError("transfer prior baseline is not real accepted evidence")
    result = evidence.core["result"]
    if not isinstance(result, dict):
        raise TypeError("transfer prior baseline result is not an object")
    value = GreedyCertifiedValueEvidence(
        task_sha256=task.digest,
        request_sha256=result["request_sha256"],  # type: ignore[arg-type]
        public_state_sha256=result["public_state_sha256"],  # type: ignore[arg-type]
        legal_raise_set_sha256=result["legal_raise_set_sha256"],  # type: ignore[arg-type]
        linear_program_sha256=result["linear_program_sha256"],  # type: ignore[arg-type]
        response_row_set_sha256=task.response_row_set.digest,
        consumer_source_sha256=result["consumer_source_sha256"],  # type: ignore[arg-type]
        consumer_protocol_sha256=result["consumer_protocol_sha256"],  # type: ignore[arg-type]
        public_highs_ds_invocation_count=result["public_call_count"],  # type: ignore[arg-type]
        raise_to_totals=tuple(result["raise_to_totals"]),  # type: ignore[arg-type]
        reduced_bet_increments=tuple(result["reduced_bet_increments"]),  # type: ignore[arg-type]
        feasible_behavioral_lower_bound_chips=_require_float_hex(
            result["feasible_lower_hex"],
            label="transfer prior baseline lower",
        ),
        certified_upper_bound_chips=_require_float_hex(
            result["certified_upper_hex"],
            label="transfer prior baseline upper",
        ),
        signed_certificate_gap_chips=_require_float_hex(
            result["signed_gap_hex"],
            label="transfer prior baseline signed gap",
        ),
        certified_gap_chips=_require_float_hex(
            result["certified_gap_hex"],
            label="transfer prior baseline gap",
        ),
    )
    value.verify_task(task)
    return value


def _qualification_value(evidence: QualificationArmEvidence) -> CertifiedChipValueInterval:
    if (
        evidence.kind is not QualificationEvidenceKind.ACCEPTED
        or evidence.synthetic
    ):
        raise ValueError("transfer prior comparator is not real accepted evidence")
    result = evidence.core["result"]
    if not isinstance(result, dict):
        raise TypeError("transfer prior comparator result is not an object")
    return CertifiedChipValueInterval(
        lower_chips=_require_float_hex(
            result["feasible_lower_hex"],
            label="transfer prior full lower",
        ),
        upper_chips=_require_float_hex(
            result["certified_upper_hex"],
            label="transfer prior full upper",
        ),
    )


@dataclass(frozen=True, slots=True)
class TransferConfirmationPriorReference:
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    payoff_span_chips: int
    qualification_campaign_sha256: str
    qualification_panel_sha256: str
    qualification_journal_sha256: str
    qualification_terminal_sha256: str
    full_qualification_task_sha256: str
    full_evidence_sha256: str
    full_value: CertifiedChipValueInterval
    baseline_qualification_task_sha256: str
    baseline_evidence_sha256: str
    baseline_task: GreedySubsetTask
    baseline: GreedyCertifiedValueEvidence

    def __post_init__(self) -> None:
        panel = _require_count(
            self.panel_position,
            label="transfer prior panel position",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT - 1,
        )
        if (
            self.pool_index != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("transfer prior crosses target-panel membership")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("transfer prior payoff span is invalid")
        for label, value in (
            ("campaign", self.qualification_campaign_sha256),
            ("panel", self.qualification_panel_sha256),
            ("journal", self.qualification_journal_sha256),
            ("terminal", self.qualification_terminal_sha256),
            ("full task", self.full_qualification_task_sha256),
            ("full evidence", self.full_evidence_sha256),
            ("baseline qualification task", self.baseline_qualification_task_sha256),
            ("baseline evidence", self.baseline_evidence_sha256),
        ):
            _require_digest(value, label=f"transfer prior {label}")
        if (
            self.qualification_campaign_sha256
            != ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256
            or self.qualification_panel_sha256
            != ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256
            or self.qualification_journal_sha256
            != ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256
            or self.qualification_terminal_sha256
            != ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256
        ):
            raise ValueError("transfer prior belongs to another qualification chain")
        if not isinstance(self.full_value, CertifiedChipValueInterval):
            raise TypeError("transfer prior requires a certified full value")
        if (
            not isinstance(self.baseline_task, GreedySubsetTask)
            or self.baseline_task.panel_position != self.panel_position
            or self.baseline_task.pool_index != self.pool_index
            or self.baseline_task.context_semantic_digest
            != self.context_semantic_sha256
            or self.baseline_task.raise_width.count != 2
        ):
            raise ValueError("transfer prior baseline task identity drifted")
        if not isinstance(self.baseline, GreedyCertifiedValueEvidence):
            raise TypeError("transfer prior requires baseline value evidence")
        self.baseline.verify_task(self.baseline_task)

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "baseline_evidence_sha256": self.baseline_evidence_sha256,
                    "baseline_qualification_task_sha256": (
                        self.baseline_qualification_task_sha256
                    ),
                    "baseline_task_sha256": self.baseline_task.digest,
                    "baseline_value_sha256": self.baseline.digest,
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "full_evidence_sha256": self.full_evidence_sha256,
                    "full_qualification_task_sha256": (
                        self.full_qualification_task_sha256
                    ),
                    "full_value": (
                        self.full_value.lower_chips.hex(),
                        self.full_value.upper_chips.hex(),
                    ),
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "qualification_journal_sha256": (
                        self.qualification_journal_sha256
                    ),
                    "qualification_panel_sha256": self.qualification_panel_sha256,
                    "qualification_campaign_sha256": (
                        self.qualification_campaign_sha256
                    ),
                    "qualification_terminal_sha256": (
                        self.qualification_terminal_sha256
                    ),
                    "version": "adr0342-transfer-confirmation-prior-reference-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class TransferConfirmationCallSlot:
    call_index: int
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    candidate_position: int

    def __post_init__(self) -> None:
        _require_count(
            self.call_index,
            label="transfer confirmation call index",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT - 1,
        )
        panel = _require_count(
            self.panel_position,
            label="transfer confirmation panel position",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT - 1,
        )
        if (
            self.pool_index != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("transfer confirmation slot crosses panel membership")
        _require_count(
            self.candidate_position,
            label="transfer confirmation candidate position",
        )

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "call_index": self.call_index,
                    "candidate_position": self.candidate_position,
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "panel_position": self.panel_position,
                    "pool_index": self.pool_index,
                    "raise_width": 3,
                    "version": "adr0342-transfer-confirmation-call-slot-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class TransferConfirmationSchedule:
    pool_sha256: str
    development_result_sha256: str
    qualification_panel_sha256: str
    prior_references: tuple[TransferConfirmationPriorReference, ...]
    tasks: tuple[GreedySubsetTask, ...]
    transitions: tuple[ClosedFiniteBlockTransition, ...]
    call_slots: tuple[TransferConfirmationCallSlot, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("pool", self.pool_sha256),
            ("development result", self.development_result_sha256),
            ("qualification panel", self.qualification_panel_sha256),
        ):
            _require_digest(value, label=f"transfer confirmation {label}")
        if (
            self.pool_sha256 != ADR0339_TRANSFER_POOL_SHA256
            or self.development_result_sha256 != ADR0338_GREEDY_RESULT_SHA256
            or self.qualification_panel_sha256
            != ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256
        ):
            raise ValueError("transfer confirmation schedule crossed its evidence chain")
        if (
            not isinstance(self.prior_references, tuple)
            or len(self.prior_references)
            != ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT
            or any(
                not isinstance(item, TransferConfirmationPriorReference)
                for item in self.prior_references
            )
            or tuple(item.panel_position for item in self.prior_references)
            != tuple(range(ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT))
        ):
            raise ValueError("transfer confirmation priors are incomplete")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT
            or any(not isinstance(item, GreedySubsetTask) for item in self.tasks)
            or tuple(item.ordinal for item in self.tasks)
            != tuple(range(ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT))
            or len({item.digest for item in self.tasks}) != len(self.tasks)
        ):
            raise ValueError("transfer confirmation task inventory drifted")
        baselines = self.tasks[:ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT]
        if baselines != tuple(item.baseline_task for item in self.prior_references):
            raise ValueError("transfer confirmation baselines differ from prior evidence")
        candidates = self.tasks[ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT:]
        if (
            len(candidates) != ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
            or any(item.raise_width.count != 3 for item in candidates)
        ):
            raise ValueError("transfer confirmation candidate task count drifted")
        if (
            not isinstance(self.transitions, tuple)
            or len(self.transitions) != ADR0342_TRANSFER_CONFIRMATION_TRANSITION_COUNT
            or any(
                not isinstance(item, ClosedFiniteBlockTransition)
                for item in self.transitions
            )
            or tuple(item.ordinal for item in self.transitions)
            != tuple(range(ADR0342_TRANSFER_CONFIRMATION_TRANSITION_COUNT))
            or tuple(item.augmented for item in self.transitions) != candidates
        ):
            raise ValueError("transfer confirmation transition inventory drifted")
        if (
            not isinstance(self.call_slots, tuple)
            or len(self.call_slots)
            != ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
            or tuple(item.call_index for item in self.call_slots)
            != tuple(range(ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT))
            or len({item.digest for item in self.call_slots})
            != ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
        ):
            raise ValueError("transfer confirmation call-slot inventory drifted")
        pool = build_adr0339_transfer_pool()
        for panel_position, prior in enumerate(self.prior_references):
            outgoing = self.transitions_for_context(panel_position)
            complete = pool.contexts[prior.pool_index].complete_raise_to_totals
            omitted = complete[1:-1]
            if (
                tuple(item.incumbent for item in outgoing)
                != (prior.baseline_task,) * len(outgoing)
                or tuple(item.proposed_raise_to_total for item in outgoing) != omitted
                or tuple(item.candidate_position for item in outgoing)
                != tuple(range(len(omitted)))
            ):
                raise ValueError("transfer confirmation omitted-raise order drifted")
            context_slots = self.call_slots_for_context(panel_position)
            if (
                tuple(item.candidate_position for item in context_slots)
                != tuple(range(len(omitted)))
                or tuple(item.pool_index for item in context_slots)
                != (prior.pool_index,) * len(omitted)
            ):
                raise ValueError("transfer confirmation context slots drifted")

    @property
    def candidate_tasks(self) -> tuple[GreedySubsetTask, ...]:
        return self.tasks[ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT:]

    def transitions_for_context(
        self,
        panel_position: int,
    ) -> tuple[ClosedFiniteBlockTransition, ...]:
        _require_count(
            panel_position,
            label="transfer confirmation transition lookup",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT - 1,
        )
        return tuple(
            item
            for item in self.transitions
            if item.incumbent.panel_position == panel_position
        )

    def call_slots_for_context(
        self,
        panel_position: int,
    ) -> tuple[TransferConfirmationCallSlot, ...]:
        _require_count(
            panel_position,
            label="transfer confirmation slot lookup",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT - 1,
        )
        return tuple(
            item for item in self.call_slots if item.panel_position == panel_position
        )

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "call_slot_sha256s": tuple(item.digest for item in self.call_slots),
                    "candidate_call_count": (
                        ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
                    ),
                    "development_result_sha256": self.development_result_sha256,
                    "prior_arm_count": ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT,
                    "prior_reference_sha256s": tuple(
                        item.digest for item in self.prior_references
                    ),
                    "qualification_panel_sha256": self.qualification_panel_sha256,
                    "raise_width": 3,
                    "task_sha256s": tuple(item.digest for item in self.tasks),
                    "transition_sha256s": tuple(
                        item.digest for item in self.transitions
                    ),
                    "pool_sha256": self.pool_sha256,
                    "version": _SCHEDULE_VERSION,
                }
            )
        ).hexdigest()


def build_adr0342_transfer_confirmation_schedule() -> TransferConfirmationSchedule:
    """Bind the frozen mechanism and exact prior evidence without solving."""

    retained = verify_adr0341_transfer_qualification_result_artifact()
    pool = build_adr0339_transfer_pool()
    qualification_schedule = build_adr0340_transfer_qualification_schedule()
    if (
        ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH
        != ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH.count
        or retained.panel.digest != ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256
        or pool.digest != ADR0339_TRANSFER_POOL_SHA256
    ):
        raise RuntimeError("transfer confirmation inherited evidence drifted")

    priors: list[TransferConfirmationPriorReference] = []
    baselines: list[GreedySubsetTask] = []
    for panel_position, pool_index in enumerate(retained.panel.qualified_indices):
        context = pool.contexts[pool_index]
        full_task = qualification_schedule.tasks[2 * pool_index]
        baseline_qualification_task = qualification_schedule.tasks[2 * pool_index + 1]
        full_evidence = retained.journal.evidences[2 * pool_index]
        baseline_evidence = retained.journal.evidences[2 * pool_index + 1]
        baseline_task = _baseline_task(
            context=context,
            panel_position=panel_position,
            pool_index=pool_index,
            request=baseline_qualification_task.request,
        )
        baseline_value = _greedy_value_from_qualification(
            task=baseline_task,
            evidence=baseline_evidence,
        )
        priors.append(
            TransferConfirmationPriorReference(
                panel_position=panel_position,
                pool_index=pool_index,
                context_semantic_sha256=context.semantic_digest,
                payoff_span_chips=context.payoff_span_chips,
                qualification_campaign_sha256=(
                    ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256
                ),
                qualification_panel_sha256=retained.panel.digest,
                qualification_journal_sha256=retained.journal.journal_sha256,
                qualification_terminal_sha256=retained.journal.terminal_sha256,
                full_qualification_task_sha256=full_task.digest,
                full_evidence_sha256=full_evidence.digest,
                full_value=_qualification_value(full_evidence),
                baseline_qualification_task_sha256=(
                    baseline_qualification_task.digest
                ),
                baseline_evidence_sha256=baseline_evidence.digest,
                baseline_task=baseline_task,
                baseline=baseline_value,
            )
        )
        baselines.append(baseline_task)

    candidates: list[GreedySubsetTask] = []
    transitions: list[ClosedFiniteBlockTransition] = []
    slots: list[TransferConfirmationCallSlot] = []
    for panel_position, prior in enumerate(priors):
        context = pool.contexts[prior.pool_index]
        baseline = prior.baseline_task
        for candidate_position, proposed in enumerate(
            context.complete_raise_to_totals[1:-1]
        ):
            amounts = (
                context.complete_raise_to_totals[0],
                proposed,
                context.complete_raise_to_totals[-1],
            )
            task = _candidate_task(
                context=context,
                panel_position=panel_position,
                pool_index=prior.pool_index,
                ordinal=(
                    ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT
                    + len(candidates)
                ),
                candidate_position=candidate_position,
                amounts=amounts,
            )
            proposed_index = task.request.legal_raise_to_totals.index(proposed)
            increment = task.response_row_set.reduced_bet_increments[proposed_index]
            transition = ClosedFiniteBlockTransition(
                ordinal=len(transitions),
                candidate_position=candidate_position,
                incumbent=baseline,
                augmented=task,
                proposed_raise_to_total=proposed,
                proposed_reduced_bet_increment=increment,
                own_block=OwnRaiseBlockIdentity(
                    context_semantic_digest=context.semantic_digest,
                    raise_to_total=proposed,
                    reduced_bet_increment=increment,
                    responder_private_range_width=ADR0323_PRIVATE_RANGE_WIDTH,
                    response_rows=_expected_response_rows(
                        context_semantic_digest=context.semantic_digest,
                        raise_to_totals=(proposed,),
                        reduced_bet_increments=(increment,),
                        responder_private_range_width=(
                            ADR0323_PRIVATE_RANGE_WIDTH
                        ),
                    ),
                ),
                phase_order=ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
            )
            slot = TransferConfirmationCallSlot(
                call_index=len(slots),
                panel_position=panel_position,
                pool_index=prior.pool_index,
                context_semantic_sha256=context.semantic_digest,
                candidate_position=candidate_position,
            )
            candidates.append(task)
            transitions.append(transition)
            slots.append(slot)

    return TransferConfirmationSchedule(
        pool_sha256=pool.digest,
        development_result_sha256=ADR0338_GREEDY_RESULT_SHA256,
        qualification_panel_sha256=retained.panel.digest,
        prior_references=tuple(priors),
        tasks=tuple((*baselines, *candidates)),
        transitions=tuple(transitions),
        call_slots=tuple(slots),
    )


class TransferConfirmationEvidenceKind(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


_EVIDENCE_CORE_KEYS = frozenset(
    {
        "call_index",
        "candidate_position",
        "context_semantic_sha256",
        "kind",
        "panel_position",
        "pool_index",
        "raise_width",
        "result",
        "slot_sha256",
        "synthetic",
        "task_sha256",
        "transition_sha256",
        "version",
    }
)


@dataclass(frozen=True, slots=True)
class TransferConfirmationArmEvidence:
    call_index: int
    slot_sha256: str
    task_sha256: str
    transition_sha256: str
    kind: TransferConfirmationEvidenceKind
    synthetic: bool
    core_canonical_json: bytes

    def __post_init__(self) -> None:
        _require_count(
            self.call_index,
            label="transfer confirmation evidence call index",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT - 1,
        )
        for label, value in (
            ("slot", self.slot_sha256),
            ("task", self.task_sha256),
            ("transition", self.transition_sha256),
        ):
            _require_digest(value, label=f"transfer confirmation evidence {label}")
        if not isinstance(self.kind, TransferConfirmationEvidenceKind):
            raise TypeError("transfer confirmation evidence kind must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("transfer confirmation evidence synthetic flag must be Boolean")
        if not isinstance(self.core_canonical_json, bytes):
            raise TypeError("transfer confirmation evidence core must be immutable")
        value = json.loads(self.core_canonical_json)
        if (
            not isinstance(value, dict)
            or frozenset(value) != _EVIDENCE_CORE_KEYS
            or canonical_journal_json_bytes(value) != self.core_canonical_json
        ):
            raise ValueError("transfer confirmation evidence core is not canonical")
        if (
            value.get("call_index") != self.call_index
            or value.get("slot_sha256") != self.slot_sha256
            or value.get("task_sha256") != self.task_sha256
            or value.get("transition_sha256") != self.transition_sha256
            or value.get("kind") != self.kind.value
            or value.get("synthetic") is not self.synthetic
            or value.get("version") != _EVIDENCE_VERSION
        ):
            raise ValueError("transfer confirmation metadata differs from its core")

    @property
    def core(self) -> dict[str, object]:
        value = json.loads(self.core_canonical_json)
        if not isinstance(value, dict):
            raise AssertionError("transfer confirmation core lost its object type")
        return value

    @property
    def digest(self) -> str:
        return sha256(self.core_canonical_json).hexdigest()

    @property
    def journal_payload(self) -> dict[str, object]:
        return {**self.core, "evidence_sha256": self.digest}

    @property
    def public_call_count(self) -> int:
        result = self.core["result"]
        if not isinstance(result, dict):
            raise AssertionError("transfer confirmation result lost its object type")
        if self.kind is TransferConfirmationEvidenceKind.UNEXPECTED_EXCEPTION:
            return 0
        return _require_count(
            result["public_call_count"],
            label="transfer confirmation evidence public calls",
            maximum=1,
        )

    @property
    def invocation_count_complete(self) -> bool:
        return self.kind is not TransferConfirmationEvidenceKind.UNEXPECTED_EXCEPTION

    def accepted_value(self, task: GreedySubsetTask) -> GreedyCertifiedValueEvidence:
        if self.kind is not TransferConfirmationEvidenceKind.ACCEPTED:
            raise ValueError("only accepted transfer confirmation evidence has a value")
        result = self.core["result"]
        if not isinstance(result, dict):
            raise AssertionError("accepted transfer confirmation result is not an object")
        evidence = GreedyCertifiedValueEvidence(
            task_sha256=task.digest,
            request_sha256=result["request_sha256"],  # type: ignore[arg-type]
            public_state_sha256=result["public_state_sha256"],  # type: ignore[arg-type]
            legal_raise_set_sha256=result["legal_raise_set_sha256"],  # type: ignore[arg-type]
            linear_program_sha256=result["linear_program_sha256"],  # type: ignore[arg-type]
            response_row_set_sha256=task.response_row_set.digest,
            consumer_source_sha256=result["consumer_source_sha256"],  # type: ignore[arg-type]
            consumer_protocol_sha256=result["consumer_protocol_sha256"],  # type: ignore[arg-type]
            public_highs_ds_invocation_count=result["public_call_count"],  # type: ignore[arg-type]
            raise_to_totals=tuple(result["raise_to_totals"]),  # type: ignore[arg-type]
            reduced_bet_increments=tuple(result["reduced_bet_increments"]),  # type: ignore[arg-type]
            feasible_behavioral_lower_bound_chips=_require_float_hex(
                result["feasible_lower_hex"],
                label="transfer confirmation accepted lower",
            ),
            certified_upper_bound_chips=_require_float_hex(
                result["certified_upper_hex"],
                label="transfer confirmation accepted upper",
            ),
            signed_certificate_gap_chips=_require_float_hex(
                result["signed_gap_hex"],
                label="transfer confirmation accepted signed gap",
            ),
            certified_gap_chips=_require_float_hex(
                result["certified_gap_hex"],
                label="transfer confirmation accepted gap",
            ),
        )
        evidence.verify_task(task)
        return evidence


def _build_evidence(
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    kind: TransferConfirmationEvidenceKind,
    synthetic: bool,
    result_payload: Mapping[str, object],
) -> TransferConfirmationArmEvidence:
    if not isinstance(slot, TransferConfirmationCallSlot):
        raise TypeError("transfer confirmation evidence requires a call slot")
    if not isinstance(task, GreedySubsetTask):
        raise TypeError("transfer confirmation evidence requires a semantic task")
    if not isinstance(transition, ClosedFiniteBlockTransition):
        raise TypeError("transfer confirmation evidence requires a transition")
    core = {
        "call_index": slot.call_index,
        "candidate_position": slot.candidate_position,
        "context_semantic_sha256": task.context_semantic_digest,
        "kind": kind.value,
        "panel_position": task.panel_position,
        "pool_index": task.pool_index,
        "raise_width": task.raise_width.count,
        "result": result_payload,
        "slot_sha256": slot.digest,
        "synthetic": synthetic,
        "task_sha256": task.digest,
        "transition_sha256": transition.digest,
        "version": _EVIDENCE_VERSION,
    }
    return TransferConfirmationArmEvidence(
        call_index=slot.call_index,
        slot_sha256=slot.digest,
        task_sha256=task.digest,
        transition_sha256=transition.digest,
        kind=kind,
        synthetic=synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )


def transfer_confirmation_evidence_from_consumer_result(
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    result: object,
) -> TransferConfirmationArmEvidence:
    if isinstance(result, CertifiedReducedSizingAcceptedV2):
        if result.request != task.request:
            raise ValueError("accepted transfer confirmation belongs to another task")
        return _build_evidence(
            slot=slot,
            task=task,
            transition=transition,
            kind=TransferConfirmationEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=_accepted_result_payload(result),
        )
    if isinstance(result, CertifiedReducedSizingRejectedV2):
        if result.request != task.request:
            raise ValueError("rejected transfer confirmation belongs to another task")
        return _build_evidence(
            slot=slot,
            task=task,
            transition=transition,
            kind=TransferConfirmationEvidenceKind.REJECTED,
            synthetic=False,
            result_payload=_rejected_result_payload(result),
        )
    raise TypeError("transfer confirmation consumer returned a nonsemantic result")


def _unexpected_evidence(
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    error: Exception,
    synthetic: bool,
) -> TransferConfirmationArmEvidence:
    return _build_evidence(
        slot=slot,
        task=task,
        transition=transition,
        kind=TransferConfirmationEvidenceKind.UNEXPECTED_EXCEPTION,
        synthetic=synthetic,
        result_payload={
            "exception_chain": _exception_payload(error),
            "invocation_count_complete": False,
            "synthetic_result": synthetic,
            "type": "unexpected_exception",
        },
    )


def _validate_evidence_against_invocation(
    evidence: TransferConfirmationArmEvidence,
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    expect_synthetic: bool,
) -> None:
    core = evidence.core
    if (
        evidence.call_index != slot.call_index
        or evidence.slot_sha256 != slot.digest
        or evidence.task_sha256 != task.digest
        or evidence.transition_sha256 != transition.digest
        or evidence.synthetic is not expect_synthetic
        or core["candidate_position"] != slot.candidate_position
        or core["panel_position"] != task.panel_position
        or core["pool_index"] != task.pool_index
        or core["context_semantic_sha256"] != task.context_semantic_digest
        or core["raise_width"] != 3
        or transition.augmented != task
        or transition.candidate_position != slot.candidate_position
    ):
        raise ValueError("transfer confirmation evidence crossed its invocation")
    result = core["result"]
    if not isinstance(result, dict):
        raise TypeError("transfer confirmation evidence result must be an object")
    if result.get("synthetic_result") is not expect_synthetic:
        raise ValueError("transfer confirmation synthetic provenance drifted")

    if evidence.kind is TransferConfirmationEvidenceKind.ACCEPTED:
        accepted = _require_exact_keys(
            result,
            _ACCEPTED_RESULT_KEYS,
            label="accepted transfer confirmation evidence",
        )
        bound = _bind_request(task.request)
        if (
            accepted["type"] != "accepted"
            or accepted["context_label"] != task.request.context_id
            or accepted["response_model"] != task.request.response_model.value
            or accepted["legal_raise_scope"] != task.request.legal_raise_scope.value
            or accepted["request_sha256"] != bound.request_sha256
            or accepted["public_state_sha256"] != bound.public_state_sha256
            or accepted["legal_raise_set_sha256"] != bound.legal_raise_set_sha256
            or accepted["linear_program_sha256"] != bound.linear_program_sha256
            or accepted["consumer_protocol_sha256"]
            != ADR0321_CONSUMER_PROTOCOL_SHA256
            or accepted["consumer_source_sha256"]
            != ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ]
            or accepted["public_call_count"] != 1
            or accepted["raise_to_totals"]
            != [item.chips for item in bound.legal_raise_to_totals]
            or accepted["reduced_bet_increments"]
            != [item.chips for item in bound.reduced_bet_increments]
            or accepted["fallback_disposition"]
            != CallerFallbackDispositionV2.NOT_REQUIRED_RESEARCH_RESULT.value
            or accepted["emitted_action"] is not None
        ):
            raise ValueError("accepted transfer confirmation identity drifted")
        lower = _require_float_hex(
            accepted["feasible_lower_hex"],
            label="accepted transfer confirmation lower",
        )
        upper = _require_float_hex(
            accepted["certified_upper_hex"],
            label="accepted transfer confirmation upper",
        )
        signed_gap = _require_float_hex(
            accepted["signed_gap_hex"],
            label="accepted transfer confirmation signed gap",
        )
        gap = _require_float_hex(
            accepted["certified_gap_hex"],
            label="accepted transfer confirmation gap",
        )
        if (
            lower > upper
            or signed_gap != upper - lower
            or gap != max(0.0, signed_gap)
        ):
            raise ValueError("accepted transfer confirmation interval drifted")
        policy = _validate_fraction_policy(
            accepted["exact_opening_policy"],
            row_count=len(task.request.joint_probabilities),
            action_count=1 + len(task.request.legal_raise_to_totals),
        )
        actions = accepted["responder_best_actions"]
        if (
            not isinstance(actions, list)
            or len(actions) != len(task.request.joint_probabilities[0])
            or any(
                not isinstance(row, list)
                or len(row) != len(task.request.legal_raise_to_totals)
                or any(action not in {"fold", "call"} for action in row)
                for row in actions
            )
        ):
            raise ValueError("accepted transfer confirmation response witness is malformed")
        multiplier_values = accepted["raw_inequality_multipliers_hex"]
        if not isinstance(multiplier_values, list):
            raise TypeError("accepted transfer confirmation multipliers must be an array")
        multipliers = tuple(
            _require_float_hex(item, label="accepted transfer confirmation multiplier")
            for item in multiplier_values
        )
        expected_multiplier_count = (
            2 * len(task.request.joint_probabilities)
            + 2
            * len(task.request.joint_probabilities[0])
            * len(task.request.legal_raise_to_totals)
        )
        if len(multipliers) != expected_multiplier_count:
            raise ValueError("accepted transfer confirmation multiplier width drifted")
        if not expect_synthetic:
            _rebind_real_accepted_value_witness(  # type: ignore[arg-type]
                task=task,
                accepted=accepted,
                policy=policy,
                multipliers=multipliers,
                lower=lower,
                upper=upper,
            )
            allowances = ADR0318_CERTIFIED_SIZING_ALLOWANCES
            if (
                signed_gap < -allowances.certificate_reversal.chips
                or signed_gap > allowances.certificate_width.chips
            ):
                raise ValueError("accepted transfer confirmation certificate width drifted")
        evidence.accepted_value(task)
    elif evidence.kind is TransferConfirmationEvidenceKind.REJECTED:
        rejected = _require_exact_keys(
            result,
            _REJECTED_RESULT_KEYS,
            label="rejected transfer confirmation evidence",
        )
        if (
            rejected["type"] != "rejected"
            or rejected["context_label"] != task.request.context_id
            or rejected["consumer_protocol_sha256"]
            != ADR0321_CONSUMER_PROTOCOL_SHA256
            or rejected["stage"]
            not in {item.value for item in CertifiedSizingConsumerStageV2}
            or rejected["reason"]
            not in {item.value for item in CertifiedSizingConsumerRejectionReasonV2}
            or rejected["fallback_disposition"]
            != CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            or rejected["emitted_action"] is not None
        ):
            raise ValueError("rejected transfer confirmation identity drifted")
        calls = _require_count(
            rejected["public_call_count"],
            label="rejected transfer confirmation public calls",
            maximum=1,
        )
        for key in (
            "consumer_source_sha256",
            "legal_raise_set_sha256",
            "public_state_sha256",
            "request_sha256",
        ):
            _require_digest(
                rejected[key],
                label=f"rejected transfer confirmation {key}",
                optional=True,
            )
        _validate_exception_chain(
            rejected["exception_chain"],
            label="rejected transfer confirmation evidence",
        )
        stage = CertifiedSizingConsumerStageV2(rejected["stage"])
        reason = CertifiedSizingConsumerRejectionReasonV2(rejected["reason"])
        expected_reason = {
            CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION: (
                CertifiedSizingConsumerRejectionReasonV2.SOURCE_DRIFT
            ),
            CertifiedSizingConsumerStageV2.RUNTIME_VERIFICATION: (
                CertifiedSizingConsumerRejectionReasonV2.RUNTIME_DRIFT
            ),
            CertifiedSizingConsumerStageV2.BACKEND_SELECTION: (
                CertifiedSizingConsumerRejectionReasonV2.BACKEND_UNAVAILABLE
            ),
            CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER: (
                CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED
            ),
            CertifiedSizingConsumerStageV2.RESULT_BINDING: (
                CertifiedSizingConsumerRejectionReasonV2.RESULT_BINDING_FAILED
            ),
        }
        if stage not in expected_reason or reason is not expected_reason[stage]:
            raise ValueError("rejected transfer confirmation stage/reason drifted")
        bound = _bind_request(task.request)
        if (
            rejected["request_sha256"] != bound.request_sha256
            or rejected["public_state_sha256"] != bound.public_state_sha256
            or rejected["legal_raise_set_sha256"] != bound.legal_raise_set_sha256
        ):
            raise ValueError("rejected transfer confirmation request identity drifted")
        source_expected = stage is not CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION
        if rejected["consumer_source_sha256"] != (
            ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ]
            if source_expected
            else None
        ):
            raise ValueError("rejected transfer confirmation source identity drifted")
        expected_calls = (
            1
            if stage
            in {
                CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER,
                CertifiedSizingConsumerStageV2.RESULT_BINDING,
            }
            else 0
        )
        if calls != expected_calls:
            raise ValueError("rejected transfer confirmation invocation count drifted")
    else:
        unexpected = _require_exact_keys(
            result,
            _UNEXPECTED_RESULT_KEYS,
            label="unexpected transfer confirmation evidence",
        )
        if (
            unexpected["type"] != "unexpected_exception"
            or unexpected["invocation_count_complete"] is not False
        ):
            raise ValueError("unexpected transfer confirmation claims complete calls")
        _validate_exception_chain(
            unexpected["exception_chain"],
            label="unexpected transfer confirmation evidence",
        )


def _rebind_evidence(
    payload: dict[str, object],
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    expect_synthetic: bool,
) -> TransferConfirmationArmEvidence:
    core = _verify_sealed_payload(
        payload,
        digest_field="evidence_sha256",
        label="transfer confirmation observation",
    )
    call_index = _require_count(
        core.get("call_index"),
        label="transfer confirmation observation call index",
        maximum=ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT - 1,
    )
    if call_index != slot.call_index:
        raise ValueError("transfer confirmation observation crossed its call slot")
    try:
        kind = TransferConfirmationEvidenceKind(core["kind"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("transfer confirmation evidence has an unknown kind") from error
    evidence = TransferConfirmationArmEvidence(
        call_index=call_index,
        slot_sha256=slot.digest,
        task_sha256=task.digest,
        transition_sha256=transition.digest,
        kind=kind,
        synthetic=expect_synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )
    _validate_evidence_against_invocation(
        evidence,
        slot=slot,
        task=task,
        transition=transition,
        expect_synthetic=expect_synthetic,
    )
    return evidence


def synthetic_transfer_confirmation_accepted_evidence(
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
    lower_chips: float,
    upper_chips: float,
) -> TransferConfirmationArmEvidence:
    """Build fake accepted evidence without a consumer or solver call."""

    lower = float(lower_chips)
    upper = float(upper_chips)
    if not isfinite(lower) or not isfinite(upper) or lower > upper:
        raise ValueError("synthetic transfer confirmation endpoints are invalid")
    bound = _bind_request(task.request)
    action_count = 1 + len(bound.legal_raise_to_totals)
    policy = tuple(
        tuple(Fraction(1, action_count) for _ in range(action_count))
        for _ in task.request.joint_probabilities
    )
    responses = tuple(
        tuple("fold" for _ in bound.legal_raise_to_totals)
        for _ in task.request.joint_probabilities[0]
    )
    multiplier_count = (
        2 * len(task.request.joint_probabilities)
        + 2
        * len(task.request.joint_probabilities[0])
        * len(bound.legal_raise_to_totals)
    )
    signed_gap = upper - lower
    return _build_evidence(
        slot=slot,
        task=task,
        transition=transition,
        kind=TransferConfirmationEvidenceKind.ACCEPTED,
        synthetic=True,
        result_payload={
            "certified_gap_hex": max(0.0, signed_gap).hex(),
            "certified_upper_hex": upper.hex(),
            "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
            "consumer_source_sha256": ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ],
            "context_label": task.request.context_id,
            "emitted_action": None,
            "exact_opening_policy": _fraction_policy_payload(policy),
            "fallback_disposition": (
                CallerFallbackDispositionV2.NOT_REQUIRED_RESEARCH_RESULT.value
            ),
            "feasible_lower_hex": lower.hex(),
            "legal_raise_scope": task.request.legal_raise_scope.value,
            "legal_raise_set_sha256": bound.legal_raise_set_sha256,
            "linear_program_sha256": bound.linear_program_sha256,
            "public_call_count": 1,
            "public_state_sha256": bound.public_state_sha256,
            "raw_inequality_multipliers_hex": tuple(
                0.0.hex() for _ in range(multiplier_count)
            ),
            "raise_to_totals": tuple(
                item.chips for item in bound.legal_raise_to_totals
            ),
            "reduced_bet_increments": tuple(
                item.chips for item in bound.reduced_bet_increments
            ),
            "request_sha256": bound.request_sha256,
            "responder_best_actions": responses,
            "response_model": task.request.response_model.value,
            "signed_gap_hex": signed_gap.hex(),
            "synthetic_result": True,
            "type": "accepted",
        },
    )


def synthetic_transfer_confirmation_rejected_evidence(
    *,
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
) -> TransferConfirmationArmEvidence:
    bound = _bind_request(task.request)
    return _build_evidence(
        slot=slot,
        task=task,
        transition=transition,
        kind=TransferConfirmationEvidenceKind.REJECTED,
        synthetic=True,
        result_payload={
            "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
            "consumer_source_sha256": ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ],
            "context_label": task.request.context_id,
            "emitted_action": None,
            "exception_chain": (
                {
                    "message": "synthetic transfer confirmation rejection",
                    "module": "pontius.synthetic",
                    "type_name": "SyntheticTransferConfirmationRejection",
                },
            ),
            "fallback_disposition": (
                CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            ),
            "legal_raise_set_sha256": bound.legal_raise_set_sha256,
            "public_call_count": 1,
            "public_state_sha256": bound.public_state_sha256,
            "reason": CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED.value,
            "request_sha256": bound.request_sha256,
            "stage": CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER.value,
            "synthetic_result": True,
            "type": "rejected",
        },
    )


@dataclass(frozen=True, slots=True)
class TransferConfirmationContextResult:
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    payoff_span_chips: int
    prior: TransferConfirmationPriorReference
    candidate_evidence_sha256s: tuple[str, ...]
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]
    selected_candidate_position: int
    teacher: TeacherWidthEnvelope
    full_regret: CertifiedChipRegretInterval
    normalized_full_regret: NormalizedTeacherRegretInterval
    teacher_excess: CertifiedGreedyTeacherExcessInterval
    normalized_teacher_excess: NormalizedGreedyTeacherExcessInterval

    def __post_init__(self) -> None:
        panel = _require_count(
            self.panel_position,
            label="transfer confirmation context panel position",
            maximum=ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT - 1,
        )
        if (
            self.pool_index != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("transfer confirmation context crosses panel membership")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("transfer confirmation payoff span is invalid")
        if (
            not isinstance(self.prior, TransferConfirmationPriorReference)
            or self.prior.panel_position != self.panel_position
            or self.prior.pool_index != self.pool_index
            or self.prior.context_semantic_sha256
            != self.context_semantic_sha256
            or self.prior.payoff_span_chips != self.payoff_span_chips
        ):
            raise ValueError("transfer confirmation context prior drifted")
        if (
            not isinstance(self.candidates, tuple)
            or not self.candidates
            or any(
                not isinstance(item, ClosedFiniteBlockCandidateEvidence)
                for item in self.candidates
            )
            or tuple(item.transition.candidate_position for item in self.candidates)
            != tuple(range(len(self.candidates)))
            or any(
                item.transition.incumbent != self.prior.baseline_task
                or item.incumbent_value_sha256 != self.prior.baseline.digest
                or item.transition.augmented.raise_width.count != 3
                for item in self.candidates
            )
        ):
            raise ValueError("transfer confirmation candidate set is incomplete")
        if (
            not isinstance(self.candidate_evidence_sha256s, tuple)
            or len(self.candidate_evidence_sha256s) != len(self.candidates)
        ):
            raise ValueError("transfer confirmation candidate receipts are incomplete")
        for digest in self.candidate_evidence_sha256s:
            _require_digest(digest, label="transfer confirmation candidate evidence")
        selected = select_greedy_candidate(self.candidates)
        position = _require_count(
            self.selected_candidate_position,
            label="transfer confirmation selected position",
            maximum=len(self.candidates) - 1,
        )
        if self.candidates[position] != selected:
            raise ValueError("transfer confirmation changed the frozen selection rule")
        teacher_candidates = tuple(
            TeacherSubsetCandidate(
                subset_index=item.transition.candidate_position,
                raise_to_totals=item.transition.augmented.raise_to_totals,
                value=item.augmented.value,
            )
            for item in self.candidates
        )
        expected_teacher = reduce_teacher_width(
            teacher_candidates,
            raise_width=ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH,
            equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
        )
        if self.teacher != expected_teacher:
            raise ValueError("transfer confirmation teacher envelope drifted")
        expected_full = certified_full_minus_subset_regret(
            full=self.prior.full_value,
            subset=selected.augmented.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_normalized_full = normalize_full_regret(
            expected_full,
            payoff_span_chips=self.payoff_span_chips,
        )
        expected_excess = certified_greedy_teacher_excess(
            teacher=self.teacher.value,
            greedy=selected.augmented.value,
        )
        expected_normalized_excess = normalize_greedy_teacher_excess(
            expected_excess,
            payoff_span_chips=self.payoff_span_chips,
        )
        if (
            self.full_regret != expected_full
            or self.normalized_full_regret != expected_normalized_full
            or self.teacher_excess != expected_excess
            or self.normalized_teacher_excess != expected_normalized_excess
        ):
            raise ValueError("transfer confirmation context metrics drifted")

    @property
    def selected(self) -> ClosedFiniteBlockCandidateEvidence:
        return self.candidates[self.selected_candidate_position]

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "candidate_evidence_sha256s": self.candidate_evidence_sha256s,
                    "candidate_sha256s": tuple(item.digest for item in self.candidates),
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "full_regret": (
                        self.full_regret.nonnegative_lower_chips.hex(),
                        self.full_regret.nonnegative_upper_chips.hex(),
                        self.full_regret.signed_lower_chips.hex(),
                        self.full_regret.signed_upper_chips.hex(),
                    ),
                    "normalized_full_regret": (
                        self.normalized_full_regret.lower.hex(),
                        self.normalized_full_regret.upper.hex(),
                    ),
                    "normalized_teacher_excess": (
                        self.normalized_teacher_excess.lower.hex(),
                        self.normalized_teacher_excess.upper.hex(),
                    ),
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "prior_reference_sha256": self.prior.digest,
                    "selected_candidate_position": self.selected_candidate_position,
                    "selected_raise_to_totals": (
                        self.selected.transition.augmented.raise_to_totals
                    ),
                    "teacher": {
                        "equivalent_subset_indices": (
                            self.teacher.equivalent_subset_indices
                        ),
                        "lower_hex": self.teacher.value.lower_chips.hex(),
                        "nondominated_subset_indices": (
                            self.teacher.nondominated_subset_indices
                        ),
                        "unique_best_subset_index": (
                            self.teacher.unique_best_subset_index
                        ),
                        "upper_hex": self.teacher.value.upper_chips.hex(),
                    },
                    "teacher_excess": (
                        self.teacher_excess.nonnegative_lower_chips.hex(),
                        self.teacher_excess.nonnegative_upper_chips.hex(),
                        self.teacher_excess.signed_lower_chips.hex(),
                        self.teacher_excess.signed_upper_chips.hex(),
                    ),
                    "version": "adr0342-transfer-confirmation-context-v1",
                }
            )
        ).hexdigest()


def _build_context_result(
    *,
    prior: TransferConfirmationPriorReference,
    evidence_digests: tuple[str, ...],
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...],
) -> TransferConfirmationContextResult:
    selected = select_greedy_candidate(candidates)
    teacher = reduce_teacher_width(
        tuple(
            TeacherSubsetCandidate(
                subset_index=item.transition.candidate_position,
                raise_to_totals=item.transition.augmented.raise_to_totals,
                value=item.augmented.value,
            )
            for item in candidates
        ),
        raise_width=ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH,
        equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    )
    full_regret = certified_full_minus_subset_regret(
        full=prior.full_value,
        subset=selected.augmented.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    teacher_excess = certified_greedy_teacher_excess(
        teacher=teacher.value,
        greedy=selected.augmented.value,
    )
    return TransferConfirmationContextResult(
        panel_position=prior.panel_position,
        pool_index=prior.pool_index,
        context_semantic_sha256=prior.context_semantic_sha256,
        payoff_span_chips=prior.payoff_span_chips,
        prior=prior,
        candidate_evidence_sha256s=evidence_digests,
        candidates=candidates,
        selected_candidate_position=selected.transition.candidate_position,
        teacher=teacher,
        full_regret=full_regret,
        normalized_full_regret=normalize_full_regret(
            full_regret,
            payoff_span_chips=prior.payoff_span_chips,
        ),
        teacher_excess=teacher_excess,
        normalized_teacher_excess=normalize_greedy_teacher_excess(
            teacher_excess,
            payoff_span_chips=prior.payoff_span_chips,
        ),
    )


def _build_confirmation_gate(
    contexts: tuple[TransferConfirmationContextResult, ...],
) -> GreedyWidthGateResult:
    if (
        not isinstance(contexts, tuple)
        or len(contexts) != ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT
        or tuple(item.panel_position for item in contexts)
        != tuple(range(ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT))
    ):
        raise ValueError("transfer confirmation gate requires the exact panel")
    recovery: ConservativeAggregateRecoveryInterval = conservative_aggregate_recovery(
        full_values=tuple(item.prior.full_value for item in contexts),
        baseline_values=tuple(item.prior.baseline.value for item in contexts),
        greedy_values=tuple(item.selected.augmented.value for item in contexts),
    )
    maximum_full = max(item.normalized_full_regret.upper for item in contexts)
    mean_full_lower = sum(
        item.normalized_full_regret.lower for item in contexts
    ) / len(contexts)
    mean_full_upper = sum(
        item.normalized_full_regret.upper for item in contexts
    ) / len(contexts)
    maximum_excess = max(
        item.normalized_teacher_excess.upper for item in contexts
    )
    mean_excess_lower = sum(
        item.normalized_teacher_excess.lower for item in contexts
    ) / len(contexts)
    mean_excess_upper = sum(
        item.normalized_teacher_excess.upper for item in contexts
    ) / len(contexts)
    return GreedyWidthGateResult(
        raise_width=ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH,
        maximum_normalized_full_regret_upper=maximum_full,
        mean_normalized_full_regret_lower=mean_full_lower,
        mean_normalized_full_regret_upper=mean_full_upper,
        aggregate_recovery=recovery,
        maximum_normalized_teacher_excess_upper=maximum_excess,
        mean_normalized_teacher_excess_lower=mean_excess_lower,
        mean_normalized_teacher_excess_upper=mean_excess_upper,
        maximum_full_regret_pass=(
            maximum_full <= ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value
        ),
        mean_full_regret_pass=(
            mean_full_upper <= ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value
        ),
        aggregate_recovery_pass=(
            recovery.lower >= ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR.value
        ),
        maximum_teacher_excess_pass=(
            maximum_excess
            <= ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT.value
        ),
        mean_teacher_excess_pass=(
            mean_excess_upper
            <= ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT.value
        ),
    )


class TransferConfirmationStopReason(StrEnum):
    COMPLETED_CONFIRMED = "completed_confirmed"
    COMPLETED_REJECTED = "completed_rejected"
    CONSUMER_REJECTED = "consumer_rejected"
    NUMERICAL_REJECTED = "numerical_rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


class TransferConfirmationFailureStage(StrEnum):
    CANDIDATE_ARM = "candidate_arm"
    CANDIDATE_PRICE = "candidate_price"
    CONTEXT_REDUCTION = "context_reduction"
    CAMPAIGN_REDUCTION = "campaign_reduction"


@dataclass(frozen=True, slots=True)
class _DerivedTransferConfirmationState:
    evidences: tuple[TransferConfirmationArmEvidence, ...]
    contexts: tuple[TransferConfirmationContextResult, ...]
    current_candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]
    current_evidence_sha256s: tuple[str, ...]
    gate: GreedyWidthGateResult | None
    stop_reason: TransferConfirmationStopReason | None
    failure_stage: TransferConfirmationFailureStage | None
    failure_exception_chain: tuple[dict[str, str], ...]
    known_public_call_count: int
    invocation_count_complete: bool


def _derive_confirmation_state(
    evidences: tuple[TransferConfirmationArmEvidence, ...],
    *,
    schedule: TransferConfirmationSchedule,
) -> _DerivedTransferConfirmationState:
    if (
        not isinstance(evidences, tuple)
        or len(evidences) > ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
        or tuple(item.call_index for item in evidences)
        != tuple(range(len(evidences)))
    ):
        raise ValueError("transfer confirmation evidence is not a contiguous prefix")
    contexts: list[TransferConfirmationContextResult] = []
    current_candidates: list[ClosedFiniteBlockCandidateEvidence] = []
    current_evidence_sha256s: list[str] = []
    stop: TransferConfirmationStopReason | None = None
    failure_stage: TransferConfirmationFailureStage | None = None
    failure_chain: tuple[dict[str, str], ...] = ()
    known_calls = 0
    invocation_complete = True
    for call_index, evidence in enumerate(evidences):
        if stop is not None:
            raise ValueError("transfer confirmation continues past a semantic stop")
        slot = schedule.call_slots[call_index]
        task = schedule.candidate_tasks[call_index]
        transition = schedule.transitions[call_index]
        if (
            evidence.slot_sha256 != slot.digest
            or evidence.task_sha256 != task.digest
            or evidence.transition_sha256 != transition.digest
        ):
            raise ValueError("transfer confirmation prefix crossed its schedule")
        if evidence.kind is TransferConfirmationEvidenceKind.UNEXPECTED_EXCEPTION:
            stop = TransferConfirmationStopReason.UNEXPECTED_EXCEPTION
            failure_stage = TransferConfirmationFailureStage.CANDIDATE_ARM
            result = evidence.core["result"]
            if not isinstance(result, dict):
                raise TypeError("unexpected confirmation result lost its object type")
            failure_chain = tuple(result["exception_chain"])  # type: ignore[arg-type]
            invocation_complete = False
            continue
        known_calls += evidence.public_call_count
        if evidence.kind is TransferConfirmationEvidenceKind.REJECTED:
            stop = TransferConfirmationStopReason.CONSUMER_REJECTED
            failure_stage = TransferConfirmationFailureStage.CANDIDATE_ARM
            result = evidence.core["result"]
            if not isinstance(result, dict):
                raise TypeError("rejected confirmation result lost its object type")
            failure_chain = tuple(result["exception_chain"])  # type: ignore[arg-type]
            continue
        try:
            value = evidence.accepted_value(task)
            candidate = build_closed_finite_block_candidate(
                transition=transition,
                incumbent=schedule.prior_references[
                    slot.panel_position
                ].baseline,
                augmented=value,
            )
        except ValueError as error:
            stop = TransferConfirmationStopReason.NUMERICAL_REJECTED
            failure_stage = TransferConfirmationFailureStage.CANDIDATE_PRICE
            failure_chain = _exception_payload(error)
            continue
        current_candidates.append(candidate)
        current_evidence_sha256s.append(evidence.digest)
        context_slots = schedule.call_slots_for_context(slot.panel_position)
        if slot.candidate_position != len(context_slots) - 1:
            continue
        try:
            context_result = _build_context_result(
                prior=schedule.prior_references[slot.panel_position],
                evidence_digests=tuple(current_evidence_sha256s),
                candidates=tuple(current_candidates),
            )
        except ValueError as error:
            stop = TransferConfirmationStopReason.NUMERICAL_REJECTED
            failure_stage = TransferConfirmationFailureStage.CONTEXT_REDUCTION
            failure_chain = _exception_payload(error)
            continue
        contexts.append(context_result)
        current_candidates = []
        current_evidence_sha256s = []

    gate: GreedyWidthGateResult | None = None
    if (
        stop is None
        and len(evidences) == ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
    ):
        if current_candidates or current_evidence_sha256s:
            raise AssertionError("complete transfer confirmation ended mid-context")
        try:
            gate = _build_confirmation_gate(tuple(contexts))
        except ValueError as error:
            stop = TransferConfirmationStopReason.NUMERICAL_REJECTED
            failure_stage = TransferConfirmationFailureStage.CAMPAIGN_REDUCTION
            failure_chain = _exception_payload(error)
        else:
            stop = (
                TransferConfirmationStopReason.COMPLETED_CONFIRMED
                if gate.passes
                else TransferConfirmationStopReason.COMPLETED_REJECTED
            )
    return _DerivedTransferConfirmationState(
        evidences=evidences,
        contexts=tuple(contexts),
        current_candidates=tuple(current_candidates),
        current_evidence_sha256s=tuple(current_evidence_sha256s),
        gate=gate,
        stop_reason=stop,
        failure_stage=failure_stage,
        failure_exception_chain=failure_chain,
        known_public_call_count=known_calls,
        invocation_count_complete=invocation_complete,
    )


class TransferConfirmationExecutionPhase(StrEnum):
    HEADER_APPEND = "header_append"
    NEXT_CALL_AUTHORIZATION = "next_call_authorization"
    ARM_EVIDENCE = "arm_evidence"
    OBSERVATION_APPEND = "observation_append"
    SEMANTIC_REDUCTION = "semantic_reduction"
    TERMINAL_APPEND = "terminal_append"
    JOURNAL_CLOSE = "journal_close"
    FINAL_REBIND = "final_rebind"


_TRANSFER_CONFIRMATION_PROTOCOL_PAYLOAD = {
    "artifact_relative_path": ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH,
    "candidate_call_count": ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT,
    "candidate_schedule": (
        "panel-order; each context's omitted interior raise-to totals in ascending order"
    ),
    "completed_record_count": ADR0342_TRANSFER_CONFIRMATION_COMPLETED_RECORD_COUNT,
    "context_count": ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT,
    "development_result_sha256": ADR0338_GREEDY_RESULT_SHA256,
    "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    "equivalence_allowance_chips_hex": (
        ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE.chips.hex()
    ),
    "execution_failure_reduction": (
        "exact-raw-journal-plus-last-receipted-semantic-prefix"
    ),
    "execution_phases": tuple(item.value for item in TransferConfirmationExecutionPhase),
    "failure_stages": tuple(item.value for item in TransferConfirmationFailureStage),
    "full_comparator": "exact retained ADR-0341 complete-integer-universe interval",
    "gate_conjuncts": (
        (
            "maximum_normalized_full_regret_upper_lte",
            ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value.hex(),
        ),
        (
            "mean_normalized_full_regret_upper_lte",
            ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value.hex(),
        ),
        (
            "aggregate_recovery_lower_gte",
            ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR.value.hex(),
        ),
        (
            "maximum_normalized_teacher_excess_upper_lte",
            ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT.value.hex(),
        ),
        (
            "mean_normalized_teacher_excess_upper_lte",
            ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT.value.hex(),
        ),
    ),
    "invocation_accounting": (
        "32 retained qualification arms are prior evidence and excluded; "
        "126 prospective candidate arms are counted one public call each when receipted"
    ),
    "mechanism": (
        "from exact retained width-two anchors, evaluate every one-interior-raise "
        "augmentation; select greatest certified behavioral lower endpoint, exact "
        "ties smaller raise-to total"
    ),
    "partial_transfer_interpretation": (
        "all-five-unchanged-conjuncts-or-reject-unrestricted-transfer"
    ),
    "payoff_normalizer": "context.payoff_span_chips; never stack",
    "prior_arm_count": ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT,
    "qualification_panel_sha256": ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    "raise_width": ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH.count,
    "reselection": "forbidden",
    "stop_reasons": tuple(item.value for item in TransferConfirmationStopReason),
    "teacher": (
        "same exhaustive width-three candidate calls; interval envelope with all "
        "certified nondominated candidates retained"
    ),
    "unreceipted_invocation_accounting": "unknown-and-excluded",
    "value_witness": (
        "exact-policy-behavioral-reconstruction-plus-dual-certificate-rebind"
    ),
    "version": "adr0342-transfer-confirmation-protocol-v1",
}
ADR0342_TRANSFER_CONFIRMATION_PROTOCOL = MappingProxyType(
    _TRANSFER_CONFIRMATION_PROTOCOL_PAYLOAD
)
ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_TRANSFER_CONFIRMATION_PROTOCOL_PAYLOAD)
).hexdigest()


def verify_adr0342_transfer_confirmation_source_and_dependencies() -> str:
    """Verify the prospective source seal and all inherited retained evidence."""

    from .fresh_action_width_transfer_confirmation_seal import (
        ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH as sealed_path,
        ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT as sealed_call_count,
        ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256 as sealed_protocol,
        ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256,
        ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST
    }
    if actual != ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0342 transfer-confirmation source closure drifted")
    verify_adr0338_greedy_result_source_and_dependencies()
    verify_adr0341_transfer_qualification_result_artifact()
    if (
        sealed_protocol != ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256
        or sealed_path != ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
        or sealed_call_count != ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
        or tuple(ADR0342_TRANSFER_CONFIRMATION_PROTOCOL["stop_reasons"])
        != tuple(item.value for item in TransferConfirmationStopReason)
        or tuple(ADR0342_TRANSFER_CONFIRMATION_PROTOCOL["failure_stages"])
        != tuple(item.value for item in TransferConfirmationFailureStage)
        or tuple(ADR0342_TRANSFER_CONFIRMATION_PROTOCOL["execution_phases"])
        != tuple(item.value for item in TransferConfirmationExecutionPhase)
    ):
        raise RuntimeError("ADR-0342 transfer-confirmation protocol drifted")
    schedule = build_adr0342_transfer_confirmation_schedule()
    if schedule.digest != ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0342 transfer-confirmation schedule drifted")
    attributes = root.parents[1] / ".gitattributes"
    required = f"/{ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH} -text"
    if required not in attributes.read_text(encoding="utf-8").splitlines():
        raise RuntimeError("ADR-0342 transfer-confirmation artifact lacks -text")
    return actual["fresh_action_width_transfer_confirmation.py"]


def _gate_payload(gate: GreedyWidthGateResult | None) -> dict[str, object] | None:
    if gate is None:
        return None
    return {
        "aggregate_recovery": {
            "achieved_gain_lower_chips_hex": (
                gate.aggregate_recovery.achieved_gain_lower_chips.hex()
            ),
            "achieved_gain_upper_chips_hex": (
                gate.aggregate_recovery.achieved_gain_upper_chips.hex()
            ),
            "available_gain_lower_chips_hex": (
                gate.aggregate_recovery.available_gain_lower_chips.hex()
            ),
            "available_gain_upper_chips_hex": (
                gate.aggregate_recovery.available_gain_upper_chips.hex()
            ),
            "lower_hex": gate.aggregate_recovery.lower.hex(),
            "upper_hex": gate.aggregate_recovery.upper.hex(),
        },
        "aggregate_recovery_pass": gate.aggregate_recovery_pass,
        "maximum_full_regret_pass": gate.maximum_full_regret_pass,
        "maximum_normalized_full_regret_upper_hex": (
            gate.maximum_normalized_full_regret_upper.hex()
        ),
        "maximum_normalized_teacher_excess_upper_hex": (
            gate.maximum_normalized_teacher_excess_upper.hex()
        ),
        "maximum_teacher_excess_pass": gate.maximum_teacher_excess_pass,
        "mean_full_regret_pass": gate.mean_full_regret_pass,
        "mean_normalized_full_regret_lower_hex": (
            gate.mean_normalized_full_regret_lower.hex()
        ),
        "mean_normalized_full_regret_upper_hex": (
            gate.mean_normalized_full_regret_upper.hex()
        ),
        "mean_normalized_teacher_excess_lower_hex": (
            gate.mean_normalized_teacher_excess_lower.hex()
        ),
        "mean_normalized_teacher_excess_upper_hex": (
            gate.mean_normalized_teacher_excess_upper.hex()
        ),
        "mean_teacher_excess_pass": gate.mean_teacher_excess_pass,
        "passes": gate.passes,
        "raise_width": gate.raise_width.count,
        "sha256": gate.digest,
    }


def _campaign_sha256(
    *,
    schedule: TransferConfirmationSchedule,
    confirmation_source_sha256: str,
    synthetic: bool,
) -> str:
    _require_digest(
        confirmation_source_sha256,
        label="transfer confirmation campaign source",
    )
    return sha256(
        canonical_journal_json_bytes(
            {
                "artifact_relative_path": (
                    ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
                ),
                "confirmation_source_sha256": confirmation_source_sha256,
                "protocol_sha256": ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
                "schedule_sha256": schedule.digest,
                "synthetic": synthetic,
                "version": _CAMPAIGN_VERSION,
            }
        )
    ).hexdigest()


def _header_payload(
    *,
    schedule: TransferConfirmationSchedule,
    confirmation_source_sha256: str,
    campaign_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    return _sealed_payload(
        {
            "artifact_relative_path": (
                ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
            ),
            "baseline_task_sha256s": tuple(
                item.baseline_task.digest for item in schedule.prior_references
            ),
            "campaign_sha256": campaign_sha256,
            "candidate_call_count": (
                ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
            ),
            "confirmation_source_sha256": confirmation_source_sha256,
            "development_result_sha256": schedule.development_result_sha256,
            "prior_arm_count": ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT,
            "prior_reference_sha256s": tuple(
                item.digest for item in schedule.prior_references
            ),
            "protocol_sha256": ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
            "qualification_panel_sha256": schedule.qualification_panel_sha256,
            "raise_width": ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH.count,
            "schedule_sha256": schedule.digest,
            "synthetic": synthetic,
            "version": _HEADER_VERSION,
        },
        digest_field="header_sha256",
    )


def _terminal_payload(
    *,
    state: _DerivedTransferConfirmationState,
    schedule: TransferConfirmationSchedule,
    confirmation_source_sha256: str,
    campaign_sha256: str,
    final_observation_line_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    if state.stop_reason is None:
        raise ValueError("transfer confirmation terminal requires a derived stop")
    _require_digest(
        final_observation_line_sha256,
        label="transfer confirmation final observation line",
    )
    confirmed: bool | None
    if state.stop_reason is TransferConfirmationStopReason.COMPLETED_CONFIRMED:
        confirmed = True
    elif state.stop_reason is TransferConfirmationStopReason.COMPLETED_REJECTED:
        confirmed = False
    else:
        confirmed = None
    return _sealed_payload(
        {
            "campaign_sha256": campaign_sha256,
            "confirmation_source_sha256": confirmation_source_sha256,
            "context_result_sha256s": tuple(item.digest for item in state.contexts),
            "evidence_sha256s": tuple(item.digest for item in state.evidences),
            "failure_exception_chain": state.failure_exception_chain,
            "failure_stage": (
                None if state.failure_stage is None else state.failure_stage.value
            ),
            "final_observation_line_sha256": final_observation_line_sha256,
            "gate": _gate_payload(state.gate),
            "invocation_count_complete": state.invocation_count_complete,
            "known_public_call_count": state.known_public_call_count,
            "observed_candidate_arm_count": len(state.evidences),
            "partial_candidate_evidence_sha256s": (
                state.current_evidence_sha256s
            ),
            "partial_candidate_sha256s": tuple(
                item.digest for item in state.current_candidates
            ),
            "prior_arm_count": ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT,
            "prior_reference_sha256s": tuple(
                item.digest for item in schedule.prior_references
            ),
            "raise_width": ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH.count,
            "record_count": len(state.evidences) + 2,
            "schedule_sha256": schedule.digest,
            "stop_reason": state.stop_reason.value,
            "synthetic": synthetic,
            "unrestricted_transfer_confirmed": confirmed,
            "version": _TERMINAL_VERSION,
        },
        digest_field="terminal_sha256",
    )


def _validate_derived_collections(
    *,
    evidences: tuple[TransferConfirmationArmEvidence, ...],
    contexts: tuple[TransferConfirmationContextResult, ...],
    gate: GreedyWidthGateResult | None,
    known_public_call_count: int,
    invocation_count_complete: bool,
) -> None:
    if (
        not isinstance(evidences, tuple)
        or len(evidences) > ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
        or any(
            not isinstance(item, TransferConfirmationArmEvidence)
            for item in evidences
        )
        or tuple(item.call_index for item in evidences)
        != tuple(range(len(evidences)))
    ):
        raise ValueError("transfer confirmation evidence prefix drifted")
    if (
        not isinstance(contexts, tuple)
        or any(
            not isinstance(item, TransferConfirmationContextResult)
            for item in contexts
        )
        or tuple(item.panel_position for item in contexts)
        != tuple(range(len(contexts)))
    ):
        raise ValueError("transfer confirmation context prefix drifted")
    if gate is not None and (
        not isinstance(gate, GreedyWidthGateResult)
        or len(contexts) != ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT
        or gate.raise_width != ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH
    ):
        raise ValueError("transfer confirmation gate lacks the complete width-three panel")
    expected_calls = sum(item.public_call_count for item in evidences)
    if known_public_call_count != expected_calls:
        raise ValueError("transfer confirmation known call count drifted")
    expected_complete = all(item.invocation_count_complete for item in evidences)
    if invocation_count_complete is not expected_complete:
        raise ValueError("transfer confirmation invocation completeness drifted")


@dataclass(frozen=True, slots=True)
class TransferConfirmationJournalPrefix:
    recovery: JournalRecovery
    evidences: tuple[TransferConfirmationArmEvidence, ...]
    contexts: tuple[TransferConfirmationContextResult, ...]
    partial_candidate_sha256s: tuple[str, ...]
    pending_stop_reason: TransferConfirmationStopReason | None
    failure_stage: TransferConfirmationFailureStage | None
    known_public_call_count: int
    invocation_count_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.recovery, JournalRecovery):
            raise TypeError("transfer confirmation prefix requires journal recovery")
        if self.recovery.is_complete:
            raise ValueError("transfer confirmation prefix cannot contain a terminal")
        _validate_derived_collections(
            evidences=self.evidences,
            contexts=self.contexts,
            gate=None,
            known_public_call_count=self.known_public_call_count,
            invocation_count_complete=self.invocation_count_complete,
        )
        for digest in self.partial_candidate_sha256s:
            _require_digest(digest, label="transfer confirmation partial candidate")
        if self.pending_stop_reason is not None and not isinstance(
            self.pending_stop_reason,
            TransferConfirmationStopReason,
        ):
            raise TypeError("transfer confirmation prefix stop must be semantic")
        if self.failure_stage is not None and not isinstance(
            self.failure_stage,
            TransferConfirmationFailureStage,
        ):
            raise TypeError("transfer confirmation prefix failure stage must be semantic")


@dataclass(frozen=True, slots=True)
class TransferConfirmationJournalResult:
    campaign_sha256: str
    journal_sha256: str
    journal_byte_count: int
    terminal_sha256: str
    evidences: tuple[TransferConfirmationArmEvidence, ...]
    contexts: tuple[TransferConfirmationContextResult, ...]
    gate: GreedyWidthGateResult | None
    stop_reason: TransferConfirmationStopReason
    failure_stage: TransferConfirmationFailureStage | None
    failure_exception_chain: tuple[dict[str, str], ...]
    known_public_call_count: int
    invocation_count_complete: bool
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("campaign", self.campaign_sha256),
            ("journal", self.journal_sha256),
            ("terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=f"transfer confirmation {label}")
        if _require_count(
            self.journal_byte_count,
            label="transfer confirmation journal bytes",
        ) == 0:
            raise ValueError("transfer confirmation terminal journal cannot be empty")
        if not isinstance(self.stop_reason, TransferConfirmationStopReason):
            raise TypeError("transfer confirmation stop must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("transfer confirmation synthetic flag must be Boolean")
        _validate_derived_collections(
            evidences=self.evidences,
            contexts=self.contexts,
            gate=self.gate,
            known_public_call_count=self.known_public_call_count,
            invocation_count_complete=self.invocation_count_complete,
        )
        completed = self.stop_reason in {
            TransferConfirmationStopReason.COMPLETED_CONFIRMED,
            TransferConfirmationStopReason.COMPLETED_REJECTED,
        }
        if completed != (self.gate is not None):
            raise ValueError("transfer confirmation completion and gate disagree")
        if completed and (
            len(self.evidences)
            != ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT
            or len(self.contexts) != ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT
            or self.failure_stage is not None
            or self.failure_exception_chain
        ):
            raise ValueError("completed transfer confirmation is incomplete")
        if self.stop_reason is TransferConfirmationStopReason.COMPLETED_CONFIRMED:
            if self.gate is None or not self.gate.passes:
                raise ValueError("confirmed transfer lacks all five conjuncts")
        if self.stop_reason is TransferConfirmationStopReason.COMPLETED_REJECTED:
            if self.gate is None or self.gate.passes:
                raise ValueError("rejected transfer did not fail a conjunct")
        if self.stop_reason is TransferConfirmationStopReason.CONSUMER_REJECTED:
            if (
                not self.evidences
                or self.evidences[-1].kind
                is not TransferConfirmationEvidenceKind.REJECTED
            ):
                raise ValueError("consumer-rejected terminal lacks rejected evidence")
        if self.stop_reason is TransferConfirmationStopReason.UNEXPECTED_EXCEPTION:
            if (
                not self.evidences
                or self.evidences[-1].kind
                is not TransferConfirmationEvidenceKind.UNEXPECTED_EXCEPTION
                or self.invocation_count_complete
            ):
                raise ValueError("unexpected terminal lacks uncertain invocation evidence")
        if (
            self.stop_reason is TransferConfirmationStopReason.NUMERICAL_REJECTED
            and self.failure_stage
            not in {
                TransferConfirmationFailureStage.CANDIDATE_PRICE,
                TransferConfirmationFailureStage.CONTEXT_REDUCTION,
                TransferConfirmationFailureStage.CAMPAIGN_REDUCTION,
            }
        ):
            raise ValueError("numerical rejection lacks its exact reduction stage")

    @property
    def unrestricted_transfer_confirmed(self) -> bool | None:
        if self.stop_reason is TransferConfirmationStopReason.COMPLETED_CONFIRMED:
            return True
        if self.stop_reason is TransferConfirmationStopReason.COMPLETED_REJECTED:
            return False
        return None


TransferConfirmationJournalRebinding = (
    TransferConfirmationJournalPrefix | TransferConfirmationJournalResult
)


def rebind_adr0342_transfer_confirmation_journal(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> TransferConfirmationJournalRebinding:
    """Reconstruct a confirmation prefix or terminal without a solver call."""

    if not isinstance(raw, bytes):
        raise TypeError("transfer confirmation rebinding requires immutable bytes")
    if not isinstance(synthetic, bool):
        raise TypeError("transfer confirmation synthetic mode must be Boolean")
    confirmation_source = verify_adr0342_transfer_confirmation_source_and_dependencies()
    schedule = build_adr0342_transfer_confirmation_schedule()
    campaign = _campaign_sha256(
        schedule=schedule,
        confirmation_source_sha256=confirmation_source,
        synthetic=synthetic,
    )
    first_line_end = raw.find(b"\n")
    if first_line_end >= 0:
        try:
            first_record = parse_journal_record_line(raw[: first_line_end + 1])
        except (TypeError, ValueError):
            pass
        else:
            if (
                first_record.body.protocol_sha256
                != ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256
                or first_record.body.campaign_sha256 != campaign
            ):
                raise ValueError(
                    "transfer confirmation belongs to another protocol or campaign"
                )
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign,
    )
    records = recovery.records
    if not records:
        return TransferConfirmationJournalPrefix(
            recovery=recovery,
            evidences=(),
            contexts=(),
            partial_candidate_sha256s=(),
            pending_stop_reason=None,
            failure_stage=None,
            known_public_call_count=0,
            invocation_count_complete=True,
        )
    header = records[0]
    if header.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("transfer confirmation first record is not its header")
    expected_header = _header_payload(
        schedule=schedule,
        confirmation_source_sha256=confirmation_source,
        campaign_sha256=campaign,
        synthetic=synthetic,
    )
    if canonical_journal_json_bytes(header.body.payload) != canonical_journal_json_bytes(
        expected_header
    ):
        raise ValueError("transfer confirmation header differs from its schedule")
    if header.body.semantic_identity_sha256 != expected_header["header_sha256"]:
        raise ValueError("transfer confirmation header identity drifted")

    terminal_record: JournalRecordEnvelope | None = None
    observation_records = records[1:]
    if (
        observation_records
        and observation_records[-1].body.kind is JournalRecordKind.TERMINAL
    ):
        terminal_record = observation_records[-1]
        observation_records = observation_records[:-1]
    if any(
        item.body.kind is not JournalRecordKind.OBSERVATION
        for item in observation_records
    ):
        raise ValueError("transfer confirmation has a non-observation in its prefix")
    if len(observation_records) > ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT:
        raise ValueError("transfer confirmation exceeds its call schedule")
    evidences: list[TransferConfirmationArmEvidence] = []
    for index, record in enumerate(observation_records):
        evidence = _rebind_evidence(
            record.body.payload,
            slot=schedule.call_slots[index],
            task=schedule.candidate_tasks[index],
            transition=schedule.transitions[index],
            expect_synthetic=synthetic,
        )
        if record.body.semantic_identity_sha256 != evidence.digest:
            raise ValueError("transfer confirmation observation identity drifted")
        evidences.append(evidence)
    state = _derive_confirmation_state(tuple(evidences), schedule=schedule)
    if terminal_record is None:
        return TransferConfirmationJournalPrefix(
            recovery=recovery,
            evidences=state.evidences,
            contexts=state.contexts,
            partial_candidate_sha256s=tuple(
                item.digest for item in state.current_candidates
            ),
            pending_stop_reason=state.stop_reason,
            failure_stage=state.failure_stage,
            known_public_call_count=state.known_public_call_count,
            invocation_count_complete=state.invocation_count_complete,
        )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("transfer confirmation terminal has trailing invalid bytes")
    if not observation_records:
        raise ValueError("transfer confirmation terminal lacks an observation")
    expected_terminal = _terminal_payload(
        state=state,
        schedule=schedule,
        confirmation_source_sha256=confirmation_source,
        campaign_sha256=campaign,
        final_observation_line_sha256=observation_records[-1].line_sha256,
        synthetic=synthetic,
    )
    terminal_payload = terminal_record.body.payload
    _verify_sealed_payload(
        terminal_payload,
        digest_field="terminal_sha256",
        label="transfer confirmation terminal",
    )
    if canonical_journal_json_bytes(terminal_payload) != canonical_journal_json_bytes(
        expected_terminal
    ):
        raise ValueError("transfer confirmation terminal differs from derived evidence")
    if (
        terminal_record.body.semantic_identity_sha256
        != terminal_payload["terminal_sha256"]
    ):
        raise ValueError("transfer confirmation terminal identity drifted")
    if state.stop_reason is None:
        raise AssertionError("transfer confirmation terminal validated without a stop")
    return TransferConfirmationJournalResult(
        campaign_sha256=campaign,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
        terminal_sha256=terminal_payload["terminal_sha256"],  # type: ignore[arg-type]
        evidences=state.evidences,
        contexts=state.contexts,
        gate=state.gate,
        stop_reason=state.stop_reason,
        failure_stage=state.failure_stage,
        failure_exception_chain=state.failure_exception_chain,
        known_public_call_count=state.known_public_call_count,
        invocation_count_complete=state.invocation_count_complete,
        synthetic=synthetic,
    )


@dataclass(frozen=True, slots=True)
class TransferConfirmationLaunchRejected:
    reason: str
    output_path: Path
    exception_chain: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("transfer confirmation launch reason must be nonempty")
        if not isinstance(self.output_path, Path):
            raise TypeError("transfer confirmation launch path must be a Path")
        if not self.exception_chain:
            raise ValueError("transfer confirmation launch requires exception evidence")


@dataclass(frozen=True, slots=True)
class TransferConfirmationExecutionFailed:
    reason: str
    phase: TransferConfirmationExecutionPhase
    output_path: Path
    failed_call_index: int | None
    unreceipted_arm_invocation: bool
    durably_recorded_evidences: tuple[TransferConfirmationArmEvidence, ...]
    known_public_call_count: int
    invocation_count_complete: bool
    raw_journal_bytes: bytes | None
    recovery: JournalRecovery | None
    exception_chain: tuple[dict[str, str], ...]
    recovery_exception_chain: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("transfer confirmation execution reason must be nonempty")
        if not isinstance(self.phase, TransferConfirmationExecutionPhase):
            raise TypeError("transfer confirmation execution phase must be semantic")
        if not isinstance(self.output_path, Path):
            raise TypeError("transfer confirmation failure path must be a Path")
        if self.failed_call_index is not None:
            _require_count(
                self.failed_call_index,
                label="transfer confirmation failed call",
                maximum=ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT - 1,
            )
        if not isinstance(self.unreceipted_arm_invocation, bool):
            raise TypeError("transfer confirmation unreceipted flag must be Boolean")
        if (
            not isinstance(self.durably_recorded_evidences, tuple)
            or any(
                not isinstance(item, TransferConfirmationArmEvidence)
                for item in self.durably_recorded_evidences
            )
        ):
            raise TypeError("transfer confirmation failure evidence is not semantic")
        expected_calls = sum(
            item.public_call_count for item in self.durably_recorded_evidences
        )
        if self.known_public_call_count != expected_calls:
            raise ValueError("transfer confirmation failure call count drifted")
        expected_complete = (
            not self.unreceipted_arm_invocation
            and all(
                item.invocation_count_complete
                for item in self.durably_recorded_evidences
            )
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("transfer confirmation failure completeness drifted")
        if not self.exception_chain:
            raise ValueError("transfer confirmation failure requires exception evidence")
        if self.raw_journal_bytes is None:
            if self.recovery is not None or not self.recovery_exception_chain:
                raise ValueError("unreadable confirmation journal lacks recovery evidence")
        elif not isinstance(self.raw_journal_bytes, bytes):
            raise TypeError("transfer confirmation failure raw journal is mutable")
        elif self.recovery is None:
            if not self.recovery_exception_chain:
                raise ValueError("transfer confirmation raw journal lacks recovery evidence")
        elif (
            not isinstance(self.recovery, JournalRecovery)
            or self.recovery.raw_bytes != self.raw_journal_bytes
        ):
            raise ValueError("transfer confirmation failure recovery lost raw bytes")

    @property
    def raw_journal_sha256(self) -> str | None:
        if self.raw_journal_bytes is None:
            return None
        return sha256(self.raw_journal_bytes).hexdigest()


TransferConfirmationRunResult = (
    TransferConfirmationJournalRebinding
    | TransferConfirmationLaunchRejected
    | TransferConfirmationExecutionFailed
)
_ArmOwner = Callable[
    [
        TransferConfirmationCallSlot,
        GreedySubsetTask,
        ClosedFiniteBlockTransition,
    ],
    TransferConfirmationArmEvidence,
]


def _execution_failure(
    *,
    writer: DurableEvidenceJournalWriter,
    output_path: Path,
    campaign_sha256: str,
    phase: TransferConfirmationExecutionPhase,
    failed_call_index: int | None,
    unreceipted_arm_invocation: bool,
    evidences: tuple[TransferConfirmationArmEvidence, ...],
    error: Exception,
) -> TransferConfirmationExecutionFailed:
    exception_chain = _exception_payload(error)
    try:
        writer.close()
    except Exception as close_error:
        exception_chain += _exception_payload(close_error)
    raw: bytes | None = None
    recovery: JournalRecovery | None = None
    recovery_exception_chain: tuple[dict[str, str], ...] = ()
    try:
        raw = output_path.read_bytes()
    except Exception as recovery_error:
        recovery_exception_chain = _exception_payload(recovery_error)
    else:
        try:
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=(
                    ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256
                ),
                expected_campaign_sha256=campaign_sha256,
            )
        except Exception as recovery_error:
            recovery_exception_chain = _exception_payload(recovery_error)
    return TransferConfirmationExecutionFailed(
        reason="transfer confirmation failed after exclusive journal creation",
        phase=phase,
        output_path=output_path,
        failed_call_index=failed_call_index,
        unreceipted_arm_invocation=unreceipted_arm_invocation,
        durably_recorded_evidences=evidences,
        known_public_call_count=sum(item.public_call_count for item in evidences),
        invocation_count_complete=(
            not unreceipted_arm_invocation
            and all(item.invocation_count_complete for item in evidences)
        ),
        raw_journal_bytes=raw,
        recovery=recovery,
        exception_chain=exception_chain,
        recovery_exception_chain=recovery_exception_chain,
    )


def _execute_transfer_confirmation(
    *,
    output_path: Path,
    pool: FreshActionWidthTransferPool,
    schedule: TransferConfirmationSchedule,
    confirmation_source_sha256: str,
    arm_owner: _ArmOwner,
    synthetic: bool,
) -> TransferConfirmationJournalResult | TransferConfirmationExecutionFailed:
    """Execute one supplied owner under the prospective durable protocol."""

    if not isinstance(pool, FreshActionWidthTransferPool):
        raise TypeError("transfer confirmation execution requires the exact pool")
    if not isinstance(schedule, TransferConfirmationSchedule):
        raise TypeError("transfer confirmation execution requires the exact schedule")
    if pool.digest != schedule.pool_sha256 or pool.digest != ADR0339_TRANSFER_POOL_SHA256:
        raise ValueError("transfer confirmation execution crossed its exact pool")
    campaign = _campaign_sha256(
        schedule=schedule,
        confirmation_source_sha256=confirmation_source_sha256,
        synthetic=synthetic,
    )
    writer = DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
        campaign_sha256=campaign,
    )
    evidences: list[TransferConfirmationArmEvidence] = []
    phase = TransferConfirmationExecutionPhase.HEADER_APPEND
    failed_call_index: int | None = None
    unreceipted_arm_invocation = False
    try:
        header = _header_payload(
            schedule=schedule,
            confirmation_source_sha256=confirmation_source_sha256,
            campaign_sha256=campaign,
            synthetic=synthetic,
        )
        authorization = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header["header_sha256"],  # type: ignore[arg-type]
            payload=header,
        )
        for call_index, (slot, task, transition) in enumerate(
            zip(
                schedule.call_slots,
                schedule.candidate_tasks,
                schedule.transitions,
                strict=True,
            )
        ):
            phase = TransferConfirmationExecutionPhase.NEXT_CALL_AUTHORIZATION
            failed_call_index = call_index
            expected_kind = (
                JournalRecordKind.HEADER
                if call_index == 0
                else JournalRecordKind.OBSERVATION
            )
            if authorization.sequence != call_index or authorization.kind is not expected_kind:
                raise RuntimeError(
                    "transfer confirmation call lacks its preceding durable receipt"
                )
            phase = TransferConfirmationExecutionPhase.ARM_EVIDENCE
            unreceipted_arm_invocation = True
            try:
                evidence = arm_owner(slot, task, transition)
                if not isinstance(evidence, TransferConfirmationArmEvidence):
                    raise TypeError(
                        "transfer confirmation arm owner returned nonsemantic evidence"
                    )
                _validate_evidence_against_invocation(
                    evidence,
                    slot=slot,
                    task=task,
                    transition=transition,
                    expect_synthetic=synthetic,
                )
            except Exception as error:
                evidence = _unexpected_evidence(
                    slot=slot,
                    task=task,
                    transition=transition,
                    error=error,
                    synthetic=synthetic,
                )
                _validate_evidence_against_invocation(
                    evidence,
                    slot=slot,
                    task=task,
                    transition=transition,
                    expect_synthetic=synthetic,
                )
            phase = TransferConfirmationExecutionPhase.OBSERVATION_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
            evidences.append(evidence)
            unreceipted_arm_invocation = False
            phase = TransferConfirmationExecutionPhase.SEMANTIC_REDUCTION
            state = _derive_confirmation_state(tuple(evidences), schedule=schedule)
            if state.stop_reason is None:
                continue
            terminal = _terminal_payload(
                state=state,
                schedule=schedule,
                confirmation_source_sha256=confirmation_source_sha256,
                campaign_sha256=campaign,
                final_observation_line_sha256=authorization.line_sha256,
                synthetic=synthetic,
            )
            phase = TransferConfirmationExecutionPhase.TERMINAL_APPEND
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=terminal["terminal_sha256"],  # type: ignore[arg-type]
                payload=terminal,
            )
            break
        else:
            raise RuntimeError("transfer confirmation exhausted without a terminal")
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_call_index=failed_call_index,
            unreceipted_arm_invocation=unreceipted_arm_invocation,
            evidences=tuple(evidences),
            error=error,
        )
    phase = TransferConfirmationExecutionPhase.JOURNAL_CLOSE
    try:
        writer.close()
        phase = TransferConfirmationExecutionPhase.FINAL_REBIND
        rebound = rebind_adr0342_transfer_confirmation_journal(
            output_path.read_bytes(),
            synthetic=synthetic,
        )
        if not isinstance(rebound, TransferConfirmationJournalResult):
            raise RuntimeError("transfer confirmation ended without a terminal result")
        return rebound
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_call_index=failed_call_index,
            unreceipted_arm_invocation=False,
            evidences=tuple(evidences),
            error=error,
        )


def _real_arm_owner(
    slot: TransferConfirmationCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition,
) -> TransferConfirmationArmEvidence:
    result = consume_certified_reduced_sizing_v2(task.request)
    return transfer_confirmation_evidence_from_consumer_result(
        slot=slot,
        task=task,
        transition=transition,
        result=result,
    )


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
    )


def run_and_retain_adr0341_transfer_confirmation() -> TransferConfirmationRunResult:
    """Open the one-shot confirmation only after ADR-0342 is committed."""

    output_path = _artifact_path()
    try:
        source = verify_adr0342_transfer_confirmation_source_and_dependencies()
        pool = build_adr0339_transfer_pool()
        schedule = build_adr0342_transfer_confirmation_schedule()
    except Exception as error:
        return TransferConfirmationLaunchRejected(
            reason="transfer confirmation source or schedule preflight rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )
    try:
        return _execute_transfer_confirmation(
            output_path=output_path,
            pool=pool,
            schedule=schedule,
            confirmation_source_sha256=source,
            arm_owner=_real_arm_owner,
            synthetic=False,
        )
    except Exception as error:
        return TransferConfirmationLaunchRejected(
            reason="transfer confirmation exclusive journal launch rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )


__all__ = [
    "ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH",
    "ADR0342_TRANSFER_CONFIRMATION_BASELINE_TASK_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_COMPLETED_RECORD_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_CONTEXT_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_PROTOCOL",
    "ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256",
    "ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH",
    "ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_TRANSITION_COUNT",
    "TransferConfirmationArmEvidence",
    "TransferConfirmationCallSlot",
    "TransferConfirmationContextResult",
    "TransferConfirmationEvidenceKind",
    "TransferConfirmationExecutionFailed",
    "TransferConfirmationExecutionPhase",
    "TransferConfirmationFailureStage",
    "TransferConfirmationJournalPrefix",
    "TransferConfirmationJournalRebinding",
    "TransferConfirmationJournalResult",
    "TransferConfirmationLaunchRejected",
    "TransferConfirmationPriorReference",
    "TransferConfirmationRunResult",
    "TransferConfirmationSchedule",
    "TransferConfirmationStopReason",
    "build_adr0342_transfer_confirmation_schedule",
    "rebind_adr0342_transfer_confirmation_journal",
    "run_and_retain_adr0341_transfer_confirmation",
    "synthetic_transfer_confirmation_accepted_evidence",
    "synthetic_transfer_confirmation_rejected_evidence",
    "transfer_confirmation_evidence_from_consumer_result",
    "verify_adr0342_transfer_confirmation_source_and_dependencies",
]
