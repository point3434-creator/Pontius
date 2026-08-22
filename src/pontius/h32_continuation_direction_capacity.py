"""Label-free capacity screen for a second h32 continuation direction family."""

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
from .cupy_sparse_incidence import release_cupy_memory_pool
from .delta_certificate_contract import interpolate_policy_atoms
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup, derive_continuation_capacities
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    direction_has_convex_scope,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_heldout_continuation_depth_value_trial import _ordered_blocks
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_policy_tt import compile_policy_probability_tape
from .real_policy import policy_digest
from .runner_harness import (
    assemble_environment,
    artifact_passed,
    finalize_gates,
    load_artifact,
    serialize_result,
)
from .selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-continuation-direction-capacity-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-continuation-direction-capacity-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-heldout-continuation-posterior-manifest-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md"
_HELDOUT_CONFIG = _ROOT / "experiments/configs/h32-heldout-continuation-depth-value-v1.json"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_continuation_direction_capacity.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_heldout_config_sha256": _HELDOUT_CONFIG,
    "expected_setup_implementation_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required direction-capacity input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def build_soft_regret_bisector_candidate(
    blueprint: Mapping[str, Mapping[Any, float]],
    soft_candidate: Mapping[str, Mapping[Any, float]],
    regret_vertex: Mapping[str, Mapping[Any, float]],
    information_keys: Sequence[str],
) -> dict[str, dict[Any, float]]:
    """Return the fixed half-soft/half-regret ray on one atomic block."""

    keys = tuple(information_keys)
    soft_block = interpolate_policy_atoms(
        blueprint, soft_candidate, keys, scale=1.0
    )
    return interpolate_policy_atoms(soft_block, regret_vertex, keys, scale=0.5)


