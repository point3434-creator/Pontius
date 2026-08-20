"""CFR action tables from target-omitted terminal contractions.

For one traverser, contract every terminal payoff with all opponents' complete
path probabilities and omit every policy factor belonging to the traverser.
A reverse public-tree pass then multiplies the traverser's policies only below
each information set.  The child vectors at a traverser node are exactly its
counterfactual action numerators.  This avoids constructing or rounding any
policy-conditioned public-node value tensor train.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Literal, Mapping

import numpy as np

from .axis_public_cfr import AxisPublicCFRState
from .game import TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _terminal_keys_by_slot
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards
from .showdown_value_rank_screen import _terminal_groups
from .sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
    contract_sparse_open_mode_showdown_batch,
)
from .sparse_open_mode_cfr import SparseCFRRegretRead
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)
from .updates import SolverVariant


@dataclass(frozen=True, slots=True)
class LeafAdjointTraverserResult:
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


@dataclass(frozen=True, slots=True)
class LeafAdjointStepTraverserWork:
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


@dataclass(frozen=True, slots=True)
class LeafAdjointStepWork:
    iteration: int
    wall_ms: float
    discount_ms: float
    traversers: tuple[LeafAdjointStepTraverserWork, ...]

    @property
    def terminal_contraction_ms(self) -> float:
        return sum(row.terminal_contraction_ms for row in self.traversers)


class LeafAdjointPublicTreeCFR(AxisPublicCFRState):
    """Alternating CFR whose backward values are terminal-leaf adjoints."""

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
        maximum_feature_width_per_batch: int = 96,
        terminal_batch_mode: Literal["literal", "heterogeneous"] = "heterogeneous",
        hands_by_player: tuple[tuple[HoleCards, ...], ...] | None = None,
        cupy_sparse: Any | None = None,
    ) -> None:
        axes = layout.hands_by_player if hands_by_player is None else hands_by_player
        super().__init__(layout, axes, variant)
        if sparse.topology is not workspace.topology:
            raise ValueError("leaf-adjoint CFR topology and workspace differ")
        if len(terminal_automata) != layout.num_players:
            raise ValueError("leaf-adjoint CFR requires one automaton library per player")
        if (
            isinstance(maximum_feature_width_per_batch, bool)
            or maximum_feature_width_per_batch < workspace.component_count
        ):
            raise ValueError("leaf-adjoint CFR feature width is too small")
        if terminal_batch_mode not in ("literal", "heterogeneous"):
            raise ValueError("leaf-adjoint CFR terminal batch mode is unknown")
        if cupy_sparse is not None and cupy_sparse.cpu is not sparse:
            raise ValueError("leaf-adjoint CuPy operators differ from CPU topology")
        terminal_keys = set(_terminal_keys_by_slot(layout))
        for library in terminal_automata:
            if set(library) != terminal_keys:
                raise ValueError("leaf-adjoint CFR terminal library is incomplete")
        self.workspace = workspace
        self.sparse = sparse
        self.terminal_automata = tuple(dict(values) for values in terminal_automata)
        self.maximum_feature_width_per_batch = maximum_feature_width_per_batch
        self.terminal_batch_mode = terminal_batch_mode
        self.cupy_sparse = cupy_sparse
        self.last_step_work: LeafAdjointStepWork | None = None

    def step(self) -> None:
        """Run one exact alternating leaf-adjoint update."""

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

            result = leaf_adjoint_cfr_traverser(
                self.layout,
                self.workspace,
                self.sparse,
                probabilities,
                self.terminal_automata[traverser],
                traverser=traverser,
                maximum_feature_width_per_batch=(
                    self.maximum_feature_width_per_batch
                ),
                terminal_batch_mode=self.terminal_batch_mode,
                cupy_sparse=self.cupy_sparse,
            )
            started = time.perf_counter()
            entries = 0
            for read in result.reads:
                regrets = self._regrets[read.node_index]
                if regrets is None:
                    raise AssertionError("leaf-adjoint traverser node has no regrets")
                regrets += read.regret_deltas
                if self.update_rule.clip_regrets:
                    np.maximum(regrets, 0.0, out=regrets)
                entries += read.regret_deltas.size
            regret_ms = (time.perf_counter() - started) * 1000.0
            traverser_work.append(
                LeafAdjointStepTraverserWork(
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
                )
            )

        started = time.perf_counter()
        self._discount_accumulators()
        discount_ms = (time.perf_counter() - started) * 1000.0
        self.last_step_work = LeafAdjointStepWork(
            iteration=self.iteration,
            wall_ms=(time.perf_counter() - step_started) * 1000.0,
            discount_ms=discount_ms,
            traversers=tuple(traverser_work),
        )

    def memory_summary(self) -> dict[str, int]:
        accumulator_bytes = self.accumulator_numeric_bytes()
        unique = {
            id(automaton): automaton
            for library in self.terminal_automata
            for automaton in library.values()
        }
        last_peak = (
            0
            if self.last_step_work is None
            else max(
                row.maximum_terminal_peak_numeric_bytes
                for row in self.last_step_work.traversers
            )
        )
        gpu_peak = (
            0
            if self.last_step_work is None
            else max(
                row.maximum_gpu_pool_total_bytes
                for row in self.last_step_work.traversers
            )
        )
        return {
            "persistent_accumulator_bytes": accumulator_bytes,
            "workspace_numeric_bytes": self.workspace.numeric_bytes,
            "topology_numeric_bytes": self.workspace.topology.numeric_bytes,
            "sparse_operator_numeric_bytes": self.sparse.numeric_bytes,
            "terminal_automaton_numeric_bytes": sum(
                automaton.numeric_bytes for automaton in unique.values()
            ),
            "last_terminal_contraction_peak_numeric_bytes": last_peak,
            "last_gpu_pool_total_bytes": gpu_peak,
        }


def build_leaf_adjoint_terminal_automata(
    layout: PublicTreeTensorEvaluator,
    strength_codes: tuple[np.ndarray, ...],
    *,
    pot: float,
    bet_size: float,
) -> tuple[dict[str, StructuredShowdownAutomaton], ...]:
    """Build one direct automaton per payoff group and target seat."""

    if len(strength_codes) != layout.num_players:
        raise ValueError("leaf-adjoint strengths require one axis per player")
    libraries = []
    groups = _terminal_groups(layout)
    for target in range(layout.num_players):
        libraries.append(
            {
                group.key: build_structured_showdown_automaton(
                    strength_codes=strength_codes,
                    contenders=group.contenders,
                    target_player=target,
                    contributed=group.contributed,
                    pot=pot,
                    bet_size=bet_size,
                )
                for group in groups
            }
        )
    return tuple(libraries)


def leaf_adjoint_cfr_traverser(
    layout: PublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, StructuredShowdownAutomaton],
    *,
    traverser: int,
    maximum_feature_width_per_batch: int = 96,
    zero_reach_value: float = 0.0,
    terminal_batch_mode: Literal["literal", "heterogeneous"] = "literal",
    cupy_sparse: Any | None = None,
) -> LeafAdjointTraverserResult:
    """Compute every CFR regret table for one traverser from terminal leaves."""

    if isinstance(traverser, bool) or traverser not in range(layout.num_players):
        raise ValueError("leaf-adjoint traverser is outside the player seats")
    if sparse.topology is not workspace.topology:
        raise ValueError("leaf-adjoint sparse topology and workspace differ")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("leaf-adjoint probability tape differs from public tree")
    terminal_keys = _terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("leaf-adjoint automata differ from terminal payoff groups")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in terminal_automata.values()):
        raise ValueError("leaf-adjoint automaton axes differ from open workspace")
    if terminal_batch_mode not in ("literal", "heterogeneous"):
        raise ValueError("leaf-adjoint terminal batch mode is unknown")
    if cupy_sparse is not None and cupy_sparse.cpu is not sparse:
        raise ValueError("leaf-adjoint CuPy operators differ from CPU topology")
    if cupy_sparse is not None and terminal_batch_mode != "heterogeneous":
        raise ValueError("leaf-adjoint CuPy requires heterogeneous batching")

    parents, parent_actions = _parent_metadata(layout)
    node_values: list[np.ndarray | None] = [None] * layout.public_node_count
    node_reaches: list[np.ndarray | None] = [None] * layout.public_node_count
    contraction_ms = 0.0
    maximum_rank = 0
    maximum_peak = 0
    terminal_count = 0
    sparse_batches = 0
    maximum_gpu_pool = 0
    terminal_terms = []
    for node_index, node in enumerate(layout.nodes):
        if node.player == TERMINAL_PLAYER:
            terminal_terms.append(
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
            )

    if terminal_batch_mode == "heterogeneous":
        started = time.perf_counter()
        contraction = contract_heterogeneous_leaf_terms(
            workspace,
            sparse,
            tuple(terminal_terms),
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
        terminal_count = len(terminal_terms)
        sparse_batches = contraction.work.batches
        maximum_rank = contraction.work.maximum_middle_rank
        maximum_peak = contraction.work.estimated_peak_total_numeric_bytes
        maximum_gpu_pool = contraction.work.maximum_gpu_pool_total_bytes
    else:
        for term in terminal_terms:
            started = time.perf_counter()
            contraction = contract_sparse_open_mode_showdown_batch(
                workspace,
                sparse,
                (term.automaton,),
                target_seats=(traverser,),
                mode_factors=term.mode_factors,
                zero_reach_value=zero_reach_value,
                maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            )
            contraction_ms += (time.perf_counter() - started) * 1000.0
            values = contraction.for_automaton(0).for_seat(traverser)
            node_values[term.key] = np.array(
                values.root_normalized_numerators,
                dtype=np.float64,
                order="C",
                copy=True,
            )
            node_reaches[term.key] = np.array(
                values.root_normalized_reaches,
                dtype=np.float64,
                order="C",
                copy=True,
            )
            maximum_rank = max(maximum_rank, *contraction.middle_ranks)
            maximum_peak = max(
                maximum_peak,
                contraction.estimated_peak_total_numeric_bytes,
            )
            sparse_batches += sum(work.batches for work in contraction.directions)
            terminal_count += 1

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
                raise ValueError("leaf-adjoint traverser node has no probabilities")
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
        terminal_contractions=terminal_count,
        terminal_sparse_batches=sparse_batches,
        terminal_contraction_ms=contraction_ms,
        reverse_adjoint_ms=(time.perf_counter() - reverse_started) * 1000.0,
        maximum_child_reach_disagreement=maximum_reach_disagreement,
        maximum_terminal_middle_rank=maximum_rank,
        maximum_terminal_peak_numeric_bytes=maximum_peak,
        maximum_gpu_pool_total_bytes=maximum_gpu_pool,
    )


def _parent_metadata(
    layout: PublicTreeTensorEvaluator,
) -> tuple[np.ndarray, np.ndarray]:
    parents = np.full(layout.public_node_count, -1, dtype=np.int32)
    actions = np.full(layout.public_node_count, -1, dtype=np.int32)
    for parent, node in enumerate(layout.nodes):
        for action_index, child in enumerate(node.children):
            if child <= parent or parents[child] >= 0:
                raise ValueError("leaf-adjoint layout is not a forward tree")
            parents[child] = parent
            actions[child] = action_index
    if layout.public_node_count > 1 and np.any(parents[1:] < 0):
        raise ValueError("leaf-adjoint public tree contains an unreachable node")
    return parents, actions


def _target_omitted_path_factors(
    layout: PublicTreeTensorEvaluator,
    probabilities: PolicyProbabilityTape,
    parents: np.ndarray,
    parent_actions: np.ndarray,
    *,
    terminal_node: int,
    traverser: int,
    shape: tuple[int, ...],
) -> tuple[np.ndarray, ...]:
    factors = [np.ones(size, dtype=np.float64) for size in shape]
    child = terminal_node
    while int(parents[child]) >= 0:
        parent = int(parents[child])
        node = layout.nodes[parent]
        if node.player == TERMINAL_PLAYER:
            raise AssertionError("terminal public node cannot own a child")
        action_index = int(parent_actions[child])
        values = probabilities[parent]
        if values is None:
            raise ValueError("leaf-adjoint strategic node has no probabilities")
        if node.player != traverser:
            factors[node.player] *= values[:, action_index]
        child = parent
    return tuple(np.ascontiguousarray(values) for values in factors)


def _required(values: np.ndarray | None) -> np.ndarray:
    if values is None:
        raise AssertionError("leaf-adjoint child was not evaluated")
    return values


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def _readonly_bool(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.bool_, order="C", copy=True)
    result.flags.writeable = False
    return result
