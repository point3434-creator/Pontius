"""Shared-topology affine resident contraction for sized terminal leaves.

For a fixed contender set and target seat, the showdown transition machine is
independent of the selected bet amount.  Its left half is entirely topological.
Its right half is one normalized winner-share basis scaled by ``final_pot``
plus one constant column scaled by ``sunk_value``.  This module stores those
two bases once per transition topology and keeps only the two affine
coefficients per logical automaton.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from math import fsum
import time
from typing import Any, Mapping

import numpy as np

from .cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules
from .heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    _feature_pieces,
    _pack_pieces,
)
from .open_mode_factor_tt import (
    OpenModeFactorTTWorkspace,
    _hand_values,
    _prepare_mode_factors,
)
from .open_mode_showdown import _automaton_half_vectors
from .resident_heterogeneous_leaf_contraction import (
    ResidentHeterogeneousLeafContraction,
    ResidentHeterogeneousLeafWork,
)
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .structured_showdown_automaton import StructuredShowdownAutomaton


@dataclass(frozen=True, slots=True)
class CuPyAffineAutomatonHalfVectors:
    """One logical automaton referencing shared device half-vector bases."""

    topology_key: str
    left_basis: Any
    right_basis: Any
    right_coefficients: Any
    middle_rank: int


@dataclass(frozen=True, slots=True)
class CuPyAffineResidentAutomatonCache:
    """Device bases shared by amount-invariant showdown topologies."""

    topology: Any
    target_seat: int
    half_vectors: Mapping[int, CuPyAffineAutomatonHalfVectors]
    automaton_ids: frozenset[int]
    unique_automata: int
    shared_topologies: int
    total_middle_rank: int
    stored_topology_middle_rank: int
    maximum_middle_rank: int
    half_prepare_ms: float
    upload_ms: float
    wall_ms: float
    basis_numeric_bytes: int
    coefficient_numeric_bytes: int
    numeric_bytes: int
    raw_equivalent_numeric_bytes: int
    pool_used_bytes: int
    pool_total_bytes: int

    @classmethod
    def compile(
        cls,
        workspace: OpenModeFactorTTWorkspace,
        automata: Mapping[str, StructuredShowdownAutomaton],
        *,
        target_seat: int,
    ) -> CuPyAffineResidentAutomatonCache:
        shape = workspace.topology.base.hand_counts
        if isinstance(target_seat, bool) or target_seat not in range(len(shape)):
            raise ValueError("affine resident target is outside the hand axes")
        if not automata:
            raise ValueError("affine resident cache requires a terminal library")
        unique = {id(automaton): automaton for automaton in automata.values()}
        if any(automaton.shape != shape for automaton in unique.values()):
            raise ValueError("affine resident automaton axes differ from workspace")
        if any(automaton.target_player != target_seat for automaton in unique.values()):
            raise ValueError("affine resident automata differ from the target seat")

        wall_started = time.perf_counter()
        half_started = time.perf_counter()
        groups: dict[str, list[tuple[int, StructuredShowdownAutomaton]]] = {}
        for identifier, automaton in unique.items():
            groups.setdefault(_transition_topology_digest(automaton), []).append(
                (identifier, automaton)
            )

        host_bases: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        host_coefficients: dict[int, np.ndarray] = {}
        topology_by_automaton: dict[int, str] = {}
        for key, rows in groups.items():
            representative = rows[0][1]
            left, right = _automaton_half_vectors(representative, workspace)
            right_basis = np.empty_like(right)
            if representative.constant_winner_shortcut:
                right_basis.fill(1.0)
            else:
                state_rank = right.shape[1] - 1
                right_basis[:, :state_rank] = (
                    right[:, :state_rank] / representative.final_pot
                )
                right_basis[:, state_rank] = 1.0
            right_basis = np.ascontiguousarray(right_basis, dtype=np.float64)
            reconstructed = right_basis * _right_coefficients(
                representative, right.shape[1]
            )[None, :]
            if not np.allclose(reconstructed, right, atol=1e-13, rtol=0.0):
                raise AssertionError("affine resident basis failed reconstruction")
            host_bases[key] = (
                np.ascontiguousarray(left, dtype=np.float64),
                right_basis,
            )
            for identifier, automaton in rows:
                if _transition_topology_digest(automaton) != key:
                    raise AssertionError("affine topology grouping is inconsistent")
                coefficients = _right_coefficients(automaton, right.shape[1])
                if coefficients.shape != (right.shape[1],):
                    raise AssertionError("affine coefficient width differs from basis")
                host_coefficients[identifier] = coefficients
                topology_by_automaton[identifier] = key
        half_prepare_ms = (time.perf_counter() - half_started) * 1000.0

        cp, _ = _cupy_modules()
        upload_started = time.perf_counter()
        device_bases = {
            key: (cp.asarray(left), cp.asarray(right))
            for key, (left, right) in host_bases.items()
        }
        device_coefficients = {
            identifier: cp.asarray(values)
            for identifier, values in host_coefficients.items()
        }
        cp.cuda.runtime.deviceSynchronize()
        upload_ms = (time.perf_counter() - upload_started) * 1000.0
        refs = {
            identifier: CuPyAffineAutomatonHalfVectors(
                topology_key=topology_by_automaton[identifier],
                left_basis=device_bases[topology_by_automaton[identifier]][0],
                right_basis=device_bases[topology_by_automaton[identifier]][1],
                right_coefficients=device_coefficients[identifier],
                middle_rank=int(device_coefficients[identifier].shape[0]),
            )
            for identifier in unique
        }
        ranks = tuple(ref.middle_rank for ref in refs.values())
        basis_bytes = sum(
            int(left.nbytes + right.nbytes) for left, right in device_bases.values()
        )
        coefficient_bytes = sum(
            int(values.nbytes) for values in device_coefficients.values()
        )
        raw_equivalent = sum(
            int(ref.left_basis.nbytes + ref.right_basis.nbytes)
            for ref in refs.values()
        )
        pool = cp.get_default_memory_pool()
        return cls(
            topology=workspace.topology,
            target_seat=target_seat,
            half_vectors=refs,
            automaton_ids=frozenset(unique),
            unique_automata=len(unique),
            shared_topologies=len(device_bases),
            total_middle_rank=sum(ranks),
            stored_topology_middle_rank=sum(
                int(right.shape[1]) for _, right in device_bases.values()
            ),
            maximum_middle_rank=max(ranks),
            half_prepare_ms=half_prepare_ms,
            upload_ms=upload_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            basis_numeric_bytes=basis_bytes,
            coefficient_numeric_bytes=coefficient_bytes,
            numeric_bytes=basis_bytes + coefficient_bytes,
            raw_equivalent_numeric_bytes=raw_equivalent,
            pool_used_bytes=int(pool.used_bytes()),
            pool_total_bytes=int(pool.total_bytes()),
        )


def contract_affine_resident_heterogeneous_leaf_terms(
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    terms: tuple[HeterogeneousLeafTerm, ...],
    *,
    target_seat: int,
    belief_cache: Any,
    automaton_cache: CuPyAffineResidentAutomatonCache,
    cupy_sparse: CuPyBidirectionalIncidence,
    maximum_feature_width_per_batch: int = 384,
    zero_reach_value: float = 0.0,
) -> ResidentHeterogeneousLeafContraction:
    """Contract one seat from shared topology bases and affine coefficients."""

    wall_started = time.perf_counter()
    if not terms:
        raise ValueError("affine resident contraction requires at least one term")
    if sparse.topology is not workspace.topology:
        raise ValueError("affine resident sparse topology and workspace differ")
    if cupy_sparse.cpu is not sparse:
        raise ValueError("affine resident CuPy operators differ from CPU topology")
    if belief_cache.workspace is not workspace:
        raise ValueError("affine resident belief cache belongs to another workspace")
    if automaton_cache.topology is not workspace.topology:
        raise ValueError("affine resident automaton cache belongs to another topology")
    if automaton_cache.target_seat != target_seat:
        raise ValueError("affine resident automaton cache belongs to another target")
    shape = workspace.topology.base.hand_counts
    players = len(shape)
    if isinstance(target_seat, bool) or target_seat not in range(players):
        raise ValueError("affine resident target is outside the hand axes")
    if len({term.key for term in terms}) != len(terms):
        raise ValueError("affine resident leaf keys must be unique")
    if any(term.automaton.shape != shape for term in terms):
        raise ValueError("affine resident leaf axes differ from workspace")
    if any(id(term.automaton) not in automaton_cache.automaton_ids for term in terms):
        raise ValueError("affine resident leaf is absent from the static cache")
    if not np.isfinite(zero_reach_value):
        raise ValueError("affine resident zero-reach value must be finite")
    components = workspace.component_count
    if (
        isinstance(maximum_feature_width_per_batch, bool)
        or maximum_feature_width_per_batch < components
    ):
        raise ValueError("affine resident feature width is too small")

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
        refs = tuple(
            automaton_cache.half_vectors[id(term.automaton)] for term in terms
        )
        source_is_affine = True
    else:
        direction = "left_to_right"
        query_half = topology.right
        source_half = topology.left
        base_query_products = belief_cache.right_component_products
        base_source_products = belief_cache.left_component_products
        query_indices = belief_cache.right_indices
        source_indices = belief_cache.left_indices
        gpu_operator = cupy_sparse.left_to_right
        refs = tuple(
            automaton_cache.half_vectors[id(term.automaton)] for term in terms
        )
        source_is_affine = False

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

    ranks = tuple(ref.middle_rank for ref in refs)
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
        affine_vector_bytes = 0
        for term_index, kind, start, stop in batch:
            if kind == "mass":
                feature = source_products[term_index]
            else:
                ref = refs[term_index]
                if source_is_affine:
                    source_vector = (
                        ref.right_basis[:, start:stop]
                        * ref.right_coefficients[None, start:stop]
                    )
                    affine_vector_bytes += int(source_vector.nbytes)
                else:
                    source_vector = ref.left_basis[:, start:stop]
                rank = stop - start
                feature = (
                    source_products[term_index, :, :, None]
                    * source_vector[:, None, :]
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
                folded = cp.einsum(
                    "k,qk,qk->q",
                    belief_cache.mixture_weights,
                    query_products[term_index],
                    block,
                    optimize=True,
                )
                reach_records[term_index] += folded
            else:
                rank = stop - start
                ref = refs[term_index]
                if source_is_affine:
                    query_vector = ref.left_basis[:, start:stop]
                else:
                    query_vector = (
                        ref.right_basis[:, start:stop]
                        * ref.right_coefficients[None, start:stop]
                    )
                    affine_vector_bytes += int(query_vector.nbytes)
                numerator_records[term_index] += cp.einsum(
                    "k,qk,qkr,qr->q",
                    belief_cache.mixture_weights,
                    query_products[term_index],
                    block.reshape(query_half.records, components, rank),
                    query_vector,
                    optimize=True,
                )
            offset += width
        maximum_scratch = max(
            maximum_scratch,
            int(
                source_features.nbytes
                + incidence.nbytes
                + compatible.nbytes
                + affine_vector_bytes
            ),
        )
    pipeline_end.record()
    pipeline_end.synchronize()
    product_generation_ms = float(cp.cuda.get_elapsed_time(product_begin, product_end))
    resident_pipeline_ms = float(cp.cuda.get_elapsed_time(product_end, pipeline_end))

    download_started = time.perf_counter()
    host_numerators = cp.asnumpy(numerator_records)
    host_reaches = cp.asnumpy(reach_records)
    cp.cuda.runtime.deviceSynchronize()
    device_to_host_ms = (time.perf_counter() - download_started) * 1000.0
    pool = cp.get_default_memory_pool()
    maximum_gpu_used = int(pool.used_bytes())
    maximum_gpu_total = int(pool.total_bytes())

    hand_started = time.perf_counter()
    depth = query_half.seats.index(target_seat)
    indices = query_half.indices[:, depth]
    results = []
    for term, numerators_by_record, reaches_by_record in zip(
        terms, host_numerators, host_reaches, strict=True
    ):
        scale = max(1.0, float(np.max(np.abs(reaches_by_record))))
        minimum = float(np.min(reaches_by_record))
        if minimum < -1e-10 * scale:
            raise ArithmeticError("affine resident leaf produced negative reach")
        if minimum < 0.0:
            reaches_by_record = np.maximum(reaches_by_record, 0.0)
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
    hand_fold_ms = (time.perf_counter() - hand_started) * 1000.0

    factor_bytes = sum(values.nbytes for values in host_factors)
    record_bytes = int(host_numerators.nbytes + host_reaches.nbytes)
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
        + record_bytes
    )
    return ResidentHeterogeneousLeafContraction(
        values=tuple(results),
        work=ResidentHeterogeneousLeafWork(
            target_seat=target_seat,
            direction=direction,
            operator_backend="gpu_cupy_affine_resident",
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
            device_to_host_ms=device_to_host_ms,
            hand_fold_ms=hand_fold_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            per_call_host_to_device_bytes=factor_bytes,
            per_call_device_to_host_bytes=record_bytes,
            legacy_equivalent_host_to_device_bytes=legacy_h2d_bytes,
            legacy_equivalent_device_to_host_bytes=legacy_d2h_bytes,
            resident_belief_numeric_bytes=belief_cache.numeric_bytes,
            resident_automaton_numeric_bytes=automaton_cache.numeric_bytes,
            per_call_device_product_bytes=product_bytes,
            per_call_device_record_bytes=record_bytes,
            maximum_batch_scratch_numeric_bytes=maximum_scratch,
            estimated_peak_host_numeric_bytes=estimated_host,
            maximum_gpu_pool_used_bytes=maximum_gpu_used,
            maximum_gpu_pool_total_bytes=maximum_gpu_total,
        ),
    )


def _right_coefficients(
    automaton: StructuredShowdownAutomaton,
    middle_rank: int,
) -> np.ndarray:
    if automaton.constant_winner_shortcut:
        if middle_rank != 1:
            raise AssertionError("constant affine basis must have unit rank")
        result = np.asarray([automaton.sunk_value], dtype=np.float64)
    else:
        if middle_rank < 2:
            raise AssertionError("winner affine basis must include its sunk column")
        result = np.empty(middle_rank, dtype=np.float64)
        result[:-1] = automaton.final_pot
        result[-1] = automaton.sunk_value
    return np.ascontiguousarray(result, dtype=np.float64)


def _transition_topology_digest(automaton: StructuredShowdownAutomaton) -> str:
    digest = hashlib.sha256()
    digest.update(
        repr(
            (
                automaton.shape,
                automaton.contenders,
                automaton.target_player,
                automaton.constant_winner_shortcut,
            )
        ).encode("ascii")
    )
    for values in (*automaton.transitions, *automaton.bond_states):
        digest.update(repr((values.shape, values.dtype.str)).encode("ascii"))
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()
