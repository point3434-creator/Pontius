"""Exact leaf-adjoint evaluation through the resident CuPy contraction path."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any, Mapping

import numpy as np

from .fixed_envelope_verifier import _stop_reason, math_is_positive_finite
from .game import Action, TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_policy_tt import (
    PolicyProbabilityTape,
    compile_policy_probability_tape,
)
from .leaf_adjoint_cfr import _parent_metadata, _target_omitted_path_factors
from .leaf_adjoint_evaluation import _external_axes, _required, _sum_children
from .public_policy_tt import _information_key, _terminal_keys_by_slot
from .real_policy import policy_digest
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
    ResidentHeterogeneousLeafWork,
    contract_resident_heterogeneous_leaf_terms,
)


@dataclass(frozen=True, slots=True)
class ResidentLeafAdjointSeatEvaluation:
    target_player: int
    profile_utility: float
    best_response_value: float
    deviation_gain: float
    best_response_actions: dict[str, Action]
    exact_action_ties: int
    minimum_action_gap: float
    terminal_contractions: int
    terminal_sparse_batches: int
    terminal_contraction_ms: float
    reverse_evaluation_ms: float
    wall_ms: float
    maximum_terminal_middle_rank: int
    maximum_terminal_peak_numeric_bytes: int
    maximum_gpu_pool_total_bytes: int
    resident_work: ResidentHeterogeneousLeafWork


def evaluate_resident_leaf_adjoint_seat(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    target_player: int,
    belief_cache: CuPyResidentBeliefCache,
    automaton_cache: CuPyResidentAutomatonCache,
    cupy_sparse: Any,
    hands_by_player: tuple[tuple[Any, ...], ...] | None = None,
    maximum_feature_width_per_batch: int = 384,
) -> ResidentLeafAdjointSeatEvaluation:
    """Evaluate one exact fixed-policy seat with resident terminal folding."""

    wall_started = time.perf_counter()
    axes = _external_axes(layout, workspace, hands_by_player)
    if isinstance(target_player, bool) or target_player not in range(layout.num_players):
        raise ValueError("resident leaf-adjoint target is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("resident leaf-adjoint topology and workspace differ")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("resident leaf-adjoint probability tape differs from tree")
    terminal_keys = _terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("resident leaf-adjoint automata differ from payoff groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("resident leaf-adjoint automata differ from hand axes")

    parents, parent_actions = _parent_metadata(layout)
    terms = tuple(
        HeterogeneousLeafTerm(
            key=node_index,
            automaton=terminal_automata[terminal_keys[node.terminal_slot]],
            mode_factors=_target_omitted_path_factors(
                layout,
                probabilities,
                parents,
                parent_actions,
                terminal_node=node_index,
                traverser=target_player,
                shape=shape,
            ),
        )
        for node_index, node in enumerate(layout.nodes)
        if node.player == TERMINAL_PLAYER
    )
    contraction_started = time.perf_counter()
    contraction = contract_resident_heterogeneous_leaf_terms(
        workspace,
        sparse,
        terms,
        target_seat=target_player,
        belief_cache=belief_cache,
        automaton_cache=automaton_cache,
        cupy_sparse=cupy_sparse,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    contraction_ms = (time.perf_counter() - contraction_started) * 1000.0

    profile_values: list[np.ndarray | None] = [None] * layout.public_node_count
    response_values: list[np.ndarray | None] = [None] * layout.public_node_count
    for node_index, values in contraction.values:
        terminal = np.array(
            values.root_normalized_numerators,
            dtype=np.float64,
            order="C",
            copy=True,
        )
        profile_values[node_index] = terminal
        response_values[node_index] = terminal

    reverse_started = time.perf_counter()
    selected_actions: dict[str, Action] = {}
    exact_ties = 0
    minimum_gap = float("inf")
    target_hands = axes[target_player]
    hand_indices = np.arange(len(target_hands), dtype=np.intp)
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continue
        profile_children = tuple(_required(profile_values[child]) for child in node.children)
        response_children = tuple(
            _required(response_values[child]) for child in node.children
        )
        if node.player != target_player:
            profile_values[node_index] = _sum_children(profile_children)
            response_values[node_index] = _sum_children(response_children)
            continue

        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise ValueError("resident target node has no policy probabilities")
        profile_scores = np.ascontiguousarray(
            np.column_stack(profile_children),
            dtype=np.float64,
        )
        response_scores = np.ascontiguousarray(
            np.column_stack(response_children),
            dtype=np.float64,
        )
        if not np.all(np.isfinite(profile_scores)) or not np.all(
            np.isfinite(response_scores)
        ):
            raise FloatingPointError("resident evaluation produced nonfinite scores")
        profile_values[node_index] = np.einsum(
            "ha,ha->h",
            node_probabilities,
            profile_scores,
            optimize=True,
        )
        selected = np.argmax(response_scores, axis=1)
        response_values[node_index] = np.ascontiguousarray(
            response_scores[hand_indices, selected],
            dtype=np.float64,
        )
        if response_scores.shape[1] > 1:
            ordered = np.partition(response_scores, -2, axis=1)
            gaps = ordered[:, -1] - ordered[:, -2]
            exact_ties += int(np.count_nonzero(gaps == 0.0))
            minimum_gap = min(minimum_gap, float(np.min(gaps)))
        for hand_index, hand in enumerate(target_hands):
            key = _information_key(layout, target_player, hand, node.history)
            action = node.actions[int(selected[hand_index])]
            previous = selected_actions.setdefault(key, action)
            if previous != action:
                raise ValueError("resident response violates information consistency")

    profile_root = _required(profile_values[0])
    response_root = _required(response_values[0])
    profile_utility = fsum(float(value) for value in profile_root)
    best_response_value = fsum(float(value) for value in response_root)
    work = contraction.work
    return ResidentLeafAdjointSeatEvaluation(
        target_player=target_player,
        profile_utility=profile_utility,
        best_response_value=best_response_value,
        deviation_gain=max(0.0, best_response_value - profile_utility),
        best_response_actions=selected_actions,
        exact_action_ties=exact_ties,
        minimum_action_gap=0.0 if minimum_gap == float("inf") else minimum_gap,
        terminal_contractions=len(terms),
        terminal_sparse_batches=work.batches,
        terminal_contraction_ms=contraction_ms,
        reverse_evaluation_ms=(time.perf_counter() - reverse_started) * 1000.0,
        wall_ms=(time.perf_counter() - wall_started) * 1000.0,
        maximum_terminal_middle_rank=work.maximum_middle_rank,
        maximum_terminal_peak_numeric_bytes=work.estimated_peak_host_numeric_bytes,
        maximum_gpu_pool_total_bytes=work.maximum_gpu_pool_total_bytes,
        resident_work=work,
    )


def verify_resident_leaf_adjoint_candidate(
    *,
    candidate_id: str,
    layout: Any,
    workspace: Any,
    sparse: Any,
    policy: dict[str, dict[str, float]],
    terminal_automata: tuple[dict[str, Any], ...],
    hands_by_player: tuple[tuple[Any, ...], ...],
    blueprint_deviation_gains: tuple[float, ...],
    best_complete_nash_conv: float,
    payoff_span: float,
    raw_guard: float,
    seat_order: tuple[int, ...],
    belief_cache: CuPyResidentBeliefCache,
    automaton_caches: tuple[CuPyResidentAutomatonCache, ...],
    cupy_sparse: Any,
    maximum_feature_width_per_batch: int,
) -> dict[str, Any]:
    """Run the fixed-envelope seat prefix through the resident evaluator."""

    players = layout.num_players
    if len(seat_order) != players or tuple(sorted(seat_order)) != tuple(range(players)):
        raise ValueError("resident verifier seat order must contain every seat")
    if len(blueprint_deviation_gains) != players:
        raise ValueError("resident blueprint vector has the wrong player count")
    if len(automaton_caches) != players:
        raise ValueError("resident verifier requires one cache per seat")
    if not math_is_positive_finite(payoff_span):
        raise ValueError("resident verifier payoff span must be positive and finite")
    if raw_guard < 0.0 or not np.isfinite(raw_guard):
        raise ValueError("resident verifier guard must be finite and nonnegative")
    if best_complete_nash_conv < 0.0 or not np.isfinite(best_complete_nash_conv):
        raise ValueError("resident incumbent NashConv must be finite and nonnegative")

    wall_started = time.perf_counter()
    probability_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(layout, hands_by_player, policy)
    probability_compile_ms = (time.perf_counter() - probability_started) * 1000.0
    digest = policy_digest(policy)
    rows = []
    partial = 0.0
    stop_reason = None
    stop_seat = None
    for seat in seat_order:
        evaluated = evaluate_resident_leaf_adjoint_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            terminal_automata[seat],
            target_player=seat,
            belief_cache=belief_cache,
            automaton_cache=automaton_caches[seat],
            cupy_sparse=cupy_sparse,
            hands_by_player=hands_by_player,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        gain = max(0.0, evaluated.best_response_value - evaluated.profile_utility)
        partial += gain
        work = evaluated.resident_work
        row = {
            "target_player": seat,
            "profile_utility": evaluated.profile_utility,
            "best_response_value": evaluated.best_response_value,
            "deviation_gain": gain,
            "partial_nash_conv": partial,
            "exact_action_ties": evaluated.exact_action_ties,
            "minimum_action_gap": evaluated.minimum_action_gap,
            "terminal_contractions": evaluated.terminal_contractions,
            "terminal_sparse_batches": evaluated.terminal_sparse_batches,
            "terminal_contraction_ms": evaluated.terminal_contraction_ms,
            "reverse_evaluation_ms": evaluated.reverse_evaluation_ms,
            "wall_ms": evaluated.wall_ms,
            "maximum_terminal_middle_rank": evaluated.maximum_terminal_middle_rank,
            "maximum_terminal_peak_numeric_bytes": (
                evaluated.maximum_terminal_peak_numeric_bytes
            ),
            "maximum_gpu_pool_total_bytes": evaluated.maximum_gpu_pool_total_bytes,
            "factor_prepare_ms": work.factor_prepare_ms,
            "factor_upload_ms": work.factor_upload_ms,
            "product_generation_gpu_ms": work.product_generation_gpu_ms,
            "resident_pipeline_gpu_ms": work.resident_pipeline_gpu_ms,
            "device_to_host_ms": work.device_to_host_ms,
            "hand_fold_ms": work.hand_fold_ms,
            "per_call_host_to_device_bytes": work.per_call_host_to_device_bytes,
            "per_call_device_to_host_bytes": work.per_call_device_to_host_bytes,
            "legacy_equivalent_host_to_device_bytes": (
                work.legacy_equivalent_host_to_device_bytes
            ),
            "legacy_equivalent_device_to_host_bytes": (
                work.legacy_equivalent_device_to_host_bytes
            ),
            "per_call_device_product_bytes": work.per_call_device_product_bytes,
            "per_call_device_record_bytes": work.per_call_device_record_bytes,
            "maximum_batch_scratch_numeric_bytes": (
                work.maximum_batch_scratch_numeric_bytes
            ),
        }
        rows.append(row)
        stop_reason = _stop_reason(
            seat=seat,
            gain=gain,
            partial_nash_conv=partial,
            blueprint_gain=float(blueprint_deviation_gains[seat]),
            best_complete_nash_conv=best_complete_nash_conv,
            raw_guard=raw_guard,
        )
        if stop_reason is not None:
            stop_seat = seat
            break

    complete = stop_reason is None
    quality = None
    if complete:
        by_seat = {int(row["target_player"]): row for row in rows}
        utilities = tuple(float(by_seat[seat]["profile_utility"]) for seat in range(players))
        responses = tuple(
            float(by_seat[seat]["best_response_value"]) for seat in range(players)
        )
        gains = tuple(float(by_seat[seat]["deviation_gain"]) for seat in range(players))
        nash_conv = fsum(gains)
        quality = {
            "policy_sha256": digest,
            "utilities": utilities,
            "best_response_values": responses,
            "deviation_gains": gains,
            "nash_conv": nash_conv,
            "normalized_nash_conv": nash_conv / payoff_span,
            "zero_sum_residual": abs(fsum(utilities)),
        }
    return {
        "candidate_id": candidate_id,
        "policy_sha256": digest,
        "probability_compile_ms": probability_compile_ms,
        "seat_rows": rows,
        "evaluated_seats": [int(row["target_player"]) for row in rows],
        "evaluated_seat_count": len(rows),
        "partial_nash_conv": partial,
        "stop_reason": "complete" if complete else stop_reason,
        "stop_seat": stop_seat,
        "complete": complete,
        "quality": quality,
        "terminal_contraction_ms": fsum(
            float(row["terminal_contraction_ms"]) for row in rows
        ),
        "reverse_evaluation_ms": fsum(
            float(row["reverse_evaluation_ms"]) for row in rows
        ),
        "terminal_sparse_batches": sum(
            int(row["terminal_sparse_batches"]) for row in rows
        ),
        "resident_pipeline_gpu_ms": fsum(
            float(row["resident_pipeline_gpu_ms"]) for row in rows
        ),
        "per_call_host_to_device_bytes": sum(
            int(row["per_call_host_to_device_bytes"]) for row in rows
        ),
        "per_call_device_to_host_bytes": sum(
            int(row["per_call_device_to_host_bytes"]) for row in rows
        ),
        "legacy_equivalent_host_to_device_bytes": sum(
            int(row["legacy_equivalent_host_to_device_bytes"]) for row in rows
        ),
        "legacy_equivalent_device_to_host_bytes": sum(
            int(row["legacy_equivalent_device_to_host_bytes"]) for row in rows
        ),
        "maximum_host_peak_numeric_bytes": max(
            int(row["maximum_terminal_peak_numeric_bytes"]) for row in rows
        ),
        "maximum_gpu_pool_bytes": max(
            int(row["maximum_gpu_pool_total_bytes"]) for row in rows
        ),
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
    }
