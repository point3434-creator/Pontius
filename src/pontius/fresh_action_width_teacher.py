"""Source-sealed exhaustive teacher for ADR-0323 finite-block research.

The module freezes the exact development-panel task schedule before any
intermediate-width value is opened.  Its public runner owns every consumer
call, conservative regret calculation, set-valued teacher reduction, stop
state, and failure record.  It is research-only and emits no betting action.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from pathlib import Path

from .certified_reduced_sizing_consumer_v2 import (
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    KernelRaiseToTotal,
    LegalRaiseSetScope,
    ReducedSizingResponseModel,
    _bind_request,
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
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
    ADR0323_RAISE_WIDTHS,
    FreshActionWidthContext,
    FreshActionWidthDevelopmentPool,
    RaiseActionWidth,
    anchored_raise_subset_family,
)


ADR0323_EXHAUSTIVE_TEACHER_FULL_TASK_COUNT = 16
ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS = (
    (2, 16),
    (3, 120),
    (4, 408),
    (5, 828),
    (6, 1_107),
)
ADR0323_EXHAUSTIVE_TEACHER_SUBSET_TASK_COUNT = 2_479
ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT = 2_495


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


def _require_positive_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


@dataclass(frozen=True, slots=True)
class TeacherEquivalenceAllowance:
    """Chip allowance for reporting a subset as certainly teacher-equivalent."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="teacher-equivalence allowance")


ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE = TeacherEquivalenceAllowance(1e-8)


@dataclass(frozen=True, slots=True)
class NormalizedTeacherRegretInterval:
    """Dimensionless certified regret interval divided by payoff span."""

    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, float) and isfinite(value)
            for value in (self.lower, self.upper)
        ):
            raise ValueError("normalized teacher-regret endpoints must be finite floats")
        if self.lower < 0.0 or self.lower > self.upper:
            raise ValueError("normalized teacher-regret interval is invalid")


def normalize_teacher_regret(
    regret: CertifiedChipRegretInterval,
    *,
    payoff_span_chips: int,
) -> NormalizedTeacherRegretInterval:
    if not isinstance(regret, CertifiedChipRegretInterval):
        raise TypeError("normalization requires certified chip regret")
    if (
        isinstance(payoff_span_chips, bool)
        or not isinstance(payoff_span_chips, int)
        or payoff_span_chips <= 0
    ):
        raise ValueError("teacher payoff span must be a positive chip count")
    return NormalizedTeacherRegretInterval(
        lower=regret.nonnegative_lower_chips / payoff_span_chips,
        upper=regret.nonnegative_upper_chips / payoff_span_chips,
    )


class ExhaustiveTeacherArm(StrEnum):
    COMPLETE_INTEGER_UNIVERSE = "complete_integer_universe"
    ANCHORED_SUBSET = "anchored_subset"


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherTask:
    ordinal: int
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    arm: ExhaustiveTeacherArm
    raise_width: RaiseActionWidth | None
    subset_index: int | None
    request: CertifiedReducedSizingRequestV2
    request_sha256: str = ""
    legal_raise_set_sha256: str = ""
    linear_program_sha256: str = ""

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.ordinal, label="teacher task ordinal")
        panel_position = _require_nonnegative_int(
            self.panel_position,
            label="teacher task panel position",
        )
        if panel_position >= 16:
            raise ValueError("teacher task panel position exceeds the sealed panel")
        _require_nonnegative_int(self.pool_index, label="teacher task pool index")
        _require_digest(self.context_semantic_digest, label="teacher task context")
        if not isinstance(self.arm, ExhaustiveTeacherArm):
            raise TypeError("teacher task arm must be semantic")
        if not isinstance(self.request, CertifiedReducedSizingRequestV2):
            raise TypeError("teacher task requires an exact consumer request")
        if self.arm is ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE:
            if self.raise_width is not None or self.subset_index is not None:
                raise ValueError("complete teacher task cannot name a subset")
            if (
                self.request.legal_raise_scope
                is not LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE
            ):
                raise ValueError("complete teacher task has restricted scope")
        else:
            if not isinstance(self.raise_width, RaiseActionWidth):
                raise TypeError("subset teacher task requires a raise-action width")
            subset_index = _require_nonnegative_int(
                self.subset_index,
                label="teacher subset index",
            )
            if subset_index != self.subset_index:
                raise AssertionError("teacher subset index normalization drifted")
            if (
                self.request.legal_raise_scope
                is not LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET
                or len(self.request.legal_raise_to_totals) != self.raise_width.count
            ):
                raise ValueError("subset teacher task has the wrong scope or width")
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
            raise ValueError("teacher task identities differ from its exact request")

    @property
    def raise_to_totals(self) -> tuple[int, ...]:
        return tuple(value.chips for value in self.request.legal_raise_to_totals)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "arm": self.arm.value,
                "context_semantic_digest": self.context_semantic_digest,
                "legal_raise_set_sha256": self.legal_raise_set_sha256,
                "linear_program_sha256": self.linear_program_sha256,
                "ordinal": self.ordinal,
                "panel_position": self.panel_position,
                "pool_index": self.pool_index,
                "raise_to_totals": self.raise_to_totals,
                "raise_width": None if self.raise_width is None else self.raise_width.count,
                "request_sha256": self.request_sha256,
                "subset_index": self.subset_index,
                "version": "adr0323-exhaustive-teacher-task-v1",
            }
        )


def _teacher_request(
    *,
    context: FreshActionWidthContext,
    amounts: tuple[KernelRaiseToTotal, ...],
    scope: LegalRaiseSetScope,
    label: str,
) -> CertifiedReducedSizingRequestV2:
    return CertifiedReducedSizingRequestV2(
        context_id=label,
        betting=context.betting,
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=scope,
        legal_raise_to_totals=amounts,
        joint_probabilities=context.joint_probabilities,
        showdown_signs=context.showdown_signs,
    )


def exhaustive_teacher_tasks_for_context(
    *,
    context: FreshActionWidthContext,
    panel_position: int,
    pool_index: int,
    start_ordinal: int,
) -> tuple[ExhaustiveTeacherTask, ...]:
    if not isinstance(context, FreshActionWidthContext):
        raise TypeError("teacher task construction requires a fresh context")
    _require_nonnegative_int(panel_position, label="teacher panel position")
    _require_nonnegative_int(pool_index, label="teacher pool index")
    _require_nonnegative_int(start_ordinal, label="teacher start ordinal")
    tasks: list[ExhaustiveTeacherTask] = []
    tasks.append(
        ExhaustiveTeacherTask(
            ordinal=start_ordinal,
            panel_position=panel_position,
            pool_index=pool_index,
            context_semantic_digest=context.semantic_digest,
            arm=ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE,
            raise_width=None,
            subset_index=None,
            request=_teacher_request(
                context=context,
                amounts=context.complete_raise_to_totals,
                scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
                label=f"{context.context_id}|exhaustive-teacher|full",
            ),
        )
    )
    for width in ADR0323_RAISE_WIDTHS:
        family = anchored_raise_subset_family(
            context.complete_raise_to_totals,
            width,
        )
        for subset_index, subset in enumerate(family.subsets):
            tasks.append(
                ExhaustiveTeacherTask(
                    ordinal=start_ordinal + len(tasks),
                    panel_position=panel_position,
                    pool_index=pool_index,
                    context_semantic_digest=context.semantic_digest,
                    arm=ExhaustiveTeacherArm.ANCHORED_SUBSET,
                    raise_width=width,
                    subset_index=subset_index,
                    request=_teacher_request(
                        context=context,
                        amounts=subset,
                        scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
                        label=(
                            f"{context.context_id}|exhaustive-teacher|"
                            f"raise-width-{width.count}|subset-{subset_index:04d}"
                        ),
                    ),
                )
            )
    return tuple(tasks)


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherSchedule:
    pool_sha256: str
    qualification_result_sha256: str
    panel_sha256: str
    tasks: tuple[ExhaustiveTeacherTask, ...]
    subset_counts_by_raise_width: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        _require_digest(self.pool_sha256, label="teacher schedule pool")
        _require_digest(
            self.qualification_result_sha256,
            label="teacher schedule qualification result",
        )
        _require_digest(self.panel_sha256, label="teacher schedule panel")
        if (
            self.qualification_result_sha256
            != ADR0323_QUALIFICATION_RESULT_SHA256
            or self.panel_sha256 != ADR0323_QUALIFIED_PANEL_SHA256
        ):
            raise ValueError("teacher schedule belongs to another qualification panel")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT
            or any(not isinstance(task, ExhaustiveTeacherTask) for task in self.tasks)
        ):
            raise TypeError("teacher schedule requires 2,495 immutable tasks")
        if tuple(task.ordinal for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("teacher schedule task ordinals are not contiguous")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("teacher schedule repeats a semantic task")
        if len({task.request_sha256 for task in self.tasks}) != len(self.tasks):
            raise ValueError("teacher schedule repeats an exact request")
        if self.subset_counts_by_raise_width != ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS:
            raise ValueError("teacher schedule subset work differs from ADR-0326")
        observed_counts = tuple(
            (
                width,
                sum(
                    task.arm is ExhaustiveTeacherArm.ANCHORED_SUBSET
                    and task.raise_width is not None
                    and task.raise_width.count == width
                    for task in self.tasks
                ),
            )
            for width, _ in ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS
        )
        if observed_counts != self.subset_counts_by_raise_width:
            raise ValueError("teacher schedule task counts differ from its ledger")
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
            if not context_tasks or context_tasks[0].arm is not (
                ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE
            ):
                raise ValueError("teacher context does not begin with its full arm")
            if any(
                task.pool_index != pool_index
                or task.context_semantic_digest != context_digest
                for task in context_tasks
            ):
                raise ValueError("teacher context tasks differ from panel membership")
            subset_tasks = context_tasks[1:]
            observed_order = tuple(
                (task.raise_width.count, task.subset_index)
                for task in subset_tasks
                if task.raise_width is not None
            )
            expected_order = tuple(
                (width, index)
                for width in range(2, 7)
                for index in range(
                    sum(
                        task.arm is ExhaustiveTeacherArm.ANCHORED_SUBSET
                        and task.raise_width is not None
                        and task.raise_width.count == width
                        for task in subset_tasks
                    )
                )
            )
            if observed_order != expected_order:
                raise ValueError("teacher subsets are not width/lexicographic ordered")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "panel_sha256": self.panel_sha256,
                "pool_sha256": self.pool_sha256,
                "qualification_result_sha256": self.qualification_result_sha256,
                "subset_counts_by_raise_width": self.subset_counts_by_raise_width,
                "task_digests": tuple(task.digest for task in self.tasks),
                "version": "adr0323-exhaustive-teacher-schedule-v1",
            }
        )


