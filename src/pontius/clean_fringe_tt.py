"""No-rounding scalar policy deltas over a cached clean TT frontier.

A candidate changes policy unaries on a set of public nodes.  Its dirty
ancestor closure is evaluated only through public reach.  Whenever that closure
exits into an unchanged child, the baseline child value TT is reused.  The
resulting identity is

``Delta U = sum_f E[(q_candidate(f) - q_baseline(f)) * V_baseline(f)]``.

Candidate reach above every changed node is load-bearing when one seat acts
multiple times on a line.  No TT rounding or SVD occurs on this read path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .batched_factor_tt_contraction import WeightedTensorTrainTerm
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyDeltaTTCache, PolicyDeltaTTPlan
from .tensor_train import TensorTrain
from .tensor_train_algebra import sum_tensor_trains

FloatArray: TypeAlias = NDArray[np.float64]
ReachFactors: TypeAlias = tuple[FloatArray, ...]


@dataclass(frozen=True, slots=True)
class CleanFringePlan:
    """A shared public cutset and both policies' factorized frontier reaches."""

    dirty_nodes: tuple[int, ...]
    frontier_nodes: tuple[int, ...]
    delta_support_frontier_nodes: tuple[int, ...]
    baseline_reaches: tuple[ReachFactors, ...]
    candidate_reaches: tuple[ReachFactors, ...]


@dataclass(frozen=True, slots=True)
class CleanFringeDeltaTrain:
    """One exact unrounded batched delta operator for a player-value cache."""

    train: TensorTrain | None
    frontier_nodes: tuple[int, ...]
    delta_support_frontier_nodes: tuple[int, ...]
    frontier_middle_ranks: tuple[int, ...]
    total_component_rank_width: int
    raw_middle_rank: int
    storage_bytes: int
    shared_fringe_error_bound: float


@dataclass(frozen=True, slots=True)
class CleanFringeDeltaTerms:
    """Frontier terms ready for bounded-width streamed contraction."""

    terms: tuple[WeightedTensorTrainTerm, ...]
    frontier_nodes: tuple[int, ...]
    delta_support_frontier_nodes: tuple[int, ...]
    frontier_middle_ranks: tuple[int, ...]
    total_component_rank_width: int
    referenced_tt_storage_bytes: int
    reach_factor_numeric_bytes: int
    shared_fringe_error_bound: float


def compile_clean_fringe_plan(
    cache: PolicyDeltaTTCache,
    policy_plan: PolicyDeltaTTPlan,
) -> CleanFringePlan:
    """Compile the common clean frontier and baseline/candidate public reach."""

    if cache.probabilities is not policy_plan.baseline_probabilities:
        raise ValueError("policy-delta plan belongs to a different baseline cache")
    layout = cache.layout
    dirty = policy_plan.dirty_nodes
    dirty_set = set(dirty)
    if not dirty:
        frontier = (0,)
    else:
        if 0 not in dirty_set:
            raise ValueError("nonempty dirty closure must contain the public root")
        frontier = tuple(
            sorted(
                child
                for node_index in dirty
                for child in layout.nodes[node_index].children
                if child not in dirty_set
            )
        )
    if not frontier:
        raise ValueError("dirty closure does not terminate at a clean frontier")
    if len(set(frontier)) != len(frontier):
        raise ValueError("public frontier is not a cutset in a tree")

    baseline = _frontier_reaches(
        cache,
        policy_plan.baseline_probabilities,
        dirty_set,
        frontier,
    )
    candidate = _frontier_reaches(
        cache,
        policy_plan.candidate_probabilities,
        dirty_set,
        frontier,
    )
    support = tuple(
        node
        for node, first, second in zip(frontier, baseline, candidate, strict=True)
        if any(
            not np.array_equal(left, right)
            for left, right in zip(first, second, strict=True)
        )
    )
    return CleanFringePlan(
        dirty_nodes=dirty,
        frontier_nodes=frontier,
        delta_support_frontier_nodes=support,
        baseline_reaches=baseline,
        candidate_reaches=candidate,
    )


def compose_clean_fringe_delta_train(
    cache: PolicyDeltaTTCache,
    plan: CleanFringePlan,
    *,
    belief_components: int,
    split_index: int = 3,
) -> CleanFringeDeltaTrain:
    """Direct-sum every nonzero frontier delta without candidate-time SVD."""

    compiled = compile_clean_fringe_delta_terms(
        cache,
        plan,
        belief_components=belief_components,
        split_index=split_index,
    )
    materialized = tuple(
        _multiply_all_modes(
            term.train,
            term.mode_factors,
            scale=term.coefficient,
        )
        for term in compiled.terms
    )
    train = sum_tensor_trains(materialized) if materialized else None
    raw_middle_rank = 0 if train is None else train.ranks[split_index]
    expected_middle_rank = sum(
        term.train.ranks[split_index] for term in compiled.terms
    )
    if raw_middle_rank != expected_middle_rank:
        raise AssertionError("batched clean-fringe direct-sum rank is inconsistent")
    return CleanFringeDeltaTrain(
        train=train,
        frontier_nodes=compiled.frontier_nodes,
        delta_support_frontier_nodes=compiled.delta_support_frontier_nodes,
        frontier_middle_ranks=compiled.frontier_middle_ranks,
        total_component_rank_width=compiled.total_component_rank_width,
        raw_middle_rank=raw_middle_rank,
        storage_bytes=0 if train is None else train.storage_bytes,
        shared_fringe_error_bound=compiled.shared_fringe_error_bound,
    )


