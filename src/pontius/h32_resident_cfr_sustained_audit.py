"""Sustained h32 resident-CFR trajectory and restart audit."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .axis_cfr_checkpoint import (
    export_axis_cfr_checkpoint,
    restore_axis_cfr_checkpoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import (
    _build_target_belief,
    parse_fresh_h32_strategy_transfer_config,
)
from .h32_resident_cfr_audit import (
    _checkpoint,
    _policy_error,
    _resident_caches,
    _source_row,
    _step_row,
    _table_error,
    _target_row,
)
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _current_policy_from_state,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-resident-cfr-sustained-audit-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-resident-cfr-sustained-audit-v1.json"
)
_TEACHER = (
    _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_TEACHER_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_RESIDENT_RESULT = (
    _ROOT / "experiments" / "results" / "h32-resident-cfr-audit-v2.json"
)
_RESIDENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v2.json"
)
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_RESIDENT_CFR = _ROOT / "src" / "pontius" / "resident_leaf_adjoint_cfr.py"
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_teacher_sha256",
    "expected_teacher_config_sha256",
    "expected_resident_result_sha256",
    "expected_resident_config_sha256",
    "expected_requirements_sha256",
    "expected_resident_cfr_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "blueprint_point",
    "warm_regret_mass_payoff_fraction",
    "final_iteration",
    "comparison_iterations",
    "restart_control",
    "maximum_feature_width_per_batch",
    "cache_charge",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_resident_cfr_sustained_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen sustained-trajectory protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("sustained resident-CFR config fields differ from ADR-0121")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0120_before_any_h32_resident_cfr_"
            "iteration_three_through_eight_timing_or_state_label"
        ),
        "seed": 20260820,
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": ["local_blocker_seat5_x2", "all_seat_strength_1_to2"],
        "blueprint_point": "64:average",
        "warm_regret_mass_payoff_fraction": 0.1,
        "final_iteration": 8,
        "comparison_iterations": [1, 2, 4, 8],
        "restart_control": {
            "range_family": "balanced",
            "target_shift": "local_blocker_seat5_x2",
            "split_iteration": 4,
            "final_iteration": 8,
        },
        "maximum_feature_width_per_batch": 384,
        "cache_charge": "one_complete_six_seat_cache_per_target",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("sustained resident-CFR workload differs from ADR-0121")
    sources = {
        "expected_teacher_sha256": _TEACHER,
        "expected_teacher_config_sha256": _TEACHER_CONFIG,
        "expected_resident_result_sha256": _RESIDENT_RESULT,
        "expected_resident_config_sha256": _RESIDENT_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_resident_cfr_sha256": _RESIDENT_CFR,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"sustained resident-CFR source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_primary_steps": 32,
        "expected_checkpoint_comparisons": 16,
        "expected_restart_steps": 4,
        "maximum_teacher_regret_error": 1e-10,
        "maximum_teacher_strategy_sum_error": 1e-10,
        "maximum_teacher_policy_probability_error": 1e-9,
        "maximum_teacher_policy_mean_tv": 1e-10,
        "maximum_restart_regret_error": 0.0,
        "maximum_restart_strategy_sum_error": 0.0,
        "require_restart_current_policy_identity": True,
        "require_restart_average_policy_identity": True,
        "require_restart_state_digest_identity": True,
        "minimum_each_target_eight_step_marginal_speedup": 1.5,
        "minimum_each_target_eight_step_cache_charged_speedup": 1.5,
        "maximum_late_to_early_median_step_ratio": 1.25,
        "maximum_static_cache_compile_ms": 120000.0,
        "maximum_step_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("sustained resident-CFR gates differ from ADR-0121")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "comparison_iterations": tuple(config["comparison_iterations"]),
        "restart_control": dict(config["restart_control"]),
        "gates": dict(config["gates"]),
    }


def _resident_solver(
    *,
    parsed: dict[str, Any],
    teacher_config: dict[str, Any],
    layout: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    hands_by_player: Any,
    belief_cache: Any,
    automaton_caches: Any,
    gpu: Any,
) -> ResidentLeafAdjointPublicTreeCFR:
    return ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        teacher_config["solver_variant"],
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        hands_by_player=hands_by_player,
    )


def _trajectory(
    solver: ResidentLeafAdjointPublicTreeCFR,
    *,
    teacher: dict[str, Any],
    final_iteration: int,
    comparison_iterations: tuple[int, ...],
) -> dict[str, Any]:
    steps = []
    snapshots = {}
    for iteration in range(1, final_iteration + 1):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        work = solver.last_step_work
        if work is None:
            raise AssertionError("sustained resident-CFR step has no telemetry")
        steps.append(_step_row(work, wall_ms=wall_ms))
        if iteration not in comparison_iterations:
            continue
        expected = _checkpoint(teacher, iteration)
        expected_state = expected["state"]
        current = solver.current_strategy()
        average = solver.average_strategy()
        exported = export_axis_cfr_checkpoint(
            solver,
            context=expected_state["context"],
            provenance=expected_state["provenance"],
        )
        snapshots[iteration] = {
            "regrets": solver.regret_table(),
            "strategy_sums": solver.strategy_sum_table(),
            "current": current,
            "average": average,
            "checkpoint": exported,
        }
    return {"steps": steps, "snapshots": snapshots}


def _comparison_rows(
    trajectory: dict[str, Any],
    *,
    teacher: dict[str, Any],
    comparison_iterations: tuple[int, ...],
) -> list[dict[str, Any]]:
    rows = []
    for iteration in comparison_iterations:
        actual = trajectory["snapshots"][iteration]
        expected = _checkpoint(teacher, iteration)
        expected_state = expected["state"]
        expected_current = _current_policy_from_state(expected_state)
        expected_average = _average_policy_from_state(expected_state)
        current_error, current_tv = _policy_error(
            actual["current"], expected_current
        )
        average_error, average_tv = _policy_error(
            actual["average"], expected_average
        )
        rows.append(
            {
                "iteration": iteration,
                "teacher_regret_error": _table_error(
                    actual["regrets"], expected_state["regrets"]
                ),
                "teacher_strategy_sum_error": _table_error(
                    actual["strategy_sums"], expected_state["strategy_sums"]
                ),
                "teacher_current_probability_error": current_error,
                "teacher_current_mean_tv": current_tv,
                "teacher_average_probability_error": average_error,
                "teacher_average_mean_tv": average_tv,
                "teacher_state_digest_identity": (
                    actual["checkpoint"]["state_sha256"]
                    == expected["state_sha256"]
                ),
                "current_policy_sha256": policy_digest(actual["current"]),
                "average_policy_sha256": policy_digest(actual["average"]),
                "state_sha256": actual["checkpoint"]["state_sha256"],
            }
        )
    return rows


def _restart_control(
    *,
    parsed: dict[str, Any],
    teacher_config: dict[str, Any],
    trajectory: dict[str, Any],
    teacher: dict[str, Any],
    layout: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    hands_by_player: Any,
    belief_cache: Any,
    automaton_caches: Any,
    gpu: Any,
) -> dict[str, Any]:
    control = parsed["restart_control"]
    split_iteration = int(control["split_iteration"])
    final_iteration = int(control["final_iteration"])
    source_checkpoint = trajectory["snapshots"][split_iteration]["checkpoint"]
    solver = _resident_solver(
        parsed=parsed,
        teacher_config=teacher_config,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        hands_by_player=hands_by_player,
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        gpu=gpu,
    )
    retained = restore_axis_cfr_checkpoint(solver, source_checkpoint)
    steps = []
    for _ in range(split_iteration, final_iteration):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        work = solver.last_step_work
        if work is None:
            raise AssertionError("restart continuation step has no telemetry")
        steps.append(_step_row(work, wall_ms=wall_ms))
    uninterrupted = trajectory["snapshots"][final_iteration]
    restarted_current = solver.current_strategy()
    restarted_average = solver.average_strategy()
    restarted = export_axis_cfr_checkpoint(
        solver,
        context=retained["context"],
        provenance=retained["provenance"],
    )
    current_error, current_tv = _policy_error(
        restarted_current, uninterrupted["current"]
    )
    average_error, average_tv = _policy_error(
        restarted_average, uninterrupted["average"]
    )
    return {
        "range_family": control["range_family"],
        "target_shift": control["target_shift"],
        "split_iteration": split_iteration,
        "final_iteration": final_iteration,
        "steps": steps,
        "regret_error": _table_error(
            solver.regret_table(), uninterrupted["regrets"]
        ),
        "strategy_sum_error": _table_error(
            solver.strategy_sum_table(), uninterrupted["strategy_sums"]
        ),
        "current_policy_probability_error": current_error,
        "current_policy_mean_tv": current_tv,
        "average_policy_probability_error": average_error,
        "average_policy_mean_tv": average_tv,
        "current_policy_identity": restarted_current == uninterrupted["current"],
        "average_policy_identity": restarted_average == uninterrupted["average"],
        "state_digest_identity": (
            restarted["state_sha256"]
            == uninterrupted["checkpoint"]["state_sha256"]
        ),
        "teacher_iteration_eight_state_digest_identity": (
            restarted["state_sha256"]
            == _checkpoint(teacher, final_iteration)["state_sha256"]
        ),
    }


def _run_target(
    *,
    parsed: dict[str, Any],
    teacher_config: dict[str, Any],
    teacher_artifact: dict[str, Any],
    family: str,
    shift: str,
    board: tuple[int, ...],
    source_belief: Any,
    source_workspace: Any,
    layout: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    target_belief, descriptor = _build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=teacher_config["local_blocker_target_seat"],
    )
    compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=teacher_config["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    workspace_compile_ms = (time.perf_counter() - compile_started) * 1000.0
    belief_cache, automaton_caches, cache_compile_ms = _resident_caches(
        workspace, automata
    )

    source = _source_row(teacher_artifact, family)
    source_checkpoint = next(
        row for row in source["checkpoints"] if int(row["iteration"]) == 64
    )
    blueprint = _average_policy_from_state(source_checkpoint["state"])
    teacher = _target_row(teacher_artifact, family, shift)
    solver = _resident_solver(
        parsed=parsed,
        teacher_config=teacher_config,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        hands_by_player=target_belief.hands_by_player,
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        gpu=gpu,
    )
    warm_mass = parsed["warm_regret_mass_payoff_fraction"] * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    trajectory = _trajectory(
        solver,
        teacher=teacher,
        final_iteration=parsed["final_iteration"],
        comparison_iterations=parsed["comparison_iterations"],
    )
    comparisons = _comparison_rows(
        trajectory,
        teacher=teacher,
        comparison_iterations=parsed["comparison_iterations"],
    )

    restart = None
    restart_spec = parsed["restart_control"]
    if (
        family == restart_spec["range_family"]
        and shift == restart_spec["target_shift"]
    ):
        restart = _restart_control(
            parsed=parsed,
            teacher_config=teacher_config,
            trajectory=trajectory,
            teacher=teacher,
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            automata=automata,
            hands_by_player=target_belief.hands_by_player,
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            gpu=gpu,
        )

    resident_steps = tuple(float(row["wall_ms"]) for row in trajectory["steps"])
    teacher_steps = tuple(
        float(row["wall_ms"]) for row in teacher["search"]["step_rows"]
    )
    early_median = float(np.median(resident_steps[:2]))
    late_median = float(np.median(resident_steps[2:]))
    economics = {
        "teacher_eight_step_ms": math.fsum(teacher_steps),
        "resident_eight_step_marginal_ms": math.fsum(resident_steps),
        "resident_eight_step_cache_charged_ms": cache_compile_ms
        + math.fsum(resident_steps),
        "eight_step_marginal_speedup": math.fsum(teacher_steps)
        / math.fsum(resident_steps),
        "eight_step_cache_charged_speedup": math.fsum(teacher_steps)
        / (cache_compile_ms + math.fsum(resident_steps)),
        "resident_early_step_median_ms": early_median,
        "resident_late_step_median_ms": late_median,
        "late_to_early_median_step_ratio": late_median / early_median,
    }
    public_checkpoints = [
        {
            **row,
            "teacher_current_policy_sha256": _checkpoint(
                teacher, int(row["iteration"])
            )["current_policy_sha256"],
            "teacher_average_policy_sha256": _checkpoint(
                teacher, int(row["iteration"])
            )["average_policy_sha256"],
            "teacher_state_sha256": _checkpoint(
                teacher, int(row["iteration"])
            )["state_sha256"],
        }
        for row in comparisons
    ]
    result = {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "blueprint_policy_sha256": policy_digest(blueprint),
        "target_belief_sha256": teacher["target_belief_sha256"],
        "workspace_compile_ms": workspace_compile_ms,
        "static_cache": {
            "compile_ms": cache_compile_ms,
            "numeric_bytes": belief_cache.numeric_bytes
            + sum(cache.numeric_bytes for cache in automaton_caches),
        },
        "steps": trajectory["steps"],
        "checkpoint_comparisons": public_checkpoints,
        "economics": economics,
    }
    del solver, trajectory, automaton_caches, belief_cache
    gc.collect()
    release_cupy_memory_pool()
    return result, restart


def run_h32_resident_cfr_sustained_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute the frozen sustained resident-CFR audit."""

    parsed = parse_h32_resident_cfr_sustained_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0121")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0121")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0121")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0121")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0121 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0121")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    teacher_config = parse_fresh_h32_strategy_transfer_config(
        json.loads(_TEACHER_CONFIG.read_text(encoding="utf-8"))
    )
    teacher = json.loads(_TEACHER.read_text(encoding="utf-8"))
    resident_result = json.loads(_RESIDENT_RESULT.read_text(encoding="utf-8"))
    source_identity = (
        teacher["status"] == "frozen_audit_executed"
        and bool(teacher["gates"]["passed"])
        and teacher["config_sha256"] == _sha256(_TEACHER_CONFIG)
        and resident_result["status"] == "frozen_successor_audit_executed"
        and bool(resident_result["gates"]["passed"])
        and resident_result["config_sha256"] == _sha256(_RESIDENT_CONFIG)
    )
    if not source_identity:
        raise ValueError("ADR-0121 source identity rejected")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    targets = []
    restart = None
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
        source_belief, layout, sparse, retained = _build_case(
            parsed=teacher_config,
            board=board,
            hand_count=parsed["hands_per_player"],
            family=family,
        )
        source_workspace, _, automata = retained
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            row, control = _run_target(
                parsed=parsed,
                teacher_config=teacher_config,
                teacher_artifact=teacher,
                family=family,
                shift=shift,
                board=board,
                source_belief=source_belief,
                source_workspace=source_workspace,
                layout=layout,
                sparse=sparse,
                automata=automata,
                gpu=gpu,
            )
            targets.append(row)
            if control is not None:
                if restart is not None:
                    raise AssertionError("sustained audit produced two restart controls")
                restart = control
        del gpu
        gc.collect()
        release_cupy_memory_pool()
    if restart is None:
        raise AssertionError("sustained audit did not execute restart control")

    comparisons = [
        row for target in targets for row in target["checkpoint_comparisons"]
    ]
    primary_steps = [row for target in targets for row in target["steps"]]
    restart_steps = restart["steps"]
    total_seconds = time.perf_counter() - started
    maximum_policy_error = max(
        max(
            row["teacher_current_probability_error"],
            row["teacher_average_probability_error"],
        )
        for row in comparisons
    )
    maximum_policy_tv = max(
        max(
            row["teacher_current_mean_tv"],
            row["teacher_average_mean_tv"],
        )
        for row in comparisons
    )
    gates_config = parsed["gates"]
    gates = {
        "source_identity": source_identity,
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "primary_steps": len(primary_steps) == gates_config["expected_primary_steps"],
        "checkpoint_comparisons": len(comparisons)
        == gates_config["expected_checkpoint_comparisons"],
        "restart_steps": len(restart_steps) == gates_config["expected_restart_steps"],
        "teacher_regret_error": max(
            row["teacher_regret_error"] for row in comparisons
        )
        <= gates_config["maximum_teacher_regret_error"],
        "teacher_strategy_sum_error": max(
            row["teacher_strategy_sum_error"] for row in comparisons
        )
        <= gates_config["maximum_teacher_strategy_sum_error"],
        "teacher_policy_probability_error": maximum_policy_error
        <= gates_config["maximum_teacher_policy_probability_error"],
        "teacher_policy_mean_tv": maximum_policy_tv
        <= gates_config["maximum_teacher_policy_mean_tv"],
        "restart_regret_error": restart["regret_error"]
        <= gates_config["maximum_restart_regret_error"],
        "restart_strategy_sum_error": restart["strategy_sum_error"]
        <= gates_config["maximum_restart_strategy_sum_error"],
        "restart_current_policy_identity": restart["current_policy_identity"]
        == gates_config["require_restart_current_policy_identity"],
        "restart_average_policy_identity": restart["average_policy_identity"]
        == gates_config["require_restart_average_policy_identity"],
        "restart_state_digest_identity": restart["state_digest_identity"]
        == gates_config["require_restart_state_digest_identity"],
        "each_target_eight_step_marginal_speedup": min(
            target["economics"]["eight_step_marginal_speedup"]
            for target in targets
        )
        >= gates_config["minimum_each_target_eight_step_marginal_speedup"],
        "each_target_eight_step_cache_charged_speedup": min(
            target["economics"]["eight_step_cache_charged_speedup"]
            for target in targets
        )
        >= gates_config["minimum_each_target_eight_step_cache_charged_speedup"],
        "late_to_early_median_step_ratio": max(
            target["economics"]["late_to_early_median_step_ratio"]
            for target in targets
        )
        <= gates_config["maximum_late_to_early_median_step_ratio"],
        "static_cache_compile_ms": max(
            target["static_cache"]["compile_ms"] for target in targets
        )
        <= gates_config["maximum_static_cache_compile_ms"],
        "step_ms": max(
            row["wall_ms"] for row in (*primary_steps, *restart_steps)
        )
        <= gates_config["maximum_step_ms"],
        "gpu_pool_bytes": max(
            row["maximum_gpu_pool_bytes"] for row in (*primary_steps, *restart_steps)
        )
        <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())

    teacher_bill = math.fsum(
        target["economics"]["teacher_eight_step_ms"] for target in targets
    )
    resident_bill = math.fsum(
        target["economics"]["resident_eight_step_marginal_ms"]
        for target in targets
    )
    charged_bill = math.fsum(
        target["economics"]["resident_eight_step_cache_charged_ms"]
        for target in targets
    )
    return {
        "schema_version": 1,
        "status": "frozen_audit_executed",
        "experiment_type": "h32_resident_cfr_sustained_trajectory",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "teacher": _sha256(_TEACHER),
            "teacher_config": _sha256(_TEACHER_CONFIG),
            "resident_result": _sha256(_RESIDENT_RESULT),
            "resident_config": _sha256(_RESIDENT_CONFIG),
            "requirements": _sha256(_REQUIREMENTS),
            "resident_cfr": _sha256(_RESIDENT_CFR),
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "targets": targets,
        "restart_control": restart,
        "correctness": {
            "maximum_teacher_regret_error": max(
                row["teacher_regret_error"] for row in comparisons
            ),
            "maximum_teacher_strategy_sum_error": max(
                row["teacher_strategy_sum_error"] for row in comparisons
            ),
            "maximum_teacher_policy_probability_error": maximum_policy_error,
            "maximum_teacher_policy_mean_tv": maximum_policy_tv,
            "teacher_state_digest_identities": sum(
                bool(row["teacher_state_digest_identity"])
                for row in comparisons
            ),
        },
        "economics": {
            "pooled_teacher_eight_step_ms": teacher_bill,
            "pooled_resident_eight_step_marginal_ms": resident_bill,
            "pooled_resident_eight_step_cache_charged_ms": charged_bill,
            "pooled_eight_step_marginal_speedup": teacher_bill / resident_bill,
            "pooled_eight_step_cache_charged_speedup": teacher_bill / charged_bill,
            "minimum_target_eight_step_marginal_speedup": min(
                target["economics"]["eight_step_marginal_speedup"]
                for target in targets
            ),
            "minimum_target_eight_step_cache_charged_speedup": min(
                target["economics"]["eight_step_cache_charged_speedup"]
                for target in targets
            ),
            "maximum_late_to_early_median_step_ratio": max(
                target["economics"]["late_to_early_median_step_ratio"]
                for target in targets
            ),
        },
        "counts": {
            "target_rows": len(targets),
            "primary_steps": len(primary_steps),
            "checkpoint_comparisons": len(comparisons),
            "restart_steps": len(restart_steps),
            "new_strategy_quality_labels": 0,
        },
        "timing": {"total_seconds": total_seconds},
        "gates": gates,
        "limitations": [
            "This bridge reuses one fresh river board and four existing target beliefs.",
            "Iteration eight does not establish sixty-four-step source-training stability.",
            "Stored transferred bills are used as the incumbent; no legacy steps are rerun.",
            "No new strategy quality, wider action tree, or hand-count crossover is claimed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    result = run_h32_resident_cfr_sustained_audit(config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(arguments.output), "gates": result["gates"]}))


if __name__ == "__main__":
    main()
