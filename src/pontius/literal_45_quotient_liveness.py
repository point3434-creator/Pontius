"""Pure literal-45 lifetime arithmetic and bounded streaming controls.

ADR-0378 permits no device entry point.  This module derives allocation rows
from shapes, sweeps their explicit phase lifetimes, and provides small exact
controls for the future streamed validation seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import comb
from types import MappingProxyType
from typing import Literal, Mapping, Sequence

import numpy as np

from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)


AVAILABLE_CARDS = 45
HAND_CARDS = 2
SOURCE_CARDS = 6
QUERY_CARDS = 4
SOURCE_LABELS = 90
QUERY_LABELS = 6
STRENGTH_CODES = 43
SOURCE_RANK = 127
FEATURE_WIDTH = SOURCE_RANK + 1
VALIDATION_CHUNK_BYTES = 67_108_864
CUDA_LIBRARY_SCRATCH_BYTES = 67_108_864

HOST_NUMERIC_CAP_BYTES = 48_000_000_000
DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
HOST_RESERVE_BYTES = 8_000_000_000
DEVICE_RESERVE_BYTES = 2_000_000_000
MINIMUM_HOST_PHYSICAL_BYTES = 60_000_000_000
MINIMUM_DEVICE_PHYSICAL_BYTES = 16_000_000_000

STAGED_MECHANISM_CANONICAL_LF_SHA256 = (
    "144b23ff92f5498624acd1e09f4b4d1d4565e5c80106e496fcc46b0bc4667750"
)
RETAINED_STAGED_ARTIFACT_SHA256 = (
    "dd5b6d04cd45db0c3a95acdd1bcd05355c72be0852701df347696442261a2b72"
)

PHASES = (
    "host_topology",
    "forward",
    "forward_reference",
    "warm_refresh_query_validation",
    "direct_validation",
    "forward_dot",
    "forward_release",
    "adjoint",
    "adjoint_validation",
    "release",
)
_PHASE_INDEX = MappingProxyType({name: index for index, name in enumerate(PHASES)})

Placement = Literal["host", "device"]
SemanticCategory = Literal[
    "host_fixture",
    "forward_operator",
    "adjoint_operator",
    "validation",
    "shared_runtime",
]

CLAIMS = MappingProxyType(
    {
        "literal_45_device_result": None,
        "live_memory_admission": None,
        "latency_result": None,
        "action_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "poker_strength_result": None,
    }
)
EXCLUDED_MEMORY_CLASSES = (
    "Python objects and interpreter storage",
    "allocator fragmentation and pool retention beyond named live rows",
    "CUDA context, module, kernel-code, driver, and page-table storage",
    "kernel registers, local memory, and implementation-selected reduction state",
    "operating-system and unrelated-process activity",
)


def _positive_integer(value: int, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _shape(value: Sequence[int]) -> tuple[int, ...]:
    result = tuple(_positive_integer(int(item), label="shape entry") for item in value)
    if not result:
        raise ValueError("numeric rows require a nonempty shape")
    return result


@dataclass(frozen=True, slots=True)
class Literal45Geometry:
    available_cards: int
    hand_width: int
    source_occupancies: int
    query_occupancies: int
    labeled_query_records: int
    source_recurrence_rows: int
    adjoint_recurrence_rows: int
    source_rank: int
    feature_width: int


def literal_45_geometry() -> Literal45Geometry:
    cards = AVAILABLE_CARDS
    return Literal45Geometry(
        available_cards=cards,
        hand_width=comb(cards, HAND_CARDS),
        source_occupancies=comb(cards, SOURCE_CARDS),
        query_occupancies=comb(cards, QUERY_CARDS),
        labeled_query_records=comb(cards, QUERY_CARDS) * QUERY_LABELS,
        source_recurrence_rows=sum(comb(cards, width) for width in range(7)),
        adjoint_recurrence_rows=sum(comb(cards, width) for width in range(5)),
        source_rank=SOURCE_RANK,
        feature_width=FEATURE_WIDTH,
    )


def staged_family_automaton(available_cards: int) -> StructuredShowdownAutomaton:
    """Derive only the small structured automaton for the frozen fixture family."""

    cards = _positive_integer(available_cards, label="available cards")
    hand_width = comb(cards, HAND_CARDS)
    strength = np.arange(hand_width, dtype=np.int32) % STRENGTH_CODES
    return build_structured_showdown_automaton(
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


@dataclass(frozen=True, slots=True)
class LifetimeRow:
    name: str
    placement: Placement
    semantic_category: SemanticCategory
    dtype: str
    shape: tuple[int, ...]
    born: str
    last_live: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.isidentifier():
            raise ValueError("lifetime row names must be nonempty identifiers")
        if self.placement not in ("host", "device"):
            raise ValueError("lifetime row placement is invalid")
        if self.semantic_category not in (
            "host_fixture",
            "forward_operator",
            "adjoint_operator",
            "validation",
            "shared_runtime",
        ):
            raise ValueError("lifetime semantic category is invalid")
        np.dtype(self.dtype)
        _shape(self.shape)
        if self.born not in _PHASE_INDEX or self.last_live not in _PHASE_INDEX:
            raise ValueError("lifetime row names an unknown phase")
        if _PHASE_INDEX[self.born] > _PHASE_INDEX[self.last_live]:
            raise ValueError("lifetime row dies before it is born")

    @property
    def elements(self) -> int:
        return int(np.prod(self.shape, dtype=object))

    @property
    def numeric_bytes(self) -> int:
        return self.elements * np.dtype(self.dtype).itemsize

    def live_at(self, phase: str) -> bool:
        index = _PHASE_INDEX.get(phase)
        if index is None:
            raise ValueError("unknown lifetime phase")
        return _PHASE_INDEX[self.born] <= index <= _PHASE_INDEX[self.last_live]


def _row(
    name: str,
    placement: Placement,
    semantic_category: SemanticCategory,
    dtype: str,
    shape: Sequence[int],
    born: str,
    last_live: str,
) -> LifetimeRow:
    return LifetimeRow(
        name=name,
        placement=placement,
        semantic_category=semantic_category,
        dtype=np.dtype(dtype).str,
        shape=_shape(shape),
        born=born,
        last_live=last_live,
    )


def _automaton_rows(
    automaton: StructuredShowdownAutomaton,
    *,
    placement: Placement,
    prefix: str,
    semantic_category: SemanticCategory,
    born: str,
    last_live: str,
    include_metadata: bool,
) -> tuple[LifetimeRow, ...]:
    rows: list[LifetimeRow] = []
    for index, values in enumerate(automaton.transitions):
        rows.append(
            _row(
                f"{prefix}_transition_{index}",
                placement,
                semantic_category,
                values.dtype.str,
                values.shape,
                born,
                last_live,
            )
        )
    rows.append(
        _row(
            f"{prefix}_terminal_values",
            placement,
            semantic_category,
            automaton.terminal_winner_values.dtype.str,
            automaton.terminal_winner_values.shape,
            born,
            last_live,
        )
    )
    rows.append(
        _row(
            f"{prefix}_sunk_scalar",
            placement,
            semantic_category,
            np.dtype(np.float64).str,
            (1,),
            born,
            last_live,
        )
    )
    if include_metadata:
        for index, values in enumerate(automaton.bond_states):
            rows.append(
                _row(
                    f"{prefix}_bond_states_{index}",
                    placement,
                    semantic_category,
                    values.dtype.str,
                    values.shape,
                    born,
                    last_live,
                )
            )
    return tuple(rows)


def literal_45_lifetime_rows() -> tuple[LifetimeRow, ...]:
    geometry = literal_45_geometry()
    automaton = staged_family_automaton(AVAILABLE_CARDS)
    hand_width = geometry.hand_width
    unary_width = 5 * hand_width + 1
    query_records = geometry.labeled_query_records
    rows: list[LifetimeRow] = [
        # Host fixture: complete topology and every validation unary are priced.
        _row("host_query_masks", "host", "host_fixture", "uint64", (query_records,), "host_topology", "release"),
        _row("host_query_hand_indices", "host", "host_fixture", "int32", (query_records, 2), "host_topology", "release"),
        _row("host_pair_to_hand", "host", "host_fixture", "int32", (AVAILABLE_CARDS, AVAILABLE_CARDS), "host_topology", "release"),
        _row("host_source_pairings", "host", "host_fixture", "int8", (SOURCE_LABELS, SOURCE_CARDS), "host_topology", "release"),
        _row("host_original_unary", "host", "host_fixture", "float64", (1, unary_width), "host_topology", "release"),
        _row("host_refreshed_unary", "host", "validation", "float64", (1, unary_width), "host_topology", "release"),
        _row("host_query_unary", "host", "validation", "float64", (1, unary_width), "host_topology", "release"),
        _row("host_mode_factors", "host", "host_fixture", "float64", (1, unary_width), "host_topology", "release"),
        _row("host_mixture", "host", "host_fixture", "float64", (1,), "host_topology", "release"),
        _row("host_unary_offsets", "host", "host_fixture", "int32", (6,), "host_topology", "release"),
        # The fixture reuses one immutable strength vector for five seats.
        _row("host_strength_codes", "host", "host_fixture", "int32", (hand_width,), "host_topology", "host_topology"),
        _row("host_controlled_strength", "host", "host_fixture", "int32", (1,), "host_topology", "host_topology"),
        # One physical large reference changes role only after the transpose dot.
        _row("host_large_reference_buffer", "host", "validation", "float64", (geometry.source_occupancies, FEATURE_WIDTH), "forward_reference", "adjoint_validation"),
        _row("host_compatible_reference_buffer", "host", "validation", "float64", (query_records, FEATURE_WIDTH), "forward_reference", "forward_dot"),
        _row("host_scalar_reference_buffer", "host", "validation", "float64", (query_records, 2), "forward_reference", "warm_refresh_query_validation"),
        _row("host_validation_staging", "host", "validation", "uint8", (VALIDATION_CHUNK_BYTES,), "forward_reference", "adjoint_validation"),
        _row("host_dot_scalars", "host", "validation", "float64", (2,), "forward_dot", "adjoint_validation"),
        # Device operator state. One active unary is overwritten between classes.
        _row("device_query_masks", "device", "forward_operator", "uint64", (query_records,), "forward", "forward_dot"),
        _row("device_query_hand_indices", "device", "forward_operator", "int32", (query_records, 2), "forward", "forward_dot"),
        _row("device_pair_to_hand", "device", "forward_operator", "int32", (AVAILABLE_CARDS, AVAILABLE_CARDS), "forward", "forward_dot"),
        _row("device_source_pairings", "device", "forward_operator", "int8", (SOURCE_LABELS, SOURCE_CARDS), "forward", "forward_dot"),
        _row("device_active_unary", "device", "forward_operator", "float64", (1, unary_width), "forward", "forward_dot"),
        _row("device_mode_factors", "device", "forward_operator", "float64", (1, unary_width), "forward", "forward_dot"),
        _row("device_mixture", "device", "forward_operator", "float64", (1,), "forward", "forward_dot"),
        _row("device_unary_offsets", "device", "forward_operator", "int32", (6,), "forward", "forward_dot"),
        _row("device_cardinality_offsets", "device", "shared_runtime", "int64", (SOURCE_CARDS + 1,), "forward", "adjoint_validation"),
        _row("device_source_recurrence", "device", "forward_operator", "float64", (geometry.source_recurrence_rows, FEATURE_WIDTH), "forward", "forward_dot"),
        _row("device_compatible_queries", "device", "forward_operator", "float64", (query_records, FEATURE_WIDTH), "forward", "forward_dot"),
        _row("device_query_numerator", "device", "forward_operator", "float64", (query_records,), "forward", "forward_dot"),
        _row("device_query_reach", "device", "forward_operator", "float64", (query_records,), "forward", "forward_dot"),
        _row("device_library_scratch", "device", "shared_runtime", "uint8", (CUDA_LIBRARY_SCRATCH_BYTES,), "forward", "adjoint_validation"),
        # Validation-only direct sample and streamed dot rows.
        _row("device_direct_source_ranks", "device", "validation", "int64", (16,), "direct_validation", "direct_validation"),
        _row("device_direct_query_masks", "device", "validation", "uint64", (8,), "direct_validation", "direct_validation"),
        _row("device_direct_features", "device", "validation", "int32", (8,), "direct_validation", "direct_validation"),
        _row("device_sample_workspace", "device", "validation", "float64", (16, FEATURE_WIDTH), "direct_validation", "direct_validation"),
        _row("device_direct_outputs", "device", "validation", "float64", (8, 8), "direct_validation", "direct_validation"),
        _row("device_query_covectors", "device", "adjoint_operator", "float64", (query_records, FEATURE_WIDTH), "forward_dot", "adjoint_validation"),
        _row("device_dot_partial_scratch", "device", "validation", "uint8", (VALIDATION_CHUNK_BYTES,), "forward_dot", "forward_dot"),
        _row("device_forward_dot_scalar", "device", "validation", "float64", (1,), "forward_dot", "forward_dot"),
        # Forward state is dead before these rows are born.
        _row("device_adjoint_aggregated_queries", "device", "adjoint_operator", "float64", (geometry.query_occupancies, FEATURE_WIDTH), "adjoint", "adjoint_validation"),
        _row("device_adjoint_recurrence", "device", "adjoint_operator", "float64", (geometry.adjoint_recurrence_rows, FEATURE_WIDTH), "adjoint", "adjoint_validation"),
        _row("device_unique_adjoint", "device", "adjoint_operator", "float64", (geometry.source_occupancies, FEATURE_WIDTH), "adjoint", "adjoint_validation"),
    ]
    rows.extend(
        _automaton_rows(
            automaton,
            placement="host",
            prefix="host_automaton",
            semantic_category="host_fixture",
            born="host_topology",
            last_live="release",
            include_metadata=True,
        )
    )
    rows.extend(
        _automaton_rows(
            automaton,
            placement="device",
            prefix="device_automaton",
            semantic_category="shared_runtime",
            born="forward",
            last_live="adjoint_validation",
            include_metadata=False,
        )
    )
    names = [row.name for row in rows]
    if len(names) != len(set(names)):
        raise AssertionError("literal-45 lifetime row names are not unique")
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class LegacyStageAllocation:
    available_cards: int
    forward_base_bytes: int
    warm_forward_peak_bytes: int
    query_only_peak_bytes: int
    adjoint_peak_bytes: int
    dot_product_peak_bytes: int
    requested_device_peak_bytes: int
    unnamed_full_product_counterfactual_bytes: int


def legacy_staged_allocation(available_cards: int) -> LegacyStageAllocation:
    """Independently reconstruct ADR-0374's old schedule without an allocation."""

    cards = _positive_integer(available_cards, label="available cards")
    hand_width = comb(cards, HAND_CARDS)
    source = comb(cards, SOURCE_CARDS)
    query = comb(cards, QUERY_CARDS)
    query_records = query * QUERY_LABELS
    source_rows = sum(comb(cards, width) for width in range(SOURCE_CARDS + 1))
    adjoint_rows = sum(comb(cards, width) for width in range(QUERY_CARDS + 1))
    automaton = staged_family_automaton(cards)
    float_bytes = np.dtype(np.float64).itemsize
    static = (
        query_records * (np.dtype(np.uint64).itemsize + 2 * np.dtype(np.int32).itemsize)
        + cards * cards * np.dtype(np.int32).itemsize
        + SOURCE_LABELS * SOURCE_CARDS * np.dtype(np.int8).itemsize
        + (5 * hand_width + 1) * float_bytes * 4
        + float_bytes
        + 6 * np.dtype(np.int32).itemsize
        + automaton.runtime_numeric_bytes
        + (SOURCE_CARDS + 1) * np.dtype(np.int64).itemsize
        + 16 * np.dtype(np.int64).itemsize
        + 8 * np.dtype(np.uint64).itemsize
        + 8 * np.dtype(np.int32).itemsize
    )
    source_feature = source * FEATURE_WIDTH * float_bytes
    compatible = query_records * FEATURE_WIDTH * float_bytes
    scalar = query_records * 2 * float_bytes
    source_table = source_rows * FEATURE_WIDTH * float_bytes
    aggregated = query * FEATURE_WIDTH * float_bytes
    adjoint_table = adjoint_rows * FEATURE_WIDTH * float_bytes
    forward = static + source_table + compatible + scalar + CUDA_LIBRARY_SCRATCH_BYTES
    warm = forward + source_feature + compatible + scalar
    query_only = forward + compatible + scalar
    adjoint = (
        static
        + compatible
        + aggregated
        + adjoint_table
        + 2 * source_feature
        + CUDA_LIBRARY_SCRATCH_BYTES
    )
    dot = (
        static
        + source_table
        + compatible
        + scalar
        + compatible
        + aggregated
        + adjoint_table
        + source_feature
        + CUDA_LIBRARY_SCRATCH_BYTES
    )
    requested = max(warm, query_only, adjoint, dot)
    return LegacyStageAllocation(
        available_cards=cards,
        forward_base_bytes=forward,
        warm_forward_peak_bytes=warm,
        query_only_peak_bytes=query_only,
        adjoint_peak_bytes=adjoint,
        dot_product_peak_bytes=dot,
        requested_device_peak_bytes=requested,
        unnamed_full_product_counterfactual_bytes=dot + compatible,
    )


