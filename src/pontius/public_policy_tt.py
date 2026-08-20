"""Compile a fixed multiway river public policy into one root tensor train."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .evaluation import Policy, policy_distribution
from .factorized_belief import FactorizedCardBelief
from .game import TERMINAL_PLAYER
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards, _format_hole
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from .showdown_value_rank_screen import _terminal_groups
from .tensor_train import TensorTrain
from .tensor_train_algebra import (
    multiply_mode_vector,
    round_tensor_train,
    sum_tensor_trains,
)


@dataclass(frozen=True, slots=True)
class PublicPolicyTTComposition:
    """One root TT plus per-node rank/rounding diagnostics."""

    root: TensorTrain
    public_nodes: int
    terminal_nodes: int
    strategic_rounds: int
    maximum_raw_rank: int
    maximum_output_rank: int
    maximum_relative_discarded_bound: float
    sum_relative_discarded_bounds: float


def representative_public_tree(
    belief: FactorizedCardBelief,
    *,
    pot: float,
    stack: float,
    bet_size: float,
) -> PublicTreeTensorEvaluator:
    """Build the range-independent public topology from one compatible deal."""

    assignment = _first_compatible_assignment(belief)
    deal = MultiwayRiverDeal(
        tuple(
            belief.hands_by_player[player][assignment[player]]
            for player in range(belief.num_players)
        )
    )
    game = MultiwayRiverHoldem.from_joint_weights(
        board=belief.board,
        pot=pot,
        stacks=(stack,) * belief.num_players,
        bet_size=bet_size,
        joint_weights={deal: 1.0},
    )
    return PublicTreeTensorEvaluator(game)


def information_schema_for_axes(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> dict[str, tuple[str, ...]]:
    """Return the exact information keys/actions for every supplied hand axis."""

    if len(hands_by_player) != layout.num_players:
        raise ValueError("public-policy axes require one hand axis per player")
    schema: dict[str, tuple[str, ...]] = {}
    for node in layout.nodes:
        if node.player == TERMINAL_PLAYER:
            continue
        for hand in hands_by_player[node.player]:
            key = _information_key(layout, node.player, hand, node.history)
            previous = schema.setdefault(key, node.actions)
            if previous != node.actions:
                raise ValueError("public-policy information schema is inconsistent")
    return dict(sorted(schema.items()))


def dense_public_policy_root(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
    terminal_operators: dict[str, np.ndarray],
) -> np.ndarray:
    """Recursively evaluate a full Cartesian root operator as an exact oracle."""

    probabilities = _hand_policy_probabilities(layout, hands_by_player, policy)
    terminal_keys = _terminal_keys_by_slot(layout)
    shape = tuple(len(hands) for hands in hands_by_player)
    if set(terminal_operators) != set(terminal_keys):
        raise ValueError("dense terminal operators do not match public payoff groups")
    for values in terminal_operators.values():
        if values.shape != shape or not np.all(np.isfinite(values)):
            raise ValueError("dense terminal operator shape or values are invalid")

    def evaluate(node_index: int) -> np.ndarray:
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            return terminal_operators[terminal_keys[node.terminal_slot]]
        node_probabilities = probabilities[node_index]
        assert node_probabilities is not None
        result = np.zeros(shape, dtype=np.float64, order="C")
        broadcast_shape = [1] * layout.num_players
        broadcast_shape[node.player] = len(hands_by_player[node.player])
        for action_index, child in enumerate(node.children):
            child_values = evaluate(child)
            result += child_values * node_probabilities[:, action_index].reshape(
                broadcast_shape
            )
        return result

    return evaluate(0)


def compose_public_policy_root_tt(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
    terminal_trains: dict[str, TensorTrain],
    *,
    relative_tolerance: float,
    maximum_rank: int | None,
) -> PublicPolicyTTComposition:
    """Apply policy unaries, exact branch sums, and per-node TT rounding."""

    probabilities = _hand_policy_probabilities(layout, hands_by_player, policy)
    terminal_keys = _terminal_keys_by_slot(layout)
    shape = tuple(len(hands) for hands in hands_by_player)
    if set(terminal_trains) != set(terminal_keys):
        raise ValueError("terminal trains do not match public payoff groups")
    if any(train.shape != shape for train in terminal_trains.values()):
        raise ValueError("terminal train modes do not match public-policy axes")

    maximum_raw_rank = 1
    maximum_output_rank = 1
    maximum_discarded = 0.0
    sum_discarded = 0.0
    strategic_rounds = 0

    def evaluate(node_index: int) -> TensorTrain:
        nonlocal maximum_raw_rank
        nonlocal maximum_output_rank
        nonlocal maximum_discarded
        nonlocal sum_discarded
        nonlocal strategic_rounds
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            return terminal_trains[terminal_keys[node.terminal_slot]]
        node_probabilities = probabilities[node_index]
        assert node_probabilities is not None
        weighted_children = tuple(
            multiply_mode_vector(
                evaluate(child),
                node.player,
                node_probabilities[:, action_index],
            )
            for action_index, child in enumerate(node.children)
        )
        raw = sum_tensor_trains(weighted_children)
        maximum_raw_rank = max(maximum_raw_rank, *raw.ranks)
        rounded = round_tensor_train(
            raw,
            relative_tolerance=relative_tolerance,
            maximum_rank=maximum_rank,
        )
        strategic_rounds += 1
        maximum_output_rank = max(maximum_output_rank, *rounded.output_ranks)
        maximum_discarded = max(
            maximum_discarded,
            rounded.relative_discarded_bound,
        )
        sum_discarded += rounded.relative_discarded_bound
        return rounded.train

    root = evaluate(0)
    return PublicPolicyTTComposition(
        root=root,
        public_nodes=layout.public_node_count,
        terminal_nodes=layout.terminal_node_count,
        strategic_rounds=strategic_rounds,
        maximum_raw_rank=maximum_raw_rank,
        maximum_output_rank=maximum_output_rank,
        maximum_relative_discarded_bound=maximum_discarded,
        sum_relative_discarded_bounds=sum_discarded,
    )


def _first_compatible_assignment(
    belief: FactorizedCardBelief,
) -> tuple[int, ...]:
    selected = [0] * belief.num_players

    def walk(player: int, used_mask: int) -> tuple[int, ...] | None:
        if player == belief.num_players:
            return tuple(selected)
        for hand_index, supplied_mask in enumerate(belief.hand_masks[player]):
            mask = int(supplied_mask)
            if used_mask & mask:
                continue
            selected[player] = hand_index
            result = walk(player + 1, used_mask | mask)
            if result is not None:
                return result
        return None

    result = walk(0, 0)
    if result is None:
        raise ValueError("public-policy axes contain no compatible joint assignment")
    return result


def _history_text(history: tuple[tuple[int, str], ...]) -> str:
    if not history:
        return "root"
    return "/".join(f"p{seat}:{action}" for seat, action in history)


def _information_key(
    layout: PublicTreeTensorEvaluator,
    player: int,
    hand: HoleCards,
    history: tuple[tuple[int, str], ...],
) -> str:
    return (
        f"river-multiway|structure={layout.game.structural_digest}|p{player}|"
        f"hand={_format_hole(hand)}|history={_history_text(history)}"
    )


def _hand_policy_probabilities(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
) -> tuple[np.ndarray | None, ...]:
    if len(hands_by_player) != layout.num_players:
        raise ValueError("public-policy axes require one hand axis per player")
    probabilities: list[np.ndarray | None] = []
    for node in layout.nodes:
        if node.player == TERMINAL_PLAYER:
            probabilities.append(None)
            continue
        values = np.empty(
            (len(hands_by_player[node.player]), len(node.actions)),
            dtype=np.float64,
            order="C",
        )
        for hand_index, hand in enumerate(hands_by_player[node.player]):
            key = _information_key(layout, node.player, hand, node.history)
            distribution = policy_distribution(policy, key, node.actions)
            values[hand_index] = tuple(
                distribution[action] for action in node.actions
            )
        probabilities.append(values)
    return tuple(probabilities)


def _terminal_keys_by_slot(
    layout: PublicTreeTensorEvaluator,
) -> tuple[str, ...]:
    result: list[str | None] = [None] * layout.terminal_node_count
    for group in _terminal_groups(layout):
        for slot in group.terminal_slots:
            if result[slot] is not None:
                raise AssertionError("terminal slot belongs to multiple payoff groups")
            result[slot] = group.key
    if any(key is None for key in result):
        raise AssertionError("one terminal slot has no payoff group")
    return tuple(key for key in result if key is not None)
