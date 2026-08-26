"""Artifact-bound assessor for the consumed ADR-0444 v2 invocation.

The source-sealed v2 reader assumed that every complete journal contained a
bootstrap observation.  The inherited owner contract also permits a complete
infrastructure terminal before the first observation.  This additive assessor
handles that exact retained lifecycle without editing either source-sealed v2
module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import subprocess

from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes


_ROOT = Path(__file__).parents[2]
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v2.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
RESULT_BYTES = 10_557
RESULT_SHA256 = "af5210920d61ef4a39dc027d303a83b64b09ada794f67526ee856ac0e5901085"
SOURCE_COMMIT = "3cf5d1d8f5667f7bf48102ed130f92fce33c9516"
PROTOCOL_SHA256 = "249f68feab6d0bef09a77c1ad7efafcde281dcf641b59df3e807a88baba9cbb1"
CAMPAIGN_SHA256 = "dc0aa1cc2d09316c469352d61b8e9b321360cc8f68cfd81e3af8e1c26cb5a357"
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"

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


@dataclass(frozen=True, slots=True)
class AssessedDevicePreflightV2Outcome:
    terminal: str
    passed: bool
    source_commit: str
    record_count: int
    event_count: int
    eligible_arms: tuple[str, ...]
    candidate_selected: None
    laboratory_elapsed_ns: None
    outside_laboratory_elapsed_ns: None
    public_elapsed_ns: int


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


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


def _integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _validate_source_commit_dependencies(header: Mapping[str, object]) -> None:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise ValueError("retained outcome Git identity differs")
    source = _mapping(header.get("source_seal_git"), label="source-seal Git")
    if source != {"commit": SOURCE_COMMIT, "dirty": False, "strict_status": True}:
        raise ValueError("retained outcome source-seal identity differs")
    resolved = subprocess.run(
        [str(GIT_PATH), "rev-parse", f"{SOURCE_COMMIT}^{{commit}}"],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != SOURCE_COMMIT:
        raise ValueError("retained outcome source commit differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="dependencies")
    if len(dependencies) != 22:
        raise ValueError("retained outcome dependency domain differs")
    for relative, expected in dependencies.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        ):
            raise ValueError("retained outcome dependency row differs")
        completed = subprocess.run(
            [str(GIT_PATH), "show", f"{SOURCE_COMMIT}:{relative}"],
            cwd=_ROOT,
            check=True,
            capture_output=True,
        )
        if sha256(_canonical_lf(completed.stdout)).hexdigest() != expected:
            raise ValueError(f"retained outcome dependency differs: {relative}")


def _validate_header(header: Mapping[str, object]) -> None:
    if set(header) != _HEADER_KEYS:
        raise ValueError("retained outcome header domain differs")
    if (
        header.get("schema_version")
        != "legal-river-fixed-width-device-owner-header-v1"
        or header.get("protocol_sha256") != PROTOCOL_SHA256
        or header.get("campaign_sha256") != CAMPAIGN_SHA256
        or header.get("config_sha256")
        != "21b74a0f7f13e8eac894d4ecf2c4dd05cde3925ab24449f11944d954ec59067c"
        or header.get("correction_config_sha256")
        != "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
        or header.get("preregistration_commit")
        != "b24eae342a51fdbfcd393025faf8e4f414a5cc4e"
        or header.get("correction_commit")
        != "e4704d9011ad4af2f7d610bfa56053d046864d96"
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("literal_worker_module")
        != "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
        or header.get("scientific_module")
        != "pontius.legal_river_quotient_fixed_width_device_preflight"
        or header.get("claims") != _CLAIMS
    ):
        raise ValueError("retained outcome header identity differs")
    predecessor = _mapping(header.get("predecessor"), label="predecessor")
    if predecessor != {
        "result_relative_path": (
            "artifacts/work_preflight/"
            "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
        ),
        "result_raw_sha256": (
            "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
        ),
        "terminal": "compiler_rejection",
    }:
        raise ValueError("retained outcome predecessor differs")
    host = _mapping(header.get("host_toolchain"), label="host toolchain")
    if (
        host.get("schema_version") != "legal-river-fixed-width-msvc-toolchain-v1"
        or host.get("full_environment_sha256")
        != "6b3ccdc1ac479b5b4b9626161cdd5ca28f5d5043f6b87cc65a6f27f8e1a3cfe6"
        or host.get("selected_environment_sha256")
        != "a313c9a0fc817a9375912aba0e9acce6984e7d9bb5b28b3ccf56e7ef23a7c1a0"
        or host.get("environment_key_count") != 55
        or host.get("compiler_executed") is not False
        or host.get("ambient_compiler_environment_inherited") is not False
    ):
        raise ValueError("retained outcome host-toolchain evidence differs")
    activation = _integer(
        host.get("activation_elapsed_ns"), label="activation elapsed"
    )
    if activation != 1_031_068_800:
        raise ValueError("retained outcome activation elapsed differs")
    _validate_source_commit_dependencies(header)


def assess_device_preflight_v2_outcome_bytes(
    raw: bytes,
) -> AssessedDevicePreflightV2Outcome:
    if type(raw) is not bytes:
        raise TypeError("retained v2 outcome reader requires immutable bytes")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if (
        not recovery.is_complete
        or recovery.invalid_suffix_bytes
        or len(recovery.records) != 2
        or recovery.records[0].body.kind is not JournalRecordKind.HEADER
        or recovery.records[1].body.kind is not JournalRecordKind.TERMINAL
    ):
        raise ValueError("retained v2 outcome journal lifecycle differs")
    header = recovery.records[0].body.payload
    terminal = recovery.records[1].body.payload
    _validate_header(header)
    if set(terminal) != _TERMINAL_KEYS:
        raise ValueError("retained v2 outcome terminal domain differs")
    reason = terminal.get("reason")
    if (
        terminal.get("schema_version")
        != "legal-river-fixed-width-device-owner-terminal-v1"
        or terminal.get("terminal") != "infrastructure_failure"
        or terminal.get("passed") is not False
        or terminal.get("event_count") != 0
        or terminal.get("laboratory_elapsed_ns") is not None
        or terminal.get("outside_laboratory_elapsed_ns") is not None
        or terminal.get("laboratory_wall_ns") != 240_000_000_000
        or terminal.get("outside_laboratory_wall_ns") != 30_000_000_000
        or terminal.get("public_elapsed_ns") != 2_614_814_700
        or terminal.get("public_wall_ns") != 270_000_000_000
        or terminal.get("claims") != _CLAIMS
        or not isinstance(reason, str)
        or not reason.endswith(
            "ValueError: MSVC full activated environment identity differs\r\n"
        )
    ):
        raise ValueError("retained v2 outcome terminal differs")
    if len(raw) != RESULT_BYTES or sha256(raw).hexdigest() != RESULT_SHA256:
        raise ValueError("retained v2 outcome raw identity differs")
    return AssessedDevicePreflightV2Outcome(
        terminal="infrastructure_failure",
        passed=False,
        source_commit=SOURCE_COMMIT,
        record_count=2,
        event_count=0,
        eligible_arms=(),
        candidate_selected=None,
        laboratory_elapsed_ns=None,
        outside_laboratory_elapsed_ns=None,
        public_elapsed_ns=2_614_814_700,
    )


def assess_device_preflight_v2_outcome_file(
    path: Path = RESULT_PATH,
) -> AssessedDevicePreflightV2Outcome:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("retained v2 device-preflight result is absent")
    return assess_device_preflight_v2_outcome_bytes(path.read_bytes())


__all__ = [
    "AssessedDevicePreflightV2Outcome",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "RESULT_SHA256",
    "assess_device_preflight_v2_outcome_bytes",
    "assess_device_preflight_v2_outcome_file",
]
