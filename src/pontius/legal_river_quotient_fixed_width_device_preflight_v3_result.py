"""Independent lifecycle reader for the ADR-0446 split-runtime successor."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from threading import RLock
from typing import Iterator, Mapping

from . import legal_river_quotient_fixed_width_device_preflight_v2_result as _parent
from .durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)


_ROOT = Path(__file__).parents[2]
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v3.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
CONFIG_SHA256 = "492458e39020fc8d5178624e4a9b8b1c6c0fc4c004852d155618fc11c955547d"
CORRECTION_CONFIG_SHA256 = _parent.CORRECTION_CONFIG_SHA256
PREREGISTRATION_COMMIT = "68e3ce35779701ef5eeb8fad9f6c42ccdd7b05ac"
CORRECTION_COMMIT = _parent.CORRECTION_COMMIT
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0446-split-runtime-fixed-width-device-owner-v3"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0446-split-runtime-fixed-width-device-campaign-v3"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
)
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v2.jsonl"
)
CONSUMED_RESULT_SHA256 = (
    "af5210920d61ef4a39dc027d303a83b64b09ada794f67526ee856ac0e5901085"
)
DEPENDENCY_RELATIVE_PATHS = (
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v4-child-runtime-environment.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v3-msvc-environment.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v2-topology.json",
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0442-retain-the-fixed-width-device-compiler-rejection.md",
    "docs/decisions/ADR-0443-preregister-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0444-source-seal-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0445-retain-the-msvc-bound-zero-event-infrastructure-rejection.md",
    "docs/decisions/ADR-0446-preregister-the-split-child-runtime-environment-successor.md",
    "docs/decisions/ADR-0447-source-seal-the-split-child-runtime-environment-successor.md",
    CONSUMED_RESULT_RELATIVE_PATH,
    "artifacts/work_preflight/legal_river_quotient_fixed_width_device_preflight_v1.jsonl",
    "run_legal_river_quotient_fixed_width_device_preflight_v3.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v3.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_result.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_outcome.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v2_outcome.py",
    "src/pontius/__init__.py",
    "src/pontius/cuda_dll_bootstrap.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_CLAIMS = {
    "action_clock_result": None,
    "action_result": None,
    "actual_45_card_value": None,
    "blueprint_result": None,
    "candidate_selected": None,
    "decision_quality_result": None,
    "device_preflight_result": None,
    "poker_strength_result": None,
    "population_25_numeric_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "truncation_authorized": False,
}
_HEADER_KEYS = set(_parent._HEADER_KEYS) | {"child_runtime_environment"}
_TERMINAL_KEYS = {
    "schema_version",
    "terminal",
    "passed",
    "reason",
    "event_count",
    "laboratory_elapsed_ns",
    "laboratory_wall_ns",
    "outside_laboratory_elapsed_ns",
    "outside_laboratory_wall_ns",
    "public_elapsed_ns",
    "public_wall_ns",
    "claims",
}
_EARLY_TERMINALS = {
    "infrastructure_failure",
    "laboratory_wall_rejection",
    "public_wall_rejection",
    "outside_laboratory_wall_rejection",
}
_PARENT_BINDING_NAMES = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "CONFIG_SHA256",
    "CORRECTION_CONFIG_SHA256",
    "PREREGISTRATION_COMMIT",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
)
_PARENT_LOCK = RLock()


@dataclass(frozen=True, slots=True)
class AssessedDevicePreflightV3:
    terminal: str
    passed: bool
    source_commit: str
    event_count: int
    eligible_arms: tuple[str, ...]
    candidate_selected: None
    laboratory_elapsed_ns: int | None
    public_elapsed_ns: int


def _canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index : index + 2] == bytes((13, 10)):
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _expected_runtime_files() -> list[dict[str, object]]:
    root = (
        r"C:\Users\point\OneDrive\Documents\ChatGPT\Pontius\.venv\Lib\site-packages"
        r"\nvidia\cu13\bin\x86_64"
    )
    rows = (
        ("cudart64_13.dll", 551_024, "b00ca6f53699120da815bf3e06e2e4285fae2f201235b883dcbb50eec51e2a2a"),
        ("nvJitLink_130_0.dll", 92_465_776, "727a0acfc4495b229143b53843004eef36e0a3463fb2e1c7c4215468607fd613"),
        ("nvrtc-builtins64_133.dll", 6_684_784, "82c703802846329d3bab3d8df06f8c956516a0eeec568033092d6c0a69b2733a"),
        ("nvrtc64_130_0.dll", 101_385_328, "c7af6b5dbd001852d1b4a18effc6fbcfc94787eddadffea629a8333cb25b05fe"),
        ("cusparse64_12.dll", 166_481_008, "fa7629e5eda676ccb685119490d2db88881b044cccf4023a9c326ad7513c425b"),
    )
    return [
        {"name": name, "path": root + "\\" + name, "bytes": size, "sha256": digest}
        for name, size, digest in rows
    ]


def _validate_runtime(value: object) -> None:
    runtime = _mapping(value, label="child runtime")
    root = (
        r"C:\Users\point\OneDrive\Documents\ChatGPT\Pontius\.venv\Lib\site-packages"
        r"\nvidia\cu13\bin\x86_64"
    )
    expected_keys = {
        "schema_version",
        "parent_activated_key_count",
        "parent_full_environment_sha256",
        "parent_selected_environment_sha256",
        "child_activated_key_count",
        "child_full_environment_sha256",
        "child_selected_environment_sha256",
        "complete_campaign_environment_key_count",
        "changed_parent_activated_keys",
        "path_prefix",
        "path_prefix_occurrence_count",
        "parent_path_is_exact_child_suffix",
        "runtime_source",
        "cuda_root",
        "static_child_values",
        "required_runtime_files",
        "resolved_tools",
        "compiler_executed",
        "cupy_scientific_imported",
        "device_queried",
    }
    if (
        set(runtime) != expected_keys
        or runtime.get("schema_version")
        != "legal-river-fixed-width-child-runtime-v1"
        or runtime.get("parent_activated_key_count") != 55
        or runtime.get("parent_full_environment_sha256")
        != "6b3ccdc1ac479b5b4b9626161cdd5ca28f5d5043f6b87cc65a6f27f8e1a3cfe6"
        or runtime.get("parent_selected_environment_sha256")
        != "a313c9a0fc817a9375912aba0e9acce6984e7d9bb5b28b3ccf56e7ef23a7c1a0"
        or runtime.get("child_activated_key_count") != 55
        or runtime.get("child_full_environment_sha256")
        != "287903a61870ad16883bfcb764f50758857cdc463fe803c5b21ee41ff2a6a874"
        or runtime.get("child_selected_environment_sha256")
        != "10068a92a3a2fe39269b77c2c22e07e0889261f0dcc696f074a2f786c1167270"
        or runtime.get("complete_campaign_environment_key_count") != 63
        or runtime.get("changed_parent_activated_keys") != ["PATH"]
        or runtime.get("path_prefix") != root
        or runtime.get("path_prefix_occurrence_count") != 1
        or runtime.get("parent_path_is_exact_child_suffix") is not True
        or runtime.get("runtime_source") != "active_python_environment"
        or runtime.get("cuda_root") != root.rsplit("\\bin\\x86_64", 1)[0]
        or runtime.get("required_runtime_files") != _expected_runtime_files()
        or runtime.get("compiler_executed") is not False
        or runtime.get("cupy_scientific_imported") is not False
        or runtime.get("device_queried") is not False
    ):
        raise ValueError("child runtime evidence differs")
    if runtime.get("static_child_values") != {
        "CUDA_PATH": root.rsplit("\\bin\\x86_64", 1)[0],
        "PONTIUS_CUDA_DLL_DIRECTORY": root,
        "PONTIUS_CUDA_DLL_SOURCE": "active_python_environment",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": r"C:\Users\point\OneDrive\Documents\ChatGPT\Pontius\src",
    }:
        raise ValueError("child runtime static values differ")
    if runtime.get("resolved_tools") != _parent.EXPECTED_RESOLVED_TOOLS:
        raise ValueError("child runtime resolved tools differ")


def _validate_fresh_journal(raw: bytes):
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if (
        not recovery.is_complete
        or recovery.invalid_suffix_bytes
        or len(recovery.records) < 2
        or recovery.records[0].body.kind is not JournalRecordKind.HEADER
        or recovery.records[-1].body.kind is not JournalRecordKind.TERMINAL
    ):
        raise ValueError("split-runtime journal lifecycle differs")
    for envelope in recovery.records:
        semantic = sha256(canonical_journal_json_bytes(envelope.body.payload)).hexdigest()
        if envelope.body.semantic_identity_sha256 != semantic:
            raise ValueError("split-runtime journal semantic identity differs")
    header = recovery.records[0].body.payload
    if set(header) != _HEADER_KEYS:
        raise ValueError("split-runtime header domain differs")
    if (
        header.get("schema_version")
        != "legal-river-fixed-width-device-owner-header-v1"
        or header.get("protocol_sha256") != PROTOCOL_SHA256
        or header.get("campaign_sha256") != CAMPAIGN_SHA256
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("correction_commit") != CORRECTION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
        or header.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or header.get("scientific_module")
        != "pontius.legal_river_quotient_fixed_width_device_preflight"
        or header.get("claims") != _CLAIMS
        or header.get("predecessor")
        != {
            "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
            "result_raw_sha256": CONSUMED_RESULT_SHA256,
            "terminal": "infrastructure_failure",
            "event_count": 0,
        }
    ):
        raise ValueError("split-runtime header identity differs")
    source = _mapping(header.get("source_seal_git"), label="source seal")
    commit = source.get("commit")
    if (
        set(source) != {"commit", "dirty", "strict_status"}
        or not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
        or source.get("dirty") is not False
        or source.get("strict_status") is not True
    ):
        raise ValueError("split-runtime source-seal identity differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="dependencies")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("split-runtime dependency domain differs")
    for relative, expected in dependencies.items():
        path = _ROOT / relative
        if (
            not isinstance(expected, str)
            or not path.is_file()
            or sha256(_canonical_lf(path.read_bytes())).hexdigest() != expected
        ):
            raise ValueError(f"split-runtime dependency differs: {relative}")
    _parent._validate_host_toolchain(header.get("host_toolchain"))
    _validate_runtime(header.get("child_runtime_environment"))
    observations = recovery.records[1:-1]
    if observations:
        first = observations[0]
        if first.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("split-runtime first observation kind differs")
        row = first.body.payload
        event = _mapping(row.get("event"), label="bootstrap")
        if (
            row.get("schema_version")
            != "legal-river-fixed-width-device-owner-observation-v1"
            or row.get("event_index") != 0
            or row.get("source_commit") != commit
            or row.get("kind") != "bootstrap_handshake"
            or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        ):
            raise ValueError("split-runtime bootstrap differs")
    return recovery


def _parent_projection_bytes(recovery) -> bytes:
    previous: str | None = None
    lines = []
    changed_paths = []
    for envelope in recovery.records:
        payload = envelope.body.payload
        if envelope.body.kind is JournalRecordKind.HEADER:
            payload = dict(payload)
            payload.pop("child_runtime_environment")
            changed_paths.append(
                "$.records[0].body.payload.child_runtime_environment"
            )
            payload["predecessor"] = {
                "result_relative_path": (
                    "artifacts/work_preflight/"
                    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
                ),
                "result_raw_sha256": (
                    "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
                ),
                "terminal": "compiler_rejection",
            }
            changed_paths.append("$.records[0].body.payload.predecessor")
        semantic = sha256(canonical_journal_json_bytes(payload)).hexdigest()
        body = build_journal_record_body(
            protocol_sha256=PROTOCOL_SHA256,
            campaign_sha256=CAMPAIGN_SHA256,
            kind=envelope.body.kind,
            sequence=envelope.body.sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=semantic,
            payload=payload,
        )
        projected = JournalRecordEnvelope(body=body)
        lines.append(projected.line_bytes)
        previous = projected.line_sha256
    if changed_paths != [
        "$.records[0].body.payload.child_runtime_environment",
        "$.records[0].body.payload.predecessor",
    ]:
        raise ValueError("split-runtime parent projection allowlist differs")
    return b"".join(lines)


@contextmanager
def _configured_parent_reader() -> Iterator[None]:
    replacements = {
        "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
        "RESULT_PATH": RESULT_PATH,
        "PROTOCOL_SHA256": PROTOCOL_SHA256,
        "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
        "CONFIG_SHA256": CONFIG_SHA256,
        "CORRECTION_CONFIG_SHA256": CORRECTION_CONFIG_SHA256,
        "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
        "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
        "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
    }
    with _PARENT_LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDING_NAMES}
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def _assess_zero_event(recovery) -> AssessedDevicePreflightV3:
    header = recovery.records[0].body.payload
    terminal = recovery.records[-1].body.payload
    if set(terminal) != _TERMINAL_KEYS:
        raise ValueError("split-runtime zero-event terminal domain differs")
    terminal_name = terminal.get("terminal")
    reason = terminal.get("reason")
    public_elapsed = _integer(
        terminal.get("public_elapsed_ns"), label="public elapsed"
    )
    if (
        terminal.get("schema_version")
        != "legal-river-fixed-width-device-owner-terminal-v1"
        or terminal_name not in _EARLY_TERMINALS
        or terminal.get("passed") is not False
        or terminal.get("event_count") != 0
        or terminal.get("laboratory_elapsed_ns") is not None
        or terminal.get("outside_laboratory_elapsed_ns") is not None
        or terminal.get("laboratory_wall_ns") != 240_000_000_000
        or terminal.get("outside_laboratory_wall_ns") != 30_000_000_000
        or terminal.get("public_wall_ns") != 270_000_000_000
        or terminal.get("claims") != _CLAIMS
        or not isinstance(reason, str)
        or not reason
    ):
        raise ValueError("split-runtime zero-event terminal differs")
    return AssessedDevicePreflightV3(
        terminal=str(terminal_name),
        passed=False,
        source_commit=str(header["source_seal_git"]["commit"]),
        event_count=0,
        eligible_arms=(),
        candidate_selected=None,
        laboratory_elapsed_ns=None,
        public_elapsed_ns=public_elapsed,
    )


def assess_device_preflight_v3_bytes(raw: bytes) -> AssessedDevicePreflightV3:
    if type(raw) is not bytes:
        raise TypeError("split-runtime reader requires immutable bytes")
    recovery = _validate_fresh_journal(raw)
    if len(recovery.records) == 2:
        return _assess_zero_event(recovery)
    projected = _parent_projection_bytes(recovery)
    with _configured_parent_reader():
        assessed = _parent.assess_device_preflight_v2_bytes(projected)
    return AssessedDevicePreflightV3(
        terminal=assessed.terminal,
        passed=assessed.passed,
        source_commit=assessed.source_commit,
        event_count=assessed.event_count,
        eligible_arms=assessed.eligible_arms,
        candidate_selected=assessed.candidate_selected,
        laboratory_elapsed_ns=assessed.laboratory_elapsed_ns,
        public_elapsed_ns=assessed.public_elapsed_ns,
    )


def assess_device_preflight_v3_file(
    path: Path = RESULT_PATH,
) -> AssessedDevicePreflightV3:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("split-runtime device-preflight result is absent")
    return assess_device_preflight_v3_bytes(path.read_bytes())


__all__ = [
    "AssessedDevicePreflightV3",
    "CAMPAIGN_SHA256",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_device_preflight_v3_bytes",
    "assess_device_preflight_v3_file",
]
