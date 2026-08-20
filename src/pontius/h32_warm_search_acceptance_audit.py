"""Test exact guarded warm search from real h32 DCFR blueprints."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

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
from .factorized_belief import FactorizedCardBelief
from .leaf_adjoint_checkpoint_ladder_audit import (
    _build_case,
    _quality_row,
    _solver,
)
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import mean_policy_total_variation, policy_digest, policy_statistics
from .reporting import environment_metadata
from .river import evaluate_seven, format_card, parse_cards
from .sparse_open_mode_factor_tt import contract_sparse_open_mode_batch
from .tensor_train import TensorTrain

_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_LADDER_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_EXTENSION_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-extension-v1.json"
)
_WIDTH_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-batch-width-audit-v2.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_width_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_leaf_adjoint_evaluation_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_factor_tt_contraction_sha256",
    "expected_open_mode_factor_tt_sha256",
    "expected_sparse_open_mode_factor_tt_sha256",
    "expected_sparse_incidence_sha256",
    "expected_structured_showdown_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "wide_hands_per_player",
    "range_families",
    "solver_variant",
    "blueprint_point",
    "control_policy_points",
    "target_shifts",
    "local_blocker_target_seat",
    "likelihood_minimum",
    "likelihood_maximum",
    "warm_regret_mass_payoff_fraction",
    "search_checkpoint_iterations",
    "primary_search_iteration",
    "acceptance_guard_normalized",
    "candidate_order",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
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
    "expected_target_rows",
    "expected_target_rows_per_family",
    "expected_candidate_rows_per_target",
    "expected_search_candidates_per_target",
    "expected_final_search_iteration",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "expected_sparse_batches_by_family",
    "require_source_policy_digest_identity",
    "require_target_axes_identity",
    "require_support_preserving_targets",
    "require_likelihood_bounds_identity",
    "minimum_target_mean_marginal_tv",
    "maximum_warm_start_probability_error",
    "maximum_warm_start_mean_tv",
    "require_checkpoint_state_digest_identity",
    "require_primary_candidate_identity",
    "maximum_training_step_ms",
    "maximum_quality_evaluation_ms",
    "maximum_target_workspace_compile_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_quality_zero_sum_residual",
    "require_finite_states_policies_and_quality",
    "maximum_total_audit_seconds",
}
_SOURCE_PATHS = {
    "expected_ladder_source_sha256": _LADDER_SOURCE,
    "expected_extension_source_sha256": _EXTENSION_SOURCE,
    "expected_width_source_sha256": _WIDTH_SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_axis_checkpoint_sha256": (
        _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py"
    ),
    "expected_base_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
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
    "expected_sparse_open_mode_factor_tt_sha256": (
        _ROOT / "src" / "pontius" / "sparse_open_mode_factor_tt.py"
    ),
    "expected_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py"
    ),
    "expected_structured_showdown_sha256": (
        _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_warm_search_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable ADR-0099 strategy experiment."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "h32 warm-search fields differ from ADR-0099: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0098_before_any_shifted_h32_blueprint_or_"
            "warm_search_quality"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "solver_variant": "dcfr",
        "blueprint_point": "64:average",
        "control_policy_points": ["32:average", "48:current"],
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "local_blocker_target_seat": 3,
        "likelihood_minimum": 1.0,
        "likelihood_maximum": 2.0,
        "warm_regret_mass_payoff_fraction": 0.1,
        "search_checkpoint_iterations": [1, 2, 4],
        "primary_search_iteration": 4,
        "acceptance_guard_normalized": 1e-10,
        "candidate_order": [
            "control_average32",
            "control_current48",
            "search_average1",
            "search_average2",
            "search_average4",
        ],
        "mixture_components": 3,
        "split_index": 3,
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
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("h32 warm-search workload differs from ADR-0099")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_target_rows_per_family": 2,
        "expected_candidate_rows_per_target": 5,
        "expected_search_candidates_per_target": 3,
        "expected_final_search_iteration": 4,
        "expected_wide_information_sets": 6144,
        "expected_wide_hand_action_entries": 12288,
        "expected_sparse_batches_by_family": {
            "balanced": 435,
            "blocker_heavy": 311,
        },
        "require_source_policy_digest_identity": True,
        "require_target_axes_identity": True,
        "require_support_preserving_targets": True,
        "require_likelihood_bounds_identity": True,
        "minimum_target_mean_marginal_tv": 1e-6,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_tv": 1e-13,
        "require_checkpoint_state_digest_identity": True,
        "require_primary_candidate_identity": True,
        "maximum_training_step_ms": 60000.0,
        "maximum_quality_evaluation_ms": 60000.0,
        "maximum_target_workspace_compile_ms": 30000.0,
        "maximum_host_peak_numeric_bytes": 3000000000,
        "maximum_gpu_pool_bytes": 4000000000,
        "maximum_quality_zero_sum_residual": 1e-9,
        "require_finite_states_policies_and_quality": True,
        "maximum_total_audit_seconds": 1800.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("h32 warm-search gates differ from ADR-0099")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "control_policy_points": tuple(config["control_policy_points"]),
        "target_shifts": tuple(config["target_shifts"]),
        "search_checkpoint_iterations": tuple(
            config["search_checkpoint_iterations"]
        ),
        "candidate_order": tuple(config["candidate_order"]),
        "gates": {
            **gates,
            "expected_sparse_batches_by_family": dict(
                gates["expected_sparse_batches_by_family"]
            ),
        },
    }


def _current_policy_from_state(state: dict[str, Any]) -> dict[str, dict[str, float]]:
    policy = {}
    for key, row in state["regrets"].items():
        positive = {action: max(0.0, float(value)) for action, value in row.items()}
        total = math.fsum(positive.values())
        if total > 0.0:
            policy[key] = {action: value / total for action, value in positive.items()}
        else:
            uniform = 1.0 / len(row)
            policy[key] = {action: uniform for action in row}
    result = dict(sorted(policy.items()))
    if policy_digest(result) != state["current_policy_sha256"]:
        raise ValueError("checkpoint current policy reconstruction differs")
    return result


def _average_policy_from_state(state: dict[str, Any]) -> dict[str, dict[str, float]]:
    current = _current_policy_from_state(state)
    policy = {}
    for key, row in state["strategy_sums"].items():
        total = math.fsum(float(value) for value in row.values())
        policy[key] = (
            dict(current[key])
            if total <= 0.0
            else {action: float(value) / total for action, value in row.items()}
        )
    result = dict(sorted(policy.items()))
    if policy_digest(result) != state["average_policy_sha256"]:
        raise ValueError("checkpoint average policy reconstruction differs")
    return result


def _checkpoint(
    source: dict[str, Any],
    *,
    family: str,
    iteration: int,
) -> dict[str, Any]:
    row = next(
        value for value in source["wide_rows"] if value["range_family"] == family
    )
    checkpoint = next(
        value
        for value in row["checkpoints"]
        if int(value["iteration"]) == iteration
    )
    if axis_cfr_checkpoint_digest(checkpoint["state"]) != checkpoint["state_sha256"]:
        raise ValueError("source checkpoint state digest differs")
    return checkpoint


def _policy_distance(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> dict[str, float]:
    if set(first) != set(second):
        raise ValueError("policy schemas differ")
    errors = []
    total_variations = []
    for key in first:
        if set(first[key]) != set(second[key]):
            raise ValueError("policy action schemas differ")
        row_errors = [
            abs(float(first[key][action]) - float(second[key][action]))
            for action in first[key]
        ]
        errors.extend(row_errors)
        total_variations.append(0.5 * math.fsum(row_errors))
    return {
        "maximum_probability_error": max(errors, default=0.0),
        "mean_total_variation": (
            math.fsum(total_variations) / len(total_variations)
            if total_variations
            else 0.0
        ),
    }


def _source_policies(
    ladder: dict[str, Any],
    extension: dict[str, Any],
    *,
    family: str,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]], dict[str, dict[str, float]], bool]:
    average32_state = _checkpoint(
        ladder,
        family=family,
        iteration=32,
    )["state"]
    current48_state = _checkpoint(
        extension,
        family=family,
        iteration=48,
    )["state"]
    average64_state = _checkpoint(
        extension,
        family=family,
        iteration=64,
    )["state"]
    average32 = _average_policy_from_state(average32_state)
    current48 = _current_policy_from_state(current48_state)
    average64 = _average_policy_from_state(average64_state)
    identity = (
        policy_digest(average32) == average32_state["average_policy_sha256"]
        and policy_digest(current48) == current48_state["current_policy_sha256"]
        and policy_digest(average64) == average64_state["average_policy_sha256"]
    )
    return average32, current48, average64, identity


def _local_blocker_likelihoods(
    belief: FactorizedCardBelief,
    *,
    board: tuple[int, ...],
    target_seat: int,
) -> tuple[tuple[np.ndarray, ...], dict[str, Any]]:
    counts: dict[int, int] = {}
    for seat, hands in enumerate(belief.hands_by_player):
        if seat == target_seat:
            continue
        for hand in hands:
            for card in hand:
                counts[card] = counts.get(card, 0) + 1
    hands = belief.hands_by_player[target_seat]
    overlaps = tuple(
        counts.get(hand[0], 0) + counts.get(hand[1], 0) for hand in hands
    )
    maximum_overlap = max(overlaps)
    overlap_candidates = tuple(
        index for index, value in enumerate(overlaps) if value == maximum_overlap
    )
    strengths = tuple(evaluate_seven((*board, *hand)) for hand in hands)
    maximum_strength = max(strengths[index] for index in overlap_candidates)
    selected = min(
        (
            index
            for index in overlap_candidates
            if strengths[index] == maximum_strength
        ),
        key=lambda index: hands[index],
    )
    likelihoods = [np.ones(count, dtype=np.float64) for count in belief.hand_counts]
    likelihoods[target_seat][selected] = 2.0
    hand = hands[selected]
    return tuple(likelihoods), {
        "selected_seat": target_seat,
        "selected_hand_index": selected,
        "selected_hand": [format_card(hand[0]), format_card(hand[1])],
        "opponent_axis_card_overlap_count": (
            counts.get(hand[0], 0) + counts.get(hand[1], 0)
        ),
        "tie_rule": "maximum_overlap_then_strength_then_smallest_canonical_hand",
    }


def _strength_likelihoods(
    belief: FactorizedCardBelief,
    *,
    board: tuple[int, ...],
) -> tuple[tuple[np.ndarray, ...], dict[str, Any]]:
    likelihoods = []
    distinct_levels = []
    for hands in belief.hands_by_player:
        strengths = tuple(evaluate_seven((*board, *hand)) for hand in hands)
        ordered = tuple(sorted(set(strengths)))
        codes = np.ascontiguousarray(
            [ordered.index(strength) for strength in strengths],
            dtype=np.float64,
        )
        scaled = (
            np.zeros_like(codes)
            if len(ordered) == 1
            else codes / float(len(ordered) - 1)
        )
        likelihoods.append(np.ascontiguousarray(1.0 + scaled, dtype=np.float64))
        distinct_levels.append(len(ordered))
    return tuple(likelihoods), {
        "distinct_strength_levels_by_seat": distinct_levels,
        "tie_rule": "equal_showdown_strength_equal_likelihood",
    }


def build_target_belief(
    belief: FactorizedCardBelief,
    *,
    board: tuple[int, ...],
    shift: str,
    local_blocker_target_seat: int,
) -> tuple[FactorizedCardBelief, dict[str, Any]]:
    """Apply one frozen positive unary likelihood family."""

    if shift == "local_blocker_seat3_x2":
        likelihoods, detail = _local_blocker_likelihoods(
            belief,
            board=board,
            target_seat=local_blocker_target_seat,
        )
    elif shift == "all_seat_strength_1_to2":
        likelihoods, detail = _strength_likelihoods(belief, board=board)
    else:
        raise ValueError("unknown h32 target shift")
    target = belief
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    all_values = np.concatenate(likelihoods)
    descriptor = {
        "shift": shift,
        "likelihood_minimum": float(np.min(all_values)),
        "likelihood_maximum": float(np.max(all_values)),
        "likelihood_mean": float(np.mean(all_values)),
        "positive_likelihoods": bool(np.all(all_values > 0.0)),
        "hand_axes_identity": target.hands_by_player == belief.hands_by_player,
        **detail,
    }
    return target, descriptor


def _constant_train(shape: tuple[int, ...]) -> TensorTrain:
    return TensorTrain(
        shape=shape,
        cores=tuple(np.ones((1, size, 1), dtype=np.float64) for size in shape),
        decomposition_singular_values=tuple(
            np.ones(1, dtype=np.float64) for _ in shape[:-1]
        ),
    )


def _root_marginals(
    workspace: OpenModeFactorTTWorkspace,
    sparse: Any,
    *,
    maximum_feature_width_per_batch: int,
) -> tuple[tuple[np.ndarray, ...], float]:
    started = time.perf_counter()
    result = contract_sparse_open_mode_batch(
        workspace,
        sparse,
        (_constant_train(workspace.topology.base.hand_counts),),
        target_seats=tuple(range(len(workspace.topology.base.hand_counts))),
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    marginals = tuple(
        np.ascontiguousarray(target.reached_hand_distribution, dtype=np.float64)
        for target in result.trains[0].targets
    )
    return marginals, (time.perf_counter() - started) * 1000.0


def compare_acceptance(
    incumbent: dict[str, Any],
    candidate: dict[str, Any],
    *,
    payoff_span: float,
    normalized_guard: float,
) -> dict[str, Any]:
    """Return aggregate and per-seat non-worsening labels."""

    guard = payoff_span * normalized_guard
    improvement = float(incumbent["nash_conv"]) - float(candidate["nash_conv"])
    gain_deltas = [
        float(new) - float(old)
        for old, new in zip(
            incumbent["deviation_gains"],
            candidate["deviation_gains"],
            strict=True,
        )
    ]
    if improvement > guard:
        aggregate_decision = "accept"
    elif improvement < -guard:
        aggregate_decision = "reject"
    else:
        aggregate_decision = "abstain"
    constraint_failures = [
        seat for seat, delta in enumerate(gain_deltas) if delta > guard
    ]
    unilateral_accept = aggregate_decision == "accept" and not constraint_failures
    return {
        "guard_raw": guard,
        "raw_nash_conv_reduction": improvement,
        "normalized_nash_conv_reduction": improvement / payoff_span,
        "deviation_gain_deltas": gain_deltas,
        "maximum_deviation_gain_increase": max(gain_deltas),
        "aggregate_decision": aggregate_decision,
        "aggregate_accept": aggregate_decision == "accept",
        "unilateral_constraint_failures": constraint_failures,
        "unilateral_accept": unilateral_accept,
    }


def build_sequential_incumbents(
    baseline: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    payoff_span: float,
    normalized_guard: float,
) -> dict[str, Any]:
    """Replay aggregate and unilateral incumbents over search candidates."""

    aggregate_quality = baseline
    aggregate_id = "blueprint_average64"
    unilateral_quality = baseline
    unilateral_id = "blueprint_average64"
    trace = []
    for row in candidates:
        aggregate = compare_acceptance(
            aggregate_quality,
            row["quality"],
            payoff_span=payoff_span,
            normalized_guard=normalized_guard,
        )
        unilateral = compare_acceptance(
            unilateral_quality,
            row["quality"],
            payoff_span=payoff_span,
            normalized_guard=normalized_guard,
        )
        if aggregate["aggregate_accept"]:
            aggregate_quality = row["quality"]
            aggregate_id = row["candidate_id"]
        if unilateral["unilateral_accept"]:
            unilateral_quality = row["quality"]
            unilateral_id = row["candidate_id"]
        trace.append(
            {
                "candidate_id": row["candidate_id"],
                "aggregate_comparison": aggregate,
                "unilateral_comparison": unilateral,
                "resulting_aggregate_incumbent": aggregate_id,
                "resulting_unilateral_incumbent": unilateral_id,
            }
        )
    return {
        "trace": trace,
        "final_aggregate_incumbent": aggregate_id,
        "final_aggregate_normalized_nash_conv": float(
            aggregate_quality["normalized_nash_conv"]
        ),
        "final_unilateral_incumbent": unilateral_id,
        "final_unilateral_normalized_nash_conv": float(
            unilateral_quality["normalized_nash_conv"]
        ),
    }


def _finite_state(state: dict[str, Any]) -> bool:
    return all(
        math.isfinite(float(value))
        for table_name in ("regrets", "strategy_sums")
        for row in state[table_name].values()
        for value in row.values()
    )


def _evaluate_policy(
    *,
    topology: Any,
    workspace: OpenModeFactorTTWorkspace,
    sparse: Any,
    automata: Any,
    gpu: Any,
    hands_by_player: Any,
    policy: dict[str, dict[str, float]],
    label: str,
    payoff_span: float,
    maximum_feature_width_per_batch: int,
) -> dict[str, Any]:
    digest = policy_digest(policy)
    result = evaluate_leaf_adjoint_profile(
        topology,
        workspace,
        sparse,
        policy,
        automata,
        hands_by_player=hands_by_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        cupy_sparse=gpu,
    )
    return _quality_row(
        policy_kind=label,
        digest=digest,
        result=result,
        payoff_span=payoff_span,
        source="ADR-0099-live",
    )


def _run_target(
    *,
    parsed: dict[str, Any],
    family: str,
    shift: str,
    board: tuple[int, ...],
    source_belief: FactorizedCardBelief,
    topology: Any,
    source_workspace: OpenModeFactorTTWorkspace,
    sparse: Any,
    automata: Any,
    gpu: Any,
    source_marginals: tuple[np.ndarray, ...],
    policies: tuple[
        dict[str, dict[str, float]],
        dict[str, dict[str, float]],
        dict[str, dict[str, float]],
    ],
) -> dict[str, Any]:
    average32, current48, blueprint = policies
    target_belief, descriptor = build_target_belief(
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
    marginal_tvs = [
        0.5 * float(np.sum(np.abs(source - target)))
        for source, target in zip(
            source_marginals,
            target_marginals,
            strict=True,
        )
    ]
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
    payoff_span = float(topology.game.payoff_span)
    baseline_quality = _evaluate_policy(
        topology=topology,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        gpu=gpu,
        hands_by_player=target_belief.hands_by_player,
        policy=blueprint,
        label="blueprint_average64",
        payoff_span=payoff_span,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    candidates = []
    for candidate_id, policy in (
        ("control_average32", average32),
        ("control_current48", current48),
    ):
        quality = _evaluate_policy(
            topology=topology,
            workspace=target_workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            hands_by_player=target_belief.hands_by_player,
            policy=policy,
            label=candidate_id,
            payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "provenance": "checkpoint_control",
                "cumulative_search_ms": 0.0,
                "policy_statistics": policy_statistics(policy),
                "quality": quality,
                "baseline_comparison": compare_acceptance(
                    baseline_quality,
                    quality,
                    payoff_span=payoff_span,
                    normalized_guard=parsed["acceptance_guard_normalized"],
                ),
                "state": None,
            }
        )

    solver = _solver(
        parsed=parsed,
        belief=target_belief,
        topology=topology,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    solver.warm_start(
        blueprint,
        parsed["warm_regret_mass_payoff_fraction"] * payoff_span,
    )
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    step_rows = []
    cumulative_search_ms = 0.0
    checkpoint_identity = True
    search_candidates = []
    context = {
        "board": parsed["board"],
        "range_family": family,
        "target_shift": shift,
        "blueprint_point": parsed["blueprint_point"],
        "hands_per_player": parsed["wide_hands_per_player"],
    }
    provenance = {
        "audit": "ADR-0099",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "extension_source_sha256": _sha256(_EXTENSION_SOURCE),
    }
    for iteration in range(1, parsed["search_checkpoint_iterations"][-1] + 1):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        cumulative_search_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("warm-search step has no telemetry")
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_host_peak_numeric_bytes": (
                    max(
                        row.maximum_terminal_peak_numeric_bytes
                        for row in work.traversers
                    )
                    + solver.accumulator_numeric_bytes()
                    + sum(
                        value.numeric_bytes
                        for value in {
                            id(automaton): automaton
                            for library in automata
                            for automaton in library.values()
                        }.values()
                    )
                ),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
            }
        )
        if iteration not in parsed["search_checkpoint_iterations"]:
            continue
        policy = solver.average_strategy()
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
        checkpoint_identity = checkpoint_identity and (
            axis_cfr_checkpoint_digest(json.loads(rendered)) == state["state_sha256"]
            and policy_digest(policy) == state["average_policy_sha256"]
        )
        candidate_id = f"search_average{iteration}"
        quality = _evaluate_policy(
            topology=topology,
            workspace=target_workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            hands_by_player=target_belief.hands_by_player,
            policy=policy,
            label=candidate_id,
            payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        row = {
            "candidate_id": candidate_id,
            "provenance": "warm_dcfr_average",
            "search_iteration": iteration,
            "cumulative_search_ms": cumulative_search_ms,
            "policy_statistics": policy_statistics(policy),
            "quality": quality,
            "baseline_comparison": compare_acceptance(
                baseline_quality,
                quality,
                payoff_span=payoff_span,
                normalized_guard=parsed["acceptance_guard_normalized"],
            ),
            "state_sha256": state["state_sha256"],
            "state_json_bytes": len(rendered.encode("utf-8")),
            "state": state,
        }
        candidates.append(row)
        search_candidates.append(row)

    candidate_ids = tuple(row["candidate_id"] for row in candidates)
    if candidate_ids != parsed["candidate_order"]:
        raise AssertionError("warm-search candidate order differs from ADR-0099")
    primary_id = f"search_average{parsed['primary_search_iteration']}"
    primary = next(row for row in candidates if row["candidate_id"] == primary_id)
    primary_comparison = primary["baseline_comparison"]
    primary_solve_ms = float(primary["cumulative_search_ms"])
    primary_evaluation_ms = float(primary["quality"]["wall_ms"])
    baseline_evaluation_ms = float(baseline_quality["wall_ms"])
    primary_costs = {
        "blind_search_ms": primary_solve_ms,
        "verified_precompiled_ms": primary_solve_ms + primary_evaluation_ms,
        "verified_one_shot_ms": (
            target_compile_ms
            + baseline_evaluation_ms
            + primary_solve_ms
            + primary_evaluation_ms
        ),
    }
    primary_arms = {
        "blind": {
            "deploy": True,
            "normalized_reduction": primary_comparison[
                "normalized_nash_conv_reduction"
            ],
        },
        "aggregate_exact": {
            "deploy": primary_comparison["aggregate_accept"],
            "normalized_reduction": (
                primary_comparison["normalized_nash_conv_reduction"]
                if primary_comparison["aggregate_accept"]
                else 0.0
            ),
        },
        "unilateral_pareto": {
            "deploy": primary_comparison["unilateral_accept"],
            "normalized_reduction": (
                primary_comparison["normalized_nash_conv_reduction"]
                if primary_comparison["unilateral_accept"]
                else 0.0
            ),
        },
    }
    finite = (
        bool(baseline_quality["finite"])
        and all(bool(row["quality"]["finite"]) for row in candidates)
        and all(
            row["state"] is None or _finite_state(row["state"])
            for row in candidates
        )
    )
    return {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "target_workspace_compile_ms": target_compile_ms,
        "target_axes_identity": (
            target_belief.hands_by_player == source_belief.hands_by_player
            and target_workspace.topology is source_workspace.topology
        ),
        "support_preserving_target": descriptor["positive_likelihoods"],
        "information_sets": len(solver.information_schema()),
        "hand_action_entries": sum(
            len(actions) for actions in solver.information_schema().values()
        ),
        "blueprint_policy_sha256": policy_digest(blueprint),
        "blueprint_quality": baseline_quality,
        "warm_start_distance": warm_distance,
        "step_rows": step_rows,
        "candidates": candidates,
        "search_candidates": len(search_candidates),
        "checkpoint_state_digest_identity": checkpoint_identity,
        "sequential_incumbents": build_sequential_incumbents(
            baseline_quality,
            search_candidates,
            payoff_span=payoff_span,
            normalized_guard=parsed["acceptance_guard_normalized"],
        ),
        "primary_candidate_id": primary_id,
        "primary_comparison": primary_comparison,
        "primary_costs": primary_costs,
        "primary_arms": primary_arms,
        "finite_states_policies_and_quality": finite,
    }


def _run_family(
    *,
    parsed: dict[str, Any],
    ladder: dict[str, Any],
    extension: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, Any]:
    source_belief, topology, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
    )
    source_workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    source_marginals, source_marginal_ms = _root_marginals(
        source_workspace,
        sparse,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    average32, current48, blueprint, source_policy_identity = _source_policies(
        ladder,
        extension,
        family=family,
    )
    targets = []
    for shift in parsed["target_shifts"]:
        targets.append(
            _run_target(
                parsed=parsed,
                family=family,
                shift=shift,
                board=board,
                source_belief=source_belief,
                topology=topology,
                source_workspace=source_workspace,
                sparse=sparse,
                automata=automata,
                gpu=gpu,
                source_marginals=source_marginals,
                policies=(average32, current48, blueprint),
            )
        )
        gc.collect()
    return {
        "range_family": family,
        "source_policy_digest_identity": source_policy_identity,
        "source_policy_digests": {
            "control_average32": policy_digest(average32),
            "control_current48": policy_digest(current48),
            "blueprint_average64": policy_digest(blueprint),
        },
        "source_workspace_timing": workspace_timing,
        "source_marginal_measurement_ms": source_marginal_ms,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "targets": targets,
    }


def _rate(numerator: float, milliseconds: float) -> float:
    return numerator / milliseconds if milliseconds > 0.0 else 0.0


def run_h32_warm_search_acceptance_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_h32_warm_search_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0099")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0099")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0099")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0099")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0099 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0099")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")
    width_source = json.loads(_WIDTH_SOURCE.read_text(encoding="utf-8"))
    if int(width_source["aggregate"]["selected_width"]) != 384:
        raise ValueError("ADR-0096 width source does not select 384")

    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    family_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        gc.collect()
        family_rows.append(
            _run_family(
                parsed=parsed,
                ladder=ladder,
                extension=extension,
                board=board,
                family=family,
            )
        )
    target_rows = [target for family in family_rows for target in family["targets"]]
    candidate_rows = [
        candidate for target in target_rows for candidate in target["candidates"]
    ]
    quality_rows = [
        target["blueprint_quality"] for target in target_rows
    ] + [candidate["quality"] for candidate in candidate_rows]
    step_rows = [step for target in target_rows for step in target["step_rows"]]
    primary_rows = target_rows
    blind_reduction = math.fsum(
        float(row["primary_arms"]["blind"]["normalized_reduction"])
        for row in primary_rows
    )
    aggregate_reduction = math.fsum(
        float(row["primary_arms"]["aggregate_exact"]["normalized_reduction"])
        for row in primary_rows
    )
    unilateral_reduction = math.fsum(
        float(row["primary_arms"]["unilateral_pareto"]["normalized_reduction"])
        for row in primary_rows
    )
    blind_ms = math.fsum(
        float(row["primary_costs"]["blind_search_ms"]) for row in primary_rows
    )
    verified_precompiled_ms = math.fsum(
        float(row["primary_costs"]["verified_precompiled_ms"])
        for row in primary_rows
    )
    verified_one_shot_ms = math.fsum(
        float(row["primary_costs"]["verified_one_shot_ms"])
        for row in primary_rows
    )
    primary = {
        "candidate_id": f"search_average{parsed['primary_search_iteration']}",
        "targets": len(primary_rows),
        "blind_normalized_reduction": blind_reduction,
        "aggregate_accepted_targets": sum(
            bool(row["primary_arms"]["aggregate_exact"]["deploy"])
            for row in primary_rows
        ),
        "aggregate_normalized_reduction": aggregate_reduction,
        "unilateral_accepted_targets": sum(
            bool(row["primary_arms"]["unilateral_pareto"]["deploy"])
            for row in primary_rows
        ),
        "unilateral_normalized_reduction": unilateral_reduction,
        "blind_search_ms": blind_ms,
        "verified_precompiled_ms": verified_precompiled_ms,
        "verified_one_shot_ms": verified_one_shot_ms,
        "blind_normalized_reduction_per_ms": _rate(blind_reduction, blind_ms),
        "aggregate_precompiled_normalized_reduction_per_ms": _rate(
            aggregate_reduction,
            verified_precompiled_ms,
        ),
        "aggregate_one_shot_normalized_reduction_per_ms": _rate(
            aggregate_reduction,
            verified_one_shot_ms,
        ),
        "unilateral_precompiled_normalized_reduction_per_ms": _rate(
            unilateral_reduction,
            verified_precompiled_ms,
        ),
    }
    primary["aggregate_verification_break_even_ms"] = (
        aggregate_reduction * blind_ms / blind_reduction - blind_ms
        if blind_reduction > 0.0 and aggregate_reduction >= 0.0
        else None
    )
    hypotheses = {
        "blind_primary_reduction_positive": blind_reduction > 0.0,
        "aggregate_precompiled_rate_beats_blind": primary[
            "aggregate_precompiled_normalized_reduction_per_ms"
        ]
        > primary["blind_normalized_reduction_per_ms"],
        "unilateral_acceptance_at_least_one_quarter": primary[
            "unilateral_accepted_targets"
        ]
        / len(primary_rows)
        >= 0.25,
        "unilateral_reduction_positive": unilateral_reduction > 0.0,
    }
    gates = parsed["gates"]
    aggregate = {
        "maximum_target_workspace_compile_ms": max(
            float(row["target_workspace_compile_ms"]) for row in target_rows
        ),
        "minimum_target_mean_marginal_tv": min(
            float(row["target_descriptor"]["mean_marginal_total_variation"])
            for row in target_rows
        ),
        "maximum_warm_start_probability_error": max(
            float(row["warm_start_distance"]["maximum_probability_error"])
            for row in target_rows
        ),
        "maximum_warm_start_mean_tv": max(
            float(row["warm_start_distance"]["mean_total_variation"])
            for row in target_rows
        ),
        "maximum_training_step_ms": max(float(row["wall_ms"]) for row in step_rows),
        "maximum_quality_evaluation_ms": max(
            float(row["wall_ms"]) for row in quality_rows
        ),
        "maximum_host_peak_numeric_bytes": max(
            max(int(row["maximum_host_peak_numeric_bytes"]) for row in quality_rows),
            max(int(row["maximum_host_peak_numeric_bytes"]) for row in step_rows),
        ),
        "maximum_gpu_pool_bytes": max(
            max(int(row["maximum_gpu_pool_bytes"]) for row in quality_rows),
            max(int(row["maximum_gpu_pool_bytes"]) for row in step_rows),
        ),
        "maximum_quality_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in quality_rows
        ),
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results = {
        "target_row_count": len(target_rows) == gates["expected_target_rows"],
        "target_rows_per_family": all(
            len(row["targets"]) == gates["expected_target_rows_per_family"]
            for row in family_rows
        ),
        "candidate_row_count": all(
            len(row["candidates"]) == gates["expected_candidate_rows_per_target"]
            for row in target_rows
        ),
        "search_candidate_count": all(
            int(row["search_candidates"])
            == gates["expected_search_candidates_per_target"]
            for row in target_rows
        ),
        "final_search_iteration": all(
            int(row["step_rows"][-1]["iteration"])
            == gates["expected_final_search_iteration"]
            for row in target_rows
        ),
        "wide_schema": all(
            int(row["information_sets"]) == gates["expected_wide_information_sets"]
            and int(row["hand_action_entries"])
            == gates["expected_wide_hand_action_entries"]
            for row in target_rows
        ),
        "sparse_batch_identity": all(
            all(
                int(step["terminal_sparse_batches"])
                == int(
                    gates["expected_sparse_batches_by_family"][row["range_family"]]
                )
                for step in row["step_rows"]
            )
            and all(
                int(quality["terminal_sparse_batches"])
                == int(
                    gates["expected_sparse_batches_by_family"][row["range_family"]]
                )
                for quality in (
                    row["blueprint_quality"],
                    *(candidate["quality"] for candidate in row["candidates"]),
                )
            )
            for row in target_rows
        ),
        "source_policy_digest_identity": all(
            bool(row["source_policy_digest_identity"]) for row in family_rows
        )
        == gates["require_source_policy_digest_identity"],
        "target_axes_identity": all(
            bool(row["target_axes_identity"]) for row in target_rows
        )
        == gates["require_target_axes_identity"],
        "support_preserving_targets": all(
            bool(row["support_preserving_target"]) for row in target_rows
        )
        == gates["require_support_preserving_targets"],
        "likelihood_bounds_identity": all(
            float(row["target_descriptor"]["likelihood_minimum"])
            == parsed["likelihood_minimum"]
            and float(row["target_descriptor"]["likelihood_maximum"])
            == parsed["likelihood_maximum"]
            for row in target_rows
        )
        == gates["require_likelihood_bounds_identity"],
        "target_marginal_shift": aggregate["minimum_target_mean_marginal_tv"]
        >= gates["minimum_target_mean_marginal_tv"],
        "warm_start_probability_identity": aggregate[
            "maximum_warm_start_probability_error"
        ]
        <= gates["maximum_warm_start_probability_error"],
        "warm_start_tv_identity": aggregate["maximum_warm_start_mean_tv"]
        <= gates["maximum_warm_start_mean_tv"],
        "checkpoint_state_identity": all(
            bool(row["checkpoint_state_digest_identity"]) for row in target_rows
        )
        == gates["require_checkpoint_state_digest_identity"],
        "primary_candidate_identity": all(
            row["primary_candidate_id"]
            == f"search_average{parsed['primary_search_iteration']}"
            for row in target_rows
        )
        == gates["require_primary_candidate_identity"],
        "training_latency": aggregate["maximum_training_step_ms"]
        <= gates["maximum_training_step_ms"],
        "quality_latency": aggregate["maximum_quality_evaluation_ms"]
        <= gates["maximum_quality_evaluation_ms"],
        "target_workspace_compile_latency": aggregate[
            "maximum_target_workspace_compile_ms"
        ]
        <= gates["maximum_target_workspace_compile_ms"],
        "host_peak": aggregate["maximum_host_peak_numeric_bytes"]
        <= gates["maximum_host_peak_numeric_bytes"],
        "gpu_peak": aggregate["maximum_gpu_pool_bytes"]
        <= gates["maximum_gpu_pool_bytes"],
        "quality_zero_sum": aggregate["maximum_quality_zero_sum_residual"]
        <= gates["maximum_quality_zero_sum_residual"],
        "finite_states_policies_and_quality": all(
            bool(row["finite_states_policies_and_quality"]) for row in target_rows
        )
        == gates["require_finite_states_policies_and_quality"],
        "total_wall": aggregate["wall_seconds_before_result_serialization"]
        <= gates["maximum_total_audit_seconds"],
    }
    gate_results["passed"] = all(gate_results.values())
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "h32_real_blueprint_warm_search_exact_acceptance",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "ladder_source_sha256": _sha256(_LADDER_SOURCE),
        "extension_source_sha256": _sha256(_EXTENSION_SOURCE),
        "width_source_sha256": _sha256(_WIDTH_SOURCE),
        "family_rows": family_rows,
        "primary": primary,
        "hypotheses": hypotheses,
        "aggregate": aggregate,
        "gates": gate_results,
        "counts": {
            "family_rows": len(family_rows),
            "target_rows": len(target_rows),
            "candidate_rows": len(candidate_rows),
        },
        "timing": {
            "wall_seconds": time.perf_counter() - started,
            "cupy_import_ms": cupy_import_ms,
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "gpu_name": str(name),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "limitations": [
            "The strategy matrix is one board, two generated beliefs, two support-preserving shifts, and four target cases.",
            "Exact leaf-adjoint verification is an offline teacher measured in tens of seconds, not an online acceptance kernel.",
            "The signed clean-fringe reader is excluded because no h32 policy-conditioned TT cache has passed.",
            "Unilateral non-worsening is not coalition safety or a multiplayer equilibrium theorem.",
            "Only warm DCFR average candidates through iteration four are searched; no scheduler is fitted.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_warm_search_acceptance_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "h32 warm-search acceptance audit: "
        f"targets={result['counts']['target_rows']}, "
        f"blind_reduction={result['primary']['blind_normalized_reduction']:.6g}, "
        f"unilateral_accepts={result['primary']['unilateral_accepted_targets']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
