"""Additive instrumentation for the frozen policy-delta TT compiler."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    PolicyProbabilityTape,
    _compose_strategic_node,
    _readonly,
    _tree_metadata,
    _validate_probability_tape,
    _validate_rounding,
    _validate_terminals,
)
from .game import TERMINAL_PLAYER
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards
from .tensor_train import TensorTrain

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ProfiledPolicyDeltaTTCache:
    """One cold cache plus measured strategic-node composition times."""

    cache: PolicyDeltaTTCache
    node_compose_ms: FloatArray


def profile_policy_delta_tt_cache_from_probabilities(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    probabilities: PolicyProbabilityTape,
    terminal_trains: Mapping[str, TensorTrain],
    terminal_bounds: Mapping[str, float],
    *,
    relative_tolerance: float,
    maximum_rank: int | None,
) -> ProfiledPolicyDeltaTTCache:
    """Cold-compose identically while timing each strategic fold and round."""

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
    node_compose_ms = np.zeros(layout.public_node_count, dtype=np.float64)

    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            key = terminal_keys[node.terminal_slot]
            node_trains[node_index] = terminal_trains[key]
            node_bounds[node_index] = float(terminal_bounds[key])
            continue
        started = time.perf_counter()
        train, propagated, local = _compose_strategic_node(
            layout=layout,
            node_index=node_index,
            probabilities=probabilities,
            node_trains=node_trains,
            node_bounds=node_bounds,
            relative_tolerance=relative_tolerance,
            maximum_rank=maximum_rank,
        )
        node_compose_ms[node_index] = (time.perf_counter() - started) * 1000.0
        node_trains[node_index] = train
        node_bounds[node_index] = propagated
        local_bounds[node_index] = local

    if any(train is None for train in node_trains):
        raise AssertionError("profiled policy composition left an uncomputed node")
    cache = PolicyDeltaTTCache(
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
    return ProfiledPolicyDeltaTTCache(
        cache=cache,
        node_compose_ms=_readonly(node_compose_ms, np.dtype(np.float64)),
    )
