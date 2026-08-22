"""One-round, label-free h32 prototype for the one-seat convex master."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .behavioral_one_seat_master import (
    BehavioralMasterSolution,
    BehavioralOneSeatAxis,
    solve_behavioral_one_seat_master,
)
from .behavioral_open_axis import behavioral_open_axis_payoff_row
from .cross_payoff_leaf_adjoint import (
    evaluate_device_fold_cross_payoff_leaf_adjoint,
)
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_one_seat_open_axis_preflight import (
    _pass_telemetry,
    _response_signature,
    _run_pass,
)
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_leaf_adjoint_response import evaluate_incremental_leaf_adjoint_seat
from .incremental_policy_tt import compile_policy_probability_tape
from .payoff_semantics import payoff_span, raw_guard
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)
from .sequence_form_open_axis import (
    SequenceFormAffineRow,
    affine_row_conditioning,
    constant_minus_affine_row,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from .shared_resident_response_context import (
    shared_device_numeric_bytes,
    unique_response_numeric_bytes,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-one-round-convex-master-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-one-round-convex-master-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT = _ROOT / "experiments/results/h32-one-seat-open-axis-preflight-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-one-seat-open-axis-preflight-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0245-h32-full-axis-rows-fit-one-conservative-cut-round.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_one_round_convex_master.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_parent_result_sha256": _PARENT,
    "expected_parent_config_sha256": _PARENT_CONFIG,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_master_sha256": _ROOT / "src/pontius/behavioral_one_seat_master.py",
    "expected_master_control_test_sha256": (
        _ROOT / "tests/test_behavioral_one_seat_master.py"
    ),
    "expected_behavioral_row_sha256": _ROOT / "src/pontius/behavioral_open_axis.py",
    "expected_sequence_row_sha256": _ROOT / "src/pontius/sequence_form_open_axis.py",
    "expected_cross_payoff_sha256": _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py",
    "expected_incremental_oracle_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_payoff_semantics_sha256": _ROOT / "src/pontius/payoff_semantics.py",
    "expected_setup_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": (
        _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
    ),
    "expected_preflight_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_seat_open_axis_preflight.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required one-round master input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corrected_one_round_reserve(
    parent_capacity: Mapping[str, Any],
    *,
    initial_master_reserve_ms: float,
) -> dict[str, float | bool]:
    """Add the initial master solve omitted from the ADR-0244 round formula."""

    required = (
        "one_round_complete_ledger_ms",
        "fixed_before_cut_rounds_ms",
        "complete_cut_round_ms",
    )
    if any(field not in parent_capacity for field in required):
        raise ValueError("one-round parent capacity fields are incomplete")
    values = tuple(float(parent_capacity[field]) for field in required) + (
        float(initial_master_reserve_ms),
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("one-round reserve values must be finite and nonnegative")
    if not math.isclose(values[0], values[1] + values[2], rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("one-round parent capacity arithmetic is inconsistent")
    corrected = values[0] + values[3]
    return {
        "parent_one_round_ledger_ms": values[0],
        "initial_master_reserve_ms": values[3],
        "corrected_one_round_ledger_ms": corrected,
        "correction_ms": values[3],
        "fits_15000_ms": corrected <= 15000.0,
    }


def bounded_gap(upper: float, lower: float, *, tolerance: float) -> float:
    """Return U-L and reject a material reversal of the minimization bound."""

    if any(not math.isfinite(value) for value in (upper, lower, tolerance)):
        raise ValueError("one-round bounds must be finite")
    if upper < 0.0 or lower < 0.0 or tolerance <= 0.0:
        raise ValueError("one-round bounds and tolerance must be nonnegative")
    gap = upper - lower
    allowance = tolerance * max(1.0, abs(upper), abs(lower))
    if gap < -allowance:
        raise ArithmeticError("one-round restricted lower bound exceeds incumbent")
    return max(0.0, gap)


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target",
        "acting_player",
        "scope",
        "master_rule",
        "oracle_rule",
        "cut_rule",
        "stopping_rule",
        "retreat_rule",
        "promotion_rule",
        "street_budget_ms",
        "emission_reserve_ms",
        "retreat_envelope_reserve_ms",
        "initial_master_reserve_ms",
        "maximum_cut_rounds",
        "acceptance_guard_normalized",
        "interior_retreat_factor",
        "lp_tolerance",
        "separation_tolerance",
        "bound_tolerance",
        "candidate_projection_tolerance",
        "envelope_numerical_allowance",
        "conditioning_tolerance",
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
        raise ValueError("one-round master config fields differ from ADR-0246")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"one-round master provenance mismatch: {field}")
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    exact = {
        "evidence_stage": "preregistered_after_adr0245_before_any_h32_master_solve_or_candidate_oracle",
        "seed": 20260822,
        "target": parent_config["target"],
        "acting_player": 0,
        "scope": "one_tight_retained_continuation_target_widest_acting_seat_one_multicut_round_label_free",
        "master_rule": "sparse_highs_dual_simplex_all_behavioral_simplex_rows_all_exact_response_rows_no_approximate_deletion",
        "oracle_rule": "all_six_exact_incremental_response_evaluations_for_every_master_candidate",
        "cut_rule": "all_epigraph_violating_opponent_response_signatures_added_in_one_multicut_round",
        "stopping_rule": "initial_master_then_oracle_then_at_most_one_multicut_resolve_then_independent_final_oracle_and_stop",
        "retreat_rule": "construct_halfway_blueprint_incumbent_mixture_for_diagnostics_only_without_emission_or_safety_authority",
        "promotion_rule": "only_closed_gap_cap_feasible_exact_final_oracle_and_complete_fifteen_second_ledger_may_authorize_a_later_quality_preregistration",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "retreat_envelope_reserve_ms": 50.0,
        "initial_master_reserve_ms": 500.0,
        "maximum_cut_rounds": 1,
        "acceptance_guard_normalized": 1e-10,
        "interior_retreat_factor": 0.5,
        "lp_tolerance": 1e-10,
        "separation_tolerance": 1e-9,
        "bound_tolerance": 1e-8,
        "candidate_projection_tolerance": 1e-10,
        "envelope_numerical_allowance": 2e-11,
        "conditioning_tolerance": 1e-12,
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
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "strategy_label_policy": "optimizer_bounds_and_feasibility_only_zero_strategy_quality_labels_immutable_blueprint_emission",
    }
    for field, value in exact.items():
        if config[field] != value:
            raise ValueError(f"one-round master field differs from ADR-0246: {field}")
    gates = {
        "expected_acting_public_nodes": 16,
        "expected_behavioral_information_sets": 512,
        "expected_policy_variables": 1024,
        "expected_epigraph_variables": 6,
        "expected_initial_profile_passes": 6,
        "expected_initial_response_passes": 5,
        "expected_initial_gain_rows": 6,
        "maximum_initial_row_error": 2e-11,
        "maximum_cut_row_error": 2e-11,
        "maximum_profile_equivalence_error": 2e-11,
        "maximum_master_primal_error": 1e-8,
        "maximum_master_dual_error": 1e-8,
        "maximum_projection_error": 1e-8,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_raw_guard_error": 1e-18,
        "maximum_cold_setup_ms": 120000.0,
        "maximum_warm_step_ms": 60000.0,
        "maximum_initial_row_ms": 60000.0,
        "maximum_master_ms": 60000.0,
        "maximum_oracle_ms": 60000.0,
        "maximum_cut_extraction_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_path_single_visit": True,
        "require_exact_external_axis_coverage": True,
        "require_all_opponent_multicut": True,
        "require_maximum_one_cut_round": True,
        "require_final_exact_oracle": True,
        "require_blueprint_emission": True,
        "require_strategy_quality_labels_zero": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("one-round master gates differ from ADR-0246")
    return {**config, "target": dict(config["target"]), "gates": gates}


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def _master_summary(solution: BehavioralMasterSolution) -> dict[str, Any]:
    return {
        key: value
        for key, value in asdict(solution).items()
        if key not in {"variables", "epigraph"}
    } | {
        "epigraph_variables": len(solution.epigraph),
        "epigraph_sha256": hashlib.sha256(
            np.asarray(solution.epigraph, dtype=np.float64).tobytes(order="C")
        ).hexdigest(),
    }


def _mix_policy(
    blueprint: Mapping[str, Mapping[Any, float]],
    endpoint: Mapping[str, Mapping[Any, float]],
    *,
    eta: float,
) -> tuple[dict[str, dict[Any, float]], float]:
    if not 0.0 <= eta <= 1.0:
        raise ValueError("one-round retreat factor must lie in [0, 1]")
    if set(blueprint) != set(endpoint):
        raise ValueError("one-round retreat policies have different schemas")
    result = {}
    maximum_mass_error = 0.0
    for key in blueprint:
        if set(blueprint[key]) != set(endpoint[key]):
            raise ValueError("one-round retreat action schemas differ")
        row = {
            action: (1.0 - eta) * float(blueprint[key][action])
            + eta * float(endpoint[key][action])
            for action in blueprint[key]
        }
        maximum_mass_error = max(maximum_mass_error, abs(sum(row.values()) - 1.0))
        result[key] = row
    return result, maximum_mass_error


def _exact_oracle(
    *,
    objects: Mapping[str, Any],
    policy: dict[str, dict[Any, float]],
    cp: Any,
    maximum_feature_width_per_batch: int,
) -> dict[str, Any]:
    layout = objects["layout"]
    context = objects["context"]
    shared = objects["shared"]
    probability_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(
        layout,
        objects["belief"].hands_by_player,
        policy,
    )
    probability_ms = (time.perf_counter() - probability_started) * 1000.0
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    evaluations = []
    for seat in range(layout.num_players):
        evaluations.append(
            evaluate_incremental_leaf_adjoint_seat(
                context.response_caches[seat],
                probabilities,
                maximum_feature_width_per_batch=maximum_feature_width_per_batch,
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[seat],
                cupy_sparse=objects["gpu"],
            )
        )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0 + probability_ms
    raw_gains = tuple(
        float(row.best_response_value - row.profile_utility) for row in evaluations
    )
    gains = tuple(max(0.0, value) for value in raw_gains)
    utilities = tuple(float(row.profile_utility) for row in evaluations)
    return {
        "policy_sha256": policy_digest(policy),
        "probabilities": probabilities,
        "evaluations": tuple(evaluations),
        "raw_gains": raw_gains,
        "gains": gains,
        "objective": math.fsum(gains),
        "response_signatures": tuple(
            _response_signature(row.best_response_actions) for row in evaluations
        ),
        "probability_compile_ms": probability_ms,
        "wall_ms": wall_ms,
        "zero_sum_residual": abs(math.fsum(utilities)),
        "response_action_flips": sum(row.response_action_flips for row in evaluations),
        "affected_terminal_contractions": sum(
            row.affected_terminal_contractions for row in evaluations
        ),
        "maximum_middle_rank": max(
            row.maximum_terminal_middle_rank for row in evaluations
        ),
        "maximum_gpu_pool_total_bytes": max(
            row.maximum_gpu_pool_total_bytes for row in evaluations
        ),
        "seat_wall_ms": tuple(float(row.wall_ms) for row in evaluations),
    }


def _oracle_summary(
    oracle: Mapping[str, Any],
    *,
    caps: tuple[float, ...],
    epigraph: tuple[float, ...],
    allowance: float,
) -> dict[str, Any]:
    cap_violations = tuple(
        gain - cap for gain, cap in zip(oracle["gains"], caps, strict=True)
    )
    epigraph_violations = tuple(
        gain - value
        for gain, value in zip(oracle["raw_gains"], epigraph, strict=True)
    )
    return {
        "policy_sha256": oracle["policy_sha256"],
        "objective": oracle["objective"],
        "response_signature_sha256": list(oracle["response_signatures"]),
        "probability_compile_ms": oracle["probability_compile_ms"],
        "wall_ms": oracle["wall_ms"],
        "zero_sum_residual": oracle["zero_sum_residual"],
        "response_action_flips": oracle["response_action_flips"],
        "affected_terminal_contractions": oracle["affected_terminal_contractions"],
        "maximum_middle_rank": oracle["maximum_middle_rank"],
        "maximum_gpu_pool_total_bytes": oracle["maximum_gpu_pool_total_bytes"],
        "seat_wall_ms": list(oracle["seat_wall_ms"]),
        "maximum_cap_violation": max(0.0, max(cap_violations)),
        "maximum_epigraph_violation": max(0.0, max(epigraph_violations)),
        "cap_feasible": max(cap_violations) <= allowance,
        "active_cap_players": [
            player
            for player, (gain, cap) in enumerate(zip(oracle["gains"], caps, strict=True))
            if cap - gain <= allowance
        ],
        "epigraph_violating_players": [
            player
            for player, violation in enumerate(epigraph_violations)
            if violation > allowance
        ],
    }


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    parent: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    cp.cuda.runtime.deviceSynchronize()
    setup_started = time.perf_counter()
    objects = _setup(parsed, source_parent, parsed["target"])
    cp.cuda.runtime.deviceSynchronize()
    cold_setup_ms = (time.perf_counter() - setup_started) * 1000.0
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    acting_player = int(parsed["acting_player"])

    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout,
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=objects["gpu"],
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
        record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * payoff_span(layout)
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [{"stage": "resident_source", **_memory_snapshot(cp)}]
    cp.cuda.runtime.deviceSynchronize()
    warm_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - warm_started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("one-round warm step emitted no work ledger")
    warm_works = tuple(row.resident_work for row in solver.last_step_work.traversers)
    warm_work = {
        "wall_ms": warm_step_ms,
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(warm_works),
    }
    memory_rows.append({"stage": "warm_step", **_memory_snapshot(cp)})

    source_probabilities = context.response_caches[0].source_probabilities
    profile_rows: dict[int, SequenceFormAffineRow] = {}
    row_libraries: list[dict[str, SequenceFormAffineRow]] = [
        {} for _ in range(layout.num_players)
    ]
    initial_pass_rows = []
    source_row_errors = []
    external_axis_splices = 0
    cp.cuda.runtime.deviceSynchronize()
    initial_started = time.perf_counter()
    for payoff_player in range(layout.num_players):
        cache = context.response_caches[payoff_player]
        row, telemetry, _ = _run_pass(
            objects=objects,
            probabilities=source_probabilities,
            acting_player=acting_player,
            payoff_player=payoff_player,
            source_value=float(cache.source_evaluation.profile_utility),
            kind="profile",
            cp=cp,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        profile_rows[payoff_player] = row
        initial_pass_rows.append(telemetry)
        source_row_errors.append(
            abs(row.value(source_probabilities) - cache.source_evaluation.profile_utility)
        )
    for payoff_player in range(layout.num_players):
        cache = context.response_caches[payoff_player]
        actions = cache.source_evaluation.best_response_actions
        signature = _response_signature(actions)
        if payoff_player == acting_player:
            gain = constant_minus_affine_row(
                cache.source_evaluation.best_response_value,
                profile_rows[payoff_player],
            )
        else:
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                source_probabilities,
                actions,
                responding_player=payoff_player,
                hands_by_player=belief.hands_by_player,
            )
            external_axis_splices += 1
            response, telemetry, _ = _run_pass(
                objects=objects,
                probabilities=response_probabilities,
                acting_player=acting_player,
                payoff_player=payoff_player,
                source_value=float(cache.source_evaluation.best_response_value),
                kind="fixed_response",
                cp=cp,
                maximum_feature_width_per_batch=int(
                    parsed["maximum_feature_width_per_batch"]
                ),
            )
            initial_pass_rows.append(telemetry)
            gain = subtract_affine_rows(response, profile_rows[payoff_player])
        source_row_errors.append(
            abs(
                gain.value(source_probabilities)
                - (
                    cache.source_evaluation.best_response_value
                    - cache.source_evaluation.profile_utility
                )
            )
        )
        row_libraries[payoff_player][signature] = gain
    cp.cuda.runtime.deviceSynchronize()
    initial_row_ms = (time.perf_counter() - initial_started) * 1000.0
    memory_rows.append({"stage": "initial_rows", **_memory_snapshot(cp)})

    axis = BehavioralOneSeatAxis.compile(
        layout,
        belief.hands_by_player,
        blueprint,
        acting_player=acting_player,
    )
    topology = compiled_layout_path_single_visit_report(layout)
    if not topology.passed:
        raise AssertionError("behavioral master topology changed after axis compilation")
    guard = raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain) for cache in context.response_caches
    )
    baseline_upper = math.fsum(source_gains)
    caps = tuple(gain + guard for gain in source_gains)
    initial_gain_rows = sum(len(rows) for rows in row_libraries)

    def solve_master() -> BehavioralMasterSolution:
        return solve_behavioral_one_seat_master(
            axis,
            tuple(tuple(rows.values()) for rows in row_libraries),
            caps,
            tolerance=float(parsed["lp_tolerance"]),
        )

    master_rows = []
    first_master = solve_master()
    master_rows.append(_master_summary(first_master))
    first_policy, first_projection_error = axis.policy_from_variables(
        first_master.variables,
        blueprint,
        tolerance=float(parsed["candidate_projection_tolerance"]),
    )
    first_oracle = _exact_oracle(
        objects=objects,
        policy=first_policy,
        cp=cp,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    first_summary = _oracle_summary(
        first_oracle,
        caps=caps,
        epigraph=first_master.epigraph,
        allowance=float(parsed["separation_tolerance"]),
    )
    memory_rows.append({"stage": "first_oracle", **_memory_snapshot(cp)})
    profile_equivalence_errors = [
        abs(
            profile_rows[player].value(first_oracle["probabilities"])
            - first_oracle["evaluations"][player].profile_utility
        )
        for player in range(layout.num_players)
    ]

    incumbent_policy = blueprint
    incumbent_upper = baseline_upper
    incumbent_source = "blueprint"
    if first_summary["cap_feasible"] and first_oracle["objective"] < incumbent_upper:
        incumbent_policy = first_policy
        incumbent_upper = float(first_oracle["objective"])
        incumbent_source = "first_master"

    violating_players = tuple(first_summary["epigraph_violating_players"])
    cut_rows = []
    cut_identity_errors = []
    cut_started = time.perf_counter()
    for player in violating_players:
        if player == acting_player:
            raise ArithmeticError("one-round invariant acting row is epigraph-violated")
        signature = first_oracle["response_signatures"][player]
        if signature in row_libraries[player]:
            raise ArithmeticError("one-round active exact response row remains violated")
        actions = first_oracle["evaluations"][player].best_response_actions
        response_probabilities = splice_fixed_response_probability_tape_for_axes(
            layout,
            source_probabilities,
            actions,
            responding_player=player,
            hands_by_player=belief.hands_by_player,
        )
        external_axis_splices += 1
        cp.cuda.runtime.deviceSynchronize()
        pass_started = time.perf_counter()
        extracted = evaluate_device_fold_cross_payoff_leaf_adjoint(
            layout,
            objects["workspace"],
            objects["sparse"],
            response_probabilities,
            objects["automata"][player],
            acting_player=acting_player,
            payoff_player=player,
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[player],
            cupy_sparse=objects["gpu"],
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
            record_to_hand_backend="gpu_cupy",
        )
        cp.cuda.runtime.deviceSynchronize()
        pass_ms = (time.perf_counter() - pass_started) * 1000.0
        response = behavioral_open_axis_payoff_row(
            layout,
            first_oracle["probabilities"],
            extracted,
            acting_player=acting_player,
            source_value=float(first_oracle["evaluations"][player].best_response_value),
        )
        gain = subtract_affine_rows(response, profile_rows[player])
        identity_error = abs(
            gain.value(first_oracle["probabilities"])
            - first_oracle["raw_gains"][player]
        )
        cut_identity_errors.append(identity_error)
        row_libraries[player][signature] = gain
        cut_rows.append(
            {
                "target_player": player,
                "response_signature_sha256": signature,
                "candidate_row_identity_error": identity_error,
                **_pass_telemetry(
                    kind="generated_response",
                    payoff_player=player,
                    wall_ms=pass_ms,
                    result=extracted,
                ),
            }
        )
    cp.cuda.runtime.deviceSynchronize()
    cut_extraction_ms = (time.perf_counter() - cut_started) * 1000.0
    memory_rows.append({"stage": "cuts", **_memory_snapshot(cp)})

    cut_rounds = int(bool(cut_rows))
    if cut_rounds > int(parsed["maximum_cut_rounds"]):
        raise AssertionError("one-round prototype exceeded the frozen cut count")
    second_master = None
    second_projection_error = 0.0
    final_oracle = first_oracle
    final_summary = first_summary
    final_policy = first_policy
    if cut_rows:
        second_master = solve_master()
        master_rows.append(_master_summary(second_master))
        final_policy, second_projection_error = axis.policy_from_variables(
            second_master.variables,
            blueprint,
            tolerance=float(parsed["candidate_projection_tolerance"]),
        )
        final_oracle = _exact_oracle(
            objects=objects,
            policy=final_policy,
            cp=cp,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        final_summary = _oracle_summary(
            final_oracle,
            caps=caps,
            epigraph=second_master.epigraph,
            allowance=float(parsed["separation_tolerance"]),
        )
        memory_rows.append({"stage": "final_oracle", **_memory_snapshot(cp)})
        profile_equivalence_errors.extend(
            abs(
                profile_rows[player].value(final_oracle["probabilities"])
                - final_oracle["evaluations"][player].profile_utility
            )
            for player in range(layout.num_players)
        )
        if final_summary["cap_feasible"] and final_oracle["objective"] < incumbent_upper:
            incumbent_policy = final_policy
            incumbent_upper = float(final_oracle["objective"])
            incumbent_source = "resolved_master"

    final_master = first_master if second_master is None else second_master
    lower_bound = max(float(row["lower_bound"]) for row in master_rows)
    lower_bound_nondecreasing = all(
        right["lower_bound"]
        >= left["lower_bound"]
        - float(parsed["bound_tolerance"])
        * max(1.0, abs(left["lower_bound"]), abs(right["lower_bound"]))
        for left, right in zip(master_rows, master_rows[1:])
    )
    gap = bounded_gap(
        incumbent_upper,
        lower_bound,
        tolerance=float(parsed["bound_tolerance"]),
    )
    converged = final_summary["maximum_epigraph_violation"] <= float(
        parsed["separation_tolerance"]
    )

    retreat_started = time.perf_counter()
    retreated, retreat_mass_error = _mix_policy(
        blueprint,
        incumbent_policy,
        eta=float(parsed["interior_retreat_factor"]),
    )
    retreat_ms = (time.perf_counter() - retreat_started) * 1000.0
    conditioning = [
        asdict(
            affine_row_conditioning(
                tuple(rows.values()),
                tolerance=float(parsed["conditioning_tolerance"]),
            )
        )
        for rows in row_libraries
    ]

    parent_capacity = parent["target"]["capacity_before_teacher"]
    corrected_reserve = corrected_one_round_reserve(
        parent_capacity,
        initial_master_reserve_ms=float(parsed["initial_master_reserve_ms"]),
    )
    master_ms = math.fsum(row["solve_ms"] for row in master_rows)
    oracle_ms = float(first_oracle["wall_ms"]) + (
        0.0 if second_master is None else float(final_oracle["wall_ms"])
    )
    measured_live_ms = (
        warm_step_ms
        + initial_row_ms
        + master_ms
        + oracle_ms
        + cut_extraction_ms
        + max(retreat_ms, float(parsed["retreat_envelope_reserve_ms"]))
        + float(parsed["emission_reserve_ms"])
    )
    final_response_signatures = tuple(final_oracle["response_signatures"])
    total_library_rows = sum(len(rows) for rows in row_libraries)
    exact_external_axis_coverage = (
        external_axis_splices == (layout.num_players - 1) + len(cut_rows)
    )
    maximum_pool = max(
        max(row["gpu_pool_total_bytes"] for row in memory_rows),
        max(row["maximum_gpu_pool_total_bytes"] for row in initial_pass_rows),
        max((row["maximum_gpu_pool_total_bytes"] for row in cut_rows), default=0),
        int(first_oracle["maximum_gpu_pool_total_bytes"]),
        int(final_oracle["maximum_gpu_pool_total_bytes"]),
    )
    minimum_free = min(row["gpu_free_bytes"] for row in memory_rows)
    maximum_master_primal = max(
        max(row["maximum_equality_error"] for row in master_rows),
        max(row["maximum_inequality_violation"] for row in master_rows),
        max(row["maximum_bound_violation"] for row in master_rows),
    )
    maximum_master_dual = max(
        max(row["maximum_stationarity_error"] for row in master_rows),
        max(row["maximum_complementarity_error"] for row in master_rows),
        max(row["duality_gap"] for row in master_rows),
    )
    result = {
        "target_id": parsed["target"]["target_id"],
        "acting_player": acting_player,
        "acting_public_nodes": len(axis.acting_nodes),
        "path_single_visit": topology.passed,
        "behavioral_information_sets": len(axis.information_sets),
        "policy_variables": axis.variable_count,
        "epigraph_variables": layout.num_players,
        "raw_guard": guard,
        "source_nash_conv": baseline_upper,
        "caps_sha256": hashlib.sha256(
            np.asarray(caps, dtype=np.float64).tobytes(order="C")
        ).hexdigest(),
        "cold_setup_ms": cold_setup_ms,
        "warm_start_distance": warm_distance,
        "warm_step": warm_work,
        "initial_profile_passes": sum(
            row["kind"] == "profile" for row in initial_pass_rows
        ),
        "initial_response_passes": sum(
            row["kind"] == "fixed_response" for row in initial_pass_rows
        ),
        "initial_gain_rows": initial_gain_rows,
        "initial_row_ms": initial_row_ms,
        "initial_pass_rows": initial_pass_rows,
        "maximum_initial_row_error": max(source_row_errors),
        "masters": master_rows,
        "first_candidate_projection_error": first_projection_error,
        "second_candidate_projection_error": second_projection_error,
        "first_oracle": first_summary,
        "cut_rounds": cut_rounds,
        "cut_rows": cut_rows,
        "cut_extraction_ms": cut_extraction_ms,
        "maximum_cut_row_error": max(cut_identity_errors, default=0.0),
        "final_oracle": final_summary,
        "final_exact_oracle_executed": True,
        "exact_oracles_executed": 1 + int(second_master is not None),
        "maximum_profile_equivalence_error": max(profile_equivalence_errors),
        "lower_bound": lower_bound,
        "lower_bound_nondecreasing": lower_bound_nondecreasing,
        "incumbent_upper_bound": incumbent_upper,
        "optimality_gap": gap,
        "incumbent_source": incumbent_source,
        "converged_after_frozen_round": converged,
        "final_cap_feasible": final_summary["cap_feasible"],
        "final_active_cap_players": final_summary["active_cap_players"],
        "final_response_signature_sha256": list(final_response_signatures),
        "row_counts_by_player": [len(rows) for rows in row_libraries],
        "total_exact_response_rows": total_library_rows,
        "conditioning_by_player": conditioning,
        "maximum_master_primal_error": maximum_master_primal,
        "maximum_master_dual_error": maximum_master_dual,
        "retreat": {
            "factor": parsed["interior_retreat_factor"],
            "applied_to": incumbent_source,
            "policy_sha256": policy_digest(retreated),
            "maximum_simplex_mass_error": retreat_mass_error,
            "guaranteed_guard_slack_restored": (
                (1.0 - float(parsed["interior_retreat_factor"])) * guard
            ),
            "independently_certified": False,
            "emitted": False,
        },
        "ledger": {
            "measured_live_ms": measured_live_ms,
            "measured_headroom_ms": float(parsed["street_budget_ms"])
            - measured_live_ms,
            "corrected_parent_reserve": corrected_reserve,
            "fits_measured_street": measured_live_ms
            <= float(parsed["street_budget_ms"]),
            "fits_corrected_conservative_street": bool(
                corrected_reserve["fits_15000_ms"]
            ),
        },
        "memory_rows": memory_rows,
        "maximum_gpu_pool_total_bytes": maximum_pool,
        "minimum_gpu_free_bytes": minimum_free,
        "resident_numeric_bytes": {
            "shared_device": shared_device_numeric_bytes(shared, (context,)),
            "unique_response_host": unique_response_numeric_bytes((context,)),
            "solver": solver.memory_summary(),
        },
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(objects["state"])
        == objects["state"]["state_sha256"]
        and _belief_digest(objects["source"])
        == parsed["target"]["source_belief_sha256"],
        "target_identity": _belief_digest(belief)
        == parsed["target"]["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"])
        == objects["state"]["average_policy_sha256"],
        "exact_external_axis_coverage": exact_external_axis_coverage,
        "external_axis_splices": external_axis_splices,
        "all_opponent_multicut": all(
            player in {row["target_player"] for row in cut_rows}
            for player in violating_players
            if player != acting_player
        ),
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "actual_emitted_policy_sha256": policy_digest(blueprint),
        "candidate_policies_emitted": 0,
        "strategy_quality_labels_generated": 0,
        "strategy_quality_claim": None,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_one_round_convex_master(
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
    parent = load_artifact(
        _PARENT,
        expected_sha256=parsed["expected_parent_result_sha256"],
        require_passed=True,
    ).payload
    target = _run_target(parsed, source, parent, cp)
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    all_master_rows = target["masters"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(row) for row in (source, parent))
        == gate["require_parents_passed"],
        "target_identity": bool(
            target["source_checkpoint_identity"] and target["target_identity"]
        )
        == gate["require_target_identity"],
        "blueprint_identity": bool(target["blueprint_identity"])
        == gate["require_blueprint_identity"],
        "warm_start_identity": (
            target["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": target["path_single_visit"]
        == gate["require_path_single_visit"],
        "acting_node_count": target["acting_public_nodes"]
        == gate["expected_acting_public_nodes"],
        "information_set_count": target["behavioral_information_sets"]
        == gate["expected_behavioral_information_sets"],
        "policy_variable_count": target["policy_variables"]
        == gate["expected_policy_variables"],
        "epigraph_variable_count": target["epigraph_variables"]
        == gate["expected_epigraph_variables"],
        "initial_profile_pass_count": target["initial_profile_passes"]
        == gate["expected_initial_profile_passes"],
        "initial_response_pass_count": target["initial_response_passes"]
        == gate["expected_initial_response_passes"],
        "initial_gain_row_count": target["initial_gain_rows"]
        == gate["expected_initial_gain_rows"],
        "initial_row_identity": target["maximum_initial_row_error"]
        <= gate["maximum_initial_row_error"],
        "cut_row_identity": target["maximum_cut_row_error"]
        <= gate["maximum_cut_row_error"],
        "profile_equivalence": target["maximum_profile_equivalence_error"]
        <= gate["maximum_profile_equivalence_error"],
        "master_primal": target["maximum_master_primal_error"]
        <= gate["maximum_master_primal_error"],
        "master_dual": target["maximum_master_dual_error"]
        <= gate["maximum_master_dual_error"],
        "candidate_projection": max(
            target["first_candidate_projection_error"],
            target["second_candidate_projection_error"],
        )
        <= gate["maximum_projection_error"],
        "raw_guard": abs(target["raw_guard"] - 3e-9)
        <= gate["maximum_raw_guard_error"],
        "cold_setup_time": target["cold_setup_ms"] <= gate["maximum_cold_setup_ms"],
        "warm_step_time": target["warm_step"]["wall_ms"]
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": target["initial_row_ms"]
        <= gate["maximum_initial_row_ms"],
        "master_time": max(row["solve_ms"] for row in all_master_rows)
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            target["first_oracle"]["wall_ms"],
            target["final_oracle"]["wall_ms"],
        )
        <= gate["maximum_oracle_ms"],
        "cut_extraction_time": target["cut_extraction_ms"]
        <= gate["maximum_cut_extraction_ms"],
        "gpu_pool": target["maximum_gpu_pool_total_bytes"]
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": target["minimum_gpu_free_bytes"]
        >= gate["minimum_physical_free_bytes"],
        "external_axis_coverage": target["exact_external_axis_coverage"]
        == gate["require_exact_external_axis_coverage"],
        "all_opponent_multicut": target["all_opponent_multicut"]
        == gate["require_all_opponent_multicut"],
        "maximum_one_cut_round": (target["cut_rounds"] <= 1)
        == gate["require_maximum_one_cut_round"],
        "master_oracle_count": (
            len(target["masters"]) == 1 + target["cut_rounds"]
            and target["exact_oracles_executed"] == 1 + target["cut_rounds"]
        ),
        "lower_bound_monotonicity": target["lower_bound_nondecreasing"],
        "final_exact_oracle": target["final_exact_oracle_executed"]
        == gate["require_final_exact_oracle"],
        "blueprint_emission": (
            target["actual_emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
            and target["candidate_policies_emitted"] == 0
        )
        == gate["require_blueprint_emission"],
        "strategy_quality_labels_zero": (
            target["strategy_quality_labels_generated"] == 0
            and target["strategy_quality_claim"] is None
        )
        == gate["require_strategy_quality_labels_zero"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    promote = bool(
        gate_result["passed"]
        and target["converged_after_frozen_round"]
        and target["final_cap_feasible"]
        and target["optimality_gap"] <= float(parsed["bound_tolerance"])
        and target["ledger"]["fits_measured_street"]
        and target["ledger"]["fits_corrected_conservative_street"]
    )
    result = {
        "schema_version": 1,
        "status": "h32_one_round_convex_master_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": 1,
            "acting_seats": 1,
            "maximum_cut_rounds": 1,
            "exact_oracles": target["exact_oracles_executed"],
            "final_exact_certificates": 1,
            "strategy_quality_labels": 0,
            "candidate_policies_emitted": 0,
        },
        "target": target,
        "aggregate": {
            "initial_lower_bound": target["masters"][0]["lower_bound"],
            "final_lower_bound": target["lower_bound"],
            "incumbent_upper_bound": target["incumbent_upper_bound"],
            "optimality_gap": target["optimality_gap"],
            "cut_rounds": target["cut_rounds"],
            "added_response_rows": len(target["cut_rows"]),
            "converged_after_frozen_round": target["converged_after_frozen_round"],
            "final_cap_feasible": target["final_cap_feasible"],
            "measured_live_ms": target["ledger"]["measured_live_ms"],
            "measured_headroom_ms": target["ledger"]["measured_headroom_ms"],
            "promote_later_quality_preregistration": promote,
        },
        **gate_result,
        "decision": (
            "authorize_later_preregistered_one_seat_quality_trial"
            if promote
            else "reject_live_one_seat_convex_master_at_current_cost_or_round_budget"
            if gate_result["passed"]
            else "reject_one_round_convex_master_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_quality_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "Optimizer bounds diagnose the one-seat program; they are not a strategy-quality claim.",
            "The prototype permits one multi-cut round and never borrows the final-certificate reserve.",
            "The half-retreat policy is not independently certified and is not emitted.",
            "Any later quality question requires a separate preregistration and exact emission certificate.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_one_round_convex_master(args.config, args.output)
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
