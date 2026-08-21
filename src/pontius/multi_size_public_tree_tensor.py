"""Exact deal-axis public-tree evaluator for sized multiway river betting."""

from __future__ import annotations

from dataclasses import replace
import numpy as np

from .game import Action, TERMINAL_PLAYER
from .public_tree_tensor import (
    PublicTreeTensorEvaluator,
    _PublicNode,
    _topology_signature,
)
from .river import HoleCards, evaluate_seven
from .river_multiway import MultiwayRiverDeal
from .river_multiway_multi_size import (
    MultiwayMultiSizeRiverHoldem,
    MultiwayMultiSizeRiverState,
)


class MultiSizePublicTreeTensorEvaluator(PublicTreeTensorEvaluator):
    """Compile a sized multiway public tree over one explicit deal axis.

    The inherited evaluation and best-response passes are deliberately reused.
    Only topology construction and contribution-aware terminal tensors differ
    from the frozen one-size evaluator.
    """

    def __init__(self, game: MultiwayMultiSizeRiverHoldem) -> None:
        if not isinstance(game, MultiwayMultiSizeRiverHoldem):
            raise TypeError(
                "sized public-tree tensor evaluation requires "
                "MultiwayMultiSizeRiverHoldem"
            )
        if not game.deals:
            raise ValueError("sized public-tree evaluation requires positive support")

        self.game = game
        self.num_players = game.num_players
        self.deals = tuple(deal for deal, _ in game.deals)
        self.deal_count = len(self.deals)
        self.weights = np.ascontiguousarray(
            [probability for _, probability in game.deals],
            dtype=np.float64,
        )

        self.hands_by_player = tuple(
            tuple(sorted(game.marginal_distribution(player)))
            for player in range(self.num_players)
        )
        hand_maps = tuple(
            {hand: index for index, hand in enumerate(hands)}
            for hands in self.hands_by_player
        )
        self.hand_ids = np.empty(
            (self.deal_count, self.num_players),
            dtype=np.int32,
            order="C",
        )
        representative_deals: list[dict[HoleCards, MultiwayRiverDeal]] = [
            {} for _ in range(self.num_players)
        ]
        for deal_index, deal in enumerate(self.deals):
            for player in range(self.num_players):
                hand = deal.hand(player)
                self.hand_ids[deal_index, player] = hand_maps[player][hand]
                representative_deals[player].setdefault(hand, deal)

        public_states: list[MultiwayMultiSizeRiverState] = []
        raw_nodes: list[tuple[int, tuple[Action, ...], tuple[int, ...], int]] = []
        terminal_states: list[MultiwayMultiSizeRiverState] = []
        representative_root = MultiwayMultiSizeRiverState(
            game=game,
            deal=self.deals[0],
            next_player=0,
        )

        def compile_state(state: MultiwayMultiSizeRiverState) -> int:
            node_index = len(raw_nodes)
            public_states.append(state)
            raw_nodes.append((state.current_player, (), (), -1))
            if state.current_player == TERMINAL_PLAYER:
                terminal_slot = len(terminal_states)
                terminal_states.append(state)
                raw_nodes[node_index] = (TERMINAL_PLAYER, (), (), terminal_slot)
                return node_index
            actions = tuple(state.legal_actions())
            if not actions or len(set(actions)) != len(actions):
                raise ValueError("public strategic actions must be nonempty and unique")
            children = tuple(
                compile_state(state.apply_action(action)) for action in actions
            )
            raw_nodes[node_index] = (
                state.current_player,
                actions,
                children,
                -1,
            )
            return node_index

        if compile_state(representative_root) != 0:
            raise AssertionError("compiled public-tree root must have index zero")

        nodes: list[_PublicNode] = []
        schema: dict[str, tuple[Action, ...]] = {}
        for state, (player, actions, children, terminal_slot) in zip(
            public_states,
            raw_nodes,
            strict=True,
        ):
            if player == TERMINAL_PLAYER:
                keys: tuple[str, ...] = ()
            else:
                keys_list = []
                for hand in self.hands_by_player[player]:
                    dealt_state = replace(
                        state,
                        deal=representative_deals[player][hand],
                    )
                    key = dealt_state.information_state_key(player)
                    previous = schema.setdefault(key, actions)
                    if previous != actions:
                        raise ValueError(f"inconsistent action schema at {key!r}")
                    keys_list.append(key)
                keys = tuple(keys_list)
            nodes.append(
                _PublicNode(
                    player=player,
                    actions=actions,
                    children=children,
                    terminal_slot=terminal_slot,
                    history=state.history,
                    information_keys=keys,
                )
            )
        self.nodes = tuple(nodes)
        self._information_schema = dict(sorted(schema.items()))
        self._reference_topology_signature = _topology_signature(representative_root)

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

        literal_ranks = tuple(
            tuple(
                evaluate_seven((*game.board, *deal.hand(player)))
                for player in range(self.num_players)
            )
            for deal in self.deals
        )
        ordered_ranks = tuple(
            sorted({rank for deal_ranks in literal_ranks for rank in deal_ranks})
        )
        rank_code = {rank: index for index, rank in enumerate(ordered_ranks)}
        hand_ranks = np.ascontiguousarray(
            [
                [rank_code[rank] for rank in deal_ranks]
                for deal_ranks in literal_ranks
            ],
            dtype=np.int32,
        )
        descriptor_by_slot = tuple(
            terminal.terminal_descriptor() for terminal in terminal_states
        )
        unique_descriptors = tuple(sorted(set(descriptor_by_slot)))
        descriptor_values = {
            descriptor: self._terminal_values_for_descriptor(
                hand_ranks,
                contenders=descriptor[0],
                contribution=descriptor[1],
            )
            for descriptor in unique_descriptors
        }
        self.terminal_values = np.empty(
            (len(terminal_states), self.deal_count, self.num_players),
            dtype=np.float64,
            order="C",
        )
        for terminal_slot, descriptor in enumerate(descriptor_by_slot):
            self.terminal_values[terminal_slot] = descriptor_values[descriptor]
        self.terminal_descriptors = descriptor_by_slot
        self.unique_terminal_descriptor_count = len(unique_descriptors)

    def _terminal_values_for_descriptor(
        self,
        hand_ranks: np.ndarray,
        *,
        contenders: tuple[int, ...],
        contribution: float,
    ) -> np.ndarray:
        values = np.empty(
            (self.deal_count, self.num_players),
            dtype=np.float64,
            order="C",
        )
        contender_indices = np.asarray(contenders, dtype=np.int32)
        contender_ranks = hand_ranks[:, contender_indices]
        best = np.max(contender_ranks, axis=1)
        winner_mask = contender_ranks == best[:, None]
        winner_count = np.sum(winner_mask, axis=1)
        final_pot = self.game.pot + contribution * len(contenders)
        sunk_share = self.game.pot / self.num_players
        contributions = np.zeros(self.num_players, dtype=np.float64)
        if contribution > 0.0:
            contributions[contender_indices] = contribution
        values[:] = -sunk_share - contributions
        for local_index, player in enumerate(contenders):
            values[:, player] += winner_mask[:, local_index] * (
                final_pot / winner_count
            )
        if float(np.max(np.abs(np.sum(values, axis=1)))) > 1e-10:
            raise AssertionError("sized tensor terminal utilities must sum to zero")
        return values

    def topology_mismatch_count(self, maximum_deals: int | None = None) -> int:
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
        mismatches = 0
        for deal in deals:
            state = MultiwayMultiSizeRiverState(
                game=self.game,
                deal=deal,
                next_player=0,
            )
            if _topology_signature(state) != self._reference_topology_signature:
                mismatches += 1
        return mismatches

    def topology_summary(self) -> dict[str, int | bool]:
        result = super().topology_summary()
        result["unique_terminal_descriptors"] = self.unique_terminal_descriptor_count
        return result
