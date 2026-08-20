"""One exact quotient-CFR step without a dense joint-deal traversal axis.

This module is an additive successor to the frozen ADR-0081 bridge.  It reads
policy-conditioned child tensor trains through the optional CSR incidence
backend and applies the resulting regret deltas.  It deliberately exposes no
best-action field: ADR-0084 rejected unguarded floating-point ``argmax`` at
exact ties, while CFR itself needs action numerators rather than a best action.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Literal, Mapping, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .game import Action, TERMINAL_PLAYER
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    PolicyProbabilityTape,
    compile_policy_delta_tt_cache_from_probabilities,
)
from .open_mode_cfr_bridge import counterfactual_mode_factors
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_tree_tensor import PublicTreeTensorEvaluator
from .public_tree_tensor_cfr import PublicTreeTensorCFR
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .sparse_open_mode_factor_tt import (
    SparseOpenModeFactorTTBatchContraction,
    contract_sparse_open_mode_batch,
)
from .tensor_train import TensorTrain
from .unrounded_policy_tt import compile_unrounded_policy_tt_cache_from_probabilities
from .updates import SolverVariant

FloatArray: TypeAlias = NDArray[np.float64]
TerminalLibrary: TypeAlias = tuple[
    Mapping[str, TensorTrain],
    Mapping[str, float],
]


@dataclass(frozen=True, slots=True)
class SparseCFRRegretRead:
    """Per-hand action numerators and regret deltas for one public node."""

    node_index: int
    target_seat: int
    actions: tuple[Action, ...]
    counterfactual_reaches: FloatArray
    action_numerators: FloatArray
    conditional_action_values: FloatArray
    positive_reach: NDArray[np.bool_]
    policy_values: FloatArray
    regret_deltas: FloatArray
    zero_reach_hands: int


@dataclass(frozen=True, slots=True)
class SparseOpenModeCFRRead:
    """One regret read and its attributable generic-TT CSR contraction."""

    values: SparseCFRRegretRead
    mode_factors: tuple[FloatArray, ...]
    contraction: SparseOpenModeFactorTTBatchContraction


@dataclass(frozen=True, slots=True)
class SparseCFRTraverserWork:
    traverser: int
    probability_compile_ms: float
    own_reach_and_average_ms: float
    cache_compile_ms: float
    action_read_ms: float
    regret_apply_ms: float
    strategic_reads: int
    hand_action_entries: int
    maximum_middle_rank: int
    maximum_total_feature_width: int
    maximum_read_peak_numeric_bytes: int
    cache_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class SparseCFRStepWork:
    iteration: int
    wall_ms: float
    discount_ms: float
    traversers: tuple[SparseCFRTraverserWork, ...]

    @property
    def cache_compile_ms(self) -> float:
        return sum(row.cache_compile_ms for row in self.traversers)

    @property
    def action_read_ms(self) -> float:
        return sum(row.action_read_ms for row in self.traversers)


def sparse_open_mode_cfr_regret_read(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    cache: PolicyDeltaTTCache,
    *,
    node_index: int,
    maximum_feature_width_per_batch: int,
    zero_reach_value: float = 0.0,
) -> SparseOpenModeCFRRead:
    """Return the CFR action table without performing an unguarded argmax."""

    layout = cache.layout
    if isinstance(node_index, bool) or node_index not in range(layout.public_node_count):
        raise ValueError("CFR regret node is outside the public tree")
    node = layout.nodes[node_index]
    if node.player == TERMINAL_PLAYER:
        raise ValueError("CFR regret read requires a strategic node")
    if sparse.topology is not workspace.topology:
        raise ValueError("sparse incidence operators belong to another topology")
    if tuple(len(hands) for hands in cache.hands_by_player) != (
        workspace.topology.base.hand_counts
    ):
        raise ValueError("CFR cache hand axes differ from open-mode topology")
    for hands, masks in zip(
        cache.hands_by_player,
        workspace.topology.base.axis_masks,
        strict=True,
    ):
        supplied = np.ascontiguousarray(
            [(1 << hand[0]) | (1 << hand[1]) for hand in hands],
            dtype=np.uint64,
        )
        if not np.array_equal(supplied, masks):
            raise ValueError("CFR cache hand axes differ from open-mode topology")

    target = node.player
    factors = counterfactual_mode_factors(
        cache,
        node_index=node_index,
        traverser=target,
    )
    contraction = contract_sparse_open_mode_batch(
        workspace,
        sparse,
        tuple(cache.node_trains[child] for child in node.children),
        target_seats=(target,),
        mode_factors=factors,
        zero_reach_value=zero_reach_value,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    children = tuple(
        result.for_seat(target) for result in contraction.trains
    )
    reaches = children[0].root_normalized_reaches
    if any(
        not np.array_equal(values.root_normalized_reaches, reaches)
        for values in children[1:]
    ):
        raise AssertionError("batched sparse CFR children produced different reaches")
    numerators = np.ascontiguousarray(
        np.column_stack(
            tuple(values.root_normalized_numerators for values in children)
        ),
        dtype=np.float64,
    )
    conditional = np.ascontiguousarray(
        np.column_stack(tuple(values.conditional_values for values in children)),
        dtype=np.float64,
    )
    positive = np.ascontiguousarray(reaches > 0.0, dtype=np.bool_)
    probabilities = cache.probabilities[node_index]
    if probabilities is None:
        raise AssertionError("strategic CFR node has no policy probabilities")
    policy_values = np.einsum(
        "ha,ha->h",
        probabilities,
        numerators,
        optimize=True,
    )
    regret_deltas = numerators - policy_values[:, None]
    regret_deltas[~positive] = 0.0
    values = SparseCFRRegretRead(
        node_index=node_index,
        target_seat=target,
        actions=node.actions,
        counterfactual_reaches=_readonly(reaches, np.float64),
        action_numerators=_readonly(numerators, np.float64),
        conditional_action_values=_readonly(conditional, np.float64),
        positive_reach=_readonly(positive, np.bool_),
        policy_values=_readonly(policy_values, np.float64),
        regret_deltas=_readonly(regret_deltas, np.float64),
        zero_reach_hands=int(np.count_nonzero(~positive)),
    )
    return SparseOpenModeCFRRead(
        values=values,
        mode_factors=factors,
        contraction=contraction,
    )


class SparseOpenModePublicTreeCFR(PublicTreeTensorCFR):
    """Alternating CFR using cached TT continuations and sparse open reads."""

    def __init__(
        self,
        layout: PublicTreeTensorEvaluator,
        workspace: OpenModeFactorTTWorkspace,
        sparse: SparseBidirectionalIncidence,
        terminal_libraries: tuple[TerminalLibrary, ...],
        variant: SolverVariant = "cfr",
        *,
        node_relative_tolerance: float = 0.0,
        node_maximum_rank: int | None = None,
        maximum_feature_width_per_batch: int = 96,
        policy_cache_mode: Literal["rounded", "unrounded"] = "rounded",
    ) -> None:
        super().__init__(layout, variant)
        if sparse.topology is not workspace.topology:
            raise ValueError("sparse CFR topology and workspace differ")
        if tuple(len(hands) for hands in layout.hands_by_player) != (
            workspace.topology.base.hand_counts
        ):
            raise ValueError("sparse CFR layout and workspace hand axes differ")
        if len(terminal_libraries) != layout.num_players:
            raise ValueError("sparse CFR requires one terminal library per player")
        if not np.isfinite(node_relative_tolerance) or node_relative_tolerance < 0.0:
            raise ValueError("sparse CFR node tolerance must be finite and nonnegative")
        if node_maximum_rank is not None and (
            isinstance(node_maximum_rank, bool) or node_maximum_rank <= 0
        ):
            raise ValueError("sparse CFR maximum rank must be positive or absent")
        if (
            isinstance(maximum_feature_width_per_batch, bool)
            or maximum_feature_width_per_batch < workspace.component_count
        ):
            raise ValueError("sparse CFR feature width is too small")
        if policy_cache_mode not in ("rounded", "unrounded"):
            raise ValueError("sparse CFR policy cache mode is unknown")

        self.workspace = workspace
        self.sparse = sparse
        self.terminal_libraries = tuple(
            (dict(trains), dict(bounds)) for trains, bounds in terminal_libraries
        )
        self.node_relative_tolerance = float(node_relative_tolerance)
        self.node_maximum_rank = node_maximum_rank
        self.maximum_feature_width_per_batch = maximum_feature_width_per_batch
        self.policy_cache_mode = policy_cache_mode
        self.last_step_work: SparseCFRStepWork | None = None

    def step(self) -> None:
        """Run one alternating update with no dense joint-deal scratch."""

        step_started = time.perf_counter()
        self.iteration += 1
        node_count = self.layout.public_node_count
        traverser_work = []

        for traverser in range(self.num_players):
            started = time.perf_counter()
            probabilities = self._immutable_strategies()
            probability_ms = (time.perf_counter() - started) * 1000.0

            started = time.perf_counter()
            own_hand_count = len(self.layout.hands_by_player[traverser])
            own_reach = np.empty(
                (node_count, own_hand_count),
                dtype=np.float64,
                order="C",
            )
            own_reach[0].fill(1.0)
            for node_index, node in enumerate(self.layout.nodes):
                if node.player == TERMINAL_PLAYER:
                    continue
                strategy = probabilities[node_index]
                if strategy is None:
                    raise AssertionError("strategic CFR node has no probabilities")
                if node.player == traverser:
                    strategy_sum = self._strategy_sums[node_index]
                    if strategy_sum is None:
                        raise AssertionError("traverser node has no strategy sum")
                    strategy_sum += own_reach[node_index, :, None] * strategy
                    for action_index, child in enumerate(node.children):
                        own_reach[child] = (
                            own_reach[node_index] * strategy[:, action_index]
                        )
                else:
                    for child in node.children:
                        own_reach[child] = own_reach[node_index]
            own_reach_ms = (time.perf_counter() - started) * 1000.0

            trains, bounds = self.terminal_libraries[traverser]
            started = time.perf_counter()
            if self.policy_cache_mode == "rounded":
                cache = compile_policy_delta_tt_cache_from_probabilities(
                    self.layout,
                    self.layout.hands_by_player,
                    probabilities,
                    trains,
                    bounds,
                    relative_tolerance=self.node_relative_tolerance,
                    maximum_rank=self.node_maximum_rank,
                )
            else:
                cache = compile_unrounded_policy_tt_cache_from_probabilities(
                    self.layout,
                    self.layout.hands_by_player,
                    probabilities,
                    trains,
                    bounds,
                ).cache
            cache_ms = (time.perf_counter() - started) * 1000.0

            reads = []
            read_ms = 0.0
            entries = 0
            maximum_rank = 0
            maximum_width = 0
            maximum_peak = 0
            for node_index in self._nodes_by_player[traverser]:
                started = time.perf_counter()
                read = sparse_open_mode_cfr_regret_read(
                    self.workspace,
                    self.sparse,
                    cache,
                    node_index=node_index,
                    maximum_feature_width_per_batch=(
                        self.maximum_feature_width_per_batch
                    ),
                )
                read_ms += (time.perf_counter() - started) * 1000.0
                reads.append((node_index, read.values.regret_deltas))
                entries += read.values.regret_deltas.size
                maximum_rank = max(
                    maximum_rank,
                    *read.contraction.middle_ranks,
                )
                maximum_width = max(
                    maximum_width,
                    *(work.total_feature_width for work in read.contraction.directions),
                )
                maximum_peak = max(
                    maximum_peak,
                    read.contraction.estimated_peak_total_numeric_bytes,
                )

            started = time.perf_counter()
            for node_index, delta in reads:
                regrets = self._regrets[node_index]
                if regrets is None:
                    raise AssertionError("traverser node has no regrets")
                regrets += delta
                if self.update_rule.clip_regrets:
                    np.maximum(regrets, 0.0, out=regrets)
            regret_ms = (time.perf_counter() - started) * 1000.0
            traverser_work.append(
                SparseCFRTraverserWork(
                    traverser=traverser,
                    probability_compile_ms=probability_ms,
                    own_reach_and_average_ms=own_reach_ms,
                    cache_compile_ms=cache_ms,
                    action_read_ms=read_ms,
                    regret_apply_ms=regret_ms,
                    strategic_reads=len(reads),
                    hand_action_entries=entries,
                    maximum_middle_rank=maximum_rank,
                    maximum_total_feature_width=maximum_width,
                    maximum_read_peak_numeric_bytes=maximum_peak,
                    cache_numeric_bytes=cache.numeric_bytes,
                )
            )

        started = time.perf_counter()
        self._discount_accumulators()
        discount_ms = (time.perf_counter() - started) * 1000.0
        self.last_step_work = SparseCFRStepWork(
            iteration=self.iteration,
            wall_ms=(time.perf_counter() - step_started) * 1000.0,
            discount_ms=discount_ms,
            traversers=tuple(traverser_work),
        )

    def _immutable_strategies(self) -> PolicyProbabilityTape:
        probabilities = []
        for values in self._strategies():
            if values is None:
                probabilities.append(None)
                continue
            retained = np.ascontiguousarray(values, dtype=np.float64)
            retained.flags.writeable = False
            probabilities.append(retained)
        return tuple(probabilities)

    def memory_summary(self) -> dict[str, int]:
        """Report persistent state and the last measured dense-free peak."""

        accumulator_bytes = sum(
            values.nbytes
            for arrays in (self._regrets, self._strategy_sums)
            for values in arrays
            if values is not None
        )
        unique_trains = {
            id(train): train
            for trains, _ in self.terminal_libraries
            for train in trains.values()
        }
        terminal_bytes = sum(train.storage_bytes for train in unique_trains.values())
        last_peak = (
            0
            if self.last_step_work is None
            else max(
                row.maximum_read_peak_numeric_bytes
                for row in self.last_step_work.traversers
            )
        )
        return {
            "persistent_accumulator_bytes": accumulator_bytes,
            "workspace_numeric_bytes": self.workspace.numeric_bytes,
            "topology_numeric_bytes": self.workspace.topology.numeric_bytes,
            "sparse_operator_numeric_bytes": self.sparse.numeric_bytes,
            "terminal_train_numeric_bytes": terminal_bytes,
            "last_step_maximum_read_peak_numeric_bytes": last_peak,
        }


def _readonly(values: object, dtype: object) -> NDArray[np.generic]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result
