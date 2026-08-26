"""Standard-library rebinder for the ADR-0404 exact-cubin diagnostic."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .durable_evidence_journal import recover_journal_bytes, recover_journal_file


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-exact-cubin-inspector-diagnostic-v1.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
CONFIG_SHA256 = "d52ac02e83f71cb50b6a61e8a9dd18403171e4ddd25227b2036bb61c2085fe8a"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0404-exact-cubin-inspector-diagnostic-exclusive-journal-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0404-exact-cubin-inspector-diagnostic-one-shot-campaign-v1"
).hexdigest()
LITERAL_WORKER_MODULE = "pontius.legal_river_exact_cubin_inspector_diagnostic_runner"
MAXIMUM_ARTIFACT_BYTES = 50_331_648
MAXIMUM_BINARY_BYTES = 8_388_608
ELF_MAGIC = b"\x7fELF"
CALLER_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)
DIRECT_KERNEL_NAMES = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)
ALL_KERNEL_NAMES = (
    "primitive_pairs",
    "source_coefficients_tile",
    "zeta_level_tile",
    "signed_targets_tile",
    "fold_query_tile",
    "build_numerator_covector_tile",
    "aggregate_query_labels_tile",
    "source_adjoint_contract_tile",
    "reduce_contiguous_pairs",
    "reduce_strided_pairs",
    "finalize_pair_result",
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
    "selected_query_weights",
)
RUNTIME_FIELDS = frozenset(
    {
        "device_name",
        "compute_capability",
        "device_total_bytes",
        "cuda_driver_version",
        "cuda_runtime_version",
        "cupy_version",
    }
)
_OUTER_TERMINALS = frozenset(
    {
        "capture_complete",
        "candidate_timeout_rejection",
        "candidate_output_limit_rejection",
        "laboratory_wall_rejection",
        "diagnostic_failure",
        "infrastructure_failure",
    }
)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"exact-cubin reader dependency is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _load_config() -> dict[str, object]:
    raw = _CONFIG.read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("exact-cubin reader config differs from ADR-0404")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("exact-cubin reader config must be an object")
    candidates = value.get("candidate_commands_in_order")
    if not isinstance(candidates, list) or len(candidates) != 5:
        raise ValueError("exact-cubin reader candidate inventory differs")
    return value


@dataclass(frozen=True, slots=True)
class BinaryEvidence:
    raw: bytes
    sha256: str
    byte_count: int


def decode_binary(value: object, *, label: str) -> BinaryEvidence:
    row = _mapping(value, label=label)
    if set(row) != {"encoding", "byte_count", "sha256", "base64"}:
        raise ValueError(f"{label} fields differ")
    if row["encoding"] != "base64_standard":
        raise ValueError(f"{label} encoding differs")
    byte_count = row["byte_count"]
    encoded = row["base64"]
    digest = _digest(row["sha256"], label=f"{label} digest")
    if (
        isinstance(byte_count, bool)
        or not isinstance(byte_count, int)
        or byte_count < 0
        or byte_count > MAXIMUM_BINARY_BYTES
        or not isinstance(encoded, str)
        or not encoded.isascii()
    ):
        raise ValueError(f"{label} bounds differ")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{label} base64 differs") from error
    if (
        len(raw) != byte_count
        or sha256(raw).hexdigest() != digest
        or base64.b64encode(raw).decode("ascii") != encoded
    ):
        raise ValueError(f"{label} bytes differ from envelope")
    return BinaryEvidence(raw=raw, sha256=digest, byte_count=byte_count)


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    candidate_id: str
    return_code: int | None
    status: str
    stdout: BinaryEvidence
    stderr: BinaryEvidence
    elapsed_ns: int


@dataclass(frozen=True, slots=True)
class ExactCubinDiagnosticRebinding:
    terminal: str
    passed: bool
    event_count: int
    source_commit: str | None
    cubin: BinaryEvidence | None
    driver_rows: Mapping[str, Mapping[str, int]] | None
    candidates: tuple[CandidateEvidence, ...]
    cleanup: Mapping[str, object] | None
    journal_byte_count: int


def _validate_current_dependencies(event: Mapping[str, object]) -> None:
    dependencies = _mapping(event.get("dependency_hashes"), label="dependency hashes")
    expected_paths = {
        "config": _CONFIG,
        "adr0403": _ROOT
        / "docs/decisions/ADR-0403-retain-the-work-preflight-v3-resource-inspector-rejection.md",
        "adr0404": _ROOT
        / "docs/decisions/ADR-0404-preregister-the-exact-cubin-inspector-diagnostic.md",
        "scientific_source": _ROOT
        / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
        "diagnostic": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic.py",
        "owner": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_runner.py",
        "reader": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py",
        "controls": _ROOT
        / "tests/test_legal_river_exact_cubin_inspector_diagnostic.py",
        "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    }
    if set(dependencies) != set(expected_paths):
        raise ValueError("exact-cubin dependency inventory differs")
    for name, path in expected_paths.items():
        if dependencies[name] != canonical_lf_sha256(path):
            raise ValueError(f"exact-cubin dependency differs: {name}")


def _validate_retained_artifacts(value: object) -> None:
    rows = _mapping(value, label="retained artifacts")
    expected = {
        "v1": (
            "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl",
            "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830",
            5322,
            3,
        ),
        "v2": (
            "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl",
            "9b9a3f606004a281773f6dc83c86fe2f70811ab825fbf1e0b8b47c1c75abdad3",
            8508,
            4,
        ),
        "v3": (
            "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl",
            "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d",
            15783,
            7,
        ),
    }
    if set(rows) != set(expected):
        raise ValueError("exact-cubin retained artifact inventory differs")
    for name, (relative, digest, byte_count, record_count) in expected.items():
        row = _mapping(rows[name], label=f"retained {name}")
        if row != {
            "relative_path": relative,
            "sha256": digest,
            "byte_count": byte_count,
            "record_count": record_count,
        }:
            raise ValueError(f"exact-cubin retained {name} facts differ")
        raw = (_ROOT / relative).read_bytes()
        if (
            sha256(raw).hexdigest() != digest
            or len(raw) != byte_count
            or len(raw.splitlines()) != record_count
        ):
            raise ValueError(f"exact-cubin retained {name} bytes differ")


def _validate_header(payload: Mapping[str, object]) -> None:
    expected = {
        "schema_version": "legal-river-exact-cubin-diagnostic-owner-header-v1",
        "protocol_sha256": PROTOCOL_SHA256,
        "campaign_sha256": CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "selected_inspector": None,
        "calibration_result": None,
        "capacity_projection": None,
    }
    if dict(payload) != expected:
        raise ValueError("exact-cubin header differs")


def _validate_handshake(event: Mapping[str, object]) -> None:
    challenge = event.get("challenge")
    if (
        event.get("schema_version")
        != "legal-river-exact-cubin-diagnostic-handshake-v1"
        or not isinstance(challenge, str)
        or len(challenge) != 64
        or any(character not in "0123456789abcdef" for character in challenge)
        or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("python_no_bytecode") is not True
        or event.get("cupy_loaded") is not False
        or event.get("scientific_source_loaded") is not False
    ):
        raise ValueError("exact-cubin bootstrap handshake differs")


def _validate_driver_rows(value: object) -> dict[str, dict[str, int]]:
    rows = _mapping(value, label="direct driver rows")
    fields = {
        "local_size_bytes",
        "registers",
        "shared_size_bytes",
        "maximum_threads_per_block",
    }
    if set(rows) != set(DIRECT_KERNEL_NAMES):
        raise ValueError("exact-cubin direct driver kernel inventory differs")
    result: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        row = _mapping(rows[name], label=f"driver row {name}")
        if set(row) != fields or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in row.values()
        ):
            raise ValueError(f"exact-cubin driver row differs: {name}")
        result[name] = {key: int(item) for key, item in row.items()}
    return result


def _validate_compiler_capture(
    event: Mapping[str, object],
) -> tuple[BinaryEvidence, dict[str, dict[str, int]]]:
    runtime = _mapping(event.get("runtime"), label="runtime")
    if (
        event.get("schema_version")
        != "legal-river-exact-cubin-compiler-capture-v1"
        or set(runtime) != RUNTIME_FIELDS
        or any(
            not isinstance(runtime[field], str) or not runtime[field]
            for field in ("device_name", "compute_capability", "cupy_version")
        )
        or any(
            isinstance(runtime[field], bool)
            or not isinstance(runtime[field], int)
            or runtime[field] < 0
            for field in (
                "device_total_bytes",
                "cuda_driver_version",
                "cuda_runtime_version",
            )
        )
        or tuple(event.get("caller_options", ())) != CALLER_OPTIONS
        or not isinstance(event.get("effective_internal_arch_option"), str)
        or not str(event["effective_internal_arch_option"]).startswith("-arch=sm_")
        or event.get("output_method") != "cubin"
        or tuple(event.get("kernel_names", ())) != ALL_KERNEL_NAMES
    ):
        raise ValueError("exact-cubin compiler capture differs")
    cubin = decode_binary(event.get("cubin"), label="cubin")
    if not cubin.raw.startswith(ELF_MAGIC):
        raise ValueError("exact-cubin capture is not ELF")
    return cubin, _validate_driver_rows(event.get("direct_driver_rows"))


def _expected_candidate_rows(config: Mapping[str, object]) -> list[Mapping[str, object]]:
    values = config["candidate_commands_in_order"]
    assert isinstance(values, list)
    return [_mapping(value, label="candidate config row") for value in values]


def _validate_candidate(
    event: Mapping[str, object],
    expected: Mapping[str, object],
    *,
    expected_index: int,
    prior_cubin_path: str | None,
) -> tuple[CandidateEvidence, str | None]:
    if (
        event.get("schema_version")
        != "legal-river-exact-cubin-candidate-command-v1"
        or event.get("candidate_index") != expected_index
        or event.get("candidate_id") != expected.get("candidate_id")
        or event.get("semantic_role") != expected.get("semantic_role")
        or event.get("uses_cubin") is not expected.get("uses_cubin")
    ):
        raise ValueError("exact-cubin candidate identity differs")
    argv = event.get("argv")
    if not isinstance(argv, list) or any(not isinstance(item, str) or not item for item in argv):
        raise ValueError("exact-cubin candidate argv differs")
    expected_tool = expected.get("tool")
    expected_tool_path = {
        "CUDA_13_3_cuobjdump": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe",
        "CUDA_13_3_nvdisasm": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe",
    }.get(expected_tool)
    if expected_tool_path is None or argv[0] != expected_tool_path:
        raise ValueError("exact-cubin candidate tool path differs")
    configured_arguments = expected.get("arguments")
    if not isinstance(configured_arguments, list):
        raise ValueError("exact-cubin configured candidate arguments differ")
    uses_cubin = expected.get("uses_cubin") is True
    if len(argv) != 1 + len(configured_arguments):
        raise ValueError("exact-cubin candidate argv length differs")
    cubin_path = prior_cubin_path
    for observed, configured in zip(argv[1:], configured_arguments, strict=True):
        if configured == "{exact_temporary_cubin}":
            if not observed.lower().endswith(".cubin"):
                raise ValueError("exact-cubin temporary path suffix differs")
            if cubin_path is None:
                cubin_path = observed
            elif cubin_path != observed:
                raise ValueError("exact-cubin candidate paths differ")
        elif observed != configured:
            raise ValueError("exact-cubin candidate argument differs")
    if uses_cubin is not ("{exact_temporary_cubin}" in configured_arguments):
        raise ValueError("exact-cubin candidate path role differs")
    status = event.get("status")
    return_code = event.get("return_code")
    elapsed_ns = event.get("elapsed_ns")
    if (
        status not in {"completed", "timeout", "output_limit"}
        or (
            return_code is not None
            and (isinstance(return_code, bool) or not isinstance(return_code, int))
        )
        or isinstance(elapsed_ns, bool)
        or not isinstance(elapsed_ns, int)
        or elapsed_ns < 0
        or (status == "completed" and elapsed_ns > 30_000_000_000)
    ):
        raise ValueError("exact-cubin candidate outcome differs")
    stdout = decode_binary(event.get("stdout"), label="candidate stdout")
    stderr = decode_binary(event.get("stderr"), label="candidate stderr")
    return (
        CandidateEvidence(
            candidate_id=str(event["candidate_id"]),
            return_code=return_code,
            status=str(status),
            stdout=stdout,
            stderr=stderr,
            elapsed_ns=elapsed_ns,
        ),
        cubin_path,
    )


def rebind_exact_cubin_diagnostic_journal(raw: bytes) -> ExactCubinDiagnosticRebinding:
    if not isinstance(raw, bytes) or len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("exact-cubin journal bytes differ")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None or recovery.invalid_suffix_bytes:
        reason = recovery.failure.reason if recovery.failure is not None else "suffix"
        raise ValueError(f"exact-cubin journal is incomplete: {reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("exact-cubin journal omits header or terminal")
    if records[0].body.kind.value != "header" or records[-1].body.kind.value != "terminal":
        raise ValueError("exact-cubin journal endpoints differ")
    _validate_header(records[0].body.payload)
    observations = records[1:-1]
    if any(record.body.kind.value != "observation" for record in observations):
        raise ValueError("exact-cubin journal has a non-observation middle record")
    terminal_payload = records[-1].body.payload
    if terminal_payload.get("schema_version") != "legal-river-exact-cubin-diagnostic-owner-terminal-v1":
        raise ValueError("exact-cubin outer terminal schema differs")
    terminal = terminal_payload.get("terminal")
    passed = terminal_payload.get("passed")
    terminal_reason = terminal_payload.get("reason")
    if (
        terminal not in _OUTER_TERMINALS
        or not isinstance(passed, bool)
        or not isinstance(terminal_reason, str)
        or not terminal_reason
        or len(terminal_reason) > 4096
        or not terminal_reason.isascii()
    ):
        raise ValueError("exact-cubin outer terminal differs")
    if passed is not (terminal == "capture_complete"):
        raise ValueError("exact-cubin outer terminal pass bit disagrees")
    if (
        terminal_payload.get("event_count") != len(observations)
        or terminal_payload.get("selected_inspector") is not None
        or terminal_payload.get("resource_gate_result") is not None
        or terminal_payload.get("calibration_result") is not None
        or terminal_payload.get("capacity_projection") is not None
    ):
        raise ValueError("exact-cubin outer terminal claims differ")
    expected_last = (
        observations[-1].body.semantic_identity_sha256 if observations else None
    )
    if terminal_payload.get("last_event_semantic_identity_sha256") != expected_last:
        raise ValueError("exact-cubin outer terminal last identity differs")

    config = _load_config()
    source_commit: str | None = None
    kinds: list[str] = []
    events: list[Mapping[str, object]] = []
    for index, record in enumerate(observations):
        payload = record.body.payload
        if (
            payload.get("schema_version")
            != "legal-river-exact-cubin-diagnostic-observation-v1"
            or payload.get("event_index") != index
            or payload.get("config_sha256") != CONFIG_SHA256
        ):
            raise ValueError("exact-cubin observation envelope differs")
        commit = payload.get("source_commit")
        if not isinstance(commit, str) or len(commit) != 40:
            raise ValueError("exact-cubin observation commit differs")
        if source_commit is None:
            source_commit = commit
        elif source_commit != commit:
            raise ValueError("exact-cubin observation commit changed")
        kind = payload.get("event_kind")
        event = _mapping(payload.get("event"), label="observation event")
        if not isinstance(kind, str):
            raise TypeError("exact-cubin observation kind must be text")
        kinds.append(kind)
        events.append(event)

    cubin: BinaryEvidence | None = None
    driver_rows: dict[str, dict[str, int]] | None = None
    candidates: list[CandidateEvidence] = []
    cleanup: Mapping[str, object] | None = None
    cursor = 0
    if events:
        if kinds[0] != "provenance":
            raise ValueError("exact-cubin first observation is not provenance")
        provenance = events[0]
        if (
            provenance.get("schema_version")
            != "legal-river-exact-cubin-diagnostic-provenance-v1"
            or provenance.get("config_sha256") != CONFIG_SHA256
            or provenance.get("source_commit") != source_commit
            or provenance.get("source_dirty") is not False
            or provenance.get("reserved_actual_result_absent") is not True
            or provenance.get("literal_worker_module") != LITERAL_WORKER_MODULE
            or _RESERVED.exists()
        ):
            raise ValueError("exact-cubin provenance differs")
        _validate_current_dependencies(provenance)
        _validate_retained_artifacts(provenance.get("retained_artifacts"))
        cursor = 1
    if cursor < len(events) and kinds[cursor] == "bootstrap_handshake":
        _validate_handshake(events[cursor])
        cursor += 1
    if cursor < len(events) and kinds[cursor] == "compiler_capture":
        cubin, driver_rows = _validate_compiler_capture(events[cursor])
        cursor += 1
        expected_candidates = _expected_candidate_rows(config)
        cubin_path: str | None = None
        while cursor < len(events) and kinds[cursor] == "candidate_command":
            if len(candidates) >= len(expected_candidates):
                raise ValueError("exact-cubin candidate count exceeds inventory")
            candidate, cubin_path = _validate_candidate(
                events[cursor],
                expected_candidates[len(candidates)],
                expected_index=len(candidates),
                prior_cubin_path=cubin_path,
            )
            candidates.append(candidate)
            cursor += 1
        if cursor < len(events) and kinds[cursor] == "cleanup":
            candidate_cleanup = events[cursor]
            if (
                candidate_cleanup.get("schema_version")
                != "legal-river-exact-cubin-cleanup-v1"
                or candidate_cleanup.get("temporary_cubin_removed") is not True
                or candidate_cleanup.get("candidate_events_retained") != len(candidates)
            ):
                raise ValueError("exact-cubin cleanup differs")
            cleanup = candidate_cleanup
            cursor += 1
    if cursor < len(events) and kinds[cursor] == "worker_failure":
        failure = events[cursor]
        if (
            failure.get("schema_version")
            != "legal-river-exact-cubin-diagnostic-worker-failure-v1"
            or not isinstance(failure.get("reason"), str)
        ):
            raise ValueError("exact-cubin worker failure differs")
        cursor += 1
    terminal_evidence: Mapping[str, object] | None = None
    if cursor < len(events) and kinds[cursor] == "terminal_evidence":
        terminal_evidence = events[cursor]
        cursor += 1
    if cursor != len(events):
        raise ValueError("exact-cubin observation order differs")
    if terminal_evidence is not None:
        evidence_reason = terminal_evidence.get("reason")
        if (
            terminal_evidence.get("schema_version")
            != "legal-river-exact-cubin-diagnostic-terminal-evidence-v1"
            or terminal_evidence.get("terminal") != terminal
            or terminal_evidence.get("passed") is not passed
            or terminal_evidence.get("candidate_events_retained") != len(candidates)
            or terminal_evidence.get("selected_inspector") is not None
            or terminal_evidence.get("resource_gate_result") is not None
            or terminal_evidence.get("calibration_result") is not None
            or terminal_evidence.get("capacity_projection") is not None
            or not isinstance(evidence_reason, str)
            or not evidence_reason
        ):
            raise ValueError("exact-cubin terminal evidence differs")
    elif terminal not in {"infrastructure_failure", "laboratory_wall_rejection"}:
        raise ValueError("exact-cubin scientific terminal evidence is absent")
    if terminal == "capture_complete":
        if (
            cubin is None
            or driver_rows is None
            or len(candidates) != 5
            or any(candidate.status != "completed" for candidate in candidates)
            or cleanup is None
            or kinds
            != [
                "provenance",
                "bootstrap_handshake",
                "compiler_capture",
                *(["candidate_command"] * 5),
                "cleanup",
                "terminal_evidence",
            ]
        ):
            raise ValueError("exact-cubin complete capture inventory differs")
    return ExactCubinDiagnosticRebinding(
        terminal=terminal,
        passed=passed,
        event_count=len(observations),
        source_commit=source_commit,
        cubin=cubin,
        driver_rows=driver_rows,
        candidates=tuple(candidates),
        cleanup=cleanup,
        journal_byte_count=len(raw),
    )


def rebind_exact_cubin_diagnostic_file(
    path: Path = _RESULT,
) -> ExactCubinDiagnosticRebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"exact-cubin diagnostic result is incomplete: {recovery.failure.reason}")
    return rebind_exact_cubin_diagnostic_journal(path.read_bytes())


__all__ = [
    "BinaryEvidence",
    "CAMPAIGN_SHA256",
    "CandidateEvidence",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "ExactCubinDiagnosticRebinding",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "canonical_lf_sha256",
    "decode_binary",
    "rebind_exact_cubin_diagnostic_file",
    "rebind_exact_cubin_diagnostic_journal",
]
