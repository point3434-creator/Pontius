"""Source-only ADR-0331 qualification owner for the sealed non-replay pool.

Every future arm result is canonicalized, appended, flushed, and fsynced before
the next arm may be called.  This module can build and synthetically exercise
the complete protocol without invoking the value-bearing consumer.
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
from .certified_reduced_sizing_highs import (
    ADR0318_CERTIFIED_SIZING_ALLOWANCES,
)
from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    JournalRecovery,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from .linear_program_certificate import certify_bounded_minimization_lower_bound
from .reduced_river_sizing_lp import compile_reduced_river_sizing_lp
from .fresh_action_width_nonreplay import (
    ADR0331_NONREPLAY_PROTOCOL_SHA256,
    FreshActionWidthNonReplayPool,
    build_adr0331_nonreplay_pool,
)
from .fresh_action_width_nonreplay_seal import (
    ADR0331_JOURNAL_PROTOCOL_SHA256,
    ADR0331_NONREPLAY_PROTOCOL_SHA256 as SEALED_NONREPLAY_PROTOCOL_SHA256,
    ADR0331_NONREPLAY_SOURCE_MANIFEST,
    ADR0331_POPULATION_CANDIDATE_ATTEMPTS,
    ADR0331_POPULATION_POOL_SHA256,
    ADR0331_SUBSET_COUNTS_BY_RAISE_WIDTH,
    ADR0331_TOTAL_SUBSET_COUNT,
)
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    ADR0323_OPPORTUNITY_FLOOR,
    ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
    ADR0323_QUALIFICATION_TARGET,
    ActionWidthQualificationArm,
    ActionWidthQualificationClassification,
    ActionWidthQualificationTask,
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
    certified_full_minus_subset_regret,
    classify_action_width_opportunity,
    qualification_requests_for_context,
)


ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-nonreplay-qualification-v1.jsonl"
)
ADR0331_QUALIFICATION_TASK_COUNT = 192
ADR0331_QUALIFICATION_TARGET = ADR0323_QUALIFICATION_TARGET
_SCHEDULE_VERSION = "adr0331-nonreplay-qualification-schedule-v1"
_HEADER_VERSION = "adr0331-nonreplay-qualification-header-v1"
_EVIDENCE_VERSION = "adr0331-nonreplay-qualification-arm-evidence-v1"
_TERMINAL_VERSION = "adr0331-nonreplay-qualification-terminal-v1"


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


def _require_count(value: object, *, label: str, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} exceeds its maximum")
    return value


def _require_exact_keys(
    value: object,
    expected: frozenset[str],
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or frozenset(value) != expected:
        raise ValueError(f"{label} has missing or extra fields")
    return value


def _float_hex(value: float, *, label: str) -> str:
    if not isinstance(value, float) or not isfinite(value):
        raise ValueError(f"{label} must be a finite float")
    return value.hex()


def _require_float_hex(value: object, *, label: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a hexadecimal float string")
    try:
        decoded = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not a hexadecimal float string") from error
    if not isfinite(decoded) or decoded.hex() != value:
        raise ValueError(f"{label} is not a canonical finite float string")
    return decoded


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
    value: dict[str, object],
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if digest_field not in value:
        raise ValueError(f"{label} lacks its digest")
    claimed = _require_digest(value[digest_field], label=f"{label} digest")
    core = {key: item for key, item in value.items() if key != digest_field}
    actual = sha256(canonical_journal_json_bytes(core)).hexdigest()
    if claimed != actual:
        raise ValueError(f"{label} digest differs from its self-free core")
    return core


@dataclass(frozen=True, slots=True)
class NonReplayQualificationSchedule:
    pool_sha256: str
    tasks: tuple[ActionWidthQualificationTask, ...]

    def __post_init__(self) -> None:
        _require_digest(self.pool_sha256, label="non-replay qualification pool")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0331_QUALIFICATION_TASK_COUNT
            or any(
                not isinstance(task, ActionWidthQualificationTask)
                for task in self.tasks
            )
        ):
            raise TypeError("non-replay qualification requires 192 semantic tasks")
        expected = tuple(
            (index, arm)
            for index in range(96)
            for arm in (
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
            )
        )
        if tuple((task.context_index, task.arm) for task in self.tasks) != expected:
            raise ValueError("non-replay qualification task order drifted")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("non-replay qualification schedule repeats a task")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "pool_sha256": self.pool_sha256,
                    "task_digests": tuple(task.digest for task in self.tasks),
                    "version": _SCHEDULE_VERSION,
                }
            )
        ).hexdigest()


def verify_adr0332_nonreplay_source_and_pool() -> FreshActionWidthNonReplayPool:
    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0331_NONREPLAY_SOURCE_MANIFEST
    }
    if actual != ADR0331_NONREPLAY_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0332 non-replay source closure drifted")
    if (
        DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
        != ADR0331_JOURNAL_PROTOCOL_SHA256
        or ADR0331_NONREPLAY_PROTOCOL_SHA256
        != SEALED_NONREPLAY_PROTOCOL_SHA256
    ):
        raise RuntimeError("ADR-0332 non-replay protocol drifted")
    pool = build_adr0331_nonreplay_pool()
    ledger = pool.subset_work_ledger
    if (
        pool.digest != ADR0331_POPULATION_POOL_SHA256
        or pool.candidate_attempts != ADR0331_POPULATION_CANDIDATE_ATTEMPTS
        or tuple(
            (width.count, count)
            for width, count in ledger.subset_counts_by_raise_width
        )
        != ADR0331_SUBSET_COUNTS_BY_RAISE_WIDTH
        or ledger.total_subset_count != ADR0331_TOTAL_SUBSET_COUNT
    ):
        raise RuntimeError("ADR-0332 non-replay population drifted")
    return pool


def build_adr0331_nonreplay_qualification_schedule(
) -> NonReplayQualificationSchedule:
    pool = verify_adr0332_nonreplay_source_and_pool()
    return NonReplayQualificationSchedule(
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


_QUALIFICATION_PROTOCOL_PAYLOAD = {
    "ambiguity_guard_chips_hex": (
        ADR0323_QUALIFICATION_AMBIGUITY_GUARD.chips.hex()
    ),
    "arm_order": tuple(arm.value for arm in ActionWidthQualificationArm),
    "artifact_relative_path": ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    "classification_order": tuple(
        value.value for value in ActionWidthQualificationClassification
    ),
    "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
    "durable_journal_protocol_sha256": (
        DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
    ),
    "evidence_version": _EVIDENCE_VERSION,
    "execution_failure_reduction": (
        "exact-raw-journal-plus-last-receipted-semantic-prefix"
    ),
    "execution_phases": (
        "header_append",
        "next_call_authorization",
        "arm_evidence",
        "observation_append",
        "semantic_reduction",
        "terminal_append",
        "journal_close",
        "final_rebind",
    ),
    "header_version": _HEADER_VERSION,
    "nested_reversal_allowance_chips_hex": (
        ADR0323_NESTED_REVERSAL_ALLOWANCE.chips.hex()
    ),
    "nonreplay_protocol_sha256": ADR0331_NONREPLAY_PROTOCOL_SHA256,
    "opportunity_floor_hex": ADR0323_OPPORTUNITY_FLOOR.value.hex(),
    "regret_interval": "[L_full-U_subset,U_full-L_subset]",
    "rejected_stage_identity": "exact-consumer-stage-contract",
    "schedule_version": _SCHEDULE_VERSION,
    "stop_reasons": (
        "target_reached",
        "pool_exhausted",
        "ambiguous",
        "nested_value_reversal",
        "consumer_rejected",
        "unexpected_exception",
    ),
    "target": ADR0331_QUALIFICATION_TARGET,
    "task_count": ADR0331_QUALIFICATION_TASK_COUNT,
    "terminal_version": _TERMINAL_VERSION,
    "unreceipted_invocation_accounting": "unknown-and-excluded",
    "value_witness": (
        "exact-policy-behavioral-reconstruction-plus-dual-certificate-rebind"
    ),
    "version": "adr0331-nonreplay-qualification-protocol-v1",
}
ADR0331_QUALIFICATION_PROTOCOL = MappingProxyType(_QUALIFICATION_PROTOCOL_PAYLOAD)
ADR0331_QUALIFICATION_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_QUALIFICATION_PROTOCOL_PAYLOAD)
).hexdigest()


def verify_adr0333_qualification_source_and_dependencies() -> str:
    from .fresh_action_width_nonreplay_qualification_seal import (
        ADR0331_QUALIFICATION_PROTOCOL_SHA256 as sealed_protocol,
        ADR0331_QUALIFICATION_SCHEDULE_SHA256,
        ADR0331_QUALIFICATION_SOURCE_MANIFEST,
        ADR0331_QUALIFICATION_TASK_COUNT as sealed_task_count,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0331_QUALIFICATION_SOURCE_MANIFEST
    }
    if actual != ADR0331_QUALIFICATION_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0333 qualification source closure drifted")
    if sealed_protocol != ADR0331_QUALIFICATION_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0333 qualification protocol drifted")
    if (
        sealed_task_count != ADR0331_QUALIFICATION_TASK_COUNT
        or tuple(ADR0331_QUALIFICATION_PROTOCOL["stop_reasons"])
        != tuple(item.value for item in NonReplayQualificationStopReason)
        or tuple(ADR0331_QUALIFICATION_PROTOCOL["execution_phases"])
        != tuple(item.value for item in QualificationExecutionPhase)
    ):
        raise RuntimeError("ADR-0333 qualification semantic enumeration drifted")
    schedule = build_adr0331_nonreplay_qualification_schedule()
    if schedule.digest != ADR0331_QUALIFICATION_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0333 qualification schedule drifted")
    return actual["fresh_action_width_nonreplay_qualification.py"]


class QualificationEvidenceKind(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


_EVIDENCE_CORE_KEYS = frozenset(
    {
        "arm",
        "context_index",
        "context_semantic_sha256",
        "kind",
        "result",
        "synthetic",
        "task_index",
        "task_sha256",
        "version",
    }
)


@dataclass(frozen=True, slots=True)
class QualificationArmEvidence:
    task_index: int
    task_sha256: str
    kind: QualificationEvidenceKind
    synthetic: bool
    core_canonical_json: bytes

    def __post_init__(self) -> None:
        _require_count(
            self.task_index,
            label="qualification evidence task index",
            maximum=ADR0331_QUALIFICATION_TASK_COUNT - 1,
        )
        _require_digest(self.task_sha256, label="qualification evidence task")
        if not isinstance(self.kind, QualificationEvidenceKind):
            raise TypeError("qualification evidence kind must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("qualification evidence synthetic flag must be boolean")
        if not isinstance(self.core_canonical_json, bytes):
            raise TypeError("qualification evidence core bytes must be immutable")
        value = json.loads(self.core_canonical_json)
        if (
            not isinstance(value, dict)
            or frozenset(value) != _EVIDENCE_CORE_KEYS
            or canonical_journal_json_bytes(value) != self.core_canonical_json
        ):
            raise ValueError("qualification evidence core is not canonical")
        if (
            value.get("task_index") != self.task_index
            or value.get("task_sha256") != self.task_sha256
            or value.get("kind") != self.kind.value
            or value.get("synthetic") is not self.synthetic
            or value.get("version") != _EVIDENCE_VERSION
        ):
            raise ValueError("qualification evidence metadata differs from its core")

    @property
    def core(self) -> dict[str, object]:
        value = json.loads(self.core_canonical_json)
        if not isinstance(value, dict):
            raise AssertionError("qualification evidence core lost its object type")
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
            raise AssertionError("qualification evidence result lost its object type")
        if self.kind is QualificationEvidenceKind.UNEXPECTED_EXCEPTION:
            return 0
        return _require_count(
            result["public_call_count"],
            label="qualification evidence public calls",
            maximum=1,
        )


def _build_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    kind: QualificationEvidenceKind,
    synthetic: bool,
    result_payload: Mapping[str, object],
) -> QualificationArmEvidence:
    if not isinstance(task, ActionWidthQualificationTask):
        raise TypeError("qualification evidence requires a semantic task")
    core = {
        "arm": task.arm.value,
        "context_index": task.context_index,
        "context_semantic_sha256": task.context_semantic_digest,
        "kind": kind.value,
        "result": result_payload,
        "synthetic": synthetic,
        "task_index": task_index,
        "task_sha256": task.digest,
        "version": _EVIDENCE_VERSION,
    }
    return QualificationArmEvidence(
        task_index=task_index,
        task_sha256=task.digest,
        kind=kind,
        synthetic=synthetic,
        core_canonical_json=canonical_journal_json_bytes(core),
    )


def _fraction_policy_payload(
    policy: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        tuple((value.numerator, value.denominator) for value in row)
        for row in policy
    )


def _accepted_result_payload(
    value: CertifiedReducedSizingAcceptedV2,
) -> dict[str, object]:
    if not isinstance(value, CertifiedReducedSizingAcceptedV2):
        raise TypeError("accepted evidence requires a certified accepted result")
    return {
        "certified_gap_hex": _float_hex(
            value.certified_gap_chips,
            label="accepted certified gap",
        ),
        "certified_upper_hex": _float_hex(
            value.certified_upper_bound_chips,
            label="accepted certified upper",
        ),
        "consumer_protocol_sha256": value.consumer_protocol_sha256,
        "consumer_source_sha256": value.consumer_source_sha256,
        "context_label": value.context_id,
        "emitted_action": value.emitted_action,
        "exact_opening_policy": _fraction_policy_payload(
            value.exact_opening_policy
        ),
        "fallback_disposition": value.fallback_disposition.value,
        "feasible_lower_hex": _float_hex(
            value.feasible_behavioral_lower_bound_chips,
            label="accepted feasible lower",
        ),
        "legal_raise_scope": value.legal_raise_scope.value,
        "legal_raise_set_sha256": value.legal_raise_set_sha256,
        "linear_program_sha256": value.solution.linear_program_sha256,
        "public_call_count": value.public_highs_ds_invocation_count,
        "public_state_sha256": value.public_state_sha256,
        "raw_inequality_multipliers_hex": tuple(
            _float_hex(item, label="accepted inequality multiplier")
            for item in value.solution.raw_inequality_multipliers
        ),
        "raise_to_totals": tuple(item.chips for item in value.legal_raise_to_totals),
        "reduced_bet_increments": tuple(
            item.chips for item in value.reduced_bet_increments
        ),
        "request_sha256": value.request_sha256,
        "responder_best_actions": value.responder_best_actions,
        "response_model": value.response_model.value,
        "signed_gap_hex": _float_hex(
            value.signed_certificate_gap_chips,
            label="accepted signed gap",
        ),
        "synthetic_result": False,
        "type": "accepted",
    }


def _rejected_result_payload(
    value: CertifiedReducedSizingRejectedV2,
) -> dict[str, object]:
    if not isinstance(value, CertifiedReducedSizingRejectedV2):
        raise TypeError("rejected evidence requires a certified rejection")
    return {
        "consumer_protocol_sha256": value.consumer_protocol_sha256,
        "consumer_source_sha256": value.consumer_source_sha256,
        "context_label": value.context_id,
        "emitted_action": value.emitted_action,
        "exception_chain": tuple(
            {
                "message": item.message,
                "module": item.module,
                "type_name": item.type_name,
            }
            for item in value.exception_chain
        ),
        "fallback_disposition": value.fallback_disposition.value,
        "legal_raise_set_sha256": value.legal_raise_set_sha256,
        "public_call_count": value.public_highs_ds_invocation_count,
        "public_state_sha256": value.public_state_sha256,
        "reason": value.reason.value,
        "request_sha256": value.request_sha256,
        "stage": value.stage.value,
        "synthetic_result": False,
        "type": "rejected",
    }


def evidence_from_consumer_result(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    result: object,
) -> QualificationArmEvidence:
    if isinstance(result, CertifiedReducedSizingAcceptedV2):
        if result.request != task.request:
            raise ValueError("accepted qualification evidence belongs to another task")
        return _build_evidence(
            task_index=task_index,
            task=task,
            kind=QualificationEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=_accepted_result_payload(result),
        )
    if isinstance(result, CertifiedReducedSizingRejectedV2):
        if result.request != task.request:
            raise ValueError("rejected qualification evidence belongs to another task")
        return _build_evidence(
            task_index=task_index,
            task=task,
            kind=QualificationEvidenceKind.REJECTED,
            synthetic=False,
            result_payload=_rejected_result_payload(result),
        )
    raise TypeError("qualification consumer returned a nonsemantic result")


def _exception_payload(error: Exception) -> tuple[dict[str, str], ...]:
    records: list[dict[str, str]] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        records.append(
            {
                "message": str(current),
                "module": type(current).__module__,
                "type_name": type(current).__qualname__,
            }
        )
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return tuple(records)


def _unexpected_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    error: Exception,
    synthetic: bool,
) -> QualificationArmEvidence:
    return _build_evidence(
        task_index=task_index,
        task=task,
        kind=QualificationEvidenceKind.UNEXPECTED_EXCEPTION,
        synthetic=synthetic,
        result_payload={
            "exception_chain": _exception_payload(error),
            "invocation_count_complete": False,
            "synthetic_result": synthetic,
            "type": "unexpected_exception",
        },
    )


_ACCEPTED_RESULT_KEYS = frozenset(
    {
        "certified_gap_hex",
        "certified_upper_hex",
        "consumer_protocol_sha256",
        "consumer_source_sha256",
        "context_label",
        "emitted_action",
        "exact_opening_policy",
        "fallback_disposition",
        "feasible_lower_hex",
        "legal_raise_scope",
        "legal_raise_set_sha256",
        "linear_program_sha256",
        "public_call_count",
        "public_state_sha256",
        "raw_inequality_multipliers_hex",
        "raise_to_totals",
        "reduced_bet_increments",
        "request_sha256",
        "responder_best_actions",
        "response_model",
        "signed_gap_hex",
        "synthetic_result",
        "type",
    }
)
_REJECTED_RESULT_KEYS = frozenset(
    {
        "consumer_protocol_sha256",
        "consumer_source_sha256",
        "context_label",
        "emitted_action",
        "exception_chain",
        "fallback_disposition",
        "legal_raise_set_sha256",
        "public_call_count",
        "public_state_sha256",
        "reason",
        "request_sha256",
        "stage",
        "synthetic_result",
        "type",
    }
)
_UNEXPECTED_RESULT_KEYS = frozenset(
    {
        "exception_chain",
        "invocation_count_complete",
        "synthetic_result",
        "type",
    }
)


def _validate_exception_chain(value: object, *, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise TypeError(f"{label} requires a nonempty exception chain")
    for item in value:
        record = _require_exact_keys(
            item,
            frozenset({"message", "module", "type_name"}),
            label=f"{label} exception",
        )
        if (
            not isinstance(record["module"], str)
            or not record["module"]
            or not isinstance(record["type_name"], str)
            or not record["type_name"]
            or not isinstance(record["message"], str)
        ):
            raise ValueError(f"{label} exception fields are invalid")


def _validate_fraction_policy(
    value: object,
    *,
    row_count: int,
    action_count: int,
) -> tuple[tuple[Fraction, ...], ...]:
    if not isinstance(value, list) or len(value) != row_count:
        raise ValueError("qualification evidence policy has the wrong row count")
    rebound: list[tuple[Fraction, ...]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != action_count:
            raise ValueError("qualification evidence policy has the wrong width")
        fractions: list[Fraction] = []
        for pair in row:
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or any(isinstance(item, bool) or not isinstance(item, int) for item in pair)
            ):
                raise ValueError("qualification evidence policy fraction is malformed")
            fraction = Fraction(pair[0], pair[1])
            if (
                fraction < 0
                or fraction.numerator != pair[0]
                or fraction.denominator != pair[1]
            ):
                raise ValueError(
                    "qualification evidence policy fraction is noncanonical or negative"
                )
            fractions.append(fraction)
        if sum(fractions, start=Fraction(0)) != 1:
            raise ValueError("qualification evidence policy row is not stochastic")
        rebound.append(tuple(fractions))
    return tuple(rebound)


def _exact_behavioral_value(
    *,
    task: ActionWidthQualificationTask,
    policy: tuple[tuple[Fraction, ...], ...],
    bet_sizes: tuple[int, ...],
) -> tuple[float, tuple[tuple[str, ...], ...]]:
    """Independently reconstruct the feasible policy value from exact inputs."""

    half_pot = Fraction(task.request.betting.pot, 2)
    probabilities = task.request.joint_probabilities
    signs = task.request.showdown_signs
    value = Fraction(0)
    for opener, probability_row in enumerate(probabilities):
        for responder, probability in enumerate(probability_row):
            value += (
                probability
                * policy[opener][0]
                * signs[opener][responder]
                * half_pot
            )
    best_actions: list[tuple[str, ...]] = []
    for responder in range(len(probabilities[0])):
        actions: list[str] = []
        for bet_index, bet in enumerate(bet_sizes):
            fold = sum(
                (
                    probabilities[opener][responder]
                    * policy[opener][bet_index + 1]
                    * half_pot
                    for opener in range(len(probabilities))
                ),
                start=Fraction(0),
            )
            call = sum(
                (
                    probabilities[opener][responder]
                    * policy[opener][bet_index + 1]
                    * signs[opener][responder]
                    * (half_pot + bet)
                    for opener in range(len(probabilities))
                ),
                start=Fraction(0),
            )
            if fold <= call:
                actions.append("fold")
                value += fold
            else:
                actions.append("call")
                value += call
        best_actions.append(tuple(actions))
    return float(value), tuple(best_actions)


def _rebind_real_accepted_value_witness(
    *,
    task: ActionWidthQualificationTask,
    accepted: dict[str, object],
    policy: tuple[tuple[Fraction, ...], ...],
    multipliers: tuple[float, ...],
    lower: float,
    upper: float,
) -> None:
    bound = _bind_request(task.request)
    bet_sizes = tuple(item.chips for item in bound.reduced_bet_increments)
    linear_program = compile_reduced_river_sizing_lp(
        pot=task.request.betting.pot,
        stack=bound.maximum_bet_increment.chips,
        minimum_bet=bound.minimum_bet_increment.chips,
        joint_probabilities=task.request.joint_probabilities,
        showdown_signs=task.request.showdown_signs,
        bet_sizes=bet_sizes,
    )
    if len(multipliers) != len(linear_program.rows):
        raise ValueError("accepted qualification multiplier width drifted")
    reconstructed_lower, reconstructed_actions = _exact_behavioral_value(
        task=task,
        policy=policy,
        bet_sizes=bet_sizes,
    )
    actions = tuple(tuple(item for item in row) for row in accepted["responder_best_actions"])
    if reconstructed_lower != lower or reconstructed_actions != actions:
        raise ValueError("accepted qualification behavioral witness drifted")
    certificate = certify_bounded_minimization_lower_bound(
        tuple(-value for value in linear_program.objective),
        linear_program.coefficients,
        linear_program.bounds,
        multipliers,
        variable_lower_bounds=linear_program.trusted_box_lower_bounds,
        variable_upper_bounds=linear_program.trusted_box_upper_bounds,
    )
    reconstructed_upper = (
        -certificate.lower_bound + linear_program.objective_offset_chips
    )
    if reconstructed_upper != upper:
        raise ValueError("accepted qualification dual certificate drifted")


def _validate_evidence_against_task(
    evidence: QualificationArmEvidence,
    *,
    task: ActionWidthQualificationTask,
    expect_synthetic: bool,
) -> None:
    core = evidence.core
    if (
        evidence.task_sha256 != task.digest
        or evidence.synthetic is not expect_synthetic
        or core["arm"] != task.arm.value
        or core["context_index"] != task.context_index
        or core["context_semantic_sha256"] != task.context_semantic_digest
    ):
        raise ValueError("qualification evidence differs from its scheduled task")
    result = core["result"]
    if not isinstance(result, dict):
        raise TypeError("qualification evidence result must be an object")
    if result.get("synthetic_result") is not expect_synthetic:
        raise ValueError("qualification evidence synthetic provenance drifted")

    if evidence.kind is QualificationEvidenceKind.ACCEPTED:
        accepted = _require_exact_keys(
            result,
            _ACCEPTED_RESULT_KEYS,
            label="accepted qualification evidence",
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
            raise ValueError("accepted qualification evidence identity drifted")
        lower = _require_float_hex(
            accepted["feasible_lower_hex"],
            label="accepted feasible lower",
        )
        upper = _require_float_hex(
            accepted["certified_upper_hex"],
            label="accepted certified upper",
        )
        signed_gap = _require_float_hex(
            accepted["signed_gap_hex"],
            label="accepted signed gap",
        )
        gap = _require_float_hex(
            accepted["certified_gap_hex"],
            label="accepted certified gap",
        )
        if (
            lower > upper
            or signed_gap != upper - lower
            or gap != max(0.0, signed_gap)
        ):
            raise ValueError("accepted qualification evidence interval drifted")
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
            raise ValueError("accepted qualification response evidence is malformed")
        multipliers_value = accepted["raw_inequality_multipliers_hex"]
        if not isinstance(multipliers_value, list):
            raise TypeError("accepted qualification multipliers must be an array")
        multipliers = tuple(
            _require_float_hex(
                item,
                label="accepted qualification inequality multiplier",
            )
            for item in multipliers_value
        )
        expected_multiplier_count = (
            2 * len(task.request.joint_probabilities)
            + 2
            * len(task.request.joint_probabilities[0])
            * len(task.request.legal_raise_to_totals)
        )
        if len(multipliers) != expected_multiplier_count:
            raise ValueError("accepted qualification multiplier width drifted")
        if not expect_synthetic:
            _rebind_real_accepted_value_witness(
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
                raise ValueError("accepted qualification certificate width drifted")
    elif evidence.kind is QualificationEvidenceKind.REJECTED:
        rejected = _require_exact_keys(
            result,
            _REJECTED_RESULT_KEYS,
            label="rejected qualification evidence",
        )
        if (
            rejected["type"] != "rejected"
            or rejected["context_label"] != task.request.context_id
            or rejected["consumer_protocol_sha256"]
            != ADR0321_CONSUMER_PROTOCOL_SHA256
            or rejected["stage"]
            not in {value.value for value in CertifiedSizingConsumerStageV2}
            or rejected["reason"]
            not in {value.value for value in CertifiedSizingConsumerRejectionReasonV2}
            or rejected["fallback_disposition"]
            != CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            or rejected["emitted_action"] is not None
        ):
            raise ValueError("rejected qualification evidence identity drifted")
        calls = _require_count(
            rejected["public_call_count"],
            label="rejected qualification public calls",
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
                label=f"rejected qualification {key}",
                optional=True,
            )
        _validate_exception_chain(
            rejected["exception_chain"],
            label="rejected qualification evidence",
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
            raise ValueError("rejected qualification stage/reason contract drifted")
        bound = _bind_request(task.request)
        if (
            rejected["request_sha256"] != bound.request_sha256
            or rejected["public_state_sha256"] != bound.public_state_sha256
            or rejected["legal_raise_set_sha256"] != bound.legal_raise_set_sha256
        ):
            raise ValueError("rejected qualification request identity drifted")
        source_expected = stage is not CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION
        if rejected["consumer_source_sha256"] != (
            ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ]
            if source_expected
            else None
        ):
            raise ValueError("rejected qualification source identity drifted")
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
            raise ValueError("rejected qualification invocation count drifted")
    else:
        unexpected = _require_exact_keys(
            result,
            _UNEXPECTED_RESULT_KEYS,
            label="unexpected qualification evidence",
        )
        if (
            unexpected["type"] != "unexpected_exception"
            or unexpected["invocation_count_complete"] is not False
        ):
            raise ValueError("unexpected qualification evidence claims complete calls")
        _validate_exception_chain(
            unexpected["exception_chain"],
            label="unexpected qualification evidence",
        )


def _rebind_evidence(
    payload: dict[str, object],
    *,
    task: ActionWidthQualificationTask,
    task_index: int,
    expect_synthetic: bool,
) -> QualificationArmEvidence:
    core = _verify_sealed_payload(
        payload,
        digest_field="evidence_sha256",
        label=f"qualification arm {task_index}",
    )
    try:
        kind = QualificationEvidenceKind(core["kind"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("qualification evidence has an unknown kind") from error
    evidence = QualificationArmEvidence(
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
class QualificationContextOutcome:
    context_index: int
    full_evidence_sha256: str
    width_two_evidence_sha256: str
    regret: CertifiedChipRegretInterval
    classification: ActionWidthQualificationClassification

    def __post_init__(self) -> None:
        _require_count(
            self.context_index,
            label="qualification context outcome index",
            maximum=95,
        )
        _require_digest(self.full_evidence_sha256, label="qualification full evidence")
        _require_digest(
            self.width_two_evidence_sha256,
            label="qualification width-two evidence",
        )
        if not isinstance(self.regret, CertifiedChipRegretInterval):
            raise TypeError("qualification context outcome requires certified regret")
        if not isinstance(self.classification, ActionWidthQualificationClassification):
            raise TypeError("qualification context outcome classification must be semantic")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "classification": self.classification.value,
            "context_index": self.context_index,
            "full_evidence_sha256": self.full_evidence_sha256,
            "regret": {
                "nonnegative_lower_hex": self.regret.nonnegative_lower_chips.hex(),
                "nonnegative_upper_hex": self.regret.nonnegative_upper_chips.hex(),
                "signed_lower_hex": self.regret.signed_lower_chips.hex(),
                "signed_upper_hex": self.regret.signed_upper_chips.hex(),
            },
            "width_two_evidence_sha256": self.width_two_evidence_sha256,
        }


class NonReplayQualificationStopReason(StrEnum):
    TARGET_REACHED = "target_reached"
    POOL_EXHAUSTED = "pool_exhausted"
    AMBIGUOUS = "ambiguous"
    NESTED_VALUE_REVERSAL = "nested_value_reversal"
    CONSUMER_REJECTED = "consumer_rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


@dataclass(frozen=True, slots=True)
class _DerivedQualificationState:
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    stop_reason: NonReplayQualificationStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool


def _accepted_interval_from_evidence(
    evidence: QualificationArmEvidence,
) -> CertifiedChipValueInterval:
    result = evidence.core["result"]
    if not isinstance(result, dict):
        raise AssertionError("accepted evidence result lost its object type")
    return CertifiedChipValueInterval(
        lower_chips=_require_float_hex(
            result["feasible_lower_hex"],
            label="qualification evidence lower",
        ),
        upper_chips=_require_float_hex(
            result["certified_upper_hex"],
            label="qualification evidence upper",
        ),
    )


def _derive_state(
    evidences: tuple[QualificationArmEvidence, ...],
    *,
    pool: FreshActionWidthNonReplayPool,
) -> _DerivedQualificationState:
    outcomes: list[QualificationContextOutcome] = []
    qualified: list[int] = []
    pending_full: QualificationArmEvidence | None = None
    stop: NonReplayQualificationStopReason | None = None
    known_calls = 0
    complete_calls = True
    for index, evidence in enumerate(evidences):
        if evidence.task_index != index:
            raise ValueError("qualification evidence is not a contiguous task prefix")
        if stop is not None:
            raise ValueError("qualification evidence continues past a terminal stop")
        if evidence.kind is QualificationEvidenceKind.UNEXPECTED_EXCEPTION:
            stop = NonReplayQualificationStopReason.UNEXPECTED_EXCEPTION
            complete_calls = False
            continue
        known_calls += evidence.public_call_count
        if evidence.kind is QualificationEvidenceKind.REJECTED:
            stop = NonReplayQualificationStopReason.CONSUMER_REJECTED
            continue
        if index % 2 == 0:
            pending_full = evidence
            continue
        if pending_full is None or pending_full.task_index != index - 1:
            raise ValueError("qualification width-two evidence lacks its full arm")
        context_index = index // 2
        try:
            regret = certified_full_minus_subset_regret(
                full=_accepted_interval_from_evidence(pending_full),
                subset=_accepted_interval_from_evidence(evidence),
                reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
            )
        except ValueError:
            stop = NonReplayQualificationStopReason.NESTED_VALUE_REVERSAL
            pending_full = None
            continue
        classification = classify_action_width_opportunity(
            regret=regret,
            payoff_span_chips=pool.contexts[context_index].payoff_span_chips,
            opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
            ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
        )
        outcomes.append(
            QualificationContextOutcome(
                context_index=context_index,
                full_evidence_sha256=pending_full.digest,
                width_two_evidence_sha256=evidence.digest,
                regret=regret,
                classification=classification,
            )
        )
        pending_full = None
        if classification is ActionWidthQualificationClassification.AMBIGUOUS:
            stop = NonReplayQualificationStopReason.AMBIGUOUS
        elif classification is ActionWidthQualificationClassification.QUALIFYING:
            qualified.append(context_index)
            if len(qualified) == ADR0331_QUALIFICATION_TARGET:
                stop = NonReplayQualificationStopReason.TARGET_REACHED
    if len(evidences) == ADR0331_QUALIFICATION_TASK_COUNT and stop is None:
        if pending_full is not None:
            raise AssertionError("complete qualification task count ended on a full arm")
        stop = NonReplayQualificationStopReason.POOL_EXHAUSTED
    return _DerivedQualificationState(
        evidences=evidences,
        outcomes=tuple(outcomes),
        qualified_indices=tuple(qualified),
        stop_reason=stop,
        known_public_call_count=known_calls,
        invocation_count_complete=complete_calls,
    )


def _campaign_sha256(
    *,
    schedule: NonReplayQualificationSchedule,
    qualification_source_sha256: str,
    synthetic: bool,
) -> str:
    _require_digest(
        qualification_source_sha256,
        label="qualification campaign source",
    )
    return sha256(
        canonical_journal_json_bytes(
            {
                "artifact_relative_path": (
                    ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH
                ),
                "pool_sha256": schedule.pool_sha256,
                "protocol_sha256": ADR0331_QUALIFICATION_PROTOCOL_SHA256,
                "qualification_source_sha256": qualification_source_sha256,
                "schedule_sha256": schedule.digest,
                "synthetic": synthetic,
                "version": "adr0331-nonreplay-qualification-campaign-v1",
            }
        )
    ).hexdigest()


def _header_payload(
    *,
    schedule: NonReplayQualificationSchedule,
    qualification_source_sha256: str,
    campaign_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    return _sealed_payload(
        {
            "artifact_relative_path": ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
            "campaign_sha256": campaign_sha256,
            "pool_sha256": schedule.pool_sha256,
            "protocol_sha256": ADR0331_QUALIFICATION_PROTOCOL_SHA256,
            "qualification_source_sha256": qualification_source_sha256,
            "schedule_sha256": schedule.digest,
            "synthetic": synthetic,
            "target": ADR0331_QUALIFICATION_TARGET,
            "task_count": ADR0331_QUALIFICATION_TASK_COUNT,
            "version": _HEADER_VERSION,
        },
        digest_field="header_sha256",
    )


def _terminal_payload(
    *,
    state: _DerivedQualificationState,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayQualificationSchedule,
    qualification_source_sha256: str,
    campaign_sha256: str,
    final_observation_line_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    if state.stop_reason is None:
        raise ValueError("qualification terminal requires a derived stop")
    _require_digest(
        final_observation_line_sha256,
        label="qualification final observation line",
    )
    return _sealed_payload(
        {
            "campaign_sha256": campaign_sha256,
            "context_outcomes": tuple(value.payload for value in state.outcomes),
            "evidence_sha256s": tuple(value.digest for value in state.evidences),
            "final_observation_line_sha256": final_observation_line_sha256,
            "invocation_count_complete": state.invocation_count_complete,
            "known_public_call_count": state.known_public_call_count,
            "observed_arm_count": len(state.evidences),
            "pool_sha256": pool.digest,
            "qualification_source_sha256": qualification_source_sha256,
            "qualified_context_semantic_sha256s": tuple(
                pool.contexts[index].semantic_digest
                for index in state.qualified_indices
            ),
            "qualified_indices": state.qualified_indices,
            "record_count": len(state.evidences) + 2,
            "schedule_sha256": schedule.digest,
            "stop_reason": state.stop_reason.value,
            "synthetic": synthetic,
            "version": _TERMINAL_VERSION,
        },
        digest_field="terminal_sha256",
    )


@dataclass(frozen=True, slots=True)
class QualificationJournalPrefix:
    recovery: JournalRecovery
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    pending_stop_reason: NonReplayQualificationStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.recovery, JournalRecovery):
            raise TypeError("qualification prefix requires generic journal recovery")
        if self.recovery.is_complete:
            raise ValueError("qualification prefix cannot contain a terminal journal")


@dataclass(frozen=True, slots=True)
class QualificationJournalResult:
    campaign_sha256: str
    journal_sha256: str
    journal_byte_count: int
    terminal_sha256: str
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    stop_reason: NonReplayQualificationStopReason
    known_public_call_count: int
    invocation_count_complete: bool
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("qualification campaign", self.campaign_sha256),
            ("qualification journal", self.journal_sha256),
            ("qualification terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=label)
        _require_count(
            self.journal_byte_count,
            label="qualification journal byte count",
        )
        if not isinstance(self.stop_reason, NonReplayQualificationStopReason):
            raise TypeError("qualification journal result stop must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("qualification journal result synthetic flag must be boolean")


QualificationJournalRebinding = QualificationJournalPrefix | QualificationJournalResult


def rebind_adr0331_qualification_journal(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> QualificationJournalRebinding:
    if not isinstance(raw, bytes):
        raise TypeError("qualification journal rebinding requires immutable bytes")
    if not isinstance(synthetic, bool):
        raise TypeError("qualification journal synthetic mode must be boolean")
    qualification_source = verify_adr0333_qualification_source_and_dependencies()
    pool = verify_adr0332_nonreplay_source_and_pool()
    schedule = build_adr0331_nonreplay_qualification_schedule()
    campaign = _campaign_sha256(
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        synthetic=synthetic,
    )
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=ADR0331_QUALIFICATION_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign,
    )
    records = recovery.records
    if not records:
        return QualificationJournalPrefix(
            recovery=recovery,
            evidences=(),
            outcomes=(),
            qualified_indices=(),
            pending_stop_reason=None,
            known_public_call_count=0,
            invocation_count_complete=True,
        )
    header = records[0]
    if header.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("qualification journal first record is not its header")
    expected_header = _header_payload(
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        campaign_sha256=campaign,
        synthetic=synthetic,
    )
    if header.body.payload != expected_header:
        raise ValueError("qualification journal header differs from its sealed schedule")
    if header.body.semantic_identity_sha256 != expected_header["header_sha256"]:
        raise ValueError("qualification journal header semantic identity drifted")

    terminal_record: JournalRecordEnvelope | None = None
    observation_records = records[1:]
    if observation_records and observation_records[-1].body.kind is JournalRecordKind.TERMINAL:
        terminal_record = observation_records[-1]
        observation_records = observation_records[:-1]
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in observation_records
    ):
        raise ValueError("qualification journal has a non-observation inside its arm prefix")
    if len(observation_records) > ADR0331_QUALIFICATION_TASK_COUNT:
        raise ValueError("qualification journal exceeds its sealed task count")
    evidences: list[QualificationArmEvidence] = []
    for index, record in enumerate(observation_records):
        evidence = _rebind_evidence(
            record.body.payload,
            task=schedule.tasks[index],
            task_index=index,
            expect_synthetic=synthetic,
        )
        if record.body.semantic_identity_sha256 != evidence.digest:
            raise ValueError("qualification observation semantic identity drifted")
        evidences.append(evidence)
    state = _derive_state(tuple(evidences), pool=pool)

    if terminal_record is None:
        return QualificationJournalPrefix(
            recovery=recovery,
            evidences=state.evidences,
            outcomes=state.outcomes,
            qualified_indices=state.qualified_indices,
            pending_stop_reason=state.stop_reason,
            known_public_call_count=state.known_public_call_count,
            invocation_count_complete=state.invocation_count_complete,
        )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("qualification journal terminal has trailing invalid bytes")
    if not evidences:
        raise ValueError("qualification journal terminal lacks an observation")
    expected_terminal = _terminal_payload(
        state=state,
        pool=pool,
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        campaign_sha256=campaign,
        final_observation_line_sha256=observation_records[-1].line_sha256,
        synthetic=synthetic,
    )
    terminal_payload = terminal_record.body.payload
    _verify_sealed_payload(
        terminal_payload,
        digest_field="terminal_sha256",
        label="qualification terminal",
    )
    if canonical_journal_json_bytes(terminal_payload) != canonical_journal_json_bytes(
        expected_terminal
    ):
        raise ValueError("qualification terminal differs from journal-derived evidence")
    if terminal_record.body.semantic_identity_sha256 != terminal_payload["terminal_sha256"]:
        raise ValueError("qualification terminal semantic identity drifted")
    if state.stop_reason is None:
        raise AssertionError("qualification terminal validated without a stop")
    return QualificationJournalResult(
        campaign_sha256=campaign,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
        terminal_sha256=terminal_payload["terminal_sha256"],
        evidences=state.evidences,
        outcomes=state.outcomes,
        qualified_indices=state.qualified_indices,
        stop_reason=state.stop_reason,
        known_public_call_count=state.known_public_call_count,
        invocation_count_complete=state.invocation_count_complete,
        synthetic=synthetic,
    )


@dataclass(frozen=True, slots=True)
class QualificationLaunchRejected:
    reason: str
    output_path: Path
    exception_chain: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("qualification launch rejection reason must be nonempty")
        if not isinstance(self.output_path, Path):
            raise TypeError("qualification launch rejection path must be a Path")
        if not self.exception_chain:
            raise ValueError("qualification launch rejection requires an exception chain")


class QualificationExecutionPhase(StrEnum):
    HEADER_APPEND = "header_append"
    NEXT_CALL_AUTHORIZATION = "next_call_authorization"
    ARM_EVIDENCE = "arm_evidence"
    OBSERVATION_APPEND = "observation_append"
    SEMANTIC_REDUCTION = "semantic_reduction"
    TERMINAL_APPEND = "terminal_append"
    JOURNAL_CLOSE = "journal_close"
    FINAL_REBIND = "final_rebind"


@dataclass(frozen=True, slots=True)
class QualificationExecutionFailed:
    reason: str
    phase: QualificationExecutionPhase
    output_path: Path
    failed_task_index: int | None
    unreceipted_arm_invocation: bool
    durably_recorded_evidences: tuple[QualificationArmEvidence, ...]
    known_public_call_count: int
    invocation_count_complete: bool
    raw_journal_bytes: bytes | None
    recovery: JournalRecovery | None
    exception_chain: tuple[dict[str, str], ...]
    recovery_exception_chain: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("qualification execution failure reason must be nonempty")
        if not isinstance(self.phase, QualificationExecutionPhase):
            raise TypeError("qualification execution failure phase must be semantic")
        if not isinstance(self.output_path, Path):
            raise TypeError("qualification execution failure path must be a Path")
        if self.failed_task_index is not None:
            _require_count(
                self.failed_task_index,
                label="qualification failed task index",
                maximum=ADR0331_QUALIFICATION_TASK_COUNT - 1,
            )
        if not isinstance(self.unreceipted_arm_invocation, bool):
            raise TypeError("qualification unreceipted-call flag must be boolean")
        if not isinstance(self.durably_recorded_evidences, tuple) or any(
            not isinstance(item, QualificationArmEvidence)
            for item in self.durably_recorded_evidences
        ):
            raise TypeError("qualification execution failure evidence is not semantic")
        expected_calls = sum(
            item.public_call_count for item in self.durably_recorded_evidences
        )
        if (
            isinstance(self.known_public_call_count, bool)
            or not isinstance(self.known_public_call_count, int)
            or self.known_public_call_count != expected_calls
        ):
            raise ValueError("qualification execution failure call count drifted")
        expected_complete = (
            not self.unreceipted_arm_invocation
            and all(
                item.kind is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
                for item in self.durably_recorded_evidences
            )
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("qualification execution failure completeness drifted")
        if not self.exception_chain:
            raise ValueError("qualification execution failure requires an exception chain")
        if self.raw_journal_bytes is None:
            if self.recovery is not None or not self.recovery_exception_chain:
                raise ValueError("qualification unreadable journal lacks recovery evidence")
        elif not isinstance(self.raw_journal_bytes, bytes):
            raise TypeError("qualification execution failure raw journal is mutable")
        elif self.recovery is None:
            if not self.recovery_exception_chain:
                raise ValueError("qualification raw journal lacks recovery evidence")
        elif (
            not isinstance(self.recovery, JournalRecovery)
            or self.recovery.raw_bytes != self.raw_journal_bytes
        ):
            raise ValueError("qualification execution failure recovery lost raw bytes")

    @property
    def raw_journal_sha256(self) -> str | None:
        if self.raw_journal_bytes is None:
            return None
        return sha256(self.raw_journal_bytes).hexdigest()

    @property
    def raw_journal_byte_count(self) -> int | None:
        if self.raw_journal_bytes is None:
            return None
        return len(self.raw_journal_bytes)


QualificationRunResult = (
    QualificationJournalRebinding
    | QualificationLaunchRejected
    | QualificationExecutionFailed
)
_ArmOwner = Callable[[int, ActionWidthQualificationTask], QualificationArmEvidence]


def _execution_failure(
    *,
    writer: DurableEvidenceJournalWriter,
    output_path: Path,
    campaign_sha256: str,
    phase: QualificationExecutionPhase,
    failed_task_index: int | None,
    unreceipted_arm_invocation: bool,
    evidences: tuple[QualificationArmEvidence, ...],
    error: Exception,
) -> QualificationExecutionFailed:
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
                expected_protocol_sha256=ADR0331_QUALIFICATION_PROTOCOL_SHA256,
                expected_campaign_sha256=campaign_sha256,
            )
        except Exception as recovery_error:
            recovery_exception_chain = _exception_payload(recovery_error)
    return QualificationExecutionFailed(
        reason="qualification failed after exclusive journal creation",
        phase=phase,
        output_path=output_path,
        failed_task_index=failed_task_index,
        unreceipted_arm_invocation=unreceipted_arm_invocation,
        durably_recorded_evidences=evidences,
        known_public_call_count=sum(item.public_call_count for item in evidences),
        invocation_count_complete=(
            not unreceipted_arm_invocation
            and all(
                item.kind is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
                for item in evidences
            )
        ),
        raw_journal_bytes=raw,
        recovery=recovery,
        exception_chain=exception_chain,
        recovery_exception_chain=recovery_exception_chain,
    )


def _execute_qualification(
    *,
    output_path: Path,
    pool: FreshActionWidthNonReplayPool,
    schedule: NonReplayQualificationSchedule,
    qualification_source_sha256: str,
    arm_owner: _ArmOwner,
    synthetic: bool,
) -> QualificationJournalResult | QualificationExecutionFailed:
    campaign = _campaign_sha256(
        schedule=schedule,
        qualification_source_sha256=qualification_source_sha256,
        synthetic=synthetic,
    )
    writer = DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=ADR0331_QUALIFICATION_PROTOCOL_SHA256,
        campaign_sha256=campaign,
    )
    evidences: list[QualificationArmEvidence] = []
    phase = QualificationExecutionPhase.HEADER_APPEND
    failed_task_index: int | None = None
    unreceipted_arm_invocation = False
    try:
        header_payload = _header_payload(
            schedule=schedule,
            qualification_source_sha256=qualification_source_sha256,
            campaign_sha256=campaign,
            synthetic=synthetic,
        )
        authorization = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header_payload["header_sha256"],
            payload=header_payload,
        )
        for task_index, task in enumerate(schedule.tasks):
            phase = QualificationExecutionPhase.NEXT_CALL_AUTHORIZATION
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
                raise RuntimeError("qualification call lacks its preceding durable receipt")
            phase = QualificationExecutionPhase.ARM_EVIDENCE
            unreceipted_arm_invocation = True
            try:
                evidence = arm_owner(task_index, task)
                if not isinstance(evidence, QualificationArmEvidence):
                    raise TypeError(
                        "qualification arm owner returned nonsemantic evidence"
                    )
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
            phase = QualificationExecutionPhase.OBSERVATION_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
            evidences.append(evidence)
            unreceipted_arm_invocation = False
            phase = QualificationExecutionPhase.SEMANTIC_REDUCTION
            state = _derive_state(tuple(evidences), pool=pool)
            if state.stop_reason is None:
                continue
            terminal_payload = _terminal_payload(
                state=state,
                pool=pool,
                schedule=schedule,
                qualification_source_sha256=qualification_source_sha256,
                campaign_sha256=campaign,
                final_observation_line_sha256=authorization.line_sha256,
                synthetic=synthetic,
            )
            phase = QualificationExecutionPhase.TERMINAL_APPEND
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
    phase = QualificationExecutionPhase.JOURNAL_CLOSE
    try:
        writer.close()
        phase = QualificationExecutionPhase.FINAL_REBIND
        rebound = rebind_adr0331_qualification_journal(
            output_path.read_bytes(),
            synthetic=synthetic,
        )
        if not isinstance(rebound, QualificationJournalResult):
            raise RuntimeError("qualification execution ended without a terminal result")
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
    task: ActionWidthQualificationTask,
) -> QualificationArmEvidence:
    result = consume_certified_reduced_sizing_v2(task.request)
    return evidence_from_consumer_result(
        task_index=task_index,
        task=task,
        result=result,
    )


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH
    )


def run_and_retain_adr0331_nonreplay_qualification() -> QualificationRunResult:
    """Open the replacement qualification only after the committed source seal."""

    output_path = _artifact_path()
    try:
        qualification_source = verify_adr0333_qualification_source_and_dependencies()
        pool = verify_adr0332_nonreplay_source_and_pool()
        schedule = build_adr0331_nonreplay_qualification_schedule()
    except Exception as error:
        return QualificationLaunchRejected(
            reason="qualification source or schedule preflight rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )
    try:
        return _execute_qualification(
            output_path=output_path,
            pool=pool,
            schedule=schedule,
            qualification_source_sha256=qualification_source,
            arm_owner=_real_arm_owner,
            synthetic=False,
        )
    except Exception as error:
        return QualificationLaunchRejected(
            reason="qualification exclusive journal launch rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )


def synthetic_accepted_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    lower_chips: float,
    upper_chips: float,
) -> QualificationArmEvidence:
    """Build fake accepted evidence without a consumer or solver call."""

    lower = float(lower_chips)
    upper = float(upper_chips)
    if not isfinite(lower) or not isfinite(upper) or lower > upper:
        raise ValueError("synthetic accepted endpoints are invalid")
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
        kind=QualificationEvidenceKind.ACCEPTED,
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


def synthetic_rejected_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    public_call_count: int = 1,
) -> QualificationArmEvidence:
    """Build fake typed rejection evidence without a consumer or solver call."""

    calls = _require_count(
        public_call_count,
        label="synthetic rejection public calls",
        maximum=1,
    )
    if calls != 1:
        raise ValueError("synthetic adapter rejection requires exactly one public call")
    bound = _bind_request(task.request)
    return _build_evidence(
        task_index=task_index,
        task=task,
        kind=QualificationEvidenceKind.REJECTED,
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
                    "message": "synthetic typed rejection",
                    "module": "pontius.synthetic",
                    "type_name": "SyntheticConsumerRejection",
                },
            ),
            "fallback_disposition": (
                CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK.value
            ),
            "legal_raise_set_sha256": bound.legal_raise_set_sha256,
            "public_call_count": calls,
            "public_state_sha256": bound.public_state_sha256,
            "reason": CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED.value,
            "request_sha256": bound.request_sha256,
            "stage": CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER.value,
            "synthetic_result": True,
            "type": "rejected",
        },
    )


__all__ = [
    "ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH",
    "ADR0331_QUALIFICATION_PROTOCOL",
    "ADR0331_QUALIFICATION_PROTOCOL_SHA256",
    "ADR0331_QUALIFICATION_TARGET",
    "ADR0331_QUALIFICATION_TASK_COUNT",
    "NonReplayQualificationSchedule",
    "NonReplayQualificationStopReason",
    "QualificationArmEvidence",
    "QualificationContextOutcome",
    "QualificationEvidenceKind",
    "QualificationExecutionFailed",
    "QualificationExecutionPhase",
    "QualificationJournalPrefix",
    "QualificationJournalRebinding",
    "QualificationJournalResult",
    "QualificationLaunchRejected",
    "QualificationRunResult",
    "build_adr0331_nonreplay_qualification_schedule",
    "evidence_from_consumer_result",
    "rebind_adr0331_qualification_journal",
    "run_and_retain_adr0331_nonreplay_qualification",
    "synthetic_accepted_evidence",
    "synthetic_rejected_evidence",
    "verify_adr0332_nonreplay_source_and_pool",
    "verify_adr0333_qualification_source_and_dependencies",
]
