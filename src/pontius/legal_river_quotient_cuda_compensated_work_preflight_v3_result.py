"""Standard-library rebinder for the serializer-safe ADR-0401 V3 journal."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
    recover_journal_file,
)
from . import legal_river_quotient_cuda_compensated_work_preflight_v2_result as _v2


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v3.json"
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
_V1_RESULT = _ROOT / V1_RESULT_RELATIVE_PATH
_V2_RESULT = _ROOT / V2_RESULT_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
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


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v3 reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _load_config() -> dict[str, object]:
    raw = _CONFIG.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight v3 reader config differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v3"
    ):
        raise ValueError("work-preflight v3 reader config schema differs")
    identity = _mapping(value.get("new_identity_contract"), label="v3 identity")
    scope = _mapping(value.get("successor_scope"), label="v3 scope")
    serializer = _mapping(value.get("serializer_contract"), label="v3 serializer")
    probe = _mapping(value.get("serializer_probe"), label="v3 probe")
    science = _mapping(value.get("inherited_science"), label="v3 science")
    claims = _mapping(value.get("claims"), label="v3 claims")
    if (
        identity.get("owner_protocol_sha256") != WORK_PREFLIGHT_V3_PROTOCOL_SHA256
        or identity.get("campaign_sha256") != WORK_PREFLIGHT_V3_CAMPAIGN_SHA256
        or scope.get("v3_result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or serializer.get("approved_dataclass_fully_qualified_name")
        != "pontius.legal_river_quotient_cuda_consumer.CudaRuntimeIdentity"
        or probe.get("expected_event_reason")
        != "RuntimeError: forced_serializer_probe_compiler_failure"
        or science.get("calibration_populations") != [10, 22]
        or science.get("projection_population_integer_only") != 25
        or science.get("phase_count") != 16
        or science.get("exact_spill_load_store_count") is not None
        or dict(claims) != CLAIMS
    ):
        raise ValueError("work-preflight v3 reader contract differs")
    return value


_DEPENDENCY_PATHS = {
    "owner_config": _CONFIG,
    "preregistration_adr": _ROOT
    / "docs/decisions/ADR-0401-preregister-the-work-preflight-v3-evidence-serializer-recovery.md",
    "v2_preregistration_adr": _ROOT
    / "docs/decisions/ADR-0398-preregister-the-bootstrap-safe-work-preflight-v2-owner.md",
    "v1_config": _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json",
    "resource_correction_config": _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v2.json",
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
    "v3_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_runner.py",
    "v3_reader": Path(__file__),
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


_V2_COMPATIBILITY_DEPENDENCIES = {
    "owner_config": "v2_owner_config",
    "preregistration_adr": "v2_preregistration_adr",
    "v1_config": "v1_config",
    "resource_correction_config": "resource_correction_config",
    "resource_correction_adr": "resource_correction_adr",
    "scientific_source": "scientific_source",
    "v1_runner": "v1_runner",
    "v1_reader": "v1_reader",
    "v1_controls": "v1_controls",
    "v2_runner": "v2_runner",
    "v2_reader": "v2_reader",
    "v2_controls": "v2_controls",
    "parent_source": "parent_source",
    "parent_controls": "parent_controls",
    "artifact_marker": "artifact_marker",
    "artifact_attributes": "artifact_attributes",
    "retained_v1_result": "retained_v1_result",
    "durable_journal": "durable_journal",
}


@dataclass(frozen=True, slots=True)
class WorkPreflightV3Rebinding:
    terminal: str
    passed: bool
    event_count: int
    handshake: Mapping[str, object] | None
    serializer_probe: Mapping[str, object] | None
    phases: tuple[object, ...]
    projection: Mapping[str, object] | None
    journal_byte_count: int
    v2_rebinding: _v2.WorkPreflightV2Rebinding


def _rebind_retained_artifacts() -> _v2.WorkPreflightV2Rebinding:
    v1 = _V1_RESULT.read_bytes()
    v2 = _V2_RESULT.read_bytes()
    if (
        len(v1) != V1_RESULT_BYTES
        or len(v1.splitlines()) != V1_RESULT_RECORDS
        or sha256(v1).hexdigest() != V1_RESULT_SHA256
        or len(v2) != V2_RESULT_BYTES
        or len(v2.splitlines()) != V2_RESULT_RECORDS
        or sha256(v2).hexdigest() != V2_RESULT_SHA256
    ):
        raise ValueError("work-preflight v3 reader retained artifact bytes differ")
    rebound = _v2.rebind_work_preflight_v2_journal(v2)
    if (
        rebound.terminal != "infrastructure_failure"
        or rebound.passed is not False
        or rebound.event_count != 2
        or rebound.handshake is None
        or rebound.phases
        or rebound.projection is not None
    ):
        raise ValueError("work-preflight v3 reader retained artifact semantics differ")
    return rebound


def _validate_handshake(event: Mapping[str, object]) -> dict[str, object]:
    if set(event) != {"schema_version", "parent_challenge_sha256", "child"}:
        raise ValueError("work-preflight v3 accepted-handshake fields differ")
    if event.get("schema_version") != (
        "legal-river-work-preflight-bootstrap-accepted-v3"
    ):
        raise ValueError("work-preflight v3 accepted-handshake schema differs")
    parent_digest = _require_digest(
        event.get("parent_challenge_sha256"),
        label="work-preflight v3 parent challenge",
    )
    child = _mapping(event.get("child"), label="work-preflight v3 child handshake")
    expected_child_keys = {
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
    if set(child) != expected_child_keys:
        raise ValueError("work-preflight v3 child-handshake fields differ")
    if (
        child.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v3"
        or child.get("challenge_sha256") != parent_digest
        or child.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or child.get("spec_name") != LITERAL_WORKER_MODULE
        or child.get("runtime_name") != "__main__"
        or child.get("package_name") != "pontius"
        or child.get("python_no_bytecode") is not True
        or child.get("argv_count") != 1
        or child.get("cupy_loaded") is not False
        or child.get("scientific_source_loaded") is not False
    ):
        raise ValueError("work-preflight v3 child-handshake contract differs")
    _require_digest(child.get("challenge_sha256"), label="v3 child challenge")
    return dict(event)


def _validate_serializer_probe(event: Mapping[str, object]) -> dict[str, object]:
    if set(event) != {"schema_version", "parent_challenge_sha256", "child"}:
        raise ValueError("work-preflight v3 accepted-probe fields differ")
    if event.get("schema_version") != (
        "legal-river-work-preflight-serializer-probe-accepted-v3"
    ):
        raise ValueError("work-preflight v3 accepted-probe schema differs")
    parent_digest = _require_digest(
        event.get("parent_challenge_sha256"),
        label="work-preflight v3 probe parent challenge",
    )
    child = _mapping(event.get("child"), label="work-preflight v3 probe child")
    if set(child) != {
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
    }:
        raise ValueError("work-preflight v3 probe-child fields differ")
    if (
        child.get("schema_version")
        != "legal-river-work-preflight-serializer-probe-child-v3"
        or child.get("challenge_sha256") != parent_digest
        or child.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or child.get("spec_name") != LITERAL_WORKER_MODULE
        or child.get("runtime_name") != "__main__"
        or child.get("package_name") != "pontius"
        or child.get("python_no_bytecode") is not True
        or child.get("argv_count") != 1
        or child.get("cupy_loaded_before") is not False
        or child.get("cupy_loaded_after") is not False
        or child.get("scientific_source_loaded_before") is not False
        or child.get("scientific_source_loaded_after") is not True
    ):
        raise ValueError("work-preflight v3 probe-child contract differs")
    probe = _mapping(child.get("probe"), label="work-preflight v3 probe result")
    if set(probe) != {
        "schema_version",
        "runtime",
        "scientific_event",
        "scientific_terminal",
        "forced_exception_reason",
        "compiler_entry_calls",
        "cupy_loaded",
        "restoration",
        "passed",
    }:
        raise ValueError("work-preflight v3 probe-result fields differ")
    runtime = _mapping(probe.get("runtime"), label="work-preflight v3 probe runtime")
    expected_runtime = {
        "device_name": "serializer-probe-device",
        "compute_capability": "00",
        "device_total_bytes": 0,
        "cuda_driver_version": 0,
        "cuda_runtime_version": 0,
        "cupy_version": "serializer-probe-no-cupy",
    }
    scientific_event = _mapping(
        probe.get("scientific_event"), label="work-preflight v3 probe event"
    )
    scientific_terminal = _mapping(
        probe.get("scientific_terminal"), label="work-preflight v3 probe terminal"
    )
    restoration = _mapping(
        probe.get("restoration"), label="work-preflight v3 probe restoration"
    )
    if (
        probe.get("schema_version") != "legal-river-work-preflight-serializer-probe-v3"
        or dict(runtime) != expected_runtime
        or probe.get("forced_exception_reason")
        != "RuntimeError: forced_serializer_probe_compiler_failure"
        or probe.get("compiler_entry_calls") != 1
        or probe.get("cupy_loaded") is not False
        or probe.get("passed") is not True
        or dict(scientific_event)
        != {
            "schema_version": "legal-river-work-preflight-laboratory-v1",
            "kind": "compiler_resource_failure",
            "runtime": expected_runtime,
            "stage": "kernel_compile_and_resource_inspection",
            "reason": "RuntimeError: forced_serializer_probe_compiler_failure",
            "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        }
        or dict(scientific_terminal)
        != {
            "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
            "terminal": "compiler_or_primitive_rejection",
            "failed_population": None,
            "passed": False,
            "projection": None,
        }
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


def _compatibility_line(
    *,
    protocol_sha256: str,
    campaign_sha256: str,
    kind: JournalRecordKind,
    sequence: int,
    previous_line_sha256: str | None,
    payload: Mapping[str, object],
) -> JournalRecordEnvelope:
    body = build_journal_record_body(
        protocol_sha256=protocol_sha256,
        campaign_sha256=campaign_sha256,
        kind=kind,
        sequence=sequence,
        previous_record_sha256=previous_line_sha256,
        semantic_identity_sha256=_semantic_digest(payload),
        payload=payload,
    )
    return JournalRecordEnvelope(body=body)


def _build_v2_validation_view(
    *,
    observations: tuple[Mapping[str, object], ...],
    terminal: Mapping[str, object],
    dependency_hashes: Mapping[str, object] | None,
) -> bytes:
    source_commit = "0" * 40
    compatibility_payloads: list[Mapping[str, object]] = []
    for observation in observations:
        kind = observation.get("event_kind")
        if kind == "serializer_probe":
            continue
        commit = observation.get("source_commit")
        if isinstance(commit, str):
            source_commit = commit
        event = _mapping(observation.get("event"), label="v3 compatibility event")
        if kind == "provenance":
            if dependency_hashes is None:
                raise ValueError("work-preflight v3 compatibility provenance is absent")
            retained_v1 = _mapping(
                event.get("retained_v1"), label="v3 retained v1"
            )
            compat_dependencies = {
                old: dependency_hashes[new]
                for old, new in _V2_COMPATIBILITY_DEPENDENCIES.items()
            }
            compat_event: Mapping[str, object] = {
                "schema_version": "legal-river-work-preflight-provenance-v2",
                "config_sha256": _v2.PREREGISTERED_CONFIG_SHA256,
                "v1_config_sha256": _v2.V1_CONFIG_SHA256,
                "correction_config_sha256": _v2.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "source_dirty": False,
                "dependency_hashes": compat_dependencies,
                "retained_v1": {
                    field: retained_v1[field]
                    for field in (
                        "sha256",
                        "byte_count",
                        "record_count",
                        "terminal",
                        "event_count",
                        "phase_count",
                        "passed",
                        "projection",
                    )
                },
                "literal_worker_module": _v2.LITERAL_WORKER_MODULE,
                "reserved_actual_result_absent": True,
            }
        elif kind == "bootstrap_handshake":
            child = _mapping(event.get("child"), label="v3 compatibility handshake")
            compat_event = {
                "schema_version": "legal-river-work-preflight-bootstrap-accepted-v2",
                "parent_challenge_sha256": event.get("parent_challenge_sha256"),
                "child": {
                    "schema_version": "legal-river-work-preflight-bootstrap-handshake-v2",
                    "challenge_sha256": child.get("challenge_sha256"),
                    "literal_worker_module": _v2.LITERAL_WORKER_MODULE,
                    "spec_name": _v2.LITERAL_WORKER_MODULE,
                    "runtime_name": child.get("runtime_name"),
                    "package_name": child.get("package_name"),
                    "python_no_bytecode": child.get("python_no_bytecode"),
                    "argv_count": child.get("argv_count"),
                    "cupy_loaded": child.get("cupy_loaded"),
                    "scientific_source_loaded": child.get("scientific_source_loaded"),
                },
            }
        else:
            compat_event = dict(event)
        compatibility_payloads.append(
            {
                "schema_version": "legal-river-work-preflight-owner-observation-v2",
                "event_index": len(compatibility_payloads),
                "event_kind": kind,
                "config_sha256": _v2.PREREGISTERED_CONFIG_SHA256,
                "v1_config_sha256": _v2.V1_CONFIG_SHA256,
                "correction_config_sha256": _v2.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "event": compat_event,
            }
        )

    header = {
        "schema_version": "legal-river-work-preflight-owner-header-v2",
        "owner_protocol_sha256": _v2.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        "campaign_sha256": _v2.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
        "config_relative_path": _v2.CONFIG_RELATIVE_PATH,
        "config_sha256": _v2.PREREGISTERED_CONFIG_SHA256,
        "result_relative_path": _v2.RESULT_RELATIVE_PATH,
        "retained_v1_result_relative_path": _v2.V1_RESULT_RELATIVE_PATH,
        "retained_v1_result_sha256": _v2.V1_RESULT_SHA256,
        "reserved_actual_result_relative_path": _v2.RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": _v2.PREREGISTRATION_COMMIT,
        "literal_worker_module": _v2.LITERAL_WORKER_MODULE,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(_v2.CLAIMS),
    }
    lines: list[bytes] = []
    previous: str | None = None
    envelope = _compatibility_line(
        protocol_sha256=_v2.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        campaign_sha256=_v2.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
        kind=JournalRecordKind.HEADER,
        sequence=0,
        previous_line_sha256=None,
        payload=header,
    )
    lines.append(envelope.line_bytes)
    previous = envelope.line_sha256
    last_event_identity: str | None = None
    for payload in compatibility_payloads:
        envelope = _compatibility_line(
            protocol_sha256=_v2.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
            campaign_sha256=_v2.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
            kind=JournalRecordKind.OBSERVATION,
            sequence=len(lines),
            previous_line_sha256=previous,
            payload=payload,
        )
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
        last_event_identity = envelope.body.semantic_identity_sha256
    compat_terminal = {
        "schema_version": "legal-river-work-preflight-owner-terminal-v2",
        "terminal": terminal.get("terminal"),
        "reason": str(terminal.get("reason", "v3 compatibility validation"))[:4096],
        "passed": terminal.get("passed"),
        "event_count": len(compatibility_payloads),
        "last_event_semantic_identity_sha256": last_event_identity,
        "handshake_passed": terminal.get("handshake_passed"),
        "claims": dict(_v2.CLAIMS),
    }
    envelope = _compatibility_line(
        protocol_sha256=_v2.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        campaign_sha256=_v2.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
        kind=JournalRecordKind.TERMINAL,
        sequence=len(lines),
        previous_line_sha256=previous,
        payload=compat_terminal,
    )
    lines.append(envelope.line_bytes)
    return b"".join(lines)


def rebind_work_preflight_v3_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> WorkPreflightV3Rebinding:
    if not isinstance(raw, bytes):
        raise TypeError("work-preflight v3 journal must be immutable bytes")
    _load_config()
    _rebind_retained_artifacts()
    if _RESERVED.exists():
        raise ValueError("work-preflight v3 reader reserved actual result is present")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight v3 journal is incomplete: {recovery.failure.reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("work-preflight v3 journal omits header or terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("work-preflight v3 first record is not a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("work-preflight v3 last record is not a terminal")
    if any(record.body.kind is JournalRecordKind.TERMINAL for record in records[:-1]):
        raise ValueError("work-preflight v3 has a suffix after terminal")
    for record in records:
        if _semantic_digest(record.body.payload) != record.body.semantic_identity_sha256:
            raise ValueError("work-preflight v3 semantic identity differs")

    expected_header = {
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
    if records[0].body.payload != expected_header:
        raise ValueError("work-preflight v3 header contract differs")

    observations: list[Mapping[str, object]] = []
    provenance: Mapping[str, object] | None = None
    dependency_hashes: Mapping[str, object] | None = None
    handshake: Mapping[str, object] | None = None
    serializer_probe: Mapping[str, object] | None = None
    bound_source_commit: str | None = None
    for index, record in enumerate(records[1:-1]):
        if record.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("work-preflight v3 middle record is not an observation")
        observation = record.body.payload
        if set(observation) != {
            "schema_version",
            "event_index",
            "event_kind",
            "config_sha256",
            "v1_config_sha256",
            "correction_config_sha256",
            "source_commit",
            "event",
        }:
            raise ValueError("work-preflight v3 observation fields differ")
        if (
            observation.get("schema_version")
            != "legal-river-work-preflight-owner-observation-v3"
            or observation.get("event_index") != index
            or observation.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
            or observation.get("v1_config_sha256") != V1_CONFIG_SHA256
            or observation.get("correction_config_sha256")
            != CORRECTION_CONFIG_SHA256
        ):
            raise ValueError("work-preflight v3 observation contract differs")
        source_commit = observation.get("source_commit")
        if (
            not isinstance(source_commit, str)
            or len(source_commit) != 40
            or any(character not in "0123456789abcdef" for character in source_commit)
        ):
            raise ValueError("work-preflight v3 observation commit is malformed")
        if bound_source_commit is None:
            bound_source_commit = source_commit
        elif source_commit != bound_source_commit:
            raise ValueError("work-preflight v3 observation commit changes")
        kind = observation.get("event_kind")
        if not isinstance(kind, str):
            raise ValueError("work-preflight v3 observation kind differs")
        event = _mapping(observation.get("event"), label="work-preflight v3 event")
        if kind == "provenance":
            if index != 0 or provenance is not None:
                raise ValueError("work-preflight v3 provenance placement differs")
            provenance = event
            if set(event) != {
                "schema_version",
                "config_sha256",
                "v1_config_sha256",
                "correction_config_sha256",
                "source_commit",
                "source_dirty",
                "dependency_hashes",
                "retained_v1",
                "retained_v2",
                "literal_worker_module",
                "serializer_boundary",
                "reserved_actual_result_absent",
            }:
                raise ValueError("work-preflight v3 provenance fields differ")
            if (
                event.get("schema_version")
                != "legal-river-work-preflight-provenance-v3"
                or event.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
                or event.get("v1_config_sha256") != V1_CONFIG_SHA256
                or event.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256
                or event.get("source_commit") != source_commit
                or event.get("source_dirty") is not False
                or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
                or event.get("serializer_boundary")
                != "exact_CudaRuntimeIdentity_only_process_local"
                or event.get("reserved_actual_result_absent") is not True
            ):
                raise ValueError("work-preflight v3 provenance contract differs")
            dependency_hashes = _mapping(
                event.get("dependency_hashes"), label="work-preflight v3 dependencies"
            )
            if set(dependency_hashes) != set(_DEPENDENCY_PATHS):
                raise ValueError("work-preflight v3 dependency set differs")
            if rebind_current_sources:
                for label, path in _DEPENDENCY_PATHS.items():
                    raw_dependency = path.read_bytes()
                    expected = sha256(
                        raw_dependency
                        if label.startswith("retained_")
                        else raw_dependency.replace(b"\r\n", b"\n")
                    ).hexdigest()
                    if dependency_hashes.get(label) != expected:
                        raise ValueError(f"work-preflight v3 dependency differs: {label}")
            expected_v1 = {
                "sha256": V1_RESULT_SHA256,
                "byte_count": V1_RESULT_BYTES,
                "record_count": V1_RESULT_RECORDS,
                "terminal": "infrastructure_failure",
                "event_count": 1,
                "handshake": False,
                "phase_count": 0,
                "passed": False,
                "projection": None,
            }
            expected_v2 = {
                "sha256": V2_RESULT_SHA256,
                "byte_count": V2_RESULT_BYTES,
                "record_count": V2_RESULT_RECORDS,
                "terminal": "infrastructure_failure",
                "event_count": 2,
                "handshake": True,
                "phase_count": 0,
                "passed": False,
                "projection": None,
            }
            if event.get("retained_v1") != expected_v1 or event.get("retained_v2") != expected_v2:
                raise ValueError("work-preflight v3 retained provenance differs")
        elif kind == "bootstrap_handshake":
            if index != 1 or provenance is None or handshake is not None:
                raise ValueError("work-preflight v3 handshake placement differs")
            handshake = _validate_handshake(event)
        elif kind == "serializer_probe":
            if (
                index != 2
                or handshake is None
                or serializer_probe is not None
            ):
                raise ValueError("work-preflight v3 serializer-probe placement differs")
            serializer_probe = _validate_serializer_probe(event)
        else:
            if handshake is None or serializer_probe is None:
                raise ValueError("work-preflight v3 science precedes lifecycle seals")
        observations.append(observation)

    if observations and provenance is None:
        raise ValueError("work-preflight v3 observations omit provenance")

    terminal = records[-1].body.payload
    if set(terminal) != {
        "schema_version",
        "terminal",
        "reason",
        "passed",
        "event_count",
        "last_event_semantic_identity_sha256",
        "handshake_passed",
        "serializer_probe_passed",
        "claims",
    }:
        raise ValueError("work-preflight v3 terminal fields differ")
    terminal_name = terminal.get("terminal")
    allowed = {
        "completed_capacity_pass",
        "completed_capacity_rejection",
        "calibration_scientific_rejection",
        "compiler_or_primitive_rejection",
        "laboratory_wall_rejection",
        "infrastructure_failure",
    }
    if (
        terminal.get("schema_version")
        != "legal-river-work-preflight-owner-terminal-v3"
        or terminal_name not in allowed
        or not isinstance(terminal.get("reason"), str)
        or not terminal.get("reason")
        or terminal.get("passed") is not (terminal_name == "completed_capacity_pass")
        or terminal.get("event_count") != len(observations)
        or terminal.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight v3 terminal contract differs")
    last_identity = None if not observations else records[-2].body.semantic_identity_sha256
    if terminal.get("last_event_semantic_identity_sha256") != last_identity:
        raise ValueError("work-preflight v3 terminal last-event identity differs")
    if terminal.get("handshake_passed") is not (handshake is not None):
        raise ValueError("work-preflight v3 terminal handshake bit differs")
    if terminal.get("serializer_probe_passed") is not (serializer_probe is not None):
        raise ValueError("work-preflight v3 terminal serializer-probe bit differs")
    if terminal_name not in {"infrastructure_failure", "laboratory_wall_rejection"} and (
        handshake is None or serializer_probe is None
    ):
        raise ValueError("work-preflight v3 scientific terminal lacks lifecycle seals")

    v2_view = _build_v2_validation_view(
        observations=tuple(observations),
        terminal=terminal,
        dependency_hashes=dependency_hashes,
    )
    rebound = _v2.rebind_work_preflight_v2_journal(
        v2_view,
        rebind_current_sources=False,
    )
    if rebound.terminal != terminal_name or rebound.passed is not terminal.get("passed"):
        raise ValueError("work-preflight v3 nested scientific terminal differs")
    return WorkPreflightV3Rebinding(
        terminal=str(terminal_name),
        passed=bool(terminal.get("passed")),
        event_count=len(observations),
        handshake=handshake,
        serializer_probe=serializer_probe,
        phases=tuple(rebound.phases),
        projection=rebound.projection,
        journal_byte_count=len(raw),
        v2_rebinding=rebound,
    )


def rebind_work_preflight_v3_file(
    path: Path = _RESULT,
) -> WorkPreflightV3Rebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight v3 result is incomplete: {recovery.failure.reason}")
    return rebind_work_preflight_v3_journal(path.read_bytes())


__all__ = [
    "CONFIG_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "V1_RESULT_RELATIVE_PATH",
    "V2_RESULT_RELATIVE_PATH",
    "WORK_PREFLIGHT_V3_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V3_PROTOCOL_SHA256",
    "WorkPreflightV3Rebinding",
    "canonical_lf_sha256",
    "rebind_work_preflight_v3_file",
    "rebind_work_preflight_v3_journal",
]
