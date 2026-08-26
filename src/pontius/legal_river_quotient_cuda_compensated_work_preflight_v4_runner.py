"""Fresh one-shot owner for the composite ADR-0413/ADR-0414 V4 preflight."""

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
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4.json"
)
ENVELOPE_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2.json"
)
SCIENTIFIC_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
RESOURCE_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
V3_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl"
)
SUFFIX_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_ENVELOPE_CONFIG = _ROOT / ENVELOPE_CONFIG_RELATIVE_PATH
_V3_RESULT = _ROOT / V3_RESULT_RELATIVE_PATH
_SUFFIX_RESULT = _ROOT / SUFFIX_RESULT_RELATIVE_PATH
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH

PREREGISTERED_CONFIG_SHA256 = (
    "80aad86a806275c4b8979025237b555332e97a84ec1090845ee12616701b4b43"
)
ENVELOPE_CONFIG_SHA256 = (
    "f4fdb2e89809f4c22422aed883b6d9f1bbb2e1aea6c32dfcf536f7a27d111ab7"
)
SCIENTIFIC_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
RESOURCE_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
V3_RESULT_SHA256 = "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d"
V3_RESULT_BYTES = 15_783
V3_RESULT_RECORDS = 7
SUFFIX_RESULT_SHA256 = (
    "f4b3de941ed57e0f4acdfc7314315b6e70b10bd0034cf82113f17bf27e39a2de"
)
SUFFIX_RESULT_BYTES = 6_164_894
SUFFIX_RESULT_RECORDS = 15
PREREGISTRATION_COMMIT = "795e8a80599d0a16f3c723dac040dfe26700f834"

WORK_PREFLIGHT_V4_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0413-work-preflight-repaired-executed-cubin-exclusive-journal-v4"
).hexdigest()
WORK_PREFLIGHT_V4_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0413-work-preflight-repaired-executed-cubin-one-shot-campaign-v4"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
)
_CHILD_MODE_ENV = "PONTIUS_ADR0413_WORK_PREFLIGHT_CHILD_MODE"
_CHILD_CHALLENGE_ENV = "PONTIUS_ADR0413_WORK_PREFLIGHT_CHILD_CHALLENGE"
_CHILD_ACK_ENV = "PONTIUS_ADR0413_WORK_PREFLIGHT_CHILD_ACK"
_HANDSHAKE_MODE = "handshake"
_ADAPTER_PROBE_MODE = "adapter_probe"
_CAMPAIGN_MODE = "campaign"
_EVENT_PREFIX = b"PONTIUS_ADR0413_EVENT "

HANDSHAKE_WALL_LIMIT_NS = 10_000_000_000
ADAPTER_PROBE_WALL_LIMIT_NS = 10_000_000_000
LABORATORY_WALL_LIMIT_NS = 240_000_000_000
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_ARTIFACT_BYTES = 67_108_864
MAXIMUM_CHILD_LINE_CHARACTERS = 1_048_576
MAXIMUM_STDERR_CHARACTERS = 4096

