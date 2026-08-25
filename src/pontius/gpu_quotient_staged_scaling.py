"""Prospective non-target scaling owner for the occupied-card GPU quotient.

ADR-0373 fixes six complete card universes and stops at forty cards.  This
module is additive: it consumes the hash-sealed ADR-0372 CUDA primitives and
does not modify or widen their public ten-card entry point.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
import json
from math import comb, isfinite
from types import MappingProxyType
from typing import Any

import numpy as np

from . import gpu_occupied_card_quotient as bounded
from .structured_showdown_automaton import build_structured_showdown_automaton


STAGE_CARDS = (10, 16, 22, 28, 34, 40)
TARGET_CARD_COUNT = 45
SOURCE_CARDS = 6
QUERY_CARDS = 4
STRENGTH_CODES = 43
SOURCE_RANK = 127
FEATURE_WIDTH = 128
SOURCE_LABELS = 90
QUERY_LABELS = 6
WARM_REPETITIONS = 5
SOURCE_REFRESH_REPETITIONS = 3
QUERY_ONLY_REPETITIONS = 5
ADJOINT_WARM_REPETITIONS = 3
SOURCE_SAMPLE_COUNT = 16
QUERY_SAMPLE_COUNT = 8
QUERY_SAMPLE_FEATURES = (0, 1, 2, 31, 63, 95, 126, 127)

MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR = 2e-12
MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR = 2e-8
MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR = 2e-11
MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR = 2e-10
MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR = 2e-8
MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR = 1e-10

STAGE_WALL_LIMIT_MS = 120_000.0
CAMPAIGN_WALL_LIMIT_MS = 600_000.0
FIXED_DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
DEVICE_RESERVE_BYTES = 2_000_000_000
MINIMUM_DEVICE_PHYSICAL_BYTES = 16_000_000_000
CUDA_LIBRARY_SCRATCH_BYTES = 67_108_864

REQUIRED_DEVICE_NAME = "NVIDIA GeForce RTX 5080"
REQUIRED_COMPUTE_CAPABILITY = "120"
REQUIRED_CUPY_VERSION = "14.2.0"
REQUIRED_CUDA_RUNTIME_VERSION = 13_020
MINIMUM_CUDA_DRIVER_VERSION = 13_030

RESULT_RELATIVE_PATH = (
    "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl"
)

STAGE_SCHEMA_VERSION = "gpu-quotient-staged-scaling-stage-v1"
STAGE_ERROR_FIELDS = (
    "source_sample_absolute",
    "source_sample_relative",
    "direct_query_absolute",
    "direct_query_relative",
    "affine_sample_absolute",
    "dot_product_absolute",
    "dot_product_relative",
)
STAGE_GATE_FIELDS = (
    "semantic_identity",
    "complete_geometry",
    "source_rank_and_feature_width",
    "fixed_allocation",
    "live_allocation",
    "source_samples",
    "direct_queries",
    "affine_samples",
    "dot_product",
    "warm_byte_identity",
    "source_refresh_byte_identity",
    "query_only_byte_identity",
    "adjoint_byte_identity",
    "refresh_work_equals_cold",
    "query_only_reuses_source",
    "adjoint_unique_only",
    "repetition_counts",
    "memory_pools_released",
    "stage_wall",
    "all_numeric_finite",
    "observed_pool_within_model",
)
STAGE_TIMING_PHASES = MappingProxyType(
    {
        "cold": (
            "source_coefficients",
            "recurrence",
            "signed_query",
            "affine_fold",
            "device_sum",
        ),
        "warm": (
            "source_coefficients",
            "recurrence",
            "signed_query",
            "affine_fold",
            "device_sum",
        ),
        "source_refresh": (
            "source_coefficients",
            "recurrence",
            "signed_query",
            "affine_fold",
            "device_sum",
        ),
        "query_only": (
            "source_coefficients",
            "recurrence",
            "signed_query",
            "affine_fold",
            "device_sum",
        ),
        "direct_query": ("direct_scan",),
        "adjoint": (
            "query_aggregation",
            "recurrence",
            "signed_source",
            "device_sum",
        ),
    }
)
STAGE_TIMING_COUNTS = MappingProxyType(
    {
        "cold": 1,
        "warm": WARM_REPETITIONS,
        "source_refresh": SOURCE_REFRESH_REPETITIONS,
        "query_only": QUERY_ONLY_REPETITIONS,
        "direct_query": 1,
        "adjoint": 1 + ADJOINT_WARM_REPETITIONS,
    }
)
STAGE_HOST_TIMING_FIELDS = (
    "topology",
    "allocation_and_transfer",
    "cold",
    "warm_campaign",
    "source_refresh_campaign",
    "query_only_campaign",
    "adjoint_campaign",
    "validation",
    "stage_total",
)
STAGE_CLAIMS = MappingProxyType(
    {
        "literal_45_card_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "poker_strength_result": None,
    }
)

_PROTOCOL_PAYLOAD: dict[str, object] = {
    "adjoint_record_expansion": "forbidden_unique_source_occupancies_only",
    "adjoint_warm_repetitions": ADJOINT_WARM_REPETITIONS,
    "campaign_wall_limit_ms": int(CAMPAIGN_WALL_LIMIT_MS),
    "claims": dict(STAGE_CLAIMS),
    "cuda_library_scratch_bytes": CUDA_LIBRARY_SCRATCH_BYTES,
    "device_identity": {
        "compute_capability": REQUIRED_COMPUTE_CAPABILITY,
        "cuda_driver_floor": MINIMUM_CUDA_DRIVER_VERSION,
        "cuda_runtime_version": REQUIRED_CUDA_RUNTIME_VERSION,
        "cupy_version": REQUIRED_CUPY_VERSION,
        "device_name": REQUIRED_DEVICE_NAME,
        "minimum_physical_bytes": MINIMUM_DEVICE_PHYSICAL_BYTES,
    },
    "device_numeric_cap_bytes": FIXED_DEVICE_NUMERIC_CAP_BYTES,
    "device_reserve_bytes": DEVICE_RESERVE_BYTES,
    "direct_query_thread_ownership": "one_thread_per_selected_query_feature",
    "feature_width": FEATURE_WIDTH,
    "gate_fields": list(STAGE_GATE_FIELDS),
    "journal": "exclusive_append_flush_fsync_first_terminal_no_retry",
    "numerical_maxima": {
        "affine_sample_absolute": float(
            MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR
        ).hex(),
        "direct_query_absolute": float(
            MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR
        ).hex(),
        "direct_query_relative": float(
            MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR
        ).hex(),
        "dot_product_absolute": float(
            MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR
        ).hex(),
        "dot_product_relative": float(
            MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR
        ).hex(),
        "source_sample_absolute": float(
            MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR
        ).hex(),
    },
    "query_cards": QUERY_CARDS,
    "query_labels": QUERY_LABELS,
    "query_only_repetitions": QUERY_ONLY_REPETITIONS,
    "query_sample_count": QUERY_SAMPLE_COUNT,
    "query_sample_features": list(QUERY_SAMPLE_FEATURES),
    "source_cards": SOURCE_CARDS,
    "source_labels": SOURCE_LABELS,
    "source_rank": SOURCE_RANK,
    "source_refresh_repetitions": SOURCE_REFRESH_REPETITIONS,
    "source_sample_count": SOURCE_SAMPLE_COUNT,
    "stage_cards": list(STAGE_CARDS),
    "stage_error_fields": list(STAGE_ERROR_FIELDS),
    "stage_host_timing_fields": list(STAGE_HOST_TIMING_FIELDS),
    "stage_timing_counts": dict(STAGE_TIMING_COUNTS),
    "stage_timing_phases": dict(STAGE_TIMING_PHASES),
    "stage_wall_limit_ms": int(STAGE_WALL_LIMIT_MS),
    "strength_codes": STRENGTH_CODES,
    "target_card_count": TARGET_CARD_COUNT,
    "target_entry": "structurally_rejected_before_cupy_import",
    "terminal_classes": [
        "completed_pass",
        "completed_stage_rejection",
        "infrastructure_failure",
    ],
    "version": "gpu-quotient-staged-scaling-protocol-v1",
    "warm_repetitions": WARM_REPETITIONS,
}
GPU_QUOTIENT_STAGED_SCALING_PROTOCOL = MappingProxyType(_PROTOCOL_PAYLOAD)
GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _PROTOCOL_PAYLOAD,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
).hexdigest()


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool) or not isinstance(item, int) or item < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return item


def _float_text(value: float) -> str:
    item = float(value)
    if not isfinite(item):
        raise ValueError("staged scaling evidence requires finite Float64")
    return item.hex()


def parse_float_text(value: object, *, label: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be an exact Float64 hexadecimal string")
    try:
        result = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not a Float64 hexadecimal string") from error
    if not isfinite(result) or result.hex() != value:
        raise ValueError(f"{label} is not canonical finite Float64")
    return result


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _semantic_digest(value: object) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _readonly(values: object, dtype: object) -> np.ndarray:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def _mask(cards: Sequence[int]) -> int:
    return sum(1 << int(card) for card in cards)


def _pairings(cards: int, pairs: int) -> tuple[tuple[int, ...], ...]:
    if pairs == 2:
        result = []
        for first in combinations(range(cards), 2):
            remaining = tuple(card for card in range(cards) if card not in first)
            result.append((*first, *remaining))
        return tuple(result)
    if pairs == 3:
        result = []
        for first in combinations(range(cards), 2):
            remaining = tuple(card for card in range(cards) if card not in first)
            for second in combinations(remaining, 2):
                final = tuple(card for card in remaining if card not in second)
                result.append((*first, *second, *final))
        return tuple(result)
    raise ValueError("staged scaling supports only two or three labeled pairs")


@dataclass(frozen=True, slots=True)
class StageGeometry:
    available_cards: int
    hand_width: int
    source_occupancies: int
    labeled_source_visits: int
    query_occupancies: int
    labeled_query_records: int
    recurrence_rows: int
    recurrence_vector_edges: int
    recurrence_scalar_additions: int
    table_plus_query_bytes: int


def stage_geometry(available_cards: int) -> StageGeometry:
    cards = _integer(available_cards, label="stage cards", minimum=1)
    if cards not in STAGE_CARDS:
        if cards == TARGET_CARD_COUNT:
            raise ValueError("literal 45-card target is forbidden in staged scaling")
        raise ValueError("card universe is outside the frozen staged ladder")
    source = comb(cards, SOURCE_CARDS)
    query_occupancies = comb(cards, QUERY_CARDS)
    query_records = query_occupancies * QUERY_LABELS
    rows = sum(comb(cards, width) for width in range(SOURCE_CARDS + 1))
    edges = sum(
        comb(cards, width) * (cards - width)
        for width in range(SOURCE_CARDS)
    )
    return StageGeometry(
        available_cards=cards,
        hand_width=comb(cards, 2),
        source_occupancies=source,
        labeled_source_visits=source * SOURCE_LABELS,
        query_occupancies=query_occupancies,
        labeled_query_records=query_records,
        recurrence_rows=rows,
        recurrence_vector_edges=edges,
        recurrence_scalar_additions=edges * FEATURE_WIDTH,
        table_plus_query_bytes=(rows + query_records)
        * FEATURE_WIDTH
        * np.dtype(np.float64).itemsize,
    )


@dataclass(frozen=True, slots=True)
class StageAllocation:
    available_cards: int
    static_device_bytes: int
    forward_base_bytes: int
    warm_forward_peak_bytes: int
    query_only_peak_bytes: int
    adjoint_peak_bytes: int
    dot_product_peak_bytes: int
    requested_device_peak_bytes: int
    fixed_cap_pass: bool
    physical_reserve_pass: bool
    live_free_bytes: int | None
    live_reserve_pass: bool | None
    arrays: Mapping[str, int]

    @property
    def all_available_gates_pass(self) -> bool:
        return (
            self.fixed_cap_pass
            and self.physical_reserve_pass
            and self.live_reserve_pass is not False
        )


def stage_allocation(
    fixture: bounded.FrozenQuotientFixture,
    *,
    live_free_bytes: int | None = None,
) -> StageAllocation:
    cards = fixture.available_cards
    geometry = stage_geometry(cards)
    if fixture.source_rank != SOURCE_RANK or fixture.feature_width != FEATURE_WIDTH:
        raise ValueError("stage fixture rank/feature width differs from ADR-0373")
    live = (
        None
        if live_free_bytes is None
        else _integer(live_free_bytes, label="live free bytes")
    )
    float_bytes = np.dtype(np.float64).itemsize
    int_bytes = np.dtype(np.int32).itemsize
    uint64_bytes = np.dtype(np.uint64).itemsize
    source_feature_bytes = (
        geometry.source_occupancies * FEATURE_WIDTH * float_bytes
    )
    compatible_bytes = (
        geometry.labeled_query_records * FEATURE_WIDTH * float_bytes
    )
    scalar_output_bytes = geometry.labeled_query_records * float_bytes * 2
    source_table_bytes = geometry.recurrence_rows * FEATURE_WIDTH * float_bytes
    query_topology_bytes = geometry.labeled_query_records * (
        uint64_bytes + 2 * int_bytes
    )
    static = {
        "query_topology": query_topology_bytes,
        "pair_to_hand": cards * cards * int_bytes,
        "source_pair_positions": SOURCE_LABELS * SOURCE_CARDS,
        "three_unary_variants_and_mode_factors": (
            fixture.unary_weights.size * float_bytes * 4
        ),
        "mixture": fixture.mixture_weights.nbytes,
        "unary_offsets": fixture.unary_offsets.nbytes,
        "direct_automaton": fixture.automaton.runtime_numeric_bytes,
        "cardinality_offsets": (SOURCE_CARDS + 1) * np.dtype(np.int64).itemsize,
        "diagnostic_indices": (
            SOURCE_SAMPLE_COUNT * np.dtype(np.int64).itemsize
            + QUERY_SAMPLE_COUNT * uint64_bytes
            + len(QUERY_SAMPLE_FEATURES) * int_bytes
        ),
    }
    static_bytes = sum(static.values())
    forward_base = (
        static_bytes
        + source_table_bytes
        + compatible_bytes
        + scalar_output_bytes
        + CUDA_LIBRARY_SCRATCH_BYTES
    )
    warm_peak = (
        forward_base
        + source_feature_bytes
        + compatible_bytes
        + scalar_output_bytes
    )
    query_only_peak = forward_base + compatible_bytes + scalar_output_bytes

    adjoint_rows = sum(comb(cards, width) for width in range(QUERY_CARDS + 1))
    query_covector_bytes = compatible_bytes
    aggregated_query_bytes = (
        geometry.query_occupancies * FEATURE_WIDTH * float_bytes
    )
    adjoint_table_bytes = adjoint_rows * FEATURE_WIDTH * float_bytes
    unique_adjoint_bytes = source_feature_bytes
    adjoint_peak = (
        static_bytes
        + query_covector_bytes
        + aggregated_query_bytes
        + adjoint_table_bytes
        + 2 * unique_adjoint_bytes
        + CUDA_LIBRARY_SCRATCH_BYTES
    )
    dot_product_peak = (
        static_bytes
        + source_table_bytes
        + compatible_bytes
        + scalar_output_bytes
        + query_covector_bytes
        + aggregated_query_bytes
        + adjoint_table_bytes
        + unique_adjoint_bytes
        + CUDA_LIBRARY_SCRATCH_BYTES
    )
    arrays = {
        **static,
        "source_recurrence_table": source_table_bytes,
        "compatible_query_features": compatible_bytes,
        "query_scalar_outputs": scalar_output_bytes,
        "warm_source_reference": source_feature_bytes,
        "warm_query_reference": compatible_bytes + scalar_output_bytes,
        "adjoint_query_covectors": query_covector_bytes,
        "adjoint_aggregated_queries": aggregated_query_bytes,
        "adjoint_recurrence_table": adjoint_table_bytes,
        "adjoint_current_and_reference": 2 * unique_adjoint_bytes,
        "cuda_library_scratch_allowance": CUDA_LIBRARY_SCRATCH_BYTES,
    }
    peak = max(
        warm_peak,
        query_only_peak,
        adjoint_peak,
        dot_product_peak,
    )
    return StageAllocation(
        available_cards=cards,
        static_device_bytes=static_bytes,
        forward_base_bytes=forward_base,
        warm_forward_peak_bytes=warm_peak,
        query_only_peak_bytes=query_only_peak,
        adjoint_peak_bytes=adjoint_peak,
        dot_product_peak_bytes=dot_product_peak,
        requested_device_peak_bytes=peak,
        fixed_cap_pass=peak <= FIXED_DEVICE_NUMERIC_CAP_BYTES,
        physical_reserve_pass=(
            peak + DEVICE_RESERVE_BYTES <= MINIMUM_DEVICE_PHYSICAL_BYTES
        ),
        live_free_bytes=live,
        live_reserve_pass=(
            None if live is None else peak + DEVICE_RESERVE_BYTES <= live
        ),
        arrays=MappingProxyType(arrays),
    )


def _allocation_evidence(
    allocation: StageAllocation,
    *,
    observed_pool_used_bytes: Sequence[int] | None = None,
    device_free_bytes_after_release: int | None = None,
    pool_used_bytes_after_release: int | None = None,
    pool_total_bytes_after_release: int | None = None,
    pinned_free_blocks_after_release: int | None = None,
    device_total_bytes_after_release: int | None = None,
) -> dict[str, object]:
    return {
        "arrays": dict(allocation.arrays),
        "static_device_bytes": allocation.static_device_bytes,
        "forward_base_bytes": allocation.forward_base_bytes,
        "warm_forward_peak_bytes": allocation.warm_forward_peak_bytes,
        "query_only_peak_bytes": allocation.query_only_peak_bytes,
        "adjoint_peak_bytes": allocation.adjoint_peak_bytes,
        "dot_product_peak_bytes": allocation.dot_product_peak_bytes,
        "requested_device_peak_bytes": allocation.requested_device_peak_bytes,
        "live_free_bytes": allocation.live_free_bytes,
        "fixed_cap_pass": allocation.fixed_cap_pass,
        "physical_reserve_pass": allocation.physical_reserve_pass,
        "live_reserve_pass": allocation.live_reserve_pass,
        "observed_pool_used_bytes": (
            None
            if observed_pool_used_bytes is None
            else [int(value) for value in observed_pool_used_bytes]
        ),
        "device_free_bytes_after_release": device_free_bytes_after_release,
        "pool_used_bytes_after_release": pool_used_bytes_after_release,
        "pool_total_bytes_after_release": pool_total_bytes_after_release,
        "pinned_free_blocks_after_release": pinned_free_blocks_after_release,
        "device_total_bytes_after_release": device_total_bytes_after_release,
    }


def stage_work(available_cards: int) -> Mapping[str, int]:
    geometry = stage_geometry(available_cards)
    signed_terms = geometry.labeled_query_records * 16
    signed_scalar_additions = signed_terms * FEATURE_WIDTH
    query_folds = geometry.labeled_query_records * SOURCE_RANK
    adjoint_edges = sum(
        comb(available_cards, width) * (available_cards - width)
        for width in range(QUERY_CARDS)
    )
    return MappingProxyType(
        {
            "cold_source_pairing_visits": geometry.labeled_source_visits,
            "cold_source_state_reach_accumulations": (
                geometry.labeled_source_visits * 2
            ),
            "cold_source_zero_writes": geometry.source_occupancies * FEATURE_WIDTH,
            "cold_recurrence_vector_edges": (
                geometry.recurrence_vector_edges
            ),
            "cold_recurrence_scalar_additions": (
                geometry.recurrence_scalar_additions
            ),
            "cold_signed_query_terms": signed_terms,
            "cold_signed_query_scalar_additions": signed_scalar_additions,
            "cold_query_automaton_state_folds": query_folds,
            "warm_full_forward_repetitions": WARM_REPETITIONS,
            "source_refresh_pairing_visits": geometry.labeled_source_visits,
            "source_refresh_state_reach_accumulations": (
                geometry.labeled_source_visits * 2
            ),
            "source_refresh_zero_writes": (
                geometry.source_occupancies * FEATURE_WIDTH
            ),
            "source_refresh_recurrence_vector_edges": (
                geometry.recurrence_vector_edges
            ),
            "source_refresh_recurrence_scalar_additions": (
                geometry.recurrence_scalar_additions
            ),
            "source_refresh_signed_query_terms": signed_terms,
            "source_refresh_signed_query_scalar_additions": (
                signed_scalar_additions
            ),
            "source_refresh_query_automaton_state_folds": query_folds,
            "source_refresh_repetitions": SOURCE_REFRESH_REPETITIONS,
            "query_only_source_pairing_visits": 0,
            "query_only_recurrence_scalar_additions": 0,
            "query_only_signed_query_terms": signed_terms,
            "query_only_signed_query_scalar_additions": signed_scalar_additions,
            "query_only_query_automaton_state_folds": query_folds,
            "query_only_repetitions": QUERY_ONLY_REPETITIONS,
            "adjoint_query_aggregation_additions": (
                geometry.query_occupancies
                * (QUERY_LABELS - 1)
                * FEATURE_WIDTH
            ),
            "adjoint_recurrence_scalar_additions": (
                adjoint_edges * FEATURE_WIDTH
            ),
            "adjoint_signed_source_additions": (
                geometry.source_occupancies * 57 * FEATURE_WIDTH
            ),
            "adjoint_modeled_label_writes": (
                geometry.labeled_source_visits * FEATURE_WIDTH
            ),
            "adjoint_allocated_label_writes": 0,
            "adjoint_repetitions": 1 + ADJOINT_WARM_REPETITIONS,
        }
    )


def _resolved_sample_ranks(
    *,
    available_cards: int,
    lane: str,
    count: int,
    population: int,
) -> tuple[int, ...]:
    if lane not in {"source", "query"}:
        raise ValueError("sample lane must be source or query")
    if count < 2 or population < count:
        raise ValueError("sample population cannot satisfy frozen sample count")
    selected = [0, population - 1]
    occupied = set(selected)
    for index in range(count - 2):
        label = (
            f"pontius|adr-0373|stage={available_cards}|lane={lane}|index={index}"
        )
        candidate = int.from_bytes(sha256(label.encode("ascii")).digest(), "big")
        candidate %= population
        while candidate in occupied:
            candidate = (candidate + 1) % population
        selected.append(candidate)
        occupied.add(candidate)
    return tuple(selected)


def source_sample_ranks(available_cards: int) -> tuple[int, ...]:
    geometry = stage_geometry(available_cards)
    return _resolved_sample_ranks(
        available_cards=available_cards,
        lane="source",
        count=SOURCE_SAMPLE_COUNT,
        population=geometry.source_occupancies,
    )


def query_sample_ranks(available_cards: int) -> tuple[int, ...]:
    geometry = stage_geometry(available_cards)
    return _resolved_sample_ranks(
        available_cards=available_cards,
        lane="query",
        count=QUERY_SAMPLE_COUNT,
        population=geometry.query_occupancies,
    )


@lru_cache(maxsize=len(STAGE_CARDS))
def compile_stage_fixture(available_cards: int) -> bounded.FrozenQuotientFixture:
    """Compile one complete host topology without importing CuPy."""

    geometry = stage_geometry(available_cards)
    cards = geometry.available_cards
    hands = tuple(combinations(range(cards), 2))
    hand_id = {hand: index for index, hand in enumerate(hands)}
    pair_to_hand = np.full((cards, cards), -1, dtype=np.int32)
    for hand, index in hand_id.items():
        pair_to_hand[hand] = index
        pair_to_hand[hand[::-1]] = index
    strength = np.asarray(
        [index % STRENGTH_CODES for index in range(len(hands))],
        dtype=np.int32,
    )
    automaton = build_structured_showdown_automaton(
        strength_codes=(
            strength,
            strength,
            strength,
            np.asarray((21,), dtype=np.int32),
            strength,
            strength,
        ),
        contenders=(0, 1, 2, 3, 4, 5),
        target_player=3,
        contributed=True,
        pot=17.0,
        bet_size=3.0,
    )
    offsets = np.asarray(
        (
            0,
            geometry.hand_width,
            2 * geometry.hand_width,
            3 * geometry.hand_width,
            3 * geometry.hand_width + 1,
            4 * geometry.hand_width + 1,
        ),
        dtype=np.int32,
    )
    total = 5 * geometry.hand_width + 1
    unary = np.empty((1, total), dtype=np.float64)
    factors = np.empty_like(unary)
    widths = (
        geometry.hand_width,
        geometry.hand_width,
        geometry.hand_width,
        1,
        geometry.hand_width,
        geometry.hand_width,
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

    query_masks: list[int] = []
    query_indices: list[tuple[int, int]] = []
    query_pairings = _pairings(QUERY_CARDS, 2)
    for occupancy_rank in range(geometry.query_occupancies):
        occupancy = bounded.colex_unrank(
            occupancy_rank,
            cards,
            QUERY_CARDS,
        )
        mask = _mask(occupancy)
        for pairing in query_pairings:
            first = tuple(
                sorted((occupancy[pairing[0]], occupancy[pairing[1]]))
            )
            second = tuple(
                sorted((occupancy[pairing[2]], occupancy[pairing[3]]))
            )
            query_masks.append(mask)
            query_indices.append((hand_id[first], hand_id[second]))
    fixture = bounded.FrozenQuotientFixture(
        available_cards=cards,
        hands=hands,
        automaton=automaton,
        unary_weights=_readonly(unary, np.float64),
        mode_factors=_readonly(factors, np.float64),
        mixture_weights=_readonly((0.61,), np.float64),
        pair_to_hand=_readonly(pair_to_hand, np.int32),
        source_pair_positions=_readonly(
            _pairings(SOURCE_CARDS, 3),
            np.int8,
        ),
        query_masks=_readonly(query_masks, np.uint64),
        query_hand_indices=_readonly(query_indices, np.int32),
        unary_offsets=_readonly(offsets, np.int32),
    )
    if fixture.source_rank != SOURCE_RANK or fixture.feature_width != FEATURE_WIDTH:
        raise AssertionError("staged direct automaton rank drifted")
    if len(fixture.query_masks) != geometry.labeled_query_records:
        raise AssertionError("staged query compiler omitted a labeled record")
    return fixture


def source_refresh_fixture(
    fixture: bounded.FrozenQuotientFixture,
) -> bounded.FrozenQuotientFixture:
    values = fixture.unary_weights.copy()
    start = int(fixture.unary_offsets[1])
    for hand in range(len(fixture.hands)):
        values[0, start + hand] *= 1.03 + (hand % 7) * 0.001
    values = np.ascontiguousarray(values, dtype=np.float64)
    values.flags.writeable = False
    return replace(fixture, unary_weights=values)


def query_only_fixture(
    fixture: bounded.FrozenQuotientFixture,
) -> bounded.FrozenQuotientFixture:
    values = fixture.unary_weights.copy()
    start = int(fixture.unary_offsets[4])
    for hand in range(len(fixture.hands)):
        values[0, start + hand] *= 0.97 + (hand % 5) * 0.002
    values = np.ascontiguousarray(values, dtype=np.float64)
    values.flags.writeable = False
    return replace(fixture, unary_weights=values)


def stage_semantic_identity(available_cards: int) -> str:
    fixture = compile_stage_fixture(available_cards)
    allocation = stage_allocation(fixture)
    payload = {
        "allocation_arrays": dict(allocation.arrays),
        "automaton_digest": fixture.automaton.digest,
        "available_cards": available_cards,
        "geometry": {
            key: getattr(stage_geometry(available_cards), key)
            for key in StageGeometry.__dataclass_fields__
        },
        "protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "query_sample_ranks": list(query_sample_ranks(available_cards)),
        "source_sample_ranks": list(source_sample_ranks(available_cards)),
        "work": dict(stage_work(available_cards)),
    }
    return _semantic_digest(payload)


_STAGED_CUDA_SOURCE = r"""
__device__ __forceinline__ long long choose_stage(int n, int k) {
    if (k < 0 || k > n) return 0;
    if (k == 0 || k == n) return 1;
    if (k > n - k) k = n - k;
    long long value = 1;
    for (int i = 1; i <= k; ++i) value = value * (n - k + i) / i;
    return value;
}

