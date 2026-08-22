"""Sparse master axis for exactly one current public decision node."""

from __future__ import annotations

from typing import Any, Mapping

from .behavioral_one_seat_master import (
    BehavioralInformationSet,
    BehavioralOneSeatAxis,
)
from .game import TERMINAL_PLAYER
from .public_policy_tt import _information_key


def compile_public_node_behavioral_axis(
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    blueprint: Mapping[str, Mapping[Any, float]],
    *,
    public_node: int,
) -> BehavioralOneSeatAxis:
    """Compile the exact simplex variables for one actor-labelled public node."""

    if isinstance(public_node, bool) or public_node not in range(
        layout.public_node_count
    ):
        raise ValueError("public-node behavioral axis is outside the layout")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("public-node axis requires one external hand axis per seat")
    node = layout.nodes[public_node]
    if node.player == TERMINAL_PLAYER:
        raise ValueError("public-node behavioral axis cannot open a terminal")
    acting_player = int(node.player)
    actions = tuple(node.actions)
    rows = []
    cursor = 0
    for hand_index, hand in enumerate(hands_by_player[acting_player]):
        key = _information_key(layout, acting_player, hand, node.history)
        if key not in blueprint or set(blueprint[key]) != set(actions):
            raise ValueError("public-node blueprint axis is incomplete")
        variables = tuple(range(cursor, cursor + len(actions)))
        cursor += len(actions)
        rows.append(
            BehavioralInformationSet(
                node_index=public_node,
                hand_index=hand_index,
                key=key,
                actions=actions,
                variable_indices=variables,
            )
        )
    if not rows:
        raise ValueError("public-node behavioral axis has no private hands")
    if len({row.key for row in rows}) != len(rows):
        raise ValueError("public-node external information keys are not unique")
    return BehavioralOneSeatAxis(
        acting_player=acting_player,
        information_sets=tuple(rows),
        acting_nodes=(public_node,),
        variable_count=cursor,
    )
