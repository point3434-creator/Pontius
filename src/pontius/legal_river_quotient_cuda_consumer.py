"""ADR-0389 offset-aware CUDA consumer for one legal river context.

Importing this module is deliberately device-free.  The public bounded entry
point is restricted to the complete 10- and 25-card conformance populations.
The actual 45-card entry point is owned separately by the durable no-argument
runner and is never called by source-seal controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import gc
from hashlib import sha256
import json
from math import comb, fsum
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .gpu_occupied_card_quotient import (
    cardinality_offsets,
    colex_rank,
    colex_unrank,
)
from .legal_river_quotient_bridge import (
    LegalRiverQuotientBridge,
    build_preregistered_legal_river_context,
    compile_legal_river_quotient_bridge,
)
from .legal_river_quotient_consumer_capacity import (
    build_legal_river_consumer_capacity_report,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/legal-river-quotient-cuda-consumer-v1.json"
PREREGISTERED_CONFIG_SHA256 = (
    "7328188d9f731415d4d70d5434b72463b982bc4b3627203347c7157a253486dd"
)

SOURCE_CARDS = 6
QUERY_CARDS = 4
QUERY_LABELS = 6
SOURCE_PAIRINGS = 90
SOURCE_RANK = 175
TOTAL_FEATURE_WIDTH = 176
PHYSICAL_STRIDE_WIDTH = 128
REACH_GLOBAL_FEATURE = 175
FEATURE_SLICES = ((0, 128), (128, 176))

_CUPY_IMPORT_CALLS = 0
_BOUNDED_EXECUTION_CALLS = 0
_ACTUAL_EXECUTION_CALLS = 0
_ACTUAL_NUMERIC_ALLOCATION_CALLS = 0
_ACTUAL_SCIENTIFIC_CALLS = 0


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"CUDA-consumer provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_cuda_consumer_config(
    path: Path = _CONFIG,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("CUDA-consumer config path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("CUDA-consumer config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != (
        PREREGISTERED_CONFIG_SHA256
    ):
        raise ValueError("CUDA-consumer config differs from ADR-0389")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("CUDA-consumer config root must be an object")
    if parsed.get("schema_version") != (
        "legal-river-quotient-cuda-consumer-config-v1"
    ):
        raise ValueError("CUDA-consumer config schema differs")
    if parsed.get("evidence_stage") != (
        "preregistered_after_adr0388_before_cuda_consumer_source_"
        "bounded_device_values_or_actual_45_card_value"
    ):
        raise ValueError("CUDA-consumer evidence stage differs")
    return parsed


_EXPECTED_SOURCE_PATHS = MappingProxyType(
    {
        "adr0384": _ROOT
        / "docs/decisions/ADR-0384-retain-the-passing-literal-45-quotient-target.md",
        "adr0388": _ROOT
        / "docs/decisions/ADR-0388-source-seal-the-actual-context-quotient-consumer-capacity.md",
        "artifact_marker": _ROOT / "artifacts/README.md",
        "consumer_capacity_config": _ROOT
        / "experiments/configs/legal-river-quotient-consumer-capacity-v1.json",
        "consumer_capacity_source": _ROOT
        / "src/pontius/legal_river_quotient_consumer_capacity.py",
        "durable_evidence_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
        "gitattributes": _ROOT / ".gitattributes",
        "gpu_occupied_card_quotient": _ROOT
        / "src/pontius/gpu_occupied_card_quotient.py",
        "gpu_quotient_validation_seam": _ROOT
        / "src/pontius/gpu_quotient_validation_seam.py",
        "legal_river_bridge_config": _ROOT
        / "experiments/configs/legal-river-quotient-bridge-v1.json",
        "legal_river_bridge_source": _ROOT
        / "src/pontius/legal_river_quotient_bridge.py",
        "literal_45_result_reader": _ROOT
        / "src/pontius/literal_45_quotient_target_result.py",
        "occupied_card_quotient": _ROOT / "src/pontius/occupied_card_quotient.py",
        "structured_showdown_automaton": _ROOT
        / "src/pontius/structured_showdown_automaton.py",
        "windows_process_memory": _ROOT / "src/pontius/windows_process_memory.py",
    }
)


def verify_preregistered_cuda_consumer_contract(
    config: Mapping[str, object] | None = None,
) -> None:
    parsed = load_preregistered_cuda_consumer_config() if config is None else config
    sources = parsed.get("expected_sources")
    if not isinstance(sources, Mapping) or set(sources) != set(_EXPECTED_SOURCE_PATHS):
        raise ValueError("CUDA-consumer dependency set differs")
    for label, path in _EXPECTED_SOURCE_PATHS.items():
        if sources[label] != canonical_lf_sha256(path):
            raise ValueError(f"CUDA-consumer dependency differs: {label}")

    geometry = parsed.get("geometry")
    streaming = parsed.get("streaming")
    slices = parsed.get("feature_slices")
    work = parsed.get("actual_work")
    claims = parsed.get("claims")
    if not all(isinstance(value, Mapping) for value in (geometry, streaming, slices, work, claims)):
        raise ValueError("CUDA-consumer typed contract sections are malformed")
    assert isinstance(geometry, Mapping)
    assert isinstance(streaming, Mapping)
    assert isinstance(slices, Mapping)
    assert isinstance(work, Mapping)
    assert isinstance(claims, Mapping)
    expected_geometry = {
        "available_cards": 45,
        "hand_width": comb(45, 2),
        "source_occupancies": comb(45, 6),
        "query_occupancies": comb(45, 4),
        "labeled_query_records": comb(45, 4) * QUERY_LABELS,
        "source_rank": SOURCE_RANK,
        "total_feature_width": TOTAL_FEATURE_WIDTH,
        "reach_global_feature_index": REACH_GLOBAL_FEATURE,
    }
    for field, expected in expected_geometry.items():
        if geometry.get(field) != expected:
            raise ValueError(f"CUDA-consumer geometry differs: {field}")
    if slices.get("ordered_global_ranges") != [[0, 128], [128, 176]]:
        raise ValueError("CUDA-consumer global feature partition differs")
    if slices.get("ordered_active_widths") != [128, 48]:
        raise ValueError("CUDA-consumer active widths differ")
    if slices.get("physical_stride_width") != PHYSICAL_STRIDE_WIDTH:
        raise ValueError("CUDA-consumer physical stride differs")
    if int(streaming.get("adjoint_query_occupancy_chunk", -1)) * QUERY_LABELS != int(
        streaming.get("adjoint_query_record_chunk", -2)
    ):
        raise ValueError("CUDA-consumer query occupancy/record units differ")
    if any("per_full_feature_pass" in str(field) for field in work):
        raise ValueError("CUDA-consumer work fields reuse the retired mixed unit")
    if work.get("source_pairing_visits_per_slice") != comb(45, 6) * 90:
        raise ValueError("CUDA-consumer source-pairing work differs")
    if work.get("source_pairing_visits_per_complete_feature_partition") != (
        comb(45, 6) * 90 * 2
    ):
        raise ValueError("CUDA-consumer complete-partition work differs")
    if not all(value is None or value is False for value in claims.values()):
        raise ValueError("CUDA-consumer preregistered claims are open")


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def bounded_execution_call_count() -> int:
    return _BOUNDED_EXECUTION_CALLS


def actual_execution_call_count() -> int:
    return _ACTUAL_EXECUTION_CALLS


def actual_numeric_allocation_call_count() -> int:
    return _ACTUAL_NUMERIC_ALLOCATION_CALLS


def actual_scientific_call_count() -> int:
    return _ACTUAL_SCIENTIFIC_CALLS


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


@dataclass(frozen=True, slots=True)
class PopulationGeometry:
    available_cards: int
    hand_width: int
    source_occupancies: int
    source_recurrence_rows: int
    query_occupancies: int
    labeled_query_records: int
    adjoint_recurrence_rows: int


def population_geometry(available_cards: int) -> PopulationGeometry:
    if isinstance(available_cards, bool) or available_cards not in (10, 25, 45):
        raise ValueError("CUDA-consumer population must be 10, 25, or 45 cards")
    return PopulationGeometry(
        available_cards=available_cards,
        hand_width=comb(45, 2),
        source_occupancies=comb(available_cards, SOURCE_CARDS),
        source_recurrence_rows=sum(
            comb(available_cards, level) for level in range(SOURCE_CARDS + 1)
        ),
        query_occupancies=comb(available_cards, QUERY_CARDS),
        labeled_query_records=comb(available_cards, QUERY_CARDS) * QUERY_LABELS,
        adjoint_recurrence_rows=sum(
            comb(available_cards, level) for level in range(QUERY_CARDS + 1)
        ),
    )


@dataclass(frozen=True, slots=True)
class ConsumerPopulationFixture:
    available_cards: int
    bridge_digest: str
    topology_digest: str
    automaton_digest: str
    unary_weights: np.ndarray
    mode_factors: np.ndarray
    mixture_weights: np.ndarray
    pair_to_hand: np.ndarray
    source_pair_positions: np.ndarray
    query_masks: np.ndarray
    query_hand_indices: np.ndarray
    unary_offsets: np.ndarray
    transitions: tuple[np.ndarray, ...]
    terminal_winner_values: np.ndarray
    sunk_value: float

    @property
    def geometry(self) -> PopulationGeometry:
        return population_geometry(self.available_cards)


def _readonly(values: object, dtype: object) -> np.ndarray:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def _mask(cards: Sequence[int]) -> int:
    return sum(1 << int(card) for card in cards)


def compile_consumer_population_fixture(
    available_cards: int,
    *,
    bridge: LegalRiverQuotientBridge | None = None,
) -> ConsumerPopulationFixture:
    geometry = population_geometry(available_cards)
    compiled = (
        compile_legal_river_quotient_bridge(
            build_preregistered_legal_river_context()
        )
        if bridge is None
        else bridge
    )
    reference = compile_legal_river_quotient_bridge(
        build_preregistered_legal_river_context()
    )
    if compiled.bridge_digest != reference.bridge_digest:
        raise ValueError("CUDA-consumer bridge digest differs from independent replay")
    capacity = build_legal_river_consumer_capacity_report(bridge=compiled)
    if (
        capacity.bridge_sha256 != compiled.bridge_digest
        or capacity.topology_sha256 != compiled.topology_digest
        or not capacity.all_source_gates_pass
    ):
        raise ValueError("CUDA-consumer source-capacity parent did not rebind")

    parent = compiled.fixture
    query_masks = np.empty(geometry.labeled_query_records, dtype=np.uint64)
    query_hands = np.empty((geometry.labeled_query_records, 2), dtype=np.int32)
    pairings = (
        (0, 1, 2, 3),
        (0, 2, 1, 3),
        (0, 3, 1, 2),
        (1, 2, 0, 3),
        (1, 3, 0, 2),
        (2, 3, 0, 1),
    )
    cursor = 0
    for rank in range(geometry.query_occupancies):
        occupancy = colex_unrank(rank, available_cards, QUERY_CARDS)
        mask = _mask(occupancy)
        for pairing in pairings:
            h4 = int(
                parent.pair_to_hand[
                    occupancy[pairing[0]], occupancy[pairing[1]]
                ]
            )
            h5 = int(
                parent.pair_to_hand[
                    occupancy[pairing[2]], occupancy[pairing[3]]
                ]
            )
            if h4 < 0 or h5 < 0:
                raise AssertionError("bounded query compiler produced an invalid hand")
            query_masks[cursor] = mask
            query_hands[cursor] = (h4, h5)
            cursor += 1
    if cursor != geometry.labeled_query_records:
        raise AssertionError("bounded query compiler omitted a label")

    return ConsumerPopulationFixture(
        available_cards=available_cards,
        bridge_digest=compiled.bridge_digest,
        topology_digest=compiled.topology_digest,
        automaton_digest=parent.automaton.digest,
        unary_weights=_readonly(parent.unary_weights, np.float64),
        mode_factors=_readonly(parent.mode_factors, np.float64),
        mixture_weights=_readonly(parent.mixture_weights, np.float64),
        pair_to_hand=_readonly(parent.pair_to_hand, np.int32),
        source_pair_positions=_readonly(parent.source_pair_positions, np.int8),
        query_masks=_readonly(query_masks, np.uint64),
        query_hand_indices=_readonly(query_hands, np.int32),
        unary_offsets=_readonly(parent.unary_offsets, np.int32),
        transitions=tuple(_readonly(value, np.int32) for value in parent.automaton.transitions),
        terminal_winner_values=_readonly(
            parent.automaton.terminal_winner_values, np.float64
        ),
        sunk_value=float(parent.automaton.sunk_value),
    )


def _source_row_exact(
    fixture: ConsumerPopulationFixture,
    occupancy_rank: int,
) -> tuple[Fraction, ...]:
    geometry = fixture.geometry
    if occupancy_rank not in range(geometry.source_occupancies):
        raise ValueError("source sample rank is outside the population")
    cards = colex_unrank(occupancy_rank, fixture.available_cards, SOURCE_CARDS)
    values = [Fraction(0) for _ in range(TOTAL_FEATURE_WIDTH)]
    t0, t1, t2 = fixture.transitions[:3]
    for positions in fixture.source_pair_positions:
        hands = tuple(
            int(
                fixture.pair_to_hand[
                    cards[int(positions[2 * seat])],
                    cards[int(positions[2 * seat + 1])],
                ]
            )
            for seat in range(3)
        )
        state0 = int(t0[0, hands[0]])
        state1 = int(t1[state0, hands[1]])
        state2 = int(t2[state1, hands[2]])
        weight = Fraction(1)
        for seat, hand in enumerate(hands):
            offset = int(fixture.unary_offsets[seat]) + hand
            weight *= Fraction.from_float(float(fixture.unary_weights[0, offset]))
            weight *= Fraction.from_float(float(fixture.mode_factors[0, offset]))
        values[state2] += weight
        values[REACH_GLOBAL_FEATURE] += weight
    return tuple(values)


def _query_weight_exact(
    fixture: ConsumerPopulationFixture,
    record: int,
) -> tuple[Fraction, int, int]:
    if record not in range(fixture.geometry.labeled_query_records):
        raise ValueError("query record is outside the population")
    h4 = int(fixture.query_hand_indices[record, 0])
    h5 = int(fixture.query_hand_indices[record, 1])
    indices = (
        int(fixture.unary_offsets[3]),
        int(fixture.unary_offsets[4]) + h4,
        int(fixture.unary_offsets[5]) + h5,
    )
    weight = Fraction.from_float(float(fixture.mixture_weights[0]))
    for index in indices:
        weight *= Fraction.from_float(float(fixture.unary_weights[0, index]))
        weight *= Fraction.from_float(float(fixture.mode_factors[0, index]))
    return weight, h4, h5


def _query_covector_exact(
    fixture: ConsumerPopulationFixture,
    record: int,
) -> tuple[Fraction, ...]:
    weight, h4, h5 = _query_weight_exact(fixture, record)
    t3, t4 = fixture.transitions[3:5]
    values = []
    for feature in range(TOTAL_FEATURE_WIDTH):
        if feature == REACH_GLOBAL_FEATURE:
            payoff = Fraction.from_float(fixture.sunk_value)
        else:
            state3 = int(t3[feature, 0])
            state4 = int(t4[state3, h4])
            payoff = Fraction.from_float(
                float(fixture.terminal_winner_values[state4, h5])
            )
        values.append(weight * payoff)
    return tuple(values)


@dataclass(frozen=True, slots=True)
class CompleteTenCardReference:
    source: np.ndarray
    compatible: np.ndarray
    fold: np.ndarray
    adjoint: np.ndarray
    scalar_order: tuple[float, ...]


def complete_ten_card_reference(
    fixture: ConsumerPopulationFixture,
) -> CompleteTenCardReference:
    if fixture.available_cards != 10:
        raise ValueError("complete exact reference is restricted to ten cards")
    geometry = fixture.geometry
    source_exact = tuple(
        _source_row_exact(fixture, rank)
        for rank in range(geometry.source_occupancies)
    )
    source = np.asarray(
        [[float(value) for value in row] for row in source_exact],
        dtype=np.float64,
    )
    compatible_exact: list[tuple[Fraction, ...]] = []
    covectors: list[tuple[Fraction, ...]] = []
    fold_exact: list[tuple[Fraction, Fraction]] = []
    universe_mask = (1 << 10) - 1
    for record in range(geometry.labeled_query_records):
        complement = universe_mask ^ int(fixture.query_masks[record])
        cards = tuple(card for card in range(10) if complement & (1 << card))
        source_rank = colex_rank(cards)
        row = source_exact[source_rank]
        covector = _query_covector_exact(fixture, record)
        compatible_exact.append(row)
        covectors.append(covector)
        numerator = sum(
            (row[feature] * covector[feature] for feature in range(TOTAL_FEATURE_WIDTH)),
            Fraction(0),
        )
        query_weight, _, _ = _query_weight_exact(fixture, record)
        reach = query_weight * row[REACH_GLOBAL_FEATURE]
        fold_exact.append((numerator, reach))

    adjoint_exact: list[tuple[Fraction, ...]] = []
    for source_rank in range(geometry.source_occupancies):
        source_cards = colex_unrank(source_rank, 10, SOURCE_CARDS)
        query_mask = universe_mask ^ _mask(source_cards)
        occupancy_cards = tuple(card for card in range(10) if query_mask & (1 << card))
        occupancy_rank = colex_rank(occupancy_cards)
        start = occupancy_rank * QUERY_LABELS
        adjoint_exact.append(
            tuple(
                sum(
                    (covectors[start + label][feature] for label in range(QUERY_LABELS)),
                    Fraction(0),
                )
                for feature in range(TOTAL_FEATURE_WIDTH)
            )
        )

    numerator = sum((row[0] for row in fold_exact), Fraction(0))
    reach = sum((row[1] for row in fold_exact), Fraction(0))
    transpose = sum(
        (
            source_exact[row][feature] * adjoint_exact[row][feature]
            for row in range(geometry.source_occupancies)
            for feature in range(TOTAL_FEATURE_WIDTH)
        ),
        Fraction(0),
    )
    if numerator != transpose or reach <= 0:
        raise AssertionError("ten-card exact transpose or reach identity failed")
    slice0 = sum(
        (
            compatible_exact[row][feature] * covectors[row][feature]
            for row in range(geometry.labeled_query_records)
            for feature in range(0, 128)
        ),
        Fraction(0),
    )
    slice1 = numerator - slice0
    transpose0 = sum(
        (
            source_exact[row][feature] * adjoint_exact[row][feature]
            for row in range(geometry.source_occupancies)
            for feature in range(0, 128)
        ),
        Fraction(0),
    )
    transpose1 = transpose - transpose0
    return CompleteTenCardReference(
        source=np.asarray(source, dtype=np.float64, order="C"),
        compatible=np.asarray(
            [[float(value) for value in row] for row in compatible_exact],
            dtype=np.float64,
            order="C",
        ),
        fold=np.asarray(
            [[float(value) for value in row] for row in fold_exact],
            dtype=np.float64,
            order="C",
        ),
        adjoint=np.asarray(
            [[float(value) for value in row] for row in adjoint_exact],
            dtype=np.float64,
            order="C",
        ),
        scalar_order=(
            float(slice0),
            float(slice1),
            float(numerator),
            float(reach),
            float(numerator / reach),
            float(transpose0),
            float(transpose1),
            float(transpose),
        ),
    )


_CUDA_SOURCE = r"""
__device__ __forceinline__ long long choose_ll(int n, int k) {
    if (k < 0 || k > n) return 0;
    if (k == 0 || k == n) return 1;
    if (k > n - k) k = n - k;
    long long value = 1;
    for (int i = 1; i <= k; ++i) value = value * (n - k + i) / i;
    return value;
}

