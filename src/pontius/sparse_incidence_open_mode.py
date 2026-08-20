"""Optional CSR backend for the fixed open-mode card-incidence operators.

The exact NumPy implementation is the dependency-free oracle.  This successor
compiles its two topology maps as sparse matrices and applies them to dense
feature blocks.  SciPy is imported lazily so the core laboratory and historical
audits retain their existing dependency and hash contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any

import numpy as np

from .factor_tt_contraction import CardHalfTopology
from .open_mode_factor_tt import (
    OpenModeFactorTTWorkspace,
    OpenModeHandValues,
    OpenModeTrainValues,
    _hand_values,
    _prepare_mode_factors,
    _weighted_half_products,
)
from .open_mode_showdown import _automaton_half_vectors
from .structured_showdown_automaton import StructuredShowdownAutomaton


@dataclass(frozen=True, slots=True)
class SparseIncidenceDirection:
    """Two fixed sparse maps: source subsets and signed compatible queries."""

    source_matrix: Any
    query_matrix: Any
    source_records: int
    query_records: int
    incidence_entries: int
    source_subset_count: int
    query_subset_count: int
    source_nnz: int
    query_nnz: int
    numeric_bytes: int
    compile_ms: float

    @classmethod
    def compile(
        cls,
        *,
        source_incidence_ids: np.ndarray,
        query_incidence_ids: np.ndarray,
        query_incidence_signs: np.ndarray,
        incidence_entries: int,
    ) -> SparseIncidenceDirection:
        try:
            from scipy.sparse import csr_matrix
        except ImportError as error:
            raise RuntimeError(
                "the optional sparse-incidence screen requires SciPy"
            ) from error
        if source_incidence_ids.ndim != 2:
            raise ValueError("sparse source incidence IDs must be a matrix")
        if (
            query_incidence_ids.ndim != 2
            or query_incidence_ids.shape != query_incidence_signs.shape
        ):
            raise ValueError("sparse query IDs and signs must be matching matrices")
        if incidence_entries <= 0:
            raise ValueError("sparse incidence entry count must be positive")
        started = time.perf_counter()
        source_records, source_subsets = source_incidence_ids.shape
        source_rows = source_incidence_ids.ravel()
        source_columns = np.repeat(
            np.arange(source_records, dtype=np.int32),
            source_subsets,
        )
        source = csr_matrix(
            (
                np.ones(len(source_rows), dtype=np.float64),
                (source_rows, source_columns),
            ),
            shape=(incidence_entries + 1, source_records),
            dtype=np.float64,
        )
        source.sum_duplicates()
        source.sort_indices()

        valid = query_incidence_ids >= 0
        query_records, query_subsets = query_incidence_ids.shape
        query_rows = np.broadcast_to(
            np.arange(query_records, dtype=np.int32)[:, None],
            query_incidence_ids.shape,
        )[valid]
        query_columns = query_incidence_ids[valid]
        query_values = query_incidence_signs[valid].astype(np.float64, copy=False)
        query = csr_matrix(
            (query_values, (query_rows, query_columns)),
            shape=(query_records, incidence_entries + 1),
            dtype=np.float64,
        )
        query.sum_duplicates()
        query.sort_indices()
        numeric_bytes = sum(
            values.nbytes
            for matrix in (source, query)
            for values in (matrix.data, matrix.indices, matrix.indptr)
        )
        return cls(
            source_matrix=source,
            query_matrix=query,
            source_records=source_records,
            query_records=query_records,
            incidence_entries=incidence_entries,
            source_subset_count=source_subsets,
            query_subset_count=query_subsets,
            source_nnz=int(source.nnz),
            query_nnz=int(query.nnz),
            numeric_bytes=numeric_bytes,
            compile_ms=(time.perf_counter() - started) * 1000.0,
        )

    def accumulate(self, features: np.ndarray) -> np.ndarray:
        if features.ndim != 2 or features.shape[0] != self.source_records:
            raise ValueError("sparse incidence features differ from source records")
        return np.ascontiguousarray(self.source_matrix @ features, dtype=np.float64)

    def query(self, incidence: np.ndarray) -> np.ndarray:
        expected = self.incidence_entries + 1
        if incidence.ndim != 2 or incidence.shape[0] != expected:
            raise ValueError("sparse query table differs from incidence entries")
        return np.ascontiguousarray(self.query_matrix @ incidence, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class SparseBidirectionalIncidence:
    """Both 3/3 incidence directions compiled against one open topology."""

    topology: object
    right_to_left: SparseIncidenceDirection
    left_to_right: SparseIncidenceDirection

    @classmethod
    def compile(
        cls,
        workspace: OpenModeFactorTTWorkspace,
    ) -> SparseBidirectionalIncidence:
        topology = workspace.topology
        forward = SparseIncidenceDirection.compile(
            source_incidence_ids=topology.base.right_incidence_ids,
            query_incidence_ids=topology.base.left_query_ids,
            query_incidence_signs=topology.base.left_query_signs,
            incidence_entries=topology.base.incidence_entries,
        )
        reverse = SparseIncidenceDirection.compile(
            source_incidence_ids=topology.left_incidence_ids,
            query_incidence_ids=topology.right_query_ids,
            query_incidence_signs=topology.right_query_signs,
            incidence_entries=topology.reverse_incidence_entries,
        )
        return cls(
            topology=topology,
            right_to_left=forward,
            left_to_right=reverse,
        )

    @property
    def numeric_bytes(self) -> int:
        return self.right_to_left.numeric_bytes + self.left_to_right.numeric_bytes

    @property
    def compile_ms(self) -> float:
        return self.right_to_left.compile_ms + self.left_to_right.compile_ms


@dataclass(frozen=True, slots=True)
class SparseOpenModeDirectionalWork:
    direction: str
    query_seats: tuple[int, ...]
    middle_ranks: tuple[int, ...]
    total_feature_width: int
    rank_slices: int
    batches: int
    maximum_batch_feature_width: int
    denominator_incidence_cached: bool
    source_nnz: int
    query_nnz: int
    denominator_accumulate_ms: float
    denominator_query_ms: float
    value_accumulate_ms: float
    value_query_ms: float
    value_fold_ms: float
    estimated_peak_scratch_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class SparseOpenModeShowdownContraction:
    automata: tuple[OpenModeTrainValues, ...]
    directions: tuple[SparseOpenModeDirectionalWork, ...]
    target_seats: tuple[int, ...]
    middle_ranks: tuple[int, ...]
    total_middle_rank: int
    mode_factors_are_identity: bool
    sparse_operator_numeric_bytes: int
    sparse_operator_compile_ms: float
    half_vector_numeric_bytes: int
    referenced_automaton_numeric_bytes: int
    result_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int

    def for_automaton(self, index: int) -> OpenModeTrainValues:
        if index not in range(len(self.automata)):
            raise KeyError(f"automaton {index} was not requested")
        return self.automata[index]


def contract_sparse_open_mode_showdown_batch(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    automata: tuple[StructuredShowdownAutomaton, ...],
    *,
    target_seats: tuple[int, ...] | None = None,
    mode_factors: tuple[object, ...] | None = None,
    zero_reach_value: float = 0.0,
    maximum_feature_width_per_batch: int = 384,
) -> SparseOpenModeShowdownContraction:
    """Apply the CSR backend to direct sparse-automaton half vectors."""

    if sparse.topology is not workspace.topology:
        raise ValueError("sparse incidence operators belong to another topology")
    if not automata:
        raise ValueError("sparse open-mode batch requires at least one automaton")
    shape = workspace.topology.base.hand_counts
    if any(automaton.shape != shape for automaton in automata):
        raise ValueError("sparse automaton modes differ from open topology")
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
    half_vectors = tuple(
        _automaton_half_vectors(automaton, workspace) for automaton in automata
    )
    middle_ranks = tuple(left.shape[1] for left, _ in half_vectors)
    requested = set(targets)
    by_automaton: list[dict[int, OpenModeHandValues]] = [
        {} for _ in automata
    ]
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
            by_automaton[index].update(row)
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
    unique = {id(automaton): automaton for automaton in automata}
    automaton_bytes = sum(value.numeric_bytes for value in unique.values())
    peak_scratch = max(
        (work.estimated_peak_scratch_numeric_bytes for work in works),
        default=0,
    )
    return SparseOpenModeShowdownContraction(
        automata=results,
        directions=tuple(works),
        target_seats=targets,
        middle_ranks=middle_ranks,
        total_middle_rank=sum(middle_ranks),
        mode_factors_are_identity=identity,
        sparse_operator_numeric_bytes=sparse.numeric_bytes,
        sparse_operator_compile_ms=sparse.compile_ms,
        half_vector_numeric_bytes=half_bytes,
        referenced_automaton_numeric_bytes=automaton_bytes,
        result_numeric_bytes=result_bytes,
        estimated_peak_total_numeric_bytes=(
            workspace.topology.numeric_bytes
            + workspace.numeric_bytes
            + sparse.numeric_bytes
            + half_bytes
            + automaton_bytes
            + result_bytes
            + peak_scratch
        ),
    )


def _contract_sparse_direction(
    *,
    workspace: OpenModeFactorTTWorkspace,
    operator: SparseIncidenceDirection,
    direction: str,
    query_half: CardHalfTopology,
    source_half: CardHalfTopology,
    query_products: np.ndarray,
    source_products: np.ndarray,
    query_vectors: tuple[np.ndarray, ...],
    source_vectors: tuple[np.ndarray, ...],
    cached_denominator_incidence: np.ndarray | None,
    targets: tuple[int, ...],
    zero_reach_value: float,
    maximum_feature_width_per_batch: int,
) -> tuple[list[dict[int, OpenModeHandValues]], SparseOpenModeDirectionalWork]:
    components = workspace.component_count
    middle_ranks = tuple(vector.shape[1] for vector in source_vectors)
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
    denominator_accumulate_ms = 0.0
    if denominator_cached:
        denominator_incidence = cached_denominator_incidence
    else:
        started = time.perf_counter()
        denominator_incidence = operator.accumulate(source_products)
        denominator_accumulate_ms = (time.perf_counter() - started) * 1000.0
    if denominator_incidence is None:
        raise AssertionError("sparse denominator incidence was not constructed")
    started = time.perf_counter()
    compatible_mass = operator.query(denominator_incidence)
    denominator_query_ms = (time.perf_counter() - started) * 1000.0
    denominator_scale = max(1.0, float(np.max(np.abs(denominator_incidence[:-1]))))
    minimum = float(np.min(compatible_mass))
    if minimum < -1e-10 * denominator_scale:
        raise ArithmeticError("sparse incidence produced negative compatible mass")
    if minimum < 0.0:
        compatible_mass = np.maximum(compatible_mass, 0.0)
    denominator_records = np.einsum(
        "k,qk,qk->q",
        workspace.base.mixture_weights,
        query_products,
        compatible_mass,
        optimize=True,
    )
    record_scale = max(1.0, float(np.max(np.abs(denominator_records))))
    negative = float(np.min(denominator_records))
    if negative < -1e-10 * record_scale:
        raise ArithmeticError("sparse open-mode query produced negative reach")
    if negative < 0.0:
        denominator_records = np.maximum(denominator_records, 0.0)

    numerator_records = [
        np.zeros(query_half.records, dtype=np.float64) for _ in source_vectors
    ]
    value_accumulate_ms = 0.0
    value_query_ms = 0.0
    value_fold_ms = 0.0
    maximum_scratch = compatible_mass.nbytes + denominator_records.nbytes
    maximum_batch_width = 0
    for batch in batches:
        widths = tuple(components * (stop - start) for _, start, stop in batch)
        batch_width = sum(widths)
        maximum_batch_width = max(maximum_batch_width, batch_width)
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
        started = time.perf_counter()
        value_incidence = operator.accumulate(source_features)
        value_accumulate_ms += (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        compatible = operator.query(value_incidence)
        value_query_ms += (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        offset = 0
        for (train_index, rank_start, rank_stop), width in zip(
            batch, widths, strict=True
        ):
            rank = rank_stop - rank_start
            block = compatible[:, offset : offset + width].reshape(
                query_half.records,
                components,
                rank,
            )
            numerator_records[train_index] += np.einsum(
                "k,qk,qkr,qr->q",
                workspace.base.mixture_weights,
                query_products,
                block,
                query_vectors[train_index][:, rank_start:rank_stop],
                optimize=True,
            )
            offset += width
        value_fold_ms += (time.perf_counter() - started) * 1000.0
        maximum_scratch = max(
            maximum_scratch,
            source_features.nbytes + value_incidence.nbytes + compatible.nbytes,
        )

    total_reach = fsum(float(value) for value in denominator_records)
    results = []
    for train_records in numerator_records:
        total_numerator = fsum(float(value) for value in train_records)
        rows = {}
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
            rows[target] = _hand_values(
                workspace=workspace,
                target=target,
                numerators=numerators,
                reaches=reaches,
                total_numerator=total_numerator,
                total_reach=total_reach,
                zero_reach_value=zero_reach_value,
            )
        results.append(rows)
    work = SparseOpenModeDirectionalWork(
        direction=direction,
        query_seats=targets,
        middle_ranks=middle_ranks,
        total_feature_width=components * sum(middle_ranks),
        rank_slices=len(pieces),
        batches=len(batches),
        maximum_batch_feature_width=maximum_batch_width,
        denominator_incidence_cached=denominator_cached,
        source_nnz=operator.source_nnz,
        query_nnz=operator.query_nnz,
        denominator_accumulate_ms=denominator_accumulate_ms,
        denominator_query_ms=denominator_query_ms,
        value_accumulate_ms=value_accumulate_ms,
        value_query_ms=value_query_ms,
        value_fold_ms=value_fold_ms,
        estimated_peak_scratch_numeric_bytes=(
            maximum_scratch
            + denominator_records.nbytes
            + sum(values.nbytes for values in numerator_records)
            + (0 if denominator_cached else denominator_incidence.nbytes)
        ),
    )
    return results, work
