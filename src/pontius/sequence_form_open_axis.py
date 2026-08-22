"""Sequence-form payoff rows from one target-omitted leaf contraction.

Each terminal contribution is assigned to the acting seat's last sequence on
that public path.  This yields an exact affine payoff row in realization-plan
coordinates even when the acting seat appears more than once on a path.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any, Mapping, TypeAlias

import numpy as np

from .game import Action, TERMINAL_PLAYER
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from .incremental_policy_tt import PolicyProbabilityTape
from .leaf_adjoint_cfr import _parent_metadata, _target_omitted_path_factors
from .public_policy_tt import _information_key, _terminal_keys_by_slot


RealizationTape: TypeAlias = tuple[np.ndarray | None, ...]


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=np.float64, order="C", copy=True)
    result.flags.writeable = False
    return result


def splice_fixed_response_probability_tape_for_axes(
    layout: Any,
    source_probabilities: PolicyProbabilityTape,
    response_actions: Mapping[str, Action],
    *,
    responding_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...],
) -> PolicyProbabilityTape:
    """Replace one player by a response keyed on the explicit external axes."""

    if (
        isinstance(responding_player, bool)
        or responding_player not in range(layout.num_players)
    ):
        raise ValueError("fixed response player is outside the layout")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("fixed response requires one explicit hand axis per player")
    if len(source_probabilities) != layout.public_node_count:
        raise ValueError("fixed response probability tape differs from the tree")

    expected_keys: set[str] = set()
    result = list(source_probabilities)
    for node_index, node in enumerate(layout.nodes):
        source = source_probabilities[node_index]
        if node.player == TERMINAL_PLAYER:
            if source is not None:
                raise ValueError("fixed response terminal has policy probabilities")
            continue
        if source is None:
            raise ValueError("fixed response strategic node has no probabilities")
        expected_shape = (
            len(hands_by_player[node.player]),
            len(node.actions),
        )
        if source.shape != expected_shape:
            raise ValueError("fixed response node probability shape differs")
        if node.player != responding_player:
            continue
        deterministic = np.zeros_like(source, dtype=np.float64, order="C")
        for hand_index, hand in enumerate(hands_by_player[responding_player]):
            key = _information_key(
                layout,
                responding_player,
                hand,
                node.history,
            )
            expected_keys.add(key)
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
    if set(response_actions) != expected_keys:
        raise ValueError("fixed response action map has missing or off-axis keys")
    return tuple(result)


def _last_acting_edge(
    layout: Any,
    parents: np.ndarray,
    parent_actions: np.ndarray,
    node_index: int,
    acting_player: int,
) -> tuple[int, int] | None:
    child = node_index
    while int(parents[child]) >= 0:
        parent = int(parents[child])
        if layout.nodes[parent].player == acting_player:
            return parent, int(parent_actions[child])
        child = parent
    return None


def sequence_form_realization_tape(
    layout: Any,
    probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...],
) -> RealizationTape:
    """Convert one behavioral policy axis to public-tree realization variables."""

    if acting_player not in range(layout.num_players):
        raise ValueError("sequence-form acting player is outside the layout")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("sequence-form probability tape differs from the tree")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("sequence-form requires one explicit hand axis per player")
    parents, parent_actions = _parent_metadata(layout)
    result: list[np.ndarray | None] = [None] * layout.public_node_count
    hand_count = len(hands_by_player[acting_player])
    for node_index, node in enumerate(layout.nodes):
        if node.player != acting_player:
            continue
        source = probabilities[node_index]
        if source is None or source.shape != (hand_count, len(node.actions)):
            raise ValueError("sequence-form acting probability row has the wrong shape")
        parent_sequence = _last_acting_edge(
            layout,
            parents,
            parent_actions,
            node_index,
            acting_player,
        )
        if parent_sequence is None:
            parent_mass = np.ones(hand_count, dtype=np.float64)
        else:
            parent_node, parent_action = parent_sequence
            parent_values = result[parent_node]
            if parent_values is None:
                raise AssertionError("sequence-form parent was not topologically available")
            parent_mass = parent_values[:, parent_action]
        realization = np.ascontiguousarray(
            parent_mass[:, None] * source,
            dtype=np.float64,
        )
        result[node_index] = _readonly(realization)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class OpenAxisNodeCoefficients:
    node_index: int
    values: np.ndarray


@dataclass(frozen=True, slots=True)
class SequenceFormAffineRow:
    acting_player: int
    constant: float
    nodes: tuple[OpenAxisNodeCoefficients, ...]

    @property
    def numeric_bytes(self) -> int:
        return sum(node.values.nbytes for node in self.nodes)

    def value(self, realization: RealizationTape) -> float:
        if not self.nodes:
            return self.constant
        total = self.constant
        for node in self.nodes:
            values = realization[node.node_index]
            if values is None or values.shape != node.values.shape:
                raise ValueError("realization tape differs from affine row")
            total += float(
                np.einsum(
                    "ha,ha->",
                    node.values,
                    values,
                    optimize=True,
                )
            )
        return total

    def flattened(self) -> np.ndarray:
        return np.ascontiguousarray(
            [self.constant, *(value for node in self.nodes for value in node.values.flat)],
            dtype=np.float64,
        )


@dataclass(frozen=True, slots=True)
class SequenceFormOpenAxisWork:
    terminal_contractions: int
    terminal_sparse_batches: int
    contraction_ms: float
    assembly_ms: float
    wall_ms: float
    maximum_middle_rank: int
    maximum_peak_numeric_bytes: int
    maximum_gpu_pool_total_bytes: int


@dataclass(frozen=True, slots=True)
class SequenceFormOpenAxisResult:
    acting_player: int
    payoff_player: int
    row: SequenceFormAffineRow
    work: SequenceFormOpenAxisWork


def extract_sequence_form_open_axis_payoff(
    layout: Any,
    workspace: Any,
    sparse: Any,
    probabilities: PolicyProbabilityTape,
    terminal_automata: Mapping[str, Any],
    *,
    acting_player: int,
    payoff_player: int,
    hands_by_player: tuple[tuple[Any, ...], ...],
    maximum_feature_width_per_batch: int = 96,
    cupy_sparse: Any | None = None,
) -> SequenceFormOpenAxisResult:
    """Extract one fixed-response payoff row over the acting realization axis."""

    wall_started = time.perf_counter()
    for label, player in (("acting", acting_player), ("payoff", payoff_player)):
        if isinstance(player, bool) or player not in range(layout.num_players):
            raise ValueError(f"open-axis {label} player is outside the layout")
    if sparse.topology is not workspace.topology:
        raise ValueError("open-axis sparse topology and workspace differ")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("open-axis requires one explicit hand axis per player")
    shape = workspace.topology.base.hand_counts
    if tuple(len(axis) for axis in hands_by_player) != shape:
        raise ValueError("open-axis hand axes differ from workspace")
    if len(probabilities) != layout.public_node_count:
        raise ValueError("open-axis probability tape differs from public tree")
    terminal_keys = _terminal_keys_by_slot(layout)
    if set(terminal_automata) != set(terminal_keys):
        raise ValueError("open-axis automata differ from terminal payoff groups")
    if any(
        automaton.target_player != payoff_player
        or automaton.shape != shape
        for automaton in terminal_automata.values()
    ):
        raise ValueError("open-axis automata have the wrong payoff role or axes")
    if cupy_sparse is not None and cupy_sparse.cpu is not sparse:
        raise ValueError("open-axis CuPy operators differ from CPU topology")

    parents, parent_actions = _parent_metadata(layout)
    terms = tuple(
        HeterogeneousLeafTerm(
            key=node_index,
            automaton=terminal_automata[terminal_keys[node.terminal_slot]],
            mode_factors=_target_omitted_path_factors(
                layout,
                probabilities,
                parents,
                parent_actions,
                terminal_node=node_index,
                traverser=acting_player,
                shape=shape,
            ),
        )
        for node_index, node in enumerate(layout.nodes)
        if node.player == TERMINAL_PLAYER
    )
    contraction_started = time.perf_counter()
    contraction = contract_heterogeneous_leaf_terms(
        workspace,
        sparse,
        terms,
        target_seat=acting_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        cupy_sparse=cupy_sparse,
    )
    contraction_ms = (time.perf_counter() - contraction_started) * 1000.0

    assembly_started = time.perf_counter()
    hand_count = len(hands_by_player[acting_player])
    coefficient_tables = {
        node_index: np.zeros(
            (hand_count, len(node.actions)),
            dtype=np.float64,
            order="C",
        )
        for node_index, node in enumerate(layout.nodes)
        if node.player == acting_player
    }
    constant = 0.0
    for terminal_node, values in contraction.values:
        vector = np.asarray(values.root_normalized_numerators, dtype=np.float64)
        if vector.shape != (hand_count,) or not np.all(np.isfinite(vector)):
            raise FloatingPointError("open-axis terminal vector is invalid")
        last_edge = _last_acting_edge(
            layout,
            parents,
            parent_actions,
            terminal_node,
            acting_player,
        )
        if last_edge is None:
            constant += fsum(float(value) for value in vector)
        else:
            node_index, action_index = last_edge
            coefficient_tables[node_index][:, action_index] += vector
    nodes = tuple(
        OpenAxisNodeCoefficients(node_index, _readonly(values))
        for node_index, values in sorted(coefficient_tables.items())
    )
    assembly_ms = (time.perf_counter() - assembly_started) * 1000.0
    row = SequenceFormAffineRow(acting_player, float(constant), nodes)
    work = contraction.work
    return SequenceFormOpenAxisResult(
        acting_player=acting_player,
        payoff_player=payoff_player,
        row=row,
        work=SequenceFormOpenAxisWork(
            terminal_contractions=len(terms),
            terminal_sparse_batches=work.batches,
            contraction_ms=contraction_ms,
            assembly_ms=assembly_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            maximum_middle_rank=work.maximum_middle_rank,
            maximum_peak_numeric_bytes=work.estimated_peak_total_numeric_bytes,
            maximum_gpu_pool_total_bytes=work.maximum_gpu_pool_total_bytes,
        ),
    )


def subtract_affine_rows(
    left: SequenceFormAffineRow,
    right: SequenceFormAffineRow,
) -> SequenceFormAffineRow:
    """Subtract two rows without changing their exact sequence coordinate set."""

    if left.acting_player != right.acting_player:
        raise ValueError("affine rows have different acting seats")
    left_nodes = {node.node_index: node.values for node in left.nodes}
    right_nodes = {node.node_index: node.values for node in right.nodes}
    if left_nodes.keys() != right_nodes.keys():
        raise ValueError("affine rows have different sequence nodes")
    nodes = []
    for node_index in sorted(left_nodes):
        if left_nodes[node_index].shape != right_nodes[node_index].shape:
            raise ValueError("affine row node shapes differ")
        nodes.append(
            OpenAxisNodeCoefficients(
                node_index,
                _readonly(left_nodes[node_index] - right_nodes[node_index]),
            )
        )
    return SequenceFormAffineRow(
        left.acting_player,
        left.constant - right.constant,
        tuple(nodes),
    )


def constant_minus_affine_row(
    constant: float,
    row: SequenceFormAffineRow,
) -> SequenceFormAffineRow:
    """Return the acting-seat gain row for an invariant best-response value."""

    if not np.isfinite(constant):
        raise ValueError("affine constant must be finite")
    return SequenceFormAffineRow(
        row.acting_player,
        float(constant) - row.constant,
        tuple(
            OpenAxisNodeCoefficients(node.node_index, _readonly(-node.values))
            for node in row.nodes
        ),
    )


@dataclass(frozen=True, slots=True)
class AffineRowConditioning:
    rows: int
    numerical_rank: int
    effective_condition_number: float | None
    minimum_normalized_separation: float | None


def affine_row_conditioning(
    rows: tuple[SequenceFormAffineRow, ...],
    *,
    tolerance: float,
) -> AffineRowConditioning:
    """Report numerical row geometry without removing any exact constraint."""

    if not rows:
        return AffineRowConditioning(0, 0, None, None)
    if tolerance <= 0.0 or not np.isfinite(tolerance):
        raise ValueError("conditioning tolerance must be finite and positive")
    widths = {row.flattened().size for row in rows}
    if len(widths) != 1:
        raise ValueError("conditioning rows have different widths")
    matrix = np.stack(tuple(row.flattened() for row in rows), axis=0)
    norms = np.linalg.norm(matrix, axis=1)
    normalized = matrix.copy()
    for index, norm in enumerate(norms):
        if norm > tolerance:
            normalized[index] /= norm
    minimum: float | None = None
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            distance = float(np.linalg.norm(normalized[left] - normalized[right]))
            minimum = distance if minimum is None else min(minimum, distance)
    singular = np.linalg.svd(normalized, compute_uv=False)
    threshold = tolerance * max(matrix.shape) * max(float(singular[0]), 1.0)
    nonzero = singular[singular > threshold]
    condition = None if len(nonzero) == 0 else float(nonzero[0] / nonzero[-1])
    return AffineRowConditioning(
        rows=len(rows),
        numerical_rank=len(nonzero),
        effective_condition_number=condition,
        minimum_normalized_separation=minimum,
    )
