"""Artifact-only semantic correction for ADR-0314's retained audit gate.

This module cannot invoke an LP backend, exact enumerator, reconstruction, or
certificate.  It accepts only canonical retained evidence, checks the complete
artifact identity before parsing, replays every unchanged HiGHS conjunct from
stored verification fields, and distinguishes a required unique maximum row
from the complete set of rows above an allowance.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Any

from .runner_harness_v2 import decode_strict_json_object, read_bounded_file_once

ADR0315_ANALYZER_VERSION = "adr0314-retained-audit-semantic-gate-correction-v1"
ADR0314_RETAINED_ARTIFACT_SHA256 = (
    "1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a"
)
ADR0314_RETAINED_ARTIFACT_BYTES = 110_068_679
ADR0313_RUNNER_VERSION = "candidate-independent-native-simplex-audit-runner-v1"
ADR0313_RUNNER_SOURCE_SHA256 = "cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16"
ADR0311_COMPLETE_CORPUS_SHA256 = "4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3"
ADR0313_ENVIRONMENT_SUBTREE_SHA256 = (
    "07137f9e865a9320102c3705777a111795df5b83b80a7db756140e65c979bd20"
)
ADR0313_PROTOCOL_SUBTREE_SHA256 = "0a9254cc546a63e944007dbe3c78b3a7d1f451f9ab44b7a9ec94325a26505377"

_CAMPAIGN_DATACLASS = "pontius.native_simplex_audit_runner.AuditCampaignResult"
_OBSERVATION_DATACLASS = "pontius.native_simplex_audit_runner.AuditInvocationObservation"
_INVOCATION_DATACLASS = "pontius.native_simplex_audit_runner.ScheduledAuditInvocation"
_BACKEND_RESULT_DATACLASS = "pontius.native_simplex_audit_runner.BackendRawResult"
_EXCEPTION_DATACLASS = "pontius.native_simplex_audit_runner.AuditExceptionRecord"
_TRACE_DATACLASS = "pontius.native_simplex_audit_runner.NativeVerificationTrace"
_COORDINATES_DATACLASS = "pontius.native_simplex_audit_runner.NativeFailureCoordinates"
_MICRO_VERIFICATION_DATACLASS = "pontius.native_simplex_audit_runner.MicroAuditVerification"
_SIZING_VERIFICATION_DATACLASS = "pontius.native_simplex_audit_runner.SizingAuditVerification"
_COORDINATE_DIAGNOSTICS_DATACLASS = (
    "pontius.native_simplex_audit_runner.BackendCoordinateDiagnostics"
)
_CERTIFICATE_DIAGNOSTICS_DATACLASS = (
    "pontius.native_simplex_audit_runner.BackendCertificateDiagnostics"
)
_EXACT_MICRO_DATACLASS = "pontius.native_simplex_audit_runner.ExactMicroEnumeration"

_BACKEND_ORDER = ("native", "highs-ds", "highs-ipm")
_HIGH_BACKENDS = ("highs-ds", "highs-ipm")
_VARIANT_KINDS = (
    "canonical",
    "row-permutation",
    "variable-permutation",
    "dyadic-row-scaling",
    "redundancy",
)
_CAMPAIGN_FIELDS = {
    "runner_version",
    "runner_source_sha256",
    "corpus_sha256",
    "environment",
    "protocol",
    "observations",
    "sealed_adr0311",
}
_OBSERVATION_FIELDS = {
    "invocation",
    "backend_result",
    "exact_micro_work",
    "coordinate_diagnostics",
    "certificate_diagnostics",
    "micro_verification",
    "sizing_verification",
    "native_failure_coordinates",
    "runner_failures",
}
_INVOCATION_FIELDS = {"ordinal", "task_index", "base_id", "variant_id", "backend"}
_BACKEND_RESULT_FIELDS = {
    "backend",
    "termination",
    "status_code",
    "status_text",
    "message",
    "iterations",
    "crossover_iterations",
    "primal_variant_coordinates",
    "reported_maximization_objective",
    "dual_hint_variant_rows",
    "dual_hint_convention",
    "elapsed_seconds",
    "exception",
    "native_verification_trace",
}
_EXCEPTION_FIELDS = {
    "stage",
    "module",
    "qualname",
    "message",
    "arguments",
    "traceback_frames",
}
_TRACE_FIELDS = {
    "primal_variant_coordinates",
    "raw_maximization_objective",
    "dual_hint_variant_rows",
    "pivots",
    "constraint_residuals_variant_rows",
    "verification_allowance",
}
_COORDINATE_FIELDS = {
    "failing_variant_rows",
    "failing_canonical_rows",
    "maximum_variant_residual",
    "verification_allowance",
}


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _canonical_result_value(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("corrected audit result cannot encode a nonfinite float")
        return {"float_hex": value.hex()}
    if isinstance(value, tuple):
        return tuple(_canonical_result_value(item) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("corrected audit result mapping keys must be text")
        return {key: _canonical_result_value(item) for key, item in sorted(value.items())}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "dataclass": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                field.name: _canonical_result_value(getattr(value, field.name))
                for field in fields(value)
            },
        }
    raise TypeError(f"corrected audit result cannot encode {type(value).__qualname__}")


def canonical_corrected_gate_bytes(value: object) -> bytes:
    """Return deterministic exact-float JSON bytes for correction evidence."""

    return _canonical_json_bytes(_canonical_result_value(value))


def canonical_lf_source_sha256(path: Path) -> str:
    """Hash source after a fail-closed CRLF-to-LF normalization."""

    if not isinstance(path, Path):
        raise TypeError("source path must be a Path")
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in raw:
        raise ValueError("source contains a non-CRLF carriage return")
    return sha256(raw).hexdigest()


def _require_positive_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


@dataclass(frozen=True, slots=True)
class MicroVariantComparisonAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="micro variant comparison allowance")


@dataclass(frozen=True, slots=True)
class CrossBackendSizingAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="cross-backend sizing allowance")


@dataclass(frozen=True, slots=True)
class CrossVariantSizingAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="cross-variant sizing allowance")


def _require_canonical_float_hex(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be float.hex text")
    try:
        decoded = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not float.hex text") from error
    if not isfinite(decoded) or decoded.hex() != value:
        raise ValueError(f"{label} must be canonical and finite")
    return value


@dataclass(frozen=True, slots=True)
class KnownRegressionSignature:
    base_id: str
    variant_id: str
    exception_module: str
    exception_qualname: str
    exception_message: str
    pivots: int
    verification_allowance_hex: str
    maximum_residual_hex: str
    required_unique_maximum_row: int
    expected_complete_failing_rows: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("regression base id", self.base_id),
            ("regression variant id", self.variant_id),
            ("regression exception module", self.exception_module),
            ("regression exception qualname", self.exception_qualname),
            ("regression exception message", self.exception_message),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be nonempty")
        for label, value in (
            ("regression pivots", self.pivots),
            ("regression maximum row", self.required_unique_maximum_row),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{label} must be nonnegative")
        _require_canonical_float_hex(
            self.verification_allowance_hex,
            label="regression verification allowance",
        )
        _require_canonical_float_hex(
            self.maximum_residual_hex,
            label="regression maximum residual",
        )
        if self.expected_complete_failing_rows is not None and (
            not isinstance(self.expected_complete_failing_rows, tuple)
            or any(
                isinstance(row, bool) or not isinstance(row, int) or row < 0
                for row in self.expected_complete_failing_rows
            )
            or tuple(sorted(set(self.expected_complete_failing_rows)))
            != self.expected_complete_failing_rows
        ):
            raise ValueError("expected complete failing rows must be sorted unique indices")


@dataclass(frozen=True, slots=True)
class RetainedAuditContract:
    artifact_sha256: str
    artifact_bytes: int
    runner_version: str
    runner_source_sha256: str
    corpus_sha256: str
    environment_subtree_sha256: str
    protocol_subtree_sha256: str
    expected_observation_count: int
    expected_variant_count: int
    expected_base_count: int
    expected_micro_base_count: int
    expected_sizing_base_count: int
    micro_variant_allowance: MicroVariantComparisonAllowance
    cross_backend_sizing_allowance: CrossBackendSizingAllowance
    cross_variant_sizing_allowance: CrossVariantSizingAllowance
    known_regression: KnownRegressionSignature

    def __post_init__(self) -> None:
        for label, value in (
            ("artifact", self.artifact_sha256),
            ("runner source", self.runner_source_sha256),
            ("corpus", self.corpus_sha256),
            ("environment subtree", self.environment_subtree_sha256),
            ("protocol subtree", self.protocol_subtree_sha256),
        ):
            if not _valid_sha256(value):
                raise ValueError(f"{label} digest must be lowercase SHA-256")
        if not isinstance(self.runner_version, str) or not self.runner_version:
            raise ValueError("runner version must be nonempty")
        for label, value in (
            ("artifact bytes", self.artifact_bytes),
            ("observation count", self.expected_observation_count),
            ("variant count", self.expected_variant_count),
            ("base count", self.expected_base_count),
            ("micro base count", self.expected_micro_base_count),
            ("sizing base count", self.expected_sizing_base_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"expected {label} must be positive")
        if self.expected_observation_count != self.expected_variant_count * len(_BACKEND_ORDER):
            raise ValueError("observation count must equal three arms per variant")
        if self.expected_variant_count != self.expected_base_count * len(_VARIANT_KINDS):
            raise ValueError("variant count must equal five representations per base")
        if (
            self.expected_micro_base_count + self.expected_sizing_base_count
            != self.expected_base_count
        ):
            raise ValueError("micro and sizing counts must partition the bases")
        semantic = (
            (self.micro_variant_allowance, MicroVariantComparisonAllowance),
            (self.cross_backend_sizing_allowance, CrossBackendSizingAllowance),
            (self.cross_variant_sizing_allowance, CrossVariantSizingAllowance),
            (self.known_regression, KnownRegressionSignature),
        )
        if any(not isinstance(value, expected) for value, expected in semantic):
            raise TypeError("retained audit contract contains a nonsemantic field")


ADR0315_RETAINED_AUDIT_CONTRACT = RetainedAuditContract(
    artifact_sha256=ADR0314_RETAINED_ARTIFACT_SHA256,
    artifact_bytes=ADR0314_RETAINED_ARTIFACT_BYTES,
    runner_version=ADR0313_RUNNER_VERSION,
    runner_source_sha256=ADR0313_RUNNER_SOURCE_SHA256,
    corpus_sha256=ADR0311_COMPLETE_CORPUS_SHA256,
    environment_subtree_sha256=ADR0313_ENVIRONMENT_SUBTREE_SHA256,
    protocol_subtree_sha256=ADR0313_PROTOCOL_SUBTREE_SHA256,
    expected_observation_count=2_655,
    expected_variant_count=885,
    expected_base_count=177,
    expected_micro_base_count=48,
    expected_sizing_base_count=129,
    micro_variant_allowance=MicroVariantComparisonAllowance(1e-9),
    cross_backend_sizing_allowance=CrossBackendSizingAllowance(1e-9),
    cross_variant_sizing_allowance=CrossVariantSizingAllowance(1e-9),
    known_regression=KnownRegressionSignature(
        base_id="adr0311-simplex-known-adr0310-qualified-b-c21-full",
        variant_id=("adr0311-simplex-known-adr0310-qualified-b-c21-full--canonical"),
        exception_module="builtins",
        exception_qualname="AssertionError",
        exception_message="linear-program solution fails primal verification",
        pivots=375,
        verification_allowance_hex="0x1.68c6fa0b2f9a2p-25",
        maximum_residual_hex="0x1.032cad8b12778p+2",
        required_unique_maximum_row=215,
        expected_complete_failing_rows=None,
    ),
)


@dataclass(frozen=True, slots=True)
class CorrectedGateFailure:
    code: str
    base_id: str | None
    variant_id: str | None
    backend: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("corrected gate failure code must be nonempty")
        if not isinstance(self.detail, str) or not self.detail:
            raise ValueError("corrected gate failure detail must be nonempty")
        for label, value in (
            ("base id", self.base_id),
            ("variant id", self.variant_id),
            ("backend", self.backend),
        ):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"corrected gate failure {label} must be text")


@dataclass(frozen=True, slots=True)
class KnownRegressionEvidence:
    failing_rows: tuple[int, ...]
    unique_maximum_rows: tuple[int, ...]
    maximum_residual: float
    verification_allowance: float
    pivots: int
    exception_module: str
    exception_qualname: str
    exception_message: str

    def __post_init__(self) -> None:
        for label, values in (
            ("failing rows", self.failing_rows),
            ("unique maximum rows", self.unique_maximum_rows),
        ):
            if (
                not isinstance(values, tuple)
                or any(
                    isinstance(row, bool) or not isinstance(row, int) or row < 0 for row in values
                )
                or tuple(sorted(set(values))) != values
            ):
                raise ValueError(f"known regression {label} must be sorted unique indices")
        _require_positive_finite(self.maximum_residual, label="known maximum residual")
        _require_positive_finite(
            self.verification_allowance,
            label="known verification allowance",
        )
        if isinstance(self.pivots, bool) or not isinstance(self.pivots, int) or self.pivots < 0:
            raise ValueError("known regression pivots must be nonnegative")
        for label, value in (
            ("exception module", self.exception_module),
            ("exception qualname", self.exception_qualname),
            ("exception message", self.exception_message),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"known regression {label} must be nonempty")


@dataclass(frozen=True, slots=True)
class CorrectedAuditGateAssessment:
    analyzer_version: str
    analyzer_source_sha256: str
    artifact_sha256: str
    artifact_bytes: int
    complete_schedule: bool
    observation_count: int
    variant_count: int
    base_count: int
    native_verified_count: int
    native_exception_count: int
    highs_ds_verified_count: int
    highs_ipm_verified_count: int
    known_native_regression_reproduced: bool
    known_native_regression: KnownRegressionEvidence | None
    highs_dual_simplex_eligible: bool
    failures: tuple[CorrectedGateFailure, ...]

    def __post_init__(self) -> None:
        if self.analyzer_version != ADR0315_ANALYZER_VERSION:
            raise ValueError("corrected assessment analyzer version drifted")
        for label, value in (
            ("analyzer source", self.analyzer_source_sha256),
            ("artifact", self.artifact_sha256),
        ):
            if not _valid_sha256(value):
                raise ValueError(f"corrected assessment {label} digest is invalid")
        for label, value in (
            ("artifact bytes", self.artifact_bytes),
            ("observations", self.observation_count),
            ("variants", self.variant_count),
            ("bases", self.base_count),
            ("native verified", self.native_verified_count),
            ("native exceptions", self.native_exception_count),
            ("dual simplex verified", self.highs_ds_verified_count),
            ("IPM verified", self.highs_ipm_verified_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"corrected assessment {label} must be nonnegative")
        if not isinstance(self.complete_schedule, bool):
            raise TypeError("corrected assessment schedule flag must be boolean")
        if not isinstance(self.known_native_regression_reproduced, bool):
            raise TypeError("corrected assessment regression flag must be boolean")
        if self.known_native_regression is not None and not isinstance(
            self.known_native_regression,
            KnownRegressionEvidence,
        ):
            raise TypeError("corrected assessment regression evidence is nonsemantic")
        if not isinstance(self.highs_dual_simplex_eligible, bool):
            raise TypeError("corrected assessment eligibility must be boolean")
        if not isinstance(self.failures, tuple) or any(
            not isinstance(failure, CorrectedGateFailure) for failure in self.failures
        ):
            raise TypeError("corrected assessment failures must be semantic and immutable")
        if self.highs_dual_simplex_eligible and (
            not self.complete_schedule
            or not self.known_native_regression_reproduced
            or self.failures
        ):
            raise ValueError("corrected assessment eligibility is not conjunctive")

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_corrected_gate_bytes(self)

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class _ParsedObservation:
    ordinal: int
    task_index: int
    base_id: str
    variant_id: str
    backend: str
    fields: Mapping[str, Any]
    backend_result: Mapping[str, Any] | None
    micro_verification: Mapping[str, Any] | None
    sizing_verification: Mapping[str, Any] | None


def _require_mapping(value: object, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise TypeError(f"{label} keys must be text")
    return value


def _require_list(value: object, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    return value


def _require_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    return value


def _require_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be nonempty text")
    return value


def _require_indices(value: object, *, label: str) -> tuple[int, ...]:
    values = _require_list(value, label=label)
    result = tuple(_require_int(item, label=label) for item in values)
    if any(item < 0 for item in result) or tuple(sorted(set(result))) != result:
        raise ValueError(f"{label} must be sorted unique nonnegative indices")
    return result


def _dataclass_fields(
    value: object,
    *,
    expected_dataclass: str,
    label: str,
    expected_fields: set[str] | None = None,
) -> Mapping[str, Any]:
    wrapped = _require_mapping(value, label=label)
    if set(wrapped) != {"dataclass", "fields"}:
        raise ValueError(f"{label} wrapper schema differs")
    if wrapped["dataclass"] != expected_dataclass:
        raise ValueError(f"{label} dataclass identity differs")
    result = _require_mapping(wrapped["fields"], label=f"{label} fields")
    if expected_fields is not None and set(result) != expected_fields:
        raise ValueError(f"{label} field schema differs")
    return result


def _decode_float(value: object, *, label: str) -> tuple[float, str]:
    wrapped = _require_mapping(value, label=label)
    if set(wrapped) != {"float_hex"}:
        raise ValueError(f"{label} must be an exact float wrapper")
    text = _require_canonical_float_hex(wrapped["float_hex"], label=label)
    return float.fromhex(text), text


def _subtree_sha256(value: object) -> str:
    return sha256(_canonical_json_bytes(value)).hexdigest()


def _reject_raw_json_floats(value: object, *, label: str = "retained audit") -> None:
    if isinstance(value, float):
        raise TypeError(f"{label} contains a raw JSON float")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_raw_json_floats(item, label=f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_raw_json_floats(item, label=f"{label}[{index}]")


def _optional_verification(
    value: object,
    *,
    expected_dataclass: str,
    label: str,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return _dataclass_fields(
        value,
        expected_dataclass=expected_dataclass,
        label=label,
    )


def _parse_observation(value: object, *, index: int) -> _ParsedObservation:
    observation = _dataclass_fields(
        value,
        expected_dataclass=_OBSERVATION_DATACLASS,
        label=f"observation {index}",
        expected_fields=_OBSERVATION_FIELDS,
    )
    invocation = _dataclass_fields(
        observation["invocation"],
        expected_dataclass=_INVOCATION_DATACLASS,
        label=f"observation {index} invocation",
        expected_fields=_INVOCATION_FIELDS,
    )
    backend_result = (
        None
        if observation["backend_result"] is None
        else _dataclass_fields(
            observation["backend_result"],
            expected_dataclass=_BACKEND_RESULT_DATACLASS,
            label=f"observation {index} backend result",
            expected_fields=_BACKEND_RESULT_FIELDS,
        )
    )
    return _ParsedObservation(
        ordinal=_require_int(invocation["ordinal"], label="invocation ordinal"),
        task_index=_require_int(invocation["task_index"], label="invocation task index"),
        base_id=_require_text(invocation["base_id"], label="invocation base id"),
        variant_id=_require_text(invocation["variant_id"], label="invocation variant id"),
        backend=_require_text(invocation["backend"], label="invocation backend"),
        fields=observation,
        backend_result=backend_result,
        micro_verification=_optional_verification(
            observation["micro_verification"],
            expected_dataclass=_MICRO_VERIFICATION_DATACLASS,
            label=f"observation {index} micro verification",
        ),
        sizing_verification=_optional_verification(
            observation["sizing_verification"],
            expected_dataclass=_SIZING_VERIFICATION_DATACLASS,
            label=f"observation {index} sizing verification",
        ),
    )


def _validate_schedule(
    observations: Sequence[_ParsedObservation],
    *,
    contract: RetainedAuditContract,
) -> tuple[dict[str, tuple[_ParsedObservation, ...]], dict[str, tuple[str, ...]]]:
    if len(observations) != contract.expected_observation_count:
        raise ValueError("retained observation count differs from its contract")
    variants: dict[str, list[_ParsedObservation]] = {}
    base_variants: dict[str, list[str]] = defaultdict(list)
    for index, observation in enumerate(observations):
        if observation.ordinal != index:
            raise ValueError("retained observation ordinals are not contiguous")
        expected_task = index // len(_BACKEND_ORDER)
        expected_backend = _BACKEND_ORDER[index % len(_BACKEND_ORDER)]
        if observation.task_index != expected_task:
            raise ValueError("retained task indices differ from variant-major order")
        if observation.backend != expected_backend:
            raise ValueError("retained backend order differs from the frozen order")
        variant = variants.setdefault(observation.variant_id, [])
        if variant and (
            variant[0].base_id != observation.base_id
            or variant[0].task_index != observation.task_index
        ):
            raise ValueError("retained variant arms disagree on identity")
        variant.append(observation)
        if expected_backend == _BACKEND_ORDER[0]:
            base_variants[observation.base_id].append(observation.variant_id)
    if len(variants) != contract.expected_variant_count:
        raise ValueError("retained variant count differs from its contract")
    if any(tuple(item.backend for item in arms) != _BACKEND_ORDER for arms in variants.values()):
        raise ValueError("retained variant omits or repeats a backend arm")
    if len(base_variants) != contract.expected_base_count:
        raise ValueError("retained base count differs from its contract")
    frozen_base_variants: dict[str, tuple[str, ...]] = {}
    for base_id, variant_ids in base_variants.items():
        expected = tuple(f"{base_id}--{kind}" for kind in _VARIANT_KINDS)
        actual = tuple(variant_ids)
        if actual != expected:
            raise ValueError("retained base representations differ from the frozen order")
        frozen_base_variants[base_id] = actual
    return (
        {key: tuple(value) for key, value in variants.items()},
        frozen_base_variants,
    )


def _verification_family(observation: _ParsedObservation) -> str:
    micro = observation.micro_verification
    sizing = observation.sizing_verification
    exact = observation.fields["exact_micro_work"]
    if micro is not None and sizing is None and exact is not None:
        _dataclass_fields(
            exact,
            expected_dataclass=_EXACT_MICRO_DATACLASS,
            label="exact micro work",
        )
        return "micro"
    if sizing is not None and micro is None and exact is None:
        return "sizing"
    raise ValueError("retained observation has an inconsistent verification family")


def _observation_verified(observation: _ParsedObservation) -> bool:
    result = observation.backend_result
    if result is None or result.get("backend") != observation.backend:
        return False
    if result.get("termination") != "optimal" or result.get("exception") is not None:
        return False
    if any(
        result.get(field) is None
        for field in (
            "primal_variant_coordinates",
            "reported_maximization_objective",
            "dual_hint_variant_rows",
        )
    ):
        return False
    if _require_list(observation.fields["runner_failures"], label="runner failures"):
        return False
    if observation.fields["coordinate_diagnostics"] is None:
        return False
    _dataclass_fields(
        observation.fields["coordinate_diagnostics"],
        expected_dataclass=_COORDINATE_DIAGNOSTICS_DATACLASS,
        label="coordinate diagnostics",
    )
    if observation.fields["certificate_diagnostics"] is None:
        return False
    _dataclass_fields(
        observation.fields["certificate_diagnostics"],
        expected_dataclass=_CERTIFICATE_DIAGNOSTICS_DATACLASS,
        label="certificate diagnostics",
    )
    verification = observation.micro_verification or observation.sizing_verification
    if verification is None:
        return False
    return not _require_list(verification.get("failures"), label="verification failures")


def _assess_known_regression(
    variants: Mapping[str, tuple[_ParsedObservation, ...]],
    *,
    signature: KnownRegressionSignature,
) -> tuple[bool, KnownRegressionEvidence | None]:
    arms = variants.get(signature.variant_id)
    if arms is None:
        return False, None
    known = next((arm for arm in arms if arm.backend == "native"), None)
    if known is None or known.base_id != signature.base_id or known.backend_result is None:
        return False, None
    result = known.backend_result
    exception = (
        None
        if result.get("exception") is None
        else _dataclass_fields(
            result["exception"],
            expected_dataclass=_EXCEPTION_DATACLASS,
            label="known native exception",
            expected_fields=_EXCEPTION_FIELDS,
        )
    )
    trace = (
        None
        if result.get("native_verification_trace") is None
        else _dataclass_fields(
            result["native_verification_trace"],
            expected_dataclass=_TRACE_DATACLASS,
            label="known native trace",
            expected_fields=_TRACE_FIELDS,
        )
    )
    coordinates = (
        None
        if known.fields["native_failure_coordinates"] is None
        else _dataclass_fields(
            known.fields["native_failure_coordinates"],
            expected_dataclass=_COORDINATES_DATACLASS,
            label="known native coordinates",
            expected_fields=_COORDINATE_FIELDS,
        )
    )
    if exception is None or trace is None or coordinates is None:
        return False, None
    if result.get("backend") != "native":
        return False, None
    residual_wrappers = _require_list(
        trace["constraint_residuals_variant_rows"],
        label="known native residuals",
    )
    residuals = tuple(
        _decode_float(value, label="known native residual")[0] for value in residual_wrappers
    )
    if not residuals:
        raise ValueError("known native trace omits residuals")
    allowance, allowance_hex = _decode_float(
        trace["verification_allowance"],
        label="known native trace allowance",
    )
    coordinate_allowance, coordinate_allowance_hex = _decode_float(
        coordinates["verification_allowance"],
        label="known native coordinate allowance",
    )
    maximum = max(0.0, max(residuals))
    maximum_rows = tuple(index for index, value in enumerate(residuals) if value == maximum)
    failing_rows = tuple(index for index, value in enumerate(residuals) if value > allowance)
    stored_variant_rows = _require_indices(
        coordinates["failing_variant_rows"],
        label="known native failing variant rows",
    )
    stored_canonical_rows = _require_indices(
        coordinates["failing_canonical_rows"],
        label="known native failing canonical rows",
    )
    stored_maximum, stored_maximum_hex = _decode_float(
        coordinates["maximum_variant_residual"],
        label="known native stored maximum",
    )
    trace_pivots = _require_int(trace["pivots"], label="known native trace pivots")
    result_pivots = _require_int(result.get("iterations"), label="known native pivots")
    if stored_variant_rows != failing_rows or stored_canonical_rows != failing_rows:
        raise ValueError("known canonical failure rows disagree with the retained trace")
    if stored_maximum != maximum:
        raise ValueError("known stored maximum disagrees with the retained trace")
    if coordinate_allowance != allowance:
        raise ValueError("known stored allowance disagrees with the retained trace")
    if trace_pivots != result_pivots:
        raise ValueError("known trace pivots disagree with the retained result")
    evidence = KnownRegressionEvidence(
        failing_rows=failing_rows,
        unique_maximum_rows=maximum_rows,
        maximum_residual=maximum,
        verification_allowance=allowance,
        pivots=result_pivots,
        exception_module=_require_text(exception.get("module"), label="exception module"),
        exception_qualname=_require_text(
            exception.get("qualname"),
            label="exception qualname",
        ),
        exception_message=_require_text(
            exception.get("message"),
            label="exception message",
        ),
    )
    reproduced = (
        result.get("termination") == "exception"
        and exception.get("stage") == "backend-invocation"
        and result.get("message") == evidence.exception_message
        and evidence.exception_module == signature.exception_module
        and evidence.exception_qualname == signature.exception_qualname
        and evidence.exception_message == signature.exception_message
        and evidence.pivots == signature.pivots
        and allowance_hex == signature.verification_allowance_hex
        and coordinate_allowance_hex == signature.verification_allowance_hex
        and stored_maximum_hex == signature.maximum_residual_hex
        and maximum.hex() == signature.maximum_residual_hex
        and maximum_rows == (signature.required_unique_maximum_row,)
        and signature.required_unique_maximum_row in failing_rows
        and (
            signature.expected_complete_failing_rows is None
            or failing_rows == signature.expected_complete_failing_rows
        )
    )
    return reproduced, evidence


def reanalyze_retained_audit_bytes(
    raw: bytes,
    *,
    contract: RetainedAuditContract,
    analyzer_source_sha256: str,
) -> CorrectedAuditGateAssessment:
    """Apply the disclosed correction to exact canonical retained bytes."""

    if not isinstance(raw, bytes):
        raise TypeError("retained audit evidence must be bytes")
    if not isinstance(contract, RetainedAuditContract):
        raise TypeError("retained audit reanalysis requires a semantic contract")
    if not _valid_sha256(analyzer_source_sha256):
        raise ValueError("analyzer source digest must be lowercase SHA-256")
    if len(raw) != contract.artifact_bytes:
        raise ValueError("retained audit byte count differs from its contract")
    artifact_sha256 = sha256(raw).hexdigest()
    if artifact_sha256 != contract.artifact_sha256:
        raise ValueError("retained audit digest differs from its contract")
    decoded = decode_strict_json_object(raw, source="retained native-simplex audit")
    _reject_raw_json_floats(decoded)
    if _canonical_json_bytes(decoded) != raw:
        raise ValueError("retained audit bytes are not canonical JSON")
    campaign = _dataclass_fields(
        decoded,
        expected_dataclass=_CAMPAIGN_DATACLASS,
        label="retained audit campaign",
        expected_fields=_CAMPAIGN_FIELDS,
    )
    if campaign["runner_version"] != contract.runner_version:
        raise ValueError("retained runner version differs from its contract")
    if campaign["runner_source_sha256"] != contract.runner_source_sha256:
        raise ValueError("retained runner source differs from its contract")
    if campaign["corpus_sha256"] != contract.corpus_sha256:
        raise ValueError("retained corpus differs from its contract")
    if campaign["sealed_adr0311"] is not True:
        raise ValueError("retained campaign is not marked as the sealed ADR-0311 audit")
    if _subtree_sha256(campaign["environment"]) != contract.environment_subtree_sha256:
        raise ValueError("retained environment identity differs from its contract")
    if _subtree_sha256(campaign["protocol"]) != contract.protocol_subtree_sha256:
        raise ValueError("retained protocol identity differs from its contract")

    observations = tuple(
        _parse_observation(value, index=index)
        for index, value in enumerate(
            _require_list(campaign["observations"], label="campaign observations")
        )
    )
    variants, base_variants = _validate_schedule(observations, contract=contract)
    regression_reproduced, regression_evidence = _assess_known_regression(
        variants,
        signature=contract.known_regression,
    )
    failures: list[CorrectedGateFailure] = []
    if not regression_reproduced:
        failures.append(
            CorrectedGateFailure(
                code="known-native-regression-mismatch",
                base_id=contract.known_regression.base_id,
                variant_id=contract.known_regression.variant_id,
                backend="native",
                detail=(
                    "expected the recorded exception, pivots, allowance, exact maximum, "
                    "and unique maximum row without assuming an exclusive failing-row set"
                ),
            )
        )

    verified_counts: Counter[str] = Counter()
    native_exception_count = 0
    high_by_base: dict[str, list[_ParsedObservation]] = defaultdict(list)
    base_families: dict[str, set[str]] = defaultdict(set)
    for observation in observations:
        result = observation.backend_result
        if observation.backend == "native" and result is not None:
            if result.get("termination") == "exception":
                native_exception_count += 1
            elif _observation_verified(observation):
                verified_counts["native"] += 1
        if observation.backend not in _HIGH_BACKENDS:
            continue
        family = _verification_family(observation)
        base_families[observation.base_id].add(family)
        high_by_base[observation.base_id].append(observation)
        if _observation_verified(observation):
            verified_counts[observation.backend] += 1
        else:
            failures.append(
                CorrectedGateFailure(
                    code="highs-instance-failed",
                    base_id=observation.base_id,
                    variant_id=observation.variant_id,
                    backend=observation.backend,
                    detail="backend, schema, semantic, or certificate verification failed",
                )
            )
    if set(base_families) != set(base_variants):
        raise ValueError("retained high-backend bases differ from the schedule")
    if any(len(families) != 1 for families in base_families.values()):
        raise ValueError("retained base mixes micro and sizing verification families")
    micro_count = sum(families == {"micro"} for families in base_families.values())
    sizing_count = sum(families == {"sizing"} for families in base_families.values())
    if (
        micro_count != contract.expected_micro_base_count
        or sizing_count != contract.expected_sizing_base_count
    ):
        raise ValueError("retained verification-family counts differ from the contract")

    for base_id, base_observations in high_by_base.items():
        if len(base_observations) != len(_VARIANT_KINDS) * len(_HIGH_BACKENDS):
            raise ValueError("retained base omits a HiGHS representation arm")
        family = next(iter(base_families[base_id]))
        if family == "micro":
            values = tuple(
                _decode_float(
                    observation.micro_verification["reconstructed_objective"],
                    label="micro reconstructed objective",
                )[0]
                for observation in base_observations
                if observation.micro_verification is not None
            )
            if len(values) != len(base_observations):
                raise ValueError("retained micro base omits a verification value")
            if max(values) - min(values) > contract.micro_variant_allowance.value:
                failures.append(
                    CorrectedGateFailure(
                        code="micro-variant-disagreement",
                        base_id=base_id,
                        variant_id=None,
                        backend=None,
                        detail="reconstructed objectives exceed the frozen allowance",
                    )
                )
            continue

        intervals: list[tuple[float, float]] = []
        by_variant: dict[str, dict[str, float]] = defaultdict(dict)
        for observation in base_observations:
            assert observation.sizing_verification is not None
            lower = _decode_float(
                observation.sizing_verification["behavioral_lower_bound_chips"],
                label="sizing behavioral lower bound",
            )[0]
            upper = _decode_float(
                observation.sizing_verification["certified_upper_bound_chips"],
                label="sizing certified upper bound",
            )[0]
            intervals.append((lower, upper))
            by_variant[observation.variant_id][observation.backend] = lower
        lower_intersection = max(lower for lower, _ in intervals)
        upper_intersection = min(upper for _, upper in intervals)
        if lower_intersection > upper_intersection + contract.cross_variant_sizing_allowance.chips:
            failures.append(
                CorrectedGateFailure(
                    code="sizing-interval-intersection-empty",
                    base_id=base_id,
                    variant_id=None,
                    backend=None,
                    detail="ten DS/IPM intervals have no allowed common intersection",
                )
            )
        for variant_id, by_backend in by_variant.items():
            if set(by_backend) != set(_HIGH_BACKENDS):
                raise ValueError("retained sizing variant omits a HiGHS backend")
            difference = abs(by_backend["highs-ds"] - by_backend["highs-ipm"])
            if difference > contract.cross_backend_sizing_allowance.chips:
                failures.append(
                    CorrectedGateFailure(
                        code="sizing-cross-backend-disagreement",
                        base_id=base_id,
                        variant_id=variant_id,
                        backend=None,
                        detail="DS/IPM reconstructed values exceed the frozen allowance",
                    )
                )

    eligible = regression_reproduced and not failures
    return CorrectedAuditGateAssessment(
        analyzer_version=ADR0315_ANALYZER_VERSION,
        analyzer_source_sha256=analyzer_source_sha256,
        artifact_sha256=artifact_sha256,
        artifact_bytes=len(raw),
        complete_schedule=True,
        observation_count=len(observations),
        variant_count=len(variants),
        base_count=len(base_variants),
        native_verified_count=verified_counts["native"],
        native_exception_count=native_exception_count,
        highs_ds_verified_count=verified_counts["highs-ds"],
        highs_ipm_verified_count=verified_counts["highs-ipm"],
        known_native_regression_reproduced=regression_reproduced,
        known_native_regression=regression_evidence,
        highs_dual_simplex_eligible=eligible,
        failures=tuple(failures),
    )


def reanalyze_sealed_adr0314_artifact(path: Path) -> CorrectedAuditGateAssessment:
    """Read and reanalyze only ADR-0314's exact retained canonical artifact."""

    from .native_simplex_audit_reanalysis_seal import ADR0315_ANALYZER_SOURCE_SHA256

    source_sha256 = canonical_lf_source_sha256(Path(__file__))
    if source_sha256 != ADR0315_ANALYZER_SOURCE_SHA256:
        raise RuntimeError("audit reanalyzer source differs from its committed seal")
    raw = read_bounded_file_once(
        path,
        maximum_bytes=ADR0315_RETAINED_AUDIT_CONTRACT.artifact_bytes,
    )
    return reanalyze_retained_audit_bytes(
        raw,
        contract=ADR0315_RETAINED_AUDIT_CONTRACT,
        analyzer_source_sha256=source_sha256,
    )


__all__ = [
    "ADR0314_RETAINED_ARTIFACT_BYTES",
    "ADR0314_RETAINED_ARTIFACT_SHA256",
    "ADR0315_ANALYZER_VERSION",
    "ADR0315_RETAINED_AUDIT_CONTRACT",
    "CorrectedAuditGateAssessment",
    "CorrectedGateFailure",
    "CrossBackendSizingAllowance",
    "CrossVariantSizingAllowance",
    "KnownRegressionEvidence",
    "KnownRegressionSignature",
    "MicroVariantComparisonAllowance",
    "RetainedAuditContract",
    "canonical_corrected_gate_bytes",
    "canonical_lf_source_sha256",
    "reanalyze_retained_audit_bytes",
    "reanalyze_sealed_adr0314_artifact",
]
