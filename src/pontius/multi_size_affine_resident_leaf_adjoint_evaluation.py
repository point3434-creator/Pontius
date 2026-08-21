"""Exact sized-policy evaluation through canonical affine resident leaves."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any, Mapping

import numpy as np

from .affine_resident_heterogeneous_leaf_contraction import (
    CuPyAffineResidentAutomatonCache,
    contract_affine_resident_heterogeneous_leaf_terms,
)
from .evaluation import EvaluationResult, Policy
from .game import Action, TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_policy_tt import (
    PolicyProbabilityTape,
    compile_policy_probability_tape,
)
from .leaf_adjoint_cfr import _parent_metadata, _target_omitted_path_factors
from .leaf_adjoint_evaluation import _external_axes, _required, _sum_children
from .multi_size_leaf_adjoint import multi_size_terminal_keys_by_slot
from .multi_size_policy_bridge import sized_policy_digest
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _information_key
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentBeliefCache,
    ResidentHeterogeneousLeafWork,
)
from .river import HoleCards
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .structured_showdown_automaton import StructuredShowdownAutomaton


@dataclass(frozen=True, slots=True)
class MultiSizeAffineResidentSeatEvaluation:
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


@dataclass(frozen=True, slots=True)
class MultiSizeAffineResidentProfileEvaluation:
    evaluation: EvaluationResult
    policy_sha256: str
    best_response_actions: tuple[dict[str, Action], ...]
    seats: tuple[MultiSizeAffineResidentSeatEvaluation, ...]
    probability_compile_ms: float
    zero_sum_residual: float
    wall_ms: float


def evaluate_multi_size_affine_resident_seat(
    layout: MultiSizePublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, StructuredShowdownAutomaton],
    *,
    target_player: int,
    belief_cache: CuPyResidentBeliefCache,
    automaton_cache: CuPyAffineResidentAutomatonCache,
    cupy_sparse: Any,
    hands_by_player: tuple[tuple[HoleCards, ...], ...] | None = None,
    maximum_feature_width_per_batch: int = 384,
) -> MultiSizeAffineResidentSeatEvaluation:
    """Evaluate one exact unilateral response in a sized public tree."""

    wall_started = time.perf_counter()
    if not isinstance(layout, MultiSizePublicTreeTensorEvaluator):
        raise TypeError("sized affine evaluation requires the sized public tree")
    axes = _external_axes(layout, workspace, hands_by_player)
    if isinstance(target_player, bool) or target_player not in range(layout.num_players):
        raise ValueError("sized affine target is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("sized affine topology and workspace differ")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("sized affine probability tape differs from the tree")
    if belief_cache.workspace is not workspace:
        raise ValueError("sized affine belief cache belongs to another workspace")
    if automaton_cache.topology is not workspace.topology:
        raise ValueError("sized affine automaton cache belongs to another topology")
    if automaton_cache.target_seat != target_player:
        raise ValueError("sized affine automaton cache belongs to another seat")
    if cupy_sparse.cpu is not sparse:
        raise ValueError("sized affine CuPy operators differ from CPU topology")
    terminal_keys = multi_size_terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("sized affine automata differ from payoff groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("sized affine automata differ from hand axes")
    expected_ids = frozenset(id(value) for value in terminal_automata.values())
    if automaton_cache.automaton_ids != expected_ids:
        raise ValueError("sized affine automaton library differs from its cache")

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
    contraction = contract_affine_resident_heterogeneous_leaf_terms(
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
            raise ValueError("sized affine target node has no probabilities")
        profile_scores = np.ascontiguousarray(
            np.column_stack(profile_children), dtype=np.float64
        )
        response_scores = np.ascontiguousarray(
            np.column_stack(response_children), dtype=np.float64
        )
        if not np.all(np.isfinite(profile_scores)) or not np.all(
            np.isfinite(response_scores)
        ):
            raise FloatingPointError("sized affine evaluation produced nonfinite scores")
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
                raise ValueError("sized affine response violates information consistency")

    profile_root = _required(profile_values[0])
    response_root = _required(response_values[0])
    profile_utility = fsum(float(value) for value in profile_root)
    best_response_value = fsum(float(value) for value in response_root)
    work = contraction.work
    return MultiSizeAffineResidentSeatEvaluation(
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


def evaluate_multi_size_affine_resident_profile(
    layout: MultiSizePublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    policy: Policy,
    terminal_automata: tuple[Mapping[str, StructuredShowdownAutomaton], ...],
    *,
    belief_cache: CuPyResidentBeliefCache,
    automaton_caches: tuple[CuPyAffineResidentAutomatonCache, ...],
    cupy_sparse: Any,
    hands_by_player: tuple[tuple[HoleCards, ...], ...] | None = None,
    maximum_feature_width_per_batch: int = 384,
) -> MultiSizeAffineResidentProfileEvaluation:
    """Evaluate a complete sized profile and all six unilateral responses."""

    wall_started = time.perf_counter()
    axes = _external_axes(layout, workspace, hands_by_player)
    if len(terminal_automata) != layout.num_players or len(automaton_caches) != layout.num_players:
        raise ValueError("sized affine profile requires one library and cache per seat")
    probability_started = time.perf_counter()
    probabilities = compile_policy_probability_tape(layout, axes, policy)
    probability_ms = (time.perf_counter() - probability_started) * 1000.0
    seats = tuple(
        evaluate_multi_size_affine_resident_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            terminal_automata[target],
            target_player=target,
            belief_cache=belief_cache,
            automaton_cache=automaton_caches[target],
            cupy_sparse=cupy_sparse,
            hands_by_player=axes,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for target in range(layout.num_players)
    )
    utilities = tuple(row.profile_utility for row in seats)
    responses = tuple(row.best_response_value for row in seats)
    gains = tuple(
        max(0.0, response - utility)
        for response, utility in zip(responses, utilities, strict=True)
    )
    nash_conv = fsum(gains)
    return MultiSizeAffineResidentProfileEvaluation(
        evaluation=EvaluationResult(
            utilities=utilities,
            best_response_values=responses,
            deviation_gains=gains,
            nash_conv=nash_conv,
            exploitability=nash_conv / 2.0 if layout.num_players == 2 else None,
        ),
        policy_sha256=sized_policy_digest(policy),
        best_response_actions=tuple(row.best_response_actions for row in seats),
        seats=seats,
        probability_compile_ms=probability_ms,
        zero_sum_residual=abs(fsum(utilities)),
        wall_ms=(time.perf_counter() - wall_started) * 1000.0,
    )
