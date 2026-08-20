"""Run the frozen fresh-board h32 strategy and verifier transfer audit."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Iterable

import numpy as np

from .axis_cfr_checkpoint import (
    axis_cfr_checkpoint_digest,
    export_axis_cfr_checkpoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fixed_envelope_verifier import simulate_fixed_envelope_verifier
from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .h32_current_interpolation_audit import interpolate_behavioral_policy
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _current_policy_from_state,
    _local_blocker_likelihoods,
    _policy_distance,
    _root_marginals,
    _strength_likelihoods,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import _build_case, _solver
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest, policy_statistics
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .resident_leaf_adjoint_evaluation import (
    evaluate_resident_leaf_adjoint_seat,
)
from .river import format_card, parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_PARENT = _ROOT / "experiments" / "results" / "h32-resident-verifier-audit-v1.json"
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_IMPLEMENTATION = Path(__file__)

_SOURCE_PATHS = {
    "expected_resident_parent_sha256": _PARENT,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_axis_checkpoint_sha256": _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py",
    "expected_base_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py",
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
    ),
    "expected_warm_search_sha256": (
        _ROOT / "src" / "pontius" / "h32_warm_search_acceptance_audit.py"
    ),
    "expected_interpolation_sha256": (
        _ROOT / "src" / "pontius" / "h32_current_interpolation_audit.py"
    ),
    "expected_acceptance_semantics_sha256": (
        _ROOT / "src" / "pontius" / "h32_acceptance_semantics_replay.py"
    ),
    "expected_fixed_verifier_sha256": (
        _ROOT / "src" / "pontius" / "fixed_envelope_verifier.py"
    ),
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "factor_tt_contraction.py"
    ),
    "expected_open_mode_factor_tt_sha256": (
        _ROOT / "src" / "pontius" / "open_mode_factor_tt.py"
    ),
    "expected_resident_contraction_sha256": (
        _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py"
    ),
    "expected_resident_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "resident_leaf_adjoint_evaluation.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    *_SOURCE_PATHS,
    "certificate_anchor_rule",
    "board",
    "disclosed_prior_boards",
    "pot",
    "stack",
    "bet_size",
    "players",
    "wide_hands_per_player",
    "range_families",
    "solver_variant",
    "source_checkpoint_iterations",
    "blueprint_point",
    "control_policy_points",
    "target_shifts",
    "local_blocker_target_seat",
    "predicted_predecessor_seat",
    "likelihood_minimum",
    "likelihood_maximum",
    "warm_regret_mass_payoff_fraction",
    "search_checkpoint_iterations",
    "interpolation_alphas",
    "candidate_order",
    "fixed_seat_order",
    "comparison_seat_order_rule",
    "acceptance_guard_normalized",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "legacy_crosscheck_family",
    "legacy_crosscheck_shift",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}

_GATE_FIELDS = {
    "expected_source_family_rows",
    "expected_source_training_steps",
    "expected_source_checkpoints",
    "expected_target_rows",
    "expected_target_rows_per_family",
    "expected_target_search_steps",
    "expected_target_search_checkpoints",
    "expected_candidate_rows",
    "expected_resident_profile_rows",
    "expected_resident_seat_rows",
    "expected_legacy_crosscheck_seat_rows",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "require_fresh_board_identity",
    "require_source_checkpoint_digest_identity",
    "require_target_checkpoint_digest_identity",
    "require_target_axes_identity",
    "require_support_preserving_targets",
    "require_likelihood_bounds_identity",
    "maximum_warm_start_probability_error",
    "maximum_warm_start_mean_tv",
    "maximum_interpolation_normalization_error",
    "maximum_quality_vector_sum_error",
    "maximum_quality_zero_sum_residual",
    "maximum_legacy_resident_utility_error",
    "maximum_legacy_resident_best_response_error",
    "maximum_legacy_resident_deviation_gain_error",
    "require_legacy_resident_action_identity",
    "require_full_pool_selection_identity",
    "require_fixed_envelope_cap_compliance",
    "require_certificate_scope_identity",
    "require_finite_states_policies_and_quality",
    "maximum_training_step_ms",
    "maximum_quality_evaluation_ms",
    "maximum_target_workspace_compile_ms",
    "maximum_static_cache_compile_ms",
    "maximum_resident_seat_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_total_audit_seconds",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _object_digest(value: Any) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def parse_fresh_h32_strategy_transfer_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable ADR-0112 protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("fresh h32 transfer config fields differ from ADR-0112")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0111_before_any_strategy_training_or_"
            "quality_measurement_on_the_fresh_h32_board"
        ),
        "seed": 20260821,
        "axis_seed": 20260819,
        "certificate_anchor_rule": (
            "immutable_episode_blueprint_never_selected_candidate"
        ),
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "disclosed_prior_boards": [
            ["2c", "7d", "9h", "Js", "Qc"],
            ["3s", "8c", "Th", "Kd", "Ac"],
        ],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "solver_variant": "dcfr",
        "source_checkpoint_iterations": [32, 48, 64],
        "blueprint_point": "64:average",
        "control_policy_points": ["32:average", "48:current"],
        "target_shifts": [
            "local_blocker_seat5_x2",
            "all_seat_strength_1_to2",
        ],
        "local_blocker_target_seat": 5,
        "predicted_predecessor_seat": 4,
        "likelihood_minimum": 1.0,
        "likelihood_maximum": 2.0,
        "warm_regret_mass_payoff_fraction": 0.1,
        "search_checkpoint_iterations": [1, 2, 4, 8],
        "interpolation_alphas": [0.25, 0.5, 0.75],
        "candidate_order": [
            "control_average32",
            "control_current48",
            "search_average1",
            "search_average2",
            "search_average4",
            "search_current1",
            "search_current2",
            "search_current4",
            "search_current8",
            "search_average8",
            "interpolate_current1_to2_alpha025",
            "interpolate_current1_to2_alpha050",
            "interpolate_current1_to2_alpha075",
        ],
        "fixed_seat_order": [0, 1, 2, 3, 4, 5],
        "comparison_seat_order_rule": (
            "ascending_absolute_blueprint_cap_then_seat"
        ),
        "acceptance_guard_normalized": 1e-10,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "legacy_crosscheck_family": "balanced",
        "legacy_crosscheck_shift": "local_blocker_seat5_x2",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("fresh h32 transfer workload differs from ADR-0112")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("fresh h32 transfer gates differ from ADR-0112")
    expected_gates = {
        "expected_source_family_rows": 2,
        "expected_source_training_steps": 128,
        "expected_source_checkpoints": 6,
        "expected_target_rows": 4,
        "expected_target_rows_per_family": 2,
        "expected_target_search_steps": 32,
        "expected_target_search_checkpoints": 16,
        "expected_candidate_rows": 52,
        "expected_resident_profile_rows": 56,
        "expected_resident_seat_rows": 336,
        "expected_legacy_crosscheck_seat_rows": 6,
        "expected_wide_information_sets": 6144,
        "expected_wide_hand_action_entries": 12288,
        "require_fresh_board_identity": True,
        "require_source_checkpoint_digest_identity": True,
        "require_target_checkpoint_digest_identity": True,
        "require_target_axes_identity": True,
        "require_support_preserving_targets": True,
        "require_likelihood_bounds_identity": True,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_tv": 1e-13,
        "maximum_interpolation_normalization_error": 1e-12,
        "maximum_quality_vector_sum_error": 1e-12,
        "maximum_quality_zero_sum_residual": 1e-9,
        "maximum_legacy_resident_utility_error": 1e-9,
        "maximum_legacy_resident_best_response_error": 1e-9,
        "maximum_legacy_resident_deviation_gain_error": 1e-9,
        "require_legacy_resident_action_identity": True,
        "require_full_pool_selection_identity": True,
        "require_fixed_envelope_cap_compliance": True,
        "require_certificate_scope_identity": True,
        "require_finite_states_policies_and_quality": True,
        "maximum_training_step_ms": 60_000.0,
        "maximum_quality_evaluation_ms": 60_000.0,
        "maximum_target_workspace_compile_ms": 30_000.0,
        "maximum_static_cache_compile_ms": 120_000.0,
        "maximum_resident_seat_ms": 60_000.0,
        "maximum_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_gpu_pool_bytes": 12_000_000_000,
        "maximum_total_audit_seconds": 9_000.0,
    }
    if gates != expected_gates:
        raise ValueError("fresh h32 transfer gates differ from ADR-0112")
    return {
        **config,
        "disclosed_prior_boards": tuple(
            tuple(board) for board in config["disclosed_prior_boards"]
        ),
        "range_families": tuple(config["range_families"]),
        "source_checkpoint_iterations": tuple(
            config["source_checkpoint_iterations"]
        ),
        "control_policy_points": tuple(config["control_policy_points"]),
        "target_shifts": tuple(config["target_shifts"]),
        "search_checkpoint_iterations": tuple(
            config["search_checkpoint_iterations"]
        ),
        "interpolation_alphas": tuple(config["interpolation_alphas"]),
        "candidate_order": tuple(config["candidate_order"]),
        "fixed_seat_order": tuple(config["fixed_seat_order"]),
        "gates": dict(gates),
    }


def _belief_digest(belief: Any) -> str:
    return _object_digest(
        {
            "board": [format_card(card) for card in belief.board],
            "hands": [
                [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
                for hands in belief.hands_by_player
            ],
            "mixture_weights": belief.mixture_weights.tolist(),
            "unary_weights": [values.tolist() for values in belief.unary_weights],
        }
    )


def _root_digest(parsed: dict[str, Any], layout: Any) -> str:
    return _object_digest(
        {
            "board": parsed["board"],
            "pot": parsed["pot"],
            "stack": parsed["stack"],
            "bet_size": parsed["bet_size"],
            "nodes": [
                {
                    "player": node.player,
                    "actions": node.actions,
                    "children": node.children,
                    "terminal_slot": node.terminal_slot,
                    "history": node.history,
                }
                for node in layout.nodes
            ],
        }
    )


def _finite_policy(policy: dict[str, dict[str, float]]) -> bool:
    return all(
        math.isfinite(float(value)) and float(value) >= 0.0
        for row in policy.values()
        for value in row.values()
    ) and all(abs(math.fsum(row.values()) - 1.0) <= 1e-12 for row in policy.values())


def _finite_state(state: dict[str, Any]) -> bool:
    return all(
        math.isfinite(float(value))
        for table in ("regrets", "strategy_sums")
        for row in state[table].values()
        for value in row.values()
    )


def _quality_vector_sum_error(quality: dict[str, Any]) -> float:
    return abs(math.fsum(float(value) for value in quality["deviation_gains"]) - float(quality["nash_conv"]))


def _absolute_cap_order(blueprint_gains: Iterable[float], *, raw_guard: float) -> tuple[int, ...]:
    gains = tuple(float(value) for value in blueprint_gains)
    if not gains or raw_guard < 0.0 or not math.isfinite(raw_guard):
        raise ValueError("absolute-cap order inputs are invalid")
    return tuple(sorted(range(len(gains)), key=lambda seat: (gains[seat] + raw_guard, seat)))


def _interpolation_diagnostics(policy: dict[str, dict[str, float]]) -> dict[str, Any]:
    totals = tuple(math.fsum(row.values()) for row in policy.values())
    values = tuple(value for row in policy.values() for value in row.values())
    return {
        "maximum_normalization_error": max(abs(total - 1.0) for total in totals),
        "minimum_probability": min(values),
        "maximum_probability": max(values),
        "finite_nonnegative": all(math.isfinite(value) and value >= 0.0 for value in values),
    }


def _build_target_belief(
    source: Any,
    *,
    board: tuple[int, ...],
    shift: str,
    local_blocker_target_seat: int,
) -> tuple[Any, dict[str, Any]]:
    if shift == "local_blocker_seat5_x2":
        likelihoods, detail = _local_blocker_likelihoods(
            source,
            board=board,
            target_seat=local_blocker_target_seat,
        )
    elif shift == "all_seat_strength_1_to2":
        likelihoods, detail = _strength_likelihoods(source, board=board)
    else:
        raise ValueError("unknown fresh h32 target shift")
    target = source
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    values = np.concatenate(likelihoods)
    return target, {
        "shift": shift,
        "likelihood_minimum": float(np.min(values)),
        "likelihood_maximum": float(np.max(values)),
        "likelihood_mean": float(np.mean(values)),
        "positive_likelihoods": bool(np.all(values > 0.0)),
        "hand_axes_identity": target.hands_by_player == source.hands_by_player,
        **detail,
    }


def _legacy_quality_row(
    result: Any,
    *,
    policy: dict[str, dict[str, float]],
    payoff_span: float,
    label: str,
) -> dict[str, Any]:
    evaluation = result.evaluation
    return {
        "policy_kind": label,
        "policy_sha256": policy_digest(policy),
        "utilities": evaluation.utilities,
        "best_response_values": evaluation.best_response_values,
        "deviation_gains": evaluation.deviation_gains,
        "nash_conv": evaluation.nash_conv,
        "normalized_nash_conv": evaluation.nash_conv / payoff_span,
        "zero_sum_residual": result.zero_sum_residual,
        "wall_ms": result.wall_ms,
        "terminal_contraction_ms": math.fsum(
            row.terminal_contraction_ms for row in result.seats
        ),
        "maximum_host_peak_numeric_bytes": max(
            row.maximum_terminal_peak_numeric_bytes for row in result.seats
        ),
        "maximum_gpu_pool_bytes": max(
            row.maximum_gpu_pool_total_bytes for row in result.seats
        ),
        "quality_vector_sum_error": abs(
            math.fsum(evaluation.deviation_gains) - evaluation.nash_conv
        ),
        "finite": all(
            math.isfinite(float(value))
            for values in (
                evaluation.utilities,
                evaluation.best_response_values,
                evaluation.deviation_gains,
            )
            for value in values
        ),
    }


def _action_digest(actions: dict[str, Any]) -> str:
    return _object_digest(
        {key: str(value) for key, value in sorted(actions.items())}
    )


def _resident_quality_row(
    *,
    layout: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    policy: dict[str, dict[str, float]],
    label: str,
    hands_by_player: Any,
    belief_cache: CuPyResidentBeliefCache,
    automaton_caches: tuple[CuPyResidentAutomatonCache, ...],
    gpu: Any,
    payoff_span: float,
    maximum_feature_width_per_batch: int,
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    wall_started = time.perf_counter()
    compile_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        policy,
    )
    probability_compile_ms = (time.perf_counter() - compile_started) * 1000.0
    evaluations = tuple(
        evaluate_resident_leaf_adjoint_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            automata[seat],
            target_player=seat,
            belief_cache=belief_cache,
            automaton_cache=automaton_caches[seat],
            cupy_sparse=gpu,
            hands_by_player=hands_by_player,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for seat in range(layout.num_players)
    )
    utilities = tuple(float(row.profile_utility) for row in evaluations)
    responses = tuple(float(row.best_response_value) for row in evaluations)
    gains = tuple(float(row.deviation_gain) for row in evaluations)
    nash_conv = math.fsum(gains)
    seat_rows = []
    for row in evaluations:
        work = row.resident_work
        seat_rows.append(
            {
                "target_player": row.target_player,
                "profile_utility": row.profile_utility,
                "best_response_value": row.best_response_value,
                "deviation_gain": row.deviation_gain,
                "best_response_actions_sha256": _action_digest(
                    row.best_response_actions
                ),
                "exact_action_ties": row.exact_action_ties,
                "minimum_action_gap": row.minimum_action_gap,
                "wall_ms": row.wall_ms,
                "terminal_contraction_ms": row.terminal_contraction_ms,
                "reverse_evaluation_ms": row.reverse_evaluation_ms,
                "terminal_sparse_batches": row.terminal_sparse_batches,
                "maximum_terminal_middle_rank": row.maximum_terminal_middle_rank,
                "maximum_host_peak_numeric_bytes": (
                    row.maximum_terminal_peak_numeric_bytes
                ),
                "maximum_gpu_pool_bytes": row.maximum_gpu_pool_total_bytes,
                "factor_prepare_ms": work.factor_prepare_ms,
                "factor_upload_ms": work.factor_upload_ms,
                "product_generation_gpu_ms": work.product_generation_gpu_ms,
                "resident_pipeline_gpu_ms": work.resident_pipeline_gpu_ms,
                "device_to_host_ms": work.device_to_host_ms,
                "hand_fold_ms": work.hand_fold_ms,
                "resident_transfer_bytes": (
                    work.per_call_host_to_device_bytes
                    + work.per_call_device_to_host_bytes
                ),
                "legacy_equivalent_transfer_bytes": (
                    work.legacy_equivalent_host_to_device_bytes
                    + work.legacy_equivalent_device_to_host_bytes
                ),
                "total_feature_width": work.total_feature_width,
            }
        )
    result = {
        "policy_kind": label,
        "policy_sha256": policy_digest(policy),
        "utilities": utilities,
        "best_response_values": responses,
        "deviation_gains": gains,
        "nash_conv": nash_conv,
        "normalized_nash_conv": nash_conv / payoff_span,
        "zero_sum_residual": abs(math.fsum(utilities)),
        "probability_compile_ms": probability_compile_ms,
        "seat_rows": seat_rows,
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
        "terminal_contraction_ms": math.fsum(
            row.terminal_contraction_ms for row in evaluations
        ),
        "quality_vector_sum_error": abs(math.fsum(gains) - nash_conv),
        "maximum_host_peak_numeric_bytes": max(
            row.maximum_terminal_peak_numeric_bytes for row in evaluations
        ),
        "maximum_gpu_pool_bytes": max(
            row.maximum_gpu_pool_total_bytes for row in evaluations
        ),
        "finite": all(
            math.isfinite(value) for values in (utilities, responses, gains) for value in values
        ),
    }
    return result, evaluations


def _cache_host_estimate(
    workspace: Any,
    sparse: Any,
    automata: tuple[dict[str, Any], ...],
    caches: tuple[CuPyResidentAutomatonCache, ...],
) -> int:
    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    return int(
        workspace.topology.numeric_bytes
        + workspace.numeric_bytes
        + sparse.numeric_bytes
        + sum(automaton.numeric_bytes for automaton in unique_automata.values())
        + max(cache.numeric_bytes for cache in caches)
    )


def _source_training(
    *,
    parsed: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    belief, layout, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
    )
    workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    solver = _solver(
        parsed=parsed,
        belief=belief,
        topology=layout,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    context = {
        "board": parsed["board"],
        "range_family": family,
        "hands_per_player": parsed["wide_hands_per_player"],
        "purpose": "fresh_h32_source_blueprint",
    }
    provenance = {
        "audit": "ADR-0112",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "solver_variant": parsed["solver_variant"],
    }
    step_rows = []
    checkpoint_rows = []
    policies: dict[str, dict[str, dict[str, float]]] = {}
    checkpoint_identity = True
    cumulative_ms = 0.0
    for iteration in range(1, parsed["source_checkpoint_iterations"][-1] + 1):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        cumulative_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("fresh source step has no work telemetry")
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_host_peak_numeric_bytes": max(
                    row.maximum_terminal_peak_numeric_bytes for row in work.traversers
                ) + solver.accumulator_numeric_bytes(),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
            }
        )
        if iteration not in parsed["source_checkpoint_iterations"]:
            continue
        current = solver.current_strategy()
        average = solver.average_strategy()
        state = export_axis_cfr_checkpoint(
            solver,
            context=context,
            provenance=provenance,
        )
        rendered = json.dumps(
            state,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        restored = json.loads(rendered)
        identity = (
            axis_cfr_checkpoint_digest(restored) == state["state_sha256"]
            and policy_digest(current) == state["current_policy_sha256"]
            and policy_digest(average) == state["average_policy_sha256"]
        )
        checkpoint_identity = checkpoint_identity and identity
        checkpoint_rows.append(
            {
                "iteration": iteration,
                "cumulative_training_ms": cumulative_ms,
                "current_policy_sha256": policy_digest(current),
                "average_policy_sha256": policy_digest(average),
                "current_policy_statistics": policy_statistics(current),
                "average_policy_statistics": policy_statistics(average),
                "state_sha256": state["state_sha256"],
                "state_json_bytes": len(rendered.encode("utf-8")),
                "state_digest_identity": identity,
                "state": state,
            }
        )
        if iteration == 32:
            policies["control_average32"] = average
        if iteration == 48:
            policies["control_current48"] = current
        if iteration == 64:
            policies["blueprint_average64"] = average

    payoff_span = float(layout.game.payoff_span)
    blueprint = policies["blueprint_average64"]
    source_evaluated = evaluate_leaf_adjoint_profile(
        layout,
        workspace,
        sparse,
        blueprint,
        automata,
        hands_by_player=belief.hands_by_player,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        cupy_sparse=gpu,
    )
    source_quality = _legacy_quality_row(
        source_evaluated,
        policy=blueprint,
        payoff_span=payoff_span,
        label="blueprint_average64_source_belief",
    )
    marginals, marginal_ms = _root_marginals(
        workspace,
        sparse,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    schema = solver.information_schema()
    row = {
        "range_family": family,
        "source_belief_sha256": _belief_digest(belief),
        "certification_root_sha256": _root_digest(parsed, layout),
        "workspace_compile_ms": workspace_timing,
        "source_marginal_measurement_ms": marginal_ms,
        "information_sets": len(schema),
        "hand_action_entries": sum(len(actions) for actions in schema.values()),
        "training_steps": step_rows,
        "checkpoints": checkpoint_rows,
        "checkpoint_digest_identity": checkpoint_identity,
        "source_blueprint_quality": source_quality,
        "source_policy_digests": {
            key: policy_digest(policy) for key, policy in policies.items()
        },
        "all_policies_finite": all(_finite_policy(policy) for policy in policies.values()),
    }
    objects = {
        "belief": belief,
        "layout": layout,
        "workspace": workspace,
        "sparse": sparse,
        "automata": automata,
        "gpu": gpu,
        "policies": policies,
        "source_marginals": marginals,
    }
    return row, objects


def _generate_target_candidates(
    *,
    parsed: dict[str, Any],
    family: str,
    shift: str,
    target_belief: Any,
    layout: Any,
    workspace: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
    source_policies: dict[str, dict[str, dict[str, float]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    blueprint = source_policies["blueprint_average64"]
    solver = _solver(
        parsed=parsed,
        belief=target_belief,
        topology=layout,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    solver.warm_start(
        blueprint,
        parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span),
    )
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    context = {
        "board": parsed["board"],
        "range_family": family,
        "target_shift": shift,
        "blueprint_point": parsed["blueprint_point"],
        "hands_per_player": parsed["wide_hands_per_player"],
    }
    provenance = {
        "audit": "ADR-0112",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "certificate_anchor_rule": parsed["certificate_anchor_rule"],
    }
    step_rows = []
    checkpoint_rows = []
    current_policies: dict[int, dict[str, dict[str, float]]] = {}
    average_policies: dict[int, dict[str, dict[str, float]]] = {}
    checkpoint_identity = True
    cumulative_ms = 0.0
    for iteration in range(1, parsed["search_checkpoint_iterations"][-1] + 1):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        cumulative_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("fresh target search step has no work telemetry")
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "cumulative_search_ms": cumulative_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_host_peak_numeric_bytes": max(
                    row.maximum_terminal_peak_numeric_bytes for row in work.traversers
                ) + solver.accumulator_numeric_bytes(),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
            }
        )
        if iteration not in parsed["search_checkpoint_iterations"]:
            continue
        current = solver.current_strategy()
        average = solver.average_strategy()
        state = export_axis_cfr_checkpoint(
            solver,
            context=context,
            provenance=provenance,
        )
        rendered = json.dumps(
            state,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        identity = (
            axis_cfr_checkpoint_digest(json.loads(rendered)) == state["state_sha256"]
            and policy_digest(current) == state["current_policy_sha256"]
            and policy_digest(average) == state["average_policy_sha256"]
        )
        checkpoint_identity = checkpoint_identity and identity
        current_policies[iteration] = current
        average_policies[iteration] = average
        checkpoint_rows.append(
            {
                "iteration": iteration,
                "cumulative_search_ms": cumulative_ms,
                "current_policy_sha256": policy_digest(current),
                "average_policy_sha256": policy_digest(average),
                "state_sha256": state["state_sha256"],
                "state_json_bytes": len(rendered.encode("utf-8")),
                "state_digest_identity": identity,
                "state": state,
            }
        )

    policies: dict[str, dict[str, dict[str, float]]] = {
        "control_average32": source_policies["control_average32"],
        "control_current48": source_policies["control_current48"],
        "search_average1": average_policies[1],
        "search_average2": average_policies[2],
        "search_average4": average_policies[4],
        "search_current1": current_policies[1],
        "search_current2": current_policies[2],
        "search_current4": current_policies[4],
        "search_current8": current_policies[8],
        "search_average8": average_policies[8],
    }
    interpolation_rows = []
    for alpha in parsed["interpolation_alphas"]:
        suffix = f"{int(round(alpha * 100)):03d}"
        candidate_id = f"interpolate_current1_to2_alpha{suffix}"
        policy = interpolate_behavioral_policy(
            current_policies[1],
            current_policies[2],
            alpha,
        )
        policies[candidate_id] = policy
        interpolation_rows.append(
            {
                "candidate_id": candidate_id,
                "alpha": alpha,
                "policy_sha256": policy_digest(policy),
                **_interpolation_diagnostics(policy),
            }
        )
    if tuple(policies) != parsed["candidate_order"]:
        raise AssertionError("fresh target candidate order differs from ADR-0112")

    cumulative_by_iteration = {
        int(row["iteration"]): float(row["cumulative_search_ms"])
        for row in step_rows
    }
    candidates = []
    for candidate_id, policy in policies.items():
        iteration = None
        if candidate_id.startswith("search_average"):
            iteration = int(candidate_id.removeprefix("search_average"))
        elif candidate_id.startswith("search_current"):
            iteration = int(candidate_id.removeprefix("search_current"))
        elif candidate_id.startswith("interpolate_"):
            iteration = 2
        candidates.append(
            {
                "candidate_id": candidate_id,
                "policy": policy,
                "policy_sha256": policy_digest(policy),
                "policy_statistics": policy_statistics(policy),
                "search_iteration": iteration,
                "cumulative_search_ms": (
                    0.0 if iteration is None else cumulative_by_iteration[iteration]
                ),
                "finite": _finite_policy(policy),
            }
        )
    metadata = {
        "warm_start_distance": warm_distance,
        "step_rows": step_rows,
        "checkpoint_rows": checkpoint_rows,
        "checkpoint_digest_identity": checkpoint_identity,
        "interpolation_rows": interpolation_rows,
    }
    return candidates, checkpoint_rows, metadata


def _candidate_cap_diagnostics(
    blueprint_quality: dict[str, Any],
    candidate_quality: dict[str, Any],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    excesses = tuple(
        float(candidate) - float(blueprint) - raw_guard
        for blueprint, candidate in zip(
            blueprint_quality["deviation_gains"],
            candidate_quality["deviation_gains"],
            strict=True,
        )
    )
    violating = tuple(seat for seat, value in enumerate(excesses) if value > 0.0)
    maximum = max(excesses)
    maximum_seat = min(
        seat for seat, value in enumerate(excesses) if value == maximum
    )
    return {
        "cap_excesses": excesses,
        "violating_seats": violating,
        "feasible": not violating,
        "maximum_cap_excess": maximum,
        "maximum_cap_excess_seat": maximum_seat,
    }


def _project_order_bill(
    simulation: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    *,
    cache_compile_ms: float,
    target_compile_ms: float,
    blueprint_quality: dict[str, Any],
) -> dict[str, Any]:
    marginal = 0.0
    probability = 0.0
    seat_ms = 0.0
    seats = 0
    for row in simulation["candidate_rows"]:
        profile = profiles[row["candidate_id"]]
        probability += float(profile["probability_compile_ms"])
        by_seat = {
            int(seat["target_player"]): seat for seat in profile["seat_rows"]
        }
        selected = math.fsum(
            float(by_seat[seat]["wall_ms"]) for seat in row["evaluated_seats"]
        )
        seat_ms += selected
        seats += len(row["evaluated_seats"])
    marginal = probability + seat_ms
    return {
        "evaluated_seats": seats,
        "probability_compile_ms": probability,
        "resident_seat_ms": seat_ms,
        "verifier_marginal_ms": marginal,
        "verifier_cache_charged_ms": cache_compile_ms + marginal,
        "full_decision_one_shot_ms": (
            target_compile_ms
            + cache_compile_ms
            + float(blueprint_quality["wall_ms"])
            + marginal
        ),
    }


def _certificate_scope(
    *,
    parsed: dict[str, Any],
    layout: Any,
    target_belief: Any,
    blueprint_quality: dict[str, Any],
    raw_guard: float,
) -> dict[str, Any]:
    blueprint_digest = str(blueprint_quality["policy_sha256"])
    return {
        "anchor_rule": parsed["certificate_anchor_rule"],
        "episode_blueprint_policy_sha256": blueprint_digest,
        "certification_public_root_sha256": _root_digest(parsed, layout),
        "belief_sha256": _belief_digest(target_belief),
        "deployed_policy_prefix_sha256": _object_digest(
            {"public_actions_before_root": []}
        ),
        "blueprint_deviation_gains": blueprint_quality["deviation_gains"],
        "cap_vector": tuple(
            float(value) + raw_guard
            for value in blueprint_quality["deviation_gains"]
        ),
        "raw_guard": raw_guard,
        "payoff_span": parsed["stack"],
        "expires_after_public_transition": True,
        "selected_candidate_becomes_anchor": False,
        "cumulative_episode_safety_claim": False,
    }


def _run_target(
    *,
    parsed: dict[str, Any],
    board: tuple[int, ...],
    family: str,
    shift: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    source_belief = source["belief"]
    layout = source["layout"]
    source_workspace = source["workspace"]
    sparse = source["sparse"]
    automata = source["automata"]
    gpu = source["gpu"]
    source_policies = source["policies"]
    target_belief, descriptor = _build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parsed["local_blocker_target_seat"],
    )
    compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    target_workspace = OpenModeFactorTTWorkspace.compile(
        source_workspace.topology,
        base,
    )
    target_compile_ms = (time.perf_counter() - compile_started) * 1000.0
    target_marginals, marginal_ms = _root_marginals(
        target_workspace,
        sparse,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    marginal_tvs = tuple(
        0.5 * float(np.sum(np.abs(first - second)))
        for first, second in zip(
            source["source_marginals"],
            target_marginals,
            strict=True,
        )
    )
    descriptor.update(
        {
            "source_partition": source_workspace.base.partition,
            "target_partition": target_workspace.base.partition,
            "target_to_source_partition_ratio": (
                target_workspace.base.partition / source_workspace.base.partition
            ),
            "marginal_total_variations": marginal_tvs,
            "mean_marginal_total_variation": math.fsum(marginal_tvs) / len(marginal_tvs),
            "maximum_marginal_total_variation": max(marginal_tvs),
            "marginal_measurement_ms": marginal_ms,
        }
    )

    candidates, checkpoint_rows, search = _generate_target_candidates(
        parsed=parsed,
        family=family,
        shift=shift,
        target_belief=target_belief,
        layout=layout,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        gpu=gpu,
        source_policies=source_policies,
    )
    blueprint_policy = source_policies["blueprint_average64"]
    legacy_control = None
    legacy_result = None
    if (
        family == parsed["legacy_crosscheck_family"]
        and shift == parsed["legacy_crosscheck_shift"]
    ):
        legacy_result = evaluate_leaf_adjoint_profile(
            layout,
            target_workspace,
            sparse,
            blueprint_policy,
            automata,
            hands_by_player=target_belief.hands_by_player,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            cupy_sparse=gpu,
        )
        legacy_control = _legacy_quality_row(
            legacy_result,
            policy=blueprint_policy,
            payoff_span=float(layout.game.payoff_span),
            label="legacy_blueprint_crosscheck",
        )

    gc.collect()
    release_cupy_memory_pool()
    cache_started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(target_workspace)
    automaton_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            target_workspace,
            automata[seat],
            target_seat=seat,
        )
        for seat in range(layout.num_players)
    )
    cache_compile_ms = (time.perf_counter() - cache_started) * 1000.0
    cache_numeric_bytes = belief_cache.numeric_bytes + sum(
        cache.numeric_bytes for cache in automaton_caches
    )
    cache_host_bytes = _cache_host_estimate(
        target_workspace,
        sparse,
        automata,
        automaton_caches,
    )
    payoff_span = float(layout.game.payoff_span)
    blueprint_quality, blueprint_evaluations = _resident_quality_row(
        layout=layout,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        policy=blueprint_policy,
        label="blueprint_average64",
        hands_by_player=target_belief.hands_by_player,
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        gpu=gpu,
        payoff_span=payoff_span,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    blueprint_row = {
        "candidate_id": "blueprint_average64",
        "quality": blueprint_quality,
    }
    evaluated_candidates = []
    profile_by_id = {}
    for candidate in candidates:
        quality, _ = _resident_quality_row(
            layout=layout,
            workspace=target_workspace,
            sparse=sparse,
            automata=automata,
            policy=candidate["policy"],
            label=candidate["candidate_id"],
            hands_by_player=target_belief.hands_by_player,
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            gpu=gpu,
            payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        cap = _candidate_cap_diagnostics(
            blueprint_quality,
            quality,
            raw_guard=parsed["acceptance_guard_normalized"] * payoff_span,
        )
        row = {
            key: value for key, value in candidate.items() if key != "policy"
        }
        row.update(
            {
                "quality": quality,
                "cap_diagnostics": cap,
                "raw_nash_conv_reduction": (
                    float(blueprint_quality["nash_conv"])
                    - float(quality["nash_conv"])
                ),
                "normalized_nash_conv_reduction": (
                    float(blueprint_quality["normalized_nash_conv"])
                    - float(quality["normalized_nash_conv"])
                ),
            }
        )
        evaluated_candidates.append(row)
        profile_by_id[row["candidate_id"]] = quality

    raw_guard = parsed["acceptance_guard_normalized"] * payoff_span
    full_selection = select_fixed_blueprint_envelope(
        blueprint_row,
        evaluated_candidates,
        raw_guard=raw_guard,
    )
    fixed_order = parsed["fixed_seat_order"]
    cap_order = _absolute_cap_order(
        blueprint_quality["deviation_gains"],
        raw_guard=raw_guard,
    )
    fixed_simulation = simulate_fixed_envelope_verifier(
        blueprint_row,
        evaluated_candidates,
        seat_order=fixed_order,
        raw_guard=raw_guard,
    )
    cap_simulation = simulate_fixed_envelope_verifier(
        blueprint_row,
        evaluated_candidates,
        seat_order=cap_order,
        raw_guard=raw_guard,
    )
    fixed_bill = _project_order_bill(
        fixed_simulation,
        profile_by_id,
        cache_compile_ms=cache_compile_ms,
        target_compile_ms=target_compile_ms,
        blueprint_quality=blueprint_quality,
    )
    cap_bill = _project_order_bill(
        cap_simulation,
        profile_by_id,
        cache_compile_ms=cache_compile_ms,
        target_compile_ms=target_compile_ms,
        blueprint_quality=blueprint_quality,
    )
    order_identity = all(
        simulation["selection"]["selected_policy_sha256"]
        == full_selection["selected_policy_sha256"]
        for simulation in (fixed_simulation, cap_simulation)
    )
    selected_quality = (
        blueprint_quality
        if full_selection["selected_candidate_id"] == "blueprint_average64"
        else next(
            row["quality"]
            for row in evaluated_candidates
            if row["candidate_id"] == full_selection["selected_candidate_id"]
        )
    )
    selected_reduction = (
        float(blueprint_quality["nash_conv"])
        - float(selected_quality["nash_conv"])
    )
    headroom_capture = (
        selected_reduction / float(blueprint_quality["nash_conv"])
        if float(blueprint_quality["nash_conv"]) > 0.0
        else 0.0
    )
    certificate = _certificate_scope(
        parsed=parsed,
        layout=layout,
        target_belief=target_belief,
        blueprint_quality=blueprint_quality,
        raw_guard=raw_guard,
    )

    crosscheck = None
    if legacy_result is not None and legacy_control is not None:
        utility_errors = tuple(
            abs(float(a) - float(b))
            for a, b in zip(
                legacy_control["utilities"],
                blueprint_quality["utilities"],
                strict=True,
            )
        )
        response_errors = tuple(
            abs(float(a) - float(b))
            for a, b in zip(
                legacy_control["best_response_values"],
                blueprint_quality["best_response_values"],
                strict=True,
            )
        )
        gain_errors = tuple(
            abs(float(a) - float(b))
            for a, b in zip(
                legacy_control["deviation_gains"],
                blueprint_quality["deviation_gains"],
                strict=True,
            )
        )
        action_identity_by_seat = tuple(
            first == second.best_response_actions
            for first, second in zip(
                legacy_result.best_response_actions,
                blueprint_evaluations,
                strict=True,
            )
        )
        crosscheck = {
            "legacy_quality": legacy_control,
            "resident_policy_sha256": blueprint_quality["policy_sha256"],
            "utility_errors": utility_errors,
            "best_response_errors": response_errors,
            "deviation_gain_errors": gain_errors,
            "maximum_utility_error": max(utility_errors),
            "maximum_best_response_error": max(response_errors),
            "maximum_deviation_gain_error": max(gain_errors),
            "action_identity_by_seat": action_identity_by_seat,
            "action_identity": all(action_identity_by_seat),
        }

    maximum_excess_seats = [
        int(row["cap_diagnostics"]["maximum_cap_excess_seat"])
        for row in evaluated_candidates
        if not row["cap_diagnostics"]["feasible"]
    ]
    predecessor = parsed["predicted_predecessor_seat"]
    result = {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "target_belief_sha256": _belief_digest(target_belief),
        "target_workspace_compile_ms": target_compile_ms,
        "target_axes_identity": (
            target_belief.hands_by_player == source_belief.hands_by_player
            and target_workspace.topology is source_workspace.topology
        ),
        "support_preserving_target": descriptor["positive_likelihoods"],
        "search": search,
        "search_checkpoints": checkpoint_rows,
        "blueprint_quality": blueprint_quality,
        "candidates": evaluated_candidates,
        "resident_profile_rows": 1 + len(evaluated_candidates),
        "resident_seat_rows": 6 * (1 + len(evaluated_candidates)),
        "static_cache": {
            "compile_ms": cache_compile_ms,
            "numeric_bytes": cache_numeric_bytes,
            "host_estimate_bytes": cache_host_bytes,
            "gpu_pool_bytes": max(
                [belief_cache.pool_total_bytes]
                + [cache.pool_total_bytes for cache in automaton_caches]
            ),
        },
        "legacy_resident_crosscheck": crosscheck,
        "full_pool_selection": full_selection,
        "fixed_order_verifier": {
            "seat_order": fixed_order,
            "simulation": fixed_simulation,
            "economics": fixed_bill,
        },
        "absolute_cap_order_verifier": {
            "seat_order": cap_order,
            "simulation": cap_simulation,
            "economics": cap_bill,
        },
        "full_pool_selection_identity": order_identity,
        "strategy_outcome": {
            "selected_candidate_id": full_selection["selected_candidate_id"],
            "selected_policy_sha256": full_selection["selected_policy_sha256"],
            "selected_raw_nash_conv_reduction": selected_reduction,
            "selected_normalized_nash_conv_reduction": (
                selected_reduction / payoff_span
            ),
            "headroom_capture_fraction": headroom_capture,
            "blueprint_abstention": full_selection["blueprint_abstention"],
        },
        "predecessor_hypothesis": {
            "predicted_predecessor_seat": predecessor,
            "infeasible_candidate_count": len(maximum_excess_seats),
            "maximum_cap_excess_seats": maximum_excess_seats,
            "predicted_predecessor_count": maximum_excess_seats.count(predecessor),
            "modal_maximum_cap_excess_seat": (
                None
                if not maximum_excess_seats
                else min(
                    range(parsed["players"]),
                    key=lambda seat: (-maximum_excess_seats.count(seat), seat),
                )
            ),
        },
        "certificate": certificate,
        "finite": (
            _finite_policy(blueprint_policy)
            and bool(blueprint_quality["finite"])
            and all(row["finite"] and row["quality"]["finite"] for row in evaluated_candidates)
            and all(_finite_state(row["state"]) for row in checkpoint_rows)
        ),
        "resources": {
            "maximum_host_peak_numeric_bytes": max(
                [cache_host_bytes, blueprint_quality["maximum_host_peak_numeric_bytes"]]
                + [row["quality"]["maximum_host_peak_numeric_bytes"] for row in evaluated_candidates]
                + [row["maximum_host_peak_numeric_bytes"] for row in search["step_rows"]]
            ),
            "maximum_gpu_pool_bytes": max(
                [
                    max(
                        [belief_cache.pool_total_bytes]
                        + [cache.pool_total_bytes for cache in automaton_caches]
                    ),
                    blueprint_quality["maximum_gpu_pool_bytes"],
                ]
                + [row["quality"]["maximum_gpu_pool_bytes"] for row in evaluated_candidates]
                + [row["maximum_gpu_pool_bytes"] for row in search["step_rows"]]
            ),
        },
    }
    del automaton_caches, belief_cache, blueprint_evaluations, legacy_result
    gc.collect()
    release_cupy_memory_pool()
    return result


def _certificate_scope_identity(
    target: dict[str, Any],
    *,
    parsed: dict[str, Any],
) -> bool:
    certificate = target["certificate"]
    required = {
        "anchor_rule",
        "episode_blueprint_policy_sha256",
        "certification_public_root_sha256",
        "belief_sha256",
        "deployed_policy_prefix_sha256",
        "blueprint_deviation_gains",
        "cap_vector",
        "raw_guard",
        "payoff_span",
        "expires_after_public_transition",
        "selected_candidate_becomes_anchor",
        "cumulative_episode_safety_claim",
    }
    return (
        set(certificate) == required
        and certificate["anchor_rule"] == parsed["certificate_anchor_rule"]
        and certificate["belief_sha256"] == target["target_belief_sha256"]
        and certificate["episode_blueprint_policy_sha256"]
        == target["blueprint_quality"]["policy_sha256"]
        and certificate["expires_after_public_transition"] is True
        and certificate["selected_candidate_becomes_anchor"] is False
        and certificate["cumulative_episode_safety_claim"] is False
    )


def run_fresh_h32_strategy_transfer_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute the sealed ADR-0112 fresh-board audit."""

    parsed = parse_fresh_h32_strategy_transfer_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0112")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0112")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0112")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0112")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0112 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0112")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")
    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    parent_identity = bool(parent["gates"]["passed"]) and parent[
        "status"
    ] == "frozen_audit_executed"
    if not parent_identity:
        raise ValueError("accepted resident parent identity rejected")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    source_rows = []
    targets = []
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
        source_row, source = _source_training(
            parsed=parsed,
            board=board,
            family=family,
        )
        source_rows.append(source_row)
        for shift in parsed["target_shifts"]:
            targets.append(
                _run_target(
                    parsed=parsed,
                    board=board,
                    family=family,
                    shift=shift,
                    source=source,
                )
            )
        del source["gpu"]
        del source
        gc.collect()
        release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    source_steps = [row for source in source_rows for row in source["training_steps"]]
    source_checkpoints = [
        row for source in source_rows for row in source["checkpoints"]
    ]
    search_steps = [
        row for target in targets for row in target["search"]["step_rows"]
    ]
    search_checkpoints = [
        row for target in targets for row in target["search_checkpoints"]
    ]
    candidates = [row for target in targets for row in target["candidates"]]
    profiles = [
        target["blueprint_quality"] for target in targets
    ] + [row["quality"] for row in candidates]
    seats = [seat for profile in profiles for seat in profile["seat_rows"]]
    crosschecks = [
        target["legacy_resident_crosscheck"]
        for target in targets
        if target["legacy_resident_crosscheck"] is not None
    ]
    gates_config = parsed["gates"]
    maximum_interpolation_error = max(
        row["maximum_normalization_error"]
        for target in targets
        for row in target["search"]["interpolation_rows"]
    )
    maximum_quality_sum_error = max(
        _quality_vector_sum_error(profile) for profile in profiles
    )
    maximum_zero_sum = max(
        [float(profile["zero_sum_residual"]) for profile in profiles]
        + [
            float(source["source_blueprint_quality"]["zero_sum_residual"])
            for source in source_rows
        ]
    )
    maximum_host = max(
        [target["resources"]["maximum_host_peak_numeric_bytes"] for target in targets]
        + [
            row["maximum_host_peak_numeric_bytes"]
            for source in source_rows
            for row in source["training_steps"]
        ]
    )
    maximum_gpu = max(
        [target["resources"]["maximum_gpu_pool_bytes"] for target in targets]
        + [
            row["maximum_gpu_pool_bytes"]
            for source in source_rows
            for row in source["training_steps"]
        ]
    )
    maximum_training_step = max(
        float(row["wall_ms"]) for row in [*source_steps, *search_steps]
    )
    maximum_quality_ms = max(
        [float(profile["wall_ms"]) for profile in profiles]
        + [
            float(source["source_blueprint_quality"]["wall_ms"])
            for source in source_rows
        ]
    )
    maximum_target_compile = max(
        float(target["target_workspace_compile_ms"]) for target in targets
    )
    maximum_cache_compile = max(
        float(target["static_cache"]["compile_ms"]) for target in targets
    )
    maximum_seat_ms = max(float(seat["wall_ms"]) for seat in seats)
    fresh_board_identity = tuple(parsed["board"]) not in parsed[
        "disclosed_prior_boards"
    ]
    fixed_cap_compliance = all(
        not target["full_pool_selection"]["selected_violating_seats"]
        and float(target["full_pool_selection"]["selected_maximum_cap_excess"])
        <= 0.0
        for target in targets
    )
    source_information_sets = {row["information_sets"] for row in source_rows}
    source_entries = {row["hand_action_entries"] for row in source_rows}
    gates = {
        "parent_identity": parent_identity,
        "source_family_rows": len(source_rows)
        == gates_config["expected_source_family_rows"],
        "source_training_steps": len(source_steps)
        == gates_config["expected_source_training_steps"],
        "source_checkpoints": len(source_checkpoints)
        == gates_config["expected_source_checkpoints"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "target_rows_per_family": all(
            sum(target["range_family"] == family for target in targets)
            == gates_config["expected_target_rows_per_family"]
            for family in parsed["range_families"]
        ),
        "target_search_steps": len(search_steps)
        == gates_config["expected_target_search_steps"],
        "target_search_checkpoints": len(search_checkpoints)
        == gates_config["expected_target_search_checkpoints"],
        "candidate_rows": len(candidates) == gates_config["expected_candidate_rows"],
        "resident_profile_rows": len(profiles)
        == gates_config["expected_resident_profile_rows"],
        "resident_seat_rows": len(seats)
        == gates_config["expected_resident_seat_rows"],
        "legacy_crosscheck_seat_rows": 6 * len(crosschecks)
        == gates_config["expected_legacy_crosscheck_seat_rows"],
        "wide_information_sets": source_information_sets
        == {gates_config["expected_wide_information_sets"]},
        "wide_hand_action_entries": source_entries
        == {gates_config["expected_wide_hand_action_entries"]},
        "fresh_board_identity": fresh_board_identity
        == gates_config["require_fresh_board_identity"],
        "source_checkpoint_digest_identity": all(
            source["checkpoint_digest_identity"] for source in source_rows
        ) == gates_config["require_source_checkpoint_digest_identity"],
        "target_checkpoint_digest_identity": all(
            target["search"]["checkpoint_digest_identity"] for target in targets
        ) == gates_config["require_target_checkpoint_digest_identity"],
        "target_axes_identity": all(target["target_axes_identity"] for target in targets)
        == gates_config["require_target_axes_identity"],
        "support_preserving_targets": all(
            target["support_preserving_target"] for target in targets
        ) == gates_config["require_support_preserving_targets"],
        "likelihood_bounds_identity": all(
            target["target_descriptor"]["likelihood_minimum"]
            == parsed["likelihood_minimum"]
            and target["target_descriptor"]["likelihood_maximum"]
            == parsed["likelihood_maximum"]
            for target in targets
        ) == gates_config["require_likelihood_bounds_identity"],
        "warm_start_probability_error": max(
            target["search"]["warm_start_distance"]["maximum_probability_error"]
            for target in targets
        ) <= gates_config["maximum_warm_start_probability_error"],
        "warm_start_mean_tv": max(
            target["search"]["warm_start_distance"]["mean_total_variation"]
            for target in targets
        ) <= gates_config["maximum_warm_start_mean_tv"],
        "interpolation_normalization_error": maximum_interpolation_error
        <= gates_config["maximum_interpolation_normalization_error"],
        "quality_vector_sum_error": maximum_quality_sum_error
        <= gates_config["maximum_quality_vector_sum_error"],
        "quality_zero_sum_residual": maximum_zero_sum
        <= gates_config["maximum_quality_zero_sum_residual"],
        "legacy_resident_utility_error": max(
            row["maximum_utility_error"] for row in crosschecks
        ) <= gates_config["maximum_legacy_resident_utility_error"],
        "legacy_resident_best_response_error": max(
            row["maximum_best_response_error"] for row in crosschecks
        ) <= gates_config["maximum_legacy_resident_best_response_error"],
        "legacy_resident_deviation_gain_error": max(
            row["maximum_deviation_gain_error"] for row in crosschecks
        ) <= gates_config["maximum_legacy_resident_deviation_gain_error"],
        "legacy_resident_action_identity": all(
            row["action_identity"] for row in crosschecks
        ) == gates_config["require_legacy_resident_action_identity"],
        "full_pool_selection_identity": all(
            target["full_pool_selection_identity"] for target in targets
        ) == gates_config["require_full_pool_selection_identity"],
        "fixed_envelope_cap_compliance": fixed_cap_compliance
        == gates_config["require_fixed_envelope_cap_compliance"],
        "certificate_scope_identity": all(
            _certificate_scope_identity(target, parsed=parsed) for target in targets
        ) == gates_config["require_certificate_scope_identity"],
        "finite_states_policies_and_quality": (
            all(source["all_policies_finite"] for source in source_rows)
            and all(_finite_state(row["state"]) for row in source_checkpoints)
            and all(target["finite"] for target in targets)
        ) == gates_config["require_finite_states_policies_and_quality"],
        "training_step_ms": maximum_training_step
        <= gates_config["maximum_training_step_ms"],
        "quality_evaluation_ms": maximum_quality_ms
        <= gates_config["maximum_quality_evaluation_ms"],
        "target_workspace_compile_ms": maximum_target_compile
        <= gates_config["maximum_target_workspace_compile_ms"],
        "static_cache_compile_ms": maximum_cache_compile
        <= gates_config["maximum_static_cache_compile_ms"],
        "resident_seat_ms": maximum_seat_ms
        <= gates_config["maximum_resident_seat_ms"],
        "host_peak_numeric_bytes": maximum_host
        <= gates_config["maximum_host_peak_numeric_bytes"],
        "gpu_pool_bytes": maximum_gpu <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())

    fixed_seats = sum(
        target["fixed_order_verifier"]["economics"]["evaluated_seats"]
        for target in targets
    )
    cap_seats = sum(
        target["absolute_cap_order_verifier"]["economics"]["evaluated_seats"]
        for target in targets
    )
    fixed_bill = math.fsum(
        target["fixed_order_verifier"]["economics"]["verifier_cache_charged_ms"]
        for target in targets
    )
    cap_bill = math.fsum(
        target["absolute_cap_order_verifier"]["economics"]["verifier_cache_charged_ms"]
        for target in targets
    )
    local_targets = [
        target for target in targets if target["target_shift"] == "local_blocker_seat5_x2"
    ]
    return {
        "schema_version": 1,
        "status": "frozen_audit_executed",
        "experiment_type": "fresh_h32_strategy_verifier_transfer",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field.removeprefix("expected_").removesuffix("_sha256"): _sha256(path)
            for field, path in _SOURCE_PATHS.items()
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
        "freshness": {
            "board": parsed["board"],
            "disclosed_prior_boards": parsed["disclosed_prior_boards"],
            "fresh_board_identity": fresh_board_identity,
            "strategy_quality_labels_observed_before_freeze": 0,
        },
        "source_family_rows": source_rows,
        "targets": targets,
        "counts": {
            "source_family_rows": len(source_rows),
            "source_training_steps": len(source_steps),
            "source_checkpoints": len(source_checkpoints),
            "target_rows": len(targets),
            "target_search_steps": len(search_steps),
            "target_search_checkpoints": len(search_checkpoints),
            "candidate_rows": len(candidates),
            "resident_profile_rows": len(profiles),
            "resident_seat_rows": len(seats),
            "legacy_crosscheck_seat_rows": 6 * len(crosschecks),
        },
        "strategy_transfer": {
            "non_blueprint_selections": sum(
                not target["strategy_outcome"]["blueprint_abstention"]
                for target in targets
            ),
            "local_non_blueprint_selections": sum(
                not target["strategy_outcome"]["blueprint_abstention"]
                for target in local_targets
            ),
            "selected_normalized_reductions": [
                target["strategy_outcome"]["selected_normalized_nash_conv_reduction"]
                for target in targets
            ],
            "headroom_capture_fractions": [
                target["strategy_outcome"]["headroom_capture_fraction"]
                for target in targets
            ],
        },
        "seat_order_transfer": {
            "fixed_evaluated_seats": fixed_seats,
            "absolute_cap_evaluated_seats": cap_seats,
            "seat_reduction": fixed_seats - cap_seats,
            "fixed_cache_charged_ms": fixed_bill,
            "absolute_cap_cache_charged_ms": cap_bill,
            "fixed_to_absolute_cap_speedup": fixed_bill / cap_bill,
        },
        "predecessor_transfer": {
            "predicted_predecessor_seat": parsed["predicted_predecessor_seat"],
            "local_target_modal_seats": [
                target["predecessor_hypothesis"]["modal_maximum_cap_excess_seat"]
                for target in local_targets
            ],
            "local_predicted_predecessor_counts": [
                target["predecessor_hypothesis"]["predicted_predecessor_count"]
                for target in local_targets
            ],
        },
        "correctness": {
            "maximum_quality_vector_sum_error": maximum_quality_sum_error,
            "maximum_zero_sum_residual": maximum_zero_sum,
            "maximum_legacy_resident_utility_error": max(
                row["maximum_utility_error"] for row in crosschecks
            ),
            "maximum_legacy_resident_best_response_error": max(
                row["maximum_best_response_error"] for row in crosschecks
            ),
            "maximum_legacy_resident_deviation_gain_error": max(
                row["maximum_deviation_gain_error"] for row in crosschecks
            ),
            "legacy_resident_action_identity": all(
                row["action_identity"] for row in crosschecks
            ),
        },
        "resources": {
            "maximum_host_peak_numeric_bytes": maximum_host,
            "maximum_gpu_pool_bytes": maximum_gpu,
            "maximum_training_step_ms": maximum_training_step,
            "maximum_quality_evaluation_ms": maximum_quality_ms,
            "maximum_target_workspace_compile_ms": maximum_target_compile,
            "maximum_static_cache_compile_ms": maximum_cache_compile,
            "maximum_resident_seat_ms": maximum_seat_ms,
        },
        "gates": gates,
        "timing": {"total_audit_seconds": total_seconds},
        "limitations": [
            "This is one fresh river board, one bet size, and equal stacks.",
            "The fixed envelope certifies unilateral deviation gains only, not coalition safety.",
            "Every certificate is one-shot and expires after a public transition.",
            "The selected policy never becomes a safety anchor implicitly.",
            "Seat-order and predecessor outcomes are transfer measurements, not deployment rules.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_fresh_h32_strategy_transfer_audit(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "fresh h32 strategy transfer audit: "
        f"passed={result['gates']['passed']} "
        f"selections={result['strategy_transfer']['non_blueprint_selections']} "
        f"order_speedup={result['seat_order_transfer']['fixed_to_absolute_cap_speedup']:.3f} "
        f"seconds={result['timing']['total_audit_seconds']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