CLAIMS = {
    "v4_source_sealed": False,
    "adapter_probe_result": None,
    "repaired_executed_cubin_result": None,
    "resource_gate_result": None,
    "calibration_result": None,
    "capacity_projection": None,
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
    correction: Mapping[str, object]
    correction_sha256: str


@dataclass(frozen=True, slots=True)
class RetainedArtifacts:
    v3: Mapping[str, object]
    suffix: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class BootstrapHandshake:
    event: Mapping[str, object]
    expected_challenge_sha256: str


@dataclass(frozen=True, slots=True)
class AdapterProbe:
    event: Mapping[str, object]
    expected_challenge_sha256: str


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v4 path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _load_json(path: Path, digest: str, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("work-preflight v4 config exceeds byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != digest:
        raise ValueError("work-preflight v4 config digest differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != schema:
        raise ValueError("work-preflight v4 config schema differs")
    return value


def _validate_parent_hashes(parent: Mapping[str, object]) -> None:
    for key, value in parent.items():
        if not key.endswith("_relative_path"):
            continue
        prefix = key[: -len("_relative_path")]
        digest_key = f"{prefix}_canonical_lf_sha256"
        if digest_key not in parent:
            continue
        if not isinstance(value, str) or canonical_lf_sha256(_ROOT / value) != parent[digest_key]:
            raise ValueError(f"work-preflight v4 bound parent differs: {prefix}")


def parse_config(
    base: Mapping[str, Any], correction: Mapping[str, Any]
) -> tuple[dict[str, object], dict[str, object]]:
    if base.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v4"
    ) or correction.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2"
    ):
        raise ValueError("work-preflight v4 composite schema differs")
    parent = _mapping(base.get("parent_identity"), label="v4 parent")
    retained = _mapping(base.get("retained_artifacts"), label="v4 retained")
    scope = _mapping(base.get("successor_scope"), label="v4 scope")
    identity = _mapping(base.get("new_identity_contract"), label="v4 identity")
    repair = _mapping(base.get("exact_repair_contract"), label="v4 repair")
    resource = _mapping(base.get("resource_semantics"), label="v4 resource")
    bounded = _mapping(base.get("bounded_evidence_contract"), label="v4 bounds")
    probe = _mapping(base.get("adapter_probe"), label="v4 probe")
    science = _mapping(base.get("inherited_science"), label="v4 science")
    transport = _mapping(base.get("child_transport"), label="v4 transport")
    lifecycle = _mapping(base.get("one_shot_lifecycle"), label="v4 lifecycle")
    claims = _mapping(base.get("claims"), label="v4 claims")
    overlay_parent = _mapping(
        correction.get("parent_identity"), label="v4 correction parent"
    )
    composite = _mapping(
        correction.get("composite_authority"), label="v4 composite authority"
    )
    journal = _mapping(
        correction.get("corrected_journal_contract"), label="v4 journal"
    )
    parser = _mapping(
        correction.get("parser_admission_contract"), label="v4 parser"
    )
    correction_claims = _mapping(
        correction.get("claims"), label="v4 correction claims"
    )
    _validate_parent_hashes(parent)
    _validate_parent_hashes(overlay_parent)
    if (
        identity.get("owner_protocol_sha256")
        != WORK_PREFLIGHT_V4_PROTOCOL_SHA256
        or identity.get("campaign_sha256")
        != WORK_PREFLIGHT_V4_CAMPAIGN_SHA256
        or transport.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or transport.get("handshake_mode") != _HANDSHAKE_MODE
        or transport.get("adapter_probe_mode") != _ADAPTER_PROBE_MODE
        or transport.get("campaign_mode") != _CAMPAIGN_MODE
        or transport.get("challenge_bytes") != 32
        or transport.get("handshake_wall_limit_ns")
        != HANDSHAKE_WALL_LIMIT_NS
        or transport.get("adapter_probe_wall_limit_ns")
        != ADAPTER_PROBE_WALL_LIMIT_NS
        or lifecycle.get("maximum_event_count") != MAXIMUM_EVENT_COUNT
        or journal.get("maximum_journal_bytes") != MAXIMUM_ARTIFACT_BYTES
        or bounded.get("maximum_child_line_characters")
        != MAXIMUM_CHILD_LINE_CHARACTERS
        or bounded.get("maximum_stderr_characters")
        != MAXIMUM_STDERR_CHARACTERS
    ):
        raise ValueError("work-preflight v4 lifecycle boundary differs")
    if (
        repair.get("original_payload_sha256")
        != "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
        or repair.get("repaired_payload_sha256")
        != "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
        or repair.get("suffix_hex") != "00"
        or resource.get("register_limit_per_thread") != 255
        or resource.get("stack_plus_local_backing_limit_bytes_per_thread")
        != 4096
        or resource.get("exact_spill_load_store_count") is not None
        or science.get("calibration_populations") != [10, 22]
        or science.get("projection_population_integer_only") != 25
        or science.get("phase_name_count") != 16
        or science.get("laboratory_total_wall_limit_ns")
        != LABORATORY_WALL_LIMIT_NS
        or science.get("target_projection_wall_limit_ns") != 180_000_000_000
    ):
        raise ValueError("work-preflight v4 scientific boundary differs")
    if (
        scope.get("v4_result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or probe.get("child_mode") != _ADAPTER_PROBE_MODE
        or composite.get(
            "all_exact_repair_resource_science_lifecycle_"
            "partial_outcome_kill_and_claim_fields_remain_binding"
        )
        is not True
        or parser.get("maximum_combined_version_output_bytes") != 32_768
        or parser.get("maximum_resource_stdout_bytes") != 262_144
        or dict(claims) != CLAIMS
        or dict(correction_claims) != CLAIMS
    ):
        raise ValueError("work-preflight v4 composite contract differs")
    v3 = _mapping(retained.get("v3_rejection"), label="v4 retained v3")
    suffix = _mapping(
        retained.get("suffix_qualification"), label="v4 retained suffix"
    )
    if (
        v3.get("sha256") != V3_RESULT_SHA256
        or v3.get("bytes") != V3_RESULT_BYTES
        or v3.get("record_count") != V3_RESULT_RECORDS
        or v3.get("terminal") != "compiler_or_primitive_rejection"
        or suffix.get("sha256") != SUFFIX_RESULT_SHA256
        or suffix.get("bytes") != SUFFIX_RESULT_BYTES
        or suffix.get("record_count") != SUFFIX_RESULT_RECORDS
        or suffix.get("terminal") != "suffix_reconstruction_pass"
    ):
        raise ValueError("work-preflight v4 retained identities differ")
    return dict(base), dict(correction)


def load_public_config() -> LoadedConfig:
    base = _load_json(
        _CONFIG,
        PREREGISTERED_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v4",
    )
    correction = _load_json(
        _ENVELOPE_CONFIG,
        ENVELOPE_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2",
    )
    parsed, parsed_correction = parse_config(base, correction)
    return LoadedConfig(
        payload=parsed,
        sha256=PREREGISTERED_CONFIG_SHA256,
        correction=parsed_correction,
        correction_sha256=ENVELOPE_CONFIG_SHA256,
    )


def rebind_retained_artifacts() -> RetainedArtifacts:
    v3_raw = _V3_RESULT.read_bytes()
    suffix_raw = _SUFFIX_RESULT.read_bytes()
    if (
        len(v3_raw) != V3_RESULT_BYTES
        or len(v3_raw.splitlines()) != V3_RESULT_RECORDS
        or sha256(v3_raw).hexdigest() != V3_RESULT_SHA256
        or len(suffix_raw) != SUFFIX_RESULT_BYTES
        or len(suffix_raw.splitlines()) != SUFFIX_RESULT_RECORDS
        or sha256(suffix_raw).hexdigest() != SUFFIX_RESULT_SHA256
    ):
        raise ValueError("work-preflight v4 retained artifact bytes differ")
    from .legal_river_exact_cubin_zero_suffix_diagnostic_result import (
        rebind_zero_suffix_diagnostic_journal,
    )
    from .legal_river_quotient_cuda_compensated_work_preflight_v3_result import (
        rebind_work_preflight_v3_journal,
    )

    v3 = rebind_work_preflight_v3_journal(v3_raw)
    suffix = rebind_zero_suffix_diagnostic_journal(suffix_raw)
    if (
        v3.terminal != "compiler_or_primitive_rejection"
        or v3.passed
        or len(v3.phases) != 0
        or v3.projection is not None
        or suffix.terminal != "suffix_reconstruction_pass"
        or not suffix.passed
        or suffix.resource_rows is None
        or suffix.qualified_resource_instrument
        != "cuobjdump_resource_usage_on_exact_zero_suffix_payload"
    ):
        raise ValueError("work-preflight v4 retained artifact semantics differ")
    return RetainedArtifacts(
        v3={
            "sha256": V3_RESULT_SHA256,
            "byte_count": V3_RESULT_BYTES,
            "record_count": V3_RESULT_RECORDS,
            "terminal": v3.terminal,
            "phase_count": len(v3.phases),
            "projection": v3.projection,
            "passed": v3.passed,
        },
        suffix={
            "sha256": SUFFIX_RESULT_SHA256,
            "byte_count": SUFFIX_RESULT_BYTES,
            "record_count": SUFFIX_RESULT_RECORDS,
            "terminal": suffix.terminal,
            "qualified_resource_instrument": suffix.qualified_resource_instrument,
            "passed": suffix.passed,
        },
    )


def _checked_git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    ).stdout


_TRACKED_REQUIRED = (
    CONFIG_RELATIVE_PATH,
    ENVELOPE_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0413-preregister-the-repaired-executed-cubin-work-preflight-v4.md",
    "docs/decisions/ADR-0414-correct-the-v4-bounded-evidence-envelope-before-source.md",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_adapter.py",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_runner.py",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_result.py",
    "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v4.py",
)


def strict_git_metadata() -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40:
        raise RuntimeError("work-preflight v4 Git commit differs")
    for relative in _TRACKED_REQUIRED:
        _checked_git("ls-files", "--error-unmatch", "--", relative)
    status = _checked_git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).decode("utf-8")
    expected = f"?? {RESULT_RELATIVE_PATH}\n"
    if status != expected:
        raise RuntimeError(
            "work-preflight v4 strict Git status differs after exclusive open"
        )
    return {"commit": commit, "dirty": False, "strict_status": True}


_DEPENDENCY_PATHS = {
    "base_config": _CONFIG,
    "envelope_config": _ENVELOPE_CONFIG,
    "preregistration_adr": _ROOT
    / "docs/decisions/ADR-0413-preregister-the-repaired-executed-cubin-work-preflight-v4.md",
    "correction_adr": _ROOT
    / "docs/decisions/ADR-0414-correct-the-v4-bounded-evidence-envelope-before-source.md",
    "scientific_config": _ROOT / SCIENTIFIC_CONFIG_RELATIVE_PATH,
    "resource_config": _ROOT / RESOURCE_CONFIG_RELATIVE_PATH,
    "scientific_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "suffix_source": _ROOT
    / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py",
    "suffix_reader": _ROOT
    / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py",
    "v3_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py",
    "v4_adapter": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_adapter.py",
    "v4_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_runner.py",
    "v4_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_result.py",
    "v4_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v4.py",
    "journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    "retained_v3": _V3_RESULT,
    "retained_suffix": _SUFFIX_RESULT,
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
}


def dependency_hashes() -> dict[str, str]:
    return {
        label: sha256(
            path.read_bytes()
            if label.startswith("retained_")
            else path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for label, path in _DEPENDENCY_PATHS.items()
    }


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-owner-header-v4",
        "owner_protocol_sha256": WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
        "campaign_sha256": WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "envelope_config_relative_path": ENVELOPE_CONFIG_RELATIVE_PATH,
        "envelope_config_sha256": ENVELOPE_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "retained_v3_result_relative_path": V3_RESULT_RELATIVE_PATH,
        "retained_v3_result_sha256": V3_RESULT_SHA256,
        "retained_suffix_result_relative_path": SUFFIX_RESULT_RELATIVE_PATH,
        "retained_suffix_result_sha256": SUFFIX_RESULT_SHA256,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(CLAIMS),
    }


def _event_observation(
    *,
    event_index: int,
    event_kind: str,
    event: Mapping[str, object],
    source_commit: str,
) -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-owner-observation-v4",
        "event_index": event_index,
        "event_kind": event_kind,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "envelope_config_sha256": ENVELOPE_CONFIG_SHA256,
        "scientific_config_sha256": SCIENTIFIC_CONFIG_SHA256,
        "resource_config_sha256": RESOURCE_CONFIG_SHA256,
        "source_commit": source_commit,
        "event": dict(event),
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    event_count: int,
    last_event_semantic_identity_sha256: str | None,
    handshake_passed: bool,
    adapter_probe_passed: bool,
) -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-owner-terminal-v4",
        "terminal": terminal,
        "reason": reason.encode("ascii", "backslashreplace").decode("ascii")[:4096],
        "passed": terminal == "completed_capacity_pass",
        "event_count": event_count,
        "last_event_semantic_identity_sha256": last_event_semantic_identity_sha256,
        "handshake_passed": handshake_passed,
        "adapter_probe_passed": adapter_probe_passed,
        "claims": dict(CLAIMS),
    }


