"""Guarded per-node tensor-train caches for fixed-belief policy edits.

The frozen public-policy composer deliberately returns only its root.  This
module preserves that implementation and adds the opposite reuse axis: every
public-node value is retained so a policy edit recomputes only the edited
nodes and their ancestor closure.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .evaluation import Policy
from .game import TERMINAL_PLAYER
from .public_policy_tt import (
    _hand_policy_probabilities,
    _terminal_keys_by_slot,
)
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards
from .tensor_train import TensorTrain
from .tensor_train_algebra import (
    multiply_mode_vector,
    round_tensor_train,
    sum_tensor_trains,
)

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]
PolicyProbabilityTape: TypeAlias = tuple[FloatArray | None, ...]


@dataclass(frozen=True, slots=True)
class PolicyDeltaTTCache:
    """Every public-node TT and conservative truncation-error propagation."""

    layout: PublicTreeTensorEvaluator
    hands_by_player: tuple[tuple[HoleCards, ...], ...]
    terminal_trains: Mapping[str, TensorTrain]
    terminal_bounds: Mapping[str, float]
    relative_tolerance: float
    maximum_rank: int | None
    probabilities: tuple[FloatArray | None, ...]
    node_trains: tuple[TensorTrain, ...]
    node_bounds: FloatArray
    local_discarded_bounds: FloatArray
    parents: IntArray
    depths: IntArray

    @property
    def root(self) -> TensorTrain:
        return self.node_trains[0]

    @property
    def root_bound(self) -> float:
        return float(self.node_bounds[0])

    @property
    def public_depth(self) -> int:
        return int(np.max(self.depths))

    @property
    def numeric_bytes(self) -> int:
        """Count unique TT cores plus cached numeric metadata and policies."""

        unique_trains: dict[int, TensorTrain] = {}
        for train in self.node_trains:
            unique_trains.setdefault(id(train), train)
        probability_bytes = sum(
            values.nbytes for values in self.probabilities if values is not None
        )
        return (
            sum(train.storage_bytes for train in unique_trains.values())
            + probability_bytes
            + self.node_bounds.nbytes
            + self.local_discarded_bounds.nbytes
            + self.parents.nbytes
            + self.depths.nbytes
        )


@dataclass(frozen=True, slots=True)
class PolicyDeltaTTRecomposition:
    """A new persistent cache and exact dirty-set diagnostics."""

    cache: PolicyDeltaTTCache
    changed_policy_nodes: tuple[int, ...]
    dirty_nodes: tuple[int, ...]
    recomputed_strategic_nodes: int
    reused_node_train_objects: int


@dataclass(frozen=True, slots=True)
class PolicyDeltaTTPlan:
    """One candidate probability tape and dirty closure shared by all seats."""

    baseline_probabilities: PolicyProbabilityTape
    candidate_probabilities: PolicyProbabilityTape
    changed_policy_nodes: tuple[int, ...]
    dirty_nodes: tuple[int, ...]


def compile_policy_delta_tt_cache(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
    terminal_trains: Mapping[str, TensorTrain],
    terminal_bounds: Mapping[str, float],
    *,
    relative_tolerance: float,
    maximum_rank: int | None,
) -> PolicyDeltaTTCache:
    """Cold-compose all nodes and retain the full persistent cache."""

    probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        policy,
    )
    return compile_policy_delta_tt_cache_from_probabilities(
        layout,
        hands_by_player,
        probabilities,
        terminal_trains,
        terminal_bounds,
        relative_tolerance=relative_tolerance,
        maximum_rank=maximum_rank,
    )


def compile_policy_probability_tape(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
) -> PolicyProbabilityTape:
    """Materialize one immutable public-node policy tape for all value seats."""

    return _readonly_probabilities(
        _hand_policy_probabilities(layout, hands_by_player, policy)
    )


def compile_policy_delta_tt_cache_from_probabilities(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    probabilities: PolicyProbabilityTape,
    terminal_trains: Mapping[str, TensorTrain],
    terminal_bounds: Mapping[str, float],
    *,
    relative_tolerance: float,
    maximum_rank: int | None,
) -> PolicyDeltaTTCache:
    """Cold-compose using a probability tape shared across player values."""

    _validate_rounding(relative_tolerance, maximum_rank)
    terminal_keys = _validate_terminals(
        layout,
        hands_by_player,
        terminal_trains,
        terminal_bounds,
    )
    parents, depths = _tree_metadata(layout)
    _validate_probability_tape(layout, hands_by_player, probabilities)
    node_trains: list[TensorTrain | None] = [None] * layout.public_node_count
    node_bounds = np.zeros(layout.public_node_count, dtype=np.float64)
    local_bounds = np.zeros(layout.public_node_count, dtype=np.float64)

    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            key = terminal_keys[node.terminal_slot]
            node_trains[node_index] = terminal_trains[key]
            node_bounds[node_index] = float(terminal_bounds[key])
            continue
        train, propagated, local = _compose_strategic_node(
            layout=layout,
            node_index=node_index,
            probabilities=probabilities,
            node_trains=node_trains,
            node_bounds=node_bounds,
            relative_tolerance=relative_tolerance,
            maximum_rank=maximum_rank,
        )
        node_trains[node_index] = train
        node_bounds[node_index] = propagated
        local_bounds[node_index] = local

    if any(train is None for train in node_trains):
        raise AssertionError("cold policy composition left an uncomputed node")
    return PolicyDeltaTTCache(
        layout=layout,
        hands_by_player=hands_by_player,
        terminal_trains=dict(terminal_trains),
        terminal_bounds=dict(terminal_bounds),
        relative_tolerance=relative_tolerance,
        maximum_rank=maximum_rank,
        probabilities=probabilities,
        node_trains=tuple(train for train in node_trains if train is not None),
        node_bounds=_readonly(node_bounds, np.dtype(np.float64)),
        local_discarded_bounds=_readonly(local_bounds, np.dtype(np.float64)),
        parents=parents,
        depths=depths,
    )


def recompose_policy_delta_tt(
    baseline: PolicyDeltaTTCache,
    candidate_policy: Policy,
) -> PolicyDeltaTTRecomposition:
    """Persistently update exactly the changed policy nodes and ancestors."""

    return apply_policy_delta_tt_plan(
        baseline,
        plan_policy_delta_tt(baseline, candidate_policy),
    )


def plan_policy_delta_tt(
    baseline: PolicyDeltaTTCache,
    candidate_policy: Policy,
) -> PolicyDeltaTTPlan:
    """Compile candidate probabilities and invalidation once for all seats."""

    return plan_policy_delta_tt_from_probabilities(
        baseline,
        compile_policy_probability_tape(
            baseline.layout,
            baseline.hands_by_player,
            candidate_policy,
        ),
    )


def plan_policy_delta_tt_from_probabilities(
    baseline: PolicyDeltaTTCache,
    candidate_probabilities: PolicyProbabilityTape,
) -> PolicyDeltaTTPlan:
    """Build a shared dirty plan from an already materialized candidate tape."""

    _validate_probability_tape(
        baseline.layout,
        baseline.hands_by_player,
        candidate_probabilities,
    )
    changed = tuple(
        node_index
        for node_index, (old, new) in enumerate(
            zip(baseline.probabilities, candidate_probabilities, strict=True)
        )
        if old is not None and new is not None and not np.array_equal(old, new)
    )
    dirty = ancestor_closure(baseline.parents, changed)
    return PolicyDeltaTTPlan(
        baseline_probabilities=baseline.probabilities,
        candidate_probabilities=candidate_probabilities,
        changed_policy_nodes=changed,
        dirty_nodes=dirty,
    )


def apply_policy_delta_tt_plan(
    baseline: PolicyDeltaTTCache,
    plan: PolicyDeltaTTPlan,
) -> PolicyDeltaTTRecomposition:
    """Apply one shared candidate plan to a single player-value cache."""

    if baseline.probabilities is not plan.baseline_probabilities:
        raise ValueError("policy-delta plan belongs to a different baseline tape")
    candidate_probabilities = plan.candidate_probabilities
    changed = plan.changed_policy_nodes
    dirty = plan.dirty_nodes
    dirty_mask = np.zeros(baseline.layout.public_node_count, dtype=np.bool_)
    dirty_mask[list(dirty)] = True

    node_trains = list(baseline.node_trains)
    node_bounds = baseline.node_bounds.copy()
    local_bounds = baseline.local_discarded_bounds.copy()
    recomputed = 0
    for node_index in range(baseline.layout.public_node_count - 1, -1, -1):
        if not dirty_mask[node_index]:
            continue
        node = baseline.layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            raise AssertionError("policy mutation unexpectedly dirtied a terminal")
        train, propagated, local = _compose_strategic_node(
            layout=baseline.layout,
            node_index=node_index,
            probabilities=candidate_probabilities,
            node_trains=node_trains,
            node_bounds=node_bounds,
            relative_tolerance=baseline.relative_tolerance,
            maximum_rank=baseline.maximum_rank,
        )
        node_trains[node_index] = train
        node_bounds[node_index] = propagated
        local_bounds[node_index] = local
        recomputed += 1

    cache = PolicyDeltaTTCache(
        layout=baseline.layout,
        hands_by_player=baseline.hands_by_player,
        terminal_trains=baseline.terminal_trains,
        terminal_bounds=baseline.terminal_bounds,
        relative_tolerance=baseline.relative_tolerance,
        maximum_rank=baseline.maximum_rank,
        probabilities=candidate_probabilities,
        node_trains=tuple(node_trains),
        node_bounds=_readonly(node_bounds, np.dtype(np.float64)),
        local_discarded_bounds=_readonly(local_bounds, np.dtype(np.float64)),
        parents=baseline.parents,
        depths=baseline.depths,
    )
    reused = sum(
        first is second
        for first, second in zip(
            baseline.node_trains,
            cache.node_trains,
            strict=True,
        )
    )
    return PolicyDeltaTTRecomposition(
        cache=cache,
        changed_policy_nodes=changed,
        dirty_nodes=dirty,
        recomputed_strategic_nodes=recomputed,
        reused_node_train_objects=reused,
    )


def ancestor_closure(
    parents: IntArray,
    changed_nodes: tuple[int, ...],
) -> tuple[int, ...]:
    """Return changed public nodes and every unique ancestor in sorted order."""

    if parents.ndim != 1:
        raise ValueError("public-tree parents must be a vector")
    dirty: set[int] = set()
    for supplied in changed_nodes:
        if isinstance(supplied, bool) or supplied not in range(len(parents)):
            raise ValueError("changed public node is outside the cache")
        node = supplied
        while node >= 0:
            dirty.add(node)
            node = int(parents[node])
    return tuple(sorted(dirty))


def _compose_strategic_node(
    *,
    layout: PublicTreeTensorEvaluator,
    node_index: int,
    probabilities: tuple[FloatArray | None, ...],
    node_trains: list[TensorTrain | None] | list[TensorTrain],
    node_bounds: FloatArray,
    relative_tolerance: float,
    maximum_rank: int | None,
) -> tuple[TensorTrain, float, float]:
    node = layout.nodes[node_index]
    node_probabilities = probabilities[node_index]
    if node.player == TERMINAL_PLAYER or node_probabilities is None:
        raise AssertionError("strategic composition received a terminal node")
    weighted = []
    for action_index, child in enumerate(node.children):
        child_train = node_trains[child]
        if child_train is None:
            raise AssertionError("public child was not composed before its parent")
        weighted.append(
            multiply_mode_vector(
                child_train,
                node.player,
                node_probabilities[:, action_index],
            )
        )
    raw = sum_tensor_trains(tuple(weighted))
    rounded = round_tensor_train(
        raw,
        relative_tolerance=relative_tolerance,
        maximum_rank=maximum_rank,
    )
    local = rounded.discarded_frobenius_bound
    propagated = max(float(node_bounds[child]) for child in node.children) + local
    return rounded.train, propagated, local


def _tree_metadata(
    layout: PublicTreeTensorEvaluator,
) -> tuple[IntArray, IntArray]:
    parents = np.full(layout.public_node_count, -1, dtype=np.int32)
    depths = np.zeros(layout.public_node_count, dtype=np.int32)
    for node_index, node in enumerate(layout.nodes):
        for child in node.children:
            if child <= node_index or parents[child] != -1:
                raise ValueError("public layout is not a forward-indexed tree")
            parents[child] = node_index
            depths[child] = depths[node_index] + 1
    if len(parents) and parents[0] != -1:
        raise ValueError("public root unexpectedly has a parent")
    if len(parents) > 1 and np.any(parents[1:] < 0):
        raise ValueError("public layout contains an unreachable node")
    return (
        _readonly(parents, np.dtype(np.int32)),
        _readonly(depths, np.dtype(np.int32)),
    )


def _validate_terminals(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    terminal_trains: Mapping[str, TensorTrain],
    terminal_bounds: Mapping[str, float],
) -> tuple[str, ...]:
    if len(hands_by_player) != layout.num_players:
        raise ValueError("policy cache requires one hand axis per player")
    shape = tuple(len(hands) for hands in hands_by_player)
    terminal_keys = _terminal_keys_by_slot(layout)
    expected = set(terminal_keys)
    if set(terminal_trains) != expected or set(terminal_bounds) != expected:
        raise ValueError("terminal train and bound keys must match payoff groups")
    if any(train.shape != shape for train in terminal_trains.values()):
        raise ValueError("terminal train modes do not match policy-cache axes")
    if any(
        isinstance(bound, bool)
        or not math.isfinite(float(bound))
        or float(bound) < 0.0
        for bound in terminal_bounds.values()
    ):
        raise ValueError("terminal bounds must be finite and nonnegative")
    return terminal_keys


def _validate_rounding(
    relative_tolerance: float,
    maximum_rank: int | None,
) -> None:
    if (
        isinstance(relative_tolerance, bool)
        or not math.isfinite(relative_tolerance)
        or not 0.0 <= relative_tolerance < 1.0
    ):
        raise ValueError("relative tolerance must lie in [0, 1)")
    if maximum_rank is not None and (
        isinstance(maximum_rank, bool) or maximum_rank <= 0
    ):
        raise ValueError("maximum rank must be positive or None")


def _validate_probability_tape(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    probabilities: PolicyProbabilityTape,
) -> None:
    if len(probabilities) != layout.public_node_count:
        raise ValueError("policy probability tape length differs from public tree")
    for node, values in zip(layout.nodes, probabilities, strict=True):
        if node.player == TERMINAL_PLAYER:
            if values is not None:
                raise ValueError("terminal policy probability entry must be None")
            continue
        expected = (len(hands_by_player[node.player]), len(node.actions))
        if (
            values is None
            or values.shape != expected
            or values.dtype != np.float64
            or not values.flags.c_contiguous
            or values.flags.writeable
            or not np.all(np.isfinite(values))
            or np.any(values < 0.0)
            or not np.allclose(np.sum(values, axis=1), 1.0, atol=1e-14, rtol=0.0)
        ):
            raise ValueError("policy probability tape entry is invalid")


def _readonly_probabilities(
    supplied: tuple[np.ndarray | None, ...],
) -> tuple[FloatArray | None, ...]:
    return tuple(
        None if values is None else _readonly(values, np.dtype(np.float64))
        for values in supplied
    )


def _readonly(values: object, dtype: np.dtype[object]) -> NDArray[object]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result
