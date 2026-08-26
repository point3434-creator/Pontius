"""Artifact-bound assessor for the consumed ADR-0447 v3 invocation.

The source-sealed reader remains the semantic authority.  This additive reader
binds that assessment to the exact retained artifact and records the small set
of outcome facts that the next prospective boundary may consume.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import subprocess

from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes
from .legal_river_quotient_fixed_width_device_preflight_v3_result import (
    CAMPAIGN_SHA256,
    PROTOCOL_SHA256,
    RESULT_PATH,
    RESULT_RELATIVE_PATH,
    assess_device_preflight_v3_bytes,
)


RESULT_BYTES = 4_175_066
RESULT_SHA256 = "6f0b53f95a5d538f7a3673fe411de4b40724fbf00cfc56c62360352cab3770bb"
SOURCE_COMMIT = "f271e6deeefe11f228d582c9734a166c0ba32b45"
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"

_EVENT_COUNTS = {
    "bootstrap_handshake": 1,
    "candidate_eligibility": 1,
    "candidate_observation": 42,
    "compile": 1,
    "durable_cubin_capture": 1,
    "external_resource_command": 2,
    "laboratory_partition": 1,
    "live_hardware_identity": 1,
    "module_load_and_resource_evidence": 1,
    "reduced_population_authority": 2,
    "symbolic_literal_45_memory_liveness": 1,
    "terminal_evidence": 1,
    "tool_identity_and_cuda_source_materialization": 1,
    "tool_versions": 1,
}
_TIMED_WALLS = {
    "batched_five_then_four_RRNS": {
        "complete_10": 529_598_900,
        "signed_12": 307_116_300,
    },
    "positional": {
        "complete_10": 570_318_700,
        "signed_12": 82_851_200,
    },
    "resident_nine_RRNS": {
        "complete_10": 389_052_400,
        "signed_12": 224_191_300,
    },
}
_MEMORY = {
    "batched_five_then_four_RRNS": (13_275_877_664, 1_818_598_112, True),
    "positional": (13_265_364_040, 1_829_111_736, True),
    "resident_nine_RRNS": (16_413_760_680, -1_319_284_904, False),
}
_OUTER_CLAIMS = {
    "action_clock_result": None,
    "action_result": None,
    "actual_45_card_value": None,
    "blueprint_result": None,
    "candidate_selected": None,
    "decision_quality_result": None,
    "device_preflight_result": True,
    "poker_strength_result": None,
    "population_25_numeric_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "truncation_authorized": False,
}


@dataclass(frozen=True, slots=True)
class AssessedDevicePreflightV3Outcome:
    terminal: str
    passed: bool
    source_commit: str
    record_count: int
    event_count: int
    eligible_arms: tuple[str, ...]
    ineligible_arms: tuple[str, ...]
    candidate_selected: None
    cubin_sha256: str
    cubin_bytes: int
    laboratory_elapsed_ns: int
    outside_laboratory_elapsed_ns: int
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


def _validate_source_commit(header: Mapping[str, object]) -> None:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise ValueError("retained v3 outcome Git identity differs")
    source = _mapping(header.get("source_seal_git"), label="source seal")
    if source != {"commit": SOURCE_COMMIT, "dirty": False, "strict_status": True}:
        raise ValueError("retained v3 outcome source identity differs")
    resolved = subprocess.run(
        [str(GIT_PATH), "rev-parse", f"{SOURCE_COMMIT}^{{commit}}"],
        cwd=RESULT_PATH.parents[2],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != SOURCE_COMMIT:
        raise ValueError("retained v3 outcome source commit differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="dependencies")
    if len(dependencies) != 34:
        raise ValueError("retained v3 outcome dependency domain differs")
    for relative, expected in dependencies.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        ):
            raise ValueError("retained v3 outcome dependency row differs")
        completed = subprocess.run(
            [str(GIT_PATH), "show", f"{SOURCE_COMMIT}:{relative}"],
            cwd=RESULT_PATH.parents[2],
            check=True,
            capture_output=True,
        )
        if sha256(_canonical_lf(completed.stdout)).hexdigest() != expected:
            raise ValueError(f"retained v3 outcome dependency differs: {relative}")


def _validate_candidate_evidence(events: Mapping[str, list[Mapping[str, object]]]) -> None:
    eligibility = events["candidate_eligibility"][0]
    if set(eligibility) != set(_TIMED_WALLS):
        raise ValueError("retained v3 candidate domain differs")
    for arm, walls in _TIMED_WALLS.items():
        row = _mapping(eligibility[arm], label=f"{arm} eligibility")
        expected_eligible = arm != "resident_nine_RRNS"
        if (
            row.get("eligible") is not expected_eligible
            or row.get("complete_reduced_exactness") is not True
            or row.get("resource_eligible") is not True
            or row.get("symbolic_literal_45_memory_eligible") is not expected_eligible
            or row.get("compile_and_resource_wall") is not True
            or row.get("laboratory_wall") is not True
            or row.get("RRNS_fault_contract") is not True
        ):
            raise ValueError(f"retained v3 {arm} eligibility differs")
        timed = _mapping(row.get("timed_population_walls"), label=f"{arm} walls")
        for population, elapsed_ns in walls.items():
            observed = _mapping(timed.get(population), label=f"{arm} {population} wall")
            if observed != {
                "elapsed_ns": elapsed_ns,
                "ceiling_ns": 30_000_000_000,
                "passed": True,
            }:
                raise ValueError(f"retained v3 {arm} {population} wall differs")

    observations = events["candidate_observation"]
    if len(observations) != 42 or not all(
        row.get("exact_verified") is True for row in observations
    ):
        raise ValueError("retained v3 reduced differential evidence differs")
    groups = Counter(
        (str(row.get("arm")), str(row.get("population"))) for row in observations
    )
    if groups != Counter(
        {
            (arm, population): 7
            for arm in _TIMED_WALLS
            for population in ("complete_10", "signed_12")
        }
    ):
        raise ValueError("retained v3 candidate schedule differs")


def _validate_memory_and_resources(
    events: Mapping[str, list[Mapping[str, object]]],
) -> None:
    liveness = events["symbolic_literal_45_memory_liveness"][0]
    if set(liveness) != set(_MEMORY):
        raise ValueError("retained v3 liveness domain differs")
    for arm, (peak, headroom, eligible) in _MEMORY.items():
        row = _mapping(liveness[arm], label=f"{arm} liveness row")
        live = _mapping(row.get("liveness"), label=f"{arm} liveness")
        observed_headroom = (
            int(live["device_total_bytes"])
            - int(live["device_reserve_bytes"])
            - int(live["peak_live_bytes"])
        )
        if (
            live.get("device_total_bytes") != 17_094_475_776
            or live.get("device_reserve_bytes") != 2_000_000_000
            or live.get("peak_live_bytes") != peak
            or observed_headroom != headroom
            or live.get("eligible") is not eligible
        ):
            raise ValueError(f"retained v3 {arm} liveness differs")

    resource = events["module_load_and_resource_evidence"][0]
    effective = _mapping(resource.get("effective"), label="effective resources")
    if (
        len(effective) != 16
        or not all(
            _mapping(row, label="resource row").get("eligible") is True
            for row in effective.values()
        )
        or max(int(row["registers"]) for row in effective.values()) != 72
        or max(int(row["backing_bytes"]) for row in effective.values()) != 40
        or max(int(row["spill_load_bytes"]) for row in effective.values()) != 0
        or max(int(row["spill_store_bytes"]) for row in effective.values()) != 0
    ):
        raise ValueError("retained v3 effective resources differ")


def assess_device_preflight_v3_outcome_bytes(
    raw: bytes,
) -> AssessedDevicePreflightV3Outcome:
    if type(raw) is not bytes:
        raise TypeError("retained v3 outcome reader requires immutable bytes")
    if len(raw) != RESULT_BYTES or sha256(raw).hexdigest() != RESULT_SHA256:
        raise ValueError("retained v3 outcome raw identity differs")
    assessed = assess_device_preflight_v3_bytes(raw)
    if (
        assessed.terminal != "completed_device_preflight"
        or assessed.passed is not True
        or assessed.source_commit != SOURCE_COMMIT
        or assessed.event_count != 57
        or assessed.eligible_arms
        != ("positional", "batched_five_then_four_RRNS")
        or assessed.candidate_selected is not None
        or assessed.laboratory_elapsed_ns != 19_672_450_800
        or assessed.public_elapsed_ns != 23_951_600_900
    ):
        raise ValueError("retained v3 semantic assessment differs")

    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if (
        not recovery.is_complete
        or recovery.invalid_suffix_bytes
        or len(recovery.records) != 59
        or recovery.records[0].body.kind is not JournalRecordKind.HEADER
        or recovery.records[-1].body.kind is not JournalRecordKind.TERMINAL
    ):
        raise ValueError("retained v3 outcome lifecycle differs")
    header = recovery.records[0].body.payload
    _validate_source_commit(header)

    observations = [record.body.payload for record in recovery.records[1:-1]]
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in recovery.records[1:-1]
    ):
        raise ValueError("retained v3 outcome observation kind differs")
    if Counter(str(row.get("kind")) for row in observations) != Counter(_EVENT_COUNTS):
        raise ValueError("retained v3 outcome event inventory differs")
    events: dict[str, list[Mapping[str, object]]] = {
        kind: [
            _mapping(row.get("event"), label=f"{kind} event")
            for row in observations
            if row.get("kind") == kind
        ]
        for kind in _EVENT_COUNTS
    }
    _validate_candidate_evidence(events)
    _validate_memory_and_resources(events)

    compile_event = events["compile"][0]
    command = _mapping(compile_event.get("command"), label="compile command")
    cubin = _mapping(
        events["durable_cubin_capture"][0].get("cubin"), label="cubin"
    )
    if (
        command.get("return_code") != 0
        or command.get("elapsed_ns") != 2_348_362_100
        or cubin.get("byte_count") != 634_144
        or cubin.get("sha256")
        != "cc19a8de2fc44bf576f41be365e797667cc4ec4d7afd842d7a14289c3188ac8d"
    ):
        raise ValueError("retained v3 compiled cubin evidence differs")

    laboratory = events["laboratory_partition"][0]
    if (
        laboratory.get("exact_sum") is not True
        or laboratory.get("total_ns") != 19_672_450_800
    ):
        raise ValueError("retained v3 laboratory partition differs")
    terminal = recovery.records[-1].body.payload
    if (
        terminal.get("terminal") != "completed_device_preflight"
        or terminal.get("passed") is not True
        or terminal.get("event_count") != 57
        or terminal.get("laboratory_elapsed_ns") != 19_672_450_800
        or terminal.get("laboratory_wall_ns") != 240_000_000_000
        or terminal.get("outside_laboratory_elapsed_ns") != 4_279_150_100
        or terminal.get("outside_laboratory_wall_ns") != 30_000_000_000
        or terminal.get("public_elapsed_ns") != 23_951_600_900
        or terminal.get("public_wall_ns") != 270_000_000_000
        or terminal.get("claims") != _OUTER_CLAIMS
    ):
        raise ValueError("retained v3 outer terminal differs")

    return AssessedDevicePreflightV3Outcome(
        terminal="completed_device_preflight",
        passed=True,
        source_commit=SOURCE_COMMIT,
        record_count=59,
        event_count=57,
        eligible_arms=("positional", "batched_five_then_four_RRNS"),
        ineligible_arms=("resident_nine_RRNS",),
        candidate_selected=None,
        cubin_sha256=(
            "cc19a8de2fc44bf576f41be365e797667cc4ec4d7afd842d7a14289c3188ac8d"
        ),
        cubin_bytes=634_144,
        laboratory_elapsed_ns=19_672_450_800,
        outside_laboratory_elapsed_ns=4_279_150_100,
        public_elapsed_ns=23_951_600_900,
    )


def assess_device_preflight_v3_outcome_file(
    path: Path = RESULT_PATH,
) -> AssessedDevicePreflightV3Outcome:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("retained v3 device-preflight result is absent")
    return assess_device_preflight_v3_outcome_bytes(path.read_bytes())


__all__ = [
    "AssessedDevicePreflightV3Outcome",
    "RESULT_BYTES",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "RESULT_SHA256",
    "assess_device_preflight_v3_outcome_bytes",
    "assess_device_preflight_v3_outcome_file",
]