def build_adr0323_exhaustive_teacher_schedule() -> ExhaustiveTeacherSchedule:
    """Build the exact value-free panel schedule without invoking the consumer."""

    retained = verify_adr0323_qualification_result_artifact()
    pool = verify_adr0324_structure_source_and_pool()
    if retained.panel.digest != ADR0323_QUALIFIED_PANEL_SHA256:
        raise RuntimeError("ADR-0326 qualified panel identity drifted")
    tasks: list[ExhaustiveTeacherTask] = []
    for panel_position, pool_index in enumerate(retained.panel.pool_indices):
        context_tasks = exhaustive_teacher_tasks_for_context(
            context=pool.contexts[pool_index],
            panel_position=panel_position,
            pool_index=pool_index,
            start_ordinal=len(tasks),
        )
        tasks.extend(context_tasks)
    return ExhaustiveTeacherSchedule(
        pool_sha256=pool.digest,
        qualification_result_sha256=retained.qualification_result_sha256,
        panel_sha256=retained.panel.digest,
        tasks=tuple(tasks),
        subset_counts_by_raise_width=ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
    )


@dataclass(frozen=True, slots=True)
class TeacherSubsetCandidate:
    subset_index: int
    raise_to_totals: tuple[int, ...]
    value: CertifiedChipValueInterval

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.subset_index, label="teacher candidate index")
        if (
            not isinstance(self.raise_to_totals, tuple)
            or len(self.raise_to_totals) < 2
            or any(
                isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0
                for amount in self.raise_to_totals
            )
            or any(
                left >= right
                for left, right in zip(
                    self.raise_to_totals,
                    self.raise_to_totals[1:],
                    strict=False,
                )
            )
        ):
            raise ValueError("teacher candidate raise totals must increase")
        if not isinstance(self.value, CertifiedChipValueInterval):
            raise TypeError("teacher candidate requires a certified value interval")


@dataclass(frozen=True, slots=True)
class TeacherWidthEnvelope:
    raise_width: RaiseActionWidth
    value: CertifiedChipValueInterval
    nondominated_subset_indices: tuple[int, ...]
    equivalent_subset_indices: tuple[int, ...]
    unique_best_subset_index: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("teacher envelope requires a raise-action width")
        if not isinstance(self.value, CertifiedChipValueInterval):
            raise TypeError("teacher envelope requires a certified value interval")
        for label, values in (
            ("nondominated", self.nondominated_subset_indices),
            ("equivalent", self.equivalent_subset_indices),
        ):
            if (
                not isinstance(values, tuple)
                or (label == "nondominated" and not values)
                or tuple(sorted(set(values))) != values
                or any(
                    isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in values
                )
            ):
                raise ValueError(f"teacher {label} subset indices are invalid")
        if self.unique_best_subset_index is not None:
            if self.nondominated_subset_indices != (self.unique_best_subset_index,):
                raise ValueError("unique teacher subset must be the sole nondominated one")


def reduce_teacher_width(
    candidates: tuple[TeacherSubsetCandidate, ...],
    *,
    raise_width: RaiseActionWidth,
    equivalence_allowance: TeacherEquivalenceAllowance,
) -> TeacherWidthEnvelope:
    """Return the conservative set-valued teacher for one action width."""

    if not isinstance(candidates, tuple) or not candidates:
        raise TypeError("teacher reduction requires immutable candidates")
    if any(not isinstance(candidate, TeacherSubsetCandidate) for candidate in candidates):
        raise TypeError("teacher reduction contains a nonsemantic candidate")
    if not isinstance(raise_width, RaiseActionWidth):
        raise TypeError("teacher reduction requires a raise-action width")
    if not isinstance(equivalence_allowance, TeacherEquivalenceAllowance):
        raise TypeError("teacher reduction requires its equivalence allowance")
    if tuple(candidate.subset_index for candidate in candidates) != tuple(
        range(len(candidates))
    ):
        raise ValueError("teacher candidates must retain lexicographic subset order")
    if any(len(candidate.raise_to_totals) != raise_width.count for candidate in candidates):
        raise ValueError("teacher candidate width differs from its semantic width")
    if len({candidate.raise_to_totals for candidate in candidates}) != len(candidates):
        raise ValueError("teacher candidates repeat a raise subset")
    lower = max(candidate.value.lower_chips for candidate in candidates)
    upper = max(candidate.value.upper_chips for candidate in candidates)
    nondominated = tuple(
        candidate.subset_index
        for candidate in candidates
        if not any(
            other.subset_index != candidate.subset_index
            and other.value.lower_chips > candidate.value.upper_chips
            for other in candidates
        )
    )
    equivalent = tuple(
        candidate.subset_index
        for candidate in candidates
        if upper - candidate.value.lower_chips <= equivalence_allowance.chips
    )
    return TeacherWidthEnvelope(
        raise_width=raise_width,
        value=CertifiedChipValueInterval(lower, upper),
        nondominated_subset_indices=nondominated,
        equivalent_subset_indices=equivalent,
        unique_best_subset_index=(nondominated[0] if len(nondominated) == 1 else None),
    )


def _accepted_interval(
    accepted: CertifiedReducedSizingAcceptedV2,
) -> CertifiedChipValueInterval:
    if not isinstance(accepted, CertifiedReducedSizingAcceptedV2):
        raise TypeError("teacher value interval requires accepted evidence")
    return CertifiedChipValueInterval(
        lower_chips=accepted.feasible_behavioral_lower_bound_chips,
        upper_chips=accepted.certified_upper_bound_chips,
    )


def _verify_accepted_task(
    accepted: CertifiedReducedSizingAcceptedV2,
    task: ExhaustiveTeacherTask,
) -> None:
    if not isinstance(accepted, CertifiedReducedSizingAcceptedV2):
        raise TypeError("teacher arm requires accepted consumer evidence")
    if not isinstance(task, ExhaustiveTeacherTask):
        raise TypeError("teacher accepted evidence requires its semantic task")
    if (
        accepted.request != task.request
        or accepted.request_sha256 != task.request_sha256
        or accepted.legal_raise_set_sha256 != task.legal_raise_set_sha256
        or accepted.solution.linear_program_sha256 != task.linear_program_sha256
        or accepted.public_highs_ds_invocation_count != 1
    ):
        raise ValueError("teacher accepted evidence differs from its exact task")


def _accepted_payload(
    accepted: CertifiedReducedSizingAcceptedV2,
) -> dict[str, object]:
    return {
        "bet_increments": tuple(
            amount.chips for amount in accepted.reduced_bet_increments
        ),
        "certified_gap_hex": accepted.certified_gap_chips.hex(),
        "certified_upper_hex": accepted.certified_upper_bound_chips.hex(),
        "consumer_protocol_sha256": accepted.consumer_protocol_sha256,
        "consumer_source_sha256": accepted.consumer_source_sha256,
        "feasible_lower_hex": accepted.feasible_behavioral_lower_bound_chips.hex(),
        "legal_raise_set_sha256": accepted.legal_raise_set_sha256,
        "linear_program_sha256": accepted.solution.linear_program_sha256,
        "public_call_count": accepted.public_highs_ds_invocation_count,
        "public_state_sha256": accepted.public_state_sha256,
        "raise_to_totals": tuple(
            amount.chips for amount in accepted.legal_raise_to_totals
        ),
        "request_sha256": accepted.request_sha256,
        "signed_gap_hex": accepted.signed_certificate_gap_chips.hex(),
    }


