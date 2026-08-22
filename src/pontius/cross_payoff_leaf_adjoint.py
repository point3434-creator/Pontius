"""Cross-payoff policy adjoints from the accepted leaf contraction primitive.

The ordinary CFR adjoint couples two roles: the omitted policy axis and the
seat whose terminal payoff is evaluated.  The contraction algebra does not
require that coupling.  Holding a payoff automaton fixed while omitting a
different acting player's policy produces every action coefficient of that
payoff with respect to the acting player's behavioral policy.

This module makes the decoupling explicit and guards the two semantics.  It is
an engineering feature extractor only; exact response certificates remain the
authority for selector stability, envelope admission, and emitted strategy.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

import numpy as np

from .device_fold_resident_leaf_adjoint_cfr import (
    device_fold_resident_leaf_adjoint_cfr_traverser,
)
from .game import Action, TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import LeafAdjointTraverserResult, leaf_adjoint_cfr_traverser
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointTraverserResult


def evaluate_cross_payoff_leaf_adjoint(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    acting_player: int,
    payoff_player: int,
    maximum_feature_width_per_batch: int = 96,
    terminal_batch_mode: str = "heterogeneous",
    cupy_sparse: Any | None = None,
) -> LeafAdjointTraverserResult:
    """Return all acting-player coefficients of one seat's profile payoff."""

    _validate_roles(layout, terminal_automata, acting_player, payoff_player)
    return leaf_adjoint_cfr_traverser(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        traverser=acting_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        terminal_batch_mode=terminal_batch_mode,
        cupy_sparse=cupy_sparse,
    )


def evaluate_device_fold_cross_payoff_leaf_adjoint(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    acting_player: int,
    payoff_player: int,
    belief_cache: Any,
    automaton_cache: Any,
    cupy_sparse: Any,
    maximum_feature_width_per_batch: int = 384,
    record_to_hand_backend: str = "gpu_cupy",
) -> ResidentLeafAdjointTraverserResult:
    """Run the cross-payoff adjoint through the accepted resident device fold.

    Resident automaton half-vectors depend on the payoff automata, while the
    fold target identifies the open policy axis.  ``replace`` changes only the
    latter metadata and shares every immutable device array.
    """

    _validate_roles(layout, terminal_automata, acting_player, payoff_player)
    if automaton_cache.target_seat != payoff_player:
        raise ValueError("cross-payoff automaton cache belongs to another payoff seat")
    open_axis_cache = replace(automaton_cache, target_seat=acting_player)
    return device_fold_resident_leaf_adjoint_cfr_traverser(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        traverser=acting_player,
        belief_cache=belief_cache,
        automaton_cache=open_axis_cache,
        cupy_sparse=cupy_sparse,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        record_to_hand_backend=record_to_hand_backend,
    )


def splice_fixed_response_probability_tape(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    response_actions: Mapping[str, Action],
    *,
    responding_player: int,
) -> PolicyProbabilityTape:
    """Replace exactly one player's policy by a deterministic response tape."""

    if (
        isinstance(responding_player, bool)
        or responding_player not in range(layout.num_players)
    ):
        raise ValueError("fixed response player is outside the layout")
    if len(source_probabilities) != layout.public_node_count:
        raise ValueError("fixed response probability tape differs from the tree")

    result = list(source_probabilities)
    for node_index, node in enumerate(layout.nodes):
        source = source_probabilities[node_index]
        if node.player == TERMINAL_PLAYER:
            if source is not None:
                raise ValueError("fixed response terminal has policy probabilities")
            continue
        if source is None:
            raise ValueError("fixed response strategic node has no probabilities")
        if node.player != responding_player:
            continue
        if source.shape != (len(node.information_keys), len(node.actions)):
            raise ValueError("fixed response node probability shape differs")
        deterministic = np.zeros_like(source, dtype=np.float64, order="C")
        for hand_index, key in enumerate(node.information_keys):
            try:
                selected = response_actions[key]
            except KeyError as exc:
                raise ValueError("fixed response action map is incomplete") from exc
            try:
                action_index = node.actions.index(selected)
            except ValueError as exc:
                raise ValueError("fixed response selected an unavailable action") from exc
            deterministic[hand_index, action_index] = 1.0
        deterministic.flags.writeable = False
        result[node_index] = deterministic
    return tuple(result)


def project_public_node_direction_slope(
    result: LeafAdjointTraverserResult | ResidentLeafAdjointTraverserResult,
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    endpoint_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    changed_public_node: int,
) -> float:
    """Project one exact one-node policy delta onto a cross-payoff adjoint."""

    if result.traverser != acting_player:
        raise ValueError("direction projection result belongs to another acting player")
    if changed_public_node not in range(layout.public_node_count):
        raise ValueError("direction projection node is outside the layout")
    if layout.nodes[changed_public_node].player != acting_player:
        raise ValueError("direction projection node belongs to another acting player")
    if len(source_probabilities) != len(endpoint_probabilities):
        raise ValueError("direction projection tapes have different lengths")
    changed = tuple(
        node_index
        for node_index, (source, endpoint) in enumerate(
            zip(source_probabilities, endpoint_probabilities, strict=True)
        )
        if source is not None
        and endpoint is not None
        and not np.array_equal(source, endpoint)
    )
    if changed != (changed_public_node,):
        raise ValueError("direction projection requires exactly the declared public node")
    source = source_probabilities[changed_public_node]
    endpoint = endpoint_probabilities[changed_public_node]
    if source is None or endpoint is None or source.shape != endpoint.shape:
        raise ValueError("direction projection probability arrays differ")
    delta = endpoint - source
    if not np.allclose(np.sum(delta, axis=1), 0.0, rtol=0.0, atol=1e-12):
        raise ValueError("direction projection rows do not preserve probability mass")
    try:
        read = next(row for row in result.reads if row.node_index == changed_public_node)
    except StopIteration as exc:
        raise ValueError("direction projection node is absent from the adjoint") from exc
    if read.action_numerators.shape != delta.shape:
        raise ValueError("direction projection action table differs from the policy row")
    return float(np.einsum("ha,ha->", delta, read.action_numerators, optimize=True))


def _validate_roles(
    layout: Any,
    terminal_automata: Mapping[str, Any],
    acting_player: int,
    payoff_player: int,
) -> None:
    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if isinstance(player, bool) or player not in range(layout.num_players):
            raise ValueError(f"cross-payoff {label} player is outside the layout")
    if not terminal_automata:
        raise ValueError("cross-payoff adjoint requires terminal automata")
    if any(automaton.target_player != payoff_player for automaton in terminal_automata.values()):
        raise ValueError("cross-payoff automata belong to another payoff player")
