"""Two-step one-size transfer audit over twelve frozen fresh-panel targets."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest, export_axis_cfr_checkpoint, restore_axis_cfr_checkpoint
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest, _finite_policy, _resident_quality_row
from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_current_interpolation_audit import interpolate_behavioral_policy
from .h32_fresh_board_panel_cache_preflight import (
    _FROZEN_DESCRIPTOR_DIGESTS, _FROZEN_PANELS, _FROZEN_SOURCE_DIGESTS,
    _FROZEN_TARGET_DIGESTS, _json_digest,
)
from .h32_resident_cfr_audit import _resident_caches, _step_row
from .h32_warm_search_acceptance_audit import _average_policy_from_state, build_target_belief
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-panel-target-transfer-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_ADR = _ROOT / "docs/decisions/ADR-0145-six-fresh-panel-source-blueprints-are-frozen.md"
_CACHE_CONFIG = _ROOT / "experiments/configs/h32-fresh-board-panel-cache-v1.json"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_panel_target_transfer_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_source_decision_sha256": _SOURCE_ADR,
    "expected_cache_config_sha256": _CACHE_CONFIG,
    "expected_axis_checkpoint_sha256": _ROOT / "src/pontius/axis_cfr_checkpoint.py",
    "expected_resident_cfr_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py",
    "expected_resident_evaluation_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_evaluation.py",
    "expected_fixed_selection_sha256": _ROOT / "src/pontius/h32_acceptance_semantics_replay.py",
    "expected_interpolation_sha256": _ROOT / "src/pontius/h32_current_interpolation_audit.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_panel_target_transfer_config(config: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "evidence_stage", *_PATHS, "panels", "source_order", "source_belief_sha256_by_source",
        "target_belief_sha256_by_target", "target_descriptor_sha256_by_target", "target_shifts",
        "target_order", "local_blocker_target_seat", "pot", "stack", "bet_size", "players",
        "hands_per_player", "range_families", "axis_seed", "solver_variant", "blueprint_point",
        "warm_regret_mass_payoff_fraction", "search_iterations", "interpolation_alphas",
        "candidate_order", "acceptance_guard_normalized", "certificate_anchor_rule",
        "mixture_components", "split_index", "query_chunk_records", "maximum_feature_width_per_batch",
        "required_numpy_version", "required_scipy_version", "required_cupy_version",
        "required_cuda_runtime_version", "minimum_cuda_driver_version", "required_compute_capability",
        "cuda_dll_environment_variable", "gates",
    }
    if set(config) != fields:
        raise ValueError("fresh-panel target-transfer fields differ from ADR-0146")
    source_order = [
        "panel_1/balanced", "panel_1/blocker_heavy", "panel_2/blocker_heavy",
        "panel_2/balanced", "panel_3/balanced", "panel_3/blocker_heavy",
    ]
    target_order = [f"{source}/{shift}" for source in source_order for shift in ("local_blocker_seat3_x2", "all_seat_strength_1_to2")]
    frozen = {
        "evidence_stage": "preregistered_after_adr0145_before_any_fresh_panel_target_policy_step_or_quality_measurement",
        "panels": list(_FROZEN_PANELS), "source_order": source_order,
        "source_belief_sha256_by_source": _FROZEN_SOURCE_DIGESTS,
        "target_belief_sha256_by_target": _FROZEN_TARGET_DIGESTS,
        "target_descriptor_sha256_by_target": _FROZEN_DESCRIPTOR_DIGESTS,
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "target_order": target_order, "local_blocker_target_seat": 3,
        "pot": 12.0, "stack": 30.0, "bet_size": 3.0, "players": 6,
        "hands_per_player": 32, "range_families": ["balanced", "blocker_heavy"],
        "axis_seed": 20260819, "solver_variant": "dcfr", "blueprint_point": "64:average",
        "warm_regret_mass_payoff_fraction": 0.1, "search_iterations": [1, 2],
        "interpolation_alphas": [0.25, 0.5, 0.75],
        "candidate_order": ["search_current1", "search_current2", "search_average2",
                            "interpolate_current1_to2_alpha025", "interpolate_current1_to2_alpha050",
                            "interpolate_current1_to2_alpha075"],
        "acceptance_guard_normalized": 1e-10,
        "certificate_anchor_rule": "immutable_source_average64_one_shot_target_certificate_never_reanchors",
        "mixture_components": 3, "split_index": 3, "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2", "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0", "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000, "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("fresh-panel target-transfer workload differs from ADR-0146")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh-panel target-transfer source mismatch: {field}")
    gates = {
        "expected_target_rows": 12, "expected_target_search_steps": 24,
        "expected_candidate_profiles": 72, "expected_blueprint_profiles": 12,
        "expected_information_sets": 6144, "expected_hand_action_entries": 12288,
        "maximum_target_compile_ms": 30000.0, "maximum_cache_compile_ms": 120000.0,
        "maximum_training_step_ms": 60000.0, "maximum_quality_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000, "maximum_zero_sum_residual": 1e-9,
        "maximum_quality_vector_sum_error": 1e-12, "maximum_interpolation_normalization_error": 1e-12,
        "maximum_total_audit_seconds": 5400.0, "require_clean_git_state": True,
        "require_source_checkpoint_identity": True, "require_target_identity": True,
        "require_warm_start_identity": True, "require_target_checkpoint_identity": True,
        "require_fixed_envelope_cap_compliance": True, "require_certificate_scope": True,
        "require_finite": True, "require_zero_sized_trees": True,
        "require_action_width_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh-panel target-transfer gates differ from ADR-0146")
    return {**config, "panels": tuple(config["panels"]), "source_order": tuple(source_order),
            "target_shifts": tuple(config["target_shifts"]), "target_order": tuple(target_order),
            "search_iterations": tuple(config["search_iterations"]),
            "interpolation_alphas": tuple(config["interpolation_alphas"]),
            "candidate_order": tuple(config["candidate_order"]), "gates": dict(gates)}


def _solver(parsed: dict[str, Any], belief: Any, layout: Any, workspace: Any, sparse: Any,
            automata: Any, gpu: Any, belief_cache: Any, automaton_caches: Any) -> ResidentLeafAdjointPublicTreeCFR:
    return ResidentLeafAdjointPublicTreeCFR(
        layout, workspace, sparse, automata, parsed["solver_variant"], belief_cache=belief_cache,
        automaton_caches=automaton_caches, cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )


def _cap(blueprint: dict[str, Any], quality: dict[str, Any], raw_guard: float) -> dict[str, Any]:
    excess = [float(new) - float(old) - raw_guard for old, new in zip(blueprint["deviation_gains"], quality["deviation_gains"], strict=True)]
    violating = [seat for seat, value in enumerate(excess) if value > 0.0]
    return {"feasible": not violating, "cap_excesses": excess, "maximum_cap_excess": max(excess), "violating_seats": violating}


def _finite_state(state: dict[str, Any]) -> bool:
    return all(math.isfinite(float(v)) for table in ("regrets", "strategy_sums") for row in state[table].values() for v in row.values())


def _run_target(parsed: dict[str, Any], parent: dict[str, Any], target_key: str, provenance: dict[str, Any]) -> dict[str, Any]:
    board_id, family, shift = target_key.split("/", 2)
    panel = next(row for row in parsed["panels"] if row["board_id"] == board_id)
    board = parse_cards(*panel["cards"])
    source_belief, layout, sparse, retained = _build_case(parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family)
    source_workspace, _timing, automata = retained
    if _belief_digest(source_belief) != parsed["source_belief_sha256_by_source"][f"{board_id}/{family}"]:
        raise AssertionError("source belief identity rejected")
    parent_row = next(row for row in parent["source_rows"] if row["source"] == f"{board_id}/{family}")
    state = parent_row["final_checkpoint"]
    source_identity = axis_cfr_checkpoint_digest(state) == state["state_sha256"] and state["average_policy_sha256"] == parent_row["final_checkpoint"]["average_policy_sha256"]
    blueprint = _average_policy_from_state(state)
    target_belief, descriptor = build_target_belief(source_belief, board=board, shift=shift, local_blocker_target_seat=parsed["local_blocker_target_seat"])
    target_digest = _belief_digest(target_belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = target_digest == parsed["target_belief_sha256_by_target"][target_key] and descriptor_digest == parsed["target_descriptor_sha256_by_target"][target_key]
    started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(source_workspace.topology.base, target_belief, query_chunk_records=parsed["query_chunk_records"])
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    target_compile_ms = (time.perf_counter() - started) * 1000.0
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache, automaton_caches, cache_ms = _resident_caches(workspace, automata)
    solver = _solver(parsed, target_belief, layout, workspace, sparse, automata, gpu, belief_cache, automaton_caches)
    solver.warm_start(blueprint, parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span))
    warm_identity = policy_digest(solver.current_strategy()) == policy_digest(blueprint)
    currents, averages, steps, checkpoints = {}, {}, [], []
    for iteration in parsed["search_iterations"]:
        tick = time.perf_counter(); solver.step(); wall = (time.perf_counter() - tick) * 1000.0
        if solver.last_step_work is None: raise AssertionError("target step telemetry absent")
        steps.append(_step_row(solver.last_step_work, wall_ms=wall))
        currents[iteration], averages[iteration] = solver.current_strategy(), solver.average_strategy()
        checkpoint = export_axis_cfr_checkpoint(solver, context={"target": target_key}, provenance=provenance)
        rendered = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"), allow_nan=False)
        checkpoints.append({"iteration": iteration, "state_sha256": checkpoint["state_sha256"],
                            "current_policy_sha256": checkpoint["current_policy_sha256"],
                            "average_policy_sha256": checkpoint["average_policy_sha256"],
                            "json_bytes": len(rendered.encode()), "finite": _finite_state(checkpoint),
                            "json_identity": axis_cfr_checkpoint_digest(json.loads(rendered)) == checkpoint["state_sha256"]})
    final = export_axis_cfr_checkpoint(solver, context={"target": target_key}, provenance=provenance)
    restored = _solver(parsed, target_belief, layout, workspace, sparse, automata, gpu, belief_cache, automaton_caches)
    restore_axis_cfr_checkpoint(restored, json.loads(json.dumps(final, sort_keys=True, separators=(",", ":"))))
    replay = export_axis_cfr_checkpoint(restored, context={"target": target_key}, provenance=provenance)
    restore_identity = replay["state_sha256"] == final["state_sha256"]
    policies = {"search_current1": currents[1], "search_current2": currents[2], "search_average2": averages[2]}
    interpolation = []
    for alpha in parsed["interpolation_alphas"]:
        name = f"interpolate_current1_to2_alpha{int(alpha * 100):03d}"
        policy = interpolate_behavioral_policy(currents[1], currents[2], alpha); policies[name] = policy
        interpolation.append({"candidate_id": name, "alpha": alpha, "maximum_normalization_error": max(abs(math.fsum(row.values()) - 1.0) for row in policy.values())})
    if tuple(policies) != parsed["candidate_order"]: raise AssertionError("candidate order differs")
    payoff_span = float(layout.game.payoff_span)
    blueprint_quality, _ = _resident_quality_row(layout=layout, workspace=workspace, sparse=sparse, automata=automata,
        policy=blueprint, label="blueprint_average64", hands_by_player=target_belief.hands_by_player,
        belief_cache=belief_cache, automaton_caches=automaton_caches, gpu=gpu, payoff_span=payoff_span,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"])
    raw_guard = parsed["acceptance_guard_normalized"] * payoff_span
    candidates = []
    for candidate_id, policy in policies.items():
        quality, _ = _resident_quality_row(layout=layout, workspace=workspace, sparse=sparse, automata=automata,
            policy=policy, label=candidate_id, hands_by_player=target_belief.hands_by_player,
            belief_cache=belief_cache, automaton_caches=automaton_caches, gpu=gpu, payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"])
        candidates.append({"candidate_id": candidate_id, "policy_sha256": policy_digest(policy), "quality": quality,
                           "cap_diagnostics": _cap(blueprint_quality, quality, raw_guard), "finite": _finite_policy(policy) and quality["finite"]})
    blueprint_row = {"candidate_id": "blueprint_average64", "quality": blueprint_quality}
    selection = select_fixed_blueprint_envelope(blueprint_row, candidates, raw_guard=raw_guard)
    selected_quality = blueprint_quality if selection["selected_candidate_id"] == "blueprint_average64" else next(row["quality"] for row in candidates if row["candidate_id"] == selection["selected_candidate_id"])
    certificate = {"anchor_rule": parsed["certificate_anchor_rule"], "source_checkpoint_state_sha256": state["state_sha256"],
                   "episode_blueprint_policy_sha256": policy_digest(blueprint), "target_belief_sha256": target_digest,
                   "blueprint_deviation_gains": blueprint_quality["deviation_gains"],
                   "cap_vector": [float(v) + raw_guard for v in blueprint_quality["deviation_gains"]], "raw_guard": raw_guard,
                   "expires_after_public_transition": True, "selected_candidate_becomes_anchor": False,
                   "cumulative_episode_safety_claim": False}
    result = {"target": target_key, "board_id": board_id, "range_family": family, "target_shift": shift,
              "source_checkpoint_identity": source_identity, "target_belief_sha256": target_digest,
              "target_descriptor_sha256": descriptor_digest, "target_descriptor": descriptor, "target_identity": target_identity,
              "target_axes_identity": target_belief.hands_by_player == source_belief.hands_by_player,
              "target_workspace_compile_ms": target_compile_ms, "cache_compile_ms": cache_ms,
              "information_sets": len(solver.information_schema()), "hand_action_entries": sum(len(v) for v in solver.information_schema().values()),
              "warm_start_identity": warm_identity, "search_steps": steps, "search_checkpoints": checkpoints,
              "final_restore_identity": restore_identity, "restored_continuation_steps": 0, "interpolation": interpolation,
              "blueprint_quality": blueprint_quality, "candidates": candidates, "selection": selection,
              "strategy_outcome": {"selected_candidate_id": selection["selected_candidate_id"],
                  "selected_policy_sha256": selection["selected_policy_sha256"],
                  "selected_normalized_nash_conv_reduction": float(blueprint_quality["normalized_nash_conv"]) - float(selected_quality["normalized_nash_conv"]),
                  "blueprint_abstention": selection["blueprint_abstention"]},
              "certificate": certificate}
    del restored, solver, automaton_caches, belief_cache, gpu, workspace, base, automata, source_workspace, sparse, layout, target_belief, source_belief
    gc.collect(); release_cupy_memory_pool()
    return result


def run_h32_fresh_panel_target_transfer_audit(config_path: Path = _CONFIG, output_path: Path = _OUTPUT) -> dict[str, Any]:
    started = time.perf_counter(); config = json.loads(config_path.read_text(encoding="utf-8")); parsed = parse_h32_fresh_panel_target_transfer_config(config)
    parent = json.loads(_SOURCE.read_text(encoding="utf-8")); git = _strict_git_metadata(); cp, runtime = _validate_runtime(parsed)
    if git["dirty"]: raise RuntimeError("target transfer requires a clean Git state")
    provenance = {"audit": "ADR-0146", "config_sha256": _sha256(config_path), "implementation_sha256": _sha256(_IMPLEMENTATION), "source_result_sha256": _sha256(_SOURCE), "clean_run_commit": git["commit"]}
    targets = []
    for key in parsed["target_order"]:
        print(f"transferring {key}", flush=True); targets.append(_run_target(parsed, parent, key, provenance))
    gates = parsed["gates"]; steps = [s for t in targets for s in t["search_steps"]]; candidates = [c for t in targets for c in t["candidates"]]
    qualities = [t["blueprint_quality"] for t in targets] + [c["quality"] for c in candidates]
    gate_results = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"], "target_count": len(targets) == gates["expected_target_rows"],
        "step_count": len(steps) == gates["expected_target_search_steps"], "candidate_count": len(candidates) == gates["expected_candidate_profiles"],
        "blueprint_count": len(targets) == gates["expected_blueprint_profiles"],
        "schema": all(t["information_sets"] == gates["expected_information_sets"] and t["hand_action_entries"] == gates["expected_hand_action_entries"] for t in targets),
        "source_identity": all(t["source_checkpoint_identity"] for t in targets) == gates["require_source_checkpoint_identity"],
        "target_identity": all(t["target_identity"] and t["target_axes_identity"] for t in targets) == gates["require_target_identity"],
        "warm_identity": all(t["warm_start_identity"] for t in targets) == gates["require_warm_start_identity"],
        "checkpoint_identity": all(c["json_identity"] and c["finite"] for t in targets for c in t["search_checkpoints"]) and all(t["final_restore_identity"] and t["restored_continuation_steps"] == 0 for t in targets) == gates["require_target_checkpoint_identity"],
        "cap_compliance": all(not t["selection"]["selected_violating_seats"] for t in targets) == gates["require_fixed_envelope_cap_compliance"],
        "certificate": all(t["certificate"]["selected_candidate_becomes_anchor"] is False and t["certificate"]["cumulative_episode_safety_claim"] is False for t in targets) == gates["require_certificate_scope"],
        "finite": all(q["finite"] for q in qualities) and all(c["finite"] for c in candidates) == gates["require_finite"],
        "zero_sum": all(q["zero_sum_residual"] <= gates["maximum_zero_sum_residual"] for q in qualities),
        "vector_sum": all(q["quality_vector_sum_error"] <= gates["maximum_quality_vector_sum_error"] for q in qualities),
        "interpolation": all(r["maximum_normalization_error"] <= gates["maximum_interpolation_normalization_error"] for t in targets for r in t["interpolation"]),
        "target_compile": all(t["target_workspace_compile_ms"] <= gates["maximum_target_compile_ms"] for t in targets),
        "cache_compile": all(t["cache_compile_ms"] <= gates["maximum_cache_compile_ms"] for t in targets),
        "step_time": all(s["wall_ms"] <= gates["maximum_training_step_ms"] for s in steps),
        "quality_time": all(q["wall_ms"] <= gates["maximum_quality_ms"] for q in qualities),
        "gpu_pool": all(s["maximum_gpu_pool_bytes"] <= gates["maximum_gpu_pool_bytes"] for s in steps) and all(q["maximum_gpu_pool_bytes"] <= gates["maximum_gpu_pool_bytes"] for q in qualities),
        "zero_sized_trees": True == gates["require_zero_sized_trees"], "action_width_claim_null": True == gates["require_action_width_claim_null"],
        "wall_time": (time.perf_counter() - started) <= gates["maximum_total_audit_seconds"],
    }
    total = time.perf_counter() - started; passed = all(gate_results.values())
    result = {"schema_version": 1, "status": "frozen_h32_fresh_panel_target_transfer_executed", "config": config,
              "config_sha256": _sha256(config_path), "implementation_sha256": _sha256(_IMPLEMENTATION),
              "environment": {**environment_metadata(), **runtime, "git": git}, "targets": targets, "gate_results": gate_results,
              "passed": passed, "decision": "accept_fresh_panel_two_step_transfer_measurement" if passed else "reject_target_transfer_mechanism",
              "strategy_transfer": {"non_blueprint_selections": sum(not t["strategy_outcome"]["blueprint_abstention"] for t in targets),
                                    "local_non_blueprint_selections": sum(t["target_shift"] == "local_blocker_seat3_x2" and not t["strategy_outcome"]["blueprint_abstention"] for t in targets)},
              "counts": {"target_search_steps": len(steps), "candidate_profiles": len(candidates), "blueprint_profiles": len(targets), "sized_trees_constructed": 0},
              "action_width_quality_claim": None, "timing": {"total_seconds": total},
              "limitations": ["Each certificate is one-shot and never reanchors.", "No two-size tree or action-width policy was constructed.", "Three deterministic boards are not a board-population estimate."]}
    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"); cp.get_default_memory_pool().free_all_blocks(); return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=_CONFIG); parser.add_argument("--output", type=Path, default=_OUTPUT); args = parser.parse_args()
    result = run_h32_fresh_panel_target_transfer_audit(args.config, args.output); print(f"fresh-panel target transfer: passed={result['passed']}, selections={result['strategy_transfer']['non_blueprint_selections']}, wall={result['timing']['total_seconds']:.3f}s")


if __name__ == "__main__": main()
