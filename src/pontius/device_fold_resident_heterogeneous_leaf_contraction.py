"""Additive resident leaf contraction with record-to-hand folding on the GPU.

The accepted host-fold implementation remains byte-identical. This module
copies its device pipeline and changes only the post-pipeline placement:
per-record accumulators are grouped on-device and only per-hand vectors return
to the host.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    _feature_pieces,
    _pack_pieces,
)
from .open_mode_factor_tt import OpenModeFactorTTWorkspace, _prepare_mode_factors
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .resident_record_to_hand_fold import (
    RecordToHandBackend,
    finalize_resident_record_accumulators,
    validate_record_to_hand_backend,
)
from .sparse_incidence_open_mode import SparseBidirectionalIncidence


@dataclass(frozen=True, slots=True)
class DeviceFoldResidentHeterogeneousLeafWork:
    """Attributable work with the fold placement kept explicit."""

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
    factor_prepare_ms: float
    factor_upload_ms: float
    product_generation_gpu_ms: float
    resident_pipeline_gpu_ms: float
    device_hand_fold_gpu_ms: float
    device_to_host_ms: float
    host_hand_fold_ms: float
    host_hand_finalize_ms: float
    wall_ms: float
    per_call_host_to_device_bytes: int
    per_call_device_to_host_bytes: int
    legacy_equivalent_host_to_device_bytes: int
    legacy_equivalent_device_to_host_bytes: int
    resident_belief_numeric_bytes: int
    resident_automaton_numeric_bytes: int
    per_call_device_product_bytes: int
    per_call_device_record_bytes: int
    device_fold_scratch_numeric_bytes: int
    maximum_batch_scratch_numeric_bytes: int
    estimated_peak_host_numeric_bytes: int
    maximum_gpu_pool_used_bytes: int
    maximum_gpu_pool_total_bytes: int


@dataclass(frozen=True, slots=True)
class DeviceFoldResidentHeterogeneousLeafContraction:
    values: tuple[tuple[int, Any], ...]
    work: DeviceFoldResidentHeterogeneousLeafWork

    def for_key(self, key: int) -> Any:
        for supplied, values in self.values:
            if supplied == key:
                return values
        raise KeyError(f"device-fold resident leaf {key} was not requested")


def contract_device_fold_resident_heterogeneous_leaf_terms(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    terms: tuple[HeterogeneousLeafTerm, ...],
    *,
    target_seat: int,
    belief_cache: CuPyResidentBeliefCache,
    automaton_cache: CuPyResidentAutomatonCache,
    cupy_sparse: CuPyBidirectionalIncidence,
    maximum_feature_width_per_batch: int = 384,
    zero_reach_value: float = 0.0,
    record_to_hand_backend: RecordToHandBackend = "gpu_cupy",
) -> DeviceFoldResidentHeterogeneousLeafContraction:
    """Run one resident contraction with an explicit final-fold placement."""

    wall_started = time.perf_counter()
    fold_backend = validate_record_to_hand_backend(record_to_hand_backend)
    if not terms:
        raise ValueError("device-fold resident contraction requires terms")
    if sparse.topology is not workspace.topology:
        raise ValueError("device-fold resident topology and workspace differ")
    if cupy_sparse.cpu is not sparse:
        raise ValueError("device-fold CuPy operators belong to another topology")
    if belief_cache.workspace is not workspace:
        raise ValueError("device-fold belief cache belongs to another workspace")
    if automaton_cache.topology is not workspace.topology:
        raise ValueError("device-fold automaton cache belongs to another topology")
    if automaton_cache.target_seat != target_seat:
        raise ValueError("device-fold automaton cache belongs to another target")
    shape = workspace.topology.base.hand_counts
    players = len(shape)
    if isinstance(target_seat, bool) or target_seat not in range(players):
        raise ValueError("device-fold target is outside the hand axes")
    if len({term.key for term in terms}) != len(terms):
        raise ValueError("device-fold resident keys must be unique")
    if any(term.automaton.shape != shape for term in terms):
        raise ValueError("device-fold resident automaton axes differ")
    if any(id(term.automaton) not in automaton_cache.automaton_ids for term in terms):
        raise ValueError("device-fold automaton is absent from the resident cache")
    if not np.isfinite(zero_reach_value):
        raise ValueError("device-fold zero-reach value must be finite")
    components = workspace.component_count
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch < components
    ):
        raise ValueError("device-fold feature width is too small")

    topology = workspace.topology.base
    if target_seat in topology.left.seats:
        direction = "right_to_left"
        query_half = topology.left
        source_half = topology.right
        base_query_products = belief_cache.left_component_products
        base_source_products = belief_cache.right_component_products
        query_indices = belief_cache.left_indices
        source_indices = belief_cache.right_indices
        gpu_operator = cupy_sparse.right_to_left
        ordered_halves = tuple(
            automaton_cache.half_vectors[id(term.automaton)] for term in terms
        )
    else:
        direction = "left_to_right"
        query_half = topology.right
        source_half = topology.left
        base_query_products = belief_cache.right_component_products
        base_source_products = belief_cache.left_component_products
        query_indices = belief_cache.right_indices
        source_indices = belief_cache.left_indices
        gpu_operator = cupy_sparse.left_to_right
        ordered_halves = tuple(
            tuple(reversed(automaton_cache.half_vectors[id(term.automaton)]))
            for term in terms
        )

    factor_started = time.perf_counter()
    prepared = tuple(_prepare_mode_factors(shape, term.mode_factors)[0] for term in terms)
    host_factors = tuple(
        np.ascontiguousarray(
            np.stack(tuple(row[seat] for row in prepared), axis=0),
            dtype=np.float64,
        )
        for seat in range(players)
    )
    factor_prepare_ms = (time.perf_counter() - factor_started) * 1000.0

    cp, _ = _cupy_modules()
    upload_started = time.perf_counter()
    device_factors = tuple(cp.asarray(values) for values in host_factors)
    cp.cuda.runtime.deviceSynchronize()
    factor_upload_ms = (time.perf_counter() - upload_started) * 1000.0

    ranks = tuple(source.shape[1] for _, source in ordered_halves)
    pieces = _feature_pieces(
        ranks,
        components=components,
        maximum_width=maximum_feature_width_per_batch,
    )
    batches = _pack_pieces(
        pieces,
        components=components,
        maximum_width=maximum_feature_width_per_batch,
    )

    term_count = len(terms)
    product_begin = cp.cuda.Event()
    product_end = cp.cuda.Event()
    pipeline_end = cp.cuda.Event()
    product_begin.record()
    query_products = cp.broadcast_to(
        base_query_products[None, :, :],
        (term_count, query_half.records, components),
    ).copy()
    source_products = cp.broadcast_to(
        base_source_products[None, :, :],
        (term_count, source_half.records, components),
    ).copy()
    for depth, seat in enumerate(query_half.seats):
        query_products *= device_factors[seat][:, query_indices[:, depth], None]
    for depth, seat in enumerate(source_half.seats):
        source_products *= device_factors[seat][:, source_indices[:, depth], None]
    numerator_records = cp.zeros((term_count, query_half.records), dtype=cp.float64)
    reach_records = cp.zeros((term_count, query_half.records), dtype=cp.float64)
    product_end.record()

    maximum_batch_width = 0
    maximum_scratch = 0
    legacy_h2d_bytes = 0
    legacy_d2h_bytes = 0
    for batch in batches:
        columns = []
        widths = []
        for term_index, kind, start, stop in batch:
            if kind == "mass":
                feature = source_products[term_index]
            else:
                source_vector = ordered_halves[term_index][1]
                rank = stop - start
                feature = (
                    source_products[term_index, :, :, None]
                    * source_vector[:, None, start:stop]
                ).reshape(source_half.records, components * rank)
            retained = cp.ascontiguousarray(feature, dtype=cp.float64)
            columns.append(retained)
            widths.append(int(retained.shape[1]))
        source_features = (
            columns[0]
            if len(columns) == 1
            else cp.ascontiguousarray(cp.concatenate(columns, axis=1))
        )
        batch_width = int(source_features.shape[1])
        maximum_batch_width = max(maximum_batch_width, batch_width)
        legacy_h2d_bytes += source_half.records * batch_width * 8
        legacy_d2h_bytes += query_half.records * batch_width * 8

        incidence = gpu_operator.source_matrix @ source_features
        compatible = gpu_operator.query_matrix @ incidence
        offset = 0
        for piece, width in zip(batch, widths, strict=True):
            term_index, kind, start, stop = piece
            block = compatible[:, offset : offset + width]
            if kind == "mass":
                reached = cp.einsum(
                    "k,qk,qk->q",
                    belief_cache.mixture_weights,
                    query_products[term_index],
                    block,
                    optimize=True,
                )
                reach_records[term_index] += reached
            else:
                rank = stop - start
                query_vector = ordered_halves[term_index][0]
                numerator_records[term_index] += cp.einsum(
                    "k,qk,qkr,qr->q",
                    belief_cache.mixture_weights,
                    query_products[term_index],
                    block.reshape(query_half.records, components, rank),
                    query_vector[:, start:stop],
                    optimize=True,
                )
            offset += width
        maximum_scratch = max(
            maximum_scratch,
            int(source_features.nbytes + incidence.nbytes + compatible.nbytes),
        )
    pipeline_end.record()
    pipeline_end.synchronize()
    product_generation_ms = float(cp.cuda.get_elapsed_time(product_begin, product_end))
    resident_pipeline_ms = float(cp.cuda.get_elapsed_time(product_end, pipeline_end))

    depth = query_half.seats.index(target_seat)
    folded = finalize_resident_record_accumulators(
        workspace,
        target_seat=target_seat,
        term_keys=tuple(term.key for term in terms),
        numerator_records=numerator_records,
        reach_records=reach_records,
        host_hand_indices=query_half.indices[:, depth],
        device_hand_indices=query_indices[:, depth],
        backend=fold_backend,
        zero_reach_value=zero_reach_value,
    )
    pool = cp.get_default_memory_pool()
    maximum_gpu_used = int(pool.used_bytes())
    maximum_gpu_total = int(pool.total_bytes())

    factor_bytes = sum(values.nbytes for values in host_factors)
    record_bytes = int(numerator_records.nbytes + reach_records.nbytes)
    product_bytes = int(query_products.nbytes + source_products.nbytes)
    unique_automaton_bytes = sum(
        term.automaton.numeric_bytes
        for term in {id(term.automaton): term for term in terms}.values()
    )
    estimated_host = int(
        workspace.topology.numeric_bytes
        + workspace.numeric_bytes
        + sparse.numeric_bytes
        + unique_automaton_bytes
        + factor_bytes
        + folded.device_to_host_bytes
    )
    return DeviceFoldResidentHeterogeneousLeafContraction(
        values=folded.values,
        work=DeviceFoldResidentHeterogeneousLeafWork(
            target_seat=target_seat,
            direction=direction,
            operator_backend=(
                "gpu_cupy_resident_device_fold"
                if fold_backend == "gpu_cupy"
                else "gpu_cupy_resident_host_fold_intervention"
            ),
            terms=term_count,
            unique_automata=len({id(term.automaton) for term in terms}),
            total_middle_rank=sum(ranks),
            maximum_middle_rank=max(ranks),
            total_feature_width=components * sum(rank + 1 for rank in ranks),
            batches=len(batches),
            maximum_batch_feature_width=maximum_batch_width,
            factor_prepare_ms=factor_prepare_ms,
            factor_upload_ms=factor_upload_ms,
            product_generation_gpu_ms=product_generation_ms,
            resident_pipeline_gpu_ms=resident_pipeline_ms,
            device_hand_fold_gpu_ms=folded.device_hand_fold_gpu_ms,
            device_to_host_ms=folded.device_to_host_ms,
            host_hand_fold_ms=folded.host_hand_fold_ms,
            host_hand_finalize_ms=folded.host_hand_finalize_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            per_call_host_to_device_bytes=factor_bytes,
            per_call_device_to_host_bytes=folded.device_to_host_bytes,
            legacy_equivalent_host_to_device_bytes=legacy_h2d_bytes,
            legacy_equivalent_device_to_host_bytes=legacy_d2h_bytes,
            resident_belief_numeric_bytes=belief_cache.numeric_bytes,
            resident_automaton_numeric_bytes=automaton_cache.numeric_bytes,
            per_call_device_product_bytes=product_bytes,
            per_call_device_record_bytes=record_bytes,
            device_fold_scratch_numeric_bytes=(
                folded.device_fold_scratch_numeric_bytes
            ),
            maximum_batch_scratch_numeric_bytes=maximum_scratch,
            estimated_peak_host_numeric_bytes=estimated_host,
            maximum_gpu_pool_used_bytes=maximum_gpu_used,
            maximum_gpu_pool_total_bytes=maximum_gpu_total,
        ),
    )