_CHILD_EVENT_INDEX = 0


def _child_emit(kind: str, payload: Mapping[str, object]) -> None:
    global _CHILD_EVENT_INDEX
    ack = os.environ.get(_CHILD_ACK_ENV)
    if not isinstance(ack, str) or len(ack) != 64:
        raise RuntimeError("work-preflight v4 child ACK identity is absent")
    line = _EVENT_PREFIX + canonical_journal_json_bytes(
        {"kind": kind, "payload": dict(payload)}
    ) + b"\n"
    if len(line) > MAXIMUM_CHILD_LINE_CHARACTERS:
        raise RuntimeError("work-preflight v4 child line exceeds ceiling")
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.flush()
    expected = f"ACK {_CHILD_EVENT_INDEX} {ack}\n".encode("ascii")
    if sys.stdin.buffer.readline() != expected:
        raise RuntimeError("work-preflight v4 child durable ACK differs")
    _CHILD_EVENT_INDEX += 1


def _validate_challenge(challenge_hex: str) -> str:
    if len(challenge_hex) != 64 or any(
        character not in "0123456789abcdef" for character in challenge_hex
    ):
        raise ValueError("work-preflight v4 child challenge is malformed")
    return sha256(bytes.fromhex(challenge_hex)).hexdigest()


def _failure_reason(error: BaseException) -> str:
    return f"{type(error).__name__}: {(str(error) or 'exception carried no message')[:4096]}"


