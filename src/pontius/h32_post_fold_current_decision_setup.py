"""Post-fold current-decision setup for the sealed h32 convex engine."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Mapping

import numpy as np

from .continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
    _state_after_public_prefix,
)
from .cupy_sparse_incidence import CuPyBidirectionalIncidence
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_decision_aligned_posterior_manifest import (
    build_public_sequence_posterior,
    public_prefix_from_observations,
)
from .h32_post_fold_posterior_manifest import observed_bet_then_one_fold_sequence
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import information_schema_for_axes
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)
from .showdown_value_rank_screen import _rank_codes


def build_post_fold_current_decision_setup(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Reconstruct one pinned post-fold posterior and current-decision root."""

    board = parse_cards(*spec["board"])
    source, full, sparse, retained = _build_case(
        parsed=dict(parsed),
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=str(spec["range_family"]),
    )
    source_workspace, _, _ = retained
    source_row = next(
        row for row in source_parent["source_rows"] if row["source"] == spec["source"]
    )
    state = source_row["final_checkpoint"]
    full_blueprint = _average_policy_from_state(state)
    observations = observed_bet_then_one_fold_sequence(
        int(spec["observed_bettor"])
    )
    public_prefix = public_prefix_from_observations(observations)
    expected_prefix = tuple(
        (int(actor), str(action)) for actor, action in spec["public_prefix"]
    )
    if public_prefix != expected_prefix:
        raise ValueError("post-fold public prefix differs from sealed manifest")
    if int(spec["observed_responder"]) != public_prefix[-1][0]:
        raise ValueError("post-fold observed responder differs from prefix")
    if str(spec["observed_response"]) != public_prefix[-1][1]:
        raise ValueError("post-fold observed action differs from prefix")
    if str(spec["observed_response"]) != "fold":
        raise ValueError("post-fold setup received a non-fold observation")
    belief, _ = build_public_sequence_posterior(source, full_blueprint, observations)
    layout = ContinuationPublicTreeTensorEvaluator(
        full.game,
        public_prefix=public_prefix,
    )
    root_state = _state_after_public_prefix(full.game, full.deals[0], public_prefix)
    acting_player = int(spec["acting_player"])
    if root_state.current_player != acting_player:
        raise ValueError("post-fold setup actor is not current at the root")
    if root_state.legal_actions() != ("fold", "call"):
        raise ValueError("post-fold setup root is not a call-fold decision")
    if len(root_state.pending_responders) != 4:
        raise ValueError("post-fold setup lost downstream response geometry")

    schema = information_schema_for_axes(layout, belief.hands_by_player)
    blueprint = {key: dict(full_blueprint[key]) for key in schema}
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        layout,
        codes,
        pot=float(parsed["pot"]),
        bet_size=float(parsed["bet_size"]),
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=int(parsed["query_chunk_records"]),
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        source_policy=blueprint,
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    return {
        "board": board,
        "source": source,
        "full": full,
        "layout": layout,
        "sparse": sparse,
        "source_workspace": source_workspace,
        "state": state,
        "full_blueprint": full_blueprint,
        "blueprint": blueprint,
        "belief": belief,
        "automata": automata,
        "base": base,
        "workspace": workspace,
        "gpu": gpu,
        "shared": shared,
        "context": context,
    }


@contextmanager
def post_fold_core_setup_adapter() -> Iterator[None]:
    """Temporarily route the sealed core through the post-fold setup."""

    from . import h32_fresh_convex_retreat_replication as core
    from .h32_continuation_root_ledger import _setup as historical_setup

    if core._setup is not historical_setup:
        raise RuntimeError("sealed convex core setup was already replaced")
    core._setup = build_post_fold_current_decision_setup
    try:
        yield
    finally:
        core._setup = historical_setup
