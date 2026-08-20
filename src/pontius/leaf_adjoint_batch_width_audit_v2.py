"""Run the corrected restored-step h32 terminal batch-width screen."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from . import leaf_adjoint_batch_width_audit as _v1
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .reporting import environment_metadata
from .river import parse_cards

_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "leaf-adjoint-batch-width-audit-v2.json"
)
_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_REJECTED_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "leaf_adjoint_batch_width_audit.py"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_checkpoint_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_heterogeneous_leaf_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_sparse_incidence_sha256",
    "expected_structured_showdown_sha256",
    "expected_rejected_audit_implementation_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "wide_hands_per_player",
    "range_families",
    "solver_variant",
    "source_iteration",
    "result_iteration",
    "warmup_width",
    "width_schedule",
    "selection_rule",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}
_GATE_FIELDS = set(_v1._GATE_FIELDS)
_SOURCE_PATHS = {
    "expected_checkpoint_source_sha256": _SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_axis_checkpoint_sha256": (
        _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py"
    ),
    "expected_base_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_heterogeneous_leaf_sha256": (
        _ROOT / "src" / "pontius" / "heterogeneous_leaf_contraction.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py"
    ),
    "expected_structured_showdown_sha256": (
        _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
    ),
    "expected_rejected_audit_implementation_sha256": _REJECTED_IMPLEMENTATION,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_leaf_adjoint_batch_width_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "corrected batch-width fields differ from ADR-0095: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0093_post_balanced_cleanup_rejection_"
            "before_any_row_values_or_blocker_execution"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "solver_variant": "dcfr",
        "source_iteration": 32,
        "result_iteration": 33,
        "warmup_width": 384,
        "width_schedule": [384, 768, 1536, 1536, 768, 384],
        "selection_rule": (
            "minimum_sum_family_median_step_ms_ties_smaller_width"
        ),
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("corrected batch-width workload differs from ADR-0095")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_rows": 12,
        "expected_repeats_per_width_per_family": 2,
        "require_exact_source_state_identity": True,
        "maximum_regret_accumulator_error": 1e-9,
        "maximum_strategy_sum_accumulator_error": 1e-9,
        "maximum_current_policy_probability_error": 1e-9,
        "maximum_average_policy_probability_error": 1e-9,
        "maximum_current_policy_mean_tv": 1e-10,
        "maximum_average_policy_mean_tv": 1e-10,
        "minimum_selected_batch_reduction": 2.0,
        "minimum_selected_pooled_step_speedup": 1.10,
        "maximum_step_ms": 60_000.0,
        "maximum_host_peak_numeric_bytes": 8_000_000_000,
        "maximum_gpu_pool_bytes": 12_000_000_000,
        "require_trace_batch_identity": True,
        "require_monotone_batch_counts": True,
        "require_finite_outputs": True,
        "maximum_total_audit_seconds": 900.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("corrected batch-width gates differ from ADR-0095")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "width_schedule": tuple(config["width_schedule"]),
        "gates": dict(gates),
    }


def _measure_family_schedule(
    *,
    parsed: dict[str, Any],
    family: str,
    belief: Any,
    topology: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
    source_state: dict[str, Any],
    workspace_timing: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return compact warmup and measured rows across the complete schedule."""

    warmup = _v1._run_restored_step(
        parsed=parsed,
        belief=belief,
        topology=topology,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        gpu=gpu,
        source_state=source_state,
        width=parsed["warmup_width"],
    )
    compact_warmup = {
        key: value for key, value in warmup.items() if not key.startswith("_")
    } | {
        "range_family": family,
        "workspace_timing": workspace_timing,
        "gpu_operator_upload_ms": gpu.upload_ms,
    }
    del warmup

    rows = []
    repeat_counts: Counter[int] = Counter()
    reference = None
    for schedule_index, width in enumerate(parsed["width_schedule"]):
        gc.collect()
        row = _v1._run_restored_step(
            parsed=parsed,
            belief=belief,
            topology=topology,
            workspace=workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            source_state=source_state,
            width=width,
        )
        repeat_counts[width] += 1
        row["range_family"] = family
        row["schedule_index"] = schedule_index
        row["repeat_index_for_width"] = repeat_counts[width]
        if reference is None:
            if width != parsed["warmup_width"]:
                raise AssertionError("first measured width is not the baseline")
            reference = {
                key: row[key]
                for key in ("_regrets", "_strategy_sums", "_current", "_average")
            }
        _v1._attach_reference_errors(row, reference)
        rows.append(row)
    return compact_warmup, rows


