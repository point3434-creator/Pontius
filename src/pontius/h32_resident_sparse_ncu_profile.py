"""Non-gating Nsight Compute profile of the actual h32 resident sparse pass."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

from . import h32_tier_b_opponent_batch_differential as batch_v1
from . import h32_tier_b_opponent_batch_differential_v2 as batch_v2
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-resident-sparse-ncu-profile-v1.json"
_FOLD_RESULT = (
    _ROOT / "experiments/results/h32-resident-record-to-hand-fold-v1.json"
)
_FOLD_DECISION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0212-device-record-fold-materially-speeds-both-resident-customers.md"
)
_SOURCE_RESULT = batch_v1.science._SOURCE
_WORKLOAD = _ROOT / "src/pontius/h32_resident_sparse_ncu_workload.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_sparse_ncu_profile.py"
_NCU = Path(
    "C:/Program Files/NVIDIA Corporation/Nsight Compute 2026.2.1/"
    "target/windows-desktop-win7-x64/ncu.exe"
)

_PATHS = {
    "expected_fold_result_sha256": _FOLD_RESULT,
    "expected_fold_decision_sha256": _FOLD_DECISION,
    "expected_source_result_sha256": _SOURCE_RESULT,
    "expected_batch_v2_config_sha256": batch_v2._CONFIG,
    "expected_workload_implementation_sha256": _WORKLOAD,
    "expected_profile_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_METRICS = (
    "gpu__time_duration.sum",
    "gpu__compute_memory_throughput.avg.pct_of_peak_sustained_elapsed",
    "sm__throughput.avg.pct_of_peak_sustained_elapsed",
    "gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed",
    "lts__throughput.avg.pct_of_peak_sustained_elapsed",
    "l1tex__throughput.avg.pct_of_peak_sustained_active",
    "sm__warps_active.avg.pct_of_peak_sustained_active",
    "launch__waves_per_multiprocessor",
    "launch__block_size",
    "launch__grid_size",
    "launch__registers_per_thread",
    "launch__shared_mem_per_block",
    "launch__occupancy_limit_blocks",
    "launch__occupancy_limit_registers",
    "launch__occupancy_limit_shared_mem",
    "launch__occupancy_limit_warps",
    "profiler__replayer_passes",
)

_REQUIRED_METRICS = (
    "gpu__time_duration.sum",
    "sm__throughput.avg.pct_of_peak_sustained_elapsed",
    "gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed",
    "lts__throughput.avg.pct_of_peak_sustained_elapsed",
    "l1tex__throughput.avg.pct_of_peak_sustained_active",
    "sm__warps_active.avg.pct_of_peak_sustained_active",
    "launch__waves_per_multiprocessor",
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required sparse-profile input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_resident_sparse_ncu_profile_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen, no-label hardware-counter profile."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "representative_target",
        "expected_source_belief_sha256",
        "directions",
        "feature_width",
        "workload_warmups",
        "nvtx_ranges",
        "ncu_path",
        "ncu_set",
        "ncu_replay_mode",
        "profile_timeout_seconds_per_direction",
        "dominant_duration_fraction",
        "pressure_threshold_pct",
        "pressure_ratio",
        "low_throughput_threshold_pct",
        "low_occupancy_threshold_pct",
        "low_waves_threshold",
        "classification_rule",
        "outcome_policy",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("resident sparse profile fields differ from ADR-0213")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0212_and_counter_permission_canary_before_"
            "any_h32_hardware_counter_collection"
        ),
        "representative_target": "panel_2/balanced/local_blocker_seat2_x2",
        "expected_source_belief_sha256": (
            "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289"
        ),
        "directions": ["right_to_left", "left_to_right"],
        "feature_width": 384,
        "workload_warmups": 2,
        "nvtx_ranges": {
            "right_to_left": "PONTIUS_H32_SPARSE_RIGHT_TO_LEFT_W384",
            "left_to_right": "PONTIUS_H32_SPARSE_LEFT_TO_RIGHT_W384",
        },
        "ncu_path": str(_NCU),
        "ncu_set": "basic",
        "ncu_replay_mode": "kernel",
        "profile_timeout_seconds_per_direction": 900.0,
        "dominant_duration_fraction": 0.90,
        "pressure_threshold_pct": 60.0,
        "pressure_ratio": 1.25,
        "low_throughput_threshold_pct": 50.0,
        "low_occupancy_threshold_pct": 40.0,
        "low_waves_threshold": 1.0,
        "classification_rule": (
            "duration_weight_the_minimum_kernel_prefix_covering_ninety_percent_"
            "classify_memory_if_peak_memory_is_at_least_sixty_percent_and_"
            "one_point_two_five_times_sm_compute_compute_symmetrically_"
            "classify_launch_or_occupancy_if_both_are_below_fifty_percent_and_"
            "occupancy_is_below_forty_percent_or_waves_below_one_else_mixed"
        ),
        "outcome_policy": (
            "counter_values_and_pressure_classification_are_diagnostic_not_"
            "validity_gates_and_authorize_no_strategy_gpu_purchase_or_kernel_"
            "rewrite_claim_without_a_separate_differential"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("resident sparse profile workload differs from ADR-0213")
    expected_gates = {
        "expected_directions": 2,
        "minimum_profiled_kernels_per_direction": 2,
        "maximum_gpu_pool_bytes": 12_000_000_000,
        "maximum_total_profile_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_fold_parent_passed": True,
        "require_source_parent_passed": True,
        "require_target_identity": True,
        "require_ncu_available": True,
        "require_counter_access": True,
        "require_nvtx_range_identity": True,
        "require_feature_width_identity": True,
        "require_workload_finite": True,
        "require_core_metrics_present": True,
        "require_metrics_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident sparse profile gates differ from ADR-0213")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident sparse profile source mismatch: {field}")
    v2_config = json.loads(batch_v2._CONFIG.read_text(encoding="utf-8"))
    corrected = batch_v2.parse_h32_tier_b_opponent_batch_v2_config(v2_config)
    live = corrected["base"]["live"]
    target = next(
        (row for row in live["targets"] if row["target"] == config["representative_target"]),
        None,
    )
    if target is None or target["source_belief_sha256"] != config[
        "expected_source_belief_sha256"
    ]:
        raise ValueError("resident sparse profile representative target differs")
    return {**config, "live": live}


def _numeric(value: str) -> float | None:
    stripped = value.strip().replace(",", "")
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def parse_ncu_raw_csv(text: str) -> dict[str, Any]:
    """Retain the frozen metric subset from Nsight's wide raw CSV page."""

    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith('"ID","Process ID"')),
        None,
    )
    if start is None:
        raise ValueError("Nsight output contains no raw CSV header")
    reader = csv.reader(io.StringIO("\n".join(lines[start:])))
    rows = list(reader)
    if len(rows) < 3:
        raise ValueError("Nsight raw CSV contains no kernel rows")
    header = rows[0]
    units = rows[1]
    unit_by_field = dict(zip(header, units, strict=True))
    retained = []
    for raw in rows[2:]:
        if len(raw) != len(header):
            continue
        row = dict(zip(header, raw, strict=True))
        if not row.get("ID", "").strip():
            continue
        metrics = {name: _numeric(row.get(name, "")) for name in _METRICS}
        retained.append(
            {
                "id": int(row["ID"]),
                "kernel_name": row["Kernel Name"],
                "context": int(row["Context"]),
                "stream": int(row["Stream"]),
                "block_size": row["Block Size"],
                "grid_size": row["Grid Size"],
                "device": row["Device"],
                "compute_capability": row["CC"],
                "nvtx_push_pop_range": next(
                    (
                        value
                        for key, value in row.items()
                        if "Push/Pop_Range" in key
                    ),
                    "",
                ),
                "metrics": metrics,
            }
        )
    if not retained:
        raise ValueError("Nsight raw CSV contains no retained kernels")
    return {
        "units": {name: unit_by_field.get(name, "") for name in _METRICS},
        "kernel_rows": retained,
        "raw_csv_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "raw_csv_bytes": len(text.encode("utf-8")),
        "raw_csv_lines": len(lines),
    }