@dataclass(frozen=True, slots=True)
class Literal45LivenessReport:
    geometry: Literal45Geometry
    rows: tuple[LifetimeRow, ...]
    host_phase_bytes: Mapping[str, int]
    device_phase_bytes: Mapping[str, int]
    host_peak_phase: str
    host_peak_bytes: int
    device_peak_phase: str
    device_peak_bytes: int
    production_forward_bytes: int
    adjoint_bytes: int
    host_numeric_cap_pass: bool
    device_numeric_cap_pass: bool
    host_physical_reserve_pass: bool
    device_physical_reserve_pass: bool
    live_host_free_bytes: None
    live_device_free_bytes: None
    live_admission_pass: None
    legacy_counterfactual: LegacyStageAllocation
    excluded_memory_classes: tuple[str, ...]
    claims: Mapping[str, object]


def _phase_totals(
    rows: Sequence[LifetimeRow], placement: Placement
) -> Mapping[str, int]:
    return MappingProxyType(
        {
            phase: sum(
                row.numeric_bytes
                for row in rows
                if row.placement == placement and row.live_at(phase)
            )
            for phase in PHASES
        }
    )


def build_literal_45_liveness_report() -> Literal45LivenessReport:
    rows = literal_45_lifetime_rows()
    host = _phase_totals(rows, "host")
    device = _phase_totals(rows, "device")
    host_peak_phase = max(PHASES, key=lambda phase: host[phase])
    device_peak_phase = max(PHASES, key=lambda phase: device[phase])
    host_peak = host[host_peak_phase]
    device_peak = device[device_peak_phase]
    return Literal45LivenessReport(
        geometry=literal_45_geometry(),
        rows=rows,
        host_phase_bytes=host,
        device_phase_bytes=device,
        host_peak_phase=host_peak_phase,
        host_peak_bytes=host_peak,
        device_peak_phase=device_peak_phase,
        device_peak_bytes=device_peak,
        production_forward_bytes=device["forward"],
        adjoint_bytes=device["adjoint"],
        host_numeric_cap_pass=host_peak <= HOST_NUMERIC_CAP_BYTES,
        device_numeric_cap_pass=device_peak <= DEVICE_NUMERIC_CAP_BYTES,
        host_physical_reserve_pass=(
            host_peak + HOST_RESERVE_BYTES <= MINIMUM_HOST_PHYSICAL_BYTES
        ),
        device_physical_reserve_pass=(
            device_peak + DEVICE_RESERVE_BYTES <= MINIMUM_DEVICE_PHYSICAL_BYTES
        ),
        live_host_free_bytes=None,
        live_device_free_bytes=None,
        live_admission_pass=None,
        legacy_counterfactual=legacy_staged_allocation(AVAILABLE_CARDS),
        excluded_memory_classes=EXCLUDED_MEMORY_CLASSES,
        claims=CLAIMS,
    )