def _source_state(
    source: dict[str, Any],
    *,
    family: str,
    iteration: int,
) -> tuple[dict[str, Any], bool]:
    source_row = next(
        row for row in source["wide_rows"] if row["range_family"] == family
    )
    checkpoint = next(
        row
        for row in source_row["checkpoints"]
        if int(row["iteration"]) == iteration
    )
    state = checkpoint["state"]
    identity = (
        axis_cfr_checkpoint_digest(state) == checkpoint["state_sha256"]
        and checkpoint["state_sha256"] == source_row["final_state_sha256"]
        and state["iteration"] == iteration
        and state["current_policy_sha256"] == checkpoint["current_policy_sha256"]
        and state["average_policy_sha256"] == checkpoint["average_policy_sha256"]
    )
    return state, identity


def run_leaf_adjoint_batch_width_v2_audit(
    config: dict[str, Any],
) -> dict[str, object]:
    parsed = parse_leaf_adjoint_batch_width_v2_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0095")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0095")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0095")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0095")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0095 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0095")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    started = time.perf_counter()
    source = json.loads(_SOURCE.read_text(encoding="utf-8"))
    board = parse_cards(*parsed["board"])
    rows = []
    warmups = []
    source_identity = True
    scheduled_widths = tuple(sorted(set(parsed["width_schedule"])))
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        belief, topology, sparse, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=parsed["wide_hands_per_player"],
            family=family,
        )
        workspace, workspace_timing, automata = retained
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        state, family_identity = _source_state(
            source,
            family=family,
            iteration=parsed["source_iteration"],
        )
        source_identity = source_identity and family_identity
        if not family_identity:
            raise AssertionError("ADR-0095 source state identity rejected")
        warmup, family_rows = _measure_family_schedule(
            parsed=parsed,
            family=family,
            belief=belief,
            topology=topology,
            workspace=workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            source_state=state,
            workspace_timing=workspace_timing,
        )
        warmups.append(warmup)
        rows.extend(family_rows)
        del gpu, automata, workspace, sparse, topology, belief
        gc.collect()

    summaries, selected_width, pooled_speedup = _v1._width_summaries(
        rows,
        families=parsed["range_families"],
        widths=scheduled_widths,
    )
    gates = parsed["gates"]
    selected = [
        row for row in summaries if int(row["width"]) == selected_width
    ]
    maximum_regret_error = max(float(row["regret_accumulator_error"]) for row in rows)
    maximum_sum_error = max(
        float(row["strategy_sum_accumulator_error"]) for row in rows
    )
    maximum_current_error = max(
        float(row["current_policy_probability_error"]) for row in rows
    )
    maximum_average_error = max(
        float(row["average_policy_probability_error"]) for row in rows
    )
    maximum_current_tv = max(float(row["current_policy_mean_tv"]) for row in rows)
    maximum_average_tv = max(float(row["average_policy_mean_tv"]) for row in rows)
    maximum_step = max(float(row["step_wall_ms"]) for row in rows)
    maximum_host = max(int(row["maximum_host_peak_numeric_bytes"]) for row in rows)
    maximum_gpu = max(int(row["maximum_gpu_pool_bytes"]) for row in rows)
    selected_batch_reduction = min(
        float(row["batch_reduction_over_384"]) for row in selected
    )
    monotone_batches = all(
        all(
            earlier["sparse_batches"] > later["sparse_batches"]
            for earlier, later in zip(family_rows, family_rows[1:])
        )
        for family in parsed["range_families"]
        for family_rows in [
            sorted(
                (row for row in summaries if row["range_family"] == family),
                key=lambda row: int(row["width"]),
            )
        ]
    )
    trace_batch_identity = all(
        int(row["transform_calls"]) == int(row["reported_sparse_batches"])
        for row in rows
    )
    finite = all(bool(row["finite"]) for row in rows) and all(
        math.isfinite(float(value))
        for row in rows
        for key, value in row.items()
        if key.endswith("_ms") or key.endswith("_error") or key.endswith("_tv")
    )
    aggregate = {
        "selected_width": selected_width,
        "selected_pooled_step_speedup": pooled_speedup,
        "selected_minimum_batch_reduction": selected_batch_reduction,
        "maximum_regret_accumulator_error": maximum_regret_error,
        "maximum_strategy_sum_accumulator_error": maximum_sum_error,
        "maximum_current_policy_probability_error": maximum_current_error,
        "maximum_average_policy_probability_error": maximum_average_error,
        "maximum_current_policy_mean_tv": maximum_current_tv,
        "maximum_average_policy_mean_tv": maximum_average_tv,
        "maximum_step_ms": maximum_step,
        "maximum_host_peak_numeric_bytes": maximum_host,
        "maximum_gpu_pool_bytes": maximum_gpu,
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results = {
        "row_count": len(rows) == gates["expected_rows"],
        "repeat_count": all(
            sum(
                row["range_family"] == family and int(row["width"]) == width
                for row in rows
            )
            == gates["expected_repeats_per_width_per_family"]
            for family in parsed["range_families"]
            for width in scheduled_widths
        ),
        "source_state_identity": source_identity
        == gates["require_exact_source_state_identity"],
        "regret_accumulator_agreement": maximum_regret_error
        <= gates["maximum_regret_accumulator_error"],
        "strategy_sum_accumulator_agreement": maximum_sum_error
        <= gates["maximum_strategy_sum_accumulator_error"],
        "current_policy_probability_agreement": maximum_current_error
        <= gates["maximum_current_policy_probability_error"],
        "average_policy_probability_agreement": maximum_average_error
        <= gates["maximum_average_policy_probability_error"],
        "current_policy_tv_agreement": maximum_current_tv
        <= gates["maximum_current_policy_mean_tv"],
        "average_policy_tv_agreement": maximum_average_tv
        <= gates["maximum_average_policy_mean_tv"],
        "selected_batch_reduction": selected_batch_reduction
        >= gates["minimum_selected_batch_reduction"],
        "selected_speedup": pooled_speedup
        >= gates["minimum_selected_pooled_step_speedup"],
        "step_latency": maximum_step <= gates["maximum_step_ms"],
        "host_peak": maximum_host <= gates["maximum_host_peak_numeric_bytes"],
        "gpu_peak": maximum_gpu <= gates["maximum_gpu_pool_bytes"],
        "trace_batch_identity": trace_batch_identity
        == gates["require_trace_batch_identity"],
        "monotone_batch_counts": monotone_batches
        == gates["require_monotone_batch_counts"],
        "finite_outputs": finite == gates["require_finite_outputs"],
        "total_wall": aggregate["wall_seconds_before_result_serialization"]
        <= gates["maximum_total_audit_seconds"],
    }
    gate_results["passed"] = all(gate_results.values())
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 2,
        "experiment_type": (
            "corrected_restored_h32_step33_leaf_adjoint_batch_width_screen"
        ),
        "status": "frozen_corrected_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "rejected_implementation_sha256": _sha256(_REJECTED_IMPLEMENTATION),
        "checkpoint_source_sha256": _sha256(_SOURCE),
        "warmup_rows": warmups,
        "rows": rows,
        "width_summaries": summaries,
        "aggregate": aggregate,
        "gates": gate_results,
        "counts": {
            "warmup_rows": len(warmups),
            "measured_rows": len(rows),
            "width_summary_rows": len(summaries),
        },
        "timing": {
            "wall_seconds": time.perf_counter() - started,
            "cupy_import_ms": cupy_import_ms,
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "gpu_name": str(name),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "limitations": [
            "The screen times only restored step thirty-three on one board and two constructed range families.",
            "It measures kernel economics and numerical state agreement, not a new strategy-quality point.",
            "The selected width is restricted to the three frozen candidates and one RTX 5080 environment.",
            "The rejected v1 executed balanced arms without emitting any row values before failing in cleanup.",
            "A width win does not remove repeated host-device transfers or authorize claims about a resident custom CUDA kernel.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_leaf_adjoint_batch_width_v2_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "corrected leaf-adjoint batch-width audit: "
        f"rows={result['counts']['measured_rows']}, "
        f"selected={result['aggregate']['selected_width']}, "
        f"speedup={result['aggregate']['selected_pooled_step_speedup']:.6g}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
