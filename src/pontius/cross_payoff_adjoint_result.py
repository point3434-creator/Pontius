"""Typed acting/payoff roles for cross-payoff adjoint traversals."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Generic, Protocol, TypeVar

import numpy as np

from . import cross_payoff_leaf_adjoint as _legacy_cross_payoff
from . import multi_size_affine_cross_payoff as _legacy_sized_cross_payoff
from .device_fold_resident_leaf_adjoint_cfr_v2 import (
    device_fold_resident_leaf_adjoint_cfr_traverser_v2,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import LeafAdjointTraverserResult
from .multi_size_leaf_adjoint import multi_size_leaf_adjoint_cfr_traverser
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointTraverserResult
from .resident_record_to_hand_fold_v2 import ResidentReachTolerances


class TraverserReadResult(Protocol):
    """Minimum raw traverser surface retained by the semantic wrapper."""

    traverser: int
    reads: tuple[Any, ...]


TraverserResultT = TypeVar("TraverserResultT", bound=TraverserReadResult)


@dataclass(frozen=True, slots=True)
class CrossPayoffContextIdentity:
    """Exact in-process and durable identity of an adjoint evaluation context."""

    layout_object_id: int
    num_players: int
    public_node_count: int
    topology_sha256: str
    action_schema_sha256: str
    layout_numeric_sha256: str
    game_structural_sha256: str
    game_provenance_sha256: str
    source_probability_sha256: str


_RESULT_FACTORY_TOKEN = object()


def _layout_numeric_digest(layout: Any) -> str:
    records = []
    for name in (
        "weights",
        "hand_ids",
        "node_players",
        "child_offsets",
        "children",
        "terminal_slots",
        "terminal_values",
    ):
        values = getattr(layout, name, None)
        if not isinstance(values, np.ndarray) or not values.flags.c_contiguous:
            raise ValueError(f"cross-payoff layout array {name} is unavailable")
        records.append(
            {
                "name": name,
                "dtype": values.dtype.str,
                "shape": list(values.shape),
                "bytes": values.tobytes(order="C").hex(),
            }
        )
    rendered = json.dumps(
        {"schema": "pontius-public-layout-numeric-v1", "arrays": records},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(rendered).hexdigest()


def _derive_context_identity(
    layout: Any,
    probabilities: PolicyProbabilityTape,
) -> CrossPayoffContextIdentity:
    """Derive context identity from live objects; callers cannot supply fields."""

    # Import lazily so the historical cache can remain an independent module
    # while both successors share its exact canonical digest definitions.
    from .pre_bet_initial_row_cache import (
        action_schema_digest,
        layout_topology_digest,
        probability_tape_digest,
    )

    structural = getattr(getattr(layout, "game", None), "structural_digest", None)
    provenance = getattr(getattr(layout, "game", None), "provenance_digest", None)
    for label, digest in (("structural", structural), ("provenance", provenance)):
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or digest != digest.lower()
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"cross-payoff layout lacks exact {label} provenance")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("cross-payoff probability tape differs from the layout")
    return CrossPayoffContextIdentity(
        layout_object_id=id(layout),
        num_players=int(layout.num_players),
        public_node_count=int(layout.public_node_count),
        topology_sha256=layout_topology_digest(layout),
        action_schema_sha256=action_schema_digest(layout),
        layout_numeric_sha256=_layout_numeric_digest(layout),
        game_structural_sha256=structural,
        game_provenance_sha256=provenance,
        source_probability_sha256=probability_tape_digest(probabilities),
    )


@dataclass(frozen=True, slots=True, init=False)
class CrossPayoffAdjointResult(Generic[TraverserResultT]):
    """One acting-policy adjoint of one explicitly identified payoff seat.

    The raw leaf-adjoint traversers historically carried only the omitted
    policy role (``traverser``).  This wrapper is the boundary at which a
    validated terminal-automaton payoff role becomes durable metadata.
    Numerical arrays and telemetry remain owned by the raw result.
    """

    acting_player: int
    payoff_player: int
    raw_result: TraverserResultT
    context_identity: CrossPayoffContextIdentity

    def __init__(
        self,
        *,
        acting_player: int,
        payoff_player: int,
        raw_result: TraverserResultT,
        context_identity: CrossPayoffContextIdentity | None = None,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _RESULT_FACTORY_TOKEN:
            raise TypeError(
                "cross-payoff results are factory-only; use a typed evaluator or "
                "bind_cross_payoff_adjoint_result"
            )
        for label, player in (
            ("acting", acting_player),
            ("payoff", payoff_player),
        ):
            if isinstance(player, bool) or not isinstance(player, int) or player < 0:
                raise ValueError(f"cross-payoff result has an invalid {label} player")
        if raw_result.traverser != acting_player:
            raise ValueError("cross-payoff raw result belongs to another acting player")
        raw_payoff = getattr(raw_result, "payoff_player", payoff_player)
        if raw_payoff != payoff_player:
            raise ValueError("cross-payoff raw result belongs to another payoff player")
        if type(context_identity) is not CrossPayoffContextIdentity:
            raise TypeError("cross-payoff result requires a derived context identity")
        if (
            acting_player not in range(context_identity.num_players)
            or payoff_player not in range(context_identity.num_players)
        ):
            raise ValueError("cross-payoff roles are outside the bound context")
        object.__setattr__(self, "acting_player", acting_player)
        object.__setattr__(self, "payoff_player", payoff_player)
        object.__setattr__(self, "raw_result", raw_result)
        object.__setattr__(self, "context_identity", context_identity)

    @property
    def traverser(self) -> int:
        """Compatibility spelling for the explicitly typed acting role."""

        return self.acting_player

    @property
    def reads(self) -> tuple[Any, ...]:
        return self.raw_result.reads

    def __getattr__(self, name: str) -> Any:
        """Delegate unchanged traversal telemetry to the underlying result."""

        return getattr(self.raw_result, name)


def bind_cross_payoff_adjoint_result(
    layout: Any,
    probabilities: PolicyProbabilityTape,
    raw_result: TraverserResultT,
    *,
    acting_player: int,
    payoff_player: int,
) -> CrossPayoffAdjointResult[TraverserResultT]:
    """Bind an independently obtained raw result to its exact live context."""

    return CrossPayoffAdjointResult(
        acting_player=acting_player,
        payoff_player=payoff_player,
        raw_result=raw_result,
        context_identity=_derive_context_identity(layout, probabilities),
        _factory_token=_RESULT_FACTORY_TOKEN,
    )


def evaluate_typed_cross_payoff_leaf_adjoint(
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
) -> CrossPayoffAdjointResult[LeafAdjointTraverserResult]:
    """Typed successor to the legacy one-size CPU cross-payoff evaluator."""

    terminal_payoff_player = _terminal_payoff_player(
        layout,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        context="cross-payoff",
    )
    raw_result = _legacy_cross_payoff.evaluate_cross_payoff_leaf_adjoint(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        terminal_batch_mode=terminal_batch_mode,
        cupy_sparse=cupy_sparse,
    )
    return bind_cross_payoff_adjoint_result(
        layout,
        probabilities,
        raw_result,
        acting_player=acting_player,
        payoff_player=terminal_payoff_player,
    )


def evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    acting_player: int,
    payoff_player: int,
    maximum_feature_width_per_batch: int = 96,
    zero_reach_value: float = 0.0,
    cupy_sparse: Any | None = None,
) -> CrossPayoffAdjointResult[LeafAdjointTraverserResult]:
    """Typed CPU cross-payoff evaluator for the sized public tree."""

    terminal_payoff_player = _terminal_payoff_player(
        layout,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        context="sized cross-payoff",
    )
    raw_result = multi_size_leaf_adjoint_cfr_traverser(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        traverser=acting_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        zero_reach_value=zero_reach_value,
        cupy_sparse=cupy_sparse,
    )
    return bind_cross_payoff_adjoint_result(
        layout,
        probabilities,
        raw_result,
        acting_player=acting_player,
        payoff_player=terminal_payoff_player,
    )


def evaluate_typed_device_fold_cross_payoff_leaf_adjoint(
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
    reach_tolerances: ResidentReachTolerances,
    maximum_feature_width_per_batch: int = 384,
    record_to_hand_backend: str = "gpu_cupy",
) -> CrossPayoffAdjointResult[ResidentLeafAdjointTraverserResult]:
    """Typed successor to the accepted resident device-fold extractor."""

    terminal_payoff_player = _terminal_payoff_player(
        layout,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        context="device-fold cross-payoff",
    )
    if automaton_cache.target_seat != terminal_payoff_player:
        raise ValueError(
            "device-fold cross-payoff cache belongs to another payoff player"
        )
    open_axis_cache = replace(automaton_cache, target_seat=acting_player)
    raw_result = device_fold_resident_leaf_adjoint_cfr_traverser_v2(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        traverser=acting_player,
        belief_cache=belief_cache,
        automaton_cache=open_axis_cache,
        cupy_sparse=cupy_sparse,
        reach_tolerances=reach_tolerances,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        record_to_hand_backend=record_to_hand_backend,
    )
    return bind_cross_payoff_adjoint_result(
        layout,
        probabilities,
        raw_result,
        acting_player=acting_player,
        payoff_player=terminal_payoff_player,
    )


def evaluate_typed_multi_size_affine_cross_payoff(
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
) -> CrossPayoffAdjointResult[ResidentLeafAdjointTraverserResult]:
    """Typed successor to the sized affine-resident cross-payoff extractor."""

    terminal_payoff_player = _terminal_payoff_player(
        layout,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        context="sized affine cross-payoff",
    )
    if automaton_cache.target_seat != terminal_payoff_player:
        raise ValueError(
            "sized affine cross-payoff cache has the wrong payoff role"
        )
    raw_result = _legacy_sized_cross_payoff.evaluate_multi_size_affine_cross_payoff(
        layout,
        workspace,
        sparse,
        probabilities,
        terminal_automata,
        acting_player=acting_player,
        payoff_player=payoff_player,
        belief_cache=belief_cache,
        automaton_cache=automaton_cache,
        cupy_sparse=cupy_sparse,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
    )
    return bind_cross_payoff_adjoint_result(
        layout,
        probabilities,
        raw_result,
        acting_player=acting_player,
        payoff_player=terminal_payoff_player,
    )


def _terminal_payoff_player(
    layout: Any,
    terminal_automata: Mapping[str, Any],
    *,
    acting_player: int,
    payoff_player: int,
    context: str,
) -> int:
    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if isinstance(player, bool) or player not in range(layout.num_players):
            raise ValueError(f"{context} {label} player is outside the layout")
    if not terminal_automata:
        raise ValueError(f"{context} requires terminal automata")
    terminal_payoff_players = {
        automaton.target_player for automaton in terminal_automata.values()
    }
    if terminal_payoff_players != {payoff_player}:
        raise ValueError(f"{context} automata belong to another payoff player")
    return next(iter(terminal_payoff_players))