__device__ __forceinline__ unsigned long long unrank_mask(
    long long rank, int n, int k
) {
    unsigned long long mask = 0ULL;
    int upper = n - 1;
    for (int i = k; i >= 1; --i) {
        int card = upper;
        while (choose_ll(card, i) > rank) --card;
        mask |= 1ULL << card;
        rank -= choose_ll(card, i);
        upper = card - 1;
    }
    return mask;
}

__device__ __forceinline__ long long rank_mask(
    unsigned long long mask, int n
) {
    long long rank = 0;
    int index = 1;
    for (int card = 0; card < n; ++card) {
        if (mask & (1ULL << card)) {
            rank += choose_ll(card, index);
            ++index;
        }
    }
    return rank;
}

__device__ __forceinline__ void unrank_six(
    long long rank, int n, int *cards
) {
    int upper = n - 1;
    for (int i = 6; i >= 1; --i) {
        int card = upper;
        while (choose_ll(card, i) > rank) --card;
        cards[i - 1] = card;
        rank -= choose_ll(card, i);
        upper = card - 1;
    }
}

__device__ __forceinline__ double query_weight(
    long long record, const int *query_hands, const double *unary,
    const double *factors, int unary_total, const int *unary_offsets,
    const double *mixture, int *h4, int *h5
) {
    *h4 = query_hands[record * 2];
    *h5 = query_hands[record * 2 + 1];
    int hero_index = unary_offsets[3];
    int fourth_index = unary_offsets[4] + *h4;
    int fifth_index = unary_offsets[5] + *h5;
    double value = mixture[0];
    value *= unary[hero_index] * factors[hero_index];
    value *= unary[fourth_index] * factors[fourth_index];
    value *= unary[fifth_index] * factors[fifth_index];
    return value;
}

__device__ __forceinline__ void compensated_add(
    double term, double *sum, double *correction
) {
    double next = *sum + term;
    double split = next - *sum;
    double error = (*sum - (next - split)) + (term - split);
    double low = *correction + error;
    double combined = next + low;
    *correction = low - (combined - next);
    *sum = combined;
}

__device__ __forceinline__ void compensated_product(
    double left, double right, double *sum, double *correction
) {
    double product = left * right;
    double error = fma(left, right, -product);
    compensated_add(product, sum, correction);
    compensated_add(error, sum, correction);
}

extern "C" __global__ void source_coefficients_slice(
    double *table, long long source_level_offset,
    long long occupancy_rank_start, long long occupancy_records,
    int global_feature_start, int active_width, int physical_stride,
    int n, int hand_width, int pair_stride, int source_rank,
    const signed char *pairings, const int *pair_to_hand,
    const double *unary, const double *factors, int unary_total,
    const int *unary_offsets, const int *transition0,
    const int *transition1, const int *transition2
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= occupancy_records) return;
    long long rank = occupancy_rank_start + local;
    double *output = table + (source_level_offset + rank) * physical_stride;
    for (int feature = 0; feature < active_width; ++feature)
        output[feature] = 0.0;
    int cards[6];
    unrank_six(rank, n, cards);
    for (int pairing = 0; pairing < 90; ++pairing) {
        const signed char *positions = pairings + pairing * 6;
        int h0 = pair_to_hand[cards[(int)positions[0]] * pair_stride
                              + cards[(int)positions[1]]];
        int h1 = pair_to_hand[cards[(int)positions[2]] * pair_stride
                              + cards[(int)positions[3]]];
        int h2 = pair_to_hand[cards[(int)positions[4]] * pair_stride
                              + cards[(int)positions[5]]];
        int state0 = transition0[h0];
        int state1 = transition1[state0 * hand_width + h1];
        int state2 = transition2[state1 * hand_width + h2];
        double weight = 1.0;
        int hands[3] = {h0, h1, h2};
        for (int seat = 0; seat < 3; ++seat) {
            int index = unary_offsets[seat] + hands[seat];
            weight *= unary[index] * factors[index];
        }
        int local_state = state2 - global_feature_start;
        if (local_state >= 0 && local_state < active_width)
            output[local_state] += weight;
        int local_reach = source_rank - global_feature_start;
        if (local_reach >= 0 && local_reach < active_width)
            output[local_reach] += weight;
    }
}