def direction_capacity_decision(
    *,
    baseline_candidate_ms: Sequence[float],
    bonus_candidate_ms: Sequence[float],
    warm_step_ms: float,
    street_budget_ms: float,
    emission_reserve_ms: float,
    certificate_reserve_ms: float,
    envelope_reserve_ms: float,
    distinct_bonus_rows: int,
) -> dict[str, Any]:
    """Price the baseline-first expanded library without consulting labels."""

    baseline = tuple(float(value) for value in baseline_candidate_ms)
    bonus = tuple(float(value) for value in bonus_candidate_ms)
    if len(baseline) != len(bonus) or not baseline:
        raise ValueError("direction capacity requires paired nonempty libraries")
    if distinct_bonus_rows not in range(len(bonus) + 1):
        raise ValueError("distinct bonus row count is invalid")
    common = {
        "warm_step_ms": warm_step_ms,
        "street_budget_ms": street_budget_ms,
        "emission_reserve_ms": emission_reserve_ms,
        "tier_c_reserve_ms": certificate_reserve_ms + envelope_reserve_ms,
    }
    baseline_capacity = derive_continuation_capacities(baseline, **common)
    expanded_capacity = derive_continuation_capacities((*baseline, *bonus), **common)
    expanded_count = len(baseline) + len(bonus)
    promote = (
        expanded_capacity["profiled_cumulative_k"] == expanded_count
        and distinct_bonus_rows == len(bonus)
    )
    return {
        "baseline_capacity": baseline_capacity,
        "expanded_capacity": expanded_capacity,
        "baseline_complete_ledger_ms": (
            warm_step_ms + math.fsum(baseline)
            + certificate_reserve_ms + envelope_reserve_ms + emission_reserve_ms
        ),
        "expanded_complete_ledger_ms": (
            warm_step_ms + math.fsum((*baseline, *bonus))
            + certificate_reserve_ms + envelope_reserve_ms + emission_reserve_ms
        ),
        "baseline_rows": len(baseline),
        "bonus_rows": len(bonus),
        "distinct_bonus_rows": distinct_bonus_rows,
        "complete_expanded_library_fits": (
            expanded_capacity["profiled_cumulative_k"] == expanded_count
        ),
        "promote_bisector_family": promote,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected_fields = {
        "evidence_stage", *_PATHS, "seed", "targets", "scope",
        "direction_families", "direction_rule", "candidate_order",
        "capacity_rule", "promotion_rule", "street_budget_ms",
        "emission_reserve_ms", "certificate_reserve_ms", "envelope_reserve_ms",
        "pot", "stack", "bet_size", "players", "hands_per_player",
        "axis_seed", "mixture_components", "split_index", "query_chunk_records",
        "solver_variant", "warm_regret_mass_payoff_fraction",
        "search_steps_per_target", "maximum_feature_width_per_batch",
        "selector_margin_allowance", "required_numpy_version",
        "required_scipy_version", "required_cupy_version",
        "required_cuda_runtime_version", "minimum_cuda_driver_version",
        "required_compute_capability", "cuda_dll_environment_variable",
        "strategy_label_policy", "gates",
    }
    if set(config) != expected_fields:
        raise ValueError("direction-capacity config fields differ from ADR-0236")
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"direction-capacity provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0235_before_any_bisector_affine_row_or_strategy_label",
        "seed": 20260822,
        "scope": "heldout_latin_c_d_targets_one_step_then_complete_regret_library_then_complete_soft_regret_bisector_library_label_free",
        "direction_families": ["regret_vertex", "soft_regret_bisector"],
        "direction_rule": "per_block_regret_vertex_then_fixed_equal_weight_bisector_of_block_soft_dcfr_and_regret_vertex_endpoints",
        "candidate_order": "all_thirty_one_regret_vertex_rows_in_continuation_preorder_then_all_thirty_one_bisector_rows_in_the_same_order",
        "capacity_rule": "one_warm_step_plus_measured_baseline_first_rows_plus_fixed_envelope_certificate_and_emission_reserves",
        "promotion_rule": "all_sixty_two_profiled_rows_fit_every_target_and_all_bonus_endpoints_are_distinct",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "certificate_reserve_ms": 1250.0,
        "envelope_reserve_ms": 10.0,
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
            raise ValueError(f"direction-capacity field differs from ADR-0236: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("direction-capacity screen requires all twelve targets")
    heldout_targets = json.loads(_HELDOUT_CONFIG.read_text(encoding="utf-8"))["targets"]
    if config["targets"] != heldout_targets:
        raise ValueError("direction-capacity targets differ from the sealed held-out panel")
    gates = {
        "expected_targets": 12,
        "expected_warm_steps": 12,
        "expected_blocks_per_target": 31,
        "expected_information_sets_per_target": 992,
        "expected_candidate_rows": 744,
        "expected_own_rows": 744,
        "expected_opponent_rows": 3720,
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
        "require_baseline_first_order": True,
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
        raise ValueError("direction-capacity gates differ from ADR-0236")
    return {**config, "targets": tuple(dict(row) for row in config["targets"]), "gates": gates}


def _price_candidate(
    *,
    parsed: Mapping[str, Any],
    objects: Mapping[str, Any],
    endpoint: Mapping[str, Mapping[Any, float]],
    block: Mapping[str, Any],
    family: str,
    schedule_index: int,
    cp: Any,
) -> tuple[dict[str, Any], float]:
    layout = objects["layout"]
    belief = objects["belief"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    seat = int(block["acting_seat"])
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    probabilities = compile_policy_probability_tape(layout, belief.hands_by_player, endpoint)
    own = evaluate_selector_stable_affine_leaf_adjoint_seat(
        context.response_caches[seat], probabilities, acting_player=seat,
        selector_margin_allowance=float(parsed["selector_margin_allowance"]),
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        belief_cache=context.belief_cache,
        automaton_cache=shared.automaton_caches[seat], cupy_sparse=gpu,
    )
    affine_rows = []
    for target_player in range(6):
        if target_player == seat:
            affine_rows.append(own)
            continue
        measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[target_player], probabilities,
            acting_player=seat,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[target_player],
            cupy_sparse=gpu, record_to_hand_backend="gpu_cupy",
        )
        affine_rows.append(measured.semantic)
    cp.cuda.runtime.deviceSynchronize()
    complete_ms = (time.perf_counter() - started) * 1000.0
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain)
        for cache in context.response_caches
    )
    intercept_error = max(
        abs(float(row.deviation_gain_intercept) - source_gains[row.target_player])
        for row in affine_rows
    )
    row = {
        "candidate_index": schedule_index,
        "direction_family": family,
        "acting_seat": seat,
        "public_history": block["public_history"],
        "information_set_count": block["information_set_count"],
        "changed_entry_count": block["changed_entry_count"],
        "convex_scope": direction_has_convex_scope(block),
        "endpoint_policy_sha256": policy_digest(endpoint),
        "own_affected_terminal_contractions": own.affected_terminal_contractions,
        "opponent_calls": 5,
        "complete_tier_b_candidate_ms": complete_ms,
    }
    return row, intercept_error


def _run_target(
    parsed: Mapping[str, Any], source_parent: Mapping[str, Any],
    spec: Mapping[str, Any], cp: Any,
) -> dict[str, Any]:
    objects = _setup(parsed, source_parent, spec)
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout, objects["workspace"], objects["sparse"], objects["automata"],
        str(parsed["solver_variant"]), belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches, cupy_sparse=objects["gpu"],
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player, record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(layout.game.payoff_span)
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - started) * 1000.0
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint, solver.regret_table(), warm_regret_mass=warm_mass,
    )
    blocks = _ordered_blocks(layout, blueprint, soft_candidate)
    endpoint_rows = []
    for block in blocks:
        keys = tuple(block["information_keys"])
        vertex = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        bisector = build_soft_regret_bisector_candidate(
            blueprint, soft_candidate, vertex, keys
        )
        endpoint_rows.append((block, vertex, bisector))

    candidate_rows = []
    maximum_intercept_error = 0.0
    for family, endpoint_position in (("regret_vertex", 1), ("soft_regret_bisector", 2)):
        for block_index, endpoint_row in enumerate(endpoint_rows):
            block = endpoint_row[0]
            endpoint = endpoint_row[endpoint_position]
            row, error = _price_candidate(
                parsed=parsed, objects=objects, endpoint=endpoint, block=block,
                family=family, schedule_index=len(candidate_rows), cp=cp,
            )
            candidate_rows.append(row)
            maximum_intercept_error = max(maximum_intercept_error, error)
            memory_rows.append(_memory_snapshot(cp))

    baseline = candidate_rows[: len(blocks)]
    bonus = candidate_rows[len(blocks) :]
    distinct_bonus_rows = sum(
        bonus_row["endpoint_policy_sha256"] != baseline_row["endpoint_policy_sha256"]
        and bonus_row["endpoint_policy_sha256"] != policy_digest(blueprint)
        for baseline_row, bonus_row in zip(baseline, bonus, strict=True)
    )
    capacity = direction_capacity_decision(
        baseline_candidate_ms=[row["complete_tier_b_candidate_ms"] for row in baseline],
        bonus_candidate_ms=[row["complete_tier_b_candidate_ms"] for row in bonus],
        warm_step_ms=warm_step_ms,
        street_budget_ms=float(parsed["street_budget_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
        certificate_reserve_ms=float(parsed["certificate_reserve_ms"]),
        envelope_reserve_ms=float(parsed["envelope_reserve_ms"]),
        distinct_bonus_rows=distinct_bonus_rows,
    )
    result = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "round": spec["round"],
        "observed_bettor": spec["observed_bettor"],
        "source_checkpoint_identity": (
            axis_cfr_checkpoint_digest(objects["state"]) == objects["state"]["state_sha256"]
            and _belief_digest(objects["source"]) == spec["source_belief_sha256"]
        ),
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"]) == objects["state"]["average_policy_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "warm_start_distance": warm_distance,
        "warm_step_ms": warm_step_ms,
        "block_manifest_count": len(blocks),
        "changed_information_set_count": sum(row[0]["information_set_count"] for row in endpoint_rows),
        "candidate_rows": candidate_rows,
        "maximum_affine_intercept_error": maximum_intercept_error,
        "capacity_before_labels": capacity,
        "strategy_labels_generated": 0,
        "quality_rows_serialized": 0,
        "affine_feature_values_serialized": 0,
        "certificates_executed": 0,
        "emitted_policy_sha256": policy_digest(blueprint),
        "memory_rows": memory_rows,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_continuation_direction_capacity(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE, expected_sha256=parsed["expected_source_result_sha256"], require_passed=True
    ).payload
    manifest = load_artifact(
        _MANIFEST, expected_sha256=parsed["expected_manifest_result_sha256"], require_passed=True
    ).payload
    target_rows = [_run_target(parsed, source, spec, cp) for spec in parsed["targets"]]
    all_rows = [row for target in target_rows for row in target["candidate_rows"]]
    total_seconds = time.perf_counter() - started
    memory_rows = [row for target in target_rows for row in target["memory_rows"]]
    gate = parsed["gates"]
    baseline_first = all(
        [row["direction_family"] for row in target["candidate_rows"]]
        == ["regret_vertex"] * 31 + ["soft_regret_bisector"] * 31
        for target in target_rows
    )
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(parent) for parent in (source, manifest)) == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "warm_step_count": len(target_rows) == gate["expected_warm_steps"],
        "block_counts": all(target["block_manifest_count"] == gate["expected_blocks_per_target"] and target["changed_information_set_count"] == gate["expected_information_sets_per_target"] for target in target_rows),
        "candidate_count": len(all_rows) == gate["expected_candidate_rows"],
        "own_row_count": len(all_rows) == gate["expected_own_rows"],
        "opponent_row_count": sum(row["opponent_calls"] for row in all_rows) == gate["expected_opponent_rows"],
        "source_checkpoint_identity": all(target["source_checkpoint_identity"] for target in target_rows) == gate["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in target_rows) == gate["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in target_rows) == gate["require_blueprint_identity"],
        "warm_start_identity": max(target["warm_start_distance"]["maximum_probability_error"] for target in target_rows) <= gate["maximum_warm_start_probability_error"] and max(target["warm_start_distance"]["mean_total_variation"] for target in target_rows) <= gate["maximum_warm_start_mean_total_variation"],
        "complete_block_partition": all(target["changed_information_set_count"] == sum(row["information_set_count"] for row in target["candidate_rows"][:31]) for target in target_rows) == gate["require_complete_block_partition"],
        "baseline_first_order": baseline_first == gate["require_baseline_first_order"],
        "convex_scope": all(row["convex_scope"] for row in all_rows) == gate["require_convex_scope"],
        "five_opponent_calls": all(row["opponent_calls"] == 5 for row in all_rows) == gate["require_five_opponent_calls"],
        "zero_own_contractions": all(row["own_affected_terminal_contractions"] == 0 for row in all_rows) == gate["require_zero_own_contractions"],
        "affine_intercepts": max(target["maximum_affine_intercept_error"] for target in target_rows) <= gate["maximum_affine_intercept_error"],
        "warm_step_time": max(target["warm_step_ms"] for target in target_rows) <= gate["maximum_warm_step_ms"],
        "candidate_time": max(row["complete_tier_b_candidate_ms"] for row in all_rows) <= gate["maximum_candidate_ms"],
        "capacity_before_labels": all(target["strategy_labels_generated"] == 0 and target["capacity_before_labels"]["expanded_capacity"]["candidate_count"] == 62 for target in target_rows) == gate["require_capacity_before_labels"],
        "gpu_pool": max(row["gpu_pool_total_bytes"] for row in memory_rows) <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["gpu_free_bytes"] for row in memory_rows) >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": all(target["emitted_policy_sha256"] == target["restricted_blueprint_policy_sha256"] for target in target_rows) == gate["require_blueprint_emission"],
        "new_strategy_labels_zero": (
            sum(target["strategy_labels_generated"] for target in target_rows) == 0
        ) == gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gates = finalize_gates(checks)
    promote = all(target["capacity_before_labels"]["promote_bisector_family"] for target in target_rows)
    baseline_ledgers = [target["capacity_before_labels"]["baseline_complete_ledger_ms"] for target in target_rows]
    expanded_ledgers = [target["capacity_before_labels"]["expanded_complete_ledger_ms"] for target in target_rows]
    aggregate = {
        "minimum_warm_step_ms": min(target["warm_step_ms"] for target in target_rows),
        "median_warm_step_ms": float(np.median([target["warm_step_ms"] for target in target_rows])),
        "maximum_warm_step_ms": max(target["warm_step_ms"] for target in target_rows),
        "minimum_candidate_ms": min(row["complete_tier_b_candidate_ms"] for row in all_rows),
        "median_candidate_ms": float(np.median([row["complete_tier_b_candidate_ms"] for row in all_rows])),
        "maximum_candidate_ms": max(row["complete_tier_b_candidate_ms"] for row in all_rows),
        "minimum_baseline_complete_ledger_ms": min(baseline_ledgers),
        "maximum_baseline_complete_ledger_ms": max(baseline_ledgers),
        "minimum_expanded_complete_ledger_ms": min(expanded_ledgers),
        "maximum_expanded_complete_ledger_ms": max(expanded_ledgers),
        "minimum_expanded_profiled_k": min(target["capacity_before_labels"]["expanded_capacity"]["profiled_cumulative_k"] for target in target_rows),
        "minimum_expanded_worst_case_k": min(target["capacity_before_labels"]["expanded_capacity"]["worst_case_safe_k"] for target in target_rows),
        "distinct_bonus_rows": sum(target["capacity_before_labels"]["distinct_bonus_rows"] for target in target_rows),
        "expected_bonus_rows": 372,
        "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        "maximum_gpu_pool_total_bytes": max(row["gpu_pool_total_bytes"] for row in memory_rows),
        "promote_bisector_family": promote,
    }
    result = {
        "schema_version": 1,
        "status": "h32_continuation_direction_capacity_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "warm_steps": len(target_rows), "candidate_rows": len(all_rows),
            "quality_rows_serialized": 0, "affine_feature_values_serialized": 0,
            "certificates": 0, "strategy_labels": 0,
        },
        "target_rows": target_rows,
        "aggregate": aggregate,
        **gates,
        "decision": "authorize_fresh_bisector_direction_value_trial" if gates["passed"] and promote else "retain_regret_vertex_only_and_do_not_open_direction_labels" if gates["passed"] else "reject_direction_capacity_screen",
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "This is a label-free timing and structural screen on twelve reduced h32 continuation targets.",
            "The bisector is one fixed added ray, not a search over mixture weights or direction families.",
            "No quality vector, affine opportunity value, certificate, or strategy label is serialized.",
            "No strategy-quality, deployment, composition, population, or broad poker-strength claim is made.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_continuation_direction_capacity(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["passed"], "decision": result["decision"], "aggregate": result["aggregate"]}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
