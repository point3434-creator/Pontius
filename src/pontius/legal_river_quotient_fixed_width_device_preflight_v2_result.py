"""Independent standard-library reader for the ADR-0443 successor journal."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from threading import RLock
from typing import Iterator, Mapping

from . import legal_river_quotient_fixed_width_device_preflight_result as _parent
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
    "legal_river_quotient_fixed_width_device_preflight_v2.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
CONFIG_SHA256 = "21b74a0f7f13e8eac894d4ecf2c4dd05cde3925ab24449f11944d954ec59067c"
CORRECTION_CONFIG_SHA256 = (
    "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
)
PREREGISTRATION_COMMIT = "b24eae342a51fdbfcd393025faf8e4f414a5cc4e"
CORRECTION_COMMIT = "e4704d9011ad4af2f7d610bfa56053d046864d96"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0443-msvc-bound-fixed-width-device-owner-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0443-msvc-bound-fixed-width-device-campaign-v2"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
)
PARENT_LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
)
SCIENTIFIC_MODULE = "pontius.legal_river_quotient_fixed_width_device_preflight"
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
)
CONSUMED_RESULT_SHA256 = (
    "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
)
FULL_ENVIRONMENT_SHA256 = (
    "6b3ccdc1ac479b5b4b9626161cdd5ca28f5d5043f6b87cc65a6f27f8e1a3cfe6"
)
SELECTED_ENVIRONMENT_SHA256 = (
    "a313c9a0fc817a9375912aba0e9acce6984e7d9bb5b28b3ccf56e7ef23a7c1a0"
)
ACTIVATION_WALL_NS = 10_000_000_000

EXPECTED_HOST_FILES = (
    ("vswhere", r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe", 469_456, "c54f3b7c9164ea9a0db8641e81ecdda80c2664ef5a47c4191406f848cc07c662"),
    ("vcvars64", r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat", 39, "6b516d8fcf543c14b2d861e1f45661e0029230fe0dc48e86ce78522801822209"),
    ("vcvarsall", r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat", 10_524, "ee67e4181ae2578b7842f9f1549a7f66e2166638fa544ce6838d9e9033a02275"),
    ("cl", r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe", 677_736, "88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d"),
    ("link", r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\link.exe", 3_252_576, "ca11e6c45debd34bf652dfe984c5360a531a005ed78bf72852330c9c2590cf0d"),
    ("rc", r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\rc.exe", 55_640, "43da1503c262c30894c851589bf0155f8365d77e63a5f7bc13982320e3a6b42d"),
    ("nvcc", r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe", 20_017_264, "92d993c6e7025e1597d0d895e65e8658f5f1d41576a477656647a7eece2cd35f"),
    ("git", r"C:\Program Files\Git\cmd\git.exe", 46_920, "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"),
)
EXPECTED_RESOLVED_TOOLS = {
    "cl.exe": EXPECTED_HOST_FILES[3][1],
    "link.exe": EXPECTED_HOST_FILES[4][1],
    "rc.exe": EXPECTED_HOST_FILES[5][1],
}
DEPENDENCY_RELATIVE_PATHS = (
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v3-msvc-environment.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v2-topology.json",
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0442-retain-the-fixed-width-device-compiler-rejection.md",
    "docs/decisions/ADR-0443-preregister-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0444-source-seal-the-msvc-bound-fixed-width-device-successor.md",
    CONSUMED_RESULT_RELATIVE_PATH,
    "run_legal_river_quotient_fixed_width_device_preflight_v2.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v2.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_HEADER_KEYS = {
    "schema_version",
    "protocol_sha256",
    "campaign_sha256",
    "config_sha256",
    "correction_config_sha256",
    "preregistration_commit",
    "correction_commit",
    "source_seal_git",
    "dependency_hashes",
    "result_relative_path",
    "reserved_actual_result_relative_path",
    "literal_worker_module",
    "scientific_module",
    "claims",
    "host_toolchain",
    "predecessor",
}
_PARENT_BINDING_NAMES = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "CONFIG_SHA256",
    "CORRECTION_CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
)
_PARENT_READER_LOCK = RLock()


@dataclass(frozen=True, slots=True)
class AssessedDevicePreflightV2:
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


def _validate_host_toolchain(value: object) -> None:
    host = _mapping(value, label="MSVC host toolchain")
    elapsed = host.get("activation_elapsed_ns")
    if (
        set(host)
        != {
            "schema_version",
            "installation_version",
            "vc_tools_version",
            "compiler_version",
            "windows_sdk_version",
            "file_identities",
            "environment_key_count",
            "full_environment_sha256",
            "selected_environment_sha256",
            "resolved_tools",
            "activation_elapsed_ns",
            "compiler_executed",
            "ambient_compiler_environment_inherited",
        }
        or host.get("schema_version") != "legal-river-fixed-width-msvc-toolchain-v1"
        or host.get("installation_version") != "17.14.37614.0"
        or host.get("vc_tools_version") != "14.44.35207"
        or host.get("compiler_version") != "19.44.35228.0"
        or host.get("windows_sdk_version") != "10.0.26100.0"
        or host.get("environment_key_count") != 55
        or host.get("full_environment_sha256") != FULL_ENVIRONMENT_SHA256
        or host.get("selected_environment_sha256") != SELECTED_ENVIRONMENT_SHA256
        or host.get("resolved_tools") != EXPECTED_RESOLVED_TOOLS
        or host.get("compiler_executed") is not False
        or host.get("ambient_compiler_environment_inherited") is not False
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, int)
        or elapsed < 0
        or elapsed > ACTIVATION_WALL_NS
    ):
        raise ValueError("MSVC host-toolchain evidence differs")
    expected_files = [
        {"role": role, "path": path, "bytes": size, "sha256": digest}
        for role, path, size, digest in EXPECTED_HOST_FILES
    ]
    if host.get("file_identities") != expected_files:
        raise ValueError("MSVC host-file evidence differs")


def _validate_fresh_journal(raw: bytes):
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or recovery.invalid_suffix_bytes or len(recovery.records) < 2:
        raise ValueError("MSVC-bound journal is torn, invalid, or incomplete")
    for envelope in recovery.records:
        semantic = sha256(canonical_journal_json_bytes(envelope.body.payload)).hexdigest()
        if envelope.body.semantic_identity_sha256 != semantic:
            raise ValueError("MSVC-bound journal semantic identity differs")
    if recovery.records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("MSVC-bound journal header is absent")
    header = recovery.records[0].body.payload
    if set(header) != _HEADER_KEYS:
        raise ValueError("MSVC-bound header domain differs")
    if (
        header.get("schema_version") != "legal-river-fixed-width-device-owner-header-v1"
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
        or header.get("scientific_module") != SCIENTIFIC_MODULE
        or header.get("claims") != _parent.HEADER_CLAIMS
        or header.get("predecessor")
        != {
            "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
            "result_raw_sha256": CONSUMED_RESULT_SHA256,
            "terminal": "compiler_rejection",
        }
    ):
        raise ValueError("MSVC-bound header identity differs")
    git = _mapping(header.get("source_seal_git"), label="MSVC source seal")
    if (
        set(git) != {"commit", "dirty", "strict_status"}
        or not isinstance(git.get("commit"), str)
        or re.fullmatch(r"[0-9a-f]{40}", git["commit"]) is None
        or git.get("dirty") is not False
        or git.get("strict_status") is not True
    ):
        raise ValueError("MSVC source-seal identity differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="MSVC dependencies")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("MSVC dependency domain differs")
    for relative, expected in dependencies.items():
        path = _ROOT / relative
        if not path.is_file() or sha256(_canonical_lf(path.read_bytes())).hexdigest() != expected:
            raise ValueError(f"MSVC dependency drifted: {relative}")
    _validate_host_toolchain(header.get("host_toolchain"))

    observations = [record.body.payload for record in recovery.records[1:-1]]
    if not observations:
        raise ValueError("MSVC-bound journal observations are absent")
    first = observations[0]
    if first.get("kind") != "bootstrap_handshake":
        raise ValueError("MSVC-bound bootstrap is not first")
    event = _mapping(first.get("event"), label="MSVC bootstrap")
    if event.get("literal_worker_module") != LITERAL_WORKER_MODULE:
        raise ValueError("MSVC bootstrap worker identity differs")
    return recovery


def _parent_projection_bytes(recovery) -> bytes:
    previous: str | None = None
    lines = []
    changed_paths = []
    for envelope in recovery.records:
        payload = envelope.body.payload
        if envelope.body.kind is JournalRecordKind.HEADER:
            payload = dict(payload)
            if payload["literal_worker_module"] != LITERAL_WORKER_MODULE:
                raise ValueError("MSVC projection source value differs")
            payload["literal_worker_module"] = PARENT_LITERAL_WORKER_MODULE
            changed_paths.append("$.records[0].body.payload.literal_worker_module")
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
    if changed_paths != ["$.records[0].body.payload.literal_worker_module"]:
        raise ValueError("MSVC parent-reader projection allowlist differs")
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
        "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
    }
    with _PARENT_READER_LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDING_NAMES}
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def assess_device_preflight_v2_bytes(raw: bytes) -> AssessedDevicePreflightV2:
    if type(raw) is not bytes:
        raise TypeError("MSVC-bound device-preflight reader requires immutable bytes")
    recovery = _validate_fresh_journal(raw)
    projected = _parent_projection_bytes(recovery)
    with _configured_parent_reader():
        assessed = _parent.assess_device_preflight_bytes(projected)
    return AssessedDevicePreflightV2(
        terminal=assessed.terminal,
        passed=assessed.passed,
        source_commit=assessed.source_commit,
        event_count=assessed.event_count,
        eligible_arms=assessed.eligible_arms,
        candidate_selected=assessed.candidate_selected,
        laboratory_elapsed_ns=assessed.laboratory_elapsed_ns,
        public_elapsed_ns=assessed.public_elapsed_ns,
    )


def assess_device_preflight_v2_file(
    path: Path = RESULT_PATH,
) -> AssessedDevicePreflightV2:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("MSVC-bound device-preflight result is absent")
    return assess_device_preflight_v2_bytes(path.read_bytes())


__all__ = [
    "AssessedDevicePreflightV2",
    "CAMPAIGN_SHA256",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_device_preflight_v2_bytes",
    "assess_device_preflight_v2_file",
]
