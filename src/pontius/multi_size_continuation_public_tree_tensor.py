"""Exact sized public-tree continuations after an actor-labelled prefix."""

from __future__ import annotations

import numpy as np

from .game import Action, TERMINAL_PLAYER
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .public_tree_tensor import _PublicNode, _topology_signature
from .river_multi_size import BetAction
from .river_multiway import MultiwayRiverDeal
from .river_multiway_multi_size import (
    MultiwayMultiSizeRiverHoldem,
    MultiwayMultiSizeRiverState,
)


def state_after_sized_public_prefix(
    game: MultiwayMultiSizeRiverHoldem,
    deal: MultiwayRiverDeal,
    public_prefix: tuple[tuple[int, Action], ...],
) -> MultiwayMultiSizeRiverState:
    """Replay one exact sized public history on a representative deal."""

    state = MultiwayMultiSizeRiverState(game=game, deal=deal, next_player=0)
    for supplied_actor, action in public_prefix:
        if supplied_actor != state.current_player:
            raise ValueError("sized public prefix actor disagrees with response order")
        state = state.apply_action(action)
    return state


class MultiSizeContinuationPublicTreeTensorEvaluator(
    MultiSizePublicTreeTensorEvaluator
):
    """Prune a sized exact layout to one current-decision continuation.

    The empty prefix is intentionally valid and denotes the street-opening
    decision. This is needed to measure action width for seat zero without
    inventing a public action that did not occur.
    """

    def __init__(
        self,
        game: MultiwayMultiSizeRiverHoldem,
        *,
        public_prefix: tuple[tuple[int, Action], ...],
    ) -> None:
        canonical = []
        for actor, action in public_prefix:
            if isinstance(actor, bool) or actor not in range(game.num_players):
                raise ValueError("sized continuation prefix has an invalid actor")
            if not isinstance(action, (str, BetAction)):
                raise ValueError("sized continuation prefix has an invalid action")
            canonical.append((actor, action))
        self.public_prefix = tuple(canonical)

        super().__init__(game)
        representative = state_after_sized_public_prefix(
            game,
            self.deals[0],
            self.public_prefix,
        )
        if representative.current_player == TERMINAL_PLAYER:
            raise ValueError("sized continuation prefix must end at a decision node")
        old_root = next(
            (
                index
                for index, node in enumerate(self.nodes)
                if node.history == representative.history
            ),
            None,
        )
        if old_root is None:
            raise ValueError("sized continuation root is absent from full layout")

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
        old_descriptors = self.terminal_descriptors
        nodes = []
        schema: dict[str, tuple[Action, ...]] = {}
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
            self.terminal_values[old_terminal_slots],
            dtype=np.float64,
        )
        self.terminal_descriptors = tuple(
            old_descriptors[old_slot] for old_slot in old_terminal_slots
        )
        self.unique_terminal_descriptor_count = len(set(self.terminal_descriptors))

        flat_children = tuple(child for node in self.nodes for child in node.children)
        offsets = [0]
        for node in self.nodes:
            offsets.append(offsets[-1] + len(node.children))
        self.node_players = np.ascontiguousarray(
            [node.player for node in self.nodes],
            dtype=np.int32,
        )
        self.child_offsets = np.ascontiguousarray(offsets, dtype=np.int32)
        self.children = np.ascontiguousarray(flat_children, dtype=np.int32)
        self.terminal_slots = np.ascontiguousarray(
            [node.terminal_slot for node in self.nodes],
            dtype=np.int32,
        )

    def topology_mismatch_count(self, maximum_deals: int | None = None) -> int:
        """Recheck the continuation topology on all or a fixed deal sample."""

        if maximum_deals is not None:
            if isinstance(maximum_deals, bool) or maximum_deals <= 0:
                raise ValueError("maximum topology-validation deals must be positive")
            if len(self.deals) > maximum_deals:
                selected = np.linspace(
                    0,
                    len(self.deals) - 1,
                    num=maximum_deals,
                    dtype=np.int64,
                )
                deals = tuple(self.deals[int(index)] for index in selected)
            else:
                deals = self.deals
        else:
            deals = self.deals
        return sum(
            _topology_signature(
                state_after_sized_public_prefix(
                    self.game,
                    deal,
                    self.public_prefix,
                )
            )
            != self._reference_topology_signature
            for deal in deals
        )
