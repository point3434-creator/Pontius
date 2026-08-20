"""Batch target-omitted terminal leaves with heterogeneous unary factors.

Each leaf has its own public-path policy factors and often reuses a payoff
automaton.  The fixed card-incidence operators are nevertheless identical.
Packing mass and value features from several leaves into one sparse-dense
multiply removes the per-leaf library-call overhead without changing the leaf
adjoint algebra.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
import time
from typing import Any

import numpy as np

from .open_mode_factor_tt import (
    OpenModeFactorTTWorkspace,
    OpenModeHandValues,
    _hand_values,
    _prepare_mode_factors,
    _weighted_half_products,
)
from .open_mode_showdown import _automaton_half_vectors
from .sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
)
from .structured_showdown_automaton import StructuredShowdownAutomaton


@dataclass(frozen=True, slots=True)
class HeterogeneousLeafTerm:
    key: int
    automaton: StructuredShowdownAutomaton
    mode_factors: tuple[np.ndarray, ...]


@dataclass(frozen=True, slots=True)
class HeterogeneousLeafWork:
    target_seat: int
    direction: str
    operator_backend: str
    terms: int
    unique_automata: int
    total_middle_rank: int
    maximum_middle_rank: int
    total_feature_width: int
    batches: int
    maximum_batch_feature_width: int
    product_prepare_ms: float
    half_vector_prepare_ms: float
    source_feature_ms: float
    sparse_accumulate_ms: float
    sparse_query_ms: float
    operator_wall_ms: float
    host_to_device_ms: float
    gpu_kernel_ms: float
    device_to_host_ms: float
    maximum_gpu_pool_used_bytes: int
    maximum_gpu_pool_total_bytes: int
    query_fold_ms: float
    hand_fold_ms: float
    sparse_operator_numeric_bytes: int
    prepared_product_numeric_bytes: int
    half_vector_numeric_bytes: int
    estimated_peak_scratch_numeric_bytes: int
    estimated_peak_total_numeric_bytes: int


@dataclass(frozen=True, slots=True)
class HeterogeneousLeafContraction:
    values: tuple[tuple[int, OpenModeHandValues], ...]
    work: HeterogeneousLeafWork

    def for_key(self, key: int) -> OpenModeHandValues:
        for supplied, values in self.values:
            if supplied == key:
                return values
        raise KeyError(f"heterogeneous leaf {key} was not requested")


def contract_heterogeneous_leaf_terms(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    terms: tuple[HeterogeneousLeafTerm, ...],
    *,
    target_seat: int,
    maximum_feature_width_per_batch: int = 384,
    zero_reach_value: float = 0.0,
    cupy_sparse: Any | None = None,
) -> HeterogeneousLeafContraction:
    """Contract many differently weighted terminal leaves for one open seat."""

    if not terms:
        raise ValueError("heterogeneous leaf contraction requires at least one term")
    if sparse.topology is not workspace.topology:
        raise ValueError("heterogeneous leaf sparse topology and workspace differ")
    if cupy_sparse is not None and cupy_sparse.cpu is not sparse:
        raise ValueError("heterogeneous CuPy operators belong to another CPU topology")
    shape = workspace.topology.base.hand_counts
    players = len(shape)
    if isinstance(target_seat, bool) or target_seat not in range(players):
        raise ValueError("heterogeneous leaf target is outside the hand axes")
    if len({term.key for term in terms}) != len(terms):
        raise ValueError("heterogeneous leaf keys must be unique")
    if any(term.automaton.shape != shape for term in terms):
        raise ValueError("heterogeneous leaf automaton axes differ from workspace")
    if not np.isfinite(zero_reach_value):
        raise ValueError("heterogeneous leaf zero-reach value must be finite")
    components = workspace.component_count
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch < components
    ):
        raise ValueError("heterogeneous leaf feature width is too small")

    topology = workspace.topology.base
    if target_seat in topology.left.seats:
        direction = "right_to_left"
        operator = sparse.right_to_left
        query_half = topology.left
        source_half = topology.right
        base_query_products = workspace.base.left_component_products
        base_source_products = workspace.base.right_component_products
        gpu_operator = None if cupy_sparse is None else cupy_sparse.right_to_left
    else:
        direction = "left_to_right"
        operator = sparse.left_to_right
        query_half = topology.right
        source_half = topology.left
        base_query_products = workspace.base.right_component_products
        base_source_products = workspace.base.left_component_products
        gpu_operator = None if cupy_sparse is None else cupy_sparse.left_to_right

    product_started = time.perf_counter()
    products = []
    for term in terms:
        factors, _ = _prepare_mode_factors(shape, term.mode_factors)
        products.append(
            (
                _weighted_half_products(
                    base_query_products,
                    query_half,
                    factors,
                    identity=False,
                ),
                _weighted_half_products(
                    base_source_products,
                    source_half,
                    factors,
                    identity=False,
                ),
            )
        )
    product_prepare_ms = (time.perf_counter() - product_started) * 1000.0

    half_started = time.perf_counter()
    cached_halves: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    halves = []
    for term in terms:
        retained = cached_halves.get(id(term.automaton))
        if retained is None:
            retained = _automaton_half_vectors(term.automaton, workspace)
            cached_halves[id(term.automaton)] = retained
        query_vector, source_vector = (
            retained if direction == "right_to_left" else (retained[1], retained[0])
        )
        halves.append((query_vector, source_vector))
    half_prepare_ms = (time.perf_counter() - half_started) * 1000.0

    pieces = _feature_pieces(
        tuple(source.shape[1] for _, source in halves),
        components=components,
        maximum_width=maximum_feature_width_per_batch,
    )
    batches = _pack_pieces(
        pieces,
        components=components,
        maximum_width=maximum_feature_width_per_batch,
    )
    numerator_records = [
        np.zeros(query_half.records, dtype=np.float64) for _ in terms
    ]
    reach_records = [np.zeros(query_half.records, dtype=np.float64) for _ in terms]
    source_feature_ms = 0.0
    accumulate_ms = 0.0
    query_ms = 0.0
    operator_wall_ms = 0.0
    host_to_device_ms = 0.0
    gpu_kernel_ms = 0.0
    device_to_host_ms = 0.0
    maximum_gpu_used = 0
    maximum_gpu_total = 0
    fold_ms = 0.0
    maximum_scratch = 0
    maximum_batch_width = 0

    for batch in batches:
        started = time.perf_counter()
        columns = []
        widths = []
        for term_index, kind, start, stop in batch:
            _, source_products = products[term_index]
            if kind == "mass":
                feature = source_products
            else:
                source_vector = halves[term_index][1]
                rank = stop - start
                feature = (
                    source_products[:, :, None]
                    * source_vector[:, None, start:stop]
                ).reshape(source_half.records, components * rank)
            retained = np.ascontiguousarray(feature, dtype=np.float64)
            columns.append(retained)
            widths.append(retained.shape[1])
        source_features = np.ascontiguousarray(
            np.concatenate(tuple(columns), axis=1),
            dtype=np.float64,
        )
        source_feature_ms += (time.perf_counter() - started) * 1000.0
        maximum_batch_width = max(maximum_batch_width, source_features.shape[1])

        if gpu_operator is None:
            started = time.perf_counter()
            incidence = operator.accumulate(source_features)
            accumulated = (time.perf_counter() - started) * 1000.0
            accumulate_ms += accumulated
            started = time.perf_counter()
            compatible = operator.query(incidence)
            queried = (time.perf_counter() - started) * 1000.0
            query_ms += queried
            operator_wall_ms += accumulated + queried
            operator_scratch = incidence.nbytes
        else:
            compatible, gpu_work = gpu_operator.transform(source_features)
            operator_wall_ms += gpu_work.wall_ms
            host_to_device_ms += gpu_work.host_to_device_ms
            gpu_kernel_ms += gpu_work.kernel_ms
            device_to_host_ms += gpu_work.device_to_host_ms
            maximum_gpu_used = max(maximum_gpu_used, gpu_work.pool_used_bytes)
            maximum_gpu_total = max(maximum_gpu_total, gpu_work.pool_total_bytes)
            operator_scratch = 0

        started = time.perf_counter()
        offset = 0
        for piece, width in zip(batch, widths, strict=True):
            term_index, kind, start, stop = piece
            query_products, _ = products[term_index]
            block = compatible[:, offset : offset + width]
            if kind == "mass":
                folded = np.einsum(
                    "k,qk,qk->q",
                    workspace.base.mixture_weights,
                    query_products,
                    block,
                    optimize=True,
                )
                scale = max(1.0, float(np.max(np.abs(folded))))
                minimum = float(np.min(folded))
                if minimum < -1e-10 * scale:
                    raise ArithmeticError("heterogeneous leaf produced negative reach")
                if minimum < 0.0:
                    folded = np.maximum(folded, 0.0)
                reach_records[term_index] += folded
            else:
                rank = stop - start
                query_vector = halves[term_index][0]
                numerator_records[term_index] += np.einsum(
                    "k,qk,qkr,qr->q",
                    workspace.base.mixture_weights,
                    query_products,
                    block.reshape(query_half.records, components, rank),
                    query_vector[:, start:stop],
                    optimize=True,
                )
            offset += width
        fold_ms += (time.perf_counter() - started) * 1000.0
        maximum_scratch = max(
            maximum_scratch,
            source_features.nbytes + operator_scratch + compatible.nbytes,
        )

    hand_started = time.perf_counter()
    depth = query_half.seats.index(target_seat)
    indices = query_half.indices[:, depth]
    results = []
    for term, numerators_by_record, reaches_by_record in zip(
        terms,
        numerator_records,
        reach_records,
        strict=True,
    ):
        numerators = np.bincount(
            indices,
            weights=numerators_by_record,
            minlength=shape[target_seat],
        ).astype(np.float64, copy=False)
        reaches = np.bincount(
            indices,
            weights=reaches_by_record,
            minlength=shape[target_seat],
        ).astype(np.float64, copy=False)
        results.append(
            (
                term.key,
                _hand_values(
                    workspace=workspace,
                    target=target_seat,
                    numerators=numerators,
                    reaches=reaches,
                    total_numerator=fsum(float(value) for value in numerators_by_record),
                    total_reach=fsum(float(value) for value in reaches_by_record),
                    zero_reach_value=zero_reach_value,
                ),
            )
        )
    hand_ms = (time.perf_counter() - hand_started) * 1000.0

    product_bytes = sum(
        query.nbytes + source.nbytes for query, source in products
    )
    half_bytes = sum(left.nbytes + right.nbytes for left, right in cached_halves.values())
    record_bytes = sum(
        values.nbytes for values in (*numerator_records, *reach_records)
    )
    ranks = tuple(source.shape[1] for _, source in halves)
    unique_automaton_bytes = sum(
        term.automaton.numeric_bytes
        for term in {id(term.automaton): term for term in terms}.values()
    )
    result_bytes = sum(
        values.unnormalized_numerators.nbytes
        + values.unnormalized_reaches.nbytes
        + values.root_normalized_numerators.nbytes
        + values.root_normalized_reaches.nbytes
        + values.reached_hand_distribution.nbytes
        + values.conditional_values.nbytes
        + values.positive_reach.nbytes
        for _, values in results
    )
    peak_scratch = product_bytes + half_bytes + record_bytes + maximum_scratch
    return HeterogeneousLeafContraction(
        values=tuple(results),
        work=HeterogeneousLeafWork(
            target_seat=target_seat,
            direction=direction,
            operator_backend="cpu_scipy" if gpu_operator is None else "gpu_cupy",
            terms=len(terms),
            unique_automata=len(cached_halves),
            total_middle_rank=sum(ranks),
            maximum_middle_rank=max(ranks),
            total_feature_width=components * sum(rank + 1 for rank in ranks),
            batches=len(batches),
            maximum_batch_feature_width=maximum_batch_width,
            product_prepare_ms=product_prepare_ms,
            half_vector_prepare_ms=half_prepare_ms,
            source_feature_ms=source_feature_ms,
            sparse_accumulate_ms=accumulate_ms,
            sparse_query_ms=query_ms,
            operator_wall_ms=operator_wall_ms,
            host_to_device_ms=host_to_device_ms,
            gpu_kernel_ms=gpu_kernel_ms,
            device_to_host_ms=device_to_host_ms,
            maximum_gpu_pool_used_bytes=maximum_gpu_used,
            maximum_gpu_pool_total_bytes=maximum_gpu_total,
            query_fold_ms=fold_ms,
            hand_fold_ms=hand_ms,
            sparse_operator_numeric_bytes=(
                operator.numeric_bytes
            ),
            prepared_product_numeric_bytes=product_bytes,
            half_vector_numeric_bytes=half_bytes,
            estimated_peak_scratch_numeric_bytes=peak_scratch,
            estimated_peak_total_numeric_bytes=(
                workspace.topology.numeric_bytes
                + workspace.numeric_bytes
                + sparse.numeric_bytes
                + unique_automaton_bytes
                + result_bytes
                + peak_scratch
            ),
        ),
    )


def _feature_pieces(
    ranks: tuple[int, ...],
    *,
    components: int,
    maximum_width: int,
) -> tuple[tuple[int, str, int, int], ...]:
    maximum_rank = max(1, maximum_width // components)
    result = []
    for term_index, rank in enumerate(ranks):
        result.append((term_index, "mass", 0, 1))
        for start in range(0, rank, maximum_rank):
            result.append((term_index, "value", start, min(start + maximum_rank, rank)))
    return tuple(result)


def _piece_width(piece: tuple[int, str, int, int], components: int) -> int:
    _, kind, start, stop = piece
    return components if kind == "mass" else components * (stop - start)


def _pack_pieces(
    pieces: tuple[tuple[int, str, int, int], ...],
    *,
    components: int,
    maximum_width: int,
) -> tuple[tuple[tuple[int, str, int, int], ...], ...]:
    batches = []
    current = []
    width = 0
    for piece in pieces:
        supplied = _piece_width(piece, components)
        if current and width + supplied > maximum_width:
            batches.append(tuple(current))
            current = []
            width = 0
        current.append(piece)
        width += supplied
    if current:
        batches.append(tuple(current))
    return tuple(batches)
