"""Bounded GPU keystone for the exact occupied-card quotient.

The public device entry point is intentionally locked to ADR-0371's complete
ten-card population.  Full-width values in this module are pure integer
preallocation/work arithmetic and cannot reach CuPy or a CUDA allocation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
from itertools import combinations
from math import comb
from time import perf_counter
from typing import Mapping

import numpy as np

from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief
from .occupied_card_quotient import (
    ExactQuotientCoefficients,
    OccupiedCardQuotientTopology,
)
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)


BOUNDED_AVAILABLE_CARDS = 10
SOURCE_CARDS = 6
QUERY_CARDS = 4
SOURCE_PAIRINGS_PER_OCCUPANCY = 90
QUERY_PAIRINGS_PER_OCCUPANCY = 6
MAXIMUM_FEATURE_BATCH = 128
FIXED_DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
FIXED_DEVICE_RESERVE_BYTES = 2_000_000_000
MINIMUM_DEVICE_PHYSICAL_BYTES = 16_000_000_000
LABORATORY_HANG_GUARD_MS = 30_000.0

MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR = 2e-12
MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR = 2e-10
MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR = 2e-10
MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR = 2e-10
MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR = 2e-10
MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR = 2e-11

_CUPY_IMPORT_CALLS = 0


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool) or not isinstance(item, int) or item < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return item


def cardinality_offsets(available_cards: int, maximum_cards: int) -> tuple[int, ...]:
    """Return row offsets for cardinalities zero through ``maximum_cards``."""

    cards = _integer(available_cards, label="available cards", minimum=1)
    maximum = _integer(maximum_cards, label="maximum cards")
    if maximum > cards:
        raise ValueError("maximum cards exceed the available universe")
    offsets = []
    cursor = 0
    for width in range(maximum + 1):
        offsets.append(cursor)
        cursor += comb(cards, width)
    return tuple(offsets)


def colex_rank(cards: tuple[int, ...]) -> int:
    """Rank one sorted combination in colexicographic order."""

    if tuple(sorted(set(cards))) != cards or any(card < 0 for card in cards):
        raise ValueError("colex cards must be sorted unique nonnegative integers")
    return sum(comb(card, index) for index, card in enumerate(cards, start=1))


def colex_unrank(rank: int, available_cards: int, width: int) -> tuple[int, ...]:
    """Invert :func:`colex_rank` for a fixed universe and cardinality."""

    item = _integer(rank, label="colex rank")
    cards = _integer(available_cards, label="available cards", minimum=1)
    count = _integer(width, label="combination width")
    if count > cards or item >= comb(cards, count):
        raise ValueError("colex rank is outside the requested combination axis")
    result = [0] * count
    upper = cards - 1
    remainder = item
    for index in range(count, 0, -1):
        card = upper
        while comb(card, index) > remainder:
            card -= 1
        result[index - 1] = card
        remainder -= comb(card, index)
        upper = card - 1
    return tuple(result)


@dataclass(frozen=True, slots=True)
class RecurrenceAllocation:
    available_cards: int
    source_cards: int
    target_cards: int
    feature_width: int
    target_records: int
    level_rows: int
    level_table_bytes: int
    target_chunk_records: int
    target_chunk_bytes: int
    persistent_bytes: int
    requested_device_bytes: int
    fixed_cap_bytes: int
    reserve_bytes: int
    minimum_physical_bytes: int
    fixed_cap_pass: bool
    physical_reserve_pass: bool
    live_free_bytes: int | None
    live_reserve_pass: bool | None

    @property
    def all_available_gates_pass(self) -> bool:
        return (
            self.fixed_cap_pass
            and self.physical_reserve_pass
            and self.live_reserve_pass is not False
        )


def recurrence_allocation(
    *,
    available_cards: int,
    source_cards: int,
    target_cards: int,
    feature_width: int,
    target_records: int,
    target_chunk_records: int,
    persistent_bytes: int = 0,
    fixed_cap_bytes: int = FIXED_DEVICE_NUMERIC_CAP_BYTES,
    reserve_bytes: int = FIXED_DEVICE_RESERVE_BYTES,
    minimum_physical_bytes: int = MINIMUM_DEVICE_PHYSICAL_BYTES,
    live_free_bytes: int | None = None,
) -> RecurrenceAllocation:
    """Price one recurrence workspace without importing CuPy."""

    cards = _integer(available_cards, label="available cards", minimum=1)
    source = _integer(source_cards, label="source cards", minimum=1)
    target = _integer(target_cards, label="target cards", minimum=1)
    width = _integer(feature_width, label="feature width", minimum=1)
    records = _integer(target_records, label="target records", minimum=1)
    chunk = _integer(target_chunk_records, label="target chunk records", minimum=1)
    persistent = _integer(persistent_bytes, label="persistent bytes")
    cap = _integer(fixed_cap_bytes, label="fixed cap bytes", minimum=1)
    reserve = _integer(reserve_bytes, label="reserve bytes")
    physical = _integer(minimum_physical_bytes, label="minimum physical bytes", minimum=1)
    live = (
        None
        if live_free_bytes is None
        else _integer(live_free_bytes, label="live free bytes")
    )
    if source > cards or target > cards:
        raise ValueError("occupancy cardinality exceeds available cards")
    level_rows = sum(comb(cards, level) for level in range(source + 1))
    table_bytes = level_rows * width * np.dtype(np.float64).itemsize
    live_chunk = min(records, chunk)
    target_bytes = live_chunk * width * np.dtype(np.float64).itemsize
    requested = persistent + table_bytes + target_bytes
    live_pass = None if live is None else requested + reserve <= live
    return RecurrenceAllocation(
        available_cards=cards,
        source_cards=source,
        target_cards=target,
        feature_width=width,
        target_records=records,
        level_rows=level_rows,
        level_table_bytes=table_bytes,
        target_chunk_records=live_chunk,
        target_chunk_bytes=target_bytes,
        persistent_bytes=persistent,
        requested_device_bytes=requested,
        fixed_cap_bytes=cap,
        reserve_bytes=reserve,
        minimum_physical_bytes=physical,
        fixed_cap_pass=requested <= cap,
        physical_reserve_pass=requested + reserve <= physical,
        live_free_bytes=live,
        live_reserve_pass=live_pass,
    )


def bounded_device_allocation(
    *,
    available_cards: int,
    source_cards: int,
    target_cards: int,
    feature_width: int,
    target_records: int,
    target_chunk_records: int,
    persistent_bytes: int = 0,
    live_free_bytes: int | None = None,
) -> RecurrenceAllocation:
    """Fail closed before CuPy for every non-ADR-0371 device geometry."""

    if available_cards != BOUNDED_AVAILABLE_CARDS:
        raise ValueError("GPU quotient keystone is restricted to ten cards")
    if source_cards not in (SOURCE_CARDS, QUERY_CARDS):
        raise ValueError("GPU quotient source cardinality is outside the bounded seam")
    if target_cards not in (SOURCE_CARDS, QUERY_CARDS) or source_cards == target_cards:
        raise ValueError("GPU quotient target cardinality is outside the bounded seam")
    if feature_width > MAXIMUM_FEATURE_BATCH:
        raise ValueError("bounded GPU quotient feature width exceeds 128")
    model = recurrence_allocation(
        available_cards=available_cards,
        source_cards=source_cards,
        target_cards=target_cards,
        feature_width=feature_width,
        target_records=target_records,
        target_chunk_records=target_chunk_records,
        persistent_bytes=persistent_bytes,
        live_free_bytes=live_free_bytes,
    )
    if not model.all_available_gates_pass:
        raise MemoryError("GPU quotient preallocation guard rejected before allocation")
    return model


def cupy_import_call_count() -> int:
    """Expose the pre-import trap counter to the conformance test."""

    return _CUPY_IMPORT_CALLS


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


@dataclass(frozen=True, slots=True)
class CardinalityRecurrenceWork:
    available_cards: int
    source_cards: int
    feature_width: int
    vector_edges: int
    scalar_additions: int


def cardinality_recurrence_work(
    available_cards: int,
    source_cards: int,
    feature_width: int,
) -> CardinalityRecurrenceWork:
    cards = _integer(available_cards, label="available cards", minimum=1)
    source = _integer(source_cards, label="source cards", minimum=1)
    width = _integer(feature_width, label="feature width", minimum=1)
    if source > cards:
        raise ValueError("source cardinality exceeds available cards")
    edges = sum(comb(cards, level) * (cards - level) for level in range(source))
    return CardinalityRecurrenceWork(
        available_cards=cards,
        source_cards=source,
        feature_width=width,
        vector_edges=edges,
        scalar_additions=edges * width,
    )


@dataclass(frozen=True, slots=True)
class FrozenQuotientFixture:
    available_cards: int
    hands: tuple[tuple[int, int], ...]
    automaton: StructuredShowdownAutomaton
    unary_weights: np.ndarray
    mode_factors: np.ndarray
    mixture_weights: np.ndarray
    pair_to_hand: np.ndarray
    source_pair_positions: np.ndarray
    query_masks: np.ndarray
    query_hand_indices: np.ndarray
    unary_offsets: np.ndarray

    @property
    def components(self) -> int:
        return int(self.mixture_weights.size)

    @property
    def source_rank(self) -> int:
        return int(self.automaton.state_ranks[3])

    @property
    def feature_width(self) -> int:
        return self.components * (self.source_rank + 1)


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
    raise ValueError("only the frozen two- and three-pair seams are supported")


def _mask(cards: tuple[int, ...]) -> int:
    return sum(1 << card for card in cards)


def _readonly(values: object, dtype: object) -> np.ndarray:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def build_frozen_quotient_fixture() -> FrozenQuotientFixture:
    """Build the outcome-independent complete ten-card natural population."""

    cards = BOUNDED_AVAILABLE_CARDS
    hands = tuple(combinations(range(cards), 2))
    hand_id = {hand: index for index, hand in enumerate(hands)}
    pair_to_hand = np.full((cards, cards), -1, dtype=np.int32)
    for hand, index in hand_id.items():
        pair_to_hand[hand] = index
        pair_to_hand[hand[::-1]] = index

    strength = np.asarray(
        [(first * 7 + second * 11 + (first * second) % 5) % 9 for first, second in hands],
        dtype=np.int32,
    )
    automaton = build_structured_showdown_automaton(
        strength_codes=(
            strength,
            strength,
            strength,
            np.asarray((4,), dtype=np.int32),
            strength,
            strength,
        ),
        contenders=(0, 1, 2, 3, 4, 5),
        target_player=3,
        contributed=True,
        pot=13.0,
        bet_size=2.0,
    )
    components = 2
    axis_widths = (len(hands), len(hands), len(hands), 1, len(hands), len(hands))
    offsets = np.asarray((0, 45, 90, 135, 136, 181), dtype=np.int32)
    total = sum(axis_widths)
    unary = np.empty((components, total), dtype=np.float64)
    factors = np.empty_like(unary)
    for component in range(components):
        for seat, width in enumerate(axis_widths):
            for hand in range(width):
                position = int(offsets[seat]) + hand
                unary[component, position] = (
                    ((component + 2) * (seat + 3) * (hand + 5)) % 19 + 1
                ) / 23.0
                factors[component, position] = (
                    ((component + 3) * (seat + 5) + hand * 2) % 13 + 2
                ) / 17.0
                if seat != 3 and (seat * 11 + hand * 3 + component) % 37 == 0:
                    unary[component, position] = 0.0
    mixture = np.asarray((0.37, 0.63), dtype=np.float64)

    query_masks = []
    query_indices = []
    query_pairings = _pairings(QUERY_CARDS, 2)
    for occupancy_rank in range(comb(cards, QUERY_CARDS)):
        occupancy = colex_unrank(occupancy_rank, cards, QUERY_CARDS)
        mask = _mask(occupancy)
        for pairing in query_pairings:
            first = tuple(sorted((occupancy[pairing[0]], occupancy[pairing[1]])))
            second = tuple(sorted((occupancy[pairing[2]], occupancy[pairing[3]])))
            query_masks.append(mask)
            query_indices.append((hand_id[first], hand_id[second]))

    return FrozenQuotientFixture(
        available_cards=cards,
        hands=hands,
        automaton=automaton,
        unary_weights=_readonly(unary, np.float64),
        mode_factors=_readonly(factors, np.float64),
        mixture_weights=_readonly(mixture, np.float64),
        pair_to_hand=_readonly(pair_to_hand, np.int32),
        source_pair_positions=_readonly(_pairings(SOURCE_CARDS, 3), np.int8),
        query_masks=_readonly(query_masks, np.uint64),
        query_hand_indices=_readonly(query_indices, np.int32),
        unary_offsets=_readonly(offsets, np.int32),
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

__device__ __forceinline__ unsigned long long unrank_mask(long long rank, int n, int k) {
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

__device__ __forceinline__ long long rank_mask(unsigned long long mask, int n) {
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

__device__ __forceinline__ void unrank_six(long long rank, int n, int *cards) {
    int upper = n - 1;
    for (int i = 6; i >= 1; --i) {
        int card = upper;
        while (choose_ll(card, i) > rank) --card;
        cards[i - 1] = card;
        rank -= choose_ll(card, i);
        upper = card - 1;
    }
}

extern "C" __global__ void source_coefficients(
    double *table, long long source_offset, int width, long long source_rows,
    int n, int hand_width, int components, int source_rank,
    const signed char *pairings, const int *pair_to_hand,
    const double *unary, const double *factors, int unary_total,
    const int *unary_offsets, const int *transition0,
    const int *transition1, const int *transition2, int drop_source_factor
) {
    long long row = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (row >= source_rows) return;
    double *output = table + (source_offset + row) * width;
    for (int feature = 0; feature < width; ++feature) output[feature] = 0.0;
    int cards[6];
    unrank_six(row, n, cards);
    for (int pairing = 0; pairing < 90; ++pairing) {
        const signed char *positions = pairings + pairing * 6;
        int h0 = pair_to_hand[cards[(int)positions[0]] * n + cards[(int)positions[1]]];
        int h1 = pair_to_hand[cards[(int)positions[2]] * n + cards[(int)positions[3]]];
        int h2 = pair_to_hand[cards[(int)positions[4]] * n + cards[(int)positions[5]]];
        int state0 = transition0[h0];
        int state1 = transition1[state0 * hand_width + h1];
        int state2 = transition2[state1 * hand_width + h2];
        for (int component = 0; component < components; ++component) {
            long long base = (long long)component * unary_total;
            double weight = 1.0;
            int hands[3] = {h0, h1, h2};
            for (int seat = 0; seat < 3; ++seat) {
                int index = unary_offsets[seat] + hands[seat];
                weight *= unary[base + index];
                if (!(drop_source_factor && seat == 1)) weight *= factors[base + index];
            }
            int feature_base = component * (source_rank + 1);
            output[feature_base + state2] += weight;
            output[feature_base + source_rank] += weight;
        }
    }
}

extern "C" __global__ void zeta_level(
    double *table, long long current_offset, long long next_offset,
    long long rows, int n, int level, int source_cards, int width,
    int divisor_delta
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = rows * width;
    if (linear >= total) return;
    long long row = linear / width;
    int feature = (int)(linear - row * width);
    unsigned long long mask = unrank_mask(row, n, level);
    double value = 0.0;
    for (int card = 0; card < n; ++card) {
        unsigned long long bit = 1ULL << card;
        if (!(mask & bit)) {
            long long next_rank = rank_mask(mask | bit, n);
            value += table[(next_offset + next_rank) * width + feature];
        }
    }
    int divisor = source_cards - level + divisor_delta;
    table[(current_offset + row) * width + feature] = value / (double)divisor;
}

extern "C" __global__ void signed_targets(
    const double *table, const long long *offsets, int source_cards,
    const unsigned long long *target_masks, int implicit_targets,
    int target_cards, long long target_rows, int n, int width,
    int reverse_sign, double *output
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = target_rows * width;
    if (linear >= total) return;
    long long row = linear / width;
    int feature = (int)(linear - row * width);
    unsigned long long mask = implicit_targets
        ? unrank_mask(row, n, target_cards)
        : target_masks[row];
    unsigned long long subset = mask;
    double value = 0.0;
    while (true) {
        int cards = __popcll(subset);
        if (cards <= source_cards) {
            long long rank = rank_mask(subset, n);
            int negative = cards & 1;
            if (reverse_sign) negative = !negative;
            double term = table[(offsets[cards] + rank) * width + feature];
            value += negative ? -term : term;
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    output[row * width + feature] = value;
}

extern "C" __global__ void aggregate_query_labels(
    const double *records, long long occupancies, int labels, int width,
    int skip_last_label, double *output
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = occupancies * width;
    if (linear >= total) return;
    long long occupancy = linear / width;
    int feature = (int)(linear - occupancy * width);
    int stop = labels - (skip_last_label ? 1 : 0);
    double value = 0.0;
    for (int label = 0; label < stop; ++label)
        value += records[(occupancy * labels + label) * width + feature];
    output[occupancy * width + feature] = value;
}

extern "C" __global__ void fold_query(
    const double *compatible, long long records, int source_rank,
    int components, const int *query_hands, const double *unary,
    const double *factors, int unary_total, const int *unary_offsets,
    const double *mixture, const int *transition3, const int *transition4,
    const double *terminal, int hand_width, double sunk,
    int duplicate_sunk, double *numerator, double *reach
) {
    long long row = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (row >= records) return;
    int h4 = query_hands[row * 2];
    int h5 = query_hands[row * 2 + 1];
    double numerator_value = 0.0;
    double reach_value = 0.0;
    for (int component = 0; component < components; ++component) {
        long long base = (long long)component * unary_total;
        int hero_index = unary_offsets[3];
        int fourth_index = unary_offsets[4] + h4;
        int fifth_index = unary_offsets[5] + h5;
        double query_weight = mixture[component];
        query_weight *= unary[base + hero_index] * factors[base + hero_index];
        query_weight *= unary[base + fourth_index] * factors[base + fourth_index];
        query_weight *= unary[base + fifth_index] * factors[base + fifth_index];
        int feature_base = component * (source_rank + 1);
        double compatible_reach = compatible[row * components * (source_rank + 1)
                                               + feature_base + source_rank];
        double winner_value = 0.0;
        for (int state = 0; state < source_rank; ++state) {
            int state3 = transition3[state];
            int state4 = transition4[state3 * hand_width + h4];
            double winner = terminal[state4 * hand_width + h5];
            winner_value += compatible[row * components * (source_rank + 1)
                                       + feature_base + state] * winner;
        }
        double sunk_term = sunk * compatible_reach;
        if (duplicate_sunk) sunk_term *= 2.0;
        numerator_value += query_weight * (winner_value + sunk_term);
        reach_value += query_weight * compatible_reach;
    }
    numerator[row] = numerator_value;
    reach[row] = reach_value;
}
"""


