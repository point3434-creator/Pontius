"""Screen wider CuPy terminal batches from exact iteration-32 CFR states."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Any

import numpy as np

from .axis_cfr_checkpoint import (
    axis_cfr_checkpoint_digest,
    restore_axis_cfr_checkpoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    CuPySparseIncidenceDirection,
    CuPyTransformWork,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case, _solver
from .real_policy import mean_policy_total_variation, policy_digest
from .reporting import environment_metadata
from .river import parse_cards

_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "leaf-adjoint-batch-width-audit-v1.json"
)
_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
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
_GATE_FIELDS = {
    "expected_rows",
    "expected_repeats_per_width_per_family",
    "require_exact_source_state_identity",
    "maximum_regret_accumulator_error",
    "maximum_strategy_sum_accumulator_error",
    "maximum_current_policy_probability_error",
    "maximum_average_policy_probability_error",
    "maximum_current_policy_mean_tv",
    "maximum_average_policy_mean_tv",
    "minimum_selected_batch_reduction",
    "minimum_selected_pooled_step_speedup",
    "maximum_step_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "require_trace_batch_identity",
    "require_monotone_batch_counts",
    "require_finite_outputs",
    "maximum_total_audit_seconds",
}
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
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_leaf_adjoint_batch_width_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "batch-width fields differ from ADR-0093: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0092_before_any_restored_h32_step33_"
            "batch_width_timing_or_state"
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
        raise ValueError("batch-width workload differs from ADR-0093")
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
        raise ValueError("batch-width gates differ from ADR-0093")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "width_schedule": tuple(config["width_schedule"]),
        "gates": dict(gates),
    }


@dataclass(frozen=True, slots=True)
class _TransformTrace:
    direction: str
    source_records: int
    query_records: int
    feature_width: int
    host_to_device_bytes: int
    device_to_host_bytes: int
    work: CuPyTransformWork


@dataclass(slots=True)
class _TracingDirection:
    direction: str
    inner: CuPySparseIncidenceDirection
    traces: list[_TransformTrace] = field(default_factory=list)

    def transform(self, features: np.ndarray) -> tuple[np.ndarray, CuPyTransformWork]:
        result, work = self.inner.transform(features)
        self.traces.append(
            _TransformTrace(
                direction=self.direction,
                source_records=int(features.shape[0]),
                query_records=int(result.shape[0]),
                feature_width=int(features.shape[1]),
                host_to_device_bytes=int(features.nbytes),
                device_to_host_bytes=int(result.nbytes),
                work=work,
            )
        )
        return result, work


@dataclass(slots=True)
class _TracingBidirectional:
    cpu: Any
    right_to_left: _TracingDirection
    left_to_right: _TracingDirection

    @classmethod
    def wrap(cls, source: CuPyBidirectionalIncidence) -> _TracingBidirectional:
        return cls(
            cpu=source.cpu,
            right_to_left=_TracingDirection(
                direction="right_to_left",
                inner=source.right_to_left,
            ),
            left_to_right=_TracingDirection(
                direction="left_to_right",
                inner=source.left_to_right,
            ),
        )

    def all_traces(self) -> tuple[_TransformTrace, ...]:
        return tuple(self.right_to_left.traces + self.left_to_right.traces)


def _table_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if set(first) != set(second):
        raise ValueError("batch-width accumulator schemas differ")
    return max(
        abs(float(first[key][action]) - float(second[key][action]))
        for key in first
        for action in first[key]
    )


def _maximum_policy_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if set(first) != set(second):
        raise ValueError("batch-width policy schemas differ")
    return max(
        abs(float(first[key][action]) - float(second[key][action]))
        for key in first
        for action in first[key]
    )


def _object_digest(value: Any) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _run_restored_step(
    *,
    parsed: dict[str, Any],
    belief: Any,
    topology: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    gpu: CuPyBidirectionalIncidence,
    source_state: dict[str, Any],
    width: int,
) -> dict[str, Any]:
    tracing = _TracingBidirectional.wrap(gpu)
    supplied = {**parsed, "maximum_feature_width_per_batch": width}
    solver = _solver(
        parsed=supplied,
        belief=belief,
        topology=topology,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=tracing,
    )
    restore_axis_cfr_checkpoint(solver, source_state)
    input_current = policy_digest(solver.current_strategy())
    input_average = policy_digest(solver.average_strategy())
    started = time.perf_counter()
    solver.step()
    outer_wall_ms = (time.perf_counter() - started) * 1000.0
    work = solver.last_step_work
    if work is None:
        raise AssertionError("restored batch-width step has no telemetry")
    traces = tracing.all_traces()
    operator_wall_ms = math.fsum(trace.work.wall_ms for trace in traces)
    host_to_device_ms = math.fsum(
        trace.work.host_to_device_ms for trace in traces
    )
    gpu_kernel_ms = math.fsum(trace.work.kernel_ms for trace in traces)
    device_to_host_ms = math.fsum(
        trace.work.device_to_host_ms for trace in traces
    )
    regrets = solver.regret_table()
    strategy_sums = solver.strategy_sum_table()
    current = solver.current_strategy()
    average = solver.average_strategy()
    unique_widths = sorted({trace.feature_width for trace in traces})
    maximum_terminal_peak = max(
        row.maximum_terminal_peak_numeric_bytes for row in work.traversers
    )
    automaton_bytes = sum(
        value.numeric_bytes
        for value in {
            id(automaton): automaton
            for library in automata
            for automaton in library.values()
        }.values()
    )
    return {
        "width": width,
        "source_iteration": source_state["iteration"],
        "result_iteration": solver.iteration,
        "source_state_sha256": source_state["state_sha256"],
        "input_current_policy_sha256": input_current,
        "input_average_policy_sha256": input_average,
        "output_current_policy_sha256": policy_digest(current),
        "output_average_policy_sha256": policy_digest(average),
        "output_accumulator_sha256": _object_digest(
            {"regrets": regrets, "strategy_sums": strategy_sums}
        ),
        "outer_wall_ms": outer_wall_ms,
        "step_wall_ms": work.wall_ms,
        "terminal_contraction_ms": work.terminal_contraction_ms,
        "nonterminal_step_ms": work.wall_ms - work.terminal_contraction_ms,
        "operator_wall_ms": operator_wall_ms,
        "host_to_device_ms": host_to_device_ms,
        "gpu_kernel_ms": gpu_kernel_ms,
        "device_to_host_ms": device_to_host_ms,
        "operator_unattributed_ms": (
            operator_wall_ms
            - host_to_device_ms
            - gpu_kernel_ms
            - device_to_host_ms
        ),
        "terminal_nonoperator_ms": work.terminal_contraction_ms - operator_wall_ms,
        "transform_calls": len(traces),
        "reported_sparse_batches": sum(
            row.terminal_sparse_batches for row in work.traversers
        ),
        "feature_widths": unique_widths,
        "maximum_feature_width": max(unique_widths),
        "host_to_device_bytes": sum(
            trace.host_to_device_bytes for trace in traces
        ),
        "device_to_host_bytes": sum(
            trace.device_to_host_bytes for trace in traces
        ),
        "maximum_gpu_pool_bytes": max(
            trace.work.pool_total_bytes for trace in traces
        ),
        "maximum_host_peak_numeric_bytes": (
            maximum_terminal_peak
            + solver.accumulator_numeric_bytes()
            + automaton_bytes
        ),
        "finite": all(
            math.isfinite(float(value))
            for table in (regrets, strategy_sums)
            for row in table.values()
            for value in row.values()
        ),
        "_regrets": regrets,
        "_strategy_sums": strategy_sums,
        "_current": current,
        "_average": average,
    }


def _attach_reference_errors(
    row: dict[str, Any], reference: dict[str, Any]
) -> None:
    row["regret_accumulator_error"] = _table_error(
        row["_regrets"], reference["_regrets"]
    )
    row["strategy_sum_accumulator_error"] = _table_error(
        row["_strategy_sums"], reference["_strategy_sums"]
    )
    row["current_policy_probability_error"] = _maximum_policy_error(
        row["_current"], reference["_current"]
    )
    row["average_policy_probability_error"] = _maximum_policy_error(
        row["_average"], reference["_average"]
    )
    row["current_policy_mean_tv"] = mean_policy_total_variation(
        row["_current"], reference["_current"]
    )
    row["average_policy_mean_tv"] = mean_policy_total_variation(
        row["_average"], reference["_average"]
    )
    for field in ("_regrets", "_strategy_sums", "_current", "_average"):
        del row[field]


def _width_summaries(
    rows: list[dict[str, Any]],
    *,
    families: tuple[str, ...],
    widths: tuple[int, ...],
) -> tuple[list[dict[str, Any]], int, float]:
    summaries = []
    family_medians: dict[tuple[str, int], float] = {}
    for family in families:
        family_rows = [row for row in rows if row["range_family"] == family]
        baseline = statistics.median(
            float(row["step_wall_ms"])
            for row in family_rows
            if int(row["width"]) == widths[0]
        )
        baseline_batches = next(
            int(row["reported_sparse_batches"])
            for row in family_rows
            if int(row["width"]) == widths[0]
        )
        for width in widths:
            retained = [row for row in family_rows if int(row["width"]) == width]
            median_step = statistics.median(
                float(row["step_wall_ms"]) for row in retained
            )
            family_medians[(family, width)] = median_step
            batches = {int(row["reported_sparse_batches"]) for row in retained}
            if len(batches) != 1:
                raise AssertionError("batch count differs across identical width runs")
            batch_count = batches.pop()
            summaries.append(
                {
                    "range_family": family,
                    "width": width,
                    "repeats": len(retained),
                    "median_step_ms": median_step,
                    "median_terminal_ms": statistics.median(
                        float(row["terminal_contraction_ms"]) for row in retained
                    ),
                    "median_operator_wall_ms": statistics.median(
                        float(row["operator_wall_ms"]) for row in retained
                    ),
                    "median_host_to_device_ms": statistics.median(
                        float(row["host_to_device_ms"]) for row in retained
                    ),
                    "median_gpu_kernel_ms": statistics.median(
                        float(row["gpu_kernel_ms"]) for row in retained
                    ),
                    "median_device_to_host_ms": statistics.median(
                        float(row["device_to_host_ms"]) for row in retained
                    ),
                    "median_terminal_nonoperator_ms": statistics.median(
                        float(row["terminal_nonoperator_ms"]) for row in retained
                    ),
                    "step_speedup_over_384": baseline / median_step,
                    "sparse_batches": batch_count,
                    "batch_reduction_over_384": baseline_batches / batch_count,
                    "maximum_gpu_pool_bytes": max(
                        int(row["maximum_gpu_pool_bytes"]) for row in retained
                    ),
                    "maximum_host_peak_numeric_bytes": max(
                        int(row["maximum_host_peak_numeric_bytes"])
                        for row in retained
                    ),
                }
            )
    pooled_costs = {
        width: math.fsum(family_medians[(family, width)] for family in families)
        for width in widths
    }
    selected = min(widths, key=lambda width: (pooled_costs[width], width))
    speedup = pooled_costs[widths[0]] / pooled_costs[selected]
    return summaries, selected, speedup


def run_leaf_adjoint_batch_width_audit(
    config: dict[str, Any],
) -> dict[str, object]:
    parsed = parse_leaf_adjoint_batch_width_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0093")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0093")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0093")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0093")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0093 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0093")
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
        source_row = next(
            row for row in source["wide_rows"] if row["range_family"] == family
        )
        checkpoint = next(
            row
            for row in source_row["checkpoints"]
            if int(row["iteration"]) == parsed["source_iteration"]
        )
        source_state = checkpoint["state"]
        family_source_identity = (
            axis_cfr_checkpoint_digest(source_state) == checkpoint["state_sha256"]
            and checkpoint["state_sha256"] == source_row["final_state_sha256"]
            and source_state["iteration"] == parsed["source_iteration"]
            and source_state["current_policy_sha256"]
            == checkpoint["current_policy_sha256"]
            and source_state["average_policy_sha256"]
            == checkpoint["average_policy_sha256"]
        )
        source_identity = source_identity and family_source_identity
        if not family_source_identity:
            raise AssertionError("ADR-0093 source state identity rejected")

        warmup = _run_restored_step(
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
        warmups.append(
            {
                key: value
                for key, value in warmup.items()
                if not key.startswith("_")
            }
            | {
                "range_family": family,
                "workspace_timing": workspace_timing,
                "gpu_operator_upload_ms": gpu.upload_ms,
            }
        )
        del warmup

        repeat_counts: Counter[int] = Counter()
        reference = None
        for schedule_index, width in enumerate(parsed["width_schedule"]):
            gc.collect()
            row = _run_restored_step(
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
            _attach_reference_errors(row, reference)
            rows.append(row)
        del warmup, reference, gpu, automata, workspace, sparse, topology, belief
        gc.collect()

    if not source_identity:
        raise AssertionError("ADR-0093 source state identity rejected")
    summaries, selected_width, pooled_speedup = _width_summaries(
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
                (
                    row
                    for row in summaries
                    if row["range_family"] == family
                ),
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
        "schema_version": 1,
        "experiment_type": "restored_h32_step33_leaf_adjoint_batch_width_screen",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
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
    result = run_leaf_adjoint_batch_width_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "leaf-adjoint batch-width audit: "
        f"rows={result['counts']['measured_rows']}, "
        f"selected={result['aggregate']['selected_width']}, "
        f"speedup={result['aggregate']['selected_pooled_step_speedup']:.6g}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
