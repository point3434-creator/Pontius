"""Behavioral affine rows from full target-omitted adjoint reads.

The shortcut in this module is valid only when the compiled public topology
proves that no player acts twice on a root-to-terminal path.  General
repeated-actor topologies must use sequence-form rows instead.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape
from .one_seat_convex_generation import require_compiled_behavioral_affine_shortcut
from .sequence_form_open_axis import (
    OpenAxisNodeCoefficients,
    SequenceFormAffineRow,
)


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def behavioral_open_axis_payoff_row(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    traverser_result: Any,
    *,
    acting_player: int,
    source_value: float,
) -> SequenceFormAffineRow:
    """Build one exact full behavioral-axis payoff row from adjoint reads.

    ``source_value`` determines the affine constant contributed by paths on
    which the acting seat never moves.  It is also an intercept identity
    control: the returned row evaluates to that value at the source tape.
    """

    require_compiled_behavioral_affine_shortcut(layout)
    if (
        isinstance(acting_player, bool)
        or acting_player not in range(layout.num_players)
    ):
        raise ValueError("behavioral open-axis acting player is outside the layout")
    if traverser_result.traverser != acting_player:
        raise ValueError("behavioral open-axis result belongs to another acting player")
    if len(source_probabilities) != layout.public_node_count:
        raise ValueError("behavioral open-axis probability tape differs from tree")
    if not np.isfinite(source_value):
        raise ValueError("behavioral open-axis source value must be finite")

    expected_nodes = tuple(
        node_index
        for node_index, node in enumerate(layout.nodes)
        if node.player == acting_player
    )
    reads = {int(read.node_index): read for read in traverser_result.reads}
    if tuple(sorted(reads)) != expected_nodes:
        raise ValueError("behavioral open-axis reads do not exactly cover acting nodes")

    nodes = []
    source_linear = 0.0
    for node_index in expected_nodes:
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            raise AssertionError("behavioral open-axis acting node is terminal")
        probabilities = source_probabilities[node_index]
        values = np.asarray(reads[node_index].action_numerators, dtype=np.float64)
        expected_shape = (values.shape[0], len(node.actions))
        if (
            probabilities is None
            or values.shape != expected_shape
            or probabilities.shape != values.shape
        ):
            raise ValueError("behavioral open-axis read has the wrong action shape")
        if not np.all(np.isfinite(values)):
            raise FloatingPointError("behavioral open-axis coefficient is invalid")
        source_linear += float(
            np.einsum("ha,ha->", probabilities, values, optimize=True)
        )
        nodes.append(OpenAxisNodeCoefficients(node_index, _readonly(values)))

    row = SequenceFormAffineRow(
        acting_player=acting_player,
        constant=float(source_value - source_linear),
        nodes=tuple(nodes),
    )
    error = abs(row.value(source_probabilities) - source_value)
    if error > 2e-11:
        raise ArithmeticError("behavioral open-axis source intercept differs")
    return row
