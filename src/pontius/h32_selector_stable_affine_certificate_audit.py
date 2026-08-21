"""Retained h32 differential audit for selector-stable affine certificates."""

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
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import (
    geometric_halving_scales,
    interpolate_policy_atoms,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_causal_direction_screen import (
    _FROZEN_TARGETS,
    build_fresh_seat2_target,
)
from .h32_fresh_public_block_value_audit import (
    build_public_node_blocks,
    information_key_public_coordinates,
)
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _memory_snapshot, _safe_ratio
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .incremental_leaf_adjoint_response import (
    evaluate_incremental_leaf_adjoint_seat,
    verify_incremental_leaf_adjoint_candidate,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)
from .selector_stable_affine_response import (
    SelectorStableAffineSeatResult,
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
    selector_stable_affine_values_at_scale,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-selector-stable-affine-certificate-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-fresh-causal-direction-screen-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-fresh-causal-direction-screen-v1.json"
_PARENT_ADR = _ROOT / "docs/decisions/ADR-0186-fresh-vertices-replicate-generator-weakness-but-no-free-selector-transfers.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_selector_stable_affine_certificate_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_parent_config_sha256": _PARENT_CONFIG,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": _ROOT / "src/pontius/h32_fresh_causal_direction_screen.py",
    "expected_public_block_builder_sha256": _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py",
    "expected_direction_builder_sha256": _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py",
    "expected_shared_context_sha256": _ROOT / "src/pontius/shared_resident_response_context.py",
    "expected_incremental_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_affine_verifier_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_resident_cfr_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py",
    "expected_atom_manifest_sha256": _ROOT / "src/pontius/h32_atomic_response_preflight.py",
    "expected_interpolation_sha256": _ROOT / "src/pontius/delta_certificate_contract.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_affine_unit_test_sha256": _ROOT / "tests/test_incremental_leaf_adjoint_response.py",
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required affine-certificate input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_selector_stable_affine_certificate_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0187's complete retained-policy differential contract."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "targets",
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
        "search_steps_per_target",
        "direction_family",
        "acting_seats",
        "affine_scope",
        "source_selector_rule",
        "selector_margin_allowance",
        "envelope_numerical_allowance",
        "safety_fraction",
        "scale_grid",
        "numerical_floor",
        "fixed_validation_scale_index",
        "seat_order",
        "acceptance_guard_normalized",
        "maximum_feature_width_per_batch",
        "measurement_context",
        "street_budget_ms",
        "emission_reserve_ms",
        "emitted_policy",
        "maximum_warm_start_probability_error",
        "maximum_warm_start_mean_total_variation",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "cuda_dll_environment_variable",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("selector-stable affine fields differ from ADR-0187")
    frozen = {
        "evidence_stage": "retained_policy_engineering_replay_after_adr0186_before_any_fresh_affine_target_label",
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
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
        "direction_family": "regret_vertex",
        "acting_seats": [0, 1, 2, 3, 4, 5],
        "affine_scope": "one_acting_seat_one_exact_public_node_source_to_scale_one_endpoint",
        "source_selector_rule": "immutable_blueprint_first_action_argmax_tape_until_first_conservative_tie",
        "selector_margin_allowance": 2e-11,
        "envelope_numerical_allowance": 2e-11,
        "safety_fraction": 0.5,
        "scale_grid": "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor",
        "numerical_floor": 1e-10,
        "fixed_validation_scale_index": 16,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "measurement_context": "off_clock_retained_policy_certificate_differential_not_a_live_scheduler",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "emitted_policy": "immutable_blueprint_engineering_replay_only",
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("selector-stable affine workload differs from ADR-0187")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"selector-stable affine source mismatch: {field}")
    gates = {
        "expected_target_rows": 6,
        "expected_search_steps": 6,
        "expected_public_blocks": 36,
        "expected_affine_seat_rows": 216,
        "expected_fixed_direct_validations": 36,
        "maximum_source_quality_error": 2e-11,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_direct_utility_error": 1e-9,
        "maximum_direct_best_response_error": 1e-9,
        "maximum_direct_deviation_gain_error": 1e-9,
        "maximum_search_step_ms": 60000.0,
        "maximum_affine_sweep_ms": 60000.0,
        "maximum_direct_validation_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_parent_direction_identity": True,
        "require_nonempty_coherent_blocks": True,
        "require_affine_scope_identity": True,
        "require_fixed_validation_inside_selector_interval": True,
        "require_fixed_validation_zero_response_flips": True,
        "require_selected_direct_completion": True,
        "require_selected_zero_response_flips": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("selector-stable affine gates differ from ADR-0187")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "acting_seats": tuple(config["acting_seats"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def _source_quality(context: Any, *, payoff_span: float) -> dict[str, Any]:
    rows = tuple(cache.source_evaluation for cache in context.response_caches)
    utilities = tuple(float(row.profile_utility) for row in rows)
    responses = tuple(float(row.best_response_value) for row in rows)
    gains = tuple(float(row.deviation_gain) for row in rows)
    nash_conv = math.fsum(gains)
    return {
        "utilities": utilities,
        "best_response_values": responses,
        "deviation_gains": gains,
        "nash_conv": nash_conv,
        "normalized_nash_conv": nash_conv / payoff_span,
        "zero_sum_residual": abs(math.fsum(utilities)),
    }


def _quality_error(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return max(
        abs(float(left_value) - float(right_value))
        for field in ("utilities", "best_response_values", "deviation_gains")
        for left_value, right_value in zip(left[field], right[field], strict=True)
    )


def _direct_rows(
    *,
    layout: Any,
    policy: dict[str, dict[str, float]],
    hands_by_player: tuple[tuple[Any, ...], ...],
    context: Any,
    shared: Any,
    gpu: Any,
    maximum_feature_width_per_batch: int,
) -> tuple[tuple[Any, ...], float]:
    started = time.perf_counter()
    probabilities = compile_policy_probability_tape(layout, hands_by_player, policy)
    rows = tuple(
        evaluate_incremental_leaf_adjoint_seat(
            cache,
            probabilities,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[seat],
            cupy_sparse=gpu,
        )
        for seat, cache in enumerate(context.response_caches)
    )
    return rows, (time.perf_counter() - started) * 1000.0


def affine_direct_errors(
    affine_rows: tuple[SelectorStableAffineSeatResult, ...],
    direct_rows: tuple[Any, ...],
    *,
    scale: float,
) -> dict[str, float]:
    """Compare one affine prediction with independent exact seat reads."""

    predicted = tuple(
        selector_stable_affine_values_at_scale(row, scale) for row in affine_rows
    )
    return {
        "maximum_utility_error": max(
            abs(values[0] - direct.profile_utility)
            for values, direct in zip(predicted, direct_rows, strict=True)
        ),
        "maximum_best_response_error": max(
            abs(values[1] - direct.best_response_value)
            for values, direct in zip(predicted, direct_rows, strict=True)
        ),
        "maximum_deviation_gain_error": max(
            abs(values[2] - direct.deviation_gain)
            for values, direct in zip(predicted, direct_rows, strict=True)
        ),
    }


def _fixed_validation_scale(
    scales: tuple[float, ...],
    *,
    preferred_index: int,
    selector_limit: float,
) -> float | None:
    target = min(scales[preferred_index], selector_limit * 0.5)
    return next((scale for scale in scales if scale <= target), None)


def _run_target(
    parsed: dict[str, Any],
    source_parent: dict[str, Any],
    parent: dict[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["hands_per_player"],
        family=family,
    )
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == source_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat2_target(
        source,
        board=board,
        target_seat=2,
    )
    target_digest = _belief_digest(belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )
    parent_target = next(
        row for row in parent["target_rows"] if row["target"] == target_spec["target"]
    )

    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=parsed["query_chunk_records"],
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
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    blueprint_quality = _source_quality(context, payoff_span=parsed["stack"])
    source_quality_error = _quality_error(
        blueprint_quality, parent_target["blueprint_quality"]
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        parsed["solver_variant"],
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )
    warm_mass = parsed["warm_regret_mass_payoff_fraction"] * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    search_started = time.perf_counter()
    solver.step()
    search_ms = (time.perf_counter() - search_started) * 1000.0
    memory_rows.append(_memory_snapshot(cp))

    construction_started = time.perf_counter()
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    anchors = select_one_atom_per_acting_seat(
        layout, belief.hands_by_player, blueprint, soft_candidate
    )
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    payloads = []
    parent_blocks = {
        (int(row["acting_seat"]), str(row["public_history"])): row
        for row in parent_target["block_rows"]
    }
    for block in blocks:
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        endpoint_probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        parent_block = parent_blocks[(int(block["acting_seat"]), block["public_history"])]
        parent_direction = next(
            row
            for row in parent_block["direction_rows"]
            if row["direction_family"] == "regret_vertex"
        )
        payloads.append(
            (block, keys, endpoint, endpoint_probabilities, parent_block, parent_direction)
        )
    construction_ms = (time.perf_counter() - construction_started) * 1000.0

    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    blueprint_gains = tuple(blueprint_quality["deviation_gains"])
    blueprint_nash = float(blueprint_quality["nash_conv"])
    block_rows = []
    for (
        block,
        keys,
        endpoint,
        endpoint_probabilities,
        parent_block,
        parent_direction,
    ) in payloads:
        seat = int(block["acting_seat"])
        affine_started = time.perf_counter()
        affine_rows = tuple(
            evaluate_selector_stable_affine_leaf_adjoint_seat(
                cache,
                endpoint_probabilities,
                acting_player=seat,
                selector_margin_allowance=parsed["selector_margin_allowance"],
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
            )
            for target_player, cache in enumerate(context.response_caches)
        )
        affine_sweep_ms = (time.perf_counter() - affine_started) * 1000.0
        memory_rows.append(_memory_snapshot(cp))
        envelope = certify_selector_stable_affine_envelope(
            affine_rows,
            blueprint_deviation_gains=blueprint_gains,
            blueprint_nash_conv=blueprint_nash,
            raw_guard=raw_guard,
            scale_grid=scales,
            safety_fraction=parsed["safety_fraction"],
            numerical_allowance=parsed["envelope_numerical_allowance"],
        )
        selector_limit = min(row.selector_stable_scale for row in affine_rows)
        fixed_scale = _fixed_validation_scale(
            scales,
            preferred_index=parsed["fixed_validation_scale_index"],
            selector_limit=selector_limit,
        )
        fixed_validation = None
        if fixed_scale is not None:
            fixed_policy = interpolate_policy_atoms(
                blueprint, endpoint, keys, scale=fixed_scale
            )
            direct_rows, direct_ms = _direct_rows(
                layout=layout,
                policy=fixed_policy,
                hands_by_player=belief.hands_by_player,
                context=context,
                shared=shared,
                gpu=gpu,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            fixed_validation = {
                "scale": fixed_scale,
                "strictly_inside_selector_interval": fixed_scale < selector_limit,
                "direct_wall_ms": direct_ms,
                "direct_response_action_flips": sum(
                    row.response_action_flips for row in direct_rows
                ),
                "errors": affine_direct_errors(
                    affine_rows, direct_rows, scale=fixed_scale
                ),
            }
            memory_rows.append(_memory_snapshot(cp))

        selected_validation = None
        selected_value = 0.0
        if envelope.complete:
            if envelope.selected_scale is None:
                raise AssertionError("complete affine envelope has no selected scale")
            selected_policy = interpolate_policy_atoms(
                blueprint, endpoint, keys, scale=envelope.selected_scale
            )
            direct = verify_incremental_leaf_adjoint_candidate(
                candidate_id=f"seat{seat}_affine_selected",
                layout=layout,
                policy=selected_policy,
                hands_by_player=belief.hands_by_player,
                response_caches=context.response_caches,
                blueprint_deviation_gains=blueprint_gains,
                best_complete_nash_conv=blueprint_nash,
                payoff_span=parsed["stack"],
                raw_guard=raw_guard,
                seat_order=parsed["seat_order"],
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
                belief_cache=context.belief_cache,
                automaton_caches=shared.automaton_caches,
                cupy_sparse=gpu,
            )
            if direct["quality"] is not None:
                selected_value = max(
                    0.0, blueprint_nash - float(direct["quality"]["nash_conv"])
                )
            selected_validation = {
                "policy_sha256": policy_digest(selected_policy),
                "direct": direct,
                "errors": (
                    None
                    if direct["quality"] is None
                    else {
                        "maximum_utility_error": max(
                            abs(left - right)
                            for left, right in zip(
                                envelope.predicted_utilities,
                                direct["quality"]["utilities"],
                                strict=True,
                            )
                        ),
                        "maximum_best_response_error": max(
                            abs(left - right)
                            for left, right in zip(
                                envelope.predicted_best_response_values,
                                direct["quality"]["best_response_values"],
                                strict=True,
                            )
                        ),
                        "maximum_deviation_gain_error": max(
                            abs(left - right)
                            for left, right in zip(
                                envelope.predicted_deviation_gains,
                                direct["quality"]["deviation_gains"],
                                strict=True,
                            )
                        ),
                    }
                ),
                "direct_positive_certified_value": selected_value,
            }
            memory_rows.append(_memory_snapshot(cp))

        affine_intercept_error = max(
            abs(row.deviation_gain_intercept - blueprint_gains[target_player])
            for target_player, row in enumerate(affine_rows)
        )
        parent_direction_identity = (
            policy_digest(endpoint) == parent_direction["direction_policy_sha256"]
            and tuple(keys) == tuple(parent_block["information_keys"])
        )
        block_rows.append(
            {
                "acting_seat": seat,
                "public_history": block["public_history"],
                "information_keys": list(keys),
                "information_set_count": len(keys),
                "direction_policy_sha256": policy_digest(endpoint),
                "parent_direction_identity": parent_direction_identity,
                "affine_scope_identity": all(
                    row.acting_player == seat
                    and row.changed_public_node
                    == affine_rows[0].changed_public_node
                    and row.changed_public_nodes == 1
                    for row in affine_rows
                ),
                "affine_sweep_ms": affine_sweep_ms,
                "affine_intercept_error": affine_intercept_error,
                "affine_rows": [asdict(row) for row in affine_rows],
                "envelope": asdict(envelope),
                "fixed_validation": fixed_validation,
                "selected_validation": selected_validation,
                "selected_positive_certified_value": selected_value,
                "parent_bounded_oracle_positive_certified_value": float(
                    parent_block["bounded_oracle_positive_certified_value"]
                ),
                "selected_capture_fraction": _safe_ratio(
                    selected_value,
                    float(parent_block["bounded_oracle_positive_certified_value"]),
                ),
            }
        )

    seat0 = next(row for row in block_rows if row["acting_seat"] == 0)
    street_ledger_ms = (
        search_ms
        + construction_ms
        + float(seat0["affine_sweep_ms"])
        + parsed["emission_reserve_ms"]
    )
    result = {
        "target": target_spec["target"],
        "board_id": target_spec["board_id"],
        "board": target_spec["board"],
        "range_family": family,
        "target_shift": target_spec["target_shift"],
        "source_belief_sha256": source_digest,
        "target_belief_sha256": target_digest,
        "target_descriptor_sha256": descriptor_digest,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "blueprint_quality": blueprint_quality,
        "source_quality_error": source_quality_error,
        "warm_start_distance": warm_start_distance,
        "search_step_ms": search_ms,
        "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "soft_candidate_policy_sha256": policy_digest(soft_candidate),
        "parent_soft_candidate_policy_sha256": parent_target[
            "soft_candidate_policy_sha256"
        ],
        "post_search_all_block_construction_ms": construction_ms,
        "block_rows": block_rows,
        "seat0_descriptive_street_ledger_ms": street_ledger_ms,
        "seat0_descriptive_street_ledger_fit": street_ledger_ms
        <= parsed["street_budget_ms"],
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_selector_stable_affine_certificate_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen retained-policy affine differential audit."""

    started = time.perf_counter()
    parsed = parse_h32_selector_stable_affine_certificate_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("selector-stable affine execution requires clean Git state")
    if not source_parent["passed"] or not parent["gates"]["passed"]:
        raise ValueError("selector-stable affine parent did not pass")

    targets = []
    for target_spec in parsed["targets"]:
        print(f"selector-stable affine audit: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, parent, target_spec, cp))

    blocks = [row for target in targets for row in target["block_rows"]]
    affine_rows = [row for block in blocks for row in block["affine_rows"]]
    fixed = [block["fixed_validation"] for block in blocks if block["fixed_validation"]]
    selected = [
        block["selected_validation"]
        for block in blocks
        if block["selected_validation"] is not None
    ]
    selected_errors = [row["errors"] for row in selected if row["errors"] is not None]
    direct_errors = [row["errors"] for row in fixed] + selected_errors
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    finite_values = [
        total_seconds,
        *(target["search_step_ms"] for target in targets),
        *(block["affine_sweep_ms"] for block in blocks),
        *(value for row in direct_errors for value in row.values()),
        *(row["direct_wall_ms"] for row in fixed),
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "parent_passed": (
            source_parent["passed"] and parent["gates"]["passed"]
        )
        == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(targets) == gates_config["expected_search_steps"],
        "public_blocks": len(blocks) == gates_config["expected_public_blocks"],
        "affine_seat_rows": len(affine_rows)
        == gates_config["expected_affine_seat_rows"],
        "fixed_direct_validations": len(fixed)
        == gates_config["expected_fixed_direct_validations"],
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in targets)
        == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            target["warm_start_distance"]["maximum_probability_error"]
            <= parsed["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= parsed["maximum_warm_start_mean_total_variation"]
            and target["soft_candidate_policy_sha256"]
            == target["parent_soft_candidate_policy_sha256"]
            for target in targets
        )
        == gates_config["require_numerical_warm_start_identity"],
        "source_quality": max(target["source_quality_error"] for target in targets)
        <= gates_config["maximum_source_quality_error"],
        "parent_direction_identity": all(
            block["parent_direction_identity"] for block in blocks
        )
        == gates_config["require_parent_direction_identity"],
        "nonempty_coherent_blocks": all(
            block["information_set_count"] > 0
            and all(
                information_key_public_coordinates(key)
                == (block["acting_seat"], block["public_history"])
                for key in block["information_keys"]
            )
            for block in blocks
        )
        == gates_config["require_nonempty_coherent_blocks"],
        "affine_scope_identity": all(block["affine_scope_identity"] for block in blocks)
        == gates_config["require_affine_scope_identity"],
        "affine_intercepts": max(block["affine_intercept_error"] for block in blocks)
        <= gates_config["maximum_affine_intercept_error"],
        "direct_utility": max(row["maximum_utility_error"] for row in direct_errors)
        <= gates_config["maximum_direct_utility_error"],
        "direct_best_response": max(
            row["maximum_best_response_error"] for row in direct_errors
        )
        <= gates_config["maximum_direct_best_response_error"],
        "direct_deviation_gain": max(
            row["maximum_deviation_gain_error"] for row in direct_errors
        )
        <= gates_config["maximum_direct_deviation_gain_error"],
        "fixed_inside_selector_interval": all(
            row["strictly_inside_selector_interval"] for row in fixed
        )
        == gates_config["require_fixed_validation_inside_selector_interval"],
        "fixed_zero_response_flips": all(
            row["direct_response_action_flips"] == 0 for row in fixed
        )
        == gates_config["require_fixed_validation_zero_response_flips"],
        "selected_direct_completion": all(
            row["direct"]["complete"] and row["direct"]["quality"] is not None
            for row in selected
        )
        == gates_config["require_selected_direct_completion"],
        "selected_zero_response_flips": all(
            row["direct"]["response_action_flips"] == 0 for row in selected
        )
        == gates_config["require_selected_zero_response_flips"],
        "search_step_ms": all(
            target["search_step_ms"] <= gates_config["maximum_search_step_ms"]
            for target in targets
        ),
        "affine_sweep_ms": all(
            block["affine_sweep_ms"] <= gates_config["maximum_affine_sweep_ms"]
            for block in blocks
        ),
        "direct_validation_ms": all(
            row["direct_wall_ms"] <= gates_config["maximum_direct_validation_ms"]
            for row in fixed
        )
        and all(
            row["direct"]["wall_ms"]
            <= gates_config["maximum_direct_validation_ms"]
            for row in selected
        ),
        "memory": max(row["gpu_pool_total_bytes"] for row in memory_rows)
        <= gates_config["maximum_gpu_pool_bytes"]
        and min(row["gpu_free_bytes"] for row in memory_rows)
        >= gates_config["minimum_physical_free_bytes"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"] == target["blueprint_policy_sha256"]
            for target in targets
        )
        == gates_config["require_blueprint_emission"],
        "finite": all(math.isfinite(float(value)) for value in finite_values)
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    selected_value = math.fsum(
        block["selected_positive_certified_value"] for block in blocks
    )
    parent_oracle = math.fsum(
        block["parent_bounded_oracle_positive_certified_value"] for block in blocks
    )
    result = {
        "schema_version": 1,
        "status": "frozen_h32_selector_stable_affine_certificate_audit_executed",
        "methodology": {
            "preregistered": True,
            "retained_policy_replay": True,
            "fresh_target_quality_labels": False,
            "one_endpoint_terminal_sweep_per_block": True,
            "source_selector_tape_only": True,
            "proof_interval_excludes_first_conservative_tie": True,
            "direct_validations_excluded_from_street_ledger": True,
            "measurement_context": parsed["measurement_context"],
            "emitted_policy": parsed["emitted_policy"],
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": targets,
        "aggregate": {
            "targets": len(targets),
            "public_blocks": len(blocks),
            "affine_seat_rows": len(affine_rows),
            "fixed_direct_validations": len(fixed),
            "selected_affine_candidates": len(selected),
            "selected_positive_certified_value": selected_value,
            "parent_bounded_oracle_positive_certified_value": parent_oracle,
            "selected_capture_fraction": _safe_ratio(selected_value, parent_oracle),
            "seat0_street_ledger_fit_targets": sum(
                target["seat0_descriptive_street_ledger_fit"] for target in targets
            ),
            "maximum_seat0_street_ledger_ms": max(
                target["seat0_descriptive_street_ledger_ms"] for target in targets
            ),
            "maximum_affine_sweep_ms": max(
                block["affine_sweep_ms"] for block in blocks
            ),
            "maximum_direct_utility_error": max(
                row["maximum_utility_error"] for row in direct_errors
            ),
            "maximum_direct_best_response_error": max(
                row["maximum_best_response_error"] for row in direct_errors
            ),
            "maximum_direct_deviation_gain_error": max(
                row["maximum_deviation_gain_error"] for row in direct_errors
            ),
            "maximum_gpu_pool_bytes": max(
                row["gpu_pool_total_bytes"] for row in memory_rows
            ),
            "minimum_gpu_free_bytes": min(
                row["gpu_free_bytes"] for row in memory_rows
            ),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "accept_selector_stable_affine_certificate_differential"
            if gates["passed"]
            else "reject_selector_stable_affine_certificate_differential"
        ),
        "total_audit_seconds": total_seconds,
        "strategy_population_claim": None,
        "limitations": [
            "All six targets and directions are retained engineering customers.",
            "Direct validations are off clock and are not part of the proposed certificate.",
            "The proof stops before the first conservative source-selector tie.",
            "Street ledgers are descriptive until a fresh prospective scheduler is frozen.",
            "No candidate is emitted and no strategy-population claim is made.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_selector_stable_affine_certificate_audit(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
