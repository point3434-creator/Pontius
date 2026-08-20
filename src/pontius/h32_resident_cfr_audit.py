"""Audit resident terminal contraction on the h32 one/two-step CFR customer."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Callable

import numpy as np

from .axis_cfr_checkpoint import export_axis_cfr_checkpoint
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
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .leaf_adjoint_cfr import LeafAdjointPublicTreeCFR
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-resident-cfr-audit-v1.json"
_PARENT = (
    _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_RESIDENT_CFR = _ROOT / "src" / "pontius" / "resident_leaf_adjoint_cfr.py"
_RESIDENT_CONTRACTION = (
    _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py"
)
_LEAF_CFR = _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
_CHECKPOINT = _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py"
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_sha256",
    "expected_parent_config_sha256",
    "expected_requirements_sha256",
    "expected_resident_cfr_sha256",
    "expected_resident_contraction_sha256",
    "expected_leaf_cfr_sha256",
    "expected_checkpoint_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "blueprint_point",
    "warm_regret_mass_payoff_fraction",
    "trajectory_iterations",
    "engine_order_by_target",
    "small_control_board",
    "small_control_hands_per_player",
    "small_control_family",
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


def parse_h32_resident_cfr_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen resident-CFR protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("resident-CFR config fields differ from ADR-0117")
    frozen = {
        "evidence_stage": (
            "preregistered_after_exact_h4_and_h7_development_screens_before_"
            "any_h32_resident_cfr_step_timing"
        ),
        "seed": 20260820,
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": ["local_blocker_seat5_x2", "all_seat_strength_1_to2"],
        "blueprint_point": "64:average",
        "warm_regret_mass_payoff_fraction": 0.1,
        "trajectory_iterations": [1, 2],
        "engine_order_by_target": [
            "legacy_then_resident",
            "resident_then_legacy",
            "resident_then_legacy",
            "legacy_then_resident",
        ],
        "small_control_board": ["3s", "8c", "Th", "Kd", "Ac"],
        "small_control_hands_per_player": 7,
        "small_control_family": "balanced",
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
        raise ValueError("resident-CFR workload differs from ADR-0117")
    sources = {
        "expected_parent_sha256": _PARENT,
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_resident_cfr_sha256": _RESIDENT_CFR,
        "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
        "expected_leaf_cfr_sha256": _LEAF_CFR,
        "expected_checkpoint_sha256": _CHECKPOINT,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-CFR source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_engine_trajectories": 8,
        "expected_engine_steps": 16,
        "expected_checkpoint_comparisons": 8,
        "maximum_small_control_regret_error": 1e-9,
        "maximum_small_control_strategy_sum_error": 1e-9,
        "maximum_legacy_teacher_regret_error": 1e-12,
        "maximum_legacy_teacher_strategy_sum_error": 1e-12,
        "require_legacy_teacher_state_digest_identity": True,
        "maximum_resident_legacy_regret_error": 1e-9,
        "maximum_resident_legacy_strategy_sum_error": 1e-9,
        "maximum_resident_legacy_policy_probability_error": 1e-9,
        "maximum_resident_legacy_policy_mean_tv": 1e-10,
        "minimum_each_target_two_step_marginal_speedup": 1.5,
        "minimum_each_target_one_step_cache_charged_speedup": 1.2,
        "minimum_each_target_two_step_cache_charged_speedup": 1.5,
        "maximum_static_cache_compile_ms": 120000.0,
        "maximum_step_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident-CFR gates differ from ADR-0117")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "trajectory_iterations": tuple(config["trajectory_iterations"]),
        "engine_order_by_target": tuple(config["engine_order_by_target"]),
        "gates": dict(config["gates"]),
    }


def _table_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if first.keys() != second.keys():
        raise ValueError("resident-CFR accumulator schemas differ")
    return max(
        abs(float(first[key][action]) - float(second[key][action]))
        for key in first
        for action in first[key]
    )


def _policy_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> tuple[float, float]:
    if first.keys() != second.keys():
        raise ValueError("resident-CFR policy schemas differ")
    maximum = 0.0
    total_tv = 0.0
    for key in first:
        if first[key].keys() != second[key].keys():
            raise ValueError("resident-CFR policy action schemas differ")
        errors = tuple(
            abs(float(first[key][action]) - float(second[key][action]))
            for action in first[key]
        )
        maximum = max(maximum, *errors)
        total_tv += 0.5 * math.fsum(errors)
    return maximum, total_tv / len(first)


def _source_row(parent: dict[str, Any], family: str) -> dict[str, Any]:
    return next(row for row in parent["source_family_rows"] if row["range_family"] == family)


def _target_row(parent: dict[str, Any], family: str, shift: str) -> dict[str, Any]:
    return next(
        row
        for row in parent["targets"]
        if row["range_family"] == family and row["target_shift"] == shift
    )


def _checkpoint(row: dict[str, Any], iteration: int) -> dict[str, Any]:
    return next(
        checkpoint
        for checkpoint in row["search"]["checkpoint_rows"]
        if int(checkpoint["iteration"]) == iteration
    )


def _step_row(work: Any, *, wall_ms: float) -> dict[str, Any]:
    traversers = work.traversers
    row = {
        "iteration": work.iteration,
        "wall_ms": wall_ms,
        "reported_wall_ms": work.wall_ms,
        "probability_compile_ms": math.fsum(
            value.probability_compile_ms for value in traversers
        ),
        "own_reach_and_average_ms": math.fsum(
            value.own_reach_and_average_ms for value in traversers
        ),
        "terminal_contraction_ms": work.terminal_contraction_ms,
        "reverse_adjoint_ms": math.fsum(
            value.reverse_adjoint_ms for value in traversers
        ),
        "regret_apply_ms": math.fsum(value.regret_apply_ms for value in traversers),
        "discount_ms": work.discount_ms,
        "terminal_sparse_batches": sum(
            value.terminal_sparse_batches for value in traversers
        ),
        "maximum_gpu_pool_bytes": max(
            value.maximum_gpu_pool_total_bytes for value in traversers
        ),
    }
    if hasattr(traversers[0], "resident_work"):
        row.update(
            {
                "factor_prepare_ms": math.fsum(
                    value.resident_work.factor_prepare_ms for value in traversers
                ),
                "factor_upload_ms": math.fsum(
                    value.resident_work.factor_upload_ms for value in traversers
                ),
                "resident_pipeline_gpu_ms": math.fsum(
                    value.resident_work.resident_pipeline_gpu_ms
                    for value in traversers
                ),
                "resident_marginal_transfer_bytes": sum(
                    value.resident_work.per_call_host_to_device_bytes
                    + value.resident_work.per_call_device_to_host_bytes
                    for value in traversers
                ),
                "legacy_equivalent_transfer_bytes": sum(
                    value.resident_work.legacy_equivalent_host_to_device_bytes
                    + value.resident_work.legacy_equivalent_device_to_host_bytes
                    for value in traversers
                ),
            }
        )
    return row


def _trajectory(
    solver: Any,
    *,
    teacher: dict[str, Any] | None = None,
) -> dict[str, Any]:
    steps = []
    snapshots = []
    for iteration in (1, 2):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        work = solver.last_step_work
        if work is None:
            raise AssertionError("resident-CFR step has no work telemetry")
        steps.append(_step_row(work, wall_ms=wall_ms))
        current = solver.current_strategy()
        average = solver.average_strategy()
        teacher_checkpoint = None if teacher is None else _checkpoint(teacher, iteration)
        exported = None
        if teacher_checkpoint is not None:
            teacher_state = teacher_checkpoint["state"]
            exported = export_axis_cfr_checkpoint(
                solver,
                context=teacher_state["context"],
                provenance=teacher_state["provenance"],
            )
        snapshots.append(
            {
                "iteration": iteration,
                "regrets": solver.regret_table(),
                "strategy_sums": solver.strategy_sum_table(),
                "current": current,
                "average": average,
                "current_policy_sha256": policy_digest(current),
                "average_policy_sha256": policy_digest(average),
                "state_sha256": None if exported is None else exported["state_sha256"],
            }
        )
    return {"steps": steps, "snapshots": snapshots}


def _public_trajectory(trajectory: dict[str, Any]) -> dict[str, Any]:
    return {
        "steps": trajectory["steps"],
        "checkpoints": [
            {
                "iteration": row["iteration"],
                "current_policy_sha256": row["current_policy_sha256"],
                "average_policy_sha256": row["average_policy_sha256"],
                "state_sha256": row["state_sha256"],
            }
            for row in trajectory["snapshots"]
        ],
    }


def _compare_trajectories(
    legacy: dict[str, Any],
    resident: dict[str, Any],
    teacher: dict[str, Any],
) -> dict[str, Any]:
    rows = []
    for iteration, left, right in zip(
        (1, 2),
        legacy["snapshots"],
        resident["snapshots"],
        strict=True,
    ):
        expected = _checkpoint(teacher, iteration)
        expected_state = expected["state"]
        current_error, current_tv = _policy_error(left["current"], right["current"])
        average_error, average_tv = _policy_error(left["average"], right["average"])
        rows.append(
            {
                "iteration": iteration,
                "legacy_teacher_regret_error": _table_error(
                    left["regrets"], expected_state["regrets"]
                ),
                "legacy_teacher_strategy_sum_error": _table_error(
                    left["strategy_sums"], expected_state["strategy_sums"]
                ),
                "legacy_teacher_state_digest_identity": (
                    left["state_sha256"] == expected["state_sha256"]
                ),
                "resident_legacy_regret_error": _table_error(
                    right["regrets"], left["regrets"]
                ),
                "resident_legacy_strategy_sum_error": _table_error(
                    right["strategy_sums"], left["strategy_sums"]
                ),
                "resident_legacy_current_probability_error": current_error,
                "resident_legacy_current_mean_tv": current_tv,
                "resident_legacy_average_probability_error": average_error,
                "resident_legacy_average_mean_tv": average_tv,
                "resident_legacy_current_digest_identity": (
                    right["current_policy_sha256"] == left["current_policy_sha256"]
                ),
                "resident_legacy_average_digest_identity": (
                    right["average_policy_sha256"] == left["average_policy_sha256"]
                ),
            }
        )
    return {"checkpoint_rows": rows}


def _resident_caches(
    workspace: Any,
    automata: tuple[dict[str, Any], ...],
) -> tuple[CuPyResidentBeliefCache, tuple[CuPyResidentAutomatonCache, ...], float]:
    started = time.perf_counter()
    belief = CuPyResidentBeliefCache.compile(workspace)
    libraries = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace,
            automata[seat],
            target_seat=seat,
        )
        for seat in range(len(automata))
    )
    return belief, libraries, (time.perf_counter() - started) * 1000.0


def _small_control(parsed: dict[str, Any], parent_config: dict[str, Any]) -> dict[str, Any]:
    board = parse_cards(*parsed["small_control_board"])
    belief, layout, sparse, retained = _build_case(
        parsed=parent_config,
        board=board,
        hand_count=parsed["small_control_hands_per_player"],
        family=parsed["small_control_family"],
    )
    workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache, automaton_caches, cache_ms = _resident_caches(workspace, automata)
    legacy = LeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        parent_config["solver_variant"],
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
    )
    resident = ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        parent_config["solver_variant"],
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )
    mass = parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    legacy.warm_start({}, mass)
    resident.warm_start({}, mass)
    left = _trajectory_one_step(legacy)
    right = _trajectory_one_step(resident)
    result = {
        "board": parsed["small_control_board"],
        "hands_per_player": parsed["small_control_hands_per_player"],
        "cache_compile_ms": cache_ms,
        "legacy_step_ms": left["wall_ms"],
        "resident_step_ms": right["wall_ms"],
        "marginal_speedup": left["wall_ms"] / right["wall_ms"],
        "cache_charged_speedup": left["wall_ms"] / (cache_ms + right["wall_ms"]),
        "regret_error": _table_error(legacy.regret_table(), resident.regret_table()),
        "strategy_sum_error": _table_error(
            legacy.strategy_sum_table(), resident.strategy_sum_table()
        ),
    }
    del automaton_caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def _trajectory_one_step(solver: Any) -> dict[str, Any]:
    started = time.perf_counter()
    solver.step()
    wall_ms = (time.perf_counter() - started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("resident-CFR control step has no work")
    return {"wall_ms": wall_ms, "work": _step_row(solver.last_step_work, wall_ms=wall_ms)}


def _run_target(
    *,
    parsed: dict[str, Any],
    parent_config: dict[str, Any],
    parent: dict[str, Any],
    family: str,
    shift: str,
    order: str,
    board: tuple[int, ...],
    source_belief: Any,
    source_workspace: Any,
    layout: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
) -> dict[str, Any]:
    target_belief, descriptor = _build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parent_config["local_blocker_target_seat"],
    )
    compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parent_config["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    workspace_compile_ms = (time.perf_counter() - compile_started) * 1000.0
    belief_cache, automaton_caches, cache_compile_ms = _resident_caches(
        workspace, automata
    )

    source = _source_row(parent, family)
    source_checkpoint = next(
        row for row in source["checkpoints"] if int(row["iteration"]) == 64
    )
    blueprint = _average_policy_from_state(source_checkpoint["state"])
    teacher = _target_row(parent, family, shift)
    mass = parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)

    def legacy_factory() -> Any:
        solver = LeafAdjointPublicTreeCFR(
            layout,
            workspace,
            sparse,
            automata,
            parent_config["solver_variant"],
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
            hands_by_player=target_belief.hands_by_player,
            cupy_sparse=gpu,
        )
        solver.warm_start(blueprint, mass)
        return solver

    def resident_factory() -> Any:
        solver = ResidentLeafAdjointPublicTreeCFR(
            layout,
            workspace,
            sparse,
            automata,
            parent_config["solver_variant"],
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
            hands_by_player=target_belief.hands_by_player,
        )
        solver.warm_start(blueprint, mass)
        return solver

    runners: dict[str, Callable[[], dict[str, Any]]] = {
        "legacy": lambda: _trajectory(legacy_factory(), teacher=teacher),
        "resident": lambda: _trajectory(resident_factory(), teacher=teacher),
    }
    engine_sequence = (
        ("legacy", "resident")
        if order == "legacy_then_resident"
        else ("resident", "legacy")
    )
    measured: dict[str, dict[str, Any]] = {}
    for engine in engine_sequence:
        measured[engine] = runners[engine]()

    correctness = _compare_trajectories(
        measured["legacy"], measured["resident"], teacher
    )
    legacy_steps = tuple(row["wall_ms"] for row in measured["legacy"]["steps"])
    resident_steps = tuple(row["wall_ms"] for row in measured["resident"]["steps"])
    economics = {
        "legacy_one_step_ms": legacy_steps[0],
        "resident_one_step_marginal_ms": resident_steps[0],
        "resident_one_step_cache_charged_ms": cache_compile_ms + resident_steps[0],
        "one_step_marginal_speedup": legacy_steps[0] / resident_steps[0],
        "one_step_cache_charged_speedup": legacy_steps[0]
        / (cache_compile_ms + resident_steps[0]),
        "legacy_two_step_ms": math.fsum(legacy_steps),
        "resident_two_step_marginal_ms": math.fsum(resident_steps),
        "resident_two_step_cache_charged_ms": cache_compile_ms
        + math.fsum(resident_steps),
        "two_step_marginal_speedup": math.fsum(legacy_steps)
        / math.fsum(resident_steps),
        "two_step_cache_charged_speedup": math.fsum(legacy_steps)
        / (cache_compile_ms + math.fsum(resident_steps)),
    }
    return {
        "range_family": family,
        "target_shift": shift,
        "engine_order": order,
        "target_descriptor": descriptor,
        "blueprint_policy_sha256": policy_digest(blueprint),
        "target_belief_sha256": teacher["target_belief_sha256"],
        "workspace_compile_ms": workspace_compile_ms,
        "static_cache": {
            "compile_ms": cache_compile_ms,
            "numeric_bytes": belief_cache.numeric_bytes
            + sum(cache.numeric_bytes for cache in automaton_caches),
        },
        "legacy": _public_trajectory(measured["legacy"]),
        "resident": _public_trajectory(measured["resident"]),
        "correctness": correctness,
        "economics": economics,
    }


def run_h32_resident_cfr_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen h32 resident-CFR audit."""

    parsed = parse_h32_resident_cfr_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0117")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0117")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0117")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0117")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0117 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0117")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    parent_config = parse_fresh_h32_strategy_transfer_config(
        json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    )
    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    source_identity = (
        parent["status"] == "frozen_audit_executed"
        and bool(parent["gates"]["passed"])
        and parent["config_sha256"] == _sha256(_PARENT_CONFIG)
        and parent["implementation_sha256"]
        == parent_config["expected_audit_implementation_sha256"]
    )
    if not source_identity:
        raise ValueError("ADR-0117 parent identity rejected")

    started = time.perf_counter()
    small = _small_control(parsed, parent_config)
    board = parse_cards(*parsed["board"])
    targets = []
    target_index = 0
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
        source_belief, layout, sparse, retained = _build_case(
            parsed=parent_config,
            board=board,
            hand_count=parsed["hands_per_player"],
            family=family,
        )
        source_workspace, _, automata = retained
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            targets.append(
                _run_target(
                    parsed=parsed,
                    parent_config=parent_config,
                    parent=parent,
                    family=family,
                    shift=shift,
                    order=parsed["engine_order_by_target"][target_index],
                    board=board,
                    source_belief=source_belief,
                    source_workspace=source_workspace,
                    layout=layout,
                    sparse=sparse,
                    automata=automata,
                    gpu=gpu,
                )
            )
            target_index += 1
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    comparisons = [
        row
        for target in targets
        for row in target["correctness"]["checkpoint_rows"]
    ]
    all_steps = [
        step
        for target in targets
        for engine in (target["legacy"], target["resident"])
        for step in engine["steps"]
    ]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    maximum_policy_error = max(
        max(
            row["resident_legacy_current_probability_error"],
            row["resident_legacy_average_probability_error"],
        )
        for row in comparisons
    )
    maximum_policy_tv = max(
        max(
            row["resident_legacy_current_mean_tv"],
            row["resident_legacy_average_mean_tv"],
        )
        for row in comparisons
    )
    gates = {
        "source_identity": source_identity,
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "engine_trajectories": 2 * len(targets)
        == gates_config["expected_engine_trajectories"],
        "engine_steps": len(all_steps) == gates_config["expected_engine_steps"],
        "checkpoint_comparisons": len(comparisons)
        == gates_config["expected_checkpoint_comparisons"],
        "small_control_regret_error": small["regret_error"]
        <= gates_config["maximum_small_control_regret_error"],
        "small_control_strategy_sum_error": small["strategy_sum_error"]
        <= gates_config["maximum_small_control_strategy_sum_error"],
        "legacy_teacher_regret_error": max(
            row["legacy_teacher_regret_error"] for row in comparisons
        )
        <= gates_config["maximum_legacy_teacher_regret_error"],
        "legacy_teacher_strategy_sum_error": max(
            row["legacy_teacher_strategy_sum_error"] for row in comparisons
        )
        <= gates_config["maximum_legacy_teacher_strategy_sum_error"],
        "legacy_teacher_state_digest_identity": all(
            row["legacy_teacher_state_digest_identity"] for row in comparisons
        )
        == gates_config["require_legacy_teacher_state_digest_identity"],
        "resident_legacy_regret_error": max(
            row["resident_legacy_regret_error"] for row in comparisons
        )
        <= gates_config["maximum_resident_legacy_regret_error"],
        "resident_legacy_strategy_sum_error": max(
            row["resident_legacy_strategy_sum_error"] for row in comparisons
        )
        <= gates_config["maximum_resident_legacy_strategy_sum_error"],
        "resident_legacy_policy_probability_error": maximum_policy_error
        <= gates_config["maximum_resident_legacy_policy_probability_error"],
        "resident_legacy_policy_mean_tv": maximum_policy_tv
        <= gates_config["maximum_resident_legacy_policy_mean_tv"],
        "each_target_two_step_marginal_speedup": min(
            target["economics"]["two_step_marginal_speedup"] for target in targets
        )
        >= gates_config["minimum_each_target_two_step_marginal_speedup"],
        "each_target_one_step_cache_charged_speedup": min(
            target["economics"]["one_step_cache_charged_speedup"]
            for target in targets
        )
        >= gates_config["minimum_each_target_one_step_cache_charged_speedup"],
        "each_target_two_step_cache_charged_speedup": min(
            target["economics"]["two_step_cache_charged_speedup"]
            for target in targets
        )
        >= gates_config["minimum_each_target_two_step_cache_charged_speedup"],
        "static_cache_compile_ms": max(
            target["static_cache"]["compile_ms"] for target in targets
        )
        <= gates_config["maximum_static_cache_compile_ms"],
        "step_ms": max(step["wall_ms"] for step in all_steps)
        <= gates_config["maximum_step_ms"],
        "gpu_pool_bytes": max(step["maximum_gpu_pool_bytes"] for step in all_steps)
        <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    pooled_legacy = math.fsum(
        target["economics"]["legacy_two_step_ms"] for target in targets
    )
    pooled_resident = math.fsum(
        target["economics"]["resident_two_step_marginal_ms"] for target in targets
    )
    pooled_charged = math.fsum(
        target["economics"]["resident_two_step_cache_charged_ms"]
        for target in targets
    )
    return {
        "schema_version": 1,
        "status": "frozen_audit_executed",
        "experiment_type": "h32_resident_leaf_adjoint_cfr",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "parent": _sha256(_PARENT),
            "parent_config": _sha256(_PARENT_CONFIG),
            "requirements": _sha256(_REQUIREMENTS),
            "resident_cfr": _sha256(_RESIDENT_CFR),
            "resident_contraction": _sha256(_RESIDENT_CONTRACTION),
            "leaf_cfr": _sha256(_LEAF_CFR),
            "checkpoint": _sha256(_CHECKPOINT),
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
        "small_axis_negative_control": small,
        "targets": targets,
        "correctness": {
            "maximum_legacy_teacher_regret_error": max(
                row["legacy_teacher_regret_error"] for row in comparisons
            ),
            "maximum_legacy_teacher_strategy_sum_error": max(
                row["legacy_teacher_strategy_sum_error"] for row in comparisons
            ),
            "legacy_teacher_state_digest_identities": sum(
                bool(row["legacy_teacher_state_digest_identity"])
                for row in comparisons
            ),
            "maximum_resident_legacy_regret_error": max(
                row["resident_legacy_regret_error"] for row in comparisons
            ),
            "maximum_resident_legacy_strategy_sum_error": max(
                row["resident_legacy_strategy_sum_error"] for row in comparisons
            ),
            "maximum_resident_legacy_policy_probability_error": maximum_policy_error,
            "maximum_resident_legacy_policy_mean_tv": maximum_policy_tv,
        },
        "economics": {
            "pooled_legacy_two_step_ms": pooled_legacy,
            "pooled_resident_two_step_marginal_ms": pooled_resident,
            "pooled_resident_two_step_cache_charged_ms": pooled_charged,
            "pooled_two_step_marginal_speedup": pooled_legacy / pooled_resident,
            "pooled_two_step_cache_charged_speedup": pooled_legacy / pooled_charged,
            "minimum_target_one_step_cache_charged_speedup": min(
                target["economics"]["one_step_cache_charged_speedup"]
                for target in targets
            ),
            "minimum_target_two_step_cache_charged_speedup": min(
                target["economics"]["two_step_cache_charged_speedup"]
                for target in targets
            ),
        },
        "counts": {
            "target_rows": len(targets),
            "engine_trajectories": 2 * len(targets),
            "engine_steps": len(all_steps),
            "checkpoint_comparisons": len(comparisons),
        },
        "timing": {"total_seconds": total_seconds},
        "gates": gates,
        "limitations": [
            "One river board, one bet size, equal stacks, and four generated target beliefs.",
            "The h7 control is an expected boundary measurement, not a fitted runtime selector.",
            "This audit measures exact search mechanics and cost, not additional strategy quality.",
            "Static cache cost is charged once per target for both the one-step and two-step bills.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    result = run_h32_resident_cfr_audit(config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(arguments.output), "gates": result["gates"]}))


if __name__ == "__main__":
    main()
