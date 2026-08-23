"""Provenance-bound exact affine payoff rows for one root public decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .cross_payoff_adjoint_result import (
    CrossPayoffAdjointResult,
    CrossPayoffContextIdentity,
    _derive_context_identity,
)
from .dense_root_cross_payoff_control import dense_root_cross_payoff_control
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape
from .sequence_form_open_axis import OpenAxisNodeCoefficients, SequenceFormAffineRow

SOURCE_IDENTITY_ATOL = 2e-11
_CONTEXT_FACTORY_TOKEN = object()


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def _snapshot_probability_tape(
    layout: Any,
    probabilities: PolicyProbabilityTape,
) -> PolicyProbabilityTape:
    if len(probabilities) != layout.public_node_count:
        raise ValueError("public-node source tape differs from the layout")
    result: list[np.ndarray | None] = []
    for node, supplied in zip(layout.nodes, probabilities, strict=True):
        if node.player == TERMINAL_PLAYER:
            if supplied is not None:
                raise ValueError("public-node terminal source probability is present")
            result.append(None)
            continue
        expected = (len(layout.hands_by_player[node.player]), len(node.actions))
        if (
            not isinstance(supplied, np.ndarray)
            or supplied.shape != expected
            or supplied.dtype != np.float64
            or not supplied.flags.c_contiguous
            or not np.all(np.isfinite(supplied))
            or np.any(supplied < 0.0)
            or np.any(supplied > 1.0)
            or not np.allclose(
                np.sum(supplied, axis=1),
                1.0,
                atol=1e-12,
                rtol=0.0,
            )
        ):
            raise ValueError("public-node source probability row is invalid")
        result.append(_readonly(supplied))
    return tuple(result)


def _independent_exact_payoff(
    layout: Any,
    probabilities: PolicyProbabilityTape,
    *,
    payoff_player: int,
) -> float:
    """Evaluate a hand-axis tape through the layout's independent dense DP."""

    deal_probabilities = []
    for node, hand_values in zip(layout.nodes, probabilities, strict=True):
        if node.player == TERMINAL_PLAYER:
            deal_probabilities.append(None)
            continue
        if hand_values is None:
            raise ValueError("public-node strategic source probability is absent")
        deal_probabilities.append(
            np.ascontiguousarray(
                hand_values[layout.hand_ids[:, node.player]],
                dtype=np.float64,
            )
        )
    evaluator = getattr(layout, "_expected_utilities", None)
    if not callable(evaluator):
        raise TypeError("public-node context requires an exact layout evaluator")
    utilities = tuple(float(value) for value in evaluator(tuple(deal_probabilities)))
    if len(utilities) != layout.num_players or any(
        not np.isfinite(value) for value in utilities
    ):
        raise FloatingPointError("public-node exact source payoff is invalid")
    return utilities[payoff_player]


