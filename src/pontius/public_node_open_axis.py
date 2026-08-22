"""Exact affine payoff rows for one current public decision node."""

from __future__ import annotations

from typing import Any

import numpy as np

from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape
from .sequence_form_open_axis import (
    OpenAxisNodeCoefficients,
    SequenceFormAffineRow,
)


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def public_node_open_axis_payoff_row(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    traverser_result: Any,
    *,
    acting_player: int,
    public_node: int,
    source_value: float,
) -> SequenceFormAffineRow:
    """Open exactly one current node while every other policy row stays fixed."""

    if (
        isinstance(acting_player, bool)
        or acting_player not in range(layout.num_players)
    ):
        raise ValueError("public-node open axis has an invalid acting player")
    if isinstance(public_node, bool) or public_node not in range(
        layout.public_node_count
    ):
        raise ValueError("public-node open axis is outside the layout")
    node = layout.nodes[public_node]
    if node.player == TERMINAL_PLAYER or node.player != acting_player:
        raise ValueError("public-node open axis belongs to another player")
    if traverser_result.traverser != acting_player:
        raise ValueError("public-node open-axis result belongs to another player")
    if len(source_probabilities) != layout.public_node_count:
        raise ValueError("public-node source tape differs from the layout")
    if not np.isfinite(source_value):
        raise ValueError("public-node source value must be finite")

    matched_reads = tuple(
        read
        for read in traverser_result.reads
        if int(read.node_index) == public_node
    )
    if len(matched_reads) != 1:
        raise ValueError("public-node open-axis read is absent")
    read = matched_reads[0]
    probabilities = source_probabilities[public_node]
    values = np.asarray(read.action_numerators, dtype=np.float64)
    if (
        probabilities is None
        or values.shape != probabilities.shape
        or values.shape[1] != len(node.actions)
    ):
        raise ValueError("public-node open-axis read has the wrong action shape")
    if not np.all(np.isfinite(values)):
        raise FloatingPointError("public-node open-axis coefficient is invalid")
    source_linear = float(
        np.einsum("ha,ha->", probabilities, values, optimize=True)
    )
    row = SequenceFormAffineRow(
        acting_player=acting_player,
        constant=float(source_value - source_linear),
        nodes=(OpenAxisNodeCoefficients(public_node, _readonly(values)),),
    )
    if abs(row.value(source_probabilities) - source_value) > 2e-11:
        raise ArithmeticError("public-node open-axis source intercept differs")
    return row