def chunk_spans(
    total_bytes: int,
    chunk_bytes: int = VALIDATION_CHUNK_BYTES,
) -> tuple[tuple[int, int], ...]:
    if isinstance(total_bytes, bool) or not isinstance(total_bytes, int) or total_bytes < 0:
        raise ValueError("total bytes must be a nonnegative integer")
    size = _positive_integer(chunk_bytes, label="chunk bytes")
    if size % np.dtype(np.float64).itemsize:
        raise ValueError("validation chunks must align to Float64")
    return tuple(
        (start, min(total_bytes, start + size))
        for start in range(0, total_bytes, size)
    )


def _byte_view(values: np.ndarray) -> memoryview:
    if not isinstance(values, np.ndarray):
        raise TypeError("chunk validation requires numpy arrays")
    if not values.flags.c_contiguous:
        raise ValueError("chunk validation requires C-contiguous arrays")
    return memoryview(values).cast("B")


def literal_chunk_equal(
    first: np.ndarray,
    second: np.ndarray,
    *,
    chunk_bytes: int = VALIDATION_CHUNK_BYTES,
) -> bool:
    if first.shape != second.shape or first.dtype != second.dtype:
        return False
    left = _byte_view(first)
    right = _byte_view(second)
    return all(
        left[start:stop] == right[start:stop]
        for start, stop in chunk_spans(len(left), chunk_bytes)
    )