def _regret_payload(regret: CertifiedChipRegretInterval) -> dict[str, str]:
    return {
        "nonnegative_lower_hex": regret.nonnegative_lower_chips.hex(),
        "nonnegative_upper_hex": regret.nonnegative_upper_chips.hex(),
        "signed_lower_hex": regret.signed_lower_chips.hex(),
        "signed_upper_hex": regret.signed_upper_chips.hex(),
    }


def _normalized_payload(
    normalized: NormalizedTeacherRegretInterval,
) -> dict[str, str]:
    return {
        "lower_hex": normalized.lower.hex(),
        "upper_hex": normalized.upper.hex(),
    }


@dataclass(frozen=True, slots=True)
class TeacherSubsetObservation:
    task: ExhaustiveTeacherTask
    full_request_sha256: str
    full_value: CertifiedChipValueInterval
    accepted: CertifiedReducedSizingAcceptedV2
    payoff_span_chips: int
    regret: CertifiedChipRegretInterval
    normalized_regret: NormalizedTeacherRegretInterval

    def __post_init__(self) -> None:
        if (
            not isinstance(self.task, ExhaustiveTeacherTask)
            or self.task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET
        ):
            raise TypeError("teacher subset observation requires a subset task")
        _require_digest(self.full_request_sha256, label="teacher observation full request")
        if not isinstance(self.full_value, CertifiedChipValueInterval):
            raise TypeError("teacher observation requires its full value interval")
        _verify_accepted_task(self.accepted, self.task)
        expected_regret = certified_full_minus_subset_regret(
            full=self.full_value,
            subset=_accepted_interval(self.accepted),
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_normalized = normalize_teacher_regret(
            expected_regret,
            payoff_span_chips=self.payoff_span_chips,
        )
        if self.regret != expected_regret or self.normalized_regret != expected_normalized:
            raise ValueError("teacher subset regret or normalization drifted")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "accepted": _accepted_payload(self.accepted),
                "full_request_sha256": self.full_request_sha256,
                "full_value": {
                    "lower_hex": self.full_value.lower_chips.hex(),
                    "upper_hex": self.full_value.upper_chips.hex(),
                },
                "normalized_regret": _normalized_payload(self.normalized_regret),
                "payoff_span_chips": self.payoff_span_chips,
                "regret": _regret_payload(self.regret),
                "task_sha256": self.task.digest,
                "version": "adr0323-exhaustive-teacher-subset-observation-v1",
            }
        )


def build_teacher_subset_observation(
    *,
    task: ExhaustiveTeacherTask,
    full: CertifiedReducedSizingAcceptedV2,
    accepted: CertifiedReducedSizingAcceptedV2,
    payoff_span_chips: int,
) -> TeacherSubsetObservation:
    if task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET:
        raise ValueError("only a subset task can produce a subset observation")
    _verify_accepted_task(accepted, task)
    if full.request.legal_raise_scope is not LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE:
        raise ValueError("teacher subset comparison requires a complete full arm")
    full_request = full.request
    subset_request = task.request
    if (
        full_request.betting != subset_request.betting
        or full_request.response_model is not subset_request.response_model
        or full_request.joint_probabilities != subset_request.joint_probabilities
        or full_request.showdown_signs != subset_request.showdown_signs
        or full.public_state_sha256 != accepted.public_state_sha256
        or any(
            amount not in full_request.legal_raise_to_totals
            for amount in subset_request.legal_raise_to_totals
        )
    ):
        raise ValueError("teacher full and subset arms belong to different games")
    full_value = _accepted_interval(full)
    regret = certified_full_minus_subset_regret(
        full=full_value,
        subset=_accepted_interval(accepted),
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    return TeacherSubsetObservation(
        task=task,
        full_request_sha256=full.request_sha256,
        full_value=full_value,
        accepted=accepted,
        payoff_span_chips=payoff_span_chips,
        regret=regret,
        normalized_regret=normalize_teacher_regret(
            regret,
            payoff_span_chips=payoff_span_chips,
        ),
    )


@dataclass(frozen=True, slots=True)
class TeacherWidthResult:
    raise_width: RaiseActionWidth
    full_request_sha256: str
    full_value: CertifiedChipValueInterval
    payoff_span_chips: int
    subset_observations: tuple[TeacherSubsetObservation, ...]
    envelope: TeacherWidthEnvelope
    full_minus_teacher_regret: CertifiedChipRegretInterval
    normalized_full_minus_teacher_regret: NormalizedTeacherRegretInterval

    def __post_init__(self) -> None:
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("teacher width result requires a raise-action width")
        _require_digest(self.full_request_sha256, label="teacher width full request")
        if not isinstance(self.full_value, CertifiedChipValueInterval):
            raise TypeError("teacher width result requires its full value interval")
        if not isinstance(self.subset_observations, tuple) or not self.subset_observations:
            raise TypeError("teacher width result requires subset observations")
        if any(
            not isinstance(observation, TeacherSubsetObservation)
            for observation in self.subset_observations
        ):
            raise TypeError("teacher width result contains a nonsemantic observation")
        if tuple(
            observation.task.subset_index for observation in self.subset_observations
        ) != tuple(range(len(self.subset_observations))):
            raise ValueError("teacher width observations lost lexicographic order")
        if any(
            observation.task.raise_width != self.raise_width
            or observation.full_request_sha256 != self.full_request_sha256
            or observation.full_value != self.full_value
            or observation.payoff_span_chips != self.payoff_span_chips
            for observation in self.subset_observations
        ):
            raise ValueError("teacher width observations differ from their full arm")
        first_task = self.subset_observations[0].task
        if any(
            observation.task.panel_position != first_task.panel_position
            or observation.task.pool_index != first_task.pool_index
            or observation.task.context_semantic_digest
            != first_task.context_semantic_digest
            for observation in self.subset_observations
        ):
            raise ValueError("teacher width observations span multiple contexts")
        candidates = tuple(
            TeacherSubsetCandidate(
                subset_index=observation.task.subset_index,
                raise_to_totals=observation.task.raise_to_totals,
                value=_accepted_interval(observation.accepted),
            )
            for observation in self.subset_observations
            if observation.task.subset_index is not None
        )
        expected_envelope = reduce_teacher_width(
            candidates,
            raise_width=self.raise_width,
            equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
        )
        expected_regret = certified_full_minus_subset_regret(
            full=self.full_value,
            subset=expected_envelope.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        expected_normalized = normalize_teacher_regret(
            expected_regret,
            payoff_span_chips=self.payoff_span_chips,
        )
        if (
            self.envelope != expected_envelope
            or self.full_minus_teacher_regret != expected_regret
            or self.normalized_full_minus_teacher_regret != expected_normalized
        ):
            raise ValueError("teacher width envelope or regret drifted")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "envelope": {
                    "equivalent_subset_indices": self.envelope.equivalent_subset_indices,
                    "lower_hex": self.envelope.value.lower_chips.hex(),
                    "nondominated_subset_indices": (
                        self.envelope.nondominated_subset_indices
                    ),
                    "unique_best_subset_index": self.envelope.unique_best_subset_index,
                    "upper_hex": self.envelope.value.upper_chips.hex(),
                },
                "full_minus_teacher_regret": _regret_payload(
                    self.full_minus_teacher_regret
                ),
                "full_request_sha256": self.full_request_sha256,
                "full_value": {
                    "lower_hex": self.full_value.lower_chips.hex(),
                    "upper_hex": self.full_value.upper_chips.hex(),
                },
                "normalized_full_minus_teacher_regret": _normalized_payload(
                    self.normalized_full_minus_teacher_regret
                ),
                "payoff_span_chips": self.payoff_span_chips,
                "raise_width": self.raise_width.count,
                "subset_observation_sha256": tuple(
                    observation.digest for observation in self.subset_observations
                ),
                "version": "adr0323-exhaustive-teacher-width-result-v1",
            }
        )


