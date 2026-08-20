"""Open-mode contraction of sparse showdown automata without dense TT cores."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .open_mode_factor_tt import (
    OpenModeBatchDirectionalWork,
    OpenModeFactorTTWorkspace,
    OpenModeHandValues,
    OpenModeTrainValues,
    _contract_batch_direction,
    _prepare_mode_factors,
    _weighted_half_products,
)
from .structured_showdown_automaton import StructuredShowdownAutomaton


@dataclass(frozen=True, slots=True)
class OpenModeShowdownBatchContraction:
    """Sparse-automaton open vectors and attributable structural storage."""

    automata: tuple[OpenModeTrainValues, ...]
    directions: tuple[OpenModeBatchDirectionalWork, ...]
    target_seats: tuple[int, ...]
    mode_factors_are_identity: bool
    middle_ranks: tuple[int, ...]
    total_middle_rank: int
    maximum_feature_width_per_batch: int
    half_vector_numeric_bytes: int
    topology_numeric_bytes: int
    belief_workspace_numeric_bytes: int
    referenced_automaton_numeric_bytes: int
    result_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int

    def for_automaton(self, index: int) -> OpenModeTrainValues:
        if index not in range(len(self.automata)):
            raise KeyError(f"automaton {index} was not requested")
        return self.automata[index]


def contract_open_mode_showdown_batch(
    workspace: OpenModeFactorTTWorkspace,
    automata: tuple[StructuredShowdownAutomaton, ...],
    *,
    target_seats: tuple[int, ...] | None = None,
    mode_factors: tuple[object, ...] | None = None,
    zero_reach_value: float = 0.0,
    maximum_feature_width_per_batch: int = 1024,
) -> OpenModeShowdownBatchContraction:
    """Contract deterministic transition tables directly through card incidence.

    The only dense values created are the two assignment-by-middle-state half
    vectors required by the contraction.  No Cartesian payoff tensor and no
    one-hot three-core tensor-train export is constructed.
    """

    if not automata:
        raise ValueError("open-mode showdown batch requires at least one automaton")
    base = workspace.base
    topology = workspace.topology
    shape = topology.base.hand_counts
    if any(automaton.shape != shape for automaton in automata):
        raise ValueError("showdown automaton modes do not match open-mode topology")
    players = len(shape)
    targets = tuple(range(players)) if target_seats is None else tuple(target_seats)
    if not targets or len(set(targets)) != len(targets):
        raise ValueError("open-mode target seats must be nonempty and unique")
    if any(
        isinstance(seat, bool) or seat not in range(players) for seat in targets
    ):
        raise ValueError("open-mode target seat is outside the hand axes")
    if not np.isfinite(zero_reach_value):
        raise ValueError("zero-reach fallback must be finite")
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch < base.component_count
    ):
        raise ValueError(
            "open-mode batch feature width cannot be smaller than component count"
        )

    factors, identity = _prepare_mode_factors(shape, mode_factors)
    left_products = _weighted_half_products(
        base.left_component_products,
        topology.base.left,
        factors,
        identity=identity,
    )
    right_products = _weighted_half_products(
        base.right_component_products,
        topology.base.right,
        factors,
        identity=identity,
    )
    half_vectors = tuple(
        _automaton_half_vectors(automaton, workspace) for automaton in automata
    )
    middle_ranks = tuple(left.shape[1] for left, _ in half_vectors)
    if any(
        right.shape[1] != rank
        for (_, right), rank in zip(half_vectors, middle_ranks, strict=True)
    ):
        raise AssertionError("showdown automaton half ranks differ")

    requested = set(targets)
    by_automaton: list[dict[int, OpenModeHandValues]] = [
        {} for _ in automata
    ]
    works: list[OpenModeBatchDirectionalWork] = []
    left_targets = tuple(seat for seat in topology.base.left.seats if seat in requested)
    if left_targets:
        values, work = _contract_batch_direction(
            workspace=workspace,
            direction="right_to_left",
            query_half=topology.base.left,
            source_half=topology.base.right,
            query_products=left_products,
            source_products=right_products,
            query_vectors=tuple(left for left, _ in half_vectors),
            source_vectors=tuple(right for _, right in half_vectors),
            source_incidence_ids=topology.base.right_incidence_ids,
            query_incidence_ids=topology.base.left_query_ids,
            query_incidence_signs=topology.base.left_query_signs,
            incidence_entries=topology.base.incidence_entries,
            cached_denominator_incidence=(
                base.right_component_incidence if identity else None
            ),
            targets=left_targets,
            zero_reach_value=float(zero_reach_value),
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for index, row in enumerate(values):
            by_automaton[index].update(row)
        works.append(work)
    right_targets = tuple(
        seat for seat in topology.base.right.seats if seat in requested
    )
    if right_targets:
        values, work = _contract_batch_direction(
            workspace=workspace,
            direction="left_to_right",
            query_half=topology.base.right,
            source_half=topology.base.left,
            query_products=right_products,
            source_products=left_products,
            query_vectors=tuple(right for _, right in half_vectors),
            source_vectors=tuple(left for left, _ in half_vectors),
            source_incidence_ids=topology.left_incidence_ids,
            query_incidence_ids=topology.right_query_ids,
            query_incidence_signs=topology.right_query_signs,
            incidence_entries=topology.reverse_incidence_entries,
            cached_denominator_incidence=(
                workspace.left_component_incidence if identity else None
            ),
            targets=right_targets,
            zero_reach_value=float(zero_reach_value),
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for index, row in enumerate(values):
            by_automaton[index].update(row)
        works.append(work)

    results = tuple(
        OpenModeTrainValues(
            train_index=index,
            targets=tuple(by_automaton[index][seat] for seat in targets),
        )
        for index in range(len(automata))
    )
    result_bytes = sum(
        target.unnormalized_numerators.nbytes
        + target.unnormalized_reaches.nbytes
        + target.root_normalized_numerators.nbytes
        + target.root_normalized_reaches.nbytes
        + target.reached_hand_distribution.nbytes
        + target.conditional_values.nbytes
        + target.positive_reach.nbytes
        for row in results
        for target in row.targets
    )
    half_bytes = sum(left.nbytes + right.nbytes for left, right in half_vectors)
    unique_automata = {id(automaton): automaton for automaton in automata}
    automaton_bytes = sum(
        automaton.numeric_bytes for automaton in unique_automata.values()
    )
    peak_scratch = max(
        (work.estimated_peak_batch_scratch_numeric_bytes for work in works),
        default=0,
    )
    return OpenModeShowdownBatchContraction(
        automata=results,
        directions=tuple(works),
        target_seats=targets,
        mode_factors_are_identity=identity,
        middle_ranks=middle_ranks,
        total_middle_rank=sum(middle_ranks),
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        half_vector_numeric_bytes=half_bytes,
        topology_numeric_bytes=topology.numeric_bytes,
        belief_workspace_numeric_bytes=workspace.numeric_bytes,
        referenced_automaton_numeric_bytes=automaton_bytes,
        result_numeric_bytes=result_bytes,
        estimated_peak_total_numeric_bytes=(
            topology.numeric_bytes
            + workspace.numeric_bytes
            + automaton_bytes
            + half_bytes
            + peak_scratch
            + result_bytes
        ),
    )


def _automaton_half_vectors(
    automaton: StructuredShowdownAutomaton,
    workspace: OpenModeFactorTTWorkspace,
) -> tuple[np.ndarray, np.ndarray]:
    topology = workspace.topology.base
    split = topology.split_index
    if automaton.num_players != len(topology.hand_counts):
        raise ValueError("showdown automaton player count differs from topology")
    if topology.left.seats != tuple(range(split)) or topology.right.seats != tuple(
        range(split, automaton.num_players)
    ):
        raise ValueError("showdown half vectors require a contiguous seat split")
    if automaton.constant_winner_shortcut:
        left = np.ones((topology.left.records, 1), dtype=np.float64)
        right = np.full(
            (topology.right.records, 1),
            automaton.sunk_value,
            dtype=np.float64,
        )
        return left, right

    left_state = np.zeros(topology.left.records, dtype=np.int32)
    left_rows = np.arange(topology.left.records)
    for mode in range(split):
        left_state = automaton.transitions[mode][
            left_state,
            topology.left.indices[:, mode],
        ]
    state_rank = len(automaton.bond_states[split - 1])
    left = np.zeros(
        (topology.left.records, state_rank + 1),
        dtype=np.float64,
        order="C",
    )
    left[left_rows, left_state] = 1.0
    left[:, state_rank] = 1.0

    right_state = np.broadcast_to(
        np.arange(state_rank, dtype=np.int32),
        (topology.right.records, state_rank),
    ).copy()
    for mode in range(split, automaton.num_players - 1):
        depth = mode - split
        hands = topology.right.indices[:, depth, None]
        right_state = automaton.transitions[mode][right_state, hands]
    final_hands = topology.right.indices[:, -1, None]
    winner = automaton.terminal_winner_values[right_state, final_hands]
    right = np.empty(
        (topology.right.records, state_rank + 1),
        dtype=np.float64,
        order="C",
    )
    right[:, :state_rank] = winner
    right[:, state_rank] = automaton.sunk_value
    return left, right