_KERNEL_NAMES = (
    "source_coefficients",
    "zeta_level",
    "signed_targets",
    "aggregate_query_labels",
    "fold_query",
)
_KERNEL_CACHE: dict[int, Mapping[str, object]] = {}


def _kernels(cp) -> Mapping[str, object]:
    device = int(cp.cuda.Device().id)
    cached = _KERNEL_CACHE.get(device)
    if cached is not None:
        return cached
    module = cp.RawModule(
        code=_CUDA_SOURCE,
        options=("--std=c++14",),
        name_expressions=_KERNEL_NAMES,
    )
    result = {name: module.get_function(name) for name in _KERNEL_NAMES}
    _KERNEL_CACHE[device] = result
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


def _fill_recurrence(
    cp,
    kernels: Mapping[str, object],
    table,
    *,
    available_cards: int,
    source_cards: int,
    feature_width: int,
    divisor_delta: int = 0,
) -> float:
    offsets = cardinality_offsets(available_cards, source_cards)

    def operation() -> None:
        for level in range(source_cards - 1, -1, -1):
            rows = comb(available_cards, level)
            _launch(
                kernels["zeta_level"],
                rows * feature_width,
                (
                    table,
                    np.int64(offsets[level]),
                    np.int64(offsets[level + 1]),
                    np.int64(rows),
                    np.int32(available_cards),
                    np.int32(level),
                    np.int32(source_cards),
                    np.int32(feature_width),
                    np.int32(divisor_delta),
                ),
            )

    return _cuda_timed(cp, operation)


