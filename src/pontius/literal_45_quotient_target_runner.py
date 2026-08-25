"""Exclusive, durable, no-argument owner for the literal-45 quotient target."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any

from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordKind,
)
from .literal_45_quotient_target_result import (
    CLAIMS,
    COMPATIBLE_REFERENCE_BYTES,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_PEAK_BYTES,
    DEVICE_RESERVE_BYTES,
    ERROR_LIMITS,
    FEATURE_WIDTH,
    HOST_NUMERIC_CAP_BYTES,
    HOST_PEAK_BYTES,
    HOST_RESERVE_BYTES,
    MAXIMUM_ARTIFACT_BYTES,
    EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS,
    EXPECTED_TARGET_SCIENTIFIC_CALLS,
    OWNER_PROTOCOL_SHA256,
    PHASE_POOL_LIMITS,
    QUERY_SAMPLE_FEATURES,
    QUERY_SAMPLE_RANKS,
    REQUIRED_RUNTIME,
    RESULT_RELATIVE_PATH,
    SOURCE_REFERENCE_BYTES,
    SOURCE_SAMPLE_RANKS,
    SOURCE_SEAL_PARENT_COMMIT,
    TARGET_WALL_LIMIT_MS,
    TELEMETRY_TRANSITIONS,
    reconstruct_target_observation,
    target_geometry,
    target_work,
)
from .runner_harness_v2 import LoadedConfig, load_config


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/literal-45-quotient-target-v1.json"
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_ARTIFACT_MARKER = _ROOT / "artifacts/README.md"
_GIT_ATTRIBUTES = _ROOT / ".gitattributes"
_ADR0379 = (
    _ROOT / "docs/decisions/ADR-0379-seal-the-literal-45-quotient-liveness-model.md"
)
_ADR0381 = (
    _ROOT / "docs/decisions/ADR-0381-seal-the-bounded-quotient-validation-seam.md"
)
_ADR0382 = (
    _ROOT
    / "docs/decisions/ADR-0382-preregister-the-one-shot-literal-45-quotient-owner.md"
)
_LIVENESS = _ROOT / "src/pontius/literal_45_quotient_liveness.py"
_BOUNDED_SEAM = _ROOT / "src/pontius/gpu_quotient_validation_seam.py"
_BOUNDED_CONTROLS = _ROOT / "tests/test_gpu_quotient_validation_seam.py"
_STAGED_KERNELS = _ROOT / "src/pontius/gpu_quotient_staged_scaling.py"
_BOUNDED_KERNELS = _ROOT / "src/pontius/gpu_occupied_card_quotient.py"
_WINDOWS_MEMORY = _ROOT / "src/pontius/windows_process_memory.py"
_DURABLE_JOURNAL = _ROOT / "src/pontius/durable_evidence_journal.py"
_TARGET = _ROOT / "src/pontius/literal_45_quotient_target.py"
_RUNNER = Path(__file__)
_READER = _ROOT / "src/pontius/literal_45_quotient_target_result.py"
_TARGET_CONTROLS = _ROOT / "tests/test_literal_45_quotient_target.py"
_READER_CONTROLS = _ROOT / "tests/test_literal_45_quotient_target_result.py"

_CANONICAL_PATHS = {
    "expected_adr0379_sha256": _ADR0379,
    "expected_adr0381_sha256": _ADR0381,
    "expected_adr0382_sha256": _ADR0382,
    "expected_liveness_sha256": _LIVENESS,
    "expected_bounded_seam_sha256": _BOUNDED_SEAM,
    "expected_bounded_controls_sha256": _BOUNDED_CONTROLS,
    "expected_staged_kernels_sha256": _STAGED_KERNELS,
    "expected_bounded_kernels_sha256": _BOUNDED_KERNELS,
    "expected_windows_memory_sha256": _WINDOWS_MEMORY,
    "expected_durable_journal_sha256": _DURABLE_JOURNAL,
    "expected_target_sha256": _TARGET,
    "expected_runner_sha256": _RUNNER,
    "expected_reader_sha256": _READER,
    "expected_target_controls_sha256": _TARGET_CONTROLS,
    "expected_reader_controls_sha256": _READER_CONTROLS,
    "expected_artifact_marker_sha256": _ARTIFACT_MARKER,
    "expected_gitattributes_sha256": _GIT_ATTRIBUTES,
}

_CAMPAIGN_SHA256 = sha256(
    (
        OWNER_PROTOCOL_SHA256
        + "|"
        + RESULT_RELATIVE_PATH
        + "|"
        + SOURCE_SEAL_PARENT_COMMIT
    ).encode("ascii")
).hexdigest()
_MAXIMUM_OBSERVATION_JSON_BYTES = 786_432


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"literal-45 provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _frozen_contract() -> dict[str, object]:
    return {
        "geometry": target_geometry(),
        "model": {
            "host_numeric_cap_bytes": HOST_NUMERIC_CAP_BYTES,
            "device_numeric_cap_bytes": DEVICE_NUMERIC_CAP_BYTES,
            "host_reserve_bytes": HOST_RESERVE_BYTES,
            "device_reserve_bytes": DEVICE_RESERVE_BYTES,
            "host_peak_bytes": HOST_PEAK_BYTES,
            "device_peak_bytes": DEVICE_PEAK_BYTES,
            "source_reference_bytes": SOURCE_REFERENCE_BYTES,
            "compatible_reference_bytes": COMPATIBLE_REFERENCE_BYTES,
            "source_reference_chunks": 125,
            "compatible_reference_chunks": 14,
            "phase_pool_limits": PHASE_POOL_LIMITS,
        },
        "work": target_work(),
        "target_call_counts": {
            "execution": 1,
            "numeric_allocation": EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS,
            "scientific": EXPECTED_TARGET_SCIENTIFIC_CALLS,
        },
        "source_sample_ranks": list(SOURCE_SAMPLE_RANKS),
        "query_sample_ranks": list(QUERY_SAMPLE_RANKS),
        "query_sample_features": list(QUERY_SAMPLE_FEATURES),
        "telemetry_transitions": list(TELEMETRY_TRANSITIONS),
        "required_runtime": REQUIRED_RUNTIME,
        "error_limits": ERROR_LIMITS,
        "target_wall_limit_ms": int(TARGET_WALL_LIMIT_MS),
        "release_allowances": {
            "device_free_bytes": 16_777_216,
            "process_private_bytes": 268_435_456,
            "host_available_physical_bytes": 536_870_912,
        },
        "claims": CLAIMS,
    }


def parse_config(config: Mapping[str, Any]) -> dict[str, object]:
    plain = _plain(config)
    expected_fields = {
        "schema_version",
        "evidence_stage",
        "source_seal_parent_commit",
        "owner_protocol_sha256",
        "durable_journal_protocol_sha256",
        "artifact_parent_relative_path",
        "artifact_marker_relative_path",
        "result_relative_path",
        "maximum_config_bytes",
        "maximum_artifact_bytes",
        "maximum_observation_json_bytes",
        "require_repository_venv",
        "require_no_arguments",
        "require_fresh_minus_b",
        "require_clean_git_state_before_result",
        "require_tracked_parent_and_sources",
        "require_result_absent",
        "require_exclusive_create",
        "require_fsync_each_record",
        "require_header_before_target_import",
        "require_stop_after_terminal",
        "require_no_retry_or_substitution",
        "require_zero_actions_quality_and_truncation",
        "contract",
        *_CANONICAL_PATHS,
    }
    if set(plain) != expected_fields:
        raise ValueError("literal-45 config fields differ from the source seal")
    for field, path in _CANONICAL_PATHS.items():
        if plain[field] != canonical_lf_sha256(path):
            raise ValueError(f"literal-45 provenance mismatch: {field}")
    frozen = {
        "schema_version": "literal-45-quotient-target-config-v1",
        "evidence_stage": "source_sealed_after_adr0382_before_first_literal_45_invocation",
        "source_seal_parent_commit": SOURCE_SEAL_PARENT_COMMIT,
        "owner_protocol_sha256": OWNER_PROTOCOL_SHA256,
        "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        "artifact_parent_relative_path": "artifacts",
        "artifact_marker_relative_path": "artifacts/README.md",
        "result_relative_path": RESULT_RELATIVE_PATH,
        "maximum_config_bytes": 1_048_576,
        "maximum_artifact_bytes": MAXIMUM_ARTIFACT_BYTES,
        "maximum_observation_json_bytes": _MAXIMUM_OBSERVATION_JSON_BYTES,
        "require_repository_venv": True,
        "require_no_arguments": True,
        "require_fresh_minus_b": True,
        "require_clean_git_state_before_result": True,
        "require_tracked_parent_and_sources": True,
        "require_result_absent": True,
        "require_exclusive_create": True,
        "require_fsync_each_record": True,
        "require_header_before_target_import": True,
        "require_stop_after_terminal": True,
        "require_no_retry_or_substitution": True,
        "require_zero_actions_quality_and_truncation": True,
        "contract": _frozen_contract(),
    }
    for field, expected in frozen.items():
        if plain[field] != expected:
            raise ValueError(f"literal-45 config drifted: {field}")
    return plain


def _validate_python_invocation() -> None:
    expected = (_ROOT / ".venv/Scripts/python.exe").resolve()
    observed = Path(sys.executable).resolve()
    if observed != expected:
        raise RuntimeError("literal-45 owner requires the repository .venv Python")
    if sys.flags.dont_write_bytecode != 1:
        raise RuntimeError("literal-45 owner requires Python -B")


def load_public_config() -> LoadedConfig:
    loaded = load_config(
        _CONFIG,
        schema_validator=parse_config,
        maximum_bytes=1_048_576,
    )
    parse_config(loaded.payload)
    _validate_python_invocation()
    return loaded


def _checked_git(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        timeout=10.0,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"literal-45 Git metadata failed: {message}")
    return result.stdout


def strict_git_metadata(output_path: Path = _OUTPUT) -> dict[str, object]:
    if output_path.resolve() != _OUTPUT.resolve():
        raise ValueError("public literal-45 Git check requires the frozen result path")
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    status_raw = _checked_git(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    entries = [entry for entry in status_raw.split(b"\0") if entry]
    allowed = f"?? {RESULT_RELATIVE_PATH}".encode("utf-8")
    unexpected = [entry for entry in entries if entry.replace(b"\\", b"/") != allowed]
    if unexpected:
        raise RuntimeError("literal-45 owner requires a clean source boundary")
    tracked_paths = [
        "artifacts/README.md",
        ".gitattributes",
        "experiments/configs/literal-45-quotient-target-v1.json",
        "src/pontius/literal_45_quotient_target.py",
        "src/pontius/literal_45_quotient_target_runner.py",
        "src/pontius/literal_45_quotient_target_result.py",
        "tests/test_literal_45_quotient_target.py",
        "tests/test_literal_45_quotient_target_result.py",
    ]
    for relative in tracked_paths:
        observed = _checked_git("ls-files", "--error-unmatch", "--", relative)
        if observed.decode("utf-8").strip().replace("\\", "/") != relative:
            raise RuntimeError(f"literal-45 source is not tracked exactly: {relative}")
    return {
        "commit": commit,
        "dirty": False,
        "strict_status": True,
        "result_is_only_untracked_path": entries == [allowed] or not entries,
        "tracked_source_count": len(tracked_paths),
    }


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            dict(payload),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


def _header_payload() -> dict[str, object]:
    return {
        "schema_version": "literal-45-quotient-owner-header-v1",
        "owner_protocol_sha256": OWNER_PROTOCOL_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "source_seal_parent_commit": SOURCE_SEAL_PARENT_COMMIT,
        "claims": dict(CLAIMS),
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    observation_semantic_identity_sha256: str | None,
) -> dict[str, object]:
    allowed = {
        "completed_pass",
        "live_admission_rejected",
        "allocation_rejected",
        "scientific_rejected",
        "infrastructure_failure",
    }
    if terminal not in allowed:
        raise ValueError("literal-45 terminal class is unknown")
    if not isinstance(reason, str) or not reason:
        raise ValueError("literal-45 terminal reason must be nonempty")
    return {
        "schema_version": "literal-45-quotient-owner-terminal-v1",
        "terminal": terminal,
        "reason": reason,
        "passed": terminal == "completed_pass",
        "observation_semantic_identity_sha256": observation_semantic_identity_sha256,
        "claims": dict(CLAIMS),
    }


def _failure_reason(error: Exception) -> str:
    message = str(error) or "exception carried no message"
    # An exception cannot be allowed to defeat the frozen artifact ceiling.
    return f"{type(error).__name__}: {message[:4096]}"


def _default_target_executor() -> Mapping[str, object]:
    # This import is intentionally below the durable header in execute_owner_to_path.
    from .literal_45_quotient_target import execute_literal_45_quotient_target

    return execute_literal_45_quotient_target()


def _observation_json_size(payload: Mapping[str, object]) -> int:
    return len(
        json.dumps(
            dict(payload),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    )


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    observation: Mapping[str, object] | None


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    target_executor: Callable[[], Mapping[str, object]] | None = None,
    monotonic: Callable[[], float] = perf_counter,
) -> OwnerExecution:
    """Consume one path; tests inject only synthetic post-header dependencies."""

    if not isinstance(output_path, Path):
        raise TypeError("literal-45 owner output must be a Path")
    started = monotonic()
    observation_payload: dict[str, object] | None = None
    observation_identity: str | None = None
    terminal_payload: dict[str, object] | None = None
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=OWNER_PROTOCOL_SHA256,
        campaign_sha256=_CAMPAIGN_SHA256,
    ) as writer:
        header = _header_payload()
        writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=_semantic_digest(header),
            payload=header,
        )
        try:
            loaded = config_loader()
            if not isinstance(loaded, LoadedConfig):
                raise TypeError("literal-45 config loader returned the wrong type")
            parsed = parse_config(loaded.payload)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("literal-45 strict Git boundary rejected")
            executor = _default_target_executor if target_executor is None else target_executor
            target = executor()
            if not isinstance(target, Mapping):
                raise TypeError("literal-45 target executor returned the wrong type")
            target_plain = _plain(target)
            if _observation_json_size(target_plain) > int(
                parsed["maximum_observation_json_bytes"]
            ):
                raise ValueError("literal-45 target observation exceeds its byte ceiling")
            rebound = reconstruct_target_observation(target_plain)
            observation_payload = {
                "schema_version": "literal-45-quotient-owner-observation-v1",
                "config_sha256": loaded.sha256,
                "source_commit": str(git["commit"]),
                "source_dirty": False,
                "target": target_plain,
            }
            observation_identity = _semantic_digest(observation_payload)
            writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=observation_identity,
                payload=observation_payload,
            )
            terminal_payload = _terminal_payload(
                terminal=rebound.terminal,
                reason=rebound.reason,
                observation_semantic_identity_sha256=observation_identity,
            )
        except Exception as error:  # noqa: BLE001 - first failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=_failure_reason(error),
                observation_semantic_identity_sha256=observation_identity,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("literal-45 completed journal exceeds its byte ceiling")
    _ = monotonic() - started  # owner overhead is not a scientific timing field
    return OwnerExecution(terminal=terminal_payload, observation=observation_payload)


def main() -> None:
    if len(sys.argv) != 1:
        raise ValueError("literal-45 owner accepts no arguments")
    if _OUTPUT.exists():
        raise FileExistsError("literal-45 authority is already consumed")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "literal-45 quotient target: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "completed_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "OwnerExecution",
    "canonical_lf_sha256",
    "execute_owner_to_path",
    "load_public_config",
    "parse_config",
    "strict_git_metadata",
]
