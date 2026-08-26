"""Serializer-safe additive owner for the ADR-0401 work preflight.

This module imports neither consumed owner.  Handshake, exact-type serializer
probe, and campaign children use one literal-module subprocess transport.  The
handshake path imports neither CuPy nor the immutable scientific source.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from queue import Empty, Full, Queue
import secrets
import subprocess
import sys
from threading import Event, Thread
from time import perf_counter_ns
from typing import Any, Callable, Mapping

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordKind,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v3.json"
)
V1_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
V1_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
V2_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_V1_CONFIG = _ROOT / V1_CONFIG_RELATIVE_PATH
_CORRECTION_CONFIG = _ROOT / CORRECTION_CONFIG_RELATIVE_PATH
_V1_RESULT = _ROOT / V1_RESULT_RELATIVE_PATH
_V2_RESULT = _ROOT / V2_RESULT_RELATIVE_PATH
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH

PREREGISTERED_CONFIG_SHA256 = (
    "2c1a407dbd2a84e3d49d30544f47fef6bb6fffa74274e22d75acbf8ece2f00c1"
)
V1_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
CORRECTION_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
V1_RESULT_SHA256 = (
    "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830"
)
V2_RESULT_SHA256 = (
    "9b9a3f606004a281773f6dc83c86fe2f70811ab825fbf1e0b8b47c1c75abdad3"
)
V1_RESULT_BYTES = 5322
V2_RESULT_BYTES = 8508
V1_RESULT_RECORDS = 3
V2_RESULT_RECORDS = 4
PREREGISTRATION_COMMIT = "e772312f3ef938c746c5d1e6ca22f0acb7534b6e"

WORK_PREFLIGHT_V3_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0401-work-preflight-serializer-safe-exclusive-journal-v3"
).hexdigest()
WORK_PREFLIGHT_V3_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0401-work-preflight-serializer-safe-one-shot-campaign-v3"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"
)
_CHILD_MODE_ENV = "PONTIUS_ADR0401_WORK_PREFLIGHT_CHILD_MODE"
_CHILD_CHALLENGE_ENV = "PONTIUS_ADR0401_WORK_PREFLIGHT_CHILD_CHALLENGE"
_HANDSHAKE_MODE = "handshake"
_SERIALIZER_PROBE_MODE = "serializer_probe"
_CAMPAIGN_MODE = "campaign"
_EVENT_PREFIX = "PONTIUS_ADR0401_EVENT "

HANDSHAKE_WALL_LIMIT_NS = 10_000_000_000
SERIALIZER_PROBE_WALL_LIMIT_NS = 10_000_000_000
LABORATORY_WALL_LIMIT_NS = 240_000_000_000
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_ARTIFACT_BYTES = 16_777_216
MAXIMUM_CHILD_LINE_CHARACTERS = 1_048_576
MAXIMUM_STDERR_CHARACTERS = 4096

CLAIMS = {
    "v3_source_sealed": False,
    "serializer_probe_result": None,
    "real_compiler_resource_result": None,
    "calibration_result": None,
    "complete_25_numerical_value": None,
    "actual_45_card_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "action_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    payload: Mapping[str, object]
    sha256: str


@dataclass(frozen=True, slots=True)
class RetainedArtifacts:
    v1: Mapping[str, object]
    v2: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class BootstrapHandshake:
    event: Mapping[str, object]
    expected_challenge_sha256: str


@dataclass(frozen=True, slots=True)
class SerializerProbe:
    event: Mapping[str, object]
    expected_challenge_sha256: str


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v3 path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def parse_config(config: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(config, Mapping) or config.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v3"
    ):
        raise ValueError("work-preflight v3 config schema differs")
    parsed = dict(config)
    section_names = (
        "parent_identity",
        "retained_artifacts",
        "successor_scope",
        "new_identity_contract",
        "serializer_contract",
        "serializer_probe",
        "child_transport",
        "inherited_science",
        "reader_contract",
        "one_shot_lifecycle",
        "kill_criteria",
        "claims",
    )
    sections = {name: parsed.get(name) for name in section_names}
    if not all(isinstance(value, Mapping) for value in sections.values()):
        raise ValueError("work-preflight v3 config sections are malformed")
    parent = sections["parent_identity"]
    retained = sections["retained_artifacts"]
    scope = sections["successor_scope"]
    identity = sections["new_identity_contract"]
    serializer = sections["serializer_contract"]
    probe = sections["serializer_probe"]
    transport = sections["child_transport"]
    science = sections["inherited_science"]
    lifecycle = sections["one_shot_lifecycle"]
    claims = sections["claims"]
    assert isinstance(parent, Mapping)
    assert isinstance(retained, Mapping)
    assert isinstance(scope, Mapping)
    assert isinstance(identity, Mapping)
    assert isinstance(serializer, Mapping)
    assert isinstance(probe, Mapping)
    assert isinstance(transport, Mapping)
    assert isinstance(science, Mapping)
    assert isinstance(lifecycle, Mapping)
    assert isinstance(claims, Mapping)

    if (
        identity.get("owner_protocol_sha256") != WORK_PREFLIGHT_V3_PROTOCOL_SHA256
        or identity.get("campaign_sha256") != WORK_PREFLIGHT_V3_CAMPAIGN_SHA256
        or transport.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or transport.get("handshake_mode") != _HANDSHAKE_MODE
        or transport.get("serializer_probe_mode") != _SERIALIZER_PROBE_MODE
        or transport.get("campaign_mode") != _CAMPAIGN_MODE
        or transport.get("challenge_bytes") != 32
        or transport.get("handshake_wall_limit_ns") != HANDSHAKE_WALL_LIMIT_NS
        or transport.get("serializer_probe_wall_limit_ns")
        != SERIALIZER_PROBE_WALL_LIMIT_NS
        or transport.get("shared_transport_queue_entries") != 64
        or transport.get("bounded_stderr_characters") != MAXIMUM_STDERR_CHARACTERS
        or lifecycle.get("laboratory_total_wall_limit_ns", LABORATORY_WALL_LIMIT_NS)
        != LABORATORY_WALL_LIMIT_NS
        or lifecycle.get("maximum_event_count") != MAXIMUM_EVENT_COUNT
        or lifecycle.get("maximum_artifact_bytes") != MAXIMUM_ARTIFACT_BYTES
    ):
        raise ValueError("work-preflight v3 lifecycle contract differs")
    if (
        serializer.get("approved_dataclass_fully_qualified_name")
        != "pontius.legal_river_quotient_cuda_consumer.CudaRuntimeIdentity"
        or serializer.get("approved_dataclass_fields_in_declared_order")
        != [
            "device_name",
            "compute_capability",
            "device_total_bytes",
            "cuda_driver_version",
            "cuda_runtime_version",
            "cupy_version",
        ]
        or serializer.get("approved_dataclass_requires_exact_type_not_subclass")
        is not True
        or serializer.get("generic_vars_or___dict___object_fallback_forbidden")
        is not True
        or serializer.get("unknown_dataclass_namedtuple_slots_or_object_family_rejected")
        is not True
    ):
        raise ValueError("work-preflight v3 serializer contract differs")
    if (
        probe.get("child_mode") != _SERIALIZER_PROBE_MODE
        or probe.get("forced_exception_type") != "RuntimeError"
        or probe.get("forced_exception_message")
        != "forced_serializer_probe_compiler_failure"
        or probe.get("expected_event_kind") != "laboratory"
        or probe.get("expected_event_subkind") != "compiler_resource_failure"
        or probe.get("expected_event_reason")
        != "RuntimeError: forced_serializer_probe_compiler_failure"
        or probe.get("expected_terminal") != "compiler_or_primitive_rejection"
    ):
        raise ValueError("work-preflight v3 serializer-probe contract differs")
    v1 = retained.get("v1")
    v2 = retained.get("v2")
    if not isinstance(v1, Mapping) or not isinstance(v2, Mapping):
        raise ValueError("work-preflight v3 retained artifacts differ")
    for row, digest, byte_count, record_count, event_count, handshake in (
        (v1, V1_RESULT_SHA256, V1_RESULT_BYTES, V1_RESULT_RECORDS, 1, False),
        (v2, V2_RESULT_SHA256, V2_RESULT_BYTES, V2_RESULT_RECORDS, 2, True),
    ):
        if (
            row.get("sha256") != digest
            or row.get("bytes") != byte_count
            or row.get("record_count") != record_count
            or row.get("terminal") != "infrastructure_failure"
            or row.get("event_count") != event_count
            or row.get("handshake") is not handshake
            or row.get("phase_count") != 0
            or row.get("projection") is not None
        ):
            raise ValueError("work-preflight v3 retained artifact identity differs")
    if (
        scope.get("v3_result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or scope.get("scientific_source_file_is_read_only_and_hash_immutable")
        is not True
        or scope.get(
            "population_25_fixture_compile_allocation_launch_scalar_digest_or_gate_forbidden"
        )
        is not True
        or science.get("calibration_populations") != [10, 22]
        or science.get("projection_population_integer_only") != 25
        or science.get("phase_count") != 16
        or science.get("laboratory_total_wall_limit_ns") != LABORATORY_WALL_LIMIT_NS
        or science.get("target_projection_wall_limit_ns") != 180_000_000_000
        or science.get("exact_spill_load_store_count") is not None
        or dict(claims) != CLAIMS
    ):
        raise ValueError("work-preflight v3 scientific boundary differs")
    return parsed


_BOUND_PARENT_FIELDS = {
    "adr0394": "adr0394_relative_path",
    "adr0395": "adr0395_relative_path",
    "adr0398": "adr0398_relative_path",
    "adr0399": "adr0399_relative_path",
    "adr0400": "adr0400_relative_path",
    "v1_scientific_config": "v1_scientific_config_relative_path",
    "resource_correction_config": "resource_correction_config_relative_path",
    "v2_owner_config": "v2_owner_config_relative_path",
    "scientific_source": "scientific_source_relative_path",
    "v2_runner": "v2_runner_relative_path",
    "v2_reader": "v2_reader_relative_path",
    "v2_controls": "v2_controls_relative_path",
}


def _validate_bound_parent_files(config: Mapping[str, object]) -> None:
    parent = config["parent_identity"]
    assert isinstance(parent, Mapping)
    for label, path_field in _BOUND_PARENT_FIELDS.items():
        relative = parent.get(path_field)
        expected = parent.get(f"{label}_canonical_lf_sha256")
        if not isinstance(relative, str) or canonical_lf_sha256(_ROOT / relative) != expected:
            raise ValueError(f"work-preflight v3 bound parent differs: {label}")


def load_public_config(path: Path = _CONFIG) -> LoadedConfig:
    if not isinstance(path, Path):
        raise TypeError("work-preflight v3 config path must be a Path")
    raw = path.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight v3 config differs from ADR-0401")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("work-preflight v3 config must be an object")
    parsed = parse_config(value)
    _validate_bound_parent_files(parsed)
    return LoadedConfig(payload=parsed, sha256=digest)


def _retained_row(
    *,
    path: Path,
    expected_sha256: str,
    expected_bytes: int,
    expected_records: int,
    terminal: str,
    event_count: int,
    handshake: bool,
) -> dict[str, object]:
    raw = path.read_bytes()
    if (
        len(raw) != expected_bytes
        or sha256(raw).hexdigest() != expected_sha256
        or len(raw.splitlines()) != expected_records
    ):
        raise ValueError(f"retained work-preflight artifact differs: {path.name}")
    return {
        "sha256": expected_sha256,
        "byte_count": expected_bytes,
        "record_count": expected_records,
        "terminal": terminal,
        "event_count": event_count,
        "handshake": handshake,
        "phase_count": 0,
        "passed": False,
        "projection": None,
    }


def rebind_retained_artifacts() -> RetainedArtifacts:
    if not _V1_RESULT.is_file() or not _V2_RESULT.is_file():
        raise ValueError("retained work-preflight artifact is absent")
    from .legal_river_quotient_cuda_compensated_work_preflight_v2_result import (
        rebind_work_preflight_v2_journal,
    )

    rebound = rebind_work_preflight_v2_journal(_V2_RESULT.read_bytes())
    if (
        rebound.terminal != "infrastructure_failure"
        or rebound.passed is not False
        or rebound.event_count != 2
        or rebound.handshake is None
        or len(rebound.phases) != 0
        or rebound.projection is not None
    ):
        raise ValueError("retained v2 work-preflight semantics differ")
    return RetainedArtifacts(
        v1=_retained_row(
            path=_V1_RESULT,
            expected_sha256=V1_RESULT_SHA256,
            expected_bytes=V1_RESULT_BYTES,
            expected_records=V1_RESULT_RECORDS,
            terminal="infrastructure_failure",
            event_count=1,
            handshake=False,
        ),
        v2=_retained_row(
            path=_V2_RESULT,
            expected_sha256=V2_RESULT_SHA256,
            expected_bytes=V2_RESULT_BYTES,
            expected_records=V2_RESULT_RECORDS,
            terminal="infrastructure_failure",
            event_count=2,
            handshake=True,
        ),
    )


def _checked_git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    )
    return completed.stdout


_TRACKED_REQUIRED = (
    CONFIG_RELATIVE_PATH,
    V1_RESULT_RELATIVE_PATH,
    V2_RESULT_RELATIVE_PATH,
    "docs/decisions/ADR-0401-preregister-the-work-preflight-v3-evidence-serializer-recovery.md",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_adapter.py",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_runner.py",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py",
    "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v3.py",
)


def strict_git_metadata(output_path: Path = _OUTPUT) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("work-preflight v3 Git commit is malformed")
    for relative in _TRACKED_REQUIRED:
        _checked_git("ls-files", "--error-unmatch", "--", relative)
    raw = _checked_git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry for entry in raw.split(b"\0") if entry]
    allowed = f"?? {output_path.relative_to(_ROOT).as_posix()}".encode("utf-8")
    if entries not in ([], [allowed]):
        raise RuntimeError("work-preflight v3 Git boundary is dirty")
    return {
        "commit": commit,
        "dirty": False,
        "strict_status": True,
        "result_is_only_untracked_path": entries == [allowed] or not entries,
        "tracked_prerequisites": True,
    }


_DEPENDENCY_PATHS = {
    "owner_config": _CONFIG,
    "preregistration_adr": _ROOT
    / "docs/decisions/ADR-0401-preregister-the-work-preflight-v3-evidence-serializer-recovery.md",
    "v2_preregistration_adr": _ROOT
    / "docs/decisions/ADR-0398-preregister-the-bootstrap-safe-work-preflight-v2-owner.md",
    "v1_config": _V1_CONFIG,
    "resource_correction_config": _CORRECTION_CONFIG,
    "resource_correction_adr": _ROOT
    / "docs/decisions/ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md",
    "scientific_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "v1_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py",
    "v1_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py",
    "v1_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
    "v2_owner_config": _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json",
    "v2_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py",
    "v2_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_result.py",
    "v2_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v2.py",
    "v3_adapter": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_adapter.py",
    "v3_runner": Path(__file__),
    "v3_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py",
    "v3_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v3.py",
    "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    "parent_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "parent_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
    "retained_v1_result": _V1_RESULT,
    "retained_v2_result": _V2_RESULT,
}


def dependency_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for label, path in _DEPENDENCY_PATHS.items():
        raw = path.read_bytes()
        result[label] = sha256(
            raw if label.startswith("retained_") else raw.replace(b"\r\n", b"\n")
        ).hexdigest()
    return result


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-owner-header-v3",
        "owner_protocol_sha256": WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
        "campaign_sha256": WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "retained_v1_result_relative_path": V1_RESULT_RELATIVE_PATH,
        "retained_v1_result_sha256": V1_RESULT_SHA256,
        "retained_v2_result_relative_path": V2_RESULT_RELATIVE_PATH,
        "retained_v2_result_sha256": V2_RESULT_SHA256,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(CLAIMS),
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    event_count: int,
    last_event_semantic_identity_sha256: str | None,
    handshake_passed: bool,
    serializer_probe_passed: bool,
) -> dict[str, object]:
    allowed = {
        "completed_capacity_pass",
        "completed_capacity_rejection",
        "calibration_scientific_rejection",
        "compiler_or_primitive_rejection",
        "laboratory_wall_rejection",
        "infrastructure_failure",
    }
    if terminal not in allowed:
        raise ValueError("work-preflight v3 terminal class is unknown")
    if not isinstance(reason, str) or not reason:
        raise ValueError("work-preflight v3 terminal reason must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-terminal-v3",
        "terminal": terminal,
        "reason": reason[:4096],
        "passed": terminal == "completed_capacity_pass",
        "event_count": event_count,
        "last_event_semantic_identity_sha256": last_event_semantic_identity_sha256,
        "handshake_passed": handshake_passed,
        "serializer_probe_passed": serializer_probe_passed,
        "claims": dict(CLAIMS),
    }


def _failure_reason(error: BaseException) -> str:
    message = str(error) or "exception carried no message"
    return f"{type(error).__name__}: {message[:4096]}"


def _event_observation(
    *,
    event_index: int,
    event_kind: str,
    event: Mapping[str, object],
    config_sha256: str,
    source_commit: str,
) -> dict[str, object]:
    if not isinstance(event_kind, str) or not event_kind:
        raise ValueError("work-preflight v3 event kind must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-observation-v3",
        "event_index": event_index,
        "event_kind": event_kind,
        "config_sha256": config_sha256,
        "v1_config_sha256": V1_CONFIG_SHA256,
        "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        "source_commit": source_commit,
        "event": dict(event),
    }


def _child_emit(kind: str, payload: Mapping[str, object]) -> None:
    line = json.dumps(
        {"kind": kind, "payload": dict(payload)},
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    print(_EVENT_PREFIX + line, flush=True)


def _validate_challenge(challenge_hex: str) -> str:
    if (
        len(challenge_hex) != 64
        or any(character not in "0123456789abcdef" for character in challenge_hex)
    ):
        raise ValueError("work-preflight v3 child challenge is malformed")
    return sha256(bytes.fromhex(challenge_hex)).hexdigest()


def _handshake_child_main(challenge_hex: str) -> int:
    challenge_digest = _validate_challenge(challenge_hex)
    scientific_module = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
    cupy_loaded = any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)
    event = {
        "schema_version": "legal-river-work-preflight-bootstrap-handshake-v3",
        "challenge_sha256": challenge_digest,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "spec_name": None if __spec__ is None else __spec__.name,
        "runtime_name": __name__,
        "package_name": __package__,
        "python_no_bytecode": sys.dont_write_bytecode,
        "argv_count": len(sys.argv),
        "cupy_loaded": cupy_loaded,
        "scientific_source_loaded": scientific_module in sys.modules,
    }
    _child_emit("bootstrap_handshake", event)
    _child_emit(
        "child_terminal",
        {
            "schema_version": "legal-river-work-preflight-bootstrap-terminal-v3",
            "terminal": "bootstrap_handshake_pass",
            "passed": True,
        },
    )
    return 0


def _serializer_probe_child_main(challenge_hex: str) -> int:
    challenge_digest = _validate_challenge(challenge_hex)
    scientific_module = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
    before_cupy = any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)
    before_source = scientific_module in sys.modules
    try:
        from .legal_river_quotient_cuda_compensated_work_preflight_v3_adapter import (
            run_forced_serializer_probe,
        )

        probe = run_forced_serializer_probe()
        after_cupy = any(
            name == "cupy" or name.startswith("cupy.") for name in sys.modules
        )
        event = {
            "schema_version": "legal-river-work-preflight-serializer-probe-child-v3",
            "challenge_sha256": challenge_digest,
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "spec_name": None if __spec__ is None else __spec__.name,
            "runtime_name": __name__,
            "package_name": __package__,
            "python_no_bytecode": sys.dont_write_bytecode,
            "argv_count": len(sys.argv),
            "cupy_loaded_before": before_cupy,
            "cupy_loaded_after": after_cupy,
            "scientific_source_loaded_before": before_source,
            "scientific_source_loaded_after": scientific_module in sys.modules,
            "probe": probe,
        }
        _child_emit("serializer_probe", event)
        _child_emit(
            "child_terminal",
            {
                "schema_version": "legal-river-work-preflight-serializer-probe-terminal-v3",
                "terminal": "serializer_probe_pass",
                "passed": True,
            },
        )
        return 0
    except BaseException as error:  # noqa: BLE001 - first probe failure is evidence
        _child_emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v3",
                "reason": _failure_reason(error),
            },
        )
        return 1


def _campaign_child_main() -> int:
    try:
        from .legal_river_quotient_cuda_compensated_work_preflight_v3_adapter import (
            run_adapted_calibration_preflight,
        )

        terminal = run_adapted_calibration_preflight(_child_emit)
        _child_emit("child_terminal", terminal)
        return 0
    except BaseException as error:  # noqa: BLE001 - first failure is evidence
        _child_emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v3",
                "reason": _failure_reason(error),
            },
        )
        return 1


ChildProcessExecutor = Callable[
    [str, str | None, Callable[[str, Mapping[str, object]], None], int],
    Mapping[str, object],
]


def _run_child_process(
    mode: str,
    challenge_hex: str | None,
    emit: Callable[[str, Mapping[str, object]], None],
    wall_limit_ns: int,
) -> Mapping[str, object]:
    if mode not in {_HANDSHAKE_MODE, _SERIALIZER_PROBE_MODE, _CAMPAIGN_MODE}:
        raise ValueError("work-preflight v3 child mode differs")
    if isinstance(wall_limit_ns, bool) or not isinstance(wall_limit_ns, int) or wall_limit_ns <= 0:
        raise ValueError("work-preflight v3 child wall must be positive")
    if mode in {_HANDSHAKE_MODE, _SERIALIZER_PROBE_MODE}:
        if not isinstance(challenge_hex, str):
            raise ValueError("work-preflight v3 child challenge is absent")
    elif challenge_hex is not None:
        raise ValueError("work-preflight v3 campaign cannot carry a challenge")

    environment = os.environ.copy()
    environment.pop(_CHILD_MODE_ENV, None)
    environment.pop(_CHILD_CHALLENGE_ENV, None)
    environment[_CHILD_MODE_ENV] = mode
    if challenge_hex is not None:
        environment[_CHILD_CHALLENGE_ENV] = challenge_hex
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
        cwd=_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="ascii",
        errors="strict",
        bufsize=1,
    )
    queue: Queue[object] = Queue(maxsize=64)
    stop_reader = Event()
    stderr_chunks: list[str] = []
    stderr_length = 0

    def read_stdout() -> None:
        def put(item: object) -> bool:
            while not stop_reader.is_set():
                try:
                    queue.put(item, timeout=0.1)
                    return True
                except Full:
                    continue
            return False

        try:
            assert process.stdout is not None
            for line in process.stdout:
                if len(line) > MAXIMUM_CHILD_LINE_CHARACTERS:
                    put(RuntimeError("work-preflight v3 child line exceeds ceiling"))
                    return
                if not put(line):
                    return
        except BaseException as error:  # noqa: BLE001 - transport failure is evidence
            put(error)
        finally:
            put(None)

    def read_stderr() -> None:
        nonlocal stderr_length
        try:
            assert process.stderr is not None
            while True:
                chunk = process.stderr.read(4096)
                if not chunk:
                    return
                remaining = MAXIMUM_STDERR_CHARACTERS - stderr_length
                if remaining > 0:
                    stderr_chunks.append(chunk[:remaining])
                    stderr_length += min(len(chunk), remaining)
        except BaseException as error:  # noqa: BLE001 - retain bounded diagnostic
            text = f"<stderr-read-failure:{type(error).__name__}>"
            remaining = MAXIMUM_STDERR_CHARACTERS - stderr_length
            if remaining > 0:
                stderr_chunks.append(text[:remaining])
                stderr_length += min(len(text), remaining)

    stdout_thread = Thread(target=read_stdout, daemon=True)
    stderr_thread = Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    started = perf_counter_ns()
    child_terminal: Mapping[str, object] | None = None
    child_failure: str | None = None
    stdout_closed = False
    child_event_count = 0
    try:
        while True:
            remaining_ns = wall_limit_ns - (perf_counter_ns() - started)
            if remaining_ns <= 0:
                process.kill()
                process.wait(timeout=30.0)
                raise TimeoutError("child_wall_crossed")
            if stdout_closed and process.poll() is not None:
                break
            try:
                item = queue.get(timeout=min(1.0, remaining_ns / 1_000_000_000))
            except Empty:
                if process.poll() is not None and stdout_closed:
                    break
                continue
            if item is None:
                stdout_closed = True
                continue
            if isinstance(item, BaseException):
                raise RuntimeError("work-preflight v3 child stdout reader failed") from item
            if not isinstance(item, str) or not item.startswith(_EVENT_PREFIX):
                raise RuntimeError("work-preflight v3 child emitted an unframed line")
            value = json.loads(item[len(_EVENT_PREFIX):])
            if not isinstance(value, dict) or set(value) != {"kind", "payload"}:
                raise RuntimeError("work-preflight v3 child event is malformed")
            kind = value["kind"]
            payload = value["payload"]
            if not isinstance(kind, str) or not isinstance(payload, dict):
                raise RuntimeError("work-preflight v3 child event types differ")
            if kind == "child_terminal":
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v3 child terminal conflicts or repeats")
                child_terminal = payload
            elif kind == "worker_failure":
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v3 child failure conflicts or repeats")
                child_failure = str(payload.get("reason", "worker failed"))
            else:
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v3 child event follows terminal")
                if child_event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v3 child event count exceeds ceiling")
                emit(kind, payload)
                child_event_count += 1
        return_code = process.wait(timeout=30.0)
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)
        if child_failure is not None:
            raise RuntimeError(child_failure)
        if return_code != 0:
            stderr = "".join(stderr_chunks)
            raise RuntimeError(f"work-preflight v3 child exited {return_code}: {stderr}")
        if child_terminal is None:
            raise RuntimeError("work-preflight v3 child omitted terminal evidence")
        return child_terminal
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=30.0)
        stop_reader.set()
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def _validated_handshake_event(
    event: Mapping[str, object],
    *,
    expected_challenge_sha256: str,
) -> dict[str, object]:
    expected_keys = {
        "schema_version",
        "challenge_sha256",
        "literal_worker_module",
        "spec_name",
        "runtime_name",
        "package_name",
        "python_no_bytecode",
        "argv_count",
        "cupy_loaded",
        "scientific_source_loaded",
    }
    if not isinstance(event, Mapping) or set(event) != expected_keys:
        raise ValueError("work-preflight v3 handshake fields differ")
    if (
        event.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v3"
        or event.get("challenge_sha256") != expected_challenge_sha256
        or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("package_name") != "pontius"
        or event.get("python_no_bytecode") is not True
        or event.get("argv_count") != 1
        or event.get("cupy_loaded") is not False
        or event.get("scientific_source_loaded") is not False
    ):
        raise ValueError("work-preflight v3 handshake contract differs")
    _require_digest(event.get("challenge_sha256"), label="handshake challenge")
    return dict(event)


def _validated_serializer_probe_event(
    event: Mapping[str, object],
    *,
    expected_challenge_sha256: str,
) -> dict[str, object]:
    expected_keys = {
        "schema_version",
        "challenge_sha256",
        "literal_worker_module",
        "spec_name",
        "runtime_name",
        "package_name",
        "python_no_bytecode",
        "argv_count",
        "cupy_loaded_before",
        "cupy_loaded_after",
        "scientific_source_loaded_before",
        "scientific_source_loaded_after",
        "probe",
    }
    if not isinstance(event, Mapping) or set(event) != expected_keys:
        raise ValueError("work-preflight v3 serializer-probe fields differ")
    if (
        event.get("schema_version")
        != "legal-river-work-preflight-serializer-probe-child-v3"
        or event.get("challenge_sha256") != expected_challenge_sha256
        or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("package_name") != "pontius"
        or event.get("python_no_bytecode") is not True
        or event.get("argv_count") != 1
        or event.get("cupy_loaded_before") is not False
        or event.get("cupy_loaded_after") is not False
        or event.get("scientific_source_loaded_before") is not False
        or event.get("scientific_source_loaded_after") is not True
    ):
        raise ValueError("work-preflight v3 serializer-probe child contract differs")
    _require_digest(event.get("challenge_sha256"), label="serializer-probe challenge")
    probe = event.get("probe")
    if not isinstance(probe, Mapping):
        raise ValueError("work-preflight v3 serializer-probe result is absent")
    scientific_event = probe.get("scientific_event")
    scientific_terminal = probe.get("scientific_terminal")
    restoration = probe.get("restoration")
    runtime = probe.get("runtime")
    if not all(
        isinstance(value, Mapping)
        for value in (scientific_event, scientific_terminal, restoration, runtime)
    ):
        raise ValueError("work-preflight v3 serializer-probe evidence is malformed")
    assert isinstance(scientific_event, Mapping)
    assert isinstance(scientific_terminal, Mapping)
    assert isinstance(restoration, Mapping)
    assert isinstance(runtime, Mapping)
    expected_runtime_keys = {
        "device_name",
        "compute_capability",
        "device_total_bytes",
        "cuda_driver_version",
        "cuda_runtime_version",
        "cupy_version",
    }
    if (
        probe.get("schema_version") != "legal-river-work-preflight-serializer-probe-v3"
        or probe.get("passed") is not True
        or probe.get("cupy_loaded") is not False
        or probe.get("compiler_entry_calls") != 1
        or probe.get("forced_exception_reason")
        != "RuntimeError: forced_serializer_probe_compiler_failure"
        or set(runtime) != expected_runtime_keys
        or scientific_event.get("kind") != "compiler_resource_failure"
        or scientific_event.get("runtime") != runtime
        or scientific_event.get("reason")
        != "RuntimeError: forced_serializer_probe_compiler_failure"
        or scientific_terminal.get("terminal") != "compiler_or_primitive_rejection"
        or scientific_terminal.get("passed") is not False
        or set(restoration)
        != {
            "scientific_plain",
            "cupy_loader",
            "runtime_identity",
            "runtime_verifier",
            "kernel_compiler",
            "bounded_call_counter",
        }
        or not all(value is True for value in restoration.values())
    ):
        raise ValueError("work-preflight v3 serializer-probe semantics differ")
    return dict(event)


def _run_challenge_stage(
    *,
    mode: str,
    expected_kind: str,
    terminal_schema: str,
    terminal_name: str,
    wall_limit_ns: int,
    validator: Callable[..., dict[str, object]],
    challenge_factory: Callable[[int], bytes],
    process_executor: ChildProcessExecutor,
) -> tuple[dict[str, object], str]:
    challenge = challenge_factory(32)
    if not isinstance(challenge, bytes) or len(challenge) != 32:
        raise ValueError("work-preflight v3 challenge factory differs")
    challenge_digest = sha256(challenge).hexdigest()
    events: list[tuple[str, Mapping[str, object]]] = []

    def collect(kind: str, payload: Mapping[str, object]) -> None:
        events.append((kind, dict(payload)))

    try:
        terminal = process_executor(mode, challenge.hex(), collect, wall_limit_ns)
    except BaseException as error:  # noqa: BLE001 - lifecycle failures are typed
        raise RuntimeError(f"{mode}_failed: {_failure_reason(error)}") from error
    if len(events) != 1 or events[0][0] != expected_kind:
        raise ValueError(f"work-preflight v3 {mode} event sequence differs")
    if (
        not isinstance(terminal, Mapping)
        or terminal.get("schema_version") != terminal_schema
        or terminal.get("terminal") != terminal_name
        or terminal.get("passed") is not True
        or set(terminal) != {"schema_version", "terminal", "passed"}
    ):
        raise ValueError(f"work-preflight v3 {mode} terminal differs")
    return (
        validator(events[0][1], expected_challenge_sha256=challenge_digest),
        challenge_digest,
    )


def run_no_cuda_bootstrap_handshake(
    *,
    challenge_factory: Callable[[int], bytes] = secrets.token_bytes,
    process_executor: ChildProcessExecutor = _run_child_process,
) -> BootstrapHandshake:
    event, digest = _run_challenge_stage(
        mode=_HANDSHAKE_MODE,
        expected_kind="bootstrap_handshake",
        terminal_schema="legal-river-work-preflight-bootstrap-terminal-v3",
        terminal_name="bootstrap_handshake_pass",
        wall_limit_ns=HANDSHAKE_WALL_LIMIT_NS,
        validator=_validated_handshake_event,
        challenge_factory=challenge_factory,
        process_executor=process_executor,
    )
    return BootstrapHandshake(event=event, expected_challenge_sha256=digest)


def run_no_cuda_serializer_probe(
    *,
    challenge_factory: Callable[[int], bytes] = secrets.token_bytes,
    process_executor: ChildProcessExecutor = _run_child_process,
) -> SerializerProbe:
    event, digest = _run_challenge_stage(
        mode=_SERIALIZER_PROBE_MODE,
        expected_kind="serializer_probe",
        terminal_schema="legal-river-work-preflight-serializer-probe-terminal-v3",
        terminal_name="serializer_probe_pass",
        wall_limit_ns=SERIALIZER_PROBE_WALL_LIMIT_NS,
        validator=_validated_serializer_probe_event,
        challenge_factory=challenge_factory,
        process_executor=process_executor,
    )
    return SerializerProbe(event=event, expected_challenge_sha256=digest)


CampaignExecutor = Callable[
    [Callable[[str, Mapping[str, object]], None], int],
    Mapping[str, object],
]
HandshakeExecutor = Callable[[], BootstrapHandshake]
SerializerProbeExecutor = Callable[[], SerializerProbe]


def _subprocess_campaign_executor(
    emit: Callable[[str, Mapping[str, object]], None],
    wall_limit_ns: int,
) -> Mapping[str, object]:
    return _run_child_process(_CAMPAIGN_MODE, None, emit, wall_limit_ns)


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    hashes_loader: Callable[[], Mapping[str, str]] = dependency_hashes,
    retained_loader: Callable[[], RetainedArtifacts] = rebind_retained_artifacts,
    handshake_executor: HandshakeExecutor = run_no_cuda_bootstrap_handshake,
    serializer_probe_executor: SerializerProbeExecutor = run_no_cuda_serializer_probe,
    campaign_executor: CampaignExecutor = _subprocess_campaign_executor,
    reserved_path: Path = _RESERVED,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> OwnerExecution:
    """Consume one V3 path; injected controls never confer bootstrap authority."""

    if not isinstance(output_path, Path):
        raise TypeError("work-preflight v3 output must be a Path")
    if not isinstance(reserved_path, Path):
        raise TypeError("work-preflight v3 reserved path must be a Path")
    terminal_payload: dict[str, object]
    event_count = 0
    last_event_identity: str | None = None
    handshake_passed = False
    serializer_probe_passed = False
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
        campaign_sha256=WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
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
                raise TypeError("work-preflight v3 config loader returned wrong type")
            parse_config(loaded.payload)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("work-preflight v3 strict Git boundary rejected")
            retained = retained_loader()
            if not isinstance(retained, RetainedArtifacts):
                raise TypeError("work-preflight v3 retained loader returned wrong type")
            provenance = {
                "schema_version": "legal-river-work-preflight-provenance-v3",
                "config_sha256": loaded.sha256,
                "v1_config_sha256": V1_CONFIG_SHA256,
                "correction_config_sha256": CORRECTION_CONFIG_SHA256,
                "source_commit": str(git["commit"]),
                "source_dirty": False,
                "dependency_hashes": dict(hashes_loader()),
                "retained_v1": dict(retained.v1),
                "retained_v2": dict(retained.v2),
                "literal_worker_module": LITERAL_WORKER_MODULE,
                "serializer_boundary": "exact_CudaRuntimeIdentity_only_process_local",
                "reserved_actual_result_absent": not reserved_path.exists(),
            }

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, last_event_identity
                if event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v3 event count exceeds ceiling")
                observation = _event_observation(
                    event_index=event_count,
                    event_kind=kind,
                    event=event,
                    config_sha256=loaded.sha256,
                    source_commit=str(git["commit"]),
                )
                identity = _semantic_digest(observation)
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                event_count += 1
                last_event_identity = identity

            append_event("provenance", provenance)
            if provenance["reserved_actual_result_absent"] is not True:
                raise RuntimeError("reserved actual authority is present")

            laboratory_started = monotonic_ns()
            handshake = handshake_executor()
            if not isinstance(handshake, BootstrapHandshake):
                raise TypeError("work-preflight v3 handshake executor returned wrong type")
            accepted_handshake = _validated_handshake_event(
                handshake.event,
                expected_challenge_sha256=handshake.expected_challenge_sha256,
            )
            append_event(
                "bootstrap_handshake",
                {
                    "schema_version": "legal-river-work-preflight-bootstrap-accepted-v3",
                    "parent_challenge_sha256": handshake.expected_challenge_sha256,
                    "child": accepted_handshake,
                },
            )
            handshake_passed = True
            remaining = LABORATORY_WALL_LIMIT_NS - (
                monotonic_ns() - laboratory_started
            )
            if remaining <= 0:
                raise TimeoutError("laboratory_wall_crossed_after_handshake")

            serializer_probe = serializer_probe_executor()
            if not isinstance(serializer_probe, SerializerProbe):
                raise TypeError("work-preflight v3 serializer probe returned wrong type")
            accepted_probe = _validated_serializer_probe_event(
                serializer_probe.event,
                expected_challenge_sha256=serializer_probe.expected_challenge_sha256,
            )
            append_event(
                "serializer_probe",
                {
                    "schema_version": "legal-river-work-preflight-serializer-probe-accepted-v3",
                    "parent_challenge_sha256": (
                        serializer_probe.expected_challenge_sha256
                    ),
                    "child": accepted_probe,
                },
            )
            serializer_probe_passed = True
            remaining = LABORATORY_WALL_LIMIT_NS - (
                monotonic_ns() - laboratory_started
            )
            if remaining <= 0:
                raise TimeoutError("laboratory_wall_crossed_after_serializer_probe")

            def append_scientific_event(kind: str, event: Mapping[str, object]) -> None:
                if kind in {"provenance", "bootstrap_handshake", "serializer_probe"}:
                    raise RuntimeError("scientific child emitted a reserved lifecycle event")
                append_event(kind, event)

            terminal_evidence = campaign_executor(append_scientific_event, remaining)
            laboratory_stop = monotonic_ns()
            if laboratory_stop - laboratory_started > LABORATORY_WALL_LIMIT_NS:
                terminal_payload = _terminal_payload(
                    terminal="laboratory_wall_rejection",
                    reason="laboratory_wall_crossed",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                    handshake_passed=handshake_passed,
                    serializer_probe_passed=serializer_probe_passed,
                )
            else:
                if not isinstance(terminal_evidence, Mapping):
                    raise TypeError("work-preflight v3 campaign returned wrong type")
                terminal = terminal_evidence.get("terminal")
                passed = terminal_evidence.get("passed")
                if not isinstance(terminal, str) or not isinstance(passed, bool):
                    raise ValueError("work-preflight v3 terminal evidence is malformed")
                if passed is not (terminal == "completed_capacity_pass"):
                    raise ValueError("work-preflight v3 terminal pass bit disagrees")
                append_event("terminal_evidence", terminal_evidence)
                terminal_payload = _terminal_payload(
                    terminal=terminal,
                    reason="retained first terminal evidence",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                    handshake_passed=handshake_passed,
                    serializer_probe_passed=serializer_probe_passed,
                )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
                handshake_passed=handshake_passed,
                serializer_probe_passed=serializer_probe_passed,
            )
        except BaseException as error:  # noqa: BLE001 - first failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
                handshake_passed=handshake_passed,
                serializer_probe_passed=serializer_probe_passed,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("work-preflight v3 journal exceeds byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> None:
    if len(sys.argv) != 1:
        raise ValueError("work-preflight v3 owner accepts no arguments")
    child_mode = os.environ.get(_CHILD_MODE_ENV)
    if child_mode is not None:
        if child_mode in {_HANDSHAKE_MODE, _SERIALIZER_PROBE_MODE}:
            challenge = os.environ.get(_CHILD_CHALLENGE_ENV)
            if not isinstance(challenge, str):
                raise ValueError("work-preflight v3 child challenge is absent")
            if child_mode == _HANDSHAKE_MODE:
                raise SystemExit(_handshake_child_main(challenge))
            raise SystemExit(_serializer_probe_child_main(challenge))
        if child_mode == _CAMPAIGN_MODE:
            if _CHILD_CHALLENGE_ENV in os.environ:
                raise ValueError("work-preflight v3 campaign challenge is present")
            raise SystemExit(_campaign_child_main())
        raise ValueError("work-preflight v3 child mode is unknown")
    if _OUTPUT.exists():
        raise FileExistsError("work-preflight v3 authority is already consumed")
    if not _V1_RESULT.is_file() or not _V2_RESULT.is_file():
        raise FileNotFoundError("retained work-preflight authority is absent")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual authority must remain absent")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "legal-river work preflight v3: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "completed_capacity_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "BootstrapHandshake",
    "CONFIG_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "LoadedConfig",
    "OwnerExecution",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "RetainedArtifacts",
    "SerializerProbe",
    "V1_RESULT_RELATIVE_PATH",
    "V2_RESULT_RELATIVE_PATH",
    "WORK_PREFLIGHT_V3_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V3_PROTOCOL_SHA256",
    "canonical_lf_sha256",
    "dependency_hashes",
    "execute_owner_to_path",
    "load_public_config",
    "parse_config",
    "rebind_retained_artifacts",
    "run_no_cuda_bootstrap_handshake",
    "run_no_cuda_serializer_probe",
]
