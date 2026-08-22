"""Label-free h32 feasibility screen for a complete cross-payoff Jacobian."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .cross_payoff_leaf_adjoint import (
    evaluate_device_fold_cross_payoff_leaf_adjoint,
    project_public_node_direction_slope,
    splice_fixed_response_probability_tape,
)
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_direction_capacity import _finite_tree
from .h32_continuation_root_ledger import _setup
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
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
_CONFIG = _ROOT / "experiments/configs/h32-cross-payoff-adjoint-feasibility-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-cross-payoff-adjoint-feasibility-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_CAPACITY = _ROOT / "experiments/results/h32-continuation-direction-capacity-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0237-full-bisector-library-does-not-fit-every-street.md"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-continuation-direction-capacity-v1.json"
_IMPLEMENTATION = Path(__file__)
_PRIMITIVE = _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py"
_TEST = _ROOT / "tests/test_h32_cross_payoff_adjoint_feasibility.py"
_PRIMITIVE_TEST = _ROOT / "tests/test_cross_payoff_leaf_adjoint.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_capacity_result_sha256": _CAPACITY,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_parent_config_sha256": _PARENT_CONFIG,
    "expected_cross_payoff_primitive_sha256": _PRIMITIVE,
    "expected_cross_payoff_control_test_sha256": _PRIMITIVE_TEST,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required cross-payoff input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reverse_adjoint_feasibility_decision(
    *,
    warm_step_ms: float,
    cross_matrix_ms: float,
    street_budget_ms: float,
    certificate_reserve_ms: float,
    envelope_reserve_ms: float,
    optimizer_reserve_ms: float,
    emission_reserve_ms: float,
) -> dict[str, Any]:
    """Price one complete Jacobian, one generated direction, and one proof."""

    values = (
        warm_step_ms,
        cross_matrix_ms,
        street_budget_ms,
        certificate_reserve_ms,
        envelope_reserve_ms,
        optimizer_reserve_ms,
        emission_reserve_ms,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("cross-payoff feasibility times must be finite and nonnegative")
    if street_budget_ms <= 0.0:
        raise ValueError("cross-payoff street budget must be positive")
    complete = (
        warm_step_ms
        + cross_matrix_ms
        + certificate_reserve_ms
        + envelope_reserve_ms
        + optimizer_reserve_ms
        + emission_reserve_ms
    )
    return {
        "complete_generated_direction_ledger_ms": complete,
        "headroom_ms": street_budget_ms - complete,
        "fits_street": complete <= street_budget_ms,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target_id",
        "scope",
        "matrix_rule",
        "zero_sum_rule",
        "teacher_rule",
        "promotion_rule",
        "street_budget_ms",
        "certificate_reserve_ms",
        "envelope_reserve_ms",
        "optimizer_reserve_ms",
        "emission_reserve_ms",
        "pot",
        "stack",
        "bet_size",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "query_chunk_records",
        "solver_variant",
        "warm_regret_mass_payoff_fraction",
        "maximum_feature_width_per_batch",
        "selector_margin_allowance",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "cuda_dll_environment_variable",
        "strategy_label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("cross-payoff config fields differ from ADR-0238")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"cross-payoff provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0237_before_any_cross_payoff_h32_pass",
        "seed": 20260822,
        "target_id": "panel_2/balanced/checks_then_bet_seat1",
        "scope": "one_tight_retained_continuation_target_complete_regret_library_label_free",
        "matrix_rule": "six_acting_seats_times_four_cross_profile_passes_plus_five_fixed_response_passes",
        "zero_sum_rule": "acting_utility_slope_from_free_affine_row_then_one_opponent_profile_slope_inferred_from_exact_six_seat_zero_sum",
        "teacher_rule": "all_thirty_one_regret_vertex_rows_times_six_affine_seats_recomputed_after_matrix_timing_only",
        "promotion_rule": "all_coefficients_match_teacher_and_complete_matrix_generated_direction_proof_emission_ledger_fits_fifteen_seconds",
        "street_budget_ms": 15000.0,
        "certificate_reserve_ms": 1250.0,
        "envelope_reserve_ms": 10.0,
        "optimizer_reserve_ms": 10.0,
        "emission_reserve_ms": 1000.0,
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
        "maximum_feature_width_per_batch": 384,
        "selector_margin_allowance": 2e-11,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "strategy_label_policy": "zero_quality_rows_zero_certificates_zero_strategy_labels",
    }
    for field, value in exact.items():
        if config[field] != value:
            raise ValueError(f"cross-payoff field differs from ADR-0238: {field}")
    gates = {
        "expected_blocks": 31,
        "expected_information_sets": 992,
        "expected_own_rows": 31,
        "expected_cross_profile_passes": 24,
        "expected_fixed_response_passes": 30,
        "expected_teacher_rows": 186,
        "maximum_profile_slope_error": 2e-11,
        "maximum_response_slope_error": 2e-11,
        "maximum_gain_slope_error": 2e-11,
        "maximum_zero_sum_source_residual": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_warm_step_ms": 60000.0,
        "maximum_cross_matrix_ms": 60000.0,
        "maximum_teacher_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_target_identity": True,
        "require_blueprint_emission": True,
        "require_new_strategy_labels_zero": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("cross-payoff gates differ from ADR-0238")
    return {**config, "gates": gates}


def _changed_node(
    source: Sequence[np.ndarray | None], endpoint: Sequence[np.ndarray | None]
) -> int:
    changed = tuple(
        index
        for index, (first, second) in enumerate(zip(source, endpoint, strict=True))
        if first is not None and second is not None and not np.array_equal(first, second)
    )
    if len(changed) != 1:
        raise ValueError("cross-payoff endpoint must change exactly one public node")
    return changed[0]


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
    warm_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - warm_started) * 1000.0
    soft = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    blocks = _ordered_blocks(layout, blueprint, soft)
    source_probabilities = context.response_caches[0].source_probabilities
    endpoints = []
    own_rows = {}
    for block_index, block in enumerate(blocks):
        acting = int(block["acting_seat"])
        endpoint = build_regret_vertex_candidate(
            blueprint,
            regret_deltas,
            tuple(block["information_keys"]),
        )
        probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        node_index = _changed_node(source_probabilities, probabilities)
        own = evaluate_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[acting],
            probabilities,
            acting_player=acting,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        )
        if own.affected_terminal_contractions != 0:
            raise AssertionError("cross-payoff own affine row performed a contraction")
        own_rows[block_index] = own
        endpoints.append((block_index, block, probabilities, node_index))

    source_utility_sum = math.fsum(
        float(cache.source_evaluation.profile_utility)
        for cache in context.response_caches
    )
    predicted: dict[tuple[int, int], tuple[float, float, float]] = {}
    profile_passes = 0
    response_passes = 0
    cross_terms = 0
    release_cupy_memory_pool()
    cp.cuda.runtime.deviceSynchronize()
    cross_started = time.perf_counter()
    for acting in range(layout.num_players):
        acting_rows = tuple(row for row in endpoints if int(row[1]["acting_seat"]) == acting)
        opponents = tuple(seat for seat in range(layout.num_players) if seat != acting)
        inferred_profile = opponents[-1]
        utility_slopes: dict[int, dict[int, float]] = {
            block_index: {acting: float(own_rows[block_index].profile_utility_slope)}
            for block_index, _, _, _ in acting_rows
        }
        for payoff in opponents[:-1]:
            adjoint = evaluate_device_fold_cross_payoff_leaf_adjoint(
                layout,
                objects["workspace"],
                objects["sparse"],
                source_probabilities,
                objects["automata"][payoff],
                acting_player=acting,
                payoff_player=payoff,
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[payoff],
                cupy_sparse=gpu,
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            )
            profile_passes += 1
            cross_terms += adjoint.terminal_contractions
            for block_index, _, probabilities, node_index in acting_rows:
                utility_slopes[block_index][payoff] = project_public_node_direction_slope(
                    adjoint,
                    layout,
                    source_probabilities,
                    probabilities,
                    acting_player=acting,
                    changed_public_node=node_index,
                )
        for block_index, _, _, _ in acting_rows:
            utility_slopes[block_index][inferred_profile] = -math.fsum(
                utility_slopes[block_index].values()
            )

        for payoff in opponents:
            response_tape = splice_fixed_response_probability_tape(
                layout,
                source_probabilities,
                context.response_caches[payoff].source_evaluation.best_response_actions,
                responding_player=payoff,
            )
            adjoint = evaluate_device_fold_cross_payoff_leaf_adjoint(
                layout,
                objects["workspace"],
                objects["sparse"],
                response_tape,
                objects["automata"][payoff],
                acting_player=acting,
                payoff_player=payoff,
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[payoff],
                cupy_sparse=gpu,
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            )
            response_passes += 1
            cross_terms += adjoint.terminal_contractions
            for block_index, _, probabilities, node_index in acting_rows:
                response_slope = project_public_node_direction_slope(
                    adjoint,
                    layout,
                    source_probabilities,
                    probabilities,
                    acting_player=acting,
                    changed_public_node=node_index,
                )
                profile_slope = utility_slopes[block_index][payoff]
                predicted[(block_index, payoff)] = (
                    profile_slope,
                    response_slope,
                    response_slope - profile_slope,
                )
        for block_index, _, _, _ in acting_rows:
            own_profile = utility_slopes[block_index][acting]
            predicted[(block_index, acting)] = (
                own_profile,
                0.0,
                -own_profile,
            )
    cp.cuda.runtime.deviceSynchronize()
    cross_matrix_ms = (time.perf_counter() - cross_started) * 1000.0
    memory_rows.append(_memory_snapshot(cp))

    maximum_profile_error = 0.0
    maximum_response_error = 0.0
    maximum_gain_error = 0.0
    teacher_rows = 0
    cp.cuda.runtime.deviceSynchronize()
    teacher_started = time.perf_counter()
    for block_index, block, probabilities, _ in endpoints:
        acting = int(block["acting_seat"])
        for payoff in range(layout.num_players):
            if payoff == acting:
                teacher = own_rows[block_index]
            else:
                teacher = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                    context.response_caches[payoff],
                    probabilities,
                    acting_player=acting,
                    selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                    maximum_feature_width_per_batch=int(
                        parsed["maximum_feature_width_per_batch"]
                    ),
                    belief_cache=context.belief_cache,
                    automaton_cache=shared.automaton_caches[payoff],
                    cupy_sparse=gpu,
                    record_to_hand_backend="gpu_cupy",
                ).semantic
            actual = predicted[(block_index, payoff)]
            maximum_profile_error = max(
                maximum_profile_error,
                abs(actual[0] - float(teacher.profile_utility_slope)),
            )
            maximum_response_error = max(
                maximum_response_error,
                abs(actual[1] - float(teacher.best_response_value_slope)),
            )
            maximum_gain_error = max(
                maximum_gain_error,
                abs(actual[2] - float(teacher.deviation_gap_slope)),
            )
            teacher_rows += 1
    cp.cuda.runtime.deviceSynchronize()
    teacher_ms = (time.perf_counter() - teacher_started) * 1000.0
    memory_rows.append(_memory_snapshot(cp))
    feasibility = reverse_adjoint_feasibility_decision(
        warm_step_ms=warm_step_ms,
        cross_matrix_ms=cross_matrix_ms,
        street_budget_ms=float(parsed["street_budget_ms"]),
        certificate_reserve_ms=float(parsed["certificate_reserve_ms"]),
        envelope_reserve_ms=float(parsed["envelope_reserve_ms"]),
        optimizer_reserve_ms=float(parsed["optimizer_reserve_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
    )
    result = {
        "target_id": spec["target_id"],
        "target_belief_sha256": spec["target_belief_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "warm_start_distance": warm_distance,
        "warm_step_ms": warm_step_ms,
        "blocks": len(blocks),
        "information_sets": sum(int(block["information_set_count"]) for block in blocks),
        "own_rows": len(own_rows),
        "cross_profile_passes": profile_passes,
        "fixed_response_passes": response_passes,
        "cross_terminal_terms": cross_terms,
        "teacher_rows": teacher_rows,
        "cross_matrix_ms": cross_matrix_ms,
        "teacher_ms": teacher_ms,
        "maximum_profile_slope_error": maximum_profile_error,
        "maximum_response_slope_error": maximum_response_error,
        "maximum_gain_slope_error": maximum_gain_error,
        "source_zero_sum_residual": abs(source_utility_sum),
        "feasibility_before_labels": feasibility,
        "quality_rows_serialized": 0,
        "certificates_executed": 0,
        "strategy_labels_generated": 0,
        "emitted_policy_sha256": policy_digest(blueprint),
        "memory_rows": memory_rows,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_cross_payoff_adjoint_feasibility(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    capacity = load_artifact(
        _CAPACITY,
        expected_sha256=parsed["expected_capacity_result_sha256"],
        require_passed=True,
    ).payload
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    spec = next(
        row for row in parent_config["targets"] if row["target_id"] == parsed["target_id"]
    )
    target = _run_target(parsed, source, spec, cp)
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    memory_rows = target["memory_rows"]
    checks = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "parents_passed": all(artifact_passed(row) for row in (source, capacity))
        == gates["require_parents_passed"],
        "target_identity": target["target_belief_sha256"] == spec["target_belief_sha256"]
        == gates["require_target_identity"],
        "block_count": target["blocks"] == gates["expected_blocks"],
        "information_set_count": target["information_sets"]
        == gates["expected_information_sets"],
        "own_row_count": target["own_rows"] == gates["expected_own_rows"],
        "cross_profile_pass_count": target["cross_profile_passes"]
        == gates["expected_cross_profile_passes"],
        "fixed_response_pass_count": target["fixed_response_passes"]
        == gates["expected_fixed_response_passes"],
        "teacher_row_count": target["teacher_rows"] == gates["expected_teacher_rows"],
        "profile_slope_identity": target["maximum_profile_slope_error"]
        <= gates["maximum_profile_slope_error"],
        "response_slope_identity": target["maximum_response_slope_error"]
        <= gates["maximum_response_slope_error"],
        "gain_slope_identity": target["maximum_gain_slope_error"]
        <= gates["maximum_gain_slope_error"],
        "source_zero_sum": target["source_zero_sum_residual"]
        <= gates["maximum_zero_sum_source_residual"],
        "warm_start_identity": target["warm_start_distance"]["maximum_probability_error"]
        <= gates["maximum_warm_start_probability_error"]
        and target["warm_start_distance"]["mean_total_variation"]
        <= gates["maximum_warm_start_mean_total_variation"],
        "warm_step_time": target["warm_step_ms"] <= gates["maximum_warm_step_ms"],
        "cross_matrix_time": target["cross_matrix_ms"]
        <= gates["maximum_cross_matrix_ms"],
        "teacher_time": target["teacher_ms"] <= gates["maximum_teacher_ms"],
        "gpu_pool": max(row["gpu_pool_total_bytes"] for row in memory_rows)
        <= gates["maximum_gpu_pool_bytes"],
        "physical_free": min(row["gpu_free_bytes"] for row in memory_rows)
        >= gates["minimum_physical_free_bytes"],
        "blueprint_emission": target["emitted_policy_sha256"]
        == target["restricted_blueprint_policy_sha256"]
        == gates["require_blueprint_emission"],
        "new_strategy_labels_zero": target["strategy_labels_generated"] == 0
        == gates["require_new_strategy_labels_zero"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
        "finite": _finite_tree(target) == gates["require_finite"],
    }
    gate_result = finalize_gates(checks)
    identity_ok = all(
        checks[field]
        for field in (
            "profile_slope_identity",
            "response_slope_identity",
            "gain_slope_identity",
            "source_zero_sum",
        )
    )
    promote = bool(
        gate_result["passed"]
        and identity_ok
        and target["feasibility_before_labels"]["fits_street"]
    )
    parent_target = next(
        row for row in capacity["target_rows"] if row["target_id"] == parsed["target_id"]
    )
    parent_baseline_ms = math.fsum(
        float(row["complete_tier_b_candidate_ms"])
        for row in parent_target["candidate_rows"][:31]
    )
    result = {
        "schema_version": 1,
        "status": "h32_cross_payoff_adjoint_feasibility_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": 1,
            "warm_steps": 1,
            "cross_profile_passes": target["cross_profile_passes"],
            "fixed_response_passes": target["fixed_response_passes"],
            "teacher_rows": target["teacher_rows"],
            "quality_rows_serialized": 0,
            "certificates": 0,
            "strategy_labels": 0,
        },
        "target": target,
        "aggregate": {
            "cross_matrix_ms": target["cross_matrix_ms"],
            "direction_specific_parent_baseline_ms": parent_baseline_ms,
            "matrix_to_parent_baseline_ratio": target["cross_matrix_ms"]
            / parent_baseline_ms,
            "complete_generated_direction_ledger_ms": target[
                "feasibility_before_labels"
            ]["complete_generated_direction_ledger_ms"],
            "ledger_headroom_ms": target["feasibility_before_labels"]["headroom_ms"],
            "promote_safe_cone_optimizer_prototype": promote,
        },
        **gate_result,
        "decision": (
            "authorize_label_free_safe_cone_optimizer_prototype"
            if promote
            else "retire_full_cross_payoff_matrix_from_live_path"
            if gate_result["passed"]
            else "reject_cross_payoff_feasibility_screen"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "This is a label-free engineering screen on one deliberately tight reduced-h32 continuation target.",
            "The matrix is compared with the accepted affine teacher but no opportunity or strategy value is serialized.",
            "A passing result authorizes only a label-free direction-constructor prototype, not strategy evaluation or deployment.",
            "A failing latency result rejects this complete-matrix live implementation, not the cross-payoff identity.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_cross_payoff_adjoint_feasibility(args.config, args.output)
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