def build_teacher_width_result(
    *,
    raise_width: RaiseActionWidth,
    full: CertifiedReducedSizingAcceptedV2,
    payoff_span_chips: int,
    subset_observations: tuple[TeacherSubsetObservation, ...],
) -> TeacherWidthResult:
    full_value = _accepted_interval(full)
    candidates = tuple(
        TeacherSubsetCandidate(
            subset_index=observation.task.subset_index,
            raise_to_totals=observation.task.raise_to_totals,
            value=_accepted_interval(observation.accepted),
        )
        for observation in subset_observations
        if observation.task.subset_index is not None
    )
    envelope = reduce_teacher_width(
        candidates,
        raise_width=raise_width,
        equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    )
    regret = certified_full_minus_subset_regret(
        full=full_value,
        subset=envelope.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    return TeacherWidthResult(
        raise_width=raise_width,
        full_request_sha256=full.request_sha256,
        full_value=full_value,
        payoff_span_chips=payoff_span_chips,
        subset_observations=subset_observations,
        envelope=envelope,
        full_minus_teacher_regret=regret,
        normalized_full_minus_teacher_regret=normalize_teacher_regret(
            regret,
            payoff_span_chips=payoff_span_chips,
        ),
    )


@dataclass(frozen=True, slots=True)
class TeacherContextResult:
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    payoff_span_chips: int
    full_task: ExhaustiveTeacherTask
    full: CertifiedReducedSizingAcceptedV2
    widths: tuple[TeacherWidthResult, ...]

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.panel_position, label="teacher context position")
        _require_nonnegative_int(self.pool_index, label="teacher context pool index")
        _require_digest(self.context_semantic_digest, label="teacher context digest")
        if (
            isinstance(self.payoff_span_chips, bool)
            or not isinstance(self.payoff_span_chips, int)
            or self.payoff_span_chips <= 0
        ):
            raise ValueError("teacher context payoff span must be positive chips")
        if (
            self.full_task.arm is not ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE
            or self.full_task.panel_position != self.panel_position
            or self.full_task.pool_index != self.pool_index
            or self.full_task.context_semantic_digest != self.context_semantic_digest
        ):
            raise ValueError("teacher context full task differs from its identity")
        _verify_accepted_task(self.full, self.full_task)
        if (
            not isinstance(self.widths, tuple)
            or tuple(result.raise_width for result in self.widths) != ADR0323_RAISE_WIDTHS
        ):
            raise ValueError("teacher context widths differ from ADR-0323")
        full_value = _accepted_interval(self.full)
        expected_counts = tuple(
            len(
                anchored_raise_subset_family(
                    self.full_task.request.legal_raise_to_totals,
                    width,
                ).subsets
            )
            for width in ADR0323_RAISE_WIDTHS
        )
        if tuple(
            len(result.subset_observations) for result in self.widths
        ) != expected_counts:
            raise ValueError("teacher context subset counts are incomplete")
        for result in self.widths:
            expected_subsets = anchored_raise_subset_family(
                self.full_task.request.legal_raise_to_totals,
                result.raise_width,
            ).subsets
            observed_subsets = tuple(
                observation.task.request.legal_raise_to_totals
                for observation in result.subset_observations
            )
            if observed_subsets != expected_subsets:
                raise ValueError("teacher context subset family drifted")
        if any(
            observation.task.panel_position != self.panel_position
            or observation.task.pool_index != self.pool_index
            or observation.task.context_semantic_digest != self.context_semantic_digest
            or result.full_request_sha256 != self.full.request_sha256
            or result.full_value != full_value
            or result.payoff_span_chips != self.payoff_span_chips
            for result in self.widths
            for observation in result.subset_observations
        ):
            raise ValueError("teacher context width evidence differs from its context")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        return 1 + sum(len(result.subset_observations) for result in self.widths)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_semantic_digest": self.context_semantic_digest,
                "full": _accepted_payload(self.full),
                "full_task_sha256": self.full_task.digest,
                "panel_position": self.panel_position,
                "payoff_span_chips": self.payoff_span_chips,
                "pool_index": self.pool_index,
                "width_result_sha256": tuple(result.digest for result in self.widths),
                "version": "adr0323-exhaustive-teacher-context-result-v1",
            }
        )


class ExhaustiveTeacherStopReason(StrEnum):
    COMPLETED = "completed"
    CONSUMER_REJECTED = "consumer_rejected"
    NUMERICAL_REJECTED = "numerical_rejected"


class ExhaustiveTeacherFailureStage(StrEnum):
    FULL_ARM = "full_arm"
    SUBSET_ARM = "subset_arm"
    SUBSET_REGRET = "subset_regret"
    WIDTH_REDUCTION = "width_reduction"


class ExhaustiveTeacherFailureKind(StrEnum):
    CONSUMER_REJECTION = "consumer_rejection"
    NUMERICAL_REJECTION = "numerical_rejection"


@dataclass(frozen=True, slots=True)
class TeacherRunnerException:
    module: str
    type_name: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.module, str) or not self.module:
            raise ValueError("teacher exception module must be nonempty")
        if not isinstance(self.type_name, str) or not self.type_name:
            raise ValueError("teacher exception type must be nonempty")
        if not isinstance(self.message, str):
            raise TypeError("teacher exception message must be text")