def _handshake_child_main(challenge_hex: str) -> int:
    challenge_digest = _validate_challenge(challenge_hex)
    scientific = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
    _child_emit(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-work-preflight-bootstrap-handshake-v4",
            "challenge_sha256": challenge_digest,
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "spec_name": None if __spec__ is None else __spec__.name,
            "runtime_name": __name__,
            "package_name": __package__,
            "python_no_bytecode": sys.dont_write_bytecode,
            "argv_count": len(sys.argv),
            "cupy_loaded": any(
                name == "cupy" or name.startswith("cupy.") for name in sys.modules
            ),
            "scientific_source_loaded": scientific in sys.modules,
        },
    )
    _child_emit(
        "child_terminal",
        {
            "schema_version": "legal-river-work-preflight-bootstrap-terminal-v4",
            "terminal": "bootstrap_handshake_pass",
            "passed": True,
        },
    )
    return 0


def _adapter_probe_child_main(challenge_hex: str) -> int:
    challenge_digest = _validate_challenge(challenge_hex)
    scientific = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
    before_cupy = any(
        name == "cupy" or name.startswith("cupy.") for name in sys.modules
    )
    before_source = scientific in sys.modules
    try:
        from .legal_river_quotient_cuda_compensated_work_preflight_v4_adapter import (
            run_device_free_adapter_probe,
        )

        probe = run_device_free_adapter_probe()
        _child_emit(
            "adapter_probe",
            {
                "schema_version": "legal-river-work-preflight-adapter-probe-child-v4",
                "challenge_sha256": challenge_digest,
                "literal_worker_module": LITERAL_WORKER_MODULE,
                "spec_name": None if __spec__ is None else __spec__.name,
                "runtime_name": __name__,
                "package_name": __package__,
                "python_no_bytecode": sys.dont_write_bytecode,
                "argv_count": len(sys.argv),
                "cupy_loaded_before": before_cupy,
                "cupy_loaded_after": any(
                    name == "cupy" or name.startswith("cupy.")
                    for name in sys.modules
                ),
                "scientific_source_loaded_before": before_source,
                "scientific_source_loaded_after": scientific in sys.modules,
                "probe": probe,
            },
        )
        _child_emit(
            "child_terminal",
            {
                "schema_version": "legal-river-work-preflight-adapter-probe-terminal-v4",
                "terminal": "adapter_probe_pass",
                "passed": True,
            },
        )
        return 0
    except BaseException as error:  # noqa: BLE001
        _child_emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v4",
                "reason": _failure_reason(error),
            },
        )
        return 1


