"""Signed and rank-optimized clean-fringe policy-delta reads.

The frozen clean-fringe reference represents every frontier contribution as
``q_candidate * V`` and ``-q_baseline * V``.  This additive successor uses the
exact product telescope

``prod(c) - prod(b) = sum_k (c_k - b_k) prod_{i<k} c_i prod_{i>k} b_i``

over the seats whose public reaches can change.  A unilateral candidate
therefore needs one term per supported frontier node instead of two.  Clean
subtrees may also be expanded to a deeper cutset by a dynamic program that
minimizes the measured all-value TT middle-rank bill.  Neither path rounds or
decomposes a tensor at candidate-read time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .batched_factor_tt_contraction import (
    BatchedFactorTTContraction,
    WeightedTensorTrainTerm,
    contract_weighted_sum,
)
from .clean_fringe_tt import CleanFringeDeltaTrain, CleanFringePlan, compile_clean_fringe_plan
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyDeltaTTCache, PolicyDeltaTTPlan
from .tensor_train import TensorTrain
from .tensor_train_algebra import sum_tensor_trains

FloatArray: TypeAlias = NDArray[np.float64]
ReachFactors: TypeAlias = tuple[FloatArray, ...]


@dataclass(frozen=True, slots=True)
class SignedCleanFringeDeltaTerms:
    """One ordered reach telescope over a shared clean public cutset."""

    terms: tuple[WeightedTensorTrainTerm, ...]
    term_nodes: tuple[int, ...]
    term_reach_modes: tuple[int, ...]
    changed_reach_modes: tuple[int, ...]
    frontier_nodes: tuple[int, ...]
    delta_support_frontier_nodes: tuple[int, ...]
    frontier_middle_ranks: tuple[int, ...]
    total_component_rank_width: int
    referenced_tt_storage_bytes: int
    reach_factor_numeric_bytes: int
    legacy_shared_fringe_error_bound: float


@dataclass(frozen=True, slots=True)
class RankOptimizedCleanFringePlan:
    """Immediate and minimum-rank clean cutsets shared by all value seats."""

    immediate_plan: CleanFringePlan
    optimized_plan: CleanFringePlan
    changed_reach_modes: tuple[int, ...]
    expanded_clean_nodes: tuple[int, ...]
    immediate_all_value_component_rank_width: int
    optimized_all_value_component_rank_width: int


@dataclass(frozen=True, slots=True)
class ReachWeightedFringeBound:
    """A factor-belief expectation upper-bounding cached-frontier error."""

    upper_bound: float
    terms: int
    total_feature_width: int
    batches: int
    referenced_tt_storage_bytes: int
    mode_factor_numeric_bytes: int
    estimated_peak_batch_scratch_bytes: int


def changed_reach_modes(
    cache: PolicyDeltaTTCache,
    policy_plan: PolicyDeltaTTPlan,
) -> tuple[int, ...]:
    """Return the declared seats whose policy edits can change public reach."""

    if cache.probabilities is not policy_plan.baseline_probabilities:
        raise ValueError("policy-delta plan belongs to a different baseline cache")
    modes = tuple(
        sorted(
            {
                cache.layout.nodes[node].player
                for node in policy_plan.changed_policy_nodes
            }
        )
    )
    if any(mode == TERMINAL_PLAYER for mode in modes):
        raise AssertionError("a terminal node cannot carry a policy edit")
    return modes


def compile_signed_clean_fringe_delta_terms(
    cache: PolicyDeltaTTCache,
    plan: CleanFringePlan,
    *,
    changed_modes: tuple[int, ...],
    belief_components: int,
    split_index: int = 3,
) -> SignedCleanFringeDeltaTerms:
    """Compile an exact ordered reach telescope without a direct-sum TT."""

    _validate_compile_arguments(
        cache,
        plan,
        changed_modes=changed_modes,
        belief_components=belief_components,
        split_index=split_index,
    )
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
    term_nodes: list[int] = []
    term_modes: list[int] = []
    ranks: list[int] = []
    supported_nodes: list[int] = []
    for node in plan.frontier_nodes:
        baseline, candidate = reach_by_node[node]
        node_terms = _telescoping_factors(
            baseline,
            candidate,
            changed_modes=changed_modes,
        )
        if not node_terms:
            continue
        supported_nodes.append(node)
        value = cache.node_trains[node]
        rank = value.ranks[split_index]
        ranks.append(rank)
        for mode, factors in node_terms:
            terms.append(
                WeightedTensorTrainTerm(
                    train=value,
                    mode_factors=factors,
                    coefficient=1.0,
                )
            )
            term_nodes.append(node)
            term_modes.append(mode)

    maximum_bound = max(
        (float(cache.node_bounds[node]) for node in supported_nodes),
        default=0.0,
    )
    unique_trains = {id(term.train): term.train for term in terms}
    unique_factors = {
        id(factor): factor
        for term in terms
        for factor in term.mode_factors
    }
    total_middle_rank = sum(
        term.train.ranks[split_index] for term in terms
    )
    return SignedCleanFringeDeltaTerms(
        terms=tuple(terms),
        term_nodes=tuple(term_nodes),
        term_reach_modes=tuple(term_modes),
        changed_reach_modes=changed_modes,
        frontier_nodes=plan.frontier_nodes,
        delta_support_frontier_nodes=tuple(supported_nodes),
        frontier_middle_ranks=tuple(ranks),
        total_component_rank_width=belief_components * total_middle_rank,
        referenced_tt_storage_bytes=sum(
            train.storage_bytes for train in unique_trains.values()
        ),
        reach_factor_numeric_bytes=sum(
            factor.nbytes for factor in unique_factors.values()
        ),
        legacy_shared_fringe_error_bound=2.0 * maximum_bound,
    )


def compose_signed_clean_fringe_delta_train(
    cache: PolicyDeltaTTCache,
    plan: CleanFringePlan,
    *,
    changed_modes: tuple[int, ...],
    belief_components: int,
    split_index: int = 3,
) -> CleanFringeDeltaTrain:
    """Materialize the signed telescope for small-axis identity controls."""

    compiled = compile_signed_clean_fringe_delta_terms(
        cache,
        plan,
        changed_modes=changed_modes,
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
        raise AssertionError("signed clean-fringe direct-sum rank is inconsistent")
    return CleanFringeDeltaTrain(
        train=train,
        frontier_nodes=compiled.frontier_nodes,
        delta_support_frontier_nodes=compiled.delta_support_frontier_nodes,
        frontier_middle_ranks=compiled.frontier_middle_ranks,
        total_component_rank_width=compiled.total_component_rank_width,
        raw_middle_rank=raw_middle_rank,
        storage_bytes=0 if train is None else train.storage_bytes,
        shared_fringe_error_bound=compiled.legacy_shared_fringe_error_bound,
    )


def compile_rank_optimized_clean_fringe_plan(
    caches: tuple[PolicyDeltaTTCache, ...],
    policy_plan: PolicyDeltaTTPlan,
    *,
    belief_components: int,
    split_index: int = 3,
) -> RankOptimizedCleanFringePlan:
    """Choose the exact clean cut with minimum all-cache feature width.

    The dynamic program compares stopping at a clean node with expanding to
    the independently optimal cuts of all children.  Its cost is the actual
    number of nonzero telescope terms at that node times the sum of cached TT
    middle ranks across the supplied value operators.
    """

    if not caches:
        raise ValueError("rank optimization requires at least one value cache")
    if belief_components <= 0:
        raise ValueError("belief component count must be positive")
    reference = caches[0]
    modes = changed_reach_modes(reference, policy_plan)
    for cache in caches:
        _validate_compatible_cache(reference, cache, policy_plan, split_index)

    immediate = compile_clean_fringe_plan(reference, policy_plan)
    baseline_by_node, candidate_by_node = _all_clean_subtree_reaches(
        reference,
        policy_plan,
        immediate,
    )
    node_term_counts = {
        node: len(
            _telescoping_factors(
                baseline_by_node[node],
                candidate_by_node[node],
                changed_modes=modes,
            )
        )
        for node in baseline_by_node
    }

    layout = reference.layout
    memo: dict[int, tuple[int, tuple[int, ...], tuple[int, ...]]] = {}

    def solve(node: int) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
        cached = memo.get(node)
        if cached is not None:
            return cached
        term_count = node_term_counts[node]
        stop_cost = term_count * sum(
            cache.node_trains[node].ranks[split_index] for cache in caches
        )
        public_node = layout.nodes[node]
        if public_node.player == TERMINAL_PLAYER or term_count == 0:
            answer = (stop_cost, (node,), ())
            memo[node] = answer
            return answer
        child_answers = tuple(solve(child) for child in public_node.children)
        expand_cost = sum(answer[0] for answer in child_answers)
        if stop_cost <= expand_cost:
            answer = (stop_cost, (node,), ())
        else:
            answer = (
                expand_cost,
                tuple(
                    frontier_node
                    for child_answer in child_answers
                    for frontier_node in child_answer[1]
                ),
                (
                    node,
                    *(
                        expanded_node
                        for child_answer in child_answers
                        for expanded_node in child_answer[2]
                    ),
                ),
            )
        memo[node] = answer
        return answer

    selected: list[int] = []
    expanded: list[int] = []
    for root in immediate.frontier_nodes:
        _, nodes, expanded_nodes = solve(root)
        selected.extend(nodes)
        expanded.extend(expanded_nodes)
    selected_frontier = tuple(sorted(selected))
    optimized = _plan_from_reach_maps(
        policy_plan,
        selected_frontier,
        baseline_by_node,
        candidate_by_node,
        changed_modes=modes,
    )
    immediate_width = _all_value_width(
        caches,
        immediate,
        changed_modes=modes,
        belief_components=belief_components,
        split_index=split_index,
    )
    optimized_width = _all_value_width(
        caches,
        optimized,
        changed_modes=modes,
        belief_components=belief_components,
        split_index=split_index,
    )
    if optimized_width > immediate_width:
        raise AssertionError("rank-optimized cut is wider than the immediate cut")
    return RankOptimizedCleanFringePlan(
        immediate_plan=immediate,
        optimized_plan=optimized,
        changed_reach_modes=modes,
        expanded_clean_nodes=tuple(sorted(expanded)),
        immediate_all_value_component_rank_width=immediate_width,
        optimized_all_value_component_rank_width=optimized_width,
    )


def evaluate_reach_weighted_fringe_bound(
    workspace: FactorTTBeliefWorkspace,
    cache: PolicyDeltaTTCache,
    signed: SignedCleanFringeDeltaTerms,
    *,
    maximum_feature_width_per_batch: int,
) -> ReachWeightedFringeBound:
    """Evaluate ``sum_f b_f E[abs(telescoped Delta q_f)]`` exactly.

    For a unilateral edit the telescope has one term and this is exactly the
    requested reach-mass-weighted frontier bound.  For multi-seat edits the
    absolute ordered telescope is a conservative triangle bound.
    Float64 arithmetic noise is intentionally separate from this truncation
    bound and must be added by the caller's certificate.
    """

    if len(signed.terms) != len(signed.term_nodes):
        raise ValueError("signed term provenance is inconsistent")
    shape = tuple(len(hands) for hands in cache.hands_by_player)
    if shape != workspace.topology.hand_counts:
        raise ValueError("bound workspace and value cache have different axes")
    unit = _constant_train(shape, 1.0)
    bound_terms: list[WeightedTensorTrainTerm] = []
    for term, node in zip(signed.terms, signed.term_nodes, strict=True):
        bound = float(cache.node_bounds[node])
        if bound < 0.0 or not np.isfinite(bound):
            raise ValueError("cached frontier bound must be finite and nonnegative")
        if bound == 0.0:
            continue
        bound_terms.append(
            WeightedTensorTrainTerm(
                train=unit,
                mode_factors=tuple(
                    np.ascontiguousarray(np.abs(factor), dtype=np.float64)
                    for factor in term.mode_factors
                ),
                coefficient=bound * abs(term.coefficient),
            )
        )
    if not bound_terms:
        return ReachWeightedFringeBound(
            upper_bound=0.0,
            terms=0,
            total_feature_width=0,
            batches=0,
            referenced_tt_storage_bytes=0,
            mode_factor_numeric_bytes=0,
            estimated_peak_batch_scratch_bytes=0,
        )
    contraction = contract_weighted_sum(
        workspace,
        tuple(bound_terms),
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    value = float(contraction.expectation)
    if value < -64.0 * np.finfo(np.float64).eps:
        raise AssertionError("nonnegative reach-bound contraction became negative")
    return _bound_result(max(0.0, value), contraction)


def _validate_compile_arguments(
    cache: PolicyDeltaTTCache,
    plan: CleanFringePlan,
    *,
    changed_modes: tuple[int, ...],
    belief_components: int,
    split_index: int,
) -> None:
    if belief_components <= 0:
        raise ValueError("belief component count must be positive")
    if split_index <= 0 or split_index >= len(cache.hands_by_player):
        raise ValueError("split index must leave two nonempty seat halves")
    if tuple(sorted(set(changed_modes))) != changed_modes:
        raise ValueError("changed reach modes must be unique and sorted")
    if any(mode not in range(len(cache.hands_by_player)) for mode in changed_modes):
        raise ValueError("changed reach mode is outside the hand axes")
    if len(plan.frontier_nodes) != len(plan.baseline_reaches) or len(
        plan.frontier_nodes
    ) != len(plan.candidate_reaches):
        raise ValueError("frontier reach table is inconsistent")


def _validate_compatible_cache(
    reference: PolicyDeltaTTCache,
    cache: PolicyDeltaTTCache,
    policy_plan: PolicyDeltaTTPlan,
    split_index: int,
) -> None:
    if cache.layout is not reference.layout:
        raise ValueError("all value caches must share one public layout")
    if cache.hands_by_player != reference.hands_by_player:
        raise ValueError("all value caches must share hand axes")
    if cache.probabilities is not policy_plan.baseline_probabilities:
        raise ValueError("all value caches must share the policy-plan baseline tape")
    if split_index <= 0 or split_index >= len(cache.hands_by_player):
        raise ValueError("split index must leave two nonempty seat halves")


def _telescoping_factors(
    baseline: ReachFactors,
    candidate: ReachFactors,
    *,
    changed_modes: tuple[int, ...],
) -> tuple[tuple[int, ReachFactors], ...]:
    if len(baseline) != len(candidate):
        raise ValueError("baseline and candidate reach orders differ")
    changed_set = set(changed_modes)
    for mode, (first, second) in enumerate(zip(baseline, candidate, strict=True)):
        if mode not in changed_set and not np.array_equal(first, second):
            raise ValueError("an undeclared reach mode changed")

    terms: list[tuple[int, ReachFactors]] = []
    for offset, changed_mode in enumerate(changed_modes):
        delta = np.ascontiguousarray(
            candidate[changed_mode] - baseline[changed_mode],
            dtype=np.float64,
        )
        if not np.any(delta):
            continue
        factors: list[FloatArray] = []
        earlier = set(changed_modes[:offset])
        for mode in range(len(baseline)):
            if mode == changed_mode:
                factors.append(delta)
            elif mode in earlier:
                factors.append(candidate[mode])
            else:
                factors.append(baseline[mode])
        if any(not np.any(factor) for factor in factors):
            continue
        terms.append((changed_mode, tuple(factors)))
    return tuple(terms)


def _all_clean_subtree_reaches(
    cache: PolicyDeltaTTCache,
    policy_plan: PolicyDeltaTTPlan,
    immediate: CleanFringePlan,
) -> tuple[dict[int, ReachFactors], dict[int, ReachFactors]]:
    baseline = dict(zip(immediate.frontier_nodes, immediate.baseline_reaches, strict=True))
    candidate = dict(
        zip(immediate.frontier_nodes, immediate.candidate_reaches, strict=True)
    )
    dirty = set(policy_plan.dirty_nodes)
    for node_index, node in enumerate(cache.layout.nodes):
        if node_index not in baseline:
            continue
        if node.player == TERMINAL_PLAYER:
            continue
        if node_index in dirty:
            raise AssertionError("clean-subtree expansion re-entered the dirty closure")
        baseline_probabilities = policy_plan.baseline_probabilities[node_index]
        candidate_probabilities = policy_plan.candidate_probabilities[node_index]
        if baseline_probabilities is None or candidate_probabilities is None:
            raise AssertionError("a strategic clean node has no policy probabilities")
        for action_index, child in enumerate(node.children):
            if child in dirty:
                raise AssertionError("a clean subtree cannot contain a dirty child")
            baseline[child] = _extend_reach(
                baseline[node_index],
                node.player,
                baseline_probabilities[:, action_index],
            )
            candidate[child] = _extend_reach(
                candidate[node_index],
                node.player,
                candidate_probabilities[:, action_index],
            )
    if set(baseline) != set(candidate):
        raise AssertionError("baseline and candidate clean reach domains differ")
    return baseline, candidate


def _extend_reach(
    parent: ReachFactors,
    player: int,
    action_probabilities: FloatArray,
) -> ReachFactors:
    child = list(parent)
    child[player] = np.ascontiguousarray(
        parent[player] * action_probabilities,
        dtype=np.float64,
    )
    return tuple(child)


def _plan_from_reach_maps(
    policy_plan: PolicyDeltaTTPlan,
    frontier: tuple[int, ...],
    baseline_by_node: dict[int, ReachFactors],
    candidate_by_node: dict[int, ReachFactors],
    *,
    changed_modes: tuple[int, ...],
) -> CleanFringePlan:
    baseline = tuple(baseline_by_node[node] for node in frontier)
    candidate = tuple(candidate_by_node[node] for node in frontier)
    support = tuple(
        node
        for node, first, second in zip(frontier, baseline, candidate, strict=True)
        if _telescoping_factors(first, second, changed_modes=changed_modes)
    )
    return CleanFringePlan(
        dirty_nodes=policy_plan.dirty_nodes,
        frontier_nodes=frontier,
        delta_support_frontier_nodes=support,
        baseline_reaches=baseline,
        candidate_reaches=candidate,
    )


def _all_value_width(
    caches: tuple[PolicyDeltaTTCache, ...],
    plan: CleanFringePlan,
    *,
    changed_modes: tuple[int, ...],
    belief_components: int,
    split_index: int,
) -> int:
    width = 0
    for baseline, candidate, node in zip(
        plan.baseline_reaches,
        plan.candidate_reaches,
        plan.frontier_nodes,
        strict=True,
    ):
        term_count = len(
            _telescoping_factors(
                baseline,
                candidate,
                changed_modes=changed_modes,
            )
        )
        width += term_count * sum(
            cache.node_trains[node].ranks[split_index] for cache in caches
        )
    return belief_components * width


def _constant_train(shape: tuple[int, ...], value: float) -> TensorTrain:
    cores = []
    for mode, size in enumerate(shape):
        core = np.ones((1, size, 1), dtype=np.float64)
        if mode == 0:
            core *= value
        cores.append(core)
    return TensorTrain(
        shape=shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(len(shape) - 1)
        ),
    )


def _bound_result(
    upper_bound: float,
    contraction: BatchedFactorTTContraction,
) -> ReachWeightedFringeBound:
    return ReachWeightedFringeBound(
        upper_bound=upper_bound,
        terms=contraction.terms,
        total_feature_width=contraction.total_feature_width,
        batches=contraction.batches,
        referenced_tt_storage_bytes=contraction.referenced_tt_storage_bytes,
        mode_factor_numeric_bytes=contraction.mode_factor_numeric_bytes,
        estimated_peak_batch_scratch_bytes=(
            contraction.estimated_peak_batch_scratch_bytes
        ),
    )


def _multiply_all_modes(
    train: TensorTrain,
    factors: ReachFactors,
    *,
    scale: float,
) -> TensorTrain:
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
