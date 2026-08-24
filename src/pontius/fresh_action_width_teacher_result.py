"""Rebind the retained ADR-0323 exhaustive-teacher result without solving.

The value-owning runner was invoked exactly once through ADR-0327's retained
wrapper.  This module treats the committed canonical artifact as evidence,
reconstructs every value-free task and exact request identity, independently
recomputes all interval reductions and nested digests, and exposes immutable
research diagnostics.  It has no solver or action-emission path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from .certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    _bind_request,
    canonical_lf_source_sha256,
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
)
from .fresh_action_width_structures import ADR0323_RAISE_WIDTHS, RaiseActionWidth
from .fresh_action_width_teacher import (
    ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
    ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    ExhaustiveTeacherArm,
    ExhaustiveTeacherSchedule,
    ExhaustiveTeacherTask,
    NormalizedTeacherRegretInterval,
    TeacherSubsetCandidate,
    build_adr0323_exhaustive_teacher_schedule,
    normalize_teacher_regret,
    reduce_teacher_width,
    verify_adr0327_exhaustive_teacher_schedule,
)
from .fresh_action_width_teacher_seal import (
    ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
    ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST,
)


ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-exhaustive-development-teacher-v1.json"
)
ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES = 4_975_258
ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256 = (
    "f94a76d283c18b681998d1c54e6037a21575b214fe613e0f58221734f4314661"
)
ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256 = (
    "8f808b87862f2c38b53a333434b74cd4f1bafe2ac639b4d9b2dad57283f85e6d"
)
ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256 = (
    "6da6f43a02c6a0f97237bcdc9c66f845bac5735c290236d0ffdab481b7f82765"
)


_TOP_LEVEL_KEYS = {
    "contexts",
    "digest",
    "failure",
    "panel_sha256",
    "pool_sha256",
    "public_call_count",
    "qualification_result_sha256",
    "result_type",
    "schedule_sha256",
    "stop_reason",
    "teacher_source_sha256",
    "version",
}
_CONTEXT_KEYS = {
    "context_result_sha256",
    "context_semantic_digest",
    "full",
    "full_task",
    "panel_position",
    "payoff_span_chips",
    "pool_index",
    "widths",
}
_TASK_KEYS = {
    "arm",
    "context_semantic_digest",
    "legal_raise_set_sha256",
    "linear_program_sha256",
    "ordinal",
    "panel_position",
    "pool_index",
    "raise_to_totals",
    "raise_width",
    "request_sha256",
    "subset_index",
    "task_sha256",
}
_ACCEPTED_KEYS = {
    "bet_increments",
    "certified_gap_hex",
    "certified_upper_hex",
    "consumer_protocol_sha256",
    "consumer_source_sha256",
    "feasible_lower_hex",
    "legal_raise_set_sha256",
    "linear_program_sha256",
    "public_call_count",
    "public_state_sha256",
    "raise_to_totals",
    "request_sha256",
    "signed_gap_hex",
}
_WIDTH_KEYS = {
    "envelope",
    "full_minus_teacher_regret",
    "full_request_sha256",
    "full_value",
    "normalized_full_minus_teacher_regret",
    "payoff_span_chips",
    "raise_width",
    "subset_observations",
    "width_result_sha256",
}
_OBSERVATION_KEYS = {
    "accepted",
    "full_request_sha256",
    "full_value",
    "normalized_regret",
    "observation_sha256",
    "payoff_span_chips",
    "regret",
    "task",
}
_VALUE_KEYS = {"lower_hex", "upper_hex"}
_REGRET_KEYS = {
    "nonnegative_lower_hex",
    "nonnegative_upper_hex",
    "signed_lower_hex",
    "signed_upper_hex",
}
_ENVELOPE_KEYS = {
    "equivalent_subset_indices",
    "lower_hex",
    "nondominated_subset_indices",
    "unique_best_subset_index",
    "upper_hex",
}


@dataclass(frozen=True, slots=True)
class RetainedExhaustiveTeacherSubset:
    task_ordinal: int
    subset_index: int
    request_sha256: str
    legal_raise_set_sha256: str
    linear_program_sha256: str
    raise_to_totals: tuple[int, ...]
    value_lower_chips: float
    value_upper_chips: float
    regret_lower_chips: float
    regret_upper_chips: float
    normalized_regret_lower: float
    normalized_regret_upper: float
    observation_sha256: str


@dataclass(frozen=True, slots=True)
class RetainedExhaustiveTeacherWidth:
    raise_width: RaiseActionWidth
    subsets: tuple[RetainedExhaustiveTeacherSubset, ...]
    teacher_lower_chips: float
    teacher_upper_chips: float
    nondominated_subset_indices: tuple[int, ...]
    equivalent_subset_indices: tuple[int, ...]
    unique_best_subset_index: int | None
    full_regret_lower_chips: float
    full_regret_upper_chips: float
    normalized_full_regret_lower: float
    normalized_full_regret_upper: float
    width_result_sha256: str

    @property
    def nondominated_subset_count(self) -> int:
        return len(self.nondominated_subset_indices)


@dataclass(frozen=True, slots=True)
class RetainedExhaustiveTeacherContext:
    panel_position: int
    pool_index: int
    context_semantic_digest: str
    payoff_span_chips: int
    full_lower_chips: float
    full_upper_chips: float
    widths: tuple[RetainedExhaustiveTeacherWidth, ...]
    context_result_sha256: str


@dataclass(frozen=True, slots=True)
class RetainedExhaustiveTeacherResult:
    artifact_sha256: str
    payload_sha256: str
    campaign_result_sha256: str
    contexts: tuple[RetainedExhaustiveTeacherContext, ...]
    public_highs_ds_invocation_count: int

    @property
    def context_width_count(self) -> int:
        return sum(len(context.widths) for context in self.contexts)


@dataclass(frozen=True, slots=True)
class _AcceptedEvidence:
    digest_payload: dict[str, object]
    value: CertifiedChipValueInterval


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_RELATIVE_PATH
    )


def _require_exact_keys(
    value: object,
    expected: set[str],
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} fields differ from the committed schema")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_exact_int(value: object, *, label: str, minimum: int = 0) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer")
    if value < minimum:
        raise ValueError(f"{label} is below its minimum")
    return value


def _require_exact_int_list(
    value: object,
    *,
    label: str,
    minimum: int = 0,
) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a JSON integer list")
    return tuple(
        _require_exact_int(item, label=f"{label} item {index}", minimum=minimum)
        for index, item in enumerate(value)
    )


def _require_float_hex(value: object, *, label: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a float hex string")
    try:
        decoded = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not a float hex string") from error
    if not isfinite(decoded) or decoded.hex() != value:
        raise ValueError(f"{label} is not a canonical finite float hex string")
    return decoded


def _value_interval(value: object, *, label: str) -> CertifiedChipValueInterval:
    payload = _require_exact_keys(value, _VALUE_KEYS, label=label)
    return CertifiedChipValueInterval(
        lower_chips=_require_float_hex(payload["lower_hex"], label=f"{label} lower"),
        upper_chips=_require_float_hex(payload["upper_hex"], label=f"{label} upper"),
    )


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


def _expected_task_payload(task: ExhaustiveTeacherTask) -> dict[str, object]:
    return {
        "arm": task.arm.value,
        "context_semantic_digest": task.context_semantic_digest,
        "legal_raise_set_sha256": task.legal_raise_set_sha256,
        "linear_program_sha256": task.linear_program_sha256,
        "ordinal": task.ordinal,
        "panel_position": task.panel_position,
        "pool_index": task.pool_index,
        "raise_to_totals": list(task.raise_to_totals),
        "raise_width": None if task.raise_width is None else task.raise_width.count,
        "request_sha256": task.request_sha256,
        "subset_index": task.subset_index,
        "task_sha256": task.digest,
    }


def _verify_task_payload(
    value: object,
    *,
    task: ExhaustiveTeacherTask,
    label: str,
) -> None:
    payload = _require_exact_keys(value, _TASK_KEYS, label=label)
    _require_exact_int(payload["ordinal"], label=f"{label} ordinal")
    _require_exact_int(payload["panel_position"], label=f"{label} panel position")
    _require_exact_int(payload["pool_index"], label=f"{label} pool index")
    _require_exact_int_list(
        payload["raise_to_totals"],
        label=f"{label} raise-to totals",
        minimum=1,
    )
    if payload["raise_width"] is not None:
        _require_exact_int(
            payload["raise_width"],
            label=f"{label} raise width",
            minimum=2,
        )
    if payload["subset_index"] is not None:
        _require_exact_int(
            payload["subset_index"],
            label=f"{label} subset index",
        )
    if payload != _expected_task_payload(task):
        raise ValueError(f"{label} differs from its sealed schedule task")


def _verify_accepted_payload(
    value: object,
    *,
    task: ExhaustiveTeacherTask,
    label: str,
) -> _AcceptedEvidence:
    payload = _require_exact_keys(value, _ACCEPTED_KEYS, label=label)
    bound = _bind_request(task.request)
    _require_exact_int_list(
        payload["bet_increments"],
        label=f"{label} bet increments",
        minimum=1,
    )
    _require_exact_int_list(
        payload["raise_to_totals"],
        label=f"{label} raise-to totals",
        minimum=1,
    )
    _require_exact_int(
        payload["public_call_count"],
        label=f"{label} public call count",
        minimum=1,
    )
    expected_identity = {
        "bet_increments": [
            amount.chips for amount in bound.reduced_bet_increments
        ],
        "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
        "consumer_source_sha256": ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST[
            "certified_reduced_sizing_consumer_v2.py"
        ],
        "legal_raise_set_sha256": bound.legal_raise_set_sha256,
        "linear_program_sha256": bound.linear_program_sha256,
        "public_call_count": 1,
        "public_state_sha256": bound.public_state_sha256,
        "raise_to_totals": [amount.chips for amount in bound.legal_raise_to_totals],
        "request_sha256": bound.request_sha256,
    }
    if any(payload[key] != expected for key, expected in expected_identity.items()):
        raise ValueError(f"{label} identity or call count drifted")
    lower = _require_float_hex(
        payload["feasible_lower_hex"],
        label=f"{label} feasible lower",
    )
    upper = _require_float_hex(
        payload["certified_upper_hex"],
        label=f"{label} certified upper",
    )
    signed_gap = _require_float_hex(
        payload["signed_gap_hex"],
        label=f"{label} signed gap",
    )
    gap = _require_float_hex(
        payload["certified_gap_hex"],
        label=f"{label} certified gap",
    )
    if lower > upper or signed_gap != upper - lower or gap != max(0.0, signed_gap):
        raise ValueError(f"{label} certificate endpoints or gap drifted")
    digest_payload = {
        "bet_increments": tuple(expected_identity["bet_increments"]),
        "certified_gap_hex": gap.hex(),
        "certified_upper_hex": upper.hex(),
        "consumer_protocol_sha256": expected_identity["consumer_protocol_sha256"],
        "consumer_source_sha256": expected_identity["consumer_source_sha256"],
        "feasible_lower_hex": lower.hex(),
        "legal_raise_set_sha256": expected_identity["legal_raise_set_sha256"],
        "linear_program_sha256": expected_identity["linear_program_sha256"],
        "public_call_count": 1,
        "public_state_sha256": expected_identity["public_state_sha256"],
        "raise_to_totals": tuple(expected_identity["raise_to_totals"]),
        "request_sha256": expected_identity["request_sha256"],
        "signed_gap_hex": signed_gap.hex(),
    }
    return _AcceptedEvidence(
        digest_payload=digest_payload,
        value=CertifiedChipValueInterval(lower_chips=lower, upper_chips=upper),
    )


def _verify_observation(
    value: object,
    *,
    task: ExhaustiveTeacherTask,
    full_request_sha256: str,
    full_value: CertifiedChipValueInterval,
    payoff_span_chips: int,
    label: str,
) -> tuple[RetainedExhaustiveTeacherSubset, TeacherSubsetCandidate, str]:
    payload = _require_exact_keys(value, _OBSERVATION_KEYS, label=label)
    if task.arm is not ExhaustiveTeacherArm.ANCHORED_SUBSET:
        raise ValueError(f"{label} is not bound to a subset task")
    _verify_task_payload(payload["task"], task=task, label=f"{label} task")
    accepted = _verify_accepted_payload(
        payload["accepted"],
        task=task,
        label=f"{label} accepted",
    )
    if payload["full_request_sha256"] != full_request_sha256:
        raise ValueError(f"{label} full request identity drifted")
    if _require_exact_int(
        payload["payoff_span_chips"],
        label=f"{label} payoff span",
        minimum=1,
    ) != payoff_span_chips:
        raise ValueError(f"{label} payoff span drifted")
    if _value_interval(payload["full_value"], label=f"{label} full value") != full_value:
        raise ValueError(f"{label} full value drifted")
    regret = certified_full_minus_subset_regret(
        full=full_value,
        subset=accepted.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    normalized = normalize_teacher_regret(
        regret,
        payoff_span_chips=payoff_span_chips,
    )
    if _require_exact_keys(
        payload["regret"],
        _REGRET_KEYS,
        label=f"{label} regret",
    ) != _regret_payload(regret):
        raise ValueError(f"{label} regret endpoint direction drifted")
    if _require_exact_keys(
        payload["normalized_regret"],
        _VALUE_KEYS,
        label=f"{label} normalized regret",
    ) != _normalized_payload(normalized):
        raise ValueError(f"{label} normalized regret drifted")
    observation_sha256 = _canonical_sha256(
        {
            "accepted": accepted.digest_payload,
            "full_request_sha256": full_request_sha256,
            "full_value": {
                "lower_hex": full_value.lower_chips.hex(),
                "upper_hex": full_value.upper_chips.hex(),
            },
            "normalized_regret": _normalized_payload(normalized),
            "payoff_span_chips": payoff_span_chips,
            "regret": _regret_payload(regret),
            "task_sha256": task.digest,
            "version": "adr0323-exhaustive-teacher-subset-observation-v1",
        }
    )
    if payload["observation_sha256"] != observation_sha256:
        raise ValueError(f"{label} nested digest drifted")
    if task.subset_index is None:
        raise AssertionError("sealed subset task lost its subset index")
    retained = RetainedExhaustiveTeacherSubset(
        task_ordinal=task.ordinal,
        subset_index=task.subset_index,
        request_sha256=task.request_sha256,
        legal_raise_set_sha256=task.legal_raise_set_sha256,
        linear_program_sha256=task.linear_program_sha256,
        raise_to_totals=task.raise_to_totals,
        value_lower_chips=accepted.value.lower_chips,
        value_upper_chips=accepted.value.upper_chips,
        regret_lower_chips=regret.nonnegative_lower_chips,
        regret_upper_chips=regret.nonnegative_upper_chips,
        normalized_regret_lower=normalized.lower,
        normalized_regret_upper=normalized.upper,
        observation_sha256=observation_sha256,
    )
    candidate = TeacherSubsetCandidate(
        subset_index=task.subset_index,
        raise_to_totals=task.raise_to_totals,
        value=accepted.value,
    )
    return retained, candidate, observation_sha256


def _verify_width(
    value: object,
    *,
    raise_width: RaiseActionWidth,
    tasks: tuple[ExhaustiveTeacherTask, ...],
    full_request_sha256: str,
    full_value: CertifiedChipValueInterval,
    payoff_span_chips: int,
    label: str,
) -> tuple[RetainedExhaustiveTeacherWidth, str]:
    payload = _require_exact_keys(value, _WIDTH_KEYS, label=label)
    if _require_exact_int(
        payload["raise_width"],
        label=f"{label} raise width",
        minimum=2,
    ) != raise_width.count:
        raise ValueError(f"{label} semantic width drifted")
    if payload["full_request_sha256"] != full_request_sha256:
        raise ValueError(f"{label} full request identity drifted")
    if _require_exact_int(
        payload["payoff_span_chips"],
        label=f"{label} payoff span",
        minimum=1,
    ) != payoff_span_chips:
        raise ValueError(f"{label} payoff span drifted")
    if _value_interval(payload["full_value"], label=f"{label} full value") != full_value:
        raise ValueError(f"{label} full value drifted")
    raw_observations = payload["subset_observations"]
    if not isinstance(raw_observations, list) or len(raw_observations) != len(tasks):
        raise ValueError(f"{label} subset family is incomplete")
    retained_subsets: list[RetainedExhaustiveTeacherSubset] = []
    candidates: list[TeacherSubsetCandidate] = []
    observation_sha256: list[str] = []
    for subset_index, (raw_observation, task) in enumerate(
        zip(raw_observations, tasks, strict=True)
    ):
        if task.raise_width != raise_width or task.subset_index != subset_index:
            raise ValueError(f"{label} sealed task order drifted")
        retained, candidate, digest = _verify_observation(
            raw_observation,
            task=task,
            full_request_sha256=full_request_sha256,
            full_value=full_value,
            payoff_span_chips=payoff_span_chips,
            label=f"{label} subset {subset_index}",
        )
        retained_subsets.append(retained)
        candidates.append(candidate)
        observation_sha256.append(digest)
    envelope = reduce_teacher_width(
        tuple(candidates),
        raise_width=raise_width,
        equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    )
    raw_envelope = _require_exact_keys(
        payload["envelope"],
        _ENVELOPE_KEYS,
        label=f"{label} envelope",
    )
    _require_exact_int_list(
        raw_envelope["equivalent_subset_indices"],
        label=f"{label} equivalent subset indices",
    )
    _require_exact_int_list(
        raw_envelope["nondominated_subset_indices"],
        label=f"{label} nondominated subset indices",
    )
    if raw_envelope["unique_best_subset_index"] is not None:
        _require_exact_int(
            raw_envelope["unique_best_subset_index"],
            label=f"{label} unique best subset index",
        )
    expected_envelope = {
        "equivalent_subset_indices": list(envelope.equivalent_subset_indices),
        "lower_hex": envelope.value.lower_chips.hex(),
        "nondominated_subset_indices": list(envelope.nondominated_subset_indices),
        "unique_best_subset_index": envelope.unique_best_subset_index,
        "upper_hex": envelope.value.upper_chips.hex(),
    }
    if raw_envelope != expected_envelope:
        raise ValueError(f"{label} set-valued envelope drifted")
    full_regret = certified_full_minus_subset_regret(
        full=full_value,
        subset=envelope.value,
        reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
    )
    normalized_full_regret = normalize_teacher_regret(
        full_regret,
        payoff_span_chips=payoff_span_chips,
    )
    if _require_exact_keys(
        payload["full_minus_teacher_regret"],
        _REGRET_KEYS,
        label=f"{label} full regret",
    ) != _regret_payload(full_regret):
        raise ValueError(f"{label} full-minus-teacher regret drifted")
    if _require_exact_keys(
        payload["normalized_full_minus_teacher_regret"],
        _VALUE_KEYS,
        label=f"{label} normalized full regret",
    ) != _normalized_payload(normalized_full_regret):
        raise ValueError(f"{label} normalized full regret drifted")
    width_sha256 = _canonical_sha256(
        {
            "envelope": {
                "equivalent_subset_indices": envelope.equivalent_subset_indices,
                "lower_hex": envelope.value.lower_chips.hex(),
                "nondominated_subset_indices": envelope.nondominated_subset_indices,
                "unique_best_subset_index": envelope.unique_best_subset_index,
                "upper_hex": envelope.value.upper_chips.hex(),
            },
            "full_minus_teacher_regret": _regret_payload(full_regret),
            "full_request_sha256": full_request_sha256,
            "full_value": {
                "lower_hex": full_value.lower_chips.hex(),
                "upper_hex": full_value.upper_chips.hex(),
            },
            "normalized_full_minus_teacher_regret": _normalized_payload(
                normalized_full_regret
            ),
            "payoff_span_chips": payoff_span_chips,
            "raise_width": raise_width.count,
            "subset_observation_sha256": tuple(observation_sha256),
            "version": "adr0323-exhaustive-teacher-width-result-v1",
        }
    )
    if payload["width_result_sha256"] != width_sha256:
        raise ValueError(f"{label} nested digest drifted")
    return (
        RetainedExhaustiveTeacherWidth(
            raise_width=raise_width,
            subsets=tuple(retained_subsets),
            teacher_lower_chips=envelope.value.lower_chips,
            teacher_upper_chips=envelope.value.upper_chips,
            nondominated_subset_indices=envelope.nondominated_subset_indices,
            equivalent_subset_indices=envelope.equivalent_subset_indices,
            unique_best_subset_index=envelope.unique_best_subset_index,
            full_regret_lower_chips=full_regret.nonnegative_lower_chips,
            full_regret_upper_chips=full_regret.nonnegative_upper_chips,
            normalized_full_regret_lower=normalized_full_regret.lower,
            normalized_full_regret_upper=normalized_full_regret.upper,
            width_result_sha256=width_sha256,
        ),
        width_sha256,
    )


def _verify_context(
    value: object,
    *,
    panel_position: int,
    schedule: ExhaustiveTeacherSchedule,
    payoff_span_chips: int,
) -> tuple[RetainedExhaustiveTeacherContext, str, int]:
    label = f"teacher context {panel_position}"
    payload = _require_exact_keys(value, _CONTEXT_KEYS, label=label)
    expected_pool_index = ADR0323_QUALIFIED_POOL_INDICES[panel_position]
    expected_context_digest = ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS[
        panel_position
    ]
    if (
        _require_exact_int(
            payload["panel_position"],
            label=f"{label} panel position",
        )
        != panel_position
        or _require_exact_int(
            payload["pool_index"],
            label=f"{label} pool index",
        )
        != expected_pool_index
        or payload["context_semantic_digest"] != expected_context_digest
    ):
        raise ValueError(f"{label} panel identity drifted")
    if _require_exact_int(
        payload["payoff_span_chips"],
        label=f"{label} payoff span",
        minimum=1,
    ) != payoff_span_chips:
        raise ValueError(f"{label} payoff span drifted")
    tasks = tuple(
        task for task in schedule.tasks if task.panel_position == panel_position
    )
    full_task = tasks[0]
    _verify_task_payload(payload["full_task"], task=full_task, label=f"{label} full task")
    full = _verify_accepted_payload(
        payload["full"],
        task=full_task,
        label=f"{label} full accepted",
    )
    raw_widths = payload["widths"]
    if not isinstance(raw_widths, list) or len(raw_widths) != len(ADR0323_RAISE_WIDTHS):
        raise ValueError(f"{label} width family is incomplete")
    retained_widths: list[RetainedExhaustiveTeacherWidth] = []
    width_sha256: list[str] = []
    call_count = 1
    for raw_width, raise_width in zip(raw_widths, ADR0323_RAISE_WIDTHS, strict=True):
        width_tasks = tuple(task for task in tasks[1:] if task.raise_width == raise_width)
        retained, digest = _verify_width(
            raw_width,
            raise_width=raise_width,
            tasks=width_tasks,
            full_request_sha256=full_task.request_sha256,
            full_value=full.value,
            payoff_span_chips=payoff_span_chips,
            label=f"{label} width {raise_width.count}",
        )
        retained_widths.append(retained)
        width_sha256.append(digest)
        call_count += len(width_tasks)
    context_sha256 = _canonical_sha256(
        {
            "context_semantic_digest": expected_context_digest,
            "full": full.digest_payload,
            "full_task_sha256": full_task.digest,
            "panel_position": panel_position,
            "payoff_span_chips": payoff_span_chips,
            "pool_index": expected_pool_index,
            "width_result_sha256": tuple(width_sha256),
            "version": "adr0323-exhaustive-teacher-context-result-v1",
        }
    )
    if payload["context_result_sha256"] != context_sha256:
        raise ValueError(f"{label} nested digest drifted")
    return (
        RetainedExhaustiveTeacherContext(
            panel_position=panel_position,
            pool_index=expected_pool_index,
            context_semantic_digest=expected_context_digest,
            payoff_span_chips=payoff_span_chips,
            full_lower_chips=full.value.lower_chips,
            full_upper_chips=full.value.upper_chips,
            widths=tuple(retained_widths),
            context_result_sha256=context_sha256,
        ),
        context_sha256,
        call_count,
    )


def exhaustive_teacher_result_protocol_sha256() -> str:
    return _canonical_sha256(
        {
            "artifact_bytes": ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES,
            "artifact_sha256": ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256,
            "campaign_result_sha256": ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256,
            "context_count": 16,
            "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
            "payload_sha256": ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256,
            "public_call_count": ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
            "rebind": (
                "tasks+requests+legal-sets+linear-programs+float-endpoints+"
                "regrets+normalization+set-envelope+nested-digests-without-solving"
            ),
            "result_type": "campaign_result",
            "schedule_sha256": ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
            "stop_reason": "completed",
            "teacher_source_sha256": ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST[
                "fresh_action_width_teacher.py"
            ],
            "version": "adr0328-exhaustive-teacher-result-protocol-v1",
        }
    )


def verify_adr0328_teacher_result_source_and_dependencies() -> str:
    from .fresh_action_width_teacher_result_seal import (
        ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256,
        ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST,
    )

    source_root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(source_root / name)
        for name in ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0328 exhaustive-teacher result source closure drifted")
    if exhaustive_teacher_result_protocol_sha256() != (
        ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256
    ):
        raise RuntimeError("ADR-0328 exhaustive-teacher result protocol drifted")
    return actual["fresh_action_width_teacher_result.py"]


def _rebind_completed_payload(
    decoded: object,
    *,
    schedule: ExhaustiveTeacherSchedule,
) -> RetainedExhaustiveTeacherResult:
    root = _require_exact_keys(decoded, _TOP_LEVEL_KEYS, label="teacher result")
    pool = verify_adr0324_structure_source_and_pool()
    _require_exact_int(
        root["public_call_count"],
        label="teacher result public call count",
        minimum=1,
    )
    expected_scalars = {
        "failure": None,
        "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
        "pool_sha256": pool.digest,
        "public_call_count": ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
        "qualification_result_sha256": ADR0323_QUALIFICATION_RESULT_SHA256,
        "result_type": "campaign_result",
        "schedule_sha256": ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
        "stop_reason": "completed",
        "teacher_source_sha256": ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST[
            "fresh_action_width_teacher.py"
        ],
        "version": "adr0323-exhaustive-teacher-artifact-v1",
    }
    if any(root[key] != expected for key, expected in expected_scalars.items()):
        raise ValueError("teacher result terminal state or provenance drifted")
    raw_contexts = root["contexts"]
    if not isinstance(raw_contexts, list) or len(raw_contexts) != 16:
        raise ValueError("teacher result must retain all 16 contexts")
    retained_contexts: list[RetainedExhaustiveTeacherContext] = []
    context_sha256: list[str] = []
    public_calls = 0
    for panel_position, raw_context in enumerate(raw_contexts):
        pool_index = ADR0323_QUALIFIED_POOL_INDICES[panel_position]
        context = pool.contexts[pool_index]
        retained, digest, calls = _verify_context(
            raw_context,
            panel_position=panel_position,
            schedule=schedule,
            payoff_span_chips=context.payoff_span_chips,
        )
        retained_contexts.append(retained)
        context_sha256.append(digest)
        public_calls += calls
    campaign_sha256 = _canonical_sha256(
        {
            "context_sha256": tuple(context_sha256),
            "failure_sha256": None,
            "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
            "pool_sha256": pool.digest,
            "qualification_result_sha256": ADR0323_QUALIFICATION_RESULT_SHA256,
            "schedule_sha256": ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
            "stop_reason": "completed",
            "teacher_source_sha256": ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST[
                "fresh_action_width_teacher.py"
            ],
            "version": "adr0323-exhaustive-teacher-campaign-result-v1",
        }
    )
    if (
        root["digest"] != campaign_sha256
        or campaign_sha256 != ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256
    ):
        raise ValueError("teacher campaign result digest drifted")
    if (
        root["public_call_count"] != public_calls
        or public_calls != ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT
    ):
        raise ValueError("teacher public HiGHS-DS call count drifted")
    return RetainedExhaustiveTeacherResult(
        artifact_sha256=ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256,
        payload_sha256=ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256,
        campaign_result_sha256=campaign_sha256,
        contexts=tuple(retained_contexts),
        public_highs_ds_invocation_count=public_calls,
    )


def verify_adr0323_exhaustive_teacher_result_artifact(
    path: Path | None = None,
) -> RetainedExhaustiveTeacherResult:
    """Verify and rebind every retained field without invoking a solver."""

    verify_adr0328_teacher_result_source_and_dependencies()
    schedule = build_adr0323_exhaustive_teacher_schedule()
    verify_adr0327_exhaustive_teacher_schedule(schedule)
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES:
        raise ValueError("ADR-0323 exhaustive-teacher artifact byte count drifted")
    if hashlib.sha256(raw).hexdigest() != ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256:
        raise ValueError("ADR-0323 exhaustive-teacher artifact SHA-256 drifted")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("ADR-0323 exhaustive-teacher artifact must have one final LF")
    payload = raw[:-1]
    if hashlib.sha256(payload).hexdigest() != ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256:
        raise ValueError("ADR-0323 exhaustive-teacher payload SHA-256 drifted")
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ADR-0323 exhaustive-teacher artifact is not JSON") from error
    if json.dumps(
        decoded,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii") != payload:
        raise ValueError("ADR-0323 exhaustive-teacher artifact is not canonical JSON")
    return _rebind_completed_payload(decoded, schedule=schedule)


__all__ = [
    "ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES",
    "ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_RELATIVE_PATH",
    "ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256",
    "ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256",
    "ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256",
    "RetainedExhaustiveTeacherContext",
    "RetainedExhaustiveTeacherResult",
    "RetainedExhaustiveTeacherSubset",
    "RetainedExhaustiveTeacherWidth",
    "exhaustive_teacher_result_protocol_sha256",
    "verify_adr0323_exhaustive_teacher_result_artifact",
    "verify_adr0328_teacher_result_source_and_dependencies",
]
