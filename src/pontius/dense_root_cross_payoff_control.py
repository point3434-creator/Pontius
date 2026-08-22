"""Literal deal-axis control for one root-node cross-payoff affine row.

This is a small independent oracle for CPU controls.  It keeps every policy
row except the public root fixed and forms the exact Float64 coefficient of
each root hand/action choice for an arbitrary payoff seat.  It deliberately
does not implement a solver, a warm step, or a deployable policy path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape


@dataclass(frozen=True, slots=True)
class DenseRootCrossPayoffRead:
    """The one hand/action coefficient table consumed by the row primitive."""

    node_index: int
    action_numerators: np.ndarray


@dataclass(frozen=True, slots=True)
class DenseRootCrossPayoffResult:
    """Literal source value and root read with acting/payoff roles separated."""

    traverser: int
    payoff_player: int
    source_value: float
    reads: tuple[DenseRootCrossPayoffRead, ...]


def dense_root_cross_payoff_control(
    layout: Any,
    probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    payoff_player: int,
) -> DenseRootCrossPayoffResult:
    """Return the literal root coefficients for one fixed-policy payoff.

    The public root is the only open policy row.  Every child continuation is
    evaluated from the supplied probability tape, including later decisions
    by the same acting seat.  The coefficient table therefore describes an
    exact one-current-node edit, not a full behavioral or sequence-form axis.
    """

    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if isinstance(player, bool) or player not in range(layout.num_players):
            raise ValueError(f"dense root cross-payoff {label} player is outside the layout")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("dense root cross-payoff tape differs from the public tree")
    root = layout.nodes[0]
    if root.player == TERMINAL_PLAYER or root.player != acting_player:
        raise ValueError("dense root cross-payoff root belongs to another player")

    continuation = np.empty(
        (layout.public_node_count, layout.deal_count),
        dtype=np.float64,
        order="C",
    )
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continuation[node_index] = layout.terminal_values[
                node.terminal_slot, :, payoff_player
            ]
            continue
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise ValueError("dense root cross-payoff strategic probability is absent")
        expected_shape = (
            len(layout.hands_by_player[node.player]),
            len(node.actions),
        )
        if node_probabilities.shape != expected_shape:
            raise ValueError("dense root cross-payoff probability shape differs")
        if not np.all(np.isfinite(node_probabilities)):
            raise FloatingPointError("dense root cross-payoff probability is invalid")
        actor_hand_ids = layout.hand_ids[:, node.player]
        continuation[node_index].fill(0.0)
        for action_index, child in enumerate(node.children):
            continuation[node_index] += (
                node_probabilities[actor_hand_ids, action_index]
                * continuation[child]
            )

    root_hand_ids = layout.hand_ids[:, acting_player]
    hand_count = len(layout.hands_by_player[acting_player])
    numerators = np.empty(
        (hand_count, len(root.actions)),
        dtype=np.float64,
        order="C",
    )
    for action_index, child in enumerate(root.children):
        numerators[:, action_index] = np.bincount(
            root_hand_ids,
            weights=layout.weights * continuation[child],
            minlength=hand_count,
        )
    if not np.all(np.isfinite(numerators)):
        raise FloatingPointError("dense root cross-payoff coefficient is invalid")
    numerators.flags.writeable = False
    source_value = float(layout.weights @ continuation[0])
    if not np.isfinite(source_value):
        raise FloatingPointError("dense root cross-payoff source value is invalid")
    return DenseRootCrossPayoffResult(
        traverser=acting_player,
        payoff_player=payoff_player,
        source_value=source_value,
        reads=(DenseRootCrossPayoffRead(0, numerators),),
    )
