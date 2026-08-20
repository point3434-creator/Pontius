"""Exact factor-TT contraction with one private-hand mode left open.

The scalar factor-TT kernel already splits seats into two compatible-assignment
halves.  For every record on the query half it computes one complete scalar
contribution after summing the source half by card-mask incidence.  Grouping
those record contributions by any query-half hand index leaves that seat's mode
open.  Consequently all seats on a half share one directional numeric pass;
all six seats need two directions, not six scalar contractions.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .factor_tt_contraction import (
    CardHalfTopology,
    FactorTTBeliefWorkspace,
    FactorTTTopology,
    _accumulate_incidence,
    _query_incidence,
    _tt_half_vectors,
)
from .tensor_train import TensorTrain

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]
SignArray: TypeAlias = NDArray[np.int8]


@dataclass(frozen=True, slots=True)
class BidirectionalFactorTTTopology:
    """The frozen forward topology plus the exact reverse incidence map."""

    base: FactorTTTopology
    left_incidence_ids: IntArray
    right_query_ids: IntArray
    right_query_signs: SignArray
    reverse_incidence_entries: int

    @classmethod
    def compile(cls, base: FactorTTTopology) -> BidirectionalFactorTTTopology:
        source_ids, query_ids, query_signs, entries = _compile_direction(
            source=base.left,
            query=base.right,
        )
        return cls(
            base=base,
            left_incidence_ids=source_ids,
            right_query_ids=query_ids,
            right_query_signs=query_signs,
            reverse_incidence_entries=entries,
        )

    @property
    def reverse_numeric_bytes(self) -> int:
        return (
            self.left_incidence_ids.nbytes
            + self.right_query_ids.nbytes
            + self.right_query_signs.nbytes
        )

    @property
    def numeric_bytes(self) -> int:
        return self.base.numeric_bytes + self.reverse_numeric_bytes

    def storage_is_contiguous_fixed_dtype(self) -> bool:
        return (
            self.base.storage_is_contiguous_fixed_dtype()
            and self.left_incidence_ids.dtype == np.int32
            and self.left_incidence_ids.flags.c_contiguous
            and self.right_query_ids.dtype == np.int32
            and self.right_query_ids.flags.c_contiguous
            and self.right_query_signs.dtype == np.int8
            and self.right_query_signs.flags.c_contiguous
        )


@dataclass(frozen=True, slots=True)
class OpenModeFactorTTWorkspace:
    """One belief with component incidence cached in both directions."""

    topology: BidirectionalFactorTTTopology
    base: FactorTTBeliefWorkspace
    left_component_incidence: FloatArray

    @classmethod
    def compile(
        cls,
        topology: BidirectionalFactorTTTopology,
        base: FactorTTBeliefWorkspace,
    ) -> OpenModeFactorTTWorkspace:
        if base.topology is not topology.base:
            raise ValueError("open-mode topology and belief workspace differ")
        left_incidence = _accumulate_incidence(
            base.left_component_products,
            topology.left_incidence_ids,
            topology.reverse_incidence_entries,
        )
        return cls(
            topology=topology,
            base=base,
            left_component_incidence=left_incidence,
        )

    @property
    def component_count(self) -> int:
        return self.base.component_count

    @property
    def numeric_bytes(self) -> int:
        return self.base.numeric_bytes + self.left_component_incidence.nbytes


@dataclass(frozen=True, slots=True)
class OpenModeHandValues:
    """Per-hand reach mass, value numerator, and explicit conditional values."""

    target_seat: int
    unnormalized_numerators: FloatArray
    unnormalized_reaches: FloatArray
    root_normalized_numerators: FloatArray
    root_normalized_reaches: FloatArray
    reached_hand_distribution: FloatArray
    conditional_values: FloatArray
    positive_reach: NDArray[np.bool_]
    total_unnormalized_numerator: float
    total_unnormalized_reach: float
    total_root_reach_probability: float
    reach_conditioned_expectation: float | None
    zero_reach_hands: int


@dataclass(frozen=True, slots=True)
class OpenModeDirectionalWork:
    """Attributable work for one source-half to query-half incidence pass."""

    direction: str
    query_seats: tuple[int, ...]
    source_records: int
    query_records: int
    source_subset_count: int
    query_subset_count: int
    incidence_entries: int
    middle_rank: int
    value_feature_width: int
    denominator_feature_width: int
    denominator_incidence_cached: bool
    value_incidence_feature_updates: int
    denominator_incidence_feature_updates: int
    value_query_feature_terms: int
    denominator_query_feature_terms: int
    operator_static_numeric_bytes: int
    estimated_peak_scratch_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class OpenModeFactorTTContraction:
    """Exact open-mode values plus two-direction work and memory accounting."""

    targets: tuple[OpenModeHandValues, ...]
    directions: tuple[OpenModeDirectionalWork, ...]
    target_seats: tuple[int, ...]
    mode_factors_are_identity: bool
    middle_rank: int
    half_vector_numeric_bytes: int
    topology_numeric_bytes: int
    belief_workspace_numeric_bytes: int
    tt_storage_bytes: int
    result_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int

    def for_seat(self, seat: int) -> OpenModeHandValues:
        for target in self.targets:
            if target.target_seat == seat:
                return target
        raise KeyError(f"seat {seat} was not requested")


@dataclass(frozen=True, slots=True)
class OpenModeTrainValues:
    """Open-hand vectors for one member of a batched TT request."""

    train_index: int
    targets: tuple[OpenModeHandValues, ...]

    def for_seat(self, seat: int) -> OpenModeHandValues:
        for target in self.targets:
            if target.target_seat == seat:
                return target
        raise KeyError(f"seat {seat} was not requested for train {self.train_index}")


@dataclass(frozen=True, slots=True)
class OpenModeBatchDirectionalWork:
    """Attributable work for one batched source-to-query direction."""

    direction: str
    query_seats: tuple[int, ...]
    trains: int
    source_records: int
    query_records: int
    source_subset_count: int
    query_subset_count: int
    incidence_entries: int
    middle_ranks: tuple[int, ...]
    total_middle_rank: int
    total_value_feature_width: int
    maximum_value_feature_width_per_batch: int
    maximum_observed_batch_feature_width: int
    rank_slices: int
    batches: int
    denominator_feature_width: int
    denominator_incidence_cached: bool
    value_incidence_feature_updates: int
    denominator_incidence_feature_updates: int
    value_query_feature_terms: int
    denominator_query_feature_terms: int
    estimated_peak_batch_scratch_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class OpenModeFactorTTBatchContraction:
    """Several value TTs contracted through shared open-mode incidence passes."""

    trains: tuple[OpenModeTrainValues, ...]
    directions: tuple[OpenModeBatchDirectionalWork, ...]
    target_seats: tuple[int, ...]
    mode_factors_are_identity: bool
    middle_ranks: tuple[int, ...]
    total_middle_rank: int
    maximum_feature_width_per_batch: int
    half_vector_numeric_bytes: int
    topology_numeric_bytes: int
    belief_workspace_numeric_bytes: int
    referenced_tt_storage_bytes: int
    result_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int

    def for_train(self, index: int) -> OpenModeTrainValues:
        if index not in range(len(self.trains)):
            raise KeyError(f"train {index} was not requested")
        return self.trains[index]


def contract_open_mode_batch(
    workspace: OpenModeFactorTTWorkspace,
    trains: tuple[TensorTrain, ...],
    *,
    target_seats: tuple[int, ...] | None = None,
    mode_factors: tuple[object, ...] | None = None,
    zero_reach_value: float = 0.0,
    maximum_feature_width_per_batch: int = 1024,
) -> OpenModeFactorTTBatchContraction:
    """Contract several TTs while sharing denominator and incidence sweeps.

    Middle bonds are split into deterministic rank slices so peak incidence
    storage is bounded by ``maximum_feature_width_per_batch``.  Each slice
    contributes to its train's per-record numerator; grouping by private hand
    occurs only after every slice has been accumulated.
    """

    if not trains:
        raise ValueError("open-mode batch requires at least one tensor train")
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch <= 0
    ):
        raise ValueError("open-mode batch feature width must be positive")
    base = workspace.base
    topology = workspace.topology
    shape = topology.base.hand_counts
    if any(train.shape != shape for train in trains):
        raise ValueError("tensor-train modes do not match open-mode topology")
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
    if maximum_feature_width_per_batch < base.component_count:
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
    half_vectors = tuple(_tt_half_vectors(train, topology.base) for train in trains)
    middle_ranks = tuple(left.shape[1] for left, _ in half_vectors)
    if any(right.shape[1] != rank for (_, right), rank in zip(
        half_vectors, middle_ranks, strict=True
    )):
        raise AssertionError("open-mode TT half ranks differ")

    requested = set(targets)
    by_train: list[dict[int, OpenModeHandValues]] = [dict() for _ in trains]
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
            by_train[index].update(row)
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
    unique_trains = {id(train): train for train in trains}
    peak_scratch = max(
        (work.estimated_peak_batch_scratch_numeric_bytes for work in works),
        default=0,
    )
    return OpenModeFactorTTBatchContraction(
        trains=train_results,
        directions=tuple(works),
        target_seats=targets,
        mode_factors_are_identity=identity,
        middle_ranks=middle_ranks,
        total_middle_rank=sum(middle_ranks),
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        half_vector_numeric_bytes=half_bytes,
        topology_numeric_bytes=topology.numeric_bytes,
        belief_workspace_numeric_bytes=workspace.numeric_bytes,
        referenced_tt_storage_bytes=sum(
            train.storage_bytes for train in unique_trains.values()
        ),
        result_numeric_bytes=result_bytes,
        estimated_peak_total_numeric_bytes=(
            topology.numeric_bytes
            + workspace.numeric_bytes
            + sum(train.storage_bytes for train in unique_trains.values())
            + half_bytes
            + peak_scratch
            + result_bytes
        ),
    )


def contract_open_modes(
    workspace: OpenModeFactorTTWorkspace,
    train: TensorTrain,
    *,
    target_seats: tuple[int, ...] | None = None,
    mode_factors: tuple[object, ...] | None = None,
    zero_reach_value: float = 0.0,
) -> OpenModeFactorTTContraction:
    """Contract one TT and return conditional vectors for requested seats.

    ``mode_factors`` are common nonnegative public-reach likelihoods, one vector
    per private-hand mode.  Numerators and reaches are normalized against the
    original belief partition, while conditional values divide the two and are
    therefore invariant to target-hand range scale.  Zero-reach hands receive
    the explicit finite ``zero_reach_value`` and a false mask entry.
    """

    base = workspace.base
    topology = workspace.topology
    if train.shape != topology.base.hand_counts:
        raise ValueError("tensor-train modes do not match open-mode topology")
    players = len(train.shape)
    if target_seats is None:
        targets = tuple(range(players))
    else:
        targets = tuple(target_seats)
    if not targets or len(set(targets)) != len(targets):
        raise ValueError("open-mode target seats must be nonempty and unique")
    if any(
        isinstance(seat, bool) or seat not in range(players) for seat in targets
    ):
        raise ValueError("open-mode target seat is outside the hand axes")
    if not np.isfinite(zero_reach_value):
        raise ValueError("zero-reach fallback must be finite")

    factors, identity = _prepare_mode_factors(train.shape, mode_factors)
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
    left_vectors, right_vectors = _tt_half_vectors(train, topology.base)
    middle_rank = left_vectors.shape[1]
    if right_vectors.shape[1] != middle_rank:
        raise AssertionError("open-mode TT half ranks differ")

    requested = set(targets)
    results: dict[int, OpenModeHandValues] = {}
    works: list[OpenModeDirectionalWork] = []
    left_targets = tuple(seat for seat in topology.base.left.seats if seat in requested)
    if left_targets:
        values, work = _contract_direction(
            workspace=workspace,
            direction="right_to_left",
            query_half=topology.base.left,
            source_half=topology.base.right,
            query_products=left_products,
            source_products=right_products,
            query_vectors=left_vectors,
            source_vectors=right_vectors,
            source_incidence_ids=topology.base.right_incidence_ids,
            query_incidence_ids=topology.base.left_query_ids,
            query_incidence_signs=topology.base.left_query_signs,
            incidence_entries=topology.base.incidence_entries,
            cached_denominator_incidence=(
                base.right_component_incidence if identity else None
            ),
            targets=left_targets,
            zero_reach_value=float(zero_reach_value),
        )
        results.update(values)
        works.append(work)

    right_targets = tuple(
        seat for seat in topology.base.right.seats if seat in requested
    )
    if right_targets:
        values, work = _contract_direction(
            workspace=workspace,
            direction="left_to_right",
            query_half=topology.base.right,
            source_half=topology.base.left,
            query_products=right_products,
            source_products=left_products,
            query_vectors=right_vectors,
            source_vectors=left_vectors,
            source_incidence_ids=topology.left_incidence_ids,
            query_incidence_ids=topology.right_query_ids,
            query_incidence_signs=topology.right_query_signs,
            incidence_entries=topology.reverse_incidence_entries,
            cached_denominator_incidence=(
                workspace.left_component_incidence if identity else None
            ),
            targets=right_targets,
            zero_reach_value=float(zero_reach_value),
        )
        results.update(values)
        works.append(work)

    ordered_results = tuple(results[seat] for seat in targets)
    result_bytes = sum(
        target.unnormalized_numerators.nbytes
        + target.unnormalized_reaches.nbytes
        + target.root_normalized_numerators.nbytes
        + target.root_normalized_reaches.nbytes
        + target.reached_hand_distribution.nbytes
        + target.conditional_values.nbytes
        + target.positive_reach.nbytes
        for target in ordered_results
    )
    half_bytes = left_vectors.nbytes + right_vectors.nbytes
    peak_direction = max(
        (
            work.operator_static_numeric_bytes
            + work.estimated_peak_scratch_numeric_bytes
            for work in works
        ),
        default=0,
    )
    return OpenModeFactorTTContraction(
        targets=ordered_results,
        directions=tuple(works),
        target_seats=targets,
        mode_factors_are_identity=identity,
        middle_rank=middle_rank,
        half_vector_numeric_bytes=half_bytes,
        topology_numeric_bytes=topology.numeric_bytes,
        belief_workspace_numeric_bytes=workspace.numeric_bytes,
        tt_storage_bytes=train.storage_bytes,
        result_numeric_bytes=result_bytes,
        estimated_peak_total_numeric_bytes=(
            topology.numeric_bytes
            + workspace.numeric_bytes
            + train.storage_bytes
            + half_bytes
            + peak_direction
            + result_bytes
        ),
    )


def _contract_batch_direction(
    *,
    workspace: OpenModeFactorTTWorkspace,
    direction: str,
    query_half: CardHalfTopology,
    source_half: CardHalfTopology,
    query_products: FloatArray,
    source_products: FloatArray,
    query_vectors: tuple[FloatArray, ...],
    source_vectors: tuple[FloatArray, ...],
    source_incidence_ids: IntArray,
    query_incidence_ids: IntArray,
    query_incidence_signs: SignArray,
    incidence_entries: int,
    cached_denominator_incidence: FloatArray | None,
    targets: tuple[int, ...],
    zero_reach_value: float,
    maximum_feature_width_per_batch: int,
) -> tuple[list[dict[int, OpenModeHandValues]], OpenModeBatchDirectionalWork]:
    components = workspace.component_count
    middle_ranks = tuple(values.shape[1] for values in source_vectors)
    if len(query_vectors) != len(source_vectors) or any(
        query.shape[1] != rank
        for query, rank in zip(query_vectors, middle_ranks, strict=True)
    ):
        raise AssertionError("batched directional TT ranks differ")
    maximum_rank_per_slice = max(
        1,
        maximum_feature_width_per_batch // components,
    )
    pieces: list[tuple[int, int, int]] = []
    for train_index, rank in enumerate(middle_ranks):
        for start in range(0, rank, maximum_rank_per_slice):
            pieces.append((train_index, start, min(start + maximum_rank_per_slice, rank)))
    batches: list[tuple[tuple[int, int, int], ...]] = []
    current: list[tuple[int, int, int]] = []
    current_width = 0
    for piece in pieces:
        width = components * (piece[2] - piece[1])
        if current and current_width + width > maximum_feature_width_per_batch:
            batches.append(tuple(current))
            current = []
            current_width = 0
        current.append(piece)
        current_width += width
    if current:
        batches.append(tuple(current))

    denominator_cached = cached_denominator_incidence is not None
    denominator_incidence = (
        cached_denominator_incidence
        if denominator_cached
        else _accumulate_incidence(
            source_products,
            source_incidence_ids,
            incidence_entries,
        )
    )
    if denominator_incidence is None:
        raise AssertionError("batched denominator incidence was not constructed")
    denominator_records = np.empty(query_half.records, dtype=np.float64)
    denominator_scale = max(
        1.0,
        float(np.max(np.abs(denominator_incidence[:-1]))),
    )
    chunk_records = workspace.base.query_chunk_records
    maximum_denominator_query_scratch = 0
    for start in range(0, query_half.records, chunk_records):
        stop = min(start + chunk_records, query_half.records)
        compatible_mass = _query_incidence(
            denominator_incidence,
            query_incidence_ids[start:stop],
            query_incidence_signs[start:stop],
        )
        minimum = float(np.min(compatible_mass))
        if minimum < -1e-11 * denominator_scale:
            raise ArithmeticError(
                "open-mode inclusion-exclusion produced negative reach mass"
            )
        if minimum < 0.0:
            compatible_mass = np.maximum(compatible_mass, 0.0)
        denominator_records[start:stop] = np.einsum(
            "k,qk,qk->q",
            workspace.base.mixture_weights,
            query_products[start:stop],
            compatible_mass,
            optimize=True,
        )
        maximum_denominator_query_scratch = max(
            maximum_denominator_query_scratch,
            compatible_mass.nbytes
            + (stop - start)
            * query_incidence_ids.shape[1]
            * components
            * np.dtype(np.float64).itemsize,
        )
    negative = float(np.min(denominator_records))
    record_scale = max(1.0, float(np.max(np.abs(denominator_records))))
    if negative < -1e-11 * record_scale:
        raise ArithmeticError("open-mode query produced negative record reach")
    if negative < 0.0:
        denominator_records = np.maximum(denominator_records, 0.0)

    numerator_records = tuple(
        np.zeros(query_half.records, dtype=np.float64) for _ in source_vectors
    )
    maximum_batch_scratch = maximum_denominator_query_scratch
    maximum_observed_width = 0
    subset_count = source_incidence_ids.shape[1]
    query_subset_count = query_incidence_ids.shape[1]
    for batch in batches:
        widths = tuple(
            components * (stop - start) for _, start, stop in batch
        )
        batch_width = sum(widths)
        maximum_observed_width = max(maximum_observed_width, batch_width)
        source_features = np.ascontiguousarray(
            np.concatenate(
                tuple(
                    (
                        source_products[:, :, None]
                        * source_vectors[train_index][:, None, start:stop]
                    ).reshape(source_half.records, width)
                    for (train_index, start, stop), width in zip(
                        batch, widths, strict=True
                    )
                ),
                axis=1,
            ),
            dtype=np.float64,
        )
        value_incidence = _accumulate_incidence(
            source_features,
            source_incidence_ids,
            incidence_entries,
        )
        for query_start in range(0, query_half.records, chunk_records):
            query_stop = min(query_start + chunk_records, query_half.records)
            compatible = _query_incidence(
                value_incidence,
                query_incidence_ids[query_start:query_stop],
                query_incidence_signs[query_start:query_stop],
            )
            offset = 0
            for (train_index, rank_start, rank_stop), width in zip(
                batch, widths, strict=True
            ):
                rank = rank_stop - rank_start
                block = compatible[:, offset : offset + width].reshape(
                    query_stop - query_start,
                    components,
                    rank,
                )
                numerator_records[train_index][query_start:query_stop] += np.einsum(
                    "k,qk,qkr,qr->q",
                    workspace.base.mixture_weights,
                    query_products[query_start:query_stop],
                    block,
                    query_vectors[train_index][
                        query_start:query_stop, rank_start:rank_stop
                    ],
                    optimize=True,
                )
                offset += width
            query_count = query_stop - query_start
            maximum_batch_scratch = max(
                maximum_batch_scratch,
                source_features.nbytes
                + value_incidence.nbytes
                + compatible.nbytes
                + query_count
                * query_subset_count
                * batch_width
                * np.dtype(np.float64).itemsize,
            )

    total_reach = fsum(float(value) for value in denominator_records)
    if total_reach < 0.0:
        raise ArithmeticError("open-mode total reach became negative")
    results: list[dict[int, OpenModeHandValues]] = []
    for train_records in numerator_records:
        total_numerator = fsum(float(value) for value in train_records)
        train_results = {}
        for target in targets:
            depth = query_half.seats.index(target)
            hand_count = workspace.topology.base.hand_counts[target]
            indices = query_half.indices[:, depth]
            numerators = np.bincount(
                indices,
                weights=train_records,
                minlength=hand_count,
            ).astype(np.float64, copy=False)
            reaches = np.bincount(
                indices,
                weights=denominator_records,
                minlength=hand_count,
            ).astype(np.float64, copy=False)
            train_results[target] = _hand_values(
                workspace=workspace,
                target=target,
                numerators=numerators,
                reaches=reaches,
                total_numerator=total_numerator,
                total_reach=total_reach,
                zero_reach_value=zero_reach_value,
            )
        results.append(train_results)

    total_rank = sum(middle_ranks)
    total_width = components * total_rank
    denominator_accumulation = (
        0
        if denominator_cached
        else source_half.records * subset_count * components
    )
    work = OpenModeBatchDirectionalWork(
        direction=direction,
        query_seats=targets,
        trains=len(source_vectors),
        source_records=source_half.records,
        query_records=query_half.records,
        source_subset_count=subset_count,
        query_subset_count=query_subset_count,
        incidence_entries=incidence_entries,
        middle_ranks=middle_ranks,
        total_middle_rank=total_rank,
        total_value_feature_width=total_width,
        maximum_value_feature_width_per_batch=maximum_feature_width_per_batch,
        maximum_observed_batch_feature_width=maximum_observed_width,
        rank_slices=len(pieces),
        batches=len(batches),
        denominator_feature_width=components,
        denominator_incidence_cached=denominator_cached,
        value_incidence_feature_updates=(
            source_half.records * subset_count * total_width
        ),
        denominator_incidence_feature_updates=denominator_accumulation,
        value_query_feature_terms=(
            query_half.records * query_subset_count * total_width
        ),
        denominator_query_feature_terms=(
            query_half.records * query_subset_count * components
        ),
        estimated_peak_batch_scratch_numeric_bytes=(
            maximum_batch_scratch
            + denominator_records.nbytes
            + sum(values.nbytes for values in numerator_records)
            + (0 if denominator_cached else denominator_incidence.nbytes)
        ),
    )
    return results, work


def _contract_direction(
    *,
    workspace: OpenModeFactorTTWorkspace,
    direction: str,
    query_half: CardHalfTopology,
    source_half: CardHalfTopology,
    query_products: FloatArray,
    source_products: FloatArray,
    query_vectors: FloatArray,
    source_vectors: FloatArray,
    source_incidence_ids: IntArray,
    query_incidence_ids: IntArray,
    query_incidence_signs: SignArray,
    incidence_entries: int,
    cached_denominator_incidence: FloatArray | None,
    targets: tuple[int, ...],
    zero_reach_value: float,
) -> tuple[dict[int, OpenModeHandValues], OpenModeDirectionalWork]:
    components = workspace.component_count
    rank = source_vectors.shape[1]
    if query_vectors.shape[1] != rank:
        raise AssertionError("directional TT ranks differ")
    value_width = components * rank
    source_features = np.ascontiguousarray(
        (
            source_products[:, :, None]
            * source_vectors[:, None, :]
        ).reshape(source_half.records, value_width),
        dtype=np.float64,
    )
    value_incidence = _accumulate_incidence(
        source_features,
        source_incidence_ids,
        incidence_entries,
    )
    denominator_cached = cached_denominator_incidence is not None
    denominator_incidence = (
        cached_denominator_incidence
        if denominator_cached
        else _accumulate_incidence(
            source_products,
            source_incidence_ids,
            incidence_entries,
        )
    )
    if denominator_incidence is None:
        raise AssertionError("denominator incidence was not constructed")

    numerator_records = np.empty(query_half.records, dtype=np.float64)
    denominator_records = np.empty(query_half.records, dtype=np.float64)
    maximum_query_scratch = 0
    denominator_scale = max(
        1.0,
        float(np.max(np.abs(denominator_incidence[:-1]))),
    )
    chunk_records = workspace.base.query_chunk_records
    for start in range(0, query_half.records, chunk_records):
        stop = min(start + chunk_records, query_half.records)
        compatible_mass = _query_incidence(
            denominator_incidence,
            query_incidence_ids[start:stop],
            query_incidence_signs[start:stop],
        )
        minimum = float(np.min(compatible_mass))
        if minimum < -1e-11 * denominator_scale:
            raise ArithmeticError(
                "open-mode inclusion-exclusion produced negative reach mass"
            )
        if minimum < 0.0:
            compatible_mass = np.maximum(compatible_mass, 0.0)
        compatible_value = _query_incidence(
            value_incidence,
            query_incidence_ids[start:stop],
            query_incidence_signs[start:stop],
        ).reshape(stop - start, components, rank)
        denominator_records[start:stop] = np.einsum(
            "k,qk,qk->q",
            workspace.base.mixture_weights,
            query_products[start:stop],
            compatible_mass,
            optimize=True,
        )
        numerator_records[start:stop] = np.einsum(
            "k,qk,qkr,qr->q",
            workspace.base.mixture_weights,
            query_products[start:stop],
            compatible_value,
            query_vectors[start:stop],
            optimize=True,
        )
        query_count = stop - start
        query_subsets = query_incidence_ids.shape[1]
        maximum_query_scratch = max(
            maximum_query_scratch,
            query_count
            * query_subsets
            * max(value_width, components)
            * np.dtype(np.float64).itemsize
            + compatible_mass.nbytes
            + compatible_value.nbytes,
        )

    negative = float(np.min(denominator_records))
    record_scale = max(1.0, float(np.max(np.abs(denominator_records))))
    if negative < -1e-11 * record_scale:
        raise ArithmeticError("open-mode query produced negative record reach")
    if negative < 0.0:
        denominator_records = np.maximum(denominator_records, 0.0)
    total_numerator = fsum(float(value) for value in numerator_records)
    total_reach = fsum(float(value) for value in denominator_records)
    if total_reach < 0.0:
        raise ArithmeticError("open-mode total reach became negative")

    results = {}
    for target in targets:
        depth = query_half.seats.index(target)
        hand_count = workspace.topology.base.hand_counts[target]
        indices = query_half.indices[:, depth]
        numerators = np.bincount(
            indices,
            weights=numerator_records,
            minlength=hand_count,
        ).astype(np.float64, copy=False)
        reaches = np.bincount(
            indices,
            weights=denominator_records,
            minlength=hand_count,
        ).astype(np.float64, copy=False)
        if len(numerators) != hand_count or len(reaches) != hand_count:
            raise AssertionError("open-mode grouped vector has the wrong hand axis")
        positive = reaches > 0.0
        conditional = np.full(hand_count, zero_reach_value, dtype=np.float64)
        np.divide(numerators, reaches, out=conditional, where=positive)
        distribution = np.zeros(hand_count, dtype=np.float64)
        if total_reach > 0.0:
            distribution = reaches / total_reach
        results[target] = OpenModeHandValues(
            target_seat=target,
            unnormalized_numerators=_readonly(numerators, np.float64),
            unnormalized_reaches=_readonly(reaches, np.float64),
            root_normalized_numerators=_readonly(
                numerators / workspace.base.partition,
                np.float64,
            ),
            root_normalized_reaches=_readonly(
                reaches / workspace.base.partition,
                np.float64,
            ),
            reached_hand_distribution=_readonly(distribution, np.float64),
            conditional_values=_readonly(conditional, np.float64),
            positive_reach=_readonly(positive, np.bool_),
            total_unnormalized_numerator=total_numerator,
            total_unnormalized_reach=total_reach,
            total_root_reach_probability=(
                total_reach / workspace.base.partition
            ),
            reach_conditioned_expectation=(
                total_numerator / total_reach if total_reach > 0.0 else None
            ),
            zero_reach_hands=int(np.count_nonzero(~positive)),
        )

    subset_count = source_incidence_ids.shape[1]
    query_subset_count = query_incidence_ids.shape[1]
    denominator_static = (
        0 if denominator_cached else denominator_incidence.nbytes
    )
    operator_static = (
        source_features.nbytes
        + value_incidence.nbytes
        + denominator_static
        + numerator_records.nbytes
        + denominator_records.nbytes
    )
    accumulation_scratch = (
        source_half.records
        * subset_count
        * max(value_width, components)
        * np.dtype(np.float64).itemsize
        + (incidence_entries + 1)
        * max(value_width, components)
        * np.dtype(np.float64).itemsize
    )
    work = OpenModeDirectionalWork(
        direction=direction,
        query_seats=targets,
        source_records=source_half.records,
        query_records=query_half.records,
        source_subset_count=subset_count,
        query_subset_count=query_subset_count,
        incidence_entries=incidence_entries,
        middle_rank=rank,
        value_feature_width=value_width,
        denominator_feature_width=components,
        denominator_incidence_cached=denominator_cached,
        value_incidence_feature_updates=(
            source_half.records * subset_count * value_width
        ),
        denominator_incidence_feature_updates=(
            0
            if denominator_cached
            else source_half.records * subset_count * components
        ),
        value_query_feature_terms=(
            query_half.records * query_subset_count * value_width
        ),
        denominator_query_feature_terms=(
            query_half.records * query_subset_count * components
        ),
        operator_static_numeric_bytes=operator_static,
        estimated_peak_scratch_numeric_bytes=max(
            accumulation_scratch,
            maximum_query_scratch,
        ),
    )
    return results, work


def _hand_values(
    *,
    workspace: OpenModeFactorTTWorkspace,
    target: int,
    numerators: FloatArray,
    reaches: FloatArray,
    total_numerator: float,
    total_reach: float,
    zero_reach_value: float,
) -> OpenModeHandValues:
    hand_count = workspace.topology.base.hand_counts[target]
    if len(numerators) != hand_count or len(reaches) != hand_count:
        raise AssertionError("open-mode grouped vector has the wrong hand axis")
    positive = reaches > 0.0
    conditional = np.full(hand_count, zero_reach_value, dtype=np.float64)
    np.divide(numerators, reaches, out=conditional, where=positive)
    distribution = np.zeros(hand_count, dtype=np.float64)
    if total_reach > 0.0:
        distribution = reaches / total_reach
    return OpenModeHandValues(
        target_seat=target,
        unnormalized_numerators=_readonly(numerators, np.float64),
        unnormalized_reaches=_readonly(reaches, np.float64),
        root_normalized_numerators=_readonly(
            numerators / workspace.base.partition,
            np.float64,
        ),
        root_normalized_reaches=_readonly(
            reaches / workspace.base.partition,
            np.float64,
        ),
        reached_hand_distribution=_readonly(distribution, np.float64),
        conditional_values=_readonly(conditional, np.float64),
        positive_reach=_readonly(positive, np.bool_),
        total_unnormalized_numerator=total_numerator,
        total_unnormalized_reach=total_reach,
        total_root_reach_probability=(
            total_reach / workspace.base.partition
        ),
        reach_conditioned_expectation=(
            total_numerator / total_reach if total_reach > 0.0 else None
        ),
        zero_reach_hands=int(np.count_nonzero(~positive)),
    )


def _compile_direction(
    *,
    source: CardHalfTopology,
    query: CardHalfTopology,
) -> tuple[IntArray, IntArray, SignArray, int]:
    source_subset_count = 1 << (2 * len(source.seats))
    query_subset_count = 1 << (2 * len(query.seats))
    keys: set[int] = set()
    source_subsets = []
    for supplied in source.masks:
        subsets = _subsets(int(supplied))
        if len(subsets) != source_subset_count:
            raise AssertionError("source half assignment does not contain distinct cards")
        source_subsets.append(subsets)
        keys.update(subsets)
    ordered = tuple(sorted(keys))
    if len(ordered) >= np.iinfo(np.int32).max:
        raise OverflowError("reverse incidence topology exceeds Int32 IDs")
    key_to_id = {key: index for index, key in enumerate(ordered)}
    source_ids = np.empty(
        (source.records, source_subset_count),
        dtype=np.int32,
        order="C",
    )
    for record, subsets in enumerate(source_subsets):
        source_ids[record] = tuple(key_to_id[subset] for subset in subsets)
    query_ids = np.empty(
        (query.records, query_subset_count),
        dtype=np.int32,
        order="C",
    )
    query_signs = np.empty_like(query_ids, dtype=np.int8)
    for record, supplied in enumerate(query.masks):
        subsets = _subsets(int(supplied))
        if len(subsets) != query_subset_count:
            raise AssertionError("query half assignment does not contain distinct cards")
        query_ids[record] = tuple(key_to_id.get(subset, -1) for subset in subsets)
        query_signs[record] = tuple(
            -1 if subset.bit_count() % 2 else 1 for subset in subsets
        )
    for values in (source_ids, query_ids, query_signs):
        values.flags.writeable = False
    return source_ids, query_ids, query_signs, len(ordered)


def _prepare_mode_factors(
    shape: tuple[int, ...],
    supplied: tuple[object, ...] | None,
) -> tuple[tuple[FloatArray, ...], bool]:
    if supplied is None:
        return (
            tuple(np.ones(size, dtype=np.float64) for size in shape),
            True,
        )
    if len(supplied) != len(shape):
        raise ValueError("open-mode reach requires one factor per hand mode")
    factors = []
    identity = True
    for size, values in zip(shape, supplied, strict=True):
        factor = np.ascontiguousarray(values, dtype=np.float64)
        if factor.shape != (size,) or not np.all(np.isfinite(factor)):
            raise ValueError("open-mode reach factor is invalid")
        if np.any(factor < 0.0):
            raise ValueError("open-mode reach factors must be nonnegative")
        identity = identity and bool(np.all(factor == 1.0))
        factors.append(factor)
    return tuple(factors), identity


def _weighted_half_products(
    base: FloatArray,
    half: CardHalfTopology,
    factors: tuple[FloatArray, ...],
    *,
    identity: bool,
) -> FloatArray:
    if identity:
        return base
    values = np.array(base, dtype=np.float64, order="C", copy=True)
    for depth, seat in enumerate(half.seats):
        values *= factors[seat][half.indices[:, depth], None]
    return np.ascontiguousarray(values, dtype=np.float64)


def _subsets(mask: int) -> tuple[int, ...]:
    result = []
    subset = mask
    while True:
        result.append(subset)
        if subset == 0:
            break
        subset = (subset - 1) & mask
    return tuple(result)


def _readonly(values: object, dtype: object) -> NDArray[np.generic]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result