def compile_clean_fringe_delta_terms(
    cache: PolicyDeltaTTCache,
    plan: CleanFringePlan,
    *,
    belief_components: int,
    split_index: int = 3,
) -> CleanFringeDeltaTerms:
    """Compile factorized delta terms without materializing a direct-sum TT."""

    if belief_components <= 0:
        raise ValueError("belief component count must be positive")
    if split_index <= 0 or split_index >= len(cache.hands_by_player):
        raise ValueError("split index must leave two nonempty seat halves")
    reach_by_node = {
        node: (baseline, candidate)
        for node, baseline, candidate in zip(
            plan.frontier_nodes,
            plan.baseline_reaches,
            plan.candidate_reaches,
            strict=True,
        )
    }
    terms: list[WeightedTensorTrainTerm] = []
    ranks = []
    for node in plan.delta_support_frontier_nodes:
        baseline, candidate = reach_by_node[node]
        value = cache.node_trains[node]
        ranks.append(value.ranks[split_index])
        terms.append(
            WeightedTensorTrainTerm(
                train=value,
                mode_factors=candidate,
                coefficient=1.0,
            )
        )
        terms.append(
            WeightedTensorTrainTerm(
                train=value,
                mode_factors=baseline,
                coefficient=-1.0,
            )
        )
    maximum_bound = max(
        (float(cache.node_bounds[node]) for node in plan.delta_support_frontier_nodes),
        default=0.0,
    )
    expected_middle_rank = 2 * sum(ranks)
    unique_trains = {id(term.train): term.train for term in terms}
    unique_factors = {
        id(factor): factor
        for term in terms
        for factor in term.mode_factors
    }
    return CleanFringeDeltaTerms(
        terms=tuple(terms),
        frontier_nodes=plan.frontier_nodes,
        delta_support_frontier_nodes=plan.delta_support_frontier_nodes,
        frontier_middle_ranks=tuple(ranks),
        total_component_rank_width=(belief_components * expected_middle_rank),
        referenced_tt_storage_bytes=sum(
            train.storage_bytes for train in unique_trains.values()
        ),
        reach_factor_numeric_bytes=sum(
            factor.nbytes for factor in unique_factors.values()
        ),
        shared_fringe_error_bound=2.0 * maximum_bound,
    )


def _frontier_reaches(
    cache: PolicyDeltaTTCache,
    probabilities: tuple[FloatArray | None, ...],
    dirty: set[int],
    frontier: tuple[int, ...],
) -> tuple[ReachFactors, ...]:
    layout = cache.layout
    needed = dirty | set(frontier)
    unit = tuple(
        np.ones(len(hands), dtype=np.float64)
        for hands in cache.hands_by_player
    )
    reaches: dict[int, ReachFactors] = {0: unit}
    for node_index, node in enumerate(layout.nodes):
        if node_index not in dirty:
            continue
        if node.player == TERMINAL_PLAYER:
            raise AssertionError("dirty policy closure unexpectedly contains a terminal")
        parent_reach = reaches[node_index]
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise AssertionError("strategic reach has no policy probabilities")
        for action_index, child in enumerate(node.children):
            if child not in needed:
                continue
            child_reach = list(parent_reach)
            child_reach[node.player] = np.ascontiguousarray(
                parent_reach[node.player] * node_probabilities[:, action_index],
                dtype=np.float64,
            )
            reaches[child] = tuple(child_reach)
    missing = set(frontier) - set(reaches)
    if missing:
        raise AssertionError(f"frontier reach was not propagated: {sorted(missing)!r}")
    return tuple(reaches[node] for node in frontier)


def _multiply_all_modes(
    train: TensorTrain,
    factors: ReachFactors,
    *,
    scale: float,
) -> TensorTrain:
    if len(factors) != len(train.shape):
        raise ValueError("frontier reach requires one factor per TT mode")
    cores = []
    for mode, (core, factor, size) in enumerate(
        zip(train.cores, factors, train.shape, strict=True)
    ):
        values = np.ascontiguousarray(factor, dtype=np.float64)
        if values.shape != (size,) or not np.all(np.isfinite(values)):
            raise ValueError("frontier reach factor is invalid")
        weighted = core * values[None, :, None]
        if mode == 0:
            weighted = weighted * scale
        cores.append(np.ascontiguousarray(weighted, dtype=np.float64))
    return TensorTrain(
        shape=train.shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(len(train.shape) - 1)
        ),
    )
