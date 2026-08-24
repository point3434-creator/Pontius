"""Source-sealed direct closed finite-block greedy owner for ADR-0323.

The module freezes every exact anchored subset arm and every possible one-raise
parent-to-child transition before the first greedy value is opened.  A proposed
own raise is priceable only after its complete semantic fold/call response block
is present in the augmented request.  The future runner is research-only,
retains failure-complete evidence, and emits no betting action.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from itertools import pairwise
from math import isfinite
from pathlib import Path

from .certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
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
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    _canonical_sha256,
    certified_full_minus_subset_regret,
    verify_adr0324_structure_source_and_pool,
)
from .fresh_action_width_qualification_result import (
    ADR0323_QUALIFICATION_RESULT_SHA256,
    ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
    ADR0323_QUALIFIED_PANEL_SHA256,
    ADR0323_QUALIFIED_POOL_INDICES,
    verify_adr0323_qualification_result_artifact,
)
from .fresh_action_width_structures import (
    ADR0323_PRIVATE_RANGE_WIDTH,
    ADR0323_RAISE_WIDTHS,
    FreshActionWidthContext,
    FreshActionWidthDevelopmentPool,
    PrivateRangeWidth,
    RaiseActionWidth,
    anchored_raise_subset_family,
)
from .fresh_action_width_teacher import NormalizedTeacherRegretInterval
from .fresh_action_width_teacher_result import (
    ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256,
    RetainedExhaustiveTeacherContext,
    RetainedExhaustiveTeacherResult,
    RetainedExhaustiveTeacherWidth,
    verify_adr0323_exhaustive_teacher_result_artifact,
)


ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH = (
    (2, 16),
    (3, 120),
    (4, 408),
    (5, 828),
    (6, 1_107),
)
ADR0323_GREEDY_ARM_COUNT = 2_479
ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH = (
    (3, 120),
    (4, 816),
    (5, 2_484),
    (6, 4_428),
)
ADR0323_GREEDY_TRANSITION_COUNT = 7_848
ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH = (
    (3, 120),
    (4, 104),
    (5, 88),
    (6, 72),
)
ADR0323_GREEDY_EXECUTED_INITIAL_CALL_COUNT = 16
ADR0323_GREEDY_EXECUTED_CANDIDATE_CALL_COUNT = 384
ADR0323_GREEDY_EXECUTED_CALL_COUNT = 400
ADR0323_GREEDY_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/"
    "fresh-action-width-closed-finite-block-greedy-development-v1.json"
)


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_nonnegative_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative")
    return value


def _require_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value):
        raise ValueError(f"{label} must be a finite float")
    return value


def _require_unit_interval(value: object, *, label: str) -> float:
    exact = _require_finite(value, label=label)
    if exact < 0.0 or exact > 1.0:
        raise ValueError(f"{label} must lie in [0, 1]")
    return exact


class OpponentResponseAction(StrEnum):
    FOLD = "fold"
    CALL = "call"


@dataclass(frozen=True, slots=True)
class OpponentResponseRowIdentity:
    """One semantic reduced-game response row, never an LP row number."""

    context_semantic_digest: str
    raise_to_total: KernelRaiseToTotal
    reduced_bet_increment: ReducedBetIncrement
    responder_private_type_index: int
    action: OpponentResponseAction

    def __post_init__(self) -> None:
        _require_digest(self.context_semantic_digest, label="response-row context")
        if not isinstance(self.raise_to_total, KernelRaiseToTotal):
            raise TypeError("response row requires a nominal raise-to total")
        if not isinstance(self.reduced_bet_increment, ReducedBetIncrement):
            raise TypeError("response row requires a nominal reduced increment")
        index = _require_nonnegative_int(
            self.responder_private_type_index,
            label="response-row private-type index",
        )
        if index >= ADR0323_PRIVATE_RANGE_WIDTH.count:
            raise ValueError("response-row private-type index exceeds h4")
        if not isinstance(self.action, OpponentResponseAction):
            raise TypeError("response row action must be semantic")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "action": self.action.value,
                "context_semantic_digest": self.context_semantic_digest,
                "raise_to_total": self.raise_to_total.chips,
                "reduced_bet_increment": self.reduced_bet_increment.chips,
                "responder_private_type_index": self.responder_private_type_index,
                "version": "adr0323-opponent-response-row-identity-v1",
            }
        )


def _expected_response_rows(
    *,
    context_semantic_digest: str,
    raise_to_totals: tuple[KernelRaiseToTotal, ...],
    reduced_bet_increments: tuple[ReducedBetIncrement, ...],
    responder_private_range_width: PrivateRangeWidth,
) -> tuple[OpponentResponseRowIdentity, ...]:
    if len(raise_to_totals) != len(reduced_bet_increments):
        raise ValueError("response-row amount mapping is not one-to-one")
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
        for responder in range(responder_private_range_width.count)
        for action in (OpponentResponseAction.FOLD, OpponentResponseAction.CALL)
    )


@dataclass(frozen=True, slots=True)
class OpponentResponseRowSetIdentity:
    """Complete fold/call rows for every admitted raise and responder type."""

    context_semantic_digest: str
    response_model: ReducedSizingResponseModel
    raise_to_totals: tuple[KernelRaiseToTotal, ...]
    reduced_bet_increments: tuple[ReducedBetIncrement, ...]
    responder_private_range_width: PrivateRangeWidth
    rows: tuple[OpponentResponseRowIdentity, ...]

    def __post_init__(self) -> None:
        _require_digest(self.context_semantic_digest, label="response-row-set context")
        if self.response_model is not (
            ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY
        ):
            raise ValueError("response-row set has the wrong reduced response model")
        if (
            not isinstance(self.raise_to_totals, tuple)
            or not self.raise_to_totals
            or any(
                not isinstance(value, KernelRaiseToTotal)
                for value in self.raise_to_totals
            )
        ):
            raise TypeError("response-row set requires nominal raise-to totals")
        if (
            not isinstance(self.reduced_bet_increments, tuple)
            or any(
                not isinstance(value, ReducedBetIncrement)
                for value in self.reduced_bet_increments
            )
        ):
            raise TypeError("response-row set requires nominal increments")
        if not isinstance(self.responder_private_range_width, PrivateRangeWidth):
            raise TypeError("response-row set requires a private-range width")
        if self.responder_private_range_width != ADR0323_PRIVATE_RANGE_WIDTH:
            raise ValueError("response-row set differs from the frozen h4 width")
        if len(self.raise_to_totals) != len(self.reduced_bet_increments):
            raise ValueError("response-row totals and increments have different widths")
        if any(
            left.chips >= right.chips
            for left, right in pairwise(self.raise_to_totals)
        ):
            raise ValueError("response-row raise-to totals are not strictly increasing")
        if any(
            left.chips >= right.chips
            for left, right in pairwise(self.reduced_bet_increments)
        ):
            raise ValueError("response-row increments are not strictly increasing")
        expected = _expected_response_rows(
            context_semantic_digest=self.context_semantic_digest,
            raise_to_totals=self.raise_to_totals,
            reduced_bet_increments=self.reduced_bet_increments,
            responder_private_range_width=self.responder_private_range_width,
        )
        if self.rows != expected:
            raise ValueError("response-row set is not complete fold/call closure")
        if len({row.digest for row in self.rows}) != len(self.rows):
            raise ValueError("response-row set repeats a semantic row")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_semantic_digest": self.context_semantic_digest,
                "raise_to_totals": tuple(value.chips for value in self.raise_to_totals),
                "reduced_bet_increments": tuple(
                    value.chips for value in self.reduced_bet_increments
                ),
                "responder_private_range_width": (
                    self.responder_private_range_width.count
                ),
                "response_model": self.response_model.value,
                "row_sha256": tuple(row.digest for row in self.rows),
                "version": "adr0323-opponent-response-row-set-identity-v1",
            }
        )

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True, slots=True)
class OwnRaiseBlockIdentity:
    """One proposed own raise plus every fold/call response row it creates."""

    context_semantic_digest: str
    raise_to_total: KernelRaiseToTotal
    reduced_bet_increment: ReducedBetIncrement
    responder_private_range_width: PrivateRangeWidth
    response_rows: tuple[OpponentResponseRowIdentity, ...]

    def __post_init__(self) -> None:
        _require_digest(self.context_semantic_digest, label="own-block context")
        if not isinstance(self.raise_to_total, KernelRaiseToTotal):
            raise TypeError("own block requires a nominal raise-to total")
        if not isinstance(self.reduced_bet_increment, ReducedBetIncrement):
            raise TypeError("own block requires a nominal reduced increment")
        if not isinstance(self.responder_private_range_width, PrivateRangeWidth):
            raise TypeError("own block requires a private-range width")
        if self.responder_private_range_width != ADR0323_PRIVATE_RANGE_WIDTH:
            raise ValueError("own block differs from the frozen h4 width")
        expected = _expected_response_rows(
            context_semantic_digest=self.context_semantic_digest,
            raise_to_totals=(self.raise_to_total,),
            reduced_bet_increments=(self.reduced_bet_increment,),
            responder_private_range_width=self.responder_private_range_width,
        )
        if self.response_rows != expected:
            raise ValueError("own block lacks complete fold/call response closure")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_semantic_digest": self.context_semantic_digest,
                "raise_to_total": self.raise_to_total.chips,
                "reduced_bet_increment": self.reduced_bet_increment.chips,
                "responder_private_range_width": (
                    self.responder_private_range_width.count
                ),
                "response_row_sha256": tuple(
                    row.digest for row in self.response_rows
                ),
                "version": "adr0323-own-raise-block-identity-v1",
            }
        )


def _response_row_set_for_request(
    *,
    context_semantic_digest: str,
    request: CertifiedReducedSizingRequestV2,
) -> OpponentResponseRowSetIdentity:
    decision = request.betting.legal_decision()
    base_raise_to = decision.street_contribution + decision.call_amount
    increments = tuple(
        ReducedBetIncrement(value.chips - base_raise_to)
        for value in request.legal_raise_to_totals
    )
    private_width = PrivateRangeWidth(len(request.joint_probabilities[0]))
    row_set = OpponentResponseRowSetIdentity(
        context_semantic_digest=context_semantic_digest,
        response_model=request.response_model,
        raise_to_totals=request.legal_raise_to_totals,
        reduced_bet_increments=increments,
        responder_private_range_width=private_width,
        rows=_expected_response_rows(
            context_semantic_digest=context_semantic_digest,
            raise_to_totals=request.legal_raise_to_totals,
            reduced_bet_increments=increments,
            responder_private_range_width=private_width,
        ),
    )

    return row_set


@dataclass(frozen=True, slots=True)
class GreedySubsetTask:
    ordinal: int
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    raise_width: RaiseActionWidth
    subset_index: int
    request: CertifiedReducedSizingRequestV2
    response_row_set: OpponentResponseRowSetIdentity
    request_sha256: str = ""
    legal_raise_set_sha256: str = ""
    linear_program_sha256: str = ""

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.ordinal, label="greedy task ordinal")
        panel = _require_nonnegative_int(
            self.panel_position,
            label="greedy task panel position",
        )
        if panel >= 16:
            raise ValueError("greedy task panel position exceeds the sealed panel")
        _require_nonnegative_int(self.pool_index, label="greedy task pool index")
        _require_digest(self.context_semantic_digest, label="greedy task context")
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("greedy task requires a raise-action width")
        _require_nonnegative_int(self.subset_index, label="greedy task subset index")
        if not isinstance(self.request, CertifiedReducedSizingRequestV2):
            raise TypeError("greedy task requires an exact consumer request")
        if (
            self.request.legal_raise_scope
            is not LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET
            or len(self.request.legal_raise_to_totals) != self.raise_width.count
        ):
            raise ValueError("greedy task has the wrong restricted scope or width")
        if not isinstance(self.response_row_set, OpponentResponseRowSetIdentity):
            raise TypeError("greedy task requires a semantic response-row set")
        bound = _bind_request(self.request)
        computed = (
            bound.request_sha256,
            bound.legal_raise_set_sha256,
            bound.linear_program_sha256,
        )
        supplied = (
            self.request_sha256,
            self.legal_raise_set_sha256,
            self.linear_program_sha256,
        )
        if supplied == ("", "", ""):
            object.__setattr__(self, "request_sha256", computed[0])
            object.__setattr__(self, "legal_raise_set_sha256", computed[1])
            object.__setattr__(self, "linear_program_sha256", computed[2])
        elif supplied != computed:
            raise ValueError("greedy task identities differ from its exact request")
        expected_rows = OpponentResponseRowSetIdentity(
            context_semantic_digest=self.context_semantic_digest,
            response_model=self.request.response_model,
            raise_to_totals=bound.legal_raise_to_totals,
            reduced_bet_increments=bound.reduced_bet_increments,
            responder_private_range_width=PrivateRangeWidth(
                len(self.request.joint_probabilities[0])
            ),
            rows=_expected_response_rows(
                context_semantic_digest=self.context_semantic_digest,
                raise_to_totals=bound.legal_raise_to_totals,
                reduced_bet_increments=bound.reduced_bet_increments,
                responder_private_range_width=PrivateRangeWidth(
                    len(self.request.joint_probabilities[0])
                ),
            ),
        )
        if self.response_row_set != expected_rows:
            raise ValueError("greedy task response rows differ from its compiled request")

    @property
    def raise_to_totals(self) -> tuple[int, ...]:
        return tuple(value.chips for value in self.request.legal_raise_to_totals)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_semantic_digest": self.context_semantic_digest,
                "legal_raise_set_sha256": self.legal_raise_set_sha256,
                "linear_program_sha256": self.linear_program_sha256,
                "ordinal": self.ordinal,
                "panel_position": self.panel_position,
                "pool_index": self.pool_index,
                "raise_to_totals": self.raise_to_totals,
                "raise_width": self.raise_width.count,
                "request_sha256": self.request_sha256,
                "response_row_set_sha256": self.response_row_set.digest,
                "subset_index": self.subset_index,
                "version": "adr0323-closed-finite-block-greedy-task-v1",
            }
        )


class ClosedFiniteBlockPhase(StrEnum):
    OWN_BLOCK_PROPOSAL = "own_block_proposal"
    OPPONENT_RESPONSE_CLOSURE = "opponent_response_closure"
    CERTIFIED_SOLVE = "certified_solve"


ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER = (
    ClosedFiniteBlockPhase.OWN_BLOCK_PROPOSAL,
    ClosedFiniteBlockPhase.OPPONENT_RESPONSE_CLOSURE,
    ClosedFiniteBlockPhase.CERTIFIED_SOLVE,
)


@dataclass(frozen=True, slots=True)
class ClosedFiniteBlockTransition:
    ordinal: int
    candidate_position: int
    incumbent: GreedySubsetTask
    augmented: GreedySubsetTask
    proposed_raise_to_total: KernelRaiseToTotal
    proposed_reduced_bet_increment: ReducedBetIncrement
    own_block: OwnRaiseBlockIdentity
    phase_order: tuple[ClosedFiniteBlockPhase, ...]

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.ordinal, label="greedy transition ordinal")
        _require_nonnegative_int(
            self.candidate_position,
            label="greedy transition candidate position",
        )
        if not isinstance(self.incumbent, GreedySubsetTask) or not isinstance(
            self.augmented,
            GreedySubsetTask,
        ):
            raise TypeError("greedy transition requires incumbent and augmented tasks")
        if (
            self.incumbent.panel_position != self.augmented.panel_position
            or self.incumbent.pool_index != self.augmented.pool_index
            or self.incumbent.context_semantic_digest
            != self.augmented.context_semantic_digest
        ):
            raise ValueError("greedy transition spans multiple contexts")
        if self.augmented.raise_width.count != self.incumbent.raise_width.count + 1:
            raise ValueError("greedy transition does not add exactly one raise")
        if not isinstance(self.proposed_raise_to_total, KernelRaiseToTotal):
            raise TypeError("greedy transition requires a nominal proposed total")
        if not isinstance(self.proposed_reduced_bet_increment, ReducedBetIncrement):
            raise TypeError("greedy transition requires a nominal proposed increment")
        parent = self.incumbent.request.legal_raise_to_totals
        child = self.augmented.request.legal_raise_to_totals
        proposed = self.proposed_raise_to_total
        if proposed in parent or tuple(
            sorted((*parent, proposed), key=lambda value: value.chips)
        ) != child:
            raise ValueError("greedy transition child is not parent plus proposal")
        proposed_index = child.index(proposed)
        if (
            self.augmented.response_row_set.reduced_bet_increments[proposed_index]
            != self.proposed_reduced_bet_increment
        ):
            raise ValueError("greedy proposal total and increment mapping drifted")
        if not isinstance(self.own_block, OwnRaiseBlockIdentity):
            raise TypeError("greedy transition requires a semantic own block")
        if (
            self.own_block.context_semantic_digest
            != self.incumbent.context_semantic_digest
            or self.own_block.raise_to_total != proposed
            or self.own_block.reduced_bet_increment
            != self.proposed_reduced_bet_increment
        ):
            raise ValueError("greedy transition own block differs from its proposal")
        parent_rows = set(self.incumbent.response_row_set.rows)
        block_rows = set(self.own_block.response_rows)
        child_rows = set(self.augmented.response_row_set.rows)
        if parent_rows & block_rows or parent_rows | block_rows != child_rows:
            raise ValueError("greedy transition response closure is incomplete")
        if self.phase_order != ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER:
            raise ValueError("greedy transition changed the closed-block phase order")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "augmented_legal_raise_set_sha256": (
                    self.augmented.legal_raise_set_sha256
                ),
                "augmented_linear_program_sha256": (
                    self.augmented.linear_program_sha256
                ),
                "augmented_request_sha256": self.augmented.request_sha256,
                "augmented_response_row_set_sha256": (
                    self.augmented.response_row_set.digest
                ),
                "augmented_task_sha256": self.augmented.digest,
                "candidate_position": self.candidate_position,
                "incumbent_legal_raise_set_sha256": (
                    self.incumbent.legal_raise_set_sha256
                ),
                "incumbent_linear_program_sha256": (
                    self.incumbent.linear_program_sha256
                ),
                "incumbent_request_sha256": self.incumbent.request_sha256,
                "incumbent_response_row_set_sha256": (
                    self.incumbent.response_row_set.digest
                ),
                "incumbent_task_sha256": self.incumbent.digest,
                "ordinal": self.ordinal,
                "own_block_sha256": self.own_block.digest,
                "phase_order": tuple(phase.value for phase in self.phase_order),
                "proposed_raise_to_total": self.proposed_raise_to_total.chips,
                "proposed_reduced_bet_increment": (
                    self.proposed_reduced_bet_increment.chips
                ),
                "version": "adr0323-closed-finite-block-transition-v1",
            }
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
            f"{context.context_id}|closed-finite-block-greedy|"
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
class ClosedFiniteBlockGreedySchedule:
    pool_sha256: str
    qualification_result_sha256: str
    panel_sha256: str
    exhaustive_teacher_result_sha256: str
    tasks: tuple[GreedySubsetTask, ...]
    transitions: tuple[ClosedFiniteBlockTransition, ...]
    arm_counts_by_width: tuple[tuple[int, int], ...]
    transition_counts_by_target_width: tuple[tuple[int, int], ...]
    executed_candidate_counts_by_target_width: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("greedy schedule pool", self.pool_sha256),
            ("greedy schedule qualification", self.qualification_result_sha256),
            ("greedy schedule panel", self.panel_sha256),
            ("greedy schedule teacher", self.exhaustive_teacher_result_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.qualification_result_sha256
            != ADR0323_QUALIFICATION_RESULT_SHA256
            or self.panel_sha256 != ADR0323_QUALIFIED_PANEL_SHA256
            or self.exhaustive_teacher_result_sha256
            != ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
        ):
            raise ValueError("greedy schedule belongs to another evidence chain")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0323_GREEDY_ARM_COUNT
            or any(not isinstance(task, GreedySubsetTask) for task in self.tasks)
        ):
            raise TypeError("greedy schedule requires 2,479 immutable arms")
        if tuple(task.ordinal for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("greedy task ordinals are not contiguous")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("greedy schedule repeats a semantic arm")
        if len({task.request_sha256 for task in self.tasks}) != len(self.tasks):
            raise ValueError("greedy schedule repeats an exact arm request")
        if (
            not isinstance(self.transitions, tuple)
            or len(self.transitions) != ADR0323_GREEDY_TRANSITION_COUNT
            or any(
                not isinstance(value, ClosedFiniteBlockTransition)
                for value in self.transitions
            )
        ):
            raise TypeError("greedy schedule requires 7,848 immutable transitions")
        if tuple(value.ordinal for value in self.transitions) != tuple(
            range(len(self.transitions))
        ):
            raise ValueError("greedy transition ordinals are not contiguous")
        if len({value.digest for value in self.transitions}) != len(self.transitions):
            raise ValueError("greedy schedule repeats a semantic transition")
        if self.arm_counts_by_width != ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH:
            raise ValueError("greedy arm counts differ from the frozen ledger")
        if (
            self.transition_counts_by_target_width
            != ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        ):
            raise ValueError("greedy transition counts differ from the frozen graph")
        if (
            self.executed_candidate_counts_by_target_width
            != ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
        ):
            raise ValueError("greedy executed-call counts differ from the frozen path")
        observed_arm_counts = tuple(
            (
                width,
                sum(task.raise_width.count == width for task in self.tasks),
            )
            for width, _ in ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH
        )
        if observed_arm_counts != self.arm_counts_by_width:
            raise ValueError("greedy schedule arm ledger does not match its tasks")
        observed_transition_counts = tuple(
            (
                width,
                sum(
                    value.augmented.raise_width.count == width
                    for value in self.transitions
                ),
            )
            for width, _ in ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        )
        if observed_transition_counts != self.transition_counts_by_target_width:
            raise ValueError("greedy schedule transition ledger does not match its graph")

        for panel_position, (pool_index, context_digest) in enumerate(
            zip(
                ADR0323_QUALIFIED_POOL_INDICES,
                ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
                strict=True,
            )
        ):
            context_tasks = tuple(
                task for task in self.tasks if task.panel_position == panel_position
            )
            if any(
                task.pool_index != pool_index
                or task.context_semantic_digest != context_digest
                for task in context_tasks
            ):
                raise ValueError("greedy tasks differ from qualified-panel membership")
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
                raise ValueError(
                    "greedy context is not the exact ordered anchored-subset family"
                )
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
                    tuple(value.candidate_position for value in outgoing)
                    != tuple(range(len(outgoing)))
                    or tuple(value.proposed_raise_to_total for value in outgoing)
                    != omitted
                ):
                    raise ValueError("greedy omitted-raise order is not exact ascending")
        task_ordinals = {task.ordinal for task in self.tasks}
        if any(
            value.incumbent.ordinal not in task_ordinals
            or value.augmented.ordinal not in task_ordinals
            or self.tasks[value.incumbent.ordinal] != value.incumbent
            or self.tasks[value.augmented.ordinal] != value.augmented
            for value in self.transitions
        ):
            raise ValueError("greedy transition references an arm outside the schedule")

    def tasks_for_context(self, panel_position: int) -> tuple[GreedySubsetTask, ...]:
        _require_nonnegative_int(panel_position, label="greedy context position")
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
            raise ValueError("greedy context has no unique width-two initial task")
        return candidates[0]

    def outgoing(
        self,
        incumbent: GreedySubsetTask,
    ) -> tuple[ClosedFiniteBlockTransition, ...]:
        if not isinstance(incumbent, GreedySubsetTask):
            raise TypeError("greedy outgoing lookup requires an incumbent task")
        return tuple(
            transition
            for transition in self.transitions
            if transition.incumbent.ordinal == incumbent.ordinal
        )

    def complete_raise_to_totals(
        self,
        panel_position: int,
    ) -> tuple[KernelRaiseToTotal, ...]:
        context_tasks = self.tasks_for_context(panel_position)
        if not context_tasks:
            raise IndexError("greedy panel position is absent")
        amounts = tuple(
            sorted(
                {
                    amount
                    for task in context_tasks
                    for amount in task.request.legal_raise_to_totals
                },
                key=lambda value: value.chips,
            )
        )
        return amounts

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "arm_counts_by_width": self.arm_counts_by_width,
                "executed_candidate_counts_by_target_width": (
                    self.executed_candidate_counts_by_target_width
                ),
                "exhaustive_teacher_result_sha256": (
                    self.exhaustive_teacher_result_sha256
                ),
                "panel_sha256": self.panel_sha256,
                "pool_sha256": self.pool_sha256,
                "qualification_result_sha256": self.qualification_result_sha256,
                "task_sha256": tuple(task.digest for task in self.tasks),
                "transition_counts_by_target_width": (
                    self.transition_counts_by_target_width
                ),
                "transition_sha256": tuple(
                    transition.digest for transition in self.transitions
                ),
                "version": "adr0323-closed-finite-block-greedy-schedule-v1",
            }
        )


def build_adr0323_closed_finite_block_greedy_schedule(
) -> ClosedFiniteBlockGreedySchedule:
    """Build the complete adaptive graph without invoking a value consumer."""

    retained = verify_adr0323_qualification_result_artifact()
    pool = verify_adr0324_structure_source_and_pool()
    if retained.panel.digest != ADR0323_QUALIFIED_PANEL_SHA256:
        raise RuntimeError("ADR-0326 qualified panel identity drifted")

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
            family = anchored_raise_subset_family(complete, width)
            for parent_subset in family.subsets:
                parent_key = tuple(value.chips for value in parent_subset)
                incumbent = task_map[parent_key]
                omitted = tuple(value for value in complete if value not in parent_subset)
                for candidate_position, proposed in enumerate(omitted):
                    child = tuple(
                        sorted(
                            (*parent_subset, proposed),
                            key=lambda value: value.chips,
                        )
                    )
                    augmented = task_map[tuple(value.chips for value in child)]
                    proposed_index = augmented.request.legal_raise_to_totals.index(
                        proposed
                    )
                    proposed_increment = (
                        augmented.response_row_set.reduced_bet_increments[
                            proposed_index
                        ]
                    )
                    block = OwnRaiseBlockIdentity(
                        context_semantic_digest=context.semantic_digest,
                        raise_to_total=proposed,
                        reduced_bet_increment=proposed_increment,
                        responder_private_range_width=ADR0323_PRIVATE_RANGE_WIDTH,
                        response_rows=_expected_response_rows(
                            context_semantic_digest=context.semantic_digest,
                            raise_to_totals=(proposed,),
                            reduced_bet_increments=(proposed_increment,),
                            responder_private_range_width=(
                                ADR0323_PRIVATE_RANGE_WIDTH
                            ),
                        ),
                    )
                    transitions.append(
                        ClosedFiniteBlockTransition(
                            ordinal=len(transitions),
                            candidate_position=candidate_position,
                            incumbent=incumbent,
                            augmented=augmented,
                            proposed_raise_to_total=proposed,
                            proposed_reduced_bet_increment=proposed_increment,
                            own_block=block,
                            phase_order=ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
                        )
                    )

    return ClosedFiniteBlockGreedySchedule(
        pool_sha256=pool.digest,
        qualification_result_sha256=retained.qualification_result_sha256,
        panel_sha256=retained.panel.digest,
        exhaustive_teacher_result_sha256=(
            ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
        ),
        tasks=tuple(tasks),
        transitions=tuple(transitions),
        arm_counts_by_width=ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH,
        transition_counts_by_target_width=(
            ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
        ),
        executed_candidate_counts_by_target_width=(
            ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
        ),
    )


@dataclass(frozen=True, slots=True)
class MaximumNormalizedFullRegretLimit:
    value: float

    def __post_init__(self) -> None:
        _require_unit_interval(self.value, label="maximum normalized full-regret limit")


@dataclass(frozen=True, slots=True)
class MeanNormalizedFullRegretLimit:
    value: float

    def __post_init__(self) -> None:
        _require_unit_interval(self.value, label="mean normalized full-regret limit")


@dataclass(frozen=True, slots=True)
class MinimumAggregateRecoveryFloor:
    value: float

    def __post_init__(self) -> None:
        _require_unit_interval(self.value, label="minimum aggregate-recovery floor")


@dataclass(frozen=True, slots=True)
class MaximumNormalizedTeacherExcessLimit:
    value: float

    def __post_init__(self) -> None:
        _require_unit_interval(
            self.value,
            label="maximum normalized teacher-excess limit",
        )


@dataclass(frozen=True, slots=True)
class MeanNormalizedTeacherExcessLimit:
    value: float

    def __post_init__(self) -> None:
        _require_unit_interval(
            self.value,
            label="mean normalized teacher-excess limit",
        )


ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT = (
    MaximumNormalizedFullRegretLimit(0.005)
)
ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT = MeanNormalizedFullRegretLimit(
    0.001
)
ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR = MinimumAggregateRecoveryFloor(0.90)
ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT = (
    MaximumNormalizedTeacherExcessLimit(0.001)
)
ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT = (
    MeanNormalizedTeacherExcessLimit(0.0002)
)


@dataclass(frozen=True, slots=True)
class CertifiedFiniteBlockPriceInterval:
    """Certified augmented-minus-incumbent chip interval."""

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
            raise ValueError("finite-block price endpoints must be finite floats")
        if self.signed_lower_chips > self.signed_upper_chips:
            raise ValueError("finite-block signed price interval is inverted")
        if (
            self.nonnegative_lower_chips != max(0.0, self.signed_lower_chips)
            or self.nonnegative_upper_chips != max(0.0, self.signed_upper_chips)
        ):
            raise ValueError("finite-block nonnegative price differs from signed price")


def certified_closed_finite_block_price(
    *,
    incumbent: CertifiedChipValueInterval,
    augmented: CertifiedChipValueInterval,
) -> CertifiedFiniteBlockPriceInterval:
    """Price a block only by conservative endpoints after response closure."""

    if not isinstance(incumbent, CertifiedChipValueInterval) or not isinstance(
        augmented,
        CertifiedChipValueInterval,
    ):
        raise TypeError("finite-block price requires certified chip-value intervals")
    signed_lower = augmented.lower_chips - incumbent.upper_chips
    signed_upper = augmented.upper_chips - incumbent.lower_chips
    if signed_upper < -ADR0323_NESTED_REVERSAL_ALLOWANCE.chips:
        raise ValueError("closed finite block reverses beyond the chip allowance")
    return CertifiedFiniteBlockPriceInterval(
        signed_lower_chips=signed_lower,
        signed_upper_chips=signed_upper,
        nonnegative_lower_chips=max(0.0, signed_lower),
        nonnegative_upper_chips=max(0.0, signed_upper),
    )


@dataclass(frozen=True, slots=True)
class CertifiedGreedyTeacherExcessInterval:
    """Width-matched teacher-minus-greedy chip interval."""

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
            raise ValueError("teacher-excess endpoints must be finite floats")
        if self.signed_lower_chips > self.signed_upper_chips:
            raise ValueError("teacher-excess signed interval is inverted")
        if (
            self.nonnegative_lower_chips != max(0.0, self.signed_lower_chips)
            or self.nonnegative_upper_chips != max(0.0, self.signed_upper_chips)
        ):
            raise ValueError("teacher-excess nonnegative view differs from signed view")


def certified_greedy_teacher_excess(
    *,
    teacher: CertifiedChipValueInterval,
    greedy: CertifiedChipValueInterval,
) -> CertifiedGreedyTeacherExcessInterval:
    regret = certified_full_minus_subset_regret(
        full=teacher,
        subset=greedy,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    return CertifiedGreedyTeacherExcessInterval(
        signed_lower_chips=regret.signed_lower_chips,
        signed_upper_chips=regret.signed_upper_chips,
        nonnegative_lower_chips=regret.nonnegative_lower_chips,
        nonnegative_upper_chips=regret.nonnegative_upper_chips,
    )


@dataclass(frozen=True, slots=True)
class NormalizedGreedyTeacherExcessInterval:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, float) and isfinite(value)
            for value in (self.lower, self.upper)
        ):
            raise ValueError("normalized teacher-excess endpoints must be finite")
        if self.lower < 0.0 or self.lower > self.upper:
            raise ValueError("normalized teacher-excess interval is invalid")


def normalize_greedy_teacher_excess(
    excess: CertifiedGreedyTeacherExcessInterval,
    *,
    payoff_span_chips: int,
) -> NormalizedGreedyTeacherExcessInterval:
    if not isinstance(excess, CertifiedGreedyTeacherExcessInterval):
        raise TypeError("teacher-excess normalization requires its nominal interval")
    if (
        isinstance(payoff_span_chips, bool)
        or not isinstance(payoff_span_chips, int)
        or payoff_span_chips <= 0
    ):
        raise ValueError("teacher-excess payoff span must be positive chips")
    return NormalizedGreedyTeacherExcessInterval(
        lower=excess.nonnegative_lower_chips / payoff_span_chips,
        upper=excess.nonnegative_upper_chips / payoff_span_chips,
    )


def normalize_full_regret(
    regret: CertifiedChipRegretInterval,
    *,
    payoff_span_chips: int,
) -> NormalizedTeacherRegretInterval:
    if not isinstance(regret, CertifiedChipRegretInterval):
        raise TypeError("full-regret normalization requires certified chip regret")
    if (
        isinstance(payoff_span_chips, bool)
        or not isinstance(payoff_span_chips, int)
        or payoff_span_chips <= 0
    ):
        raise ValueError("full-regret payoff span must be positive chips")
    return NormalizedTeacherRegretInterval(
        lower=regret.nonnegative_lower_chips / payoff_span_chips,
        upper=regret.nonnegative_upper_chips / payoff_span_chips,
    )


@dataclass(frozen=True, slots=True)
class ConservativeAggregateRecoveryInterval:
    lower: float
    upper: float
    achieved_gain_lower_chips: float
    achieved_gain_upper_chips: float
    available_gain_lower_chips: float
    available_gain_upper_chips: float

    def __post_init__(self) -> None:
        values = (
            self.lower,
            self.upper,
            self.achieved_gain_lower_chips,
            self.achieved_gain_upper_chips,
            self.available_gain_lower_chips,
            self.available_gain_upper_chips,
        )
        if not all(isinstance(value, float) and isfinite(value) for value in values):
            raise ValueError("aggregate-recovery values must be finite floats")
        if (
            self.achieved_gain_lower_chips < 0.0
            or self.achieved_gain_lower_chips > self.achieved_gain_upper_chips
            or self.available_gain_lower_chips <= 0.0
            or self.available_gain_lower_chips > self.available_gain_upper_chips
            or self.lower < 0.0
            or self.lower > self.upper
        ):
            raise ValueError("aggregate-recovery interval is invalid")
        if self.lower != (
            self.achieved_gain_lower_chips / self.available_gain_upper_chips
        ) or self.upper != (
            self.achieved_gain_upper_chips / self.available_gain_lower_chips
        ):
            raise ValueError("aggregate recovery was not formed from summed endpoints")


def conservative_aggregate_recovery(
    *,
    full_values: tuple[CertifiedChipValueInterval, ...],
    baseline_values: tuple[CertifiedChipValueInterval, ...],
    greedy_values: tuple[CertifiedChipValueInterval, ...],
) -> ConservativeAggregateRecoveryInterval:
    """Sum chip endpoints first, then divide in the conservative direction."""

    if (
        not isinstance(full_values, tuple)
        or not full_values
        or len(full_values) != len(baseline_values)
        or len(full_values) != len(greedy_values)
        or any(
            not isinstance(value, CertifiedChipValueInterval)
            for values in (full_values, baseline_values, greedy_values)
            for value in values
        )
    ):
        raise TypeError("aggregate recovery requires aligned value-interval tuples")
    available = tuple(
        certified_full_minus_subset_regret(
            full=full,
            subset=baseline,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        for full, baseline in zip(full_values, baseline_values, strict=True)
    )
    achieved = tuple(
        certified_full_minus_subset_regret(
            full=greedy,
            subset=baseline,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        for greedy, baseline in zip(greedy_values, baseline_values, strict=True)
    )
    available_lower = sum(item.nonnegative_lower_chips for item in available)
    available_upper = sum(item.nonnegative_upper_chips for item in available)
    achieved_lower = sum(item.nonnegative_lower_chips for item in achieved)
    achieved_upper = sum(item.nonnegative_upper_chips for item in achieved)
    if available_lower <= 0.0:
        raise ValueError("aggregate recovery has no certified available gain")
    return ConservativeAggregateRecoveryInterval(
        lower=achieved_lower / available_upper,
        upper=achieved_upper / available_lower,
        achieved_gain_lower_chips=achieved_lower,
        achieved_gain_upper_chips=achieved_upper,
        available_gain_lower_chips=available_lower,
        available_gain_upper_chips=available_upper,
    )


@dataclass(frozen=True, slots=True)
class GreedyCertifiedValueEvidence:
    """Artifact-sized accepted evidence rebound to one exact greedy arm."""

    task_sha256: str
    request_sha256: str
    public_state_sha256: str
    legal_raise_set_sha256: str
    linear_program_sha256: str
    response_row_set_sha256: str
    consumer_source_sha256: str
    consumer_protocol_sha256: str
    public_highs_ds_invocation_count: int
    raise_to_totals: tuple[int, ...]
    reduced_bet_increments: tuple[int, ...]
    feasible_behavioral_lower_bound_chips: float
    certified_upper_bound_chips: float
    signed_certificate_gap_chips: float
    certified_gap_chips: float

    def __post_init__(self) -> None:
        for label, value in (
            ("greedy value task", self.task_sha256),
            ("greedy value request", self.request_sha256),
            ("greedy value public state", self.public_state_sha256),
            ("greedy value legal set", self.legal_raise_set_sha256),
            ("greedy value LP", self.linear_program_sha256),
            ("greedy value response-row set", self.response_row_set_sha256),
            ("greedy value consumer source", self.consumer_source_sha256),
            ("greedy value consumer protocol", self.consumer_protocol_sha256),
        ):
            _require_digest(value, label=label)
        if self.consumer_protocol_sha256 != ADR0321_CONSUMER_PROTOCOL_SHA256:
            raise ValueError("greedy value consumer protocol drifted")
        if self.consumer_source_sha256 != ADR0321_CONSUMER_SOURCE_MANIFEST[
            "certified_reduced_sizing_consumer_v2.py"
        ]:
            raise ValueError("greedy value consumer source drifted")
        if self.public_highs_ds_invocation_count != 1:
            raise ValueError("greedy accepted evidence must own one public call")
        for label, values in (
            ("raise-to totals", self.raise_to_totals),
            ("reduced increments", self.reduced_bet_increments),
        ):
            if (
                not isinstance(values, tuple)
                or not values
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value <= 0
                    for value in values
                )
            ):
                raise TypeError(f"greedy value {label} must be positive chip integers")
        if len(self.raise_to_totals) != len(self.reduced_bet_increments):
            raise ValueError("greedy value amount mapping is not one-to-one")
        for label, value in (
            ("feasible lower", self.feasible_behavioral_lower_bound_chips),
            ("certified upper", self.certified_upper_bound_chips),
            ("signed gap", self.signed_certificate_gap_chips),
            ("certified gap", self.certified_gap_chips),
        ):
            _require_finite(value, label=f"greedy value {label}")
        if (
            self.feasible_behavioral_lower_bound_chips
            > self.certified_upper_bound_chips
            or self.signed_certificate_gap_chips
            != self.certified_upper_bound_chips
            - self.feasible_behavioral_lower_bound_chips
            or self.certified_gap_chips
            != max(0.0, self.signed_certificate_gap_chips)
        ):
            raise ValueError("greedy value certificate endpoints or gap drifted")

    @property
    def value(self) -> CertifiedChipValueInterval:
        return CertifiedChipValueInterval(
            lower_chips=self.feasible_behavioral_lower_bound_chips,
            upper_chips=self.certified_upper_bound_chips,
        )

    @property
    def digest(self) -> str:
        return _canonical_sha256(_value_evidence_payload(self))

    def verify_task(self, task: GreedySubsetTask) -> None:
        if not isinstance(task, GreedySubsetTask):
            raise TypeError("greedy value rebinding requires a semantic task")
        bound = _bind_request(task.request)
        expected = (
            task.digest,
            bound.request_sha256,
            bound.public_state_sha256,
            bound.legal_raise_set_sha256,
            bound.linear_program_sha256,
            task.response_row_set.digest,
            tuple(value.chips for value in bound.legal_raise_to_totals),
            tuple(value.chips for value in bound.reduced_bet_increments),
        )
        observed = (
            self.task_sha256,
            self.request_sha256,
            self.public_state_sha256,
            self.legal_raise_set_sha256,
            self.linear_program_sha256,
            self.response_row_set_sha256,
            self.raise_to_totals,
            self.reduced_bet_increments,
        )
        if observed != expected:
            raise ValueError("greedy value evidence differs from its exact task")


def _value_evidence_from_accepted(
    *,
    task: GreedySubsetTask,
    accepted: CertifiedReducedSizingAcceptedV2,
) -> GreedyCertifiedValueEvidence:
    if not isinstance(accepted, CertifiedReducedSizingAcceptedV2):
        raise TypeError("greedy value evidence requires accepted consumer output")
    if (
        accepted.request != task.request
        or accepted.request_sha256 != task.request_sha256
        or accepted.legal_raise_set_sha256 != task.legal_raise_set_sha256
        or accepted.solution.linear_program_sha256 != task.linear_program_sha256
        or accepted.public_highs_ds_invocation_count != 1
    ):
        raise ValueError("greedy accepted output differs from its exact task")
    evidence = GreedyCertifiedValueEvidence(
        task_sha256=task.digest,
        request_sha256=accepted.request_sha256,
        public_state_sha256=accepted.public_state_sha256,
        legal_raise_set_sha256=accepted.legal_raise_set_sha256,
        linear_program_sha256=accepted.solution.linear_program_sha256,
        response_row_set_sha256=task.response_row_set.digest,
        consumer_source_sha256=accepted.consumer_source_sha256,
        consumer_protocol_sha256=accepted.consumer_protocol_sha256,
        public_highs_ds_invocation_count=accepted.public_highs_ds_invocation_count,
        raise_to_totals=tuple(
            value.chips for value in accepted.legal_raise_to_totals
        ),
        reduced_bet_increments=tuple(
            value.chips for value in accepted.reduced_bet_increments
        ),
        feasible_behavioral_lower_bound_chips=(
            accepted.feasible_behavioral_lower_bound_chips
        ),
        certified_upper_bound_chips=accepted.certified_upper_bound_chips,
        signed_certificate_gap_chips=accepted.signed_certificate_gap_chips,
        certified_gap_chips=accepted.certified_gap_chips,
    )
    evidence.verify_task(task)
    return evidence


def _value_evidence_payload(
    evidence: GreedyCertifiedValueEvidence,
) -> dict[str, object]:
    return {
        "bet_increments": evidence.reduced_bet_increments,
        "certified_gap_hex": evidence.certified_gap_chips.hex(),
        "certified_upper_hex": evidence.certified_upper_bound_chips.hex(),
        "consumer_protocol_sha256": evidence.consumer_protocol_sha256,
        "consumer_source_sha256": evidence.consumer_source_sha256,
        "feasible_lower_hex": (
            evidence.feasible_behavioral_lower_bound_chips.hex()
        ),
        "legal_raise_set_sha256": evidence.legal_raise_set_sha256,
        "linear_program_sha256": evidence.linear_program_sha256,
        "public_call_count": evidence.public_highs_ds_invocation_count,
        "public_state_sha256": evidence.public_state_sha256,
        "raise_to_totals": evidence.raise_to_totals,
        "request_sha256": evidence.request_sha256,
        "response_row_set_sha256": evidence.response_row_set_sha256,
        "signed_gap_hex": evidence.signed_certificate_gap_chips.hex(),
        "task_sha256": evidence.task_sha256,
    }


@dataclass(frozen=True, slots=True)
class ClosedFiniteBlockCandidateEvidence:
    transition: ClosedFiniteBlockTransition
    incumbent_value_sha256: str
    augmented: GreedyCertifiedValueEvidence
    price: CertifiedFiniteBlockPriceInterval

    def __post_init__(self) -> None:
        if not isinstance(self.transition, ClosedFiniteBlockTransition):
            raise TypeError("finite-block candidate requires a semantic transition")
        _require_digest(
            self.incumbent_value_sha256,
            label="finite-block incumbent value",
        )
        if not isinstance(self.augmented, GreedyCertifiedValueEvidence):
            raise TypeError("finite-block candidate requires augmented evidence")
        self.augmented.verify_task(self.transition.augmented)
        if not isinstance(self.price, CertifiedFiniteBlockPriceInterval):
            raise TypeError("finite-block candidate requires a nominal price")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "augmented_value_sha256": self.augmented.digest,
                "incumbent_value_sha256": self.incumbent_value_sha256,
                "price": _finite_block_price_payload(self.price),
                "transition_sha256": self.transition.digest,
                "version": "adr0323-closed-finite-block-candidate-evidence-v1",
            }
        )


def build_closed_finite_block_candidate(
    *,
    transition: ClosedFiniteBlockTransition,
    incumbent: GreedyCertifiedValueEvidence,
    augmented: GreedyCertifiedValueEvidence,
) -> ClosedFiniteBlockCandidateEvidence:
    incumbent.verify_task(transition.incumbent)
    augmented.verify_task(transition.augmented)
    return ClosedFiniteBlockCandidateEvidence(
        transition=transition,
        incumbent_value_sha256=incumbent.digest,
        augmented=augmented,
        price=certified_closed_finite_block_price(
            incumbent=incumbent.value,
            augmented=augmented.value,
        ),
    )


def select_greedy_candidate(
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...],
) -> ClosedFiniteBlockCandidateEvidence:
    """Greatest behavioral lower endpoint; exact ties choose smaller raise."""

    if not isinstance(candidates, tuple) or not candidates or any(
        not isinstance(value, ClosedFiniteBlockCandidateEvidence)
        for value in candidates
    ):
        raise TypeError("greedy selection requires immutable candidate evidence")
    incumbent_digest = candidates[0].transition.incumbent.digest
    incumbent_value_digest = candidates[0].incumbent_value_sha256
    if any(
        candidate.transition.incumbent.digest != incumbent_digest
        or candidate.incumbent_value_sha256 != incumbent_value_digest
        for candidate in candidates
    ):
        raise ValueError("greedy candidates do not share one incumbent")
    expected_order = tuple(
        sorted(candidates, key=lambda item: item.transition.proposed_raise_to_total.chips)
    )
    if candidates != expected_order or tuple(
        item.transition.candidate_position for item in candidates
    ) != tuple(range(len(candidates))):
        raise ValueError("greedy candidates are not in exact omitted-raise order")
    greatest_lower = max(
        candidate.augmented.feasible_behavioral_lower_bound_chips
        for candidate in candidates
    )
    return next(
        candidate
        for candidate in candidates
        if candidate.augmented.feasible_behavioral_lower_bound_chips
        == greatest_lower
    )


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherWidthReference:
    """Exact retained teacher evidence for the selected width and subset."""

    exhaustive_teacher_result_sha256: str
    context_result_sha256: str
    width_result_sha256: str
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    raise_width: RaiseActionWidth
    payoff_span_chips: int
    full_value: CertifiedChipValueInterval
    teacher_value: CertifiedChipValueInterval
    selected_subset_index: int
    selected_request_sha256: str
    selected_legal_raise_set_sha256: str
    selected_linear_program_sha256: str
    selected_raise_to_totals: tuple[int, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("teacher reference campaign", self.exhaustive_teacher_result_sha256),
            ("teacher reference context", self.context_result_sha256),
            ("teacher reference width", self.width_result_sha256),
            ("teacher reference semantic context", self.context_semantic_digest),
            ("teacher reference request", self.selected_request_sha256),
            ("teacher reference legal set", self.selected_legal_raise_set_sha256),
            ("teacher reference LP", self.selected_linear_program_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.exhaustive_teacher_result_sha256
            != ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
        ):
            raise ValueError("teacher reference belongs to another campaign")
        panel = _require_nonnegative_int(
            self.panel_position,
            label="teacher reference panel position",
        )
        if panel >= 16:
            raise ValueError("teacher reference panel position exceeds the panel")
        _require_nonnegative_int(self.pool_index, label="teacher reference pool index")
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("teacher reference requires a raise-action width")
        if self.raise_width.count not in range(3, 7):
            raise ValueError("teacher reference width lies outside greedy rounds")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("teacher reference payoff span must be positive chips")
        if not isinstance(self.full_value, CertifiedChipValueInterval) or not isinstance(
            self.teacher_value,
            CertifiedChipValueInterval,
        ):
            raise TypeError("teacher reference requires certified value intervals")
        _require_nonnegative_int(
            self.selected_subset_index,
            label="teacher reference selected subset index",
        )
        if (
            not isinstance(self.selected_raise_to_totals, tuple)
            or len(self.selected_raise_to_totals) != self.raise_width.count
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                for value in self.selected_raise_to_totals
            )
        ):
            raise TypeError("teacher reference selected totals have the wrong width")

    def verify_selected_task(self, task: GreedySubsetTask) -> None:
        if not isinstance(task, GreedySubsetTask):
            raise TypeError("teacher reference requires a semantic selected task")
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
            self.context_semantic_digest,
            self.raise_width,
            self.selected_subset_index,
            self.selected_request_sha256,
            self.selected_legal_raise_set_sha256,
            self.selected_linear_program_sha256,
            self.selected_raise_to_totals,
        )
        if observed != expected:
            raise ValueError("teacher reference differs from selected greedy arm")

    @property
    def digest(self) -> str:
        return _canonical_sha256(_teacher_reference_payload(self))


def _teacher_reference_for_selected(
    *,
    teacher_result: RetainedExhaustiveTeacherResult,
    teacher_context: RetainedExhaustiveTeacherContext,
    teacher_width: RetainedExhaustiveTeacherWidth,
    selected_task: GreedySubsetTask,
) -> ExhaustiveTeacherWidthReference:
    if teacher_result.campaign_result_sha256 != (
        ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
    ):
        raise ValueError("greedy teacher reference uses another campaign")
    if (
        teacher_context.panel_position != selected_task.panel_position
        or teacher_context.pool_index != selected_task.pool_index
        or teacher_context.context_semantic_digest
        != selected_task.context_semantic_digest
        or teacher_width.raise_width != selected_task.raise_width
    ):
        raise ValueError("greedy selected arm and teacher context differ")
    subset = teacher_width.subsets[selected_task.subset_index]
    expected = (
        subset.subset_index,
        subset.request_sha256,
        subset.legal_raise_set_sha256,
        subset.linear_program_sha256,
        subset.raise_to_totals,
    )
    observed = (
        selected_task.subset_index,
        selected_task.request_sha256,
        selected_task.legal_raise_set_sha256,
        selected_task.linear_program_sha256,
        selected_task.raise_to_totals,
    )
    if observed != expected:
        raise ValueError("selected greedy arm lacks an exact teacher counterpart")
    reference = ExhaustiveTeacherWidthReference(
        exhaustive_teacher_result_sha256=teacher_result.campaign_result_sha256,
        context_result_sha256=teacher_context.context_result_sha256,
        width_result_sha256=teacher_width.width_result_sha256,
        panel_position=teacher_context.panel_position,
        pool_index=teacher_context.pool_index,
        context_semantic_digest=teacher_context.context_semantic_digest,
        raise_width=teacher_width.raise_width,
        payoff_span_chips=teacher_context.payoff_span_chips,
        full_value=CertifiedChipValueInterval(
            lower_chips=teacher_context.full_lower_chips,
            upper_chips=teacher_context.full_upper_chips,
        ),
        teacher_value=CertifiedChipValueInterval(
            lower_chips=teacher_width.teacher_lower_chips,
            upper_chips=teacher_width.teacher_upper_chips,
        ),
        selected_subset_index=subset.subset_index,
        selected_request_sha256=subset.request_sha256,
        selected_legal_raise_set_sha256=subset.legal_raise_set_sha256,
        selected_linear_program_sha256=subset.linear_program_sha256,
        selected_raise_to_totals=subset.raise_to_totals,
    )
    reference.verify_selected_task(selected_task)
    return reference


@dataclass(frozen=True, slots=True)
class GreedyRoundResult:
    target_raise_width: RaiseActionWidth
    incumbent_task: GreedySubsetTask
    incumbent: GreedyCertifiedValueEvidence
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]
    selected_candidate_position: int
    teacher_reference: ExhaustiveTeacherWidthReference
    full_regret: CertifiedChipRegretInterval
    normalized_full_regret: NormalizedTeacherRegretInterval
    teacher_excess: CertifiedGreedyTeacherExcessInterval
    normalized_teacher_excess: NormalizedGreedyTeacherExcessInterval

    def __post_init__(self) -> None:
        if not isinstance(self.target_raise_width, RaiseActionWidth):
            raise TypeError("greedy round requires a target raise width")
        if self.target_raise_width.count not in range(3, 7):
            raise ValueError("greedy target width lies outside three through six")
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
        decision = self.incumbent_task.request.betting.legal_decision()
        bounds = decision.raise_bounds
        if bounds is None:
            raise ValueError("greedy round incumbent has no complete legal universe")
        universe_width = bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        if len(self.candidates) != universe_width - self.incumbent_task.raise_width.count:
            raise ValueError("greedy round candidate set is not complete")
        for candidate in self.candidates:
            if (
                candidate.transition.incumbent != self.incumbent_task
                or candidate.incumbent_value_sha256 != self.incumbent.digest
                or candidate.transition.augmented.raise_width
                != self.target_raise_width
                or candidate.price
                != certified_closed_finite_block_price(
                    incumbent=self.incumbent.value,
                    augmented=candidate.augmented.value,
                )
            ):
                raise ValueError("greedy round candidate evidence drifted")
        selected = select_greedy_candidate(self.candidates)
        selected_position = _require_nonnegative_int(
            self.selected_candidate_position,
            label="greedy selected candidate position",
        )
        if (
            selected_position >= len(self.candidates)
            or self.candidates[selected_position] != selected
        ):
            raise ValueError("greedy round did not apply the frozen selection rule")
        if not isinstance(self.teacher_reference, ExhaustiveTeacherWidthReference):
            raise TypeError("greedy round requires width-matched teacher evidence")
        self.teacher_reference.verify_selected_task(selected.transition.augmented)
        if self.teacher_reference.payoff_span_chips != (
            self.incumbent_task.request.betting.pot
            + 2 * self.incumbent_task.request.betting.stacks[0]
        ):
            raise ValueError("greedy round normalized by something other than payoff span")
        expected_full_regret = certified_full_minus_subset_regret(
            full=self.teacher_reference.full_value,
            subset=selected.augmented.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_normalized_full = normalize_full_regret(
            expected_full_regret,
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
            self.full_regret != expected_full_regret
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
        return _canonical_sha256(
            {
                "candidate_sha256": tuple(value.digest for value in self.candidates),
                "full_regret": _regret_payload(self.full_regret),
                "incumbent_task_sha256": self.incumbent_task.digest,
                "incumbent_value_sha256": self.incumbent.digest,
                "normalized_full_regret": _normalized_regret_payload(
                    self.normalized_full_regret
                ),
                "normalized_teacher_excess": _normalized_excess_payload(
                    self.normalized_teacher_excess
                ),
                "selected_candidate_position": self.selected_candidate_position,
                "target_raise_width": self.target_raise_width.count,
                "teacher_excess": _teacher_excess_payload(self.teacher_excess),
                "teacher_reference_sha256": self.teacher_reference.digest,
                "version": "adr0323-closed-finite-block-greedy-round-v1",
            }
        )


def build_greedy_round_result(
    *,
    target_raise_width: RaiseActionWidth,
    incumbent_task: GreedySubsetTask,
    incumbent: GreedyCertifiedValueEvidence,
    candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...],
    teacher_result: RetainedExhaustiveTeacherResult,
    teacher_context: RetainedExhaustiveTeacherContext,
) -> GreedyRoundResult:
    selected = select_greedy_candidate(candidates)
    teacher_width = next(
        value
        for value in teacher_context.widths
        if value.raise_width == target_raise_width
    )
    reference = _teacher_reference_for_selected(
        teacher_result=teacher_result,
        teacher_context=teacher_context,
        teacher_width=teacher_width,
        selected_task=selected.transition.augmented,
    )
    full_regret = certified_full_minus_subset_regret(
        full=reference.full_value,
        subset=selected.augmented.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    teacher_excess = certified_greedy_teacher_excess(
        teacher=reference.teacher_value,
        greedy=selected.augmented.value,
    )
    return GreedyRoundResult(
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
        teacher_excess=teacher_excess,
        normalized_teacher_excess=normalize_greedy_teacher_excess(
            teacher_excess,
            payoff_span_chips=reference.payoff_span_chips,
        ),
    )


@dataclass(frozen=True, slots=True)
class GreedyContextResult:
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    payoff_span_chips: int
    initial_task: GreedySubsetTask
    initial: GreedyCertifiedValueEvidence
    rounds: tuple[GreedyRoundResult, ...]

    def __post_init__(self) -> None:
        panel = _require_nonnegative_int(
            self.panel_position,
            label="greedy context panel position",
        )
        if panel >= 16:
            raise ValueError("greedy context panel position exceeds the panel")
        _require_nonnegative_int(self.pool_index, label="greedy context pool index")
        _require_digest(self.context_semantic_digest, label="greedy context identity")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("greedy context payoff span must be positive chips")
        if (
            not isinstance(self.initial_task, GreedySubsetTask)
            or self.initial_task.raise_width.count != 2
            or self.initial_task.subset_index != 0
            or self.initial_task.panel_position != self.panel_position
            or self.initial_task.pool_index != self.pool_index
            or self.initial_task.context_semantic_digest
            != self.context_semantic_digest
        ):
            raise ValueError("greedy context has the wrong anchored initial arm")
        if not isinstance(self.initial, GreedyCertifiedValueEvidence):
            raise TypeError("greedy context requires initial value evidence")
        self.initial.verify_task(self.initial_task)
        if (
            not isinstance(self.rounds, tuple)
            or tuple(value.target_raise_width.count for value in self.rounds)
            != (3, 4, 5, 6)
        ):
            raise ValueError("greedy context requires exact width-three-through-six rounds")
        incumbent_task = self.initial_task
        incumbent = self.initial
        for round_result in self.rounds:
            if (
                round_result.incumbent_task != incumbent_task
                or round_result.incumbent != incumbent
                or round_result.teacher_reference.panel_position
                != self.panel_position
                or round_result.teacher_reference.pool_index != self.pool_index
                or round_result.teacher_reference.context_semantic_digest
                != self.context_semantic_digest
                or round_result.teacher_reference.payoff_span_chips
                != self.payoff_span_chips
            ):
                raise ValueError("greedy context round chain drifted")
            incumbent_task = round_result.selected.transition.augmented
            incumbent = round_result.selected.augmented

    @property
    def public_highs_ds_invocation_count(self) -> int:
        return 1 + sum(len(value.candidates) for value in self.rounds)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_semantic_digest": self.context_semantic_digest,
                "initial_task_sha256": self.initial_task.digest,
                "initial_value_sha256": self.initial.digest,
                "panel_position": self.panel_position,
                "payoff_span_chips": self.payoff_span_chips,
                "pool_index": self.pool_index,
                "round_sha256": tuple(value.digest for value in self.rounds),
                "version": "adr0323-closed-finite-block-greedy-context-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class GreedyWidthGateResult:
    raise_width: RaiseActionWidth
    maximum_normalized_full_regret_upper: float
    mean_normalized_full_regret_lower: float
    mean_normalized_full_regret_upper: float
    aggregate_recovery: ConservativeAggregateRecoveryInterval
    maximum_normalized_teacher_excess_upper: float
    mean_normalized_teacher_excess_lower: float
    mean_normalized_teacher_excess_upper: float
    maximum_full_regret_pass: bool
    mean_full_regret_pass: bool
    aggregate_recovery_pass: bool
    maximum_teacher_excess_pass: bool
    mean_teacher_excess_pass: bool

    def __post_init__(self) -> None:
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("greedy width gate requires a raise-action width")
        if self.raise_width.count not in range(3, 7):
            raise ValueError("greedy width gate lies outside three through six")
        numeric = (
            self.maximum_normalized_full_regret_upper,
            self.mean_normalized_full_regret_lower,
            self.mean_normalized_full_regret_upper,
            self.maximum_normalized_teacher_excess_upper,
            self.mean_normalized_teacher_excess_lower,
            self.mean_normalized_teacher_excess_upper,
        )
        if not all(
            isinstance(value, float) and isfinite(value) and value >= 0.0
            for value in numeric
        ):
            raise ValueError("greedy width gate metrics must be finite nonnegative")
        if (
            self.mean_normalized_full_regret_lower
            > self.mean_normalized_full_regret_upper
            or self.mean_normalized_teacher_excess_lower
            > self.mean_normalized_teacher_excess_upper
        ):
            raise ValueError("greedy width gate mean interval is inverted")
        if not isinstance(
            self.aggregate_recovery,
            ConservativeAggregateRecoveryInterval,
        ):
            raise TypeError("greedy width gate requires aggregate recovery")
        expected = (
            self.maximum_normalized_full_regret_upper
            <= ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value,
            self.mean_normalized_full_regret_upper
            <= ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value,
            self.aggregate_recovery.lower
            >= ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR.value,
            self.maximum_normalized_teacher_excess_upper
            <= ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT.value,
            self.mean_normalized_teacher_excess_upper
            <= ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT.value,
        )
        observed = (
            self.maximum_full_regret_pass,
            self.mean_full_regret_pass,
            self.aggregate_recovery_pass,
            self.maximum_teacher_excess_pass,
            self.mean_teacher_excess_pass,
        )
        if any(not isinstance(value, bool) for value in observed) or observed != expected:
            raise ValueError("greedy width gate booleans differ from frozen conjuncts")

    @property
    def passes(self) -> bool:
        return all(
            (
                self.maximum_full_regret_pass,
                self.mean_full_regret_pass,
                self.aggregate_recovery_pass,
                self.maximum_teacher_excess_pass,
                self.mean_teacher_excess_pass,
            )
        )

    @property
    def digest(self) -> str:
        return _canonical_sha256(_width_gate_payload(self))


def build_greedy_width_gate_result(
    *,
    raise_width: RaiseActionWidth,
    contexts: tuple[GreedyContextResult, ...],
) -> GreedyWidthGateResult:
    if (
        not isinstance(contexts, tuple)
        or len(contexts) != 16
        or tuple(value.panel_position for value in contexts) != tuple(range(16))
    ):
        raise ValueError("greedy width aggregation requires the complete panel")
    rounds = tuple(
        next(
            round_result
            for round_result in context.rounds
            if round_result.target_raise_width == raise_width
        )
        for context in contexts
    )
    full_values = tuple(value.teacher_reference.full_value for value in rounds)
    baseline_values = tuple(context.initial.value for context in contexts)
    greedy_values = tuple(value.selected.augmented.value for value in rounds)
    recovery = conservative_aggregate_recovery(
        full_values=full_values,
        baseline_values=baseline_values,
        greedy_values=greedy_values,
    )
    maximum_full = max(value.normalized_full_regret.upper for value in rounds)
    mean_full_lower = sum(
        value.normalized_full_regret.lower for value in rounds
    ) / len(rounds)
    mean_full_upper = sum(
        value.normalized_full_regret.upper for value in rounds
    ) / len(rounds)
    maximum_excess = max(
        value.normalized_teacher_excess.upper for value in rounds
    )
    mean_excess_lower = sum(
        value.normalized_teacher_excess.lower for value in rounds
    ) / len(rounds)
    mean_excess_upper = sum(
        value.normalized_teacher_excess.upper for value in rounds
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


class GreedyStopReason(StrEnum):
    COMPLETED_SELECTED = "completed_selected"
    COMPLETED_NO_WIDTH = "completed_no_width"
    CONSUMER_REJECTED = "consumer_rejected"
    NUMERICAL_REJECTED = "numerical_rejected"


class GreedyFailureKind(StrEnum):
    CONSUMER_REJECTION = "consumer_rejection"
    NUMERICAL_REJECTION = "numerical_rejection"


class GreedyFailureStage(StrEnum):
    INITIAL_ARM = "initial_arm"
    CANDIDATE_ARM = "candidate_arm"
    CANDIDATE_PRICE = "candidate_price"
    ROUND_REDUCTION = "round_reduction"
    CAMPAIGN_REDUCTION = "campaign_reduction"


@dataclass(frozen=True, slots=True)
class GreedyRunnerException:
    module: str
    type_name: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.module, str) or not self.module:
            raise ValueError("greedy exception module must be nonempty")
        if not isinstance(self.type_name, str) or not self.type_name:
            raise ValueError("greedy exception type must be nonempty")
        if not isinstance(self.message, str):
            raise TypeError("greedy exception message must be text")


def _exception_chain(error: Exception) -> tuple[GreedyRunnerException, ...]:
    result: list[GreedyRunnerException] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        result.append(
            GreedyRunnerException(
                module=type(current).__module__,
                type_name=type(current).__qualname__,
                message=str(current),
            )
        )
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return tuple(result)


@dataclass(frozen=True, slots=True)
class GreedyPartialContextEvidence:
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    payoff_span_chips: int
    initial_task: GreedySubsetTask
    initial: GreedyCertifiedValueEvidence | None
    completed_rounds: tuple[GreedyRoundResult, ...]
    incomplete_candidates: tuple[ClosedFiniteBlockCandidateEvidence, ...]

    def __post_init__(self) -> None:
        panel = _require_nonnegative_int(
            self.panel_position,
            label="partial greedy panel position",
        )
        if panel >= 16:
            raise ValueError("partial greedy panel position exceeds the panel")
        _require_nonnegative_int(self.pool_index, label="partial greedy pool index")
        _require_digest(
            self.context_semantic_digest,
            label="partial greedy context",
        )
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("partial greedy payoff span must be positive chips")
        if (
            not isinstance(self.initial_task, GreedySubsetTask)
            or self.initial_task.panel_position != self.panel_position
            or self.initial_task.pool_index != self.pool_index
            or self.initial_task.context_semantic_digest
            != self.context_semantic_digest
            or self.initial_task.raise_width.count != 2
        ):
            raise ValueError("partial greedy initial task differs from its context")
        if self.initial is not None:
            if not isinstance(self.initial, GreedyCertifiedValueEvidence):
                raise TypeError("partial greedy initial evidence must be semantic")
            self.initial.verify_task(self.initial_task)
        elif self.completed_rounds or self.incomplete_candidates:
            raise ValueError("partial greedy candidate evidence lacks its initial arm")
        if not isinstance(self.completed_rounds, tuple) or any(
            not isinstance(value, GreedyRoundResult)
            for value in self.completed_rounds
        ):
            raise TypeError("partial greedy completed rounds must be semantic")
        if tuple(
            value.target_raise_width.count for value in self.completed_rounds
        ) != tuple(range(3, 3 + len(self.completed_rounds))):
            raise ValueError("partial greedy completed rounds are not a width prefix")
        incumbent_task = self.initial_task
        incumbent = self.initial
        for round_result in self.completed_rounds:
            if (
                round_result.incumbent_task != incumbent_task
                or round_result.incumbent != incumbent
            ):
                raise ValueError("partial greedy completed round chain drifted")
            incumbent_task = round_result.selected.transition.augmented
            incumbent = round_result.selected.augmented
        if not isinstance(self.incomplete_candidates, tuple) or any(
            not isinstance(value, ClosedFiniteBlockCandidateEvidence)
            for value in self.incomplete_candidates
        ):
            raise TypeError("partial greedy candidates must be semantic")
        if self.incomplete_candidates:
            if incumbent is None or any(
                value.transition.incumbent != incumbent_task
                or value.incumbent_value_sha256 != incumbent.digest
                for value in self.incomplete_candidates
            ):
                raise ValueError("partial greedy candidates differ from their incumbent")
            if tuple(
                value.transition.candidate_position
                for value in self.incomplete_candidates
            ) != tuple(range(len(self.incomplete_candidates))):
                raise ValueError("partial greedy candidates are not a prefix")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        return (
            (0 if self.initial is None else 1)
            + sum(len(value.candidates) for value in self.completed_rounds)
            + len(self.incomplete_candidates)
        )

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "completed_round_sha256": tuple(
                    value.digest for value in self.completed_rounds
                ),
                "context_semantic_digest": self.context_semantic_digest,
                "incomplete_candidate_sha256": tuple(
                    value.digest for value in self.incomplete_candidates
                ),
                "initial_task_sha256": self.initial_task.digest,
                "initial_value_sha256": (
                    None if self.initial is None else self.initial.digest
                ),
                "panel_position": self.panel_position,
                "payoff_span_chips": self.payoff_span_chips,
                "pool_index": self.pool_index,
                "version": "adr0323-closed-finite-block-partial-context-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class GreedyFailure:
    kind: GreedyFailureKind
    stage: GreedyFailureStage
    current_task: GreedySubsetTask
    current_transition: ClosedFiniteBlockTransition | None
    partial_context: GreedyPartialContextEvidence | None
    rejected: CertifiedReducedSizingRejectedV2 | None = None
    accepted_at_failure: GreedyCertifiedValueEvidence | None = None
    exception_chain: tuple[GreedyRunnerException, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, GreedyFailureKind):
            raise TypeError("greedy failure kind must be semantic")
        if not isinstance(self.stage, GreedyFailureStage):
            raise TypeError("greedy failure stage must be semantic")
        if not isinstance(self.current_task, GreedySubsetTask):
            raise TypeError("greedy failure requires its exact current task")
        if self.current_transition is not None and not isinstance(
            self.current_transition,
            ClosedFiniteBlockTransition,
        ):
            raise TypeError("greedy failure transition must be semantic")
        if self.partial_context is not None and not isinstance(
            self.partial_context,
            GreedyPartialContextEvidence,
        ):
            raise TypeError("greedy failure partial context must be semantic")
        if self.stage is GreedyFailureStage.CAMPAIGN_REDUCTION:
            if self.partial_context is not None or self.current_transition is not None:
                raise ValueError("campaign reduction cannot retain a partial context")
        else:
            if (
                self.partial_context is None
                or self.current_task.panel_position
                != self.partial_context.panel_position
            ):
                raise ValueError("greedy failure lacks its current partial context")
        if self.stage is GreedyFailureStage.INITIAL_ARM:
            if self.current_transition is not None:
                raise ValueError("initial-arm failure cannot name a transition")
        elif self.stage is not GreedyFailureStage.CAMPAIGN_REDUCTION:
            if (
                self.current_transition is None
                or self.current_transition.augmented != self.current_task
            ):
                raise ValueError("candidate failure lacks its exact transition")

        if self.kind is GreedyFailureKind.CONSUMER_REJECTION:
            if (
                not isinstance(self.rejected, CertifiedReducedSizingRejectedV2)
                or self.accepted_at_failure is not None
                or self.exception_chain
                or self.stage
                not in (
                    GreedyFailureStage.INITIAL_ARM,
                    GreedyFailureStage.CANDIDATE_ARM,
                )
                or self.rejected.request != self.current_task.request
            ):
                raise ValueError("consumer greedy failure has the wrong evidence")
        else:
            if self.rejected is not None or not self.exception_chain:
                raise ValueError("numerical greedy failure has the wrong evidence")
            if self.stage is GreedyFailureStage.CANDIDATE_PRICE:
                if not isinstance(
                    self.accepted_at_failure,
                    GreedyCertifiedValueEvidence,
                ):
                    raise TypeError("candidate-price failure must retain accepted value")
                self.accepted_at_failure.verify_task(self.current_task)
            elif self.accepted_at_failure is not None:
                raise ValueError("non-price numerical failure cannot add a value")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        count = (
            0
            if self.partial_context is None
            else self.partial_context.public_highs_ds_invocation_count
        )
        if self.rejected is not None:
            count += self.rejected.public_highs_ds_invocation_count
        if self.accepted_at_failure is not None:
            count += 1
        return count

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "accepted_at_failure_sha256": (
                    None
                    if self.accepted_at_failure is None
                    else self.accepted_at_failure.digest
                ),
                "current_task_sha256": self.current_task.digest,
                "current_transition_sha256": (
                    None
                    if self.current_transition is None
                    else self.current_transition.digest
                ),
                "exception_chain": tuple(
                    (value.module, value.type_name, value.message)
                    for value in self.exception_chain
                ),
                "kind": self.kind.value,
                "partial_context_sha256": (
                    None if self.partial_context is None else self.partial_context.digest
                ),
                "rejected": (
                    None if self.rejected is None else _rejected_payload(self.rejected)
                ),
                "stage": self.stage.value,
                "version": "adr0323-closed-finite-block-greedy-failure-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class GreedyDevelopmentCampaignResult:
    pool_sha256: str
    qualification_result_sha256: str
    panel_sha256: str
    exhaustive_teacher_result_sha256: str
    schedule_sha256: str
    greedy_source_sha256: str
    contexts: tuple[GreedyContextResult, ...]
    width_gates: tuple[GreedyWidthGateResult, ...]
    selected_raise_width: RaiseActionWidth | None
    stop_reason: GreedyStopReason
    failure: GreedyFailure | None = None

    def __post_init__(self) -> None:
        from .fresh_action_width_greedy_seal import (
            ADR0329_GREEDY_SCHEDULE_SHA256,
            ADR0329_GREEDY_SOURCE_MANIFEST,
        )
        from .fresh_action_width_structures_seal import (
            ADR0323_DEVELOPMENT_POOL_SHA256,
        )

        for label, value in (
            ("greedy result pool", self.pool_sha256),
            ("greedy result qualification", self.qualification_result_sha256),
            ("greedy result panel", self.panel_sha256),
            ("greedy result teacher", self.exhaustive_teacher_result_sha256),
            ("greedy result schedule", self.schedule_sha256),
            ("greedy result source", self.greedy_source_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.pool_sha256 != ADR0323_DEVELOPMENT_POOL_SHA256
            or self.qualification_result_sha256
            != ADR0323_QUALIFICATION_RESULT_SHA256
            or self.panel_sha256 != ADR0323_QUALIFIED_PANEL_SHA256
            or self.exhaustive_teacher_result_sha256
            != ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
            or self.schedule_sha256 != ADR0329_GREEDY_SCHEDULE_SHA256
            or self.greedy_source_sha256
            != ADR0329_GREEDY_SOURCE_MANIFEST["fresh_action_width_greedy.py"]
        ):
            raise ValueError("greedy result belongs to another evidence chain")
        if not isinstance(self.contexts, tuple) or any(
            not isinstance(value, GreedyContextResult) for value in self.contexts
        ):
            raise TypeError("greedy result contexts must be semantic")
        if tuple(value.panel_position for value in self.contexts) != tuple(
            range(len(self.contexts))
        ):
            raise ValueError("greedy result contexts are not a contiguous prefix")
        if any(
            context.pool_index != ADR0323_QUALIFIED_POOL_INDICES[context.panel_position]
            or context.context_semantic_digest
            != ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS[
                context.panel_position
            ]
            for context in self.contexts
        ):
            raise ValueError("greedy result contexts differ from the sealed panel")
        if not isinstance(self.stop_reason, GreedyStopReason):
            raise TypeError("greedy result stop reason must be semantic")
        completed = self.stop_reason in (
            GreedyStopReason.COMPLETED_SELECTED,
            GreedyStopReason.COMPLETED_NO_WIDTH,
        )
        if completed:
            if (
                len(self.contexts) != 16
                or tuple(value.raise_width.count for value in self.width_gates)
                != (3, 4, 5, 6)
                or self.failure is not None
            ):
                raise ValueError("completed greedy result has the wrong evidence")
            expected_gates = tuple(
                build_greedy_width_gate_result(
                    raise_width=width,
                    contexts=self.contexts,
                )
                for width in ADR0323_RAISE_WIDTHS[1:]
            )
            if self.width_gates != expected_gates:
                raise ValueError("greedy result gates differ from retained contexts")
            passing = tuple(value for value in self.width_gates if value.passes)
            expected_selection = None if not passing else passing[0].raise_width
            if self.selected_raise_width != expected_selection:
                raise ValueError("greedy selected width differs from the frozen gates")
            expected_reason = (
                GreedyStopReason.COMPLETED_NO_WIDTH
                if expected_selection is None
                else GreedyStopReason.COMPLETED_SELECTED
            )
            if self.stop_reason is not expected_reason:
                raise ValueError("greedy completed stop reason differs from selection")
            if self.public_highs_ds_invocation_count != (
                ADR0323_GREEDY_EXECUTED_CALL_COUNT
            ):
                raise ValueError("completed greedy result has the wrong call count")
        else:
            if self.width_gates or self.selected_raise_width is not None:
                raise ValueError("rejected greedy result cannot publish width gates")
            if not isinstance(self.failure, GreedyFailure):
                raise TypeError("rejected greedy result must retain its failure")
            expected_reason = (
                GreedyStopReason.CONSUMER_REJECTED
                if self.failure.kind is GreedyFailureKind.CONSUMER_REJECTION
                else GreedyStopReason.NUMERICAL_REJECTED
            )
            if self.stop_reason is not expected_reason:
                raise ValueError("greedy stop reason differs from failure kind")
            if self.failure.stage is GreedyFailureStage.CAMPAIGN_REDUCTION:
                if len(self.contexts) != 16:
                    raise ValueError("campaign reduction lacks the complete panel")
            elif (
                self.failure.partial_context is None
                or self.failure.partial_context.panel_position != len(self.contexts)
                or self.failure.current_task.panel_position != len(self.contexts)
            ):
                raise ValueError("greedy failure does not follow completed contexts")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        return sum(
            value.public_highs_ds_invocation_count for value in self.contexts
        ) + (0 if self.failure is None else self.failure.public_highs_ds_invocation_count)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_sha256": tuple(value.digest for value in self.contexts),
                "exhaustive_teacher_result_sha256": (
                    self.exhaustive_teacher_result_sha256
                ),
                "failure_sha256": None if self.failure is None else self.failure.digest,
                "greedy_source_sha256": self.greedy_source_sha256,
                "panel_sha256": self.panel_sha256,
                "pool_sha256": self.pool_sha256,
                "qualification_result_sha256": self.qualification_result_sha256,
                "schedule_sha256": self.schedule_sha256,
                "selected_raise_width": (
                    None
                    if self.selected_raise_width is None
                    else self.selected_raise_width.count
                ),
                "stop_reason": self.stop_reason.value,
                "width_gate_sha256": tuple(value.digest for value in self.width_gates),
                "version": "adr0323-closed-finite-block-greedy-campaign-v1",
            }
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_greedy_result_bytes(self)


class GreedyRunnerStage(StrEnum):
    SOURCE_PREFLIGHT = "source_preflight"
    EXECUTION = "execution"


@dataclass(frozen=True, slots=True)
class GreedyRunnerRejected:
    stage: GreedyRunnerStage
    reason: str
    pool_sha256: str | None
    qualification_result_sha256: str | None
    panel_sha256: str | None
    exhaustive_teacher_result_sha256: str | None
    schedule_sha256: str | None
    greedy_source_sha256: str | None
    completed_contexts: tuple[GreedyContextResult, ...]
    current_task: GreedySubsetTask | None
    current_transition: ClosedFiniteBlockTransition | None
    known_public_highs_ds_invocation_count: int
    invocation_count_complete: bool
    exception_chain: tuple[GreedyRunnerException, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.stage, GreedyRunnerStage):
            raise TypeError("greedy runner stage must be semantic")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("greedy runner rejection reason must be nonempty")
        if not isinstance(self.completed_contexts, tuple) or any(
            not isinstance(value, GreedyContextResult)
            for value in self.completed_contexts
        ):
            raise TypeError("greedy runner completed contexts must be semantic")
        if tuple(value.panel_position for value in self.completed_contexts) != tuple(
            range(len(self.completed_contexts))
        ):
            raise ValueError("greedy runner contexts are not a prefix")
        _require_nonnegative_int(
            self.known_public_highs_ds_invocation_count,
            label="known greedy public-call count",
        )
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("greedy invocation completeness must be boolean")
        if not isinstance(self.exception_chain, tuple) or not self.exception_chain:
            raise TypeError("greedy runner rejection requires an exception chain")
        identities = (
            self.pool_sha256,
            self.qualification_result_sha256,
            self.panel_sha256,
            self.exhaustive_teacher_result_sha256,
            self.schedule_sha256,
            self.greedy_source_sha256,
        )
        if self.stage is GreedyRunnerStage.SOURCE_PREFLIGHT:
            if (
                any(value is not None for value in identities)
                or self.completed_contexts
                or self.current_task is not None
                or self.current_transition is not None
                or self.known_public_highs_ds_invocation_count != 0
                or not self.invocation_count_complete
            ):
                raise ValueError("greedy preflight rejection has execution evidence")
        else:
            from .fresh_action_width_greedy_seal import (
                ADR0329_GREEDY_SCHEDULE_SHA256,
                ADR0329_GREEDY_SOURCE_MANIFEST,
            )
            from .fresh_action_width_structures_seal import (
                ADR0323_DEVELOPMENT_POOL_SHA256,
            )

            for label, value in zip(
                (
                    "greedy runner pool",
                    "greedy runner qualification",
                    "greedy runner panel",
                    "greedy runner teacher",
                    "greedy runner schedule",
                    "greedy runner source",
                ),
                identities,
                strict=True,
            ):
                _require_digest(value, label=label)
            if (
                self.pool_sha256 != ADR0323_DEVELOPMENT_POOL_SHA256
                or self.qualification_result_sha256
                != ADR0323_QUALIFICATION_RESULT_SHA256
                or self.panel_sha256 != ADR0323_QUALIFIED_PANEL_SHA256
                or self.exhaustive_teacher_result_sha256
                != ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
                or self.schedule_sha256 != ADR0329_GREEDY_SCHEDULE_SHA256
                or self.greedy_source_sha256
                != ADR0329_GREEDY_SOURCE_MANIFEST[
                    "fresh_action_width_greedy.py"
                ]
            ):
                raise ValueError("greedy execution rejection belongs to another seal")
            if not isinstance(self.current_task, GreedySubsetTask):
                raise TypeError("greedy execution rejection requires current task")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "completed_context_sha256": tuple(
                    value.digest for value in self.completed_contexts
                ),
                "current_task_sha256": (
                    None if self.current_task is None else self.current_task.digest
                ),
                "current_transition_sha256": (
                    None
                    if self.current_transition is None
                    else self.current_transition.digest
                ),
                "exception_chain": tuple(
                    (value.module, value.type_name, value.message)
                    for value in self.exception_chain
                ),
                "exhaustive_teacher_result_sha256": (
                    self.exhaustive_teacher_result_sha256
                ),
                "greedy_source_sha256": self.greedy_source_sha256,
                "invocation_count_complete": self.invocation_count_complete,
                "known_public_call_count": (
                    self.known_public_highs_ds_invocation_count
                ),
                "panel_sha256": self.panel_sha256,
                "pool_sha256": self.pool_sha256,
                "qualification_result_sha256": self.qualification_result_sha256,
                "reason": self.reason,
                "schedule_sha256": self.schedule_sha256,
                "stage": self.stage.value,
                "version": "adr0323-closed-finite-block-greedy-runner-rejection-v1",
            }
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_greedy_result_bytes(self)


GreedyDevelopmentResult = GreedyDevelopmentCampaignResult | GreedyRunnerRejected


def closed_finite_block_greedy_protocol_sha256() -> str:
    """Bind every prospective greedy rule independently of source bytes."""

    return _canonical_sha256(
        {
            "adaptive_graph": "all-anchored-parent-plus-one-raise-transitions",
            "aggregate_recovery": (
                "sum-achieved-endpoints/sum-available-endpoints-before-division"
            ),
            "arm_count": ADR0323_GREEDY_ARM_COUNT,
            "arm_counts_by_width": ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH,
            "artifact_retention": (
                "reserve-no-clobber-staging-before-run+canonical-json+byte-postcheck"
            ),
            "candidate_order": "omitted-kernel-raise-to-total-ascending",
            "consumer": "certified-reduced-sizing-v2-one-public-highs-ds-call",
            "consumer_failure": "stop-no-retry-no-fallback-no-skip",
            "executed_call_count": ADR0323_GREEDY_EXECUTED_CALL_COUNT,
            "executed_candidate_counts_by_target_width": (
                ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH
            ),
            "exhaustive_teacher_result_sha256": (
                ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
            ),
            "finite_block_price": "[L_aug-U_inc,U_aug-L_inc]",
            "maximum_normalized_full_regret_limit": (
                ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value
            ),
            "maximum_normalized_teacher_excess_limit": (
                ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT.value
            ),
            "mean_normalized_full_regret_limit": (
                ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value
            ),
            "mean_normalized_teacher_excess_limit": (
                ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT.value
            ),
            "minimum_aggregate_recovery_floor": (
                ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR.value
            ),
            "normalizer": "pot+2*effective_stack",
            "panel_context_sha256": ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
            "panel_pool_indices": ADR0323_QUALIFIED_POOL_INDICES,
            "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
            "phase_order": tuple(
                value.value for value in ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER
            ),
            "qualification_result_sha256": ADR0323_QUALIFICATION_RESULT_SHA256,
            "response_closure": (
                "every-admitted-raise-x-every-h4-responder-type-x-fold-and-call"
            ),
            "response_model": (
                ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY.value
            ),
            "selection": (
                "greatest-feasible-behavioral-lower-bound-then-smallest-raise-to"
            ),
            "selected_width": "smallest-width-three-through-six-passing-all-five-gates",
            "teacher_excess": "[L_teacher-U_greedy,U_teacher-L_greedy]",
            "transition_count": ADR0323_GREEDY_TRANSITION_COUNT,
            "transition_counts_by_target_width": (
                ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH
            ),
            "version": "adr0323-closed-finite-block-greedy-protocol-v1",
        }
    )


def verify_adr0329_greedy_source_and_dependencies() -> str:
    """Verify the complete greedy source closure before any consumer call."""

    from .fresh_action_width_greedy_seal import (
        ADR0329_GREEDY_ARM_COUNT,
        ADR0329_GREEDY_EXECUTED_CALL_COUNT,
        ADR0329_GREEDY_PROTOCOL_SHA256,
        ADR0329_GREEDY_SOURCE_MANIFEST,
        ADR0329_GREEDY_TRANSITION_COUNT,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0329_GREEDY_SOURCE_MANIFEST
    }
    if actual != ADR0329_GREEDY_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0329 greedy source closure drifted")
    if (
        closed_finite_block_greedy_protocol_sha256()
        != ADR0329_GREEDY_PROTOCOL_SHA256
        or ADR0329_GREEDY_ARM_COUNT != ADR0323_GREEDY_ARM_COUNT
        or ADR0329_GREEDY_TRANSITION_COUNT != ADR0323_GREEDY_TRANSITION_COUNT
        or ADR0329_GREEDY_EXECUTED_CALL_COUNT != ADR0323_GREEDY_EXECUTED_CALL_COUNT
    ):
        raise RuntimeError("ADR-0329 greedy protocol drifted")
    return actual["fresh_action_width_greedy.py"]


def verify_adr0329_greedy_schedule(
    schedule: ClosedFiniteBlockGreedySchedule,
) -> None:
    from .fresh_action_width_greedy_seal import ADR0329_GREEDY_SCHEDULE_SHA256

    if not isinstance(schedule, ClosedFiniteBlockGreedySchedule):
        raise TypeError("greedy schedule verification requires a semantic schedule")
    if schedule.digest != ADR0329_GREEDY_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0329 greedy schedule drifted")


def _partial_context(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    pool_index: int,
    initial_task: GreedySubsetTask,
    initial: GreedyCertifiedValueEvidence | None,
    completed_rounds: list[GreedyRoundResult],
    incomplete_candidates: list[ClosedFiniteBlockCandidateEvidence],
) -> GreedyPartialContextEvidence:
    return GreedyPartialContextEvidence(
        panel_position=panel_position,
        pool_index=pool_index,
        context_semantic_digest=context.semantic_digest,
        payoff_span_chips=context.payoff_span_chips,
        initial_task=initial_task,
        initial=initial,
        completed_rounds=tuple(completed_rounds),
        incomplete_candidates=tuple(incomplete_candidates),
    )


def _campaign_result(
    *,
    schedule: ClosedFiniteBlockGreedySchedule,
    greedy_source_sha256: str,
    contexts: list[GreedyContextResult],
    stop_reason: GreedyStopReason,
    width_gates: tuple[GreedyWidthGateResult, ...] = (),
    selected_raise_width: RaiseActionWidth | None = None,
    failure: GreedyFailure | None = None,
) -> GreedyDevelopmentCampaignResult:
    return GreedyDevelopmentCampaignResult(
        pool_sha256=schedule.pool_sha256,
        qualification_result_sha256=schedule.qualification_result_sha256,
        panel_sha256=schedule.panel_sha256,
        exhaustive_teacher_result_sha256=(
            schedule.exhaustive_teacher_result_sha256
        ),
        schedule_sha256=schedule.digest,
        greedy_source_sha256=greedy_source_sha256,
        contexts=tuple(contexts),
        width_gates=width_gates,
        selected_raise_width=selected_raise_width,
        stop_reason=stop_reason,
        failure=failure,
    )


def run_adr0323_closed_finite_block_greedy_development(
) -> GreedyDevelopmentResult:
    """Run the sealed development graph once; never retry a rejected arm."""

    try:
        source_sha256 = verify_adr0329_greedy_source_and_dependencies()
        schedule = build_adr0323_closed_finite_block_greedy_schedule()
        verify_adr0329_greedy_schedule(schedule)
        teacher_result = verify_adr0323_exhaustive_teacher_result_artifact()
        if teacher_result.campaign_result_sha256 != (
            schedule.exhaustive_teacher_result_sha256
        ):
            raise RuntimeError("greedy preflight rebound another teacher result")
        pool = verify_adr0324_structure_source_and_pool()
    except Exception as error:
        return GreedyRunnerRejected(
            stage=GreedyRunnerStage.SOURCE_PREFLIGHT,
            reason="greedy source, schedule, or teacher preflight failed",
            pool_sha256=None,
            qualification_result_sha256=None,
            panel_sha256=None,
            exhaustive_teacher_result_sha256=None,
            schedule_sha256=None,
            greedy_source_sha256=None,
            completed_contexts=(),
            current_task=None,
            current_transition=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=_exception_chain(error),
        )
    return _execute_adr0323_closed_finite_block_greedy_development(
        greedy_source_sha256=source_sha256,
        pool=pool,
        schedule=schedule,
        teacher_result=teacher_result,
    )


def _execute_adr0323_closed_finite_block_greedy_development(
    *,
    greedy_source_sha256: str,
    pool: FreshActionWidthDevelopmentPool,
    schedule: ClosedFiniteBlockGreedySchedule,
    teacher_result: RetainedExhaustiveTeacherResult,
) -> GreedyDevelopmentResult:
    contexts: list[GreedyContextResult] = []
    completed_rounds: list[GreedyRoundResult] = []
    incomplete_candidates: list[ClosedFiniteBlockCandidateEvidence] = []
    current_task = schedule.tasks[0]
    current_transition: ClosedFiniteBlockTransition | None = None
    known_calls = 0
    try:
        if not isinstance(pool, FreshActionWidthDevelopmentPool):
            raise TypeError("greedy execution requires the sealed development pool")
        for panel_position, pool_index in enumerate(ADR0323_QUALIFIED_POOL_INDICES):
            context = pool.contexts[pool_index]
            teacher_context = teacher_result.contexts[panel_position]
            initial_task = schedule.initial_task(panel_position)
            current_task = initial_task
            current_transition = None
            completed_rounds = []
            incomplete_candidates = []

            initial_result = consume_certified_reduced_sizing_v2(initial_task.request)
            if isinstance(
                initial_result,
                (CertifiedReducedSizingAcceptedV2, CertifiedReducedSizingRejectedV2),
            ):
                known_calls += initial_result.public_highs_ds_invocation_count
            if isinstance(initial_result, CertifiedReducedSizingRejectedV2):
                partial = _partial_context(
                    context=context,
                    panel_position=panel_position,
                    pool_index=pool_index,
                    initial_task=initial_task,
                    initial=None,
                    completed_rounds=[],
                    incomplete_candidates=[],
                )
                return _campaign_result(
                    schedule=schedule,
                    greedy_source_sha256=greedy_source_sha256,
                    contexts=contexts,
                    stop_reason=GreedyStopReason.CONSUMER_REJECTED,
                    failure=GreedyFailure(
                        kind=GreedyFailureKind.CONSUMER_REJECTION,
                        stage=GreedyFailureStage.INITIAL_ARM,
                        current_task=initial_task,
                        current_transition=None,
                        partial_context=partial,
                        rejected=initial_result,
                    ),
                )
            if not isinstance(initial_result, CertifiedReducedSizingAcceptedV2):
                raise TypeError("greedy initial arm returned a nonsemantic result")
            initial = _value_evidence_from_accepted(
                task=initial_task,
                accepted=initial_result,
            )
            incumbent_task = initial_task
            incumbent = initial

            for target_width in ADR0323_RAISE_WIDTHS[1:]:
                outgoing = schedule.outgoing(incumbent_task)
                incomplete_candidates = []
                for transition in outgoing:
                    current_transition = transition
                    current_task = transition.augmented
                    candidate_result = consume_certified_reduced_sizing_v2(
                        current_task.request
                    )
                    if isinstance(
                        candidate_result,
                        (
                            CertifiedReducedSizingAcceptedV2,
                            CertifiedReducedSizingRejectedV2,
                        ),
                    ):
                        known_calls += candidate_result.public_highs_ds_invocation_count
                    if isinstance(candidate_result, CertifiedReducedSizingRejectedV2):
                        partial = _partial_context(
                            context=context,
                            panel_position=panel_position,
                            pool_index=pool_index,
                            initial_task=initial_task,
                            initial=initial,
                            completed_rounds=completed_rounds,
                            incomplete_candidates=incomplete_candidates,
                        )
                        return _campaign_result(
                            schedule=schedule,
                            greedy_source_sha256=greedy_source_sha256,
                            contexts=contexts,
                            stop_reason=GreedyStopReason.CONSUMER_REJECTED,
                            failure=GreedyFailure(
                                kind=GreedyFailureKind.CONSUMER_REJECTION,
                                stage=GreedyFailureStage.CANDIDATE_ARM,
                                current_task=current_task,
                                current_transition=transition,
                                partial_context=partial,
                                rejected=candidate_result,
                            ),
                        )
                    if not isinstance(
                        candidate_result,
                        CertifiedReducedSizingAcceptedV2,
                    ):
                        raise TypeError("greedy candidate arm returned a nonsemantic result")
                    accepted = _value_evidence_from_accepted(
                        task=current_task,
                        accepted=candidate_result,
                    )
                    try:
                        candidate = build_closed_finite_block_candidate(
                            transition=transition,
                            incumbent=incumbent,
                            augmented=accepted,
                        )
                    except (ArithmeticError, ValueError) as error:
                        partial = _partial_context(
                            context=context,
                            panel_position=panel_position,
                            pool_index=pool_index,
                            initial_task=initial_task,
                            initial=initial,
                            completed_rounds=completed_rounds,
                            incomplete_candidates=incomplete_candidates,
                        )
                        return _campaign_result(
                            schedule=schedule,
                            greedy_source_sha256=greedy_source_sha256,
                            contexts=contexts,
                            stop_reason=GreedyStopReason.NUMERICAL_REJECTED,
                            failure=GreedyFailure(
                                kind=GreedyFailureKind.NUMERICAL_REJECTION,
                                stage=GreedyFailureStage.CANDIDATE_PRICE,
                                current_task=current_task,
                                current_transition=transition,
                                partial_context=partial,
                                accepted_at_failure=accepted,
                                exception_chain=_exception_chain(error),
                            ),
                        )
                    incomplete_candidates.append(candidate)

                try:
                    round_result = build_greedy_round_result(
                        target_raise_width=target_width,
                        incumbent_task=incumbent_task,
                        incumbent=incumbent,
                        candidates=tuple(incomplete_candidates),
                        teacher_result=teacher_result,
                        teacher_context=teacher_context,
                    )
                except (ArithmeticError, ValueError) as error:
                    partial = _partial_context(
                        context=context,
                        panel_position=panel_position,
                        pool_index=pool_index,
                        initial_task=initial_task,
                        initial=initial,
                        completed_rounds=completed_rounds,
                        incomplete_candidates=incomplete_candidates,
                    )
                    return _campaign_result(
                        schedule=schedule,
                        greedy_source_sha256=greedy_source_sha256,
                        contexts=contexts,
                        stop_reason=GreedyStopReason.NUMERICAL_REJECTED,
                        failure=GreedyFailure(
                            kind=GreedyFailureKind.NUMERICAL_REJECTION,
                            stage=GreedyFailureStage.ROUND_REDUCTION,
                            current_task=current_task,
                            current_transition=current_transition,
                            partial_context=partial,
                            exception_chain=_exception_chain(error),
                        ),
                    )
                completed_rounds.append(round_result)
                incumbent_task = round_result.selected.transition.augmented
                incumbent = round_result.selected.augmented
                incomplete_candidates = []

            contexts.append(
                GreedyContextResult(
                    panel_position=panel_position,
                    pool_index=pool_index,
                    context_semantic_digest=context.semantic_digest,
                    payoff_span_chips=context.payoff_span_chips,
                    initial_task=initial_task,
                    initial=initial,
                    rounds=tuple(completed_rounds),
                )
            )

        try:
            width_gates = tuple(
                build_greedy_width_gate_result(
                    raise_width=width,
                    contexts=tuple(contexts),
                )
                for width in ADR0323_RAISE_WIDTHS[1:]
            )
        except (ArithmeticError, ValueError) as error:
            return _campaign_result(
                schedule=schedule,
                greedy_source_sha256=greedy_source_sha256,
                contexts=contexts,
                stop_reason=GreedyStopReason.NUMERICAL_REJECTED,
                failure=GreedyFailure(
                    kind=GreedyFailureKind.NUMERICAL_REJECTION,
                    stage=GreedyFailureStage.CAMPAIGN_REDUCTION,
                    current_task=current_task,
                    current_transition=None,
                    partial_context=None,
                    exception_chain=_exception_chain(error),
                ),
            )
        selected = next(
            (value.raise_width for value in width_gates if value.passes),
            None,
        )
        return _campaign_result(
            schedule=schedule,
            greedy_source_sha256=greedy_source_sha256,
            contexts=contexts,
            width_gates=width_gates,
            selected_raise_width=selected,
            stop_reason=(
                GreedyStopReason.COMPLETED_NO_WIDTH
                if selected is None
                else GreedyStopReason.COMPLETED_SELECTED
            ),
        )
    except Exception as error:
        return GreedyRunnerRejected(
            stage=GreedyRunnerStage.EXECUTION,
            reason="greedy runner failed outside a typed campaign stop",
            pool_sha256=schedule.pool_sha256,
            qualification_result_sha256=schedule.qualification_result_sha256,
            panel_sha256=schedule.panel_sha256,
            exhaustive_teacher_result_sha256=(
                schedule.exhaustive_teacher_result_sha256
            ),
            schedule_sha256=schedule.digest,
            greedy_source_sha256=greedy_source_sha256,
            completed_contexts=tuple(contexts),
            current_task=current_task,
            current_transition=current_transition,
            known_public_highs_ds_invocation_count=known_calls,
            invocation_count_complete=False,
            exception_chain=_exception_chain(error),
        )


def _task_payload(task: GreedySubsetTask) -> dict[str, object]:
    return {
        "context_semantic_digest": task.context_semantic_digest,
        "legal_raise_set_sha256": task.legal_raise_set_sha256,
        "linear_program_sha256": task.linear_program_sha256,
        "ordinal": task.ordinal,
        "panel_position": task.panel_position,
        "pool_index": task.pool_index,
        "raise_to_totals": task.raise_to_totals,
        "raise_width": task.raise_width.count,
        "request_sha256": task.request_sha256,
        "response_row_set_sha256": task.response_row_set.digest,
        "subset_index": task.subset_index,
        "task_sha256": task.digest,
    }


def _transition_payload(
    transition: ClosedFiniteBlockTransition,
) -> dict[str, object]:
    return {
        "augmented_task": _task_payload(transition.augmented),
        "candidate_position": transition.candidate_position,
        "incumbent_task": _task_payload(transition.incumbent),
        "ordinal": transition.ordinal,
        "own_block_sha256": transition.own_block.digest,
        "phase_order": tuple(value.value for value in transition.phase_order),
        "proposed_raise_to_total": transition.proposed_raise_to_total.chips,
        "proposed_reduced_bet_increment": (
            transition.proposed_reduced_bet_increment.chips
        ),
        "transition_sha256": transition.digest,
    }


def _finite_block_price_payload(
    price: CertifiedFiniteBlockPriceInterval,
) -> dict[str, str]:
    return {
        "nonnegative_lower_hex": price.nonnegative_lower_chips.hex(),
        "nonnegative_upper_hex": price.nonnegative_upper_chips.hex(),
        "signed_lower_hex": price.signed_lower_chips.hex(),
        "signed_upper_hex": price.signed_upper_chips.hex(),
    }


def _regret_payload(regret: CertifiedChipRegretInterval) -> dict[str, str]:
    return {
        "nonnegative_lower_hex": regret.nonnegative_lower_chips.hex(),
        "nonnegative_upper_hex": regret.nonnegative_upper_chips.hex(),
        "signed_lower_hex": regret.signed_lower_chips.hex(),
        "signed_upper_hex": regret.signed_upper_chips.hex(),
    }


def _teacher_excess_payload(
    excess: CertifiedGreedyTeacherExcessInterval,
) -> dict[str, str]:
    return {
        "nonnegative_lower_hex": excess.nonnegative_lower_chips.hex(),
        "nonnegative_upper_hex": excess.nonnegative_upper_chips.hex(),
        "signed_lower_hex": excess.signed_lower_chips.hex(),
        "signed_upper_hex": excess.signed_upper_chips.hex(),
    }


def _normalized_regret_payload(
    value: NormalizedTeacherRegretInterval,
) -> dict[str, str]:
    return {"lower_hex": value.lower.hex(), "upper_hex": value.upper.hex()}


def _normalized_excess_payload(
    value: NormalizedGreedyTeacherExcessInterval,
) -> dict[str, str]:
    return {"lower_hex": value.lower.hex(), "upper_hex": value.upper.hex()}


def _teacher_reference_payload(
    reference: ExhaustiveTeacherWidthReference,
) -> dict[str, object]:
    return {
        "context_result_sha256": reference.context_result_sha256,
        "context_semantic_digest": reference.context_semantic_digest,
        "exhaustive_teacher_result_sha256": (
            reference.exhaustive_teacher_result_sha256
        ),
        "full_value": {
            "lower_hex": reference.full_value.lower_chips.hex(),
            "upper_hex": reference.full_value.upper_chips.hex(),
        },
        "panel_position": reference.panel_position,
        "payoff_span_chips": reference.payoff_span_chips,
        "pool_index": reference.pool_index,
        "raise_width": reference.raise_width.count,
        "selected_legal_raise_set_sha256": (
            reference.selected_legal_raise_set_sha256
        ),
        "selected_linear_program_sha256": (
            reference.selected_linear_program_sha256
        ),
        "selected_raise_to_totals": reference.selected_raise_to_totals,
        "selected_request_sha256": reference.selected_request_sha256,
        "selected_subset_index": reference.selected_subset_index,
        "teacher_value": {
            "lower_hex": reference.teacher_value.lower_chips.hex(),
            "upper_hex": reference.teacher_value.upper_chips.hex(),
        },
        "width_result_sha256": reference.width_result_sha256,
    }


def _candidate_payload(
    candidate: ClosedFiniteBlockCandidateEvidence,
) -> dict[str, object]:
    return {
        "augmented": _value_evidence_payload(candidate.augmented),
        "candidate_sha256": candidate.digest,
        "incumbent_value_sha256": candidate.incumbent_value_sha256,
        "price": _finite_block_price_payload(candidate.price),
        "transition": _transition_payload(candidate.transition),
    }


def _round_payload(result: GreedyRoundResult) -> dict[str, object]:
    return {
        "candidates": tuple(_candidate_payload(value) for value in result.candidates),
        "full_regret": _regret_payload(result.full_regret),
        "incumbent": _value_evidence_payload(result.incumbent),
        "incumbent_task": _task_payload(result.incumbent_task),
        "normalized_full_regret": _normalized_regret_payload(
            result.normalized_full_regret
        ),
        "normalized_teacher_excess": _normalized_excess_payload(
            result.normalized_teacher_excess
        ),
        "round_sha256": result.digest,
        "selected_candidate_position": result.selected_candidate_position,
        "target_raise_width": result.target_raise_width.count,
        "teacher_excess": _teacher_excess_payload(result.teacher_excess),
        "teacher_reference": _teacher_reference_payload(result.teacher_reference),
    }


def _context_payload(context: GreedyContextResult) -> dict[str, object]:
    return {
        "context_result_sha256": context.digest,
        "context_semantic_digest": context.context_semantic_digest,
        "initial": _value_evidence_payload(context.initial),
        "initial_task": _task_payload(context.initial_task),
        "panel_position": context.panel_position,
        "payoff_span_chips": context.payoff_span_chips,
        "pool_index": context.pool_index,
        "rounds": tuple(_round_payload(value) for value in context.rounds),
    }


def _recovery_payload(
    recovery: ConservativeAggregateRecoveryInterval,
) -> dict[str, str]:
    return {
        "achieved_gain_lower_chips_hex": (
            recovery.achieved_gain_lower_chips.hex()
        ),
        "achieved_gain_upper_chips_hex": (
            recovery.achieved_gain_upper_chips.hex()
        ),
        "available_gain_lower_chips_hex": (
            recovery.available_gain_lower_chips.hex()
        ),
        "available_gain_upper_chips_hex": (
            recovery.available_gain_upper_chips.hex()
        ),
        "lower_hex": recovery.lower.hex(),
        "upper_hex": recovery.upper.hex(),
    }


def _width_gate_payload(result: GreedyWidthGateResult) -> dict[str, object]:
    return {
        "aggregate_recovery": _recovery_payload(result.aggregate_recovery),
        "aggregate_recovery_pass": result.aggregate_recovery_pass,
        "maximum_full_regret_pass": result.maximum_full_regret_pass,
        "maximum_normalized_full_regret_upper_hex": (
            result.maximum_normalized_full_regret_upper.hex()
        ),
        "maximum_normalized_teacher_excess_upper_hex": (
            result.maximum_normalized_teacher_excess_upper.hex()
        ),
        "maximum_teacher_excess_pass": result.maximum_teacher_excess_pass,
        "mean_full_regret_pass": result.mean_full_regret_pass,
        "mean_normalized_full_regret_lower_hex": (
            result.mean_normalized_full_regret_lower.hex()
        ),
        "mean_normalized_full_regret_upper_hex": (
            result.mean_normalized_full_regret_upper.hex()
        ),
        "mean_normalized_teacher_excess_lower_hex": (
            result.mean_normalized_teacher_excess_lower.hex()
        ),
        "mean_normalized_teacher_excess_upper_hex": (
            result.mean_normalized_teacher_excess_upper.hex()
        ),
        "mean_teacher_excess_pass": result.mean_teacher_excess_pass,
        "passes": result.passes,
        "raise_width": result.raise_width.count,
        "width_gate_sha256": result.digest,
    }


def _partial_context_payload(
    partial: GreedyPartialContextEvidence,
) -> dict[str, object]:
    return {
        "completed_rounds": tuple(
            _round_payload(value) for value in partial.completed_rounds
        ),
        "context_semantic_digest": partial.context_semantic_digest,
        "incomplete_candidates": tuple(
            _candidate_payload(value) for value in partial.incomplete_candidates
        ),
        "initial": (
            None if partial.initial is None else _value_evidence_payload(partial.initial)
        ),
        "initial_task": _task_payload(partial.initial_task),
        "panel_position": partial.panel_position,
        "partial_context_sha256": partial.digest,
        "payoff_span_chips": partial.payoff_span_chips,
        "pool_index": partial.pool_index,
    }


def _rejected_payload(
    rejected: CertifiedReducedSizingRejectedV2,
) -> dict[str, object]:
    return {
        "consumer_protocol_sha256": rejected.consumer_protocol_sha256,
        "consumer_source_sha256": rejected.consumer_source_sha256,
        "exception_chain": tuple(
            (value.module, value.type_name, value.message)
            for value in rejected.exception_chain
        ),
        "legal_raise_set_sha256": rejected.legal_raise_set_sha256,
        "public_call_count": rejected.public_highs_ds_invocation_count,
        "public_state_sha256": rejected.public_state_sha256,
        "reason": rejected.reason.value,
        "request_sha256": rejected.request_sha256,
        "stage": rejected.stage.value,
    }


def _failure_payload(failure: GreedyFailure) -> dict[str, object]:
    return {
        "accepted_at_failure": (
            None
            if failure.accepted_at_failure is None
            else _value_evidence_payload(failure.accepted_at_failure)
        ),
        "current_task": _task_payload(failure.current_task),
        "current_transition": (
            None
            if failure.current_transition is None
            else _transition_payload(failure.current_transition)
        ),
        "exception_chain": tuple(
            {
                "message": value.message,
                "module": value.module,
                "type_name": value.type_name,
            }
            for value in failure.exception_chain
        ),
        "failure_sha256": failure.digest,
        "kind": failure.kind.value,
        "partial_context": (
            None
            if failure.partial_context is None
            else _partial_context_payload(failure.partial_context)
        ),
        "rejected": (
            None if failure.rejected is None else _rejected_payload(failure.rejected)
        ),
        "stage": failure.stage.value,
    }


def greedy_result_payload(result: GreedyDevelopmentResult) -> dict[str, object]:
    """Return the complete canonical schema for one future owned invocation."""

    if isinstance(result, GreedyDevelopmentCampaignResult):
        return {
            "contexts": tuple(_context_payload(value) for value in result.contexts),
            "digest": result.digest,
            "exhaustive_teacher_result_sha256": (
                result.exhaustive_teacher_result_sha256
            ),
            "failure": None if result.failure is None else _failure_payload(result.failure),
            "greedy_source_sha256": result.greedy_source_sha256,
            "panel_sha256": result.panel_sha256,
            "pool_sha256": result.pool_sha256,
            "public_call_count": result.public_highs_ds_invocation_count,
            "qualification_result_sha256": result.qualification_result_sha256,
            "result_type": "campaign_result",
            "schedule_sha256": result.schedule_sha256,
            "selected_raise_width": (
                None
                if result.selected_raise_width is None
                else result.selected_raise_width.count
            ),
            "stop_reason": result.stop_reason.value,
            "version": "adr0323-closed-finite-block-greedy-artifact-v1",
            "width_gates": tuple(
                _width_gate_payload(value) for value in result.width_gates
            ),
        }
    if not isinstance(result, GreedyRunnerRejected):
        raise TypeError("greedy artifact requires a semantic runner result")
    return {
        "completed_contexts": tuple(
            _context_payload(value) for value in result.completed_contexts
        ),
        "current_task": (
            None if result.current_task is None else _task_payload(result.current_task)
        ),
        "current_transition": (
            None
            if result.current_transition is None
            else _transition_payload(result.current_transition)
        ),
        "digest": result.digest,
        "exception_chain": tuple(
            {
                "message": value.message,
                "module": value.module,
                "type_name": value.type_name,
            }
            for value in result.exception_chain
        ),
        "exhaustive_teacher_result_sha256": (
            result.exhaustive_teacher_result_sha256
        ),
        "greedy_source_sha256": result.greedy_source_sha256,
        "invocation_count_complete": result.invocation_count_complete,
        "known_public_call_count": result.known_public_highs_ds_invocation_count,
        "panel_sha256": result.panel_sha256,
        "pool_sha256": result.pool_sha256,
        "qualification_result_sha256": result.qualification_result_sha256,
        "reason": result.reason,
        "result_type": "runner_rejected",
        "schedule_sha256": result.schedule_sha256,
        "stage": result.stage.value,
        "version": "adr0323-closed-finite-block-greedy-artifact-v1",
    }


def canonical_greedy_result_bytes(result: GreedyDevelopmentResult) -> bytes:
    return (
        json.dumps(
            greedy_result_payload(result),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def retain_greedy_result(
    result: GreedyDevelopmentResult,
    *,
    output_path: Path,
) -> tuple[str, int]:
    """Publish one canonical result without clobbering any prior evidence."""

    if not isinstance(output_path, Path):
        raise TypeError("greedy artifact output path must be a Path")
    temporary = output_path.with_suffix(f"{output_path.suffix}.partial")
    if output_path.exists() or temporary.exists():
        raise FileExistsError("greedy artifact or staging path already exists")
    rendered = canonical_greedy_result_bytes(result)
    try:
        with temporary.open("xb") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output_path)
        if output_path.read_bytes() != rendered:
            raise OSError("persisted greedy artifact differs from canonical bytes")
        temporary.unlink()
    except BaseException:
        raise
    return sha256(rendered).hexdigest(), len(rendered)


def run_and_retain_adr0323_closed_finite_block_greedy_development(
    *,
    output_path: Path,
) -> GreedyDevelopmentResult:
    """Reserve the evidence path before the first future consumer call."""

    if not isinstance(output_path, Path):
        raise TypeError("greedy artifact output path must be a Path")
    temporary = output_path.with_suffix(f"{output_path.suffix}.partial")
    if output_path.exists() or temporary.exists():
        raise FileExistsError("greedy artifact or staging path already exists")
    if not output_path.parent.is_dir():
        raise FileNotFoundError("greedy artifact parent directory does not exist")
    with temporary.open("xb") as stream:
        stream.write(b"adr0323 closed finite-block greedy invocation in progress\n")
        stream.flush()
        os.fsync(stream.fileno())
        result = run_adr0323_closed_finite_block_greedy_development()
        rendered = canonical_greedy_result_bytes(result)
        stream.seek(0)
        stream.truncate()
        stream.write(rendered)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, output_path)
    if output_path.read_bytes() != rendered:
        raise OSError("persisted greedy artifact differs from canonical bytes")
    temporary.unlink()
    return result


__all__ = [
    "ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER",
    "ADR0323_GREEDY_ARM_COUNT",
    "ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH",
    "ADR0323_GREEDY_ARTIFACT_RELATIVE_PATH",
    "ADR0323_GREEDY_EXECUTED_CALL_COUNT",
    "ADR0323_GREEDY_EXECUTED_CANDIDATE_CALL_COUNT",
    "ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH",
    "ADR0323_GREEDY_EXECUTED_INITIAL_CALL_COUNT",
    "ADR0323_GREEDY_TRANSITION_COUNT",
    "ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH",
    "ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT",
    "ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT",
    "ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT",
    "ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT",
    "ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR",
    "CertifiedFiniteBlockPriceInterval",
    "CertifiedGreedyTeacherExcessInterval",
    "ClosedFiniteBlockCandidateEvidence",
    "ClosedFiniteBlockGreedySchedule",
    "ClosedFiniteBlockPhase",
    "ClosedFiniteBlockTransition",
    "ConservativeAggregateRecoveryInterval",
    "ExhaustiveTeacherWidthReference",
    "GreedyCertifiedValueEvidence",
    "GreedyContextResult",
    "GreedyDevelopmentCampaignResult",
    "GreedyDevelopmentResult",
    "GreedyFailure",
    "GreedyFailureKind",
    "GreedyFailureStage",
    "GreedyPartialContextEvidence",
    "GreedyRoundResult",
    "GreedyRunnerException",
    "GreedyRunnerRejected",
    "GreedyRunnerStage",
    "GreedyStopReason",
    "GreedySubsetTask",
    "GreedyWidthGateResult",
    "MaximumNormalizedFullRegretLimit",
    "MaximumNormalizedTeacherExcessLimit",
    "MeanNormalizedFullRegretLimit",
    "MeanNormalizedTeacherExcessLimit",
    "MinimumAggregateRecoveryFloor",
    "NormalizedGreedyTeacherExcessInterval",
    "OpponentResponseAction",
    "OpponentResponseRowIdentity",
    "OpponentResponseRowSetIdentity",
    "OwnRaiseBlockIdentity",
    "build_adr0323_closed_finite_block_greedy_schedule",
    "build_closed_finite_block_candidate",
    "build_greedy_round_result",
    "build_greedy_width_gate_result",
    "canonical_greedy_result_bytes",
    "certified_closed_finite_block_price",
    "certified_greedy_teacher_excess",
    "closed_finite_block_greedy_protocol_sha256",
    "conservative_aggregate_recovery",
    "greedy_result_payload",
    "normalize_full_regret",
    "normalize_greedy_teacher_excess",
    "retain_greedy_result",
    "run_adr0323_closed_finite_block_greedy_development",
    "run_and_retain_adr0323_closed_finite_block_greedy_development",
    "select_greedy_candidate",
    "verify_adr0329_greedy_schedule",
    "verify_adr0329_greedy_source_and_dependencies",
]
