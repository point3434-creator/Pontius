"""Additive exact continuation subtree for the one-bet public tensor layout."""

from __future__ import annotations

import numpy as np

from .game import TERMINAL_PLAYER
from .public_tree_tensor import (
    PublicTreeTensorEvaluator,
    _PublicNode,
    _topology_signature,
)
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem, MultiwayRiverState


def _state_after_public_prefix(
    game: MultiwayRiverHoldem,
    deal: MultiwayRiverDeal,
    public_prefix: tuple[tuple[int, str], ...],
) -> MultiwayRiverState:
    state = MultiwayRiverState(game=game, deal=deal, next_player=0)
    for supplied_actor, action in public_prefix:
        if supplied_actor != state.current_player:
            raise ValueError("public prefix actor disagrees with legal response order")
        state = state.apply_action(action)
    return state


class ContinuationPublicTreeTensorEvaluator(PublicTreeTensorEvaluator):
    """Prune an exact full layout to one actor-labelled public continuation."""

    def __init__(
        self,
        game: MultiwayRiverHoldem,
        *,
        public_prefix: tuple[tuple[int, str], ...],
    ) -> None:
        if not public_prefix:
            raise ValueError("continuation public prefix must be nonempty")
        canonical = []
        for actor, action in public_prefix:
            if isinstance(actor, bool) or actor not in range(game.num_players):
                raise ValueError("continuation public prefix contains an invalid actor")
            if not isinstance(action, str):
                raise ValueError("continuation public prefix action must be text")
            canonical.append((actor, action))
        self.public_prefix = tuple(canonical)

        super().__init__(game)
        representative = _state_after_public_prefix(
            game,
            self.deals[0],
            self.public_prefix,
        )
        if representative.current_player == TERMINAL_PLAYER:
            raise ValueError("public continuation prefix must end at a decision node")
        root_history = representative.history
        old_root = next(
            (index for index, node in enumerate(self.nodes) if node.history == root_history),
            None,
        )
        if old_root is None:
            raise ValueError("public continuation root is absent from full layout")

        old_indices = []

        def collect(old_index: int) -> None:
            old_indices.append(old_index)
            for child in self.nodes[old_index].children:
                collect(child)

        collect(old_root)
        old_to_new = {old: new for new, old in enumerate(old_indices)}
        old_terminal_slots = [
            self.nodes[old].terminal_slot
            for old in old_indices
            if self.nodes[old].terminal_slot >= 0
        ]
        terminal_to_new = {
            old: new for new, old in enumerate(old_terminal_slots)
        }
        nodes = []
        schema: dict[str, tuple[object, ...]] = {}
        for old_index in old_indices:
            old = self.nodes[old_index]
            node = _PublicNode(
                player=old.player,
                actions=old.actions,
                children=tuple(old_to_new[child] for child in old.children),
                terminal_slot=(
                    -1
                    if old.terminal_slot < 0
                    else terminal_to_new[old.terminal_slot]
                ),
                history=old.history,
                information_keys=old.information_keys,
            )
            nodes.append(node)
            for key in node.information_keys:
                schema[key] = node.actions
        self.nodes = tuple(nodes)
        self._information_schema = dict(sorted(schema.items()))
        self._reference_topology_signature = _topology_signature(representative)
        self.terminal_values = np.ascontiguousarray(
            self.terminal_values[old_terminal_slots], dtype=np.float64
        )

        flat_children = tuple(child for node in self.nodes for child in node.children)
        offsets = [0]
        for node in self.nodes:
            offsets.append(offsets[-1] + len(node.children))
        self.node_players = np.ascontiguousarray(
            [node.player for node in self.nodes], dtype=np.int32
        )
        self.child_offsets = np.ascontiguousarray(offsets, dtype=np.int32)
        self.children = np.ascontiguousarray(flat_children, dtype=np.int32)
        self.terminal_slots = np.ascontiguousarray(
            [node.terminal_slot for node in self.nodes], dtype=np.int32
        )

    def topology_mismatch_count(self) -> int:
        mismatches = 0
        for deal in self.deals:
            state = _state_after_public_prefix(
                self.game,
                deal,
                self.public_prefix,
            )
            if _topology_signature(state) != self._reference_topology_signature:
                mismatches += 1
        return mismatches
