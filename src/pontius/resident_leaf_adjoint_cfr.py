"""Alternating CFR through the device-resident leaf-adjoint contraction.

This module changes only the terminal contraction boundary of
``LeafAdjointPublicTreeCFR``.  The public-tree reverse adjoint, regret update,
own-reach averaging, and discount recurrence deliberately match the transferred
solver so that residency is an implementation change rather than a new CFR
algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Mapping

import numpy as np

from .game import TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import (
    LeafAdjointPublicTreeCFR,
    _parent_metadata,
    _readonly,
    _readonly_bool,
    _required,
    _target_omitted_path_factors,
)
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _terminal_keys_by_slot
from .public_tree_tensor import PublicTreeTensorEvaluator
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
    ResidentHeterogeneousLeafWork,
    contract_resident_heterogeneous_leaf_terms,
)
from .river import HoleCards
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .sparse_open_mode_cfr import SparseCFRRegretRead
from .structured_showdown_automaton import StructuredShowdownAutomaton
from .updates import SolverVariant


@dataclass(frozen=True, slots=True)
class ResidentLeafAdjointTraverserResult:
    traverser: int
    reads: tuple[SparseCFRRegretRead, ...]
    terminal_contractions: int
    terminal_sparse_batches: int
    terminal_contraction_ms: float
    reverse_adjoint_ms: float
    maximum_child_reach_disagreement: float
    maximum_terminal_middle_rank: int
    maximum_terminal_peak_numeric_bytes: int
    maximum_gpu_pool_total_bytes: int
    resident_work: ResidentHeterogeneousLeafWork


@dataclass(frozen=True, slots=True)
class ResidentLeafAdjointStepTraverserWork:
    traverser: int
    probability_compile_ms: float
    own_reach_and_average_ms: float
    terminal_contraction_ms: float
    reverse_adjoint_ms: float
    regret_apply_ms: float
    terminal_contractions: int
    terminal_sparse_batches: int
    strategic_reads: int
    hand_action_entries: int
    maximum_child_reach_disagreement: float
    maximum_terminal_middle_rank: int
    maximum_terminal_peak_numeric_bytes: int
    maximum_gpu_pool_total_bytes: int
    resident_work: ResidentHeterogeneousLeafWork


@dataclass(frozen=True, slots=True)
class ResidentLeafAdjointStepWork:
    iteration: int
    wall_ms: float
    discount_ms: float
    traversers: tuple[ResidentLeafAdjointStepTraverserWork, ...]

    @property
    def terminal_contraction_ms(self) -> float:
        return sum(row.terminal_contraction_ms for row in self.traversers)


class ResidentLeafAdjointPublicTreeCFR(LeafAdjointPublicTreeCFR):
    """Leaf-adjoint CFR with static belief and automaton tensors on the GPU."""

    def __init__(
        self,
        layout: PublicTreeTensorEvaluator,
        workspace: OpenModeFactorTTWorkspace,
        sparse: SparseBidirectionalIncidence,
        terminal_automata: tuple[
            Mapping[str, StructuredShowdownAutomaton], ...
        ],
        variant: SolverVariant = "cfr",
        *,
        belief_cache: CuPyResidentBeliefCache,
        automaton_caches: tuple[CuPyResidentAutomatonCache, ...],
        cupy_sparse: Any,
        maximum_feature_width_per_batch: int = 384,
        hands_by_player: tuple[tuple[HoleCards, ...], ...] | None = None,
    ) -> None:
        super().__init__(
            layout,
            workspace,
            sparse,
            terminal_automata,
            variant,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            terminal_batch_mode="heterogeneous",
            hands_by_player=hands_by_player,
            cupy_sparse=cupy_sparse,
        )
        if belief_cache.workspace is not workspace:
            raise ValueError("resident CFR belief cache belongs to another workspace")
        if len(automaton_caches) != layout.num_players:
            raise ValueError("resident CFR requires one automaton cache per player")
        for seat, cache in enumerate(automaton_caches):
            if cache.topology is not workspace.topology or cache.target_seat != seat:
                raise ValueError("resident CFR automaton cache differs from its seat")
            expected_ids = frozenset(
                id(automaton) for automaton in self.terminal_automata[seat].values()
            )
            if cache.automaton_ids != expected_ids:
                raise ValueError("resident CFR automaton library differs from cache")
        self.belief_cache = belief_cache
        self.automaton_caches = automaton_caches
        self.last_step_work: ResidentLeafAdjointStepWork | None = None

    def step(self) -> None:
        """Run one alternating update without transferring terminal features."""

        step_started = time.perf_counter()
        self.iteration += 1
        traverser_work = []
        for traverser in range(self.num_players):
            started = time.perf_counter()
            probabilities = self.immutable_strategies()
            probability_ms = (time.perf_counter() - started) * 1000.0

            started = time.perf_counter()
            self.accumulate_average_for_traverser(traverser, probabilities)
            own_reach_ms = (time.perf_counter() - started) * 1000.0

            result = resident_leaf_adjoint_cfr_traverser(
                self.layout,
                self.workspace,
                self.sparse,
                probabilities,
                self.terminal_automata[traverser],
                traverser=traverser,
                belief_cache=self.belief_cache,
                automaton_cache=self.automaton_caches[traverser],
                cupy_sparse=self.cupy_sparse,
                maximum_feature_width_per_batch=(
                    self.maximum_feature_width_per_batch
                ),
            )
            started = time.perf_counter()
            entries = 0
            for read in result.reads:
                regrets = self._regrets[read.node_index]
                if regrets is None:
                    raise AssertionError("resident CFR traverser node has no regrets")
                regrets += read.regret_deltas
                if self.update_rule.clip_regrets:
                    np.maximum(regrets, 0.0, out=regrets)
                entries += read.regret_deltas.size
            regret_ms = (time.perf_counter() - started) * 1000.0
            traverser_work.append(
                ResidentLeafAdjointStepTraverserWork(
                    traverser=traverser,
                    probability_compile_ms=probability_ms,
                    own_reach_and_average_ms=own_reach_ms,
                    terminal_contraction_ms=result.terminal_contraction_ms,
                    reverse_adjoint_ms=result.reverse_adjoint_ms,
                    regret_apply_ms=regret_ms,
                    terminal_contractions=result.terminal_contractions,
                    terminal_sparse_batches=result.terminal_sparse_batches,
                    strategic_reads=len(result.reads),
                    hand_action_entries=entries,
                    maximum_child_reach_disagreement=(
                        result.maximum_child_reach_disagreement
                    ),
                    maximum_terminal_middle_rank=(
                        result.maximum_terminal_middle_rank
                    ),
                    maximum_terminal_peak_numeric_bytes=(
                        result.maximum_terminal_peak_numeric_bytes
                    ),
                    maximum_gpu_pool_total_bytes=(
                        result.maximum_gpu_pool_total_bytes
                    ),
                    resident_work=result.resident_work,
                )
            )

        started = time.perf_counter()
        self._discount_accumulators()
        discount_ms = (time.perf_counter() - started) * 1000.0
        self.last_step_work = ResidentLeafAdjointStepWork(
            iteration=self.iteration,
            wall_ms=(time.perf_counter() - step_started) * 1000.0,
            discount_ms=discount_ms,
            traversers=tuple(traverser_work),
        )

    def memory_summary(self) -> dict[str, int]:
        summary = super().memory_summary()
        summary.update(
            {
                "resident_belief_numeric_bytes": self.belief_cache.numeric_bytes,
                "resident_automaton_numeric_bytes": sum(
                    cache.numeric_bytes for cache in self.automaton_caches
                ),
            }
        )
        return summary


def resident_leaf_adjoint_cfr_traverser(
    layout: PublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, StructuredShowdownAutomaton],
    *,
    traverser: int,
    belief_cache: CuPyResidentBeliefCache,
    automaton_cache: CuPyResidentAutomatonCache,
    cupy_sparse: Any,
    maximum_feature_width_per_batch: int = 384,
    zero_reach_value: float = 0.0,
) -> ResidentLeafAdjointTraverserResult:
    """Compute one traverser's CFR action tables through resident leaves."""

    if isinstance(traverser, bool) or traverser not in range(layout.num_players):
        raise ValueError("resident CFR traverser is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("resident CFR sparse topology and workspace differ")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("resident CFR probability tape differs from public tree")
    terminal_keys = _terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("resident CFR automata differ from terminal payoff groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("resident CFR automaton axes differ from open workspace")
    if belief_cache.workspace is not workspace:
        raise ValueError("resident CFR belief cache belongs to another workspace")
    if automaton_cache.target_seat != traverser:
        raise ValueError("resident CFR automaton cache belongs to another traverser")
    if cupy_sparse.cpu is not sparse:
        raise ValueError("resident CFR CuPy operators differ from CPU topology")

    parents, parent_actions = _parent_metadata(layout)
    node_values: list[np.ndarray | None] = [None] * layout.public_node_count
    node_reaches: list[np.ndarray | None] = [None] * layout.public_node_count
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
                traverser=traverser,
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
        target_seat=traverser,
        belief_cache=belief_cache,
        automaton_cache=automaton_cache,
        cupy_sparse=cupy_sparse,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        zero_reach_value=zero_reach_value,
    )
    contraction_ms = (time.perf_counter() - contraction_started) * 1000.0
    for node_index, values in contraction.values:
        node_values[node_index] = np.array(
            values.root_normalized_numerators,
            dtype=np.float64,
            order="C",
            copy=True,
        )
        node_reaches[node_index] = np.array(
            values.root_normalized_reaches,
            dtype=np.float64,
            order="C",
            copy=True,
        )

    reverse_started = time.perf_counter()
    reads = []
    maximum_reach_disagreement = 0.0
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continue
        child_values = tuple(_required(node_values[child]) for child in node.children)
        child_reaches = tuple(_required(node_reaches[child]) for child in node.children)
        if node.player == traverser:
            node_probabilities = probabilities[node_index]
            if node_probabilities is None:
                raise ValueError("resident CFR traverser node has no probabilities")
            action_numerators = np.ascontiguousarray(
                np.column_stack(child_values),
                dtype=np.float64,
            )
            action_reaches = np.ascontiguousarray(
                np.column_stack(child_reaches),
                dtype=np.float64,
            )
            policy_values = np.einsum(
                "ha,ha->h",
                node_probabilities,
                action_numerators,
                optimize=True,
            )
            reaches = np.einsum(
                "ha,ha->h",
                node_probabilities,
                action_reaches,
                optimize=True,
            )
            if action_reaches.shape[1] > 1:
                maximum_reach_disagreement = max(
                    maximum_reach_disagreement,
                    float(
                        np.max(
                            np.max(action_reaches, axis=1)
                            - np.min(action_reaches, axis=1)
                        )
                    ),
                )
            positive = reaches > 0.0
            conditional = np.full_like(action_numerators, zero_reach_value)
            np.divide(
                action_numerators,
                reaches[:, None],
                out=conditional,
                where=positive[:, None],
            )
            regret_deltas = action_numerators - policy_values[:, None]
            regret_deltas[~positive] = 0.0
            reads.append(
                SparseCFRRegretRead(
                    node_index=node_index,
                    target_seat=traverser,
                    actions=node.actions,
                    counterfactual_reaches=_readonly(reaches),
                    action_numerators=_readonly(action_numerators),
                    conditional_action_values=_readonly(conditional),
                    positive_reach=_readonly_bool(positive),
                    policy_values=_readonly(policy_values),
                    regret_deltas=_readonly(regret_deltas),
                    zero_reach_hands=int(np.count_nonzero(~positive)),
                )
            )
            node_values[node_index] = policy_values
            node_reaches[node_index] = reaches
        else:
            node_values[node_index] = np.ascontiguousarray(
                np.sum(np.stack(child_values, axis=0), axis=0),
                dtype=np.float64,
            )
            node_reaches[node_index] = np.ascontiguousarray(
                np.sum(np.stack(child_reaches, axis=0), axis=0),
                dtype=np.float64,
            )

    work = contraction.work
    return ResidentLeafAdjointTraverserResult(
        traverser=traverser,
        reads=tuple(sorted(reads, key=lambda row: row.node_index)),
        terminal_contractions=len(terms),
        terminal_sparse_batches=work.batches,
        terminal_contraction_ms=contraction_ms,
        reverse_adjoint_ms=(time.perf_counter() - reverse_started) * 1000.0,
        maximum_child_reach_disagreement=maximum_reach_disagreement,
        maximum_terminal_middle_rank=work.maximum_middle_rank,
        maximum_terminal_peak_numeric_bytes=work.estimated_peak_host_numeric_bytes,
        maximum_gpu_pool_total_bytes=work.maximum_gpu_pool_total_bytes,
        resident_work=work,
    )