def _exception_chain(error: Exception) -> tuple[TeacherRunnerException, ...]:
    records: list[TeacherRunnerException] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        records.append(
            TeacherRunnerException(
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
    return tuple(records)


def _rejected_payload(
    rejected: CertifiedReducedSizingRejectedV2,
) -> dict[str, object]:
    return {
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
    }


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherFailure:
    """Complete evidence for a typed, no-retry campaign stop."""

    kind: ExhaustiveTeacherFailureKind
    stage: ExhaustiveTeacherFailureStage
    task: ExhaustiveTeacherTask
    completed_full: CertifiedReducedSizingAcceptedV2 | None
    completed_width_results: tuple[TeacherWidthResult, ...]
    incomplete_subset_observations: tuple[TeacherSubsetObservation, ...]
    rejected: CertifiedReducedSizingRejectedV2 | None = None
    accepted_at_failure: CertifiedReducedSizingAcceptedV2 | None = None
    exception_chain: tuple[TeacherRunnerException, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ExhaustiveTeacherFailureKind):
            raise TypeError("teacher failure kind must be semantic")
        if not isinstance(self.stage, ExhaustiveTeacherFailureStage):
            raise TypeError("teacher failure stage must be semantic")
        if not isinstance(self.task, ExhaustiveTeacherTask):
            raise TypeError("teacher failure requires its exact current task")
        if not isinstance(self.completed_width_results, tuple) or any(
            not isinstance(value, TeacherWidthResult)
            for value in self.completed_width_results
        ):
            raise TypeError("teacher failure completed widths must be semantic")
        if tuple(
            result.raise_width for result in self.completed_width_results
        ) != ADR0323_RAISE_WIDTHS[: len(self.completed_width_results)]:
            raise ValueError("teacher failure completed widths are not a prefix")
        if not isinstance(self.incomplete_subset_observations, tuple) or any(
            not isinstance(value, TeacherSubsetObservation)
            for value in self.incomplete_subset_observations
        ):
            raise TypeError("teacher failure incomplete observations must be semantic")

        if self.completed_full is None:
            if self.completed_width_results or self.incomplete_subset_observations:
                raise ValueError("teacher failure has subset evidence without a full arm")
        else:
            if not isinstance(self.completed_full, CertifiedReducedSizingAcceptedV2):
                raise TypeError("teacher failure full evidence must be accepted")
            if (
                self.completed_full.request.legal_raise_scope
                is not LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE
            ):
                raise ValueError("teacher failure full evidence is not a complete universe")

        expected_incomplete_width = ADR0323_RAISE_WIDTHS[
            len(self.completed_width_results)
        ] if len(self.completed_width_results) < len(ADR0323_RAISE_WIDTHS) else None
        if self.incomplete_subset_observations:
            if expected_incomplete_width is None or any(
                observation.task.raise_width != expected_incomplete_width
                for observation in self.incomplete_subset_observations
            ):
                raise ValueError("teacher failure incomplete observations have wrong width")
            if tuple(
                observation.task.subset_index
                for observation in self.incomplete_subset_observations
            ) != tuple(range(len(self.incomplete_subset_observations))):
                raise ValueError("teacher failure incomplete observations are not a prefix")

        semantic_objects = tuple(
            observation
            for result in self.completed_width_results
            for observation in result.subset_observations
        ) + self.incomplete_subset_observations
        if any(
            observation.task.panel_position != self.task.panel_position
            or observation.task.pool_index != self.task.pool_index
            or observation.task.context_semantic_digest
            != self.task.context_semantic_digest
            for observation in semantic_objects
        ):
            raise ValueError("teacher failure evidence belongs to another context")
        if self.completed_full is not None:
            full_value = _accepted_interval(self.completed_full)
            if any(
                result.full_request_sha256 != self.completed_full.request_sha256
                or result.full_value != full_value
                for result in self.completed_width_results
            ) or any(
                observation.full_request_sha256
                != self.completed_full.request_sha256
                or observation.full_value != full_value
                for observation in self.incomplete_subset_observations
            ):
                raise ValueError("teacher failure evidence changed its full arm")
            complete_totals = self.completed_full.request.legal_raise_to_totals
            for result in self.completed_width_results:
                expected_subsets = anchored_raise_subset_family(
                    complete_totals,
                    result.raise_width,
                ).subsets
                observed_subsets = tuple(
                    observation.task.request.legal_raise_to_totals
                    for observation in result.subset_observations
                )
                if observed_subsets != expected_subsets:
                    raise ValueError("teacher failure completed subset family drifted")
            if expected_incomplete_width is not None:
                expected_prefix = anchored_raise_subset_family(
                    complete_totals,
                    expected_incomplete_width,
                ).subsets[: len(self.incomplete_subset_observations)]
                observed_prefix = tuple(
                    observation.task.request.legal_raise_to_totals
                    for observation in self.incomplete_subset_observations
                )
                if observed_prefix != expected_prefix:
                    raise ValueError("teacher failure subset prefix drifted")

        if self.kind is ExhaustiveTeacherFailureKind.CONSUMER_REJECTION:
            if (
                not isinstance(self.rejected, CertifiedReducedSizingRejectedV2)
                or self.accepted_at_failure is not None
                or self.exception_chain
                or self.stage
                not in (
                    ExhaustiveTeacherFailureStage.FULL_ARM,
                    ExhaustiveTeacherFailureStage.SUBSET_ARM,
                )
            ):
                raise ValueError("consumer teacher failure has the wrong evidence")
            if self.rejected.request != self.task.request:
                raise ValueError("teacher rejection differs from its exact task")
        else:
            if (
                self.rejected is not None
                or not self.exception_chain
                or self.stage
                not in (
                    ExhaustiveTeacherFailureStage.SUBSET_REGRET,
                    ExhaustiveTeacherFailureStage.WIDTH_REDUCTION,
                )
            ):
                raise ValueError("numerical teacher failure has the wrong evidence")
            if self.stage is ExhaustiveTeacherFailureStage.SUBSET_REGRET:
                if not isinstance(
                    self.accepted_at_failure,
                    CertifiedReducedSizingAcceptedV2,
                ):
                    raise TypeError("subset-regret rejection must retain accepted evidence")
                _verify_accepted_task(self.accepted_at_failure, self.task)
            elif self.accepted_at_failure is not None:
                raise ValueError("width reduction cannot add another accepted call")

        if self.stage is ExhaustiveTeacherFailureStage.FULL_ARM:
            if (
                self.task.arm is not ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE
                or self.completed_full is not None
            ):
                raise ValueError("full-arm failure has subset or completed-full state")
        else:
            if (
                self.task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET
                or self.completed_full is None
                or self.task.raise_width != expected_incomplete_width
            ):
                raise ValueError("subset failure lacks its completed full arm")
        if self.stage is ExhaustiveTeacherFailureStage.WIDTH_REDUCTION:
            if (
                not self.incomplete_subset_observations
                or self.incomplete_subset_observations[-1].task != self.task
            ):
                raise ValueError("width reduction failure must name its last subset")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        count = 0 if self.completed_full is None else 1
        count += sum(
            len(result.subset_observations)
            for result in self.completed_width_results
        )
        count += len(self.incomplete_subset_observations)
        if self.rejected is not None:
            count += self.rejected.public_highs_ds_invocation_count
        if self.accepted_at_failure is not None:
            count += self.accepted_at_failure.public_highs_ds_invocation_count
        return count

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "accepted_at_failure": (
                    None
                    if self.accepted_at_failure is None
                    else _accepted_payload(self.accepted_at_failure)
                ),
                "completed_full": (
                    None
                    if self.completed_full is None
                    else _accepted_payload(self.completed_full)
                ),
                "completed_width_sha256": tuple(
                    result.digest for result in self.completed_width_results
                ),
                "exception_chain": tuple(
                    (item.module, item.type_name, item.message)
                    for item in self.exception_chain
                ),
                "incomplete_subset_sha256": tuple(
                    observation.digest
                    for observation in self.incomplete_subset_observations
                ),
                "kind": self.kind.value,
                "rejected": (
                    None if self.rejected is None else _rejected_payload(self.rejected)
                ),
                "stage": self.stage.value,
                "task_sha256": self.task.digest,
                "version": "adr0323-exhaustive-teacher-failure-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherCampaignResult:
    pool_sha256: str
    qualification_result_sha256: str
    panel_sha256: str
    schedule_sha256: str
    teacher_source_sha256: str
    contexts: tuple[TeacherContextResult, ...]
    stop_reason: ExhaustiveTeacherStopReason
    failure: ExhaustiveTeacherFailure | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("teacher result pool", self.pool_sha256),
            ("teacher result qualification", self.qualification_result_sha256),
            ("teacher result panel", self.panel_sha256),
            ("teacher result schedule", self.schedule_sha256),
            ("teacher result source", self.teacher_source_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.qualification_result_sha256
            != ADR0323_QUALIFICATION_RESULT_SHA256
            or self.panel_sha256 != ADR0323_QUALIFIED_PANEL_SHA256
        ):
            raise ValueError("teacher result belongs to another qualified panel")
        if not isinstance(self.contexts, tuple) or any(
            not isinstance(value, TeacherContextResult) for value in self.contexts
        ):
            raise TypeError("teacher result contexts must be semantic")
        if tuple(context.panel_position for context in self.contexts) != tuple(
            range(len(self.contexts))
        ):
            raise ValueError("teacher result contexts are not a contiguous prefix")
        if not isinstance(self.stop_reason, ExhaustiveTeacherStopReason):
            raise TypeError("teacher stop reason must be semantic")
        if self.stop_reason is ExhaustiveTeacherStopReason.COMPLETED:
            if len(self.contexts) != 16 or self.failure is not None:
                raise ValueError("completed teacher result has the wrong stop state")
        else:
            if not isinstance(self.failure, ExhaustiveTeacherFailure):
                raise TypeError("rejected teacher result must retain its failure")
            if self.failure.task.panel_position != len(self.contexts):
                raise ValueError("teacher failure does not follow completed contexts")
            expected_reason = (
                ExhaustiveTeacherStopReason.CONSUMER_REJECTED
                if self.failure.kind
                is ExhaustiveTeacherFailureKind.CONSUMER_REJECTION
                else ExhaustiveTeacherStopReason.NUMERICAL_REJECTED
            )
            if self.stop_reason is not expected_reason:
                raise ValueError("teacher stop reason differs from its failure kind")

    @property
    def public_highs_ds_invocation_count(self) -> int:
        return sum(
            context.public_highs_ds_invocation_count for context in self.contexts
        ) + (0 if self.failure is None else self.failure.public_highs_ds_invocation_count)

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "context_sha256": tuple(context.digest for context in self.contexts),
                "failure_sha256": None if self.failure is None else self.failure.digest,
                "panel_sha256": self.panel_sha256,
                "pool_sha256": self.pool_sha256,
                "qualification_result_sha256": self.qualification_result_sha256,
                "schedule_sha256": self.schedule_sha256,
                "stop_reason": self.stop_reason.value,
                "teacher_source_sha256": self.teacher_source_sha256,
                "version": "adr0323-exhaustive-teacher-campaign-result-v1",
            }
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_exhaustive_teacher_result_bytes(self)

    def verify_against_schedule(self, schedule: ExhaustiveTeacherSchedule) -> None:
        if not isinstance(schedule, ExhaustiveTeacherSchedule):
            raise TypeError("teacher result verification requires its exact schedule")
        if (
            self.pool_sha256 != schedule.pool_sha256
            or self.qualification_result_sha256
            != schedule.qualification_result_sha256
            or self.panel_sha256 != schedule.panel_sha256
            or self.schedule_sha256 != schedule.digest
        ):
            raise ValueError("teacher result schedule identities drifted")

        tasks_by_context = tuple(
            tuple(
                task
                for task in schedule.tasks
                if task.panel_position == panel_position
            )
            for panel_position in range(16)
        )
        for context in self.contexts:
            expected = tasks_by_context[context.panel_position]
            observed = (context.full_task,) + tuple(
                observation.task
                for result in context.widths
                for observation in result.subset_observations
            )
            if observed != expected:
                raise ValueError("teacher context evidence differs from schedule")

        if self.failure is None:
            return
        failure = self.failure
        expected = tasks_by_context[failure.task.panel_position]
        observed: tuple[ExhaustiveTeacherTask, ...] = ()
        if failure.completed_full is not None:
            _verify_accepted_task(failure.completed_full, expected[0])
            observed += (expected[0],)
        observed += tuple(
            observation.task
            for result in failure.completed_width_results
            for observation in result.subset_observations
        )
        observed += tuple(
            observation.task
            for observation in failure.incomplete_subset_observations
        )
        current_is_already_observed = (
            failure.stage is ExhaustiveTeacherFailureStage.WIDTH_REDUCTION
        )
        if not current_is_already_observed:
            observed += (failure.task,)
        if observed != expected[: len(observed)]:
            raise ValueError("teacher failure evidence is not the exact schedule prefix")
        if current_is_already_observed and (
            not observed or observed[-1] != failure.task
        ):
            raise ValueError("teacher reduction failure does not end at its named task")


class ExhaustiveTeacherRunnerStage(StrEnum):
    SOURCE_PREFLIGHT = "source_preflight"
    EXECUTION = "execution"


@dataclass(frozen=True, slots=True)
class ExhaustiveTeacherRunnerRejected:
    """Unexpected owner failure; the public-call count is only a known prefix."""

    stage: ExhaustiveTeacherRunnerStage
    reason: str
    pool_sha256: str | None
    qualification_result_sha256: str | None
    panel_sha256: str | None
    schedule_sha256: str | None
    teacher_source_sha256: str | None
    completed_contexts: tuple[TeacherContextResult, ...]
    current_task: ExhaustiveTeacherTask | None
    known_public_highs_ds_invocation_count: int
    invocation_count_complete: bool
    exception_chain: tuple[TeacherRunnerException, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.stage, ExhaustiveTeacherRunnerStage):
            raise TypeError("teacher runner stage must be semantic")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("teacher runner rejection reason must be nonempty")
        if not isinstance(self.completed_contexts, tuple) or any(
            not isinstance(value, TeacherContextResult)
            for value in self.completed_contexts
        ):
            raise TypeError("teacher runner completed contexts must be semantic")
        if tuple(
            context.panel_position for context in self.completed_contexts
        ) != tuple(range(len(self.completed_contexts))):
            raise ValueError("teacher runner completed contexts are not a prefix")
        _require_nonnegative_int(
            self.known_public_highs_ds_invocation_count,
            label="known teacher public-call count",
        )
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("teacher invocation completeness must be boolean")
        if not isinstance(self.exception_chain, tuple) or not self.exception_chain:
            raise TypeError("teacher runner rejection requires an exception chain")

        identities = (
            self.pool_sha256,
            self.qualification_result_sha256,
            self.panel_sha256,
            self.schedule_sha256,
            self.teacher_source_sha256,
        )
        if self.stage is ExhaustiveTeacherRunnerStage.SOURCE_PREFLIGHT:
            if (
                any(value is not None for value in identities)
                or self.completed_contexts
                or self.current_task is not None
                or self.known_public_highs_ds_invocation_count != 0
                or not self.invocation_count_complete
            ):
                raise ValueError("teacher preflight rejection has execution evidence")
        else:
            for label, value in zip(
                (
                    "teacher runner pool",
                    "teacher runner qualification",
                    "teacher runner panel",
                    "teacher runner schedule",
                    "teacher runner source",
                ),
                identities,
                strict=True,
            ):
                _require_digest(value, label=label)
            if not isinstance(self.current_task, ExhaustiveTeacherTask):
                raise TypeError("teacher execution rejection requires its current task")
            allowed_positions = {len(self.completed_contexts)}
            if self.completed_contexts:
                allowed_positions.add(len(self.completed_contexts) - 1)
            if self.current_task.panel_position not in allowed_positions:
                raise ValueError("teacher runner current task is outside the prefix")
            if self.invocation_count_complete:
                raise ValueError("unexpected execution failure cannot claim complete calls")

    @property
    def digest(self) -> str:
        return _canonical_sha256(
            {
                "completed_context_sha256": tuple(
                    context.digest for context in self.completed_contexts
                ),
                "current_task_sha256": (
                    None if self.current_task is None else self.current_task.digest
                ),
                "exception_chain": tuple(
                    (item.module, item.type_name, item.message)
                    for item in self.exception_chain
                ),
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
                "teacher_source_sha256": self.teacher_source_sha256,
                "version": "adr0323-exhaustive-teacher-runner-rejection-v1",
            }
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_exhaustive_teacher_result_bytes(self)


ExhaustiveTeacherResult = (
    ExhaustiveTeacherCampaignResult | ExhaustiveTeacherRunnerRejected
)


def exhaustive_teacher_protocol_sha256() -> str:
    """Bind the prospective value semantics independently of source bytes."""

    return _canonical_sha256(
        {
            "artifact_retention": (
                "reserve-no-clobber-staging-before-run+canonical-json+byte-postcheck"
            ),
            "consumer": "certified-reduced-sizing-v2-one-public-highs-ds-call",
            "consumer_failure": "stop-no-retry-no-fallback-no-skip",
            "dominance": "other.lower>candidate.upper",
            "equivalence_allowance_chips": (
                ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE.chips
            ),
            "equivalence_effect": "reporting-only-no-selection-no-certificate-excuse",
            "exact_meaning": (
                "integer-legal-universe+rational-input+exact-subset+certified-interval"
            ),
            "full_arm_count": ADR0323_EXHAUSTIVE_TEACHER_FULL_TASK_COUNT,
            "full_reuse": "once-per-context-by-exact-request-digest-within-invocation",
            "headline_flatness_measure": "nondominated-subset-cardinality-by-context-width",
            "normalizer": "pot+2*effective_stack",
            "panel_context_sha256": ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
            "panel_pool_indices": ADR0323_QUALIFIED_POOL_INDICES,
            "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
            "qualification_result_sha256": ADR0323_QUALIFICATION_RESULT_SHA256,
            "raise_widths": tuple(width.count for width in ADR0323_RAISE_WIDTHS),
            "regret_interval": "[L_full-U_subset,U_full-L_subset]",
            "regret_nonnegative_clip": "[max(0,L),max(0,U)]",
            "response_model": ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY.value,
            "scope_order": (
                LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE.value,
                LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET.value,
            ),
            "subset_counts": ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
            "subset_order": "raise-width-ascending-then-lexicographic",
            "subset_task_count": ADR0323_EXHAUSTIVE_TEACHER_SUBSET_TASK_COUNT,
            "task_count": ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
            "teacher_interval": "[max(candidate.lower),max(candidate.upper)]",
            "teacher_selection": "all-nondominated;unique-only-if-sole-survivor",
            "tie_boundary": "teacher-preserves-ties;no-runtime-cost-election-here",
            "version": "adr0323-exhaustive-teacher-protocol-v1",
        }
    )


def verify_adr0327_teacher_source_and_dependencies() -> str:
    """Verify the exhaustive-teacher source closure before any consumer call."""

    from .fresh_action_width_teacher_seal import (
        ADR0327_EXHAUSTIVE_TEACHER_PROTOCOL_SHA256,
        ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST,
        ADR0327_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
        ADR0327_EXHAUSTIVE_TEACHER_TASK_COUNT,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST
    }
    if actual != ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0327 exhaustive-teacher source closure drifted")
    if (
        exhaustive_teacher_protocol_sha256()
        != ADR0327_EXHAUSTIVE_TEACHER_PROTOCOL_SHA256
        or ADR0327_EXHAUSTIVE_TEACHER_TASK_COUNT
        != ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT
        or ADR0327_EXHAUSTIVE_TEACHER_SUBSET_COUNTS
        != ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS
    ):
        raise RuntimeError("ADR-0327 exhaustive-teacher protocol drifted")
    return actual["fresh_action_width_teacher.py"]


def verify_adr0327_exhaustive_teacher_schedule(
    schedule: ExhaustiveTeacherSchedule,
) -> None:
    from .fresh_action_width_teacher_seal import (
        ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
    )

    if not isinstance(schedule, ExhaustiveTeacherSchedule):
        raise TypeError("teacher schedule verification requires a semantic schedule")
    if schedule.digest != ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0327 exhaustive-teacher schedule drifted")


def _campaign_result(
    *,
    schedule: ExhaustiveTeacherSchedule,
    teacher_source_sha256: str,
    contexts: list[TeacherContextResult],
    stop_reason: ExhaustiveTeacherStopReason,
    failure: ExhaustiveTeacherFailure | None = None,
) -> ExhaustiveTeacherCampaignResult:
    result = ExhaustiveTeacherCampaignResult(
        pool_sha256=schedule.pool_sha256,
        qualification_result_sha256=schedule.qualification_result_sha256,
        panel_sha256=schedule.panel_sha256,
        schedule_sha256=schedule.digest,
        teacher_source_sha256=teacher_source_sha256,
        contexts=tuple(contexts),
        stop_reason=stop_reason,
        failure=failure,
    )
    result.verify_against_schedule(schedule)
    return result


def run_adr0323_exhaustive_development_teacher() -> ExhaustiveTeacherResult:
    """Own the first exhaustive width-three-through-six development values."""

    try:
        teacher_source = verify_adr0327_teacher_source_and_dependencies()
        pool = verify_adr0324_structure_source_and_pool()
        schedule = build_adr0323_exhaustive_teacher_schedule()
        verify_adr0327_exhaustive_teacher_schedule(schedule)
    except Exception as error:
        return ExhaustiveTeacherRunnerRejected(
            stage=ExhaustiveTeacherRunnerStage.SOURCE_PREFLIGHT,
            reason="teacher source, panel, or schedule drift",
            pool_sha256=None,
            qualification_result_sha256=None,
            panel_sha256=None,
            schedule_sha256=None,
            teacher_source_sha256=None,
            completed_contexts=(),
            current_task=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=_exception_chain(error),
        )
    return _execute_adr0323_exhaustive_development_teacher(
        teacher_source=teacher_source,
        pool=pool,
        schedule=schedule,
    )


def _task_payload(task: ExhaustiveTeacherTask) -> dict[str, object]:
    return {
        "arm": task.arm.value,
        "context_semantic_digest": task.context_semantic_digest,
        "legal_raise_set_sha256": task.legal_raise_set_sha256,
        "linear_program_sha256": task.linear_program_sha256,
        "ordinal": task.ordinal,
        "panel_position": task.panel_position,
        "pool_index": task.pool_index,
        "raise_to_totals": task.raise_to_totals,
        "raise_width": None if task.raise_width is None else task.raise_width.count,
        "request_sha256": task.request_sha256,
        "subset_index": task.subset_index,
        "task_sha256": task.digest,
    }


def _observation_payload(
    observation: TeacherSubsetObservation,
) -> dict[str, object]:
    return {
        "accepted": _accepted_payload(observation.accepted),
        "full_request_sha256": observation.full_request_sha256,
        "full_value": {
            "lower_hex": observation.full_value.lower_chips.hex(),
            "upper_hex": observation.full_value.upper_chips.hex(),
        },
        "normalized_regret": _normalized_payload(observation.normalized_regret),
        "observation_sha256": observation.digest,
        "payoff_span_chips": observation.payoff_span_chips,
        "regret": _regret_payload(observation.regret),
        "task": _task_payload(observation.task),
    }


def _width_payload(result: TeacherWidthResult) -> dict[str, object]:
    return {
        "envelope": {
            "equivalent_subset_indices": result.envelope.equivalent_subset_indices,
            "lower_hex": result.envelope.value.lower_chips.hex(),
            "nondominated_subset_indices": (
                result.envelope.nondominated_subset_indices
            ),
            "unique_best_subset_index": result.envelope.unique_best_subset_index,
            "upper_hex": result.envelope.value.upper_chips.hex(),
        },
        "full_minus_teacher_regret": _regret_payload(
            result.full_minus_teacher_regret
        ),
        "full_request_sha256": result.full_request_sha256,
        "full_value": {
            "lower_hex": result.full_value.lower_chips.hex(),
            "upper_hex": result.full_value.upper_chips.hex(),
        },
        "normalized_full_minus_teacher_regret": _normalized_payload(
            result.normalized_full_minus_teacher_regret
        ),
        "payoff_span_chips": result.payoff_span_chips,
        "raise_width": result.raise_width.count,
        "subset_observations": tuple(
            _observation_payload(observation)
            for observation in result.subset_observations
        ),
        "width_result_sha256": result.digest,
    }


def _context_payload(context: TeacherContextResult) -> dict[str, object]:
    return {
        "context_result_sha256": context.digest,
        "context_semantic_digest": context.context_semantic_digest,
        "full": _accepted_payload(context.full),
        "full_task": _task_payload(context.full_task),
        "panel_position": context.panel_position,
        "payoff_span_chips": context.payoff_span_chips,
        "pool_index": context.pool_index,
        "widths": tuple(_width_payload(result) for result in context.widths),
    }


def _failure_payload(failure: ExhaustiveTeacherFailure) -> dict[str, object]:
    return {
        "accepted_at_failure": (
            None
            if failure.accepted_at_failure is None
            else _accepted_payload(failure.accepted_at_failure)
        ),
        "completed_full": (
            None
            if failure.completed_full is None
            else _accepted_payload(failure.completed_full)
        ),
        "completed_widths": tuple(
            _width_payload(result) for result in failure.completed_width_results
        ),
        "exception_chain": tuple(
            {
                "message": item.message,
                "module": item.module,
                "type_name": item.type_name,
            }
            for item in failure.exception_chain
        ),
        "failure_sha256": failure.digest,
        "incomplete_subset_observations": tuple(
            _observation_payload(observation)
            for observation in failure.incomplete_subset_observations
        ),
        "kind": failure.kind.value,
        "rejected": (
            None if failure.rejected is None else _rejected_payload(failure.rejected)
        ),
        "stage": failure.stage.value,
        "task": _task_payload(failure.task),
    }


def exhaustive_teacher_result_payload(
    result: ExhaustiveTeacherResult,
) -> dict[str, object]:
    """Return the complete canonical artifact payload for one owned invocation."""

    if isinstance(result, ExhaustiveTeacherCampaignResult):
        return {
            "contexts": tuple(_context_payload(context) for context in result.contexts),
            "digest": result.digest,
            "failure": None if result.failure is None else _failure_payload(result.failure),
            "panel_sha256": result.panel_sha256,
            "pool_sha256": result.pool_sha256,
            "public_call_count": result.public_highs_ds_invocation_count,
            "qualification_result_sha256": result.qualification_result_sha256,
            "result_type": "campaign_result",
            "schedule_sha256": result.schedule_sha256,
            "stop_reason": result.stop_reason.value,
            "teacher_source_sha256": result.teacher_source_sha256,
            "version": "adr0323-exhaustive-teacher-artifact-v1",
        }
    if not isinstance(result, ExhaustiveTeacherRunnerRejected):
        raise TypeError("teacher artifact requires a semantic runner result")
    return {
        "completed_contexts": tuple(
            _context_payload(context) for context in result.completed_contexts
        ),
        "current_task": (
            None if result.current_task is None else _task_payload(result.current_task)
        ),
        "digest": result.digest,
        "exception_chain": tuple(
            {
                "message": item.message,
                "module": item.module,
                "type_name": item.type_name,
            }
            for item in result.exception_chain
        ),
        "invocation_count_complete": result.invocation_count_complete,
        "known_public_call_count": result.known_public_highs_ds_invocation_count,
        "panel_sha256": result.panel_sha256,
        "pool_sha256": result.pool_sha256,
        "qualification_result_sha256": result.qualification_result_sha256,
        "reason": result.reason,
        "result_type": "runner_rejected",
        "schedule_sha256": result.schedule_sha256,
        "stage": result.stage.value,
        "teacher_source_sha256": result.teacher_source_sha256,
        "version": "adr0323-exhaustive-teacher-artifact-v1",
    }


def canonical_exhaustive_teacher_result_bytes(
    result: ExhaustiveTeacherResult,
) -> bytes:
    payload = exhaustive_teacher_result_payload(result)
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def retain_exhaustive_teacher_result(
    result: ExhaustiveTeacherResult,
    *,
    output_path: Path,
) -> tuple[str, int]:
    """No-clobber, atomically publish and byte-verify one canonical result."""

    if not isinstance(output_path, Path):
        raise TypeError("teacher artifact output path must be a Path")
    temporary = output_path.with_suffix(f"{output_path.suffix}.partial")
    if output_path.exists() or temporary.exists():
        raise FileExistsError("teacher artifact or staging path already exists")
    rendered = canonical_exhaustive_teacher_result_bytes(result)
    try:
        with temporary.open("xb") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output_path)
        persisted = output_path.read_bytes()
        if persisted != rendered:
            raise OSError("persisted teacher artifact differs from canonical bytes")
        temporary.unlink()
    except BaseException:
        # Preserve a partial or linked diagnostic; never overwrite or silently retry.
        raise
    return sha256(rendered).hexdigest(), len(rendered)


def run_and_retain_adr0323_exhaustive_development_teacher(
    *,
    output_path: Path,
) -> ExhaustiveTeacherResult:
    """Execute once only when both final and staging artifact paths are absent."""

    if not isinstance(output_path, Path):
        raise TypeError("teacher artifact output path must be a Path")
    temporary = output_path.with_suffix(f"{output_path.suffix}.partial")
    if output_path.exists() or temporary.exists():
        raise FileExistsError("teacher artifact or staging path already exists")
    if not output_path.parent.is_dir():
        raise FileNotFoundError("teacher artifact parent directory does not exist")
    with temporary.open("xb") as stream:
        stream.write(b"adr0323 exhaustive teacher invocation in progress\n")
        stream.flush()
        os.fsync(stream.fileno())
        result = run_adr0323_exhaustive_development_teacher()
        rendered = canonical_exhaustive_teacher_result_bytes(result)
        stream.seek(0)
        stream.truncate()
        stream.write(rendered)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, output_path)
    if output_path.read_bytes() != rendered:
        raise OSError("persisted teacher artifact differs from canonical bytes")
    temporary.unlink()
    return result


