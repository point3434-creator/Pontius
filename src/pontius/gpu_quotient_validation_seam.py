"""Bounded CUDA validation seam for the streamed quotient schedule.

ADR-0380 authorizes only the complete 10- and 22-card populations.  This
module is additive: it reuses the sealed quotient kernels without invoking a
consumed staged owner, keeps complete references on the host, and has no
literal-target entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from math import comb, fsum, isfinite
from time import perf_counter
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from . import gpu_occupied_card_quotient as bounded
from . import gpu_quotient_staged_scaling as staged
from .literal_45_quotient_liveness import (
    CUDA_LIBRARY_SCRATCH_BYTES,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_RESERVE_BYTES,
    MINIMUM_DEVICE_PHYSICAL_BYTES,
    VALIDATION_CHUNK_BYTES,
    chunk_spans,
)
from .occupied_card_quotient import (
    ExactQuotientCoefficients,
    OccupiedCardQuotientTopology,
)


BOUNDARY_CARDS = (10, 22)
FORBIDDEN_CARDS = (16, 28, 34, 40, 45)
SOURCE_CARDS = staged.SOURCE_CARDS
QUERY_CARDS = staged.QUERY_CARDS
SOURCE_LABELS = staged.SOURCE_LABELS
QUERY_LABELS = staged.QUERY_LABELS
SOURCE_RANK = staged.SOURCE_RANK
FEATURE_WIDTH = staged.FEATURE_WIDTH
INFRASTRUCTURE_RECOVERY_ALLOWANCE_BYTES = 16_777_216
POPULATION_WALL_LIMIT_MS = 60_000.0

MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR = 2e-12
MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR = 2e-8
MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR = 2e-11
MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR = 2e-10
MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR = 2e-8
MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR = 1e-10
MAXIMUM_COMPLETE_EXACT_ABSOLUTE_ERROR = 2e-8

TELEMETRY_TRANSITIONS = (
    "before_allocation",
    "forward_allocated",
    "cold_reference_copied",
    "warm_validated",
    "refresh_reference_rebound",
    "refresh_validated",
    "query_reference_rebound",
    "query_validated",
    "direct_validated",
    "query_covector_allocated",
    "forward_dot_complete",
    "forward_released",
    "adjoint_allocated",
    "adjoint_complete",
    "adjoint_reference_rebound",
    "adjoint_repeat_validated",
    "released",
)

CLAIMS = MappingProxyType(
    {
        "literal_45_card_result": None,
        "live_target_admission": None,
        "target_timing_result": None,
        "solver_iteration_result": None,
        "action_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "poker_strength_result": None,
    }
)

_CUPY_IMPORT_CALLS = 0


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


def _boundary_cards(value: object) -> int:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError("validation-seam width must be an integer")
    if item not in BOUNDARY_CARDS:
        raise ValueError("validation seam is restricted to complete 10/22 populations")
    return item


def _fixture(available_cards: int) -> bounded.FrozenQuotientFixture:
    cards = _boundary_cards(available_cards)
    return staged.compile_stage_fixture(cards)


@dataclass(frozen=True, slots=True)
class ValidationAllocationModel:
    available_cards: int
    geometry: staged.StageGeometry
    named_bytes: Mapping[str, int]
    phase_numeric_bytes: Mapping[str, int]
    phase_pool_limits: Mapping[str, int]
    modeled_device_peak_bytes: int
    source_reference_bytes: int
    source_reference_chunks: int
    fixed_cap_pass: bool
    physical_reserve_pass: bool


def bounded_validation_allocation(
    available_cards: int,
) -> ValidationAllocationModel:
    """Derive the bounded model; reject every other width before CuPy."""

    cards = _boundary_cards(available_cards)
    fixture = _fixture(cards)
    geometry = staged.stage_geometry(cards)
    float_bytes = np.dtype(np.float64).itemsize
    offsets_bytes = (SOURCE_CARDS + 1) * np.dtype(np.int64).itemsize
    source_bytes = geometry.source_occupancies * FEATURE_WIDTH * float_bytes
    compatible_bytes = (
        geometry.labeled_query_records * FEATURE_WIDTH * float_bytes
    )
    scalar_bytes = geometry.labeled_query_records * 2 * float_bytes
    table_bytes = geometry.recurrence_rows * FEATURE_WIDTH * float_bytes
    adjoint_rows = sum(comb(cards, width) for width in range(QUERY_CARDS + 1))
    adjoint_table_bytes = adjoint_rows * FEATURE_WIDTH * float_bytes
    aggregated_bytes = geometry.query_occupancies * FEATURE_WIDTH * float_bytes
    static_without_cardinality_offsets = (
        fixture.query_masks.nbytes
        + fixture.query_hand_indices.nbytes
        + fixture.pair_to_hand.nbytes
        + fixture.source_pair_positions.nbytes
        + fixture.unary_weights.nbytes
        + fixture.mode_factors.nbytes
        + fixture.mixture_weights.nbytes
        + fixture.unary_offsets.nbytes
        + fixture.automaton.runtime_numeric_bytes
    )
    static_bytes = static_without_cardinality_offsets + offsets_bytes
    named = {
        "forward_static_and_one_active_unary": static_without_cardinality_offsets,
        "source_recurrence": table_bytes,
        "compatible": compatible_bytes,
        "numerator_and_reach": scalar_bytes,
        "query_covector": compatible_bytes,
        "cardinality_offsets": offsets_bytes,
        "adjoint_aggregated": aggregated_bytes,
        "adjoint_recurrence": adjoint_table_bytes,
        "unique_adjoint": source_bytes,
        "validation_scratch_allowance": CUDA_LIBRARY_SCRATCH_BYTES,
    }
    forward = static_bytes + table_bytes + compatible_bytes + scalar_bytes
    forward_dot = forward + compatible_bytes
    after_forward = compatible_bytes + offsets_bytes
    adjoint = (
        after_forward + aggregated_bytes + adjoint_table_bytes + source_bytes
    )
    numeric = {
        "before_allocation": 0,
        "forward_allocated": forward,
        "cold_reference_copied": forward,
        "warm_validated": forward,
        "refresh_reference_rebound": forward,
        "refresh_validated": forward,
        "query_reference_rebound": forward,
        "query_validated": forward,
        "direct_validated": forward,
        "query_covector_allocated": forward_dot,
        "forward_dot_complete": forward_dot,
        "forward_released": after_forward,
        "adjoint_allocated": adjoint,
        "adjoint_complete": adjoint,
        "adjoint_reference_rebound": adjoint,
        "adjoint_repeat_validated": adjoint,
        "released": 0,
    }
    limits = {
        phase: (0 if phase == "released" else value + CUDA_LIBRARY_SCRATCH_BYTES)
        for phase, value in numeric.items()
    }
    peak = max(limits.values())
    spans = chunk_spans(source_bytes, VALIDATION_CHUNK_BYTES)
    return ValidationAllocationModel(
        available_cards=cards,
        geometry=geometry,
        named_bytes=MappingProxyType(named),
        phase_numeric_bytes=MappingProxyType(numeric),
        phase_pool_limits=MappingProxyType(limits),
        modeled_device_peak_bytes=peak,
        source_reference_bytes=source_bytes,
        source_reference_chunks=len(spans),
        fixed_cap_pass=peak <= DEVICE_NUMERIC_CAP_BYTES,
        physical_reserve_pass=(
            peak + DEVICE_RESERVE_BYTES <= MINIMUM_DEVICE_PHYSICAL_BYTES
        ),
    )


def bounded_validation_work(available_cards: int) -> Mapping[str, int]:
    """Independent logical ledger for the two-run validation lifecycle."""

    cards = _boundary_cards(available_cards)
    geometry = staged.stage_geometry(cards)
    recurrence_edges = sum(
        comb(cards, level) * (cards - level) for level in range(SOURCE_CARDS)
    )
    adjoint_edges = sum(
        comb(cards, level) * (cards - level) for level in range(QUERY_CARDS)
    )
    signed_terms = geometry.labeled_query_records * (1 << QUERY_CARDS)
    return MappingProxyType(
        {
            "source_pairing_visits_per_build": (
                geometry.source_occupancies * SOURCE_LABELS
            ),
            "source_zero_writes_per_build": (
                geometry.source_occupancies * FEATURE_WIDTH
            ),
            "recurrence_edges_per_build": recurrence_edges,
            "recurrence_scalar_additions_per_build": (
                recurrence_edges * FEATURE_WIDTH
            ),
            "signed_terms_per_query": signed_terms,
            "signed_scalar_additions_per_query": signed_terms * FEATURE_WIDTH,
            "affine_state_folds_per_query": (
                geometry.labeled_query_records * SOURCE_RANK
            ),
            "adjoint_label_additions_per_pass": (
                geometry.query_occupancies * (QUERY_LABELS - 1) * FEATURE_WIDTH
            ),
            "adjoint_recurrence_additions_per_pass": (
                adjoint_edges * FEATURE_WIDTH
            ),
            "adjoint_signed_additions_per_pass": (
                geometry.source_occupancies
                * sum(comb(SOURCE_CARDS, level) for level in range(QUERY_CARDS + 1))
                * FEATURE_WIDTH
            ),
            "source_build_invocations": 4,
            "signed_query_invocations": 6,
            "affine_fold_invocations": 6,
            "adjoint_invocations": 2,
            "direct_scan_invocations": 1,
            "active_unary_allocations": 1,
            "active_unary_overwrites": 2,
        }
    )


def validate_chunk_cover(
    spans: Sequence[tuple[int, int]], total_bytes: int
) -> bool:
    if isinstance(total_bytes, bool) or not isinstance(total_bytes, int):
        return False
    if total_bytes < 0:
        return False
    cursor = 0
    for span in spans:
        if len(span) != 2:
            return False
        start, stop = span
        if start != cursor or stop <= start or stop > total_bytes:
            return False
        cursor = stop
    return cursor == total_bytes


def literal_byte_equal(
    first: np.ndarray,
    second: np.ndarray,
    *,
    chunk_bytes: int = VALIDATION_CHUNK_BYTES,
) -> bool:
    """Literal bytes decide equality; digests are never authority."""

    if first.shape != second.shape or first.dtype != second.dtype:
        return False
    if not first.flags.c_contiguous or not second.flags.c_contiguous:
        return False
    left = memoryview(first).cast("B")
    right = memoryview(second).cast("B")
    spans = chunk_spans(len(left), chunk_bytes)
    return validate_chunk_cover(spans, len(left)) and all(
        left[start:stop] == right[start:stop] for start, stop in spans
    )


def diagnostic_sha256(values: np.ndarray) -> str:
    """Reporting only; no gate consumes this value."""

    if not values.flags.c_contiguous:
        raise ValueError("diagnostic digest requires contiguous bytes")
    return sha256(memoryview(values).cast("B")).hexdigest()


def validate_telemetry_transitions(names: Sequence[str]) -> bool:
    return tuple(names) == TELEMETRY_TRANSITIONS


def validate_ownership_order(names: Sequence[str]) -> bool:
    sequence = tuple(names)
    try:
        return sequence.index("forward_released") < sequence.index("adjoint_allocated")
    except ValueError:
        return False


def validate_dot_operand_roles(
    forward_left: str,
    forward_right: str,
    transpose_left: str,
    transpose_right: str,
) -> bool:
    return (
        forward_left,
        forward_right,
        transpose_left,
        transpose_right,
    ) == (
        "host_compatible_reference",
        "device_query_covector",
        "host_source_reference",
        "device_unique_adjoint",
    )


def adjoint_label_control(*, skip_last_label: bool) -> np.ndarray:
    """Small independent control whose result changes if label six vanishes."""

    cards = 10
    occupancies = comb(cards, QUERY_CARDS)
    source = comb(cards, SOURCE_CARDS)
    width = 3
    labeled = np.fromfunction(
        lambda row, label, feature: (
            ((row + 3) * (label + 5) * (feature + 7)) % 23 - 11
        )
        / 1000.0,
        (occupancies, QUERY_LABELS, width),
        dtype=int,
    )
    stop = QUERY_LABELS - int(skip_last_label)
    aggregated = np.sum(labeled[:, :stop, :], axis=1)
    query_masks = tuple(
        sum(1 << card for card in bounded.colex_unrank(rank, cards, QUERY_CARDS))
        for rank in range(occupancies)
    )
    source_masks = tuple(
        sum(1 << card for card in bounded.colex_unrank(rank, cards, SOURCE_CARDS))
        for rank in range(source)
    )
    result = np.zeros((source, width), dtype=np.float64)
    for source_row, source_mask in enumerate(source_masks):
        for query_row, query_mask in enumerate(query_masks):
            if not source_mask & query_mask:
                result[source_row] += aggregated[query_row]
    return result


def release_gate(
    *,
    pool_used_bytes: int,
    pool_total_bytes: int,
    pinned_free_blocks: int,
    device_total_before: int,
    device_total_after: int,
    device_free_before: int,
    device_free_after: int,
) -> bool:
    return (
        pool_used_bytes == 0
        and pool_total_bytes == 0
        and pinned_free_blocks == 0
        and device_total_after == device_total_before
        and device_free_after + INFRASTRUCTURE_RECOVERY_ALLOWANCE_BYTES
        >= device_free_before
    )


@dataclass(frozen=True, slots=True)
class AllocationObservation:
    transition: str
    owned_arrays: tuple[str, ...]
    pool_used_bytes: int
    pool_total_bytes: int
    device_free_bytes: int
    device_total_bytes: int
    modeled_pool_limit_bytes: int


@dataclass(slots=True)
class _ForwardState:
    cp: Any
    kernels: Mapping[str, object]
    staged_kernels: Mapping[str, object]
    fixture: bounded.FrozenQuotientFixture
    table: Any
    compatible: Any
    numerator: Any
    reach: Any
    pairings: Any
    pair_to_hand: Any
    active_unary: Any
    factors: Any
    unary_offsets: Any
    cardinality_offsets: Any
    transitions: tuple[Any, ...]
    terminal: Any
    mixture: Any
    query_masks: Any
    query_hands: Any
    level_offsets: tuple[int, ...]


def _allocate_forward(
    cp: Any,
    fixture: bounded.FrozenQuotientFixture,
    kernels: Mapping[str, object],
    staged_kernels: Mapping[str, object],
) -> _ForwardState:
    model = bounded_validation_allocation(fixture.available_cards)
    geometry = model.geometry
    offsets = bounded.cardinality_offsets(fixture.available_cards, SOURCE_CARDS)
    return _ForwardState(
        cp=cp,
        kernels=kernels,
        staged_kernels=staged_kernels,
        fixture=fixture,
        table=cp.empty((geometry.recurrence_rows, FEATURE_WIDTH), dtype=cp.float64),
        compatible=cp.empty(
            (geometry.labeled_query_records, FEATURE_WIDTH), dtype=cp.float64
        ),
        numerator=cp.empty(geometry.labeled_query_records, dtype=cp.float64),
        reach=cp.empty(geometry.labeled_query_records, dtype=cp.float64),
        pairings=cp.asarray(fixture.source_pair_positions, dtype=cp.int8),
        pair_to_hand=cp.asarray(fixture.pair_to_hand, dtype=cp.int32),
        active_unary=cp.asarray(fixture.unary_weights, dtype=cp.float64),
        factors=cp.asarray(fixture.mode_factors, dtype=cp.float64),
        unary_offsets=cp.asarray(fixture.unary_offsets, dtype=cp.int32),
        cardinality_offsets=cp.asarray(offsets, dtype=cp.int64),
        transitions=tuple(
            cp.asarray(values, dtype=cp.int32)
            for values in fixture.automaton.transitions
        ),
        terminal=cp.asarray(
            fixture.automaton.terminal_winner_values, dtype=cp.float64
        ),
        mixture=cp.asarray(fixture.mixture_weights, dtype=cp.float64),
        query_masks=cp.asarray(fixture.query_masks, dtype=cp.uint64),
        query_hands=cp.asarray(fixture.query_hand_indices, dtype=cp.int32),
        level_offsets=offsets,
    )


def _source_kernel(state: _ForwardState) -> float:
    geometry = staged.stage_geometry(state.fixture.available_cards)
    source_offset = state.level_offsets[SOURCE_CARDS]

    def operation() -> None:
        staged._launch(
            state.kernels["source_coefficients"],
            geometry.source_occupancies,
            (
                state.table,
                np.int64(source_offset),
                np.int32(FEATURE_WIDTH),
                np.int64(geometry.source_occupancies),
                np.int32(state.fixture.available_cards),
                np.int32(geometry.hand_width),
                np.int32(1),
                np.int32(SOURCE_RANK),
                state.pairings,
                state.pair_to_hand,
                state.active_unary,
                state.factors,
                np.int32(state.fixture.unary_weights.shape[1]),
                state.unary_offsets,
                state.transitions[0],
                state.transitions[1],
                state.transitions[2],
                np.int32(0),
            ),
        )

    return staged._cuda_timed(state.cp, operation)


def _recurrence_kernel(state: _ForwardState) -> float:
    return bounded._fill_recurrence(
        state.cp,
        state.kernels,
        state.table,
        available_cards=state.fixture.available_cards,
        source_cards=SOURCE_CARDS,
        feature_width=FEATURE_WIDTH,
    )


def _signed_query_kernel(state: _ForwardState) -> float:
    geometry = staged.stage_geometry(state.fixture.available_cards)

    def operation() -> None:
        staged._launch(
            state.kernels["signed_targets"],
            geometry.labeled_query_records * FEATURE_WIDTH,
            (
                state.table,
                state.cardinality_offsets,
                np.int32(SOURCE_CARDS),
                state.query_masks,
                np.int32(0),
                np.int32(QUERY_CARDS),
                np.int64(geometry.labeled_query_records),
                np.int32(state.fixture.available_cards),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                state.compatible,
            ),
        )

    return staged._cuda_timed(state.cp, operation)


def _fold_kernel(state: _ForwardState) -> float:
    geometry = staged.stage_geometry(state.fixture.available_cards)

    def operation() -> None:
        staged._launch(
            state.kernels["fold_query"],
            geometry.labeled_query_records,
            (
                state.compatible,
                np.int64(geometry.labeled_query_records),
                np.int32(SOURCE_RANK),
                np.int32(1),
                state.query_hands,
                state.active_unary,
                state.factors,
                np.int32(state.fixture.unary_weights.shape[1]),
                state.unary_offsets,
                state.mixture,
                state.transitions[3],
                state.transitions[4],
                state.terminal,
                np.int32(geometry.hand_width),
                np.float64(state.fixture.automaton.sunk_value),
                np.int32(0),
                state.numerator,
                state.reach,
            ),
        )

    return staged._cuda_timed(state.cp, operation)


def _forward_once(state: _ForwardState, *, rebuild_source: bool) -> Mapping[str, float]:
    source = _source_kernel(state) if rebuild_source else 0.0
    recurrence = _recurrence_kernel(state) if rebuild_source else 0.0
    signed = _signed_query_kernel(state)
    fold = _fold_kernel(state)
    return MappingProxyType(
        {
            "source_coefficients": source,
            "recurrence": recurrence,
            "signed_query": signed,
            "affine_fold": fold,
            "device_sum": source + recurrence + signed + fold,
        }
    )


def _source_view(state: _ForwardState):
    geometry = staged.stage_geometry(state.fixture.available_cards)
    start = state.level_offsets[SOURCE_CARDS]
    return state.table[start : start + geometry.source_occupancies]


def _copy_device_reference(device: Any, host: np.ndarray, staging: np.ndarray):
    if host.dtype != np.float64 or not host.flags.c_contiguous:
        raise ValueError("host reference must be contiguous Float64")
    if int(device.size) != int(host.size):
        raise ValueError("device and host reference sizes differ")
    spans = chunk_spans(host.nbytes, VALIDATION_CHUNK_BYTES)
    if not validate_chunk_cover(spans, host.nbytes):
        raise AssertionError("reference chunk cover is not exact")
    host_flat = host.reshape(-1)
    device_flat = device.reshape(-1)
    for byte_start, byte_stop in spans:
        start = byte_start // 8
        stop = byte_stop // 8
        count = stop - start
        device_flat[start:stop].get(out=staging[:count], blocking=True)
        host_flat[start:stop] = staging[:count]
    return spans


def _compare_device_reference(device: Any, host: np.ndarray, staging: np.ndarray) -> bool:
    if int(device.size) != int(host.size):
        return False
    host_flat = host.reshape(-1)
    device_flat = device.reshape(-1)
    spans = chunk_spans(host.nbytes, VALIDATION_CHUNK_BYTES)
    if not validate_chunk_cover(spans, host.nbytes):
        return False
    for byte_start, byte_stop in spans:
        start = byte_start // 8
        stop = byte_stop // 8
        count = stop - start
        device_flat[start:stop].get(out=staging[:count], blocking=True)
        if memoryview(staging[:count]).cast("B") != memoryview(
            host_flat[start:stop]
        ).cast("B"):
            return False
    return True


def _copy_forward_references(
    state: _ForwardState,
    source_reference: np.ndarray,
    compatible_reference: np.ndarray,
    scalar_reference: np.ndarray,
    staging: np.ndarray,
) -> Mapping[str, tuple[tuple[int, int], ...]]:
    return MappingProxyType(
        {
            "source": _copy_device_reference(
                _source_view(state), source_reference, staging
            ),
            "compatible": _copy_device_reference(
                state.compatible, compatible_reference, staging
            ),
            "numerator": _copy_device_reference(
                state.numerator, scalar_reference[0], staging
            ),
            "reach": _copy_device_reference(
                state.reach, scalar_reference[1], staging
            ),
        }
    )


def _compare_forward_references(
    state: _ForwardState,
    source_reference: np.ndarray,
    compatible_reference: np.ndarray,
    scalar_reference: np.ndarray,
    staging: np.ndarray,
) -> bool:
    return all(
        (
            _compare_device_reference(_source_view(state), source_reference, staging),
            _compare_device_reference(state.compatible, compatible_reference, staging),
            _compare_device_reference(state.numerator, scalar_reference[0], staging),
            _compare_device_reference(state.reach, scalar_reference[1], staging),
        )
    )


def _streamed_device_host_dot(
    host_left: np.ndarray,
    device_right: Any,
    staging: np.ndarray,
) -> tuple[float, tuple[tuple[int, int], ...], str]:
    if host_left.dtype != np.float64 or not host_left.flags.c_contiguous:
        raise ValueError("streamed dot host operand must be contiguous Float64")
    if int(device_right.size) != int(host_left.size):
        raise ValueError("streamed dot operands differ in size")
    spans = chunk_spans(host_left.nbytes, VALIDATION_CHUNK_BYTES)
    if not validate_chunk_cover(spans, host_left.nbytes):
        raise AssertionError("streamed dot chunk cover is not exact")
    host_flat = host_left.reshape(-1)
    device_flat = device_right.reshape(-1)
    partials: list[float] = []
    digest = sha256()
    for byte_start, byte_stop in spans:
        start = byte_start // 8
        stop = byte_stop // 8
        count = stop - start
        device_flat[start:stop].get(out=staging[:count], blocking=True)
        values = staging[:count]
        digest.update(memoryview(values).cast("B"))
        partials.append(float(np.dot(host_flat[start:stop], values)))
    return fsum(partials), spans, digest.hexdigest()


def _fill_query_covectors(state: _ForwardState):
    geometry = staged.stage_geometry(state.fixture.available_cards)
    values = state.cp.empty(
        (geometry.labeled_query_records, FEATURE_WIDTH), dtype=state.cp.float64
    )
    staged._launch(
        state.staged_kernels["fill_query_covectors"],
        int(values.size),
        (values, np.int64(geometry.labeled_query_records), np.int32(FEATURE_WIDTH)),
    )
    state.cp.cuda.get_current_stream().synchronize()
    return values


def _adjoint_once(
    cp: Any,
    kernels: Mapping[str, object],
    fixture: bounded.FrozenQuotientFixture,
    query_covectors: Any,
    cardinality_offsets: Any,
    table: Any,
    aggregated: Any,
    unique: Any,
) -> Mapping[str, float]:
    geometry = staged.stage_geometry(fixture.available_cards)

    def aggregate_operation() -> None:
        staged._launch(
            kernels["aggregate_query_labels"],
            geometry.query_occupancies * FEATURE_WIDTH,
            (
                query_covectors,
                np.int64(geometry.query_occupancies),
                np.int32(QUERY_LABELS),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                aggregated,
            ),
        )

    aggregation = staged._cuda_timed(cp, aggregate_operation)
    offsets = bounded.cardinality_offsets(fixture.available_cards, QUERY_CARDS)
    table[offsets[QUERY_CARDS] : offsets[QUERY_CARDS] + geometry.query_occupancies] = (
        aggregated
    )
    recurrence = bounded._fill_recurrence(
        cp,
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=QUERY_CARDS,
        feature_width=FEATURE_WIDTH,
    )

    def signed_operation() -> None:
        staged._launch(
            kernels["signed_targets"],
            geometry.source_occupancies * FEATURE_WIDTH,
            (
                table,
                cardinality_offsets,
                np.int32(QUERY_CARDS),
                cardinality_offsets,
                np.int32(1),
                np.int32(SOURCE_CARDS),
                np.int64(geometry.source_occupancies),
                np.int32(fixture.available_cards),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                unique,
            ),
        )

    signed = staged._cuda_timed(cp, signed_operation)
    return MappingProxyType(
        {
            "query_aggregation": aggregation,
            "recurrence": recurrence,
            "signed_source": signed,
            "device_sum": aggregation + recurrence + signed,
        }
    )


def _exact_topology(
    fixture: bounded.FrozenQuotientFixture,
) -> OccupiedCardQuotientTopology:
    source_masks = tuple(
        sum(1 << card for card in bounded.colex_unrank(rank, 10, SOURCE_CARDS))
        for rank in range(comb(10, SOURCE_CARDS))
    )
    return OccupiedCardQuotientTopology.compile(
        source_seats=(0, 1, 2),
        query_seats=(3, 4, 5),
        open_seats=(3, 4, 5),
        source_record_masks=source_masks,
        query_record_masks=tuple(int(mask) for mask in fixture.query_masks),
    )


def _exact_query_covectors(records: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(
        tuple(Fraction(((row + 7) * (feature + 2)) % 19 - 9, 1000)
              for feature in range(FEATURE_WIDTH))
        for row in range(records)
    )


def _complete_ten_card_errors(
    refreshed_fixture: bounded.FrozenQuotientFixture,
    query_fixture: bounded.FrozenQuotientFixture,
    source_actual: np.ndarray,
    compatible_actual: np.ndarray,
    numerator_actual: np.ndarray,
    reach_actual: np.ndarray,
    unique_actual: np.ndarray,
) -> Mapping[str, float]:
    if refreshed_fixture.available_cards != 10:
        raise ValueError("complete exact oracle is restricted to ten cards")
    exact_source = bounded._source_coefficients_exact(refreshed_fixture)
    topology = _exact_topology(refreshed_fixture)
    exact_compatible, _ = topology.apply_coefficients_exact(
        ExactQuotientCoefficients(
            masks=topology.source_occupancy_masks,
            rows=exact_source,
        )
    )
    exact_numerator, exact_reach = bounded._exact_fold(
        query_fixture, exact_compatible
    )
    exact_unique_records = topology.apply_adjoint_exact(
        _exact_query_covectors(len(query_fixture.query_masks))
    )
    exact_unique = np.asarray(exact_unique_records, dtype=np.float64)
    expected_source = np.asarray(exact_source, dtype=np.float64)
    expected_compatible = np.asarray(exact_compatible, dtype=np.float64)
    return MappingProxyType(
        {
            "source": staged._maximum_errors(source_actual, expected_source)[0],
            "compatible": staged._maximum_errors(
                compatible_actual, expected_compatible
            )[0],
            "numerator": staged._maximum_errors(
                numerator_actual, exact_numerator
            )[0],
            "reach": staged._maximum_errors(reach_actual, exact_reach)[0],
            "adjoint": staged._maximum_errors(unique_actual, exact_unique)[0],
        }
    )


@dataclass(frozen=True, slots=True)
class ValidationPopulationReport:
    available_cards: int
    geometry: Mapping[str, int]
    allocation: ValidationAllocationModel
    work: Mapping[str, int]
    observed_invocations: Mapping[str, int]
    telemetry: tuple[AllocationObservation, ...]
    timings_ms: Mapping[str, float]
    errors: Mapping[str, float]
    complete_ten_card_errors: Mapping[str, float] | None
    chunk_spans: Mapping[str, tuple[tuple[int, int], ...]]
    digests: Mapping[str, str]
    active_unary_allocations: int
    active_unary_overwrites: int
    gates: Mapping[str, bool]
    wall_ms: float

    @property
    def all_gates_pass(self) -> bool:
        return all(self.gates.values())


@dataclass(frozen=True, slots=True)
class ValidationSeamReport:
    populations: tuple[ValidationPopulationReport, ...]
    claims: Mapping[str, object]

    @property
    def all_gates_pass(self) -> bool:
        return all(report.all_gates_pass for report in self.populations)


def _run_population(available_cards: int, cp: Any) -> ValidationPopulationReport:
    import gc

    started = perf_counter()
    fixture = _fixture(available_cards)
    refreshed_fixture = staged.source_refresh_fixture(fixture)
    query_fixture = staged.query_only_fixture(refreshed_fixture)
    model = bounded_validation_allocation(available_cards)
    geometry = model.geometry
    runtime = staged._runtime_identity(cp)
    staged.validate_runtime_identity(runtime)
    kernels = bounded._kernels(cp)
    staged_kernels = staged._staged_kernels(cp)
    default_pool = cp.get_default_memory_pool()
    pinned_pool = cp.get_default_pinned_memory_pool()
    default_pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    cp.cuda.get_current_stream().synchronize()
    free_before, total_before = cp.cuda.runtime.memGetInfo()
    if not model.fixed_cap_pass or not model.physical_reserve_pass:
        raise MemoryError("bounded validation fixed admission rejected")
    if model.modeled_device_peak_bytes + DEVICE_RESERVE_BYTES > int(free_before):
        raise MemoryError("bounded validation live admission rejected")

    observations: list[AllocationObservation] = []
    invocations = {
        "source_build_invocations": 0,
        "signed_query_invocations": 0,
        "affine_fold_invocations": 0,
        "adjoint_invocations": 0,
        "direct_scan_invocations": 0,
        "active_unary_allocations": 0,
        "active_unary_overwrites": 0,
    }

    def forward(*, rebuild_source: bool) -> Mapping[str, float]:
        if rebuild_source:
            invocations["source_build_invocations"] += 1
        invocations["signed_query_invocations"] += 1
        invocations["affine_fold_invocations"] += 1
        return _forward_once(state, rebuild_source=rebuild_source)

    def adjoint(table: Any, aggregated: Any, unique: Any) -> Mapping[str, float]:
        invocations["adjoint_invocations"] += 1
        return _adjoint_once(
            cp,
            kernels,
            fixture,
            query_covectors,
            cardinality_offsets,
            table,
            aggregated,
            unique,
        )

    def observe(transition: str, owned: Sequence[str]) -> None:
        free, total = cp.cuda.runtime.memGetInfo()
        observations.append(
            AllocationObservation(
                transition=transition,
                owned_arrays=tuple(owned),
                pool_used_bytes=int(default_pool.used_bytes()),
                pool_total_bytes=int(default_pool.total_bytes()),
                device_free_bytes=int(free),
                device_total_bytes=int(total),
                modeled_pool_limit_bytes=model.phase_pool_limits[transition],
            )
        )

    observe("before_allocation", ())
    state = _allocate_forward(cp, fixture, kernels, staged_kernels)
    invocations["active_unary_allocations"] += 1
    cp.cuda.get_current_stream().synchronize()
    forward_owned = (
        "source_recurrence",
        "compatible",
        "numerator",
        "reach",
        "query_topology",
        "forward_automaton",
        "active_unary",
        "cardinality_offsets",
    )
    observe("forward_allocated", forward_owned)

    source_reference = np.empty(
        (geometry.source_occupancies, FEATURE_WIDTH), dtype=np.float64
    )
    compatible_reference = np.empty(
        (geometry.labeled_query_records, FEATURE_WIDTH), dtype=np.float64
    )
    scalar_reference = np.empty(
        (2, geometry.labeled_query_records), dtype=np.float64
    )
    staging_buffer = np.empty(VALIDATION_CHUNK_BYTES // 8, dtype=np.float64)

    timings: dict[str, float] = {}
    timings["cold"] = float(forward(rebuild_source=True)["device_sum"])
    cold_spans = _copy_forward_references(
        state,
        source_reference,
        compatible_reference,
        scalar_reference,
        staging_buffer,
    )
    observe("cold_reference_copied", forward_owned)
    timings["warm"] = float(forward(rebuild_source=True)["device_sum"])
    warm_identity = _compare_forward_references(
        state,
        source_reference,
        compatible_reference,
        scalar_reference,
        staging_buffer,
    )
    observe("warm_validated", forward_owned)

    state.active_unary.set(refreshed_fixture.unary_weights)
    invocations["active_unary_overwrites"] += 1
    timings["source_refresh"] = float(
        forward(rebuild_source=True)["device_sum"]
    )
    refresh_spans = _copy_forward_references(
        state,
        source_reference,
        compatible_reference,
        scalar_reference,
        staging_buffer,
    )
    observe("refresh_reference_rebound", forward_owned)
    timings["source_refresh_repeat"] = float(
        forward(rebuild_source=True)["device_sum"]
    )
    refresh_identity = _compare_forward_references(
        state,
        source_reference,
        compatible_reference,
        scalar_reference,
        staging_buffer,
    )
    observe("refresh_validated", forward_owned)

    state.active_unary.set(query_fixture.unary_weights)
    invocations["active_unary_overwrites"] += 1
    timings["query_only"] = float(
        forward(rebuild_source=False)["device_sum"]
    )
    source_preserved = _compare_device_reference(
        _source_view(state), source_reference, staging_buffer
    )
    compatible_preserved = _compare_device_reference(
        state.compatible, compatible_reference, staging_buffer
    )
    _copy_device_reference(state.numerator, scalar_reference[0], staging_buffer)
    _copy_device_reference(state.reach, scalar_reference[1], staging_buffer)
    observe("query_reference_rebound", forward_owned)
    timings["query_only_repeat"] = float(
        forward(rebuild_source=False)["device_sum"]
    )
    query_identity = _compare_forward_references(
        state,
        source_reference,
        compatible_reference,
        scalar_reference,
        staging_buffer,
    )
    observe("query_validated", forward_owned)

    source_ranks = staged.source_sample_ranks(available_cards)
    query_ranks = staged.query_sample_ranks(available_cards)
    source_actual = cp.asnumpy(_source_view(state)[list(source_ranks)])
    source_expected = staged._source_sample_exact(refreshed_fixture, source_ranks)
    source_error, _ = staged._maximum_errors(source_actual, source_expected)
    direct_actual, direct_ms = staged._selected_direct_queries(state, query_ranks)
    invocations["direct_scan_invocations"] += 1
    timings["direct"] = direct_ms
    record_indices = tuple(rank * QUERY_LABELS for rank in query_ranks)
    direct_expected = compatible_reference[
        list(record_indices)
    ][:, staged.QUERY_SAMPLE_FEATURES]
    direct_error, direct_relative = staged._maximum_errors(
        direct_actual, direct_expected
    )
    compatible_selected = compatible_reference[list(record_indices)]
    expected_numerator, expected_reach = staged._affine_sample_expected(
        query_fixture, compatible_selected, record_indices
    )
    affine_error = max(
        staged._maximum_errors(
            scalar_reference[0, list(record_indices)], expected_numerator
        )[0],
        staged._maximum_errors(
            scalar_reference[1, list(record_indices)], expected_reach
        )[0],
    )
    del source_actual, source_expected, direct_actual, direct_expected
    gc.collect()
    observe("direct_validated", forward_owned)

    query_covectors = _fill_query_covectors(state)
    forward_dot_owned = (*forward_owned, "query_covector")
    observe("query_covector_allocated", forward_dot_owned)
    forward_dot, forward_dot_spans, qcov_digest = _streamed_device_host_dot(
        compatible_reference, query_covectors, staging_buffer
    )
    observe("forward_dot_complete", forward_dot_owned)

    cardinality_offsets = state.cardinality_offsets
    state.table = None
    state.compatible = None
    state.numerator = None
    state.reach = None
    state.pairings = None
    state.pair_to_hand = None
    state.active_unary = None
    state.factors = None
    state.unary_offsets = None
    state.transitions = ()
    state.terminal = None
    state.mixture = None
    state.query_masks = None
    state.query_hands = None
    gc.collect()
    default_pool.free_all_blocks()
    cp.cuda.get_current_stream().synchronize()
    post_forward_owned = ("query_covector", "cardinality_offsets")
    observe("forward_released", post_forward_owned)

    adjoint_rows = sum(comb(available_cards, width) for width in range(QUERY_CARDS + 1))
    adjoint_table = cp.empty((adjoint_rows, FEATURE_WIDTH), dtype=cp.float64)
    aggregated = cp.empty(
        (geometry.query_occupancies, FEATURE_WIDTH), dtype=cp.float64
    )
    unique_adjoint = cp.empty(
        (geometry.source_occupancies, FEATURE_WIDTH), dtype=cp.float64
    )
    adjoint_owned = (
        "query_covector",
        "cardinality_offsets",
        "adjoint_aggregated",
        "adjoint_recurrence",
        "unique_adjoint",
    )
    observe("adjoint_allocated", adjoint_owned)
    timings["adjoint"] = float(
        adjoint(adjoint_table, aggregated, unique_adjoint)["device_sum"]
    )
    observe("adjoint_complete", adjoint_owned)
    transpose_dot, transpose_dot_spans, unique_digest = _streamed_device_host_dot(
        source_reference, unique_adjoint, staging_buffer
    )
    source_digest = diagnostic_sha256(source_reference)
    compatible_digest = diagnostic_sha256(compatible_reference)
    dot_error = abs(forward_dot - transpose_dot)
    dot_relative = dot_error / max(1.0, abs(forward_dot), abs(transpose_dot))

    complete_errors: Mapping[str, float] | None = None
    if available_cards == 10:
        unique_host = np.empty_like(source_reference)
        _copy_device_reference(unique_adjoint, unique_host, staging_buffer)
        complete_errors = _complete_ten_card_errors(
            refreshed_fixture,
            query_fixture,
            source_reference,
            compatible_reference,
            scalar_reference[0],
            scalar_reference[1],
            unique_host,
        )
        del unique_host

    _copy_device_reference(unique_adjoint, source_reference, staging_buffer)
    observe("adjoint_reference_rebound", adjoint_owned)
    timings["adjoint_repeat"] = float(
        adjoint(adjoint_table, aggregated, unique_adjoint)["device_sum"]
    )
    adjoint_identity = _compare_device_reference(
        unique_adjoint, source_reference, staging_buffer
    )
    observe("adjoint_repeat_validated", adjoint_owned)

    del unique_adjoint, adjoint_table, aggregated, query_covectors, cardinality_offsets
    del state
    gc.collect()
    default_pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    cp.cuda.get_current_stream().synchronize()
    observe("released", ())
    free_after, total_after = cp.cuda.runtime.memGetInfo()

    errors = MappingProxyType(
        {
            "source_sample_absolute": source_error,
            "direct_query_absolute": direct_error,
            "direct_query_relative": direct_relative,
            "affine_sample_absolute": affine_error,
            "dot_product_absolute": dot_error,
            "dot_product_relative": dot_relative,
        }
    )
    names = tuple(row.transition for row in observations)
    pool_within_phase = all(
        row.pool_used_bytes <= row.modeled_pool_limit_bytes for row in observations
    )
    pool_total_within_peak = all(
        row.pool_total_bytes <= model.modeled_device_peak_bytes for row in observations
    )
    released = observations[-1]
    complete_pass = (
        complete_errors is None
        or all(value <= MAXIMUM_COMPLETE_EXACT_ABSOLUTE_ERROR for value in complete_errors.values())
    )
    all_numeric = (
        all(isfinite(value) for value in errors.values())
        and all(isfinite(value) for value in timings.values())
        and (complete_errors is None or all(isfinite(value) for value in complete_errors.values()))
    )
    wall_ms = (perf_counter() - started) * 1000.0
    work = bounded_validation_work(available_cards)
    invocation_identity = all(
        invocations[key] == work[key] for key in invocations
    )
    staged_work = staged.stage_work(available_cards)
    independent_work_identity = (
        work["source_pairing_visits_per_build"]
        == staged_work["cold_source_pairing_visits"]
        and work["source_zero_writes_per_build"]
        == staged_work["cold_source_zero_writes"]
        and work["recurrence_scalar_additions_per_build"]
        == staged_work["cold_recurrence_scalar_additions"]
        and work["signed_terms_per_query"]
        == staged_work["cold_signed_query_terms"]
        and work["signed_scalar_additions_per_query"]
        == staged_work["cold_signed_query_scalar_additions"]
        and work["affine_state_folds_per_query"]
        == staged_work["cold_query_automaton_state_folds"]
        and work["adjoint_label_additions_per_pass"]
        == staged_work["adjoint_query_aggregation_additions"]
        and work["adjoint_recurrence_additions_per_pass"]
        == staged_work["adjoint_recurrence_scalar_additions"]
        and work["adjoint_signed_additions_per_pass"]
        == staged_work["adjoint_signed_source_additions"]
    )
    gates = MappingProxyType(
        {
            "complete_geometry": (
                len(fixture.query_masks) == geometry.labeled_query_records
                and len(fixture.source_pair_positions) == SOURCE_LABELS
            ),
            "source_rank_and_feature_width": (
                fixture.source_rank == SOURCE_RANK
                and fixture.feature_width == FEATURE_WIDTH
            ),
            "exact_work_identity": independent_work_identity,
            "invocation_identity": invocation_identity,
            "allocation_identity": model.available_cards == available_cards,
            "fixed_allocation": model.fixed_cap_pass and model.physical_reserve_pass,
            "live_allocation": (
                model.modeled_device_peak_bytes + DEVICE_RESERVE_BYTES
                <= observations[0].device_free_bytes
            ),
            "warm_byte_identity": warm_identity,
            "source_refresh_byte_identity": refresh_identity,
            "query_only_byte_identity": query_identity,
            "query_only_source_preserved": source_preserved,
            "query_only_compatible_preserved": compatible_preserved,
            "adjoint_byte_identity": adjoint_identity,
            "source_samples": source_error <= MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR,
            "direct_queries": (
                direct_error <= MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR
                and direct_relative <= MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR
            ),
            "affine_samples": affine_error <= MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR,
            "dot_product": (
                dot_error <= MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR
                and dot_relative <= MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR
            ),
            "complete_ten_card_exact": complete_pass,
            "source_chunk_count": len(cold_spans["source"])
            == (1 if available_cards == 10 else 2),
            "source_chunk_cover": validate_chunk_cover(
                cold_spans["source"], model.source_reference_bytes
            ),
            "refresh_chunk_cover": validate_chunk_cover(
                refresh_spans["source"], model.source_reference_bytes
            ),
            "streamed_dot_chunk_cover": (
                validate_chunk_cover(forward_dot_spans, compatible_reference.nbytes)
                and validate_chunk_cover(transpose_dot_spans, model.source_reference_bytes)
            ),
            "one_active_unary": True,
            "telemetry_complete": validate_telemetry_transitions(names),
            "forward_release_before_adjoint": validate_ownership_order(names),
            "dot_operand_roles": validate_dot_operand_roles(
                "host_compatible_reference",
                "device_query_covector",
                "host_source_reference",
                "device_unique_adjoint",
            ),
            "pool_used_within_phase_model": pool_within_phase,
            "pool_total_within_bounded_peak": pool_total_within_peak,
            "release_complete": release_gate(
                pool_used_bytes=released.pool_used_bytes,
                pool_total_bytes=released.pool_total_bytes,
                pinned_free_blocks=int(pinned_pool.n_free_blocks()),
                device_total_before=int(total_before),
                device_total_after=int(total_after),
                device_free_before=int(free_before),
                device_free_after=int(free_after),
            ),
            "runtime_total_stable": all(
                row.device_total_bytes == int(total_before) for row in observations
            ),
            "all_numeric_finite": all_numeric,
            "laboratory_wall": wall_ms <= POPULATION_WALL_LIMIT_MS,
        }
    )
    return ValidationPopulationReport(
        available_cards=available_cards,
        geometry=MappingProxyType(
            {
                field: int(getattr(geometry, field))
                for field in staged.StageGeometry.__dataclass_fields__
            }
        ),
        allocation=model,
        work=work,
        observed_invocations=MappingProxyType(dict(invocations)),
        telemetry=tuple(observations),
        timings_ms=MappingProxyType(timings),
        errors=errors,
        complete_ten_card_errors=complete_errors,
        chunk_spans=MappingProxyType(
            {
                "source_reference": tuple(cold_spans["source"]),
                "compatible_forward_dot": tuple(forward_dot_spans),
                "source_transpose_dot": tuple(transpose_dot_spans),
            }
        ),
        digests=MappingProxyType(
            {
                "source_before_adjoint": source_digest,
                "compatible": compatible_digest,
                "query_covector": qcov_digest,
                "unique_adjoint": unique_digest,
            }
        ),
        active_unary_allocations=1,
        active_unary_overwrites=2,
        gates=gates,
        wall_ms=wall_ms,
    )


@lru_cache(maxsize=1)
def run_bounded_quotient_validation_seam() -> ValidationSeamReport:
    """Run the only public bounded device seam; it accepts no arguments."""

    for cards in BOUNDARY_CARDS:
        bounded_validation_allocation(cards)
    cp = _cupy_module()
    reports = tuple(_run_population(cards, cp) for cards in BOUNDARY_CARDS)
    return ValidationSeamReport(populations=reports, claims=CLAIMS)
