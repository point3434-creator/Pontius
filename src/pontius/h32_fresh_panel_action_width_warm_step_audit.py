"""Frozen one-step common-game action-width audit on the fresh h32 panel."""

from __future__ import annotations

import argparse
import gc
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from . import h32_action_width_quality_audit as action_width
from . import h32_fresh_panel_target_transfer_audit as transfer
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .fresh_h32_strategy_transfer_audit import _belief_digest, _finite_policy
from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .h32_affine_resident_cache_preflight import (
    _representative_sized_tree,
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_fresh_board_panel_cache_preflight import (
    parse_h32_fresh_board_panel_cache_config,
)
from .h32_fresh_panel_source_blueprint_audit import (
    parse_h32_fresh_panel_source_blueprint_config,
)
from .h32_fresh_panel_target_transfer_audit_v2 import (
    parse_h32_fresh_panel_target_transfer_v2_config,
)
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    build_target_belief,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from .multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from .multi_size_leaf_adjoint import build_multi_size_leaf_adjoint_terminal_automata
from .multi_size_policy_bridge import (
    deserialize_compact_sized_policy,
    embed_one_size_policy,
    serialize_compact_sized_policy,
    sized_policy_digest,
)
from .real_policy import mean_policy_total_variation, policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-action-width-warm-step-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-panel-action-width-warm-step-v1.json"
_CACHE = _ROOT / "experiments/results/h32-fresh-board-panel-cache-v1.json"
_CACHE_CONFIG = _ROOT / "experiments/configs/h32-fresh-board-panel-cache-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-source-blueprints-v1.json"
_TRANSFER = _ROOT / "experiments/results/h32-fresh-panel-target-transfer-v2.json"
_TRANSFER_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v2.json"
_TARGET_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v1.json"
_ACTION_WIDTH = _ROOT / "src/pontius/h32_action_width_quality_audit.py"
_POLICY_BRIDGE = _ROOT / "src/pontius/multi_size_policy_bridge.py"
_SIZED_CFR = _ROOT / "src/pontius/multi_size_affine_resident_leaf_adjoint_cfr.py"
_SIZED_EVALUATION = _ROOT / "src/pontius/multi_size_affine_resident_leaf_adjoint_evaluation.py"
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests/test_h32_fresh_panel_action_width_warm_step_audit.py"

_SOURCE_PATHS = {
    "expected_cache_result_sha256": _CACHE,
    "expected_cache_config_sha256": _CACHE_CONFIG,
    "expected_source_result_sha256": _SOURCE,
    "expected_source_config_sha256": _SOURCE_CONFIG,
    "expected_disclosed_transfer_result_sha256": _TRANSFER,
    "expected_disclosed_transfer_config_sha256": _TRANSFER_CONFIG,
    "expected_target_config_sha256": _TARGET_CONFIG,
    "expected_action_width_implementation_sha256": _ACTION_WIDTH,
    "expected_policy_bridge_sha256": _POLICY_BRIDGE,
    "expected_sized_cfr_sha256": _SIZED_CFR,
    "expected_sized_evaluation_sha256": _SIZED_EVALUATION,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _CONTROL_TEST,
}

_FIELDS = {
    "evidence_stage", *tuple(_SOURCE_PATHS), "disclosed_prior_outcome",
    "scheduling_independence_rule", "one_size_bet", "two_size_bets",
    "expected_one_size_payoff_span", "expected_two_size_payoff_span",
    "target_order", "arm_order_by_target", "solver_variant",
    "warm_regret_mass_payoff_fraction", "complete_steps_per_arm",
    "candidate_rule", "quality_rule", "fixed_seat_order",
    "acceptance_guard_normalized", "query_chunk_records",
    "maximum_feature_width_per_batch", "required_numpy_version",
    "required_scipy_version", "required_cupy_version",
    "required_cuda_runtime_version", "minimum_cuda_driver_version",
    "required_compute_capability", "cuda_dll_environment_variable", "gates",
}


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_fresh_panel_action_width_warm_step_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the complete ADR-0150 outcome-neutral contract."""
    if set(config) != _FIELDS:
        raise ValueError("fresh-panel action-width fields differ from ADR-0150")
    target_raw = json.loads(_TARGET_CONFIG.read_text(encoding="utf-8"))
    target = transfer.parse_h32_fresh_panel_target_transfer_config(target_raw)
    cache_raw = json.loads(_CACHE_CONFIG.read_text(encoding="utf-8"))
    parse_h32_fresh_board_panel_cache_config(cache_raw)
    source_raw = json.loads(_SOURCE_CONFIG.read_text(encoding="utf-8"))
    parse_h32_fresh_panel_source_blueprint_config(source_raw)
    transfer_v2_raw = json.loads(_TRANSFER_CONFIG.read_text(encoding="utf-8"))
    parse_h32_fresh_panel_target_transfer_v2_config(transfer_v2_raw)

    expected_order = list(target["target_order"])
    expected = {
        "evidence_stage": "preregistered_after_adr0149_before_any_fresh_panel_h32_two_size_policy_step_or_quality_measurement",
        "disclosed_prior_outcome": "adr0149_one_size_transfer_selected_one_non_blueprint_candidate_but_is_not_a_gate_filter_or_width_label",
        "scheduling_independence_rule": "all_twelve_targets_and_both_arms_are_scheduled_before_any_new_quality_label_and_adr0149_outcomes_cannot_change_order_gates_or_execution",
        "one_size_bet": 3.0,
        "two_size_bets": [3.0, 6.0],
        "expected_one_size_payoff_span": 30.0,
        "expected_two_size_payoff_span": 48.0,
        "target_order": expected_order,
        "arm_order_by_target": [
            "one_then_two" if index % 2 == 0 else "two_then_one"
            for index in range(len(expected_order))
        ],
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "complete_steps_per_arm": 1,
        "candidate_rule": "current_policy_after_exactly_one_complete_resident_warm_step_only",
        "quality_rule": "finish_both_arm_steps_then_fully_evaluate_incumbent_and_both_candidates_in_the_same_two_size_game_against_separate_immutable_blueprint_caps",
        "fixed_seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    for key, value in expected.items():
        if config[key] != value:
            raise ValueError(f"fresh-panel action-width workload differs: {key}")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh-panel action-width source mismatch: {field}")
    gates = {
        "expected_targets": 12,
        "expected_arms": 24,
        "expected_steps": 24,
        "expected_complete_quality_profiles": 36,
        "maximum_warm_start_mean_tv": 1e-12,
        "maximum_complete_step_ms": 60000.0,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_quality_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_quality_vector_sum_error": 1e-10,
        "maximum_zero_sum_residual": 1e-9,
        "maximum_total_seconds": 5400.0,
        "require_clean_git_state": True,
        "require_parent_identity": True,
        "require_cache_headroom_safe": True,
        "require_target_identity": True,
        "require_compact_round_trip": True,
        "require_planning_before_quality": True,
        "require_fixed_envelope_cap_compliance": True,
        "require_finite": True,
        "require_strategy_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh-panel action-width gates differ from ADR-0150")
    return {**target, **expected, "gates": gates}


def _warm_distance(
    left: Mapping[str, Mapping[Any, float]],
    right: Mapping[str, Mapping[Any, float]],
) -> dict[str, float]:
    maximum = 0.0
    for key in left:
        for action in left[key]:
            maximum = max(maximum, abs(float(left[key][action]) - float(right[key][action])))
    return {
        "mean_total_variation": mean_policy_total_variation(left, right),
        "maximum_absolute_probability_error": maximum,
    }


def _step_row(work: Any, wall_ms: float) -> dict[str, Any]:
    return {
        "iteration": 1,
        "wall_ms": wall_ms,
        "reported_wall_ms": work.wall_ms,
        "terminal_contraction_ms": work.terminal_contraction_ms,
        "terminal_sparse_batches": sum(row.terminal_sparse_batches for row in work.traversers),
        "maximum_gpu_pool_bytes": max(row.maximum_gpu_pool_total_bytes for row in work.traversers),
        "maximum_middle_rank": max(row.maximum_terminal_middle_rank for row in work.traversers),
    }


def _one_step_plan(
    *, parsed: dict[str, Any], cp: Any, arm: str, source_workspace: Any,
    target_belief: Any, sparse: Any, gpu: Any, one_layout: Any,
    one_libraries: Any, sized_layout: Any, sized_libraries: Any,
    one_blueprint: dict[str, Any], sized_blueprint: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    gc.collect()
    release_cupy_memory_pool()
    started = time.perf_counter()
    workspace, workspace_ms = action_width._target_workspace(
        source_workspace, target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    if arm == "one_size":
        layout, libraries, blueprint = one_layout, one_libraries, one_blueprint
    elif arm == "two_size":
        layout, libraries, blueprint = sized_layout, sized_libraries, sized_blueprint
    else:
        raise ValueError("unknown fresh-panel action-width arm")
    cache, belief_cache, automaton_caches = action_width._compile_cache(
        cp, workspace, libraries, arm=arm,
    )
    if arm == "one_size":
        solver: Any = ResidentLeafAdjointPublicTreeCFR(
            layout, workspace, sparse, libraries, parsed["solver_variant"],
            belief_cache=belief_cache, automaton_caches=automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
            hands_by_player=target_belief.hands_by_player,
        )
    else:
        solver = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
            layout, workspace, sparse, libraries, parsed["solver_variant"],
            belief_cache=belief_cache, automaton_caches=automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
            hands_by_player=target_belief.hands_by_player,
        )
    warm_mass = parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    solver.warm_start(blueprint, warm_mass)
    warm_policy = solver.current_strategy()
    warm_distance = _warm_distance(blueprint, warm_policy)
    tick = time.perf_counter()
    solver.step()
    step_ms = (time.perf_counter() - tick) * 1000.0
    if solver.iteration != 1 or solver.last_step_work is None:
        raise AssertionError("fresh-panel action-width arm did not complete exactly one step")
    policy = solver.current_strategy()
    sized_policy = (
        embed_one_size_policy(
            one_layout, sized_layout, target_belief.hands_by_player, policy,
            retained_bet_size=parsed["one_size_bet"],
        )
        if arm == "one_size" else policy
    )
    compact = serialize_compact_sized_policy(
        sized_policy, sized_layout, target_belief.hands_by_player,
    )
    restored = deserialize_compact_sized_policy(
        compact, sized_layout, target_belief.hands_by_player,
    )
    row = {
        "arm": arm,
        "solver_payoff_span": float(layout.game.payoff_span),
        "warm_regret_mass": warm_mass,
        "warm_start_distance": warm_distance,
        "target_workspace_compile_ms": workspace_ms,
        "cache": cache,
        "complete_steps": 1,
        "step": _step_row(solver.last_step_work, step_ms),
        "candidate_id": "warm_current1",
        "candidate_rule": parsed["candidate_rule"],
        "policy_sha256": sized_policy_digest(sized_policy),
        "native_policy_sha256": policy_digest(policy) if arm == "one_size" else None,
        "compact_policy_artifact": compact,
        "compact_round_trip": restored == sized_policy,
        "finite": _finite_policy(sized_policy),
        "mean_tv_from_embedded_incumbent": mean_policy_total_variation(
            sized_blueprint, sized_policy,
        ),
        "added_bet": action_width._added_bet_diagnostics(
            sized_layout, target_belief.hands_by_player, sized_policy,
            added_amount=parsed["two_size_bets"][-1],
        ),
        "construction_and_step_ms": (time.perf_counter() - started) * 1000.0,
        "accumulator_numeric_bytes": solver.accumulator_numeric_bytes(),
    }
    del solver, automaton_caches, belief_cache, workspace
    gc.collect()
    release_cupy_memory_pool()
    return row, sized_policy


def _profile(
    *, label: str, policy: dict[str, Any], layout: Any, workspace: Any,
    sparse: Any, libraries: Any, belief_cache: Any, automaton_caches: Any,
    gpu: Any, hands: Any, width: int,
) -> dict[str, Any]:
    evaluated = evaluate_multi_size_affine_resident_profile(
        layout, workspace, sparse, policy, libraries,
        belief_cache=belief_cache, automaton_caches=automaton_caches,
        cupy_sparse=gpu, hands_by_player=hands,
        maximum_feature_width_per_batch=width,
    )
    return action_width._profile_row(
        label, evaluated, payoff_span=float(layout.game.payoff_span),
    )


def _selection(incumbent: dict[str, Any], candidate: dict[str, Any], raw_guard: float) -> dict[str, Any]:
    candidate_row = {
        "candidate_id": candidate["candidate_id"],
        "policy_sha256": candidate["quality"]["policy_sha256"],
        "quality": candidate["quality"],
    }
    selected = select_fixed_blueprint_envelope(
        {"candidate_id": incumbent["candidate_id"], "quality": incumbent["quality"]},
        [candidate_row], raw_guard=raw_guard,
    )
    chosen = incumbent["quality"] if selected["blueprint_abstention"] else candidate["quality"]
    return {
        **selected,
        "candidate_cap_diagnostics": transfer._cap(
            incumbent["quality"], candidate["quality"], raw_guard,
        ),
        "selected_normalized_nash_conv_reduction": (
            float(incumbent["quality"]["normalized_nash_conv"])
            - float(chosen["normalized_nash_conv"])
        ),
    }


def run_h32_fresh_panel_action_width_warm_step_audit(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen all-target, one-step-per-arm comparison once."""
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_panel_action_width_warm_step_config(config)
    cache_parent = json.loads(_CACHE.read_text(encoding="utf-8"))
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    transfer_parent = json.loads(_TRANSFER.read_text(encoding="utf-8"))
    parent_identity = (
        all(config[field] == _sha256(path) for field, path in _SOURCE_PATHS.items())
        and cache_parent["passed"]
        and cache_parent["headroom"]["all_twenty_four_caches_safe"]
        and cache_parent["h32_steps_executed"] == 0
        and cache_parent["h32_policies_constructed"] == 0
        and cache_parent["h32_strategy_quality_evaluations"] == 0
        and cache_parent["strategy_quality_claim"] is None
        and source_parent["passed"]
        and transfer_parent["passed"]
        and transfer_parent["action_width_quality_claim"] is None
    )
    if not parent_identity:
        raise RuntimeError("fresh-panel action-width parent identity rejected")
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("fresh-panel action-width execution requires a clean Git state")
    cp, runtime = _validate_runtime(parsed)
    small = action_width._small_control(parsed)
    if not (
        small["profile_utility_error"] <= 2e-13
        and small["quality_error"] <= 2e-11
        and small["zero_sum_residual"] <= 2e-11
        and small["compact_round_trip"]
        and small["shared_affine_bases"] == 378
        and small["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"]
    ):
        raise RuntimeError("fresh-panel action-width h2 control rejected")

    targets = []
    for target_index, target_key in enumerate(parsed["target_order"]):
        print(f"fresh action-width {target_key}", flush=True)
        board_id, family, shift = target_key.split("/", 2)
        panel = next(row for row in parsed["panels"] if row["board_id"] == board_id)
        board = parse_cards(*panel["cards"])
        source_belief, one_layout, sparse, retained = _build_case(
            parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family,
        )
        source_workspace, _, one_libraries = retained
        source_key = f"{board_id}/{family}"
        source_row = next(row for row in source_parent["source_rows"] if row["source"] == source_key)
        one_blueprint = _average_policy_from_state(source_row["final_checkpoint"])
        source_identity = (
            _belief_digest(source_belief) == parsed["source_belief_sha256_by_source"][source_key]
            and policy_digest(one_blueprint) == source_row["final_checkpoint"]["average_policy_sha256"]
        )
        target_belief, descriptor = build_target_belief(
            source_belief, board=board, shift=shift,
            local_blocker_target_seat=parsed["local_blocker_target_seat"],
        )
        target_identity = (
            _belief_digest(target_belief) == parsed["target_belief_sha256_by_target"][target_key]
            and transfer._json_digest(descriptor) == parsed["target_descriptor_sha256_by_target"][target_key]
            and target_belief.hands_by_player == source_belief.hands_by_player
        )
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(board, source_belief.hands_by_player)
        )
        sized_layout = _representative_sized_tree(
            source_belief, pot=parsed["pot"], stack=parsed["stack"],
            bet_sizes=parsed["two_size_bets"],
        )
        sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
            sized_layout, codes, pot=parsed["pot"],
        )
        sized_blueprint = embed_one_size_policy(
            one_layout, sized_layout, source_belief.hands_by_player, one_blueprint,
            retained_bet_size=parsed["one_size_bet"],
        )
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        order_name = parsed["arm_order_by_target"][target_index]
        arm_order = ("one_size", "two_size") if order_name == "one_then_two" else ("two_size", "one_size")
        plans, live = {}, {}
        for arm in arm_order:
            plans[arm], live[arm] = _one_step_plan(
                parsed=parsed, cp=cp, arm=arm, source_workspace=source_workspace,
                target_belief=target_belief, sparse=sparse, gpu=gpu,
                one_layout=one_layout, one_libraries=one_libraries,
                sized_layout=sized_layout, sized_libraries=sized_libraries,
                one_blueprint=one_blueprint, sized_blueprint=sized_blueprint,
            )
        planning_finished = time.perf_counter()
        verifier_workspace, verifier_workspace_ms = action_width._target_workspace(
            source_workspace, target_belief,
            query_chunk_records=parsed["query_chunk_records"],
        )
        verifier_cache, verifier_belief, verifier_automata = action_width._compile_cache(
            cp, verifier_workspace, sized_libraries, arm="two_size",
        )
        quality_started = time.perf_counter()
        incumbent = _profile(
            label="immutable_embedded_source_average64", policy=sized_blueprint,
            layout=sized_layout, workspace=verifier_workspace, sparse=sparse,
            libraries=sized_libraries, belief_cache=verifier_belief,
            automaton_caches=verifier_automata, gpu=gpu,
            hands=target_belief.hands_by_player,
            width=parsed["maximum_feature_width_per_batch"],
        )
        candidates, selections = {}, {}
        raw_guard = parsed["acceptance_guard_normalized"] * float(sized_layout.game.payoff_span)
        for arm in arm_order:
            candidate = _profile(
                label=f"{arm}_warm_current1", policy=live[arm],
                layout=sized_layout, workspace=verifier_workspace, sparse=sparse,
                libraries=sized_libraries, belief_cache=verifier_belief,
                automaton_caches=verifier_automata, gpu=gpu,
                hands=target_belief.hands_by_player,
                width=parsed["maximum_feature_width_per_batch"],
            )
            candidates[arm] = candidate
            selections[arm] = _selection(incumbent, candidate, raw_guard)
        targets.append({
            "target": target_key, "board_id": board_id, "range_family": family,
            "target_shift": shift, "arm_order": order_name,
            "source_identity": source_identity, "target_identity": target_identity,
            "target_belief_sha256": _belief_digest(target_belief),
            "target_descriptor": descriptor,
            "one_size_payoff_span": float(one_layout.game.payoff_span),
            "two_size_payoff_span": float(sized_layout.game.payoff_span),
            "one_size_public_nodes": one_layout.public_node_count,
            "two_size_public_nodes": sized_layout.public_node_count,
            "arm_planning": plans,
            "planning_finished_before_quality": planning_finished <= quality_started,
            "verifier_workspace_compile_ms": verifier_workspace_ms,
            "verifier_cache": verifier_cache,
            "incumbent": incumbent,
            "candidates": candidates,
            "selections": selections,
            "two_minus_one_candidate_normalized_reduction": (
                float(incumbent["quality"]["normalized_nash_conv"])
                - float(candidates["two_size"]["quality"]["normalized_nash_conv"])
            ) - (
                float(incumbent["quality"]["normalized_nash_conv"])
                - float(candidates["one_size"]["quality"]["normalized_nash_conv"])
            ),
        })
        del verifier_automata, verifier_belief, verifier_workspace, live, gpu
        gc.collect()
        release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    arm_rows = [target["arm_planning"][arm] for target in targets for arm in ("one_size", "two_size")]
    quality_rows = [target["incumbent"]["quality"] for target in targets]
    quality_rows += [target["candidates"][arm]["quality"] for target in targets for arm in ("one_size", "two_size")]
    gates = parsed["gates"]
    gate_results = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "cache_headroom_safe": cache_parent["headroom"]["all_twenty_four_caches_safe"] == gates["require_cache_headroom_safe"],
        "target_count": len(targets) == gates["expected_targets"],
        "arm_count": len(arm_rows) == gates["expected_arms"],
        "step_count": sum(row["complete_steps"] for row in arm_rows) == gates["expected_steps"],
        "quality_count": len(quality_rows) == gates["expected_complete_quality_profiles"],
        "source_target_identity": all(row["source_identity"] and row["target_identity"] for row in targets) == gates["require_target_identity"],
        "payoff_spans": all(row["one_size_payoff_span"] == parsed["expected_one_size_payoff_span"] and row["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"] for row in targets),
        "warm_start_distance": all(row["warm_start_distance"]["mean_total_variation"] <= gates["maximum_warm_start_mean_tv"] for row in arm_rows),
        "step_ceiling": all(row["step"]["wall_ms"] <= gates["maximum_complete_step_ms"] for row in arm_rows),
        "cache_ceiling": all(row["cache"]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"] for row in arm_rows) and all(row["verifier_cache"]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"] for row in targets),
        "quality_ceiling": all(row["wall_ms"] <= gates["maximum_quality_ms"] for row in quality_rows),
        "gpu_pool": max([row["cache"]["pool_total_bytes"] for row in arm_rows] + [row["step"]["maximum_gpu_pool_bytes"] for row in arm_rows] + [row["verifier_cache"]["pool_total_bytes"] for row in targets]) <= gates["maximum_gpu_pool_bytes"],
        "compact_round_trip": all(row["compact_round_trip"] for row in arm_rows) == gates["require_compact_round_trip"],
        "planning_before_quality": all(row["planning_finished_before_quality"] for row in targets) == gates["require_planning_before_quality"],
        "quality_exactness": all(row["quality_vector_sum_error"] <= gates["maximum_quality_vector_sum_error"] and row["zero_sum_residual"] <= gates["maximum_zero_sum_residual"] for row in quality_rows),
        "fixed_envelope_cap_compliance": all((selection["selected_candidate_id"] == "immutable_embedded_source_average64") or selection["candidate_cap_diagnostics"]["feasible"] for target in targets for selection in target["selections"].values()) == gates["require_fixed_envelope_cap_compliance"],
        "finite": all(row["finite"] for row in arm_rows) and all(row["finite"] for row in quality_rows) == gates["require_finite"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
        "strategy_claim_null": (None is None) == gates["require_strategy_claim_null"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_panel_action_width_warm_step_executed",
        "experiment_type": "all_target_one_step_common_game_action_width_diagnostic",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), "git": git, "runtime": runtime},
        "parent_identity": parent_identity,
        "small_control": small,
        "targets": targets,
        "gate_results": gate_results,
        "passed": passed,
        "strategy_quality_claim": None,
        "decision": "record_claim_null_fresh_panel_action_width_diagnostic" if passed else "reject_fresh_panel_action_width_mechanism",
        "work_accounting": {
            "h32_one_size_steps": 12,
            "h32_two_size_steps": 12,
            "h32_widened_quality_profiles": len(quality_rows),
            "targets_filtered_by_prior_outcome": 0,
        },
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            "The audit reports paired one-step diagnostics and makes no strategy-quality or action-width ranking claim.",
            "Each arm is separately certified against the same immutable embedded source blueprint; no selected candidate becomes a future anchor.",
            "ADR-0149 is disclosed and pinned but cannot filter targets, alter order, or define a gate.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_panel_action_width_warm_step_audit(args.config, args.output)
    print(f"fresh-panel action-width warm step: passed={result['passed']}, wall={result['timing']['total_seconds']:.3f}s")


if __name__ == "__main__":
    main()
