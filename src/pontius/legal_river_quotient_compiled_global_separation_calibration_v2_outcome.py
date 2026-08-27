"""Artifact-bound assessment of the consumed ADR-0461 calibration result."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes
from .legal_river_quotient_compiled_global_separation_calibration_v2_result import (
    CAMPAIGN_SHA256,
    PROTOCOL_SHA256,
    RESULT_PATH,
    RESULT_RELATIVE_PATH,
    assess_calibration_bytes,
)


RESULT_BYTES = 3_299_268
RESULT_SHA256 = "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d"
SOURCE_COMMIT = "08bb6857f47f9669b8f531c65079d4decd52a573"
COMPLETED_CELL_KEY = (
    "10|contract_first_direct_57_scan|positive_witness|opaque_per_source_base|"
    "exact_provenance_hit|positional"
)
FAILING_KERNEL = "direct_prices_rrns_batch"

_EVENT_COUNTS = {
    "arithmetic_admission": 1,
    "bootstrap_handshake": 1,
    "calibration_cell": 1,
    "compile": 1,
    "compile_resource_evidence": 1,
    "cuda_source_materialization": 1,
    "device_domain_prepared": 5,
    "device_memory_admission": 1,
    "durable_cubin_capture": 1,
    "fixture_authority": 1,
    "hybrid_switch_controls": 1,
    "module_load_and_runtime": 1,
    "production_base_audit": 1,
    "resource_command": 2,
    "source_contract": 1,
    "tool_versions": 1,
}


@dataclass(frozen=True, slots=True)
class AssessedCompiledCalibrationV2Outcome:
    terminal: str
    passed: bool
    source_commit: str
    record_count: int
    event_count: int
    scientific_call_count: int
    measured_call_count: int
    public_elapsed_ns: int
    cubin_sha256: str
    cubin_bytes: int
    device_name: str
    compute_capability: str
    device_total_bytes: int
    reduced_campaign_peak_bytes: int
    completed_cell_key: str
    completed_cell_primitive_ns: int
    failing_kernel: str
    failure_code: str
    candidate_selected: None
    topology_selected: None
    arithmetic_schedule_selected: None


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def assess_compiled_calibration_v2_outcome_bytes(
    raw: bytes,
) -> AssessedCompiledCalibrationV2Outcome:
    if type(raw) is not bytes:
        raise TypeError("retained calibration outcome requires immutable bytes")
    if len(raw) != RESULT_BYTES or sha256(raw).hexdigest() != RESULT_SHA256:
        raise ValueError("retained calibration raw identity differs")

    assessed = assess_calibration_bytes(raw)
    if (
        assessed.terminal != "compiled_reduced_calibration_rejected"
        or assessed.passed is not False
        or assessed.complete is not True
        or assessed.event_count != 21
        or assessed.scientific_call_count != 1
        or assessed.measured_call_count != 0
        or assessed.material_zeta_speed_claim is not None
        or assessed.production_base_classification != "producer_absent"
        or assessed.candidate_selected is not None
        or assessed.topology_selected is not None
        or assessed.arithmetic_schedule_selected is not None
        or assessed.source_commit != SOURCE_COMMIT
        or assessed.raw_sha256 != RESULT_SHA256
    ):
        raise ValueError("retained calibration semantic assessment differs")

    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if (
        not recovery.is_complete
        or recovery.invalid_suffix_bytes
        or len(recovery.records) != 23
        or recovery.records[0].body.kind is not JournalRecordKind.HEADER
        or recovery.records[-1].body.kind is not JournalRecordKind.TERMINAL
        or any(
            record.body.kind is not JournalRecordKind.OBSERVATION
            for record in recovery.records[1:-1]
        )
    ):
        raise ValueError("retained calibration lifecycle differs")

    observations = [record.body.payload for record in recovery.records[1:-1]]
    if Counter(str(row.get("kind")) for row in observations) != Counter(_EVENT_COUNTS):
        raise ValueError("retained calibration event inventory differs")
    events: dict[str, list[Mapping[str, object]]] = {
        kind: [
            _mapping(row.get("event"), label=f"{kind} event")
            for row in observations
            if row.get("kind") == kind
        ]
        for kind in _EVENT_COUNTS
    }

    compile_command = _mapping(events["compile"][0].get("command"), label="compile command")
    cubin = _mapping(
        events["durable_cubin_capture"][0].get("cubin"), label="cubin capture"
    )
    resources = events["compile_resource_evidence"][0]
    if (
        compile_command.get("return_code") != 0
        or compile_command.get("elapsed_ns") != 1_927_017_900
        or cubin.get("byte_count") != 582_880
        or cubin.get("sha256")
        != "2ee4c01232a68ae7608c3f6d1976335621dee61453f7f3b8f432fcde19c10f5b"
        or resources.get("passed") is not True
        or resources.get("spill_load_ceiling_bytes") != 0
        or resources.get("spill_store_ceiling_bytes") != 0
    ):
        raise ValueError("retained calibration compile evidence differs")

    module = events["module_load_and_runtime"][0]
    runtime = _mapping(module.get("runtime"), label="runtime")
    memory = events["device_memory_admission"][0]
    campaign = _mapping(memory.get("campaign"), label="campaign memory")
    if (
        module.get("kernel_count") != 28
        or runtime.get("device_name") != "NVIDIA GeForce RTX 5080"
        or runtime.get("compute_capability") != "120"
        or runtime.get("device_total_bytes") != 17_094_475_776
        or campaign.get("peak_bytes") != 194_402_210
        or campaign.get("ceiling_passed") is not True
        or campaign.get("reserve_passed") is not True
        or memory.get("physical_RRNS_table_arena_allocations") != 1
        or memory.get("RRNS_table_arena_channel_capacity") != 5
    ):
        raise ValueError("retained calibration device admission differs")

    cell = events["calibration_cell"][0]
    differential = _mapping(cell.get("differential"), label="cell differential")
    partition = _mapping(cell.get("phase_partition"), label="phase partition")
    cell_terminal = _mapping(cell.get("terminal"), label="cell terminal")
    if (
        cell.get("canonical_cell_key") != COMPLETED_CELL_KEY
        or cell.get("pass_index") != 0
        or cell.get("measured") is not False
        or partition.get("primitive_total_ns") != 2_126_968_200
        or differential.get("unbounded_integer_authority_matched") is not True
        or cell_terminal.get("status") != 0
        or cell_terminal.get("found_positive") != 1
        or cell_terminal.get("witness_price") != 1
    ):
        raise ValueError("retained calibration completed-cell evidence differs")

    terminal = recovery.records[-1].body.payload
    reason = terminal.get("reason")
    claims = _mapping(terminal.get("claims"), label="terminal claims")
    if (
        terminal.get("terminal") != "compiled_reduced_calibration_rejected"
        or terminal.get("passed") is not False
        or terminal.get("event_count") != 21
        or terminal.get("public_elapsed_ns") != 173_015_658_900
        or not isinstance(reason, str)
        or "_run_calibration_cell" not in reason
        or "line 4222" not in reason
        or "CUDA_ERROR_INVALID_VALUE: invalid argument" not in reason
        or claims.get("compiled_calibration_result") is not None
        or claims.get("material_zeta_speed_claim") is not None
        or claims.get("candidate_selected") is not None
        or claims.get("topology_selected") is not None
        or claims.get("arithmetic_schedule_selected") is not None
    ):
        raise ValueError("retained calibration rejecting terminal differs")

    return AssessedCompiledCalibrationV2Outcome(
        terminal="compiled_reduced_calibration_rejected",
        passed=False,
        source_commit=SOURCE_COMMIT,
        record_count=23,
        event_count=21,
        scientific_call_count=1,
        measured_call_count=0,
        public_elapsed_ns=173_015_658_900,
        cubin_sha256=(
            "2ee4c01232a68ae7608c3f6d1976335621dee61453f7f3b8f432fcde19c10f5b"
        ),
        cubin_bytes=582_880,
        device_name="NVIDIA GeForce RTX 5080",
        compute_capability="120",
        device_total_bytes=17_094_475_776,
        reduced_campaign_peak_bytes=194_402_210,
        completed_cell_key=COMPLETED_CELL_KEY,
        completed_cell_primitive_ns=2_126_968_200,
        failing_kernel=FAILING_KERNEL,
        failure_code="CUDA_ERROR_INVALID_VALUE",
        candidate_selected=None,
        topology_selected=None,
        arithmetic_schedule_selected=None,
    )


def assess_compiled_calibration_v2_outcome_file(
    path: Path = RESULT_PATH,
) -> AssessedCompiledCalibrationV2Outcome:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("retained calibration result is absent")
    return assess_compiled_calibration_v2_outcome_bytes(path.read_bytes())


__all__ = [
    "AssessedCompiledCalibrationV2Outcome",
    "COMPLETED_CELL_KEY",
    "FAILING_KERNEL",
    "RESULT_BYTES",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "RESULT_SHA256",
    "assess_compiled_calibration_v2_outcome_bytes",
    "assess_compiled_calibration_v2_outcome_file",
]