__all__ = [
    "ADR0323_EXHAUSTIVE_TEACHER_FULL_TASK_COUNT",
    "ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS",
    "ADR0323_EXHAUSTIVE_TEACHER_SUBSET_TASK_COUNT",
    "ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT",
    "ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE",
    "ExhaustiveTeacherArm",
    "ExhaustiveTeacherCampaignResult",
    "ExhaustiveTeacherFailure",
    "ExhaustiveTeacherFailureKind",
    "ExhaustiveTeacherFailureStage",
    "ExhaustiveTeacherResult",
    "ExhaustiveTeacherRunnerRejected",
    "ExhaustiveTeacherRunnerStage",
    "ExhaustiveTeacherSchedule",
    "ExhaustiveTeacherStopReason",
    "ExhaustiveTeacherTask",
    "NormalizedTeacherRegretInterval",
    "TeacherContextResult",
    "TeacherEquivalenceAllowance",
    "TeacherRunnerException",
    "TeacherSubsetCandidate",
    "TeacherSubsetObservation",
    "TeacherWidthEnvelope",
    "TeacherWidthResult",
    "build_adr0323_exhaustive_teacher_schedule",
    "build_teacher_subset_observation",
    "build_teacher_width_result",
    "canonical_exhaustive_teacher_result_bytes",
    "exhaustive_teacher_protocol_sha256",
    "exhaustive_teacher_result_payload",
    "exhaustive_teacher_tasks_for_context",
    "normalize_teacher_regret",
    "reduce_teacher_width",
    "retain_exhaustive_teacher_result",
    "run_adr0323_exhaustive_development_teacher",
    "run_and_retain_adr0323_exhaustive_development_teacher",
    "verify_adr0327_exhaustive_teacher_schedule",
    "verify_adr0327_teacher_source_and_dependencies",
]