def _signed_targets(
    cp,
    kernels: Mapping[str, object],
    table,
    *,
    available_cards: int,
    source_cards: int,
    target_cards: int,
    feature_width: int,
    target_masks: np.ndarray | None,
    target_rows: int,
    reverse_sign: bool = False,
):
    offsets = cp.asarray(cardinality_offsets(available_cards, source_cards), dtype=cp.int64)
    if target_masks is None:
        device_masks = cp.zeros(1, dtype=cp.uint64)
        implicit = 1
    else:
        device_masks = cp.asarray(target_masks, dtype=cp.uint64)
        implicit = 0
    output = cp.empty((target_rows, feature_width), dtype=cp.float64)

    def operation() -> None:
        _launch(
            kernels["signed_targets"],
            target_rows * feature_width,
            (
                table,
                offsets,
                np.int32(source_cards),
                device_masks,
                np.int32(implicit),
                np.int32(target_cards),
                np.int64(target_rows),
                np.int32(available_cards),
                np.int32(feature_width),
                np.int32(int(reverse_sign)),
                output,
            ),
        )

    elapsed = _cuda_timed(cp, operation)
    return output, elapsed


def _source_coefficients_exact(fixture: FrozenQuotientFixture) -> tuple[tuple[Fraction, ...], ...]:
    rows = []
    transitions = fixture.automaton.transitions
    rank = fixture.source_rank
    width = fixture.feature_width
    for occupancy_rank in range(comb(fixture.available_cards, SOURCE_CARDS)):
        cards = colex_unrank(occupancy_rank, fixture.available_cards, SOURCE_CARDS)
        values = [Fraction(0) for _ in range(width)]
        for pairing in fixture.source_pair_positions:
            hands = []
            for seat in range(3):
                supplied = tuple(
                    sorted((cards[int(pairing[2 * seat])], cards[int(pairing[2 * seat + 1])]))
                )
                hands.append(int(fixture.pair_to_hand[supplied]))
            state0 = int(transitions[0][0, hands[0]])
            state1 = int(transitions[1][state0, hands[1]])
            state2 = int(transitions[2][state1, hands[2]])
            for component in range(fixture.components):
                weight = Fraction(1)
                for seat, hand in enumerate(hands):
                    index = int(fixture.unary_offsets[seat]) + hand
                    weight *= Fraction.from_float(float(fixture.unary_weights[component, index]))
                    weight *= Fraction.from_float(float(fixture.mode_factors[component, index]))
                base = component * (rank + 1)
                values[base + state2] += weight
                values[base + rank] += weight
        rows.append(tuple(values))
    return tuple(rows)