def classify_kernel_pressure(
    kernel_rows: Sequence[Mapping[str, Any]],
    *,
    dominant_fraction: float,
    pressure_threshold: float,
    pressure_ratio: float,
    low_throughput: float,
    low_occupancy: float,
    low_waves: float,
) -> dict[str, Any]:
    """Classify only the duration-dominant kernel prefix under frozen rules."""

    duration_name = "gpu__time_duration.sum"
    ordered = sorted(
        kernel_rows,
        key=lambda row: float(row["metrics"].get(duration_name) or 0.0),
        reverse=True,
    )
    total = math.fsum(float(row["metrics"].get(duration_name) or 0.0) for row in ordered)
    if total <= 0.0:
        raise ValueError("Nsight kernels have no positive duration")
    dominant = []
    covered = 0.0
    for row in ordered:
        dominant.append(row)
        covered += float(row["metrics"].get(duration_name) or 0.0)
        if covered / total >= dominant_fraction:
            break

    def weighted(metric: str) -> float:
        pairs = [
            (
                float(row["metrics"][metric]),
                float(row["metrics"].get(duration_name) or 0.0),
            )
            for row in dominant
            if row["metrics"].get(metric) is not None
        ]
        if not pairs or math.fsum(weight for _, weight in pairs) <= 0.0:
            return 0.0
        return math.fsum(value * weight for value, weight in pairs) / math.fsum(
            weight for _, weight in pairs
        )

    sm = weighted("sm__throughput.avg.pct_of_peak_sustained_elapsed")
    memories = {
        "dram": weighted(
            "gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed"
        ),
        "l2": weighted("lts__throughput.avg.pct_of_peak_sustained_elapsed"),
        "l1tex": weighted("l1tex__throughput.avg.pct_of_peak_sustained_active"),
    }
    memory_name = max(memories, key=memories.get)
    memory = memories[memory_name]
    occupancy = weighted("sm__warps_active.avg.pct_of_peak_sustained_active")
    waves = weighted("launch__waves_per_multiprocessor")
    if memory >= pressure_threshold and memory >= pressure_ratio * sm:
        classification = "memory_pressure"
    elif sm >= pressure_threshold and sm >= pressure_ratio * memory:
        classification = "compute_pressure"
    elif max(sm, memory) < low_throughput and (
        occupancy < low_occupancy or waves < low_waves
    ):
        classification = "launch_or_occupancy_pressure"
    else:
        classification = "mixed_or_unresolved"
    return {
        "classification": classification,
        "profiled_kernel_count": len(ordered),
        "dominant_kernel_count": len(dominant),
        "dominant_duration_fraction": covered / total,
        "total_profiled_kernel_duration_ns": total,
        "dominant_kernel_names": [row["kernel_name"] for row in dominant],
        "duration_weighted_sm_throughput_pct": sm,
        "duration_weighted_memory_throughput_pct": memory,
        "dominant_memory_level": memory_name,
        "memory_levels_pct": memories,
        "duration_weighted_achieved_occupancy_pct": occupancy,
        "duration_weighted_waves_per_multiprocessor": waves,
    }