def _campaign_child_main() -> int:
    try:
        from .legal_river_quotient_cuda_compensated_work_preflight_v4_adapter import (
            run_repaired_calibration_preflight,
        )

        terminal = run_repaired_calibration_preflight(_child_emit)
        _child_emit("child_terminal", terminal)
        return 0
    except BaseException as error:  # noqa: BLE001
        _child_emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v4",
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
    if mode not in {_HANDSHAKE_MODE, _ADAPTER_PROBE_MODE, _CAMPAIGN_MODE}:
        raise ValueError("work-preflight v4 child mode differs")
    if isinstance(wall_limit_ns, bool) or not isinstance(wall_limit_ns, int) or wall_limit_ns <= 0:
        raise ValueError("work-preflight v4 child wall must be positive")
    if mode in {_HANDSHAKE_MODE, _ADAPTER_PROBE_MODE} and not isinstance(
        challenge_hex, str
    ):
        raise ValueError("work-preflight v4 child challenge is absent")
    if mode == _CAMPAIGN_MODE and challenge_hex is not None:
        raise ValueError("work-preflight v4 campaign challenge is present")
    ack = secrets.token_hex(32)
    environment = os.environ.copy()
    environment[_CHILD_MODE_ENV] = mode
    environment[_CHILD_ACK_ENV] = ack
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if challenge_hex is None:
        environment.pop(_CHILD_CHALLENGE_ENV, None)
    else:
        environment[_CHILD_CHALLENGE_ENV] = challenge_hex
    prefix = os.pathsep.join((str(_ROOT / "src"), str(_ROOT)))
    current = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = prefix + (os.pathsep + current if current else "")
    creationflags = (
        int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0
    )
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
        cwd=_ROOT,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeError("work-preflight v4 child pipes are absent")
    stdout_queue: Queue[bytes | None | BaseException] = Queue(maxsize=64)
    stderr_queue: Queue[bytes] = Queue(maxsize=2)
    stop_reader = Event()

    def read_stdout() -> None:
        try:
            while not stop_reader.is_set():
                line = process.stdout.readline()
                if not line:
                    break
                while not stop_reader.is_set():
                    try:
                        stdout_queue.put(line, timeout=0.1)
                        break
                    except Full:
                        continue
        except BaseException as error:  # noqa: BLE001
            stdout_queue.put(error)
        finally:
            process.stdout.close()
            stdout_queue.put(None)

    def read_stderr() -> None:
        collected = bytearray()
        overflow = False
        try:
            while True:
                chunk = process.stderr.read(4096)
                if not chunk:
                    break
                room = max(0, MAXIMUM_STDERR_CHARACTERS - len(collected))
                collected.extend(chunk[:room])
                overflow = overflow or len(chunk) > room
        finally:
            process.stderr.close()
            stderr_queue.put(b"__OVERFLOW__" if overflow else bytes(collected))

    stdout_thread = Thread(target=read_stdout, daemon=True)
    stderr_thread = Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    started = perf_counter_ns()
    child_terminal: Mapping[str, object] | None = None
    child_failure: str | None = None
    stdout_closed = False
    event_index = 0
    try:
        while True:
            remaining_ns = wall_limit_ns - (perf_counter_ns() - started)
            if remaining_ns <= 0:
                raise TimeoutError("child_wall_crossed")
            if stdout_closed and process.poll() is not None:
                break
            try:
                item = stdout_queue.get(
                    timeout=min(0.5, remaining_ns / 1_000_000_000)
                )
            except Empty:
                continue
            if item is None:
                stdout_closed = True
                continue
            if isinstance(item, BaseException):
                raise RuntimeError("work-preflight v4 child stdout reader failed") from item
            if len(item) > MAXIMUM_CHILD_LINE_CHARACTERS:
                raise RuntimeError("work-preflight v4 child line exceeds ceiling")
            if not item.startswith(_EVENT_PREFIX) or not item.endswith(b"\n"):
                raise RuntimeError("work-preflight v4 child emitted an unframed line")
            value = json.loads(item[len(_EVENT_PREFIX) :])
            if not isinstance(value, dict) or set(value) != {"kind", "payload"}:
                raise RuntimeError("work-preflight v4 child event is malformed")
            kind, payload = value["kind"], value["payload"]
            if not isinstance(kind, str) or not isinstance(payload, dict):
                raise RuntimeError("work-preflight v4 child event types differ")
            if child_terminal is not None or child_failure is not None:
                raise RuntimeError("work-preflight v4 child emitted after terminal")
            if kind == "child_terminal":
                child_terminal = payload
            elif kind == "worker_failure":
                child_failure = str(payload.get("reason", "worker failed"))
            else:
                if event_index >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v4 child event count exceeds ceiling")
                emit(kind, payload)
            process.stdin.write(f"ACK {event_index} {ack}\n".encode("ascii"))
            process.stdin.flush()
            event_index += 1
        process.stdin.close()
        remaining = max(
            0.001, (wall_limit_ns - (perf_counter_ns() - started)) / 1_000_000_000
        )
        return_code = process.wait(timeout=remaining)
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5.0)
        if not process.stdin.closed:
            process.stdin.close()
        raise
    finally:
        stop_reader.set()
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        raise RuntimeError("work-preflight v4 child drain did not terminate")
    stderr = stderr_queue.get_nowait() if not stderr_queue.empty() else b""
    if stderr == b"__OVERFLOW__":
        raise RuntimeError("work-preflight v4 child stderr exceeds ceiling")
    if child_failure is not None:
        raise RuntimeError(child_failure)
    if return_code != 0:
        raise RuntimeError(
            f"work-preflight v4 child exited {return_code}: "
            + stderr.decode("utf-8", "replace")
        )
    if child_terminal is None:
        raise RuntimeError("work-preflight v4 child omitted terminal evidence")
    return child_terminal


