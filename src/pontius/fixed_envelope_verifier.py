"""Exact acceptance-aware verification for a fixed blueprint safety envelope."""

from __future__ import annotations

from math import fsum
import time
from typing import Any, Iterable

import numpy as np

from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import _parent_metadata, _target_omitted_path_factors
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_seat
from .game import TERMINAL_PLAYER
from .public_policy_tt import _terminal_keys_by_slot
from .real_policy import policy_digest


def _stop_reason(
    *,
    seat: int,
    gain: float,
    partial_nash_conv: float,
    blueprint_gain: float,
    best_complete_nash_conv: float,
    raw_guard: float,
) -> str | None:
    if gain > blueprint_gain + raw_guard:
        return "blueprint_cap"
    if partial_nash_conv > best_complete_nash_conv + raw_guard:
        return "objective_lower_bound"
    return None


def simulate_fixed_envelope_verifier(
    blueprint: dict[str, Any],
    ordered_candidates: Iterable[dict[str, Any]],
    *,
    seat_order: tuple[int, ...],
    raw_guard: float,
) -> dict[str, Any]:
    """Replay exact stopping from already measured per-seat quality vectors."""

    players = len(blueprint["quality"]["deviation_gains"])
    _validate_seat_order(seat_order, players=players)
    best_complete = float(blueprint["quality"]["nash_conv"])
    completed: list[dict[str, Any]] = []
    rows = []
    for candidate in ordered_candidates:
        gains = tuple(float(value) for value in candidate["quality"]["deviation_gains"])
        if len(gains) != players:
            raise ValueError("candidate acceptance vector has the wrong player count")
        partial = 0.0
        stop_reason = None
        stop_seat = None
        evaluated = []
        for seat in seat_order:
            gain = gains[seat]
            partial += gain
            evaluated.append(seat)
            stop_reason = _stop_reason(
                seat=seat,
                gain=gain,
                partial_nash_conv=partial,
                blueprint_gain=float(
                    blueprint["quality"]["deviation_gains"][seat]
                ),
                best_complete_nash_conv=best_complete,
                raw_guard=raw_guard,
            )
            if stop_reason is not None:
                stop_seat = seat
                break
        complete = stop_reason is None
        if complete:
            completed.append(candidate)
            best_complete = min(
                best_complete,
                float(candidate["quality"]["nash_conv"]),
            )
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "policy_sha256": candidate["quality"]["policy_sha256"],
                "evaluated_seats": evaluated,
                "evaluated_seat_count": len(evaluated),
                "partial_nash_conv": partial,
                "stop_reason": "complete" if complete else stop_reason,
                "stop_seat": stop_seat,
                "complete": complete,
                "best_complete_nash_conv_after_candidate": best_complete,
            }
        )
    selection = select_fixed_blueprint_envelope(
        blueprint,
        completed,
        raw_guard=raw_guard,
    )
    return {
        "candidate_rows": rows,
        "candidate_count": len(rows),
        "evaluated_seat_count": sum(row["evaluated_seat_count"] for row in rows),
        "complete_candidate_count": len(completed),
        "selection": selection,
    }


def verify_leaf_adjoint_candidate(
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
    maximum_feature_width_per_batch: int,
    cupy_sparse: Any | None,
) -> dict[str, Any]:
    """Evaluate only the exact seat prefix needed to classify one candidate."""

    players = layout.num_players
    _validate_seat_order(seat_order, players=players)
    if len(blueprint_deviation_gains) != players:
        raise ValueError("blueprint acceptance vector has the wrong player count")
    if not math_is_positive_finite(payoff_span):
        raise ValueError("verifier payoff span must be positive and finite")
    if raw_guard < 0.0 or not np.isfinite(raw_guard):
        raise ValueError("verifier guard must be finite and nonnegative")
    if best_complete_nash_conv < 0.0 or not np.isfinite(best_complete_nash_conv):
        raise ValueError("verifier incumbent NashConv must be finite and nonnegative")

    wall_started = time.perf_counter()
    probability_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        policy,
    )
    probability_compile_ms = (time.perf_counter() - probability_started) * 1000.0
    digest = policy_digest(policy)
    rows = []
    partial = 0.0
    stop_reason = None
    stop_seat = None
    for seat in seat_order:
        evaluated = evaluate_leaf_adjoint_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            terminal_automata[seat],
            target_player=seat,
            hands_by_player=hands_by_player,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            cupy_sparse=cupy_sparse,
        )
        gain = max(0.0, evaluated.best_response_value - evaluated.profile_utility)
        partial += gain
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
            "maximum_gpu_pool_total_bytes": (
                evaluated.maximum_gpu_pool_total_bytes
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
    wall_ms = (time.perf_counter() - wall_started) * 1000.0
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
        "maximum_host_peak_numeric_bytes": max(
            int(row["maximum_terminal_peak_numeric_bytes"]) for row in rows
        ),
        "maximum_gpu_pool_bytes": max(
            int(row["maximum_gpu_pool_total_bytes"]) for row in rows
        ),
        "wall_ms": wall_ms,
    }


