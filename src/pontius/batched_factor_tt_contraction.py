"""Bounded-width contraction of weighted tensor-train sums.

This successor module deliberately leaves the frozen single-operator
contraction kernel untouched.  It streams a sum of factor-weighted tensor
trains through the same compiled card-incidence topology without first
materializing a high-rank direct-sum train.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .factor_tt_contraction import (
    FactorTTBeliefWorkspace,
    _accumulate_incidence,
    _query_incidence,
    _tt_half_vectors,
)
from .tensor_train import TensorTrain

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class WeightedTensorTrainTerm:
    """One signed TT with a pointwise unary factor on every hand mode."""

    train: TensorTrain
    mode_factors: tuple[FloatArray, ...]
    coefficient: float


@dataclass(frozen=True, slots=True)
class BatchedFactorTTContraction:
    """A weighted-sum expectation and attributable streaming-work bill."""

    expectation: float
    unnormalized_numerator: float
    terms: int
    rank_slices: int
    batches: int
    total_middle_rank: int
    total_feature_width: int
    maximum_batch_feature_width: int
    maximum_feature_width_per_batch: int
    incidence_feature_updates: int
    query_feature_terms: int
    referenced_tt_storage_bytes: int
    mode_factor_numeric_bytes: int
    estimated_peak_batch_scratch_bytes: int


def contract_weighted_sum(
    workspace: FactorTTBeliefWorkspace,
    terms: tuple[WeightedTensorTrainTerm, ...],
    *,
    maximum_feature_width_per_batch: int,
) -> BatchedFactorTTContraction:
    """Contract weighted TTs in rank slices bounded by a feature-width cap."""

    if not terms:
        raise ValueError("batched contraction requires at least one term")
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch <= 0
    ):
        raise ValueError("batch feature width must be a positive integer")
    if maximum_feature_width_per_batch < workspace.component_count:
        raise ValueError("batch feature width cannot be smaller than component count")

    prepared: list[tuple[FloatArray, FloatArray]] = []
    unique_trains: dict[int, TensorTrain] = {}
    unique_factors: dict[int, FloatArray] = {}
    total_middle_rank = 0
    for term in terms:
        if term.train.shape != workspace.topology.hand_counts:
            raise ValueError("weighted TT shape differs from belief topology")
        if len(term.mode_factors) != len(term.train.shape):
            raise ValueError("weighted TT requires one factor per mode")
        if not np.isfinite(term.coefficient):
            raise ValueError("weighted TT coefficient must be finite")

        factors: list[FloatArray] = []
        for size, supplied in zip(
            term.train.shape, term.mode_factors, strict=True
        ):
            values = np.ascontiguousarray(supplied, dtype=np.float64)
            if values.shape != (size,) or not np.all(np.isfinite(values)):
                raise ValueError("weighted TT mode factor is invalid")
            factors.append(values)
            unique_factors.setdefault(id(supplied), values)

        left, right = _tt_half_vectors(term.train, workspace.topology)
        left_weights = np.ones(workspace.topology.left.records, dtype=np.float64)
        for depth, seat in enumerate(workspace.topology.left.seats):
            left_weights *= factors[seat][workspace.topology.left.indices[:, depth]]
        right_weights = np.ones(workspace.topology.right.records, dtype=np.float64)
        for depth, seat in enumerate(workspace.topology.right.seats):
            right_weights *= factors[seat][workspace.topology.right.indices[:, depth]]
        left = np.ascontiguousarray(
            left * term.coefficient * left_weights[:, None], dtype=np.float64
        )
        right = np.ascontiguousarray(
            right * right_weights[:, None], dtype=np.float64
        )
        prepared.append((left, right))
        total_middle_rank += left.shape[1]
        unique_trains.setdefault(id(term.train), term.train)

    maximum_rank_per_slice = max(
        1, maximum_feature_width_per_batch // workspace.component_count
    )
    pieces: list[tuple[FloatArray, FloatArray]] = []
    for left, right in prepared:
        for start in range(0, left.shape[1], maximum_rank_per_slice):
            stop = min(start + maximum_rank_per_slice, left.shape[1])
            pieces.append((left[:, start:stop], right[:, start:stop]))

    batches: list[tuple[tuple[FloatArray, FloatArray], ...]] = []
    current: list[tuple[FloatArray, FloatArray]] = []
    current_width = 0
    for piece in pieces:
        width = workspace.component_count * piece[0].shape[1]
        if current and current_width + width > maximum_feature_width_per_batch:
            batches.append(tuple(current))
            current = []
            current_width = 0
        current.append(piece)
        current_width += width
    if current:
        batches.append(tuple(current))

    contributions_by_left = np.zeros(
        workspace.topology.left.records, dtype=np.float64
    )
    maximum_scratch = 0
    maximum_batch_width = 0
    for batch in batches:
        widths = tuple(
            workspace.component_count * left.shape[1] for left, _ in batch
        )
        batch_width = sum(widths)
        maximum_batch_width = max(maximum_batch_width, batch_width)
        right_features = np.ascontiguousarray(
            np.concatenate(
                tuple(
                    (
                        workspace.right_component_products[:, :, None]
                        * right[:, None, :]
                    ).reshape(workspace.topology.right.records, width)
                    for (_, right), width in zip(batch, widths, strict=True)
                ),
                axis=1,
            ),
            dtype=np.float64,
        )
        feature_incidence = _accumulate_incidence(
            right_features,
            workspace.topology.right_incidence_ids,
            workspace.topology.incidence_entries,
        )
        for start in range(
            0, workspace.topology.left.records, workspace.query_chunk_records
        ):
            stop = min(
                start + workspace.query_chunk_records,
                workspace.topology.left.records,
            )
            compatible = _query_incidence(
                feature_incidence,
                workspace.topology.left_query_ids[start:stop],
                workspace.topology.left_query_signs[start:stop],
            )
            offset = 0
            for (left, _), width in zip(batch, widths, strict=True):
                rank = left.shape[1]
                block = compatible[:, offset : offset + width].reshape(
                    stop - start, workspace.component_count, rank
                )
                contributions_by_left[start:stop] += np.einsum(
                    "k,lk,lkr,lr->l",
                    workspace.mixture_weights,
                    workspace.left_component_products[start:stop],
                    block,
                    left[start:stop],
                    optimize=True,
                )
                offset += width

        query_records = min(
            workspace.query_chunk_records, workspace.topology.left.records
        )
        query_subset_count = workspace.topology.left_query_ids.shape[1]
        maximum_scratch = max(
            maximum_scratch,
            right_features.nbytes
            + feature_incidence.nbytes
            + query_records
            * query_subset_count
            * batch_width
            * np.dtype(np.float64).itemsize
            + query_records * batch_width * np.dtype(np.float64).itemsize,
        )

    numerator = fsum(float(value) for value in contributions_by_left)
    subset_count = workspace.topology.right_incidence_ids.shape[1]
    query_subset_count = workspace.topology.left_query_ids.shape[1]
    total_feature_width = workspace.component_count * total_middle_rank
    return BatchedFactorTTContraction(
        expectation=numerator / workspace.partition,
        unnormalized_numerator=numerator,
        terms=len(terms),
        rank_slices=len(pieces),
        batches=len(batches),
        total_middle_rank=total_middle_rank,
        total_feature_width=total_feature_width,
        maximum_batch_feature_width=maximum_batch_width,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        incidence_feature_updates=(
            workspace.topology.right.records * subset_count * total_feature_width
        ),
        query_feature_terms=(
            workspace.topology.left.records
            * query_subset_count
            * total_feature_width
        ),
        referenced_tt_storage_bytes=sum(
            train.storage_bytes for train in unique_trains.values()
        ),
        mode_factor_numeric_bytes=sum(
            factor.nbytes for factor in unique_factors.values()
        ),
        estimated_peak_batch_scratch_bytes=maximum_scratch,
    )
