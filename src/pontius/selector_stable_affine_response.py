"""Selector-stable affine certificates over immutable incremental responses."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any, Mapping

import numpy as np

from .game import Action, TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_leaf_adjoint_response import (
    LeafAdjointResponseSeatCache,
    _contract,
    _readonly,
    _required,
    _sum_children,
    _validate_probability_tape,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import _target_omitted_path_factors
from .public_policy_tt import _information_key, _terminal_keys_by_slot


@dataclass(frozen=True, slots=True)
class SelectorStableAffineSeatResult:
    """One-seat affine response proof under the immutable source selectors."""

    target_player: int
    acting_player: int
    changed_public_node: int
    profile_utility_intercept: float
    profile_utility_slope: float
    best_response_value_intercept: float
    best_response_value_slope: float
    deviation_gain_intercept: float
    deviation_gap_slope: float
    selector_stable_scale: float
    first_switch_information_key: str | None
    first_switch_source_action: Action | None
    first_switch_competing_action: Action | None
    first_switch_hand_index: int | None
    selector_comparisons: int
    exact_source_action_ties: int
    changed_public_nodes: int
    changed_opponent_public_nodes: int
    affected_terminal_contractions: int
    full_terminal_contractions: int
    reused_terminal_numerators: int
    terminal_contraction_ms: float
    reverse_evaluation_ms: float
    wall_ms: float
    maximum_terminal_middle_rank: int
    maximum_gpu_pool_total_bytes: int


@dataclass(frozen=True, slots=True)
class SelectorStableAffineEnvelopeResult:
    """Conservative scale and predicted quality from six affine seat proofs."""

    complete: bool
    stop_reason: str
    selected_scale: float | None
    selector_scale_limit: float
    cap_scale_limit: float
    objective_scale_limit: float
    safe_scale_limit: float
    predicted_utilities: tuple[float, ...] | None
    predicted_best_response_values: tuple[float, ...] | None
    predicted_deviation_gains: tuple[float, ...] | None
    predicted_nash_conv: float | None
    positive_certified_value: float


def evaluate_selector_stable_affine_leaf_adjoint_seat(
    cache: LeafAdjointResponseSeatCache,
    endpoint_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    selector_margin_allowance: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_cache: Any | None = None,
    cupy_sparse: Any | None = None,
) -> SelectorStableAffineSeatResult:
    """Prove an affine response interval for one exact public-node direction.

    Terminal numerators are evaluated once at scale one. A direction changing
    exactly one public node is affine between the immutable source and that
    endpoint. Reverse evaluation follows the source best-response action tape
    and returns the first conservative scale at which any competing action can
    tie it. No claim is made at or beyond that breakpoint.
    """

    started = time.perf_counter()
    layout = cache.layout
    _validate_probability_tape(layout, cache.hands_by_player, endpoint_probabilities)
    if (
        isinstance(acting_player, bool)
        or acting_player not in range(layout.num_players)
    ):
        raise ValueError("affine response acting player is outside the layout")
    if not np.isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("affine selector allowance must be finite and nonnegative")

    changed_nodes = tuple(
        node_index
        for node_index, (source, endpoint) in enumerate(
            zip(cache.source_probabilities, endpoint_probabilities, strict=True)
        )
        if source is not None
        and endpoint is not None
        and not np.array_equal(source, endpoint)
    )
    if len(changed_nodes) != 1:
        raise ValueError("affine response scope requires exactly one changed public node")
    changed_node = changed_nodes[0]
    if layout.nodes[changed_node].player != acting_player:
        raise ValueError("affine response changed node belongs to another acting player")

    changed_opponents = int(acting_player != cache.target_player)
    terminal_keys = _terminal_keys_by_slot(layout)
    shape = cache.workspace.topology.base.hand_counts
    terms = []
    for node_index, node in enumerate(layout.nodes):
        if node.player != TERMINAL_PLAYER:
            continue
        source_factors = _target_omitted_path_factors(
            layout,
            cache.source_probabilities,
            cache.parents,
            cache.parent_actions,
            terminal_node=node_index,
            traverser=cache.target_player,
            shape=shape,
        )
        endpoint_factors = _target_omitted_path_factors(
            layout,
            endpoint_probabilities,
            cache.parents,
            cache.parent_actions,
            terminal_node=node_index,
            traverser=cache.target_player,
            shape=shape,
        )
        if all(
            np.array_equal(first, second)
            for first, second in zip(source_factors, endpoint_factors, strict=True)
        ):
            continue
        terms.append(
            HeterogeneousLeafTerm(
                key=node_index,
                automaton=cache.terminal_automata[terminal_keys[node.terminal_slot]],
                mode_factors=endpoint_factors,
            )
        )

    endpoint_terminal_values = list(cache.terminal_values)
    contraction_ms = 0.0
    maximum_rank = 0
    maximum_pool = 0
    if terms:
        contraction_started = time.perf_counter()
        contraction = _contract(
            cache.workspace,
            cache.sparse,
            tuple(terms),
            target_player=cache.target_player,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=cupy_sparse,
        )
        contraction_ms = (time.perf_counter() - contraction_started) * 1000.0
        maximum_rank = int(contraction.work.maximum_middle_rank)
        maximum_pool = int(contraction.work.maximum_gpu_pool_total_bytes)
        for node_index, values in contraction.values:
            endpoint_terminal_values[node_index] = _readonly(
                values.root_normalized_numerators
            )

    reverse_started = time.perf_counter()
    affine = _selector_stable_affine_reverse(
        layout,
        cache.source_probabilities,
        endpoint_probabilities,
        list(cache.terminal_values),
        endpoint_terminal_values,
        target_player=cache.target_player,
        hands_by_player=cache.hands_by_player,
        source_actions=cache.source_evaluation.best_response_actions,
        selector_margin_allowance=selector_margin_allowance,
    )
    reverse_ms = (time.perf_counter() - reverse_started) * 1000.0
    source = cache.source_evaluation
    identity_error = max(
        abs(affine["profile_utility_intercept"] - source.profile_utility),
        abs(affine["best_response_value_intercept"] - source.best_response_value),
        abs(affine["deviation_gain_intercept"] - source.deviation_gain),
    )
    if identity_error > max(1e-12, selector_margin_allowance):
        raise ArithmeticError("affine response intercept differs from source cache")

    return SelectorStableAffineSeatResult(
        target_player=cache.target_player,
        acting_player=acting_player,
        changed_public_node=changed_node,
        profile_utility_intercept=affine["profile_utility_intercept"],
        profile_utility_slope=affine["profile_utility_slope"],
        best_response_value_intercept=affine[
            "best_response_value_intercept"
        ],
        best_response_value_slope=affine["best_response_value_slope"],
        deviation_gain_intercept=affine["deviation_gain_intercept"],
        deviation_gap_slope=affine["deviation_gap_slope"],
        selector_stable_scale=affine["selector_stable_scale"],
        first_switch_information_key=affine["first_switch_information_key"],
        first_switch_source_action=affine["first_switch_source_action"],
        first_switch_competing_action=affine["first_switch_competing_action"],
        first_switch_hand_index=affine["first_switch_hand_index"],
        selector_comparisons=affine["selector_comparisons"],
        exact_source_action_ties=affine["exact_source_action_ties"],
        changed_public_nodes=1,
        changed_opponent_public_nodes=changed_opponents,
        affected_terminal_contractions=len(terms),
        full_terminal_contractions=cache.terminal_contractions,
        reused_terminal_numerators=cache.terminal_contractions - len(terms),
        terminal_contraction_ms=contraction_ms,
        reverse_evaluation_ms=reverse_ms,
        wall_ms=(time.perf_counter() - started) * 1000.0,
        maximum_terminal_middle_rank=maximum_rank,
        maximum_gpu_pool_total_bytes=maximum_pool,
    )


def selector_stable_affine_values_at_scale(
    result: SelectorStableAffineSeatResult,
    scale: float,
) -> tuple[float, float, float]:
    """Return utility, response value, and gain inside the proof interval."""

    if not np.isfinite(scale) or scale < 0.0 or scale > 1.0:
        raise ValueError("affine response scale must lie in [0, 1]")
    if scale > result.selector_stable_scale:
        raise ValueError("affine response scale exceeds selector-stable interval")
    utility = result.profile_utility_intercept + scale * result.profile_utility_slope
    response = (
        result.best_response_value_intercept
        + scale * result.best_response_value_slope
    )
    gain = max(0.0, response - utility)
    return float(utility), float(response), float(gain)


def certify_selector_stable_affine_envelope(
    seat_results: tuple[SelectorStableAffineSeatResult, ...],
    *,
    blueprint_deviation_gains: tuple[float, ...],
    blueprint_nash_conv: float,
    raw_guard: float,
    scale_grid: tuple[float, ...],
    safety_fraction: float,
    numerical_allowance: float,
) -> SelectorStableAffineEnvelopeResult:
    """Choose one conservative grid scale from complete affine seat proofs."""

    players = len(seat_results)
    if players == 0 or tuple(row.target_player for row in seat_results) != tuple(
        range(players)
    ):
        raise ValueError("affine envelope requires one ordered proof per seat")
    if len(blueprint_deviation_gains) != players:
        raise ValueError("affine envelope blueprint vector has the wrong width")
    if len({row.acting_player for row in seat_results}) != 1 or len(
        {row.changed_public_node for row in seat_results}
    ) != 1:
        raise ValueError("affine envelope seat proofs have different scopes")
    scalar_values = (
        blueprint_nash_conv,
        raw_guard,
        safety_fraction,
        numerical_allowance,
        *blueprint_deviation_gains,
        *scale_grid,
    )
    if any(not np.isfinite(value) for value in scalar_values):
        raise ValueError("affine envelope values must be finite")
    if blueprint_nash_conv < 0.0 or raw_guard < 0.0 or numerical_allowance < 0.0:
        raise ValueError("affine envelope bounds must be nonnegative")
    if not 0.0 < safety_fraction < 1.0:
        raise ValueError("affine envelope safety fraction must lie in (0, 1)")
    if (
        not scale_grid
        or any(scale <= 0.0 or scale > 1.0 for scale in scale_grid)
        or any(left <= right for left, right in zip(scale_grid, scale_grid[1:]))
    ):
        raise ValueError("affine envelope scale grid must strictly descend in (0, 1]")

    intercept_error = max(
        abs(row.deviation_gain_intercept - blueprint_deviation_gains[seat])
        for seat, row in enumerate(seat_results)
    )
    if intercept_error > numerical_allowance:
        raise ArithmeticError("affine envelope intercept differs from blueprint vector")

    selector_limit = min(1.0, *(row.selector_stable_scale for row in seat_results))
    cap_limit = 1.0
    for seat, row in enumerate(seat_results):
        cap_budget = (
            blueprint_deviation_gains[seat]
            + raw_guard
            - numerical_allowance
            - row.deviation_gain_intercept
        )
        if cap_budget < 0.0:
            cap_limit = 0.0
            break
        if row.deviation_gap_slope > 0.0:
            cap_limit = min(cap_limit, cap_budget / row.deviation_gap_slope)
    cap_limit = min(1.0, max(0.0, cap_limit))
    preliminary_limit = min(selector_limit, cap_limit)

    def predicted_nash(scale: float) -> float:
        return float(
            fsum(
                max(
                    0.0,
                    row.deviation_gain_intercept
                    + scale * row.deviation_gap_slope,
                )
                for row in seat_results
            )
        )

    initial_slope = fsum(
        (
            row.deviation_gap_slope
            if row.deviation_gain_intercept > numerical_allowance
            else max(0.0, row.deviation_gap_slope)
        )
        for row in seat_results
    )
    objective_limit = 0.0
    if preliminary_limit > 0.0 and initial_slope < 0.0:
        if predicted_nash(preliminary_limit) <= blueprint_nash_conv:
            objective_limit = preliminary_limit
        else:
            low = 0.0
            high = preliminary_limit
            for _ in range(80):
                middle = (low + high) * 0.5
                if predicted_nash(middle) <= blueprint_nash_conv:
                    low = middle
                else:
                    high = middle
            objective_limit = low
    safe_limit = min(preliminary_limit, objective_limit)
    target_scale = safety_fraction * safe_limit
    selected_scale = next(
        (scale for scale in scale_grid if scale <= target_scale),
        None,
    )
    if selected_scale is None:
        return SelectorStableAffineEnvelopeResult(
            complete=False,
            stop_reason=(
                "objective_nonimproving"
                if objective_limit <= 0.0
                else "scale_below_grid"
            ),
            selected_scale=None,
            selector_scale_limit=selector_limit,
            cap_scale_limit=cap_limit,
            objective_scale_limit=objective_limit,
            safe_scale_limit=safe_limit,
            predicted_utilities=None,
            predicted_best_response_values=None,
            predicted_deviation_gains=None,
            predicted_nash_conv=None,
            positive_certified_value=0.0,
        )

    values = tuple(
        selector_stable_affine_values_at_scale(row, selected_scale)
        for row in seat_results
    )
    utilities = tuple(row[0] for row in values)
    responses = tuple(row[1] for row in values)
    gains = tuple(row[2] for row in values)
    nash_conv = fsum(gains)
    cap_ok = all(
        gain
        <= blueprint_deviation_gains[seat] + raw_guard - numerical_allowance
        for seat, gain in enumerate(gains)
    )
    objective_value = blueprint_nash_conv - nash_conv
    if not cap_ok or objective_value <= numerical_allowance:
        return SelectorStableAffineEnvelopeResult(
            complete=False,
            stop_reason=("blueprint_cap" if not cap_ok else "objective_allowance"),
            selected_scale=None,
            selector_scale_limit=selector_limit,
            cap_scale_limit=cap_limit,
            objective_scale_limit=objective_limit,
            safe_scale_limit=safe_limit,
            predicted_utilities=None,
            predicted_best_response_values=None,
            predicted_deviation_gains=None,
            predicted_nash_conv=None,
            positive_certified_value=0.0,
        )
    return SelectorStableAffineEnvelopeResult(
        complete=True,
        stop_reason="complete",
        selected_scale=selected_scale,
        selector_scale_limit=selector_limit,
        cap_scale_limit=cap_limit,
        objective_scale_limit=objective_limit,
        safe_scale_limit=safe_limit,
        predicted_utilities=utilities,
        predicted_best_response_values=responses,
        predicted_deviation_gains=gains,
        predicted_nash_conv=nash_conv,
        positive_certified_value=objective_value,
    )


def _selector_stable_affine_reverse(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    endpoint_probabilities: PolicyProbabilityTape,
    source_terminal_values: list[np.ndarray | None],
    endpoint_terminal_values: list[np.ndarray | None],
    *,
    target_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...],
    source_actions: Mapping[str, Action],
    selector_margin_allowance: float,
) -> dict[str, Any]:
    """Reverse one affine direction until the first source-selector tie."""

    profile_base = list(source_terminal_values)
    response_base = list(source_terminal_values)
    profile_slope = [
        None
        if source is None or endpoint is None
        else np.ascontiguousarray(endpoint - source, dtype=np.float64)
        for source, endpoint in zip(
            source_terminal_values, endpoint_terminal_values, strict=True
        )
    ]
    response_slope = list(profile_slope)
    selector_limit = 1.0
    first_switch: tuple[str, Action, Action, int] | None = None
    selector_comparisons = 0
    exact_ties = 0
    target_hands = hands_by_player[target_player]
    hand_indices = np.arange(len(target_hands), dtype=np.intp)

    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continue
        profile_base_children = tuple(
            _required(profile_base[child]) for child in node.children
        )
        response_base_children = tuple(
            _required(response_base[child]) for child in node.children
        )
        profile_slope_children = tuple(
            _required(profile_slope[child]) for child in node.children
        )
        response_slope_children = tuple(
            _required(response_slope[child]) for child in node.children
        )
        if node.player != target_player:
            profile_base[node_index] = _sum_children(profile_base_children)
            response_base[node_index] = _sum_children(response_base_children)
            profile_slope[node_index] = _sum_children(profile_slope_children)
            response_slope[node_index] = _sum_children(response_slope_children)
            continue

        source_node_probabilities = source_probabilities[node_index]
        endpoint_node_probabilities = endpoint_probabilities[node_index]
        if source_node_probabilities is None or endpoint_node_probabilities is None:
            raise ValueError("affine response target node has no policy probabilities")
        probability_slope = endpoint_node_probabilities - source_node_probabilities
        profile_base_scores = np.ascontiguousarray(
            np.column_stack(profile_base_children), dtype=np.float64
        )
        profile_slope_scores = np.ascontiguousarray(
            np.column_stack(profile_slope_children), dtype=np.float64
        )
        if np.any(probability_slope * profile_slope_scores != 0.0):
            raise ValueError("affine response scope creates a quadratic profile term")
        profile_base[node_index] = np.einsum(
            "ha,ha->h",
            source_node_probabilities,
            profile_base_scores,
            optimize=True,
        )
        profile_slope[node_index] = np.ascontiguousarray(
            np.einsum(
                "ha,ha->h",
                source_node_probabilities,
                profile_slope_scores,
                optimize=True,
            )
            + np.einsum(
                "ha,ha->h",
                probability_slope,
                profile_base_scores,
                optimize=True,
            ),
            dtype=np.float64,
        )

        response_base_scores = np.ascontiguousarray(
            np.column_stack(response_base_children), dtype=np.float64
        )
        response_slope_scores = np.ascontiguousarray(
            np.column_stack(response_slope_children), dtype=np.float64
        )
        selected = np.argmax(response_base_scores, axis=1)
        selected_base = response_base_scores[hand_indices, selected]
        selected_slope = response_slope_scores[hand_indices, selected]
        response_base[node_index] = np.ascontiguousarray(
            selected_base, dtype=np.float64
        )
        response_slope[node_index] = np.ascontiguousarray(
            selected_slope, dtype=np.float64
        )
        for hand_index, hand in enumerate(target_hands):
            selected_index = int(selected[hand_index])
            information_key = _information_key(
                layout, target_player, hand, node.history
            )
            source_action = node.actions[selected_index]
            if source_actions.get(information_key) != source_action:
                raise ArithmeticError(
                    "affine response source selector differs from immutable tape"
                )
            for competing_index, competing_action in enumerate(node.actions):
                if competing_index == selected_index:
                    continue
                selector_comparisons += 1
                margin = float(
                    selected_base[hand_index]
                    - response_base_scores[hand_index, competing_index]
                )
                if margin < -selector_margin_allowance:
                    raise ArithmeticError("affine response source selector is not maximal")
                if margin == 0.0:
                    exact_ties += 1
                closing_slope = float(
                    response_slope_scores[hand_index, competing_index]
                    - selected_slope[hand_index]
                )
                if closing_slope <= 0.0:
                    continue
                conservative_margin = max(
                    0.0, margin - selector_margin_allowance
                )
                breakpoint = conservative_margin / closing_slope
                if breakpoint < selector_limit:
                    selector_limit = max(0.0, breakpoint)
                    first_switch = (
                        information_key,
                        source_action,
                        competing_action,
                        hand_index,
                    )

    profile_intercept = fsum(float(value) for value in _required(profile_base[0]))
    profile_direction = fsum(float(value) for value in _required(profile_slope[0]))
    response_intercept = fsum(float(value) for value in _required(response_base[0]))
    response_direction = fsum(float(value) for value in _required(response_slope[0]))
    return {
        "profile_utility_intercept": profile_intercept,
        "profile_utility_slope": profile_direction,
        "best_response_value_intercept": response_intercept,
        "best_response_value_slope": response_direction,
        "deviation_gain_intercept": max(
            0.0, response_intercept - profile_intercept
        ),
        "deviation_gap_slope": response_direction - profile_direction,
        "selector_stable_scale": min(1.0, max(0.0, selector_limit)),
        "first_switch_information_key": (
            None if first_switch is None else first_switch[0]
        ),
        "first_switch_source_action": (
            None if first_switch is None else first_switch[1]
        ),
        "first_switch_competing_action": (
            None if first_switch is None else first_switch[2]
        ),
        "first_switch_hand_index": (
            None if first_switch is None else first_switch[3]
        ),
        "selector_comparisons": selector_comparisons,
        "exact_source_action_ties": exact_ties,
    }
