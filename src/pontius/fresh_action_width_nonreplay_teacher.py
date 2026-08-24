"""Source-only exhaustive teacher for ADR-0334's non-replay panel.

The prospective value owner writes and fsyncs every arm before another call.
Its solver-free reader independently reconstructs accepted value witnesses,
conservative regrets, set-valued teacher envelopes, and the terminal state.
This module can exercise the complete protocol synthetically without opening a
teacher value and emits no betting action.
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
    CertifiedSizingConsumerRejectionReasonV2,
    CertifiedSizingConsumerStageV2,
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
    recover_journal_bytes,
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
from .fresh_action_width_nonreplay_qualification_seal import (
    ADR0331_QUALIFICATION_SCHEDULE_SHA256,
)
from .fresh_action_width_nonreplay_seal import ADR0331_POPULATION_POOL_SHA256
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    certified_full_minus_subset_regret,
)
from .fresh_action_width_structures import ADR0323_RAISE_WIDTHS, RaiseActionWidth
from .fresh_action_width_teacher import (
    ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    ExhaustiveTeacherArm,
    ExhaustiveTeacherTask,
    NormalizedTeacherRegretInterval,
    TeacherSubsetCandidate,
    TeacherWidthEnvelope,
    exhaustive_teacher_tasks_for_context,
    normalize_teacher_regret,
    reduce_teacher_width,
)


ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/"
    "fresh-action-width-nonreplay-exhaustive-teacher-v1.jsonl"
)
ADR0335_TEACHER_FULL_TASK_COUNT = 16
ADR0335_TEACHER_SUBSET_COUNTS = (
    (2, 16),
    (3, 114),
    (4, 367),
    (5, 705),
    (6, 895),
)
ADR0335_TEACHER_SUBSET_TASK_COUNT = 2_097
ADR0335_TEACHER_TASK_COUNT = 2_113

_SCHEDULE_VERSION = "adr0335-nonreplay-exhaustive-teacher-schedule-v1"
_HEADER_VERSION = "adr0335-nonreplay-exhaustive-teacher-header-v1"
_EVIDENCE_VERSION = "adr0335-nonreplay-exhaustive-teacher-arm-evidence-v1"
_TERMINAL_VERSION = "adr0335-nonreplay-exhaustive-teacher-terminal-v1"


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
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} exceeds its maximum")
    return value


def _validate_exception_descriptors(
    value: object,
    *,
    label: str,
    optional: bool = False,
) -> None:
    if optional and value == ():
        return
    if not isinstance(value, tuple) or not value:
        raise TypeError(f"{label} requires an immutable nonempty exception chain")
    for item in value:
        if not isinstance(item, dict) or frozenset(item) != frozenset(
            {"message", "module", "type_name"}
        ):
            raise ValueError(f"{label} exception descriptor is malformed")
        if (
            not isinstance(item["module"], str)
            or not item["module"]
            or not isinstance(item["type_name"], str)
            or not item["type_name"]
            or not isinstance(item["message"], str)
        ):
            raise ValueError(f"{label} exception descriptor fields are invalid")


def _sealed_payload(
    core: Mapping[str, object],
    *,
    digest_field: str,
) -> dict[str, object]:
    if digest_field in core:
        raise ValueError("self-free core already contains its digest")
    digest = sha256(canonical_journal_json_bytes(core)).hexdigest()
    return {**core, digest_field: digest}


def _verify_sealed_payload(
    payload: dict[str, object],
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if digest_field not in payload:
        raise ValueError(f"{label} lacks its digest")
    claimed = _require_digest(payload[digest_field], label=f"{label} digest")
    core = {key: value for key, value in payload.items() if key != digest_field}
    actual = sha256(canonical_journal_json_bytes(core)).hexdigest()
    if claimed != actual:
        raise ValueError(f"{label} digest differs from its self-free core")
    return core


@dataclass(frozen=True, slots=True)
class NonReplayExhaustiveTeacherSchedule:
    pool_sha256: str
    qualification_schedule_sha256: str
    qualification_journal_sha256: str
    qualification_terminal_sha256: str
    panel_sha256: str
    tasks: tuple[ExhaustiveTeacherTask, ...]
    subset_counts_by_raise_width: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("teacher schedule pool", self.pool_sha256),
            ("teacher schedule qualification schedule", self.qualification_schedule_sha256),
            ("teacher schedule qualification journal", self.qualification_journal_sha256),
            ("teacher schedule qualification terminal", self.qualification_terminal_sha256),
            ("teacher schedule panel", self.panel_sha256),
        ):
            _require_digest(value, label=label)
        if (
            self.pool_sha256 != ADR0331_POPULATION_POOL_SHA256
            or self.qualification_schedule_sha256
            != ADR0331_QUALIFICATION_SCHEDULE_SHA256
            or self.qualification_journal_sha256
            != ADR0334_QUALIFICATION_ARTIFACT_SHA256
            or self.qualification_terminal_sha256
            != ADR0334_QUALIFICATION_TERMINAL_SHA256
            or self.panel_sha256 != ADR0334_QUALIFIED_PANEL_SHA256
        ):
            raise ValueError("teacher schedule belongs to another qualification panel")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0335_TEACHER_TASK_COUNT
            or any(not isinstance(task, ExhaustiveTeacherTask) for task in self.tasks)
        ):
            raise TypeError("teacher schedule requires 2,113 immutable tasks")
        if tuple(task.ordinal for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("teacher schedule task ordinals are not contiguous")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("teacher schedule repeats a semantic task")
        if len({task.request_sha256 for task in self.tasks}) != len(self.tasks):
            raise ValueError("teacher schedule repeats an exact request")
        if tuple(task.panel_position for task in self.tasks) != tuple(
            sorted(task.panel_position for task in self.tasks)
        ):
            raise ValueError("teacher schedule contexts are not contiguous")
        if sum(
            task.arm is ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE
            for task in self.tasks
        ) != ADR0335_TEACHER_FULL_TASK_COUNT:
            raise ValueError("teacher schedule has the wrong full-arm count")
        if self.subset_counts_by_raise_width != ADR0335_TEACHER_SUBSET_COUNTS:
            raise ValueError("teacher schedule subset work differs from ADR-0334")
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
            for width, _ in ADR0335_TEACHER_SUBSET_COUNTS
        )
        if observed_counts != self.subset_counts_by_raise_width:
            raise ValueError("teacher schedule task counts differ from its ledger")
        for panel_position, (pool_index, context_digest) in enumerate(
            zip(
                ADR0334_QUALIFIED_POOL_INDICES,
                ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
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
                task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET
                for task in context_tasks[1:]
            ):
                raise ValueError("teacher context contains an extra full arm")
            if any(
                task.pool_index != pool_index
                or task.context_semantic_digest != context_digest
                for task in context_tasks
            ):
                raise ValueError("teacher context tasks differ from panel membership")
            observed_order = tuple(
                (task.raise_width.count, task.subset_index)
                for task in context_tasks[1:]
                if task.raise_width is not None
            )
            if len(observed_order) != len(context_tasks) - 1:
                raise ValueError("teacher subset lost its width")
            expected_order = tuple(
                (width, index)
                for width in range(2, 7)
                for index in range(
                    sum(
                        task.raise_width is not None
                        and task.raise_width.count == width
                        for task in context_tasks[1:]
                    )
                )
            )
            if observed_order != expected_order:
                raise ValueError("teacher subsets are not width/lexicographic ordered")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "panel_sha256": self.panel_sha256,
                    "pool_sha256": self.pool_sha256,
                    "qualification_journal_sha256": self.qualification_journal_sha256,
                    "qualification_schedule_sha256": self.qualification_schedule_sha256,
                    "qualification_terminal_sha256": self.qualification_terminal_sha256,
                    "subset_counts_by_raise_width": self.subset_counts_by_raise_width,
                    "task_digests": tuple(task.digest for task in self.tasks),
                    "version": _SCHEDULE_VERSION,
                }
            )
        ).hexdigest()


def build_adr0334_nonreplay_exhaustive_teacher_schedule(
) -> NonReplayExhaustiveTeacherSchedule:
    """Build all value-free tasks from the exact retained target-only panel."""

    retained = verify_adr0334_nonreplay_qualification_result_artifact()
    pool = build_adr0331_nonreplay_pool()
    if (
        pool.digest != ADR0331_POPULATION_POOL_SHA256
        or retained.panel.digest != ADR0334_QUALIFIED_PANEL_SHA256
    ):
        raise RuntimeError("ADR-0334 teacher inputs drifted")
    tasks: list[ExhaustiveTeacherTask] = []
    for panel_position, pool_index in enumerate(retained.panel.pool_indices):
        tasks.extend(
            exhaustive_teacher_tasks_for_context(
                context=pool.contexts[pool_index],
                panel_position=panel_position,
                pool_index=pool_index,
                start_ordinal=len(tasks),
            )
        )
    return NonReplayExhaustiveTeacherSchedule(
        pool_sha256=pool.digest,
        qualification_schedule_sha256=ADR0331_QUALIFICATION_SCHEDULE_SHA256,
        qualification_journal_sha256=retained.journal.journal_sha256,
        qualification_terminal_sha256=retained.journal.terminal_sha256,
        panel_sha256=retained.panel.digest,
        tasks=tuple(tasks),
        subset_counts_by_raise_width=ADR0335_TEACHER_SUBSET_COUNTS,
    )


class NonReplayTeacherEvidenceKind(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


_EVIDENCE_CORE_KEYS = frozenset(
    {
        "arm",
        "context_semantic_sha256",
        "kind",
        "panel_position",
        "pool_index",
        "result",
        "synthetic",
        "task_index",
        "task_sha256",
        "version",
    }
)


@dataclass(frozen=True, slots=True)
class NonReplayTeacherArmEvidence:
    task_index: int
    task_sha256: str
    kind: NonReplayTeacherEvidenceKind
    synthetic: bool
    core_canonical_json: bytes

    def __post_init__(self) -> None:
        _require_count(
            self.task_index,
            label="teacher evidence task index",
            maximum=ADR0335_TEACHER_TASK_COUNT - 1,
        )
        _require_digest(self.task_sha256, label="teacher evidence task")
        if not isinstance(self.kind, NonReplayTeacherEvidenceKind):
            raise TypeError("teacher evidence kind must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("teacher evidence synthetic flag must be Boolean")
        if not isinstance(self.core_canonical_json, bytes):
            raise TypeError("teacher evidence core bytes must be immutable")
        value = json.loads(self.core_canonical_json)
        if (
            not isinstance(value, dict)
            or frozenset(value) != _EVIDENCE_CORE_KEYS
            or canonical_journal_json_bytes(value) != self.core_canonical_json
        ):
            raise ValueError("teacher evidence core is not canonical")
        if (
            value.get("task_index") != self.task_index
            or value.get("task_sha256") != self.task_sha256
            or value.get("kind") != self.kind.value
            or value.get("synthetic") is not self.synthetic
            or value.get("version") != _EVIDENCE_VERSION
        ):
            raise ValueError("teacher evidence metadata differs from its core")

    @property
    def core(self) -> dict[str, object]:
        value = json.loads(self.core_canonical_json)
        if not isinstance(value, dict):
            raise AssertionError("teacher evidence core lost its object type")
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
            raise AssertionError("teacher evidence result lost its object type")
        if self.kind is NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION:
            return 0
        return _require_count(
            result["public_call_count"],
            label="teacher evidence public calls",
            maximum=1,
        )

    @property
    def value(self) -> CertifiedChipValueInterval:
        if self.kind is not NonReplayTeacherEvidenceKind.ACCEPTED:
            raise ValueError("only accepted teacher evidence has a value")
        result = self.core["result"]
        if not isinstance(result, dict):
            raise AssertionError("teacher accepted result lost its object type")
        return CertifiedChipValueInterval(
            lower_chips=_require_float_hex(
                result["feasible_lower_hex"],
                label="teacher accepted lower",
            ),
            upper_chips=_require_float_hex(
                result["certified_upper_hex"],
                label="teacher accepted upper",
            ),
        )


def _build_evidence(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
    kind: NonReplayTeacherEvidenceKind,
    synthetic: bool,
    result_payload: Mapping[str, object],
) -> NonReplayTeacherArmEvidence:
    if not isinstance(task, ExhaustiveTeacherTask):
        raise TypeError("teacher evidence requires a semantic task")
    core = {
        "arm": task.arm.value,
        "context_semantic_sha256": task.context_semantic_digest,
        "kind": kind.value,
        "panel_position": task.panel_position,
        "pool_index": task.pool_index,
        "result": result_payload,
        "synthetic": synthetic,
        "task_index": task_index,
        "task_sha256": task.digest,
        "version": _EVIDENCE_VERSION,
    }
    return NonReplayTeacherArmEvidence(
        task_index=task_index,
        task_sha256=task.digest,
        kind=kind,
        synthetic=synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )


def teacher_evidence_from_consumer_result(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
    result: object,
) -> NonReplayTeacherArmEvidence:
    if isinstance(result, CertifiedReducedSizingAcceptedV2):
        if result.request != task.request:
            raise ValueError("accepted teacher evidence belongs to another task")
        return _build_evidence(
            task_index=task_index,
            task=task,
            kind=NonReplayTeacherEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=_accepted_result_payload(result),
        )
    if isinstance(result, CertifiedReducedSizingRejectedV2):
        if result.request != task.request:
            raise ValueError("rejected teacher evidence belongs to another task")
        return _build_evidence(
            task_index=task_index,
            task=task,
            kind=NonReplayTeacherEvidenceKind.REJECTED,
            synthetic=False,
            result_payload=_rejected_result_payload(result),
        )
    raise TypeError("teacher consumer returned a nonsemantic result")


def _unexpected_evidence(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
    error: Exception,
    synthetic: bool,
) -> NonReplayTeacherArmEvidence:
    return _build_evidence(
        task_index=task_index,
        task=task,
        kind=NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION,
        synthetic=synthetic,
        result_payload={
            "exception_chain": _exception_payload(error),
            "invocation_count_complete": False,
            "synthetic_result": synthetic,
            "type": "unexpected_exception",
        },
    )


def _validate_evidence_against_task(
    evidence: NonReplayTeacherArmEvidence,
    *,
    task: ExhaustiveTeacherTask,
    expect_synthetic: bool,
) -> None:
    core = evidence.core
    if (
        evidence.task_index != task.ordinal
        or evidence.task_sha256 != task.digest
        or evidence.synthetic is not expect_synthetic
        or core["arm"] != task.arm.value
        or core["panel_position"] != task.panel_position
        or core["pool_index"] != task.pool_index
        or core["context_semantic_sha256"] != task.context_semantic_digest
    ):
        raise ValueError("teacher evidence differs from its scheduled task")
    result = core["result"]
    if not isinstance(result, dict):
        raise TypeError("teacher evidence result must be an object")
    if result.get("synthetic_result") is not expect_synthetic:
        raise ValueError("teacher evidence synthetic provenance drifted")

    if evidence.kind is NonReplayTeacherEvidenceKind.ACCEPTED:
        accepted = _require_exact_keys(
            result,
            _ACCEPTED_RESULT_KEYS,
            label="accepted teacher evidence",
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
            raise ValueError("accepted teacher evidence identity drifted")
        lower = _require_float_hex(
            accepted["feasible_lower_hex"],
            label="accepted teacher lower",
        )
        upper = _require_float_hex(
            accepted["certified_upper_hex"],
            label="accepted teacher upper",
        )
        signed_gap = _require_float_hex(
            accepted["signed_gap_hex"],
            label="accepted teacher signed gap",
        )
        gap = _require_float_hex(
            accepted["certified_gap_hex"],
            label="accepted teacher gap",
        )
        if (
            lower > upper
            or signed_gap != upper - lower
            or gap != max(0.0, signed_gap)
        ):
            raise ValueError("accepted teacher evidence interval drifted")
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
            raise ValueError("accepted teacher response evidence is malformed")
        multipliers_value = accepted["raw_inequality_multipliers_hex"]
        if not isinstance(multipliers_value, list):
            raise TypeError("accepted teacher multipliers must be an array")
        multipliers = tuple(
            _require_float_hex(item, label="accepted teacher multiplier")
            for item in multipliers_value
        )
        expected_multiplier_count = (
            2 * len(task.request.joint_probabilities)
            + 2
            * len(task.request.joint_probabilities[0])
            * len(task.request.legal_raise_to_totals)
        )
        if len(multipliers) != expected_multiplier_count:
            raise ValueError("accepted teacher multiplier width drifted")
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
                raise ValueError("accepted teacher certificate width drifted")
    elif evidence.kind is NonReplayTeacherEvidenceKind.REJECTED:
        rejected = _require_exact_keys(
            result,
            _REJECTED_RESULT_KEYS,
            label="rejected teacher evidence",
        )
        if (
            rejected["type"] != "rejected"
            or rejected["context_label"] != task.request.context_id
            or rejected["consumer_protocol_sha256"]
            != ADR0321_CONSUMER_PROTOCOL_SHA256
            or rejected["stage"]
            not in {value.value for value in CertifiedSizingConsumerStageV2}
            or rejected["reason"]
            not in {
                value.value for value in CertifiedSizingConsumerRejectionReasonV2
            }
            or rejected["fallback_disposition"]
            != CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            or rejected["emitted_action"] is not None
        ):
            raise ValueError("rejected teacher evidence identity drifted")
        calls = _require_count(
            rejected["public_call_count"],
            label="rejected teacher public calls",
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
                label=f"rejected teacher {key}",
                optional=True,
            )
        _validate_exception_chain(
            rejected["exception_chain"],
            label="rejected teacher evidence",
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
            raise ValueError("rejected teacher stage/reason contract drifted")
        bound = _bind_request(task.request)
        if (
            rejected["request_sha256"] != bound.request_sha256
            or rejected["public_state_sha256"] != bound.public_state_sha256
            or rejected["legal_raise_set_sha256"] != bound.legal_raise_set_sha256
        ):
            raise ValueError("rejected teacher request identity drifted")
        source_expected = stage is not CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION
        if rejected["consumer_source_sha256"] != (
            ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ]
            if source_expected
            else None
        ):
            raise ValueError("rejected teacher source identity drifted")
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
            raise ValueError("rejected teacher invocation count drifted")
    else:
        unexpected = _require_exact_keys(
            result,
            _UNEXPECTED_RESULT_KEYS,
            label="unexpected teacher evidence",
        )
        if (
            unexpected["type"] != "unexpected_exception"
            or unexpected["invocation_count_complete"] is not False
        ):
            raise ValueError("unexpected teacher evidence claims complete calls")
        _validate_exception_chain(
            unexpected["exception_chain"],
            label="unexpected teacher evidence",
        )


def _rebind_evidence(
    payload: dict[str, object],
    *,
    task: ExhaustiveTeacherTask,
    task_index: int,
    expect_synthetic: bool,
) -> NonReplayTeacherArmEvidence:
    core = _verify_sealed_payload(
        payload,
        digest_field="evidence_sha256",
        label=f"teacher arm {task_index}",
    )
    try:
        kind = NonReplayTeacherEvidenceKind(core["kind"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("teacher evidence has an unknown kind") from error
    evidence = NonReplayTeacherArmEvidence(
        task_index=task_index,
        task_sha256=task.digest,
        kind=kind,
        synthetic=expect_synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )
    _validate_evidence_against_task(
        evidence,
        task=task,
        expect_synthetic=expect_synthetic,
    )
    return evidence


@dataclass(frozen=True, slots=True)
class NonReplayTeacherSubsetObservation:
    task_index: int
    task: ExhaustiveTeacherTask
    evidence_sha256: str
    full_evidence_sha256: str
    full_value: CertifiedChipValueInterval
    subset_value: CertifiedChipValueInterval
    payoff_span_chips: int
    regret: CertifiedChipRegretInterval
    normalized_regret: NormalizedTeacherRegretInterval

    def __post_init__(self) -> None:
        _require_count(
            self.task_index,
            label="teacher subset observation task index",
            maximum=ADR0335_TEACHER_TASK_COUNT - 1,
        )
        if (
            not isinstance(self.task, ExhaustiveTeacherTask)
            or self.task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET
            or self.task.ordinal != self.task_index
        ):
            raise TypeError("teacher subset observation requires its subset task")
        _require_digest(self.evidence_sha256, label="teacher subset evidence")
        _require_digest(self.full_evidence_sha256, label="teacher full evidence")
        if not isinstance(self.full_value, CertifiedChipValueInterval) or not isinstance(
            self.subset_value,
            CertifiedChipValueInterval,
        ):
            raise TypeError("teacher subset observation requires value intervals")
        expected_regret = certified_full_minus_subset_regret(
            full=self.full_value,
            subset=self.subset_value,
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
        return sha256(
            canonical_journal_json_bytes(
                {
                    "evidence_sha256": self.evidence_sha256,
                    "full_evidence_sha256": self.full_evidence_sha256,
                    "full_value": (
                        self.full_value.lower_chips.hex(),
                        self.full_value.upper_chips.hex(),
                    ),
                    "normalized_regret": (
                        self.normalized_regret.lower.hex(),
                        self.normalized_regret.upper.hex(),
                    ),
                    "payoff_span_chips": self.payoff_span_chips,
                    "regret": (
                        self.regret.nonnegative_lower_chips.hex(),
                        self.regret.nonnegative_upper_chips.hex(),
                        self.regret.signed_lower_chips.hex(),
                        self.regret.signed_upper_chips.hex(),
                    ),
                    "subset_value": (
                        self.subset_value.lower_chips.hex(),
                        self.subset_value.upper_chips.hex(),
                    ),
                    "task_sha256": self.task.digest,
                    "version": "adr0335-nonreplay-teacher-subset-observation-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class NonReplayTeacherWidthResult:
    raise_width: RaiseActionWidth
    full_evidence_sha256: str
    full_value: CertifiedChipValueInterval
    payoff_span_chips: int
    subset_observations: tuple[NonReplayTeacherSubsetObservation, ...]
    envelope: TeacherWidthEnvelope
    full_minus_teacher_regret: CertifiedChipRegretInterval
    normalized_full_minus_teacher_regret: NormalizedTeacherRegretInterval

    def __post_init__(self) -> None:
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("teacher width result requires a raise width")
        _require_digest(self.full_evidence_sha256, label="teacher width full evidence")
        if not isinstance(self.full_value, CertifiedChipValueInterval):
            raise TypeError("teacher width result requires its full value")
        if (
            not isinstance(self.subset_observations, tuple)
            or not self.subset_observations
            or any(
                not isinstance(item, NonReplayTeacherSubsetObservation)
                for item in self.subset_observations
            )
        ):
            raise TypeError("teacher width result requires immutable observations")
        expected_indices = tuple(range(len(self.subset_observations)))
        if any(
            item.task.subset_index is None for item in self.subset_observations
        ):
            raise ValueError("teacher width observation lost its subset index")
        if tuple(
            item.task.subset_index for item in self.subset_observations
        ) != expected_indices:
            raise ValueError("teacher width observations lost subset order")
        if any(
            item.task.raise_width != self.raise_width
            or item.full_evidence_sha256 != self.full_evidence_sha256
            or item.full_value != self.full_value
            or item.payoff_span_chips != self.payoff_span_chips
            for item in self.subset_observations
        ):
            raise ValueError("teacher width observations differ from their width")
        expected_envelope = reduce_teacher_width(
            tuple(
                TeacherSubsetCandidate(
                    subset_index=item.task.subset_index,  # type: ignore[arg-type]
                    raise_to_totals=item.task.raise_to_totals,
                    value=item.subset_value,
                )
                for item in self.subset_observations
            ),
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
            raise ValueError("teacher width reduction drifted")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "envelope": {
                        "equivalent_subset_indices": (
                            self.envelope.equivalent_subset_indices
                        ),
                        "lower_hex": self.envelope.value.lower_chips.hex(),
                        "nondominated_subset_indices": (
                            self.envelope.nondominated_subset_indices
                        ),
                        "unique_best_subset_index": (
                            self.envelope.unique_best_subset_index
                        ),
                        "upper_hex": self.envelope.value.upper_chips.hex(),
                    },
                    "full_evidence_sha256": self.full_evidence_sha256,
                    "full_minus_teacher_regret": (
                        self.full_minus_teacher_regret.nonnegative_lower_chips.hex(),
                        self.full_minus_teacher_regret.nonnegative_upper_chips.hex(),
                        self.full_minus_teacher_regret.signed_lower_chips.hex(),
                        self.full_minus_teacher_regret.signed_upper_chips.hex(),
                    ),
                    "full_value": (
                        self.full_value.lower_chips.hex(),
                        self.full_value.upper_chips.hex(),
                    ),
                    "normalized_full_minus_teacher_regret": (
                        self.normalized_full_minus_teacher_regret.lower.hex(),
                        self.normalized_full_minus_teacher_regret.upper.hex(),
                    ),
                    "payoff_span_chips": self.payoff_span_chips,
                    "raise_width": self.raise_width.count,
                    "subset_observation_sha256s": tuple(
                        item.digest for item in self.subset_observations
                    ),
                    "version": "adr0335-nonreplay-teacher-width-result-v1",
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class NonReplayTeacherContextResult:
    panel_position: int
    pool_index: int
    context_semantic_sha256: str
    payoff_span_chips: int
    full_task_sha256: str
    full_evidence_sha256: str
    full_value: CertifiedChipValueInterval
    widths: tuple[NonReplayTeacherWidthResult, ...]

    def __post_init__(self) -> None:
        panel_position = _require_count(
            self.panel_position,
            label="teacher context panel position",
            maximum=15,
        )
        _require_count(self.pool_index, label="teacher context pool index", maximum=95)
        _require_digest(self.context_semantic_sha256, label="teacher context semantic")
        _require_digest(self.full_task_sha256, label="teacher context full task")
        _require_digest(self.full_evidence_sha256, label="teacher context full evidence")
        if (
            self.pool_index != ADR0334_QUALIFIED_POOL_INDICES[panel_position]
            or self.context_semantic_sha256
            != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S[panel_position]
        ):
            raise ValueError("teacher context differs from the target-only panel")
        if not isinstance(self.full_value, CertifiedChipValueInterval):
            raise TypeError("teacher context requires its full value")
        if not isinstance(self.widths, tuple) or any(
            not isinstance(item, NonReplayTeacherWidthResult)
            for item in self.widths
        ):
            raise TypeError("teacher context requires immutable width results")
        if (
            tuple(item.raise_width for item in self.widths)
            != ADR0323_RAISE_WIDTHS
            or any(
                item.full_evidence_sha256 != self.full_evidence_sha256
                or item.full_value != self.full_value
                or item.payoff_span_chips != self.payoff_span_chips
                for item in self.widths
            )
        ):
            raise ValueError("teacher context width reductions are incomplete")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "context_semantic_sha256": self.context_semantic_sha256,
                    "full_evidence_sha256": self.full_evidence_sha256,
                    "full_task_sha256": self.full_task_sha256,
                    "full_value": (
                        self.full_value.lower_chips.hex(),
                        self.full_value.upper_chips.hex(),
                    ),
                    "panel_position": self.panel_position,
                    "payoff_span_chips": self.payoff_span_chips,
                    "pool_index": self.pool_index,
                    "version": "adr0335-nonreplay-teacher-context-result-v1",
                    "width_result_sha256s": tuple(item.digest for item in self.widths),
                }
            )
        ).hexdigest()


class NonReplayTeacherStopReason(StrEnum):
    COMPLETED = "completed"
    CONSUMER_REJECTED = "consumer_rejected"
    NESTED_VALUE_REVERSAL = "nested_value_reversal"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


@dataclass(frozen=True, slots=True)
class _DerivedTeacherState:
    evidences: tuple[NonReplayTeacherArmEvidence, ...]
    contexts: tuple[NonReplayTeacherContextResult, ...]
    completed_widths: tuple[NonReplayTeacherWidthResult, ...]
    incomplete_observations: tuple[NonReplayTeacherSubsetObservation, ...]
    pending_full_evidence: NonReplayTeacherArmEvidence | None
    stop_reason: NonReplayTeacherStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool

    @property
    def pending_full_evidence_sha256(self) -> str | None:
        return (
            None
            if self.pending_full_evidence is None
            else self.pending_full_evidence.digest
        )


class _NestedValueReversalDetected(ValueError):
    """Internal distinction between a value reversal and structural invalidity."""


def _build_subset_observation(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
    evidence: NonReplayTeacherArmEvidence,
    full_evidence: NonReplayTeacherArmEvidence,
    payoff_span_chips: int,
) -> NonReplayTeacherSubsetObservation:
    try:
        regret = certified_full_minus_subset_regret(
            full=full_evidence.value,
            subset=evidence.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
    except ValueError as error:
        raise _NestedValueReversalDetected from error
    return NonReplayTeacherSubsetObservation(
        task_index=task_index,
        task=task,
        evidence_sha256=evidence.digest,
        full_evidence_sha256=full_evidence.digest,
        full_value=full_evidence.value,
        subset_value=evidence.value,
        payoff_span_chips=payoff_span_chips,
        regret=regret,
        normalized_regret=normalize_teacher_regret(
            regret,
            payoff_span_chips=payoff_span_chips,
        ),
    )


def _build_width_result(
    *,
    raise_width: RaiseActionWidth,
    full_evidence: NonReplayTeacherArmEvidence,
    payoff_span_chips: int,
    observations: tuple[NonReplayTeacherSubsetObservation, ...],
) -> NonReplayTeacherWidthResult:
    if any(item.task.subset_index is None for item in observations):
        raise ValueError("teacher width input lost its subset index")
    envelope = reduce_teacher_width(
        tuple(
            TeacherSubsetCandidate(
                subset_index=item.task.subset_index,  # type: ignore[arg-type]
                raise_to_totals=item.task.raise_to_totals,
                value=item.subset_value,
            )
            for item in observations
        ),
        raise_width=raise_width,
        equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    )
    try:
        regret = certified_full_minus_subset_regret(
            full=full_evidence.value,
            subset=envelope.value,
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
    except ValueError as error:
        raise _NestedValueReversalDetected from error
    return NonReplayTeacherWidthResult(
        raise_width=raise_width,
        full_evidence_sha256=full_evidence.digest,
        full_value=full_evidence.value,
        payoff_span_chips=payoff_span_chips,
        subset_observations=observations,
        envelope=envelope,
        full_minus_teacher_regret=regret,
        normalized_full_minus_teacher_regret=normalize_teacher_regret(
            regret,
            payoff_span_chips=payoff_span_chips,
        ),
    )


def _empty_derived_state() -> _DerivedTeacherState:
    return _DerivedTeacherState(
        evidences=(),
        contexts=(),
        completed_widths=(),
        incomplete_observations=(),
        pending_full_evidence=None,
        stop_reason=None,
        known_public_call_count=0,
        invocation_count_complete=True,
    )


def _advance_state(
    state: _DerivedTeacherState,
    evidence: NonReplayTeacherArmEvidence,
    *,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayExhaustiveTeacherSchedule,
) -> _DerivedTeacherState:
    task_index = len(state.evidences)
    if evidence.task_index != task_index:
        raise ValueError("teacher evidence is not a contiguous task prefix")
    if state.stop_reason is not None:
        raise ValueError("teacher evidence continues past a terminal stop")
    if task_index >= len(schedule.tasks):
        raise ValueError("teacher evidence exceeds its sealed task schedule")
    task = schedule.tasks[task_index]
    contexts = list(state.contexts)
    completed_widths = list(state.completed_widths)
    incomplete = list(state.incomplete_observations)
    pending_full = state.pending_full_evidence
    stop: NonReplayTeacherStopReason | None = None
    known_calls = state.known_public_call_count
    complete_calls = state.invocation_count_complete
    evidences = state.evidences + (evidence,)

    if evidence.kind is NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION:
        stop = NonReplayTeacherStopReason.UNEXPECTED_EXCEPTION
        complete_calls = False
    else:
        known_calls += evidence.public_call_count
        if evidence.kind is NonReplayTeacherEvidenceKind.REJECTED:
            stop = NonReplayTeacherStopReason.CONSUMER_REJECTED
        elif task.arm is ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE:
            if pending_full is not None or completed_widths or incomplete:
                raise ValueError("teacher full arm began before prior context closed")
            pending_full = evidence
        else:
            if pending_full is None or task.panel_position != len(contexts):
                raise ValueError("teacher subset lacks its exact full arm")
            context = pool.contexts[task.pool_index]
            try:
                observation = _build_subset_observation(
                    task_index=task_index,
                    task=task,
                    evidence=evidence,
                    full_evidence=pending_full,
                    payoff_span_chips=context.payoff_span_chips,
                )
            except _NestedValueReversalDetected:
                stop = NonReplayTeacherStopReason.NESTED_VALUE_REVERSAL
            else:
                incomplete.append(observation)
                next_task = (
                    schedule.tasks[task_index + 1]
                    if task_index + 1 < len(schedule.tasks)
                    else None
                )
                width_ends = (
                    next_task is None
                    or next_task.panel_position != task.panel_position
                    or next_task.raise_width != task.raise_width
                )
                if width_ends:
                    if task.raise_width is None:
                        raise AssertionError("teacher subset lost its semantic width")
                    try:
                        width_result = _build_width_result(
                            raise_width=task.raise_width,
                            full_evidence=pending_full,
                            payoff_span_chips=context.payoff_span_chips,
                            observations=tuple(incomplete),
                        )
                    except _NestedValueReversalDetected:
                        stop = NonReplayTeacherStopReason.NESTED_VALUE_REVERSAL
                    else:
                        completed_widths.append(width_result)
                        incomplete = []
                context_ends = (
                    next_task is None
                    or next_task.panel_position != task.panel_position
                )
                if context_ends and stop is None:
                    contexts.append(
                        NonReplayTeacherContextResult(
                            panel_position=task.panel_position,
                            pool_index=task.pool_index,
                            context_semantic_sha256=task.context_semantic_digest,
                            payoff_span_chips=context.payoff_span_chips,
                            full_task_sha256=schedule.tasks[
                                pending_full.task_index
                            ].digest,
                            full_evidence_sha256=pending_full.digest,
                            full_value=pending_full.value,
                            widths=tuple(completed_widths),
                        )
                    )
                    pending_full = None
                    completed_widths = []
                    incomplete = []

    if len(evidences) == ADR0335_TEACHER_TASK_COUNT and stop is None:
        if pending_full is not None or completed_widths or incomplete:
            raise AssertionError("complete teacher schedule retained partial state")
        stop = NonReplayTeacherStopReason.COMPLETED
    return _DerivedTeacherState(
        evidences=evidences,
        contexts=tuple(contexts),
        completed_widths=tuple(completed_widths),
        incomplete_observations=tuple(incomplete),
        pending_full_evidence=pending_full,
        stop_reason=stop,
        known_public_call_count=known_calls,
        invocation_count_complete=complete_calls,
    )


def _derive_state(
    evidences: tuple[NonReplayTeacherArmEvidence, ...],
    *,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayExhaustiveTeacherSchedule,
) -> _DerivedTeacherState:
    state = _empty_derived_state()
    for evidence in evidences:
        state = _advance_state(
            state,
            evidence,
            pool=pool,
            schedule=schedule,
        )
    return state


class NonReplayTeacherExecutionPhase(StrEnum):
    HEADER_APPEND = "header_append"
    NEXT_CALL_AUTHORIZATION = "next_call_authorization"
    ARM_EVIDENCE = "arm_evidence"
    OBSERVATION_APPEND = "observation_append"
    SEMANTIC_REDUCTION = "semantic_reduction"
    TERMINAL_APPEND = "terminal_append"
    JOURNAL_CLOSE = "journal_close"
    FINAL_REBIND = "final_rebind"


_TEACHER_PROTOCOL_PAYLOAD = {
    "artifact_relative_path": ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
    "consumer": "certified-reduced-sizing-v2-one-public-highs-ds-call",
    "dominance": "other.lower>candidate.upper",
    "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    "equivalence_allowance_chips_hex": (
        ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE.chips.hex()
    ),
    "equivalence_effect": "reporting-only-no-selection-no-certificate-excuse",
    "evidence_version": _EVIDENCE_VERSION,
    "execution_phases": tuple(item.value for item in NonReplayTeacherExecutionPhase),
    "full_arm_count": ADR0335_TEACHER_FULL_TASK_COUNT,
    "full_reuse": "once-per-context-by-exact-request-within-invocation",
    "header_version": _HEADER_VERSION,
    "next_call_authority": "exact-preceding-post-fsync-receipt",
    "normalizer": "pot+2*effective_stack",
    "panel_context_sha256s": ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
    "panel_pool_indices": ADR0334_QUALIFIED_POOL_INDICES,
    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
    "qualification_journal_sha256": ADR0334_QUALIFICATION_ARTIFACT_SHA256,
    "qualification_terminal_sha256": ADR0334_QUALIFICATION_TERMINAL_SHA256,
    "raise_widths": tuple(width.count for width in ADR0323_RAISE_WIDTHS),
    "regret_interval": "[L_full-U_subset,U_full-L_subset]",
    "response_model": "heads_up_fold_call_only",
    "stop_reasons": tuple(item.value for item in NonReplayTeacherStopReason),
    "subset_counts": ADR0335_TEACHER_SUBSET_COUNTS,
    "subset_order": "raise-width-ascending-then-lexicographic",
    "subset_task_count": ADR0335_TEACHER_SUBSET_TASK_COUNT,
    "task_count": ADR0335_TEACHER_TASK_COUNT,
    "teacher_interval": "[max(candidate.lower),max(candidate.upper)]",
    "teacher_selection": "all-nondominated;unique-only-if-sole-survivor",
    "terminal_version": _TERMINAL_VERSION,
    "tie_boundary": "teacher-preserves-ties;runtime-cost-cannot-edit-evidence",
    "value_witness": "exact-policy-lower-plus-dual-certificate-upper",
    "version": "adr0335-nonreplay-exhaustive-teacher-protocol-v1",
}
ADR0335_TEACHER_PROTOCOL = MappingProxyType(_TEACHER_PROTOCOL_PAYLOAD)
ADR0335_TEACHER_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_TEACHER_PROTOCOL_PAYLOAD)
).hexdigest()


def verify_adr0335_teacher_source_and_dependencies() -> str:
    from .fresh_action_width_nonreplay_teacher_seal import (
        ADR0335_TEACHER_PROTOCOL_SHA256 as sealed_protocol,
        ADR0335_TEACHER_SCHEDULE_SHA256,
        ADR0335_TEACHER_SOURCE_MANIFEST,
        ADR0335_TEACHER_SUBSET_COUNTS as sealed_counts,
        ADR0335_TEACHER_TASK_COUNT as sealed_task_count,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0335_TEACHER_SOURCE_MANIFEST
    }
    if actual != ADR0335_TEACHER_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0335 exhaustive-teacher source closure drifted")
    if (
        sealed_protocol != ADR0335_TEACHER_PROTOCOL_SHA256
        or sealed_counts != ADR0335_TEACHER_SUBSET_COUNTS
        or sealed_task_count != ADR0335_TEACHER_TASK_COUNT
        or tuple(ADR0335_TEACHER_PROTOCOL["stop_reasons"])
        != tuple(item.value for item in NonReplayTeacherStopReason)
        or tuple(ADR0335_TEACHER_PROTOCOL["execution_phases"])
        != tuple(item.value for item in NonReplayTeacherExecutionPhase)
    ):
        raise RuntimeError("ADR-0335 exhaustive-teacher protocol drifted")
    schedule = build_adr0334_nonreplay_exhaustive_teacher_schedule()
    if schedule.digest != ADR0335_TEACHER_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0335 exhaustive-teacher schedule drifted")
    return actual["fresh_action_width_nonreplay_teacher.py"]


def _campaign_sha256(
    *,
    schedule: NonReplayExhaustiveTeacherSchedule,
    teacher_source_sha256: str,
    synthetic: bool,
) -> str:
    _require_digest(teacher_source_sha256, label="teacher campaign source")
    return sha256(
        canonical_journal_json_bytes(
            {
                "artifact_relative_path": ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
                "panel_sha256": schedule.panel_sha256,
                "pool_sha256": schedule.pool_sha256,
                "protocol_sha256": ADR0335_TEACHER_PROTOCOL_SHA256,
                "qualification_journal_sha256": (
                    schedule.qualification_journal_sha256
                ),
                "schedule_sha256": schedule.digest,
                "synthetic": synthetic,
                "teacher_source_sha256": teacher_source_sha256,
                "version": "adr0335-nonreplay-exhaustive-teacher-campaign-v1",
            }
        )
    ).hexdigest()


def _header_payload(
    *,
    schedule: NonReplayExhaustiveTeacherSchedule,
    teacher_source_sha256: str,
    campaign_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    return _sealed_payload(
        {
            "artifact_relative_path": ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
            "campaign_sha256": campaign_sha256,
            "panel_sha256": schedule.panel_sha256,
            "pool_sha256": schedule.pool_sha256,
            "protocol_sha256": ADR0335_TEACHER_PROTOCOL_SHA256,
            "qualification_journal_sha256": schedule.qualification_journal_sha256,
            "qualification_terminal_sha256": (
                schedule.qualification_terminal_sha256
            ),
            "schedule_sha256": schedule.digest,
            "subset_counts": schedule.subset_counts_by_raise_width,
            "synthetic": synthetic,
            "task_count": ADR0335_TEACHER_TASK_COUNT,
            "teacher_source_sha256": teacher_source_sha256,
            "version": _HEADER_VERSION,
        },
        digest_field="header_sha256",
    )


def _terminal_payload(
    *,
    state: _DerivedTeacherState,
    schedule: NonReplayExhaustiveTeacherSchedule,
    teacher_source_sha256: str,
    campaign_sha256: str,
    final_observation_line_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    if state.stop_reason is None:
        raise ValueError("teacher terminal requires a derived stop")
    _require_digest(
        final_observation_line_sha256,
        label="teacher final observation line",
    )
    return _sealed_payload(
        {
            "campaign_sha256": campaign_sha256,
            "completed_context_sha256s": tuple(
                context.digest for context in state.contexts
            ),
            "completed_width_sha256s": tuple(
                width.digest for width in state.completed_widths
            ),
            "evidence_sha256s": tuple(item.digest for item in state.evidences),
            "final_observation_line_sha256": final_observation_line_sha256,
            "incomplete_observation_sha256s": tuple(
                item.digest for item in state.incomplete_observations
            ),
            "invocation_count_complete": state.invocation_count_complete,
            "known_public_call_count": state.known_public_call_count,
            "observed_arm_count": len(state.evidences),
            "panel_sha256": schedule.panel_sha256,
            "pending_full_evidence_sha256": state.pending_full_evidence_sha256,
            "pool_sha256": schedule.pool_sha256,
            "qualification_journal_sha256": schedule.qualification_journal_sha256,
            "record_count": len(state.evidences) + 2,
            "schedule_sha256": schedule.digest,
            "stop_reason": state.stop_reason.value,
            "synthetic": synthetic,
            "teacher_source_sha256": teacher_source_sha256,
            "version": _TERMINAL_VERSION,
        },
        digest_field="terminal_sha256",
    )


@dataclass(frozen=True, slots=True)
class NonReplayTeacherJournalPrefix:
    recovery: JournalRecovery
    evidences: tuple[NonReplayTeacherArmEvidence, ...]
    contexts: tuple[NonReplayTeacherContextResult, ...]
    completed_widths: tuple[NonReplayTeacherWidthResult, ...]
    incomplete_observations: tuple[NonReplayTeacherSubsetObservation, ...]
    pending_full_evidence_sha256: str | None
    pending_stop_reason: NonReplayTeacherStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.recovery, JournalRecovery):
            raise TypeError("teacher prefix requires generic journal recovery")
        if self.recovery.is_complete:
            raise ValueError("teacher prefix cannot contain a terminal journal")
        for label, values, expected_type in (
            ("evidences", self.evidences, NonReplayTeacherArmEvidence),
            ("contexts", self.contexts, NonReplayTeacherContextResult),
            ("completed widths", self.completed_widths, NonReplayTeacherWidthResult),
            (
                "incomplete observations",
                self.incomplete_observations,
                NonReplayTeacherSubsetObservation,
            ),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(item, expected_type) for item in values
            ):
                raise TypeError(f"teacher prefix {label} are not semantic")
        if tuple(item.task_index for item in self.evidences) != tuple(
            range(len(self.evidences))
        ):
            raise ValueError("teacher prefix evidences are not contiguous")
        _require_digest(
            self.pending_full_evidence_sha256,
            label="teacher prefix pending full evidence",
            optional=True,
        )
        if self.pending_stop_reason is not None and not isinstance(
            self.pending_stop_reason,
            NonReplayTeacherStopReason,
        ):
            raise TypeError("teacher prefix pending stop is not semantic")
        calls = _require_count(
            self.known_public_call_count,
            label="teacher prefix known calls",
            maximum=ADR0335_TEACHER_TASK_COUNT,
        )
        if calls != sum(item.public_call_count for item in self.evidences):
            raise ValueError("teacher prefix call count drifted")
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("teacher prefix completeness must be Boolean")
        expected_complete = all(
            item.kind is not NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION
            for item in self.evidences
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("teacher prefix invocation completeness drifted")
        expected_records = 0 if not self.recovery.records else len(self.evidences) + 1
        if len(self.recovery.records) != expected_records:
            raise ValueError("teacher prefix recovery/evidence counts differ")


@dataclass(frozen=True, slots=True)
class NonReplayTeacherJournalResult:
    campaign_sha256: str
    journal_sha256: str
    journal_byte_count: int
    terminal_sha256: str
    evidences: tuple[NonReplayTeacherArmEvidence, ...]
    contexts: tuple[NonReplayTeacherContextResult, ...]
    completed_widths: tuple[NonReplayTeacherWidthResult, ...]
    incomplete_observations: tuple[NonReplayTeacherSubsetObservation, ...]
    pending_full_evidence_sha256: str | None
    stop_reason: NonReplayTeacherStopReason
    known_public_call_count: int
    invocation_count_complete: bool
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("teacher campaign", self.campaign_sha256),
            ("teacher journal", self.journal_sha256),
            ("teacher terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=label)
        _require_count(self.journal_byte_count, label="teacher journal byte count")
        if self.journal_byte_count == 0:
            raise ValueError("teacher terminal journal cannot be empty")
        if not isinstance(self.stop_reason, NonReplayTeacherStopReason):
            raise TypeError("teacher result stop must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("teacher result synthetic flag must be Boolean")
        for label, values, expected_type in (
            ("evidences", self.evidences, NonReplayTeacherArmEvidence),
            ("contexts", self.contexts, NonReplayTeacherContextResult),
            ("completed widths", self.completed_widths, NonReplayTeacherWidthResult),
            (
                "incomplete observations",
                self.incomplete_observations,
                NonReplayTeacherSubsetObservation,
            ),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(item, expected_type) for item in values
            ):
                raise TypeError(f"teacher result {label} are not semantic")
        if not self.evidences or tuple(
            item.task_index for item in self.evidences
        ) != tuple(range(len(self.evidences))):
            raise ValueError("teacher result evidences are not a nonempty prefix")
        if any(item.synthetic is not self.synthetic for item in self.evidences):
            raise ValueError("teacher result mixes evidence provenance")
        if tuple(item.panel_position for item in self.contexts) != tuple(
            range(len(self.contexts))
        ):
            raise ValueError("teacher result contexts are not a contiguous prefix")
        _require_digest(
            self.pending_full_evidence_sha256,
            label="teacher result pending full evidence",
            optional=True,
        )
        calls = _require_count(
            self.known_public_call_count,
            label="teacher result known calls",
            maximum=ADR0335_TEACHER_TASK_COUNT,
        )
        if calls != sum(item.public_call_count for item in self.evidences):
            raise ValueError("teacher result call count drifted")
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("teacher result completeness must be Boolean")
        expected_complete = all(
            item.kind is not NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION
            for item in self.evidences
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("teacher result invocation completeness drifted")
        if self.stop_reason is NonReplayTeacherStopReason.CONSUMER_REJECTED and (
            self.evidences[-1].kind is not NonReplayTeacherEvidenceKind.REJECTED
        ):
            raise ValueError("teacher rejection terminal lacks rejected evidence")
        if self.stop_reason is NonReplayTeacherStopReason.UNEXPECTED_EXCEPTION and (
            self.evidences[-1].kind
            is not NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION
        ):
            raise ValueError("teacher unexpected terminal lacks unexpected evidence")
        if self.stop_reason is NonReplayTeacherStopReason.NESTED_VALUE_REVERSAL and (
            self.evidences[-1].kind is not NonReplayTeacherEvidenceKind.ACCEPTED
        ):
            raise ValueError("teacher reversal terminal lacks accepted evidence")
        if self.stop_reason is NonReplayTeacherStopReason.COMPLETED and (
            len(self.evidences) != ADR0335_TEACHER_TASK_COUNT
            or len(self.contexts) != ADR0335_TEACHER_FULL_TASK_COUNT
            or self.completed_widths
            or self.incomplete_observations
            or self.pending_full_evidence_sha256 is not None
        ):
            raise ValueError("teacher completed terminal retains partial state")


NonReplayTeacherJournalRebinding = (
    NonReplayTeacherJournalPrefix | NonReplayTeacherJournalResult
)


def rebind_adr0335_teacher_journal(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> NonReplayTeacherJournalRebinding:
    if not isinstance(raw, bytes):
        raise TypeError("teacher journal rebinding requires immutable bytes")
    if not isinstance(synthetic, bool):
        raise TypeError("teacher journal synthetic mode must be Boolean")
    teacher_source = verify_adr0335_teacher_source_and_dependencies()
    pool = build_adr0331_nonreplay_pool()
    schedule = build_adr0334_nonreplay_exhaustive_teacher_schedule()
    campaign = _campaign_sha256(
        schedule=schedule,
        teacher_source_sha256=teacher_source,
        synthetic=synthetic,
    )
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=ADR0335_TEACHER_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign,
    )
    records = recovery.records
    if not records:
        return NonReplayTeacherJournalPrefix(
            recovery=recovery,
            evidences=(),
            contexts=(),
            completed_widths=(),
            incomplete_observations=(),
            pending_full_evidence_sha256=None,
            pending_stop_reason=None,
            known_public_call_count=0,
            invocation_count_complete=True,
        )
    header = records[0]
    if header.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("teacher journal first record is not its header")
    expected_header = _header_payload(
        schedule=schedule,
        teacher_source_sha256=teacher_source,
        campaign_sha256=campaign,
        synthetic=synthetic,
    )
    if canonical_journal_json_bytes(
        header.body.payload
    ) != canonical_journal_json_bytes(expected_header):
        raise ValueError("teacher journal header differs from its sealed schedule")
    if header.body.semantic_identity_sha256 != expected_header["header_sha256"]:
        raise ValueError("teacher journal header semantic identity drifted")

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
        raise ValueError("teacher journal has a non-observation inside its arm prefix")
    if len(observation_records) > ADR0335_TEACHER_TASK_COUNT:
        raise ValueError("teacher journal exceeds its sealed task count")
    evidences: list[NonReplayTeacherArmEvidence] = []
    for task_index, record in enumerate(observation_records):
        evidence = _rebind_evidence(
            record.body.payload,
            task=schedule.tasks[task_index],
            task_index=task_index,
            expect_synthetic=synthetic,
        )
        if record.body.semantic_identity_sha256 != evidence.digest:
            raise ValueError("teacher observation semantic identity drifted")
        evidences.append(evidence)
    state = _derive_state(tuple(evidences), pool=pool, schedule=schedule)

    if terminal_record is None:
        return NonReplayTeacherJournalPrefix(
            recovery=recovery,
            evidences=state.evidences,
            contexts=state.contexts,
            completed_widths=state.completed_widths,
            incomplete_observations=state.incomplete_observations,
            pending_full_evidence_sha256=state.pending_full_evidence_sha256,
            pending_stop_reason=state.stop_reason,
            known_public_call_count=state.known_public_call_count,
            invocation_count_complete=state.invocation_count_complete,
        )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("teacher journal terminal has trailing invalid bytes")
    if not evidences:
        raise ValueError("teacher journal terminal lacks an observation")
    expected_terminal = _terminal_payload(
        state=state,
        schedule=schedule,
        teacher_source_sha256=teacher_source,
        campaign_sha256=campaign,
        final_observation_line_sha256=observation_records[-1].line_sha256,
        synthetic=synthetic,
    )
    terminal_payload = terminal_record.body.payload
    _verify_sealed_payload(
        terminal_payload,
        digest_field="terminal_sha256",
        label="teacher terminal",
    )
    if canonical_journal_json_bytes(terminal_payload) != canonical_journal_json_bytes(
        expected_terminal
    ):
        raise ValueError("teacher terminal differs from journal-derived evidence")
    if terminal_record.body.semantic_identity_sha256 != terminal_payload[
        "terminal_sha256"
    ]:
        raise ValueError("teacher terminal semantic identity drifted")
    if state.stop_reason is None:
        raise AssertionError("teacher terminal validated without a stop")
    return NonReplayTeacherJournalResult(
        campaign_sha256=campaign,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
        terminal_sha256=terminal_payload["terminal_sha256"],
        evidences=state.evidences,
        contexts=state.contexts,
        completed_widths=state.completed_widths,
        incomplete_observations=state.incomplete_observations,
        pending_full_evidence_sha256=state.pending_full_evidence_sha256,
        stop_reason=state.stop_reason,
        known_public_call_count=state.known_public_call_count,
        invocation_count_complete=state.invocation_count_complete,
        synthetic=synthetic,
    )


@dataclass(frozen=True, slots=True)
class NonReplayTeacherLaunchRejected:
    reason: str
    output_path: Path
    exception_chain: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("teacher launch rejection reason must be nonempty")
        if not isinstance(self.output_path, Path):
            raise TypeError("teacher launch rejection path must be a Path")
        _validate_exception_descriptors(
            self.exception_chain,
            label="teacher launch rejection",
        )


@dataclass(frozen=True, slots=True)
class NonReplayTeacherExecutionFailed:
    reason: str
    phase: NonReplayTeacherExecutionPhase
    output_path: Path
    failed_task_index: int | None
    unreceipted_arm_invocation: bool
    durably_recorded_evidences: tuple[NonReplayTeacherArmEvidence, ...]
    known_public_call_count: int
    invocation_count_complete: bool
    raw_journal_bytes: bytes | None
    recovery: JournalRecovery | None
    exception_chain: tuple[dict[str, str], ...]
    recovery_exception_chain: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("teacher execution failure reason must be nonempty")
        if not isinstance(self.phase, NonReplayTeacherExecutionPhase):
            raise TypeError("teacher execution failure phase must be semantic")
        if not isinstance(self.output_path, Path):
            raise TypeError("teacher execution failure path must be a Path")
        if self.failed_task_index is not None:
            _require_count(
                self.failed_task_index,
                label="teacher failed task index",
                maximum=ADR0335_TEACHER_TASK_COUNT - 1,
            )
        if not isinstance(self.unreceipted_arm_invocation, bool):
            raise TypeError("teacher unreceipted-call flag must be Boolean")
        if not isinstance(self.durably_recorded_evidences, tuple) or any(
            not isinstance(item, NonReplayTeacherArmEvidence)
            for item in self.durably_recorded_evidences
        ):
            raise TypeError("teacher execution failure evidence is not semantic")
        expected_calls = sum(
            item.public_call_count for item in self.durably_recorded_evidences
        )
        _require_count(
            self.known_public_call_count,
            label="teacher execution failure known calls",
            maximum=ADR0335_TEACHER_TASK_COUNT,
        )
        if self.known_public_call_count != expected_calls:
            raise ValueError("teacher execution failure call count drifted")
        if not isinstance(self.invocation_count_complete, bool):
            raise TypeError("teacher execution failure completeness must be Boolean")
        expected_complete = (
            not self.unreceipted_arm_invocation
            and all(
                item.kind is not NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION
                for item in self.durably_recorded_evidences
            )
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("teacher execution failure completeness drifted")
        if not self.exception_chain:
            raise ValueError("teacher execution failure requires an exception chain")
        _validate_exception_descriptors(
            self.exception_chain,
            label="teacher execution failure",
        )
        _validate_exception_descriptors(
            self.recovery_exception_chain,
            label="teacher execution recovery failure",
            optional=True,
        )
        if self.raw_journal_bytes is None:
            if self.recovery is not None or not self.recovery_exception_chain:
                raise ValueError("teacher unreadable journal lacks recovery evidence")
        elif not isinstance(self.raw_journal_bytes, bytes):
            raise TypeError("teacher execution failure raw journal is mutable")
        elif self.recovery is None:
            if not self.recovery_exception_chain:
                raise ValueError("teacher raw journal lacks recovery evidence")
        elif (
            not isinstance(self.recovery, JournalRecovery)
            or self.recovery.raw_bytes != self.raw_journal_bytes
        ):
            raise ValueError("teacher execution failure recovery lost raw bytes")


NonReplayTeacherRunResult = (
    NonReplayTeacherJournalRebinding
    | NonReplayTeacherLaunchRejected
    | NonReplayTeacherExecutionFailed
)
_ArmOwner = Callable[
    [int, ExhaustiveTeacherTask],
    NonReplayTeacherArmEvidence,
]


def _execution_failure(
    *,
    writer: DurableEvidenceJournalWriter,
    output_path: Path,
    campaign_sha256: str,
    phase: NonReplayTeacherExecutionPhase,
    failed_task_index: int | None,
    unreceipted_arm_invocation: bool,
    evidences: tuple[NonReplayTeacherArmEvidence, ...],
    error: Exception,
) -> NonReplayTeacherExecutionFailed:
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
                expected_protocol_sha256=ADR0335_TEACHER_PROTOCOL_SHA256,
                expected_campaign_sha256=campaign_sha256,
            )
        except Exception as recovery_error:
            recovery_exception_chain = _exception_payload(recovery_error)
    return NonReplayTeacherExecutionFailed(
        reason="teacher failed after exclusive journal creation",
        phase=phase,
        output_path=output_path,
        failed_task_index=failed_task_index,
        unreceipted_arm_invocation=unreceipted_arm_invocation,
        durably_recorded_evidences=evidences,
        known_public_call_count=sum(item.public_call_count for item in evidences),
        invocation_count_complete=(
            not unreceipted_arm_invocation
            and all(
                item.kind is not NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION
                for item in evidences
            )
        ),
        raw_journal_bytes=raw,
        recovery=recovery,
        exception_chain=exception_chain,
        recovery_exception_chain=recovery_exception_chain,
    )


def _execute_teacher(
    *,
    output_path: Path,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayExhaustiveTeacherSchedule,
    teacher_source_sha256: str,
    arm_owner: _ArmOwner,
    synthetic: bool,
) -> NonReplayTeacherJournalResult | NonReplayTeacherExecutionFailed:
    campaign = _campaign_sha256(
        schedule=schedule,
        teacher_source_sha256=teacher_source_sha256,
        synthetic=synthetic,
    )
    writer = DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=ADR0335_TEACHER_PROTOCOL_SHA256,
        campaign_sha256=campaign,
    )
    evidences: list[NonReplayTeacherArmEvidence] = []
    state = _empty_derived_state()
    phase = NonReplayTeacherExecutionPhase.HEADER_APPEND
    failed_task_index: int | None = None
    unreceipted_arm_invocation = False
    try:
        header_payload = _header_payload(
            schedule=schedule,
            teacher_source_sha256=teacher_source_sha256,
            campaign_sha256=campaign,
            synthetic=synthetic,
        )
        authorization = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header_payload["header_sha256"],
            payload=header_payload,
        )
        for task_index, task in enumerate(schedule.tasks):
            phase = NonReplayTeacherExecutionPhase.NEXT_CALL_AUTHORIZATION
            failed_task_index = task_index
            expected_receipt_kind = (
                JournalRecordKind.HEADER
                if task_index == 0
                else JournalRecordKind.OBSERVATION
            )
            if (
                authorization.sequence != task_index
                or authorization.kind is not expected_receipt_kind
            ):
                raise RuntimeError("teacher call lacks its preceding durable receipt")
            phase = NonReplayTeacherExecutionPhase.ARM_EVIDENCE
            unreceipted_arm_invocation = True
            try:
                evidence = arm_owner(task_index, task)
                if not isinstance(evidence, NonReplayTeacherArmEvidence):
                    raise TypeError("teacher arm owner returned nonsemantic evidence")
                _validate_evidence_against_task(
                    evidence,
                    task=task,
                    expect_synthetic=synthetic,
                )
            except Exception as error:
                evidence = _unexpected_evidence(
                    task_index=task_index,
                    task=task,
                    error=error,
                    synthetic=synthetic,
                )
                _validate_evidence_against_task(
                    evidence,
                    task=task,
                    expect_synthetic=synthetic,
                )
            phase = NonReplayTeacherExecutionPhase.OBSERVATION_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
            evidences.append(evidence)
            unreceipted_arm_invocation = False
            phase = NonReplayTeacherExecutionPhase.SEMANTIC_REDUCTION
            state = _advance_state(
                state,
                evidence,
                pool=pool,
                schedule=schedule,
            )
            if state.stop_reason is None:
                continue
            terminal_payload = _terminal_payload(
                state=state,
                schedule=schedule,
                teacher_source_sha256=teacher_source_sha256,
                campaign_sha256=campaign,
                final_observation_line_sha256=authorization.line_sha256,
                synthetic=synthetic,
            )
            phase = NonReplayTeacherExecutionPhase.TERMINAL_APPEND
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=terminal_payload["terminal_sha256"],
                payload=terminal_payload,
            )
            break
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_task_index=failed_task_index,
            unreceipted_arm_invocation=unreceipted_arm_invocation,
            evidences=tuple(evidences),
            error=error,
        )
    phase = NonReplayTeacherExecutionPhase.JOURNAL_CLOSE
    try:
        writer.close()
        phase = NonReplayTeacherExecutionPhase.FINAL_REBIND
        rebound = rebind_adr0335_teacher_journal(
            output_path.read_bytes(),
            synthetic=synthetic,
        )
        if not isinstance(rebound, NonReplayTeacherJournalResult):
            raise RuntimeError("teacher execution ended without a terminal result")
        return rebound
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_task_index=failed_task_index,
            unreceipted_arm_invocation=False,
            evidences=tuple(evidences),
            error=error,
        )


def _real_arm_owner(
    task_index: int,
    task: ExhaustiveTeacherTask,
) -> NonReplayTeacherArmEvidence:
    result = consume_certified_reduced_sizing_v2(task.request)
    return teacher_evidence_from_consumer_result(
        task_index=task_index,
        task=task,
        result=result,
    )


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH


def run_and_retain_adr0334_nonreplay_exhaustive_teacher(
) -> NonReplayTeacherRunResult:
    """Open teacher values only after ADR-0335's exact source seal exists."""

    output_path = _artifact_path()
    try:
        teacher_source = verify_adr0335_teacher_source_and_dependencies()
        retained = verify_adr0334_nonreplay_qualification_result_artifact()
        pool = build_adr0331_nonreplay_pool()
        schedule = build_adr0334_nonreplay_exhaustive_teacher_schedule()
        if retained.panel.digest != schedule.panel_sha256:
            raise RuntimeError("teacher preflight panel drifted")
    except Exception as error:
        return NonReplayTeacherLaunchRejected(
            reason="teacher source, panel, or schedule preflight rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )
    try:
        return _execute_teacher(
            output_path=output_path,
            pool=pool,
            schedule=schedule,
            teacher_source_sha256=teacher_source,
            arm_owner=_real_arm_owner,
            synthetic=False,
        )
    except Exception as error:
        return NonReplayTeacherLaunchRejected(
            reason="teacher exclusive journal launch rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )


def synthetic_teacher_accepted_evidence(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
    lower_chips: float,
    upper_chips: float,
) -> NonReplayTeacherArmEvidence:
    lower = float(lower_chips)
    upper = float(upper_chips)
    if not isfinite(lower) or not isfinite(upper) or lower > upper:
        raise ValueError("synthetic teacher endpoints are invalid")
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
        task_index=task_index,
        task=task,
        kind=NonReplayTeacherEvidenceKind.ACCEPTED,
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


def synthetic_teacher_rejected_evidence(
    *,
    task_index: int,
    task: ExhaustiveTeacherTask,
) -> NonReplayTeacherArmEvidence:
    bound = _bind_request(task.request)
    return _build_evidence(
        task_index=task_index,
        task=task,
        kind=NonReplayTeacherEvidenceKind.REJECTED,
        synthetic=True,
        result_payload={
            "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
            "consumer_source_sha256": None,
            "context_label": task.request.context_id,
            "emitted_action": None,
            "exception_chain": (
                {
                    "message": "synthetic source drift",
                    "module": "builtins",
                    "type_name": "RuntimeError",
                },
            ),
            "fallback_disposition": (
                CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            ),
            "legal_raise_set_sha256": bound.legal_raise_set_sha256,
            "public_call_count": 0,
            "public_state_sha256": bound.public_state_sha256,
            "reason": CertifiedSizingConsumerRejectionReasonV2.SOURCE_DRIFT.value,
            "request_sha256": bound.request_sha256,
            "stage": CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION.value,
            "synthetic_result": True,
            "type": "rejected",
        },
    )


__all__ = [
    "ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH",
    "ADR0335_TEACHER_FULL_TASK_COUNT",
    "ADR0335_TEACHER_PROTOCOL",
    "ADR0335_TEACHER_PROTOCOL_SHA256",
    "ADR0335_TEACHER_SUBSET_COUNTS",
    "ADR0335_TEACHER_SUBSET_TASK_COUNT",
    "ADR0335_TEACHER_TASK_COUNT",
    "NonReplayExhaustiveTeacherSchedule",
    "NonReplayTeacherArmEvidence",
    "NonReplayTeacherContextResult",
    "NonReplayTeacherEvidenceKind",
    "NonReplayTeacherExecutionFailed",
    "NonReplayTeacherExecutionPhase",
    "NonReplayTeacherJournalPrefix",
    "NonReplayTeacherJournalRebinding",
    "NonReplayTeacherJournalResult",
    "NonReplayTeacherLaunchRejected",
    "NonReplayTeacherRunResult",
    "NonReplayTeacherStopReason",
    "NonReplayTeacherSubsetObservation",
    "NonReplayTeacherWidthResult",
    "build_adr0334_nonreplay_exhaustive_teacher_schedule",
    "rebind_adr0335_teacher_journal",
    "run_and_retain_adr0334_nonreplay_exhaustive_teacher",
    "synthetic_teacher_accepted_evidence",
    "synthetic_teacher_rejected_evidence",
    "teacher_evidence_from_consumer_result",
    "verify_adr0335_teacher_source_and_dependencies",
]
