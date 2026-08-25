"""One-shot literal-45 CUDA contraction target, inert until explicitly called.

Importing this module compiles no target fixture, imports no CuPy, and performs
no target allocation.  ADR-0382 authorizes only the no-argument runner to call
``execute_literal_45_quotient_target`` after its durable header and admission
plumbing are in place.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from itertools import combinations
from math import comb, fsum
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence, TypeVar

import numpy as np

from . import gpu_occupied_card_quotient as bounded
from . import gpu_quotient_staged_scaling as staged
from .literal_45_quotient_liveness import (
    LITERAL_45_LIVENESS_REPORT,
    VALIDATION_CHUNK_BYTES,
    chunk_spans,
    staged_family_automaton,
)
from .literal_45_quotient_target_result import (
    CLAIMS,
    COMPATIBLE_REFERENCE_BYTES,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_PEAK_BYTES,
    DEVICE_RESERVE_BYTES,
    ERROR_LIMITS,
    EXPECTED_INVOCATIONS,
    FEATURE_WIDTH,
    HOST_NUMERIC_CAP_BYTES,
    HOST_PEAK_BYTES,
    HOST_RESERVE_BYTES,
    OWNER_PROTOCOL_SHA256,
    PHASE_POOL_LIMITS,
    QUERY_SAMPLE_FEATURES,
    QUERY_SAMPLE_RANKS,
    REQUIRED_RUNTIME,
    SOURCE_REFERENCE_BYTES,
    SOURCE_SAMPLE_RANKS,
    TARGET_WALL_LIMIT_MS,
    TELEMETRY_TRANSITIONS,
    target_geometry,
    target_work,
)
from .windows_process_memory import typed_windows_memory_snapshot


AVAILABLE_CARDS = 45
SOURCE_CARDS = 6
QUERY_CARDS = 4
SOURCE_LABELS = 90
QUERY_LABELS = 6
SOURCE_RANK = 127
STRENGTH_CODES = 43

_TARGET_EXECUTION_CALLS = 0
_TARGET_NUMERIC_ALLOCATION_CALLS = 0
_TARGET_SCIENTIFIC_CALLS = 0
_CUPY_IMPORT_CALLS = 0

_T = TypeVar("_T")


def target_execution_call_count() -> int:
    return _TARGET_EXECUTION_CALLS


def target_numeric_allocation_call_count() -> int:
    return _TARGET_NUMERIC_ALLOCATION_CALLS


def target_scientific_call_count() -> int:
    return _TARGET_SCIENTIFIC_CALLS


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


@dataclass(frozen=True, slots=True)
class TargetAllocationFailure(Exception):
    birth: str
    failure_type: str
    message: str

    def __str__(self) -> str:
        return f"{self.birth}: {self.failure_type}: {self.message}"


def _is_allocation_error(error: BaseException) -> bool:
    return isinstance(error, MemoryError) or type(error).__name__ in {
        "OutOfMemoryError",
        "MemoryAllocationError",
    }


def _allocate(label: str, builder: Callable[[], _T]) -> _T:
    global _TARGET_NUMERIC_ALLOCATION_CALLS
    if not isinstance(label, str) or not label:
        raise ValueError("target allocation labels must be nonempty")
    _TARGET_NUMERIC_ALLOCATION_CALLS += 1
    try:
        return builder()
    except BaseException as error:
        if _is_allocation_error(error):
            raise TargetAllocationFailure(
                birth=label,
                failure_type=type(error).__name__,
                message=str(error) or "numeric allocation failed",
            ) from error
        raise


def _readonly(values: np.ndarray, dtype: object) -> np.ndarray:
    result = np.ascontiguousarray(values, dtype=dtype)
    result.flags.writeable = False
    return result


def compile_literal_45_fixture() -> bounded.FrozenQuotientFixture:
    """Compile the exact host fixture; callers must first pass live admission."""

    geometry = target_geometry()
    cards = geometry["available_cards"]
    if cards != AVAILABLE_CARDS:
        raise AssertionError("literal-45 fixture geometry drifted")
    hands = tuple(combinations(range(cards), 2))
    hand_id = {hand: index for index, hand in enumerate(hands)}
    pair_to_hand = np.full((cards, cards), -1, dtype=np.int32)
    for hand, index in hand_id.items():
        pair_to_hand[hand] = index
        pair_to_hand[hand[::-1]] = index

    automaton = staged_family_automaton(cards)
    offsets = np.asarray(
        (
            0,
            geometry["hand_width"],
            2 * geometry["hand_width"],
            3 * geometry["hand_width"],
            3 * geometry["hand_width"] + 1,
            4 * geometry["hand_width"] + 1,
        ),
        dtype=np.int32,
    )
    total = 5 * geometry["hand_width"] + 1
    unary = np.empty((1, total), dtype=np.float64)
    factors = np.empty_like(unary)
    widths = (
        geometry["hand_width"],
        geometry["hand_width"],
        geometry["hand_width"],
        1,
        geometry["hand_width"],
        geometry["hand_width"],
    )
    for seat, width in enumerate(widths):
        for hand in range(width):
            position = int(offsets[seat]) + hand
            unary[0, position] = (
                ((cards + 3) * (seat + 5) * (hand + 7)) % 31 + 1
            ) / 127.0
            factors[0, position] = (
                ((cards + 7) * (seat + 3) + hand * 5) % 29 + 1
            ) / 113.0
            if seat != 3 and (cards * 13 + seat * 17 + hand) % 211 == 0:
                unary[0, position] = 0.0

    query_records = geometry["labeled_query_records"]
    query_masks = np.empty(query_records, dtype=np.uint64)
    query_indices = np.empty((query_records, 2), dtype=np.int32)
    query_pairings = staged._pairings(QUERY_CARDS, 2)
    cursor = 0
    for occupancy_rank in range(geometry["query_occupancies"]):
        occupancy = bounded.colex_unrank(
            occupancy_rank, cards, QUERY_CARDS
        )
        mask = sum(1 << card for card in occupancy)
        for pairing in query_pairings:
            first = tuple(
                sorted((occupancy[pairing[0]], occupancy[pairing[1]]))
            )
            second = tuple(
                sorted((occupancy[pairing[2]], occupancy[pairing[3]]))
            )
            query_masks[cursor] = mask
            query_indices[cursor] = (hand_id[first], hand_id[second])
            cursor += 1
    if cursor != query_records:
        raise AssertionError("literal-45 query compiler omitted a labeled record")

    fixture = bounded.FrozenQuotientFixture(
        available_cards=cards,
        hands=hands,
        automaton=automaton,
        unary_weights=_readonly(unary, np.float64),
        mode_factors=_readonly(factors, np.float64),
        mixture_weights=_readonly(np.asarray((0.61,), dtype=np.float64), np.float64),
        pair_to_hand=_readonly(pair_to_hand, np.int32),
        source_pair_positions=_readonly(
            np.asarray(staged._pairings(SOURCE_CARDS, 3), dtype=np.int8),
            np.int8,
        ),
        query_masks=_readonly(query_masks, np.uint64),
        query_hand_indices=_readonly(query_indices, np.int32),
        unary_offsets=_readonly(offsets, np.int32),
    )
    if fixture.source_rank != SOURCE_RANK or fixture.feature_width != FEATURE_WIDTH:
        raise AssertionError("literal-45 direct automaton rank drifted")
    return fixture


def source_refresh_fixture(
    fixture: bounded.FrozenQuotientFixture,
) -> bounded.FrozenQuotientFixture:
    values = fixture.unary_weights.copy()
    start = int(fixture.unary_offsets[1])
    for hand in range(len(fixture.hands)):
        values[0, start + hand] *= 1.03 + (hand % 7) * 0.001
    values.flags.writeable = False
    return replace(fixture, unary_weights=values)


def query_only_fixture(
    fixture: bounded.FrozenQuotientFixture,
) -> bounded.FrozenQuotientFixture:
    values = fixture.unary_weights.copy()
    start = int(fixture.unary_offsets[4])
    for hand in range(len(fixture.hands)):
        values[0, start + hand] *= 0.97 + (hand % 5) * 0.002
    values.flags.writeable = False
    return replace(fixture, unary_weights=values)


def target_sample_ranks(*, lane: str) -> tuple[int, ...]:
    if lane not in {"source", "query"}:
        raise ValueError("literal-45 sample lane must be source or query")
    population = comb(AVAILABLE_CARDS, SOURCE_CARDS if lane == "source" else QUERY_CARDS)
    count = 16 if lane == "source" else 8
    selected = [0, population - 1]
    occupied = set(selected)
    for index in range(count - 2):
        label = (
            f"pontius|adr-0382|target=45|lane={lane}|index={index}"
        )
        candidate = int.from_bytes(sha256(label.encode("ascii")).digest(), "big")
        candidate %= population
        while candidate in occupied:
            candidate = (candidate + 1) % population
        selected.append(candidate)
        occupied.add(candidate)
    result = tuple(selected)
    expected = SOURCE_SAMPLE_RANKS if lane == "source" else QUERY_SAMPLE_RANKS
    if result != expected:
        raise AssertionError("literal-45 independent sample ranks drifted")
    return result


def target_model() -> dict[str, object]:
    report = LITERAL_45_LIVENESS_REPORT
    if (
        report.host_peak_bytes != HOST_PEAK_BYTES
        or report.device_peak_bytes != DEVICE_PEAK_BYTES
    ):
        raise AssertionError("literal-45 liveness peak drifted")
    return {
        "host_numeric_cap_bytes": HOST_NUMERIC_CAP_BYTES,
        "device_numeric_cap_bytes": DEVICE_NUMERIC_CAP_BYTES,
        "host_reserve_bytes": HOST_RESERVE_BYTES,
        "device_reserve_bytes": DEVICE_RESERVE_BYTES,
        "host_peak_bytes": HOST_PEAK_BYTES,
        "device_peak_bytes": DEVICE_PEAK_BYTES,
        "source_reference_bytes": SOURCE_REFERENCE_BYTES,
        "compatible_reference_bytes": COMPATIBLE_REFERENCE_BYTES,
        "source_reference_chunks": len(chunk_spans(SOURCE_REFERENCE_BYTES)),
        "compatible_reference_chunks": len(chunk_spans(COMPATIBLE_REFERENCE_BYTES)),
        "phase_pool_limits": dict(PHASE_POOL_LIMITS),
    }


def _runtime_identity(cp: Any) -> dict[str, object]:
    properties = cp.cuda.runtime.getDeviceProperties(int(cp.cuda.Device().id))
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "compute_capability": str(cp.cuda.Device().compute_capability),
        "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "cupy_version": str(cp.__version__),
        "device_name": str(name),
        "device_total_bytes": int(properties["totalGlobalMem"]),
    }


def _memory_fields() -> dict[str, int]:
    snapshot = typed_windows_memory_snapshot()
    return {
        "host_total_physical_bytes": int(snapshot["host_total_physical_bytes"]),
        "host_available_physical_bytes": int(
            snapshot["host_available_physical_bytes"]
        ),
        "process_working_set_bytes": int(snapshot["process_working_set_bytes"]),
        "process_private_bytes": int(snapshot["process_private_bytes"]),
    }


def _telemetry_row(
    *,
    cp: Any,
    default_pool: Any,
    pinned_pool: Any,
    transition: str,
    owned_arrays: Sequence[str],
) -> dict[str, object]:
    if transition not in TELEMETRY_TRANSITIONS:
        raise ValueError("literal-45 telemetry transition is unknown")
    cp.cuda.get_current_stream().synchronize()
    free, total = cp.cuda.runtime.memGetInfo()
    host = _memory_fields()
    return {
        "transition": transition,
        "owned_arrays": list(owned_arrays),
        "pool_used_bytes": int(default_pool.used_bytes()),
        "pool_total_bytes": int(default_pool.total_bytes()),
        "pinned_free_blocks": int(pinned_pool.n_free_blocks()),
        "device_free_bytes": int(free),
        "device_total_bytes": int(total),
        "host_available_physical_bytes": host["host_available_physical_bytes"],
        "process_working_set_bytes": host["process_working_set_bytes"],
        "process_private_bytes": host["process_private_bytes"],
        "modeled_pool_limit_bytes": PHASE_POOL_LIMITS[transition],
    }


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


def _device_array(label: str, builder: Callable[[], _T]) -> _T:
    return _allocate(label, builder)


def _allocate_forward(
    cp: Any,
    fixture: bounded.FrozenQuotientFixture,
    kernels: Mapping[str, object],
    staged_kernels: Mapping[str, object],
) -> _ForwardState:
    geometry = target_geometry()
    offsets = bounded.cardinality_offsets(AVAILABLE_CARDS, SOURCE_CARDS)
    return _ForwardState(
        cp=cp,
        kernels=kernels,
        staged_kernels=staged_kernels,
        fixture=fixture,
        table=_device_array(
            "device_source_recurrence",
            lambda: cp.empty(
                (geometry["source_recurrence_rows"], FEATURE_WIDTH),
                dtype=cp.float64,
            ),
        ),
        compatible=_device_array(
            "device_compatible_queries",
            lambda: cp.empty(
                (geometry["labeled_query_records"], FEATURE_WIDTH),
                dtype=cp.float64,
            ),
        ),
        numerator=_device_array(
            "device_query_numerator",
            lambda: cp.empty(geometry["labeled_query_records"], dtype=cp.float64),
        ),
        reach=_device_array(
            "device_query_reach",
            lambda: cp.empty(geometry["labeled_query_records"], dtype=cp.float64),
        ),
        pairings=_device_array(
            "device_source_pairings",
            lambda: cp.asarray(fixture.source_pair_positions, dtype=cp.int8),
        ),
        pair_to_hand=_device_array(
            "device_pair_to_hand",
            lambda: cp.asarray(fixture.pair_to_hand, dtype=cp.int32),
        ),
        active_unary=_device_array(
            "device_active_unary",
            lambda: cp.asarray(fixture.unary_weights, dtype=cp.float64),
        ),
        factors=_device_array(
            "device_mode_factors",
            lambda: cp.asarray(fixture.mode_factors, dtype=cp.float64),
        ),
        unary_offsets=_device_array(
            "device_unary_offsets",
            lambda: cp.asarray(fixture.unary_offsets, dtype=cp.int32),
        ),
        cardinality_offsets=_device_array(
            "device_cardinality_offsets",
            lambda: cp.asarray(offsets, dtype=cp.int64),
        ),
        transitions=tuple(
            _device_array(
                f"device_automaton_transition_{index}",
                lambda values=values: cp.asarray(values, dtype=cp.int32),
            )
            for index, values in enumerate(fixture.automaton.transitions)
        ),
        terminal=_device_array(
            "device_automaton_terminal_values",
            lambda: cp.asarray(
                fixture.automaton.terminal_winner_values, dtype=cp.float64
            ),
        ),
        mixture=_device_array(
            "device_mixture",
            lambda: cp.asarray(fixture.mixture_weights, dtype=cp.float64),
        ),
        query_masks=_device_array(
            "device_query_masks",
            lambda: cp.asarray(fixture.query_masks, dtype=cp.uint64),
        ),
        query_hands=_device_array(
            "device_query_hand_indices",
            lambda: cp.asarray(fixture.query_hand_indices, dtype=cp.int32),
        ),
        level_offsets=offsets,
    )


def _source_view(state: _ForwardState):
    start = state.level_offsets[SOURCE_CARDS]
    return state.table[start : start + target_geometry()["source_occupancies"]]


def _source_kernel(state: _ForwardState) -> float:
    geometry = target_geometry()
    source_offset = state.level_offsets[SOURCE_CARDS]

    def operation() -> None:
        staged._launch(
            state.kernels["source_coefficients"],
            geometry["source_occupancies"],
            (
                state.table,
                np.int64(source_offset),
                np.int32(FEATURE_WIDTH),
                np.int64(geometry["source_occupancies"]),
                np.int32(AVAILABLE_CARDS),
                np.int32(geometry["hand_width"]),
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
        available_cards=AVAILABLE_CARDS,
        source_cards=SOURCE_CARDS,
        feature_width=FEATURE_WIDTH,
    )


def _signed_query_kernel(state: _ForwardState) -> float:
    geometry = target_geometry()

    def operation() -> None:
        staged._launch(
            state.kernels["signed_targets"],
            geometry["labeled_query_records"] * FEATURE_WIDTH,
            (
                state.table,
                state.cardinality_offsets,
                np.int32(SOURCE_CARDS),
                state.query_masks,
                np.int32(0),
                np.int32(QUERY_CARDS),
                np.int64(geometry["labeled_query_records"]),
                np.int32(AVAILABLE_CARDS),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                state.compatible,
            ),
        )

    return staged._cuda_timed(state.cp, operation)


def _fold_kernel(state: _ForwardState) -> float:
    geometry = target_geometry()

    def operation() -> None:
        staged._launch(
            state.kernels["fold_query"],
            geometry["labeled_query_records"],
            (
                state.compatible,
                np.int64(geometry["labeled_query_records"]),
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
                np.int32(geometry["hand_width"]),
                np.float64(state.fixture.automaton.sunk_value),
                np.int32(0),
                state.numerator,
                state.reach,
            ),
        )

    return staged._cuda_timed(state.cp, operation)


def _copy_device_reference(
    device: Any, host: np.ndarray, staging: np.ndarray
) -> tuple[tuple[int, int], ...]:
    if host.dtype != np.float64 or not host.flags.c_contiguous:
        raise ValueError("literal-45 host reference must be contiguous Float64")
    if int(device.size) != int(host.size):
        raise ValueError("literal-45 device and host reference sizes differ")
    spans = chunk_spans(host.nbytes, VALIDATION_CHUNK_BYTES)
    host_flat = host.reshape(-1)
    device_flat = device.reshape(-1)
    for byte_start, byte_stop in spans:
        start = byte_start // 8
        stop = byte_stop // 8
        count = stop - start
        device_flat[start:stop].get(out=staging[:count], blocking=True)
        host_flat[start:stop] = staging[:count]
    return spans


def _compare_device_reference(
    device: Any, host: np.ndarray, staging: np.ndarray
) -> bool:
    if int(device.size) != int(host.size):
        return False
    host_flat = host.reshape(-1)
    device_flat = device.reshape(-1)
    for byte_start, byte_stop in chunk_spans(host.nbytes, VALIDATION_CHUNK_BYTES):
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
) -> dict[str, tuple[tuple[int, int], ...]]:
    return {
        "source": _copy_device_reference(
            _source_view(state), source_reference, staging
        ),
        "compatible": _copy_device_reference(
            state.compatible, compatible_reference, staging
        ),
        "numerator": _copy_device_reference(
            state.numerator, scalar_reference[0], staging
        ),
        "reach": _copy_device_reference(state.reach, scalar_reference[1], staging),
    }


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
            _compare_device_reference(
                state.compatible, compatible_reference, staging
            ),
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
        raise ValueError("literal-45 dot host operand must be contiguous Float64")
    if int(device_right.size) != int(host_left.size):
        raise ValueError("literal-45 dot operands differ in size")
    spans = chunk_spans(host_left.nbytes, VALIDATION_CHUNK_BYTES)
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
    geometry = target_geometry()
    values = _device_array(
        "device_query_covectors",
        lambda: state.cp.empty(
            (geometry["labeled_query_records"], FEATURE_WIDTH),
            dtype=state.cp.float64,
        ),
    )
    staged._launch(
        state.staged_kernels["fill_query_covectors"],
        int(values.size),
        (
            values,
            np.int64(geometry["labeled_query_records"]),
            np.int32(FEATURE_WIDTH),
        ),
    )
    state.cp.cuda.get_current_stream().synchronize()
    return values


def _selected_direct_queries(
    state: _ForwardState,
    occupancy_ranks: tuple[int, ...],
    *,
    on_scientific_call: Callable[[], None],
) -> tuple[np.ndarray, float]:
    cp = state.cp
    masks = np.asarray(
        [
            sum(
                1 << card
                for card in bounded.colex_unrank(
                    rank, AVAILABLE_CARDS, QUERY_CARDS
                )
            )
            for rank in occupancy_ranks
        ],
        dtype=np.uint64,
    )
    device_masks = _device_array(
        "device_direct_query_masks", lambda: cp.asarray(masks, dtype=cp.uint64)
    )
    features = _device_array(
        "device_direct_features",
        lambda: cp.asarray(QUERY_SAMPLE_FEATURES, dtype=cp.int32),
    )
    output = _device_array(
        "device_direct_outputs",
        lambda: cp.empty(
            (len(occupancy_ranks), len(QUERY_SAMPLE_FEATURES)),
            dtype=cp.float64,
        ),
    )

    def operation() -> None:
        staged._launch(
            state.staged_kernels["direct_selected_queries"],
            len(occupancy_ranks) * len(QUERY_SAMPLE_FEATURES),
            (
                _source_view(state),
                np.int64(target_geometry()["source_occupancies"]),
                np.int32(AVAILABLE_CARDS),
                np.int32(FEATURE_WIDTH),
                device_masks,
                np.int32(len(occupancy_ranks)),
                features,
                np.int32(len(QUERY_SAMPLE_FEATURES)),
                output,
            ),
        )

    on_scientific_call()
    wall = staged._cuda_timed(cp, operation)
    result = cp.asnumpy(output)
    del output, features, device_masks
    return result, wall


def _adjoint_once(
    cp: Any,
    kernels: Mapping[str, object],
    query_covectors: Any,
    cardinality_offsets: Any,
    table: Any,
    aggregated: Any,
    unique: Any,
) -> dict[str, float]:
    geometry = target_geometry()

    def aggregate_operation() -> None:
        staged._launch(
            kernels["aggregate_query_labels"],
            geometry["query_occupancies"] * FEATURE_WIDTH,
            (
                query_covectors,
                np.int64(geometry["query_occupancies"]),
                np.int32(QUERY_LABELS),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                aggregated,
            ),
        )

    aggregation = staged._cuda_timed(cp, aggregate_operation)
    offsets = bounded.cardinality_offsets(AVAILABLE_CARDS, QUERY_CARDS)
    table[offsets[QUERY_CARDS] : offsets[QUERY_CARDS] + geometry["query_occupancies"]] = aggregated
    recurrence = bounded._fill_recurrence(
        cp,
        kernels,
        table,
        available_cards=AVAILABLE_CARDS,
        source_cards=QUERY_CARDS,
        feature_width=FEATURE_WIDTH,
    )

    def signed_operation() -> None:
        staged._launch(
            kernels["signed_targets"],
            geometry["source_occupancies"] * FEATURE_WIDTH,
            (
                table,
                cardinality_offsets,
                np.int32(QUERY_CARDS),
                cardinality_offsets,
                np.int32(1),
                np.int32(SOURCE_CARDS),
                np.int64(geometry["source_occupancies"]),
                np.int32(AVAILABLE_CARDS),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                unique,
            ),
        )

    signed = staged._cuda_timed(cp, signed_operation)
    return {
        "query_aggregation": aggregation,
        "recurrence": recurrence,
        "signed_source": signed,
        "device_sum": aggregation + recurrence + signed,
    }


def _reporting_digest(values: np.ndarray) -> str:
    if not values.flags.c_contiguous:
        raise ValueError("literal-45 reporting digest requires contiguous bytes")
    return sha256(memoryview(values).cast("B")).hexdigest()


def _blank_scientific_fields() -> dict[str, object]:
    return {
        "work": target_work(),
        "observed_invocations": {key: 0 for key in EXPECTED_INVOCATIONS},
        "identities": {
            "warm_byte_identity": None,
            "source_refresh_byte_identity": None,
            "query_only_byte_identity": None,
            "query_only_source_preserved": None,
            "query_only_compatible_preserved": None,
            "adjoint_byte_identity": None,
            "forward_dot_left": None,
            "forward_dot_right": None,
            "transpose_dot_left": None,
            "transpose_dot_right": None,
        },
        "errors_hex": {key: None for key in ERROR_LIMITS},
        "timings_hex": {},
        "chunks": {},
        "digests": {},
    }


def _base_payload(
    *,
    runtime: Mapping[str, object],
    admission: Mapping[str, int],
    telemetry: Sequence[Mapping[str, object]],
    wall_ms: float,
    allocation_failure: Mapping[str, object] | None,
    scientific: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "literal-45-quotient-target-observation-v1",
        "protocol_sha256": OWNER_PROTOCOL_SHA256,
        "claims": dict(CLAIMS),
        "geometry": target_geometry(),
        "model": target_model(),
        "runtime": dict(runtime),
        "admission": dict(admission),
        "telemetry": [dict(row) for row in telemetry],
        **dict(scientific),
        "counters": {
            "target_execution_calls": _TARGET_EXECUTION_CALLS,
            "target_numeric_allocation_calls": _TARGET_NUMERIC_ALLOCATION_CALLS,
            "target_scientific_call_count": _TARGET_SCIENTIFIC_CALLS,
        },
        "wall_hex": float(wall_ms).hex(),
        "allocation_failure": (
            None if allocation_failure is None else dict(allocation_failure)
        ),
    }


def execute_literal_45_quotient_target() -> dict[str, object]:
    """Execute the literal target once; the durable runner is the sole caller."""

    global _TARGET_EXECUTION_CALLS, _TARGET_SCIENTIFIC_CALLS
    if _TARGET_EXECUTION_CALLS != 0:
        raise RuntimeError("literal-45 target is single-call within its fresh process")
    _TARGET_EXECUTION_CALLS += 1
    started = perf_counter()

    cp = _cupy_module()
    runtime = _runtime_identity(cp)
    kernels = bounded._kernels(cp)
    staged_kernels = staged._staged_kernels(cp)
    default_pool = cp.get_default_memory_pool()
    pinned_pool = cp.get_default_pinned_memory_pool()
    cp.cuda.get_current_stream().synchronize()
    import gc

    gc.collect()
    default_pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    cp.cuda.get_current_stream().synchronize()

    telemetry: list[dict[str, object]] = []
    before = _telemetry_row(
        cp=cp,
        default_pool=default_pool,
        pinned_pool=pinned_pool,
        transition="before_allocation",
        owned_arrays=(),
    )
    telemetry.append(before)
    host = _memory_fields()
    admission = {
        "host_total_physical_bytes": host["host_total_physical_bytes"],
        "host_available_physical_bytes": int(
            before["host_available_physical_bytes"]
        ),
        "process_working_set_bytes": int(before["process_working_set_bytes"]),
        "process_private_bytes": int(before["process_private_bytes"]),
        "device_free_bytes": int(before["device_free_bytes"]),
        "device_total_bytes": int(before["device_total_bytes"]),
        "pool_used_bytes": int(before["pool_used_bytes"]),
        "pool_total_bytes": int(before["pool_total_bytes"]),
        "pinned_free_blocks": int(before["pinned_free_blocks"]),
        "target_numeric_allocation_calls": _TARGET_NUMERIC_ALLOCATION_CALLS,
        "target_scientific_call_count": _TARGET_SCIENTIFIC_CALLS,
    }
    admission_pass = (
        HOST_PEAK_BYTES <= HOST_NUMERIC_CAP_BYTES
        and DEVICE_PEAK_BYTES <= DEVICE_NUMERIC_CAP_BYTES
        and HOST_PEAK_BYTES + HOST_RESERVE_BYTES
        <= admission["host_available_physical_bytes"]
        and DEVICE_PEAK_BYTES + DEVICE_RESERVE_BYTES
        <= admission["device_free_bytes"]
        and runtime == REQUIRED_RUNTIME
        and admission["device_total_bytes"] == REQUIRED_RUNTIME["device_total_bytes"]
        and admission["pool_used_bytes"] == 0
        and admission["pool_total_bytes"] == 0
        and admission["pinned_free_blocks"] == 0
        and admission["target_numeric_allocation_calls"] == 0
        and admission["target_scientific_call_count"] == 0
    )
    if not admission_pass:
        return _base_payload(
            runtime=runtime,
            admission=admission,
            telemetry=telemetry,
            wall_ms=(perf_counter() - started) * 1000.0,
            allocation_failure=None,
            scientific=_blank_scientific_fields(),
        )

    geometry = target_geometry()
    fixture = refreshed_fixture = query_fixture = None
    state = None
    source_reference = compatible_reference = scalar_reference = staging_buffer = None
    source_rank_device = source_sample_device = None
    source_actual = source_expected = direct_actual = direct_expected = None
    query_covectors = cardinality_offsets = None
    adjoint_table = aggregated = unique_adjoint = None
    last_completed = "before_allocation"
    allocation_failure: TargetAllocationFailure | None = None
    timings: dict[str, float] = {}
    identities: dict[str, object] = {}
    errors: dict[str, float] = {}
    chunk_rows: dict[str, tuple[tuple[int, int], ...]] = {}
    digests: dict[str, str] = {}
    invocations = {key: 0 for key in EXPECTED_INVOCATIONS}

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

    def observe(transition: str, owned: Sequence[str]) -> None:
        nonlocal last_completed
        telemetry.append(
            _telemetry_row(
                cp=cp,
                default_pool=default_pool,
                pinned_pool=pinned_pool,
                transition=transition,
                owned_arrays=owned,
            )
        )
        last_completed = transition

    def guard() -> None:
        if (perf_counter() - started) * 1000.0 > TARGET_WALL_LIMIT_MS:
            raise TimeoutError("literal-45 laboratory wall guard crossed")

    def forward(*, rebuild_source: bool) -> dict[str, float]:
        nonlocal state
        global _TARGET_SCIENTIFIC_CALLS
        if state is None:
            raise RuntimeError("literal-45 forward state is absent")
        guard()
        source = 0.0
        recurrence = 0.0
        if rebuild_source:
            invocations["source_build_invocations"] += 1
            _TARGET_SCIENTIFIC_CALLS += 1
            source = _source_kernel(state)
            recurrence = _recurrence_kernel(state)
        invocations["signed_query_invocations"] += 1
        invocations["affine_fold_invocations"] += 1
        _TARGET_SCIENTIFIC_CALLS += 2
        signed = _signed_query_kernel(state)
        fold = _fold_kernel(state)
        return {
            "source_coefficients": source,
            "recurrence": recurrence,
            "signed_query": signed,
            "affine_fold": fold,
            "device_sum": source + recurrence + signed + fold,
        }

    try:
        fixture = _allocate("host_fixture", compile_literal_45_fixture)
        refreshed_fixture = _allocate(
            "host_refreshed_unary", lambda: source_refresh_fixture(fixture)
        )
        query_fixture = _allocate(
            "host_query_unary", lambda: query_only_fixture(refreshed_fixture)
        )
        state = _allocate_forward(cp, fixture, kernels, staged_kernels)
        invocations["active_unary_allocations"] = 1
        observe("forward_allocated", forward_owned)

        source_reference = _allocate(
            "host_large_reference_buffer",
            lambda: np.empty(
                (geometry["source_occupancies"], FEATURE_WIDTH), dtype=np.float64
            ),
        )
        compatible_reference = _allocate(
            "host_compatible_reference_buffer",
            lambda: np.empty(
                (geometry["labeled_query_records"], FEATURE_WIDTH),
                dtype=np.float64,
            ),
        )
        scalar_reference = _allocate(
            "host_scalar_reference_buffer",
            lambda: np.empty(
                (2, geometry["labeled_query_records"]), dtype=np.float64
            ),
        )
        staging_buffer = _allocate(
            "host_validation_staging",
            lambda: np.empty(VALIDATION_CHUNK_BYTES // 8, dtype=np.float64),
        )

        timings["cold"] = forward(rebuild_source=True)["device_sum"]
        cold_spans = _copy_forward_references(
            state,
            source_reference,
            compatible_reference,
            scalar_reference,
            staging_buffer,
        )
        observe("cold_reference_copied", forward_owned)

        timings["warm"] = forward(rebuild_source=True)["device_sum"]
        identities["warm_byte_identity"] = _compare_forward_references(
            state,
            source_reference,
            compatible_reference,
            scalar_reference,
            staging_buffer,
        )
        observe("warm_validated", forward_owned)

        state.active_unary.set(refreshed_fixture.unary_weights)
        invocations["active_unary_overwrites"] += 1
        timings["source_refresh"] = forward(rebuild_source=True)["device_sum"]
        refresh_spans = _copy_forward_references(
            state,
            source_reference,
            compatible_reference,
            scalar_reference,
            staging_buffer,
        )
        observe("refresh_reference_rebound", forward_owned)
        timings["source_refresh_repeat"] = forward(rebuild_source=True)["device_sum"]
        identities["source_refresh_byte_identity"] = _compare_forward_references(
            state,
            source_reference,
            compatible_reference,
            scalar_reference,
            staging_buffer,
        )
        observe("refresh_validated", forward_owned)

        state.active_unary.set(query_fixture.unary_weights)
        invocations["active_unary_overwrites"] += 1
        timings["query_only"] = forward(rebuild_source=False)["device_sum"]
        identities["query_only_source_preserved"] = _compare_device_reference(
            _source_view(state), source_reference, staging_buffer
        )
        identities["query_only_compatible_preserved"] = _compare_device_reference(
            state.compatible, compatible_reference, staging_buffer
        )
        _copy_device_reference(state.numerator, scalar_reference[0], staging_buffer)
        _copy_device_reference(state.reach, scalar_reference[1], staging_buffer)
        observe("query_reference_rebound", forward_owned)
        timings["query_only_repeat"] = forward(rebuild_source=False)["device_sum"]
        identities["query_only_byte_identity"] = _compare_forward_references(
            state,
            source_reference,
            compatible_reference,
            scalar_reference,
            staging_buffer,
        )
        observe("query_validated", forward_owned)

        source_ranks = target_sample_ranks(lane="source")
        query_ranks = target_sample_ranks(lane="query")
        source_rank_device = _device_array(
            "device_direct_source_ranks",
            lambda: cp.asarray(source_ranks, dtype=cp.int64),
        )
        source_sample_device = _device_array(
            "device_sample_workspace",
            lambda: cp.take(_source_view(state), source_rank_device, axis=0),
        )
        source_actual = cp.asnumpy(source_sample_device)
        source_rank_device = source_sample_device = None
        source_expected = staged._source_sample_exact(refreshed_fixture, source_ranks)
        source_error, _ = staged._maximum_errors(source_actual, source_expected)
        def record_direct_scan() -> None:
            global _TARGET_SCIENTIFIC_CALLS
            invocations["direct_scan_invocations"] += 1
            _TARGET_SCIENTIFIC_CALLS += 1

        direct_actual, timings["direct"] = _selected_direct_queries(
            state,
            query_ranks,
            on_scientific_call=record_direct_scan,
        )
        record_indices = tuple(rank * QUERY_LABELS for rank in query_ranks)
        direct_expected = compatible_reference[list(record_indices)][
            :, QUERY_SAMPLE_FEATURES
        ]
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
        errors.update(
            {
                "source_sample_absolute": source_error,
                "direct_query_absolute": direct_error,
                "direct_query_relative": direct_relative,
                "affine_sample_absolute": affine_error,
            }
        )
        source_rank_device = source_sample_device = None
        source_actual = source_expected = direct_actual = direct_expected = None
        compatible_selected = expected_numerator = expected_reach = None
        gc.collect()
        observe("direct_validated", forward_owned)

        query_covectors = _fill_query_covectors(state)
        forward_dot_owned = (*forward_owned, "query_covector")
        observe("query_covector_allocated", forward_dot_owned)
        forward_dot, forward_spans, qcov_digest = _streamed_device_host_dot(
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
        compatible_digest = _reporting_digest(compatible_reference)
        compatible_reference = None
        scalar_reference = None
        gc.collect()
        default_pool.free_all_blocks()
        cp.cuda.get_current_stream().synchronize()
        post_forward_owned = ("query_covector", "cardinality_offsets")
        observe("forward_released", post_forward_owned)

        adjoint_table = _device_array(
            "device_adjoint_recurrence",
            lambda: cp.empty(
                (geometry["adjoint_recurrence_rows"], FEATURE_WIDTH),
                dtype=cp.float64,
            ),
        )
        aggregated = _device_array(
            "device_adjoint_aggregated_queries",
            lambda: cp.empty(
                (geometry["query_occupancies"], FEATURE_WIDTH), dtype=cp.float64
            ),
        )
        unique_adjoint = _device_array(
            "device_unique_adjoint",
            lambda: cp.empty(
                (geometry["source_occupancies"], FEATURE_WIDTH), dtype=cp.float64
            ),
        )
        adjoint_owned = (
            "query_covector",
            "cardinality_offsets",
            "adjoint_aggregated",
            "adjoint_recurrence",
            "unique_adjoint",
        )
        observe("adjoint_allocated", adjoint_owned)

        def run_adjoint() -> dict[str, float]:
            global _TARGET_SCIENTIFIC_CALLS
            guard()
            invocations["adjoint_invocations"] += 1
            _TARGET_SCIENTIFIC_CALLS += 1
            return _adjoint_once(
                cp,
                kernels,
                query_covectors,
                cardinality_offsets,
                adjoint_table,
                aggregated,
                unique_adjoint,
            )

        timings["adjoint"] = run_adjoint()["device_sum"]
        observe("adjoint_complete", adjoint_owned)
        transpose_dot, transpose_spans, unique_digest = _streamed_device_host_dot(
            source_reference, unique_adjoint, staging_buffer
        )
        source_digest = _reporting_digest(source_reference)
        dot_error = abs(forward_dot - transpose_dot)
        dot_relative = dot_error / max(1.0, abs(forward_dot), abs(transpose_dot))
        errors["dot_product_absolute"] = dot_error
        errors["dot_product_relative"] = dot_relative

        _copy_device_reference(unique_adjoint, source_reference, staging_buffer)
        observe("adjoint_reference_rebound", adjoint_owned)
        timings["adjoint_repeat"] = run_adjoint()["device_sum"]
        identities["adjoint_byte_identity"] = _compare_device_reference(
            unique_adjoint, source_reference, staging_buffer
        )
        observe("adjoint_repeat_validated", adjoint_owned)

        identities.update(
            {
                "forward_dot_left": "host_compatible_reference",
                "forward_dot_right": "device_query_covector",
                "transpose_dot_left": "host_source_reference",
                "transpose_dot_right": "device_unique_adjoint",
            }
        )
        chunk_rows = {
            "source_reference": tuple(refresh_spans["source"]),
            "compatible_forward_dot": tuple(forward_spans),
            "source_transpose_dot": tuple(transpose_spans),
        }
        if tuple(cold_spans["source"]) != tuple(refresh_spans["source"]):
            raise AssertionError("literal-45 source chunk partition drifted")
        digests = {
            "source_before_adjoint": source_digest,
            "compatible": compatible_digest,
            "query_covector": qcov_digest,
            "unique_adjoint": unique_digest,
        }
    except TargetAllocationFailure as error:
        allocation_failure = error
    finally:
        failure_last_completed = last_completed
        unique_adjoint = adjoint_table = aggregated = None
        query_covectors = cardinality_offsets = None
        if state is not None:
            state.table = None
            state.compatible = None
            state.numerator = None
            state.reach = None
            state.pairings = None
            state.pair_to_hand = None
            state.active_unary = None
            state.factors = None
            state.unary_offsets = None
            state.cardinality_offsets = None
            state.transitions = ()
            state.terminal = None
            state.mixture = None
            state.query_masks = None
            state.query_hands = None
        state = None
        source_reference = compatible_reference = scalar_reference = staging_buffer = None
        source_rank_device = source_sample_device = None
        source_actual = source_expected = direct_actual = direct_expected = None
        query_fixture = refreshed_fixture = fixture = None
        gc.collect()
        default_pool.free_all_blocks()
        pinned_pool.free_all_blocks()
        cp.cuda.get_current_stream().synchronize()
        observe("released", ())
        if allocation_failure is not None:
            last_completed = failure_last_completed

    wall_ms = (perf_counter() - started) * 1000.0
    if allocation_failure is not None:
        failure_payload = {
            "birth": allocation_failure.birth,
            "failure_type": allocation_failure.failure_type,
            "message": allocation_failure.message,
            "last_completed_transition": last_completed,
        }
        scientific = _blank_scientific_fields()
        scientific["observed_invocations"] = dict(invocations)
        return _base_payload(
            runtime=runtime,
            admission=admission,
            telemetry=telemetry,
            wall_ms=wall_ms,
            allocation_failure=failure_payload,
            scientific=scientific,
        )

    scientific = {
        "work": target_work(),
        "observed_invocations": dict(invocations),
        "identities": identities,
        "errors_hex": {key: float(errors[key]).hex() for key in ERROR_LIMITS},
        "timings_hex": {key: float(value).hex() for key, value in timings.items()},
        "chunks": {
            key: [list(span) for span in spans] for key, spans in chunk_rows.items()
        },
        "digests": digests,
    }
    return _base_payload(
        runtime=runtime,
        admission=admission,
        telemetry=telemetry,
        wall_ms=wall_ms,
        allocation_failure=None,
        scientific=scientific,
    )


__all__ = [
    "TargetAllocationFailure",
    "compile_literal_45_fixture",
    "cupy_import_call_count",
    "execute_literal_45_quotient_target",
    "query_only_fixture",
    "source_refresh_fixture",
    "target_execution_call_count",
    "target_model",
    "target_numeric_allocation_call_count",
    "target_sample_ranks",
    "target_scientific_call_count",
]
