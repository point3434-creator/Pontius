"""Solver-free owner for ADR-0353's retained tie-aware h4 rejection.

The ADR-0352 public runner is permanently closed.  This module reads only its
exact retained JSON artifact, verifies the sealed source closure, and rebinds
the typed active-tape-bound failure.  It imports no game, evaluator, optimizer,
runner, action, clock, or write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


ADR0353_INVOCATION_SOURCE_COMMIT = (
    "b7c1ecc7f9113cbd8ddb6e27dfa4b2372534c4ff"
)
ADR0353_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-tie-aware-affine-v1.json"
)
ADR0353_ARTIFACT_BYTES = 961
ADR0353_ARTIFACT_SHA256 = (
    "7608abd221114ed6143aa7fbf9af510a09024442f85fd8f4f3f5ed53e036f652"
)
ADR0353_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-responder-raise-h4-tie-aware-affine-v1.json"
)
ADR0353_CONFIG_SHA256 = (
    "9dae1dbe1c93e1952699f7a2bc11f3837bed2e2cf0296e0bafc5c5b87dceff3f"
)
ADR0353_IMPLEMENTATION_SHA256 = (
    "99b7db5e7ee49d35769fb4f41a72ef251469df8439ac52a924b7edefcdf4f28d"
)
ADR0353_HISTORICAL_RUNNER_CONTROL_SHA256 = (
    "dd691d01b271dfabb599a68df338602286e304287f35b7ae6fc1fc0a8709d92e"
)
ADR0353_TOTAL_SECONDS = 64.65051910001785


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "parent_decision": (
            "docs/decisions/"
            "ADR-0352-preregister-the-legal-h4-tie-aware-affine-envelope-"
            "integration.md"
        ),
        "config": ADR0353_CONFIG_RELATIVE_PATH,
        "exact_active_row_oracle": (
            "src/pontius/exact_tie_aware_affine_envelope.py"
        ),
        "tie_aware_adapter": "src/pontius/tie_aware_affine_adapter.py",
        "selector_window_v2": "src/pontius/selector_window_v2.py",
        "prospective_runner": (
            "src/pontius/legal_responder_raise_h4_tie_aware_affine.py"
        ),
        "oracle_adapter_control": (
            "tests/test_exact_tie_aware_affine_envelope.py"
        ),
        "retired_runner_lifecycle_control": (
            "tests/test_legal_responder_raise_h4_tie_aware_affine.py"
        ),
    }
)
_EXPECTED_SOURCE_HASHES = MappingProxyType(
    {
        "parent_decision": (
            "0373040f5ed3eb62c883f936f48f9672b45dfc535ff99a35e1dcd7c288c4adc4"
        ),
        "config": ADR0353_CONFIG_SHA256,
        "exact_active_row_oracle": (
            "ee922a9cf15be88cc2566a8c0b45496dd0db6cb5856b738f52ecbaf7429c6695"
        ),
        "tie_aware_adapter": (
            "3982179667e185148560b8fb3f2e882f29e6ab185c7295be882beab3f0f364c5"
        ),
        "selector_window_v2": (
            "78af151aaaf6dfdc69ce7f2fba141a16fc76edfef4b43be4732380140b03f644"
        ),
        "prospective_runner": ADR0353_IMPLEMENTATION_SHA256,
        "oracle_adapter_control": (
            "00c5f5c736ec5c327f479c715f558560d81707abd15134ac1190b7582b1c4aec"
        ),
        "retired_runner_lifecycle_control": (
            "6567b3f17ce9e14baf6154091d4bb7f76afb6c377215fc7cfe9c22ff2d18c3f3"
        ),
    }
)
_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "config_sha256",
        "decision",
        "environment",
        "failure",
        "implementation_sha256",
        "passed",
        "schema_version",
        "status",
        "strategy_quality_claim",
        "total_seconds",
    }
)
_EXPECTED_ENVIRONMENT_KEYS = frozenset({"git", "platform", "python", "runtime"})
_EXPECTED_GIT_KEYS = frozenset({"commit", "dirty", "strict_status"})
_EXPECTED_RUNTIME_KEYS = frozenset({"backend"})
_EXPECTED_FAILURE_KEYS = frozenset({"message", "stage", "type"})

_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0353_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0353_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0353_ARTIFACT_SHA256,
    "config_sha256": ADR0353_CONFIG_SHA256,
    "failure": {
        "message": "exact active-tape closure exceeds its frozen bound",
        "stage": "tie_aware_affine",
        "type": "RuntimeError",
    },
    "implementation_sha256": ADR0353_IMPLEMENTATION_SHA256,
    "invocation_source_commit": ADR0353_INVOCATION_SOURCE_COMMIT,
    "historical_runner_control_sha256": (
        ADR0353_HISTORICAL_RUNNER_CONTROL_SHA256
    ),
    "source_hashes": dict(_EXPECTED_SOURCE_HASHES),
    "total_seconds_hex": ADR0353_TOTAL_SECONDS.hex(),
    "version": "adr0353-legal-h4-tie-aware-affine-result-protocol-v1",
}
ADR0353_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0353_RESULT_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _RESULT_PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


def _raw_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256(raw).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class RetainedLegalH4TieAwareAffineRejection:
    """Authenticated first terminal of the closed ADR-0352 owner."""

    record: Mapping[str, Any]
    source_commit: str
    artifact_bytes: int
    artifact_sha256: str
    failure_classification: str
    successor_authorized: bool


def verify_adr0353_result_source_and_dependencies() -> str:
    """Verify the result owner, protocol, and complete preregistered closure."""

    from .legal_responder_raise_h4_tie_aware_affine_result_seal import (
        ADR0353_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0353_RESULT_SOURCE_MANIFEST,
    )

    module_path = Path(__file__).resolve()
    actual_module = _canonical_lf_sha256(module_path)
    if ADR0353_RESULT_SOURCE_MANIFEST != {module_path.name: actual_module}:
        raise RuntimeError("ADR-0353 result-owner source manifest mismatch")
    if sealed_protocol != ADR0353_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0353 result protocol mismatch")
    for label, relative_path in _SOURCE_PATHS.items():
        actual = _raw_sha256(_ROOT / relative_path)
        if actual != _EXPECTED_SOURCE_HASHES[label]:
            raise RuntimeError(f"ADR-0353 source-closure mismatch: {label}")
    return actual_module


def verify_adr0353_legal_h4_tie_aware_affine_record(
    record: object,
) -> Mapping[str, Any]:
    """Rebind the complete typed-failure schema without trusting its outer hash."""

    if not isinstance(record, dict) or set(record) != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("ADR-0353 result top-level schema mismatch")
    environment = record["environment"]
    failure = record["failure"]
    if not isinstance(environment, dict) or set(environment) != _EXPECTED_ENVIRONMENT_KEYS:
        raise ValueError("ADR-0353 environment schema mismatch")
    if not isinstance(failure, dict) or set(failure) != _EXPECTED_FAILURE_KEYS:
        raise ValueError("ADR-0353 failure schema mismatch")
    git = environment["git"]
    runtime = environment["runtime"]
    if not isinstance(git, dict) or set(git) != _EXPECTED_GIT_KEYS:
        raise ValueError("ADR-0353 git schema mismatch")
    if not isinstance(runtime, dict) or set(runtime) != _EXPECTED_RUNTIME_KEYS:
        raise ValueError("ADR-0353 runtime schema mismatch")

    expected_failure = _RESULT_PROTOCOL_PAYLOAD["failure"]
    if (
        record["schema_version"] != 1
        or record["status"] != "legal_responder_raise_h4_tie_aware_affine_failed"
        or record["decision"] != "reject_legal_h4_tie_aware_affine_integration"
        or record["passed"] is not False
        or record["strategy_quality_claim"] is not None
        or record["config_sha256"] != ADR0353_CONFIG_SHA256
        or record["implementation_sha256"] != ADR0353_IMPLEMENTATION_SHA256
        or failure != expected_failure
        or git
        != {
            "commit": ADR0353_INVOCATION_SOURCE_COMMIT,
            "dirty": False,
            "strict_status": True,
        }
        or runtime
        != {"backend": "cpu_float64_fixed_rows_plus_fraction_active_set"}
        or environment["platform"] != "Windows-11-10.0.26200-SP0"
        or environment["python"]
        != (
            "3.14.6 (tags/v3.14.6:c63aec6, Jun 10 2026, 10:26:10) "
            "[MSC v.1944 64 bit (AMD64)]"
        )
    ):
        raise ValueError("ADR-0353 retained terminal identity mismatch")
    total_seconds = record["total_seconds"]
    if (
        isinstance(total_seconds, bool)
        or not isinstance(total_seconds, (int, float))
        or not isfinite(total_seconds)
        or float(total_seconds).hex() != ADR0353_TOTAL_SECONDS.hex()
        or not 0.0 < total_seconds < 120.0
    ):
        raise ValueError("ADR-0353 retained terminal timing mismatch")
    return _freeze(record)


def verify_adr0353_legal_h4_tie_aware_affine_result_artifact(
    path: Path | None = None,
) -> RetainedLegalH4TieAwareAffineRejection:
    """Authenticate and semantically rebind the retained exclusive artifact."""

    verify_adr0353_result_source_and_dependencies()
    artifact_path = _ROOT / ADR0353_ARTIFACT_RELATIVE_PATH if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0353_ARTIFACT_BYTES:
        raise ValueError("ADR-0353 artifact byte count mismatch")
    if sha256(raw).hexdigest() != ADR0353_ARTIFACT_SHA256:
        raise ValueError("ADR-0353 artifact SHA-256 mismatch")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ADR-0353 artifact is not valid UTF-8 JSON") from exc
    frozen = verify_adr0353_legal_h4_tie_aware_affine_record(record)
    return RetainedLegalH4TieAwareAffineRejection(
        record=frozen,
        source_commit=ADR0353_INVOCATION_SOURCE_COMMIT,
        artifact_bytes=ADR0353_ARTIFACT_BYTES,
        artifact_sha256=ADR0353_ARTIFACT_SHA256,
        failure_classification="frozen_active_tape_cartesian_bound_rejection",
        successor_authorized=False,
    )


__all__ = [
    "ADR0353_ARTIFACT_BYTES",
    "ADR0353_ARTIFACT_RELATIVE_PATH",
    "ADR0353_ARTIFACT_SHA256",
    "ADR0353_CONFIG_SHA256",
    "ADR0353_HISTORICAL_RUNNER_CONTROL_SHA256",
    "ADR0353_IMPLEMENTATION_SHA256",
    "ADR0353_INVOCATION_SOURCE_COMMIT",
    "ADR0353_RESULT_PROTOCOL",
    "ADR0353_RESULT_PROTOCOL_SHA256",
    "ADR0353_TOTAL_SECONDS",
    "RetainedLegalH4TieAwareAffineRejection",
    "verify_adr0353_legal_h4_tie_aware_affine_record",
    "verify_adr0353_legal_h4_tie_aware_affine_result_artifact",
    "verify_adr0353_result_source_and_dependencies",
]
