"""Exact public-tree evaluation with caller-supplied terminal deal tensors."""

from __future__ import annotations

from math import fsum

import numpy as np

from .evaluation import EvaluationResult, Policy
from .game import Action, TERMINAL_PLAYER
from .public_tree_tensor import (
    FloatArray,
    PublicTreeTensorEvaluator,
    PublicTreeTensorResult,
)


def evaluate_with_terminal_values(
    layout: PublicTreeTensorEvaluator,
    policy: Policy,
    terminal_values: object,
) -> PublicTreeTensorResult:
    """Use ``layout`` semantics with an exact-shape alternative terminal tensor."""

    supplied = np.ascontiguousarray(terminal_values, dtype=np.float64)
    expected_shape = (
        layout.terminal_node_count,
        layout.deal_count,
        layout.num_players,
    )
    if supplied.shape != expected_shape:
        raise ValueError(
            f"terminal tensor shape {supplied.shape!r} != {expected_shape!r}"
        )
    if not np.all(np.isfinite(supplied)):
        raise ValueError("terminal tensor values must be finite")
    probabilities = layout._prepare_policy(policy)

    node_values = np.empty(
        (layout.public_node_count, layout.deal_count, layout.num_players),
        dtype=np.float64,
        order="C",
    )
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            node_values[node_index] = supplied[node.terminal_slot]
            continue
        node_probabilities = probabilities[node_index]
        assert node_probabilities is not None
        node_values[node_index].fill(0.0)
        for action_index, child in enumerate(node.children):
            node_values[node_index] += (
                node_probabilities[:, action_index, None] * node_values[child]
            )
    utilities = tuple(float(value) for value in layout.weights @ node_values[0])

    responses = tuple(
        _best_response_with_terminal_values(
            layout,
            probabilities,
            supplied,
            player,
        )
        for player in range(layout.num_players)
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
    return PublicTreeTensorResult(
        evaluation=EvaluationResult(
            utilities=utilities,
            best_response_values=best_response_values,
            deviation_gains=deviation_gains,
            nash_conv=nash_conv,
            exploitability=nash_conv / 2.0 if layout.num_players == 2 else None,
        ),
        best_response_actions=tuple(actions for _, actions in responses),
    )


def _best_response_with_terminal_values(
    layout: PublicTreeTensorEvaluator,
    probabilities: tuple[FloatArray | None, ...],
    terminal_values: FloatArray,
    target_player: int,
) -> tuple[float, dict[str, Action]]:
    counterfactual_reach = np.zeros(
        (layout.public_node_count, layout.deal_count),
        dtype=np.float64,
        order="C",
    )
    counterfactual_reach[0] = layout.weights
    for node_index, node in enumerate(layout.nodes):
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
        (layout.public_node_count, layout.deal_count),
        dtype=np.float64,
        order="C",
    )
    selected_actions: dict[str, Action] = {}
    deal_indices = np.arange(layout.deal_count)
    target_hand_ids = layout.hand_ids[:, target_player]
    target_hand_count = len(layout.hands_by_player[target_player])
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continuation[node_index] = terminal_values[
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
                weights=(counterfactual_reach[node_index] * continuation[child]),
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

    return float(layout.weights @ continuation[0]), selected_actions
