"""Source-relative terminal-numerator cache for exact leaf-adjoint responses."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any, Mapping

import numpy as np

from .game import Action, TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from .incremental_policy_tt import PolicyProbabilityTape, compile_policy_probability_tape
from .leaf_adjoint_cfr import _parent_metadata, _target_omitted_path_factors
from .leaf_adjoint_evaluation import LeafAdjointSeatEvaluation, _external_axes
from .fixed_envelope_verifier import _stop_reason, math_is_positive_finite
from .public_policy_tt import _information_key, _terminal_keys_by_slot
from .real_policy import policy_digest
from .resident_heterogeneous_leaf_contraction import (
    contract_resident_heterogeneous_leaf_terms,
)


@dataclass(frozen=True, slots=True)
class LeafAdjointResponseSeatCache:
    """Immutable source terminal numerators and exact source response for one seat."""

    layout: Any
    workspace: Any
    sparse: Any
    terminal_automata: Mapping[str, Any]
    hands_by_player: tuple[tuple[Any, ...], ...]
    target_player: int
    source_probabilities: PolicyProbabilityTape
    parents: np.ndarray
    parent_actions: np.ndarray
    terminal_values: tuple[np.ndarray | None, ...]
    source_evaluation: LeafAdjointSeatEvaluation
    terminal_contractions: int
    persistent_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class IncrementalLeafAdjointSeatResult:
    """One exact source-relative candidate seat read and reuse diagnostics."""

    target_player: int
    profile_utility: float
    best_response_value: float
    deviation_gain: float
    best_response_actions: dict[str, Action]
    response_action_flips: int
    exact_action_ties: int
    minimum_action_gap: float
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


def compile_leaf_adjoint_response_seat_cache(
    layout: Any,
    workspace: Any,
    sparse: Any,
    source_probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    target_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...] | None = None,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_cache: Any | None = None,
    cupy_sparse: Any | None = None,
) -> LeafAdjointResponseSeatCache:
    """Compile the complete source once and retain every terminal numerator."""

    axes, parents, parent_actions, terminal_keys = _validate_common(
        layout,
        workspace,
        sparse,
        source_probabilities,
        terminal_automata,
        target_player=target_player,
        hands_by_player=hands_by_player,
    )
    terms = _terminal_terms(
        layout,
        workspace,
        source_probabilities,
        terminal_automata,
        target_player=target_player,
        parents=parents,
        parent_actions=parent_actions,
        terminal_keys=terminal_keys,
    )
    contraction_started = time.perf_counter()
    contraction = _contract(
        workspace,
        sparse,
        terms,
        target_player=target_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        belief_cache=belief_cache,
        automaton_cache=automaton_cache,
        cupy_sparse=cupy_sparse,
    )
    contraction_ms = (time.perf_counter() - contraction_started) * 1000.0
    terminal_values: list[np.ndarray | None] = [None] * layout.public_node_count
    for node_index, values in contraction.values:
        terminal_values[node_index] = _readonly(values.root_normalized_numerators)
    source = _reverse(
        layout,
        source_probabilities,
        terminal_values,
        target_player=target_player,
        hands_by_player=axes,
        terminal_contractions=len(terms),
        terminal_sparse_batches=int(contraction.work.batches),
        terminal_contraction_ms=contraction_ms,
        maximum_terminal_middle_rank=int(contraction.work.maximum_middle_rank),
        maximum_terminal_peak_numeric_bytes=int(_work_peak_bytes(contraction.work)),
        maximum_gpu_pool_total_bytes=int(contraction.work.maximum_gpu_pool_total_bytes),
    )
    parents.flags.writeable = False
    parent_actions.flags.writeable = False
    persistent = (
        sum(values.nbytes for values in terminal_values if values is not None)
        + parents.nbytes
        + parent_actions.nbytes
        + sum(values.nbytes for values in source_probabilities if values is not None)
    )
    return LeafAdjointResponseSeatCache(
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        terminal_automata=dict(terminal_automata),
        hands_by_player=axes,
        target_player=target_player,
        source_probabilities=source_probabilities,
        parents=parents,
        parent_actions=parent_actions,
        terminal_values=tuple(terminal_values),
        source_evaluation=source,
        terminal_contractions=len(terms),
        persistent_numeric_bytes=persistent,
    )


def evaluate_incremental_leaf_adjoint_seat(
    cache: LeafAdjointResponseSeatCache,
    candidate_probabilities: PolicyProbabilityTape,
    *,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_cache: Any | None = None,
    cupy_sparse: Any | None = None,
) -> IncrementalLeafAdjointSeatResult:
    """Recontract only terminals whose target-omitted factors changed."""

    started = time.perf_counter()
    layout = cache.layout
    _validate_probability_tape(layout, cache.hands_by_player, candidate_probabilities)
    changed_nodes = tuple(
        node_index
        for node_index, (source, candidate) in enumerate(
            zip(cache.source_probabilities, candidate_probabilities, strict=True)
        )
        if source is not None
        and candidate is not None
        and not np.array_equal(source, candidate)
    )
    changed_opponents = sum(
        layout.nodes[node].player != cache.target_player for node in changed_nodes
    )
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
        candidate_factors = _target_omitted_path_factors(
            layout,
            candidate_probabilities,
            cache.parents,
            cache.parent_actions,
            terminal_node=node_index,
            traverser=cache.target_player,
            shape=shape,
        )
        if all(
            np.array_equal(first, second)
            for first, second in zip(source_factors, candidate_factors, strict=True)
        ):
            continue
        terms.append(
            HeterogeneousLeafTerm(
                key=node_index,
                automaton=cache.terminal_automata[terminal_keys[node.terminal_slot]],
                mode_factors=candidate_factors,
            )
        )

    terminal_values = list(cache.terminal_values)
    contraction_ms = 0.0
    sparse_batches = 0
    maximum_rank = 0
    maximum_peak = 0
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
        sparse_batches = int(contraction.work.batches)
        maximum_rank = int(contraction.work.maximum_middle_rank)
        maximum_peak = int(_work_peak_bytes(contraction.work))
        maximum_pool = int(contraction.work.maximum_gpu_pool_total_bytes)
        for node_index, values in contraction.values:
            terminal_values[node_index] = _readonly(values.root_normalized_numerators)

    reverse_started = time.perf_counter()
    evaluated = _reverse(
        layout,
        candidate_probabilities,
        terminal_values,
        target_player=cache.target_player,
        hands_by_player=cache.hands_by_player,
        terminal_contractions=len(terms),
        terminal_sparse_batches=sparse_batches,
        terminal_contraction_ms=contraction_ms,
        maximum_terminal_middle_rank=maximum_rank,
        maximum_terminal_peak_numeric_bytes=maximum_peak,
        maximum_gpu_pool_total_bytes=maximum_pool,
    )
    reverse_ms = (time.perf_counter() - reverse_started) * 1000.0
    source_actions = cache.source_evaluation.best_response_actions
    flips = sum(
        source_actions.get(key) != evaluated.best_response_actions.get(key)
        for key in set(source_actions) | set(evaluated.best_response_actions)
    )
    return IncrementalLeafAdjointSeatResult(
        target_player=cache.target_player,
        profile_utility=evaluated.profile_utility,
        best_response_value=evaluated.best_response_value,
        deviation_gain=evaluated.deviation_gain,
        best_response_actions=evaluated.best_response_actions,
        response_action_flips=flips,
        exact_action_ties=evaluated.exact_action_ties,
        minimum_action_gap=evaluated.minimum_action_gap,
        changed_public_nodes=len(changed_nodes),
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


def compile_leaf_adjoint_response_caches(
    layout: Any,
    workspace: Any,
    sparse: Any,
    source_policy: dict[str, dict[str, float]],
    terminal_automata: tuple[Mapping[str, Any], ...],
    *,
    hands_by_player: tuple[tuple[Any, ...], ...],
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_caches: tuple[Any, ...] | None = None,
    cupy_sparse: Any | None = None,
) -> tuple[LeafAdjointResponseSeatCache, ...]:
    """Compile one shared source tape and one immutable cache per target seat."""

    probabilities = compile_policy_probability_tape(layout, hands_by_player, source_policy)
    if len(terminal_automata) != layout.num_players:
        raise ValueError("response cache requires one terminal library per seat")
    if automaton_caches is not None and len(automaton_caches) != layout.num_players:
        raise ValueError("response cache requires one resident automaton cache per seat")
    return tuple(
        compile_leaf_adjoint_response_seat_cache(
            layout,
            workspace,
            sparse,
            probabilities,
            terminal_automata[seat],
            target_player=seat,
            hands_by_player=hands_by_player,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            belief_cache=belief_cache,
            automaton_cache=(None if automaton_caches is None else automaton_caches[seat]),
            cupy_sparse=cupy_sparse,
        )
        for seat in range(layout.num_players)
    )


def verify_incremental_leaf_adjoint_candidate(
    *,
    candidate_id: str,
    layout: Any,
    policy: dict[str, dict[str, float]],
    hands_by_player: tuple[tuple[Any, ...], ...],
    response_caches: tuple[LeafAdjointResponseSeatCache, ...],
    blueprint_deviation_gains: tuple[float, ...],
    best_complete_nash_conv: float,
    payoff_span: float,
    raw_guard: float,
    seat_order: tuple[int, ...],
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_caches: tuple[Any, ...] | None = None,
    cupy_sparse: Any | None = None,
) -> dict[str, Any]:
    """Run the accepted fixed envelope over incremental exact seat reads."""

    players = layout.num_players
    if len(seat_order) != players or tuple(sorted(seat_order)) != tuple(range(players)):
        raise ValueError("incremental verifier seat order must contain every seat")
    if len(response_caches) != players or any(
        cache.layout is not layout or cache.target_player != seat
        for seat, cache in enumerate(response_caches)
    ):
        raise ValueError("incremental verifier response caches differ from the layout")
    if len(blueprint_deviation_gains) != players:
        raise ValueError("incremental verifier blueprint vector has the wrong width")
    if automaton_caches is not None and len(automaton_caches) != players:
        raise ValueError("incremental verifier resident cache vector has the wrong width")
    if not math_is_positive_finite(payoff_span):
        raise ValueError("incremental verifier payoff span must be positive and finite")
    if raw_guard < 0.0 or not np.isfinite(raw_guard):
        raise ValueError("incremental verifier guard must be finite and nonnegative")
    if best_complete_nash_conv < 0.0 or not np.isfinite(best_complete_nash_conv):
        raise ValueError("incremental verifier incumbent must be finite and nonnegative")

    wall_started = time.perf_counter()
    probability_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(layout, hands_by_player, policy)
    probability_compile_ms = (time.perf_counter() - probability_started) * 1000.0
    rows = []
    partial = 0.0
    stop_reason = None
    stop_seat = None
    for seat in seat_order:
        evaluated = evaluate_incremental_leaf_adjoint_seat(
            response_caches[seat],
            probabilities,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            belief_cache=belief_cache,
            automaton_cache=(None if automaton_caches is None else automaton_caches[seat]),
            cupy_sparse=cupy_sparse,
        )
        partial += evaluated.deviation_gain
        rows.append(
            {
                "target_player": seat,
                "profile_utility": evaluated.profile_utility,
                "best_response_value": evaluated.best_response_value,
                "deviation_gain": evaluated.deviation_gain,
                "partial_nash_conv": partial,
                "response_action_flips": evaluated.response_action_flips,
                "exact_action_ties": evaluated.exact_action_ties,
                "minimum_action_gap": evaluated.minimum_action_gap,
                "changed_public_nodes": evaluated.changed_public_nodes,
                "changed_opponent_public_nodes": evaluated.changed_opponent_public_nodes,
                "affected_terminal_contractions": evaluated.affected_terminal_contractions,
                "full_terminal_contractions": evaluated.full_terminal_contractions,
                "reused_terminal_numerators": evaluated.reused_terminal_numerators,
                "terminal_contraction_ms": evaluated.terminal_contraction_ms,
                "reverse_evaluation_ms": evaluated.reverse_evaluation_ms,
                "wall_ms": evaluated.wall_ms,
                "maximum_terminal_middle_rank": evaluated.maximum_terminal_middle_rank,
                "maximum_gpu_pool_total_bytes": evaluated.maximum_gpu_pool_total_bytes,
            }
        )
        stop_reason = _stop_reason(
            seat=seat,
            gain=evaluated.deviation_gain,
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
            "policy_sha256": policy_digest(policy),
            "utilities": utilities,
            "best_response_values": responses,
            "deviation_gains": gains,
            "nash_conv": nash_conv,
            "normalized_nash_conv": nash_conv / payoff_span,
            "zero_sum_residual": abs(fsum(utilities)),
        }
    return {
        "candidate_id": candidate_id,
        "policy_sha256": policy_digest(policy),
        "probability_compile_ms": probability_compile_ms,
        "seat_rows": rows,
        "evaluated_seats": [int(row["target_player"]) for row in rows],
        "evaluated_seat_count": len(rows),
        "partial_nash_conv": partial,
        "stop_reason": "complete" if complete else stop_reason,
        "stop_seat": stop_seat,
        "complete": complete,
        "quality": quality,
        "affected_terminal_contractions": sum(
            int(row["affected_terminal_contractions"]) for row in rows
        ),
        "full_terminal_contractions_for_evaluated_seats": sum(
            int(row["full_terminal_contractions"]) for row in rows
        ),
        "reused_terminal_numerators": sum(
            int(row["reused_terminal_numerators"]) for row in rows
        ),
        "response_action_flips": sum(int(row["response_action_flips"]) for row in rows),
        "terminal_contraction_ms": fsum(
            float(row["terminal_contraction_ms"]) for row in rows
        ),
        "reverse_evaluation_ms": fsum(
            float(row["reverse_evaluation_ms"]) for row in rows
        ),
        "maximum_gpu_pool_bytes": max(
            (int(row["maximum_gpu_pool_total_bytes"]) for row in rows),
            default=0,
        ),
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
    }


def _validate_common(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    target_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...] | None,
) -> tuple[tuple[tuple[Any, ...], ...], np.ndarray, np.ndarray, tuple[str, ...]]:
    axes = _external_axes(layout, workspace, hands_by_player)
    if isinstance(target_player, bool) or target_player not in range(layout.num_players):
        raise ValueError("response cache target is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("response cache topology and workspace differ")
    _validate_probability_tape(layout, axes, probabilities)
    terminal_keys = _terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("response cache automata differ from payoff groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("response cache automata differ from hand axes")
    parents, actions = _parent_metadata(layout)
    return axes, parents, actions, terminal_keys


def _validate_probability_tape(
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    probabilities: PolicyProbabilityTape,
) -> None:
    if len(probabilities) != layout.public_node_count:
        raise ValueError("response cache probability tape differs from tree")
    for node_index, node in enumerate(layout.nodes):
        values = probabilities[node_index]
        if node.player == TERMINAL_PLAYER:
            if values is not None:
                raise ValueError("response cache terminal has policy probabilities")
            continue
        if values is None or values.shape != (
            len(hands_by_player[node.player]),
            len(node.actions),
        ):
            raise ValueError("response cache strategic probability shape differs")
        if not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise ValueError("response cache probabilities must be finite and nonnegative")
        if not np.allclose(np.sum(values, axis=1), 1.0, rtol=0.0, atol=1e-12):
            raise ValueError("response cache probabilities must sum to one")


def _terminal_terms(
    layout: Any,
    workspace: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    target_player: int,
    parents: np.ndarray,
    parent_actions: np.ndarray,
    terminal_keys: tuple[str, ...],
) -> tuple[HeterogeneousLeafTerm, ...]:
    shape = workspace.topology.base.hand_counts
    return tuple(
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


def _contract(
    workspace: Any,
    sparse: Any,
    terms: tuple[HeterogeneousLeafTerm, ...],
    *,
    target_player: int,
    maximum_feature_width_per_batch: int,
    belief_cache: Any | None,
    automaton_cache: Any | None,
    cupy_sparse: Any | None,
) -> Any:
    supplied = (belief_cache is not None, automaton_cache is not None, cupy_sparse is not None)
    if any(supplied) and not all(supplied):
        raise ValueError("resident response contraction requires all three resident inputs")
    if all(supplied):
        return contract_resident_heterogeneous_leaf_terms(
            workspace,
            sparse,
            terms,
            target_seat=target_player,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=cupy_sparse,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
    return contract_heterogeneous_leaf_terms(
        workspace,
        sparse,
        terms,
        target_seat=target_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )


def _reverse(
    layout: Any,
    probabilities: PolicyProbabilityTape,
    terminal_values: list[np.ndarray | None],
    *,
    target_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...],
    terminal_contractions: int,
    terminal_sparse_batches: int,
    terminal_contraction_ms: float,
    maximum_terminal_middle_rank: int,
    maximum_terminal_peak_numeric_bytes: int,
    maximum_gpu_pool_total_bytes: int,
) -> LeafAdjointSeatEvaluation:
    started = time.perf_counter()
    profile_values = list(terminal_values)
    response_values = list(terminal_values)
    selected_actions: dict[str, Action] = {}
    exact_ties = 0
    minimum_gap = float("inf")
    target_hands = hands_by_player[target_player]
    hand_indices = np.arange(len(target_hands), dtype=np.intp)
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continue
        profile_children = tuple(_required(profile_values[child]) for child in node.children)
        response_children = tuple(_required(response_values[child]) for child in node.children)
        if node.player != target_player:
            profile_values[node_index] = _sum_children(profile_children)
            response_values[node_index] = _sum_children(response_children)
            continue
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise ValueError("response cache target node has no policy probabilities")
        profile_scores = np.ascontiguousarray(np.column_stack(profile_children), dtype=np.float64)
        response_scores = np.ascontiguousarray(np.column_stack(response_children), dtype=np.float64)
        profile_values[node_index] = np.einsum(
            "ha,ha->h", node_probabilities, profile_scores, optimize=True
        )
        selected = np.argmax(response_scores, axis=1)
        response_values[node_index] = np.ascontiguousarray(
            response_scores[hand_indices, selected], dtype=np.float64
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
                raise ValueError("response cache violates information consistency")
    profile_root = _required(profile_values[0])
    response_root = _required(response_values[0])
    profile_utility = fsum(float(value) for value in profile_root)
    best_response_value = fsum(float(value) for value in response_root)
    reverse_ms = (time.perf_counter() - started) * 1000.0
    return LeafAdjointSeatEvaluation(
        target_player=target_player,
        profile_utility=profile_utility,
        best_response_value=best_response_value,
        deviation_gain=max(0.0, best_response_value - profile_utility),
        best_response_actions=selected_actions,
        exact_action_ties=exact_ties,
        minimum_action_gap=0.0 if minimum_gap == float("inf") else minimum_gap,
        terminal_contractions=terminal_contractions,
        terminal_sparse_batches=terminal_sparse_batches,
        terminal_contraction_ms=terminal_contraction_ms,
        reverse_evaluation_ms=reverse_ms,
        wall_ms=terminal_contraction_ms + reverse_ms,
        maximum_terminal_middle_rank=maximum_terminal_middle_rank,
        maximum_terminal_peak_numeric_bytes=maximum_terminal_peak_numeric_bytes,
        maximum_gpu_pool_total_bytes=maximum_gpu_pool_total_bytes,
    )


def _work_peak_bytes(work: Any) -> int:
    return int(
        getattr(
            work,
            "estimated_peak_host_numeric_bytes",
            getattr(work, "estimated_peak_total_numeric_bytes", 0),
        )
    )


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def _required(values: np.ndarray | None) -> np.ndarray:
    if values is None:
        raise AssertionError("response cache child was not available")
    return values


def _sum_children(children: tuple[np.ndarray, ...]) -> np.ndarray:
    return np.ascontiguousarray(np.sum(np.stack(children, axis=0), axis=0), dtype=np.float64)
