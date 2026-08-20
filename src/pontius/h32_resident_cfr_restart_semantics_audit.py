"""Separate exact checkpoint restoration from numerical GPU continuation."""

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
    _resident_quality_row,
    parse_fresh_h32_strategy_transfer_config,
)
from .h32_resident_cfr_audit import (
    _policy_error,
    _resident_caches,
    _source_row,
    _step_row,
    _table_error,
    _target_row,
)
from .h32_resident_cfr_sustained_audit import _resident_solver
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-resident-cfr-restart-semantics-audit-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments"
    / "results"
    / "h32-resident-cfr-restart-semantics-audit-v1.json"
)
_PARENT = (
    _ROOT / "experiments" / "results" / "h32-resident-cfr-sustained-audit-v1.json"
)
_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-resident-cfr-sustained-audit-v1.json"
)
_PARENT_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0122-sustained-resident-cfr-is-stable-but-not-bitwise-deterministic.md"
)
_TEACHER = (
    _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_TEACHER_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_FRESH_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "fresh_h32_strategy_transfer_audit.py"
)
_RESIDENT_CFR = _ROOT / "src" / "pontius" / "resident_leaf_adjoint_cfr.py"
_RESIDENT_EVALUATION = (
    _ROOT / "src" / "pontius" / "resident_leaf_adjoint_evaluation.py"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_sha256",
    "expected_parent_config_sha256",
    "expected_parent_decision_sha256",
    "expected_teacher_sha256",
    "expected_teacher_config_sha256",
    "expected_fresh_implementation_sha256",
    "expected_resident_cfr_sha256",
    "expected_resident_evaluation_sha256",
    "expected_audit_implementation_sha256",
    "range_family",
    "target_shift",
    "split_iteration",
    "final_iteration",
    "continuation_arms",
    "quality_policy_kinds",
    "maximum_feature_width_per_batch",
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


def parse_h32_resident_cfr_restart_semantics_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the one-correction restart-semantics protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("restart-semantics config fields differ from ADR-0123")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0122_before_any_repeated_restore_"
            "continuation_or_quality_label"
        ),
        "seed": 20260820,
        "range_family": "balanced",
        "target_shift": "local_blocker_seat5_x2",
        "split_iteration": 4,
        "final_iteration": 8,
        "continuation_arms": [
            "uninterrupted",
            "restored_a",
            "restored_b",
        ],
        "quality_policy_kinds": [
            "uninterrupted_current8",
            "restored_a_current8",
            "uninterrupted_average8",
            "restored_a_average8",
        ],
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("restart-semantics workload differs from ADR-0123")
    sources = {
        "expected_parent_sha256": _PARENT,
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_parent_decision_sha256": _PARENT_DECISION,
        "expected_teacher_sha256": _TEACHER,
        "expected_teacher_config_sha256": _TEACHER_CONFIG,
        "expected_fresh_implementation_sha256": _FRESH_IMPLEMENTATION,
        "expected_resident_cfr_sha256": _RESIDENT_CFR,
        "expected_resident_evaluation_sha256": _RESIDENT_EVALUATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"restart-semantics source hash mismatch for {field}")
    expected_gates = {
        "require_parent_formal_failure": True,
        "require_parent_only_restart_gates_failed": True,
        "expected_training_steps": 16,
        "expected_immediate_restore_rows": 2,
        "expected_quality_profiles": 4,
        "expected_quality_seat_evaluations": 24,
        "require_immediate_restore_state_digest_identity": True,
        "require_immediate_restore_current_policy_identity": True,
        "require_immediate_restore_average_policy_identity": True,
        "maximum_continuation_regret_error": 1e-10,
        "maximum_continuation_strategy_sum_error": 1e-10,
        "maximum_continuation_policy_probability_error": 1e-9,
        "maximum_continuation_policy_mean_tv": 1e-10,
        "maximum_quality_utility_error": 1e-10,
        "maximum_quality_best_response_error": 1e-10,
        "maximum_quality_deviation_gain_error": 1e-10,
        "maximum_quality_nash_conv_error": 1e-10,
        "maximum_quality_zero_sum_residual": 1e-9,
        "maximum_step_ms": 60000.0,
        "maximum_quality_profile_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("restart-semantics gates differ from ADR-0123")
    return {
        **config,
        "continuation_arms": tuple(config["continuation_arms"]),
        "quality_policy_kinds": tuple(config["quality_policy_kinds"]),
        "gates": dict(config["gates"]),
    }


def _run_steps(solver: Any, count: int) -> list[dict[str, Any]]:
    rows = []
    for _ in range(count):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        work = solver.last_step_work
        if work is None:
            raise AssertionError("restart-semantics step has no telemetry")
        rows.append(_step_row(work, wall_ms=wall_ms))
    return rows


def _solver_snapshot(solver: Any, *, context: Any, provenance: Any) -> dict[str, Any]:
    current = solver.current_strategy()
    average = solver.average_strategy()
    return {
        "regrets": solver.regret_table(),
        "strategy_sums": solver.strategy_sum_table(),
        "current": current,
        "average": average,
        "checkpoint": export_axis_cfr_checkpoint(
            solver,
            context=context,
            provenance=provenance,
        ),
    }


def _continuation_comparison(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    current_error, current_tv = _policy_error(first["current"], second["current"])
    average_error, average_tv = _policy_error(first["average"], second["average"])
    return {
        "comparison": label,
        "regret_error": _table_error(first["regrets"], second["regrets"]),
        "strategy_sum_error": _table_error(
            first["strategy_sums"], second["strategy_sums"]
        ),
        "current_policy_probability_error": current_error,
        "current_policy_mean_tv": current_tv,
        "average_policy_probability_error": average_error,
        "average_policy_mean_tv": average_tv,
        "current_policy_digest_identity": policy_digest(first["current"])
        == policy_digest(second["current"]),
        "average_policy_digest_identity": policy_digest(first["average"])
        == policy_digest(second["average"]),
        "state_digest_identity": first["checkpoint"]["state_sha256"]
        == second["checkpoint"]["state_sha256"],
    }


def _quality_error(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    return {
        "comparison": label,
        "utility_error": max(
            abs(float(left) - float(right))
            for left, right in zip(
                first["utilities"], second["utilities"], strict=True
            )
        ),
        "best_response_error": max(
            abs(float(left) - float(right))
            for left, right in zip(
                first["best_response_values"],
                second["best_response_values"],
                strict=True,
            )
        ),
        "deviation_gain_error": max(
            abs(float(left) - float(right))
            for left, right in zip(
                first["deviation_gains"],
                second["deviation_gains"],
                strict=True,
            )
        ),
        "nash_conv_error": abs(float(first["nash_conv"]) - float(second["nash_conv"])),
    }


def run_h32_resident_cfr_restart_semantics_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute the frozen repeated-restore and quality-equivalence audit."""

    parsed = parse_h32_resident_cfr_restart_semantics_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0123")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0123")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0123")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0123")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0123 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0123")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    failed_parent = tuple(
        key
        for key, value in parent["gates"].items()
        if key != "passed" and not bool(value)
    )
    expected_failed = (
        "restart_regret_error",
        "restart_strategy_sum_error",
        "restart_current_policy_identity",
        "restart_average_policy_identity",
        "restart_state_digest_identity",
    )
    teacher_config = parse_fresh_h32_strategy_transfer_config(
        json.loads(_TEACHER_CONFIG.read_text(encoding="utf-8"))
    )
    teacher = json.loads(_TEACHER.read_text(encoding="utf-8"))
    source_identity = (
        parent["status"] == "frozen_audit_executed"
        and not bool(parent["gates"]["passed"])
        and set(failed_parent) == set(expected_failed)
        and teacher["status"] == "frozen_audit_executed"
        and bool(teacher["gates"]["passed"])
    )
    if not source_identity:
        raise ValueError("ADR-0123 source identity rejected")

    started = time.perf_counter()
    board = parse_cards(*teacher_config["board"])
    source_belief, layout, sparse, retained = _build_case(
        parsed=teacher_config,
        board=board,
        hand_count=teacher_config["wide_hands_per_player"],
        family=parsed["range_family"],
    )
    source_workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    target_belief, descriptor = _build_target_belief(
        source_belief,
        board=board,
        shift=parsed["target_shift"],
        local_blocker_target_seat=teacher_config["local_blocker_target_seat"],
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=teacher_config["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    belief_cache, automaton_caches, cache_compile_ms = _resident_caches(
        workspace, automata
    )
    source = _source_row(teacher, parsed["range_family"])
    source_checkpoint = next(
        row for row in source["checkpoints"] if int(row["iteration"]) == 64
    )
    blueprint = _average_policy_from_state(source_checkpoint["state"])
    teacher_target = _target_row(
        teacher, parsed["range_family"], parsed["target_shift"]
    )
    teacher_eight = next(
        row
        for row in teacher_target["search"]["checkpoint_rows"]
        if int(row["iteration"]) == parsed["final_iteration"]
    )
    context = teacher_eight["state"]["context"]
    provenance = teacher_eight["state"]["provenance"]
    solver_args = {
        "parsed": {
            **teacher_config,
            "maximum_feature_width_per_batch": parsed[
                "maximum_feature_width_per_batch"
            ],
        },
        "teacher_config": teacher_config,
        "layout": layout,
        "workspace": workspace,
        "sparse": sparse,
        "automata": automata,
        "hands_by_player": target_belief.hands_by_player,
        "belief_cache": belief_cache,
        "automaton_caches": automaton_caches,
        "gpu": gpu,
    }
    warm_mass = teacher_config["warm_regret_mass_payoff_fraction"] * float(
        layout.game.payoff_span
    )
    uninterrupted_solver = _resident_solver(**solver_args)
    uninterrupted_solver.warm_start(blueprint, warm_mass)
    steps = _run_steps(uninterrupted_solver, parsed["split_iteration"])
    split = export_axis_cfr_checkpoint(
        uninterrupted_solver,
        context=context,
        provenance=provenance,
    )
    serialized_split = json.loads(
        json.dumps(split, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )

    restored_solvers = []
    immediate_rows = []
    for label in ("restored_a", "restored_b"):
        solver = _resident_solver(**solver_args)
        retained_metadata = restore_axis_cfr_checkpoint(solver, serialized_split)
        immediate = export_axis_cfr_checkpoint(
            solver,
            context=retained_metadata["context"],
            provenance=retained_metadata["provenance"],
        )
        immediate_rows.append(
            {
                "arm": label,
                "state_digest_identity": immediate["state_sha256"]
                == serialized_split["state_sha256"],
                "current_policy_identity": immediate["current_policy_sha256"]
                == serialized_split["current_policy_sha256"],
                "average_policy_identity": immediate["average_policy_sha256"]
                == serialized_split["average_policy_sha256"],
            }
        )
        restored_solvers.append((label, solver))

    steps.extend(
        _run_steps(
            uninterrupted_solver,
            parsed["final_iteration"] - parsed["split_iteration"],
        )
    )
    uninterrupted = _solver_snapshot(
        uninterrupted_solver, context=context, provenance=provenance
    )
    restored_snapshots = {}
    for label, solver in restored_solvers:
        steps.extend(
            _run_steps(solver, parsed["final_iteration"] - parsed["split_iteration"])
        )
        restored_snapshots[label] = _solver_snapshot(
            solver, context=context, provenance=provenance
        )

    continuation_rows = [
        _continuation_comparison(
            uninterrupted,
            restored_snapshots["restored_a"],
            label="uninterrupted_vs_restored_a",
        ),
        _continuation_comparison(
            restored_snapshots["restored_a"],
            restored_snapshots["restored_b"],
            label="restored_a_vs_restored_b",
        ),
    ]
    policies = {
        "uninterrupted_current8": uninterrupted["current"],
        "restored_a_current8": restored_snapshots["restored_a"]["current"],
        "uninterrupted_average8": uninterrupted["average"],
        "restored_a_average8": restored_snapshots["restored_a"]["average"],
    }
    quality_profiles = {}
    maximum_quality_gpu = 0
    for label in parsed["quality_policy_kinds"]:
        quality, evaluations = _resident_quality_row(
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            automata=automata,
            policy=policies[label],
            label=label,
            hands_by_player=target_belief.hands_by_player,
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            gpu=gpu,
            payoff_span=float(layout.game.payoff_span),
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        quality_profiles[label] = quality
        maximum_quality_gpu = max(
            maximum_quality_gpu,
            *(row.maximum_gpu_pool_total_bytes for row in evaluations),
        )
    quality_rows = [
        _quality_error(
            quality_profiles["uninterrupted_current8"],
            quality_profiles["restored_a_current8"],
            label="current8",
        ),
        _quality_error(
            quality_profiles["uninterrupted_average8"],
            quality_profiles["restored_a_average8"],
            label="average8",
        ),
    ]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    maximum_policy_error = max(
        max(
            row["current_policy_probability_error"],
            row["average_policy_probability_error"],
        )
        for row in continuation_rows
    )
    maximum_policy_tv = max(
        max(
            row["current_policy_mean_tv"], row["average_policy_mean_tv"]
        )
        for row in continuation_rows
    )
    gates = {
        "source_identity": source_identity,
        "parent_formal_failure": (not bool(parent["gates"]["passed"]))
        == gates_config["require_parent_formal_failure"],
        "parent_only_restart_gates_failed": (set(failed_parent) == set(expected_failed))
        == gates_config["require_parent_only_restart_gates_failed"],
        "training_steps": len(steps) == gates_config["expected_training_steps"],
        "immediate_restore_rows": len(immediate_rows)
        == gates_config["expected_immediate_restore_rows"],
        "quality_profiles": len(quality_profiles)
        == gates_config["expected_quality_profiles"],
        "quality_seat_evaluations": sum(
            len(row["seat_rows"]) for row in quality_profiles.values()
        )
        == gates_config["expected_quality_seat_evaluations"],
        "immediate_restore_state_digest_identity": all(
            row["state_digest_identity"] for row in immediate_rows
        )
        == gates_config["require_immediate_restore_state_digest_identity"],
        "immediate_restore_current_policy_identity": all(
            row["current_policy_identity"] for row in immediate_rows
        )
        == gates_config["require_immediate_restore_current_policy_identity"],
        "immediate_restore_average_policy_identity": all(
            row["average_policy_identity"] for row in immediate_rows
        )
        == gates_config["require_immediate_restore_average_policy_identity"],
        "continuation_regret_error": max(
            row["regret_error"] for row in continuation_rows
        )
        <= gates_config["maximum_continuation_regret_error"],
        "continuation_strategy_sum_error": max(
            row["strategy_sum_error"] for row in continuation_rows
        )
        <= gates_config["maximum_continuation_strategy_sum_error"],
        "continuation_policy_probability_error": maximum_policy_error
        <= gates_config["maximum_continuation_policy_probability_error"],
        "continuation_policy_mean_tv": maximum_policy_tv
        <= gates_config["maximum_continuation_policy_mean_tv"],
        "quality_utility_error": max(row["utility_error"] for row in quality_rows)
        <= gates_config["maximum_quality_utility_error"],
        "quality_best_response_error": max(
            row["best_response_error"] for row in quality_rows
        )
        <= gates_config["maximum_quality_best_response_error"],
        "quality_deviation_gain_error": max(
            row["deviation_gain_error"] for row in quality_rows
        )
        <= gates_config["maximum_quality_deviation_gain_error"],
        "quality_nash_conv_error": max(
            row["nash_conv_error"] for row in quality_rows
        )
        <= gates_config["maximum_quality_nash_conv_error"],
        "quality_zero_sum_residual": max(
            row["zero_sum_residual"] for row in quality_profiles.values()
        )
        <= gates_config["maximum_quality_zero_sum_residual"],
        "step_ms": max(row["wall_ms"] for row in steps)
        <= gates_config["maximum_step_ms"],
        "quality_profile_ms": max(
            row["wall_ms"] for row in quality_profiles.values()
        )
        <= gates_config["maximum_quality_profile_ms"],
        "gpu_pool_bytes": max(
            maximum_quality_gpu,
            *(row["maximum_gpu_pool_bytes"] for row in steps),
        )
        <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())

    public_quality = {
        label: {
            key: value
            for key, value in row.items()
            if key != "seat_rows"
        }
        for label, row in quality_profiles.items()
    }
    result = {
        "schema_version": 1,
        "status": "frozen_successor_audit_executed",
        "experiment_type": "h32_resident_cfr_restart_semantics",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "parent": _sha256(_PARENT),
            "parent_config": _sha256(_PARENT_CONFIG),
            "parent_decision": _sha256(_PARENT_DECISION),
            "teacher": _sha256(_TEACHER),
            "teacher_config": _sha256(_TEACHER_CONFIG),
            "fresh_implementation": _sha256(_FRESH_IMPLEMENTATION),
            "resident_cfr": _sha256(_RESIDENT_CFR),
            "resident_evaluation": _sha256(_RESIDENT_EVALUATION),
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
        "target_descriptor": descriptor,
        "cache_compile_ms": cache_compile_ms,
        "split_checkpoint_sha256": serialized_split["state_sha256"],
        "immediate_restore_rows": immediate_rows,
        "continuation_rows": continuation_rows,
        "quality_profiles": public_quality,
        "quality_comparison_rows": quality_rows,
        "counts": {
            "training_steps": len(steps),
            "immediate_restore_rows": len(immediate_rows),
            "quality_profiles": len(quality_profiles),
            "quality_seat_evaluations": sum(
                len(row["seat_rows"]) for row in quality_profiles.values()
            ),
            "new_candidate_directions": 0,
        },
        "resources": {
            "maximum_gpu_pool_bytes": max(
                maximum_quality_gpu,
                *(row["maximum_gpu_pool_bytes"] for row in steps),
            ),
        },
        "timing": {"total_seconds": total_seconds},
        "gates": gates,
        "limitations": [
            "The correction is tested on one balanced/local target only.",
            (
                "Numerical continuation identity does not promise bitwise "
                "deterministic CUDA reductions."
            ),
            (
                "Quality equivalence through iteration eight does not establish "
                "64-step training equivalence."
            ),
            "No new candidate, selector, action tree, or strategy-improvement claim is introduced.",
        ],
    }
    del restored_solvers, uninterrupted_solver, automaton_caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    result = run_h32_resident_cfr_restart_semantics_audit(config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(arguments.output), "gates": result["gates"]}))


if __name__ == "__main__":
    main()