extern "C" __global__ void zeta_level_slice(
    double *table, long long current_offset, long long next_offset,
    long long rows, int n, int level, int source_cards,
    int active_width, int physical_stride
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = rows * active_width;
    if (linear >= total) return;
    long long row = linear / active_width;
    int feature = (int)(linear - row * active_width);
    unsigned long long mask = unrank_mask(row, n, level);
    double value = 0.0;
    double correction = 0.0;
    for (int card = 0; card < n; ++card) {
        unsigned long long bit = 1ULL << card;
        if (!(mask & bit)) {
            long long next_rank = rank_mask(mask | bit, n);
            compensated_add(
                table[(next_offset + next_rank) * physical_stride + feature],
                &value, &correction
            );
        }
    }
    table[(current_offset + row) * physical_stride + feature]
        = (value + correction) / (double)(source_cards - level);
}

extern "C" __global__ void signed_targets_chunk(
    const double *table, const long long *offsets, int source_cards,
    const unsigned long long *target_masks, int implicit_targets,
    int target_cards, long long target_rank_or_record_start,
    long long target_records, int n, int active_width, int physical_stride,
    double *output
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = target_records * active_width;
    if (linear >= total) return;
    long long local_row = linear / active_width;
    int feature = (int)(linear - local_row * active_width);
    long long global_row = target_rank_or_record_start + local_row;
    unsigned long long mask = implicit_targets
        ? unrank_mask(global_row, n, target_cards)
        : target_masks[global_row];
    unsigned long long subset = mask;
    double value = 0.0;
    double correction = 0.0;
    while (true) {
        int cards = __popcll(subset);
        if (cards <= source_cards) {
            long long rank = rank_mask(subset, n);
            double term = table[(offsets[cards] + rank) * physical_stride + feature];
            compensated_add((cards & 1) ? -term : term, &value, &correction);
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    output[local_row * physical_stride + feature] = value + correction;
}

extern "C" __global__ void fold_query_slice(
    const double *compatible, long long query_record_start,
    long long records, int global_feature_start, int active_width,
    int physical_stride, int source_rank, int reach_owner,
    const int *query_hands, const double *unary, const double *factors,
    int unary_total, const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *numerator, double *reach
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= records) return;
    long long record = query_record_start + local;
    int h4, h5;
    double weight = query_weight(
        record, query_hands, unary, factors, unary_total, unary_offsets,
        mixture, &h4, &h5
    );
    double partial = 0.0;
    double partial_correction = 0.0;
    double reach_value = 0.0;
    for (int feature = 0; feature < active_width; ++feature) {
        int global_feature = global_feature_start + feature;
        double coefficient = compatible[local * physical_stride + feature];
        if (global_feature == source_rank) {
            compensated_product(
                coefficient, sunk, &partial, &partial_correction
            );
            if (reach_owner) reach_value = weight * coefficient;
        } else if (global_feature < source_rank) {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            compensated_product(
                coefficient, terminal[state4 * hand_width + h5],
                &partial, &partial_correction
            );
        }
    }
    numerator[local] = weight * (partial + partial_correction);
    reach[local] = reach_value;
}

extern "C" __global__ void build_numerator_covector_chunk(
    double *output, long long query_record_start, long long records,
    int global_feature_start, int active_width, int physical_stride,
    int source_rank, const int *query_hands, const double *unary,
    const double *factors, int unary_total, const int *unary_offsets,
    const double *mixture, const int *transition3, const int *transition4,
    const double *terminal, int hand_width, double sunk
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = records * active_width;
    if (linear >= total) return;
    long long local = linear / active_width;
    int feature = (int)(linear - local * active_width);
    long long record = query_record_start + local;
    int h4, h5;
    double weight = query_weight(
        record, query_hands, unary, factors, unary_total, unary_offsets,
        mixture, &h4, &h5
    );
    int global_feature = global_feature_start + feature;
    double payoff;
    if (global_feature == source_rank) {
        payoff = sunk;
    } else {
        int state3 = transition3[global_feature];
        int state4 = transition4[state3 * hand_width + h4];
        payoff = terminal[state4 * hand_width + h5];
    }
    output[local * physical_stride + feature] = weight * payoff;
}

extern "C" __global__ void aggregate_query_labels_into_level(
    const double *records, long long occupancy_rank_start,
    long long occupancies, int labels, int active_width, int physical_stride,
    long long query_level_offset, int skip_last_label, double *table
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = occupancies * active_width;
    if (linear >= total) return;
    long long local_occupancy = linear / active_width;
    int feature = (int)(linear - local_occupancy * active_width);
    int stop = labels - (skip_last_label ? 1 : 0);
    double value = 0.0;
    double correction = 0.0;
    for (int label = 0; label < stop; ++label)
        compensated_add(
            records[(local_occupancy * labels + label) * physical_stride + feature],
            &value, &correction
        );
    long long global_occupancy = occupancy_rank_start + local_occupancy;
    table[(query_level_offset + global_occupancy) * physical_stride + feature]
        = value + correction;
}

extern "C" __global__ void source_adjoint_contract_chunk(
    double *unique, long long source_rank_start, long long source_records,
    int global_feature_start, int active_width, int physical_stride,
    int n, int hand_width, int pair_stride, int source_rank,
    const signed char *pairings, const int *pair_to_hand,
    const double *unary, const double *factors, int unary_total,
    const int *unary_offsets, const int *transition0,
    const int *transition1, const int *transition2
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= source_records) return;
    long long rank = source_rank_start + local;
    int cards[6];
    unrank_six(rank, n, cards);
    const double *adjoint = unique + local * physical_stride;
    double coefficients[128];
    for (int feature = 0; feature < active_width; ++feature)
        coefficients[feature] = 0.0;
    for (int pairing = 0; pairing < 90; ++pairing) {
        const signed char *positions = pairings + pairing * 6;
        int h0 = pair_to_hand[cards[(int)positions[0]] * pair_stride
                              + cards[(int)positions[1]]];
        int h1 = pair_to_hand[cards[(int)positions[2]] * pair_stride
                              + cards[(int)positions[3]]];
        int h2 = pair_to_hand[cards[(int)positions[4]] * pair_stride
                              + cards[(int)positions[5]]];
        int state0 = transition0[h0];
        int state1 = transition1[state0 * hand_width + h1];
        int state2 = transition2[state1 * hand_width + h2];
        double weight = 1.0;
        int hands[3] = {h0, h1, h2};
        for (int seat = 0; seat < 3; ++seat) {
            int index = unary_offsets[seat] + hands[seat];
            weight *= unary[index] * factors[index];
        }
        int local_state = state2 - global_feature_start;
        if (local_state >= 0 && local_state < active_width)
            coefficients[local_state] += weight;
        int local_reach = source_rank - global_feature_start;
        if (local_reach >= 0 && local_reach < active_width)
            coefficients[local_reach] += weight;
    }
    double value = 0.0;
    double correction = 0.0;
    for (int feature = 0; feature < active_width; ++feature)
        compensated_product(
            coefficients[feature], adjoint[feature], &value, &correction
        );
    unique[local * physical_stride] = value + correction;
}

extern "C" __global__ void reduce_pair_in_place(
    double *first, double *second, long long input_count,
    long long global_start, double *carry
) {
    if (blockIdx.x || threadIdx.x) return;
    for (long long local = 0; local < input_count; ++local) {
        unsigned long long index = (unsigned long long)(global_start + local);
        double first_value = first[local];
        double second_value = second[local];
        int level = 0;
        while (index & (1ULL << level)) {
            first_value = carry[level] + first_value;
            second_value = carry[64 + level] + second_value;
            ++level;
        }
        carry[level] = first_value;
        carry[64 + level] = second_value;
    }
    long long remaining = input_count;
    while (remaining > 1) {
        long long outputs = (remaining + 1) / 2;
        for (long long output = 0; output < outputs; ++output) {
            long long left = output * 2;
            long long right = left + 1;
            double first_value = first[left];
            double second_value = second[left];
            if (right < remaining) {
                first_value += first[right];
                second_value += second[right];
            }
            first[output] = first_value;
            second[output] = second_value;
        }
        remaining = outputs;
    }
}

extern "C" __global__ void reduce_scalar_in_place(
    double *values, long long input_count, int physical_stride,
    long long global_start, double *carry
) {
    if (blockIdx.x || threadIdx.x) return;
    for (long long local = 0; local < input_count; ++local) {
        unsigned long long index = (unsigned long long)(global_start + local);
        double value = values[local * physical_stride];
        int level = 0;
        while (index & (1ULL << level)) {
            value = carry[level] + value;
            ++level;
        }
        carry[level] = value;
    }
    long long remaining = input_count;
    while (remaining > 1) {
        long long outputs = (remaining + 1) / 2;
        for (long long output = 0; output < outputs; ++output) {
            long long left = output * 2;
            long long right = left + 1;
            double value = values[left * physical_stride];
            if (right < remaining)
                value += values[right * physical_stride];
            values[output * physical_stride] = value;
        }
        remaining = outputs;
    }
}

extern "C" __global__ void accumulate_results(
    double *results, const double *carry, const double *unused, int mode,
    unsigned long long processed_count, int finalize
) {
    if (blockIdx.x || threadIdx.x) return;
    if (!finalize) return;
    double first_value = 0.0;
    double second_value = 0.0;
    int have_value = 0;
    for (int level = 63; level >= 0; --level) {
        if (processed_count & (1ULL << level)) {
            if (!have_value) {
                first_value = carry[level];
                if (mode == 0) second_value = carry[64 + level];
                have_value = 1;
            } else {
                first_value += carry[level];
                if (mode == 0) second_value += carry[64 + level];
            }
        }
    }
    results[0] += first_value;
    if (mode == 0) results[1] += second_value;
}

extern "C" __global__ void direct_selected_queries(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *query_masks, int query_count,
    const int *global_features, int feature_count,
    int global_feature_start, int active_width, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= query_count * feature_count) return;
    int query = index / feature_count;
    int feature_index = index - query * feature_count;
    int global_feature = global_features[feature_index];
    int local_feature = global_feature - global_feature_start;
    if (local_feature < 0 || local_feature >= active_width) return;
    double value = 0.0;
    double correction = 0.0;
    unsigned long long query_mask = query_masks[query];
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_mask(row, n, 6);
        if (!(source_mask & query_mask))
            compensated_add(
                source[(source_level_offset + row) * physical_stride
                       + local_feature],
                &value, &correction
            );
    }
    output[index] = value + correction;
}

extern "C" __global__ void direct_selected_fold(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *selected_query_masks,
    const long long *selected_query_records, int query_count,
    int global_feature_start, int active_width, int source_rank,
    const int *query_hands, const double *unary, const double *factors,
    int unary_total, const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *numerator, double *reach
) {
    int query = blockDim.x * blockIdx.x + threadIdx.x;
    if (query >= query_count) return;
    long long record = selected_query_records[query];
    int h4, h5;
    double weight = query_weight(
        record, query_hands, unary, factors, unary_total, unary_offsets,
        mixture, &h4, &h5
    );
    unsigned long long query_mask = selected_query_masks[query];
    double partial = 0.0;
    double partial_correction = 0.0;
    double reach_value = 0.0;
    double reach_correction = 0.0;
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_mask(row, n, 6);
        if (source_mask & query_mask) continue;
        const double *coefficients = source
            + (source_level_offset + row) * physical_stride;
        for (int feature = 0; feature < active_width; ++feature) {
            int global_feature = global_feature_start + feature;
            double coefficient = coefficients[feature];
            if (global_feature == source_rank) {
                compensated_product(
                    coefficient, sunk, &partial, &partial_correction
                );
                compensated_add(
                    coefficient, &reach_value, &reach_correction
                );
            } else {
                int state3 = transition3[global_feature];
                int state4 = transition4[state3 * hand_width + h4];
                compensated_product(
                    coefficient, terminal[state4 * hand_width + h5],
                    &partial, &partial_correction
                );
            }
        }
    }
    numerator[query] = weight * (partial + partial_correction);
    reach[query] = weight * (reach_value + reach_correction);
}

