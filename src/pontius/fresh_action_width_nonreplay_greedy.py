"""Non-replay direct closed finite-block owner for ADR-0331.

This source freezes the complete adaptive graph and the exact realized call-slot
schedule before any replacement direct-mechanism value is opened.  The old
ADR-0329 campaign remains closed: this module reuses only its source-sealed pure
semantic primitives and never calls either historical execution entry point.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping

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
    ReducedBetIncrement,
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
    JournalAppendReceipt,
    JournalRecordKind,
    JournalRecordEnvelope,
    JournalRecovery,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from .fresh_action_width_greedy import (
    ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
    ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
    CertifiedFiniteBlockPriceInterval,
    CertifiedGreedyTeacherExcessInterval,
    ClosedFiniteBlockCandidateEvidence,
    ClosedFiniteBlockTransition,
    ConservativeAggregateRecoveryInterval,
    GreedyCertifiedValueEvidence,
    GreedySubsetTask,
    GreedyWidthGateResult,
    NormalizedGreedyTeacherExcessInterval,
    OpponentResponseAction,
    OpponentResponseRowIdentity,
    OpponentResponseRowSetIdentity,
    OwnRaiseBlockIdentity,
    build_closed_finite_block_candidate,
    certified_greedy_teacher_excess,
    conservative_aggregate_recovery,
    normalize_full_regret,
    normalize_greedy_teacher_excess,
    select_greedy_candidate,
)
from .fresh_action_width_nonreplay import (
    FreshActionWidthNonReplayPool,
    build_adr0331_nonreplay_pool,
)
from .fresh_action_width_nonreplay_qualification import (
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
from .fresh_action_width_nonreplay_qualification_result import (
    ADR0334_QUALIFICATION_ARTIFACT_SHA256,
    ADR0334_QUALIFICATION_TERMINAL_SHA256,
    ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
    ADR0334_QUALIFIED_PANEL_SHA256,
    ADR0334_QUALIFIED_POOL_INDICES,
    verify_adr0334_nonreplay_qualification_result_artifact,
)
from .fresh_action_width_nonreplay_teacher import (
    NonReplayTeacherContextResult,
    NonReplayTeacherWidthResult,
)
from .fresh_action_width_nonreplay_teacher_result import (
    ADR0336_TEACHER_ARTIFACT_SHA256,
    ADR0336_TEACHER_RESULT_SHA256,
    ADR0336_TEACHER_TERMINAL_SHA256,
    RetainedNonReplayTeacherResult,
    verify_adr0336_nonreplay_teacher_result_artifact,
)
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    certified_full_minus_subset_regret,
)
from .fresh_action_width_structures import (
    ADR0323_PRIVATE_RANGE_WIDTH,
    ADR0323_RAISE_WIDTHS,
    FreshActionWidthContext,
    PrivateRangeWidth,
    RaiseActionWidth,
    anchored_raise_subset_family,
)
from .fresh_action_width_teacher import NormalizedTeacherRegretInterval


ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/"
    "fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl"
)
ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH = (
    (2, 16),
    (3, 114),
    (4, 367),
    (5, 705),
    (6, 895),
)
ADR0337_GREEDY_ARM_COUNT = 2_097
ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH = (
    (3, 114),
    (4, 734),
    (5, 2_115),
    (6, 3_580),
)
ADR0337_GREEDY_TRANSITION_COUNT = 6_543
ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH = (
    (3, 114),
    (4, 98),
    (5, 82),
    (6, 66),
)
ADR0337_GREEDY_INITIAL_CALL_COUNT = 16
ADR0337_GREEDY_CANDIDATE_CALL_COUNT = 360
ADR0337_GREEDY_CALL_COUNT = 376
ADR0337_GREEDY_COMPLETED_RECORD_COUNT = 378

_EVIDENCE_VERSION = "adr0337-nonreplay-greedy-evidence-v1"
_HEADER_VERSION = "adr0337-nonreplay-greedy-header-v1"
_TERMINAL_VERSION = "adr0337-nonreplay-greedy-terminal-v1"


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
    payload = dict(core)
    payload[digest_field] = sha256(canonical_journal_json_bytes(core)).hexdigest()
    return payload


def _verify_sealed_payload(
    payload: dict[str, object],
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if digest_field not in payload:
        raise ValueError(f"{label} lacks its digest")
    supplied = payload[digest_field]
    _require_digest(supplied, label=f"{label} digest")
    core = {key: value for key, value in payload.items() if key != digest_field}
    if sha256(canonical_journal_json_bytes(core)).hexdigest() != supplied:
        raise ValueError(f"{label} digest drifted")
    return core


def _expected_response_rows(
    *,
    context_semantic_digest: str,
    raise_to_totals: tuple[KernelRaiseToTotal, ...],
    reduced_bet_increments: tuple[ReducedBetIncrement, ...],
    private_width: PrivateRangeWidth,
) -> tuple[OpponentResponseRowIdentity, ...]:
    if len(raise_to_totals) != len(reduced_bet_increments):
        raise ValueError("non-replay response amounts are not one-to-one")
    return tuple(
        OpponentResponseRowIdentity(
            context_semantic_digest=context_semantic_digest,
            raise_to_total=raise_to,
            reduced_bet_increment=increment,
            responder_private_type_index=responder,
            action=action,
        )
        for raise_to, increment in zip(
            raise_to_totals,
            reduced_bet_increments,
            strict=True,
        )
        for responder in range(private_width.count)
        for action in (OpponentResponseAction.FOLD, OpponentResponseAction.CALL)
    )


def _response_row_set_for_request(
    *,
    context_semantic_digest: str,
    request: CertifiedReducedSizingRequestV2,
) -> OpponentResponseRowSetIdentity:
    bound = _bind_request(request)
    private_width = PrivateRangeWidth(len(request.joint_probabilities[0]))
    return OpponentResponseRowSetIdentity(
        context_semantic_digest=context_semantic_digest,
        response_model=request.response_model,
        raise_to_totals=bound.legal_raise_to_totals,
        reduced_bet_increments=bound.reduced_bet_increments,
        responder_private_range_width=private_width,
        rows=_expected_response_rows(
            context_semantic_digest=context_semantic_digest,
            raise_to_totals=bound.legal_raise_to_totals,
            reduced_bet_increments=bound.reduced_bet_increments,
            private_width=private_width,
        ),
    )


def _greedy_request(
    *,
    context: FreshActionWidthContext,
    amounts: tuple[KernelRaiseToTotal, ...],
    width: RaiseActionWidth,
    subset_index: int,
) -> CertifiedReducedSizingRequestV2:
    return CertifiedReducedSizingRequestV2(
        context_id=(
            f"{context.context_id}|nonreplay-closed-finite-block|"
            f"raise-width-{width.count}|subset-{subset_index:04d}"
        ),
        betting=context.betting,
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
        legal_raise_to_totals=amounts,
        joint_probabilities=context.joint_probabilities,
        showdown_signs=context.showdown_signs,
    )


def _task_for_subset(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    pool_index: int,
    ordinal: int,
    width: RaiseActionWidth,
    subset_index: int,
    amounts: tuple[KernelRaiseToTotal, ...],
) -> GreedySubsetTask:
    request = _greedy_request(
        context=context,
        amounts=amounts,
        width=width,
        subset_index=subset_index,
    )
    return GreedySubsetTask(
        ordinal=ordinal,
        panel_position=panel_position,
        pool_index=pool_index,
        context_semantic_digest=context.semantic_digest,
        raise_width=width,
        subset_index=subset_index,
        request=request,
        response_row_set=_response_row_set_for_request(
            context_semantic_digest=context.semantic_digest,
            request=request,
        ),
    )


@dataclass(frozen=True, slots=True)
class NonReplayGreedyCallSlot:
    call_index: int
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    target_raise_width: RaiseActionWidth
    candidate_position: int | None

    def __post_init__(self) -> None:
        _require_count(
            self.call_index,
            label="greedy call-slot index",
            maximum=ADR0337_GREEDY_CALL_COUNT - 1,
        )
        panel = _require_count(
            self.panel_position,
            label="greedy call-slot panel position",
            maximum=15,
        )
        if (
            self.pool_index != ADR0334_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("greedy call slot differs from panel membership")
        if not isinstance(self.target_raise_width, RaiseActionWidth):
            raise TypeError("greedy call slot requires a semantic raise width")
        if self.target_raise_width.count == 2:
            if self.candidate_position is not None:
                raise ValueError("greedy initial call slot cannot name a candidate")
        else:
            _require_count(
                self.candidate_position,
                label="greedy call-slot candidate position",
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
                    "target_raise_width": self.target_raise_width.count,
                    "version": "adr0337-nonreplay-greedy-call-slot-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class NonReplayClosedFiniteBlockSchedule:
    pool_sha256: str
    qualification_journal_sha256: str
    qualification_terminal_sha256: str
    panel_sha256: str
    teacher_artifact_sha256: str
    teacher_terminal_sha256: str
    teacher_result_sha256: str
    tasks: tuple[GreedySubsetTask, ...]
    transitions: tuple[ClosedFiniteBlockTransition, ...]
    call_slots: tuple[NonReplayGreedyCallSlot, ...]
    arm_counts_by_width: tuple[tuple[int, int], ...]
    transition_counts_by_target_width: tuple[tuple[int, int], ...]
    executed_candidate_counts_by_target_width: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("greedy schedule pool", self.pool_sha256),
            ("greedy schedule qualification journal", self.qualification_journal_sha256),
            ("greedy schedule qualification terminal", self.qualification_terminal_sha256),
            ("greedy schedule panel", self.panel_sha256),
            ("greedy schedule teacher artifact", self.teacher_artifact_sha256),
            ("greedy schedule teacher terminal", self.teacher_terminal_sha256),
            ("greedy schedule teacher result", self.teacher_result_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.qualification_journal_sha256
            != ADR0334_QUALIFICATION_ARTIFACT_SHA256
            or self.qualification_terminal_sha256
            != ADR0334_QUALIFICATION_TERMINAL_SHA256
            or self.panel_sha256 != ADR0334_QUALIFIED_PANEL_SHA256
            or self.teacher_artifact_sha256 != ADR0336_TEACHER_ARTIFACT_SHA256
            or self.teacher_terminal_sha256 != ADR0336_TEACHER_TERMINAL_SHA256
            or self.teacher_result_sha256 != ADR0336_TEACHER_RESULT_SHA256
        ):
            raise ValueError("greedy schedule belongs to another evidence chain")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0337_GREEDY_ARM_COUNT
            or any(not isinstance(task, GreedySubsetTask) for task in self.tasks)
        ):
            raise TypeError("greedy schedule requires all immutable subset arms")
        if tuple(task.ordinal for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("greedy task ordinals are not contiguous")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("greedy schedule repeats a semantic arm")
        if len({task.request_sha256 for task in self.tasks}) != len(self.tasks):
            raise ValueError("greedy schedule repeats an exact request")
        if (
            not isinstance(self.transitions, tuple)
            or len(self.transitions) != ADR0337_GREEDY_TRANSITION_COUNT
            or any(
                not isinstance(item, ClosedFiniteBlockTransition)
                for item in self.transitions
            )
        ):
            raise TypeError("greedy schedule requires all immutable transitions")
        if tuple(item.ordinal for item in self.transitions) != tuple(
            range(len(self.transitions))
        ):
            raise ValueError("greedy transition ordinals are not contiguous")
        if len({item.digest for item in self.transitions}) != len(self.transitions):
            raise ValueError("greedy schedule repeats a semantic transition")
        if (
            not isinstance(self.call_slots, tuple)
            or len(self.call_slots) != ADR0337_GREEDY_CALL_COUNT
            or any(not isinstance(item, NonReplayGreedyCallSlot) for item in self.call_slots)
            or tuple(item.call_index for item in self.call_slots)
            != tuple(range(ADR0337_GREEDY_CALL_COUNT))
            or len({item.digest for item in self.call_slots})
            != ADR0337_GREEDY_CALL_COUNT
        ):
            raise ValueError("greedy realized call-slot schedule drifted")
        if self.arm_counts_by_width != ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH:
            raise ValueError("greedy arm ledger drifted")
        if (
            self.transition_counts_by_target_width
            != ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        ):
            raise ValueError("greedy transition ledger drifted")
        if (
            self.executed_candidate_counts_by_target_width
            != ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
        ):
            raise ValueError("greedy executed-candidate ledger drifted")
        observed_arms = tuple(
            (width, sum(task.raise_width.count == width for task in self.tasks))
            for width, _ in ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH
        )
        observed_transitions = tuple(
            (
                width,
                sum(item.augmented.raise_width.count == width for item in self.transitions),
            )
            for width, _ in ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        )
        observed_calls = tuple(
            (
                width,
                sum(
                    item.target_raise_width.count == width
                    for item in self.call_slots
                    if item.candidate_position is not None
                ),
            )
            for width, _ in ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
        )
        if (
            observed_arms != self.arm_counts_by_width
            or observed_transitions != self.transition_counts_by_target_width
            or observed_calls != self.executed_candidate_counts_by_target_width
        ):
            raise ValueError("greedy ledgers differ from their semantic members")
        for panel_position, (pool_index, context_digest) in enumerate(
            zip(
                ADR0334_QUALIFIED_POOL_INDICES,
                ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
                strict=True,
            )
        ):
            context_tasks = self.tasks_for_context(panel_position)
            if any(
                task.pool_index != pool_index
                or task.context_semantic_digest != context_digest
                for task in context_tasks
            ):
                raise ValueError("greedy tasks differ from target-panel membership")
            width_two = tuple(
                task for task in context_tasks if task.raise_width.count == 2
            )
            if len(width_two) != 1 or width_two[0].subset_index != 0:
                raise ValueError("greedy context lacks one anchored initial arm")
            complete = self.complete_raise_to_totals(panel_position)
            expected_family = tuple(
                (
                    width.count,
                    subset_index,
                    tuple(value.chips for value in subset),
                )
                for width in ADR0323_RAISE_WIDTHS
                for subset_index, subset in enumerate(
                    anchored_raise_subset_family(complete, width).subsets
                )
            )
            observed_family = tuple(
                (task.raise_width.count, task.subset_index, task.raise_to_totals)
                for task in context_tasks
            )
            if observed_family != expected_family:
                raise ValueError("greedy context lost its anchored subset family")
            for parent in (
                task for task in context_tasks if task.raise_width.count < 6
            ):
                outgoing = self.outgoing(parent)
                omitted = tuple(
                    amount
                    for amount in complete
                    if amount not in parent.request.legal_raise_to_totals
                )
                if (
                    tuple(item.candidate_position for item in outgoing)
                    != tuple(range(len(outgoing)))
                    or tuple(item.proposed_raise_to_total for item in outgoing)
                    != omitted
                ):
                    raise ValueError("greedy omitted-raise order drifted")
        task_ordinals = {task.ordinal for task in self.tasks}
        if any(
            item.incumbent.ordinal not in task_ordinals
            or item.augmented.ordinal not in task_ordinals
            or self.tasks[item.incumbent.ordinal] != item.incumbent
            or self.tasks[item.augmented.ordinal] != item.augmented
            for item in self.transitions
        ):
            raise ValueError("greedy transition references an external task")

    def tasks_for_context(self, panel_position: int) -> tuple[GreedySubsetTask, ...]:
        _require_count(
            panel_position,
            label="greedy task lookup panel position",
            maximum=15,
        )
        return tuple(
            task for task in self.tasks if task.panel_position == panel_position
        )

    def initial_task(self, panel_position: int) -> GreedySubsetTask:
        candidates = tuple(
            task
            for task in self.tasks_for_context(panel_position)
            if task.raise_width.count == 2
        )
        if len(candidates) != 1:
            raise ValueError("greedy context has no unique initial task")
        return candidates[0]

    def outgoing(
        self,
        incumbent: GreedySubsetTask,
    ) -> tuple[ClosedFiniteBlockTransition, ...]:
        if not isinstance(incumbent, GreedySubsetTask):
            raise TypeError("greedy outgoing lookup requires a semantic task")
        return tuple(
            item
            for item in self.transitions
            if item.incumbent.ordinal == incumbent.ordinal
        )

    def complete_raise_to_totals(
        self,
        panel_position: int,
    ) -> tuple[KernelRaiseToTotal, ...]:
        context_tasks = self.tasks_for_context(panel_position)
        if not context_tasks:
            raise IndexError("greedy panel position is absent")
        return tuple(
            sorted(
                {
                    amount
                    for task in context_tasks
                    for amount in task.request.legal_raise_to_totals
                },
                key=lambda value: value.chips,
            )
        )

    def task_by_digest(self, digest: str) -> GreedySubsetTask:
        _require_digest(digest, label="greedy task lookup")
        matches = tuple(task for task in self.tasks if task.digest == digest)
        if len(matches) != 1:
            raise ValueError("greedy task digest is absent or ambiguous")
        return matches[0]

    def transition_by_digest(self, digest: str) -> ClosedFiniteBlockTransition:
        _require_digest(digest, label="greedy transition lookup")
        matches = tuple(item for item in self.transitions if item.digest == digest)
        if len(matches) != 1:
            raise ValueError("greedy transition digest is absent or ambiguous")
        return matches[0]

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "arm_counts_by_width": self.arm_counts_by_width,
                    "call_slot_sha256s": tuple(item.digest for item in self.call_slots),
                    "executed_candidate_counts_by_target_width": (
                        self.executed_candidate_counts_by_target_width
                    ),
                    "panel_sha256": self.panel_sha256,
                    "pool_sha256": self.pool_sha256,
                    "qualification_journal_sha256": self.qualification_journal_sha256,
                    "qualification_terminal_sha256": self.qualification_terminal_sha256,
                    "task_sha256s": tuple(task.digest for task in self.tasks),
                    "teacher_artifact_sha256": self.teacher_artifact_sha256,
                    "teacher_result_sha256": self.teacher_result_sha256,
                    "teacher_terminal_sha256": self.teacher_terminal_sha256,
                    "transition_counts_by_target_width": (
                        self.transition_counts_by_target_width
                    ),
                    "transition_sha256s": tuple(
                        item.digest for item in self.transitions
                    ),
                    "version": "adr0337-nonreplay-closed-finite-block-schedule-v1",
                }
            )
        ).hexdigest()


def build_adr0336_nonreplay_closed_finite_block_schedule(
) -> NonReplayClosedFiniteBlockSchedule:
    """Build the complete graph and call slots without invoking a value owner."""

    retained = verify_adr0334_nonreplay_qualification_result_artifact()
    pool = build_adr0331_nonreplay_pool()
    if retained.panel.digest != ADR0334_QUALIFIED_PANEL_SHA256:
        raise RuntimeError("ADR-0334 target panel identity drifted")
    tasks: list[GreedySubsetTask] = []
    context_maps: list[dict[tuple[int, ...], GreedySubsetTask]] = []
    for panel_position, pool_index in enumerate(retained.panel.pool_indices):
        context = pool.contexts[pool_index]
        task_map: dict[tuple[int, ...], GreedySubsetTask] = {}
        for width in ADR0323_RAISE_WIDTHS:
            family = anchored_raise_subset_family(
                context.complete_raise_to_totals,
                width,
            )
            for subset_index, subset in enumerate(family.subsets):
                task = _task_for_subset(
                    context=context,
                    panel_position=panel_position,
                    pool_index=pool_index,
                    ordinal=len(tasks),
                    width=width,
                    subset_index=subset_index,
                    amounts=subset,
                )
                tasks.append(task)
                task_map[tuple(value.chips for value in subset)] = task
        context_maps.append(task_map)

    transitions: list[ClosedFiniteBlockTransition] = []
    for panel_position, pool_index in enumerate(retained.panel.pool_indices):
        context = pool.contexts[pool_index]
        task_map = context_maps[panel_position]
        complete = context.complete_raise_to_totals
        for width in ADR0323_RAISE_WIDTHS[:-1]:
            for parent_subset in anchored_raise_subset_family(complete, width).subsets:
                incumbent = task_map[tuple(value.chips for value in parent_subset)]
                omitted = tuple(
                    value for value in complete if value not in parent_subset
                )
                for candidate_position, proposed in enumerate(omitted):
                    child = tuple(
                        sorted((*parent_subset, proposed), key=lambda value: value.chips)
                    )
                    augmented = task_map[tuple(value.chips for value in child)]
                    proposed_index = augmented.request.legal_raise_to_totals.index(
                        proposed
                    )
                    increment = augmented.response_row_set.reduced_bet_increments[
                        proposed_index
                    ]
                    block = OwnRaiseBlockIdentity(
                        context_semantic_digest=context.semantic_digest,
                        raise_to_total=proposed,
                        reduced_bet_increment=increment,
                        responder_private_range_width=ADR0323_PRIVATE_RANGE_WIDTH,
                        response_rows=_expected_response_rows(
                            context_semantic_digest=context.semantic_digest,
                            raise_to_totals=(proposed,),
                            reduced_bet_increments=(increment,),
                            private_width=ADR0323_PRIVATE_RANGE_WIDTH,
                        ),
                    )
                    transitions.append(
                        ClosedFiniteBlockTransition(
                            ordinal=len(transitions),
                            candidate_position=candidate_position,
                            incumbent=incumbent,
                            augmented=augmented,
                            proposed_raise_to_total=proposed,
                            proposed_reduced_bet_increment=increment,
                            own_block=block,
                            phase_order=ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
                        )
                    )

    call_slots: list[NonReplayGreedyCallSlot] = []
    for panel_position, pool_index in enumerate(retained.panel.pool_indices):
        context = pool.contexts[pool_index]
        call_slots.append(
            NonReplayGreedyCallSlot(
                call_index=len(call_slots),
                panel_position=panel_position,
                pool_index=pool_index,
                context_semantic_sha256=context.semantic_digest,
                target_raise_width=RaiseActionWidth(2),
                candidate_position=None,
            )
        )
        universe_width = len(context.complete_raise_to_totals)
        for target_width in range(3, 7):
            for candidate_position in range(universe_width - target_width + 1):
                call_slots.append(
                    NonReplayGreedyCallSlot(
                        call_index=len(call_slots),
                        panel_position=panel_position,
                        pool_index=pool_index,
                        context_semantic_sha256=context.semantic_digest,
                        target_raise_width=RaiseActionWidth(target_width),
                        candidate_position=candidate_position,
                    )
                )

    return NonReplayClosedFiniteBlockSchedule(
        pool_sha256=pool.digest,
        qualification_journal_sha256=ADR0334_QUALIFICATION_ARTIFACT_SHA256,
        qualification_terminal_sha256=ADR0334_QUALIFICATION_TERMINAL_SHA256,
        panel_sha256=retained.panel.digest,
        teacher_artifact_sha256=ADR0336_TEACHER_ARTIFACT_SHA256,
        teacher_terminal_sha256=ADR0336_TEACHER_TERMINAL_SHA256,
        teacher_result_sha256=ADR0336_TEACHER_RESULT_SHA256,
        tasks=tuple(tasks),
        transitions=tuple(transitions),
        call_slots=tuple(call_slots),
        arm_counts_by_width=ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH,
        transition_counts_by_target_width=(
            ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        ),
        executed_candidate_counts_by_target_width=(
            ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
        ),
    )


class NonReplayGreedyEvidenceKind(StrEnum):
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
class NonReplayGreedyArmEvidence:
    call_index: int
    slot_sha256: str
    task_sha256: str
    transition_sha256: str | None
    kind: NonReplayGreedyEvidenceKind
    synthetic: bool
    core_canonical_json: bytes

    def __post_init__(self) -> None:
        _require_count(
            self.call_index,
            label="greedy evidence call index",
            maximum=ADR0337_GREEDY_CALL_COUNT - 1,
        )
        _require_digest(self.slot_sha256, label="greedy evidence call slot")
        _require_digest(self.task_sha256, label="greedy evidence task")
        _require_digest(
            self.transition_sha256,
            label="greedy evidence transition",
            optional=True,
        )
        if not isinstance(self.kind, NonReplayGreedyEvidenceKind):
            raise TypeError("greedy evidence kind must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("greedy evidence synthetic flag must be Boolean")
        if not isinstance(self.core_canonical_json, bytes):
            raise TypeError("greedy evidence core bytes must be immutable")
        value = json.loads(self.core_canonical_json)
        if (
            not isinstance(value, dict)
            or frozenset(value) != _EVIDENCE_CORE_KEYS
            or canonical_journal_json_bytes(value) != self.core_canonical_json
        ):
            raise ValueError("greedy evidence core is not canonical")
        if (
            value.get("call_index") != self.call_index
            or value.get("slot_sha256") != self.slot_sha256
            or value.get("task_sha256") != self.task_sha256
            or value.get("transition_sha256") != self.transition_sha256
            or value.get("kind") != self.kind.value
            or value.get("synthetic") is not self.synthetic
            or value.get("version") != _EVIDENCE_VERSION
        ):
            raise ValueError("greedy evidence metadata differs from its core")

    @property
    def core(self) -> dict[str, object]:
        value = json.loads(self.core_canonical_json)
        if not isinstance(value, dict):
            raise AssertionError("greedy evidence core lost its object type")
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
            raise AssertionError("greedy evidence result lost its object type")
        if self.kind is NonReplayGreedyEvidenceKind.UNEXPECTED_EXCEPTION:
            return 0
        return _require_count(
            result["public_call_count"],
            label="greedy evidence public calls",
            maximum=1,
        )

    @property
    def invocation_count_complete(self) -> bool:
        return self.kind is not NonReplayGreedyEvidenceKind.UNEXPECTED_EXCEPTION

    def accepted_value(self, task: GreedySubsetTask) -> GreedyCertifiedValueEvidence:
        if self.kind is not NonReplayGreedyEvidenceKind.ACCEPTED:
            raise ValueError("only accepted greedy evidence has a value")
        result = self.core["result"]
        if not isinstance(result, dict):
            raise AssertionError("greedy accepted result lost its object type")
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
            reduced_bet_increments=tuple(
                result["reduced_bet_increments"]  # type: ignore[arg-type]
            ),
            feasible_behavioral_lower_bound_chips=_require_float_hex(
                result["feasible_lower_hex"],
                label="greedy accepted lower",
            ),
            certified_upper_bound_chips=_require_float_hex(
                result["certified_upper_hex"],
                label="greedy accepted upper",
            ),
            signed_certificate_gap_chips=_require_float_hex(
                result["signed_gap_hex"],
                label="greedy accepted signed gap",
            ),
            certified_gap_chips=_require_float_hex(
                result["certified_gap_hex"],
                label="greedy accepted certificate gap",
            ),
        )
        evidence.verify_task(task)
        return evidence


def _build_evidence(
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    kind: NonReplayGreedyEvidenceKind,
    synthetic: bool,
    result_payload: Mapping[str, object],
) -> NonReplayGreedyArmEvidence:
    if not isinstance(slot, NonReplayGreedyCallSlot):
        raise TypeError("greedy evidence requires a semantic call slot")
    if not isinstance(task, GreedySubsetTask):
        raise TypeError("greedy evidence requires a semantic task")
    if transition is not None and not isinstance(
        transition,
        ClosedFiniteBlockTransition,
    ):
        raise TypeError("greedy evidence transition must be semantic")
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
        "transition_sha256": None if transition is None else transition.digest,
        "version": _EVIDENCE_VERSION,
    }
    return NonReplayGreedyArmEvidence(
        call_index=slot.call_index,
        slot_sha256=slot.digest,
        task_sha256=task.digest,
        transition_sha256=None if transition is None else transition.digest,
        kind=kind,
        synthetic=synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )


def greedy_evidence_from_consumer_result(
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    result: object,
) -> NonReplayGreedyArmEvidence:
    if isinstance(result, CertifiedReducedSizingAcceptedV2):
        if result.request != task.request:
            raise ValueError("accepted greedy evidence belongs to another task")
        return _build_evidence(
            slot=slot,
            task=task,
            transition=transition,
            kind=NonReplayGreedyEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=_accepted_result_payload(result),
        )
    if isinstance(result, CertifiedReducedSizingRejectedV2):
        if result.request != task.request:
            raise ValueError("rejected greedy evidence belongs to another task")
        return _build_evidence(
            slot=slot,
            task=task,
            transition=transition,
            kind=NonReplayGreedyEvidenceKind.REJECTED,
            synthetic=False,
            result_payload=_rejected_result_payload(result),
        )
    raise TypeError("greedy consumer returned a nonsemantic result")


def _unexpected_evidence(
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    error: Exception,
    synthetic: bool,
) -> NonReplayGreedyArmEvidence:
    return _build_evidence(
        slot=slot,
        task=task,
        transition=transition,
        kind=NonReplayGreedyEvidenceKind.UNEXPECTED_EXCEPTION,
        synthetic=synthetic,
        result_payload={
            "exception_chain": _exception_payload(error),
            "invocation_count_complete": False,
            "synthetic_result": synthetic,
            "type": "unexpected_exception",
        },
    )


def _validate_evidence_against_invocation(
    evidence: NonReplayGreedyArmEvidence,
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    expect_synthetic: bool,
) -> None:
    core = evidence.core
    if (
        evidence.call_index != slot.call_index
        or evidence.slot_sha256 != slot.digest
        or evidence.task_sha256 != task.digest
        or evidence.transition_sha256
        != (None if transition is None else transition.digest)
        or evidence.synthetic is not expect_synthetic
        or core["candidate_position"] != slot.candidate_position
        or core["panel_position"] != task.panel_position
        or core["pool_index"] != task.pool_index
        or core["context_semantic_sha256"] != task.context_semantic_digest
        or core["raise_width"] != task.raise_width.count
    ):
        raise ValueError("greedy evidence differs from its realized invocation")
    if transition is None:
        if slot.candidate_position is not None or task.raise_width.count != 2:
            raise ValueError("greedy initial evidence has candidate semantics")
    elif (
        transition.augmented != task
        or transition.candidate_position != slot.candidate_position
        or transition.augmented.raise_width != slot.target_raise_width
    ):
        raise ValueError("greedy candidate evidence crosses its transition")
    result = core["result"]
    if not isinstance(result, dict):
        raise TypeError("greedy evidence result must be an object")
    if result.get("synthetic_result") is not expect_synthetic:
        raise ValueError("greedy evidence synthetic provenance drifted")

    if evidence.kind is NonReplayGreedyEvidenceKind.ACCEPTED:
        accepted = _require_exact_keys(
            result,
            _ACCEPTED_RESULT_KEYS,
            label="accepted greedy evidence",
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
            raise ValueError("accepted greedy evidence identity drifted")
        lower = _require_float_hex(
            accepted["feasible_lower_hex"],
            label="accepted greedy lower",
        )
        upper = _require_float_hex(
            accepted["certified_upper_hex"],
            label="accepted greedy upper",
        )
        signed_gap = _require_float_hex(
            accepted["signed_gap_hex"],
            label="accepted greedy signed gap",
        )
        gap = _require_float_hex(
            accepted["certified_gap_hex"],
            label="accepted greedy certificate gap",
        )
        if (
            lower > upper
            or signed_gap != upper - lower
            or gap != max(0.0, signed_gap)
        ):
            raise ValueError("accepted greedy interval drifted")
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
            raise ValueError("accepted greedy response witness is malformed")
        multiplier_values = accepted["raw_inequality_multipliers_hex"]
        if not isinstance(multiplier_values, list):
            raise TypeError("accepted greedy multipliers must be an array")
        multipliers = tuple(
            _require_float_hex(item, label="accepted greedy multiplier")
            for item in multiplier_values
        )
        expected_multiplier_count = (
            2 * len(task.request.joint_probabilities)
            + 2
            * len(task.request.joint_probabilities[0])
            * len(task.request.legal_raise_to_totals)
        )
        if len(multipliers) != expected_multiplier_count:
            raise ValueError("accepted greedy multiplier width drifted")
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
                raise ValueError("accepted greedy certificate width drifted")
        evidence.accepted_value(task)
    elif evidence.kind is NonReplayGreedyEvidenceKind.REJECTED:
        rejected = _require_exact_keys(
            result,
            _REJECTED_RESULT_KEYS,
            label="rejected greedy evidence",
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
            raise ValueError("rejected greedy evidence identity drifted")
        calls = _require_count(
            rejected["public_call_count"],
            label="rejected greedy public calls",
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
                label=f"rejected greedy {key}",
                optional=True,
            )
        _validate_exception_chain(
            rejected["exception_chain"],
            label="rejected greedy evidence",
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
            raise ValueError("rejected greedy stage/reason contract drifted")
        bound = _bind_request(task.request)
        if (
            rejected["request_sha256"] != bound.request_sha256
            or rejected["public_state_sha256"] != bound.public_state_sha256
            or rejected["legal_raise_set_sha256"] != bound.legal_raise_set_sha256
        ):
            raise ValueError("rejected greedy request identity drifted")
        source_expected = stage is not CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION
        if rejected["consumer_source_sha256"] != (
            ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ]
            if source_expected
            else None
        ):
            raise ValueError("rejected greedy source identity drifted")
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
            raise ValueError("rejected greedy invocation count drifted")
    else:
        unexpected = _require_exact_keys(
            result,
            _UNEXPECTED_RESULT_KEYS,
            label="unexpected greedy evidence",
        )
        if (
            unexpected["type"] != "unexpected_exception"
            or unexpected["invocation_count_complete"] is not False
        ):
            raise ValueError("unexpected greedy evidence claims complete calls")
        _validate_exception_chain(
            unexpected["exception_chain"],
            label="unexpected greedy evidence",
        )


def _rebind_evidence(
    payload: dict[str, object],
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    expect_synthetic: bool,
) -> NonReplayGreedyArmEvidence:
    core = _verify_sealed_payload(
        payload,
        digest_field="evidence_sha256",
        label="greedy observation",
    )
    call_index = _require_count(
        core.get("call_index"),
        label="greedy observation call index",
        maximum=ADR0337_GREEDY_CALL_COUNT - 1,
    )
    if call_index != slot.call_index:
        raise ValueError("greedy observation crossed its expected call slot")
    try:
        kind = NonReplayGreedyEvidenceKind(core["kind"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("greedy evidence has an unknown kind") from error
    evidence = NonReplayGreedyArmEvidence(
        call_index=call_index,
        slot_sha256=slot.digest,
        task_sha256=task.digest,
        transition_sha256=None if transition is None else transition.digest,
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


def synthetic_greedy_accepted_evidence(
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
    lower_chips: float,
    upper_chips: float,
) -> NonReplayGreedyArmEvidence:
    """Build fake accepted evidence without a consumer or solver call."""

    lower = float(lower_chips)
    upper = float(upper_chips)
    if not isfinite(lower) or not isfinite(upper) or lower > upper:
        raise ValueError("synthetic greedy endpoints are invalid")
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
        kind=NonReplayGreedyEvidenceKind.ACCEPTED,
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


def synthetic_greedy_rejected_evidence(
    *,
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
) -> NonReplayGreedyArmEvidence:
    bound = _bind_request(task.request)
    return _build_evidence(
        slot=slot,
        task=task,
        transition=transition,
        kind=NonReplayGreedyEvidenceKind.REJECTED,
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
                    "message": "synthetic adapter rejection",
                    "module": "pontius.synthetic",
                    "type_name": "SyntheticGreedyRejection",
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
class NonReplayGreedyTeacherReference:
    teacher_result_sha256: str
    context_result_sha256: str
    width_result_sha256: str
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    raise_width: RaiseActionWidth
    payoff_span_chips: int
    full_value: CertifiedChipValueInterval
    teacher_value: CertifiedChipValueInterval
    selected_subset_index: int
    selected_request_sha256: str
    selected_legal_raise_set_sha256: str
    selected_linear_program_sha256: str
    selected_raise_to_totals: tuple[int, ...]
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("greedy teacher result", self.teacher_result_sha256),
            ("greedy teacher context", self.context_result_sha256),
            ("greedy teacher width", self.width_result_sha256),
            ("greedy teacher semantic context", self.context_semantic_sha256),
            ("greedy teacher selected request", self.selected_request_sha256),
            ("greedy teacher selected legal set", self.selected_legal_raise_set_sha256),
            ("greedy teacher selected LP", self.selected_linear_program_sha256),
        ):
            _require_digest(value, label=label)
        panel = _require_count(
            self.panel_position,
            label="greedy teacher panel position",
            maximum=15,
        )
        if (
            self.pool_index != ADR0334_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("greedy teacher reference crosses panel membership")
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("greedy teacher reference requires a raise width")
        if self.raise_width.count not in range(3, 7):
            raise ValueError("greedy teacher reference width is outside three through six")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("greedy teacher reference payoff span is invalid")
        if not isinstance(self.full_value, CertifiedChipValueInterval) or not isinstance(
            self.teacher_value,
            CertifiedChipValueInterval,
        ):
            raise TypeError("greedy teacher reference requires chip-value intervals")
        _require_count(
            self.selected_subset_index,
            label="greedy teacher selected subset",
        )
        if (
            not isinstance(self.selected_raise_to_totals, tuple)
            or len(self.selected_raise_to_totals) != self.raise_width.count
            or any(
                isinstance(item, bool) or not isinstance(item, int) or item <= 0
                for item in self.selected_raise_to_totals
            )
            or tuple(sorted(self.selected_raise_to_totals))
            != self.selected_raise_to_totals
        ):
            raise ValueError("greedy teacher selected amounts are invalid")
        if not isinstance(self.synthetic, bool):
            raise TypeError("greedy teacher synthetic flag must be Boolean")
        if not self.synthetic and self.teacher_result_sha256 != (
            ADR0336_TEACHER_RESULT_SHA256
        ):
            raise ValueError("real greedy reference belongs to another teacher result")

    def verify_selected_task(self, task: GreedySubsetTask) -> None:
        if not isinstance(task, GreedySubsetTask):
            raise TypeError("greedy teacher rebinding requires a semantic task")
        observed = (
            task.panel_position,
            task.pool_index,
            task.context_semantic_digest,
            task.raise_width,
            task.subset_index,
            task.request_sha256,
            task.legal_raise_set_sha256,
            task.linear_program_sha256,
            task.raise_to_totals,
        )
        expected = (
            self.panel_position,
            self.pool_index,
            self.context_semantic_sha256,
            self.raise_width,
            self.selected_subset_index,
            self.selected_request_sha256,
            self.selected_legal_raise_set_sha256,
            self.selected_linear_program_sha256,
            self.selected_raise_to_totals,
        )
        if observed != expected:
            raise ValueError("greedy teacher reference differs from selected task")
        if self.payoff_span_chips != (
            task.request.betting.pot + 2 * task.request.betting.stacks[0]
        ):
            raise ValueError("greedy teacher reference reused stack as payoff span")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "context_result_sha256": self.context_result_sha256,
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "full_value": (
                        self.full_value.lower_chips.hex(),
                        self.full_value.upper_chips.hex(),
                    ),
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "raise_width": self.raise_width.count,
                    "selected_legal_raise_set_sha256": (
                        self.selected_legal_raise_set_sha256
                    ),
                    "selected_linear_program_sha256": (
                        self.selected_linear_program_sha256
                    ),
                    "selected_raise_to_totals": self.selected_raise_to_totals,
                    "selected_request_sha256": self.selected_request_sha256,
                    "selected_subset_index": self.selected_subset_index,
                    "synthetic": self.synthetic,
                    "teacher_result_sha256": self.teacher_result_sha256,
                    "teacher_value": (
                        self.teacher_value.lower_chips.hex(),
                        self.teacher_value.upper_chips.hex(),
                    ),
                    "version": "adr0337-nonreplay-greedy-teacher-reference-v1",
                    "width_result_sha256": self.width_result_sha256,
                }
            )
        ).hexdigest()


def _teacher_reference_for_selected(
    *,
    selected_task: GreedySubsetTask,
    teacher_result: RetainedNonReplayTeacherResult | None,
    synthetic: bool,
) -> NonReplayGreedyTeacherReference:
    if synthetic:
        synthetic_value = CertifiedChipValueInterval(
            lower_chips=100.0,
            upper_chips=100.0,
        )
        return NonReplayGreedyTeacherReference(
            teacher_result_sha256=sha256(
                b"adr0337-synthetic-greedy-teacher-result"
            ).hexdigest(),
            context_result_sha256=sha256(
                f"adr0337-synthetic-context-{selected_task.panel_position}".encode()
            ).hexdigest(),
            width_result_sha256=sha256(
                (
                    "adr0337-synthetic-width-"
                    f"{selected_task.panel_position}-{selected_task.raise_width.count}"
                ).encode()
            ).hexdigest(),
            panel_position=selected_task.panel_position,
            pool_index=selected_task.pool_index,
            context_semantic_sha256=selected_task.context_semantic_digest,
            raise_width=selected_task.raise_width,
            payoff_span_chips=(
                selected_task.request.betting.pot
                + 2 * selected_task.request.betting.stacks[0]
            ),
            full_value=synthetic_value,
            teacher_value=synthetic_value,
            selected_subset_index=selected_task.subset_index,
            selected_request_sha256=selected_task.request_sha256,
            selected_legal_raise_set_sha256=selected_task.legal_raise_set_sha256,
            selected_linear_program_sha256=selected_task.linear_program_sha256,
            selected_raise_to_totals=selected_task.raise_to_totals,
            synthetic=True,
        )
    if not isinstance(teacher_result, RetainedNonReplayTeacherResult):
        raise TypeError("real greedy reduction requires the retained teacher")
    teacher_context: NonReplayTeacherContextResult = teacher_result.journal.contexts[
        selected_task.panel_position
    ]
    teacher_width: NonReplayTeacherWidthResult = next(
        item
        for item in teacher_context.widths
        if item.raise_width == selected_task.raise_width
    )
    observation = teacher_width.subset_observations[selected_task.subset_index]
    teacher_task = observation.task
    expected = (
        teacher_task.panel_position,
        teacher_task.pool_index,
        teacher_task.context_semantic_digest,
        teacher_task.raise_width,
        teacher_task.subset_index,
        teacher_task.request_sha256,
        teacher_task.legal_raise_set_sha256,
        teacher_task.linear_program_sha256,
        teacher_task.raise_to_totals,
    )
    observed = (
        selected_task.panel_position,
        selected_task.pool_index,
        selected_task.context_semantic_digest,
        selected_task.raise_width,
        selected_task.subset_index,
        selected_task.request_sha256,
        selected_task.legal_raise_set_sha256,
        selected_task.linear_program_sha256,
        selected_task.raise_to_totals,
    )
    if observed != expected:
        raise ValueError("selected greedy arm lacks an exact teacher counterpart")
    reference = NonReplayGreedyTeacherReference(
        teacher_result_sha256=teacher_result.digest,
        context_result_sha256=teacher_context.digest,
        width_result_sha256=teacher_width.digest,
        panel_position=teacher_context.panel_position,
        pool_index=teacher_context.pool_index,
        context_semantic_sha256=teacher_context.context_semantic_sha256,
        raise_width=teacher_width.raise_width,
        payoff_span_chips=teacher_context.payoff_span_chips,
        full_value=teacher_context.full_value,
        teacher_value=teacher_width.envelope.value,
        selected_subset_index=selected_task.subset_index,
        selected_request_sha256=selected_task.request_sha256,
        selected_legal_raise_set_sha256=selected_task.legal_raise_set_sha256,
        selected_linear_program_sha256=selected_task.linear_program_sha256,
        selected_raise_to_totals=selected_task.raise_to_totals,
        synthetic=False,
    )
    reference.verify_selected_task(selected_task)
    return reference


@dataclass(frozen=True, slots=True)
class NonReplayGreedyRoundResult:
    target_raise_width: RaiseActionWidth
    incumbent_task: GreedySubsetTask
    incumbent: GreedyCertifiedValueEvidence
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]
    selected_candidate_position: int
    teacher_reference: NonReplayGreedyTeacherReference
    full_regret: CertifiedChipRegretInterval
    normalized_full_regret: NormalizedTeacherRegretInterval
    teacher_excess: CertifiedGreedyTeacherExcessInterval
    normalized_teacher_excess: NormalizedGreedyTeacherExcessInterval

    def __post_init__(self) -> None:
        if not isinstance(self.target_raise_width, RaiseActionWidth):
            raise TypeError("greedy round requires a semantic target width")
        if self.target_raise_width.count not in range(3, 7):
            raise ValueError("greedy round target lies outside three through six")
        if (
            not isinstance(self.incumbent_task, GreedySubsetTask)
            or self.incumbent_task.raise_width.count
            != self.target_raise_width.count - 1
        ):
            raise ValueError("greedy round incumbent has the wrong width")
        if not isinstance(self.incumbent, GreedyCertifiedValueEvidence):
            raise TypeError("greedy round requires incumbent value evidence")
        self.incumbent.verify_task(self.incumbent_task)
        if not isinstance(self.candidates, tuple) or not self.candidates:
            raise TypeError("greedy round requires immutable candidate evidence")
        bounds = self.incumbent_task.request.betting.legal_decision().raise_bounds
        if bounds is None:
            raise ValueError("greedy round incumbent lacks a legal universe")
        universe_width = bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        if len(self.candidates) != universe_width - self.incumbent_task.raise_width.count:
            raise ValueError("greedy round candidate set is incomplete")
        for candidate in self.candidates:
            if (
                candidate.transition.incumbent != self.incumbent_task
                or candidate.incumbent_value_sha256 != self.incumbent.digest
                or candidate.transition.augmented.raise_width
                != self.target_raise_width
            ):
                raise ValueError("greedy round candidate chain drifted")
        selected = select_greedy_candidate(self.candidates)
        position = _require_count(
            self.selected_candidate_position,
            label="greedy round selected position",
        )
        if position >= len(self.candidates) or self.candidates[position] != selected:
            raise ValueError("greedy round changed lower-bound/smaller-raise selection")
        if not isinstance(self.teacher_reference, NonReplayGreedyTeacherReference):
            raise TypeError("greedy round requires teacher evidence")
        self.teacher_reference.verify_selected_task(selected.transition.augmented)
        expected_full = certified_full_minus_subset_regret(
            full=self.teacher_reference.full_value,
            subset=selected.augmented.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_normalized_full = normalize_full_regret(
            expected_full,
            payoff_span_chips=self.teacher_reference.payoff_span_chips,
        )
        expected_excess = certified_greedy_teacher_excess(
            teacher=self.teacher_reference.teacher_value,
            greedy=selected.augmented.value,
        )
        expected_normalized_excess = normalize_greedy_teacher_excess(
            expected_excess,
            payoff_span_chips=self.teacher_reference.payoff_span_chips,
        )
        if (
            self.full_regret != expected_full
            or self.normalized_full_regret != expected_normalized_full
            or self.teacher_excess != expected_excess
            or self.normalized_teacher_excess != expected_normalized_excess
        ):
            raise ValueError("greedy round regret or teacher excess drifted")

    @property
    def selected(self) -> ClosedFiniteBlockCandidateEvidence:
        return self.candidates[self.selected_candidate_position]

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "candidate_sha256s": tuple(item.digest for item in self.candidates),
                    "full_regret": (
                        self.full_regret.nonnegative_lower_chips.hex(),
                        self.full_regret.nonnegative_upper_chips.hex(),
                        self.full_regret.signed_lower_chips.hex(),
                        self.full_regret.signed_upper_chips.hex(),
                    ),
                    "incumbent_task_sha256": self.incumbent_task.digest,
                    "incumbent_value_sha256": self.incumbent.digest,
                    "normalized_full_regret": (
                        self.normalized_full_regret.lower.hex(),
                        self.normalized_full_regret.upper.hex(),
                    ),
                    "normalized_teacher_excess": (
                        self.normalized_teacher_excess.lower.hex(),
                        self.normalized_teacher_excess.upper.hex(),
                    ),
                    "selected_candidate_position": self.selected_candidate_position,
                    "target_raise_width": self.target_raise_width.count,
                    "teacher_excess": (
                        self.teacher_excess.nonnegative_lower_chips.hex(),
                        self.teacher_excess.nonnegative_upper_chips.hex(),
                        self.teacher_excess.signed_lower_chips.hex(),
                        self.teacher_excess.signed_upper_chips.hex(),
                    ),
                    "teacher_reference_sha256": self.teacher_reference.digest,
                    "version": "adr0337-nonreplay-greedy-round-v1",
                }
            )
        ).hexdigest()


def _build_round_result(
    *,
    target_raise_width: RaiseActionWidth,
    incumbent_task: GreedySubsetTask,
    incumbent: GreedyCertifiedValueEvidence,
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...],
    teacher_result: RetainedNonReplayTeacherResult | None,
    synthetic: bool,
) -> NonReplayGreedyRoundResult:
    selected = select_greedy_candidate(candidates)
    reference = _teacher_reference_for_selected(
        selected_task=selected.transition.augmented,
        teacher_result=teacher_result,
        synthetic=synthetic,
    )
    full_regret = certified_full_minus_subset_regret(
        full=reference.full_value,
        subset=selected.augmented.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    excess = certified_greedy_teacher_excess(
        teacher=reference.teacher_value,
        greedy=selected.augmented.value,
    )
    return NonReplayGreedyRoundResult(
        target_raise_width=target_raise_width,
        incumbent_task=incumbent_task,
        incumbent=incumbent,
        candidates=candidates,
        selected_candidate_position=selected.transition.candidate_position,
        teacher_reference=reference,
        full_regret=full_regret,
        normalized_full_regret=normalize_full_regret(
            full_regret,
            payoff_span_chips=reference.payoff_span_chips,
        ),
        teacher_excess=excess,
        normalized_teacher_excess=normalize_greedy_teacher_excess(
            excess,
            payoff_span_chips=reference.payoff_span_chips,
        ),
    )


@dataclass(frozen=True, slots=True)
class NonReplayGreedyContextResult:
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    payoff_span_chips: int
    initial_task: GreedySubsetTask
    initial_evidence_sha256: str
    initial: GreedyCertifiedValueEvidence
    rounds: tuple[NonReplayGreedyRoundResult, ...]

    def __post_init__(self) -> None:
        panel = _require_count(
            self.panel_position,
            label="greedy context panel position",
            maximum=15,
        )
        if (
            self.pool_index != ADR0334_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("greedy context differs from panel membership")
        _require_digest(self.initial_evidence_sha256, label="greedy initial evidence")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("greedy context payoff span is invalid")
        if (
            not isinstance(self.initial_task, GreedySubsetTask)
            or self.initial_task.raise_width.count != 2
            or self.initial_task.subset_index != 0
            or self.initial_task.panel_position != self.panel_position
            or self.initial_task.pool_index != self.pool_index
            or self.initial_task.context_semantic_digest
            != self.context_semantic_sha256
        ):
            raise ValueError("greedy context has the wrong initial task")
        if not isinstance(self.initial, GreedyCertifiedValueEvidence):
            raise TypeError("greedy context requires initial value evidence")
        self.initial.verify_task(self.initial_task)
        if (
            not isinstance(self.rounds, tuple)
            or tuple(item.target_raise_width.count for item in self.rounds)
            != (3, 4, 5, 6)
        ):
            raise ValueError("greedy context requires widths three through six")
        incumbent_task = self.initial_task
        incumbent = self.initial
        for round_result in self.rounds:
            if (
                round_result.incumbent_task != incumbent_task
                or round_result.incumbent != incumbent
                or round_result.teacher_reference.panel_position
                != self.panel_position
                or round_result.teacher_reference.pool_index != self.pool_index
                or round_result.teacher_reference.context_semantic_sha256
                != self.context_semantic_sha256
                or round_result.teacher_reference.payoff_span_chips
                != self.payoff_span_chips
            ):
                raise ValueError("greedy context round chain drifted")
            incumbent_task = round_result.selected.transition.augmented
            incumbent = round_result.selected.augmented

    @property
    def public_call_count(self) -> int:
        return 1 + sum(len(item.candidates) for item in self.rounds)

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "initial_evidence_sha256": self.initial_evidence_sha256,
                    "initial_task_sha256": self.initial_task.digest,
                    "initial_value_sha256": self.initial.digest,
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "round_sha256s": tuple(item.digest for item in self.rounds),
                    "version": "adr0337-nonreplay-greedy-context-v1",
                }
            )
        ).hexdigest()


def _build_width_gate_result(
    *,
    raise_width: RaiseActionWidth,
    contexts: tuple[NonReplayGreedyContextResult, ...],
) -> GreedyWidthGateResult:
    if (
        not isinstance(contexts, tuple)
        or len(contexts) != 16
        or tuple(item.panel_position for item in contexts) != tuple(range(16))
    ):
        raise ValueError("greedy width gate requires the complete panel")
    rounds = tuple(
        next(
            round_result
            for round_result in context.rounds
            if round_result.target_raise_width == raise_width
        )
        for context in contexts
    )
    recovery: ConservativeAggregateRecoveryInterval = conservative_aggregate_recovery(
        full_values=tuple(item.teacher_reference.full_value for item in rounds),
        baseline_values=tuple(context.initial.value for context in contexts),
        greedy_values=tuple(item.selected.augmented.value for item in rounds),
    )
    maximum_full = max(item.normalized_full_regret.upper for item in rounds)
    mean_full_lower = sum(
        item.normalized_full_regret.lower for item in rounds
    ) / len(rounds)
    mean_full_upper = sum(
        item.normalized_full_regret.upper for item in rounds
    ) / len(rounds)
    maximum_excess = max(item.normalized_teacher_excess.upper for item in rounds)
    mean_excess_lower = sum(
        item.normalized_teacher_excess.lower for item in rounds
    ) / len(rounds)
    mean_excess_upper = sum(
        item.normalized_teacher_excess.upper for item in rounds
    ) / len(rounds)
    return GreedyWidthGateResult(
        raise_width=raise_width,
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


class NonReplayGreedyStopReason(StrEnum):
    COMPLETED_SELECTED = "completed_selected"
    COMPLETED_NO_WIDTH = "completed_no_width"
    CONSUMER_REJECTED = "consumer_rejected"
    NUMERICAL_REJECTED = "numerical_rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


class NonReplayGreedyFailureStage(StrEnum):
    INITIAL_ARM = "initial_arm"
    CANDIDATE_ARM = "candidate_arm"
    CANDIDATE_PRICE = "candidate_price"
    ROUND_REDUCTION = "round_reduction"
    CAMPAIGN_REDUCTION = "campaign_reduction"


@dataclass(frozen=True, slots=True)
class NonReplayGreedyPartialContext:
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    payoff_span_chips: int
    initial_task: GreedySubsetTask
    initial_evidence_sha256: str | None
    initial: GreedyCertifiedValueEvidence | None
    completed_rounds: tuple[NonReplayGreedyRoundResult, ...]
    incomplete_candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]

    def __post_init__(self) -> None:
        panel = _require_count(
            self.panel_position,
            label="partial greedy panel position",
            maximum=15,
        )
        if (
            self.pool_index != ADR0334_QUALIFIED_POOL_INDICES[panel]
            or self.context_semantic_sha256
            != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel]
        ):
            raise ValueError("partial greedy context differs from panel membership")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("partial greedy payoff span is invalid")
        if (
            not isinstance(self.initial_task, GreedySubsetTask)
            or self.initial_task.panel_position != panel
            or self.initial_task.pool_index != self.pool_index
            or self.initial_task.context_semantic_digest
            != self.context_semantic_sha256
            or self.initial_task.raise_width.count != 2
            or self.initial_task.subset_index != 0
        ):
            raise ValueError("partial greedy initial task drifted")
        _require_digest(
            self.initial_evidence_sha256,
            label="partial greedy initial evidence",
            optional=True,
        )
        if not isinstance(self.completed_rounds, tuple) or any(
            not isinstance(item, NonReplayGreedyRoundResult)
            for item in self.completed_rounds
        ):
            raise TypeError("partial greedy rounds are not semantic")
        if not isinstance(self.incomplete_candidates, tuple) or any(
            not isinstance(item, ClosedFiniteBlockCandidateEvidence)
            for item in self.incomplete_candidates
        ):
            raise TypeError("partial greedy candidates are not semantic")
        if self.initial is None:
            if (
                self.initial_evidence_sha256 is not None
                or self.completed_rounds
                or self.incomplete_candidates
            ):
                raise ValueError("partial greedy candidate chain lacks its initial arm")
            return
        if not isinstance(self.initial, GreedyCertifiedValueEvidence):
            raise TypeError("partial greedy initial value is not semantic")
        self.initial.verify_task(self.initial_task)
        if self.initial_evidence_sha256 is None:
            raise ValueError("partial greedy initial value lacks raw evidence")
        if tuple(
            item.target_raise_width.count for item in self.completed_rounds
        ) != tuple(range(3, 3 + len(self.completed_rounds))):
            raise ValueError("partial greedy rounds are not a width prefix")
        incumbent_task = self.initial_task
        incumbent = self.initial
        for round_result in self.completed_rounds:
            if (
                round_result.incumbent_task != incumbent_task
                or round_result.incumbent != incumbent
            ):
                raise ValueError("partial greedy completed-round chain drifted")
            incumbent_task = round_result.selected.transition.augmented
            incumbent = round_result.selected.augmented
        if self.incomplete_candidates and (
            tuple(
                item.transition.candidate_position
                for item in self.incomplete_candidates
            )
            != tuple(range(len(self.incomplete_candidates)))
            or any(
                item.transition.incumbent != incumbent_task
                or item.incumbent_value_sha256 != incumbent.digest
                for item in self.incomplete_candidates
            )
        ):
            raise ValueError("partial greedy candidate prefix drifted")

    @property
    def incumbent_task(self) -> GreedySubsetTask:
        if self.initial is None:
            return self.initial_task
        if self.completed_rounds:
            return self.completed_rounds[-1].selected.transition.augmented
        return self.initial_task

    @property
    def incumbent(self) -> GreedyCertifiedValueEvidence | None:
        if self.completed_rounds:
            return self.completed_rounds[-1].selected.augmented
        return self.initial

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "completed_round_sha256s": tuple(
                        item.digest for item in self.completed_rounds
                    ),
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "incomplete_candidate_sha256s": tuple(
                        item.digest for item in self.incomplete_candidates
                    ),
                    "initial_evidence_sha256": self.initial_evidence_sha256,
                    "initial_task_sha256": self.initial_task.digest,
                    "initial_value_sha256": (
                        None if self.initial is None else self.initial.digest
                    ),
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "version": "adr0337-nonreplay-greedy-partial-context-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class _DerivedGreedyState:
    evidences: tuple[NonReplayGreedyArmEvidence, ...]
    contexts: tuple[NonReplayGreedyContextResult, ...]
    partial_context: NonReplayGreedyPartialContext | None
    width_gates: tuple[GreedyWidthGateResult, ...]
    selected_raise_width: RaiseActionWidth | None
    stop_reason: NonReplayGreedyStopReason | None
    failure_stage: NonReplayGreedyFailureStage | None
    failure_exception_chain: tuple[dict[str, str], ...]
    known_public_call_count: int
    invocation_count_complete: bool


def _empty_derived_state() -> _DerivedGreedyState:
    return _DerivedGreedyState(
        evidences=(),
        contexts=(),
        partial_context=None,
        width_gates=(),
        selected_raise_width=None,
        stop_reason=None,
        failure_stage=None,
        failure_exception_chain=(),
        known_public_call_count=0,
        invocation_count_complete=True,
    )


def _next_invocation(
    state: _DerivedGreedyState,
    *,
    schedule: NonReplayClosedFiniteBlockSchedule,
) -> tuple[
    NonReplayGreedyCallSlot,
    GreedySubsetTask,
    ClosedFiniteBlockTransition | None,
]:
    if state.stop_reason is not None:
        raise ValueError("greedy invocation requested after a terminal stop")
    call_index = len(state.evidences)
    if call_index >= ADR0337_GREEDY_CALL_COUNT:
        raise ValueError("greedy invocation exceeds its exact call schedule")
    slot = schedule.call_slots[call_index]
    partial = state.partial_context
    if partial is None:
        panel_position = len(state.contexts)
        if panel_position >= 16:
            raise ValueError("greedy complete panel lacks its terminal reduction")
        task = schedule.initial_task(panel_position)
        transition = None
    else:
        incumbent = partial.incumbent_task
        outgoing = schedule.outgoing(incumbent)
        candidate_position = len(partial.incomplete_candidates)
        if candidate_position >= len(outgoing):
            raise ValueError("greedy candidate prefix should already be reduced")
        transition = outgoing[candidate_position]
        task = transition.augmented
    if (
        slot.panel_position != task.panel_position
        or slot.pool_index != task.pool_index
        or slot.context_semantic_sha256 != task.context_semantic_digest
        or slot.target_raise_width != task.raise_width
        or slot.candidate_position
        != (None if transition is None else transition.candidate_position)
    ):
        raise ValueError("greedy dynamic invocation differs from its frozen call slot")
    return slot, task, transition


def _partial_for_initial(
    *,
    task: GreedySubsetTask,
    pool: FreshActionWidthNonReplayPool,
    evidence: NonReplayGreedyArmEvidence | None,
    initial: GreedyCertifiedValueEvidence | None,
) -> NonReplayGreedyPartialContext:
    context = pool.contexts[task.pool_index]
    return NonReplayGreedyPartialContext(
        panel_position=task.panel_position,
        pool_index=task.pool_index,
        context_semantic_sha256=task.context_semantic_digest,
        payoff_span_chips=context.payoff_span_chips,
        initial_task=task,
        initial_evidence_sha256=None if evidence is None else evidence.digest,
        initial=initial,
        completed_rounds=(),
        incomplete_candidates=(),
    )


def _state_with_stop(
    state: _DerivedGreedyState,
    *,
    evidence: NonReplayGreedyArmEvidence,
    partial_context: NonReplayGreedyPartialContext | None,
    reason: NonReplayGreedyStopReason,
    stage: NonReplayGreedyFailureStage,
    exception_chain: tuple[dict[str, str], ...] = (),
) -> _DerivedGreedyState:
    return _DerivedGreedyState(
        evidences=state.evidences + (evidence,),
        contexts=state.contexts,
        partial_context=partial_context,
        width_gates=(),
        selected_raise_width=None,
        stop_reason=reason,
        failure_stage=stage,
        failure_exception_chain=exception_chain,
        known_public_call_count=(
            state.known_public_call_count + evidence.public_call_count
        ),
        invocation_count_complete=(
            state.invocation_count_complete and evidence.invocation_count_complete
        ),
    )


def _advance_state(
    state: _DerivedGreedyState,
    evidence: NonReplayGreedyArmEvidence,
    *,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayClosedFiniteBlockSchedule,
    teacher_result: RetainedNonReplayTeacherResult | None,
    synthetic: bool,
) -> _DerivedGreedyState:
    slot, task, transition = _next_invocation(state, schedule=schedule)
    _validate_evidence_against_invocation(
        evidence,
        slot=slot,
        task=task,
        transition=transition,
        expect_synthetic=synthetic,
    )
    partial = state.partial_context
    failure_stage = (
        NonReplayGreedyFailureStage.INITIAL_ARM
        if transition is None
        else NonReplayGreedyFailureStage.CANDIDATE_ARM
    )
    if partial is None:
        partial = _partial_for_initial(
            task=task,
            pool=pool,
            evidence=None,
            initial=None,
        )
    if evidence.kind is NonReplayGreedyEvidenceKind.UNEXPECTED_EXCEPTION:
        return _state_with_stop(
            state,
            evidence=evidence,
            partial_context=partial,
            reason=NonReplayGreedyStopReason.UNEXPECTED_EXCEPTION,
            stage=failure_stage,
        )
    if evidence.kind is NonReplayGreedyEvidenceKind.REJECTED:
        return _state_with_stop(
            state,
            evidence=evidence,
            partial_context=partial,
            reason=NonReplayGreedyStopReason.CONSUMER_REJECTED,
            stage=failure_stage,
        )

    accepted = evidence.accepted_value(task)
    evidences = state.evidences + (evidence,)
    known_calls = state.known_public_call_count + evidence.public_call_count
    if transition is None:
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=state.contexts,
            partial_context=_partial_for_initial(
                task=task,
                pool=pool,
                evidence=evidence,
                initial=accepted,
            ),
            width_gates=(),
            selected_raise_width=None,
            stop_reason=None,
            failure_stage=None,
            failure_exception_chain=(),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    incumbent = partial.incumbent
    if incumbent is None:
        raise ValueError("greedy candidate lacks an accepted incumbent")
    try:
        candidate = build_closed_finite_block_candidate(
            transition=transition,
            incumbent=incumbent,
            augmented=accepted,
        )
    except (ArithmeticError, ValueError) as error:
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=state.contexts,
            partial_context=partial,
            width_gates=(),
            selected_raise_width=None,
            stop_reason=NonReplayGreedyStopReason.NUMERICAL_REJECTED,
            failure_stage=NonReplayGreedyFailureStage.CANDIDATE_PRICE,
            failure_exception_chain=_exception_payload(error),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    candidates = partial.incomplete_candidates + (candidate,)
    outgoing = schedule.outgoing(partial.incumbent_task)
    if len(candidates) < len(outgoing):
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=state.contexts,
            partial_context=NonReplayGreedyPartialContext(
                panel_position=partial.panel_position,
                pool_index=partial.pool_index,
                context_semantic_sha256=partial.context_semantic_sha256,
                payoff_span_chips=partial.payoff_span_chips,
                initial_task=partial.initial_task,
                initial_evidence_sha256=partial.initial_evidence_sha256,
                initial=partial.initial,
                completed_rounds=partial.completed_rounds,
                incomplete_candidates=candidates,
            ),
            width_gates=(),
            selected_raise_width=None,
            stop_reason=None,
            failure_stage=None,
            failure_exception_chain=(),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    if len(candidates) != len(outgoing):
        raise AssertionError("greedy candidate count crossed its exact round boundary")
    try:
        round_result = _build_round_result(
            target_raise_width=task.raise_width,
            incumbent_task=partial.incumbent_task,
            incumbent=incumbent,
            candidates=candidates,
            teacher_result=teacher_result,
            synthetic=synthetic,
        )
    except (ArithmeticError, ValueError) as error:
        failed_partial = NonReplayGreedyPartialContext(
            panel_position=partial.panel_position,
            pool_index=partial.pool_index,
            context_semantic_sha256=partial.context_semantic_sha256,
            payoff_span_chips=partial.payoff_span_chips,
            initial_task=partial.initial_task,
            initial_evidence_sha256=partial.initial_evidence_sha256,
            initial=partial.initial,
            completed_rounds=partial.completed_rounds,
            incomplete_candidates=candidates,
        )
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=state.contexts,
            partial_context=failed_partial,
            width_gates=(),
            selected_raise_width=None,
            stop_reason=NonReplayGreedyStopReason.NUMERICAL_REJECTED,
            failure_stage=NonReplayGreedyFailureStage.ROUND_REDUCTION,
            failure_exception_chain=_exception_payload(error),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    rounds = partial.completed_rounds + (round_result,)
    if task.raise_width.count < 6:
        next_partial = NonReplayGreedyPartialContext(
            panel_position=partial.panel_position,
            pool_index=partial.pool_index,
            context_semantic_sha256=partial.context_semantic_sha256,
            payoff_span_chips=partial.payoff_span_chips,
            initial_task=partial.initial_task,
            initial_evidence_sha256=partial.initial_evidence_sha256,
            initial=partial.initial,
            completed_rounds=rounds,
            incomplete_candidates=(),
        )
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=state.contexts,
            partial_context=next_partial,
            width_gates=(),
            selected_raise_width=None,
            stop_reason=None,
            failure_stage=None,
            failure_exception_chain=(),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    if partial.initial is None or partial.initial_evidence_sha256 is None:
        raise AssertionError("complete greedy context lost its initial arm")
    context_result = NonReplayGreedyContextResult(
        panel_position=partial.panel_position,
        pool_index=partial.pool_index,
        context_semantic_sha256=partial.context_semantic_sha256,
        payoff_span_chips=partial.payoff_span_chips,
        initial_task=partial.initial_task,
        initial_evidence_sha256=partial.initial_evidence_sha256,
        initial=partial.initial,
        rounds=rounds,
    )
    contexts = state.contexts + (context_result,)
    if len(contexts) < 16:
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=contexts,
            partial_context=None,
            width_gates=(),
            selected_raise_width=None,
            stop_reason=None,
            failure_stage=None,
            failure_exception_chain=(),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    try:
        gates = tuple(
            _build_width_gate_result(raise_width=width, contexts=contexts)
            for width in ADR0323_RAISE_WIDTHS[1:]
        )
    except (ArithmeticError, ValueError) as error:
        return _DerivedGreedyState(
            evidences=evidences,
            contexts=contexts,
            partial_context=None,
            width_gates=(),
            selected_raise_width=None,
            stop_reason=NonReplayGreedyStopReason.NUMERICAL_REJECTED,
            failure_stage=NonReplayGreedyFailureStage.CAMPAIGN_REDUCTION,
            failure_exception_chain=_exception_payload(error),
            known_public_call_count=known_calls,
            invocation_count_complete=state.invocation_count_complete,
        )
    passing = tuple(item for item in gates if item.passes)
    selected_width = None if not passing else passing[0].raise_width
    return _DerivedGreedyState(
        evidences=evidences,
        contexts=contexts,
        partial_context=None,
        width_gates=gates,
        selected_raise_width=selected_width,
        stop_reason=(
            NonReplayGreedyStopReason.COMPLETED_NO_WIDTH
            if selected_width is None
            else NonReplayGreedyStopReason.COMPLETED_SELECTED
        ),
        failure_stage=None,
        failure_exception_chain=(),
        known_public_call_count=known_calls,
        invocation_count_complete=state.invocation_count_complete,
    )


def _derive_state(
    evidences: tuple[NonReplayGreedyArmEvidence, ...],
    *,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayClosedFiniteBlockSchedule,
    teacher_result: RetainedNonReplayTeacherResult | None,
    synthetic: bool,
) -> _DerivedGreedyState:
    state = _empty_derived_state()
    for evidence in evidences:
        state = _advance_state(
            state,
            evidence,
            pool=pool,
            schedule=schedule,
            teacher_result=teacher_result,
            synthetic=synthetic,
        )
    return state


class NonReplayGreedyExecutionPhase(StrEnum):
    HEADER_APPEND = "header_append"
    NEXT_CALL_AUTHORIZATION = "next_call_authorization"
    ARM_EVIDENCE = "arm_evidence"
    OBSERVATION_APPEND = "observation_append"
    SEMANTIC_REDUCTION = "semantic_reduction"
    TERMINAL_APPEND = "terminal_append"
    JOURNAL_CLOSE = "journal_close"
    FINAL_REBIND = "final_rebind"


_GREEDY_PROTOCOL_PAYLOAD = {
    "adaptive_graph": "all-anchored-parent-plus-one-raise-transitions",
    "aggregate_recovery": (
        "sum-achieved-chip-endpoints/sum-available-chip-endpoints-before-division"
    ),
    "arm_count": ADR0337_GREEDY_ARM_COUNT,
    "arm_counts_by_width": ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH,
    "artifact_relative_path": ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH,
    "candidate_order": "omitted-kernel-raise-to-total-ascending",
    "call_count": ADR0337_GREEDY_CALL_COUNT,
    "consumer": "certified-reduced-sizing-v2-one-public-highs-ds-call",
    "consumer_failure": "stop-no-retry-no-fallback-no-skip",
    "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    "evidence_version": _EVIDENCE_VERSION,
    "executed_candidate_counts_by_target_width": (
        ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
    ),
    "execution_phases": tuple(item.value for item in NonReplayGreedyExecutionPhase),
    "finite_block_price": "[L_aug-U_inc,U_aug-L_inc]",
    "header_version": _HEADER_VERSION,
    "maximum_normalized_full_regret_limit_hex": (
        ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value.hex()
    ),
    "maximum_normalized_teacher_excess_limit_hex": (
        ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT.value.hex()
    ),
    "mean_normalized_full_regret_limit_hex": (
        ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value.hex()
    ),
    "mean_normalized_teacher_excess_limit_hex": (
        ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT.value.hex()
    ),
    "minimum_aggregate_recovery_floor_hex": (
        ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR.value.hex()
    ),
    "next_call_authority": "exact-preceding-post-fsync-receipt",
    "normalizer": "pot+2*effective_stack",
    "panel_context_sha256s": ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
    "panel_pool_indices": ADR0334_QUALIFIED_POOL_INDICES,
    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
    "phase_order": tuple(
        item.value for item in ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER
    ),
    "qualification_journal_sha256": ADR0334_QUALIFICATION_ARTIFACT_SHA256,
    "qualification_terminal_sha256": ADR0334_QUALIFICATION_TERMINAL_SHA256,
    "response_closure": (
        "every-admitted-raise-x-every-h4-responder-type-x-fold-and-call"
    ),
    "response_model": ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY.value,
    "selection": (
        "greatest-feasible-behavioral-lower-endpoint-then-smallest-raise-to"
    ),
    "selected_width": "smallest-width-three-through-six-passing-all-five-gates",
    "stop_reasons": tuple(item.value for item in NonReplayGreedyStopReason),
    "teacher_artifact_sha256": ADR0336_TEACHER_ARTIFACT_SHA256,
    "teacher_excess": "[L_teacher-U_greedy,U_teacher-L_greedy]",
    "teacher_result_sha256": ADR0336_TEACHER_RESULT_SHA256,
    "teacher_terminal_sha256": ADR0336_TEACHER_TERMINAL_SHA256,
    "terminal_version": _TERMINAL_VERSION,
    "transition_count": ADR0337_GREEDY_TRANSITION_COUNT,
    "transition_counts_by_target_width": (
        ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
    ),
    "value_witness": "exact-policy-lower-plus-dual-certificate-upper",
    "version": "adr0337-nonreplay-closed-finite-block-greedy-protocol-v1",
}
ADR0337_GREEDY_PROTOCOL = MappingProxyType(_GREEDY_PROTOCOL_PAYLOAD)
ADR0337_GREEDY_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_GREEDY_PROTOCOL_PAYLOAD)
).hexdigest()


def _preflight_adr0337_greedy_source_and_schedule(
) -> tuple[str, NonReplayClosedFiniteBlockSchedule]:
    from .fresh_action_width_nonreplay_greedy_seal import (
        ADR0337_GREEDY_ARM_COUNT as sealed_arm_count,
        ADR0337_GREEDY_CALL_COUNT as sealed_call_count,
        ADR0337_GREEDY_PROTOCOL_SHA256 as sealed_protocol,
        ADR0337_GREEDY_SCHEDULE_SHA256,
        ADR0337_GREEDY_SOURCE_MANIFEST,
        ADR0337_GREEDY_TRANSITION_COUNT as sealed_transition_count,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0337_GREEDY_SOURCE_MANIFEST
    }
    if actual != ADR0337_GREEDY_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0337 greedy source closure drifted")
    if (
        sealed_protocol != ADR0337_GREEDY_PROTOCOL_SHA256
        or sealed_arm_count != ADR0337_GREEDY_ARM_COUNT
        or sealed_transition_count != ADR0337_GREEDY_TRANSITION_COUNT
        or sealed_call_count != ADR0337_GREEDY_CALL_COUNT
        or tuple(ADR0337_GREEDY_PROTOCOL["stop_reasons"])
        != tuple(item.value for item in NonReplayGreedyStopReason)
        or tuple(ADR0337_GREEDY_PROTOCOL["execution_phases"])
        != tuple(item.value for item in NonReplayGreedyExecutionPhase)
    ):
        raise RuntimeError("ADR-0337 greedy protocol drifted")
    schedule = build_adr0336_nonreplay_closed_finite_block_schedule()
    if schedule.digest != ADR0337_GREEDY_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0337 greedy schedule drifted")
    return actual["fresh_action_width_nonreplay_greedy.py"], schedule


def verify_adr0337_greedy_source_and_dependencies() -> str:
    """Verify the additive non-replay owner without opening a value."""

    source_sha256, _ = _preflight_adr0337_greedy_source_and_schedule()
    return source_sha256


def _campaign_sha256(
    *,
    schedule: NonReplayClosedFiniteBlockSchedule,
    greedy_source_sha256: str,
    synthetic: bool,
) -> str:
    _require_digest(greedy_source_sha256, label="greedy campaign source")
    return sha256(
        canonical_journal_json_bytes(
            {
                "artifact_relative_path": ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH,
                "greedy_source_sha256": greedy_source_sha256,
                "panel_sha256": schedule.panel_sha256,
                "pool_sha256": schedule.pool_sha256,
                "protocol_sha256": ADR0337_GREEDY_PROTOCOL_SHA256,
                "qualification_journal_sha256": (
                    schedule.qualification_journal_sha256
                ),
                "schedule_sha256": schedule.digest,
                "synthetic": synthetic,
                "teacher_artifact_sha256": schedule.teacher_artifact_sha256,
                "teacher_result_sha256": schedule.teacher_result_sha256,
                "version": "adr0337-nonreplay-greedy-campaign-v1",
            }
        )
    ).hexdigest()


def _header_payload(
    *,
    schedule: NonReplayClosedFiniteBlockSchedule,
    greedy_source_sha256: str,
    campaign_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    return _sealed_payload(
        {
            "arm_count": ADR0337_GREEDY_ARM_COUNT,
            "arm_counts_by_width": schedule.arm_counts_by_width,
            "artifact_relative_path": ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH,
            "call_count": ADR0337_GREEDY_CALL_COUNT,
            "call_slot_sha256s": tuple(
                item.digest for item in schedule.call_slots
            ),
            "campaign_sha256": campaign_sha256,
            "executed_candidate_counts_by_target_width": (
                schedule.executed_candidate_counts_by_target_width
            ),
            "greedy_source_sha256": greedy_source_sha256,
            "panel_sha256": schedule.panel_sha256,
            "pool_sha256": schedule.pool_sha256,
            "protocol_sha256": ADR0337_GREEDY_PROTOCOL_SHA256,
            "qualification_journal_sha256": (
                schedule.qualification_journal_sha256
            ),
            "qualification_terminal_sha256": (
                schedule.qualification_terminal_sha256
            ),
            "schedule_sha256": schedule.digest,
            "synthetic": synthetic,
            "teacher_artifact_sha256": schedule.teacher_artifact_sha256,
            "teacher_result_sha256": schedule.teacher_result_sha256,
            "teacher_terminal_sha256": schedule.teacher_terminal_sha256,
            "transition_count": ADR0337_GREEDY_TRANSITION_COUNT,
            "transition_counts_by_target_width": (
                schedule.transition_counts_by_target_width
            ),
            "version": _HEADER_VERSION,
        },
        digest_field="header_sha256",
    )


def _terminal_payload(
    *,
    state: _DerivedGreedyState,
    schedule: NonReplayClosedFiniteBlockSchedule,
    greedy_source_sha256: str,
    campaign_sha256: str,
    final_observation_line_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    if state.stop_reason is None:
        raise ValueError("greedy terminal requires a derived stop")
    _require_digest(
        final_observation_line_sha256,
        label="greedy final observation line",
    )
    return _sealed_payload(
        {
            "campaign_sha256": campaign_sha256,
            "completed_context_sha256s": tuple(
                item.digest for item in state.contexts
            ),
            "evidence_sha256s": tuple(item.digest for item in state.evidences),
            "failure_exception_chain": state.failure_exception_chain,
            "failure_stage": (
                None if state.failure_stage is None else state.failure_stage.value
            ),
            "final_observation_line_sha256": final_observation_line_sha256,
            "greedy_source_sha256": greedy_source_sha256,
            "invocation_count_complete": state.invocation_count_complete,
            "known_public_call_count": state.known_public_call_count,
            "observed_arm_count": len(state.evidences),
            "panel_sha256": schedule.panel_sha256,
            "partial_context_sha256": (
                None
                if state.partial_context is None
                else state.partial_context.digest
            ),
            "pool_sha256": schedule.pool_sha256,
            "record_count": len(state.evidences) + 2,
            "schedule_sha256": schedule.digest,
            "selected_raise_width": (
                None
                if state.selected_raise_width is None
                else state.selected_raise_width.count
            ),
            "stop_reason": state.stop_reason.value,
            "synthetic": synthetic,
            "teacher_result_sha256": schedule.teacher_result_sha256,
            "version": _TERMINAL_VERSION,
            "width_gate_sha256s": tuple(item.digest for item in state.width_gates),
        },
        digest_field="terminal_sha256",
    )


@dataclass(frozen=True, slots=True)
class NonReplayGreedyJournalPrefix:
    recovery: JournalRecovery
    evidences: tuple[NonReplayGreedyArmEvidence, ...]
    contexts: tuple[NonReplayGreedyContextResult, ...]
    partial_context: NonReplayGreedyPartialContext | None
    pending_stop_reason: NonReplayGreedyStopReason | None
    pending_failure_stage: NonReplayGreedyFailureStage | None
    known_public_call_count: int
    invocation_count_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.recovery, JournalRecovery):
            raise TypeError("greedy prefix requires generic journal recovery")
        if self.recovery.is_complete:
            raise ValueError("greedy prefix cannot contain a terminal journal")
        if not isinstance(self.evidences, tuple) or any(
            not isinstance(item, NonReplayGreedyArmEvidence)
            for item in self.evidences
        ):
            raise TypeError("greedy prefix evidences are not semantic")
        if tuple(item.call_index for item in self.evidences) != tuple(
            range(len(self.evidences))
        ):
            raise ValueError("greedy prefix evidence is not contiguous")
        if not isinstance(self.contexts, tuple) or tuple(
            item.panel_position for item in self.contexts
        ) != tuple(range(len(self.contexts))):
            raise ValueError("greedy prefix contexts are not contiguous")
        if self.partial_context is not None and not isinstance(
            self.partial_context,
            NonReplayGreedyPartialContext,
        ):
            raise TypeError("greedy prefix partial context is not semantic")
        if self.pending_stop_reason is not None and not isinstance(
            self.pending_stop_reason,
            NonReplayGreedyStopReason,
        ):
            raise TypeError("greedy prefix pending stop is not semantic")
        if self.pending_failure_stage is not None and not isinstance(
            self.pending_failure_stage,
            NonReplayGreedyFailureStage,
        ):
            raise TypeError("greedy prefix failure stage is not semantic")
        calls = _require_count(
            self.known_public_call_count,
            label="greedy prefix known calls",
            maximum=ADR0337_GREEDY_CALL_COUNT,
        )
        if calls != sum(item.public_call_count for item in self.evidences):
            raise ValueError("greedy prefix call count drifted")
        expected_complete = all(
            item.invocation_count_complete for item in self.evidences
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("greedy prefix invocation completeness drifted")
        expected_records = 0 if not self.recovery.records else len(self.evidences) + 1
        if len(self.recovery.records) != expected_records:
            raise ValueError("greedy prefix recovery/evidence counts differ")


@dataclass(frozen=True, slots=True)
class NonReplayGreedyJournalResult:
    campaign_sha256: str
    raw_journal_bytes: bytes
    journal_sha256: str
    terminal_sha256: str
    evidences: tuple[NonReplayGreedyArmEvidence, ...]
    contexts: tuple[NonReplayGreedyContextResult, ...]
    partial_context: NonReplayGreedyPartialContext | None
    width_gates: tuple[GreedyWidthGateResult, ...]
    selected_raise_width: RaiseActionWidth | None
    stop_reason: NonReplayGreedyStopReason
    failure_stage: NonReplayGreedyFailureStage | None
    failure_exception_chain: tuple[dict[str, str], ...]
    known_public_call_count: int
    invocation_count_complete: bool
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("greedy campaign", self.campaign_sha256),
            ("greedy journal", self.journal_sha256),
            ("greedy terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=label)
        if (
            not isinstance(self.raw_journal_bytes, bytes)
            or not self.raw_journal_bytes
            or sha256(self.raw_journal_bytes).hexdigest() != self.journal_sha256
        ):
            raise ValueError("greedy result raw journal identity drifted")
        if not isinstance(self.evidences, tuple) or not self.evidences or tuple(
            item.call_index for item in self.evidences
        ) != tuple(range(len(self.evidences))):
            raise ValueError("greedy result evidence is not a nonempty prefix")
        if any(item.synthetic is not self.synthetic for item in self.evidences):
            raise ValueError("greedy result mixes evidence provenance")
        if not isinstance(self.contexts, tuple) or tuple(
            item.panel_position for item in self.contexts
        ) != tuple(range(len(self.contexts))):
            raise ValueError("greedy result contexts are not contiguous")
        if self.partial_context is not None and not isinstance(
            self.partial_context,
            NonReplayGreedyPartialContext,
        ):
            raise TypeError("greedy result partial context is not semantic")
        if not isinstance(self.stop_reason, NonReplayGreedyStopReason):
            raise TypeError("greedy result stop is not semantic")
        if self.failure_stage is not None and not isinstance(
            self.failure_stage,
            NonReplayGreedyFailureStage,
        ):
            raise TypeError("greedy result failure stage is not semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("greedy result synthetic flag must be Boolean")
        calls = _require_count(
            self.known_public_call_count,
            label="greedy result known calls",
            maximum=ADR0337_GREEDY_CALL_COUNT,
        )
        if calls != sum(item.public_call_count for item in self.evidences):
            raise ValueError("greedy result call count drifted")
        expected_complete = all(
            item.invocation_count_complete for item in self.evidences
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("greedy result invocation completeness drifted")
        completed = self.stop_reason in {
            NonReplayGreedyStopReason.COMPLETED_SELECTED,
            NonReplayGreedyStopReason.COMPLETED_NO_WIDTH,
        }
        if completed:
            if (
                len(self.evidences) != ADR0337_GREEDY_CALL_COUNT
                or len(self.contexts) != 16
                or self.partial_context is not None
                or tuple(item.raise_width.count for item in self.width_gates)
                != (3, 4, 5, 6)
                or self.failure_stage is not None
                or self.failure_exception_chain
            ):
                raise ValueError("completed greedy result has partial evidence")
            passing = tuple(item for item in self.width_gates if item.passes)
            expected_selection = None if not passing else passing[0].raise_width
            if self.selected_raise_width != expected_selection:
                raise ValueError("greedy selected width differs from five gates")
            expected_reason = (
                NonReplayGreedyStopReason.COMPLETED_NO_WIDTH
                if expected_selection is None
                else NonReplayGreedyStopReason.COMPLETED_SELECTED
            )
            if self.stop_reason is not expected_reason:
                raise ValueError("greedy completion reason differs from selection")
        elif self.width_gates or self.selected_raise_width is not None:
            raise ValueError("stopped greedy result cannot publish a width")
        if self.stop_reason is NonReplayGreedyStopReason.CONSUMER_REJECTED:
            if (
                self.evidences[-1].kind
                is not NonReplayGreedyEvidenceKind.REJECTED
                or self.failure_stage
                not in {
                    NonReplayGreedyFailureStage.INITIAL_ARM,
                    NonReplayGreedyFailureStage.CANDIDATE_ARM,
                }
                or self.failure_exception_chain
            ):
                raise ValueError("greedy consumer stop has the wrong evidence")
        elif self.stop_reason is NonReplayGreedyStopReason.UNEXPECTED_EXCEPTION:
            if (
                self.evidences[-1].kind
                is not NonReplayGreedyEvidenceKind.UNEXPECTED_EXCEPTION
                or self.failure_stage
                not in {
                    NonReplayGreedyFailureStage.INITIAL_ARM,
                    NonReplayGreedyFailureStage.CANDIDATE_ARM,
                }
                or self.failure_exception_chain
            ):
                raise ValueError("greedy unexpected stop has the wrong evidence")
        elif self.stop_reason is NonReplayGreedyStopReason.NUMERICAL_REJECTED:
            if (
                self.evidences[-1].kind
                is not NonReplayGreedyEvidenceKind.ACCEPTED
                or self.failure_stage
                not in {
                    NonReplayGreedyFailureStage.CANDIDATE_PRICE,
                    NonReplayGreedyFailureStage.ROUND_REDUCTION,
                    NonReplayGreedyFailureStage.CAMPAIGN_REDUCTION,
                }
                or not self.failure_exception_chain
            ):
                raise ValueError("greedy numerical stop has the wrong evidence")
            _validate_exception_descriptors(
                self.failure_exception_chain,
                label="greedy numerical stop",
            )

    @property
    def journal_byte_count(self) -> int:
        return len(self.raw_journal_bytes)


NonReplayGreedyJournalRebinding = (
    NonReplayGreedyJournalPrefix | NonReplayGreedyJournalResult
)


def rebind_adr0337_greedy_journal(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> NonReplayGreedyJournalRebinding:
    if not isinstance(raw, bytes):
        raise TypeError("greedy journal rebinding requires immutable bytes")
    if not isinstance(synthetic, bool):
        raise TypeError("greedy journal synthetic mode must be Boolean")
    greedy_source, schedule = _preflight_adr0337_greedy_source_and_schedule()
    pool = build_adr0331_nonreplay_pool()
    teacher_result = (
        None
        if synthetic
        else verify_adr0336_nonreplay_teacher_result_artifact()
    )
    if teacher_result is not None and teacher_result.digest != (
        schedule.teacher_result_sha256
    ):
        raise RuntimeError("greedy retained teacher result drifted")
    campaign = _campaign_sha256(
        schedule=schedule,
        greedy_source_sha256=greedy_source,
        synthetic=synthetic,
    )
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=ADR0337_GREEDY_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign,
    )
    records = recovery.records
    if not records:
        return NonReplayGreedyJournalPrefix(
            recovery=recovery,
            evidences=(),
            contexts=(),
            partial_context=None,
            pending_stop_reason=None,
            pending_failure_stage=None,
            known_public_call_count=0,
            invocation_count_complete=True,
        )
    header = records[0]
    if header.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("greedy journal first record is not its header")
    expected_header = _header_payload(
        schedule=schedule,
        greedy_source_sha256=greedy_source,
        campaign_sha256=campaign,
        synthetic=synthetic,
    )
    if canonical_journal_json_bytes(
        header.body.payload
    ) != canonical_journal_json_bytes(expected_header):
        raise ValueError("greedy journal header differs from its sealed schedule")
    if header.body.semantic_identity_sha256 != expected_header["header_sha256"]:
        raise ValueError("greedy journal header semantic identity drifted")

    terminal_record: JournalRecordEnvelope | None = None
    observation_records = records[1:]
    if observation_records and observation_records[-1].body.kind is (
        JournalRecordKind.TERMINAL
    ):
        terminal_record = observation_records[-1]
        observation_records = observation_records[:-1]
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in observation_records
    ):
        raise ValueError("greedy journal has a non-observation inside its call prefix")
    if len(observation_records) > ADR0337_GREEDY_CALL_COUNT:
        raise ValueError("greedy journal exceeds its exact call count")
    evidences: list[NonReplayGreedyArmEvidence] = []
    state = _empty_derived_state()
    for call_index, record in enumerate(observation_records):
        if state.stop_reason is not None:
            raise ValueError("greedy journal continues after its derived stop")
        slot, task, transition = _next_invocation(state, schedule=schedule)
        evidence = _rebind_evidence(
            record.body.payload,
            slot=slot,
            task=task,
            transition=transition,
            expect_synthetic=synthetic,
        )
        if evidence.call_index != call_index:
            raise ValueError("greedy journal observation skipped a call slot")
        if record.body.semantic_identity_sha256 != evidence.digest:
            raise ValueError("greedy observation semantic identity drifted")
        evidences.append(evidence)
        state = _advance_state(
            state,
            evidence,
            pool=pool,
            schedule=schedule,
            teacher_result=teacher_result,
            synthetic=synthetic,
        )

    if terminal_record is None:
        return NonReplayGreedyJournalPrefix(
            recovery=recovery,
            evidences=state.evidences,
            contexts=state.contexts,
            partial_context=state.partial_context,
            pending_stop_reason=state.stop_reason,
            pending_failure_stage=state.failure_stage,
            known_public_call_count=state.known_public_call_count,
            invocation_count_complete=state.invocation_count_complete,
        )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("greedy journal terminal has trailing invalid bytes")
    if not observation_records or state.stop_reason is None:
        raise ValueError("greedy terminal lacks a derived stopping observation")
    expected_terminal = _terminal_payload(
        state=state,
        schedule=schedule,
        greedy_source_sha256=greedy_source,
        campaign_sha256=campaign,
        final_observation_line_sha256=observation_records[-1].line_sha256,
        synthetic=synthetic,
    )
    terminal_payload = terminal_record.body.payload
    _verify_sealed_payload(
        terminal_payload,
        digest_field="terminal_sha256",
        label="greedy terminal",
    )
    if canonical_journal_json_bytes(
        terminal_payload
    ) != canonical_journal_json_bytes(expected_terminal):
        raise ValueError("greedy terminal differs from journal-derived evidence")
    if terminal_record.body.semantic_identity_sha256 != terminal_payload[
        "terminal_sha256"
    ]:
        raise ValueError("greedy terminal semantic identity drifted")
    return NonReplayGreedyJournalResult(
        campaign_sha256=campaign,
        raw_journal_bytes=raw,
        journal_sha256=sha256(raw).hexdigest(),
        terminal_sha256=terminal_payload["terminal_sha256"],  # type: ignore[arg-type]
        evidences=state.evidences,
        contexts=state.contexts,
        partial_context=state.partial_context,
        width_gates=state.width_gates,
        selected_raise_width=state.selected_raise_width,
        stop_reason=state.stop_reason,
        failure_stage=state.failure_stage,
        failure_exception_chain=state.failure_exception_chain,
        known_public_call_count=state.known_public_call_count,
        invocation_count_complete=state.invocation_count_complete,
        synthetic=synthetic,
    )


def _validate_exception_descriptors(
    value: tuple[dict[str, str], ...],
    *,
    label: str,
    optional: bool = False,
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{label} exception chain must be immutable")
    if not value:
        if optional:
            return
        raise ValueError(f"{label} requires an exception chain")
    decoded = json.loads(canonical_journal_json_bytes(value))
    _validate_exception_chain(decoded, label=label)


@dataclass(frozen=True, slots=True)
class NonReplayGreedyLaunchRejected:
    reason: str
    output_path: Path
    exception_chain: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("greedy launch rejection reason must be nonempty")
        if not isinstance(self.output_path, Path):
            raise TypeError("greedy launch rejection path must be a Path")
        _validate_exception_descriptors(
            self.exception_chain,
            label="greedy launch rejection",
        )


@dataclass(frozen=True, slots=True)
class NonReplayGreedyExecutionFailed:
    reason: str
    phase: NonReplayGreedyExecutionPhase
    output_path: Path
    failed_call_index: int | None
    unreceipted_arm_invocation: bool
    durably_recorded_evidences: tuple[NonReplayGreedyArmEvidence, ...]
    last_receipt: JournalAppendReceipt | None
    known_public_call_count: int
    invocation_count_complete: bool
    raw_journal_bytes: bytes | None
    recovery: JournalRecovery | None
    exception_chain: tuple[dict[str, str], ...]
    recovery_exception_chain: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("greedy execution failure reason must be nonempty")
        if not isinstance(self.phase, NonReplayGreedyExecutionPhase):
            raise TypeError("greedy execution failure phase must be semantic")
        if not isinstance(self.output_path, Path):
            raise TypeError("greedy execution failure path must be a Path")
        if self.failed_call_index is not None:
            _require_count(
                self.failed_call_index,
                label="greedy failed call index",
                maximum=ADR0337_GREEDY_CALL_COUNT - 1,
            )
        if not isinstance(self.unreceipted_arm_invocation, bool):
            raise TypeError("greedy unreceipted-call flag must be Boolean")
        if not isinstance(self.durably_recorded_evidences, tuple) or any(
            not isinstance(item, NonReplayGreedyArmEvidence)
            for item in self.durably_recorded_evidences
        ):
            raise TypeError("greedy execution failure evidence is not semantic")
        if tuple(
            item.call_index for item in self.durably_recorded_evidences
        ) != tuple(range(len(self.durably_recorded_evidences))):
            raise ValueError("greedy execution failure evidence is not contiguous")
        if self.last_receipt is not None and not isinstance(
            self.last_receipt,
            JournalAppendReceipt,
        ):
            raise TypeError("greedy execution failure receipt is not semantic")
        calls = _require_count(
            self.known_public_call_count,
            label="greedy execution failure known calls",
            maximum=ADR0337_GREEDY_CALL_COUNT,
        )
        if calls != sum(
            item.public_call_count for item in self.durably_recorded_evidences
        ):
            raise ValueError("greedy execution failure call count drifted")
        expected_complete = (
            not self.unreceipted_arm_invocation
            and all(
                item.invocation_count_complete
                for item in self.durably_recorded_evidences
            )
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("greedy execution failure completeness drifted")
        _validate_exception_descriptors(
            self.exception_chain,
            label="greedy execution failure",
        )
        _validate_exception_descriptors(
            self.recovery_exception_chain,
            label="greedy execution recovery failure",
            optional=True,
        )
        if self.raw_journal_bytes is None:
            if self.recovery is not None or not self.recovery_exception_chain:
                raise ValueError("unreadable greedy journal lacks recovery evidence")
        elif not isinstance(self.raw_journal_bytes, bytes):
            raise TypeError("greedy execution failure raw journal is mutable")
        elif self.recovery is None:
            if not self.recovery_exception_chain:
                raise ValueError("greedy raw journal lacks recovery evidence")
        elif (
            not isinstance(self.recovery, JournalRecovery)
            or self.recovery.raw_bytes != self.raw_journal_bytes
        ):
            raise ValueError("greedy execution recovery lost its raw bytes")


NonReplayGreedyRunResult = (
    NonReplayGreedyJournalRebinding
    | NonReplayGreedyLaunchRejected
    | NonReplayGreedyExecutionFailed
)
_GreedyArmOwner = Callable[
    [
        NonReplayGreedyCallSlot,
        GreedySubsetTask,
        ClosedFiniteBlockTransition | None,
    ],
    NonReplayGreedyArmEvidence,
]


def _execution_failure(
    *,
    writer: DurableEvidenceJournalWriter,
    output_path: Path,
    campaign_sha256: str,
    phase: NonReplayGreedyExecutionPhase,
    failed_call_index: int | None,
    unreceipted_arm_invocation: bool,
    evidences: tuple[NonReplayGreedyArmEvidence, ...],
    last_receipt: JournalAppendReceipt | None,
    error: Exception,
) -> NonReplayGreedyExecutionFailed:
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
                expected_protocol_sha256=ADR0337_GREEDY_PROTOCOL_SHA256,
                expected_campaign_sha256=campaign_sha256,
            )
        except Exception as recovery_error:
            recovery_exception_chain = _exception_payload(recovery_error)
    return NonReplayGreedyExecutionFailed(
        reason="greedy campaign failed after exclusive journal creation",
        phase=phase,
        output_path=output_path,
        failed_call_index=failed_call_index,
        unreceipted_arm_invocation=unreceipted_arm_invocation,
        durably_recorded_evidences=evidences,
        last_receipt=last_receipt,
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


def _execute_greedy(
    *,
    output_path: Path,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayClosedFiniteBlockSchedule,
    greedy_source_sha256: str,
    teacher_result: RetainedNonReplayTeacherResult | None,
    arm_owner: _GreedyArmOwner,
    synthetic: bool,
) -> NonReplayGreedyJournalResult | NonReplayGreedyExecutionFailed:
    campaign = _campaign_sha256(
        schedule=schedule,
        greedy_source_sha256=greedy_source_sha256,
        synthetic=synthetic,
    )
    writer = DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=ADR0337_GREEDY_PROTOCOL_SHA256,
        campaign_sha256=campaign,
    )
    evidences: list[NonReplayGreedyArmEvidence] = []
    state = _empty_derived_state()
    phase = NonReplayGreedyExecutionPhase.HEADER_APPEND
    failed_call_index: int | None = None
    unreceipted_arm_invocation = False
    authorization: JournalAppendReceipt | None = None
    try:
        header_payload = _header_payload(
            schedule=schedule,
            greedy_source_sha256=greedy_source_sha256,
            campaign_sha256=campaign,
            synthetic=synthetic,
        )
        authorization = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header_payload["header_sha256"],  # type: ignore[arg-type]
            payload=header_payload,
        )
        while state.stop_reason is None:
            slot, task, transition = _next_invocation(state, schedule=schedule)
            phase = NonReplayGreedyExecutionPhase.NEXT_CALL_AUTHORIZATION
            failed_call_index = slot.call_index
            expected_kind = (
                JournalRecordKind.HEADER
                if slot.call_index == 0
                else JournalRecordKind.OBSERVATION
            )
            if (
                not isinstance(authorization, JournalAppendReceipt)
                or authorization.sequence != slot.call_index
                or authorization.kind is not expected_kind
            ):
                raise RuntimeError("greedy call lacks its preceding durable receipt")
            phase = NonReplayGreedyExecutionPhase.ARM_EVIDENCE
            unreceipted_arm_invocation = True
            try:
                evidence = arm_owner(slot, task, transition)
                if not isinstance(evidence, NonReplayGreedyArmEvidence):
                    raise TypeError("greedy arm owner returned nonsemantic evidence")
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
            phase = NonReplayGreedyExecutionPhase.OBSERVATION_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
            evidences.append(evidence)
            unreceipted_arm_invocation = False
            phase = NonReplayGreedyExecutionPhase.SEMANTIC_REDUCTION
            state = _advance_state(
                state,
                evidence,
                pool=pool,
                schedule=schedule,
                teacher_result=teacher_result,
                synthetic=synthetic,
            )
            if state.stop_reason is None:
                continue
            terminal_payload = _terminal_payload(
                state=state,
                schedule=schedule,
                greedy_source_sha256=greedy_source_sha256,
                campaign_sha256=campaign,
                final_observation_line_sha256=authorization.line_sha256,
                synthetic=synthetic,
            )
            phase = NonReplayGreedyExecutionPhase.TERMINAL_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=terminal_payload["terminal_sha256"],  # type: ignore[arg-type]
                payload=terminal_payload,
            )
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_call_index=failed_call_index,
            unreceipted_arm_invocation=unreceipted_arm_invocation,
            evidences=tuple(evidences),
            last_receipt=authorization,
            error=error,
        )
    phase = NonReplayGreedyExecutionPhase.JOURNAL_CLOSE
    try:
        writer.close()
        phase = NonReplayGreedyExecutionPhase.FINAL_REBIND
        rebound = rebind_adr0337_greedy_journal(
            output_path.read_bytes(),
            synthetic=synthetic,
        )
        if not isinstance(rebound, NonReplayGreedyJournalResult):
            raise RuntimeError("greedy execution ended without a terminal result")
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
            last_receipt=authorization,
            error=error,
        )


def _real_arm_owner(
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
) -> NonReplayGreedyArmEvidence:
    result = consume_certified_reduced_sizing_v2(task.request)
    return greedy_evidence_from_consumer_result(
        slot=slot,
        task=task,
        transition=transition,
        result=result,
    )


def _synthetic_success_arm_owner(
    slot: NonReplayGreedyCallSlot,
    task: GreedySubsetTask,
    transition: ClosedFiniteBlockTransition | None,
) -> NonReplayGreedyArmEvidence:
    value = 0.0 if task.raise_width.count == 2 else 100.0
    return synthetic_greedy_accepted_evidence(
        slot=slot,
        task=task,
        transition=transition,
        lower_chips=value,
        upper_chips=value,
    )


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH


def run_and_retain_adr0336_nonreplay_closed_finite_block_greedy(
) -> NonReplayGreedyRunResult:
    """Run the sealed replacement once; callers must never retry a terminal path."""

    output_path = _artifact_path()
    try:
        greedy_source, schedule = _preflight_adr0337_greedy_source_and_schedule()
        pool = build_adr0331_nonreplay_pool()
        teacher_result = verify_adr0336_nonreplay_teacher_result_artifact()
        if teacher_result.digest != schedule.teacher_result_sha256:
            raise RuntimeError("greedy preflight teacher result drifted")
    except Exception as error:
        return NonReplayGreedyLaunchRejected(
            reason="greedy source, schedule, or teacher preflight rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )
    try:
        return _execute_greedy(
            output_path=output_path,
            pool=pool,
            schedule=schedule,
            greedy_source_sha256=greedy_source,
            teacher_result=teacher_result,
            arm_owner=_real_arm_owner,
            synthetic=False,
        )
    except Exception as error:
        return NonReplayGreedyLaunchRejected(
            reason="greedy exclusive journal launch rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )


def write_adr0337_synthetic_completed_journal(
    output_path: Path,
) -> NonReplayGreedyJournalResult | NonReplayGreedyExecutionFailed:
    """Exercise the complete terminal path without a consumer or solver call."""

    if not isinstance(output_path, Path):
        raise TypeError("synthetic greedy output path must be a Path")
    greedy_source, schedule = _preflight_adr0337_greedy_source_and_schedule()
    return _execute_greedy(
        output_path=output_path,
        pool=build_adr0331_nonreplay_pool(),
        schedule=schedule,
        greedy_source_sha256=greedy_source,
        teacher_result=None,
        arm_owner=_synthetic_success_arm_owner,
        synthetic=True,
    )


__all__ = [
    "ADR0337_GREEDY_ARM_COUNT",
    "ADR0337_GREEDY_ARM_COUNTS_BY_WIDTH",
    "ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH",
    "ADR0337_GREEDY_CALL_COUNT",
    "ADR0337_GREEDY_COMPLETED_RECORD_COUNT",
    "ADR0337_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH",
    "ADR0337_GREEDY_PROTOCOL",
    "ADR0337_GREEDY_PROTOCOL_SHA256",
    "ADR0337_GREEDY_TRANSITION_COUNT",
    "ADR0337_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH",
    "NonReplayClosedFiniteBlockSchedule",
    "NonReplayGreedyArmEvidence",
    "NonReplayGreedyCallSlot",
    "NonReplayGreedyContextResult",
    "NonReplayGreedyEvidenceKind",
    "NonReplayGreedyExecutionFailed",
    "NonReplayGreedyExecutionPhase",
    "NonReplayGreedyFailureStage",
    "NonReplayGreedyJournalPrefix",
    "NonReplayGreedyJournalRebinding",
    "NonReplayGreedyJournalResult",
    "NonReplayGreedyLaunchRejected",
    "NonReplayGreedyPartialContext",
    "NonReplayGreedyRoundResult",
    "NonReplayGreedyRunResult",
    "NonReplayGreedyStopReason",
    "NonReplayGreedyTeacherReference",
    "build_adr0336_nonreplay_closed_finite_block_schedule",
    "greedy_evidence_from_consumer_result",
    "rebind_adr0337_greedy_journal",
    "run_and_retain_adr0336_nonreplay_closed_finite_block_greedy",
    "synthetic_greedy_accepted_evidence",
    "synthetic_greedy_rejected_evidence",
    "verify_adr0337_greedy_source_and_dependencies",
    "write_adr0337_synthetic_completed_journal",
]
