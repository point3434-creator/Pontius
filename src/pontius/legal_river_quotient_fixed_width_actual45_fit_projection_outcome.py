"""Artifact-bound outcome assessor for the consumed ADR-0451 projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .legal_river_quotient_fixed_width_actual45_fit_projection_result import (
    ARMS,
    INPUT_PATH,
    RESULT_PATH,
    rebind_projection_result_bytes,
)


RESULT_BYTES = 55_997
RESULT_SHA256 = "afebfee99349d1e36077084619fc213dbe2b8eee8da8fe8a55c62cc41b0ececa"
SOURCE_COMMIT = "d6f85ac9d95bf87149e9c411b2ec81bae86977ba"
TERMINAL = "projection_rejected_before_target_allocation"
EXPECTED_ARMS = {
    "positional": {
        "runtime_component_projection_ns": 3_186_554_546_230,
        "laboratory_validation_projection_ns": 79_733_044_478,
        "complete_laboratory_projection_ns": 3_266_287_590_708,
        "component_ceiling_ns": 14_000_000_000,
        "component_wall_passed": False,
        "projection_eligible": False,
        "symbolic_memory": {
            "peak_live_bytes": 13_265_364_040,
            "headroom_after_reserve_bytes": 1_829_111_736,
            "eligible": True,
            "live_allocation": None,
        },
        "dominant_runtime_phase": (
            "adjoint_streamed_global_scan_and_scalar_contract",
            2_890_023_432_000,
        ),
    },
    "batched_five_then_four_RRNS": {
        "runtime_component_projection_ns": 9_908_352_862_122,
        "laboratory_validation_projection_ns": 482_477_634_835,
        "complete_laboratory_projection_ns": 10_390_830_496_957,
        "component_ceiling_ns": 14_000_000_000,
        "component_wall_passed": False,
        "projection_eligible": False,
        "symbolic_memory": {
            "peak_live_bytes": 13_275_877_664,
            "headroom_after_reserve_bytes": 1_818_598_112,
            "eligible": True,
            "live_allocation": None,
        },
        "dominant_runtime_phase": (
            "second_batch_adjoint_streamed_global_scan_and_scalar_contract",
            5_111_530_368_000,
        ),
    },
}


@dataclass(frozen=True, slots=True)
class AssessedFitProjectionOutcome:
    source_commit: str
    terminal: str
    eligible_arms: tuple[str, ...]
    candidate_selected: None
    runtime_component_projection_ns: tuple[tuple[str, int], ...]
    component_ceiling_ns: int


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"fit-projection outcome {label} must be an object")
    return value


def assess_fit_projection_outcome_bytes(
    result_raw: bytes,
    input_raw: bytes,
) -> AssessedFitProjectionOutcome:
    if type(result_raw) is not bytes or type(input_raw) is not bytes:
        raise TypeError("fit-projection outcome requires immutable bytes")
    if len(result_raw) != RESULT_BYTES or sha256(result_raw).hexdigest() != RESULT_SHA256:
        raise ValueError("fit-projection outcome result identity differs")
    rebound = rebind_projection_result_bytes(result_raw, input_raw)
    if (
        rebound.source_commit != SOURCE_COMMIT
        or rebound.terminal != TERMINAL
        or rebound.eligible_arms
        or rebound.candidate_selected is not None
    ):
        raise ValueError("fit-projection rebound outcome differs")
    document = json.loads(result_raw)
    projection = _mapping(document.get("projection"), label="projection")
    if (
        projection.get("terminal") != TERMINAL
        or projection.get("projection_eligible_arms") != []
        or projection.get("candidate_selected") is not None
    ):
        raise ValueError("fit-projection stored terminal differs")
    arm_rows = _mapping(projection.get("arms"), label="arms")
    if set(arm_rows) != set(ARMS):
        raise ValueError("fit-projection outcome arm domain differs")
    for arm, expected in EXPECTED_ARMS.items():
        observed = _mapping(arm_rows.get(arm), label=f"{arm} row")
        for field in (
            "runtime_component_projection_ns",
            "laboratory_validation_projection_ns",
            "complete_laboratory_projection_ns",
            "component_ceiling_ns",
            "component_wall_passed",
            "projection_eligible",
        ):
            if observed.get(field) != expected[field]:
                raise ValueError(f"fit-projection outcome {arm} {field} differs")
        if _mapping(observed.get("symbolic_memory"), label=f"{arm} memory") != expected["symbolic_memory"]:
            raise ValueError(f"fit-projection outcome {arm} memory differs")
        phases = observed.get("phase_projections")
        if not isinstance(phases, list):
            raise ValueError(f"fit-projection outcome {arm} phases differ")
        runtime = [
            _mapping(row, label=f"{arm} phase")
            for row in phases
            if isinstance(row, Mapping) and row.get("classification") == "runtime_component"
        ]
        dominant = max(runtime, key=lambda row: int(row["phase_upper_ns"]))
        if (
            dominant.get("phase"),
            dominant.get("phase_upper_ns"),
        ) != expected["dominant_runtime_phase"]:
            raise ValueError(f"fit-projection outcome {arm} dominant phase differs")
    return AssessedFitProjectionOutcome(
        SOURCE_COMMIT,
        TERMINAL,
        (),
        None,
        tuple(
            (
                arm,
                int(EXPECTED_ARMS[arm]["runtime_component_projection_ns"]),
            )
            for arm in ARMS
        ),
        14_000_000_000,
    )


def assess_fit_projection_outcome_file(
    result_path: Path = RESULT_PATH,
    input_path: Path = INPUT_PATH,
) -> AssessedFitProjectionOutcome:
    if result_path != RESULT_PATH or input_path != INPUT_PATH:
        raise ValueError("fit-projection outcome path differs")
    return assess_fit_projection_outcome_bytes(
        result_path.read_bytes(),
        input_path.read_bytes(),
    )


__all__ = [
    "AssessedFitProjectionOutcome",
    "EXPECTED_ARMS",
    "RESULT_BYTES",
    "RESULT_SHA256",
    "SOURCE_COMMIT",
    "TERMINAL",
    "assess_fit_projection_outcome_bytes",
    "assess_fit_projection_outcome_file",
]
