"""Bridge exact open-mode factor-TT reads to quotient-CFR action tables.

At an information set, CFR needs one counterfactual reach vector and one value
numerator per legal action and private hand.  Public reach above the node is a
product of unary action probabilities with the traverser's own actions omitted;
the cached child TT contains the complete continuation below the chosen action.
The open-mode contraction therefore produces the literal CFR table without a
joint-deal axis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .game import Action, TERMINAL_PLAYER
from .incremental_policy_tt import PolicyDeltaTTCache, PolicyProbabilityTape
from .open_mode_factor_tt import (
    OpenModeFactorTTBatchContraction,
    OpenModeFactorTTWorkspace,
    contract_open_mode_batch,
)
from .public_tree_tensor import PublicTreeTensorEvaluator

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]


@dataclass(frozen=True, slots=True)
class CFRActionComparison:
    """One exact per-hand action table in quotient-CFR units."""

    node_index: int
    target_seat: int
    actions: tuple[Action, ...]
    counterfactual_reaches: FloatArray
    action_numerators: FloatArray
    conditional_action_values: FloatArray
    positive_reach: NDArray[np.bool_]
    selected_action_indices: IntArray
    policy_values: FloatArray
    regret_deltas: FloatArray
    zero_reach_hands: int


@dataclass(frozen=True, slots=True)
class OpenModeCFRActionRead:
    """One CFR action table plus the shared child-contraction bill."""

    comparison: CFRActionComparison
    mode_factors: tuple[FloatArray, ...]
    contraction: OpenModeFactorTTBatchContraction


def counterfactual_mode_factors(
    cache: PolicyDeltaTTCache,
    *,
    node_index: int,
    traverser: int,
) -> tuple[FloatArray, ...]:
    """Return public reach above ``node_index`` with traverser actions omitted."""

    layout = cache.layout
    if isinstance(node_index, bool) or node_index not in range(layout.public_node_count):
        raise ValueError("counterfactual node is outside the public tree")
    if isinstance(traverser, bool) or traverser not in range(layout.num_players):
        raise ValueError("counterfactual traverser is outside the player seats")
    factors = [
        np.ones(len(hands), dtype=np.float64) for hands in cache.hands_by_player
    ]
    child = node_index
    while int(cache.parents[child]) >= 0:
        parent = int(cache.parents[child])
        parent_node = layout.nodes[parent]
        if parent_node.player == TERMINAL_PLAYER:
            raise AssertionError("terminal public node cannot be an ancestor")
        try:
            action_index = parent_node.children.index(child)
        except ValueError as error:
            raise AssertionError("public parent does not contain its declared child") from error
        if parent_node.player != traverser:
            probabilities = cache.probabilities[parent]
            if probabilities is None:
                raise AssertionError("strategic ancestor has no policy probabilities")
            factors[parent_node.player] *= probabilities[:, action_index]
        child = parent
    result = tuple(np.ascontiguousarray(values, dtype=np.float64) for values in factors)
    for values in result:
        values.flags.writeable = False
    return result


def open_mode_cfr_action_read(
    workspace: OpenModeFactorTTWorkspace,
    cache: PolicyDeltaTTCache,
    *,
    node_index: int,
    maximum_feature_width_per_batch: int,
    zero_reach_action_index: int = 0,
    zero_reach_value: float = 0.0,
) -> OpenModeCFRActionRead:
    """Build the exact child-action table for one acting public node.

    Zero-reach hands are handled semantically: every regret delta is exactly
    zero and action comparison selects the declared legal fallback (the first
    action by default), independent of floating-point residue.
    """

    layout = cache.layout
    if isinstance(node_index, bool) or node_index not in range(layout.public_node_count):
        raise ValueError("CFR action node is outside the public tree")
    node = layout.nodes[node_index]
    if node.player == TERMINAL_PLAYER:
        raise ValueError("CFR action comparison requires a strategic node")
    if tuple(len(hands) for hands in cache.hands_by_player) != (
        workspace.topology.base.hand_counts
    ):
        raise ValueError("CFR cache hand axes differ from open-mode topology")
    for hands, masks in zip(
        cache.hands_by_player,
        workspace.topology.base.axis_masks,
        strict=True,
    ):
        supplied = np.ascontiguousarray(
            [(1 << hand[0]) | (1 << hand[1]) for hand in hands],
            dtype=np.uint64,
        )
        if not np.array_equal(supplied, masks):
            raise ValueError("CFR cache hand axes differ from open-mode topology")
    if (
        isinstance(zero_reach_action_index, bool)
        or zero_reach_action_index not in range(len(node.actions))
    ):
        raise ValueError("zero-reach action fallback is outside the legal actions")

    target = node.player
    factors = counterfactual_mode_factors(
        cache,
        node_index=node_index,
        traverser=target,
    )
    contraction = contract_open_mode_batch(
        workspace,
        tuple(cache.node_trains[child] for child in node.children),
        target_seats=(target,),
        mode_factors=factors,
        zero_reach_value=zero_reach_value,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    child_values = tuple(
        train_result.for_seat(target) for train_result in contraction.trains
    )
    reaches = child_values[0].root_normalized_reaches
    if any(
        not np.array_equal(values.root_normalized_reaches, reaches)
        for values in child_values[1:]
    ):
        raise AssertionError("batched CFR children produced different reach vectors")
    action_numerators = np.ascontiguousarray(
        np.column_stack(
            tuple(values.root_normalized_numerators for values in child_values)
        ),
        dtype=np.float64,
    )
    conditional = np.ascontiguousarray(
        np.column_stack(tuple(values.conditional_values for values in child_values)),
        dtype=np.float64,
    )
    positive = np.ascontiguousarray(reaches > 0.0, dtype=np.bool_)
    selected = np.argmax(action_numerators, axis=1).astype(np.int32, copy=False)
    selected[~positive] = zero_reach_action_index
    probabilities = cache.probabilities[node_index]
    if probabilities is None:
        raise AssertionError("strategic CFR node has no policy probabilities")
    policy_values = np.einsum(
        "ha,ha->h",
        probabilities,
        action_numerators,
        optimize=True,
    )
    regret_deltas = action_numerators - policy_values[:, None]
    regret_deltas[~positive] = 0.0
    comparison = CFRActionComparison(
        node_index=node_index,
        target_seat=target,
        actions=node.actions,
        counterfactual_reaches=_readonly(reaches, np.float64),
        action_numerators=_readonly(action_numerators, np.float64),
        conditional_action_values=_readonly(conditional, np.float64),
        positive_reach=_readonly(positive, np.bool_),
        selected_action_indices=_readonly(selected, np.int32),
        policy_values=_readonly(policy_values, np.float64),
        regret_deltas=_readonly(regret_deltas, np.float64),
        zero_reach_hands=int(np.count_nonzero(~positive)),
    )
    return OpenModeCFRActionRead(
        comparison=comparison,
        mode_factors=factors,
        contraction=contraction,
    )


def dense_cfr_action_comparisons(
    layout: PublicTreeTensorEvaluator,
    probabilities: PolicyProbabilityTape,
    *,
    traverser: int,
    zero_reach_action_index: int = 0,
    zero_reach_value: float = 0.0,
) -> tuple[CFRActionComparison, ...]:
    """Literal deal-axis oracle for the internals of one quotient-CFR traversal."""

    if isinstance(traverser, bool) or traverser not in range(layout.num_players):
        raise ValueError("dense CFR traverser is outside the player seats")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("dense CFR probability tape differs from the public tree")
    counterfactual = np.empty(
        (layout.public_node_count, layout.deal_count),
        dtype=np.float64,
        order="C",
    )
    counterfactual[0] = layout.weights
    for node_index, node in enumerate(layout.nodes):
        if node.player == TERMINAL_PLAYER:
            continue
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise ValueError("dense CFR strategic probability entry is absent")
        actor_hand_ids = layout.hand_ids[:, node.player]
        if node.player == traverser:
            for child in node.children:
                counterfactual[child] = counterfactual[node_index]
        else:
            for action_index, child in enumerate(node.children):
                counterfactual[child] = (
                    counterfactual[node_index]
                    * node_probabilities[actor_hand_ids, action_index]
                )

    continuation = np.empty(
        (layout.public_node_count, layout.deal_count),
        dtype=np.float64,
        order="C",
    )
    comparisons = []
    target_hand_ids = layout.hand_ids[:, traverser]
    hand_count = len(layout.hands_by_player[traverser])
    for node_index in range(layout.public_node_count - 1, -1, -1):
        node = layout.nodes[node_index]
        if node.player == TERMINAL_PLAYER:
            continuation[node_index] = layout.terminal_values[
                node.terminal_slot, :, traverser
            ]
            continue
        node_probabilities = probabilities[node_index]
        if node_probabilities is None:
            raise ValueError("dense CFR strategic probability entry is absent")
        actor_hand_ids = layout.hand_ids[:, node.player]
        continuation[node_index].fill(0.0)
        for action_index, child in enumerate(node.children):
            continuation[node_index] += (
                node_probabilities[actor_hand_ids, action_index]
                * continuation[child]
            )
        if node.player != traverser:
            continue
        if (
            isinstance(zero_reach_action_index, bool)
            or zero_reach_action_index not in range(len(node.actions))
        ):
            raise ValueError("zero-reach action fallback is outside the legal actions")
        reaches = np.bincount(
            target_hand_ids,
            weights=counterfactual[node_index],
            minlength=hand_count,
        )
        action_numerators = np.empty(
            (hand_count, len(node.actions)), dtype=np.float64, order="C"
        )
        for action_index, child in enumerate(node.children):
            action_numerators[:, action_index] = np.bincount(
                target_hand_ids,
                weights=counterfactual[node_index] * continuation[child],
                minlength=hand_count,
            )
        positive = reaches > 0.0
        conditional = np.full_like(action_numerators, zero_reach_value)
        np.divide(
            action_numerators,
            reaches[:, None],
            out=conditional,
            where=positive[:, None],
        )
        selected = np.argmax(action_numerators, axis=1).astype(np.int32, copy=False)
        selected[~positive] = zero_reach_action_index
        own_probabilities = probabilities[node_index]
        if own_probabilities is None:
            raise AssertionError("traverser node has no policy probabilities")
        policy_values = np.einsum(
            "ha,ha->h", own_probabilities, action_numerators, optimize=True
        )
        regret_deltas = action_numerators - policy_values[:, None]
        regret_deltas[~positive] = 0.0
        comparisons.append(
            CFRActionComparison(
                node_index=node_index,
                target_seat=traverser,
                actions=node.actions,
                counterfactual_reaches=_readonly(reaches, np.float64),
                action_numerators=_readonly(action_numerators, np.float64),
                conditional_action_values=_readonly(conditional, np.float64),
                positive_reach=_readonly(positive, np.bool_),
                selected_action_indices=_readonly(selected, np.int32),
                policy_values=_readonly(policy_values, np.float64),
                regret_deltas=_readonly(regret_deltas, np.float64),
                zero_reach_hands=int(np.count_nonzero(~positive)),
            )
        )
    return tuple(sorted(comparisons, key=lambda row: row.node_index))


def _readonly(values: object, dtype: object) -> NDArray[np.generic]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result