def _exact_compatible(
    fixture: FrozenQuotientFixture,
    source_rows: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    source_masks = tuple(
        _mask(colex_unrank(rank, fixture.available_cards, SOURCE_CARDS))
        for rank in range(comb(fixture.available_cards, SOURCE_CARDS))
    )
    topology = OccupiedCardQuotientTopology.compile(
        source_seats=(0, 1, 2),
        query_seats=(3, 4, 5),
        open_seats=(3, 4, 5),
        source_record_masks=source_masks,
        query_record_masks=tuple(int(mask) for mask in fixture.query_masks),
    )
    coefficients = ExactQuotientCoefficients(masks=source_masks, rows=source_rows)
    return topology.apply_coefficients_exact(coefficients)[0]


def _exact_fold(
    fixture: FrozenQuotientFixture,
    compatible: tuple[tuple[Fraction, ...], ...],
) -> tuple[np.ndarray, np.ndarray]:
    numerator = []
    reach = []
    rank = fixture.source_rank
    transitions = fixture.automaton.transitions
    terminal = fixture.automaton.terminal_winner_values
    for record, (h4, h5) in enumerate(fixture.query_hand_indices):
        numerator_value = Fraction(0)
        reach_value = Fraction(0)
        for component in range(fixture.components):
            query_weight = Fraction.from_float(float(fixture.mixture_weights[component]))
            for seat, hand in ((3, 0), (4, int(h4)), (5, int(h5))):
                index = int(fixture.unary_offsets[seat]) + hand
                query_weight *= Fraction.from_float(float(fixture.unary_weights[component, index]))
                query_weight *= Fraction.from_float(float(fixture.mode_factors[component, index]))
            base = component * (rank + 1)
            compatible_reach = compatible[record][base + rank]
            winner = Fraction(0)
            for state in range(rank):
                state3 = int(transitions[3][state, 0])
                state4 = int(transitions[4][state3, int(h4)])
                payoff = Fraction.from_float(float(terminal[state4, int(h5)]))
                winner += compatible[record][base + state] * payoff
            sunk = Fraction.from_float(float(fixture.automaton.sunk_value))
            numerator_value += query_weight * (winner + sunk * compatible_reach)
            reach_value += query_weight * compatible_reach
        numerator.append(float(numerator_value))
        reach.append(float(reach_value))
    return np.asarray(numerator, dtype=np.float64), np.asarray(reach, dtype=np.float64)


def _maximum_errors(actual: np.ndarray, expected: np.ndarray) -> tuple[float, float]:
    absolute = np.abs(actual - expected)
    maximum_absolute = float(np.max(absolute, initial=0.0))
    relative = absolute / np.maximum(1.0, np.abs(expected))
    return maximum_absolute, float(np.max(relative, initial=0.0))


def _digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for values in arrays:
        contiguous = np.ascontiguousarray(values)
        digest.update(repr((contiguous.shape, contiguous.dtype.str)).encode("ascii"))
        digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class _StructuredGpuRun:
    source_coefficients: np.ndarray
    compatible: np.ndarray
    numerator: np.ndarray
    reach: np.ndarray
    table: object
    cp: object
    kernels: Mapping[str, object]
    timings_ms: Mapping[str, float]
    allocation: RecurrenceAllocation


def _run_structured_gpu(
    fixture: FrozenQuotientFixture,
    *,
    drop_source_factor: bool = False,
    divisor_delta: int = 0,
    reverse_sign: bool = False,
    duplicate_sunk: bool = False,
) -> _StructuredGpuRun:
    if fixture.available_cards != BOUNDED_AVAILABLE_CARDS:
        raise ValueError("GPU quotient keystone is restricted to ten cards")
    target_records = len(fixture.query_masks)
    pure = bounded_device_allocation(
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=fixture.feature_width,
        target_records=target_records,
        target_chunk_records=target_records,
        persistent_bytes=fixture.automaton.numeric_bytes,
    )
    cp = _cupy_module()
    free_bytes, _ = cp.cuda.runtime.memGetInfo()
    allocation = bounded_device_allocation(
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=fixture.feature_width,
        target_records=target_records,
        target_chunk_records=target_records,
        persistent_bytes=fixture.automaton.numeric_bytes,
        live_free_bytes=int(free_bytes),
    )
    if allocation.requested_device_bytes != pure.requested_device_bytes:
        raise AssertionError("live admission changed the pure byte request")
    kernels = _kernels(cp)
    offsets = cardinality_offsets(fixture.available_cards, SOURCE_CARDS)
    table = cp.empty((allocation.level_rows, fixture.feature_width), dtype=cp.float64)
    pairings = cp.asarray(fixture.source_pair_positions, dtype=cp.int8)
    pair_to_hand = cp.asarray(fixture.pair_to_hand, dtype=cp.int32)
    unary = cp.asarray(fixture.unary_weights, dtype=cp.float64)
    factors = cp.asarray(fixture.mode_factors, dtype=cp.float64)
    unary_offsets = cp.asarray(fixture.unary_offsets, dtype=cp.int32)
    transitions = tuple(
        cp.asarray(value, dtype=cp.int32)
        for value in fixture.automaton.transitions
    )
    terminal = cp.asarray(fixture.automaton.terminal_winner_values, dtype=cp.float64)
    mixture = cp.asarray(fixture.mixture_weights, dtype=cp.float64)
    query_hands = cp.asarray(fixture.query_hand_indices, dtype=cp.int32)
    source_rows = comb(fixture.available_cards, SOURCE_CARDS)

    def source_operation() -> None:
        _launch(
            kernels["source_coefficients"],
            source_rows,
            (
                table,
                np.int64(offsets[SOURCE_CARDS]),
                np.int32(fixture.feature_width),
                np.int64(source_rows),
                np.int32(fixture.available_cards),
                np.int32(len(fixture.hands)),
                np.int32(fixture.components),
                np.int32(fixture.source_rank),
                pairings,
                pair_to_hand,
                unary,
                factors,
                np.int32(fixture.unary_weights.shape[1]),
                unary_offsets,
                transitions[0],
                transitions[1],
                transitions[2],
                np.int32(int(drop_source_factor)),
            ),
        )

    source_ms = _cuda_timed(cp, source_operation)
    recurrence_ms = _fill_recurrence(
        cp,
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        feature_width=fixture.feature_width,
        divisor_delta=divisor_delta,
    )
    compatible_device, query_ms = _signed_targets(
        cp,
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=fixture.feature_width,
        target_masks=fixture.query_masks,
        target_rows=target_records,
        reverse_sign=reverse_sign,
    )
    numerator_device = cp.empty(target_records, dtype=cp.float64)
    reach_device = cp.empty(target_records, dtype=cp.float64)

    def fold_operation() -> None:
        _launch(
            kernels["fold_query"],
            target_records,
            (
                compatible_device,
                np.int64(target_records),
                np.int32(fixture.source_rank),
                np.int32(fixture.components),
                query_hands,
                unary,
                factors,
                np.int32(fixture.unary_weights.shape[1]),
                unary_offsets,
                mixture,
                transitions[3],
                transitions[4],
                terminal,
                np.int32(len(fixture.hands)),
                np.float64(fixture.automaton.sunk_value),
                np.int32(int(duplicate_sunk)),
                numerator_device,
                reach_device,
            ),
        )

    fold_ms = _cuda_timed(cp, fold_operation)
    source_coefficients = cp.asnumpy(
        table[offsets[SOURCE_CARDS] : offsets[SOURCE_CARDS] + source_rows]
    )
    compatible = cp.asnumpy(compatible_device)
    numerator = cp.asnumpy(numerator_device)
    reach = cp.asnumpy(reach_device)
    return _StructuredGpuRun(
        source_coefficients=source_coefficients,
        compatible=compatible,
        numerator=numerator,
        reach=reach,
        table=table,
        cp=cp,
        kernels=kernels,
        timings_ms={
            "source_coefficients": source_ms,
            "forward_recurrence": recurrence_ms,
            "signed_query": query_ms,
            "affine_fold": fold_ms,
            "device_phases": source_ms + recurrence_ms + query_ms + fold_ms,
        },
        allocation=allocation,
    )


def _query_only_gpu(
    run: _StructuredGpuRun,
    fixture: FrozenQuotientFixture,
) -> tuple[np.ndarray, np.ndarray, Mapping[str, float]]:
    cp = run.cp
    kernels = run.kernels
    records = len(fixture.query_masks)
    compatible, query_ms = _signed_targets(
        cp,
        kernels,
        run.table,
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=fixture.feature_width,
        target_masks=fixture.query_masks,
        target_rows=records,
    )
    unary = cp.asarray(fixture.unary_weights, dtype=cp.float64)
    factors = cp.asarray(fixture.mode_factors, dtype=cp.float64)
    unary_offsets = cp.asarray(fixture.unary_offsets, dtype=cp.int32)
    mixture = cp.asarray(fixture.mixture_weights, dtype=cp.float64)
    query_hands = cp.asarray(fixture.query_hand_indices, dtype=cp.int32)
    transitions = tuple(
        cp.asarray(value, dtype=cp.int32)
        for value in fixture.automaton.transitions
    )
    terminal = cp.asarray(fixture.automaton.terminal_winner_values, dtype=cp.float64)
    numerator = cp.empty(records, dtype=cp.float64)
    reach = cp.empty(records, dtype=cp.float64)

    def operation() -> None:
        _launch(
            kernels["fold_query"],
            records,
            (
                compatible,
                np.int64(records),
                np.int32(fixture.source_rank),
                np.int32(fixture.components),
                query_hands,
                unary,
                factors,
                np.int32(fixture.unary_weights.shape[1]),
                unary_offsets,
                mixture,
                transitions[3],
                transitions[4],
                terminal,
                np.int32(len(fixture.hands)),
                np.float64(fixture.automaton.sunk_value),
                np.int32(0),
                numerator,
                reach,
            ),
        )

    fold_ms = _cuda_timed(cp, operation)
    return (
        cp.asnumpy(numerator),
        cp.asnumpy(reach),
        {
            "source_coefficients": 0.0,
            "forward_recurrence": 0.0,
            "signed_query": query_ms,
            "affine_fold": fold_ms,
        },
    )


def _generic_forward_gpu(
    cp,
    kernels: Mapping[str, object],
    source_rows: np.ndarray,
    target_masks: np.ndarray,
    *,
    divisor_delta: int = 0,
    reverse_sign: bool = False,
) -> tuple[np.ndarray, Mapping[str, float]]:
    width = int(source_rows.shape[1])
    allocation = bounded_device_allocation(
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=width,
        target_records=len(target_masks),
        target_chunk_records=len(target_masks),
    )
    table = cp.zeros((allocation.level_rows, width), dtype=cp.float64)
    offsets = cardinality_offsets(BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS)
    table[
        offsets[SOURCE_CARDS] : offsets[SOURCE_CARDS] + len(source_rows)
    ] = cp.asarray(source_rows)
    recurrence_ms = _fill_recurrence(
        cp,
        kernels,
        table,
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=SOURCE_CARDS,
        feature_width=width,
        divisor_delta=divisor_delta,
    )
    result, query_ms = _signed_targets(
        cp,
        kernels,
        table,
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=SOURCE_CARDS,
        target_cards=QUERY_CARDS,
        feature_width=width,
        target_masks=target_masks,
        target_rows=len(target_masks),
        reverse_sign=reverse_sign,
    )
    return cp.asnumpy(result), {"recurrence": recurrence_ms, "signed_query": query_ms}


def _generic_adjoint_gpu(
    cp,
    kernels: Mapping[str, object],
    query_rows: np.ndarray,
    *,
    skip_last_label: bool = False,
) -> tuple[np.ndarray, np.ndarray, Mapping[str, float]]:
    width = int(query_rows.shape[1])
    occupancies = comb(BOUNDED_AVAILABLE_CARDS, QUERY_CARDS)
    source_occupancies = comb(BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS)
    allocation = bounded_device_allocation(
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=QUERY_CARDS,
        target_cards=SOURCE_CARDS,
        feature_width=width,
        target_records=source_occupancies,
        target_chunk_records=source_occupancies,
    )
    records = cp.asarray(query_rows, dtype=cp.float64)
    aggregated = cp.empty((occupancies, width), dtype=cp.float64)

    def aggregate_operation() -> None:
        _launch(
            kernels["aggregate_query_labels"],
            occupancies * width,
            (
                records,
                np.int64(occupancies),
                np.int32(QUERY_PAIRINGS_PER_OCCUPANCY),
                np.int32(width),
                np.int32(int(skip_last_label)),
                aggregated,
            ),
        )

    aggregation_ms = _cuda_timed(cp, aggregate_operation)
    table = cp.zeros((allocation.level_rows, width), dtype=cp.float64)
    offsets = cardinality_offsets(BOUNDED_AVAILABLE_CARDS, QUERY_CARDS)
    table[offsets[QUERY_CARDS] : offsets[QUERY_CARDS] + occupancies] = aggregated
    recurrence_ms = _fill_recurrence(
        cp,
        kernels,
        table,
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=QUERY_CARDS,
        feature_width=width,
    )
    unique, signed_ms = _signed_targets(
        cp,
        kernels,
        table,
        available_cards=BOUNDED_AVAILABLE_CARDS,
        source_cards=QUERY_CARDS,
        target_cards=SOURCE_CARDS,
        feature_width=width,
        target_masks=None,
        target_rows=source_occupancies,
    )
    expanded = cp.repeat(unique, SOURCE_PAIRINGS_PER_OCCUPANCY, axis=0)
    cp.cuda.get_current_stream().synchronize()
    return (
        cp.asnumpy(unique),
        cp.asnumpy(expanded),
        {
            "query_aggregation": aggregation_ms,
            "adjoint_recurrence": recurrence_ms,
            "signed_source": signed_ms,
        },
    )


def _exact_generic(
    source_rows: np.ndarray,
    query_masks: np.ndarray,
) -> tuple[tuple[tuple[Fraction, ...], ...], OccupiedCardQuotientTopology]:
    source_masks = tuple(
        _mask(colex_unrank(rank, BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS))
        for rank in range(comb(BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS))
    )
    topology = OccupiedCardQuotientTopology.compile(
        source_seats=(0, 1, 2),
        query_seats=(3, 4, 5),
        open_seats=(3, 4, 5),
        source_record_masks=source_masks,
        query_record_masks=tuple(int(mask) for mask in query_masks),
    )
    exact_rows = tuple(
        tuple(Fraction.from_float(float(value)) for value in row) for row in source_rows
    )
    coefficients = ExactQuotientCoefficients(masks=source_masks, rows=exact_rows)
    return topology.apply_coefficients_exact(coefficients)[0], topology


def _current_stack_value(fixture: FrozenQuotientFixture) -> tuple[float, float]:
    combined_unaries = []
    axis_widths = (45, 45, 45, 1, 45, 45)
    for seat, width in enumerate(axis_widths):
        start = int(fixture.unary_offsets[seat])
        combined_unaries.append(
            fixture.unary_weights[:, start : start + width]
            * fixture.mode_factors[:, start : start + width]
        )
    belief = FactorizedCardBelief(
        hands_by_player=(
            fixture.hands,
            fixture.hands,
            fixture.hands,
            ((10, 11),),
            fixture.hands,
            fixture.hands,
        ),
        mixture_weights=fixture.mixture_weights,
        unary_weights=tuple(combined_unaries),
    )
    topology = FactorTTTopology.compile(belief, split_index=3)
    workspace = FactorTTBeliefWorkspace.compile(topology, belief, query_chunk_records=512)
    contraction = workspace.contract(fixture.automaton.to_tensor_train())
    return float(contraction.expectation), float(contraction.partition)


@dataclass(frozen=True, slots=True)
class GpuQuotientKeystoneReport:
    available_cards: int
    source_occupancies: int
    labeled_source_pairings: int
    query_occupancies: int
    labeled_query_records: int
    source_rank: int
    feature_width: int
    maximum_errors: Mapping[str, float]
    work: Mapping[str, int]
    timings_ms: Mapping[str, float]
    device: Mapping[str, object]
    allocation: RecurrenceAllocation
    digests: Mapping[str, str]
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return bool(self.gates) and all(self.gates.values())


def run_frozen_gpu_quotient_keystone() -> GpuQuotientKeystoneReport:
    """Run ADR-0371's complete bounded natural and adversarial controls."""

    host_start = perf_counter()
    fixture = build_frozen_quotient_fixture()
    exact_source = _source_coefficients_exact(fixture)
    exact_compatible = _exact_compatible(fixture, exact_source)
    expected_source = np.asarray([[float(value) for value in row] for row in exact_source])
    expected_compatible = np.asarray([[float(value) for value in row] for row in exact_compatible])
    expected_numerator, expected_reach = _exact_fold(fixture, exact_compatible)

    run = _run_structured_gpu(fixture)
    warm = _run_structured_gpu(fixture)
    source_abs, source_rel = _maximum_errors(run.source_coefficients, expected_source)
    forward_abs, forward_rel = _maximum_errors(run.compatible, expected_compatible)
    numerator_abs, numerator_rel = _maximum_errors(run.numerator, expected_numerator)
    reach_abs, reach_rel = _maximum_errors(run.reach, expected_reach)

    current_value, current_partition = _current_stack_value(fixture)
    gpu_value = float(np.sum(run.numerator) / np.sum(run.reach))
    current_value_error = abs(gpu_value - current_value)

    source_rows = np.asarray(
        [
            [(((row + 3) * (feature + 5)) % 23 - 11) / 1000.0 for feature in range(3)]
            for row in range(comb(BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS))
        ],
        dtype=np.float64,
    )
    query_covectors = np.asarray(
        [
            [(((row + 7) * (feature + 2)) % 19 - 9) / 1000.0 for feature in range(3)]
            for row in range(len(fixture.query_masks))
        ],
        dtype=np.float64,
    )
    forward, forward_timing = _generic_forward_gpu(
        run.cp, run.kernels, source_rows, fixture.query_masks
    )
    exact_forward, generic_topology = _exact_generic(source_rows, fixture.query_masks)
    expected_forward = np.asarray([[float(value) for value in row] for row in exact_forward])
    generic_forward_abs, generic_forward_rel = _maximum_errors(forward, expected_forward)
    adjoint_unique, adjoint_expanded, adjoint_timing = _generic_adjoint_gpu(
        run.cp, run.kernels, query_covectors
    )
    exact_query = tuple(
        tuple(Fraction.from_float(float(value)) for value in row) for row in query_covectors
    )
    exact_adjoint_unique = generic_topology.apply_adjoint_exact(exact_query)
    expected_adjoint_unique = np.asarray(
        [[float(value) for value in row] for row in exact_adjoint_unique]
    )
    expected_adjoint_expanded = np.repeat(
        expected_adjoint_unique,
        SOURCE_PAIRINGS_PER_OCCUPANCY,
        axis=0,
    )
    adjoint_abs, adjoint_rel = _maximum_errors(adjoint_unique, expected_adjoint_unique)
    expanded_abs, _ = _maximum_errors(adjoint_expanded, expected_adjoint_expanded)
    forward_dot = float(np.sum(forward * query_covectors))
    transpose_dot = float(np.sum(source_rows * adjoint_unique))
    dot_error = abs(forward_dot - transpose_dot)

    refreshed_unary = fixture.unary_weights.copy()
    start = int(fixture.unary_offsets[1])
    refreshed_unary[:, start : start + len(fixture.hands)] *= np.asarray((1.07, 0.91))[:, None]
    refreshed_fixture = replace(fixture, unary_weights=np.ascontiguousarray(refreshed_unary))
    refreshed = _run_structured_gpu(refreshed_fixture)
    refreshed_exact_source = _source_coefficients_exact(refreshed_fixture)
    refreshed_expected = np.asarray(
        [[float(value) for value in row] for row in refreshed_exact_source]
    )
    refresh_abs, refresh_rel = _maximum_errors(refreshed.source_coefficients, refreshed_expected)

    query_unary = fixture.unary_weights.copy()
    qstart = int(fixture.unary_offsets[4])
    query_unary[:, qstart : qstart + len(fixture.hands)] *= np.asarray((0.93, 1.04))[:, None]
    query_fixture = replace(fixture, unary_weights=np.ascontiguousarray(query_unary))
    query_num, query_reach, query_timings = _query_only_gpu(run, query_fixture)
    query_exact_num, query_exact_reach = _exact_fold(query_fixture, exact_compatible)
    query_num_abs, query_num_rel = _maximum_errors(query_num, query_exact_num)
    query_reach_abs, query_reach_rel = _maximum_errors(query_reach, query_exact_reach)

    permuted_unary = fixture.unary_weights.copy()
    permuted_factors = fixture.mode_factors.copy()
    source_slices = [
        slice(
            int(fixture.unary_offsets[seat]),
            int(fixture.unary_offsets[seat]) + 45,
        )
        for seat in range(3)
    ]
    for destination, origin in enumerate((2, 0, 1)):
        permuted_unary[:, source_slices[destination]] = fixture.unary_weights[
            :, source_slices[origin]
        ]
        permuted_factors[:, source_slices[destination]] = fixture.mode_factors[
            :, source_slices[origin]
        ]
    permuted_fixture = replace(
        fixture,
        unary_weights=np.ascontiguousarray(permuted_unary),
        mode_factors=np.ascontiguousarray(permuted_factors),
    )
    permuted = _run_structured_gpu(permuted_fixture)
    permutation_abs, permutation_rel = _maximum_errors(
        permuted.source_coefficients, run.source_coefficients
    )

    wrong_divisor, _ = _generic_forward_gpu(
        run.cp, run.kernels, source_rows, fixture.query_masks, divisor_delta=1
    )
    wrong_sign, _ = _generic_forward_gpu(
        run.cp, run.kernels, source_rows, fixture.query_masks, reverse_sign=True
    )
    _, skipped_aggregate, _ = _generic_adjoint_gpu(
        run.cp, run.kernels, query_covectors, skip_last_label=True
    )
    dropped_factor = _run_structured_gpu(fixture, drop_source_factor=True)
    duplicate_sunk = _run_structured_gpu(fixture, duplicate_sunk=True)

    rank_roundtrip = all(
        colex_rank(colex_unrank(rank, BOUNDED_AVAILABLE_CARDS, width)) == rank
        for width in range(SOURCE_CARDS + 1)
        for rank in range(comb(BOUNDED_AVAILABLE_CARDS, width))
    )
    recurrence_work = cardinality_recurrence_work(
        BOUNDED_AVAILABLE_CARDS, SOURCE_CARDS, fixture.feature_width
    )
    adjoint_work = cardinality_recurrence_work(
        BOUNDED_AVAILABLE_CARDS, QUERY_CARDS, 3
    )
    maximum_relative = max(
        source_rel,
        forward_rel,
        numerator_rel,
        reach_rel,
        generic_forward_rel,
        adjoint_rel,
        refresh_rel,
        query_num_rel,
        query_reach_rel,
        permutation_rel,
    )
    maximum_errors = {
        "source_coefficient_absolute": source_abs,
        "forward_row_absolute": max(forward_abs, generic_forward_abs),
        "adjoint_row_absolute": max(adjoint_abs, expanded_abs),
        "affine_fold_absolute": max(numerator_abs, reach_abs, query_num_abs, query_reach_abs),
        "dot_product_absolute": dot_error,
        "current_stack_normalized_value_absolute": current_value_error,
        "source_refresh_absolute": refresh_abs,
        "source_permutation_absolute": permutation_abs,
        "scale_normalized_relative": maximum_relative,
    }
    work = {
        "source_pairing_visits": comb(10, 6) * SOURCE_PAIRINGS_PER_OCCUPANCY,
        "source_state_reach_accumulations": (
            comb(10, 6)
            * SOURCE_PAIRINGS_PER_OCCUPANCY
            * fixture.components
            * 2
        ),
        "source_coefficient_zero_writes": comb(10, 6) * fixture.feature_width,
        "forward_recurrence_vector_edges": recurrence_work.vector_edges,
        "forward_recurrence_scalar_additions": recurrence_work.scalar_additions,
        "signed_query_terms": len(fixture.query_masks) * 16,
        "signed_query_scalar_additions": (
            len(fixture.query_masks) * 16 * fixture.feature_width
        ),
        "query_automaton_state_folds": (
            len(fixture.query_masks) * fixture.components * fixture.source_rank
        ),
        "source_refresh_pairing_visits": comb(10, 6) * SOURCE_PAIRINGS_PER_OCCUPANCY,
        "source_refresh_recurrence_scalar_additions": recurrence_work.scalar_additions,
        "query_only_source_pairing_visits": 0,
        "query_only_recurrence_scalar_additions": 0,
        "adjoint_query_aggregation_additions": comb(10, 4) * (QUERY_PAIRINGS_PER_OCCUPANCY - 1) * 3,
        "adjoint_recurrence_scalar_additions": adjoint_work.scalar_additions,
        "adjoint_signed_source_additions": comb(10, 6) * 57 * 3,
        "adjoint_label_writes": comb(10, 6) * SOURCE_PAIRINGS_PER_OCCUPANCY * 3,
    }
    timings = dict(run.timings_ms)
    timings.update(
        {f"warm_{key}": value for key, value in warm.timings_ms.items()}
    )
    timings.update(
        {
            f"source_refresh_{key}": value
            for key, value in refreshed.timings_ms.items()
        }
    )
    timings.update({f"generic_forward_{key}": value for key, value in forward_timing.items()})
    timings.update(adjoint_timing)
    timings.update({f"query_only_{key}": value for key, value in query_timings.items()})
    timings["host_end_to_end"] = (perf_counter() - host_start) * 1000.0
    device_properties = run.cp.cuda.runtime.getDeviceProperties(
        int(run.cp.cuda.Device().id)
    )
    device_name = device_properties["name"]
    if isinstance(device_name, bytes):
        device_name = device_name.decode("utf-8")
    device = {
        "name": str(device_name),
        "compute_capability": str(run.cp.cuda.Device().compute_capability),
        "cupy_version": str(run.cp.__version__),
        "cuda_runtime_version": int(run.cp.cuda.runtime.runtimeGetVersion()),
        "cuda_driver_version": int(run.cp.cuda.runtime.driverGetVersion()),
        "total_bytes": int(device_properties["totalGlobalMem"]),
    }
    gates = {
        "complete_geometry": (
            len(fixture.query_masks) == comb(10, 4) * 6
            and len(exact_source) == comb(10, 6)
            and fixture.source_pair_positions.shape == (90, 6)
        ),
        "colex_roundtrip": rank_roundtrip,
        "source_coefficients": source_abs <= MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR,
        "forward_rows": max(forward_abs, generic_forward_abs) <= MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR,
        "adjoint_rows": (
            max(adjoint_abs, expanded_abs) <= MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR
        ),
        "affine_fold": (
            max(numerator_abs, reach_abs, query_num_abs, query_reach_abs)
            <= MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR
        ),
        "dot_product": dot_error <= MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR,
        "relative_envelope": maximum_relative <= MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR,
        "current_stack": (
            current_value_error <= MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR
            and current_partition > 0.0
        ),
        "warm_byte_identity": (
            run.source_coefficients.tobytes() == warm.source_coefficients.tobytes()
            and run.compatible.tobytes() == warm.compatible.tobytes()
            and run.numerator.tobytes() == warm.numerator.tobytes()
            and run.reach.tobytes() == warm.reach.tobytes()
        ),
        "source_refresh": refresh_abs <= MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR,
        "refresh_work_equals_cold": (
            work["source_refresh_pairing_visits"] == work["source_pairing_visits"]
            and work["source_refresh_recurrence_scalar_additions"]
            == work["forward_recurrence_scalar_additions"]
        ),
        "query_only_reuses_source": (
            query_timings["source_coefficients"] == 0.0
            and query_timings["forward_recurrence"] == 0.0
        ),
        "source_seat_permutation": (
            permutation_abs <= MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR
        ),
        "wrong_divisor_detected": not np.allclose(
            wrong_divisor,
            expected_forward,
            rtol=0.0,
            atol=MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR,
        ),
        "wrong_sign_detected": not np.allclose(
            wrong_sign,
            expected_forward,
            rtol=0.0,
            atol=MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR,
        ),
        "adjoint_seam_detected": not np.allclose(
            skipped_aggregate,
            expected_adjoint_expanded,
            rtol=0.0,
            atol=MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR,
        ),
        "dropped_source_factor_detected": not np.allclose(
            dropped_factor.source_coefficients,
            expected_source,
            rtol=0.0,
            atol=MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR,
        ),
        "duplicate_sunk_detected": not np.allclose(
            duplicate_sunk.numerator,
            expected_numerator,
            rtol=0.0,
            atol=MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR,
        ),
        "fixed_allocation": (
            run.allocation.fixed_cap_pass
            and run.allocation.physical_reserve_pass
        ),
        "live_allocation": run.allocation.live_reserve_pass is True,
        "laboratory_hang_guard": timings["host_end_to_end"] <= LABORATORY_HANG_GUARD_MS,
    }
    return GpuQuotientKeystoneReport(
        available_cards=fixture.available_cards,
        source_occupancies=comb(10, 6),
        labeled_source_pairings=comb(10, 6) * 90,
        query_occupancies=comb(10, 4),
        labeled_query_records=len(fixture.query_masks),
        source_rank=fixture.source_rank,
        feature_width=fixture.feature_width,
        maximum_errors=maximum_errors,
        work=work,
        timings_ms=timings,
        device=device,
        allocation=run.allocation,
        digests={
            "source_coefficients": _digest(run.source_coefficients),
            "compatible": _digest(run.compatible),
            "affine_outputs": _digest(run.numerator, run.reach),
            "adjoint": _digest(adjoint_unique, adjoint_expanded),
        },
        gates=gates,
    )


__all__ = [
    "BOUNDED_AVAILABLE_CARDS",
    "CardinalityRecurrenceWork",
    "FIXED_DEVICE_NUMERIC_CAP_BYTES",
    "FIXED_DEVICE_RESERVE_BYTES",
    "FrozenQuotientFixture",
    "GpuQuotientKeystoneReport",
    "LABORATORY_HANG_GUARD_MS",
    "MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR",
    "MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR",
    "MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR",
    "MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR",
    "MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR",
    "MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR",
    "RecurrenceAllocation",
    "bounded_device_allocation",
    "build_frozen_quotient_fixture",
    "cardinality_offsets",
    "cardinality_recurrence_work",
    "colex_rank",
    "colex_unrank",
    "cupy_import_call_count",
    "recurrence_allocation",
    "run_frozen_gpu_quotient_keystone",
]
