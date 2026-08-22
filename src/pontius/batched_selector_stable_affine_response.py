"""Batch several opponent-conditioned affine directions through one GPU call.

The accepted scalar affine verifier evaluates one candidate and one responding
seat at a time.  This module preserves that algebra while packing all candidate
terminal terms for a fixed responding seat into one heterogeneous resident
contraction.  Acting-seat rows are deliberately out of scope: their own best
response is policy-invariant and requires no opponent-conditioned contraction.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import numpy as np

from .game import TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_leaf_adjoint_response import (
    LeafAdjointResponseSeatCache,
    _contract,
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
class BatchedSelectorStableAffineOpponentWork:
    """Shared work for one responding seat across several acting-seat edits."""

    target_player: int
    candidate_rows: int
    contraction_calls: int
    affected_terminal_contractions: int
    terminal_sparse_batches: int
    term_prepare_ms: float
    terminal_contraction_ms: float
    reverse_evaluation_ms: float
    wall_ms: float
    maximum_terminal_middle_rank: int
    maximum_gpu_pool_used_bytes: int
    maximum_gpu_pool_total_bytes: int
    factor_prepare_ms: float
    factor_upload_ms: float
    product_generation_gpu_ms: float
    resident_pipeline_gpu_ms: float
    device_to_host_ms: float
    hand_fold_ms: float


@dataclass(frozen=True, slots=True)
class BatchedSelectorStableAffineOpponentResult:
    """Scalar-compatible semantic rows plus their one shared timing ledger."""

    seat_results: tuple[SelectorStableAffineSeatResult, ...]
    work: BatchedSelectorStableAffineOpponentWork


def evaluate_batched_selector_stable_affine_opponents(
    cache: LeafAdjointResponseSeatCache,
    endpoint_probabilities: tuple[PolicyProbabilityTape, ...],
    *,
    acting_players: tuple[int, ...],
    selector_margin_allowance: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
    belief_cache: Any | None = None,
    automaton_cache: Any | None = None,
    cupy_sparse: Any | None = None,
) -> BatchedSelectorStableAffineOpponentResult:
    """Evaluate many opponent edits for one responding seat in one contraction.

    The returned scalar rows carry zero ``terminal_contraction_ms`` because the
    device work is shared and cannot be assigned additively to one candidate.
    Customers must charge ``result.work`` exactly once.
    """

    started = time.perf_counter()
    if not endpoint_probabilities:
        raise ValueError("batched affine opponent evaluation requires candidates")
    if len(endpoint_probabilities) != len(acting_players):
        raise ValueError("batched affine opponent candidate and actor counts differ")
    if not np.isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("batched affine selector allowance must be finite and nonnegative")

    layout = cache.layout
    terminal_keys = _terminal_keys_by_slot(layout)
    shape = cache.workspace.topology.base.hand_counts
    term_started = time.perf_counter()
    changed_nodes: list[int] = []
    candidate_term_counts: list[int] = []
    terms: list[HeterogeneousLeafTerm] = []
    for candidate_index, (endpoint, acting_player) in enumerate(
        zip(endpoint_probabilities, acting_players, strict=True)
    ):
        _validate_probability_tape(layout, cache.hands_by_player, endpoint)
        if (
            isinstance(acting_player, bool)
            or acting_player not in range(layout.num_players)
        ):
            raise ValueError("batched affine acting player is outside the layout")
        if acting_player == cache.target_player:
            raise ValueError("batched affine path accepts opponent edits only")
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
            raise ValueError(
                "batched affine scope requires exactly one changed public node"
            )
        changed_node = changed[0]
        if layout.nodes[changed_node].player != acting_player:
            raise ValueError("batched affine changed node belongs to another player")
        changed_nodes.append(changed_node)

        before = len(terms)
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
                for first, second in zip(
                    source_factors, endpoint_factors, strict=True
                )
            ):
                continue
            terms.append(
                HeterogeneousLeafTerm(
                    key=candidate_index * layout.public_node_count + node_index,
                    automaton=cache.terminal_automata[
                        terminal_keys[node.terminal_slot]
                    ],
                    mode_factors=endpoint_factors,
                )
            )
        candidate_term_counts.append(len(terms) - before)
    term_prepare_ms = (time.perf_counter() - term_started) * 1000.0

    endpoint_terminal_values = [list(cache.terminal_values) for _ in changed_nodes]
    contraction_ms = 0.0
    contraction_calls = 0
    sparse_batches = 0
    maximum_rank = 0
    maximum_used = 0
    maximum_pool = 0
    component_times = {
        "factor_prepare_ms": 0.0,
        "factor_upload_ms": 0.0,
        "product_generation_gpu_ms": 0.0,
        "resident_pipeline_gpu_ms": 0.0,
        "device_to_host_ms": 0.0,
        "hand_fold_ms": 0.0,
    }
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
        contraction_calls = 1
        sparse_batches = int(contraction.work.batches)
        maximum_rank = int(contraction.work.maximum_middle_rank)
        maximum_used = int(
            getattr(contraction.work, "maximum_gpu_pool_used_bytes", 0)
        )
        maximum_pool = int(
            getattr(contraction.work, "maximum_gpu_pool_total_bytes", 0)
        )
        for field in component_times:
            component_times[field] = float(getattr(contraction.work, field, 0.0))
        for supplied_key, values in contraction.values:
            candidate_index, node_index = divmod(
                int(supplied_key), layout.public_node_count
            )
            endpoint_terminal_values[candidate_index][node_index] = _readonly(
                values.root_normalized_numerators
            )

    reverse_ms = 0.0
    rows = []
    source = cache.source_evaluation
    for candidate_index, (endpoint, acting_player, changed_node) in enumerate(
        zip(
            endpoint_probabilities,
            acting_players,
            changed_nodes,
            strict=True,
        )
    ):
        reverse_started = time.perf_counter()
        affine = _selector_stable_affine_reverse(
            layout,
            cache.source_probabilities,
            endpoint,
            list(cache.terminal_values),
            endpoint_terminal_values[candidate_index],
            target_player=cache.target_player,
            hands_by_player=cache.hands_by_player,
            source_actions=source.best_response_actions,
            selector_margin_allowance=selector_margin_allowance,
        )
        row_reverse_ms = (time.perf_counter() - reverse_started) * 1000.0
        reverse_ms += row_reverse_ms
        identity_error = max(
            abs(affine["profile_utility_intercept"] - source.profile_utility),
            abs(
                affine["best_response_value_intercept"]
                - source.best_response_value
            ),
            abs(affine["deviation_gain_intercept"] - source.deviation_gain),
        )
        if identity_error > max(1e-12, selector_margin_allowance):
            raise ArithmeticError(
                "batched affine response intercept differs from source cache"
            )
        rows.append(
            SelectorStableAffineSeatResult(
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
                first_switch_information_key=affine[
                    "first_switch_information_key"
                ],
                first_switch_source_action=affine["first_switch_source_action"],
                first_switch_competing_action=affine[
                    "first_switch_competing_action"
                ],
                first_switch_hand_index=affine["first_switch_hand_index"],
                selector_comparisons=affine["selector_comparisons"],
                exact_source_action_ties=affine["exact_source_action_ties"],
                changed_public_nodes=1,
                changed_opponent_public_nodes=1,
                affected_terminal_contractions=candidate_term_counts[candidate_index],
                full_terminal_contractions=cache.terminal_contractions,
                reused_terminal_numerators=(
                    cache.terminal_contractions
                    - candidate_term_counts[candidate_index]
                ),
                terminal_contraction_ms=0.0,
                reverse_evaluation_ms=row_reverse_ms,
                wall_ms=row_reverse_ms,
                maximum_terminal_middle_rank=maximum_rank,
                maximum_gpu_pool_total_bytes=maximum_pool,
            )
        )

    return BatchedSelectorStableAffineOpponentResult(
        seat_results=tuple(rows),
        work=BatchedSelectorStableAffineOpponentWork(
            target_player=cache.target_player,
            candidate_rows=len(rows),
            contraction_calls=contraction_calls,
            affected_terminal_contractions=len(terms),
            terminal_sparse_batches=sparse_batches,
            term_prepare_ms=term_prepare_ms,
            terminal_contraction_ms=contraction_ms,
            reverse_evaluation_ms=reverse_ms,
            wall_ms=(time.perf_counter() - started) * 1000.0,
            maximum_terminal_middle_rank=maximum_rank,
            maximum_gpu_pool_used_bytes=maximum_used,
            maximum_gpu_pool_total_bytes=maximum_pool,
            **component_times,
        ),
    )
