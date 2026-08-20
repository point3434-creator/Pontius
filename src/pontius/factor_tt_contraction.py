"""Direct contraction of exact factorized card beliefs with tensor trains.

The card-disjointness topology is compiled into contiguous integer arrays once.
One belief workspace then caches half-range products and its compatible
partition.  Signed tensor-train operators reuse both layers and never
materialize a full joint probability or value tensor.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .factorized_belief import FactorizedCardBelief
from .tensor_train import TensorTrain

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]
SignArray: TypeAlias = NDArray[np.int8]
UIntArray: TypeAlias = NDArray[np.uint64]


def _readonly_contiguous(values: object, dtype: np.dtype[object]) -> NDArray[object]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def _subsets(mask: int) -> tuple[int, ...]:
    result = []
    subset = mask
    while True:
        result.append(subset)
        if subset == 0:
            break
        subset = (subset - 1) & mask
    return tuple(result)


@dataclass(frozen=True, slots=True)
class CardHalfTopology:
    """Compatible assignments for one contiguous half of the seat axis."""

    seats: tuple[int, ...]
    masks: UIntArray
    indices: IntArray

    @property
    def records(self) -> int:
        return len(self.masks)

    @property
    def numeric_bytes(self) -> int:
        return self.masks.nbytes + self.indices.nbytes


@dataclass(frozen=True, slots=True)
class FactorTTTopology:
    """Range-independent card compatibility topology for one TT split."""

    hand_counts: tuple[int, ...]
    axis_masks: tuple[UIntArray, ...]
    split_index: int
    left: CardHalfTopology
    right: CardHalfTopology
    right_incidence_ids: IntArray
    left_query_ids: IntArray
    left_query_signs: SignArray
    incidence_entries: int

    @classmethod
    def compile(
        cls,
        belief: FactorizedCardBelief,
        *,
        split_index: int,
    ) -> FactorTTTopology:
        if split_index <= 0 or split_index >= belief.num_players:
            raise ValueError("TT split must leave two nonempty contiguous halves")
        left_seats = tuple(range(split_index))
        right_seats = tuple(range(split_index, belief.num_players))
        if len(left_seats) > 3 or len(right_seats) > 3:
            raise ValueError("compiled subset topology supports at most three seats per half")

        axis_masks = tuple(
            _readonly_contiguous(values, np.dtype(np.uint64))
            for values in belief.hand_masks
        )
        left = _enumerate_half(axis_masks, left_seats)
        right = _enumerate_half(axis_masks, right_seats)

        right_subset_count = 1 << (2 * len(right_seats))
        left_subset_count = 1 << (2 * len(left_seats))
        incidence_keys: set[int] = set()
        for supplied_mask in right.masks:
            subsets = _subsets(int(supplied_mask))
            if len(subsets) != right_subset_count:
                raise AssertionError("right half assignment did not contain distinct cards")
            incidence_keys.update(subsets)
        ordered_keys = tuple(sorted(incidence_keys))
        if len(ordered_keys) >= np.iinfo(np.int32).max:
            raise OverflowError("incidence topology exceeds Int32 IDs")
        key_to_id = {key: index for index, key in enumerate(ordered_keys)}

        right_ids = np.empty(
            (right.records, right_subset_count),
            dtype=np.int32,
            order="C",
        )
        for record, supplied_mask in enumerate(right.masks):
            right_ids[record] = tuple(
                key_to_id[subset] for subset in _subsets(int(supplied_mask))
            )

        left_ids = np.empty(
            (left.records, left_subset_count),
            dtype=np.int32,
            order="C",
        )
        left_signs = np.empty_like(left_ids, dtype=np.int8)
        for record, supplied_mask in enumerate(left.masks):
            subsets = _subsets(int(supplied_mask))
            if len(subsets) != left_subset_count:
                raise AssertionError("left half assignment did not contain distinct cards")
            left_ids[record] = tuple(key_to_id.get(subset, -1) for subset in subsets)
            left_signs[record] = tuple(
                -1 if subset.bit_count() % 2 else 1 for subset in subsets
            )

        right_ids.flags.writeable = False
        left_ids.flags.writeable = False
        left_signs.flags.writeable = False
        return cls(
            hand_counts=belief.hand_counts,
            axis_masks=axis_masks,
            split_index=split_index,
            left=left,
            right=right,
            right_incidence_ids=right_ids,
            left_query_ids=left_ids,
            left_query_signs=left_signs,
            incidence_entries=len(ordered_keys),
        )

    @property
    def numeric_bytes(self) -> int:
        return (
            sum(values.nbytes for values in self.axis_masks)
            + self.left.numeric_bytes
            + self.right.numeric_bytes
            + self.right_incidence_ids.nbytes
            + self.left_query_ids.nbytes
            + self.left_query_signs.nbytes
        )

    def storage_is_contiguous_fixed_dtype(self) -> bool:
        return (
            all(
                values.dtype == np.uint64 and values.flags.c_contiguous
                for values in self.axis_masks
            )
            and self.left.masks.dtype == np.uint64
            and self.left.masks.flags.c_contiguous
            and self.right.masks.dtype == np.uint64
            and self.right.masks.flags.c_contiguous
            and self.left.indices.dtype == np.int32
            and self.left.indices.flags.c_contiguous
            and self.right.indices.dtype == np.int32
            and self.right.indices.flags.c_contiguous
            and self.right_incidence_ids.dtype == np.int32
            and self.right_incidence_ids.flags.c_contiguous
            and self.left_query_ids.dtype == np.int32
            and self.left_query_ids.flags.c_contiguous
            and self.left_query_signs.dtype == np.int8
            and self.left_query_signs.flags.c_contiguous
        )


@dataclass(frozen=True, slots=True)
class FactorTTContraction:
    """One normalized expectation plus explicit work and memory accounting."""

    expectation: float
    unnormalized_numerator: float
    partition: float
    middle_rank: int
    feature_width: int
    left_records: int
    right_records: int
    incidence_entries: int
    incidence_feature_updates: int
    query_feature_terms: int
    topology_numeric_bytes: int
    belief_workspace_numeric_bytes: int
    tt_storage_bytes: int
    operator_static_numeric_bytes: int
    estimated_peak_scratch_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int
    numerator_absolute_term_sum: float
    numerator_cancellation_ratio: float | None


@dataclass(frozen=True, slots=True)
class EnumeratedFactorTTExpectation:
    """Explicit compatible-joint oracle for correctness and timing controls."""

    expectation: float
    partition: float
    compatible_assignments: int
    numeric_bytes: int


@dataclass(frozen=True, slots=True)
class FactorTTBeliefWorkspace:
    """One exact range compiled against a reusable card topology."""

    topology: FactorTTTopology
    mixture_weights: FloatArray
    left_component_products: FloatArray
    right_component_products: FloatArray
    right_component_incidence: FloatArray
    partition: float
    query_chunk_records: int

    @classmethod
    def compile(
        cls,
        topology: FactorTTTopology,
        belief: FactorizedCardBelief,
        *,
        query_chunk_records: int = 256,
    ) -> FactorTTBeliefWorkspace:
        if isinstance(query_chunk_records, bool) or query_chunk_records <= 0:
            raise ValueError("query chunk records must be a positive integer")
        _validate_belief_topology(topology, belief)
        mixture = _readonly_contiguous(
            belief.mixture_weights,
            np.dtype(np.float64),
        )
        left_products = _half_component_products(
            belief,
            topology.left,
        )
        right_products = _half_component_products(
            belief,
            topology.right,
        )
        component_incidence = _accumulate_incidence(
            right_products,
            topology.right_incidence_ids,
            topology.incidence_entries,
        )

        terms: list[float] = []
        scale = max(1.0, float(np.max(np.abs(component_incidence[:-1]))))
        for start in range(0, topology.left.records, query_chunk_records):
            stop = min(start + query_chunk_records, topology.left.records)
            compatible = _query_incidence(
                component_incidence,
                topology.left_query_ids[start:stop],
                topology.left_query_signs[start:stop],
            )
            minimum = float(np.min(compatible))
            if minimum < -1e-11 * scale:
                raise ArithmeticError(
                    "belief inclusion-exclusion produced materially negative mass"
                )
            if minimum < 0.0:
                compatible = np.maximum(compatible, 0.0)
            masses = np.einsum(
                "k,lk,lk->l",
                mixture,
                left_products[start:stop],
                compatible,
                optimize=True,
            )
            terms.extend(float(value) for value in masses)
        partition = fsum(terms)
        if partition <= 0.0:
            raise ValueError("factor–TT belief workspace has zero compatible mass")
        return cls(
            topology=topology,
            mixture_weights=mixture,
            left_component_products=left_products,
            right_component_products=right_products,
            right_component_incidence=component_incidence,
            partition=partition,
            query_chunk_records=query_chunk_records,
        )

    @property
    def component_count(self) -> int:
        return len(self.mixture_weights)

    @property
    def numeric_bytes(self) -> int:
        return (
            self.mixture_weights.nbytes
            + self.left_component_products.nbytes
            + self.right_component_products.nbytes
            + self.right_component_incidence.nbytes
        )

    def contract(self, train: TensorTrain) -> FactorTTContraction:
        if train.shape != self.topology.hand_counts:
            raise ValueError("tensor-train modes do not match topology hand axes")
        left_vectors, right_vectors = _tt_half_vectors(train, self.topology)
        middle_rank = left_vectors.shape[1]
        if right_vectors.shape[1] != middle_rank:
            raise AssertionError("left and right TT middle ranks differ")
        feature_width = self.component_count * middle_rank
        right_features = np.ascontiguousarray(
            (
                self.right_component_products[:, :, None]
                * right_vectors[:, None, :]
            ).reshape(self.topology.right.records, feature_width),
            dtype=np.float64,
        )
        feature_incidence = _accumulate_incidence(
            right_features,
            self.topology.right_incidence_ids,
            self.topology.incidence_entries,
        )

        terms: list[float] = []
        for start in range(
            0,
            self.topology.left.records,
            self.query_chunk_records,
        ):
            stop = min(
                start + self.query_chunk_records,
                self.topology.left.records,
            )
            compatible = _query_incidence(
                feature_incidence,
                self.topology.left_query_ids[start:stop],
                self.topology.left_query_signs[start:stop],
            ).reshape(stop - start, self.component_count, middle_rank)
            contributions = np.einsum(
                "k,lk,lkr,lr->l",
                self.mixture_weights,
                self.left_component_products[start:stop],
                compatible,
                left_vectors[start:stop],
                optimize=True,
            )
            terms.extend(float(value) for value in contributions)
        numerator = fsum(terms)
        absolute_term_sum = fsum(abs(value) for value in terms)
        cancellation = (
            absolute_term_sum / abs(numerator) if numerator != 0.0 else None
        )

        subset_count = self.topology.right_incidence_ids.shape[1]
        query_subset_count = self.topology.left_query_ids.shape[1]
        operator_static = (
            left_vectors.nbytes
            + right_vectors.nbytes
            + right_features.nbytes
            + feature_incidence.nbytes
        )
        accumulation_scratch = (
            self.topology.right.records * subset_count * np.dtype(np.float64).itemsize
            + (self.topology.incidence_entries + 1)
            * np.dtype(np.float64).itemsize
        )
        query_records = min(
            self.query_chunk_records,
            self.topology.left.records,
        )
        query_scratch = (
            query_records
            * query_subset_count
            * feature_width
            * np.dtype(np.float64).itemsize
            + query_records * feature_width * np.dtype(np.float64).itemsize
            + query_records * np.dtype(np.float64).itemsize
        )
        peak_scratch = max(accumulation_scratch, query_scratch)
        peak_total = (
            self.topology.numeric_bytes
            + self.numeric_bytes
            + train.storage_bytes
            + operator_static
            + peak_scratch
        )
        return FactorTTContraction(
            expectation=numerator / self.partition,
            unnormalized_numerator=numerator,
            partition=self.partition,
            middle_rank=middle_rank,
            feature_width=feature_width,
            left_records=self.topology.left.records,
            right_records=self.topology.right.records,
            incidence_entries=self.topology.incidence_entries,
            incidence_feature_updates=(
                self.topology.right.records * subset_count * feature_width
            ),
            query_feature_terms=(
                self.topology.left.records * query_subset_count * feature_width
            ),
            topology_numeric_bytes=self.topology.numeric_bytes,
            belief_workspace_numeric_bytes=self.numeric_bytes,
            tt_storage_bytes=train.storage_bytes,
            operator_static_numeric_bytes=operator_static,
            estimated_peak_scratch_numeric_bytes=peak_scratch,
            estimated_peak_total_numeric_bytes=peak_total,
            numerator_absolute_term_sum=absolute_term_sum,
            numerator_cancellation_ratio=cancellation,
        )


def evaluate_tensor_train_assignments(
    train: TensorTrain,
    assignments: object,
) -> FloatArray:
    """Evaluate a TT for a batch of integer mode assignments."""

    indices = np.ascontiguousarray(assignments, dtype=np.int32)
    if indices.ndim != 2 or indices.shape[1] != len(train.shape):
        raise ValueError("TT assignments require one integer column per mode")
    if any(
        np.any(indices[:, mode] < 0) or np.any(indices[:, mode] >= size)
        for mode, size in enumerate(train.shape)
    ):
        raise ValueError("TT assignment contains an out-of-range mode index")
    values = train.cores[0][0, indices[:, 0], :]
    for mode, core in enumerate(train.cores[1:], start=1):
        gathered = np.transpose(core[:, indices[:, mode], :], (1, 0, 2))
        values = np.einsum("li,lij->lj", values, gathered, optimize=True)
    return np.ascontiguousarray(values[:, 0], dtype=np.float64)


def enumerated_factor_tt_expectation(
    belief: FactorizedCardBelief,
    train: TensorTrain,
) -> EnumeratedFactorTTExpectation:
    """Materialize the compatible joint and evaluate the TT as an exact oracle."""

    if train.shape != belief.hand_counts:
        raise ValueError("tensor-train modes do not match belief hand axes")
    materialized = belief.materialize()
    indices = np.ascontiguousarray(materialized.assignments, dtype=np.int32)
    values = evaluate_tensor_train_assignments(train, indices)
    expectation = float(materialized.probabilities @ values)
    return EnumeratedFactorTTExpectation(
        expectation=expectation,
        partition=materialized.partition,
        compatible_assignments=materialized.card_compatible_assignments,
        numeric_bytes=(
            indices.nbytes
            + values.nbytes
            + materialized.probabilities.nbytes
            + materialized.unnormalized_weights.nbytes
        ),
    )


def _enumerate_half(
    axis_masks: tuple[UIntArray, ...],
    seats: tuple[int, ...],
) -> CardHalfTopology:
    masks: list[int] = []
    indices: list[tuple[int, ...]] = []
    selected = [0] * len(seats)

    def walk(depth: int, used_mask: int) -> None:
        if depth == len(seats):
            masks.append(used_mask)
            indices.append(tuple(selected))
            return
        seat = seats[depth]
        for hand_index, supplied_mask in enumerate(axis_masks[seat]):
            mask = int(supplied_mask)
            if used_mask & mask:
                continue
            selected[depth] = hand_index
            walk(depth + 1, used_mask | mask)

    walk(0, 0)
    if not masks:
        raise ValueError("one card-topology half has no compatible assignments")
    mask_array = _readonly_contiguous(masks, np.dtype(np.uint64))
    index_array = _readonly_contiguous(indices, np.dtype(np.int32))
    return CardHalfTopology(
        seats=seats,
        masks=mask_array,  # type: ignore[arg-type]
        indices=index_array,  # type: ignore[arg-type]
    )


def _validate_belief_topology(
    topology: FactorTTTopology,
    belief: FactorizedCardBelief,
) -> None:
    if belief.hand_counts != topology.hand_counts:
        raise ValueError("belief hand counts do not match the card topology")
    if len(belief.hand_masks) != len(topology.axis_masks) or any(
        not np.array_equal(first, second)
        for first, second in zip(
            belief.hand_masks,
            topology.axis_masks,
            strict=True,
        )
    ):
        raise ValueError("belief hand masks do not match the card topology")


def _half_component_products(
    belief: FactorizedCardBelief,
    half: CardHalfTopology,
) -> FloatArray:
    values = np.ones(
        (half.records, belief.component_count),
        dtype=np.float64,
        order="C",
    )
    for depth, seat in enumerate(half.seats):
        values *= belief.unary_weights[seat][:, half.indices[:, depth]].T
    values.flags.writeable = False
    return values


def _accumulate_incidence(
    features: FloatArray,
    incidence_ids: IntArray,
    incidence_entries: int,
) -> FloatArray:
    if features.ndim != 2 or features.shape[0] != incidence_ids.shape[0]:
        raise ValueError("incidence features do not match right topology records")
    table = np.zeros(
        (incidence_entries + 1, features.shape[1]),
        dtype=np.float64,
        order="C",
    )
    flat_ids = incidence_ids.ravel()
    repeats = incidence_ids.shape[1]
    for feature in range(features.shape[1]):
        weights = np.repeat(features[:, feature], repeats)
        table[:-1, feature] = np.bincount(
            flat_ids,
            weights=weights,
            minlength=incidence_entries,
        )
    table.flags.writeable = False
    return table


def _query_incidence(
    table: FloatArray,
    query_ids: IntArray,
    query_signs: SignArray,
) -> FloatArray:
    if query_ids.shape != query_signs.shape:
        raise ValueError("incidence query IDs and signs must have identical shapes")
    sentinel = len(table) - 1
    safe_ids = np.where(query_ids < 0, sentinel, query_ids)
    gathered = table[safe_ids]
    return np.ascontiguousarray(
        np.einsum(
            "lq,lqf->lf",
            query_signs,
            gathered,
            optimize=True,
        ),
        dtype=np.float64,
    )


def _tt_half_vectors(
    train: TensorTrain,
    topology: FactorTTTopology,
) -> tuple[FloatArray, FloatArray]:
    left_indices = topology.left.indices
    left = train.cores[0][0, left_indices[:, 0], :]
    for mode in range(1, topology.split_index):
        core = train.cores[mode]
        gathered = np.transpose(core[:, left_indices[:, mode], :], (1, 0, 2))
        left = np.einsum("li,lij->lj", left, gathered, optimize=True)

    right_indices = topology.right.indices
    final_depth = len(topology.right.seats) - 1
    right = train.cores[-1][:, right_indices[:, final_depth], 0].T
    for mode in range(len(train.shape) - 2, topology.split_index - 1, -1):
        depth = mode - topology.split_index
        core = train.cores[mode]
        gathered = np.transpose(core[:, right_indices[:, depth], :], (1, 0, 2))
        right = np.einsum("lij,lj->li", gathered, right, optimize=True)
    return (
        np.ascontiguousarray(left, dtype=np.float64),
        np.ascontiguousarray(right, dtype=np.float64),
    )
