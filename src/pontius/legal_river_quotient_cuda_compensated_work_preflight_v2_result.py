"""Standard-library rebinder for the bootstrap-safe ADR-0398 v2 journal."""

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
from . import legal_river_quotient_cuda_compensated_work_preflight_result as _v1


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json"
)
V1_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_V1_RESULT = _ROOT / V1_RESULT_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH

PREREGISTERED_CONFIG_SHA256 = (
    "e7f2a60035aad77d20461b4e5288bd85375f751b2d9ec410d2f197cfcacaf334"
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
V1_RESULT_BYTES = 5322
V1_RESULT_RECORDS = 3
PREREGISTRATION_COMMIT = "2432bee9d003edda665673652b790f9a44e0b120"
WORK_PREFLIGHT_V2_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0398-work-preflight-bootstrap-safe-exclusive-journal-v2"
).hexdigest()
WORK_PREFLIGHT_V2_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0398-work-preflight-bootstrap-safe-one-shot-campaign-v2"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
)

CLAIMS = {
    "bootstrap_handshake_result": None,
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
        raise ValueError(f"work-preflight v2 reader path is absent: {path}")
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
        raise ValueError("work-preflight v2 reader config differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v2"
    ):
        raise ValueError("work-preflight v2 reader config schema differs")
    return value


_DEPENDENCY_PATHS = {
    "owner_config": _CONFIG,
    "preregistration_adr": _ROOT
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
    "v2_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py",
    "v2_reader": Path(__file__),
    "v2_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v2.py",
    "parent_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "parent_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
    "retained_v1_result": _V1_RESULT,
    "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
}


_V1_COMPATIBILITY_DEPENDENCIES = {
    "config": "v1_config",
    "resource_correction_config": "resource_correction_config",
    "resource_correction_adr": "resource_correction_adr",
    "source": "scientific_source",
    "controls": "v1_controls",
    "runner": "v1_runner",
    "reader": "v1_reader",
    "parent_source": "parent_source",
    "parent_controls": "parent_controls",
    "artifact_marker": "artifact_marker",
    "artifact_attributes": "artifact_attributes",
}


@dataclass(frozen=True, slots=True)
class WorkPreflightV2Rebinding:
    terminal: str
    passed: bool
    event_count: int
    handshake: Mapping[str, object] | None
    phases: tuple[_v1.ReboundPhase, ...]
    projection: Mapping[str, object] | None
    journal_byte_count: int
    scientific_rebinding: _v1.WorkPreflightRebinding


def _rebind_retained_v1() -> _v1.WorkPreflightRebinding:
    raw = _V1_RESULT.read_bytes()
    if (
        len(raw) != V1_RESULT_BYTES
        or len(raw.splitlines()) != V1_RESULT_RECORDS
        or sha256(raw).hexdigest() != V1_RESULT_SHA256
    ):
        raise ValueError("work-preflight v2 reader retained v1 bytes differ")
    rebound = _v1.rebind_work_preflight_journal(raw)
    if (
        rebound.terminal != "infrastructure_failure"
        or rebound.passed is not False
        or rebound.event_count != 1
        or rebound.phases
        or rebound.projection is not None
    ):
        raise ValueError("work-preflight v2 reader retained v1 semantics differ")
    return rebound


def _validate_handshake(event: Mapping[str, object]) -> dict[str, object]:
    if set(event) != {"schema_version", "parent_challenge_sha256", "child"}:
        raise ValueError("work-preflight v2 accepted-handshake fields differ")
    if event.get("schema_version") != (
        "legal-river-work-preflight-bootstrap-accepted-v2"
    ):
        raise ValueError("work-preflight v2 accepted-handshake schema differs")
    parent_digest = _require_digest(
        event.get("parent_challenge_sha256"),
        label="work-preflight v2 parent challenge",
    )
    child = _mapping(event.get("child"), label="work-preflight v2 child handshake")
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
        raise ValueError("work-preflight v2 child-handshake fields differ")
    if (
        child.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v2"
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
        raise ValueError("work-preflight v2 child-handshake contract differs")
    _require_digest(child.get("challenge_sha256"), label="work-preflight v2 child challenge")
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


def _build_v1_scientific_validation_view(
    *,
    observations: tuple[Mapping[str, object], ...],
    terminal: Mapping[str, object],
    dependency_hashes: Mapping[str, object] | None,
) -> bytes:
    source_commit = "0" * 40
    compatibility_payloads: list[Mapping[str, object]] = []
    for observation in observations:
        kind = observation.get("event_kind")
        if kind == "bootstrap_handshake":
            continue
        commit = observation.get("source_commit")
        if isinstance(commit, str):
            source_commit = commit
        event = _mapping(observation.get("event"), label="compatibility event")
        if kind == "provenance":
            if dependency_hashes is None:
                raise ValueError("work-preflight v2 compatibility provenance is absent")
            compat_dependencies = {
                old: dependency_hashes[new]
                for old, new in _V1_COMPATIBILITY_DEPENDENCIES.items()
            }
            compat_event = {
                "schema_version": "legal-river-work-preflight-provenance-v1",
                "config_sha256": _v1.PREREGISTERED_CONFIG_SHA256,
                "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "source_dirty": False,
                "dependency_hashes": compat_dependencies,
                "reserved_actual_result_absent": True,
            }
        else:
            compat_event = dict(event)
        compatibility_payloads.append(
            {
                "schema_version": "legal-river-work-preflight-owner-observation-v1",
                "event_index": len(compatibility_payloads),
                "event_kind": kind,
                "config_sha256": _v1.PREREGISTERED_CONFIG_SHA256,
                "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "event": compat_event,
            }
        )

    header = {
        "schema_version": "legal-river-work-preflight-owner-header-v1",
        "owner_protocol_sha256": _v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
        "config_relative_path": _v1.CONFIG_RELATIVE_PATH,
        "correction_config_relative_path": _v1.CORRECTION_CONFIG_RELATIVE_PATH,
        "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
        "result_relative_path": _v1.RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": _v1.RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": _v1.PREREGISTRATION_COMMIT,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(_v1.CLAIMS),
    }
    lines: list[bytes] = []
    previous: str | None = None
    envelope = _compatibility_line(
        protocol_sha256=_v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
        campaign_sha256=_v1.WORK_PREFLIGHT_CAMPAIGN_SHA256,
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
            protocol_sha256=_v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
            campaign_sha256=_v1.WORK_PREFLIGHT_CAMPAIGN_SHA256,
            kind=JournalRecordKind.OBSERVATION,
            sequence=len(lines),
            previous_line_sha256=previous,
            payload=payload,
        )
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
        last_event_identity = envelope.body.semantic_identity_sha256
    compat_terminal = {
        "schema_version": "legal-river-work-preflight-owner-terminal-v1",
        "terminal": terminal.get("terminal"),
        "reason": str(terminal.get("reason", "v2 compatibility validation"))[:4096],
        "passed": terminal.get("passed"),
        "event_count": len(compatibility_payloads),
        "last_event_semantic_identity_sha256": last_event_identity,
        "claims": dict(_v1.CLAIMS),
    }
    envelope = _compatibility_line(
        protocol_sha256=_v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
        campaign_sha256=_v1.WORK_PREFLIGHT_CAMPAIGN_SHA256,
        kind=JournalRecordKind.TERMINAL,
        sequence=len(lines),
        previous_line_sha256=previous,
        payload=compat_terminal,
    )
    lines.append(envelope.line_bytes)
    return b"".join(lines)


def rebind_work_preflight_v2_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> WorkPreflightV2Rebinding:
    if not isinstance(raw, bytes):
        raise TypeError("work-preflight v2 journal must be immutable bytes")
    config = _load_config()
    _rebind_retained_v1()
    if _RESERVED.exists():
        raise ValueError("work-preflight v2 reader reserved actual result is present")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight v2 journal is incomplete: {recovery.failure.reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("work-preflight v2 journal omits header or terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("work-preflight v2 first record is not a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("work-preflight v2 last record is not a terminal")
    if any(record.body.kind is JournalRecordKind.TERMINAL for record in records[:-1]):
        raise ValueError("work-preflight v2 has a suffix after terminal")
    for record in records:
        if _semantic_digest(record.body.payload) != record.body.semantic_identity_sha256:
            raise ValueError("work-preflight v2 semantic identity differs")

    header = records[0].body.payload
    expected_header = {
        "schema_version": "legal-river-work-preflight-owner-header-v2",
        "owner_protocol_sha256": WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        "campaign_sha256": WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "retained_v1_result_relative_path": V1_RESULT_RELATIVE_PATH,
        "retained_v1_result_sha256": V1_RESULT_SHA256,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(CLAIMS),
    }
    if header != expected_header:
        raise ValueError("work-preflight v2 header contract differs")

    observations: list[Mapping[str, object]] = []
    provenance: Mapping[str, object] | None = None
    dependency_hashes: Mapping[str, object] | None = None
    handshake: Mapping[str, object] | None = None
    bound_source_commit: str | None = None
    for index, record in enumerate(records[1:-1]):
        if record.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("work-preflight v2 middle record is not an observation")
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
            raise ValueError("work-preflight v2 observation fields differ")
        if (
            observation.get("schema_version")
            != "legal-river-work-preflight-owner-observation-v2"
            or observation.get("event_index") != index
            or observation.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
            or observation.get("v1_config_sha256") != V1_CONFIG_SHA256
            or observation.get("correction_config_sha256")
            != CORRECTION_CONFIG_SHA256
        ):
            raise ValueError("work-preflight v2 observation contract differs")
        source_commit = observation.get("source_commit")
        if (
            not isinstance(source_commit, str)
            or len(source_commit) != 40
            or any(character not in "0123456789abcdef" for character in source_commit)
        ):
            raise ValueError("work-preflight v2 observation commit is malformed")
        if bound_source_commit is None:
            bound_source_commit = source_commit
        elif source_commit != bound_source_commit:
            raise ValueError("work-preflight v2 observation commit changes")
        kind = observation.get("event_kind")
        if not isinstance(kind, str):
            raise ValueError("work-preflight v2 observation kind differs")
        event = _mapping(observation.get("event"), label="work-preflight v2 event")
        if kind == "provenance":
            if index != 0 or provenance is not None:
                raise ValueError("work-preflight v2 provenance placement differs")
            provenance = event
            expected_provenance_keys = {
                "schema_version",
                "config_sha256",
                "v1_config_sha256",
                "correction_config_sha256",
                "source_commit",
                "source_dirty",
                "dependency_hashes",
                "retained_v1",
                "literal_worker_module",
                "reserved_actual_result_absent",
            }
            if set(event) != expected_provenance_keys:
                raise ValueError("work-preflight v2 provenance fields differ")
            if (
                event.get("schema_version")
                != "legal-river-work-preflight-provenance-v2"
                or event.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
                or event.get("v1_config_sha256") != V1_CONFIG_SHA256
                or event.get("correction_config_sha256")
                != CORRECTION_CONFIG_SHA256
                or event.get("source_commit") != source_commit
                or event.get("source_dirty") is not False
                or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
                or event.get("reserved_actual_result_absent") is not True
            ):
                raise ValueError("work-preflight v2 provenance contract differs")
            dependency_hashes = _mapping(
                event.get("dependency_hashes"), label="work-preflight v2 dependencies"
            )
            if set(dependency_hashes) != set(_DEPENDENCY_PATHS):
                raise ValueError("work-preflight v2 dependency set differs")
            if rebind_current_sources:
                for label, path in _DEPENDENCY_PATHS.items():
                    if dependency_hashes.get(label) != canonical_lf_sha256(path):
                        raise ValueError(f"work-preflight v2 dependency differs: {label}")
            retained = _mapping(event.get("retained_v1"), label="retained v1")
            if retained != {
                "sha256": V1_RESULT_SHA256,
                "byte_count": V1_RESULT_BYTES,
                "record_count": V1_RESULT_RECORDS,
                "terminal": "infrastructure_failure",
                "event_count": 1,
                "phase_count": 0,
                "passed": False,
                "projection": None,
            }:
                raise ValueError("work-preflight v2 retained-v1 provenance differs")
        elif kind == "bootstrap_handshake":
            if index != 1 or provenance is None or handshake is not None:
                raise ValueError("work-preflight v2 handshake placement differs")
            handshake = _validate_handshake(event)
        else:
            if handshake is None:
                raise ValueError("work-preflight v2 science precedes handshake")
        observations.append(observation)

    if observations and provenance is None:
        raise ValueError("work-preflight v2 observations omit provenance")

    terminal = records[-1].body.payload
    if set(terminal) != {
        "schema_version",
        "terminal",
        "reason",
        "passed",
        "event_count",
        "last_event_semantic_identity_sha256",
        "handshake_passed",
        "claims",
    }:
        raise ValueError("work-preflight v2 terminal fields differ")
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
        != "legal-river-work-preflight-owner-terminal-v2"
        or terminal_name not in allowed
        or not isinstance(terminal.get("reason"), str)
        or not terminal.get("reason")
        or terminal.get("passed") is not (terminal_name == "completed_capacity_pass")
        or terminal.get("event_count") != len(observations)
        or terminal.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight v2 terminal contract differs")
    last_identity = (
        None if not observations else records[-2].body.semantic_identity_sha256
    )
    if terminal.get("last_event_semantic_identity_sha256") != last_identity:
        raise ValueError("work-preflight v2 terminal last-event identity differs")
    if terminal.get("handshake_passed") is not (handshake is not None):
        raise ValueError("work-preflight v2 terminal handshake bit differs")
    if terminal_name != "infrastructure_failure" and handshake is None:
        raise ValueError("work-preflight v2 non-infrastructure terminal lacks handshake")

    scientific_view = _build_v1_scientific_validation_view(
        observations=tuple(observations),
        terminal=terminal,
        dependency_hashes=dependency_hashes,
    )
    scientific = _v1.rebind_work_preflight_journal(
        scientific_view,
        rebind_current_sources=False,
    )
    if scientific.terminal != terminal_name or scientific.passed is not terminal.get("passed"):
        raise ValueError("work-preflight v2 scientific terminal differs")
    return WorkPreflightV2Rebinding(
        terminal=str(terminal_name),
        passed=bool(terminal.get("passed")),
        event_count=len(observations),
        handshake=handshake,
        phases=scientific.phases,
        projection=scientific.projection,
        journal_byte_count=len(raw),
        scientific_rebinding=scientific,
    )


def rebind_work_preflight_v2_file(
    path: Path = _RESULT,
) -> WorkPreflightV2Rebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight v2 result is incomplete: {recovery.failure.reason}")
    return rebind_work_preflight_v2_journal(path.read_bytes())


__all__ = [
    "CONFIG_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "V1_RESULT_RELATIVE_PATH",
    "WORK_PREFLIGHT_V2_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V2_PROTOCOL_SHA256",
    "WorkPreflightV2Rebinding",
    "canonical_lf_sha256",
    "rebind_work_preflight_v2_file",
    "rebind_work_preflight_v2_journal",
]
