"""Label-free wall ledger for the exact h32 post-action continuation root."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .continuation_public_tree_tensor import ContinuationPublicTreeTensorEvaluator
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import build_action_conditioned_posterior
from .h32_action_conditioned_widened_selector_trial import (
    build_all_changed_public_node_blocks,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_preflight import checks_then_bet_prefix
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    direction_has_convex_scope,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import information_schema_for_axes
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-continuation-root-ledger-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-continuation-root-ledger-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_PREFLIGHT = _ROOT / "experiments/results/h32-continuation-root-preflight-v1.json"
_PREFLIGHT_DECISION = _ROOT / "docs/decisions/ADR-0224-continuation-root-is-exact-and-removes-five-sixths-of-strategic-nodes.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_continuation_root_ledger.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_preflight_result_sha256": _PREFLIGHT,
    "expected_preflight_decision_sha256": _PREFLIGHT_DECISION,
    "expected_continuation_implementation_sha256": _ROOT / "src/pontius/continuation_public_tree_tensor.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_ledger_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required continuation ledger input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def derive_continuation_capacities(
    candidate_ms: Sequence[float],
    *,
    warm_step_ms: float,
    street_budget_ms: float,
    emission_reserve_ms: float,
    tier_c_reserve_ms: float,
) -> dict[str, Any]:
    """Return frozen worst-case K and profiled cumulative prefix capacity."""

    costs = tuple(float(value) for value in candidate_ms)
    if not costs or any(not math.isfinite(value) or value < 0.0 for value in costs):
        raise ValueError("continuation capacity requires finite candidate costs")
    ledger_inputs = (
        warm_step_ms,
        street_budget_ms,
        emission_reserve_ms,
        tier_c_reserve_ms,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in ledger_inputs):
        raise ValueError("continuation capacity requires finite nonnegative ledger inputs")
    if street_budget_ms == 0.0:
        raise ValueError("continuation capacity requires a positive street budget")
    available = (
        street_budget_ms
        - emission_reserve_ms
        - tier_c_reserve_ms
        - warm_step_ms
    )
    maximum = max(costs)
    worst_case_k = 0
    if available >= 0.0:
        worst_case_k = (
            len(costs)
            if maximum == 0.0
            else min(len(costs), math.floor(available / maximum))
        )
    cumulative = 0.0
    cumulative_k = 0
    prefix_rows = []
    for index, cost in enumerate(costs):
        next_total = cumulative + cost
        fits = next_total <= available
        prefix_rows.append(
            {
                "candidate_index": index,
                "candidate_ms": cost,
                "cumulative_candidate_ms": next_total,
                "complete_ledger_ms": (
                    warm_step_ms
                    + next_total
                    + tier_c_reserve_ms
                    + emission_reserve_ms
                ),
                "fits": fits,
            }
        )
        if not fits:
            break
        cumulative = next_total
        cumulative_k += 1
    return {
        "candidate_count": len(costs),
        "warm_step_ms": warm_step_ms,
        "street_budget_ms": street_budget_ms,
        "emission_reserve_ms": emission_reserve_ms,
        "tier_c_reserve_ms": tier_c_reserve_ms,
        "available_candidate_ms": available,
        "maximum_candidate_ms": maximum,
        "worst_case_safe_k": worst_case_k,
        "profiled_cumulative_k": cumulative_k,
        "worst_case_library_limited": worst_case_k == len(costs),
        "profiled_cumulative_library_limited": cumulative_k == len(costs),
        "profiled_cumulative_is_development_capacity_not_live_deadline_guarantee": True,
        "prefix_rows": prefix_rows,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"continuation ledger provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0224_before_any_continuation_warm_step_tier_b_measurement_or_strategy_label",
        "seed": 20260822,
        "scope": "all_twelve_exact_continuation_targets_one_device_fold_warm_step_and_all_thirty_one_tier_b_rows_label_free",
        "candidate_order": "continuation_public_tree_preorder_then_actor_then_full_public_history",
        "capacity_rule": "report_worst_case_safe_k_and_profiled_cumulative_prefix_k_from_measured_label_independent_costs",
        "promotion_rule": "authorize_fresh_continuation_strategy_preregistration_only_if_minimum_worst_case_k_at_least_six_and_minimum_profiled_cumulative_k_at_least_eight",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "tier_c_reserve_ms": 10.0,
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "search_steps_per_target": 1,
        "maximum_feature_width_per_batch": 384,
        "selector_margin_allowance": 2e-11,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "strategy_label_policy": "zero_quality_rows_zero_affine_feature_values_zero_certificates_zero_strategy_labels",
    }
    for field, value in exact.items():
        if config.get(field) != value:
            raise ValueError(f"continuation ledger field differs from ADR-0225: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("continuation ledger requires all twelve targets")
    gates = {
        "expected_targets": 12,
        "expected_warm_steps": 12,
        "expected_blocks_per_target": 31,
        "expected_information_sets_per_target": 992,
        "expected_own_rows": 372,
        "expected_opponent_rows": 1860,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_warm_step_ms": 60000.0,
        "maximum_candidate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_complete_block_partition": True,
        "require_convex_scope": True,
        "require_five_opponent_calls": True,
        "require_zero_own_contractions": True,
        "require_capacity_before_labels": True,
        "require_blueprint_emission": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config.get("gates") != gates:
        raise ValueError("continuation ledger gates differ from ADR-0225")
    return {**config, "targets": tuple(dict(row) for row in config["targets"]), "gates": gates}


def _setup(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    board = parse_cards(*spec["board"])
    source, full, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=str(spec["range_family"]),
    )
    source_workspace, _, _ = retained
    source_row = next(
        row for row in source_parent["source_rows"] if row["source"] == spec["source"]
    )
    state = source_row["final_checkpoint"]
    full_blueprint = _average_policy_from_state(state)
    belief, _ = build_action_conditioned_posterior(
        source,
        full_blueprint,
        bettor=int(spec["observed_bettor"]),
    )
    layout = ContinuationPublicTreeTensorEvaluator(
        full.game,
        public_prefix=checks_then_bet_prefix(int(spec["observed_bettor"])),
    )
    schema = information_schema_for_axes(layout, belief.hands_by_player)
    blueprint = {key: dict(full_blueprint[key]) for key in schema}
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        layout,
        codes,
        pot=float(parsed["pot"]),
        bet_size=float(parsed["bet_size"]),
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=int(parsed["query_chunk_records"]),
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        source_policy=blueprint,
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    return {
        "board": board,
        "source": source,
        "full": full,
        "layout": layout,
        "sparse": sparse,
        "source_workspace": source_workspace,
        "state": state,
        "full_blueprint": full_blueprint,
        "blueprint": blueprint,
        "belief": belief,
        "automata": automata,
        "base": base,
        "workspace": workspace,
        "gpu": gpu,
        "shared": shared,
        "context": context,
    }


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    objects = _setup(parsed, source_parent, spec)
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout,
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
        record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("continuation warm step emitted no work ledger")
    warm_works = [row.resident_work for row in solver.last_step_work.traversers]
    warm_work = {
        "wall_ms": warm_step_ms,
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(warm_works),
    }
    candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    blocks = build_all_changed_public_node_blocks(blueprint, candidate)
    node_order = {
        (node.player, "root" if not node.history else "/".join(f"p{seat}:{action}" for seat, action in node.history)): index
        for index, node in enumerate(layout.nodes)
        if node.player >= 0
    }
    blocks = tuple(
        sorted(
            blocks,
            key=lambda row: (
                node_order[(int(row["acting_seat"]), str(row["public_history"]))],
                int(row["acting_seat"]),
                str(row["public_history"]),
            ),
        )
    )
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain)
        for cache in context.response_caches
    )
    rows = []
    maximum_intercept_error = 0.0
    for index, block in enumerate(blocks):
        cp.cuda.runtime.deviceSynchronize()
        candidate_started = time.perf_counter()
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        convex = direction_has_convex_scope(block)
        probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        construction_ms = (time.perf_counter() - candidate_started) * 1000.0
        own = evaluate_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[seat],
            probabilities,
            acting_player=seat,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[seat],
            cupy_sparse=gpu,
        )
        opponent_rows = []
        works = []
        for target_player in range(6):
            if target_player == seat:
                continue
            measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                context.response_caches[target_player],
                probabilities,
                acting_player=seat,
                selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
                record_to_hand_backend="gpu_cupy",
            )
            opponent_rows.append(measured.semantic)
            if measured.work is not None:
                works.append(measured.work)
        cp.cuda.runtime.deviceSynchronize()
        complete_ms = (time.perf_counter() - candidate_started) * 1000.0
        affine_rows = [own, *opponent_rows]
        maximum_intercept_error = max(
            maximum_intercept_error,
            max(
                abs(float(row.deviation_gain_intercept) - source_gains[row.target_player])
                for row in affine_rows
            ),
        )
        rows.append(
            {
                "candidate_index": index,
                "acting_seat": seat,
                "public_history": block["public_history"],
                "information_set_count": block["information_set_count"],
                "changed_entry_count": block["changed_entry_count"],
                "convex_scope": convex,
                "endpoint_policy_sha256": policy_digest(endpoint),
                "own_affected_terminal_contractions": own.affected_terminal_contractions,
                "opponent_calls": len(opponent_rows),
                "opponent_affected_terminal_contractions": sum(
                    row.affected_terminal_contractions for row in opponent_rows
                ),
                "opponent_full_terminal_contractions": sum(
                    row.full_terminal_contractions for row in opponent_rows
                ),
                "maximum_terminal_middle_rank": max(
                    (row.maximum_terminal_middle_rank for row in opponent_rows),
                    default=0,
                ),
                "timing": {
                    "endpoint_construction_ms": construction_ms,
                    "own_zero_contraction_ms": own.wall_ms,
                    "opponent_wall_ms": math.fsum(row.wall_ms for row in opponent_rows),
                    "complete_tier_b_candidate_ms": complete_ms,
                },
                "device_work": _work_ledger(works),
            }
        )
        memory_rows.append(_memory_snapshot(cp))
    capacities = derive_continuation_capacities(
        [row["timing"]["complete_tier_b_candidate_ms"] for row in rows],
        warm_step_ms=warm_step_ms,
        street_budget_ms=float(parsed["street_budget_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
        tier_c_reserve_ms=float(parsed["tier_c_reserve_ms"]),
    )
    result = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "observed_bettor": spec["observed_bettor"],
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(objects["state"])
        == objects["state"]["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"],
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"])
        == objects["state"]["average_policy_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "warm_start_distance": warm_distance,
        "warm_step": warm_work,
        "changed_information_set_count": sum(
            row["information_set_count"] for row in rows
        ),
        "candidate_rows": rows,
        "maximum_affine_intercept_error": maximum_intercept_error,
        "capacity_before_labels": capacities,
        "memory_rows": memory_rows,
        "emitted_policy_sha256": policy_digest(blueprint),
        "strategy_labels_generated": 0,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_continuation_root_ledger(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    preflight = json.loads(_PREFLIGHT.read_text(encoding="utf-8"))
    target_rows = [
        _run_target(parsed, source_parent, spec, cp) for spec in parsed["targets"]
    ]
    all_rows = [row for target in target_rows for row in target["candidate_rows"]]
    total_seconds = time.perf_counter() - started
    minimum_free = min(
        memory["gpu_free_bytes"]
        for target in target_rows
        for memory in target["memory_rows"]
    )
    maximum_pool = max(
        memory["gpu_pool_total_bytes"]
        for target in target_rows
        for memory in target["memory_rows"]
    )
    gate = parsed["gates"]
    gates = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": bool(manifest["passed"] and preflight["passed"])
        == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "warm_step_count": len(target_rows) == gate["expected_warm_steps"],
        "block_counts": all(
            len(target["candidate_rows"]) == gate["expected_blocks_per_target"]
            and target["changed_information_set_count"]
            == gate["expected_information_sets_per_target"]
            for target in target_rows
        ),
        "own_row_count": len(all_rows) == gate["expected_own_rows"],
        "opponent_row_count": sum(row["opponent_calls"] for row in all_rows)
        == gate["expected_opponent_rows"],
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in target_rows
        )
        == gate["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in target_rows)
        == gate["require_target_identity"],
        "blueprint_identity": all(
            target["blueprint_identity"] for target in target_rows
        )
        == gate["require_blueprint_identity"],
        "warm_start_identity": max(
            target["warm_start_distance"]["maximum_probability_error"]
            for target in target_rows
        )
        <= gate["maximum_warm_start_probability_error"]
        and max(
            target["warm_start_distance"]["mean_total_variation"]
            for target in target_rows
        )
        <= gate["maximum_warm_start_mean_total_variation"],
        "complete_block_partition": all(
            target["changed_information_set_count"]
            == sum(row["information_set_count"] for row in target["candidate_rows"])
            for target in target_rows
        )
        == gate["require_complete_block_partition"],
        "convex_scope": all(row["convex_scope"] for row in all_rows)
        == gate["require_convex_scope"],
        "five_opponent_calls": all(row["opponent_calls"] == 5 for row in all_rows)
        == gate["require_five_opponent_calls"],
        "zero_own_contractions": all(
            row["own_affected_terminal_contractions"] == 0 for row in all_rows
        )
        == gate["require_zero_own_contractions"],
        "affine_intercepts": max(
            target["maximum_affine_intercept_error"] for target in target_rows
        )
        <= gate["maximum_affine_intercept_error"],
        "warm_step_time": max(
            target["warm_step"]["wall_ms"] for target in target_rows
        )
        <= gate["maximum_warm_step_ms"],
        "candidate_time": max(
            row["timing"]["complete_tier_b_candidate_ms"] for row in all_rows
        )
        <= gate["maximum_candidate_ms"],
        "capacity_before_labels": all(
            target["strategy_labels_generated"] == 0
            and target["capacity_before_labels"]["candidate_count"] == 31
            for target in target_rows
        )
        == gate["require_capacity_before_labels"],
        "gpu_pool": maximum_pool <= gate["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": all(
            target["emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
            for target in target_rows
        )
        == gate["require_blueprint_emission"],
        "new_strategy_labels_zero": (
            sum(target["strategy_labels_generated"] for target in target_rows)
            == 0
        )
        == gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gates["passed"] = all(gates.values())
    minimum_worst = min(
        target["capacity_before_labels"]["worst_case_safe_k"]
        for target in target_rows
    )
    minimum_cumulative = min(
        target["capacity_before_labels"]["profiled_cumulative_k"]
        for target in target_rows
    )
    promotion = minimum_worst >= 6 and minimum_cumulative >= 8
    result = {
        "schema_version": 1,
        "status": "h32_continuation_root_ledger_executed",
        "environment": {**environment_metadata(), "runtime": runtime, "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "device_fold_warm_steps": len(target_rows),
            "tier_b_candidate_rows": len(all_rows),
            "own_affine_rows": len(all_rows),
            "opponent_affine_rows": sum(row["opponent_calls"] for row in all_rows),
            "quality_rows_serialized": 0,
            "affine_feature_values_serialized": 0,
            "certificates": 0,
            "strategy_labels": 0,
        },
        "target_rows": target_rows,
        "aggregate": {
            "minimum_warm_step_ms": min(target["warm_step"]["wall_ms"] for target in target_rows),
            "median_warm_step_ms": float(np.median([target["warm_step"]["wall_ms"] for target in target_rows])),
            "maximum_warm_step_ms": max(target["warm_step"]["wall_ms"] for target in target_rows),
            "minimum_candidate_ms": min(row["timing"]["complete_tier_b_candidate_ms"] for row in all_rows),
            "median_candidate_ms": float(np.median([row["timing"]["complete_tier_b_candidate_ms"] for row in all_rows])),
            "maximum_candidate_ms": max(row["timing"]["complete_tier_b_candidate_ms"] for row in all_rows),
            "minimum_worst_case_safe_k": minimum_worst,
            "maximum_worst_case_safe_k": max(target["capacity_before_labels"]["worst_case_safe_k"] for target in target_rows),
            "minimum_profiled_cumulative_k": minimum_cumulative,
            "maximum_profiled_cumulative_k": max(target["capacity_before_labels"]["profiled_cumulative_k"] for target in target_rows),
            "maximum_affine_intercept_error": max(target["maximum_affine_intercept_error"] for target in target_rows),
            "minimum_gpu_free_bytes": minimum_free,
            "maximum_gpu_pool_total_bytes": maximum_pool,
            "promotion_threshold_met": promotion,
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "authorize_fresh_continuation_strategy_preregistration"
            if gates["passed"] and promotion
            else "hold_fresh_continuation_labels_and_reprice_scheduler"
            if gates["passed"]
            else "reject_continuation_root_ledger"
        ),
        "emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "Profiled cumulative K uses measured development costs and is not a live hard-deadline guarantee.",
            "No quality vector, affine opportunity feature value, certificate, or strategy label is serialized.",
            "This ledger makes no strategy-quality, selector-transfer, deployment, or population claim.",
        ],
    }
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
    result = run_h32_continuation_root_ledger(args.config, args.output)
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