def _execute_adr0323_exhaustive_development_teacher(
    *,
    teacher_source: str,
    pool: FreshActionWidthDevelopmentPool,
    schedule: ExhaustiveTeacherSchedule,
) -> ExhaustiveTeacherResult:
    contexts: list[TeacherContextResult] = []
    completed_widths: list[TeacherWidthResult] = []
    incomplete_observations: list[TeacherSubsetObservation] = []
    completed_full: CertifiedReducedSizingAcceptedV2 | None = None
    current_task = schedule.tasks[0]
    known_calls = 0
    try:
        for panel_position, pool_index in enumerate(
            ADR0323_QUALIFIED_POOL_INDICES
        ):
            context = pool.contexts[pool_index]
            context_tasks = tuple(
                task
                for task in schedule.tasks
                if task.panel_position == panel_position
            )
            full_task = context_tasks[0]
            current_task = full_task
            completed_full = None
            completed_widths = []
            incomplete_observations = []

            full_result = consume_certified_reduced_sizing_v2(full_task.request)
            if isinstance(
                full_result,
                (CertifiedReducedSizingAcceptedV2, CertifiedReducedSizingRejectedV2),
            ):
                known_calls += full_result.public_highs_ds_invocation_count
            if isinstance(full_result, CertifiedReducedSizingRejectedV2):
                return _campaign_result(
                    schedule=schedule,
                    teacher_source_sha256=teacher_source,
                    contexts=contexts,
                    stop_reason=ExhaustiveTeacherStopReason.CONSUMER_REJECTED,
                    failure=ExhaustiveTeacherFailure(
                        kind=ExhaustiveTeacherFailureKind.CONSUMER_REJECTION,
                        stage=ExhaustiveTeacherFailureStage.FULL_ARM,
                        task=full_task,
                        completed_full=None,
                        completed_width_results=(),
                        incomplete_subset_observations=(),
                        rejected=full_result,
                    ),
                )
            if not isinstance(full_result, CertifiedReducedSizingAcceptedV2):
                raise TypeError("teacher full arm returned a nonsemantic result")
            _verify_accepted_task(full_result, full_task)
            completed_full = full_result

            subset_tasks = context_tasks[1:]
            task_offset = 0
            for width in ADR0323_RAISE_WIDTHS:
                width_tasks = tuple(
                    task for task in subset_tasks if task.raise_width == width
                )
                if subset_tasks[task_offset : task_offset + len(width_tasks)] != width_tasks:
                    raise ValueError("teacher execution schedule lost width order")
                task_offset += len(width_tasks)
                incomplete_observations = []
                for subset_task in width_tasks:
                    current_task = subset_task
                    subset_result = consume_certified_reduced_sizing_v2(
                        subset_task.request
                    )
                    if isinstance(
                        subset_result,
                        (
                            CertifiedReducedSizingAcceptedV2,
                            CertifiedReducedSizingRejectedV2,
                        ),
                    ):
                        known_calls += subset_result.public_highs_ds_invocation_count
                    if isinstance(subset_result, CertifiedReducedSizingRejectedV2):
                        return _campaign_result(
                            schedule=schedule,
                            teacher_source_sha256=teacher_source,
                            contexts=contexts,
                            stop_reason=(
                                ExhaustiveTeacherStopReason.CONSUMER_REJECTED
                            ),
                            failure=ExhaustiveTeacherFailure(
                                kind=(
                                    ExhaustiveTeacherFailureKind.CONSUMER_REJECTION
                                ),
                                stage=ExhaustiveTeacherFailureStage.SUBSET_ARM,
                                task=subset_task,
                                completed_full=full_result,
                                completed_width_results=tuple(completed_widths),
                                incomplete_subset_observations=tuple(
                                    incomplete_observations
                                ),
                                rejected=subset_result,
                            ),
                        )
                    if not isinstance(
                        subset_result,
                        CertifiedReducedSizingAcceptedV2,
                    ):
                        raise TypeError("teacher subset arm returned a nonsemantic result")
                    _verify_accepted_task(subset_result, subset_task)
                    try:
                        observation = build_teacher_subset_observation(
                            task=subset_task,
                            full=full_result,
                            accepted=subset_result,
                            payoff_span_chips=context.payoff_span_chips,
                        )
                    except (ArithmeticError, ValueError) as error:
                        return _campaign_result(
                            schedule=schedule,
                            teacher_source_sha256=teacher_source,
                            contexts=contexts,
                            stop_reason=(
                                ExhaustiveTeacherStopReason.NUMERICAL_REJECTED
                            ),
                            failure=ExhaustiveTeacherFailure(
                                kind=(
                                    ExhaustiveTeacherFailureKind.NUMERICAL_REJECTION
                                ),
                                stage=ExhaustiveTeacherFailureStage.SUBSET_REGRET,
                                task=subset_task,
                                completed_full=full_result,
                                completed_width_results=tuple(completed_widths),
                                incomplete_subset_observations=tuple(
                                    incomplete_observations
                                ),
                                accepted_at_failure=subset_result,
                                exception_chain=_exception_chain(error),
                            ),
                        )
                    incomplete_observations.append(observation)

                try:
                    width_result = build_teacher_width_result(
                        raise_width=width,
                        full=full_result,
                        payoff_span_chips=context.payoff_span_chips,
                        subset_observations=tuple(incomplete_observations),
                    )
                except (ArithmeticError, ValueError) as error:
                    return _campaign_result(
                        schedule=schedule,
                        teacher_source_sha256=teacher_source,
                        contexts=contexts,
                        stop_reason=ExhaustiveTeacherStopReason.NUMERICAL_REJECTED,
                        failure=ExhaustiveTeacherFailure(
                            kind=ExhaustiveTeacherFailureKind.NUMERICAL_REJECTION,
                            stage=ExhaustiveTeacherFailureStage.WIDTH_REDUCTION,
                            task=current_task,
                            completed_full=full_result,
                            completed_width_results=tuple(completed_widths),
                            incomplete_subset_observations=tuple(
                                incomplete_observations
                            ),
                            exception_chain=_exception_chain(error),
                        ),
                    )
                completed_widths.append(width_result)
                incomplete_observations = []

            if task_offset != len(subset_tasks):
                raise ValueError("teacher execution did not consume every subset task")

            context_result = TeacherContextResult(
                panel_position=panel_position,
                pool_index=pool_index,
                context_semantic_digest=context.semantic_digest,
                payoff_span_chips=context.payoff_span_chips,
                full_task=full_task,
                full=full_result,
                widths=tuple(completed_widths),
            )
            contexts.append(context_result)
            completed_full = None
            completed_widths = []
            incomplete_observations = []

        return _campaign_result(
            schedule=schedule,
            teacher_source_sha256=teacher_source,
            contexts=contexts,
            stop_reason=ExhaustiveTeacherStopReason.COMPLETED,
        )
    except Exception as error:
        return ExhaustiveTeacherRunnerRejected(
            stage=ExhaustiveTeacherRunnerStage.EXECUTION,
            reason="teacher runner failed outside a typed campaign stop",
            pool_sha256=schedule.pool_sha256,
            qualification_result_sha256=schedule.qualification_result_sha256,
            panel_sha256=schedule.panel_sha256,
            schedule_sha256=schedule.digest,
            teacher_source_sha256=teacher_source,
            completed_contexts=tuple(contexts),
            current_task=current_task,
            known_public_highs_ds_invocation_count=known_calls,
            invocation_count_complete=False,
            exception_chain=_exception_chain(error),
        )
