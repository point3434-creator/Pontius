"""Exact deal-axis tensor evaluation for the multiway river public tree.

The dependency tape intentionally supports generic extensive-form games.  This
module exploits a narrower fact of :class:`MultiwayRiverHoldem`: after the root
deal, every private deal has the identical public betting tree.  The tree is
compiled once and values are propagated over a contiguous deal axis.

No belief approximation occurs here.  Every positive joint deal, private hand,
information state, terminal payoff, and unilateral best-response action remains
literal.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import fsum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .evaluation import EvaluationResult, Policy, policy_distribution
from .game import Action, TERMINAL_PLAYER
from .river import HoleCards, _format_hole, evaluate_seven
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem, MultiwayRiverState

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]


@dataclass(frozen=True, slots=True)
class _PublicNode:
    player: int
    actions: tuple[Action, ...]
    children: tuple[int, ...]
    terminal_slot: int
    history: tuple[tuple[int, str], ...]
    information_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PublicTreeTensorResult:
    """An exact profile evaluation and every literal response action map."""

    evaluation: EvaluationResult
    best_response_actions: tuple[dict[str, Action], ...]


def _public_history(history: tuple[tuple[int, str], ...]) -> str:
    if not history:
        return "root"
    return "/".join(f"p{seat}:{action}" for seat, action in history)


def _topology_signature(state: MultiwayRiverState) -> tuple[object, ...]:
    """Return the complete DFS public signature below one dealt state."""

    records: list[object] = []

    def walk(current: MultiwayRiverState) -> None:
        player = current.current_player
        actions = tuple(current.legal_actions())
        records.append(
            (
                player,
                actions,
                current.history,
                current.bettor,
                current.pending_responders,
                tuple(sorted(current.callers)),
                tuple(sorted(current.folded)),
                current.terminal,
            )
        )
        if player == TERMINAL_PLAYER:
            return
        for action in actions:
            walk(current.apply_action(action))

    walk(state)
    return tuple(records)


class PublicTreeTensorEvaluator:
    """Compile one exact public tree and evaluate all private deals in Float64."""

    def __init__(self, game: MultiwayRiverHoldem) -> None:
        if not isinstance(game, MultiwayRiverHoldem):
            raise TypeError("public-tree tensor evaluation requires MultiwayRiverHoldem")
        if not game.deals:
            raise ValueError("public-tree tensor evaluation requires positive support")

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

        public_states: list[MultiwayRiverState] = []
        raw_nodes: list[tuple[int, tuple[Action, ...], tuple[int, ...], int]] = []
        terminal_states: list[MultiwayRiverState] = []
        representative_root = MultiwayRiverState(
            game=game,
            deal=self.deals[0],
            next_player=0,
        )

        def compile_state(state: MultiwayRiverState) -> int:
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

        root_index = compile_state(representative_root)
        if root_index != 0:
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

        flat_children = tuple(
            child for node in self.nodes for child in node.children
        )
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

        hand_ranks = tuple(
            tuple(
                evaluate_seven((*game.board, *deal.hand(player)))
                for player in range(self.num_players)
            )
            for deal in self.deals
        )
        terminal_values = np.empty(
            (len(terminal_states), self.deal_count, self.num_players),
            dtype=np.float64,
            order="C",
        )
        sunk_share = game.pot / self.num_players
        for terminal_slot, terminal in enumerate(terminal_states):
            contenders = (
                tuple(range(self.num_players))
                if terminal.bettor is None
                else tuple(sorted(terminal.callers))
            )
            contributions = tuple(
                game.bet_size
                if terminal.bettor is not None and player in terminal.callers
                else 0.0
                for player in range(self.num_players)
            )
            final_pot = game.pot + fsum(contributions)
            for deal_index in range(self.deal_count):
                best_rank = max(hand_ranks[deal_index][player] for player in contenders)
                winners = tuple(
                    player
                    for player in contenders
                    if hand_ranks[deal_index][player] == best_rank
                )
                winner_share = final_pot / len(winners)
                utilities = [
                    -sunk_share - contributions[player]
                    for player in range(self.num_players)
                ]
                for winner in winners:
                    utilities[winner] += winner_share
                if abs(fsum(utilities)) > 1e-10:
                    raise AssertionError("tensor terminal utilities must sum to zero")
                terminal_values[terminal_slot, deal_index] = utilities
        self.terminal_values = terminal_values

    @property
    def public_node_count(self) -> int:
        return len(self.nodes)

    @property
    def terminal_node_count(self) -> int:
        return self.terminal_values.shape[0]

    @property
    def strategic_node_count(self) -> int:
        return self.public_node_count - self.terminal_node_count

    def information_schema(self) -> dict[str, tuple[Action, ...]]:
        return dict(self._information_schema)

    def topology_mismatch_count(self) -> int:
        """Validate the compiled public signature against every supported deal."""

        mismatches = 0
        for deal in self.deals:
            state = MultiwayRiverState(game=self.game, deal=deal, next_player=0)
            if _topology_signature(state) != self._reference_topology_signature:
                mismatches += 1
        return mismatches

    def _prepare_policy(self, policy: Policy) -> tuple[FloatArray | None, ...]:
        probabilities: list[FloatArray | None] = []
        for node in self.nodes:
            if node.player == TERMINAL_PLAYER:
                probabilities.append(None)
                continue
            hand_probabilities = np.empty(
                (len(node.information_keys), len(node.actions)),
                dtype=np.float64,
                order="C",
            )
            for hand_index, key in enumerate(node.information_keys):
                distribution = policy_distribution(policy, key, node.actions)
                hand_probabilities[hand_index] = tuple(
                    distribution[action] for action in node.actions
                )
            deal_probabilities = np.ascontiguousarray(
                hand_probabilities[self.hand_ids[:, node.player]],
                dtype=np.float64,
            )
            probabilities.append(deal_probabilities)
        return tuple(probabilities)

    def policy_tensors_are_float64_contiguous(self, policy: Policy) -> bool:
        return all(
            values is None
            or (values.dtype == np.float64 and values.flags.c_contiguous)
            for values in self._prepare_policy(policy)
        )

    def numeric_tensors_are_float64_contiguous(self) -> bool:
        return all(
            values.dtype == np.float64 and values.flags.c_contiguous
            for values in (self.weights, self.terminal_values)
        ) and all(
            values.dtype == np.int32 and values.flags.c_contiguous
            for values in (
                self.hand_ids,
                self.node_players,
                self.child_offsets,
                self.children,
                self.terminal_slots,
            )
        )

    def _expected_utilities(
        self,
        probabilities: tuple[FloatArray | None, ...],
    ) -> tuple[float, ...]:
        values = np.empty(
            (self.public_node_count, self.deal_count, self.num_players),
            dtype=np.float64,
            order="C",
        )
        for node_index in range(self.public_node_count - 1, -1, -1):
            node = self.nodes[node_index]
            if node.player == TERMINAL_PLAYER:
                values[node_index] = self.terminal_values[node.terminal_slot]
                continue
            node_probabilities = probabilities[node_index]
            assert node_probabilities is not None
            values[node_index].fill(0.0)
            for action_index, child in enumerate(node.children):
                values[node_index] += (
                    node_probabilities[:, action_index, None] * values[child]
                )
        utilities = self.weights @ values[0]
        return tuple(float(value) for value in utilities)

    def _best_response(
        self,
        probabilities: tuple[FloatArray | None, ...],
        target_player: int,
    ) -> tuple[float, dict[str, Action]]:
        counterfactual_reach = np.zeros(
            (self.public_node_count, self.deal_count),
            dtype=np.float64,
            order="C",
        )
        counterfactual_reach[0] = self.weights
        for node_index, node in enumerate(self.nodes):
            if node.player == TERMINAL_PLAYER:
                continue
            if node.player == target_player:
                for child in node.children:
                    counterfactual_reach[child] = counterfactual_reach[node_index]
                continue
            node_probabilities = probabilities[node_index]
            assert node_probabilities is not None
            for action_index, child in enumerate(node.children):
                counterfactual_reach[child] = (
                    counterfactual_reach[node_index]
                    * node_probabilities[:, action_index]
                )

        continuation = np.empty(
            (self.public_node_count, self.deal_count),
            dtype=np.float64,
            order="C",
        )
        selected_actions: dict[str, Action] = {}
        deal_indices = np.arange(self.deal_count)
        target_hand_ids = self.hand_ids[:, target_player]
        target_hand_count = len(self.hands_by_player[target_player])
        for node_index in range(self.public_node_count - 1, -1, -1):
            node = self.nodes[node_index]
            if node.player == TERMINAL_PLAYER:
                continuation[node_index] = self.terminal_values[
                    node.terminal_slot,
                    :,
                    target_player,
                ]
                continue
            if node.player != target_player:
                node_probabilities = probabilities[node_index]
                assert node_probabilities is not None
                continuation[node_index].fill(0.0)
                for action_index, child in enumerate(node.children):
                    continuation[node_index] += (
                        node_probabilities[:, action_index] * continuation[child]
                    )
                continue

            action_scores = np.empty(
                (target_hand_count, len(node.actions)),
                dtype=np.float64,
                order="C",
            )
            for action_index, child in enumerate(node.children):
                action_scores[:, action_index] = np.bincount(
                    target_hand_ids,
                    weights=(
                        counterfactual_reach[node_index] * continuation[child]
                    ),
                    minlength=target_hand_count,
                )
            selected_by_hand = np.argmax(action_scores, axis=1)
            child_values = np.stack(
                tuple(continuation[child] for child in node.children),
                axis=1,
            )
            continuation[node_index] = child_values[
                deal_indices,
                selected_by_hand[target_hand_ids],
            ]
            for hand_index, key in enumerate(node.information_keys):
                selected_actions[key] = node.actions[int(selected_by_hand[hand_index])]

        best_response_value = float(self.weights @ continuation[0])
        return best_response_value, selected_actions

    def evaluate(self, policy: Policy) -> PublicTreeTensorResult:
        """Return exact utilities and unilateral best responses for ``policy``."""

        probabilities = self._prepare_policy(policy)
        utilities = self._expected_utilities(probabilities)
        responses = tuple(
            self._best_response(probabilities, player)
            for player in range(self.num_players)
        )
        best_response_values = tuple(value for value, _ in responses)
        deviation_gains = tuple(
            max(0.0, best_response - utility)
            for best_response, utility in zip(
                best_response_values,
                utilities,
                strict=True,
            )
        )
        nash_conv = fsum(deviation_gains)
        evaluation = EvaluationResult(
            utilities=utilities,
            best_response_values=best_response_values,
            deviation_gains=deviation_gains,
            nash_conv=nash_conv,
            exploitability=nash_conv / 2.0 if self.num_players == 2 else None,
        )
        return PublicTreeTensorResult(
            evaluation=evaluation,
            best_response_actions=tuple(actions for _, actions in responses),
        )

    def memory_summary(self) -> dict[str, int]:
        persistent_arrays = (
            self.weights,
            self.hand_ids,
            self.node_players,
            self.child_offsets,
            self.children,
            self.terminal_slots,
            self.terminal_values,
        )
        persistent_bytes = sum(values.nbytes for values in persistent_arrays)
        policy_bytes = sum(
            self.deal_count * len(node.actions) * np.dtype(np.float64).itemsize
            for node in self.nodes
            if node.player != TERMINAL_PLAYER
        )
        utility_bytes = (
            self.public_node_count
            * self.deal_count
            * self.num_players
            * np.dtype(np.float64).itemsize
        )
        response_bytes = (
            2
            * self.public_node_count
            * self.deal_count
            * np.dtype(np.float64).itemsize
        )
        maximum_score_bytes = max(
            (
                len(self.hands_by_player[node.player])
                * len(node.actions)
                * np.dtype(np.float64).itemsize
                for node in self.nodes
                if node.player != TERMINAL_PLAYER
            ),
            default=0,
        )
        hot_scratch_bytes = policy_bytes + max(
            utility_bytes,
            response_bytes + maximum_score_bytes,
        )
        return {
            "persistent_numeric_bytes": persistent_bytes,
            "estimated_hot_scratch_bytes": hot_scratch_bytes,
            "root_probability_bytes": self.weights.nbytes,
            "hand_index_bytes": self.hand_ids.nbytes,
            "public_topology_bytes": sum(
                values.nbytes
                for values in (
                    self.node_players,
                    self.child_offsets,
                    self.children,
                    self.terminal_slots,
                )
            ),
            "terminal_value_bytes": self.terminal_values.nbytes,
        }

    def topology_summary(self) -> dict[str, int | bool]:
        return {
            "joint_deals": self.deal_count,
            "public_nodes": self.public_node_count,
            "strategic_public_nodes": self.strategic_node_count,
            "terminal_public_nodes": self.terminal_node_count,
            "information_sets": len(self._information_schema),
            "children_are_topological": all(
                child > parent
                for parent, node in enumerate(self.nodes)
                for child in node.children
            ),
            "numeric_tensors_are_float64_contiguous": (
                self.numeric_tensors_are_float64_contiguous()
            ),
        }
