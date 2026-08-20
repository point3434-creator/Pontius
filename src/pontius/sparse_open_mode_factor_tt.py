"""Optional CSR open-mode contraction for generic tensor trains.

ADR-0083 froze the direct-showdown wrapper.  Policy-conditioned public-tree
values are ordinary tensor trains, but they use the same fixed incidence maps.
This additive successor reuses the frozen sparse direction kernel without
changing the audited terminal implementation or making SciPy a core import.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .factor_tt_contraction import _tt_half_vectors
from .open_mode_factor_tt import (
    OpenModeFactorTTWorkspace,
    OpenModeHandValues,
    OpenModeTrainValues,
    _prepare_mode_factors,
    _weighted_half_products,
)
from .sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
    SparseOpenModeDirectionalWork,
    _contract_sparse_direction,
)
from .tensor_train import TensorTrain


@dataclass(frozen=True, slots=True)
class SparseOpenModeFactorTTBatchContraction:
    """Several generic value TTs read through shared fixed CSR operators."""

    trains: tuple[OpenModeTrainValues, ...]
    directions: tuple[SparseOpenModeDirectionalWork, ...]
    target_seats: tuple[int, ...]
    middle_ranks: tuple[int, ...]
    total_middle_rank: int
    mode_factors_are_identity: bool
    maximum_feature_width_per_batch: int
    sparse_operator_numeric_bytes: int
    sparse_operator_compile_ms: float
    half_vector_numeric_bytes: int
    referenced_tt_storage_bytes: int
    result_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int

    def for_train(self, index: int) -> OpenModeTrainValues:
        if index not in range(len(self.trains)):
            raise KeyError(f"tensor train {index} was not requested")
        return self.trains[index]


def contract_sparse_open_mode_batch(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    trains: tuple[TensorTrain, ...],
    *,
    target_seats: tuple[int, ...] | None = None,
    mode_factors: tuple[object, ...] | None = None,
    zero_reach_value: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
) -> SparseOpenModeFactorTTBatchContraction:
    """Contract generic TTs with the CSR incidence backend.

    Rank slices, per-record folds, and per-hand grouping are intentionally the
    same as the frozen direct-automaton backend.  Only construction of the half
    vectors differs.
    """

    if sparse.topology is not workspace.topology:
        raise ValueError("sparse incidence operators belong to another topology")
    if not trains:
        raise ValueError("sparse open-mode batch requires at least one tensor train")
    shape = workspace.topology.base.hand_counts
    if any(train.shape != shape for train in trains):
        raise ValueError("tensor-train modes differ from open topology")
    players = len(shape)
    targets = tuple(range(players)) if target_seats is None else tuple(target_seats)
    if not targets or len(set(targets)) != len(targets):
        raise ValueError("sparse open-mode target seats must be nonempty and unique")
    if any(
        isinstance(seat, bool) or seat not in range(players) for seat in targets
    ):
        raise ValueError("sparse open-mode target is outside the hand axes")
    if not np.isfinite(zero_reach_value):
        raise ValueError("sparse zero-reach fallback must be finite")
    components = workspace.component_count
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch < components
    ):
        raise ValueError("sparse feature batch is smaller than component count")

    factors, identity = _prepare_mode_factors(shape, mode_factors)
    topology = workspace.topology.base
    left_products = _weighted_half_products(
        workspace.base.left_component_products,
        topology.left,
        factors,
        identity=identity,
    )
    right_products = _weighted_half_products(
        workspace.base.right_component_products,
        topology.right,
        factors,
        identity=identity,
    )
    half_vectors = tuple(_tt_half_vectors(train, topology) for train in trains)
    middle_ranks = tuple(left.shape[1] for left, _ in half_vectors)
    if any(
        right.shape[1] != rank
        for (_, right), rank in zip(half_vectors, middle_ranks, strict=True)
    ):
        raise AssertionError("sparse generic-TT half ranks differ")

    requested = set(targets)
    by_train: list[dict[int, OpenModeHandValues]] = [dict() for _ in trains]
    works = []
    left_targets = tuple(seat for seat in topology.left.seats if seat in requested)
    if left_targets:
        values, work = _contract_sparse_direction(
            workspace=workspace,
            operator=sparse.right_to_left,
            direction="right_to_left",
            query_half=topology.left,
            source_half=topology.right,
            query_products=left_products,
            source_products=right_products,
            query_vectors=tuple(left for left, _ in half_vectors),
            source_vectors=tuple(right for _, right in half_vectors),
            cached_denominator_incidence=(
                workspace.base.right_component_incidence if identity else None
            ),
            targets=left_targets,
            zero_reach_value=float(zero_reach_value),
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for index, row in enumerate(values):
            by_train[index].update(row)
        works.append(work)

    right_targets = tuple(seat for seat in topology.right.seats if seat in requested)
    if right_targets:
        values, work = _contract_sparse_direction(
            workspace=workspace,
            operator=sparse.left_to_right,
            direction="left_to_right",
            query_half=topology.right,
            source_half=topology.left,
            query_products=right_products,
            source_products=left_products,
            query_vectors=tuple(right for _, right in half_vectors),
            source_vectors=tuple(left for left, _ in half_vectors),
            cached_denominator_incidence=(
                workspace.left_component_incidence if identity else None
            ),
            targets=right_targets,
            zero_reach_value=float(zero_reach_value),
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for index, row in enumerate(values):
            by_train[index].update(row)
        works.append(work)

    train_results = tuple(
        OpenModeTrainValues(
            train_index=index,
            targets=tuple(by_train[index][seat] for seat in targets),
        )
        for index in range(len(trains))
    )
    result_bytes = sum(
        target.unnormalized_numerators.nbytes
        + target.unnormalized_reaches.nbytes
        + target.root_normalized_numerators.nbytes
        + target.root_normalized_reaches.nbytes
        + target.reached_hand_distribution.nbytes
        + target.conditional_values.nbytes
        + target.positive_reach.nbytes
        for train_result in train_results
        for target in train_result.targets
    )
    half_bytes = sum(left.nbytes + right.nbytes for left, right in half_vectors)
    unique = {id(train): train for train in trains}
    train_bytes = sum(train.storage_bytes for train in unique.values())
    peak_scratch = max(
        (work.estimated_peak_scratch_numeric_bytes for work in works),
        default=0,
    )
    return SparseOpenModeFactorTTBatchContraction(
        trains=train_results,
        directions=tuple(works),
        target_seats=targets,
        middle_ranks=middle_ranks,
        total_middle_rank=sum(middle_ranks),
        mode_factors_are_identity=identity,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        sparse_operator_numeric_bytes=sparse.numeric_bytes,
        sparse_operator_compile_ms=sparse.compile_ms,
        half_vector_numeric_bytes=half_bytes,
        referenced_tt_storage_bytes=train_bytes,
        result_numeric_bytes=result_bytes,
        estimated_peak_total_numeric_bytes=(
            workspace.topology.numeric_bytes
            + workspace.numeric_bytes
            + sparse.numeric_bytes
            + half_bytes
            + train_bytes
            + result_bytes
            + peak_scratch
        ),
    )