def _ncu_version() -> str:
    completed = subprocess.run(
        [str(_NCU), "--version"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10.0,
    )
    return " ".join((completed.stdout + " " + completed.stderr).split())


def _run_direction(
    parsed: Mapping[str, Any],
    config_path: Path,
    *,
    direction: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pontius-ncu-") as temporary:
        metadata_path = Path(temporary) / f"{direction}.json"
        range_name = parsed["nvtx_ranges"][direction]
        command = [
            str(_NCU),
            "--config-file",
            "off",
            "--target-processes",
            "application-only",
            "--replay-mode",
            str(parsed["ncu_replay_mode"]),
            "--set",
            str(parsed["ncu_set"]),
            "--apply-rules",
            "off",
            "--nvtx",
            "--nvtx-include",
            f"{range_name}]",
            "--csv",
            "--page",
            "raw",
            "--print-units",
            "base",
            "--print-fp",
            sys.executable,
            "-m",
            "pontius.h32_resident_sparse_ncu_workload",
            "--config",
            str(config_path),
            "--direction",
            direction,
            "--metadata-output",
            str(metadata_path),
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=_ROOT,
            env=os.environ.copy(),
            capture_output=True,
            check=False,
            text=True,
            timeout=float(parsed["profile_timeout_seconds_per_direction"]),
        )
        wall_seconds = time.perf_counter() - started
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.is_file()
            else None
        )
    parsed_csv = None
    parse_error = None
    try:
        parsed_csv = parse_ncu_raw_csv(completed.stdout)
    except ValueError as error:
        parse_error = str(error)
    classification = None
    if parsed_csv is not None:
        classification = classify_kernel_pressure(
            parsed_csv["kernel_rows"],
            dominant_fraction=float(parsed["dominant_duration_fraction"]),
            pressure_threshold=float(parsed["pressure_threshold_pct"]),
            pressure_ratio=float(parsed["pressure_ratio"]),
            low_throughput=float(parsed["low_throughput_threshold_pct"]),
            low_occupancy=float(parsed["low_occupancy_threshold_pct"]),
            low_waves=float(parsed["low_waves_threshold"]),
        )
    return {
        "direction": direction,
        "nvtx_range": range_name,
        "return_code": completed.returncode,
        "wall_seconds": wall_seconds,
        "counter_permission_error": "ERR_NVGPUCTRPERM" in completed.stderr,
        "stderr": completed.stderr.strip(),
        "parse_error": parse_error,
        "workload": metadata,
        "profile": parsed_csv,
        "classification": classification,
    }


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def run_h32_resident_sparse_ncu_profile(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Collect one NVTX-isolated basic counter set in each sparse direction."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_resident_sparse_ncu_profile_config(config)
    fold_parent = json.loads(_FOLD_RESULT.read_text(encoding="utf-8"))
    source_parent = json.loads(_SOURCE_RESULT.read_text(encoding="utf-8"))
    git = batch_v1._strict_git_metadata()
    _, runtime = batch_v1._validate_runtime(parsed["live"])
    if git["dirty"]:
        raise RuntimeError("resident sparse profile requires clean Git state")

    direction_rows = []
    for direction in parsed["directions"]:
        print(f"Nsight resident sparse profile: {direction}", flush=True)
        direction_rows.append(
            _run_direction(parsed, config_path, direction=direction)
        )
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    workloads = [row["workload"] for row in direction_rows if row["workload"]]
    profiles = [row["profile"] for row in direction_rows if row["profile"]]
    all_kernels = [
        kernel for profile in profiles for kernel in profile["kernel_rows"]
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "fold_parent_passed": bool(fold_parent["passed"])
        == gates_config["require_fold_parent_passed"],
        "source_parent_passed": bool(source_parent["passed"])
        == gates_config["require_source_parent_passed"],
        "direction_count": len(direction_rows) == gates_config["expected_directions"],
        "kernel_count": all(
            row["profile"] is not None
            and len(row["profile"]["kernel_rows"])
            >= gates_config["minimum_profiled_kernels_per_direction"]
            for row in direction_rows
        ),
        "target_identity": all(
            row["source_belief_sha256"] == parsed["expected_source_belief_sha256"]
            for row in workloads
        )
        == gates_config["require_target_identity"],
        "ncu_available": _NCU.is_file() == gates_config["require_ncu_available"],
        "counter_access": all(
            row["return_code"] == 0 and not row["counter_permission_error"]
            for row in direction_rows
        )
        == gates_config["require_counter_access"],
        "nvtx_range_identity": all(
            row["workload"] is not None
            and row["workload"]["nvtx_range"] == row["nvtx_range"]
            and row["profile"] is not None
            and all(
                row["nvtx_range"] in kernel["nvtx_push_pop_range"]
                for kernel in row["profile"]["kernel_rows"]
            )
            for row in direction_rows
        )
        == gates_config["require_nvtx_range_identity"],
        "feature_width_identity": all(
            row["feature_width"] == parsed["feature_width"] for row in workloads
        )
        == gates_config["require_feature_width_identity"],
        "gpu_pool": max(
            (int(row["gpu_pool_total_bytes"]) for row in workloads), default=0
        )
        <= gates_config["maximum_gpu_pool_bytes"],
        "total_profile_seconds": total_seconds
        <= gates_config["maximum_total_profile_seconds"],
        "workload_finite": all(row["finite"] for row in workloads)
        == gates_config["require_workload_finite"],
        "core_metrics_present": all(
            kernel["metrics"].get(metric) is not None
            for kernel in all_kernels
            for metric in _REQUIRED_METRICS
        )
        == gates_config["require_core_metrics_present"],
        "metrics_finite": _finite_tree(
            [kernel["metrics"] for kernel in all_kernels]
        )
        == gates_config["require_metrics_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    classifications = [
        row["classification"]["classification"]
        for row in direction_rows
        if row["classification"] is not None
    ]
    if not gates["passed"]:
        decision = "reject_resident_sparse_ncu_profile"
    elif classifications and len(set(classifications)) == 1:
        decision = f"profile_identifies_{classifications[0]}"
    else:
        decision = "profile_is_direction_mixed_or_unresolved"
    result = {
        "schema_version": 1,
        "status": "h32_resident_sparse_ncu_profile_executed",
        "methodology": {
            "representative_target": parsed["representative_target"],
            "strategy_labels_loaded": 0,
            "directions": list(parsed["directions"]),
            "feature_width": parsed["feature_width"],
            "actual_resident_csr_operators": True,
            "synthetic_dense_feature_values": True,
            "nvtx_isolated_two_spmm_pass": True,
            "counter_values_are_non_gating": True,
        },
        "environment": {
            **environment_metadata(),
            **runtime,
            "git": git,
            "ncu_path": str(_NCU),
            "ncu_version": _ncu_version(),
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "workload_implementation_sha256": _sha256(_WORKLOAD),
        "direction_rows": direction_rows,
        "aggregate": {
            "profiled_directions": len(direction_rows),
            "profiled_kernels": len(all_kernels),
            "direction_classifications": classifications,
            "median_event_elapsed_ms_diagnostic": statistics.median(
                row["event_elapsed_ms_diagnostic"] for row in workloads
            )
            if workloads
            else None,
            "maximum_gpu_pool_bytes": max(
                (int(row["gpu_pool_total_bytes"]) for row in workloads), default=0
            ),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": decision,
        "strategy_population_claim": None,
        "total_profile_seconds": total_seconds,
        "limitations": [
            "The profile covers one maximum-width sparse pass in each direction.",
            "Dense feature values are synthetic but shapes and resident CSR operators are actual.",
            "Kernel replay counter values are not ordinary wall-time measurements.",
            "The frozen classification is a diagnostic screen, not a rewrite decision.",
            "No strategy, deployment, population, GPU-purchase, or broad hardware claim is authorized.",
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_resident_sparse_ncu_profile(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
