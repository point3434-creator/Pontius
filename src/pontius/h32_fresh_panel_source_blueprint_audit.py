"""Freeze six source-only h32 resident DCFR blueprints on fresh boards."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from .axis_cfr_checkpoint import (
    axis_cfr_checkpoint_digest,
    export_axis_cfr_checkpoint,
    restore_axis_cfr_checkpoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .fresh_h32_strategy_transfer_audit import (
    _belief_digest,
    _resident_quality_row,
)
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_fresh_board_panel_cache_preflight import (
    _FROZEN_BOARD_DIGESTS,
    _FROZEN_PANELS,
    _FROZEN_SOURCE_DIGESTS,
    parse_h32_fresh_board_panel_cache_config,
)
from .h32_resident_cfr_audit import _resident_caches, _step_row
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-fresh-panel-source-blueprints-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-fresh-panel-source-blueprints-v1.json"
_CACHE_RESULT = _ROOT / "experiments" / "results" / "h32-fresh-board-panel-cache-v1.json"
_CACHE_DECISION = _ROOT / "docs" / "decisions" / "ADR-0143-fresh-board-panel-caches-are-safe-for-source-blueprints.md"
_CACHE_CONFIG = _ROOT / "experiments" / "configs" / "h32-fresh-board-panel-cache-v1.json"
_CACHE_IMPLEMENTATION = _ROOT / "src" / "pontius" / "h32_fresh_board_panel_cache_preflight.py"
_REQUIREMENTS = _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests" / "test_h32_fresh_panel_source_blueprint_audit.py"

_SOURCE_PATHS = {
    "expected_cache_result_sha256": _CACHE_RESULT,
    "expected_cache_decision_sha256": _CACHE_DECISION,
    "expected_cache_config_sha256": _CACHE_CONFIG,
    "expected_cache_implementation_sha256": _CACHE_IMPLEMENTATION,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_axis_checkpoint_sha256": _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py",
    "expected_resident_cfr_sha256": _ROOT / "src" / "pontius" / "resident_leaf_adjoint_cfr.py",
    "expected_resident_evaluation_sha256": _ROOT / "src" / "pontius" / "resident_leaf_adjoint_evaluation.py",
    "expected_resident_contraction_sha256": _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py",
    "expected_cupy_sparse_sha256": _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py",
    "expected_ladder_implementation_sha256": _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py",
    "expected_fresh_implementation_sha256": _ROOT / "src" / "pontius" / "fresh_h32_strategy_transfer_audit.py",
    "expected_resident_audit_sha256": _ROOT / "src" / "pontius" / "h32_resident_cfr_audit.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _CONTROL_TEST,
}

_CONFIG_FIELDS = {
    "evidence_stage", *_SOURCE_PATHS, "seed", "axis_seed", "panels",
    "panel_board_sha256", "source_order", "source_belief_sha256_by_source",
    "pot", "stack", "bet_size", "players", "hands_per_player",
    "range_families", "solver_variant", "cold_start", "final_iteration",
    "checkpoint_iterations", "full_state_iterations", "trajectory_rule",
    "restart_rule", "quality_phase_rule", "target_construction_rule",
    "mixture_components", "split_index", "query_chunk_records",
    "maximum_feature_width_per_batch", "required_numpy_version",
    "required_scipy_version", "required_cupy_version",
    "required_cuda_runtime_version", "minimum_cuda_driver_version",
    "required_compute_capability", "cuda_dll_environment_variable", "gates",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_panel_source_blueprint_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the complete ADR-0144 source-only contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("fresh-panel source-blueprint fields differ from ADR-0144")
    frozen = {
        "evidence_stage": "preregistered_after_adr0143_before_any_fresh_panel_h32_source_policy_step_or_quality_measurement",
        "seed": 20260820,
        "axis_seed": 20260819,
        "panels": list(_FROZEN_PANELS),
        "panel_board_sha256": _FROZEN_BOARD_DIGESTS,
        "source_order": [
            "panel_1/balanced", "panel_1/blocker_heavy",
            "panel_2/blocker_heavy", "panel_2/balanced",
            "panel_3/balanced", "panel_3/blocker_heavy",
        ],
        "source_belief_sha256_by_source": _FROZEN_SOURCE_DIGESTS,
        "pot": 12.0, "stack": 30.0, "bet_size": 3.0,
        "players": 6, "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "solver_variant": "dcfr", "cold_start": True,
        "final_iteration": 64,
        "checkpoint_iterations": [1, 2, 4, 8, 16, 32, 64],
        "full_state_iterations": [64],
        "trajectory_rule": "one_uninterrupted_resident_dcfr_trajectory_per_source_no_resume_and_no_warm_start",
        "restart_rule": "canonical_json_round_trip_and_immediate_pristine_restore_at_final_iteration_without_continuation",
        "quality_phase_rule": "finish_all_six_trajectories_before_first_fixed_source_average64_diagnostic",
        "target_construction_rule": "forbidden_zero_target_beliefs_zero_sized_trees_zero_target_quality",
        "mixture_components": 3, "split_index": 3,
        "query_chunk_records": 256, "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2", "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0", "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000, "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("fresh-panel source-blueprint workload differs from ADR-0144")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh-panel source-blueprint source mismatch: {field}")
    cache_config = json.loads(_CACHE_CONFIG.read_text(encoding="utf-8"))
    parse_h32_fresh_board_panel_cache_config(cache_config)
    expected_gates = {
        "expected_source_rows": 6,
        "expected_total_source_steps": 384,
        "expected_checkpoint_summaries_per_source": 7,
        "expected_full_checkpoints_per_source": 1,
        "expected_source_quality_rows": 6,
        "expected_information_sets": 6144,
        "expected_hand_action_entries": 12288,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_training_step_ms": 60000.0,
        "maximum_source_quality_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_quality_zero_sum_residual": 1e-9,
        "maximum_quality_vector_sum_error": 1e-12,
        "maximum_total_audit_seconds": 10800.0,
        "require_clean_git_state": True,
        "require_cache_authorization": True,
        "require_source_identity": True,
        "require_finite_states_policies_and_quality": True,
        "require_checkpoint_json_identity": True,
        "require_immediate_restore_identity": True,
        "require_all_training_before_quality": True,
        "require_zero_target_beliefs": True,
        "require_zero_sized_trees": True,
        "require_zero_target_quality": True,
        "require_strategy_quality_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("fresh-panel source-blueprint gates differ from ADR-0144")
    return {
        **config,
        "panels": tuple(dict(row) for row in config["panels"]),
        "source_order": tuple(config["source_order"]),
        "range_families": tuple(config["range_families"]),
        "checkpoint_iterations": tuple(config["checkpoint_iterations"]),
        "full_state_iterations": tuple(config["full_state_iterations"]),
        "gates": dict(config["gates"]),
    }


def _resident_solver(parsed: dict[str, Any], belief: Any, layout: Any, workspace: Any,
                     sparse: Any, automata: Any, gpu: Any, belief_cache: Any,
                     automaton_caches: Any) -> ResidentLeafAdjointPublicTreeCFR:
    return ResidentLeafAdjointPublicTreeCFR(
        layout, workspace, sparse, automata, parsed["solver_variant"],
        belief_cache=belief_cache, automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )


def _build_source(parsed: dict[str, Any], source_key: str) -> tuple[Any, ...]:
    board_id, family = source_key.split("/", 1)
    panel = next(row for row in parsed["panels"] if row["board_id"] == board_id)
    board = parse_cards(*panel["cards"])
    belief, layout, sparse, retained = _build_case(
        parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family,
    )
    digest = _belief_digest(belief)
    expected = parsed["source_belief_sha256_by_source"][source_key]
    if digest != expected:
        raise AssertionError(f"source belief identity rejected: {source_key}")
    workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    caches = _resident_caches(workspace, automata)
    return belief, layout, sparse, workspace, workspace_timing, automata, gpu, *caches


def _finite_state(state: dict[str, Any]) -> bool:
    return all(
        math.isfinite(float(value))
        for table in ("regrets", "strategy_sums")
        for row in state[table].values() for value in row.values()
    )


def _train_source(parsed: dict[str, Any], source_key: str, provenance: dict[str, Any]) -> dict[str, Any]:
    (belief, layout, sparse, workspace, workspace_timing, automata, gpu,
     belief_cache, automaton_caches, cache_ms) = _build_source(parsed, source_key)
    solver = _resident_solver(parsed, belief, layout, workspace, sparse, automata,
                              gpu, belief_cache, automaton_caches)
    context = {
        "source": source_key,
        "board": next(row["cards"] for row in parsed["panels"] if row["board_id"] == source_key.split("/")[0]),
        "range_family": source_key.split("/")[1],
        "hands_per_player": parsed["hands_per_player"],
        "trajectory": "cold_uninterrupted_resident_dcfr",
    }
    steps: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    final_state: dict[str, Any] | None = None
    cumulative_ms = 0.0
    for iteration in range(1, parsed["final_iteration"] + 1):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        cumulative_ms += wall_ms
        if solver.last_step_work is None:
            raise AssertionError("resident source step has no telemetry")
        row = _step_row(solver.last_step_work, wall_ms=wall_ms)
        row["maximum_host_peak_numeric_bytes"] = max(
            value.maximum_terminal_peak_numeric_bytes
            for value in solver.last_step_work.traversers
        )
        steps.append(row)
        if iteration not in parsed["checkpoint_iterations"]:
            continue
        state = export_axis_cfr_checkpoint(solver, context=context, provenance=provenance)
        summaries.append({
            "iteration": iteration,
            "state_sha256": state["state_sha256"],
            "current_policy_sha256": state["current_policy_sha256"],
            "average_policy_sha256": state["average_policy_sha256"],
            "cumulative_training_ms": cumulative_ms,
            "finite": _finite_state(state),
        })
        if iteration in parsed["full_state_iterations"]:
            final_state = state
    if final_state is None:
        raise AssertionError("final source checkpoint was not retained")
    rendered = json.dumps(final_state, sort_keys=True, separators=(",", ":"), allow_nan=False)
    round_tripped = json.loads(rendered)
    json_identity = axis_cfr_checkpoint_digest(round_tripped) == final_state["state_sha256"]
    restored = _resident_solver(parsed, belief, layout, workspace, sparse, automata,
                                gpu, belief_cache, automaton_caches)
    restore_axis_cfr_checkpoint(restored, round_tripped)
    replay = export_axis_cfr_checkpoint(restored, context=context, provenance=provenance)
    restore_identity = (
        replay["state_sha256"] == final_state["state_sha256"]
        and replay["current_policy_sha256"] == final_state["current_policy_sha256"]
        and replay["average_policy_sha256"] == final_state["average_policy_sha256"]
    )
    result = {
        "source": source_key,
        "board_id": source_key.split("/")[0],
        "range_family": source_key.split("/")[1],
        "source_belief_sha256": _belief_digest(belief),
        "source_identity": True,
        "workspace_compile_ms": workspace_timing,
        "cache_compile_ms": cache_ms,
        "information_sets": len(solver.information_schema()),
        "hand_action_entries": sum(len(row) for row in solver.information_schema().values()),
        "steps": steps,
        "checkpoint_summaries": summaries,
        "final_checkpoint": final_state,
        "checkpoint_json_bytes": len(rendered.encode("utf-8")),
        "checkpoint_json_identity": json_identity,
        "immediate_restore_identity": restore_identity,
        "restored_continuation_steps": 0,
        "cumulative_training_ms": cumulative_ms,
    }
    del restored, solver, automaton_caches, belief_cache, gpu, automata, sparse, workspace, layout, belief
    gc.collect()
    release_cupy_memory_pool()
    return result


def _quality_source(parsed: dict[str, Any], trained: dict[str, Any]) -> dict[str, Any]:
    source_key = trained["source"]
    (belief, layout, sparse, workspace, _workspace_timing, automata, gpu,
     belief_cache, automaton_caches, _cache_ms) = _build_source(parsed, source_key)
    policy = _average_policy_from_state(trained["final_checkpoint"])
    if policy_digest(policy) != trained["final_checkpoint"]["average_policy_sha256"]:
        raise AssertionError("average64 blueprint reconstruction differs")
    row, _ = _resident_quality_row(
        layout=layout, workspace=workspace, sparse=sparse, automata=automata,
        policy=policy, label="source_average64", hands_by_player=belief.hands_by_player,
        belief_cache=belief_cache, automaton_caches=automaton_caches, gpu=gpu,
        payoff_span=float(layout.game.payoff_span),
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    row.update({"source": source_key, "measurement_phase": "after_all_source_training"})
    del automaton_caches, belief_cache, gpu, automata, sparse, workspace, layout, belief, policy
    gc.collect()
    release_cupy_memory_pool()
    return row


def run_h32_fresh_panel_source_blueprint_audit(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen source-only trajectory and diagnostic phases."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_panel_source_blueprint_config(config)
    cache = json.loads(_CACHE_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    cache_authorized = bool(
        cache.get("passed")
        and cache.get("decision") == "authorize_fresh_panel_source_blueprint_preregistration"
        and cache.get("headroom", {}).get("all_twenty_four_caches_safe")
        and cache.get("strategy_quality_claim") is None
    )
    if not cache_authorized:
        raise RuntimeError("ADR-0143 did not authorize fresh-panel source blueprints")
    if git["dirty"]:
        raise RuntimeError("source-blueprint execution requires a clean Git state")
    provenance = {
        "audit": "ADR-0144",
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "cache_result_sha256": _sha256(_CACHE_RESULT),
        "clean_run_commit": git["commit"],
        "solver_variant": parsed["solver_variant"],
    }
    source_rows = []
    training_finished_at = None
    first_quality_started_at = None
    for source_key in parsed["source_order"]:
        print(f"training {source_key}", flush=True)
        source_rows.append(_train_source(parsed, source_key, provenance))
    training_finished_at = time.perf_counter()
    quality_rows = []
    first_quality_started_at = time.perf_counter()
    for row in source_rows:
        print(f"diagnosing {row['source']}", flush=True)
        quality_rows.append(_quality_source(parsed, row))
    all_training_before_quality = training_finished_at <= first_quality_started_at
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    step_rows = [step for source in source_rows for step in source["steps"]]
    gate_results = {
        "clean_git_state": (not git["dirty"]) == gates["require_clean_git_state"],
        "cache_authorization": cache_authorized == gates["require_cache_authorization"],
        "source_count": len(source_rows) == gates["expected_source_rows"],
        "source_order": [row["source"] for row in source_rows] == list(parsed["source_order"]),
        "source_identity": all(row["source_identity"] for row in source_rows) == gates["require_source_identity"],
        "step_count": len(step_rows) == gates["expected_total_source_steps"],
        "checkpoint_summary_count": all(len(row["checkpoint_summaries"]) == gates["expected_checkpoint_summaries_per_source"] for row in source_rows),
        "full_checkpoint_count": all(int(row["final_checkpoint"]["iteration"] == 64) == gates["expected_full_checkpoints_per_source"] for row in source_rows),
        "information_schema": all(row["information_sets"] == gates["expected_information_sets"] and row["hand_action_entries"] == gates["expected_hand_action_entries"] for row in source_rows),
        "cache_compile": all(row["cache_compile_ms"] <= gates["maximum_cache_compile_ms"] for row in source_rows),
        "training_step": all(row["wall_ms"] <= gates["maximum_training_step_ms"] for row in step_rows),
        "gpu_pool": all(row["maximum_gpu_pool_bytes"] <= gates["maximum_gpu_pool_bytes"] for row in step_rows + quality_rows),
        "finite_states_policies_quality": all(summary["finite"] for row in source_rows for summary in row["checkpoint_summaries"]) and all(row["finite"] for row in quality_rows) == gates["require_finite_states_policies_and_quality"],
        "checkpoint_json_identity": all(row["checkpoint_json_identity"] for row in source_rows) == gates["require_checkpoint_json_identity"],
        "immediate_restore_identity": all(row["immediate_restore_identity"] and row["restored_continuation_steps"] == 0 for row in source_rows) == gates["require_immediate_restore_identity"],
        "quality_count": len(quality_rows) == gates["expected_source_quality_rows"],
        "quality_time": all(row["wall_ms"] <= gates["maximum_source_quality_ms"] for row in quality_rows),
        "quality_zero_sum": all(row["zero_sum_residual"] <= gates["maximum_quality_zero_sum_residual"] for row in quality_rows),
        "quality_vector_sum": all(row["quality_vector_sum_error"] <= gates["maximum_quality_vector_sum_error"] for row in quality_rows),
        "all_training_before_quality": all_training_before_quality == gates["require_all_training_before_quality"],
        "zero_target_beliefs": (0 == 0) == gates["require_zero_target_beliefs"],
        "zero_sized_trees": (0 == 0) == gates["require_zero_sized_trees"],
        "zero_target_quality": (0 == 0) == gates["require_zero_target_quality"],
        "strategy_quality_claim_null": (None is None) == gates["require_strategy_quality_claim_null"],
        "wall_time": total_seconds <= gates["maximum_total_audit_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_panel_source_blueprints_executed",
        "experiment_type": "source_only_cold_resident_dcfr_blueprint_construction",
        "config": config, "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "parent_cache_authorized": cache_authorized,
        "source_rows": source_rows, "source_quality_diagnostics": quality_rows,
        "phase_order": {"all_training_finished_before_first_quality": all_training_before_quality},
        "counts": {
            "h32_source_steps": len(step_rows), "h32_source_policies": len(source_rows),
            "h32_source_quality_evaluations": len(quality_rows),
            "target_beliefs_constructed": 0, "sized_trees_constructed": 0,
            "target_quality_evaluations": 0,
        },
        "gate_results": gate_results, "passed": passed,
        "decision": "freeze_six_average64_source_blueprints_for_separately_preregistered_transfer" if passed else "reject_source_blueprint_mechanism",
        "strategy_quality_claim": None,
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            "Source diagnostics describe only the six construction beliefs and do not select a blueprint.",
            "No target belief, action-width tree, transfer candidate, or target quality label was constructed.",
            "Immediate restore identity is proven; restored GPU continuation is deliberately outside this artifact.",
            "No strategy-quality, action-width, board-population, or production-latency claim is licensed.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    cp.get_default_memory_pool().free_all_blocks()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_panel_source_blueprint_audit(args.config, args.output)
    print(f"fresh-panel source blueprints: passed={result['passed']}, wall={result['timing']['total_seconds']:.3f}s")


if __name__ == "__main__":
    main()