def chunk_diagnostic_sha256(
    values: np.ndarray,
    *,
    chunk_bytes: int = VALIDATION_CHUNK_BYTES,
) -> str:
    """Reporting-only digest; literal_chunk_equal remains acceptance authority."""

    raw = _byte_view(values)
    digest = sha256()
    for start, stop in chunk_spans(len(raw), chunk_bytes):
        digest.update(raw[start:stop])
    return digest.hexdigest()


def streamed_dot_exact(
    left: np.ndarray,
    right: np.ndarray,
    *,
    chunk_bytes: int = VALIDATION_CHUNK_BYTES,
) -> Fraction:
    """Bounded exact oracle for chunk-partition invariance, never target runtime."""

    if left.shape != right.shape or left.dtype != np.float64 or right.dtype != np.float64:
        raise ValueError("streamed exact dot requires equal Float64 shapes")
    if not left.flags.c_contiguous or not right.flags.c_contiguous:
        raise ValueError("streamed exact dot requires C-contiguous arrays")
    size = _positive_integer(chunk_bytes, label="chunk bytes")
    itemsize = np.dtype(np.float64).itemsize
    if size % itemsize:
        raise ValueError("dot chunks must align to Float64")
    elements_per_chunk = size // itemsize
    left_flat = left.reshape(-1)
    right_flat = right.reshape(-1)
    total = Fraction(0)
    for start in range(0, left_flat.size, elements_per_chunk):
        stop = min(left_flat.size, start + elements_per_chunk)
        for index in range(start, stop):
            total += Fraction.from_float(float(left_flat[index])) * Fraction.from_float(
                float(right_flat[index])
            )
    return total


LITERAL_45_LIVENESS_REPORT = build_literal_45_liveness_report()