def _validated_handshake_event(
    event: Mapping[str, object], *, expected_challenge_sha256: str
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
    if (
        set(event) != expected_keys
        or event.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v4"
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
        raise ValueError("work-preflight v4 handshake semantics differ")
    return dict(event)


def _validated_adapter_probe_event(
    event: Mapping[str, object], *, expected_challenge_sha256: str
) -> dict[str, object]:
    if (
        event.get("schema_version")
        != "legal-river-work-preflight-adapter-probe-child-v4"
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
        raise ValueError("work-preflight v4 adapter-probe child differs")
    probe = _mapping(event.get("probe"), label="v4 adapter probe")
    if (
        probe.get("schema_version")
        != "legal-river-work-preflight-adapter-probe-v4"
        or probe.get("passed") is not True
        or probe.get("cupy_loaded") is not False
        or probe.get("original_payload_sha256")
        != "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
        or probe.get("repaired_payload_sha256")
        != "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
        or probe.get("scientific_call_counter_unchanged") is not True
        or probe.get("identities_and_caches_restored") is not True
        or not all(_mapping(probe.get("resource_gates"), label="probe gates").values())
    ):
        raise ValueError("work-preflight v4 adapter-probe semantics differ")
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
        raise ValueError("work-preflight v4 challenge factory differs")
    digest = sha256(challenge).hexdigest()
    events: list[tuple[str, Mapping[str, object]]] = []
    terminal = process_executor(
        mode,
        challenge.hex(),
        lambda kind, payload: events.append((kind, dict(payload))),
        wall_limit_ns,
    )
    if len(events) != 1 or events[0][0] != expected_kind:
        raise ValueError(f"work-preflight v4 {mode} event sequence differs")
    if (
        terminal.get("schema_version") != terminal_schema
        or terminal.get("terminal") != terminal_name
        or terminal.get("passed") is not True
        or set(terminal) != {"schema_version", "terminal", "passed"}
    ):
        raise ValueError(f"work-preflight v4 {mode} terminal differs")
    return validator(events[0][1], expected_challenge_sha256=digest), digest


def run_no_cuda_bootstrap_handshake(
    *,
    challenge_factory: Callable[[int], bytes] = secrets.token_bytes,
    process_executor: ChildProcessExecutor = _run_child_process,
) -> BootstrapHandshake:
    event, digest = _run_challenge_stage(
        mode=_HANDSHAKE_MODE,
        expected_kind="bootstrap_handshake",
        terminal_schema="legal-river-work-preflight-bootstrap-terminal-v4",
        terminal_name="bootstrap_handshake_pass",
        wall_limit_ns=HANDSHAKE_WALL_LIMIT_NS,
        validator=_validated_handshake_event,
        challenge_factory=challenge_factory,
        process_executor=process_executor,
    )
    return BootstrapHandshake(event=event, expected_challenge_sha256=digest)


def run_no_cuda_adapter_probe(
    *,
    challenge_factory: Callable[[int], bytes] = secrets.token_bytes,
    process_executor: ChildProcessExecutor = _run_child_process,
) -> AdapterProbe:
    event, digest = _run_challenge_stage(
        mode=_ADAPTER_PROBE_MODE,
        expected_kind="adapter_probe",
        terminal_schema="legal-river-work-preflight-adapter-probe-terminal-v4",
        terminal_name="adapter_probe_pass",
        wall_limit_ns=ADAPTER_PROBE_WALL_LIMIT_NS,
        validator=_validated_adapter_probe_event,
        challenge_factory=challenge_factory,
        process_executor=process_executor,
    )
    return AdapterProbe(event=event, expected_challenge_sha256=digest)


CampaignExecutor = Callable[
    [Callable[[str, Mapping[str, object]], None], int], Mapping[str, object]
]


def _subprocess_campaign_executor(
    emit: Callable[[str, Mapping[str, object]], None], wall_limit_ns: int
) -> Mapping[str, object]:
    return _run_child_process(_CAMPAIGN_MODE, None, emit, wall_limit_ns)


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    hashes_loader: Callable[[], Mapping[str, str]] = dependency_hashes,
    retained_loader: Callable[[], RetainedArtifacts] = rebind_retained_artifacts,
    handshake_executor: Callable[[], BootstrapHandshake] = run_no_cuda_bootstrap_handshake,
    adapter_probe_executor: Callable[[], AdapterProbe] = run_no_cuda_adapter_probe,
    campaign_executor: CampaignExecutor = _subprocess_campaign_executor,
    reserved_path: Path = _RESERVED,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> OwnerExecution:
    if not isinstance(output_path, Path) or not isinstance(reserved_path, Path):
        raise TypeError("work-preflight v4 owner paths must be Paths")
    event_count = 0
    last_identity: str | None = None
    last_line_sha256: str | None = None
    handshake_passed = False
    adapter_probe_passed = False
    terminal_payload: dict[str, object]
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
        campaign_sha256=WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
    ) as writer:
        header = _header_payload()
        receipt = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=_semantic_digest(header),
            payload=header,
        )
        last_line_sha256 = receipt.line_sha256
        try:
            loaded = config_loader()
            if not isinstance(loaded, LoadedConfig):
                raise TypeError("work-preflight v4 config loader returned wrong type")
            parse_config(loaded.payload, loaded.correction)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("work-preflight v4 strict Git boundary rejected")
            retained = retained_loader()
            if not isinstance(retained, RetainedArtifacts):
                raise TypeError("work-preflight v4 retained loader returned wrong type")

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, last_identity, last_line_sha256
                if event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v4 event count exceeds ceiling")
                observation = _event_observation(
                    event_index=event_count,
                    event_kind=kind,
                    event=event,
                    source_commit=str(git["commit"]),
                )
                identity = _semantic_digest(observation)
                assert last_line_sha256 is not None
                body = build_journal_record_body(
                    protocol_sha256=WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
                    campaign_sha256=WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
                    kind=JournalRecordKind.OBSERVATION,
                    sequence=writer.next_sequence,
                    previous_record_sha256=last_line_sha256,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                prospective = JournalRecordEnvelope(body=body)
                reserve_payload = _terminal_payload(
                    terminal="infrastructure_failure",
                    reason="x" * 4096,
                    event_count=MAXIMUM_EVENT_COUNT,
                    last_event_semantic_identity_sha256="f" * 64,
                    handshake_passed=True,
                    adapter_probe_passed=True,
                )
                reserve_body = build_journal_record_body(
                    protocol_sha256=WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
                    campaign_sha256=WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
                    kind=JournalRecordKind.TERMINAL,
                    sequence=writer.next_sequence + 1,
                    previous_record_sha256=prospective.line_sha256,
                    semantic_identity_sha256=_semantic_digest(reserve_payload),
                    payload=reserve_payload,
                )
                reserve = JournalRecordEnvelope(body=reserve_body)
                if (
                    output_path.stat().st_size
                    + len(prospective.line_bytes)
                    + len(reserve.line_bytes)
                    > MAXIMUM_ARTIFACT_BYTES
                ):
                    raise RuntimeError(
                        "work-preflight v4 observation would exceed journal cap"
                    )
                appended = writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                if appended.line_sha256 != prospective.line_sha256:
                    raise RuntimeError(
                        "work-preflight v4 prospective line identity differs"
                    )
                event_count += 1
                last_identity = identity
                last_line_sha256 = appended.line_sha256

            append_event(
                "provenance",
                {
                    "schema_version": "legal-river-work-preflight-provenance-v4",
                    "config_sha256": loaded.sha256,
                    "envelope_config_sha256": loaded.correction_sha256,
                    "scientific_config_sha256": SCIENTIFIC_CONFIG_SHA256,
                    "resource_config_sha256": RESOURCE_CONFIG_SHA256,
                    "source_commit": git["commit"],
                    "source_dirty": False,
                    "dependency_hashes": dict(hashes_loader()),
                    "retained_v3": dict(retained.v3),
                    "retained_suffix": dict(retained.suffix),
                    "literal_worker_module": LITERAL_WORKER_MODULE,
                    "adapter_boundary": (
                        "exact_serializer_repair_before_load_same_inspected_bytes"
                    ),
                    "reserved_actual_result_absent": not reserved_path.exists(),
                },
            )
            if reserved_path.exists():
                raise RuntimeError("reserved actual authority is present")
            started = monotonic_ns()
            handshake = handshake_executor()
            accepted_handshake = _validated_handshake_event(
                handshake.event,
                expected_challenge_sha256=handshake.expected_challenge_sha256,
            )
            append_event(
                "bootstrap_handshake",
                {
                    "schema_version": (
                        "legal-river-work-preflight-bootstrap-accepted-v4"
                    ),
                    "parent_challenge_sha256": handshake.expected_challenge_sha256,
                    "child": accepted_handshake,
                },
            )
            handshake_passed = True
            probe = adapter_probe_executor()
            accepted_probe = _validated_adapter_probe_event(
                probe.event,
                expected_challenge_sha256=probe.expected_challenge_sha256,
            )
            append_event(
                "adapter_probe",
                {
                    "schema_version": (
                        "legal-river-work-preflight-adapter-probe-accepted-v4"
                    ),
                    "parent_challenge_sha256": probe.expected_challenge_sha256,
                    "child": accepted_probe,
                },
            )
            adapter_probe_passed = True
            remaining = LABORATORY_WALL_LIMIT_NS - (monotonic_ns() - started)
            if remaining <= 0:
                raise TimeoutError("laboratory_wall_crossed_after_adapter_probe")

            def append_science(kind: str, event: Mapping[str, object]) -> None:
                if kind in {"provenance", "bootstrap_handshake", "adapter_probe"}:
                    raise RuntimeError(
                        "work-preflight v4 science emitted reserved lifecycle event"
                    )
                append_event(kind, event)

            terminal_evidence = campaign_executor(append_science, remaining)
            if monotonic_ns() - started > LABORATORY_WALL_LIMIT_NS:
                raise TimeoutError("laboratory_wall_crossed")
            terminal = terminal_evidence.get("terminal")
            passed = terminal_evidence.get("passed")
            if not isinstance(terminal, str) or not isinstance(passed, bool):
                raise ValueError("work-preflight v4 terminal evidence differs")
            if passed is not (terminal == "completed_capacity_pass"):
                raise ValueError("work-preflight v4 terminal pass bit disagrees")
            append_event("terminal_evidence", terminal_evidence)
            terminal_payload = _terminal_payload(
                terminal=terminal,
                reason="retained first V4 terminal evidence",
                event_count=event_count,
                last_event_semantic_identity_sha256=last_identity,
                handshake_passed=handshake_passed,
                adapter_probe_passed=adapter_probe_passed,
            )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_identity,
                handshake_passed=handshake_passed,
                adapter_probe_passed=adapter_probe_passed,
            )
        except BaseException as error:  # noqa: BLE001
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_identity,
                handshake_passed=handshake_passed,
                adapter_probe_passed=adapter_probe_passed,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("work-preflight v4 journal exceeds byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> None:
    if len(sys.argv) != 1:
        raise ValueError("work-preflight v4 owner accepts no arguments")
    child_mode = os.environ.get(_CHILD_MODE_ENV)
    if child_mode is not None:
        if child_mode in {_HANDSHAKE_MODE, _ADAPTER_PROBE_MODE}:
            challenge = os.environ.get(_CHILD_CHALLENGE_ENV)
            if not isinstance(challenge, str):
                raise ValueError("work-preflight v4 child challenge is absent")
            if child_mode == _HANDSHAKE_MODE:
                raise SystemExit(_handshake_child_main(challenge))
            raise SystemExit(_adapter_probe_child_main(challenge))
        if child_mode == _CAMPAIGN_MODE:
            if _CHILD_CHALLENGE_ENV in os.environ:
                raise ValueError("work-preflight v4 campaign challenge is present")
            raise SystemExit(_campaign_child_main())
        raise ValueError("work-preflight v4 child mode is unknown")
    if _OUTPUT.exists():
        raise FileExistsError("work-preflight v4 authority is already consumed")
    if not _V3_RESULT.is_file() or not _SUFFIX_RESULT.is_file():
        raise FileNotFoundError("retained V4 parent authority is absent")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual authority must remain absent")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "legal-river work preflight v4: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "completed_capacity_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "ADAPTER_PROBE_WALL_LIMIT_NS",
    "AdapterProbe",
    "BootstrapHandshake",
    "CONFIG_RELATIVE_PATH",
    "ENVELOPE_CONFIG_RELATIVE_PATH",
    "ENVELOPE_CONFIG_SHA256",
    "LITERAL_WORKER_MODULE",
    "LoadedConfig",
    "MAXIMUM_ARTIFACT_BYTES",
    "OwnerExecution",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "RetainedArtifacts",
    "WORK_PREFLIGHT_V4_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V4_PROTOCOL_SHA256",
    "canonical_lf_sha256",
    "dependency_hashes",
    "execute_owner_to_path",
    "load_public_config",
    "parse_config",
    "rebind_retained_artifacts",
    "run_no_cuda_adapter_probe",
    "run_no_cuda_bootstrap_handshake",
]