@dataclass(frozen=True, slots=True, init=False)
class PublicNodeAffineSourceContext:
    """Factory-only snapshot binding coefficients, source tape, roles and game."""

    layout: Any
    probabilities: PolicyProbabilityTape
    acting_player: int
    payoff_player: int
    public_node: int
    source_value: float
    action_coefficients: np.ndarray
    identity: CrossPayoffContextIdentity

    def __init__(
        self,
        *,
        layout: Any,
        probabilities: PolicyProbabilityTape,
        acting_player: int,
        payoff_player: int,
        public_node: int,
        source_value: float,
        action_coefficients: np.ndarray,
        identity: CrossPayoffContextIdentity,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _CONTEXT_FACTORY_TOKEN:
            raise TypeError(
                "public-node affine contexts are factory-only; use "
                "build_public_node_affine_source_context"
            )
        object.__setattr__(self, "layout", layout)
        object.__setattr__(self, "probabilities", probabilities)
        object.__setattr__(self, "acting_player", acting_player)
        object.__setattr__(self, "payoff_player", payoff_player)
        object.__setattr__(self, "public_node", public_node)
        object.__setattr__(self, "source_value", source_value)
        object.__setattr__(self, "action_coefficients", action_coefficients)
        object.__setattr__(self, "identity", identity)


def build_public_node_affine_source_context(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    traverser_result: CrossPayoffAdjointResult[Any],
    *,
    acting_player: int,
    payoff_player: int,
    public_node: int,
) -> PublicNodeAffineSourceContext:
    """Independently bind and validate one root affine-row source context."""

    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if (
            isinstance(player, bool)
            or not isinstance(player, int)
            or player not in range(layout.num_players)
        ):
            raise ValueError(f"public-node open axis has an invalid {label} player")
    if (
        isinstance(public_node, bool)
        or not isinstance(public_node, int)
        or public_node not in range(layout.public_node_count)
    ):
        raise ValueError("public-node open axis is outside the layout")
    if public_node != 0:
        raise ValueError(
            "public-node open axis supports only root public node 0 until "
            "upstream own reach is represented"
        )
    if not isinstance(traverser_result, CrossPayoffAdjointResult):
        raise TypeError("public-node open axis requires a typed cross-payoff result")
    node = layout.nodes[public_node]
    if node.player == TERMINAL_PLAYER or node.player != acting_player:
        raise ValueError("public-node open axis belongs to another player")
    if traverser_result.acting_player != acting_player:
        raise ValueError("public-node open-axis result belongs to another player")
    if traverser_result.payoff_player != payoff_player:
        raise ValueError("public-node open-axis payoff roles are crossed")

    snapshot = _snapshot_probability_tape(layout, source_probabilities)
    identity = _derive_context_identity(layout, snapshot)
    if identity != traverser_result.context_identity:
        raise ValueError(
            "public-node open-axis result belongs to another layout or source tape"
        )
    matched_reads = tuple(
        read for read in traverser_result.reads if int(read.node_index) == public_node
    )
    if len(matched_reads) != 1:
        raise ValueError("public-node open-axis read is absent")
    current = snapshot[public_node]
    coefficients = np.asarray(matched_reads[0].action_numerators, dtype=np.float64)
    if (
        current is None
        or coefficients.shape != current.shape
        or coefficients.shape[1] != len(node.actions)
        or not np.all(np.isfinite(coefficients))
    ):
        raise ValueError("public-node open-axis read has the wrong action values")
    owned_coefficients = _readonly(coefficients)
    independent = dense_root_cross_payoff_control(
        layout,
        snapshot,
        acting_player=acting_player,
        payoff_player=payoff_player,
    )
    independent_reads = tuple(
        read for read in independent.reads if int(read.node_index) == public_node
    )
    if len(independent_reads) != 1 or not np.allclose(
        owned_coefficients,
        independent_reads[0].action_numerators,
        atol=SOURCE_IDENTITY_ATOL,
        rtol=0.0,
    ):
        raise ArithmeticError(
            "public-node adjoint coefficients disagree with the independent dense oracle"
        )
    source_value = _independent_exact_payoff(
        layout,
        snapshot,
        payoff_player=payoff_player,
    )
    source_linear = float(
        np.einsum("ha,ha->", current, owned_coefficients, optimize=True)
    )
    if not np.isfinite(source_linear):
        raise FloatingPointError("public-node open-axis source contraction is invalid")
    if abs(source_linear - source_value) > SOURCE_IDENTITY_ATOL:
        raise ArithmeticError(
            "public-node adjoint disagrees with the independent exact source payoff"
        )
    if abs(independent.source_value - source_value) > SOURCE_IDENTITY_ATOL:
        raise ArithmeticError(
            "public-node dense oracle disagrees with the independent source payoff"
        )
    raw_source = getattr(traverser_result.raw_result, "source_value", source_value)
    if not np.isfinite(raw_source) or abs(float(raw_source) - source_value) > (
        SOURCE_IDENTITY_ATOL
    ):
        raise ArithmeticError(
            "public-node raw result disagrees with the independent exact source payoff"
        )
    return PublicNodeAffineSourceContext(
        layout=layout,
        probabilities=snapshot,
        acting_player=acting_player,
        payoff_player=payoff_player,
        public_node=public_node,
        source_value=source_value,
        action_coefficients=owned_coefficients,
        identity=identity,
        _factory_token=_CONTEXT_FACTORY_TOKEN,
    )


def public_node_open_axis_payoff_row(
    context: PublicNodeAffineSourceContext,
) -> SequenceFormAffineRow:
    """Build a row only from one independently validated source context."""

    if not isinstance(context, PublicNodeAffineSourceContext):
        raise TypeError("public-node open axis requires a bound source context")
    live_identity = _derive_context_identity(context.layout, context.probabilities)
    if live_identity != context.identity:
        raise ValueError("public-node affine context changed after construction")
    current = context.probabilities[context.public_node]
    if current is None:
        raise AssertionError("public-node affine context lost its current row")
    source_linear = float(
        np.einsum(
            "ha,ha->",
            current,
            context.action_coefficients,
            optimize=True,
        )
    )
    row = SequenceFormAffineRow(
        acting_player=context.acting_player,
        constant=float(context.source_value - source_linear),
        nodes=(
            OpenAxisNodeCoefficients(
                context.public_node,
                context.action_coefficients,
            ),
        ),
    )
    if abs(row.value(context.probabilities) - context.source_value) > (
        SOURCE_IDENTITY_ATOL
    ):
        raise ArithmeticError("public-node open-axis source intercept differs")
    return row


__all__ = [
    "SOURCE_IDENTITY_ATOL",
    "PublicNodeAffineSourceContext",
    "build_public_node_affine_source_context",
    "public_node_open_axis_payoff_row",
]
