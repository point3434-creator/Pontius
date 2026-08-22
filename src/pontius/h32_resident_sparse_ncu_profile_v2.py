"""Corrected h32 resident sparse profile with explicit per-kernel output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping

from . import h32_resident_sparse_ncu_profile as v1
from . import h32_tier_b_opponent_batch_differential as batch_v1
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-resident-sparse-ncu-profile-v2.json"
_V1_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v1.json"
_V1_RESULT = _ROOT / "experiments/results/h32-resident-sparse-ncu-profile-v1.json"
_V1_DECISION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0214-reject-first-resident-sparse-profile-on-empty-console-page.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_sparse_ncu_profile_v2.py"

_PATHS = {
    "expected_v1_config_sha256": _V1_CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_v1_result_sha256": _V1_RESULT,
    "expected_v1_rejection_sha256": _V1_DECISION,
    "expected_v2_implementation_sha256": _IMPLEMENTATION,
    "expected_v2_control_test_sha256": _TEST,
}


def parse_h32_resident_sparse_ncu_profile_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the one-line console-output correction and unchanged base."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_rule",
        "output_rule",
    }
    if set(config) != fields:
        raise ValueError("resident sparse profile v2 fields differ from ADR-0215")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0214_before_any_corrected_h32_hardware_"
            "counter_collection"
        ),
        "correction_rule": (
            "add_print_summary_per_kernel_require_nonempty_stdout_and_make_"
            "core_metric_presence_nonvacuous"
        ),
        "output_rule": "write_only_h32_resident_sparse_ncu_profile_v2_json",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("resident sparse profile v2 correction differs from ADR-0215")
    for field, path in _PATHS.items():
        if config[field] != v1._sha256(path):
            raise ValueError(f"resident sparse profile v2 source mismatch: {field}")
    live_base = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    rejected = json.loads(_V1_RESULT.read_text(encoding="utf-8"))
    if rejected.get("passed") is not False or rejected.get("decision") != (
        "reject_resident_sparse_ncu_profile"
    ):
        raise ValueError("resident sparse profile v2 rejection parent differs")
    parsed_base = v1.parse_h32_resident_sparse_ncu_profile_config(live_base)
    return {**config, "parsed_base": parsed_base}


def _run_direction(
    parsed: Mapping[str, Any],
    base_config_path: Path,
    *,
    direction: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pontius-ncu-v2-") as temporary:
        metadata_path = Path(temporary) / f"{direction}.json"
        range_name = parsed["nvtx_ranges"][direction]
        command = [
            str(v1._NCU),
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
            "--print-summary",
            "per-kernel",
            "--print-units",
            "base",
            "--print-fp",
            sys.executable,
            "-m",
            "pontius.h32_resident_sparse_ncu_workload",
            "--config",
            str(base_config_path),
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
        parsed_csv = v1.parse_ncu_raw_csv(completed.stdout)
    except ValueError as error:
        parse_error = str(error)
    classification = None
    if parsed_csv is not None:
        classification = v1.classify_kernel_pressure(
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
        "stdout_bytes": len(completed.stdout.encode("utf-8")),
        "counter_permission_error": "ERR_NVGPUCTRPERM" in completed.stderr,
        "stderr": completed.stderr.strip(),
        "parse_error": parse_error,
        "workload": metadata,
        "profile": parsed_csv,
        "classification": classification,
    }


def run_h32_resident_sparse_ncu_profile_v2(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Repeat only the rejected console-output path under the frozen workload."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    corrected = parse_h32_resident_sparse_ncu_profile_v2_config(config)
    parsed = corrected["parsed_base"]
    fold_parent = json.loads(v1._FOLD_RESULT.read_text(encoding="utf-8"))
    source_parent = json.loads(v1._SOURCE_RESULT.read_text(encoding="utf-8"))
    git = batch_v1._strict_git_metadata()
    _, runtime = batch_v1._validate_runtime(parsed["live"])
    if git["dirty"]:
        raise RuntimeError("resident sparse profile v2 requires clean Git state")

    rows = []
    for direction in parsed["directions"]:
        print(f"Nsight resident sparse profile v2: {direction}", flush=True)
        rows.append(_run_direction(parsed, _V1_CONFIG, direction=direction))
    total_seconds = time.perf_counter() - started
    gate_config = parsed["gates"]
    workloads = [row["workload"] for row in rows if row["workload"]]
    profiles = [row["profile"] for row in rows if row["profile"]]
    kernels = [kernel for profile in profiles for kernel in profile["kernel_rows"]]
    gates = {
        "clean_git": (not git["dirty"]) == gate_config["require_clean_git_state"],
        "fold_parent_passed": bool(fold_parent["passed"])
        == gate_config["require_fold_parent_passed"],
        "source_parent_passed": bool(source_parent["passed"])
        == gate_config["require_source_parent_passed"],
        "direction_count": len(rows) == gate_config["expected_directions"],
        "stdout_nonempty": all(row["stdout_bytes"] > 0 for row in rows),
        "kernel_count": all(
            row["profile"] is not None
            and len(row["profile"]["kernel_rows"])
            >= gate_config["minimum_profiled_kernels_per_direction"]
            for row in rows
        ),
        "target_identity": len(workloads) == len(rows)
        and all(
            row["source_belief_sha256"] == parsed["expected_source_belief_sha256"]
            for row in workloads
        )
        == gate_config["require_target_identity"],
        "ncu_available": v1._NCU.is_file() == gate_config["require_ncu_available"],
        "counter_access": all(
            row["return_code"] == 0 and not row["counter_permission_error"]
            for row in rows
        )
        == gate_config["require_counter_access"],
        "nvtx_range_identity": all(
            row["workload"] is not None
            and row["workload"]["nvtx_range"] == row["nvtx_range"]
            and row["profile"] is not None
            and all(
                row["nvtx_range"] in kernel["nvtx_push_pop_range"]
                for kernel in row["profile"]["kernel_rows"]
            )
            for row in rows
        )
        == gate_config["require_nvtx_range_identity"],
        "feature_width_identity": len(workloads) == len(rows)
        and all(row["feature_width"] == parsed["feature_width"] for row in workloads)
        == gate_config["require_feature_width_identity"],
        "gpu_pool": max(
            (int(row["gpu_pool_total_bytes"]) for row in workloads), default=0
        )
        <= gate_config["maximum_gpu_pool_bytes"],
        "total_profile_seconds": total_seconds
        <= gate_config["maximum_total_profile_seconds"],
        "workload_finite": len(workloads) == len(rows)
        and all(row["finite"] for row in workloads)
        == gate_config["require_workload_finite"],
        "core_metrics_present": bool(kernels)
        and all(
            kernel["metrics"].get(metric) is not None
            for kernel in kernels
            for metric in v1._REQUIRED_METRICS
        )
        == gate_config["require_core_metrics_present"],
        "metrics_finite": bool(kernels)
        and v1._finite_tree([kernel["metrics"] for kernel in kernels])
        == gate_config["require_metrics_finite"],
        "strategy_population_claim_null": True
        == gate_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    classifications = [
        row["classification"]["classification"]
        for row in rows
        if row["classification"] is not None
    ]
    if not gates["passed"]:
        decision = "reject_corrected_resident_sparse_ncu_profile"
    elif classifications and len(set(classifications)) == 1:
        decision = f"profile_identifies_{classifications[0]}"
    else:
        decision = "profile_is_direction_mixed_or_unresolved"
    result = {
        "schema_version": 2,
        "status": "h32_resident_sparse_ncu_profile_v2_executed",
        "methodology": {
            "correction": "explicit_print_summary_per_kernel",
            "rejected_v1_reused": False,
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
            "ncu_path": str(v1._NCU),
            "ncu_version": v1._ncu_version(),
        },
        "config_sha256": v1._sha256(config_path),
        "implementation_sha256": v1._sha256(_IMPLEMENTATION),
        "direction_rows": rows,
        "aggregate": {
            "profiled_directions": len(rows),
            "profiled_kernels": len(kernels),
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
            "The corrected run changes only console-page emission and empty-evidence gates.",
            "The profile covers one maximum-width sparse pass in each direction.",
            "Dense values are synthetic but resident CSR operators and shapes are actual.",
            "Kernel replay counter values are not ordinary wall-time measurements.",
            "The classifier is diagnostic and authorizes no rewrite by itself.",
            "No strategy, deployment, population, GPU-purchase, or hardware claim is authorized.",
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
    result = run_h32_resident_sparse_ncu_profile_v2(args.config, args.output)
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
