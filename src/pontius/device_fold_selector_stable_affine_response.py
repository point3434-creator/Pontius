"""Selector-stable affine responses through the additive device-fold path."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import numpy as np

from .device_fold_resident_heterogeneous_leaf_contraction import (
    DeviceFoldResidentHeterogeneousLeafWork,
    contract_device_fold_resident_heterogeneous_leaf_terms,
)
from .game import TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_leaf_adjoint_response import (
    LeafAdjointResponseSeatCache,
    _readonly,
    _validate_probability_tape,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import _target_omitted_path_factors
from .public_policy_tt import _terminal_keys_by_slot
from .selector_stable_affine_response import (
    SelectorStableAffineSeatResult,
    _selector_stable_affine_reverse,
)


@dataclass(frozen=True, slots=True)
class DeviceFoldSelectorStableAffineResult:
    semantic: SelectorStableAffineSeatResult
    work: DeviceFoldResidentHeterogeneousLeafWork | None


@dataclass(frozen=True, slots=True)
class DeviceFoldBatchedSelectorWork:
    target_player: int
    candidate_rows: int
    contraction_calls: int
    affected_terminal_contractions: int
    terminal_sparse_batches: int
    term_prepare_ms: float
    terminal_contraction_ms: float
    reverse_evaluation_ms: float
    wall_ms: float
    contraction: DeviceFoldResidentHeterogeneousLeafWork | None


@dataclass(frozen=True, slots=True)
class DeviceFoldBatchedSelectorResult:
    seat_results: tuple[SelectorStableAffineSeatResult, ...]
    work: DeviceFoldBatchedSelectorWork


def _changed_node(
    cache: LeafAdjointResponseSeatCache,
    endpoint: PolicyProbabilityTape,
    *,
    acting_player: int,
) -> int:
    layout = cache.layout
    _validate_probability_tape(layout, cache.hands_by_player, endpoint)
    if isinstance(acting_player, bool) or acting_player not in range(layout.num_players):
        raise ValueError("device-fold affine actor is outside the layout")
    changed = tuple(
        node_index
        for node_index, (source, candidate) in enumerate(
            zip(cache.source_probabilities, endpoint, strict=True)
        )
        if source is not None
        and candidate is not None
        and not np.array_equal(source, candidate)
    )
    if len(changed) != 1:
        raise ValueError("device-fold affine scope requires one changed public node")
    if layout.nodes[changed[0]].player != acting_player:
        raise ValueError("device-fold affine node belongs to another actor")
    return changed[0]


def _terms(
    cache: LeafAdjointResponseSeatCache,
    endpoint: PolicyProbabilityTape,
    *,
    supplied_key_offset: int = 0,
) -> tuple[HeterogeneousLeafTerm, ...]:
    layout = cache.layout
    terminal_keys = _terminal_keys_by_slot(layout)
    shape = cache.workspace.topology.base.hand_counts
    rows = []
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
            endpoint,
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
        rows.append(
            HeterogeneousLeafTerm(
                key=supplied_key_offset + node_index,
                automaton=cache.terminal_automata[terminal_keys[node.terminal_slot]],
                mode_factors=endpoint_factors,
            )
        )
    return tuple(rows)


def _semantic_row(
    cache: LeafAdjointResponseSeatCache,
    endpoint: PolicyProbabilityTape,
    *,
    acting_player: int,
    changed_node: int,
    endpoint_terminal_values: list[np.ndarray | None],
    selector_margin_allowance: float,
    affected_terms: int,
    terminal_contraction_ms: float,
    reverse_started: float,
    maximum_rank: int,
    maximum_pool: int,
) -> SelectorStableAffineSeatResult:
    affine = _selector_stable_affine_reverse(
        cache.layout,
        cache.source_probabilities,
        endpoint,
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
        raise ArithmeticError("device-fold affine intercept differs from source")
    return SelectorStableAffineSeatResult(
        target_player=cache.target_player,
        acting_player=acting_player,
        changed_public_node=changed_node,
        profile_utility_intercept=affine["profile_utility_intercept"],
        profile_utility_slope=affine["profile_utility_slope"],
        best_response_value_intercept=affine["best_response_value_intercept"],
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
        changed_opponent_public_nodes=int(acting_player != cache.target_player),
        affected_terminal_contractions=affected_terms,
        full_terminal_contractions=cache.terminal_contractions,
        reused_terminal_numerators=cache.terminal_contractions - affected_terms,
        terminal_contraction_ms=terminal_contraction_ms,
        reverse_evaluation_ms=reverse_ms,
        wall_ms=terminal_contraction_ms + reverse_ms,
        maximum_terminal_middle_rank=maximum_rank,
        maximum_gpu_pool_total_bytes=maximum_pool,
    )


def evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
    cache: LeafAdjointResponseSeatCache,
    endpoint_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    selector_margin_allowance: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any,
    automaton_cache: Any,
    cupy_sparse: Any,
) -> DeviceFoldSelectorStableAffineResult:
    """Evaluate one opponent coefficient with device record folding."""

    if not np.isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("device-fold selector allowance must be nonnegative")
    changed = _changed_node(
        cache, endpoint_probabilities, acting_player=acting_player
    )
    if acting_player == cache.target_player:
        raise ValueError("device-fold affine path accepts opponent edits only")
    terms = _terms(cache, endpoint_probabilities)
    endpoint_values = list(cache.terminal_values)
    contraction_ms = 0.0
    work = None
    maximum_rank = 0
    maximum_pool = 0
    if terms:
        started = time.perf_counter()
        contraction = contract_device_fold_resident_heterogeneous_leaf_terms(
            cache.workspace,
            cache.sparse,
            terms,
            target_seat=cache.target_player,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=cupy_sparse,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        contraction_ms = (time.perf_counter() - started) * 1000.0
        work = contraction.work
        maximum_rank = work.maximum_middle_rank
        maximum_pool = work.maximum_gpu_pool_total_bytes
        for node_index, values in contraction.values:
            endpoint_values[node_index] = _readonly(values.root_normalized_numerators)
    reverse_started = time.perf_counter()
    semantic = _semantic_row(
        cache,
        endpoint_probabilities,
        acting_player=acting_player,
        changed_node=changed,
        endpoint_terminal_values=endpoint_values,
        selector_margin_allowance=selector_margin_allowance,
        affected_terms=len(terms),
        terminal_contraction_ms=contraction_ms,
        reverse_started=reverse_started,
        maximum_rank=maximum_rank,
        maximum_pool=maximum_pool,
    )
    return DeviceFoldSelectorStableAffineResult(semantic=semantic, work=work)


def evaluate_device_fold_batched_selector_stable_affine_opponents(
    cache: LeafAdjointResponseSeatCache,
    endpoint_probabilities: tuple[PolicyProbabilityTape, ...],
    *,
    acting_players: tuple[int, ...],
    selector_margin_allowance: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any,
    automaton_cache: Any,
    cupy_sparse: Any,
) -> DeviceFoldBatchedSelectorResult:
    """Pack several opponent directions and fold their records on-device."""

    wall_started = time.perf_counter()
    if not endpoint_probabilities:
        raise ValueError("device-fold batch requires candidates")
    if len(endpoint_probabilities) != len(acting_players):
        raise ValueError("device-fold batch candidate and actor counts differ")
    if not np.isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("device-fold selector allowance must be nonnegative")

    term_started = time.perf_counter()
    changed_nodes = []
    term_counts = []
    terms = []
    for candidate_index, (endpoint, acting_player) in enumerate(
        zip(endpoint_probabilities, acting_players, strict=True)
    ):
        changed_nodes.append(
            _changed_node(cache, endpoint, acting_player=acting_player)
        )
        if acting_player == cache.target_player:
            raise ValueError("device-fold batch accepts opponent edits only")
        candidate_terms = _terms(
            cache,
            endpoint,
            supplied_key_offset=candidate_index * cache.layout.public_node_count,
        )
        term_counts.append(len(candidate_terms))
        terms.extend(candidate_terms)
    term_prepare_ms = (time.perf_counter() - term_started) * 1000.0

    endpoint_values = [list(cache.terminal_values) for _ in endpoint_probabilities]
    contraction_ms = 0.0
    contraction_work = None
    if terms:
        started = time.perf_counter()
        contraction = contract_device_fold_resident_heterogeneous_leaf_terms(
            cache.workspace,
            cache.sparse,
            tuple(terms),
            target_seat=cache.target_player,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=cupy_sparse,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        contraction_ms = (time.perf_counter() - started) * 1000.0
        contraction_work = contraction.work
        for supplied_key, values in contraction.values:
            candidate_index, node_index = divmod(
                int(supplied_key), cache.layout.public_node_count
            )
            endpoint_values[candidate_index][node_index] = _readonly(
                values.root_normalized_numerators
            )

    rows = []
    reverse_ms = 0.0
    maximum_rank = 0 if contraction_work is None else contraction_work.maximum_middle_rank
    maximum_pool = (
        0 if contraction_work is None else contraction_work.maximum_gpu_pool_total_bytes
    )
    for index, (endpoint, acting_player, changed) in enumerate(
        zip(
            endpoint_probabilities,
            acting_players,
            changed_nodes,
            strict=True,
        )
    ):
        reverse_started = time.perf_counter()
        row = _semantic_row(
            cache,
            endpoint,
            acting_player=acting_player,
            changed_node=changed,
            endpoint_terminal_values=endpoint_values[index],
            selector_margin_allowance=selector_margin_allowance,
            affected_terms=term_counts[index],
            terminal_contraction_ms=0.0,
            reverse_started=reverse_started,
            maximum_rank=maximum_rank,
            maximum_pool=maximum_pool,
        )
        reverse_ms += row.reverse_evaluation_ms
        rows.append(row)
    return DeviceFoldBatchedSelectorResult(
        seat_results=tuple(rows),
        work=DeviceFoldBatchedSelectorWork(
            target_player=cache.target_player,
            candidate_rows=len(rows),
            contraction_calls=int(bool(terms)),
            affected_terminal_contractions=len(terms),
            terminal_sparse_batches=(
                0 if contraction_work is None else contraction_work.batches
            ),
            term_prepare_ms=term_prepare_ms,
            terminal_contraction_ms=contraction_ms,
            reverse_evaluation_ms=reverse_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            contraction=contraction_work,
        ),
    )