extern "C" __global__ void direct_selected_adjoint(
    const long long *source_ranks, int source_count,
    const int *global_features, int feature_count,
    int global_feature_start, int active_width, int n,
    const unsigned long long *query_masks, long long query_records,
    int source_rank, const int *query_hands, const double *unary,
    const double *factors, int unary_total, const int *unary_offsets,
    const double *mixture, const int *transition3, const int *transition4,
    const double *terminal, int hand_width, double sunk, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= source_count * feature_count) return;
    int source_index = index / feature_count;
    int feature_index = index - source_index * feature_count;
    int global_feature = global_features[feature_index];
    int local_feature = global_feature - global_feature_start;
    if (local_feature < 0 || local_feature >= active_width) return;
    unsigned long long source_mask = unrank_mask(source_ranks[source_index], n, 6);
    double value = 0.0;
    double correction = 0.0;
    for (long long record = 0; record < query_records; ++record) {
        if (source_mask & query_masks[record]) continue;
        int h4, h5;
        double weight = query_weight(
            record, query_hands, unary, factors, unary_total, unary_offsets,
            mixture, &h4, &h5
        );
        double payoff;
        if (global_feature == source_rank) {
            payoff = sunk;
        } else {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            payoff = terminal[state4 * hand_width + h5];
        }
        compensated_product(weight, payoff, &value, &correction);
    }
    output[index] = value + correction;
}
"""


_KERNEL_NAMES = (
    "source_coefficients_slice",
    "zeta_level_slice",
    "signed_targets_chunk",
    "fold_query_slice",
    "build_numerator_covector_chunk",
    "aggregate_query_labels_into_level",
    "source_adjoint_contract_chunk",
    "reduce_pair_in_place",
    "reduce_scalar_in_place",
    "accumulate_results",
    "direct_selected_queries",
    "direct_selected_fold",
    "direct_selected_adjoint",
)
_KERNEL_CACHE: dict[int, Mapping[str, object]] = {}


def _kernels(cp: Any) -> Mapping[str, object]:
    device = int(cp.cuda.Device().id)
    cached = _KERNEL_CACHE.get(device)
    if cached is not None:
        return cached
    module = cp.RawModule(
        code=_CUDA_SOURCE,
        options=("--std=c++14",),
        name_expressions=_KERNEL_NAMES,
    )
    result = MappingProxyType(
        {name: module.get_function(name) for name in _KERNEL_NAMES}
    )
    _KERNEL_CACHE[device] = result
    return result


def _launch(kernel: Any, total: int, arguments: tuple[object, ...]) -> None:
    if total <= 0:
        raise ValueError("CUDA-consumer launch total must be positive")
    threads = 128
    blocks = (int(total) + threads - 1) // threads
    kernel((blocks,), (threads,), arguments)


def _cuda_timed(cp: Any, operation: Callable[[], None]) -> float:
    start = cp.cuda.Event()
    stop = cp.cuda.Event()
    start.record()
    operation()
    stop.record()
    stop.synchronize()
    return float(cp.cuda.get_elapsed_time(start, stop))


def _maximum_errors(
    actual: np.ndarray,
    expected: np.ndarray,
) -> tuple[float, float]:
    if actual.shape != expected.shape:
        raise ValueError("CUDA-consumer error operands differ in shape")
    absolute = np.abs(actual - expected)
    maximum_absolute = float(np.max(absolute, initial=0.0))
    relative = absolute / np.maximum(1.0, np.abs(expected))
    return maximum_absolute, float(np.max(relative, initial=0.0))


def _float64_digest(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values, dtype=np.float64)
    return sha256(memoryview(contiguous).cast("B")).hexdigest()


_POISON = np.float64(9.876543210123456e197)
_BOUNDARY_FEATURES = (0, 1, 63, 126, 127, 128, 129, 174, 175)


@dataclass(frozen=True, slots=True)
class CudaRuntimeIdentity:
    device_name: str
    compute_capability: str
    device_total_bytes: int
    cuda_driver_version: int
    cuda_runtime_version: int
    cupy_version: str


@dataclass(frozen=True, slots=True)
class PopulationExecution:
    available_cards: int
    feature_order: tuple[tuple[int, int], ...]
    forward_query_chunk: int
    adjoint_query_occupancy_chunk: int
    adjoint_source_chunk: int
    scalar_results: tuple[float, ...]
    streamed_reference_scalars: tuple[float, float, float] | None
    streamed_pairwise_scalars: tuple[float, float, float, float] | None
    source_samples: np.ndarray
    query_samples: np.ndarray
    fold_samples: np.ndarray
    adjoint_samples: np.ndarray
    direct_query_samples: np.ndarray
    direct_fold_samples: np.ndarray
    direct_adjoint_samples: np.ndarray
    source_slice_digests: tuple[str, str]
    compatible_slice_digests: tuple[str, str]
    fold_slice_digests: tuple[str, str]
    adjoint_slice_digests: tuple[str, str]
    full_source: np.ndarray | None
    full_compatible: np.ndarray | None
    full_fold: np.ndarray | None
    full_adjoint: np.ndarray | None
    repeat_byte_identity: bool
    inactive_poison_pass: bool
    nonzero_query_offset_observed: bool
    nonzero_source_offset_observed: bool
    forward_released_before_adjoint: bool
    accumulator_lifecycle_pass: bool
    missing_label_changed_result: bool | None
    maximum_pool_total_bytes: int
    released_pool_used_bytes: int
    released_pool_total_bytes: int
    released_pinned_blocks: int
    wall_ms: float


@dataclass(frozen=True, slots=True)
class BoundedPopulationEvidence:
    available_cards: int
    wall_ms: float
    scalar_results: tuple[float, ...]
    maximum_errors: Mapping[str, float]
    reporting_digests: Mapping[str, str]
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return all(self.gates.values())


@dataclass(frozen=True, slots=True)
class BoundedCudaConsumerReport:
    config_sha256: str
    bridge_sha256: str
    topology_sha256: str
    runtime: CudaRuntimeIdentity
    ten_card: BoundedPopulationEvidence
    twenty_five_card: BoundedPopulationEvidence
    actual_execution_calls_before: int
    actual_execution_calls_after: int
    actual_numeric_allocation_calls_before: int
    actual_numeric_allocation_calls_after: int
    actual_scientific_calls_before: int
    actual_scientific_calls_after: int
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return (
            self.ten_card.all_gates_pass
            and self.twenty_five_card.all_gates_pass
            and all(self.gates.values())
        )


@dataclass(slots=True)
class _DeviceResident:
    pairings: Any
    pair_to_hand: Any
    unary: Any
    factors: Any
    mixture: Any
    unary_offsets: Any
    query_masks: Any
    query_hands: Any
    transitions: tuple[Any, ...]
    terminal: Any
    source_offsets: Any
    adjoint_offsets: Any
    results: Any


def _runtime_identity(cp: Any) -> CudaRuntimeIdentity:
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return CudaRuntimeIdentity(
        device_name=str(name),
        compute_capability=f"{int(properties['major'])}{int(properties['minor'])}",
        device_total_bytes=int(properties["totalGlobalMem"]),
        cuda_driver_version=int(cp.cuda.runtime.driverGetVersion()),
        cuda_runtime_version=int(cp.cuda.runtime.runtimeGetVersion()),
        cupy_version=str(cp.__version__),
    )


def _verify_runtime(
    runtime: CudaRuntimeIdentity,
    config: Mapping[str, object],
) -> None:
    expected = config.get("required_runtime")
    if not isinstance(expected, Mapping):
        raise ValueError("CUDA-consumer runtime contract is malformed")
    for field in (
        "device_name",
        "compute_capability",
        "device_total_bytes",
        "cuda_driver_version",
        "cuda_runtime_version",
        "cupy_version",
    ):
        if getattr(runtime, field) != expected.get(field):
            raise RuntimeError(f"CUDA-consumer runtime differs: {field}")


def _allocate_resident(
    cp: Any,
    fixture: ConsumerPopulationFixture,
) -> _DeviceResident:
    return _DeviceResident(
        pairings=cp.asarray(fixture.source_pair_positions, dtype=cp.int8),
        pair_to_hand=cp.asarray(fixture.pair_to_hand, dtype=cp.int32),
        unary=cp.asarray(fixture.unary_weights.reshape(-1), dtype=cp.float64),
        factors=cp.asarray(fixture.mode_factors.reshape(-1), dtype=cp.float64),
        mixture=cp.asarray(fixture.mixture_weights, dtype=cp.float64),
        unary_offsets=cp.asarray(fixture.unary_offsets, dtype=cp.int32),
        query_masks=cp.asarray(fixture.query_masks, dtype=cp.uint64),
        query_hands=cp.asarray(fixture.query_hand_indices, dtype=cp.int32),
        transitions=tuple(cp.asarray(value, dtype=cp.int32) for value in fixture.transitions),
        terminal=cp.asarray(fixture.terminal_winner_values, dtype=cp.float64),
        source_offsets=cp.asarray(
            cardinality_offsets(fixture.available_cards, SOURCE_CARDS),
            dtype=cp.int64,
        ),
        adjoint_offsets=cp.asarray(
            cardinality_offsets(fixture.available_cards, QUERY_CARDS),
            dtype=cp.int64,
        ),
        results=cp.zeros(2, dtype=cp.float64),
    )


def _fill_recurrence_slice(
    cp: Any,
    kernels: Mapping[str, object],
    table: Any,
    *,
    available_cards: int,
    source_cards: int,
    active_width: int,
) -> None:
    offsets = cardinality_offsets(available_cards, source_cards)
    for level in range(source_cards - 1, -1, -1):
        rows = comb(available_cards, level)
        _launch(
            kernels["zeta_level_slice"],
            rows * active_width,
            (
                table,
                np.int64(offsets[level]),
                np.int64(offsets[level + 1]),
                np.int64(rows),
                np.int32(available_cards),
                np.int32(level),
                np.int32(source_cards),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
            ),
        )


def _reduce_pair(
    kernels: Mapping[str, object],
    first: Any,
    second: Any,
    count: int,
    global_start: int,
    carry: Any,
) -> None:
    _launch(
        kernels["reduce_pair_in_place"],
        1,
        (first, second, np.int64(count), np.int64(global_start), carry),
    )


def _reduce_scalar(
    kernels: Mapping[str, object],
    values: Any,
    count: int,
    global_start: int,
    carry: Any,
) -> None:
    _launch(
        kernels["reduce_scalar_in_place"],
        1,
        (
            values,
            np.int64(count),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            np.int64(global_start),
            carry,
        ),
    )


def _sample_rows(
    config: Mapping[str, object], available_cards: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if available_cards == 10:
        source = (0, 1, 17, 63, 127, 208, 209)
        query = (0, 1, 17, 127, 511, 1258, 1259)
        return source, query
    samples = config.get("samples")
    if not isinstance(samples, Mapping):
        raise ValueError("CUDA-consumer sample contract is malformed")
    return (
        tuple(int(value) for value in samples["bounded_25_source_occupancy_ranks"]),
        tuple(int(value) for value in samples["bounded_25_query_record_ranks"]),
    )


def _copy_selected_source(
    table: Any,
    level_offset: int,
    source_ranks: Sequence[int],
    global_start: int,
    active_width: int,
) -> np.ndarray:
    result = np.empty((len(source_ranks), active_width), dtype=np.float64)
    for index, rank in enumerate(source_ranks):
        result[index] = table[
            level_offset + int(rank), :active_width
        ].get()
    return result


def _direct_forward_samples(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    source_table: Any,
    selected_records: Sequence[int],
    global_start: int,
    active_width: int,
) -> tuple[np.ndarray, np.ndarray]:
    records = np.asarray(selected_records, dtype=np.int64)
    masks = np.asarray(
        [fixture.query_masks[int(record)] for record in records],
        dtype=np.uint64,
    )
    features = np.arange(global_start, global_start + active_width, dtype=np.int32)
    device_masks = cp.asarray(masks, dtype=cp.uint64)
    device_records = cp.asarray(records, dtype=cp.int64)
    device_features = cp.asarray(features, dtype=cp.int32)
    query_output = cp.zeros((len(records), active_width), dtype=cp.float64)
    numerator_output = cp.empty(len(records), dtype=cp.float64)
    reach_output = cp.empty(len(records), dtype=cp.float64)
    source_offset = cardinality_offsets(fixture.available_cards, SOURCE_CARDS)[SOURCE_CARDS]
    _launch(
        kernels["direct_selected_queries"],
        len(records) * active_width,
        (
            source_table,
            np.int64(source_offset),
            np.int64(fixture.geometry.source_occupancies),
            np.int32(fixture.available_cards),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            device_masks,
            np.int32(len(records)),
            device_features,
            np.int32(active_width),
            np.int32(global_start),
            np.int32(active_width),
            query_output,
        ),
    )
    _launch(
        kernels["direct_selected_fold"],
        len(records),
        (
            source_table,
            np.int64(source_offset),
            np.int64(fixture.geometry.source_occupancies),
            np.int32(fixture.available_cards),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            device_masks,
            device_records,
            np.int32(len(records)),
            np.int32(global_start),
            np.int32(active_width),
            np.int32(SOURCE_RANK),
            resident.query_hands,
            resident.unary,
            resident.factors,
            np.int32(fixture.unary_weights.size),
            resident.unary_offsets,
            resident.mixture,
            resident.transitions[3],
            resident.transitions[4],
            resident.terminal,
            np.int32(fixture.geometry.hand_width),
            np.float64(fixture.sunk_value),
            numerator_output,
            reach_output,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    return query_output.get(), np.column_stack(
        (numerator_output.get(), reach_output.get())
    )


def _forward_once(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    *,
    global_start: int,
    active_width: int,
    query_chunk: int,
    table: Any,
    compatible: Any,
    numerator: Any,
    reach: Any,
    source_ranks: Sequence[int],
    query_records: Sequence[int],
    collect_full: bool,
    collect_direct: bool,
) -> dict[str, object]:
    geometry = fixture.geometry
    source_offset = cardinality_offsets(fixture.available_cards, SOURCE_CARDS)[SOURCE_CARDS]
    table.fill(_POISON)
    _launch(
        kernels["source_coefficients_slice"],
        geometry.source_occupancies,
        (
            table,
            np.int64(source_offset),
            np.int64(0),
            np.int64(geometry.source_occupancies),
            np.int32(global_start),
            np.int32(active_width),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            np.int32(fixture.available_cards),
            np.int32(geometry.hand_width),
            np.int32(fixture.pair_to_hand.shape[1]),
            np.int32(SOURCE_RANK),
            resident.pairings,
            resident.pair_to_hand,
            resident.unary,
            resident.factors,
            np.int32(fixture.unary_weights.size),
            resident.unary_offsets,
            resident.transitions[0],
            resident.transitions[1],
            resident.transitions[2],
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    source_samples = _copy_selected_source(
        table, source_offset, source_ranks, global_start, active_width
    )
    full_source = (
        table[
            source_offset : source_offset + geometry.source_occupancies,
            :active_width,
        ].get()
        if collect_full
        else None
    )
    inactive_pass = True
    if active_width < PHYSICAL_STRIDE_WIDTH:
        for rank in (0, geometry.source_occupancies - 1):
            inactive = table[
                source_offset + rank, active_width:PHYSICAL_STRIDE_WIDTH
            ].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))
    direct_query = np.empty((0, active_width), dtype=np.float64)
    direct_fold = np.empty((0, 2), dtype=np.float64)
    if collect_direct:
        direct_query, direct_fold = _direct_forward_samples(
            cp,
            kernels,
            resident,
            fixture,
            table,
            query_records,
            global_start,
            active_width,
        )
    _fill_recurrence_slice(
        cp,
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        active_width=active_width,
    )
    carry_offset = cardinality_offsets(fixture.available_cards, SOURCE_CARDS)[5]
    carry = table[carry_offset:].reshape(-1)
    carry[:128].fill(np.float64(0.0))
    compatible_digest = sha256()
    fold_digest = sha256()
    selected_lookup = {int(record): index for index, record in enumerate(query_records)}
    query_samples = np.full((len(query_records), active_width), np.nan, dtype=np.float64)
    fold_samples = np.full((len(query_records), 2), np.nan, dtype=np.float64)
    full_compatible = (
        np.empty((geometry.labeled_query_records, active_width), dtype=np.float64)
        if collect_full
        else None
    )
    full_fold = (
        np.empty((geometry.labeled_query_records, 2), dtype=np.float64)
        if collect_full
        else None
    )
    scalar_rows = (
        np.empty((geometry.labeled_query_records, 2), dtype=np.float64)
        if collect_direct
        else None
    )
    nonzero_offset = False
    for start in range(0, geometry.labeled_query_records, query_chunk):
        records = min(query_chunk, geometry.labeled_query_records - start)
        nonzero_offset = nonzero_offset or start > 0
        compatible.fill(_POISON)
        _launch(
            kernels["signed_targets_chunk"],
            records * active_width,
            (
                table,
                resident.source_offsets,
                np.int32(SOURCE_CARDS),
                resident.query_masks,
                np.int32(0),
                np.int32(QUERY_CARDS),
                np.int64(start),
                np.int64(records),
                np.int32(fixture.available_cards),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                compatible,
            ),
        )
        _launch(
            kernels["fold_query_slice"],
            records,
            (
                compatible,
                np.int64(start),
                np.int64(records),
                np.int32(global_start),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(SOURCE_RANK),
                np.int32(int(global_start <= REACH_GLOBAL_FEATURE < global_start + active_width)),
                resident.query_hands,
                resident.unary,
                resident.factors,
                np.int32(fixture.unary_weights.size),
                resident.unary_offsets,
                resident.mixture,
                resident.transitions[3],
                resident.transitions[4],
                resident.terminal,
                np.int32(geometry.hand_width),
                np.float64(fixture.sunk_value),
                numerator,
                reach,
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        compatible_host = compatible[:records, :active_width].get()
        numerator_host = numerator[:records].get()
        reach_host = reach[:records].get()
        compatible_digest.update(memoryview(np.ascontiguousarray(compatible_host)).cast("B"))
        fold_host = np.column_stack((numerator_host, reach_host))
        fold_digest.update(memoryview(np.ascontiguousarray(fold_host)).cast("B"))
        if full_compatible is not None and full_fold is not None:
            full_compatible[start : start + records] = compatible_host
            full_fold[start : start + records] = fold_host
        if scalar_rows is not None:
            scalar_rows[start : start + records] = fold_host
        for record, output_index in selected_lookup.items():
            if start <= record < start + records:
                local = record - start
                query_samples[output_index] = compatible_host[local]
                fold_samples[output_index] = fold_host[local]
        if active_width < PHYSICAL_STRIDE_WIDTH:
            inactive = compatible[0, active_width:PHYSICAL_STRIDE_WIDTH].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))
        _reduce_pair(kernels, numerator, reach, records, start, carry)
        _launch(
            kernels["accumulate_results"],
            1,
            (
                resident.results,
                carry,
                reach,
                np.int32(0),
                np.uint64(start + records),
                np.int32(int(start + records == geometry.labeled_query_records)),
            ),
        )
    cp.cuda.get_current_stream().synchronize()
    if not np.all(np.isfinite(query_samples)) or not np.all(np.isfinite(fold_samples)):
        raise AssertionError("CUDA-consumer forward samples were not captured")
    return {
        "source_samples": source_samples,
        "query_samples": query_samples,
        "fold_samples": fold_samples,
        "direct_query": direct_query,
        "direct_fold": direct_fold,
        "source_digest": _float64_digest(source_samples),
        "compatible_digest": compatible_digest.hexdigest(),
        "fold_digest": fold_digest.hexdigest(),
        "full_source": full_source,
        "full_compatible": full_compatible,
        "full_fold": full_fold,
        "scalar_rows": scalar_rows,
        "inactive_pass": inactive_pass,
        "nonzero_offset": nonzero_offset,
    }


def _direct_adjoint_samples(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    source_ranks: Sequence[int],
    global_start: int,
    active_width: int,
) -> np.ndarray:
    ranks = cp.asarray(np.asarray(source_ranks, dtype=np.int64), dtype=cp.int64)
    features = cp.asarray(
        np.arange(global_start, global_start + active_width, dtype=np.int32),
        dtype=cp.int32,
    )
    output = cp.zeros((len(source_ranks), active_width), dtype=cp.float64)
    _launch(
        kernels["direct_selected_adjoint"],
        len(source_ranks) * active_width,
        (
            ranks,
            np.int32(len(source_ranks)),
            features,
            np.int32(active_width),
            np.int32(global_start),
            np.int32(active_width),
            np.int32(fixture.available_cards),
            resident.query_masks,
            np.int64(fixture.geometry.labeled_query_records),
            np.int32(SOURCE_RANK),
            resident.query_hands,
            resident.unary,
            resident.factors,
            np.int32(fixture.unary_weights.size),
            resident.unary_offsets,
            resident.mixture,
            resident.transitions[3],
            resident.transitions[4],
            resident.terminal,
            np.int32(fixture.geometry.hand_width),
            np.float64(fixture.sunk_value),
            output,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    return output.get()


def _adjoint_once(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    *,
    global_start: int,
    active_width: int,
    query_occupancy_chunk: int,
    source_chunk: int,
    table: Any,
    covector: Any,
    unique: Any,
    source_ranks: Sequence[int],
    collect_full: bool,
    collect_direct: bool,
    skip_last_label: bool = False,
) -> dict[str, object]:
    geometry = fixture.geometry
    query_offset = cardinality_offsets(fixture.available_cards, QUERY_CARDS)[QUERY_CARDS]
    table.fill(_POISON)
    nonzero_query_offset = False
    for occupancy_start in range(0, geometry.query_occupancies, query_occupancy_chunk):
        occupancies = min(
            query_occupancy_chunk,
            geometry.query_occupancies - occupancy_start,
        )
        records = occupancies * QUERY_LABELS
        record_start = occupancy_start * QUERY_LABELS
        nonzero_query_offset = nonzero_query_offset or occupancy_start > 0
        covector.fill(_POISON)
        _launch(
            kernels["build_numerator_covector_chunk"],
            records * active_width,
            (
                covector,
                np.int64(record_start),
                np.int64(records),
                np.int32(global_start),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(SOURCE_RANK),
                resident.query_hands,
                resident.unary,
                resident.factors,
                np.int32(fixture.unary_weights.size),
                resident.unary_offsets,
                resident.mixture,
                resident.transitions[3],
                resident.transitions[4],
                resident.terminal,
                np.int32(geometry.hand_width),
                np.float64(fixture.sunk_value),
            ),
        )
        _launch(
            kernels["aggregate_query_labels_into_level"],
            occupancies * active_width,
            (
                covector,
                np.int64(occupancy_start),
                np.int64(occupancies),
                np.int32(QUERY_LABELS),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int64(query_offset),
                np.int32(int(skip_last_label)),
                table,
            ),
        )
    _fill_recurrence_slice(
        cp,
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=QUERY_CARDS,
        active_width=active_width,
    )
    carry = covector.reshape(-1)
    carry[:128].fill(np.float64(0.0))
    direct_adjoint = np.empty((0, active_width), dtype=np.float64)
    if collect_direct:
        direct_adjoint = _direct_adjoint_samples(
            cp,
            kernels,
            resident,
            fixture,
            source_ranks,
            global_start,
            active_width,
        )
    selected_lookup = {int(rank): index for index, rank in enumerate(source_ranks)}
    adjoint_samples = np.full((len(source_ranks), active_width), np.nan, dtype=np.float64)
    full_adjoint = (
        np.empty((geometry.source_occupancies, active_width), dtype=np.float64)
        if collect_full
        else None
    )
    contract_rows = (
        np.empty(geometry.source_occupancies, dtype=np.float64)
        if collect_direct
        else None
    )
    digest = sha256()
    inactive_pass = True
    nonzero_source_offset = False
    for start in range(0, geometry.source_occupancies, source_chunk):
        records = min(source_chunk, geometry.source_occupancies - start)
        nonzero_source_offset = nonzero_source_offset or start > 0
        unique.fill(_POISON)
        _launch(
            kernels["signed_targets_chunk"],
            records * active_width,
            (
                table,
                resident.adjoint_offsets,
                np.int32(QUERY_CARDS),
                resident.query_masks,
                np.int32(1),
                np.int32(SOURCE_CARDS),
                np.int64(start),
                np.int64(records),
                np.int32(fixture.available_cards),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                unique,
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        unique_host = unique[:records, :active_width].get()
        digest.update(memoryview(np.ascontiguousarray(unique_host)).cast("B"))
        if full_adjoint is not None:
            full_adjoint[start : start + records] = unique_host
        for rank, output_index in selected_lookup.items():
            if start <= rank < start + records:
                adjoint_samples[output_index] = unique_host[rank - start]
        if active_width < PHYSICAL_STRIDE_WIDTH:
            inactive = unique[0, active_width:PHYSICAL_STRIDE_WIDTH].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))
        _launch(
            kernels["source_adjoint_contract_chunk"],
            records,
            (
                unique,
                np.int64(start),
                np.int64(records),
                np.int32(global_start),
                np.int32(active_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(fixture.available_cards),
                np.int32(geometry.hand_width),
                np.int32(fixture.pair_to_hand.shape[1]),
                np.int32(SOURCE_RANK),
                resident.pairings,
                resident.pair_to_hand,
                resident.unary,
                resident.factors,
                np.int32(fixture.unary_weights.size),
                resident.unary_offsets,
                resident.transitions[0],
                resident.transitions[1],
                resident.transitions[2],
            ),
        )
        if contract_rows is not None:
            cp.cuda.get_current_stream().synchronize()
            contract_rows[start : start + records] = unique[:records, 0].get()
        _reduce_scalar(kernels, unique, records, start, carry)
        _launch(
            kernels["accumulate_results"],
            1,
            (
                resident.results,
                carry,
                resident.results,
                np.int32(1),
                np.uint64(start + records),
                np.int32(int(start + records == geometry.source_occupancies)),
            ),
        )
    cp.cuda.get_current_stream().synchronize()
    if not np.all(np.isfinite(adjoint_samples)):
        raise AssertionError("CUDA-consumer adjoint samples were not captured")
    if active_width < PHYSICAL_STRIDE_WIDTH:
        for rank in (0, geometry.query_occupancies - 1):
            inactive = table[
                query_offset + rank, active_width:PHYSICAL_STRIDE_WIDTH
            ].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))
    return {
        "adjoint_samples": adjoint_samples,
        "direct_adjoint": direct_adjoint,
        "adjoint_digest": digest.hexdigest(),
        "full_adjoint": full_adjoint,
        "contract_rows": contract_rows,
        "inactive_pass": inactive_pass,
        "nonzero_query_offset": nonzero_query_offset,
        "nonzero_source_offset": nonzero_source_offset,
    }


def _same_capture(
    first: Mapping[str, object], second: Mapping[str, object], keys: Sequence[str]
) -> bool:
    for key in keys:
        left = first[key]
        right = second[key]
        if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
            if (
                left.dtype != right.dtype
                or left.shape != right.shape
                or left.tobytes() != right.tobytes()
            ):
                return False
        elif left != right:
            return False
    return True


def _positive_zero_pair(values: np.ndarray) -> bool:
    return (
        values.shape == (2,)
        and values[0].tobytes() == np.float64(0.0).tobytes()
        and values[1].tobytes() == np.float64(0.0).tobytes()
    )


def _online_pairwise_sum(values: Sequence[float], *, high_to_low: bool) -> float:
    carry = [0.0] * 64
    count = 0
    for item in values:
        value = float(item)
        level = 0
        index = count
        while index & (1 << level):
            value = carry[level] + value
            level += 1
        carry[level] = value
        count += 1
    levels = range(63, -1, -1) if high_to_low else range(64)
    selected = [carry[level] for level in levels if count & (1 << level)]
    if not selected:
        return 0.0
    result = selected[0]
    for value in selected[1:]:
        result += value
    return result


def _run_device_population(
    cp: Any,
    kernels: Mapping[str, object],
    config: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
    *,
    forward_query_chunk: int,
    adjoint_query_occupancy_chunk: int,
    adjoint_source_chunk: int,
    feature_order: tuple[tuple[int, int], ...] = FEATURE_SLICES,
    missing_label_control: bool = False,
) -> PopulationExecution:
    started = perf_counter()
    geometry = fixture.geometry
    if tuple(sorted(feature_order)) != tuple(sorted(FEATURE_SLICES)):
        raise ValueError("CUDA-consumer feature order is not the frozen partition")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in (
            forward_query_chunk,
            adjoint_query_occupancy_chunk,
            adjoint_source_chunk,
        )
    ):
        raise ValueError("CUDA-consumer chunk sizes must be positive integers")
    if forward_query_chunk > geometry.labeled_query_records:
        forward_query_chunk = geometry.labeled_query_records
    if adjoint_query_occupancy_chunk > geometry.query_occupancies:
        adjoint_query_occupancy_chunk = geometry.query_occupancies
    if adjoint_source_chunk > geometry.source_occupancies:
        adjoint_source_chunk = geometry.source_occupancies

    pool = cp.get_default_memory_pool()
    pinned = cp.get_default_pinned_memory_pool()
    pool.free_all_blocks()
    pinned.free_all_blocks()
    if int(pool.used_bytes()) != 0 or int(pool.total_bytes()) != 0:
        raise RuntimeError("CUDA-consumer default pool was nonzero before bounded birth")
    source_ranks, query_records = _sample_rows(config, fixture.available_cards)
    resident = _allocate_resident(cp, fixture)
    maximum_pool_total = int(pool.total_bytes())
    collect_full = fixture.available_cards == 10
    collect_direct = fixture.available_cards == 25

    source_samples = np.empty((len(source_ranks), TOTAL_FEATURE_WIDTH), dtype=np.float64)
    query_samples = np.empty((len(query_records), TOTAL_FEATURE_WIDTH), dtype=np.float64)
    adjoint_samples = np.empty((len(source_ranks), TOTAL_FEATURE_WIDTH), dtype=np.float64)
    direct_query = np.empty_like(query_samples)
    direct_adjoint = np.empty_like(adjoint_samples)
    fold_parts = np.empty((2, len(query_records), 2), dtype=np.float64)
    direct_fold_parts = np.empty_like(fold_parts)
    full_source = (
        np.empty((geometry.source_occupancies, TOTAL_FEATURE_WIDTH), dtype=np.float64)
        if collect_full
        else None
    )
    full_compatible = (
        np.empty((geometry.labeled_query_records, TOTAL_FEATURE_WIDTH), dtype=np.float64)
        if collect_full
        else None
    )
    full_fold_parts = (
        np.empty((2, geometry.labeled_query_records, 2), dtype=np.float64)
        if collect_full
        else None
    )
    full_adjoint = (
        np.empty((geometry.source_occupancies, TOTAL_FEATURE_WIDTH), dtype=np.float64)
        if collect_full
        else None
    )
    source_digests = ["", ""]
    compatible_digests = ["", ""]
    fold_digests = ["", ""]
    adjoint_digests = ["", ""]
    forward_partials = [0.0, 0.0]
    transpose_partials = [0.0, 0.0]
    streamed_forward_rows: list[np.ndarray | None] = [None, None]
    streamed_contract_rows: list[np.ndarray | None] = [None, None]
    repeat_identity = True
    poison_pass = True
    accumulator_pass = True
    nonzero_query_offset = False
    nonzero_source_offset = False

    forward_rows = sum(
        comb(fixture.available_cards, level) for level in range(SOURCE_CARDS + 1)
    )
    table = cp.empty((forward_rows, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64)
    compatible = cp.empty(
        (forward_query_chunk, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64
    )
    numerator = cp.empty(forward_query_chunk, dtype=cp.float64)
    reach = cp.empty(forward_query_chunk, dtype=cp.float64)
    maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    for global_start, stop in feature_order:
        active_width = stop - global_start
        slice_index = 0 if global_start == 0 else 1
        before = resident.results.get()
        first = _forward_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            active_width=active_width,
            query_chunk=forward_query_chunk,
            table=table,
            compatible=compatible,
            numerator=numerator,
            reach=reach,
            source_ranks=source_ranks,
            query_records=query_records,
            collect_full=collect_full,
            collect_direct=collect_direct,
        )
        after_first = resident.results.get()
        resident.results.set(before)
        second = _forward_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            active_width=active_width,
            query_chunk=forward_query_chunk,
            table=table,
            compatible=compatible,
            numerator=numerator,
            reach=reach,
            source_ranks=source_ranks,
            query_records=query_records,
            collect_full=collect_full,
            collect_direct=collect_direct,
        )
        after_second = resident.results.get()
        capture_keys = (
            "source_samples",
            "query_samples",
            "fold_samples",
            "direct_query",
            "direct_fold",
            "source_digest",
            "compatible_digest",
            "fold_digest",
            "inactive_pass",
            "nonzero_offset",
        )
        repeat_identity = repeat_identity and _same_capture(first, second, capture_keys)
        repeat_identity = repeat_identity and after_first.tobytes() == after_second.tobytes()
        accumulator_pass = accumulator_pass and (
            after_second[1].tobytes() == before[1].tobytes()
            if slice_index == 0
            else True
        )
        partial = after_second - before
        forward_partials[slice_index] = float(partial[0])
        if slice_index == 1:
            accumulator_pass = accumulator_pass and partial[1] > 0.0
        source_samples[:, global_start:stop] = second["source_samples"]
        query_samples[:, global_start:stop] = second["query_samples"]
        fold_parts[slice_index] = second["fold_samples"]
        if collect_direct:
            direct_query[:, global_start:stop] = second["direct_query"]
            direct_fold_parts[slice_index] = second["direct_fold"]
            streamed_forward_rows[slice_index] = second["scalar_rows"]
        source_digests[slice_index] = str(second["source_digest"])
        compatible_digests[slice_index] = str(second["compatible_digest"])
        fold_digests[slice_index] = str(second["fold_digest"])
        poison_pass = poison_pass and bool(second["inactive_pass"])
        nonzero_query_offset = nonzero_query_offset or bool(second["nonzero_offset"])
        if full_source is not None and full_compatible is not None and full_fold_parts is not None:
            full_source[:, global_start:stop] = second["full_source"]
            full_compatible[:, global_start:stop] = second["full_compatible"]
            full_fold_parts[slice_index] = second["full_fold"]
        maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    forward_result = resident.results.get()
    forward_reach = float(forward_result[1])
    forward_numerator = float(forward_result[0])
    if not (np.isfinite(forward_numerator) and np.isfinite(forward_reach) and forward_reach > 0.0):
        raise ArithmeticError(
            "CUDA-consumer bounded forward scalar is outside its units: "
            f"numerator={forward_numerator!r}, reach={forward_reach!r}"
        )
    forward_value = forward_numerator / forward_reach
    full_fold = None
    if full_fold_parts is not None:
        full_fold = np.empty_like(full_fold_parts[0])
        full_fold[:, 0] = full_fold_parts[0, :, 0] + full_fold_parts[1, :, 0]
        full_fold[:, 1] = full_fold_parts[0, :, 1] + full_fold_parts[1, :, 1]
    fold_samples = np.empty_like(fold_parts[0])
    fold_samples[:, 0] = fold_parts[0, :, 0] + fold_parts[1, :, 0]
    fold_samples[:, 1] = fold_parts[0, :, 1] + fold_parts[1, :, 1]
    direct_fold = np.empty_like(direct_fold_parts[0])
    if collect_direct:
        direct_fold[:, 0] = direct_fold_parts[0, :, 0] + direct_fold_parts[1, :, 0]
        direct_fold[:, 1] = direct_fold_parts[0, :, 1] + direct_fold_parts[1, :, 1]
    else:
        direct_fold.fill(np.nan)

    del table, compatible, numerator, reach
    gc.collect()
    pool.free_all_blocks()
    forward_pool_total = int(pool.total_bytes())
    resident.results.fill(np.float64(0.0))
    cp.cuda.get_current_stream().synchronize()
    accumulator_pass = accumulator_pass and _positive_zero_pair(resident.results.get())
    forward_released = forward_pool_total < maximum_pool_total

    adjoint_rows = sum(
        comb(fixture.available_cards, level) for level in range(QUERY_CARDS + 1)
    )
    table = cp.empty((adjoint_rows, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64)
    covector = cp.empty(
        (adjoint_query_occupancy_chunk * QUERY_LABELS, PHYSICAL_STRIDE_WIDTH),
        dtype=cp.float64,
    )
    unique = cp.empty((adjoint_source_chunk, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64)
    maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    for global_start, stop in feature_order:
        active_width = stop - global_start
        slice_index = 0 if global_start == 0 else 1
        before = resident.results.get()
        first = _adjoint_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            active_width=active_width,
            query_occupancy_chunk=adjoint_query_occupancy_chunk,
            source_chunk=adjoint_source_chunk,
            table=table,
            covector=covector,
            unique=unique,
            source_ranks=source_ranks,
            collect_full=collect_full,
            collect_direct=collect_direct,
        )
        after_first = resident.results.get()
        resident.results.set(before)
        second = _adjoint_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            active_width=active_width,
            query_occupancy_chunk=adjoint_query_occupancy_chunk,
            source_chunk=adjoint_source_chunk,
            table=table,
            covector=covector,
            unique=unique,
            source_ranks=source_ranks,
            collect_full=collect_full,
            collect_direct=collect_direct,
        )
        after_second = resident.results.get()
        capture_keys = (
            "adjoint_samples",
            "direct_adjoint",
            "adjoint_digest",
            "inactive_pass",
            "nonzero_query_offset",
            "nonzero_source_offset",
        )
        repeat_identity = repeat_identity and _same_capture(first, second, capture_keys)
        repeat_identity = repeat_identity and after_first.tobytes() == after_second.tobytes()
        accumulator_pass = accumulator_pass and (
            after_second[1].tobytes() == np.float64(0.0).tobytes()
        )
        transpose_partials[slice_index] = float(after_second[0] - before[0])
        adjoint_samples[:, global_start:stop] = second["adjoint_samples"]
        if collect_direct:
            direct_adjoint[:, global_start:stop] = second["direct_adjoint"]
            streamed_contract_rows[slice_index] = second["contract_rows"]
        adjoint_digests[slice_index] = str(second["adjoint_digest"])
        poison_pass = poison_pass and bool(second["inactive_pass"])
        nonzero_query_offset = nonzero_query_offset or bool(second["nonzero_query_offset"])
        nonzero_source_offset = nonzero_source_offset or bool(second["nonzero_source_offset"])
        if full_adjoint is not None:
            full_adjoint[:, global_start:stop] = second["full_adjoint"]
        maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    transpose_result = resident.results.get()
    accumulator_pass = (
        accumulator_pass
        and transpose_result[1].tobytes() == np.float64(0.0).tobytes()
    )
    missing_changed: bool | None = None
    if missing_label_control:
        saved = transpose_result.copy()
        resident.results.fill(np.float64(0.0))
        mutated = _adjoint_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=0,
            active_width=128,
            query_occupancy_chunk=adjoint_query_occupancy_chunk,
            source_chunk=adjoint_source_chunk,
            table=table,
            covector=covector,
            unique=unique,
            source_ranks=source_ranks,
            collect_full=False,
            collect_direct=False,
            skip_last_label=True,
        )
        mutated_result = resident.results.get()
        missing_changed = (
            str(mutated["adjoint_digest"]) != adjoint_digests[0]
            and mutated_result[0].tobytes() != np.float64(transpose_partials[0]).tobytes()
        )
        resident.results.set(saved)

    scalar_results = (
        forward_partials[0],
        forward_partials[1],
        forward_numerator,
        forward_reach,
        forward_value,
        transpose_partials[0],
        transpose_partials[1],
        float(transpose_result[0]),
    )
    streamed_reference_scalars: tuple[float, float, float] | None = None
    streamed_pairwise_scalars: tuple[float, float, float, float] | None = None
    if collect_direct:
        if any(value is None for value in streamed_forward_rows + streamed_contract_rows):
            raise AssertionError("bounded scalar reference rows were not retained")
        assert streamed_forward_rows[0] is not None
        assert streamed_forward_rows[1] is not None
        assert streamed_contract_rows[0] is not None
        assert streamed_contract_rows[1] is not None
        streamed_reference_scalars = (
            fsum(
                float(value)
                for part in streamed_forward_rows
                for value in part[:, 0]
            ),
            fsum(
                float(value)
                for value in (
                    streamed_forward_rows[0][:, 1]
                    + streamed_forward_rows[1][:, 1]
                )
            ),
            fsum(
                float(value)
                for part in streamed_contract_rows
                for value in part
            ),
        )
        streamed_pairwise_scalars = (
            _online_pairwise_sum(
                streamed_forward_rows[0][:, 0], high_to_low=True
            )
            + _online_pairwise_sum(
                streamed_forward_rows[1][:, 0], high_to_low=True
            ),
            _online_pairwise_sum(
                streamed_forward_rows[0][:, 0], high_to_low=False
            )
            + _online_pairwise_sum(
                streamed_forward_rows[1][:, 0], high_to_low=False
            ),
            _online_pairwise_sum(
                streamed_contract_rows[0], high_to_low=True
            )
            + _online_pairwise_sum(
                streamed_contract_rows[1], high_to_low=True
            ),
            _online_pairwise_sum(
                streamed_contract_rows[0], high_to_low=False
            )
            + _online_pairwise_sum(
                streamed_contract_rows[1], high_to_low=False
            ),
        )
    del table, covector, unique, resident
    gc.collect()
    pool.free_all_blocks()
    pinned.free_all_blocks()
    released_used = int(pool.used_bytes())
    released_total = int(pool.total_bytes())
    released_pinned = int(pinned.n_free_blocks())
    return PopulationExecution(
        available_cards=fixture.available_cards,
        feature_order=feature_order,
        forward_query_chunk=forward_query_chunk,
        adjoint_query_occupancy_chunk=adjoint_query_occupancy_chunk,
        adjoint_source_chunk=adjoint_source_chunk,
        scalar_results=scalar_results,
        streamed_reference_scalars=streamed_reference_scalars,
        streamed_pairwise_scalars=streamed_pairwise_scalars,
        source_samples=source_samples[:, _BOUNDARY_FEATURES],
        query_samples=query_samples[:, _BOUNDARY_FEATURES],
        fold_samples=fold_samples,
        adjoint_samples=adjoint_samples[:, _BOUNDARY_FEATURES],
        direct_query_samples=(
            direct_query[:, _BOUNDARY_FEATURES]
            if collect_direct
            else np.empty((0, len(_BOUNDARY_FEATURES)), dtype=np.float64)
        ),
        direct_fold_samples=(
            direct_fold
            if collect_direct
            else np.empty((0, 2), dtype=np.float64)
        ),
        direct_adjoint_samples=(
            direct_adjoint[:, _BOUNDARY_FEATURES]
            if collect_direct
            else np.empty((0, len(_BOUNDARY_FEATURES)), dtype=np.float64)
        ),
        source_slice_digests=tuple(source_digests),
        compatible_slice_digests=tuple(compatible_digests),
        fold_slice_digests=tuple(fold_digests),
        adjoint_slice_digests=tuple(adjoint_digests),
        full_source=full_source,
        full_compatible=full_compatible,
        full_fold=full_fold,
        full_adjoint=full_adjoint,
        repeat_byte_identity=repeat_identity,
        inactive_poison_pass=poison_pass,
        nonzero_query_offset_observed=nonzero_query_offset,
        nonzero_source_offset_observed=nonzero_source_offset,
        forward_released_before_adjoint=forward_released,
        accumulator_lifecycle_pass=accumulator_pass,
        missing_label_changed_result=missing_changed,
        maximum_pool_total_bytes=maximum_pool_total,
        released_pool_used_bytes=released_used,
        released_pool_total_bytes=released_total,
        released_pinned_blocks=released_pinned,
        wall_ms=(perf_counter() - started) * 1000.0,
    )


def _errors_are_valid(errors: Mapping[str, float]) -> bool:
    return all(np.isfinite(value) and value >= 0.0 for value in errors.values())


def _reporting_digest(*arrays: np.ndarray) -> str:
    digest = sha256()
    for values in arrays:
        contiguous = np.ascontiguousarray(values)
        digest.update(repr((contiguous.shape, contiguous.dtype.str)).encode("ascii"))
        digest.update(memoryview(contiguous).cast("B"))
    return digest.hexdigest()


def _ten_card_evidence(
    cp: Any,
    kernels: Mapping[str, object],
    config: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
) -> BoundedPopulationEvidence:
    controls = config["bounded_device_controls"]
    assert isinstance(controls, Mapping)
    exact_control = controls["exact_population_10"]
    assert isinstance(exact_control, Mapping)
    reference = complete_ten_card_reference(fixture)
    chunks = (
        int(exact_control["forward_query_record_chunk"]),
        int(exact_control["adjoint_query_occupancy_chunk"]),
        int(exact_control["adjoint_source_occupancy_chunk"]),
    )
    normal = _run_device_population(
        cp,
        kernels,
        config,
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        feature_order=FEATURE_SLICES,
        missing_label_control=True,
    )
    reversed_order = _run_device_population(
        cp,
        kernels,
        config,
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        feature_order=tuple(reversed(FEATURE_SLICES)),
    )
    if any(
        value is None
        for value in (
            normal.full_source,
            normal.full_compatible,
            normal.full_fold,
            normal.full_adjoint,
        )
    ):
        raise AssertionError("ten-card CUDA consumer omitted a complete matrix")
    assert normal.full_source is not None
    assert normal.full_compatible is not None
    assert normal.full_fold is not None
    assert normal.full_adjoint is not None
    source_abs, source_rel = _maximum_errors(normal.full_source, reference.source)
    query_abs, query_rel = _maximum_errors(normal.full_compatible, reference.compatible)
    fold_abs, fold_rel = _maximum_errors(normal.full_fold, reference.fold)
    adjoint_abs, adjoint_rel = _maximum_errors(normal.full_adjoint, reference.adjoint)
    scalar_abs, scalar_rel = _maximum_errors(
        np.asarray(normal.scalar_results), np.asarray(reference.scalar_order)
    )
    errors = MappingProxyType(
        {
            "source_absolute": source_abs,
            "source_scale_relative": source_rel,
            "forward_row_absolute": query_abs,
            "forward_row_scale_relative": query_rel,
            "fold_absolute": fold_abs,
            "fold_scale_relative": fold_rel,
            "adjoint_row_absolute": adjoint_abs,
            "adjoint_row_scale_relative": adjoint_rel,
            "scalar_absolute": scalar_abs,
            "scalar_scale_relative": scalar_rel,
            "transpose_absolute": abs(
                normal.scalar_results[2] - normal.scalar_results[7]
            ),
        }
    )
    limits = config["numerical_limits"]
    assert isinstance(limits, Mapping)
    normal_reverse_rows = all(
        left is not None
        and right is not None
        and left.tobytes() == right.tobytes()
        for left, right in (
            (normal.full_source, reversed_order.full_source),
            (normal.full_compatible, reversed_order.full_compatible),
            (normal.full_fold, reversed_order.full_fold),
            (normal.full_adjoint, reversed_order.full_adjoint),
        )
    )
    reverse_scalar_abs, reverse_scalar_rel = _maximum_errors(
        np.asarray(normal.scalar_results),
        np.asarray(reversed_order.scalar_results),
    )
    gates = MappingProxyType(
        {
            "complete_fraction_source": source_abs
            <= float(limits["bounded_source_sample_absolute"]),
            "complete_fraction_forward": query_abs
            <= float(limits["bounded_forward_row_absolute"]),
            "complete_fraction_fold": fold_abs
            <= float(limits["bounded_fold_absolute"]),
            "complete_fraction_adjoint": adjoint_abs
            <= float(limits["bounded_adjoint_row_absolute"]),
            "complete_fraction_scalar_scale": scalar_rel
            <= float(limits["bounded_scale_normalized_relative"]),
            "scale_normalized_relative": max(
                source_rel, query_rel, fold_rel, adjoint_rel, scalar_rel
            )
            <= float(limits["bounded_scale_normalized_relative"]),
            "transpose_identity": errors["transpose_absolute"]
            <= float(limits["bounded_transpose_dot_absolute"]),
            "normal_reverse_slice_order": normal_reverse_rows
            and reverse_scalar_rel
            <= float(limits["bounded_scale_normalized_relative"])
            and np.isfinite(reverse_scalar_abs),
            "repeat_byte_identity": normal.repeat_byte_identity
            and reversed_order.repeat_byte_identity,
            "inactive_poison": normal.inactive_poison_pass
            and reversed_order.inactive_poison_pass,
            "nonzero_query_offset": normal.nonzero_query_offset_observed,
            "nonzero_source_offset": normal.nonzero_source_offset_observed,
            "forward_release_before_adjoint": normal.forward_released_before_adjoint
            and reversed_order.forward_released_before_adjoint,
            "accumulator_lifecycle": normal.accumulator_lifecycle_pass
            and reversed_order.accumulator_lifecycle_pass,
            "missing_label_rejected": normal.missing_label_changed_result is True,
            "pool_release": normal.released_pool_used_bytes == 0
            and normal.released_pool_total_bytes == 0
            and normal.released_pinned_blocks == 0
            and reversed_order.released_pool_used_bytes == 0
            and reversed_order.released_pool_total_bytes == 0
            and reversed_order.released_pinned_blocks == 0,
            "finite_two_sided_errors": _errors_are_valid(errors),
            "chip_units": -10.0 <= normal.scalar_results[4] <= 50.0,
        }
    )
    return BoundedPopulationEvidence(
        available_cards=10,
        wall_ms=normal.wall_ms + reversed_order.wall_ms,
        scalar_results=normal.scalar_results,
        maximum_errors=errors,
        reporting_digests=MappingProxyType(
            {
                "source": _reporting_digest(normal.full_source),
                "compatible": _reporting_digest(normal.full_compatible),
                "fold": _reporting_digest(normal.full_fold),
                "adjoint": _reporting_digest(normal.full_adjoint),
                "reference": _reporting_digest(
                    reference.source,
                    reference.compatible,
                    reference.fold,
                    reference.adjoint,
                    np.asarray(reference.scalar_order),
                ),
            }
        ),
        gates=gates,
    )


def _twenty_five_card_evidence(
    cp: Any,
    kernels: Mapping[str, object],
    config: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
) -> BoundedPopulationEvidence:
    controls = config["bounded_device_controls"]
    assert isinstance(controls, Mapping)
    multichunk = controls["multichunk_population_25"]
    streaming = config["streaming"]
    assert isinstance(multichunk, Mapping)
    assert isinstance(streaming, Mapping)
    default = _run_device_population(
        cp,
        kernels,
        config,
        fixture,
        forward_query_chunk=int(streaming["forward_query_record_chunk"]),
        adjoint_query_occupancy_chunk=int(streaming["adjoint_query_occupancy_chunk"]),
        adjoint_source_chunk=int(streaming["adjoint_source_occupancy_chunk"]),
    )
    alternate = _run_device_population(
        cp,
        kernels,
        config,
        fixture,
        forward_query_chunk=int(multichunk["alternate_forward_query_record_chunk"]),
        adjoint_query_occupancy_chunk=int(
            multichunk["alternate_adjoint_query_occupancy_chunk"]
        ),
        adjoint_source_chunk=int(
            multichunk["alternate_adjoint_source_occupancy_chunk"]
        ),
    )
    source_ranks, _ = _sample_rows(config, 25)
    expected_source = np.asarray(
        [
            [float(_source_row_exact(fixture, rank)[feature]) for feature in _BOUNDARY_FEATURES]
            for rank in source_ranks
        ],
        dtype=np.float64,
    )
    source_abs, source_rel = _maximum_errors(default.source_samples, expected_source)
    query_abs, query_rel = _maximum_errors(
        default.query_samples, default.direct_query_samples
    )
    fold_abs, fold_rel = _maximum_errors(
        default.fold_samples, default.direct_fold_samples
    )
    adjoint_abs, adjoint_rel = _maximum_errors(
        default.adjoint_samples, default.direct_adjoint_samples
    )
    scalar_array = np.asarray(default.scalar_results, dtype=np.float64)
    alternate_scalar = np.asarray(alternate.scalar_results, dtype=np.float64)
    scalar_abs, scalar_rel = _maximum_errors(scalar_array, alternate_scalar)
    errors = MappingProxyType(
        {
            "source_absolute": source_abs,
            "source_scale_relative": source_rel,
            "direct_forward_absolute": query_abs,
            "direct_forward_scale_relative": query_rel,
            "direct_fold_absolute": fold_abs,
            "direct_fold_scale_relative": fold_rel,
            "direct_adjoint_absolute": adjoint_abs,
            "direct_adjoint_scale_relative": adjoint_rel,
            "alternate_scalar_absolute": scalar_abs,
            "alternate_scalar_scale_relative": scalar_rel,
            "transpose_absolute": abs(
                default.scalar_results[2] - default.scalar_results[7]
            ),
            "transpose_scale_relative": abs(
                default.scalar_results[2] - default.scalar_results[7]
            )
            / max(1.0, abs(default.scalar_results[2])),
        }
    )
    limits = config["numerical_limits"]
    assert isinstance(limits, Mapping)
    digest_identity = (
        default.compatible_slice_digests == alternate.compatible_slice_digests
        and default.fold_slice_digests == alternate.fold_slice_digests
        and default.adjoint_slice_digests == alternate.adjoint_slice_digests
        and default.source_samples.tobytes() == alternate.source_samples.tobytes()
        and default.query_samples.tobytes() == alternate.query_samples.tobytes()
        and default.fold_samples.tobytes() == alternate.fold_samples.tobytes()
        and default.adjoint_samples.tobytes() == alternate.adjoint_samples.tobytes()
        and np.asarray(default.scalar_results, dtype=np.float64).tobytes()
        == np.asarray(alternate.scalar_results, dtype=np.float64).tobytes()
    )
    wall_ms = default.wall_ms + alternate.wall_ms
    gates = MappingProxyType(
        {
            "selected_fraction_source": source_abs
            <= float(limits["bounded_source_sample_absolute"]),
            "selected_direct_forward": query_abs
            <= float(limits["bounded_forward_row_absolute"]),
            "selected_direct_fold": fold_abs
            <= float(limits["bounded_fold_absolute"]),
            "selected_direct_adjoint": adjoint_abs
            <= float(limits["bounded_adjoint_row_absolute"]),
            "scale_normalized_relative": max(
                source_rel, query_rel, fold_rel, adjoint_rel
            )
            <= float(limits["bounded_scale_normalized_relative"]),
            "default_alternate_byte_identity": digest_identity,
            "default_alternate_scalar_consistency": scalar_rel
            <= float(limits["bounded_scale_normalized_relative"]),
            "transpose_identity": errors["transpose_absolute"]
            <= float(limits["bounded_transpose_dot_absolute"])
            and errors["transpose_scale_relative"]
            <= float(limits["bounded_scale_normalized_relative"]),
            "repeat_byte_identity": default.repeat_byte_identity
            and alternate.repeat_byte_identity,
            "inactive_poison": default.inactive_poison_pass
            and alternate.inactive_poison_pass,
            "nonzero_query_offset": default.nonzero_query_offset_observed
            and alternate.nonzero_query_offset_observed,
            "nonzero_source_offset": default.nonzero_source_offset_observed
            and alternate.nonzero_source_offset_observed,
            "forward_release_before_adjoint": default.forward_released_before_adjoint
            and alternate.forward_released_before_adjoint,
            "accumulator_lifecycle": default.accumulator_lifecycle_pass
            and alternate.accumulator_lifecycle_pass,
            "pool_cap": max(
                default.maximum_pool_total_bytes,
                alternate.maximum_pool_total_bytes,
            )
            <= int(multichunk["maximum_device_numeric_bytes"]),
            "pool_release": default.released_pool_used_bytes == 0
            and default.released_pool_total_bytes == 0
            and default.released_pinned_blocks == 0
            and alternate.released_pool_used_bytes == 0
            and alternate.released_pool_total_bytes == 0
            and alternate.released_pinned_blocks == 0,
            "population_wall": wall_ms <= float(multichunk["population_wall_limit_ms"]),
            "finite_two_sided_errors": _errors_are_valid(errors),
            "chip_units": -10.0 <= default.scalar_results[4] <= 50.0,
        }
    )
    return BoundedPopulationEvidence(
        available_cards=25,
        wall_ms=wall_ms,
        scalar_results=default.scalar_results,
        maximum_errors=errors,
        reporting_digests=MappingProxyType(
            {
                "source_samples": _reporting_digest(default.source_samples),
                "query_samples": _reporting_digest(default.query_samples),
                "fold_samples": _reporting_digest(default.fold_samples),
                "adjoint_samples": _reporting_digest(default.adjoint_samples),
                "direct_samples": _reporting_digest(
                    default.direct_query_samples,
                    default.direct_fold_samples,
                    default.direct_adjoint_samples,
                ),
                "compatible_stream": sha256(
                    "|".join(default.compatible_slice_digests).encode("ascii")
                ).hexdigest(),
                "adjoint_stream": sha256(
                    "|".join(default.adjoint_slice_digests).encode("ascii")
                ).hexdigest(),
            }
        ),
        gates=gates,
    )


def run_bounded_cuda_consumer_conformance() -> BoundedCudaConsumerReport:
    """Run only ADR-0389's complete 10- and 25-card device controls."""

    global _BOUNDED_EXECUTION_CALLS
    _BOUNDED_EXECUTION_CALLS += 1
    config = load_preregistered_cuda_consumer_config()
    verify_preregistered_cuda_consumer_contract(config)
    actual_before = actual_execution_call_count()
    allocations_before = actual_numeric_allocation_call_count()
    science_before = actual_scientific_call_count()
    fixture10 = compile_consumer_population_fixture(10)
    fixture25 = compile_consumer_population_fixture(25)
    if (
        fixture10.bridge_digest != fixture25.bridge_digest
        or fixture10.topology_digest != fixture25.topology_digest
    ):
        raise ValueError("bounded CUDA-consumer fixtures did not share one legal bridge")
    cp = _cupy_module()
    kernels = _kernels(cp)
    runtime = _runtime_identity(cp)
    _verify_runtime(runtime, config)
    ten = _ten_card_evidence(cp, kernels, config, fixture10)
    twenty_five = _twenty_five_card_evidence(cp, kernels, config, fixture25)
    actual_after = actual_execution_call_count()
    allocations_after = actual_numeric_allocation_call_count()
    science_after = actual_scientific_call_count()
    gates = MappingProxyType(
        {
            "source_rebind": True,
            "same_legal_bridge": fixture10.bridge_digest == fixture25.bridge_digest,
            "same_runtime_as_actual_contract": True,
            "actual_entry_not_called": actual_before == actual_after == 0,
            "actual_numeric_allocation_not_called": allocations_before
            == allocations_after
            == 0,
            "actual_scientific_path_not_called": science_before == science_after == 0,
            "reserved_population_not_compiled": fixture10.available_cards == 10
            and fixture25.available_cards == 25,
        }
    )
    return BoundedCudaConsumerReport(
        config_sha256=PREREGISTERED_CONFIG_SHA256,
        bridge_sha256=fixture10.bridge_digest,
        topology_sha256=fixture10.topology_digest,
        runtime=runtime,
        ten_card=ten,
        twenty_five_card=twenty_five,
        actual_execution_calls_before=actual_before,
        actual_execution_calls_after=actual_after,
        actual_numeric_allocation_calls_before=allocations_before,
        actual_numeric_allocation_calls_after=allocations_after,
        actual_scientific_calls_before=science_before,
        actual_scientific_calls_after=science_after,
        gates=gates,
    )


__all__ = [
    "BoundedCudaConsumerReport",
    "BoundedPopulationEvidence",
    "CompleteTenCardReference",
    "ConsumerPopulationFixture",
    "CudaRuntimeIdentity",
    "FEATURE_SLICES",
    "PHYSICAL_STRIDE_WIDTH",
    "PREREGISTERED_CONFIG_SHA256",
    "PopulationGeometry",
    "actual_execution_call_count",
    "actual_numeric_allocation_call_count",
    "actual_scientific_call_count",
    "bounded_execution_call_count",
    "canonical_lf_sha256",
    "compile_consumer_population_fixture",
    "complete_ten_card_reference",
    "cupy_import_call_count",
    "load_preregistered_cuda_consumer_config",
    "population_geometry",
    "run_bounded_cuda_consumer_conformance",
    "verify_preregistered_cuda_consumer_contract",
]
