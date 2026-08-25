"""Typed-telemetry successor to the closed ADR-0363 capacity owner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from . import full_width_river_capacity_preflight as v1
from .runner_harness_v2 import load_config
from .windows_process_memory import (
    typed_memory_telemetry_control,
    typed_windows_memory_snapshot,
)

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/full-width-river-capacity-preflight-v2.json"
_OUTPUT = _ROOT / "experiments/results/full-width-river-capacity-preflight-v2.json"
_V1_CONFIG = _ROOT / "experiments/configs/full-width-river-capacity-preflight-v1.json"
_V1_RESULT = _ROOT / "experiments/results/full-width-river-capacity-preflight-v1.json"
_V1_RUNNER = _ROOT / "src/pontius/full_width_river_capacity_preflight.py"
_ALLOCATION_MODEL = _ROOT / "src/pontius/full_width_factor_tt_capacity.py"
_MEMORY_TELEMETRY = _ROOT / "src/pontius/windows_process_memory.py"
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests/test_full_width_river_capacity_preflight_v2.py"
_MEMORY_CONTROL_TEST = _ROOT / "tests/test_windows_process_memory.py"
_PARENT_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0364-retain-the-full-width-capacity-telemetry-failure.md"
)

_CANONICAL_PATHS = {
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_v1_config_sha256": _V1_CONFIG,
    "expected_v1_runner_sha256": _V1_RUNNER,
    "expected_allocation_model_sha256": _ALLOCATION_MODEL,
    "expected_memory_telemetry_sha256": _MEMORY_TELEMETRY,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _CONTROL_TEST,
    "expected_memory_control_test_sha256": _MEMORY_CONTROL_TEST,
}
_LITERAL_PATHS = {"expected_v1_result_sha256": _V1_RESULT}


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"v2 capacity provenance path is absent: {path}")
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _literal_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"v2 capacity retained artifact is absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _parse_config(config: Mapping[str, Any]) -> dict[str, Any]:
    plain = _plain(config)
    expected_fields = {
        "schema_version",
        "evidence_stage",
        "hash_semantics",
        *_CANONICAL_PATHS,
        *_LITERAL_PATHS,
        "target_semantics",
        "telemetry_contract",
        "maximum_process_memory_cross_source_delta_bytes",
        "required_process_counter_struct_bytes",
        "maximum_result_bytes",
        "require_clean_git_state",
        "require_v1_terminal_typed_failure",
        "require_v1_target_absent",
        "require_typed_telemetry_control",
        "require_unchanged_v1_target_semantics",
        "require_zero_actions_strategy_labels_and_quality_rows",
    }
    if set(plain) != expected_fields:
        raise ValueError("v2 full-width capacity config fields differ from ADR-0365")
    for field, path in _CANONICAL_PATHS.items():
        if plain[field] != _canonical_lf_sha256(path):
            raise ValueError(f"v2 full-width capacity provenance mismatch: {field}")
    for field, path in _LITERAL_PATHS.items():
        if plain[field] != _literal_sha256(path):
            raise ValueError(f"v2 full-width capacity artifact mismatch: {field}")

    frozen = {
        "schema_version": "full-width-river-capacity-preflight-v2-config-v1",
        "evidence_stage": (
            "source_sealed_after_adr0364_before_any_v2_live_literal_full_width_"
            "hardware_capacity_invocation"
        ),
        "hash_semantics": (
            "canonical_lf_for_text_sources_literal_sha256_for_retained_v1_result"
        ),
        "target_semantics": (
            "exact_adr0363_target_unchanged_only_windows_process_memory_abi_replaced"
        ),
        "telemetry_contract": (
            "explicit_win64_signatures_psapi_kernel32_and_powershell_sampling_control"
        ),
        "maximum_process_memory_cross_source_delta_bytes": 536_870_912,
        "required_process_counter_struct_bytes": 80,
        "maximum_result_bytes": 1_048_576,
        "require_clean_git_state": True,
        "require_v1_terminal_typed_failure": True,
        "require_v1_target_absent": True,
        "require_typed_telemetry_control": True,
        "require_unchanged_v1_target_semantics": True,
        "require_zero_actions_strategy_labels_and_quality_rows": True,
    }
    for field, expected in frozen.items():
        if plain[field] != expected:
            raise ValueError(f"v2 full-width capacity field differs: {field}")

    v1_config = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    parsed_v1 = v1._parse_config(v1_config)
    v1_result = json.loads(_V1_RESULT.read_text(encoding="utf-8"))
    if (
        v1_result.get("terminal") != "typed_failure"
        or v1_result.get("passed") is not False
        or v1_result.get("failure")
        != {"message": "GetProcessMemoryInfo failed", "type": "OSError"}
    ):
        raise ValueError("v2 parent is not the exact retained telemetry failure")
    if any(
        field in v1_result
        for field in (
            "control",
            "target",
            "runtime_at_target_admission",
            "campaign_wall_seconds",
        )
    ):
        raise ValueError("v2 parent unexpectedly contains capacity payload")
    return {**plain, "v1": parsed_v1}


def _strict_git_metadata() -> dict[str, object]:
    def checked(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"v2 strict Git metadata failed: {message}")
        return result.stdout.strip()

    commit = checked("rev-parse", "HEAD")
    status = checked("status", "--porcelain=v1", "--untracked-files=all")
    return {"commit": commit, "dirty": bool(status), "strict_status": True}


def _runtime_snapshot(
    parsed: Mapping[str, Any],
) -> tuple[Any, dict[str, object], dict[str, object]]:
    import scipy

    v1_config = parsed["v1"]
    telemetry = typed_memory_telemetry_control(
        maximum_delta_bytes=parsed[
            "maximum_process_memory_cross_source_delta_bytes"
        ]
    )
    if not telemetry["passed"]:
        raise RuntimeError("typed Windows memory telemetry control rejected")
    snapshot = telemetry["snapshot"]
    if (
        snapshot["process_counter_struct_bytes"]
        != parsed["required_process_counter_struct_bytes"]
    ):
        raise RuntimeError("Windows process-memory structure size drifted")
    cp, _ = v1._cupy_modules()
    device_name = cp.cuda.runtime.getDeviceProperties(0)["name"]
    if isinstance(device_name, bytes):
        device_name = device_name.decode("ascii")
    runtime = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": cp.__version__,
        "cuda_runtime": int(cp.cuda.runtime.runtimeGetVersion()),
        "cuda_driver": int(cp.cuda.runtime.driverGetVersion()),
        "compute_capability": str(cp.cuda.Device(0).compute_capability),
        "device_name": str(device_name),
    }
    required_equal = {
        "numpy": v1_config["required_numpy_version"],
        "scipy": v1_config["required_scipy_version"],
        "cupy": v1_config["required_cupy_version"],
        "cuda_runtime": v1_config["required_cuda_runtime_version"],
        "compute_capability": v1_config["required_compute_capability"],
        "device_name": v1_config["required_device_name"],
    }
    for field, expected in required_equal.items():
        if runtime[field] != expected:
            raise RuntimeError(f"v2 full-width capacity runtime differs: {field}")
    if runtime["cuda_driver"] < v1_config["minimum_cuda_driver_version"]:
        raise RuntimeError("CUDA driver is below the v2 full-width capacity floor")
    free, total = cp.cuda.runtime.memGetInfo()
    return (
        cp,
        {
            **runtime,
            **{
                key: value
                for key, value in snapshot.items()
                if key not in {"psapi", "kernel32"}
            },
            "device_free_bytes": int(free),
            "device_total_bytes": int(total),
        },
        telemetry,
    )


def run_full_width_river_capacity_preflight_v2(
    config: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, object]:
    parsed = _parse_config(config)
    v1_config = parsed["v1"]
    if parsed["require_clean_git_state"] and git.get("dirty") is not False:
        raise RuntimeError("v2 full-width capacity target requires a clean Git state")
    campaign_started = time.perf_counter()
    cp, runtime, telemetry = _runtime_snapshot(parsed)
    gates_config = v1_config["gates"]
    hardware_gate = bool(
        gates_config["minimum_host_total_bytes"]
        <= runtime["host_total_physical_bytes"]
        <= gates_config["maximum_host_total_bytes"]
        and gates_config["minimum_device_total_bytes"]
        <= runtime["device_total_bytes"]
        <= gates_config["maximum_device_total_bytes"]
    )
    if not hardware_gate:
        raise RuntimeError("v2 full-width capacity hardware differs from frozen host")

    control = v1._small_control(v1_config)
    v1.release_cupy_memory_pool()
    free, total = cp.cuda.runtime.memGetInfo()
    refreshed = typed_windows_memory_snapshot()
    runtime = {
        **runtime,
        **{
            key: value
            for key, value in refreshed.items()
            if key not in {"psapi", "kernel32"}
        },
        "device_free_bytes": int(free),
        "device_total_bytes": int(total),
    }
    target = v1._run_target(v1_config, runtime=runtime, control=control)
    final_memory = typed_windows_memory_snapshot()
    device_free, device_total = cp.cuda.runtime.memGetInfo()
    campaign_seconds = time.perf_counter() - campaign_started
    emissions = {
        "actions": 0,
        "strategy_labels": 0,
        "strategy_quality_rows": 0,
        "quality_claim": None,
    }
    protocol_gates = {
        "clean_git_state": git.get("dirty") is False,
        "frozen_hardware": hardware_gate,
        "typed_memory_telemetry_control": telemetry["passed"],
        "target_gates": target["gates_passed"],
        "campaign_within_bound": (
            campaign_seconds <= gates_config["maximum_campaign_seconds"]
        ),
        "zero_actions_strategy_labels_and_quality_rows": emissions
        == {
            "actions": 0,
            "strategy_labels": 0,
            "strategy_quality_rows": 0,
            "quality_claim": None,
        },
        "finite": math.isfinite(campaign_seconds),
    }
    return {
        "schema_version": "full-width-river-capacity-preflight-v2-result-v1",
        "experiment_type": (
            "label_free_literal_full_width_river_capacity_preflight_v2"
        ),
        "evidence_stage": parsed["evidence_stage"],
        "source_commit": git["commit"],
        "source_dirty": git["dirty"],
        "parent_v1_result_sha256": parsed["expected_v1_result_sha256"],
        "target_semantics": parsed["target_semantics"],
        "telemetry_contract": parsed["telemetry_contract"],
        "runtime_at_target_admission": runtime,
        "typed_memory_telemetry_control": telemetry,
        "final_memory": {
            **{
                key: value
                for key, value in final_memory.items()
                if key not in {"psapi", "kernel32"}
            },
            "device_free_bytes": int(device_free),
            "device_total_bytes": int(device_total),
        },
        "control": control,
        "target": target,
        "campaign_wall_seconds": campaign_seconds,
        "emissions": emissions,
        "claims": {
            "capacity_admitted": target["capacity_admitted"],
            "representation_result_only": True,
            "strategy_quality_prior": None,
            "action_clock_claim": (
                "one_warm_contraction_only_if_executed_not_a_complete_decision_"
                "iteration_or_solve"
            ),
            "certified_truncation_authorized": False,
        },
        "gates": protocol_gates,
        "passed": all(protocol_gates.values()),
    }


def _write_exclusive(path: Path, rendered: bytes, *, maximum_bytes: int) -> None:
    if len(rendered) > maximum_bytes:
        raise ValueError("v2 full-width capacity result exceeds byte ceiling")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def _typed_failure_result(
    error: Exception,
    *,
    git: Mapping[str, Any],
    evidence_stage: str,
) -> dict[str, object]:
    return {
        "schema_version": "full-width-river-capacity-preflight-v2-result-v1",
        "experiment_type": (
            "label_free_literal_full_width_river_capacity_preflight_v2"
        ),
        "evidence_stage": evidence_stage,
        "source_commit": git["commit"],
        "source_dirty": git["dirty"],
        "terminal": "typed_failure",
        "failure": {"type": type(error).__name__, "message": str(error)},
        "emissions": {
            "actions": 0,
            "strategy_labels": 0,
            "strategy_quality_rows": 0,
            "quality_claim": None,
        },
        "passed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    if arguments.config.resolve() != _CONFIG.resolve():
        raise ValueError("v2 full-width capacity config path is frozen")
    if arguments.output.resolve() != _OUTPUT.resolve():
        raise ValueError("v2 full-width capacity output path is frozen")
    loaded = load_config(
        arguments.config,
        schema_validator=lambda payload: _parse_config(payload),
        maximum_bytes=1_048_576,
    )
    git = _strict_git_metadata()
    parsed = _parse_config(loaded.payload)
    failed = False
    try:
        result = run_full_width_river_capacity_preflight_v2(
            loaded.payload,
            git=git,
        )
    except Exception as error:  # noqa: BLE001 - first v2 target failure is evidence
        failed = True
        result = _typed_failure_result(
            error,
            git=git,
            evidence_stage=parsed["evidence_stage"],
        )
    result["config_sha256"] = loaded.sha256
    result["implementation_sha256"] = _canonical_lf_sha256(_IMPLEMENTATION)
    rendered = (
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _write_exclusive(
        arguments.output,
        rendered,
        maximum_bytes=parsed["maximum_result_bytes"],
    )
    if failed:
        print(
            "full-width river capacity preflight v2: "
            f"passed=False terminal={result['terminal']}"
        )
        raise SystemExit(1)
    print(
        "full-width river capacity preflight v2: "
        f"passed={result['passed']} "
        f"capacity_admitted={result['target']['capacity_admitted']} "
        f"terminal={result['target']['terminal']}"
    )


if __name__ == "__main__":
    main()


__all__ = [
    "_parse_config",
    "_runtime_snapshot",
    "_typed_failure_result",
    "_write_exclusive",
    "run_full_width_river_capacity_preflight_v2",
]
