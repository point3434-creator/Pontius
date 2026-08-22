"""Final target-process correction for the h32 resident sparse profile."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping

from . import h32_resident_sparse_ncu_profile as v1
from . import h32_resident_sparse_ncu_profile_v2 as v2


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v3.json"
_OUTPUT = _ROOT / "experiments/results/h32-resident-sparse-ncu-profile-v3.json"
_V2_RESULT = _ROOT / "experiments/results/h32-resident-sparse-ncu-profile-v2.json"
_V2_DECISION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0216-reject-second-sparse-profile-on-python-child-targeting.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_sparse_ncu_profile_v3.py"

_PATHS = {
    "expected_v1_result_sha256": v2._V1_RESULT,
    "expected_v1_rejection_sha256": v2._V1_DECISION,
    "expected_v2_config_sha256": v2._CONFIG,
    "expected_v2_implementation_sha256": v2._IMPLEMENTATION,
    "expected_v2_control_test_sha256": v2._TEST,
    "expected_v2_result_sha256": _V2_RESULT,
    "expected_v2_rejection_sha256": _V2_DECISION,
    "expected_v3_implementation_sha256": _IMPLEMENTATION,
    "expected_v3_control_test_sha256": _TEST,
}


def parse_h32_resident_sparse_ncu_profile_v3_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen child-target and raw-page correction."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_rule",
        "output_rule",
    }
    if set(config) != fields:
        raise ValueError("resident sparse profile v3 fields differ from ADR-0217")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0216_before_any_final_corrected_h32_"
            "hardware_counter_collection"
        ),
        "correction_rule": (
            "target_all_python_child_processes_and_restore_the_v1_wide_raw_"
            "page_without_per_kernel_summary"
        ),
        "output_rule": "write_only_h32_resident_sparse_ncu_profile_v3_json",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("resident sparse profile v3 correction differs from ADR-0217")
    for field, path in _PATHS.items():
        if config[field] != v1._sha256(path):
            raise ValueError(f"resident sparse profile v3 source mismatch: {field}")
    rejected = json.loads(_V2_RESULT.read_text(encoding="utf-8"))
    if rejected.get("passed") is not False or rejected.get("decision") != (
        "reject_corrected_resident_sparse_ncu_profile"
    ):
        raise ValueError("resident sparse profile v3 rejection parent differs")
    return config


def _run_direction(
    parsed: Mapping[str, Any],
    base_config_path: Path,
    *,
    direction: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pontius-ncu-v3-") as temporary:
        metadata_path = Path(temporary) / f"{direction}.json"
        range_name = parsed["nvtx_ranges"][direction]
        command = [
            str(v1._NCU),
            "--config-file",
            "off",
            "--target-processes",
            "all",
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


def run_h32_resident_sparse_ncu_profile_v3(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Run the frozen profile through the child Python target."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parse_h32_resident_sparse_ncu_profile_v3_config(config)
    original = v2._run_direction
    try:
        v2._run_direction = _run_direction
        result = v2.run_h32_resident_sparse_ncu_profile_v2(v2._CONFIG, output_path)
    finally:
        v2._run_direction = original
    result["schema_version"] = 3
    result["status"] = "h32_resident_sparse_ncu_profile_v3_executed"
    result["methodology"]["correction"] = (
        "target_all_python_children_and_restore_wide_raw_page"
    )
    result["methodology"]["rejected_v2_reused"] = False
    result["config_sha256"] = v1._sha256(config_path)
    result["implementation_sha256"] = v1._sha256(_IMPLEMENTATION)
    result["limitations"][0] = (
        "The final correction changes only Python child targeting and console-page shape."
    )
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
    result = run_h32_resident_sparse_ncu_profile_v3(args.config, args.output)
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