__device__ __forceinline__ unsigned long long unrank_stage(
    long long rank, int n, int k
) {
    unsigned long long mask = 0ULL;
    int upper = n - 1;
    for (int i = k; i >= 1; --i) {
        int card = upper;
        while (choose_stage(card, i) > rank) --card;
        mask |= 1ULL << card;
        rank -= choose_stage(card, i);
        upper = card - 1;
    }
    return mask;
}

extern "C" __global__ void direct_selected_queries(
    const double *source, long long source_rows, int n, int width,
    const unsigned long long *query_masks, int query_count,
    const int *features, int feature_count, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= query_count * feature_count) return;
    int query = index / feature_count;
    int feature_index = index - query * feature_count;
    int feature = features[feature_index];
    double sum = 0.0;
    unsigned long long query_mask = query_masks[query];
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_stage(row, n, 6);
        if (!(source_mask & query_mask))
            sum += source[row * width + feature];
    }
    output[index] = sum;
}

extern "C" __global__ void compare_float64_bits(
    const double *first, const double *second, long long count, int *different
) {
    long long index = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= count) return;
    if (__double_as_longlong(first[index]) != __double_as_longlong(second[index]))
        atomicExch(different, 1);
}

extern "C" __global__ void fill_query_covectors(
    double *output, long long rows, int width
) {
    long long index = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long count = rows * width;
    if (index >= count) return;
    long long row = index / width;
    int feature = (int)(index - row * width);
    long long residue = ((row + 7) * (feature + 2)) % 19;
    output[index] = ((double)residue - 9.0) / 1000.0;
}
"""

_STAGED_KERNEL_NAMES = (
    "direct_selected_queries",
    "compare_float64_bits",
    "fill_query_covectors",
)
_STAGED_KERNEL_CACHE: dict[int, Mapping[str, object]] = {}


def _staged_kernels(cp) -> Mapping[str, object]:
    device = int(cp.cuda.Device().id)
    cached = _STAGED_KERNEL_CACHE.get(device)
    if cached is not None:
        return cached
    module = cp.RawModule(
        code=_STAGED_CUDA_SOURCE,
        options=("--std=c++14",),
        name_expressions=_STAGED_KERNEL_NAMES,
    )
    result = {
        name: module.get_function(name)
        for name in _STAGED_KERNEL_NAMES
    }
    _STAGED_KERNEL_CACHE[device] = result
    return result


def _launch(kernel, total: int, arguments: tuple[object, ...]) -> None:
    threads = 128
    blocks = (total + threads - 1) // threads
    kernel((blocks,), (threads,), arguments)


def _cuda_timed(cp, operation) -> float:
    start = cp.cuda.Event()
    stop = cp.cuda.Event()
    start.record()
    operation()
    stop.record()
    stop.synchronize()
    return float(cp.cuda.get_elapsed_time(start, stop))


def _runtime_identity(cp) -> dict[str, object]:
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


def validate_runtime_identity(runtime: Mapping[str, object]) -> None:
    expected = {
        "compute_capability": REQUIRED_COMPUTE_CAPABILITY,
        "cuda_runtime_version": REQUIRED_CUDA_RUNTIME_VERSION,
        "cupy_version": REQUIRED_CUPY_VERSION,
        "device_name": REQUIRED_DEVICE_NAME,
    }
    for field, value in expected.items():
        if runtime.get(field) != value:
            raise RuntimeError(f"staged scaling runtime differs: {field}")
    driver = runtime.get("cuda_driver_version")
    total = runtime.get("device_total_bytes")
    if isinstance(driver, bool) or not isinstance(driver, int):
        raise RuntimeError("staged scaling CUDA driver is not integral")
    if driver < MINIMUM_CUDA_DRIVER_VERSION:
        raise RuntimeError("staged scaling CUDA driver is below the floor")
    if isinstance(total, bool) or not isinstance(total, int):
        raise RuntimeError("staged scaling device bytes are not integral")
    if total < MINIMUM_DEVICE_PHYSICAL_BYTES:
        raise RuntimeError("staged scaling device is below physical capacity")


@dataclass(slots=True)
class _DeviceStage:
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
    factors: Any
    unary_offsets: Any
    transitions: tuple[Any, ...]
    terminal: Any
    mixture: Any
    query_masks: Any
    query_hands: Any
    level_offsets: tuple[int, ...]


def _allocate_device_stage(
    cp,
    fixture: bounded.FrozenQuotientFixture,
) -> _DeviceStage:
    geometry = stage_geometry(fixture.available_cards)
    allocation = stage_allocation(fixture)
    table = cp.empty(
        (geometry.recurrence_rows, FEATURE_WIDTH),
        dtype=cp.float64,
    )
    compatible = cp.empty(
        (geometry.labeled_query_records, FEATURE_WIDTH),
        dtype=cp.float64,
    )
    numerator = cp.empty(geometry.labeled_query_records, dtype=cp.float64)
    reach = cp.empty(geometry.labeled_query_records, dtype=cp.float64)
    if allocation.requested_device_peak_bytes > FIXED_DEVICE_NUMERIC_CAP_BYTES:
        raise AssertionError("device allocation bypassed the pure stage model")
    return _DeviceStage(
        cp=cp,
        kernels=bounded._kernels(cp),
        staged_kernels=_staged_kernels(cp),
        fixture=fixture,
        table=table,
        compatible=compatible,
        numerator=numerator,
        reach=reach,
        pairings=cp.asarray(fixture.source_pair_positions, dtype=cp.int8),
        pair_to_hand=cp.asarray(fixture.pair_to_hand, dtype=cp.int32),
        factors=cp.asarray(fixture.mode_factors, dtype=cp.float64),
        unary_offsets=cp.asarray(fixture.unary_offsets, dtype=cp.int32),
        transitions=tuple(
            cp.asarray(value, dtype=cp.int32)
            for value in fixture.automaton.transitions
        ),
        terminal=cp.asarray(
            fixture.automaton.terminal_winner_values,
            dtype=cp.float64,
        ),
        mixture=cp.asarray(fixture.mixture_weights, dtype=cp.float64),
        query_masks=cp.asarray(fixture.query_masks, dtype=cp.uint64),
        query_hands=cp.asarray(fixture.query_hand_indices, dtype=cp.int32),
        level_offsets=bounded.cardinality_offsets(
            fixture.available_cards,
            SOURCE_CARDS,
        ),
    )


def _source_kernel(
    state: _DeviceStage,
    unary,
) -> float:
    fixture = state.fixture
    geometry = stage_geometry(fixture.available_cards)
    source_offset = state.level_offsets[SOURCE_CARDS]

    def operation() -> None:
        _launch(
            state.kernels["source_coefficients"],
            geometry.source_occupancies,
            (
                state.table,
                np.int64(source_offset),
                np.int32(FEATURE_WIDTH),
                np.int64(geometry.source_occupancies),
                np.int32(fixture.available_cards),
                np.int32(geometry.hand_width),
                np.int32(1),
                np.int32(SOURCE_RANK),
                state.pairings,
                state.pair_to_hand,
                unary,
                state.factors,
                np.int32(fixture.unary_weights.shape[1]),
                state.unary_offsets,
                state.transitions[0],
                state.transitions[1],
                state.transitions[2],
                np.int32(0),
            ),
        )

    return _cuda_timed(state.cp, operation)


def _recurrence_kernel(state: _DeviceStage) -> float:
    return bounded._fill_recurrence(
        state.cp,
        state.kernels,
        state.table,
        available_cards=state.fixture.available_cards,
        source_cards=SOURCE_CARDS,
        feature_width=FEATURE_WIDTH,
    )


def _signed_query_kernel(state: _DeviceStage) -> float:
    cp = state.cp
    geometry = stage_geometry(state.fixture.available_cards)
    offsets = cp.asarray(state.level_offsets, dtype=cp.int64)

    def operation() -> None:
        _launch(
            state.kernels["signed_targets"],
            geometry.labeled_query_records * FEATURE_WIDTH,
            (
                state.table,
                offsets,
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

    return _cuda_timed(cp, operation)


def _fold_kernel(
    state: _DeviceStage,
    unary,
) -> float:
    fixture = state.fixture
    geometry = stage_geometry(fixture.available_cards)

    def operation() -> None:
        _launch(
            state.kernels["fold_query"],
            geometry.labeled_query_records,
            (
                state.compatible,
                np.int64(geometry.labeled_query_records),
                np.int32(SOURCE_RANK),
                np.int32(1),
                state.query_hands,
                unary,
                state.factors,
                np.int32(fixture.unary_weights.shape[1]),
                state.unary_offsets,
                state.mixture,
                state.transitions[3],
                state.transitions[4],
                state.terminal,
                np.int32(geometry.hand_width),
                np.float64(fixture.automaton.sunk_value),
                np.int32(0),
                state.numerator,
                state.reach,
            ),
        )

    return _cuda_timed(state.cp, operation)


def _forward_once(
    state: _DeviceStage,
    unary,
) -> dict[str, float]:
    source = _source_kernel(state, unary)
    recurrence = _recurrence_kernel(state)
    signed = _signed_query_kernel(state)
    fold = _fold_kernel(state, unary)
    return {
        "source_coefficients": source,
        "recurrence": recurrence,
        "signed_query": signed,
        "affine_fold": fold,
        "device_sum": source + recurrence + signed + fold,
    }


def _query_only_once(
    state: _DeviceStage,
    unary,
) -> dict[str, float]:
    signed = _signed_query_kernel(state)
    fold = _fold_kernel(state, unary)
    return {
        "source_coefficients": 0.0,
        "recurrence": 0.0,
        "signed_query": signed,
        "affine_fold": fold,
        "device_sum": signed + fold,
    }


def _bit_identical(state: _DeviceStage, first, second) -> bool:
    cp = state.cp
    if first.shape != second.shape or first.dtype != cp.float64:
        return False
    different = cp.zeros(1, dtype=cp.int32)
    _launch(
        state.staged_kernels["compare_float64_bits"],
        int(first.size),
        (first, second, np.int64(first.size), different),
    )
    return int(cp.asnumpy(different)[0]) == 0


def _source_slice(state: _DeviceStage):
    geometry = stage_geometry(state.fixture.available_cards)
    start = state.level_offsets[SOURCE_CARDS]
    return state.table[start : start + geometry.source_occupancies]


def _source_sample_exact(
    fixture: bounded.FrozenQuotientFixture,
    ranks: tuple[int, ...],
) -> np.ndarray:
    from fractions import Fraction

    result = np.zeros((len(ranks), FEATURE_WIDTH), dtype=np.float64)
    transitions = fixture.automaton.transitions
    for output_row, occupancy_rank in enumerate(ranks):
        cards = bounded.colex_unrank(
            occupancy_rank,
            fixture.available_cards,
            SOURCE_CARDS,
        )
        values = [Fraction(0) for _ in range(FEATURE_WIDTH)]
        for pairing in fixture.source_pair_positions:
            hand_indices = []
            for seat in range(3):
                hand = tuple(
                    sorted(
                        (
                            cards[int(pairing[2 * seat])],
                            cards[int(pairing[2 * seat + 1])],
                        )
                    )
                )
                hand_indices.append(int(fixture.pair_to_hand[hand]))
            state0 = int(transitions[0][0, hand_indices[0]])
            state1 = int(transitions[1][state0, hand_indices[1]])
            state2 = int(transitions[2][state1, hand_indices[2]])
            weight = Fraction(1)
            for seat, hand in enumerate(hand_indices):
                index = int(fixture.unary_offsets[seat]) + hand
                weight *= Fraction.from_float(
                    float(fixture.unary_weights[0, index])
                )
                weight *= Fraction.from_float(
                    float(fixture.mode_factors[0, index])
                )
            values[state2] += weight
            values[SOURCE_RANK] += weight
        result[output_row] = tuple(float(value) for value in values)
    return result


def _maximum_errors(
    actual: np.ndarray,
    expected: np.ndarray,
) -> tuple[float, float]:
    absolute = np.abs(actual - expected)
    maximum_absolute = float(np.max(absolute, initial=0.0))
    relative = absolute / np.maximum(1.0, np.abs(expected))
    return maximum_absolute, float(np.max(relative, initial=0.0))


def _selected_direct_queries(
    state: _DeviceStage,
    occupancy_ranks: tuple[int, ...],
) -> tuple[np.ndarray, float]:
    cp = state.cp
    fixture = state.fixture
    geometry = stage_geometry(fixture.available_cards)
    masks = np.asarray(
        [
            _mask(
                bounded.colex_unrank(
                    rank,
                    fixture.available_cards,
                    QUERY_CARDS,
                )
            )
            for rank in occupancy_ranks
        ],
        dtype=np.uint64,
    )
    device_masks = cp.asarray(masks, dtype=cp.uint64)
    features = cp.asarray(QUERY_SAMPLE_FEATURES, dtype=cp.int32)
    output = cp.empty(
        (len(occupancy_ranks), len(QUERY_SAMPLE_FEATURES)),
        dtype=cp.float64,
    )

    def operation() -> None:
        _launch(
            state.staged_kernels["direct_selected_queries"],
            len(occupancy_ranks) * len(QUERY_SAMPLE_FEATURES),
            (
                _source_slice(state),
                np.int64(geometry.source_occupancies),
                np.int32(fixture.available_cards),
                np.int32(FEATURE_WIDTH),
                device_masks,
                np.int32(len(occupancy_ranks)),
                features,
                np.int32(len(QUERY_SAMPLE_FEATURES)),
                output,
            ),
        )

    wall = _cuda_timed(cp, operation)
    return cp.asnumpy(output), wall


def _affine_sample_expected(
    fixture: bounded.FrozenQuotientFixture,
    compatible_rows: np.ndarray,
    record_indices: tuple[int, ...],
) -> tuple[np.ndarray, np.ndarray]:
    numerator = np.empty(len(record_indices), dtype=np.float64)
    reach = np.empty(len(record_indices), dtype=np.float64)
    transitions = fixture.automaton.transitions
    terminal = fixture.automaton.terminal_winner_values
    for output, record in enumerate(record_indices):
        h4, h5 = fixture.query_hand_indices[record]
        query_weight = float(fixture.mixture_weights[0])
        for seat, hand in ((3, 0), (4, int(h4)), (5, int(h5))):
            index = int(fixture.unary_offsets[seat]) + hand
            query_weight *= float(fixture.unary_weights[0, index])
            query_weight *= float(fixture.mode_factors[0, index])
        winner = 0.0
        for source_state in range(SOURCE_RANK):
            state3 = int(transitions[3][source_state, 0])
            state4 = int(transitions[4][state3, int(h4)])
            winner += (
                compatible_rows[output, source_state]
                * float(terminal[state4, int(h5)])
            )
        compatible_reach = compatible_rows[output, SOURCE_RANK]
        numerator[output] = query_weight * (
            winner + fixture.automaton.sunk_value * compatible_reach
        )
        reach[output] = query_weight * compatible_reach
    return numerator, reach


def _fill_query_covectors(state: _DeviceStage):
    geometry = stage_geometry(state.fixture.available_cards)
    values = state.cp.empty(
        (geometry.labeled_query_records, FEATURE_WIDTH),
        dtype=state.cp.float64,
    )
    _launch(
        state.staged_kernels["fill_query_covectors"],
        int(values.size),
        (
            values,
            np.int64(geometry.labeled_query_records),
            np.int32(FEATURE_WIDTH),
        ),
    )
    state.cp.cuda.get_current_stream().synchronize()
    return values


def _adjoint_once(
    state: _DeviceStage,
    query_covectors,
    table,
    aggregated,
    unique,
) -> dict[str, float]:
    cp = state.cp
    fixture = state.fixture
    geometry = stage_geometry(fixture.available_cards)

    def aggregate_operation() -> None:
        _launch(
            state.kernels["aggregate_query_labels"],
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

    aggregation = _cuda_timed(cp, aggregate_operation)
    offsets = bounded.cardinality_offsets(
        fixture.available_cards,
        QUERY_CARDS,
    )
    table[
        offsets[QUERY_CARDS] : offsets[QUERY_CARDS]
        + geometry.query_occupancies
    ] = aggregated
    recurrence = bounded._fill_recurrence(
        cp,
        state.kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=QUERY_CARDS,
        feature_width=FEATURE_WIDTH,
    )
    device_offsets = cp.asarray(offsets, dtype=cp.int64)
    dummy_masks = cp.zeros(1, dtype=cp.uint64)

    def signed_operation() -> None:
        _launch(
            state.kernels["signed_targets"],
            geometry.source_occupancies * FEATURE_WIDTH,
            (
                table,
                device_offsets,
                np.int32(QUERY_CARDS),
                dummy_masks,
                np.int32(1),
                np.int32(SOURCE_CARDS),
                np.int64(geometry.source_occupancies),
                np.int32(fixture.available_cards),
                np.int32(FEATURE_WIDTH),
                np.int32(0),
                unique,
            ),
        )

    signed = _cuda_timed(cp, signed_operation)
    return {
        "query_aggregation": aggregation,
        "recurrence": recurrence,
        "signed_source": signed,
        "device_sum": aggregation + recurrence + signed,
    }


def _timing_summary(rows: Sequence[Mapping[str, float]]) -> dict[str, object]:
    if not rows:
        raise ValueError("timing summary requires at least one observation")
    fields = tuple(rows[0])
    if any(tuple(row) != fields for row in rows):
        raise ValueError("timing observations have inconsistent phases")
    result: dict[str, object] = {"count": len(rows), "phases": {}}
    phases: dict[str, object] = {}
    for field in fields:
        values = np.asarray([float(row[field]) for row in rows], dtype=np.float64)
        phases[field] = {
            "raw_hex": [_float_text(value) for value in values],
            "median_hex": _float_text(float(np.median(values))),
            "maximum_hex": _float_text(float(np.max(values))),
        }
    result["phases"] = phases
    return result


def _sample_digest(*arrays: np.ndarray) -> str:
    digest = sha256()
    for values in arrays:
        contiguous = np.ascontiguousarray(values)
        digest.update(repr((contiguous.shape, contiguous.dtype.str)).encode("ascii"))
        digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def execute_gpu_stage(available_cards: int) -> dict[str, object]:
    """Execute one preregistered stage; the exclusive runner is its only owner."""

    import gc
    from time import perf_counter

    stage_started = perf_counter()
    topology_started = perf_counter()
    fixture = compile_stage_fixture(available_cards)
    expected_semantic_identity = stage_semantic_identity(available_cards)
    refreshed_fixture = source_refresh_fixture(fixture)
    query_fixture = query_only_fixture(refreshed_fixture)
    pure_allocation = stage_allocation(fixture)
    topology_ms = (perf_counter() - topology_started) * 1000.0
    if not pure_allocation.fixed_cap_pass or not pure_allocation.physical_reserve_pass:
        return build_allocation_rejection_stage_payload(
            available_cards,
            allocation=pure_allocation,
            topology_ms=topology_ms,
            stage_total_ms=(perf_counter() - stage_started) * 1000.0,
            reason="fixed_preallocation_rejected",
        )

    cp = bounded._cupy_module()
    runtime = _runtime_identity(cp)
    validate_runtime_identity(runtime)
    default_pool = cp.get_default_memory_pool()
    pinned_pool = cp.get_default_pinned_memory_pool()
    default_pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    free_before, total = cp.cuda.runtime.memGetInfo()
    if int(total) != runtime["device_total_bytes"]:
        raise RuntimeError("staged scaling device total changed before admission")
    live_allocation = stage_allocation(
        fixture,
        live_free_bytes=int(free_before),
    )
    if not live_allocation.all_available_gates_pass:
        return build_allocation_rejection_stage_payload(
            available_cards,
            allocation=live_allocation,
            topology_ms=topology_ms,
            stage_total_ms=(perf_counter() - stage_started) * 1000.0,
            reason="live_preallocation_rejected",
            runtime=runtime,
        )

    transfer_started = perf_counter()
    state = _allocate_device_stage(cp, fixture)
    original_unary = cp.asarray(fixture.unary_weights, dtype=cp.float64)
    refreshed_unary = cp.asarray(
        refreshed_fixture.unary_weights,
        dtype=cp.float64,
    )
    query_unary = cp.asarray(query_fixture.unary_weights, dtype=cp.float64)
    cp.cuda.get_current_stream().synchronize()
    transfer_ms = (perf_counter() - transfer_started) * 1000.0
    observed_pool_bytes = [int(default_pool.used_bytes())]

    cold_host_started = perf_counter()
    cold_timing = _forward_once(state, original_unary)
    cold_host_ms = (perf_counter() - cold_host_started) * 1000.0

    validation_host_ms = 0.0
    validation_started = perf_counter()
    source_ranks = source_sample_ranks(available_cards)
    query_ranks = query_sample_ranks(available_cards)
    source_actual = cp.asnumpy(_source_slice(state)[list(source_ranks)])
    source_expected = _source_sample_exact(fixture, source_ranks)
    source_error, source_relative = _maximum_errors(
        source_actual,
        source_expected,
    )
    direct_actual, direct_wall_ms = _selected_direct_queries(state, query_ranks)
    record_indices = tuple(rank * QUERY_LABELS for rank in query_ranks)
    compatible_selected = cp.asnumpy(
        state.compatible[list(record_indices)]
    )
    direct_expected = compatible_selected[:, QUERY_SAMPLE_FEATURES]
    direct_error, direct_relative = _maximum_errors(
        direct_actual,
        direct_expected,
    )
    expected_numerator, expected_reach = _affine_sample_expected(
        fixture,
        compatible_selected,
        record_indices,
    )
    actual_numerator = cp.asnumpy(state.numerator[list(record_indices)])
    actual_reach = cp.asnumpy(state.reach[list(record_indices)])
    affine_numerator_error, _ = _maximum_errors(
        actual_numerator,
        expected_numerator,
    )
    affine_reach_error, _ = _maximum_errors(actual_reach, expected_reach)
    validation_host_ms += (perf_counter() - validation_started) * 1000.0

    source_reference = cp.copy(_source_slice(state))
    compatible_reference = cp.copy(state.compatible)
    numerator_reference = cp.copy(state.numerator)
    reach_reference = cp.copy(state.reach)
    observed_pool_bytes.append(int(default_pool.used_bytes()))
    warm_identity_observations: list[bool] = []
    warm_timings: list[dict[str, float]] = []
    warm_host_started = perf_counter()
    for _ in range(WARM_REPETITIONS):
        warm_timings.append(_forward_once(state, original_unary))
        warm_identity_observations.append(
            all(
                (
                    _bit_identical(state, _source_slice(state), source_reference),
                    _bit_identical(state, state.compatible, compatible_reference),
                    _bit_identical(state, state.numerator, numerator_reference),
                    _bit_identical(state, state.reach, reach_reference),
                )
            )
        )
    warm_host_ms = (perf_counter() - warm_host_started) * 1000.0
    del source_reference, compatible_reference, numerator_reference, reach_reference
    gc.collect()

    refresh_timings: list[dict[str, float]] = []
    refresh_identity_observations: list[bool] = []
    refresh_host_started = perf_counter()
    refresh_timings.append(_forward_once(state, refreshed_unary))
    validation_started = perf_counter()
    refreshed_source_actual = cp.asnumpy(_source_slice(state)[list(source_ranks)])
    refreshed_source_expected = _source_sample_exact(
        refreshed_fixture,
        source_ranks,
    )
    refreshed_source_error, refreshed_source_relative = _maximum_errors(
        refreshed_source_actual,
        refreshed_source_expected,
    )
    validation_host_ms += (perf_counter() - validation_started) * 1000.0
    refresh_source_reference = cp.copy(_source_slice(state))
    refresh_compatible_reference = cp.copy(state.compatible)
    refresh_numerator_reference = cp.copy(state.numerator)
    refresh_reach_reference = cp.copy(state.reach)
    observed_pool_bytes.append(int(default_pool.used_bytes()))
    refresh_identity_observations.append(True)
    for _ in range(SOURCE_REFRESH_REPETITIONS - 1):
        refresh_timings.append(_forward_once(state, refreshed_unary))
        refresh_identity_observations.append(
            all(
                (
                    _bit_identical(
                        state,
                        _source_slice(state),
                        refresh_source_reference,
                    ),
                    _bit_identical(
                        state,
                        state.compatible,
                        refresh_compatible_reference,
                    ),
                    _bit_identical(
                        state,
                        state.numerator,
                        refresh_numerator_reference,
                    ),
                    _bit_identical(state, state.reach, refresh_reach_reference),
                )
            )
        )
    refresh_host_ms = (perf_counter() - refresh_host_started) * 1000.0
    del (
        refresh_source_reference,
        refresh_compatible_reference,
        refresh_numerator_reference,
        refresh_reach_reference,
    )
    gc.collect()

    query_timings: list[dict[str, float]] = []
    query_identity_observations: list[bool] = []
    query_host_started = perf_counter()
    query_timings.append(_query_only_once(state, query_unary))
    validation_started = perf_counter()
    query_compatible_selected = cp.asnumpy(
        state.compatible[list(record_indices)]
    )
    query_expected_numerator, query_expected_reach = _affine_sample_expected(
        query_fixture,
        query_compatible_selected,
        record_indices,
    )
    query_actual_numerator = cp.asnumpy(state.numerator[list(record_indices)])
    query_actual_reach = cp.asnumpy(state.reach[list(record_indices)])
    query_numerator_error, _ = _maximum_errors(
        query_actual_numerator,
        query_expected_numerator,
    )
    query_reach_error, _ = _maximum_errors(
        query_actual_reach,
        query_expected_reach,
    )
    validation_host_ms += (perf_counter() - validation_started) * 1000.0
    query_compatible_reference = cp.copy(state.compatible)
    query_numerator_reference = cp.copy(state.numerator)
    query_reach_reference = cp.copy(state.reach)
    query_identity_observations.append(True)
    for _ in range(QUERY_ONLY_REPETITIONS - 1):
        query_timings.append(_query_only_once(state, query_unary))
        query_identity_observations.append(
            all(
                (
                    _bit_identical(
                        state,
                        state.compatible,
                        query_compatible_reference,
                    ),
                    _bit_identical(
                        state,
                        state.numerator,
                        query_numerator_reference,
                    ),
                    _bit_identical(state, state.reach, query_reach_reference),
                )
            )
        )
    query_host_ms = (perf_counter() - query_host_started) * 1000.0
    del query_compatible_reference, query_numerator_reference, query_reach_reference
    gc.collect()

    geometry = stage_geometry(available_cards)
    query_covectors = _fill_query_covectors(state)
    adjoint_rows = sum(
        comb(available_cards, width)
        for width in range(QUERY_CARDS + 1)
    )
    adjoint_table = cp.empty((adjoint_rows, FEATURE_WIDTH), dtype=cp.float64)
    aggregated = cp.empty(
        (geometry.query_occupancies, FEATURE_WIDTH),
        dtype=cp.float64,
    )
    unique_adjoint = cp.empty(
        (geometry.source_occupancies, FEATURE_WIDTH),
        dtype=cp.float64,
    )
    adjoint_host_started = perf_counter()
    adjoint_timings = [
        _adjoint_once(
            state,
            query_covectors,
            adjoint_table,
            aggregated,
            unique_adjoint,
        )
    ]
    forward_dot = float(cp.asnumpy(cp.sum(state.compatible * query_covectors)))
    transpose_dot = float(
        cp.asnumpy(cp.sum(_source_slice(state) * unique_adjoint))
    )
    dot_error = abs(forward_dot - transpose_dot)
    dot_relative = dot_error / max(
        1.0,
        abs(forward_dot),
        abs(transpose_dot),
    )
    observed_pool_bytes.append(int(default_pool.used_bytes()))

    state.table = None
    state.compatible = None
    state.numerator = None
    state.reach = None
    gc.collect()
    default_pool.free_all_blocks()
    adjoint_reference = cp.copy(unique_adjoint)
    observed_pool_bytes.append(int(default_pool.used_bytes()))
    adjoint_identity_observations = [True]
    for _ in range(ADJOINT_WARM_REPETITIONS):
        adjoint_timings.append(
            _adjoint_once(
                state,
                query_covectors,
                adjoint_table,
                aggregated,
                unique_adjoint,
            )
        )
        adjoint_identity_observations.append(
            _bit_identical(
                state,
                unique_adjoint,
                adjoint_reference,
            )
        )
    adjoint_host_ms = (perf_counter() - adjoint_host_started) * 1000.0

    validation_started = perf_counter()
    affine_error = max(
        affine_numerator_error,
        affine_reach_error,
        query_numerator_error,
        query_reach_error,
    )
    maximum_source_error = max(source_error, refreshed_source_error)
    maximum_source_relative = max(source_relative, refreshed_source_relative)
    validation_arrays = (
        source_actual,
        source_expected,
        refreshed_source_actual,
        refreshed_source_expected,
        direct_actual,
        direct_expected,
        actual_numerator,
        expected_numerator,
        actual_reach,
        expected_reach,
        query_actual_numerator,
        query_expected_numerator,
        query_actual_reach,
        query_expected_reach,
        np.asarray((forward_dot, transpose_dot), dtype=np.float64),
    )
    sample_sha256 = _sample_digest(*validation_arrays)

    errors = {
        "source_sample_absolute": maximum_source_error,
        "source_sample_relative": maximum_source_relative,
        "direct_query_absolute": direct_error,
        "direct_query_relative": direct_relative,
        "affine_sample_absolute": affine_error,
        "dot_product_absolute": dot_error,
        "dot_product_relative": dot_relative,
    }
    work = dict(stage_work(available_cards))
    validation_host_ms += (perf_counter() - validation_started) * 1000.0
    gates = {
        "semantic_identity": (
            stage_semantic_identity(available_cards) == expected_semantic_identity
        ),
        "complete_geometry": (
            len(fixture.query_masks) == geometry.labeled_query_records
            and len(fixture.source_pair_positions) == SOURCE_LABELS
        ),
        "source_rank_and_feature_width": (
            fixture.source_rank == SOURCE_RANK
            and fixture.feature_width == FEATURE_WIDTH
        ),
        "fixed_allocation": live_allocation.fixed_cap_pass
        and live_allocation.physical_reserve_pass,
        "live_allocation": live_allocation.live_reserve_pass is True,
        "source_samples": (
            maximum_source_error <= MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR
        ),
        "direct_queries": (
            direct_error <= MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR
            and direct_relative <= MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR
        ),
        "affine_samples": affine_error <= MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR,
        "dot_product": (
            dot_error <= MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR
            and dot_relative <= MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR
        ),
        "warm_byte_identity": all(warm_identity_observations),
        "source_refresh_byte_identity": all(refresh_identity_observations),
        "query_only_byte_identity": all(query_identity_observations),
        "adjoint_byte_identity": all(adjoint_identity_observations),
        "refresh_work_equals_cold": (
            work["source_refresh_pairing_visits"]
            == work["cold_source_pairing_visits"]
            and work["source_refresh_recurrence_scalar_additions"]
            == work["cold_recurrence_scalar_additions"]
        ),
        "query_only_reuses_source": (
            work["query_only_source_pairing_visits"] == 0
            and work["query_only_recurrence_scalar_additions"] == 0
        ),
        "adjoint_unique_only": work["adjoint_allocated_label_writes"] == 0,
        "repetition_counts": (
            len(warm_timings) == WARM_REPETITIONS
            and len(refresh_timings) == SOURCE_REFRESH_REPETITIONS
            and len(query_timings) == QUERY_ONLY_REPETITIONS
            and len(adjoint_timings) == 1 + ADJOINT_WARM_REPETITIONS
        ),
    }

    del (
        adjoint_reference,
        unique_adjoint,
        adjoint_table,
        aggregated,
        query_covectors,
        original_unary,
        refreshed_unary,
        query_unary,
        state,
    )
    gc.collect()
    default_pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    cp.cuda.get_current_stream().synchronize()
    free_after, total_after = cp.cuda.runtime.memGetInfo()
    pool_used_after = int(default_pool.used_bytes())
    pool_total_after = int(default_pool.total_bytes())
    pinned_free_after = int(pinned_pool.n_free_blocks())
    pools_released = (
        pool_used_after == 0
        and pool_total_after == 0
        and pinned_free_after == 0
        and int(total_after) == int(total)
    )
    gates["memory_pools_released"] = pools_released
    stage_wall_ms = (perf_counter() - stage_started) * 1000.0
    gates["stage_wall"] = stage_wall_ms <= STAGE_WALL_LIMIT_MS
    gates["all_numeric_finite"] = all(isfinite(value) for value in errors.values())
    gates["observed_pool_within_model"] = (
        max(observed_pool_bytes, default=0)
        <= live_allocation.requested_device_peak_bytes
    )
    passed = all(gates.values())
    return {
        "schema_version": STAGE_SCHEMA_VERSION,
        "available_cards": available_cards,
        "semantic_identity_sha256": expected_semantic_identity,
        "runtime": runtime,
        "geometry": {
            field: getattr(geometry, field)
            for field in StageGeometry.__dataclass_fields__
        },
        "allocation": _allocation_evidence(
            live_allocation,
            observed_pool_used_bytes=observed_pool_bytes,
            device_free_bytes_after_release=int(free_after),
            pool_used_bytes_after_release=pool_used_after,
            pool_total_bytes_after_release=pool_total_after,
            pinned_free_blocks_after_release=pinned_free_after,
            device_total_bytes_after_release=int(total_after),
        ),
        "work": work,
        "samples": {
            "source_ranks": list(source_ranks),
            "query_ranks": list(query_ranks),
            "query_features": list(QUERY_SAMPLE_FEATURES),
            "sample_sha256": sample_sha256,
            "identity_observations": {
                "warm": warm_identity_observations,
                "source_refresh": refresh_identity_observations,
                "query_only": query_identity_observations,
                "adjoint": adjoint_identity_observations,
            },
        },
        "errors_hex": {
            field: _float_text(value) for field, value in errors.items()
        },
        "timings": {
            "cold": _timing_summary((cold_timing,)),
            "warm": _timing_summary(warm_timings),
            "source_refresh": _timing_summary(refresh_timings),
            "query_only": _timing_summary(query_timings),
            "direct_query": _timing_summary(
                ({"direct_scan": direct_wall_ms},)
            ),
            "adjoint": _timing_summary(adjoint_timings),
            "host_hex": {
                "topology": _float_text(topology_ms),
                "allocation_and_transfer": _float_text(transfer_ms),
                "cold": _float_text(cold_host_ms),
                "warm_campaign": _float_text(warm_host_ms),
                "source_refresh_campaign": _float_text(refresh_host_ms),
                "query_only_campaign": _float_text(query_host_ms),
                "adjoint_campaign": _float_text(adjoint_host_ms),
                "validation": _float_text(validation_host_ms),
                "stage_total": _float_text(stage_wall_ms),
            },
        },
        "gates": gates,
        "passed": passed,
        "rejection_reason": None if passed else "stage_conjunct_rejected",
        "claims": dict(STAGE_CLAIMS),
    }


def build_allocation_rejection_stage_payload(
    available_cards: int,
    *,
    allocation: StageAllocation,
    topology_ms: float,
    stage_total_ms: float,
    reason: str,
    runtime: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if reason not in {"fixed_preallocation_rejected", "live_preallocation_rejected"}:
        raise ValueError("unknown staged allocation rejection")
    geometry = stage_geometry(available_cards)
    gates = {
        "fixed_allocation": allocation.fixed_cap_pass
        and allocation.physical_reserve_pass,
        "live_allocation": allocation.live_reserve_pass is True,
    }
    return {
        "schema_version": STAGE_SCHEMA_VERSION,
        "available_cards": available_cards,
        "semantic_identity_sha256": stage_semantic_identity(available_cards),
        "runtime": None if runtime is None else dict(runtime),
        "geometry": {
            field: getattr(geometry, field)
            for field in StageGeometry.__dataclass_fields__
        },
        "allocation": _allocation_evidence(allocation),
        "work": dict(stage_work(available_cards)),
        "samples": None,
        "errors_hex": None,
        "timings": {
            "host_hex": {
                "topology": _float_text(topology_ms),
                "stage_total": _float_text(stage_total_ms),
            }
        },
        "gates": gates,
        "passed": False,
        "rejection_reason": reason,
        "claims": dict(STAGE_CLAIMS),
    }


def build_synthetic_stage_payload(
    available_cards: int,
    *,
    passed: bool = True,
) -> dict[str, object]:
    """Build schema-complete synthetic evidence without importing CuPy."""

    fixture = compile_stage_fixture(available_cards)
    allocation = stage_allocation(fixture, live_free_bytes=15_000_000_000)
    geometry = stage_geometry(available_cards)
    timings: dict[str, object] = {}
    for lane, count in STAGE_TIMING_COUNTS.items():
        rows = []
        for index in range(count):
            base = (available_cards + index + len(lane)) / 10_000.0
            if lane == "direct_query":
                row = {"direct_scan": base}
            elif lane == "adjoint":
                row = {
                    "query_aggregation": base,
                    "recurrence": base * 2.0,
                    "signed_source": base * 3.0,
                }
                row["device_sum"] = sum(row.values())
            else:
                row = {
                    "source_coefficients": 0.0 if lane == "query_only" else base,
                    "recurrence": 0.0 if lane == "query_only" else base * 2.0,
                    "signed_query": base * 3.0,
                    "affine_fold": base * 4.0,
                }
                row["device_sum"] = sum(row.values())
            rows.append(row)
        timings[lane] = _timing_summary(rows)
    identity_observations = {
        "warm": [True] * WARM_REPETITIONS,
        "source_refresh": [True] * SOURCE_REFRESH_REPETITIONS,
        "query_only": [True] * QUERY_ONLY_REPETITIONS,
        "adjoint": [True] * (1 + ADJOINT_WARM_REPETITIONS),
    }
    work = dict(stage_work(available_cards))
    errors = {
        "source_sample_absolute": (
            1e-15 if passed else 2.0 * MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR
        ),
        "source_sample_relative": 1e-15,
        "direct_query_absolute": 1e-12,
        "direct_query_relative": 1e-13,
        "affine_sample_absolute": 1e-13,
        "dot_product_absolute": 1e-12,
        "dot_product_relative": 1e-13,
    }
    stage_total = 10.0 + available_cards
    gates = {
        "semantic_identity": True,
        "complete_geometry": True,
        "source_rank_and_feature_width": True,
        "fixed_allocation": allocation.fixed_cap_pass
        and allocation.physical_reserve_pass,
        "live_allocation": allocation.live_reserve_pass is True,
        "source_samples": passed,
        "direct_queries": True,
        "affine_samples": True,
        "dot_product": True,
        "warm_byte_identity": True,
        "source_refresh_byte_identity": True,
        "query_only_byte_identity": True,
        "adjoint_byte_identity": True,
        "refresh_work_equals_cold": (
            work["source_refresh_pairing_visits"]
            == work["cold_source_pairing_visits"]
            and work["source_refresh_recurrence_scalar_additions"]
            == work["cold_recurrence_scalar_additions"]
        ),
        "query_only_reuses_source": (
            work["query_only_source_pairing_visits"] == 0
            and work["query_only_recurrence_scalar_additions"] == 0
        ),
        "adjoint_unique_only": work["adjoint_allocated_label_writes"] == 0,
        "repetition_counts": True,
        "memory_pools_released": True,
        "stage_wall": stage_total <= STAGE_WALL_LIMIT_MS,
        "all_numeric_finite": all(isfinite(value) for value in errors.values()),
        "observed_pool_within_model": True,
    }
    runtime = {
        "device_name": REQUIRED_DEVICE_NAME,
        "compute_capability": REQUIRED_COMPUTE_CAPABILITY,
        "cupy_version": REQUIRED_CUPY_VERSION,
        "cuda_runtime_version": REQUIRED_CUDA_RUNTIME_VERSION,
        "cuda_driver_version": MINIMUM_CUDA_DRIVER_VERSION,
        "device_total_bytes": 17_094_475_776,
    }
    return {
        "schema_version": STAGE_SCHEMA_VERSION,
        "available_cards": available_cards,
        "semantic_identity_sha256": stage_semantic_identity(available_cards),
        "runtime": runtime,
        "geometry": {
            field: getattr(geometry, field)
            for field in StageGeometry.__dataclass_fields__
        },
        "allocation": _allocation_evidence(
            allocation,
            observed_pool_used_bytes=(allocation.requested_device_peak_bytes,),
            device_free_bytes_after_release=15_000_000_000,
            pool_used_bytes_after_release=0,
            pool_total_bytes_after_release=0,
            pinned_free_blocks_after_release=0,
            device_total_bytes_after_release=int(runtime["device_total_bytes"]),
        ),
        "work": work,
        "samples": {
            "source_ranks": list(source_sample_ranks(available_cards)),
            "query_ranks": list(query_sample_ranks(available_cards)),
            "query_features": list(QUERY_SAMPLE_FEATURES),
            "sample_sha256": sha256(
                f"synthetic-stage-{available_cards}".encode("ascii")
            ).hexdigest(),
            "identity_observations": identity_observations,
        },
        "errors_hex": {field: _float_text(value) for field, value in errors.items()},
        "timings": {
            **timings,
            "host_hex": {
                "topology": _float_text(1.0),
                "allocation_and_transfer": _float_text(2.0),
                "cold": _float_text(3.0),
                "warm_campaign": _float_text(4.0),
                "source_refresh_campaign": _float_text(5.0),
                "query_only_campaign": _float_text(6.0),
                "adjoint_campaign": _float_text(7.0),
                "validation": _float_text(8.0),
                "stage_total": _float_text(stage_total),
            },
        },
        "gates": gates,
        "passed": all(gates.values()),
        "rejection_reason": None if passed else "synthetic_numerical_rejection",
        "claims": dict(STAGE_CLAIMS),
    }


def _validate_stage_allocation(
    value: object,
    *,
    fixture: bounded.FrozenQuotientFixture,
    runtime: Mapping[str, object] | None,
    completed: bool,
) -> tuple[StageAllocation, dict[str, object]]:
    if not isinstance(value, Mapping):
        raise TypeError("stage allocation must be a mapping")
    recorded = dict(value)
    expected_fields = set(_allocation_evidence(stage_allocation(fixture)))
    if set(recorded) != expected_fields:
        raise ValueError("stage allocation fields drifted")
    live_free = recorded["live_free_bytes"]
    if live_free is not None:
        live_free = _integer(live_free, label="stage live free bytes")
    modeled = stage_allocation(fixture, live_free_bytes=live_free)
    expected_fixed = _allocation_evidence(modeled)
    for field in (
        "arrays",
        "static_device_bytes",
        "forward_base_bytes",
        "warm_forward_peak_bytes",
        "query_only_peak_bytes",
        "adjoint_peak_bytes",
        "dot_product_peak_bytes",
        "requested_device_peak_bytes",
        "live_free_bytes",
        "fixed_cap_pass",
        "physical_reserve_pass",
        "live_reserve_pass",
    ):
        if recorded[field] != expected_fixed[field]:
            raise ValueError(f"stage allocation model drifted: {field}")

    diagnostic_fields = (
        "observed_pool_used_bytes",
        "device_free_bytes_after_release",
        "pool_used_bytes_after_release",
        "pool_total_bytes_after_release",
        "pinned_free_blocks_after_release",
        "device_total_bytes_after_release",
    )
    if not completed:
        if any(recorded[field] is not None for field in diagnostic_fields):
            raise ValueError("allocation rejection records post-allocation diagnostics")
        return modeled, recorded
    if runtime is None:
        raise ValueError("completed stage omits runtime identity")
    runtime_total = int(runtime["device_total_bytes"])
    observations = recorded["observed_pool_used_bytes"]
    if not isinstance(observations, list) or not observations:
        raise ValueError("completed stage omits pool observations")
    for observation in observations:
        measured = _integer(observation, label="observed pool bytes")
        if measured > runtime_total:
            raise ValueError("observed pool bytes exceed physical device")
    for field in diagnostic_fields[1:]:
        _integer(recorded[field], label=field)
    if recorded["device_free_bytes_after_release"] > runtime_total:
        raise ValueError("released free bytes exceed physical device")
    if recorded["device_total_bytes_after_release"] != runtime_total:
        raise ValueError("device total changed across stage release")
    return modeled, recorded


def _validate_timing_lane(
    value: object,
    *,
    lane: str,
) -> dict[str, tuple[float, ...]]:
    if not isinstance(value, Mapping) or set(value) != {"count", "phases"}:
        raise ValueError(f"timing {lane} summary fields drifted")
    count = STAGE_TIMING_COUNTS[lane]
    if value["count"] != count:
        raise ValueError("timing repetition count drifted")
    phases = value["phases"]
    if not isinstance(phases, Mapping) or set(phases) != set(STAGE_TIMING_PHASES[lane]):
        raise ValueError(f"timing {lane} phase order drifted")
    parsed_phases: dict[str, tuple[float, ...]] = {}
    for phase, record in phases.items():
        if not isinstance(record, Mapping) or set(record) != {
            "raw_hex",
            "median_hex",
            "maximum_hex",
        }:
            raise ValueError(f"timing phase {lane}.{phase} fields drifted")
        raw = record["raw_hex"]
        if not isinstance(raw, list) or len(raw) != count:
            raise ValueError("timing raw observations drifted")
        parsed = tuple(
            parse_float_text(item, label=f"timing {lane}.{phase}")
            for item in raw
        )
        if any(item < 0.0 for item in parsed):
            raise ValueError("timing observation is negative")
        median = parse_float_text(
            record["median_hex"],
            label=f"timing {lane}.{phase} median",
        )
        maximum = parse_float_text(
            record["maximum_hex"],
            label=f"timing {lane}.{phase} maximum",
        )
        if median != float(np.median(np.asarray(parsed, dtype=np.float64))):
            raise ValueError("timing median is not independently reproduced")
        if maximum != max(parsed):
            raise ValueError("timing maximum is not independently reproduced")
        parsed_phases[str(phase)] = parsed
    if "device_sum" in parsed_phases:
        components = tuple(
            phase for phase in STAGE_TIMING_PHASES[lane] if phase != "device_sum"
        )
        for index, recorded_sum in enumerate(parsed_phases["device_sum"]):
            reconstructed = sum(parsed_phases[phase][index] for phase in components)
            if recorded_sum != reconstructed:
                raise ValueError(f"timing {lane} device sum drifted")
    if lane == "query_only" and any(
        value != 0.0
        for phase in ("source_coefficients", "recurrence")
        for value in parsed_phases[phase]
    ):
        raise ValueError("query-only timing performs source work")
    return parsed_phases


def _lower_hex_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is not a lowercase SHA-256 digest")
    return value


def validate_stage_payload(
    payload: Mapping[str, object],
    *,
    expected_cards: int,
) -> dict[str, object]:
    """Rebind one stage without importing CuPy or trusting recorded summaries."""

    if not isinstance(payload, Mapping):
        raise TypeError("stage payload must be a mapping")
    plain = dict(payload)
    required = {
        "schema_version",
        "available_cards",
        "semantic_identity_sha256",
        "runtime",
        "geometry",
        "allocation",
        "work",
        "samples",
        "errors_hex",
        "timings",
        "gates",
        "passed",
        "rejection_reason",
        "claims",
    }
    if set(plain) != required:
        raise ValueError("stage payload fields differ from ADR-0373")
    if plain["schema_version"] != STAGE_SCHEMA_VERSION:
        raise ValueError("stage payload schema drifted")
    if plain["available_cards"] != expected_cards:
        raise ValueError("stage payload card order drifted")
    expected_semantic = stage_semantic_identity(expected_cards)
    if plain["semantic_identity_sha256"] != expected_semantic:
        raise ValueError("stage semantic identity drifted")
    expected_geometry = stage_geometry(expected_cards)
    geometry = plain["geometry"]
    if not isinstance(geometry, Mapping) or dict(geometry) != {
        field: getattr(expected_geometry, field)
        for field in StageGeometry.__dataclass_fields__
    }:
        raise ValueError("stage geometry drifted")
    expected_work = dict(stage_work(expected_cards))
    if not isinstance(plain["work"], Mapping) or dict(plain["work"]) != expected_work:
        raise ValueError("stage work ledger drifted")
    claims = plain["claims"]
    if not isinstance(claims, Mapping) or dict(claims) != dict(STAGE_CLAIMS):
        raise ValueError("stage claims boundary drifted")
    if type(plain["passed"]) is not bool:
        raise TypeError("stage pass bit is not Boolean")

    errors_payload = plain["errors_hex"]
    samples_payload = plain["samples"]
    completed = errors_payload is not None or samples_payload is not None
    if (errors_payload is None) != (samples_payload is None):
        raise ValueError("stage samples and errors have different completion state")

    runtime_payload = plain["runtime"]
    runtime: dict[str, object] | None
    if runtime_payload is None:
        runtime = None
    else:
        if not isinstance(runtime_payload, Mapping):
            raise TypeError("stage runtime must be a mapping or null")
        runtime = dict(runtime_payload)
        if set(runtime) != {
            "device_name",
            "compute_capability",
            "cupy_version",
            "cuda_runtime_version",
            "cuda_driver_version",
            "device_total_bytes",
        }:
            raise ValueError("stage runtime fields drifted")
        validate_runtime_identity(runtime)
    fixture = compile_stage_fixture(expected_cards)
    allocation, allocation_payload = _validate_stage_allocation(
        plain["allocation"],
        fixture=fixture,
        runtime=runtime,
        completed=completed,
    )
    gates_payload = plain["gates"]
    if not isinstance(gates_payload, Mapping) or any(
        type(value) is not bool for value in gates_payload.values()
    ):
        raise TypeError("stage gates must be Booleans")
    gates = dict(gates_payload)
    timings_payload = plain["timings"]
    if not isinstance(timings_payload, Mapping):
        raise TypeError("stage timings must be a mapping")

    if not completed:
        if set(timings_payload) != {"host_hex"}:
            raise ValueError("allocation rejection records device timings")
        host = timings_payload["host_hex"]
        if not isinstance(host, Mapping) or set(host) != {"topology", "stage_total"}:
            raise ValueError("allocation rejection host timings drifted")
        host_values = {
            field: parse_float_text(value, label=f"host timing {field}")
            for field, value in host.items()
        }
        if any(value < 0.0 for value in host_values.values()):
            raise ValueError("allocation rejection host timing is negative")
        if host_values["stage_total"] < host_values["topology"]:
            raise ValueError("allocation rejection stage wall precedes topology")
        reason = plain["rejection_reason"]
        if reason not in {"fixed_preallocation_rejected", "live_preallocation_rejected"}:
            raise ValueError("allocation rejection reason drifted")
        expected_gates = {
            "fixed_allocation": (
                allocation.fixed_cap_pass and allocation.physical_reserve_pass
            ),
            "live_allocation": allocation.live_reserve_pass is True,
        }
        if reason == "fixed_preallocation_rejected":
            if expected_gates["fixed_allocation"] or runtime is not None:
                raise ValueError("fixed allocation rejection is inconsistent")
        elif (
            not expected_gates["fixed_allocation"]
            or expected_gates["live_allocation"]
            or runtime is None
        ):
            raise ValueError("live allocation rejection is inconsistent")
        if gates != expected_gates:
            raise ValueError("allocation rejection gates were not reconstructed")
        if plain["passed"] is not False:
            raise ValueError("allocation rejection is marked passing")
        return plain

    if runtime is None:
        raise ValueError("completed stage omits runtime identity")
    if set(timings_payload) != {*STAGE_TIMING_PHASES, "host_hex"}:
        raise ValueError("completed stage timing lanes drifted")
    parsed_lanes = {
        lane: _validate_timing_lane(timings_payload[lane], lane=lane)
        for lane in STAGE_TIMING_PHASES
    }
    host = timings_payload["host_hex"]
    if not isinstance(host, Mapping) or set(host) != set(STAGE_HOST_TIMING_FIELDS):
        raise ValueError("completed stage host timing fields drifted")
    host_values = {
        field: parse_float_text(value, label=f"host timing {field}")
        for field, value in host.items()
    }
    if any(value < 0.0 for value in host_values.values()):
        raise ValueError("completed stage host timing is negative")
    if host_values["stage_total"] < max(host_values.values()):
        raise ValueError("stage total is smaller than a component wall")

    if not isinstance(errors_payload, Mapping) or set(errors_payload) != set(
        STAGE_ERROR_FIELDS
    ):
        raise ValueError("stage numerical error fields drifted")
    errors = {
        field: parse_float_text(value, label=f"stage error {field}")
        for field, value in errors_payload.items()
    }
    if any(value < 0.0 for value in errors.values()):
        raise ValueError("stage numerical error is negative")
    if not isinstance(samples_payload, Mapping) or set(samples_payload) != {
        "source_ranks",
        "query_ranks",
        "query_features",
        "sample_sha256",
        "identity_observations",
    }:
        raise ValueError("stage sample fields drifted")
    if samples_payload["source_ranks"] != list(source_sample_ranks(expected_cards)):
        raise ValueError("stage source sample ranks drifted")
    if samples_payload["query_ranks"] != list(query_sample_ranks(expected_cards)):
        raise ValueError("stage query sample ranks drifted")
    if samples_payload["query_features"] != list(QUERY_SAMPLE_FEATURES):
        raise ValueError("stage query sample features drifted")
    _lower_hex_digest(samples_payload["sample_sha256"], label="stage sample")
    observations_payload = samples_payload["identity_observations"]
    expected_observation_counts = {
        "warm": WARM_REPETITIONS,
        "source_refresh": SOURCE_REFRESH_REPETITIONS,
        "query_only": QUERY_ONLY_REPETITIONS,
        "adjoint": 1 + ADJOINT_WARM_REPETITIONS,
    }
    if not isinstance(observations_payload, Mapping) or set(
        observations_payload
    ) != set(expected_observation_counts):
        raise ValueError("stage identity-observation lanes drifted")
    identity_observations: dict[str, list[bool]] = {}
    for lane, count in expected_observation_counts.items():
        values = observations_payload[lane]
        if (
            not isinstance(values, list)
            or len(values) != count
            or any(type(value) is not bool for value in values)
        ):
            raise ValueError("stage identity observations drifted")
        identity_observations[lane] = values

    observed_pool = allocation_payload["observed_pool_used_bytes"]
    memory_released = (
        allocation_payload["pool_used_bytes_after_release"] == 0
        and allocation_payload["pool_total_bytes_after_release"] == 0
        and allocation_payload["pinned_free_blocks_after_release"] == 0
        and allocation_payload["device_total_bytes_after_release"]
        == runtime["device_total_bytes"]
    )
    expected_gates = {
        "semantic_identity": plain["semantic_identity_sha256"] == expected_semantic,
        "complete_geometry": True,
        "source_rank_and_feature_width": (
            fixture.source_rank == SOURCE_RANK
            and fixture.feature_width == FEATURE_WIDTH
        ),
        "fixed_allocation": (
            allocation.fixed_cap_pass and allocation.physical_reserve_pass
        ),
        "live_allocation": allocation.live_reserve_pass is True,
        "source_samples": (
            errors["source_sample_absolute"]
            <= MAXIMUM_SOURCE_SAMPLE_ABSOLUTE_ERROR
        ),
        "direct_queries": (
            errors["direct_query_absolute"]
            <= MAXIMUM_DIRECT_QUERY_ABSOLUTE_ERROR
            and errors["direct_query_relative"]
            <= MAXIMUM_DIRECT_QUERY_RELATIVE_ERROR
        ),
        "affine_samples": (
            errors["affine_sample_absolute"]
            <= MAXIMUM_AFFINE_SAMPLE_ABSOLUTE_ERROR
        ),
        "dot_product": (
            errors["dot_product_absolute"] <= MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR
            and errors["dot_product_relative"]
            <= MAXIMUM_DOT_PRODUCT_RELATIVE_ERROR
        ),
        "warm_byte_identity": all(identity_observations["warm"]),
        "source_refresh_byte_identity": all(
            identity_observations["source_refresh"]
        ),
        "query_only_byte_identity": all(identity_observations["query_only"]),
        "adjoint_byte_identity": all(identity_observations["adjoint"]),
        "refresh_work_equals_cold": (
            expected_work["source_refresh_pairing_visits"]
            == expected_work["cold_source_pairing_visits"]
            and expected_work["source_refresh_recurrence_scalar_additions"]
            == expected_work["cold_recurrence_scalar_additions"]
        ),
        "query_only_reuses_source": (
            expected_work["query_only_source_pairing_visits"] == 0
            and expected_work["query_only_recurrence_scalar_additions"] == 0
        ),
        "adjoint_unique_only": expected_work["adjoint_allocated_label_writes"] == 0,
        "repetition_counts": all(
            len(parsed_lanes[lane][next(iter(parsed_lanes[lane]))])
            == STAGE_TIMING_COUNTS[lane]
            for lane in STAGE_TIMING_COUNTS
        ),
        "memory_pools_released": memory_released,
        "stage_wall": host_values["stage_total"] <= STAGE_WALL_LIMIT_MS,
        "all_numeric_finite": all(isfinite(value) for value in errors.values()),
        "observed_pool_within_model": (
            max(observed_pool, default=0)
            <= allocation.requested_device_peak_bytes
        ),
    }
    if set(gates) != set(STAGE_GATE_FIELDS) or gates != expected_gates:
        raise ValueError("stage gates were not independently reconstructed")
    expected_pass = all(expected_gates.values())
    if plain["passed"] is not expected_pass:
        raise ValueError("stage pass bit differs from reconstructed gates")
    reason = plain["rejection_reason"]
    if expected_pass:
        if reason is not None:
            raise ValueError("passing stage records a rejection reason")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("rejected stage omits its reason")
    return plain


__all__ = [
    "ADJOINT_WARM_REPETITIONS",
    "CAMPAIGN_WALL_LIMIT_MS",
    "DEVICE_RESERVE_BYTES",
    "FEATURE_WIDTH",
    "FIXED_DEVICE_NUMERIC_CAP_BYTES",
    "GPU_QUOTIENT_STAGED_SCALING_PROTOCOL",
    "GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256",
    "MINIMUM_DEVICE_PHYSICAL_BYTES",
    "QUERY_ONLY_REPETITIONS",
    "QUERY_SAMPLE_FEATURES",
    "RESULT_RELATIVE_PATH",
    "SOURCE_RANK",
    "SOURCE_REFRESH_REPETITIONS",
    "STAGE_CARDS",
    "STAGE_WALL_LIMIT_MS",
    "StageAllocation",
    "StageGeometry",
    "WARM_REPETITIONS",
    "build_allocation_rejection_stage_payload",
    "build_synthetic_stage_payload",
    "compile_stage_fixture",
    "execute_gpu_stage",
    "parse_float_text",
    "query_only_fixture",
    "query_sample_ranks",
    "source_refresh_fixture",
    "source_sample_ranks",
    "stage_allocation",
    "stage_geometry",
    "stage_semantic_identity",
    "stage_work",
    "validate_runtime_identity",
    "validate_stage_payload",
]
