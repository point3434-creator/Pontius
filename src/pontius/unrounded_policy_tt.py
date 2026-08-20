"""Exact direct-sum public-policy TT composition without per-node SVD.

The rounded cache is economical when its roots are reused, but a CFR step
rebuilds one player-value cache after each alternating traverser update.  This
screening compiler moves no approximation onto that hot write path: children
are weighted by unary policy vectors and combined as exact block direct sums.
The tradeoff is explicitly larger ranks and a wider subsequent open read.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Mapping

import numpy as np

from .game import TERMINAL_PLAYER
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    PolicyProbabilityTape,
    _readonly,
    _tree_metadata,
    _validate_probability_tape,
    _validate_terminals,
)
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards
from .tensor_train import TensorTrain
from .tensor_train_algebra import multiply_mode_vector, sum_tensor_trains


@dataclass(frozen=True, slots=True)
class UnroundedPolicyTTCompilation:
    cache: PolicyDeltaTTCache
    strategic_nodes: int
    maximum_rank: int
    compile_ms: float


def compile_unrounded_policy_tt_cache_from_probabilities(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    probabilities: PolicyProbabilityTape,
    terminal_trains: Mapping[str, TensorTrain],
    terminal_bounds: Mapping[str, float],
) -> UnroundedPolicyTTCompilation:
    """Compose every public node exactly as TT direct sums, with no SVD."""

    terminal_keys = _validate_terminals(
        layout,
        hands_by_player,
        terminal_trains,
        terminal_bounds,
    )
    _validate_probability_tape(layout, hands_by_player, probabilities)
    parents, depths = _tree_metadata(layout)
    node_trains: list[TensorTrain | None] = [None] * layout.public_node_count
    node_bounds = np.zeros(layout.public_node_count, dtype=np.float64)
    local_bounds = np.zeros(layout.public_node_count, dtype=np.float64)
    strategic = 0
    maximum_rank = 1
    started = time.perf_counter()

    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            key = terminal_keys[node.terminal_slot]
            train = terminal_trains[key]
            node_trains[node_index] = train
            node_bounds[node_index] = float(terminal_bounds[key])
            maximum_rank = max(maximum_rank, *train.ranks)
            continue
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise AssertionError("strategic public node has no policy probabilities")
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
        train = sum_tensor_trains(tuple(weighted))
        node_trains[node_index] = train
        node_bounds[node_index] = max(
            float(node_bounds[child]) for child in node.children
        )
        strategic += 1
        maximum_rank = max(maximum_rank, *train.ranks)

    if any(train is None for train in node_trains):
        raise AssertionError("unrounded policy composition left a missing node")
    cache = PolicyDeltaTTCache(
        layout=layout,
        hands_by_player=hands_by_player,
        terminal_trains=dict(terminal_trains),
        terminal_bounds=dict(terminal_bounds),
        relative_tolerance=0.0,
        maximum_rank=None,
        probabilities=probabilities,
        node_trains=tuple(train for train in node_trains if train is not None),
        node_bounds=_readonly(node_bounds, np.dtype(np.float64)),
        local_discarded_bounds=_readonly(local_bounds, np.dtype(np.float64)),
        parents=parents,
        depths=depths,
    )
    return UnroundedPolicyTTCompilation(
        cache=cache,
        strategic_nodes=strategic,
        maximum_rank=maximum_rank,
        compile_ms=(time.perf_counter() - started) * 1000.0,
    )
