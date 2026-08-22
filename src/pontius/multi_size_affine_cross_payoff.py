"""Cross-payoff open-axis reads through canonical sized resident caches."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .affine_resident_heterogeneous_leaf_contraction import (
    CuPyAffineResidentAutomatonCache,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .multi_size_affine_resident_leaf_adjoint_cfr import (
    multi_size_affine_resident_leaf_adjoint_cfr_traverser,
)
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .resident_heterogeneous_leaf_contraction import CuPyResidentBeliefCache
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointTraverserResult
from .structured_showdown_automaton import StructuredShowdownAutomaton


def evaluate_multi_size_affine_cross_payoff(
    layout: MultiSizePublicTreeTensorEvaluator,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, StructuredShowdownAutomaton],
    *,
    acting_player: int,
    payoff_player: int,
    belief_cache: CuPyResidentBeliefCache,
    automaton_cache: CuPyAffineResidentAutomatonCache,
    cupy_sparse: Any,
    maximum_feature_width_per_batch: int = 384,
) -> ResidentLeafAdjointTraverserResult:
    """Return acting-seat coefficients of one sized fixed-response payoff."""

    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if isinstance(player, bool) or player not in range(layout.num_players):
            raise ValueError(f"sized cross-payoff {label} player is outside the layout")
    if not terminal_automata:
        raise ValueError("sized cross-payoff requires terminal automata")
    if any(
        automaton.target_player != payoff_player
        for automaton in terminal_automata.values()
    ):
        raise ValueError("sized cross-payoff automata have the wrong payoff role")
    if automaton_cache.target_seat != payoff_player:
        raise ValueError("sized cross-payoff cache has the wrong payoff role")
    open_axis_cache = replace(automaton_cache, target_seat=acting_player)
    return multi_size_affine_resident_leaf_adjoint_cfr_traverser(
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
    )
