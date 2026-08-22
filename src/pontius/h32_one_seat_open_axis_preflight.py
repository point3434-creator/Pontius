"""Label-free h32 preflight for one complete acting-seat affine row library."""

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
from .behavioral_open_axis import behavioral_open_axis_payoff_row
from .cross_payoff_leaf_adjoint import (
    evaluate_device_fold_cross_payoff_leaf_adjoint,
)
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_heldout_continuation_depth_value_trial import _ordered_blocks
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_policy_tt import compile_policy_probability_tape
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)
from .selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
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
_CONFIG = _ROOT / "experiments/configs/h32-one-seat-open-axis-preflight-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-one-seat-open-axis-preflight-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_CAPACITY = _ROOT / "experiments/results/h32-continuation-direction-capacity-v1.json"
_CAPACITY_CONFIG = _ROOT / "experiments/configs/h32-continuation-direction-capacity-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0243-h4-open-axis-rows-match-dense-teachers.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_one_seat_open_axis_preflight.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_capacity_result_sha256": _CAPACITY,
    "expected_capacity_config_sha256": _CAPACITY_CONFIG,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_behavioral_row_sha256": _ROOT / "src/pontius/behavioral_open_axis.py",
    "expected_behavioral_control_test_sha256": (
        _ROOT / "tests/test_behavioral_open_axis.py"
    ),
    "expected_sequence_row_sha256": _ROOT / "src/pontius/sequence_form_open_axis.py",
    "expected_cross_payoff_sha256": _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py",
    "expected_setup_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": (
        _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required one-seat preflight input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_cut_round_capacity(
    *,
    warm_step_ms: float,
    initial_row_construction_ms: float,
    source_response_oracle_ms: float,
    response_row_construction_ms: float,
    street_budget_ms: float,
    response_oracle_safety_factor: float,
    row_round_safety_factor: float,
    minimum_final_certificate_reserve_ms: float,
    master_reserve_per_round_ms: float,
    retreat_envelope_reserve_ms: float,
    emission_reserve_ms: float,
) -> dict[str, Any]:
    """Price complete cut rounds and a separate independent final proof."""

    values = (
        warm_step_ms,
        initial_row_construction_ms,
        source_response_oracle_ms,
        response_row_construction_ms,
        street_budget_ms,
        response_oracle_safety_factor,
        row_round_safety_factor,
        minimum_final_certificate_reserve_ms,
        master_reserve_per_round_ms,
        retreat_envelope_reserve_ms,
        emission_reserve_ms,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("one-seat capacity inputs must be finite and nonnegative")
    if street_budget_ms <= 0.0:
        raise ValueError("one-seat capacity requires a positive street budget")
    if response_oracle_safety_factor < 1.0 or row_round_safety_factor < 1.0:
        raise ValueError("one-seat safety factors must be at least one")

    oracle_reserve = max(
        minimum_final_certificate_reserve_ms,
        response_oracle_safety_factor * source_response_oracle_ms,
    )
    row_reserve = row_round_safety_factor * response_row_construction_ms
    round_ms = oracle_reserve + row_reserve + master_reserve_per_round_ms
    fixed_ms = (
        warm_step_ms
        + initial_row_construction_ms
        + oracle_reserve
        + retreat_envelope_reserve_ms
        + emission_reserve_ms
    )
    available = street_budget_ms - fixed_ms
    rounds = 0
    if available >= 0.0:
        rounds = 0 if round_ms == 0.0 else math.floor(available / round_ms)
    return {
        "warm_step_ms": warm_step_ms,
        "initial_row_construction_ms": initial_row_construction_ms,
        "measured_source_response_oracle_ms": source_response_oracle_ms,
        "measured_five_response_row_ms": response_row_construction_ms,
        "response_oracle_and_final_certificate_reserve_ms": oracle_reserve,
        "new_response_rows_reserve_per_round_ms": row_reserve,
        "master_reserve_per_round_ms": master_reserve_per_round_ms,
        "retreat_envelope_reserve_ms": retreat_envelope_reserve_ms,
        "emission_reserve_ms": emission_reserve_ms,
        "fixed_before_cut_rounds_ms": fixed_ms,
        "complete_cut_round_ms": round_ms,
        "available_cut_round_ms": available,
        "conservative_complete_cut_rounds": rounds,
        "one_round_complete_ledger_ms": fixed_ms + round_ms,
        "fits_one_complete_cut_round": rounds >= 1,
        "final_certificate_is_reserved_separately_from_every_cut_oracle": True,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target",
        "acting_player",
        "scope",
        "row_rule",
        "teacher_rule",
        "capacity_rule",
        "promotion_rule",
        "street_budget_ms",
        "response_oracle_safety_factor",
        "row_round_safety_factor",
        "minimum_final_certificate_reserve_ms",
        "master_reserve_per_round_ms",
        "retreat_envelope_reserve_ms",
        "emission_reserve_ms",
        "minimum_complete_cut_rounds_for_promotion",
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
        "conditioning_tolerance",
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
        raise ValueError("one-seat h32 config fields differ from ADR-0244")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"one-seat h32 provenance mismatch: {field}")

    capacity_config = json.loads(_CAPACITY_CONFIG.read_text(encoding="utf-8"))
    expected_target = next(
        row
        for row in capacity_config["targets"]
        if row["target_id"] == "panel_2/balanced/checks_then_bet_seat1"
    )
    exact = {
        "evidence_stage": "preregistered_after_adr0243_before_any_h32_full_axis_row_pass",
        "seed": 20260822,
        "target": expected_target,
        "acting_player": 0,
        "scope": "one_tight_retained_continuation_target_widest_acting_seat_label_free",
        "row_rule": (
            "six_profile_plus_five_source_response_full_behavioral_axis_passes_"
            "without_row_deletion"
        ),
        "teacher_rule": (
            "all_six_gain_rows_projected_on_sixteen_frozen_regret_vertex_blocks_"
            "after_capacity_is_priced"
        ),
        "capacity_rule": (
            "warm_step_plus_initial_rows_plus_complete_oracle_rows_master_rounds_"
            "plus_separate_full_oracle_final_certificate_and_emission"
        ),
        "promotion_rule": (
            "identity_and_residency_pass_with_at_least_one_conservative_complete_"
            "cut_round_authorizes_label_free_master_prototype"
        ),
        "street_budget_ms": 15000.0,
        "response_oracle_safety_factor": 1.25,
        "row_round_safety_factor": 1.25,
        "minimum_final_certificate_reserve_ms": 1250.0,
        "master_reserve_per_round_ms": 500.0,
        "retreat_envelope_reserve_ms": 50.0,
        "emission_reserve_ms": 1000.0,
        "minimum_complete_cut_rounds_for_promotion": 1,
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
        "conditioning_tolerance": 1e-12,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "strategy_label_policy": (
            "zero_quality_values_zero_certificates_zero_strategy_labels_"
            "immutable_blueprint_emission"
        ),
    }
    for field, value in exact.items():
        if config[field] != value:
            raise ValueError(f"one-seat h32 field differs from ADR-0244: {field}")
    gates = {
        "expected_acting_public_nodes": 16,
        "expected_acting_information_sets": 512,
        "expected_entries_per_row": 1024,
        "expected_profile_passes": 6,
        "expected_fixed_response_passes": 5,
        "expected_gain_rows": 6,
        "expected_teacher_directions": 16,
        "expected_teacher_rows": 96,
        "maximum_profile_slope_error": 2e-11,
        "maximum_response_slope_error": 2e-11,
        "maximum_gain_slope_error": 2e-11,
        "maximum_source_row_error": 2e-11,
        "maximum_source_zero_sum_residual": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_cold_setup_ms": 120000.0,
        "maximum_warm_step_ms": 60000.0,
        "maximum_row_construction_ms": 60000.0,
        "maximum_teacher_ms": 120000.0,
        "maximum_gain_row_persistent_bytes": 1000000,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_path_single_visit": True,
        "require_exact_response_axis_coverage": True,
        "require_blueprint_emission": True,
        "require_new_strategy_labels_zero": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("one-seat h32 gates differ from ADR-0244")
    return {**config, "target": dict(config["target"]), "gates": gates}


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def _response_signature(actions: Mapping[str, Any]) -> str:
    payload = "\n".join(f"{key}|{actions[key]}" for key in sorted(actions))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _row_signature(row: SequenceFormAffineRow) -> str:
    return hashlib.sha256(row.flattened().tobytes(order="C")).hexdigest()


def _pass_telemetry(
    *,
    kind: str,
    payoff_player: int,
    wall_ms: float,
    result: Any,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "payoff_player": payoff_player,
        "wall_ms": wall_ms,
        "terminal_contraction_ms": result.terminal_contraction_ms,
        "reverse_adjoint_ms": result.reverse_adjoint_ms,
        "terminal_contractions": result.terminal_contractions,
        "terminal_sparse_batches": result.terminal_sparse_batches,
        "maximum_middle_rank": result.maximum_terminal_middle_rank,
        "maximum_peak_numeric_bytes": result.maximum_terminal_peak_numeric_bytes,
        "maximum_gpu_pool_total_bytes": result.maximum_gpu_pool_total_bytes,
        "work": _work_ledger((result.resident_work,)),
    }


def _run_pass(
    *,
    objects: Mapping[str, Any],
    probabilities: Any,
    acting_player: int,
    payoff_player: int,
    source_value: float,
    kind: str,
    cp: Any,
    maximum_feature_width_per_batch: int,
) -> tuple[SequenceFormAffineRow, dict[str, Any], Any]:
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    result = evaluate_device_fold_cross_payoff_leaf_adjoint(
        objects["layout"],
        objects["workspace"],
        objects["sparse"],
        probabilities,
        objects["automata"][payoff_player],
        acting_player=acting_player,
        payoff_player=payoff_player,
        belief_cache=objects["context"].belief_cache,
        automaton_cache=objects["shared"].automaton_caches[payoff_player],
        cupy_sparse=objects["gpu"],
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        record_to_hand_backend="gpu_cupy",
    )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    row = behavioral_open_axis_payoff_row(
        objects["layout"],
        objects["context"].response_caches[0].source_probabilities,
        result,
        acting_player=acting_player,
        source_value=source_value,
    )
    return row, _pass_telemetry(
        kind=kind,
        payoff_player=payoff_player,
        wall_ms=wall_ms,
        result=result,
    ), result


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    cp.cuda.runtime.deviceSynchronize()
    setup_started = time.perf_counter()
    objects = _setup(parsed, source_parent, spec)
    cp.cuda.runtime.deviceSynchronize()
    cold_setup_ms = (time.perf_counter() - setup_started) * 1000.0
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    acting_player = int(parsed["acting_player"])
    topology = compiled_layout_path_single_visit_report(layout)

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
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
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
        raise AssertionError("one-seat h32 warm step emitted no work ledger")
    warm_works = tuple(row.resident_work for row in solver.last_step_work.traversers)
    warm_work = {
        "wall_ms": warm_step_ms,
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(warm_works),
    }
    memory_rows.append({"stage": "warm_step", **_memory_snapshot(cp)})

    source_probabilities = context.response_caches[0].source_probabilities
    profile_rows: dict[int, SequenceFormAffineRow] = {}
    response_rows: dict[int, SequenceFormAffineRow] = {}
    pass_rows = []
    response_signatures = []
    exact_axis_coverage = True
    cp.cuda.runtime.deviceSynchronize()
    construction_started = time.perf_counter()
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
        pass_rows.append(telemetry)
        memory_rows.append(
            {"stage": f"profile_{payoff_player}", **_memory_snapshot(cp)}
        )

    for payoff_player in range(layout.num_players):
        if payoff_player == acting_player:
            continue
        cache = context.response_caches[payoff_player]
        actions = cache.source_evaluation.best_response_actions
        response_signatures.append(_response_signature(actions))
        response_probabilities = splice_fixed_response_probability_tape_for_axes(
            layout,
            source_probabilities,
            actions,
            responding_player=payoff_player,
            hands_by_player=belief.hands_by_player,
        )
        exact_axis_coverage = exact_axis_coverage and all(
            values is not None
            and values.shape
            == (
                len(belief.hands_by_player[layout.nodes[node_index].player]),
                len(layout.nodes[node_index].actions),
            )
            for node_index, values in enumerate(response_probabilities)
            if layout.nodes[node_index].player >= 0
        )
        row, telemetry, _ = _run_pass(
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
        response_rows[payoff_player] = row
        pass_rows.append(telemetry)
        memory_rows.append(
            {"stage": f"response_{payoff_player}", **_memory_snapshot(cp)}
        )
    cp.cuda.runtime.deviceSynchronize()
    row_construction_ms = (time.perf_counter() - construction_started) * 1000.0

    gain_rows = []
    source_row_errors = []
    for payoff_player in range(layout.num_players):
        cache = context.response_caches[payoff_player]
        profile = profile_rows[payoff_player]
        source_row_errors.append(
            abs(profile.value(source_probabilities) - cache.source_evaluation.profile_utility)
        )
        if payoff_player == acting_player:
            gain = constant_minus_affine_row(
                cache.source_evaluation.best_response_value,
                profile,
            )
        else:
            response = response_rows[payoff_player]
            source_row_errors.append(
                abs(
                    response.value(source_probabilities)
                    - cache.source_evaluation.best_response_value
                )
            )
            gain = subtract_affine_rows(response, profile)
        source_row_errors.append(
            abs(
                gain.value(source_probabilities)
                - (
                    cache.source_evaluation.best_response_value
                    - cache.source_evaluation.profile_utility
                )
            )
        )
        gain_rows.append(gain)

    conditioning = affine_row_conditioning(
        tuple(gain_rows),
        tolerance=float(parsed["conditioning_tolerance"]),
    )
    response_pass_ms = math.fsum(
        row["wall_ms"] for row in pass_rows if row["kind"] == "fixed_response"
    )
    capacity = derive_cut_round_capacity(
        warm_step_ms=warm_step_ms,
        initial_row_construction_ms=row_construction_ms,
        source_response_oracle_ms=float(context.response_compile_ms),
        response_row_construction_ms=response_pass_ms,
        street_budget_ms=float(parsed["street_budget_ms"]),
        response_oracle_safety_factor=float(parsed["response_oracle_safety_factor"]),
        row_round_safety_factor=float(parsed["row_round_safety_factor"]),
        minimum_final_certificate_reserve_ms=float(
            parsed["minimum_final_certificate_reserve_ms"]
        ),
        master_reserve_per_round_ms=float(parsed["master_reserve_per_round_ms"]),
        retreat_envelope_reserve_ms=float(parsed["retreat_envelope_reserve_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
    )

    soft = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    all_blocks = _ordered_blocks(layout, blueprint, soft)
    blocks = tuple(
        block for block in all_blocks if int(block["acting_seat"]) == acting_player
    )
    maximum_profile_error = 0.0
    maximum_response_error = 0.0
    maximum_gain_error = 0.0
    teacher_rows = 0
    cp.cuda.runtime.deviceSynchronize()
    teacher_started = time.perf_counter()
    for block in blocks:
        endpoint_policy = build_regret_vertex_candidate(
            blueprint,
            regret_deltas,
            tuple(block["information_keys"]),
        )
        endpoint = compile_policy_probability_tape(
            layout,
            belief.hands_by_player,
            endpoint_policy,
        )
        for payoff_player in range(layout.num_players):
            profile_slope = (
                profile_rows[payoff_player].value(endpoint)
                - profile_rows[payoff_player].value(source_probabilities)
            )
            if payoff_player == acting_player:
                response_slope = 0.0
                teacher = evaluate_selector_stable_affine_leaf_adjoint_seat(
                    context.response_caches[payoff_player],
                    endpoint,
                    acting_player=acting_player,
                    selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                    maximum_feature_width_per_batch=int(
                        parsed["maximum_feature_width_per_batch"]
                    ),
                )
            else:
                response_slope = (
                    response_rows[payoff_player].value(endpoint)
                    - response_rows[payoff_player].value(source_probabilities)
                )
                teacher = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                    context.response_caches[payoff_player],
                    endpoint,
                    acting_player=acting_player,
                    selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                    maximum_feature_width_per_batch=int(
                        parsed["maximum_feature_width_per_batch"]
                    ),
                    belief_cache=context.belief_cache,
                    automaton_cache=shared.automaton_caches[payoff_player],
                    cupy_sparse=objects["gpu"],
                    record_to_hand_backend="gpu_cupy",
                ).semantic
            gain_slope = response_slope - profile_slope
            maximum_profile_error = max(
                maximum_profile_error,
                abs(profile_slope - float(teacher.profile_utility_slope)),
            )
            maximum_response_error = max(
                maximum_response_error,
                abs(response_slope - float(teacher.best_response_value_slope)),
            )
            maximum_gain_error = max(
                maximum_gain_error,
                abs(gain_slope - float(teacher.deviation_gap_slope)),
            )
            teacher_rows += 1
    cp.cuda.runtime.deviceSynchronize()
    teacher_ms = (time.perf_counter() - teacher_started) * 1000.0
    memory_rows.append({"stage": "teacher_complete", **_memory_snapshot(cp)})

    acting_nodes = tuple(
        node_index
        for node_index, node in enumerate(layout.nodes)
        if node.player == acting_player
    )
    entries_per_row = sum(
        node.values.size for node in gain_rows[0].nodes
    )
    source_utility_sum = math.fsum(
        float(cache.source_evaluation.profile_utility)
        for cache in context.response_caches
    )
    result = {
        "target_id": spec["target_id"],
        "target_belief_sha256": spec["target_belief_sha256"],
        "acting_player": acting_player,
        "path_single_visit": topology.passed,
        "repeated_player": topology.repeated_player,
        "acting_public_nodes": len(acting_nodes),
        "acting_information_sets": sum(
            len(belief.hands_by_player[acting_player]) for _ in acting_nodes
        ),
        "entries_per_row": entries_per_row,
        "profile_passes": sum(row["kind"] == "profile" for row in pass_rows),
        "fixed_response_passes": sum(
            row["kind"] == "fixed_response" for row in pass_rows
        ),
        "gain_rows": len(gain_rows),
        "gain_row_persistent_bytes": sum(
            row.numeric_bytes + np.dtype(np.float64).itemsize for row in gain_rows
        ),
        "gain_row_sha256": [_row_signature(row) for row in gain_rows],
        "exact_response_signatures": response_signatures,
        "exact_response_axis_coverage": exact_axis_coverage,
        "maximum_source_row_error": max(source_row_errors),
        "source_zero_sum_residual": abs(source_utility_sum),
        "maximum_profile_slope_error": maximum_profile_error,
        "maximum_response_slope_error": maximum_response_error,
        "maximum_gain_slope_error": maximum_gain_error,
        "conditioning": asdict(conditioning),
        "cold_setup_ms": cold_setup_ms,
        "belief_compile_ms": context.belief_compile_ms,
        "source_response_oracle_ms": context.response_compile_ms,
        "warm_start_distance": warm_distance,
        "warm_step": warm_work,
        "row_construction_ms": row_construction_ms,
        "pass_rows": pass_rows,
        "teacher_directions": len(blocks),
        "teacher_rows": teacher_rows,
        "teacher_ms": teacher_ms,
        "capacity_before_teacher": capacity,
        "memory_rows": memory_rows,
        "resident_numeric_bytes": {
            "shared_device": shared_device_numeric_bytes(shared, (context,)),
            "unique_response_host": unique_response_numeric_bytes((context,)),
            "solver": solver.memory_summary(),
        },
        "maximum_middle_rank": max(row["maximum_middle_rank"] for row in pass_rows),
        "maximum_peak_numeric_bytes": max(
            row["maximum_peak_numeric_bytes"] for row in pass_rows
        ),
        "maximum_gpu_pool_total_bytes": max(
            max(row["maximum_gpu_pool_total_bytes"] for row in pass_rows),
            max(row["gpu_pool_total_bytes"] for row in memory_rows),
        ),
        "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(objects["state"])
        == objects["state"]["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"],
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"])
        == objects["state"]["average_policy_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "quality_values_serialized": 0,
        "certificates_executed": 0,
        "strategy_labels_generated": 0,
        "emitted_policy_sha256": policy_digest(blueprint),
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_one_seat_open_axis_preflight(
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
    capacity_parent = load_artifact(
        _CAPACITY,
        expected_sha256=parsed["expected_capacity_result_sha256"],
        require_passed=True,
    ).payload
    target = _run_target(parsed, source, parsed["target"], cp)
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(row) for row in (source, capacity_parent))
        == gate["require_parents_passed"],
        "target_identity": bool(
            target["source_checkpoint_identity"] and target["target_identity"]
        )
        == gate["require_target_identity"],
        "blueprint_identity": bool(target["blueprint_identity"])
        == gate["require_blueprint_identity"],
        "path_single_visit": target["path_single_visit"]
        == gate["require_path_single_visit"],
        "acting_node_count": target["acting_public_nodes"]
        == gate["expected_acting_public_nodes"],
        "acting_information_set_count": target["acting_information_sets"]
        == gate["expected_acting_information_sets"],
        "row_width": target["entries_per_row"] == gate["expected_entries_per_row"],
        "profile_pass_count": target["profile_passes"]
        == gate["expected_profile_passes"],
        "fixed_response_pass_count": target["fixed_response_passes"]
        == gate["expected_fixed_response_passes"],
        "gain_row_count": target["gain_rows"] == gate["expected_gain_rows"],
        "teacher_direction_count": target["teacher_directions"]
        == gate["expected_teacher_directions"],
        "teacher_row_count": target["teacher_rows"] == gate["expected_teacher_rows"],
        "profile_slope_identity": target["maximum_profile_slope_error"]
        <= gate["maximum_profile_slope_error"],
        "response_slope_identity": target["maximum_response_slope_error"]
        <= gate["maximum_response_slope_error"],
        "gain_slope_identity": target["maximum_gain_slope_error"]
        <= gate["maximum_gain_slope_error"],
        "source_row_identity": target["maximum_source_row_error"]
        <= gate["maximum_source_row_error"],
        "source_zero_sum": target["source_zero_sum_residual"]
        <= gate["maximum_source_zero_sum_residual"],
        "warm_start_identity": target["warm_start_distance"]["maximum_probability_error"]
        <= gate["maximum_warm_start_probability_error"]
        and target["warm_start_distance"]["mean_total_variation"]
        <= gate["maximum_warm_start_mean_total_variation"],
        "external_axis_coverage": target["exact_response_axis_coverage"]
        == gate["require_exact_response_axis_coverage"],
        "cold_setup_time": target["cold_setup_ms"] <= gate["maximum_cold_setup_ms"],
        "warm_step_time": target["warm_step"]["wall_ms"]
        <= gate["maximum_warm_step_ms"],
        "row_construction_time": target["row_construction_ms"]
        <= gate["maximum_row_construction_ms"],
        "teacher_time": target["teacher_ms"] <= gate["maximum_teacher_ms"],
        "row_bytes": target["gain_row_persistent_bytes"]
        <= gate["maximum_gain_row_persistent_bytes"],
        "gpu_pool": target["maximum_gpu_pool_total_bytes"]
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": target["minimum_gpu_free_bytes"]
        >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": (
            target["emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
        )
        == gate["require_blueprint_emission"],
        "new_strategy_labels_zero": (target["strategy_labels_generated"] == 0)
        == gate["require_new_strategy_labels_zero"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    rounds = target["capacity_before_teacher"]["conservative_complete_cut_rounds"]
    promote = bool(
        gate_result["passed"]
        and rounds >= int(parsed["minimum_complete_cut_rounds_for_promotion"])
    )
    result = {
        "schema_version": 1,
        "status": "h32_one_seat_open_axis_preflight_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": 1,
            "acting_seats": 1,
            "warm_steps": 1,
            "profile_passes": target["profile_passes"],
            "fixed_response_passes": target["fixed_response_passes"],
            "teacher_rows": target["teacher_rows"],
            "quality_values_serialized": 0,
            "certificates": 0,
            "strategy_labels": 0,
        },
        "target": target,
        "aggregate": {
            "cold_setup_ms": target["cold_setup_ms"],
            "warm_step_ms": target["warm_step"]["wall_ms"],
            "initial_row_construction_ms": target["row_construction_ms"],
            "source_response_oracle_ms": target["source_response_oracle_ms"],
            "gain_row_persistent_bytes": target["gain_row_persistent_bytes"],
            "maximum_middle_rank": target["maximum_middle_rank"],
            "maximum_gpu_pool_total_bytes": target["maximum_gpu_pool_total_bytes"],
            "minimum_gpu_free_bytes": target["minimum_gpu_free_bytes"],
            "conservative_complete_cut_rounds": rounds,
            "one_round_complete_ledger_ms": target["capacity_before_teacher"][
                "one_round_complete_ledger_ms"
            ],
            "promote_label_free_master_prototype": promote,
        },
        **gate_result,
        "decision": (
            "authorize_label_free_h32_one_seat_master_prototype"
            if promote
            else "retain_open_axis_rows_off_clock_and_reject_live_master_prototype"
            if gate_result["passed"]
            else "reject_h32_one_seat_open_axis_preflight"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_quality_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "This is one label-free target and one widest acting seat, not a "
                "strategy-quality trial."
            ),
            (
                "The source oracle prices future full exact oracles; cut count and "
                "master latency remain unmeasured."
            ),
            (
                "The projection teacher uses frozen one-node regret vertices and "
                "opens no value or admission labels."
            ),
            (
                "A pass authorizes only a label-free master prototype; the exact "
                "verifier remains emission authority."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_one_seat_open_axis_preflight(args.config, args.output)
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