def leaf_policy_delta_width_screen(
    *,
    layout: Any,
    workspace: Any,
    baseline_policy: dict[str, dict[str, float]],
    candidate_policy: dict[str, dict[str, float]],
    terminal_automata: tuple[dict[str, Any], ...],
    hands_by_player: tuple[tuple[Any, ...], ...],
    comparison_tolerance: float,
) -> dict[str, Any]:
    """Count an optimistic ordered-seat terminal-delta representation.

    The screen assumes baseline terminal numerators are cached.  A candidate
    terminal delta is represented by the exact ordered product telescope over
    changed opponent-seat path factors.  It charges value rank only—no reach
    feature—so it is optimistic relative to the current full evaluator.
    """

    if comparison_tolerance < 0.0 or not np.isfinite(comparison_tolerance):
        raise ValueError("policy-delta comparison tolerance is invalid")
    players = layout.num_players
    if len(terminal_automata) != players:
        raise ValueError("policy-delta screen requires one automaton library per seat")
    baseline = compile_policy_probability_tape(layout, hands_by_player, baseline_policy)
    candidate = compile_policy_probability_tape(layout, hands_by_player, candidate_policy)
    parents, parent_actions = _parent_metadata(layout)
    terminal_keys = _terminal_keys_by_slot(layout)
    terminal_nodes = tuple(
        (node_index, node)
        for node_index, node in enumerate(layout.nodes)
        if node.player == TERMINAL_PLAYER
    )
    components = int(workspace.component_count)
    split = int(workspace.topology.base.split_index)
    shape = workspace.topology.base.hand_counts

    changed_public_nodes = []
    changed_seats = set()
    maximum_probability_delta = 0.0
    for node_index, node in enumerate(layout.nodes):
        if node.player == TERMINAL_PLAYER:
            continue
        first = baseline[node_index]
        second = candidate[node_index]
        if first is None or second is None:
            raise ValueError("policy-delta screen encountered missing probabilities")
        delta = float(np.max(np.abs(first - second)))
        maximum_probability_delta = max(maximum_probability_delta, delta)
        if delta > comparison_tolerance:
            changed_public_nodes.append(node_index)
            changed_seats.add(int(node.player))

    full_value_width = 0
    full_existing_width = 0
    delta_value_width = 0
    full_terms = 0
    supported_delta_terms = 0
    maximum_path_factor_delta = 0.0
    per_target = []
    for target in range(players):
        target_full_value = 0
        target_full_existing = 0
        target_delta_value = 0
        target_delta_terms = 0
        for terminal_node, node in terminal_nodes:
            automaton = terminal_automata[target][terminal_keys[node.terminal_slot]]
            rank = (
                1
                if automaton.constant_winner_shortcut
                else len(automaton.bond_states[split - 1]) + 1
            )
            value_width = components * rank
            target_full_value += value_width
            target_full_existing += components * (rank + 1)
            full_terms += 1
            baseline_factors = _target_omitted_path_factors(
                layout,
                baseline,
                parents,
                parent_actions,
                terminal_node=terminal_node,
                traverser=target,
                shape=shape,
            )
            candidate_factors = _target_omitted_path_factors(
                layout,
                candidate,
                parents,
                parent_actions,
                terminal_node=terminal_node,
                traverser=target,
                shape=shape,
            )
            for seat, (first, second) in enumerate(
                zip(baseline_factors, candidate_factors, strict=True)
            ):
                if seat == target:
                    continue
                delta = float(np.max(np.abs(first - second)))
                maximum_path_factor_delta = max(maximum_path_factor_delta, delta)
                if delta > comparison_tolerance:
                    target_delta_terms += 1
                    target_delta_value += value_width
        full_value_width += target_full_value
        full_existing_width += target_full_existing
        delta_value_width += target_delta_value
        supported_delta_terms += target_delta_terms
        per_target.append(
            {
                "target_player": target,
                "full_value_feature_width": target_full_value,
                "full_existing_feature_width": target_full_existing,
                "delta_value_feature_width": target_delta_value,
                "supported_delta_terms": target_delta_terms,
                "optimistic_delta_to_existing_width_ratio": (
                    target_delta_value / target_full_existing
                ),
            }
        )
    terminal_count = len(terminal_nodes)
    baseline_terminal_numerator_cache_bytes = (
        terminal_count * sum(shape) * np.dtype(np.float64).itemsize
    )
    return {
        "baseline_policy_sha256": policy_digest(baseline_policy),
        "candidate_policy_sha256": policy_digest(candidate_policy),
        "changed_public_nodes": len(changed_public_nodes),
        "changed_public_node_fraction": (
            len(changed_public_nodes)
            / sum(node.player >= 0 for node in layout.nodes)
        ),
        "changed_seats": sorted(changed_seats),
        "maximum_probability_delta": maximum_probability_delta,
        "maximum_path_factor_delta": maximum_path_factor_delta,
        "terminal_nodes": terminal_count,
        "full_terms": full_terms,
        "supported_delta_terms": supported_delta_terms,
        "full_value_feature_width": full_value_width,
        "full_existing_feature_width": full_existing_width,
        "delta_value_feature_width": delta_value_width,
        "optimistic_delta_to_value_width_ratio": (
            delta_value_width / full_value_width
        ),
        "optimistic_delta_to_existing_width_ratio": (
            delta_value_width / full_existing_width
        ),
        "baseline_terminal_numerator_cache_bytes": (
            baseline_terminal_numerator_cache_bytes
        ),
        "per_target": per_target,
    }


def _validate_seat_order(seat_order: tuple[int, ...], *, players: int) -> None:
    if len(seat_order) != players or tuple(sorted(seat_order)) != tuple(range(players)):
        raise ValueError("verifier seat order must contain each seat exactly once")


def math_is_positive_finite(value: float) -> bool:
    return bool(np.isfinite(value) and value > 0.0)
