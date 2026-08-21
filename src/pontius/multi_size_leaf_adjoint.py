"""Contribution-aware terminal groups and leaf adjoints for sized river bets."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
import time
from typing import Any

import numpy as np

from .game import TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import (
    LeafAdjointTraverserResult,
    _parent_metadata,
    _readonly,
    _readonly_bool,
    _required,
    _target_omitted_path_factors,
)
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .sparse_open_mode_cfr import SparseCFRRegretRead
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)


@dataclass(frozen=True, slots=True)
class MultiSizeTerminalGroup:
    """Terminal slots sharing contenders and one common contribution."""

    key: str
    contenders: tuple[int, ...]
    contribution: float
    terminal_slots: tuple[int, ...]

    @property
    def contributed(self) -> bool:
        return self.contribution > 0.0


def multi_size_terminal_groups(
    layout: MultiSizePublicTreeTensorEvaluator,
) -> tuple[MultiSizeTerminalGroup, ...]:
    """Group sized terminal slots without erasing the selected bet amount."""

    if not isinstance(layout, MultiSizePublicTreeTensorEvaluator):
        raise TypeError("sized terminal groups require the sized public-tree layout")
    grouped: dict[tuple[tuple[int, ...], float], list[int]] = defaultdict(list)
    for node in layout.nodes:
        if node.player != TERMINAL_PLAYER:
            continue
        descriptor = layout.terminal_descriptors[node.terminal_slot]
        grouped[descriptor].append(node.terminal_slot)

    groups = []
    for (contenders, contribution), slots in sorted(grouped.items()):
        contender_text = "_".join(map(str, contenders))
        key = (
            "all_check"
            if contribution == 0.0
            else f"bet_{contribution.hex()}__contenders_{contender_text}"
        )
        groups.append(
            MultiSizeTerminalGroup(
                key=key,
                contenders=contenders,
                contribution=contribution,
                terminal_slots=tuple(sorted(slots)),
            )
        )
    if len(groups) != layout.unique_terminal_descriptor_count:
        raise AssertionError("sized terminal grouping lost a payoff descriptor")
    return tuple(groups)


def multi_size_terminal_keys_by_slot(
    layout: MultiSizePublicTreeTensorEvaluator,
) -> tuple[str, ...]:
    result: list[str | None] = [None] * layout.terminal_node_count
    for group in multi_size_terminal_groups(layout):
        for slot in group.terminal_slots:
            if result[slot] is not None:
                raise AssertionError("sized terminal slot belongs to multiple groups")
            result[slot] = group.key
    if any(key is None for key in result):
        raise AssertionError("one sized terminal slot has no payoff group")
    return tuple(key for key in result if key is not None)


def build_multi_size_leaf_adjoint_terminal_automata(
    layout: MultiSizePublicTreeTensorEvaluator,
    strength_codes: tuple[np.ndarray, ...],
    *,
    pot: float,
) -> tuple[dict[str, StructuredShowdownAutomaton], ...]:
    """Build one exact contribution-aware automaton per group and target."""

    if len(strength_codes) != layout.num_players:
        raise ValueError("sized leaf-adjoint strengths require one axis per player")
    groups = multi_size_terminal_groups(layout)
    return tuple(
        {
            group.key: build_structured_showdown_automaton(
                strength_codes=strength_codes,
                contenders=group.contenders,
                target_player=target,
                contributed=group.contributed,
                pot=pot,
                bet_size=group.contribution,
            )
            for group in groups
        }
        for target in range(layout.num_players)
    )


def multi_size_leaf_adjoint_cfr_traverser(
    layout: MultiSizePublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, StructuredShowdownAutomaton],
    *,
    traverser: int,
    maximum_feature_width_per_batch: int = 96,
    zero_reach_value: float = 0.0,
    cupy_sparse: Any | None = None,
) -> LeafAdjointTraverserResult:
    """Compute exact sized-tree CFR action tables from terminal adjoints."""

    if isinstance(traverser, bool) or traverser not in range(layout.num_players):
        raise ValueError("sized leaf-adjoint traverser is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("sized leaf-adjoint topology and workspace differ")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("sized leaf-adjoint probability tape differs from tree")
    terminal_keys = multi_size_terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("sized leaf-adjoint automata differ from terminal groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("sized leaf-adjoint automata differ from belief axes")
    if cupy_sparse is not None and cupy_sparse.cpu is not sparse:
        raise ValueError("sized leaf-adjoint CuPy operators differ from CPU topology")

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

    started = time.perf_counter()
    contraction = contract_heterogeneous_leaf_terms(
        workspace,
        sparse,
        terms,
        target_seat=traverser,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        zero_reach_value=zero_reach_value,
        cupy_sparse=cupy_sparse,
    )
    contraction_ms = (time.perf_counter() - started) * 1000.0
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
    reads: list[SparseCFRRegretRead] = []
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
                raise ValueError("sized leaf-adjoint node has no probabilities")
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

    return LeafAdjointTraverserResult(
        traverser=traverser,
        reads=tuple(sorted(reads, key=lambda row: row.node_index)),
        terminal_contractions=len(terms),
        terminal_sparse_batches=contraction.work.batches,
        terminal_contraction_ms=contraction_ms,
        reverse_adjoint_ms=(time.perf_counter() - reverse_started) * 1000.0,
        maximum_child_reach_disagreement=maximum_reach_disagreement,
        maximum_terminal_middle_rank=contraction.work.maximum_middle_rank,
        maximum_terminal_peak_numeric_bytes=(
            contraction.work.estimated_peak_total_numeric_bytes
        ),
        maximum_gpu_pool_total_bytes=contraction.work.maximum_gpu_pool_total_bytes,
    )
