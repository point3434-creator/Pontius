"""ADR-0391/0392 paired high/low bounded CUDA arithmetic successor.

Importing this module is device-free.  Its only device authority is the
complete 10- and 25-card bounded conformance campaign.  It deliberately has
no actual-context owner, reader, runner, or 45-card entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import gc
from hashlib import sha256
import json
import math
from math import comb
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from . import legal_river_quotient_cuda_consumer as _parent
from .gpu_occupied_card_quotient import cardinality_offsets, colex_rank, colex_unrank


_ROOT = Path(__file__).parents[2]
_CONFIG_V1 = (
    _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json"
)
_CONFIG_V2 = (
    _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json"
)
PREREGISTERED_CONFIG_V1_SHA256 = (
    "431846ffeb2064486f1768c4847a820d010d6bc8b39840f26a06c72f43e5256c"
)
PREREGISTERED_CONFIG_V2_SHA256 = (
    "58df9401ff34d18159e33e82db09efd13925abf95a7040fb39508ca8d99bd01f"
)

SOURCE_CARDS = 6
QUERY_CARDS = 4
QUERY_LABELS = 6
SOURCE_RANK = 175
TOTAL_FEATURE_WIDTH = 176
PHYSICAL_STRIDE_WIDTH = 128
REACH_GLOBAL_FEATURE = 175
LOGICAL_TILES = ((0, 64), (64, 128), (128, 176))
_BOUNDARY_FEATURES = (0, 1, 63, 64, 127, 128, 174, 175)
_POISON = np.float64(9.876543210123456e197)

ConsumerPopulationFixture = _parent.ConsumerPopulationFixture
PopulationGeometry = _parent.PopulationGeometry
CudaRuntimeIdentity = _parent.CudaRuntimeIdentity
compile_consumer_population_fixture = _parent.compile_consumer_population_fixture
population_geometry = _parent.population_geometry

_CUPY_IMPORT_CALLS = 0
_BOUNDED_EXECUTION_CALLS = 0


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"paired-tile provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load_config(path: Path, expected_hash: str, schema: str) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("paired-tile config path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("paired-tile config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != expected_hash:
        raise ValueError("paired-tile config differs from its ADR")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != schema:
        raise ValueError("paired-tile config schema differs")
    return parsed


def load_preregistered_compensated_tile_configs(
    v1_path: Path = _CONFIG_V1,
    v2_path: Path = _CONFIG_V2,
) -> tuple[dict[str, object], dict[str, object]]:
    return (
        _load_config(
            v1_path,
            PREREGISTERED_CONFIG_V1_SHA256,
            "legal-river-quotient-cuda-compensated-tiles-config-v1",
        ),
        _load_config(
            v2_path,
            PREREGISTERED_CONFIG_V2_SHA256,
            "legal-river-quotient-cuda-compensated-tiles-correction-v2",
        ),
    )


_V1_SOURCE_PATHS = MappingProxyType(
    {
        "adr0390": _ROOT
        / "docs/decisions/ADR-0390-retain-the-bounded-cuda-consumer-numerical-rejection.md",
        "parent_consumer_config": _ROOT
        / "experiments/configs/legal-river-quotient-cuda-consumer-v1.json",
        "parent_consumer_source": _ROOT
        / "src/pontius/legal_river_quotient_cuda_consumer.py",
        "parent_consumer_controls": _ROOT
        / "tests/test_legal_river_quotient_cuda_consumer.py",
        "consumer_capacity_source": _ROOT
        / "src/pontius/legal_river_quotient_consumer_capacity.py",
        "legal_river_bridge_config": _ROOT
        / "experiments/configs/legal-river-quotient-bridge-v1.json",
        "legal_river_bridge_source": _ROOT
        / "src/pontius/legal_river_quotient_bridge.py",
        "gitattributes": _ROOT / ".gitattributes",
        "artifact_marker": _ROOT / "artifacts/README.md",
    }
)
_ADR0391 = (
    _ROOT
    / "docs/decisions/ADR-0391-preregister-the-paired-high-low-cuda-tile-repair.md"
)


def verify_preregistered_compensated_tile_contract(
    configs: tuple[Mapping[str, object], Mapping[str, object]] | None = None,
) -> None:
    v1, v2 = (
        load_preregistered_compensated_tile_configs()
        if configs is None
        else configs
    )
    expected_sources = v1.get("expected_sources")
    if not isinstance(expected_sources, Mapping):
        raise ValueError("paired-tile v1 source contract is malformed")
    if set(expected_sources) != set(_V1_SOURCE_PATHS):
        raise ValueError("paired-tile v1 dependency set differs")
    for label, path in _V1_SOURCE_PATHS.items():
        if expected_sources[label] != canonical_lf_sha256(path):
            raise ValueError(f"paired-tile dependency differs: {label}")

    identity = v2.get("parent_identity")
    composite = v2.get("composite_authority")
    corrected = v2.get("corrected_arithmetic_contract")
    claims1 = v1.get("claims")
    claims2 = v2.get("claims")
    if not all(
        isinstance(value, Mapping)
        for value in (identity, composite, corrected, claims1, claims2)
    ):
        raise ValueError("paired-tile composite contract is malformed")
    assert isinstance(identity, Mapping)
    assert isinstance(composite, Mapping)
    assert isinstance(corrected, Mapping)
    assert isinstance(claims1, Mapping)
    assert isinstance(claims2, Mapping)
    if identity.get("adr0391_canonical_lf_sha256") != canonical_lf_sha256(
        _ADR0391
    ):
        raise ValueError("paired-tile ADR-0391 parent differs")
    if identity.get("v1_config_canonical_lf_sha256") != (
        PREREGISTERED_CONFIG_V1_SHA256
    ):
        raise ValueError("paired-tile v2 does not bind v1")
    if not composite.get(
        "all_v1_fields_remain_binding_except_required_primitives_"
        "source_weight_contract_and_normalization_contract_replaced_below"
    ):
        raise ValueError("paired-tile v2 overlay scope differs")

    tiles = v1.get("logical_tile_contract")
    limits = v1.get("numerical_limits")
    runtime = v1.get("required_runtime")
    reduction = v1.get("global_reduction_contract")
    allocation = v1.get("allocation_contract")
    if not all(
        isinstance(value, Mapping)
        for value in (tiles, limits, runtime, reduction, allocation)
    ):
        raise ValueError("paired-tile v1 typed sections are malformed")
    assert isinstance(tiles, Mapping)
    assert isinstance(limits, Mapping)
    assert isinstance(reduction, Mapping)
    assert isinstance(allocation, Mapping)
    if tiles.get("ordered_global_logical_ranges") != [
        [0, 64],
        [64, 128],
        [128, 176],
    ]:
        raise ValueError("paired-tile logical ranges differ")
    if tiles.get("ordered_physical_active_widths") != [128, 128, 96]:
        raise ValueError("paired-tile physical widths differ")
    if tiles.get("reach_physical_columns_in_owner_tile") != [94, 95]:
        raise ValueError("paired-tile reach location differs")
    if limits.get("bounded_transpose_dot_absolute") != 2e-10:
        raise ValueError("paired-tile absolute limit differs")
    if limits.get("bounded_scale_normalized_relative") != 2e-11:
        raise ValueError("paired-tile relative limit differs")
    if reduction.get("result_float64_slots") != 8:
        raise ValueError("paired-tile result slot count differs")
    if allocation.get("successor_predicted_named_device_peak_bytes") != 9910940380:
        raise ValueError("paired-tile predicted peak differs")

    primitives = corrected.get("required_primitives_replacement")
    divide = corrected.get("pair_divide_positive_small_integer_contract")
    source_weight = corrected.get("source_weight_contract_replacement")
    query_weight = corrected.get("query_weight_contract")
    normalization = corrected.get("normalization_contract_replacement")
    if not all(
        isinstance(value, Mapping)
        for value in (divide, source_weight, query_weight, normalization)
    ) or not isinstance(primitives, list):
        raise ValueError("paired-tile corrected arithmetic is malformed")
    assert isinstance(divide, Mapping)
    assert isinstance(source_weight, Mapping)
    assert isinstance(query_weight, Mapping)
    assert isinstance(normalization, Mapping)
    if "pair_divide_positive_small_integer" not in primitives:
        raise ValueError("paired-tile division primitive is absent")
    if divide.get("allowed_divisors") != [1, 2, 3, 4, 5, 6]:
        raise ValueError("paired-tile divisors differ")
    if source_weight.get("seat_order") != [0, 1, 2]:
        raise ValueError("paired-tile source factor order differs")
    if query_weight.get("seat_order") != [3, 4, 5]:
        raise ValueError("paired-tile query factor order differs")
    if not normalization.get("no_device_pair_divide_pair_primitive_authorized"):
        raise ValueError("paired-tile normalization authority differs")
    if not all(value is None or value is False for value in claims1.values()):
        raise ValueError("paired-tile v1 preregistered claims are open")
    if not all(value is None or value is False for value in claims2.values()):
        raise ValueError("paired-tile v2 preregistered claims are open")
    reserved = _ROOT / str(identity["reserved_actual_result_relative_path"])
    if reserved.exists():
        raise ValueError("paired-tile reserved actual result already exists")


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def bounded_execution_call_count() -> int:
    return _BOUNDED_EXECUTION_CALLS


def actual_execution_call_count() -> int:
    return _parent.actual_execution_call_count()


def actual_numeric_allocation_call_count() -> int:
    return _parent.actual_numeric_allocation_call_count()


def actual_scientific_call_count() -> int:
    return _parent.actual_scientific_call_count()


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


@dataclass(frozen=True, slots=True)
class FloatPair:
    high: float
    low: float

    @property
    def exact(self) -> Fraction:
        return Fraction.from_float(self.high) + Fraction.from_float(self.low)


def _two_sum_host(left: float, right: float) -> FloatPair:
    high = left + right
    split = high - left
    low = (left - (high - split)) + (right - split)
    return FloatPair(high, low)


def _quick_two_sum_host(left: float, right: float) -> FloatPair:
    high = left + right
    return FloatPair(high, right - (high - left))


def _two_product_host(left: float, right: float) -> FloatPair:
    high = left * right
    return FloatPair(high, math.fma(left, right, -high))


def _pair_add_host(left: FloatPair, right: FloatPair) -> FloatPair:
    high_sum = _two_sum_host(left.high, right.high)
    low_sum = _two_sum_host(left.low, right.low)
    middle = high_sum.low + low_sum.high
    normalized = _quick_two_sum_host(high_sum.high, middle)
    tail = normalized.low + low_sum.low
    return _quick_two_sum_host(normalized.high, tail)


def _pair_subtract_host(left: FloatPair, right: FloatPair) -> FloatPair:
    return _pair_add_host(left, FloatPair(-right.high, -right.low))


def _pair_times_float64_host(value: FloatPair, scalar: float) -> FloatPair:
    result = _two_product_host(value.high, scalar)
    return _pair_add_host(result, _two_product_host(value.low, scalar))


def _pair_times_pair_host(left: FloatPair, right: FloatPair) -> FloatPair:
    result = _two_product_host(left.high, right.high)
    result = _pair_add_host(result, _two_product_host(left.high, right.low))
    result = _pair_add_host(result, _two_product_host(left.low, right.high))
    return _pair_add_host(result, _two_product_host(left.low, right.low))


def _pair_divide_small_integer_host(value: FloatPair, divisor: int) -> FloatPair:
    if isinstance(divisor, bool) or divisor not in range(1, 7):
        raise ValueError("paired-tile divisor must be an integer from one to six")
    denominator = float(divisor)
    q1 = value.high / denominator
    r1 = _pair_subtract_host(value, _two_product_host(q1, denominator))
    q2 = r1.high / denominator
    r2 = _pair_subtract_host(r1, _two_product_host(q2, denominator))
    q3 = (r2.high + r2.low) / denominator
    return _pair_add_host(
        _pair_add_host(FloatPair(q1, 0.0), FloatPair(q2, 0.0)),
        FloatPair(q3, 0.0),
    )


def _pair_weight_host(
    initial: float,
    unary: np.ndarray,
    factors: np.ndarray,
    indices: Sequence[int],
) -> FloatPair:
    result = FloatPair(float(initial), 0.0)
    for index in indices:
        result = _pair_times_float64_host(result, float(unary[int(index)]))
        result = _pair_times_float64_host(result, float(factors[int(index)]))
    return result


_CUDA_SOURCE = r"""
struct DD {
    double high;
    double low;
};

__device__ __forceinline__ DD make_dd(double high, double low) {
    DD value;
    value.high = high;
    value.low = low;
    return value;
}

__device__ __forceinline__ DD two_sum(double left, double right) {
    double high = left + right;
    double split = high - left;
    double low = (left - (high - split)) + (right - split);
    return make_dd(high, low);
}

__device__ __forceinline__ DD quick_two_sum(double left, double right) {
    double high = left + right;
    return make_dd(high, right - (high - left));
}

__device__ __forceinline__ DD two_product(double left, double right) {
    double high = left * right;
    return make_dd(high, fma(left, right, -high));
}

__device__ __forceinline__ DD pair_add(DD left, DD right) {
    DD high_sum = two_sum(left.high, right.high);
    DD low_sum = two_sum(left.low, right.low);
    double middle = high_sum.low + low_sum.high;
    DD normalized = quick_two_sum(high_sum.high, middle);
    double tail = normalized.low + low_sum.low;
    return quick_two_sum(normalized.high, tail);
}

__device__ __forceinline__ DD pair_subtract(DD left, DD right) {
    return pair_add(left, make_dd(-right.high, -right.low));
}

__device__ __forceinline__ DD pair_times_float64(DD value, double scalar) {
    DD result = two_product(value.high, scalar);
    return pair_add(result, two_product(value.low, scalar));
}

__device__ __forceinline__ DD pair_times_pair(DD left, DD right) {
    DD result = two_product(left.high, right.high);
    result = pair_add(result, two_product(left.high, right.low));
    result = pair_add(result, two_product(left.low, right.high));
    return pair_add(result, two_product(left.low, right.low));
}

__device__ __forceinline__ DD pair_divide_small_integer(DD value, int divisor) {
    double denominator = (double)divisor;
    double q1 = value.high / denominator;
    DD r1 = pair_subtract(value, two_product(q1, denominator));
    double q2 = r1.high / denominator;
    DD r2 = pair_subtract(r1, two_product(q2, denominator));
    double q3 = (r2.high + r2.low) / denominator;
    DD result = pair_add(make_dd(q1, 0.0), make_dd(q2, 0.0));
    return pair_add(result, make_dd(q3, 0.0));
}

__device__ __forceinline__ DD load_pair(const double *row, int logical) {
    return make_dd(row[2 * logical], row[2 * logical + 1]);
}

__device__ __forceinline__ void store_pair(double *row, int logical, DD value) {
    row[2 * logical] = value.high;
    row[2 * logical + 1] = value.low;
}

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

__device__ __forceinline__ DD query_weight_pair(
    long long record, const int *query_hands, const double *unary,
    const double *factors, const int *unary_offsets,
    const double *mixture, int *h4, int *h5
) {
    *h4 = query_hands[record * 2];
    *h5 = query_hands[record * 2 + 1];
    int indices[3] = {
        unary_offsets[3], unary_offsets[4] + *h4, unary_offsets[5] + *h5
    };
    DD value = make_dd(mixture[0], 0.0);
    for (int seat = 0; seat < 3; ++seat) {
        int index = indices[seat];
        value = pair_times_float64(value, unary[index]);
        value = pair_times_float64(value, factors[index]);
    }
    return value;
}

extern "C" __global__ void primitive_pairs(
    const double *a_high, const double *a_low,
    const double *b_high, const double *b_low,
    const int *operations, const int *divisors, int count,
    double *out_high, double *out_low
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= count) return;
    DD left = make_dd(a_high[index], a_low[index]);
    DD right = make_dd(b_high[index], b_low[index]);
    DD result;
    int operation = operations[index];
    if (operation == 0) result = two_sum(left.high, right.high);
    else if (operation == 1) result = two_product(left.high, right.high);
    else if (operation == 2) result = pair_add(left, right);
    else if (operation == 3) result = pair_subtract(left, right);
    else if (operation == 4) result = pair_times_float64(left, right.high);
    else if (operation == 5) result = pair_times_pair(left, right);
    else result = pair_divide_small_integer(left, divisors[index]);
    out_high[index] = result.high;
    out_low[index] = result.low;
}

extern "C" __global__ void source_coefficients_tile(
    double *table, long long source_level_offset,
    long long occupancy_rank_start, long long occupancy_records,
    int global_feature_start, int logical_width, int physical_stride,
    int n, int hand_width, int pair_stride, int source_rank,
    const signed char *pairings, const int *pair_to_hand,
    const double *unary, const double *factors, const int *unary_offsets,
    const int *transition0, const int *transition1, const int *transition2
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= occupancy_records) return;
    long long rank = occupancy_rank_start + local;
    double *output = table + (source_level_offset + rank) * physical_stride;
    for (int column = 0; column < 2 * logical_width; ++column)
        output[column] = 0.0;
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
        int hands[3] = {h0, h1, h2};
        DD weight = make_dd(1.0, 0.0);
        for (int seat = 0; seat < 3; ++seat) {
            int index = unary_offsets[seat] + hands[seat];
            weight = pair_times_float64(weight, unary[index]);
            weight = pair_times_float64(weight, factors[index]);
        }
        int local_state = state2 - global_feature_start;
        if (local_state >= 0 && local_state < logical_width)
            store_pair(output, local_state,
                       pair_add(load_pair(output, local_state), weight));
        int local_reach = source_rank - global_feature_start;
        if (local_reach >= 0 && local_reach < logical_width)
            store_pair(output, local_reach,
                       pair_add(load_pair(output, local_reach), weight));
    }
}

extern "C" __global__ void zeta_level_tile(
    double *table, long long current_offset, long long next_offset,
    long long rows, int n, int level, int source_cards,
    int logical_width, int physical_stride
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = rows * logical_width;
    if (linear >= total) return;
    long long row = linear / logical_width;
    int logical = (int)(linear - row * logical_width);
    unsigned long long mask = unrank_mask(row, n, level);
    DD value = make_dd(0.0, 0.0);
    for (int card = 0; card < n; ++card) {
        unsigned long long bit = 1ULL << card;
        if (!(mask & bit)) {
            long long next_rank = rank_mask(mask | bit, n);
            const double *child = table
                + (next_offset + next_rank) * physical_stride;
            value = pair_add(value, load_pair(child, logical));
        }
    }
    double *output = table + (current_offset + row) * physical_stride;
    store_pair(
        output, logical,
        pair_divide_small_integer(value, source_cards - level)
    );
}

extern "C" __global__ void signed_targets_tile(
    const double *table, const long long *offsets, int source_cards,
    const unsigned long long *target_masks, int implicit_targets,
    int target_cards, long long target_rank_or_record_start,
    long long target_records, int n, int logical_width, int physical_stride,
    double *output
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = target_records * logical_width;
    if (linear >= total) return;
    long long local_row = linear / logical_width;
    int logical = (int)(linear - local_row * logical_width);
    long long global_row = target_rank_or_record_start + local_row;
    unsigned long long mask = implicit_targets
        ? unrank_mask(global_row, n, target_cards)
        : target_masks[global_row];
    unsigned long long subset = mask;
    DD value = make_dd(0.0, 0.0);
    while (true) {
        int cards = __popcll(subset);
        if (cards <= source_cards) {
            long long rank = rank_mask(subset, n);
            const double *source = table
                + (offsets[cards] + rank) * physical_stride;
            DD term = load_pair(source, logical);
            value = (cards & 1)
                ? pair_subtract(value, term)
                : pair_add(value, term);
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    store_pair(output + local_row * physical_stride, logical, value);
}

extern "C" __global__ void fold_query_tile(
    double *compatible, long long query_record_start, long long records,
    int global_feature_start, int logical_width, int physical_stride,
    int source_rank, int reach_owner, const int *query_hands,
    const double *unary, const double *factors, const int *unary_offsets,
    const double *mixture, const int *transition3, const int *transition4,
    const double *terminal, int hand_width, double sunk,
    double *numerator_high, double *numerator_low
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= records) return;
    long long record = query_record_start + local;
    int h4, h5;
    DD weight = query_weight_pair(
        record, query_hands, unary, factors, unary_offsets, mixture, &h4, &h5
    );
    double *row = compatible + local * physical_stride;
    DD numerator = make_dd(0.0, 0.0);
    DD reach = make_dd(0.0, 0.0);
    for (int logical = 0; logical < logical_width; ++logical) {
        int global_feature = global_feature_start + logical;
        DD coefficient = load_pair(row, logical);
        double payoff;
        if (global_feature == source_rank) payoff = sunk;
        else {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            payoff = terminal[state4 * hand_width + h5];
        }
        DD covector = pair_times_float64(weight, payoff);
        numerator = pair_add(
            numerator, pair_times_pair(coefficient, covector)
        );
        if (reach_owner && global_feature == source_rank)
            reach = pair_times_pair(coefficient, weight);
    }
    numerator_high[local] = numerator.high;
    numerator_low[local] = numerator.low;
    row[0] = reach.high;
    row[1] = reach.low;
}

extern "C" __global__ void build_numerator_covector_tile(
    double *output, long long query_record_start, long long records,
    int global_feature_start, int logical_width, int physical_stride,
    int source_rank, const int *query_hands, const double *unary,
    const double *factors, const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = records * logical_width;
    if (linear >= total) return;
    long long local = linear / logical_width;
    int logical = (int)(linear - local * logical_width);
    long long record = query_record_start + local;
    int h4, h5;
    DD weight = query_weight_pair(
        record, query_hands, unary, factors, unary_offsets, mixture, &h4, &h5
    );
    int global_feature = global_feature_start + logical;
    double payoff;
    if (global_feature == source_rank) payoff = sunk;
    else {
        int state3 = transition3[global_feature];
        int state4 = transition4[state3 * hand_width + h4];
        payoff = terminal[state4 * hand_width + h5];
    }
    store_pair(
        output + local * physical_stride, logical,
        pair_times_float64(weight, payoff)
    );
}

extern "C" __global__ void aggregate_query_labels_tile(
    const double *records, long long occupancy_rank_start,
    long long occupancies, int labels, int logical_width,
    int physical_stride, long long query_level_offset,
    int skip_last_label, double *table
) {
    long long linear = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long total = occupancies * logical_width;
    if (linear >= total) return;
    long long local_occupancy = linear / logical_width;
    int logical = (int)(linear - local_occupancy * logical_width);
    int stop = labels - (skip_last_label ? 1 : 0);
    DD value = make_dd(0.0, 0.0);
    for (int label = 0; label < stop; ++label) {
        const double *row = records
            + (local_occupancy * labels + label) * physical_stride;
        value = pair_add(value, load_pair(row, logical));
    }
    long long global_occupancy = occupancy_rank_start + local_occupancy;
    store_pair(
        table + (query_level_offset + global_occupancy) * physical_stride,
        logical, value
    );
}

extern "C" __global__ void source_adjoint_contract_tile(
    double *unique, long long source_rank_start, long long source_records,
    int global_feature_start, int logical_width, int physical_stride,
    int n, int hand_width, int pair_stride, int source_rank,
    const signed char *pairings, const int *pair_to_hand,
    const double *unary, const double *factors, const int *unary_offsets,
    const int *transition0, const int *transition1, const int *transition2
) {
    long long local = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= source_records) return;
    long long rank = source_rank_start + local;
    int cards[6];
    unrank_six(rank, n, cards);
    const double *adjoint = unique + local * physical_stride;
    double coefficients[128];
    for (int column = 0; column < 2 * logical_width; ++column)
        coefficients[column] = 0.0;
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
        int hands[3] = {h0, h1, h2};
        DD weight = make_dd(1.0, 0.0);
        for (int seat = 0; seat < 3; ++seat) {
            int index = unary_offsets[seat] + hands[seat];
            weight = pair_times_float64(weight, unary[index]);
            weight = pair_times_float64(weight, factors[index]);
        }
        int local_state = state2 - global_feature_start;
        if (local_state >= 0 && local_state < logical_width) {
            DD prior = load_pair(coefficients, local_state);
            store_pair(coefficients, local_state, pair_add(prior, weight));
        }
        int local_reach = source_rank - global_feature_start;
        if (local_reach >= 0 && local_reach < logical_width) {
            DD prior = load_pair(coefficients, local_reach);
            store_pair(coefficients, local_reach, pair_add(prior, weight));
        }
    }
    DD value = make_dd(0.0, 0.0);
    for (int logical = 0; logical < logical_width; ++logical)
        value = pair_add(
            value,
            pair_times_pair(load_pair(coefficients, logical),
                            load_pair(adjoint, logical))
        );
    unique[local * physical_stride] = value.high;
    unique[local * physical_stride + 1] = value.low;
}

extern "C" __global__ void reduce_contiguous_pairs(
    double *high, double *low, long long count,
    long long global_start, double *carry
) {
    if (blockIdx.x || threadIdx.x) return;
    for (long long local = 0; local < count; ++local) {
        unsigned long long index = (unsigned long long)(global_start + local);
        DD value = make_dd(high[local], low[local]);
        int level = 0;
        while (index & (1ULL << level)) {
            value = pair_add(load_pair(carry, level), value);
            ++level;
        }
        store_pair(carry, level, value);
    }
}

extern "C" __global__ void reduce_strided_pairs(
    double *rows, int physical_stride, int high_column, int low_column,
    long long count, long long global_start, double *carry
) {
    if (blockIdx.x || threadIdx.x) return;
    for (long long local = 0; local < count; ++local) {
        unsigned long long index = (unsigned long long)(global_start + local);
        DD value = make_dd(
            rows[local * physical_stride + high_column],
            rows[local * physical_stride + low_column]
        );
        int level = 0;
        while (index & (1ULL << level)) {
            value = pair_add(load_pair(carry, level), value);
            ++level;
        }
        store_pair(carry, level, value);
    }
}

extern "C" __global__ void finalize_pair_result(
    const double *carry, unsigned long long processed_count,
    double *results, int result_high_slot
) {
    if (blockIdx.x || threadIdx.x) return;
    DD value = make_dd(0.0, 0.0);
    for (int level = 63; level >= 0; --level)
        if (processed_count & (1ULL << level))
            value = pair_add(value, load_pair(carry, level));
    results[result_high_slot] = value.high;
    results[result_high_slot + 1] = value.low;
}

extern "C" __global__ void direct_selected_queries_tile(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *query_masks, int query_count,
    const int *global_features, int feature_count,
    int global_feature_start, int logical_width, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= query_count * feature_count) return;
    int query = index / feature_count;
    int feature_index = index - query * feature_count;
    int logical = global_features[feature_index] - global_feature_start;
    if (logical < 0 || logical >= logical_width) return;
    DD value = make_dd(0.0, 0.0);
    unsigned long long query_mask = query_masks[query];
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_mask(row, n, 6);
        if (!(source_mask & query_mask))
            value = pair_add(
                value,
                load_pair(source + (source_level_offset + row) * physical_stride,
                          logical)
            );
    }
    output[2 * index] = value.high;
    output[2 * index + 1] = value.low;
}

extern "C" __global__ void direct_selected_fold_tile(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *selected_query_masks,
    const long long *selected_query_records, int query_count,
    int global_feature_start, int logical_width, int source_rank,
    const int *query_hands, const double *unary, const double *factors,
    const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *output
) {
    int query = blockDim.x * blockIdx.x + threadIdx.x;
    if (query >= query_count) return;
    long long record = selected_query_records[query];
    int h4, h5;
    DD weight = query_weight_pair(
        record, query_hands, unary, factors, unary_offsets, mixture, &h4, &h5
    );
    unsigned long long query_mask = selected_query_masks[query];
    DD numerator = make_dd(0.0, 0.0);
    DD reach = make_dd(0.0, 0.0);
    for (int logical = 0; logical < logical_width; ++logical) {
        DD coefficient = make_dd(0.0, 0.0);
        for (long long row = 0; row < source_rows; ++row) {
            unsigned long long source_mask = unrank_mask(row, n, 6);
            if (!(source_mask & query_mask))
                coefficient = pair_add(
                    coefficient,
                    load_pair(source + (source_level_offset + row)
                              * physical_stride, logical)
                );
        }
        int global_feature = global_feature_start + logical;
        double payoff;
        if (global_feature == source_rank) payoff = sunk;
        else {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            payoff = terminal[state4 * hand_width + h5];
        }
        numerator = pair_add(
            numerator,
            pair_times_pair(coefficient, pair_times_float64(weight, payoff))
        );
        if (global_feature == source_rank)
            reach = pair_times_pair(coefficient, weight);
    }
    output[query * 4] = numerator.high;
    output[query * 4 + 1] = numerator.low;
    output[query * 4 + 2] = reach.high;
    output[query * 4 + 3] = reach.low;
}

extern "C" __global__ void direct_selected_adjoint_tile(
    const long long *source_ranks, int source_count,
    const int *global_features, int feature_count,
    int global_feature_start, int logical_width, int n,
    const unsigned long long *query_masks, long long query_records,
    int source_rank, const int *query_hands, const double *unary,
    const double *factors, const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= source_count * feature_count) return;
    int source_index = index / feature_count;
    int feature_index = index - source_index * feature_count;
    int global_feature = global_features[feature_index];
    int logical = global_feature - global_feature_start;
    if (logical < 0 || logical >= logical_width) return;
    unsigned long long source_mask = unrank_mask(source_ranks[source_index], n, 6);
    DD value = make_dd(0.0, 0.0);
    for (long long record = 0; record < query_records; ++record) {
        if (source_mask & query_masks[record]) continue;
        int h4, h5;
        DD weight = query_weight_pair(
            record, query_hands, unary, factors, unary_offsets,
            mixture, &h4, &h5
        );
        double payoff;
        if (global_feature == source_rank) payoff = sunk;
        else {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            payoff = terminal[state4 * hand_width + h5];
        }
        value = pair_add(value, pair_times_float64(weight, payoff));
    }
    output[2 * index] = value.high;
    output[2 * index + 1] = value.low;
}

extern "C" __global__ void selected_query_weights(
    const long long *records, int count, const int *query_hands,
    const double *unary, const double *factors, const int *unary_offsets,
    const double *mixture, double *output
) {
    int index = blockDim.x * blockIdx.x + threadIdx.x;
    if (index >= count) return;
    int h4, h5;
    DD value = query_weight_pair(
        records[index], query_hands, unary, factors, unary_offsets,
        mixture, &h4, &h5
    );
    output[2 * index] = value.high;
    output[2 * index + 1] = value.low;
}
"""


_KERNEL_NAMES = (
    "primitive_pairs",
    "source_coefficients_tile",
    "zeta_level_tile",
    "signed_targets_tile",
    "fold_query_tile",
    "build_numerator_covector_tile",
    "aggregate_query_labels_tile",
    "source_adjoint_contract_tile",
    "reduce_contiguous_pairs",
    "reduce_strided_pairs",
    "finalize_pair_result",
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
    "selected_query_weights",
)
_KERNEL_CACHE: dict[int, Mapping[str, object]] = {}
_MODULE_CACHE: dict[int, object] = {}
_NVRTC_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)


def _kernels(cp: Any) -> Mapping[str, object]:
    device = int(cp.cuda.Device().id)
    cached = _KERNEL_CACHE.get(device)
    if cached is not None:
        return cached
    binary, _ = cp.cuda.compiler.compile_using_nvrtc(
        _CUDA_SOURCE,
        options=_NVRTC_OPTIONS,
        cache_in_memory=True,
    )
    module = cp.cuda.function.Module()
    module.load(binary)
    result = MappingProxyType(
        {name: module.get_function(name) for name in _KERNEL_NAMES}
    )
    _MODULE_CACHE[device] = module
    _KERNEL_CACHE[device] = result
    return result


def _launch(kernel: Any, total: int, arguments: tuple[object, ...]) -> None:
    if total <= 0:
        raise ValueError("paired-tile launch total must be positive")
    kernel.linear_launch(
        int(total),
        arguments,
        shared_mem=0,
        block_max_size=128,
    )


def _rawmodule_options_for_static_control() -> tuple[str, ...]:
    """Expose the exact direct-NVRTC option tuple without compiling."""

    return _NVRTC_OPTIONS


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
    runtime: CudaRuntimeIdentity, config: Mapping[str, object]
) -> None:
    expected = config.get("required_runtime")
    if not isinstance(expected, Mapping):
        raise ValueError("paired-tile runtime contract is malformed")
    for field in (
        "device_name",
        "compute_capability",
        "device_total_bytes",
        "cuda_driver_version",
        "cuda_runtime_version",
        "cupy_version",
    ):
        if getattr(runtime, field) != expected.get(field):
            raise RuntimeError(f"paired-tile runtime differs: {field}")


@dataclass(frozen=True, slots=True)
class PrimitiveEvidence:
    operation_count: int
    maximum_absolute_errors: Mapping[str, float]
    low_lane_nonzero_counts: Mapping[str, int]
    reporting_digest: str
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return all(self.gates.values())


def _primitive_cases() -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    rows: list[tuple[FloatPair, FloatPair, int, int]] = []
    values = (
        (1.0, 2.0),
        (1.0, math.ulp(1.0)),
        (2.0**50, 1.0),
        (2.0**-40, -(2.0**-40) + 2.0**-90),
        (-17.25, 3.5),
        (0.0, -0.0),
    )
    for left, right in values:
        rows.append((FloatPair(left, 0.0), FloatPair(right, 0.0), 0, 1))
        rows.append((FloatPair(left, 0.0), FloatPair(right, 0.0), 1, 1))
    paired = (
        (FloatPair(1.0, 2.0**-54), FloatPair(-1.0, 2.0**-53)),
        (FloatPair(2.0**30, 2.0**-30), FloatPair(2.0**-20, -2.0**-80)),
        (FloatPair(-7.0, 2.0**-52), FloatPair(3.0, -2.0**-53)),
    )
    for left, right in paired:
        for operation in (2, 3, 4, 5):
            rows.append((left, right, operation, 1))
    division_inputs = (
        FloatPair(0.0, 0.0),
        FloatPair(1.0, 0.0),
        FloatPair(1.0, 2.0**-54),
        FloatPair(-11.0, 2.0**-50),
        FloatPair(2.0**40, 2.0**-20),
    )
    for value in division_inputs:
        for divisor in range(1, 7):
            rows.append((value, FloatPair(0.0, 0.0), 6, divisor))
    return tuple(
        np.asarray(values, dtype=dtype)
        for values, dtype in (
            ([row[0].high for row in rows], np.float64),
            ([row[0].low for row in rows], np.float64),
            ([row[1].high for row in rows], np.float64),
            ([row[1].low for row in rows], np.float64),
            ([row[2] for row in rows], np.int32),
            ([row[3] for row in rows], np.int32),
        )
    )


def _expected_primitive(
    left: FloatPair, right: FloatPair, operation: int, divisor: int
) -> FloatPair:
    if operation == 0:
        return _two_sum_host(left.high, right.high)
    if operation == 1:
        return _two_product_host(left.high, right.high)
    if operation == 2:
        return _pair_add_host(left, right)
    if operation == 3:
        return _pair_subtract_host(left, right)
    if operation == 4:
        return _pair_times_float64_host(left, right.high)
    if operation == 5:
        return _pair_times_pair_host(left, right)
    return _pair_divide_small_integer_host(left, divisor)


def _run_primitive_controls(
    cp: Any, kernels: Mapping[str, object]
) -> PrimitiveEvidence:
    a_high, a_low, b_high, b_low, operations, divisors = _primitive_cases()
    count = len(operations)
    output_high = cp.empty(count, dtype=cp.float64)
    output_low = cp.empty(count, dtype=cp.float64)
    _launch(
        kernels["primitive_pairs"],
        count,
        (
            cp.asarray(a_high),
            cp.asarray(a_low),
            cp.asarray(b_high),
            cp.asarray(b_low),
            cp.asarray(operations),
            cp.asarray(divisors),
            np.int32(count),
            output_high,
            output_low,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    actual_high = output_high.get()
    actual_low = output_low.get()
    del output_high, output_low

    exact_two_sum = True
    exact_two_product = True
    byte_replay = True
    errors = {name: Fraction(0) for name in (
        "pair_add",
        "pair_subtract",
        "pair_times_float64",
        "pair_times_pair",
        "pair_divide_small_integer",
    )}
    names = {
        2: "pair_add",
        3: "pair_subtract",
        4: "pair_times_float64",
        5: "pair_times_pair",
        6: "pair_divide_small_integer",
    }
    low_counts = {name: 0 for name in (
        "two_sum",
        "two_product",
        *errors,
    )}
    for index in range(count):
        left = FloatPair(float(a_high[index]), float(a_low[index]))
        right = FloatPair(float(b_high[index]), float(b_low[index]))
        operation = int(operations[index])
        divisor = int(divisors[index])
        actual = FloatPair(float(actual_high[index]), float(actual_low[index]))
        expected = _expected_primitive(left, right, operation, divisor)
        byte_replay = byte_replay and (
            np.float64(actual.high).tobytes() == np.float64(expected.high).tobytes()
            and np.float64(actual.low).tobytes() == np.float64(expected.low).tobytes()
        )
        if actual.low != 0.0:
            key = "two_sum" if operation == 0 else (
                "two_product" if operation == 1 else names[operation]
            )
            low_counts[key] += 1
        if operation == 0:
            authority = Fraction.from_float(left.high) + Fraction.from_float(
                right.high
            )
            exact_two_sum = exact_two_sum and actual.exact == authority
        elif operation == 1:
            authority = Fraction.from_float(left.high) * Fraction.from_float(
                right.high
            )
            exact_two_product = exact_two_product and actual.exact == authority
        else:
            if operation == 2:
                authority = left.exact + right.exact
            elif operation == 3:
                authority = left.exact - right.exact
            elif operation == 4:
                authority = left.exact * Fraction.from_float(right.high)
            elif operation == 5:
                authority = left.exact * right.exact
            else:
                authority = left.exact / divisor
            error = abs(actual.exact - authority)
            name = names[operation]
            errors[name] = max(errors[name], error)

    finite = bool(np.all(np.isfinite(actual_high)) and np.all(np.isfinite(actual_low)))
    drop_low_changes = any(
        FloatPair(float(actual_high[index]), 0.0).exact
        != FloatPair(float(actual_high[index]), float(actual_low[index])).exact
        for index in range(count)
        if int(operations[index]) >= 2
    )
    mutation_left = FloatPair(1.0, 2.0**-54)
    mutation_right = FloatPair(-1.0, 2.0**-53)
    swapped_pair_changes = (
        _pair_times_pair_host(mutation_left, mutation_right).exact
        != _pair_times_pair_host(
            FloatPair(mutation_left.low, mutation_left.high), mutation_right
        ).exact
    )
    low_low_left = FloatPair(0.0, 1.5)
    low_low_right = FloatPair(0.0, -2.0)
    full_product = _pair_times_pair_host(low_low_left, low_low_right)
    omitted_low_low = _pair_add_host(
        _pair_add_host(
            _two_product_host(low_low_left.high, low_low_right.high),
            _two_product_host(low_low_left.high, low_low_right.low),
        ),
        _two_product_host(low_low_left.low, low_low_right.high),
    )
    omitted_low_low_changes = omitted_low_low.exact != full_product.exact
    reciprocal_divide_changes = any(
        _pair_divide_small_integer_host(mutation_left, divisor).exact
        != _pair_times_float64_host(mutation_left, 1.0 / divisor).exact
        for divisor in range(1, 7)
    )
    high_only_remainder_changes = any(
        _pair_divide_small_integer_host(mutation_left, divisor).exact
        != FloatPair(mutation_left.high / float(divisor), 0.0).exact
        for divisor in range(1, 7)
    )
    single_pass_changes = (
        _pair_add_host(mutation_left, mutation_right).exact
        != FloatPair(mutation_left.high + mutation_right.high, 0.0).exact
    )
    digest = sha256(
        np.column_stack((actual_high, actual_low)).tobytes()
    ).hexdigest()
    return PrimitiveEvidence(
        operation_count=count,
        maximum_absolute_errors=MappingProxyType(
            {name: float(value) for name, value in errors.items()}
        ),
        low_lane_nonzero_counts=MappingProxyType(low_counts),
        reporting_digest=digest,
        gates=MappingProxyType(
            {
                "exact_two_sum": exact_two_sum,
                "exact_two_product": exact_two_product,
                "host_device_byte_replay": byte_replay,
                "finite_outputs": finite,
                "all_six_divisors": set(int(value) for value in divisors if value)
                == set(range(1, 7)),
                "low_lane_detecting_mass": sum(low_counts.values()) > 0,
                "dropped_low_mutation_changes_value": drop_low_changes,
                "swapped_pair_mutation_rejected": swapped_pair_changes,
                "omitted_low_low_mutation_rejected": omitted_low_low_changes,
                "reciprocal_divide_mutation_rejected": reciprocal_divide_changes,
                "high_only_remainder_mutation_rejected": high_only_remainder_changes,
                "single_pass_mutation_rejected": single_pass_changes,
                "strict_compile_options": _NVRTC_OPTIONS
                == (
                    "--std=c++14",
                    "--ftz=false",
                    "--prec-div=true",
                    "--prec-sqrt=true",
                    "--fmad=false",
                ),
            }
        ),
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


def _allocate_resident(cp: Any, fixture: ConsumerPopulationFixture) -> _DeviceResident:
    return _DeviceResident(
        pairings=cp.asarray(fixture.source_pair_positions, dtype=cp.int8),
        pair_to_hand=cp.asarray(fixture.pair_to_hand, dtype=cp.int32),
        unary=cp.asarray(fixture.unary_weights.reshape(-1), dtype=cp.float64),
        factors=cp.asarray(fixture.mode_factors.reshape(-1), dtype=cp.float64),
        mixture=cp.asarray(fixture.mixture_weights, dtype=cp.float64),
        unary_offsets=cp.asarray(fixture.unary_offsets, dtype=cp.int32),
        query_masks=cp.asarray(fixture.query_masks, dtype=cp.uint64),
        query_hands=cp.asarray(fixture.query_hand_indices, dtype=cp.int32),
        transitions=tuple(
            cp.asarray(value, dtype=cp.int32) for value in fixture.transitions
        ),
        terminal=cp.asarray(fixture.terminal_winner_values, dtype=cp.float64),
        source_offsets=cp.asarray(
            cardinality_offsets(fixture.available_cards, SOURCE_CARDS),
            dtype=cp.int64,
        ),
        adjoint_offsets=cp.asarray(
            cardinality_offsets(fixture.available_cards, QUERY_CARDS),
            dtype=cp.int64,
        ),
        results=cp.zeros(8, dtype=cp.float64),
    )


def _fill_recurrence_tile(
    kernels: Mapping[str, object],
    table: Any,
    *,
    available_cards: int,
    source_cards: int,
    logical_width: int,
) -> None:
    offsets = cardinality_offsets(available_cards, source_cards)
    for level in range(source_cards - 1, -1, -1):
        rows = comb(available_cards, level)
        _launch(
            kernels["zeta_level_tile"],
            rows * logical_width,
            (
                table,
                np.int64(offsets[level]),
                np.int64(offsets[level + 1]),
                np.int64(rows),
                np.int32(available_cards),
                np.int32(level),
                np.int32(source_cards),
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
            ),
        )


def _reduce_contiguous(
    kernels: Mapping[str, object],
    high: Any,
    low: Any,
    count: int,
    global_start: int,
    carry: Any,
) -> None:
    _launch(
        kernels["reduce_contiguous_pairs"],
        1,
        (high, low, np.int64(count), np.int64(global_start), carry),
    )


def _reduce_strided(
    kernels: Mapping[str, object],
    rows: Any,
    count: int,
    global_start: int,
    carry: Any,
) -> None:
    _launch(
        kernels["reduce_strided_pairs"],
        1,
        (
            rows,
            np.int32(PHYSICAL_STRIDE_WIDTH),
            np.int32(0),
            np.int32(1),
            np.int64(count),
            np.int64(global_start),
            carry,
        ),
    )


def _finalize_pair(
    kernels: Mapping[str, object],
    carry: Any,
    count: int,
    results: Any,
    slot: int,
) -> None:
    _launch(
        kernels["finalize_pair_result"],
        1,
        (carry, np.uint64(count), results, np.int32(slot)),
    )


def _sample_rows(
    available_cards: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    parent_config = _parent.load_preregistered_cuda_consumer_config()
    return _parent._sample_rows(parent_config, available_cards)


def _tile_index(global_start: int) -> int:
    try:
        return tuple(start for start, _ in LOGICAL_TILES).index(global_start)
    except ValueError as exc:
        raise ValueError("paired-tile global start is outside the partition") from exc


def _tile_boundary_features(global_start: int, stop: int) -> tuple[int, ...]:
    return tuple(
        feature
        for feature in _BOUNDARY_FEATURES
        if global_start <= feature < stop
    )


def _copy_pair_rows(
    table: Any,
    level_offset: int,
    row_ranks: Sequence[int],
    logical_width: int,
) -> np.ndarray:
    result = np.empty((len(row_ranks), logical_width, 2), dtype=np.float64)
    physical = logical_width * 2
    for index, rank in enumerate(row_ranks):
        result[index] = table[
            level_offset + int(rank), :physical
        ].get().reshape(logical_width, 2)
    return result


def _pair_digest(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values, dtype=np.float64)
    return sha256(memoryview(contiguous).cast("B")).hexdigest()


def _pair_from_array(values: np.ndarray) -> FloatPair:
    if values.shape != (2,):
        raise ValueError("paired-tile scalar must have exactly two components")
    return FloatPair(float(values[0]), float(values[1]))


def _combine_pair_scalars(values: Sequence[FloatPair]) -> FloatPair:
    result = FloatPair(0.0, 0.0)
    for value in values:
        result = _pair_add_host(result, value)
    return result


def _combine_pair_arrays(parts: Sequence[np.ndarray]) -> np.ndarray:
    if not parts:
        raise ValueError("paired-tile array combination is empty")
    shape = parts[0].shape
    if shape[-1] != 2 or any(part.shape != shape for part in parts):
        raise ValueError("paired-tile array combination shapes differ")
    result = np.zeros(shape, dtype=np.float64)
    flat_result = result.reshape(-1, 2)
    flat_parts = [part.reshape(-1, 2) for part in parts]
    for index in range(len(flat_result)):
        combined = _combine_pair_scalars(
            [_pair_from_array(part[index]) for part in flat_parts]
        )
        flat_result[index] = (combined.high, combined.low)
    return result


def _exact_pair_sum(values: np.ndarray) -> Fraction:
    if values.shape[-1] != 2:
        raise ValueError("paired-tile exact sum lacks a component axis")
    result = Fraction(0)
    for high, low in values.reshape(-1, 2):
        result += Fraction.from_float(float(high))
        result += Fraction.from_float(float(low))
    return result


def _pair_error(
    actual: FloatPair,
    expected: Fraction,
) -> Fraction:
    return abs(actual.exact - expected)


def _scale_relative(error: Fraction, expected: Fraction) -> Fraction:
    return error / max(Fraction(1), abs(expected))


def _maximum_pair_errors(
    actual: np.ndarray,
    expected: Sequence[Fraction],
) -> tuple[Fraction, Fraction]:
    flat = actual.reshape(-1, 2)
    if len(flat) != len(expected):
        raise ValueError("paired-tile error operands differ in size")
    maximum_absolute = Fraction(0)
    maximum_relative = Fraction(0)
    for pair, authority in zip(flat, expected, strict=True):
        error = _pair_error(_pair_from_array(pair), authority)
        maximum_absolute = max(maximum_absolute, error)
        maximum_relative = max(maximum_relative, _scale_relative(error, authority))
    return maximum_absolute, maximum_relative


def _pair_arrays_byte_equal(left: np.ndarray, right: np.ndarray) -> bool:
    return (
        left.dtype == right.dtype
        and left.shape == right.shape
        and left.tobytes() == right.tobytes()
    )


def _same_capture(
    first: Mapping[str, object],
    second: Mapping[str, object],
    keys: Sequence[str],
) -> bool:
    for key in keys:
        left = first[key]
        right = second[key]
        if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
            if not _pair_arrays_byte_equal(left, right):
                return False
        elif left != right:
            return False
    return True


def _positive_zero_slots(values: np.ndarray) -> bool:
    positive_zero = np.float64(0.0).tobytes()
    return values.shape == (8,) and all(
        value.tobytes() == positive_zero for value in values
    )


def _numeric_scan(values: np.ndarray) -> tuple[bool, int, int | None, int | None]:
    """Scan stored Float64 components without collapsing adjacent pairs."""

    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = bool(np.all(np.isfinite(flat)))
    absolute = np.abs(flat[np.nonzero(flat)])
    if absolute.size == 0:
        return finite, 0, None, None
    tiny = np.finfo(np.float64).tiny
    subnormal_count = int(np.count_nonzero(absolute < tiny))
    exponents = np.frexp(absolute)[1]
    return finite, subnormal_count, int(exponents.min()), int(exponents.max())


def _merge_numeric_scans(
    scans: Sequence[tuple[bool, int, int | None, int | None]],
) -> tuple[bool, int, int | None, int | None]:
    finite = all(scan[0] for scan in scans)
    subnormal = sum(scan[1] for scan in scans)
    minima = [scan[2] for scan in scans if scan[2] is not None]
    maxima = [scan[3] for scan in scans if scan[3] is not None]
    return (
        finite,
        subnormal,
        min(minima) if minima else None,
        max(maxima) if maxima else None,
    )


@dataclass(frozen=True, slots=True)
class TenCardAuthority:
    source: tuple[tuple[Fraction, ...], ...]
    compatible_source_ranks: tuple[int, ...]
    covectors: tuple[tuple[Fraction, ...], ...]
    fold: tuple[tuple[Fraction, Fraction], ...]
    adjoint: tuple[tuple[Fraction, ...], ...]
    forward_tiles: tuple[Fraction, Fraction, Fraction]
    transpose_tiles: tuple[Fraction, Fraction, Fraction]
    numerator: Fraction
    reach: Fraction
    transpose: Fraction


def _ten_card_authority(
    fixture: ConsumerPopulationFixture,
) -> TenCardAuthority:
    if fixture.available_cards != 10:
        raise ValueError("paired-tile exact authority is restricted to ten cards")
    geometry = fixture.geometry
    source = tuple(
        _parent._source_row_exact(fixture, rank)
        for rank in range(geometry.source_occupancies)
    )
    universe_mask = (1 << 10) - 1
    compatible_ranks: list[int] = []
    covectors: list[tuple[Fraction, ...]] = []
    fold: list[tuple[Fraction, Fraction]] = []
    for record in range(geometry.labeled_query_records):
        complement = universe_mask ^ int(fixture.query_masks[record])
        cards = tuple(card for card in range(10) if complement & (1 << card))
        source_rank = colex_rank(cards)
        compatible_ranks.append(source_rank)
        covector = _parent._query_covector_exact(fixture, record)
        covectors.append(covector)
        row = source[source_rank]
        numerator = sum(
            (
                row[feature] * covector[feature]
                for feature in range(TOTAL_FEATURE_WIDTH)
            ),
            Fraction(0),
        )
        query_weight, _, _ = _parent._query_weight_exact(fixture, record)
        fold.append((numerator, query_weight * row[REACH_GLOBAL_FEATURE]))

    adjoint: list[tuple[Fraction, ...]] = []
    for source_rank in range(geometry.source_occupancies):
        source_cards = colex_unrank(source_rank, 10, SOURCE_CARDS)
        query_mask = universe_mask ^ sum(1 << card for card in source_cards)
        query_cards = tuple(card for card in range(10) if query_mask & (1 << card))
        query_rank = colex_rank(query_cards)
        start = query_rank * QUERY_LABELS
        adjoint.append(
            tuple(
                sum(
                    (
                        covectors[start + label][feature]
                        for label in range(QUERY_LABELS)
                    ),
                    Fraction(0),
                )
                for feature in range(TOTAL_FEATURE_WIDTH)
            )
        )

    forward_tiles = tuple(
        sum(
            (
                source[compatible_ranks[record]][feature]
                * covectors[record][feature]
                for record in range(geometry.labeled_query_records)
                for feature in range(start, stop)
            ),
            Fraction(0),
        )
        for start, stop in LOGICAL_TILES
    )
    transpose_tiles = tuple(
        sum(
            (
                source[row][feature] * adjoint[row][feature]
                for row in range(geometry.source_occupancies)
                for feature in range(start, stop)
            ),
            Fraction(0),
        )
        for start, stop in LOGICAL_TILES
    )
    numerator = sum((value[0] for value in fold), Fraction(0))
    reach = sum((value[1] for value in fold), Fraction(0))
    transpose = sum(transpose_tiles, Fraction(0))
    if numerator != sum(forward_tiles, Fraction(0)) or numerator != transpose:
        raise AssertionError("paired-tile ten-card exact transpose identity failed")
    if reach <= 0:
        raise AssertionError("paired-tile ten-card exact reach is nonpositive")
    return TenCardAuthority(
        source=source,
        compatible_source_ranks=tuple(compatible_ranks),
        covectors=tuple(covectors),
        fold=tuple(fold),
        adjoint=tuple(adjoint),
        forward_tiles=forward_tiles,
        transpose_tiles=transpose_tiles,
        numerator=numerator,
        reach=reach,
        transpose=transpose,
    )


@dataclass(frozen=True, slots=True)
class QueryWeightEvidence:
    records: tuple[int, ...]
    maximum_absolute_error: float
    nonzero_low_count: int
    reporting_digest: str
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return all(self.gates.values())


def _query_weight_evidence(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
) -> QueryWeightEvidence:
    records = tuple(
        record
        for record in (0, 1, 17, 127, 511, 1258, 1259)
        if record < fixture.geometry.labeled_query_records
    )
    device_records = cp.asarray(np.asarray(records, dtype=np.int64))
    output = cp.empty((len(records), 2), dtype=cp.float64)
    _launch(
        kernels["selected_query_weights"],
        len(records),
        (
            device_records,
            np.int32(len(records)),
            resident.query_hands,
            resident.unary,
            resident.factors,
            resident.unary_offsets,
            resident.mixture,
            output,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    actual = output.get()
    unary = fixture.unary_weights.reshape(-1)
    factors = fixture.mode_factors.reshape(-1)
    maximum_error = Fraction(0)
    byte_replay = True
    parent_float_changed = False
    for index, record in enumerate(records):
        h4 = int(fixture.query_hand_indices[record, 0])
        h5 = int(fixture.query_hand_indices[record, 1])
        indices = (
            int(fixture.unary_offsets[3]),
            int(fixture.unary_offsets[4]) + h4,
            int(fixture.unary_offsets[5]) + h5,
        )
        pair = _pair_weight_host(
            float(fixture.mixture_weights[0]), unary, factors, indices
        )
        observed = _pair_from_array(actual[index])
        byte_replay = byte_replay and (
            np.float64(observed.high).tobytes() == np.float64(pair.high).tobytes()
            and np.float64(observed.low).tobytes() == np.float64(pair.low).tobytes()
        )
        exact = Fraction.from_float(float(fixture.mixture_weights[0]))
        for factor_index in indices:
            exact *= Fraction.from_float(float(unary[factor_index]))
            exact *= Fraction.from_float(float(factors[factor_index]))
        maximum_error = max(maximum_error, abs(observed.exact - exact))
        parent_float = float(fixture.mixture_weights[0])
        for factor_index in indices:
            parent_float *= float(unary[factor_index]) * float(
                factors[factor_index]
            )
        parent_float_changed = parent_float_changed or (
            Fraction.from_float(parent_float) != observed.exact
        )
    engineered_factors = tuple(
        float.fromhex(value)
        for value in (
            "0x1.63d3845f675c1p+20",
            "0x1.7fc2db67fa0b7p-12",
            "0x1.1dbb9a650799bp-17",
            "0x1.64ef5e4c36dbdp-14",
            "0x1.032870c1035adp+0",
            "0x1.59f30835c21f6p-17",
        )
    )
    engineered = FloatPair(0.7, 0.0)
    for factor in engineered_factors:
        engineered = _pair_times_float64_host(engineered, factor)
    engineered_preproduct = FloatPair(0.7, 0.0)
    for index in range(0, len(engineered_factors), 2):
        engineered_preproduct = _pair_times_float64_host(
            engineered_preproduct,
            engineered_factors[index] * engineered_factors[index + 1],
        )
    engineered_reversed = FloatPair(0.7, 0.0)
    for factor in reversed(engineered_factors):
        engineered_reversed = _pair_times_float64_host(
            engineered_reversed, factor
        )
    return QueryWeightEvidence(
        records=records,
        maximum_absolute_error=float(maximum_error),
        nonzero_low_count=int(np.count_nonzero(actual[:, 1])),
        reporting_digest=_pair_digest(actual),
        gates=MappingProxyType(
            {
                "host_device_byte_replay": byte_replay,
                "finite": bool(np.all(np.isfinite(actual))),
                "nonzero_low_lane": bool(np.any(actual[:, 1] != 0.0)),
                "parent_float_helper_mutation_changes_value": parent_float_changed,
                "engineered_factor_preproduct_mutation_rejected": (
                    engineered_preproduct.exact != engineered.exact
                ),
                "engineered_factor_order_mutation_rejected": (
                    engineered_reversed.exact != engineered.exact
                ),
            }
        ),
    )


def _direct_forward_samples(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    source_table: Any,
    selected_records: Sequence[int],
    global_start: int,
    logical_width: int,
) -> tuple[np.ndarray, np.ndarray, tuple[int, ...]]:
    """Evaluate selected compatible rows and folds without the recurrence."""

    features = _tile_boundary_features(global_start, global_start + logical_width)
    records = np.asarray(selected_records, dtype=np.int64)
    masks = np.asarray(
        [fixture.query_masks[int(record)] for record in records], dtype=np.uint64
    )
    device_masks = cp.asarray(masks, dtype=cp.uint64)
    device_records = cp.asarray(records, dtype=cp.int64)
    device_features = cp.asarray(np.asarray(features, dtype=np.int32))
    query_output = cp.empty(
        (len(records), len(features), 2), dtype=cp.float64
    )
    fold_output = cp.empty((len(records), 4), dtype=cp.float64)
    source_offset = cardinality_offsets(
        fixture.available_cards, SOURCE_CARDS
    )[SOURCE_CARDS]
    _launch(
        kernels["direct_selected_queries_tile"],
        len(records) * len(features),
        (
            source_table,
            np.int64(source_offset),
            np.int64(fixture.geometry.source_occupancies),
            np.int32(fixture.available_cards),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            device_masks,
            np.int32(len(records)),
            device_features,
            np.int32(len(features)),
            np.int32(global_start),
            np.int32(logical_width),
            query_output,
        ),
    )
    _launch(
        kernels["direct_selected_fold_tile"],
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
            np.int32(logical_width),
            np.int32(SOURCE_RANK),
            resident.query_hands,
            resident.unary,
            resident.factors,
            resident.unary_offsets,
            resident.mixture,
            resident.transitions[3],
            resident.transitions[4],
            resident.terminal,
            np.int32(fixture.geometry.hand_width),
            np.float64(fixture.sunk_value),
            fold_output,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    return query_output.get(), fold_output.get().reshape(-1, 2, 2), features


def _direct_adjoint_samples(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    source_ranks: Sequence[int],
    global_start: int,
    logical_width: int,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Evaluate selected adjoint rows directly from compatible query records."""

    features = _tile_boundary_features(global_start, global_start + logical_width)
    ranks = cp.asarray(np.asarray(source_ranks, dtype=np.int64))
    device_features = cp.asarray(np.asarray(features, dtype=np.int32))
    output = cp.empty((len(source_ranks), len(features), 2), dtype=cp.float64)
    _launch(
        kernels["direct_selected_adjoint_tile"],
        len(source_ranks) * len(features),
        (
            ranks,
            np.int32(len(source_ranks)),
            device_features,
            np.int32(len(features)),
            np.int32(global_start),
            np.int32(logical_width),
            np.int32(fixture.available_cards),
            resident.query_masks,
            np.int64(fixture.geometry.labeled_query_records),
            np.int32(SOURCE_RANK),
            resident.query_hands,
            resident.unary,
            resident.factors,
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
    return output.get(), features


def _launch_source_tile(
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    table: Any,
    source_offset: int,
    rank_start: int,
    records: int,
    global_start: int,
    logical_width: int,
) -> None:
    _launch(
        kernels["source_coefficients_tile"],
        records,
        (
            table,
            np.int64(source_offset),
            np.int64(rank_start),
            np.int64(records),
            np.int32(global_start),
            np.int32(logical_width),
            np.int32(PHYSICAL_STRIDE_WIDTH),
            np.int32(fixture.available_cards),
            np.int32(fixture.geometry.hand_width),
            np.int32(fixture.pair_to_hand.shape[1]),
            np.int32(SOURCE_RANK),
            resident.pairings,
            resident.pair_to_hand,
            resident.unary,
            resident.factors,
            resident.unary_offsets,
            resident.transitions[0],
            resident.transitions[1],
            resident.transitions[2],
        ),
    )


def _forward_once(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    *,
    global_start: int,
    logical_width: int,
    query_chunk: int,
    table: Any,
    compatible: Any,
    numerator_high: Any,
    numerator_low: Any,
    source_ranks: Sequence[int],
    query_records: Sequence[int],
    collect_full: bool,
    collect_direct: bool,
) -> dict[str, object]:
    """Run one deterministic paired forward tile, including one global tree."""

    geometry = fixture.geometry
    tile = _tile_index(global_start)
    physical_active = 2 * logical_width
    source_offset = cardinality_offsets(
        fixture.available_cards, SOURCE_CARDS
    )[SOURCE_CARDS]
    table.fill(_POISON)
    _launch_source_tile(
        kernels,
        resident,
        fixture,
        table,
        source_offset,
        0,
        geometry.source_occupancies,
        global_start,
        logical_width,
    )
    cp.cuda.get_current_stream().synchronize()

    source_samples = _copy_pair_rows(
        table, source_offset, source_ranks, logical_width
    )
    source_digest = _pair_digest(source_samples)
    full_source = (
        table[
            source_offset : source_offset + geometry.source_occupancies,
            :physical_active,
        ].get().reshape(geometry.source_occupancies, logical_width, 2)
        if collect_full
        else None
    )
    source_offset_pass = True
    offset_rank = next((int(rank) for rank in source_ranks if int(rank) > 0), 1)
    if offset_rank < geometry.source_occupancies:
        original = table[source_offset + offset_rank, :physical_active].get()
        table[source_offset + offset_rank, :physical_active].fill(_POISON)
        _launch_source_tile(
            kernels,
            resident,
            fixture,
            table,
            source_offset,
            offset_rank,
            1,
            global_start,
            logical_width,
        )
        cp.cuda.get_current_stream().synchronize()
        replay = table[source_offset + offset_rank, :physical_active].get()
        source_offset_pass = original.tobytes() == replay.tobytes()

    inactive_pass = True
    if physical_active < PHYSICAL_STRIDE_WIDTH:
        for rank in (0, geometry.source_occupancies - 1):
            inactive = table[
                source_offset + rank,
                physical_active:PHYSICAL_STRIDE_WIDTH,
            ].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))

    direct_query = np.empty((0, 0, 2), dtype=np.float64)
    direct_fold = np.empty((0, 2, 2), dtype=np.float64)
    direct_features: tuple[int, ...] = ()
    if collect_direct:
        direct_query, direct_fold, direct_features = _direct_forward_samples(
            cp,
            kernels,
            resident,
            fixture,
            table,
            query_records,
            global_start,
            logical_width,
        )

    _fill_recurrence_tile(
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=SOURCE_CARDS,
        logical_width=logical_width,
    )
    carry_row = cardinality_offsets(fixture.available_cards, SOURCE_CARDS)[5]
    carries = table[carry_row : carry_row + 2].reshape(-1)
    numerator_carry = carries[:128]
    reach_carry = carries[128:256]
    numerator_carry.fill(np.float64(0.0))
    reach_carry.fill(np.float64(0.0))

    selected_lookup = {int(record): index for index, record in enumerate(query_records)}
    query_samples = np.full(
        (len(query_records), logical_width, 2), np.nan, dtype=np.float64
    )
    fold_samples = np.full(
        (len(query_records), 2, 2), np.nan, dtype=np.float64
    )
    full_compatible = (
        np.empty(
            (geometry.labeled_query_records, logical_width, 2), dtype=np.float64
        )
        if collect_full
        else None
    )
    full_fold = (
        np.empty((geometry.labeled_query_records, 2, 2), dtype=np.float64)
        if collect_full
        else None
    )
    contributions = np.empty(
        (geometry.labeled_query_records, 2), dtype=np.float64
    )
    compatible_digest = sha256()
    fold_digest = sha256()
    nonzero_offset = False
    low_counts = {
        "source": int(np.count_nonzero(source_samples[..., 1])),
        "compatible": 0,
        "fold": 0,
        "reduction": 0,
    }
    numeric_scans = [_numeric_scan(source_samples)]
    reach_owner = int(tile == 2)
    for start in range(0, geometry.labeled_query_records, query_chunk):
        records = min(query_chunk, geometry.labeled_query_records - start)
        nonzero_offset = nonzero_offset or start > 0
        compatible.fill(_POISON)
        _launch(
            kernels["signed_targets_tile"],
            records * logical_width,
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
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                compatible,
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        compatible_host = compatible[:records, :physical_active].get().reshape(
            records, logical_width, 2
        )
        compatible_digest.update(memoryview(compatible_host).cast("B"))
        low_counts["compatible"] += int(
            np.count_nonzero(compatible_host[..., 1])
        )
        numeric_scans.append(_numeric_scan(compatible_host))
        if full_compatible is not None:
            full_compatible[start : start + records] = compatible_host
        for record, output_index in selected_lookup.items():
            if start <= record < start + records:
                query_samples[output_index] = compatible_host[record - start]
        if physical_active < PHYSICAL_STRIDE_WIDTH:
            inactive = compatible[
                0, physical_active:PHYSICAL_STRIDE_WIDTH
            ].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))

        _launch(
            kernels["fold_query_tile"],
            records,
            (
                compatible,
                np.int64(start),
                np.int64(records),
                np.int32(global_start),
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(SOURCE_RANK),
                np.int32(reach_owner),
                resident.query_hands,
                resident.unary,
                resident.factors,
                resident.unary_offsets,
                resident.mixture,
                resident.transitions[3],
                resident.transitions[4],
                resident.terminal,
                np.int32(geometry.hand_width),
                np.float64(fixture.sunk_value),
                numerator_high,
                numerator_low,
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        numerator_host = np.column_stack(
            (numerator_high[:records].get(), numerator_low[:records].get())
        )
        reach_host = compatible[:records, :2].get().reshape(records, 2)
        fold_host = np.stack((numerator_host, reach_host), axis=1)
        contributions[start : start + records] = numerator_host
        fold_digest.update(memoryview(np.ascontiguousarray(fold_host)).cast("B"))
        low_counts["fold"] += int(np.count_nonzero(fold_host[..., 1]))
        numeric_scans.append(_numeric_scan(fold_host))
        if full_fold is not None:
            full_fold[start : start + records] = fold_host
        for record, output_index in selected_lookup.items():
            if start <= record < start + records:
                fold_samples[output_index] = fold_host[record - start]

        _reduce_contiguous(
            kernels, numerator_high, numerator_low, records, start, numerator_carry
        )
        if reach_owner:
            _reduce_strided(kernels, compatible, records, start, reach_carry)

    _finalize_pair(
        kernels,
        numerator_carry,
        geometry.labeled_query_records,
        resident.results,
        2 * tile,
    )
    if reach_owner:
        _finalize_pair(
            kernels,
            reach_carry,
            geometry.labeled_query_records,
            resident.results,
            6,
        )
    cp.cuda.get_current_stream().synchronize()
    result_pair = resident.results[2 * tile : 2 * tile + 2].get()
    low_counts["reduction"] = int(result_pair[1] != 0.0)
    if not np.all(np.isfinite(query_samples)) or not np.all(
        np.isfinite(fold_samples)
    ):
        raise AssertionError("paired-tile forward samples were not captured")
    return {
        "source_samples": source_samples,
        "query_samples": query_samples,
        "fold_samples": fold_samples,
        "direct_query": direct_query,
        "direct_fold": direct_fold,
        "direct_features": direct_features,
        "source_digest": source_digest,
        "compatible_digest": compatible_digest.hexdigest(),
        "fold_digest": fold_digest.hexdigest(),
        "full_source": full_source,
        "full_compatible": full_compatible,
        "full_fold": full_fold,
        "contributions": contributions,
        "inactive_pass": inactive_pass,
        "nonzero_offset": nonzero_offset,
        "source_offset_pass": source_offset_pass,
        "low_counts": MappingProxyType(low_counts),
        "numeric_scan": _merge_numeric_scans(numeric_scans),
    }


def _adjoint_once(
    cp: Any,
    kernels: Mapping[str, object],
    resident: _DeviceResident,
    fixture: ConsumerPopulationFixture,
    *,
    global_start: int,
    logical_width: int,
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
    """Run one deterministic paired adjoint tile and its global contraction."""

    geometry = fixture.geometry
    tile = _tile_index(global_start)
    physical_active = 2 * logical_width
    query_offset = cardinality_offsets(
        fixture.available_cards, QUERY_CARDS
    )[QUERY_CARDS]
    table.fill(_POISON)
    nonzero_query_offset = False
    covector_low_count = 0
    numeric_scans: list[tuple[bool, int, int | None, int | None]] = []
    for occupancy_start in range(
        0, geometry.query_occupancies, query_occupancy_chunk
    ):
        occupancies = min(
            query_occupancy_chunk,
            geometry.query_occupancies - occupancy_start,
        )
        records = occupancies * QUERY_LABELS
        record_start = occupancy_start * QUERY_LABELS
        nonzero_query_offset = nonzero_query_offset or occupancy_start > 0
        covector.fill(_POISON)
        _launch(
            kernels["build_numerator_covector_tile"],
            records * logical_width,
            (
                covector,
                np.int64(record_start),
                np.int64(records),
                np.int32(global_start),
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(SOURCE_RANK),
                resident.query_hands,
                resident.unary,
                resident.factors,
                resident.unary_offsets,
                resident.mixture,
                resident.transitions[3],
                resident.transitions[4],
                resident.terminal,
                np.int32(geometry.hand_width),
                np.float64(fixture.sunk_value),
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        covector_probe = covector[
            : min(records, 32), :physical_active
        ].get().reshape(min(records, 32), logical_width, 2)
        covector_low_count += int(np.count_nonzero(covector_probe[..., 1]))
        numeric_scans.append(_numeric_scan(covector_probe))
        _launch(
            kernels["aggregate_query_labels_tile"],
            occupancies * logical_width,
            (
                covector,
                np.int64(occupancy_start),
                np.int64(occupancies),
                np.int32(QUERY_LABELS),
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int64(query_offset),
                np.int32(int(skip_last_label)),
                table,
            ),
        )
    cp.cuda.get_current_stream().synchronize()
    inactive_pass = True
    if physical_active < PHYSICAL_STRIDE_WIDTH:
        for rank in (0, geometry.query_occupancies - 1):
            inactive = table[
                query_offset + rank,
                physical_active:PHYSICAL_STRIDE_WIDTH,
            ].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))

    _fill_recurrence_tile(
        kernels,
        table,
        available_cards=fixture.available_cards,
        source_cards=QUERY_CARDS,
        logical_width=logical_width,
    )
    carry = covector.reshape(-1)[:128]
    carry.fill(np.float64(0.0))

    direct_adjoint = np.empty((0, 0, 2), dtype=np.float64)
    direct_features: tuple[int, ...] = ()
    if collect_direct and not skip_last_label:
        direct_adjoint, direct_features = _direct_adjoint_samples(
            cp,
            kernels,
            resident,
            fixture,
            source_ranks,
            global_start,
            logical_width,
        )

    selected_lookup = {int(rank): index for index, rank in enumerate(source_ranks)}
    adjoint_samples = np.full(
        (len(source_ranks), logical_width, 2), np.nan, dtype=np.float64
    )
    full_adjoint = (
        np.empty((geometry.source_occupancies, logical_width, 2), dtype=np.float64)
        if collect_full
        else None
    )
    contributions = np.empty((geometry.source_occupancies, 2), dtype=np.float64)
    digest = sha256()
    nonzero_source_offset = False
    adjoint_low_count = 0
    contraction_low_count = 0
    for start in range(0, geometry.source_occupancies, source_chunk):
        records = min(source_chunk, geometry.source_occupancies - start)
        nonzero_source_offset = nonzero_source_offset or start > 0
        unique.fill(_POISON)
        _launch(
            kernels["signed_targets_tile"],
            records * logical_width,
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
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                unique,
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        unique_host = unique[:records, :physical_active].get().reshape(
            records, logical_width, 2
        )
        digest.update(memoryview(unique_host).cast("B"))
        adjoint_low_count += int(np.count_nonzero(unique_host[..., 1]))
        numeric_scans.append(_numeric_scan(unique_host))
        if full_adjoint is not None:
            full_adjoint[start : start + records] = unique_host
        for rank, output_index in selected_lookup.items():
            if start <= rank < start + records:
                adjoint_samples[output_index] = unique_host[rank - start]
        if physical_active < PHYSICAL_STRIDE_WIDTH:
            inactive = unique[0, physical_active:PHYSICAL_STRIDE_WIDTH].get()
            inactive_pass = inactive_pass and bool(np.all(inactive == _POISON))

        _launch(
            kernels["source_adjoint_contract_tile"],
            records,
            (
                unique,
                np.int64(start),
                np.int64(records),
                np.int32(global_start),
                np.int32(logical_width),
                np.int32(PHYSICAL_STRIDE_WIDTH),
                np.int32(fixture.available_cards),
                np.int32(geometry.hand_width),
                np.int32(fixture.pair_to_hand.shape[1]),
                np.int32(SOURCE_RANK),
                resident.pairings,
                resident.pair_to_hand,
                resident.unary,
                resident.factors,
                resident.unary_offsets,
                resident.transitions[0],
                resident.transitions[1],
                resident.transitions[2],
            ),
        )
        cp.cuda.get_current_stream().synchronize()
        contribution_host = unique[:records, :2].get().reshape(records, 2)
        contributions[start : start + records] = contribution_host
        contraction_low_count += int(np.count_nonzero(contribution_host[:, 1]))
        numeric_scans.append(_numeric_scan(contribution_host))
        _reduce_strided(kernels, unique, records, start, carry)

    _finalize_pair(
        kernels,
        carry,
        geometry.source_occupancies,
        resident.results,
        2 * tile,
    )
    cp.cuda.get_current_stream().synchronize()
    result_pair = resident.results[2 * tile : 2 * tile + 2].get()
    if not skip_last_label and not np.all(np.isfinite(adjoint_samples)):
        raise AssertionError("paired-tile adjoint samples were not captured")
    return {
        "adjoint_samples": adjoint_samples,
        "direct_adjoint": direct_adjoint,
        "direct_features": direct_features,
        "adjoint_digest": digest.hexdigest(),
        "full_adjoint": full_adjoint,
        "contributions": contributions,
        "inactive_pass": inactive_pass,
        "nonzero_query_offset": nonzero_query_offset,
        "nonzero_source_offset": nonzero_source_offset,
        "low_counts": MappingProxyType(
            {
                "covector": covector_low_count,
                "adjoint": adjoint_low_count,
                "contraction": contraction_low_count,
                "reduction": int(result_pair[1] != 0.0),
            }
        ),
        "numeric_scan": _merge_numeric_scans(numeric_scans),
    }


@dataclass(frozen=True, slots=True)
class PairedPopulationExecution:
    available_cards: int
    tile_order: tuple[tuple[int, int], ...]
    forward_query_chunk: int
    adjoint_query_occupancy_chunk: int
    adjoint_source_chunk: int
    forward_tiles: tuple[FloatPair, FloatPair, FloatPair]
    numerator: FloatPair
    reach: FloatPair
    conditional_value: Fraction
    transpose_tiles: tuple[FloatPair, FloatPair, FloatPair]
    transpose: FloatPair
    source_samples: np.ndarray
    query_samples: np.ndarray
    fold_samples: np.ndarray
    adjoint_samples: np.ndarray
    direct_query_samples: np.ndarray
    direct_fold_samples: np.ndarray
    direct_adjoint_samples: np.ndarray
    source_tile_digests: tuple[str, str, str]
    compatible_tile_digests: tuple[str, str, str]
    fold_tile_digests: tuple[str, str, str]
    adjoint_tile_digests: tuple[str, str, str]
    full_source: np.ndarray | None
    full_compatible: np.ndarray | None
    full_fold: np.ndarray | None
    full_adjoint: np.ndarray | None
    forward_contribution_tiles: tuple[np.ndarray, np.ndarray, np.ndarray]
    transpose_contribution_tiles: tuple[np.ndarray, np.ndarray, np.ndarray]
    repeat_byte_identity: bool
    inactive_poison_pass: bool
    source_offset_control_pass: bool
    nonzero_query_offset_observed: bool
    nonzero_source_offset_observed: bool
    forward_released_before_adjoint: bool
    accumulator_lifecycle_pass: bool
    missing_label_changed_result: bool | None
    low_lane_counts: Mapping[str, int]
    stored_numeric_scan: tuple[bool, int, int | None, int | None]
    maximum_pool_total_bytes: int
    maximum_host_numeric_bytes: int
    released_pool_used_bytes: int
    released_pool_total_bytes: int
    released_pinned_blocks: int
    wall_ms: float


def _unchanged_result_slots(
    before: np.ndarray,
    after: np.ndarray,
    changed_slots: set[int],
) -> bool:
    return all(
        before[index].tobytes() == after[index].tobytes()
        for index in range(8)
        if index not in changed_slots
    )


def _run_device_population(
    cp: Any,
    kernels: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
    *,
    forward_query_chunk: int,
    adjoint_query_occupancy_chunk: int,
    adjoint_source_chunk: int,
    tile_order: tuple[tuple[int, int], ...] = LOGICAL_TILES,
    missing_label_control: bool = False,
) -> PairedPopulationExecution:
    """Run one bounded population with ordinal storage and repeat replay."""

    started = perf_counter()
    geometry = fixture.geometry
    if tuple(sorted(tile_order)) != tuple(sorted(LOGICAL_TILES)):
        raise ValueError("paired-tile execution order is not the frozen partition")
    chunks = (
        forward_query_chunk,
        adjoint_query_occupancy_chunk,
        adjoint_source_chunk,
    )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in chunks
    ):
        raise ValueError("paired-tile chunk sizes must be positive integers")
    forward_query_chunk = min(
        forward_query_chunk, geometry.labeled_query_records
    )
    adjoint_query_occupancy_chunk = min(
        adjoint_query_occupancy_chunk, geometry.query_occupancies
    )
    adjoint_source_chunk = min(adjoint_source_chunk, geometry.source_occupancies)

    pool = cp.get_default_memory_pool()
    pinned = cp.get_default_pinned_memory_pool()
    pool.free_all_blocks()
    pinned.free_all_blocks()
    if int(pool.used_bytes()) != 0 or int(pool.total_bytes()) != 0:
        raise RuntimeError("paired-tile pool was nonzero before bounded birth")

    source_ranks, query_records = _sample_rows(fixture.available_cards)
    resident = _allocate_resident(cp, fixture)
    maximum_pool_total = int(pool.total_bytes())
    collect_full = fixture.available_cards == 10
    collect_direct = fixture.available_cards == 25

    source_samples = np.full(
        (len(source_ranks), TOTAL_FEATURE_WIDTH, 2), np.nan, dtype=np.float64
    )
    query_samples = np.full(
        (len(query_records), TOTAL_FEATURE_WIDTH, 2), np.nan, dtype=np.float64
    )
    adjoint_samples = np.full(
        (len(source_ranks), TOTAL_FEATURE_WIDTH, 2), np.nan, dtype=np.float64
    )
    direct_query = np.full_like(query_samples, np.nan)
    direct_adjoint = np.full_like(adjoint_samples, np.nan)
    fold_parts = np.empty((3, len(query_records), 2, 2), dtype=np.float64)
    direct_fold_parts = np.empty_like(fold_parts)
    full_source = (
        np.empty(
            (geometry.source_occupancies, TOTAL_FEATURE_WIDTH, 2),
            dtype=np.float64,
        )
        if collect_full
        else None
    )
    full_compatible = (
        np.empty(
            (geometry.labeled_query_records, TOTAL_FEATURE_WIDTH, 2),
            dtype=np.float64,
        )
        if collect_full
        else None
    )
    full_fold_parts = (
        np.empty(
            (3, geometry.labeled_query_records, 2, 2), dtype=np.float64
        )
        if collect_full
        else None
    )
    full_adjoint = (
        np.empty(
            (geometry.source_occupancies, TOTAL_FEATURE_WIDTH, 2),
            dtype=np.float64,
        )
        if collect_full
        else None
    )
    source_digests = ["", "", ""]
    compatible_digests = ["", "", ""]
    fold_digests = ["", "", ""]
    adjoint_digests = ["", "", ""]
    forward_contributions: list[np.ndarray | None] = [None, None, None]
    transpose_contributions: list[np.ndarray | None] = [None, None, None]
    repeat_identity = True
    poison_pass = True
    source_offset_pass = True
    accumulator_pass = True
    nonzero_query_offset = False
    nonzero_source_offset = False
    low_counts: dict[str, int] = {}
    numeric_scans: list[tuple[bool, int, int | None, int | None]] = []

    forward_rows = sum(
        comb(fixture.available_cards, level)
        for level in range(SOURCE_CARDS + 1)
    )
    table = cp.empty((forward_rows, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64)
    compatible = cp.empty(
        (forward_query_chunk, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64
    )
    numerator_high = cp.empty(forward_query_chunk, dtype=cp.float64)
    numerator_low = cp.empty(forward_query_chunk, dtype=cp.float64)
    maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    for global_start, stop in tile_order:
        tile = _tile_index(global_start)
        logical_width = stop - global_start
        before = resident.results.get()
        first = _forward_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            logical_width=logical_width,
            query_chunk=forward_query_chunk,
            table=table,
            compatible=compatible,
            numerator_high=numerator_high,
            numerator_low=numerator_low,
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
            logical_width=logical_width,
            query_chunk=forward_query_chunk,
            table=table,
            compatible=compatible,
            numerator_high=numerator_high,
            numerator_low=numerator_low,
            source_ranks=source_ranks,
            query_records=query_records,
            collect_full=collect_full,
            collect_direct=collect_direct,
        )
        after_second = resident.results.get()
        repeat_keys = (
            "source_samples",
            "query_samples",
            "fold_samples",
            "direct_query",
            "direct_fold",
            "direct_features",
            "source_digest",
            "compatible_digest",
            "fold_digest",
            "contributions",
            "inactive_pass",
            "nonzero_offset",
            "source_offset_pass",
            "low_counts",
            "numeric_scan",
        )
        repeat_identity = repeat_identity and _same_capture(
            first, second, repeat_keys
        )
        repeat_identity = repeat_identity and (
            after_first.tobytes() == after_second.tobytes()
        )
        changed = {2 * tile, 2 * tile + 1}
        if tile == 2:
            changed.update((6, 7))
        accumulator_pass = accumulator_pass and _unchanged_result_slots(
            before, after_second, changed
        )

        source_samples[:, global_start:stop] = second["source_samples"]
        query_samples[:, global_start:stop] = second["query_samples"]
        fold_parts[tile] = second["fold_samples"]
        direct_features = tuple(int(value) for value in second["direct_features"])
        if collect_direct:
            direct_query[:, direct_features] = second["direct_query"]
            direct_fold_parts[tile] = second["direct_fold"]
        if full_source is not None and full_compatible is not None:
            full_source[:, global_start:stop] = second["full_source"]
            full_compatible[:, global_start:stop] = second["full_compatible"]
        if full_fold_parts is not None:
            full_fold_parts[tile] = second["full_fold"]
        source_digests[tile] = str(second["source_digest"])
        compatible_digests[tile] = str(second["compatible_digest"])
        fold_digests[tile] = str(second["fold_digest"])
        forward_contributions[tile] = second["contributions"]
        poison_pass = poison_pass and bool(second["inactive_pass"])
        source_offset_pass = source_offset_pass and bool(
            second["source_offset_pass"]
        )
        nonzero_query_offset = nonzero_query_offset or bool(
            second["nonzero_offset"]
        )
        for stage, count in dict(second["low_counts"]).items():
            low_counts[f"forward_{stage}_tile_{tile}"] = int(count)
        numeric_scans.append(second["numeric_scan"])
        maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))
        del first, second

    forward_result = resident.results.get()
    forward_tiles = tuple(
        _pair_from_array(forward_result[2 * tile : 2 * tile + 2])
        for tile in range(3)
    )
    numerator = _combine_pair_scalars(forward_tiles)
    reach = _pair_from_array(forward_result[6:8])
    if not (
        math.isfinite(numerator.high)
        and math.isfinite(numerator.low)
        and math.isfinite(reach.high)
        and math.isfinite(reach.low)
        and reach.exact > 0
    ):
        raise ArithmeticError("paired-tile bounded forward scalar is invalid")
    conditional_value = numerator.exact / reach.exact

    fold_numerator = _combine_pair_arrays(
        [fold_parts[tile, :, 0, :] for tile in range(3)]
    )
    fold_samples_combined = np.stack(
        (fold_numerator, fold_parts[2, :, 1, :]), axis=1
    )
    direct_fold_combined = np.empty_like(fold_samples_combined)
    if collect_direct:
        direct_fold_combined[:, 0, :] = _combine_pair_arrays(
            [direct_fold_parts[tile, :, 0, :] for tile in range(3)]
        )
        direct_fold_combined[:, 1, :] = direct_fold_parts[2, :, 1, :]
    else:
        direct_fold_combined.fill(np.nan)
    full_fold = None
    if full_fold_parts is not None:
        full_fold = np.empty_like(full_fold_parts[0])
        full_fold[:, 0, :] = _combine_pair_arrays(
            [full_fold_parts[tile, :, 0, :] for tile in range(3)]
        )
        full_fold[:, 1, :] = full_fold_parts[2, :, 1, :]

    del table, compatible, numerator_high, numerator_low
    gc.collect()
    pool.free_all_blocks()
    forward_pool_total = int(pool.total_bytes())
    resident.results.fill(np.float64(0.0))
    cp.cuda.get_current_stream().synchronize()
    accumulator_pass = accumulator_pass and _positive_zero_slots(
        resident.results.get()
    )
    forward_released = forward_pool_total < maximum_pool_total

    adjoint_rows = sum(
        comb(fixture.available_cards, level)
        for level in range(QUERY_CARDS + 1)
    )
    table = cp.empty((adjoint_rows, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64)
    covector = cp.empty(
        (adjoint_query_occupancy_chunk * QUERY_LABELS, PHYSICAL_STRIDE_WIDTH),
        dtype=cp.float64,
    )
    unique = cp.empty(
        (adjoint_source_chunk, PHYSICAL_STRIDE_WIDTH), dtype=cp.float64
    )
    maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))

    for global_start, stop in tile_order:
        tile = _tile_index(global_start)
        logical_width = stop - global_start
        before = resident.results.get()
        first = _adjoint_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=global_start,
            logical_width=logical_width,
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
            logical_width=logical_width,
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
        repeat_keys = (
            "adjoint_samples",
            "direct_adjoint",
            "direct_features",
            "adjoint_digest",
            "contributions",
            "inactive_pass",
            "nonzero_query_offset",
            "nonzero_source_offset",
            "low_counts",
            "numeric_scan",
        )
        repeat_identity = repeat_identity and _same_capture(
            first, second, repeat_keys
        )
        repeat_identity = repeat_identity and (
            after_first.tobytes() == after_second.tobytes()
        )
        changed = {2 * tile, 2 * tile + 1}
        accumulator_pass = accumulator_pass and _unchanged_result_slots(
            before, after_second, changed
        )
        adjoint_samples[:, global_start:stop] = second["adjoint_samples"]
        direct_features = tuple(int(value) for value in second["direct_features"])
        if collect_direct:
            direct_adjoint[:, direct_features] = second["direct_adjoint"]
        if full_adjoint is not None:
            full_adjoint[:, global_start:stop] = second["full_adjoint"]
        adjoint_digests[tile] = str(second["adjoint_digest"])
        transpose_contributions[tile] = second["contributions"]
        poison_pass = poison_pass and bool(second["inactive_pass"])
        nonzero_query_offset = nonzero_query_offset or bool(
            second["nonzero_query_offset"]
        )
        nonzero_source_offset = nonzero_source_offset or bool(
            second["nonzero_source_offset"]
        )
        for stage, count in dict(second["low_counts"]).items():
            low_counts[f"adjoint_{stage}_tile_{tile}"] = int(count)
        numeric_scans.append(second["numeric_scan"])
        maximum_pool_total = max(maximum_pool_total, int(pool.total_bytes()))
        del first, second

    transpose_result = resident.results.get()
    transpose_tiles = tuple(
        _pair_from_array(transpose_result[2 * tile : 2 * tile + 2])
        for tile in range(3)
    )
    transpose = _combine_pair_scalars(transpose_tiles)
    accumulator_pass = accumulator_pass and all(
        transpose_result[index].tobytes() == np.float64(0.0).tobytes()
        for index in (6, 7)
    )

    missing_changed: bool | None = None
    if missing_label_control:
        saved = transpose_result.copy()
        mutated = _adjoint_once(
            cp,
            kernels,
            resident,
            fixture,
            global_start=0,
            logical_width=64,
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
        mutated_pair = resident.results[:2].get()
        missing_changed = (
            str(mutated["adjoint_digest"]) != adjoint_digests[0]
            and mutated_pair.tobytes() != saved[:2].tobytes()
        )
        resident.results.set(saved)
        del mutated

    if any(value is None for value in forward_contributions):
        raise AssertionError("paired-tile forward contributions were omitted")
    if any(value is None for value in transpose_contributions):
        raise AssertionError("paired-tile transpose contributions were omitted")
    forward_tuple = tuple(forward_contributions)
    transpose_tuple = tuple(transpose_contributions)
    assert all(isinstance(value, np.ndarray) for value in forward_tuple)
    assert all(isinstance(value, np.ndarray) for value in transpose_tuple)

    retained_host_bytes = sum(
        values.nbytes
        for values in (
            source_samples,
            query_samples,
            adjoint_samples,
            direct_query,
            direct_adjoint,
            fold_parts,
            direct_fold_parts,
            *(value for value in forward_tuple if isinstance(value, np.ndarray)),
            *(value for value in transpose_tuple if isinstance(value, np.ndarray)),
        )
    )
    chunk_host_bytes = max(
        forward_query_chunk * PHYSICAL_STRIDE_WIDTH * 8,
        adjoint_source_chunk * PHYSICAL_STRIDE_WIDTH * 8,
    )
    maximum_host_numeric = retained_host_bytes + 2 * chunk_host_bytes

    del table, covector, unique, resident
    gc.collect()
    pool.free_all_blocks()
    pinned.free_all_blocks()
    released_used = int(pool.used_bytes())
    released_total = int(pool.total_bytes())
    released_pinned = int(pinned.n_free_blocks())
    return PairedPopulationExecution(
        available_cards=fixture.available_cards,
        tile_order=tile_order,
        forward_query_chunk=forward_query_chunk,
        adjoint_query_occupancy_chunk=adjoint_query_occupancy_chunk,
        adjoint_source_chunk=adjoint_source_chunk,
        forward_tiles=forward_tiles,  # type: ignore[arg-type]
        numerator=numerator,
        reach=reach,
        conditional_value=conditional_value,
        transpose_tiles=transpose_tiles,  # type: ignore[arg-type]
        transpose=transpose,
        source_samples=source_samples[:, _BOUNDARY_FEATURES, :],
        query_samples=query_samples[:, _BOUNDARY_FEATURES, :],
        fold_samples=fold_samples_combined,
        adjoint_samples=adjoint_samples[:, _BOUNDARY_FEATURES, :],
        direct_query_samples=(
            direct_query[:, _BOUNDARY_FEATURES, :]
            if collect_direct
            else np.empty((0, len(_BOUNDARY_FEATURES), 2), dtype=np.float64)
        ),
        direct_fold_samples=(
            direct_fold_combined
            if collect_direct
            else np.empty((0, 2, 2), dtype=np.float64)
        ),
        direct_adjoint_samples=(
            direct_adjoint[:, _BOUNDARY_FEATURES, :]
            if collect_direct
            else np.empty((0, len(_BOUNDARY_FEATURES), 2), dtype=np.float64)
        ),
        source_tile_digests=tuple(source_digests),  # type: ignore[arg-type]
        compatible_tile_digests=tuple(compatible_digests),  # type: ignore[arg-type]
        fold_tile_digests=tuple(fold_digests),  # type: ignore[arg-type]
        adjoint_tile_digests=tuple(adjoint_digests),  # type: ignore[arg-type]
        full_source=full_source,
        full_compatible=full_compatible,
        full_fold=full_fold,
        full_adjoint=full_adjoint,
        forward_contribution_tiles=forward_tuple,  # type: ignore[arg-type]
        transpose_contribution_tiles=transpose_tuple,  # type: ignore[arg-type]
        repeat_byte_identity=repeat_identity,
        inactive_poison_pass=poison_pass,
        source_offset_control_pass=source_offset_pass,
        nonzero_query_offset_observed=nonzero_query_offset,
        nonzero_source_offset_observed=nonzero_source_offset,
        forward_released_before_adjoint=forward_released,
        accumulator_lifecycle_pass=accumulator_pass,
        missing_label_changed_result=missing_changed,
        low_lane_counts=MappingProxyType(low_counts),
        stored_numeric_scan=_merge_numeric_scans(numeric_scans),
        maximum_pool_total_bytes=maximum_pool_total,
        maximum_host_numeric_bytes=maximum_host_numeric,
        released_pool_used_bytes=released_used,
        released_pool_total_bytes=released_total,
        released_pinned_blocks=released_pinned,
        wall_ms=(perf_counter() - started) * 1000.0,
    )


@dataclass(frozen=True, slots=True)
class BoundedPairedPopulationEvidence:
    available_cards: int
    wall_ms: float
    scalar_pairs: Mapping[str, tuple[float, float]]
    conditional_value: float
    maximum_errors: Mapping[str, float]
    exact_stream_diagnostics: Mapping[str, float]
    exponent_envelope: tuple[int | None, int | None]
    low_lane_counts: Mapping[str, int]
    telemetry: Mapping[str, int]
    reporting_digests: Mapping[str, str]
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return all(self.gates.values())


@dataclass(frozen=True, slots=True)
class BoundedCompensatedTileReport:
    config_v1_sha256: str
    config_v2_sha256: str
    bridge_sha256: str
    topology_sha256: str
    runtime: CudaRuntimeIdentity
    primitive: PrimitiveEvidence
    query_weight: QueryWeightEvidence
    kernel_resources: Mapping[str, Mapping[str, int]]
    ten_card: BoundedPairedPopulationEvidence
    twenty_five_card: BoundedPairedPopulationEvidence
    actual_execution_calls_before: int
    actual_execution_calls_after: int
    actual_numeric_allocation_calls_before: int
    actual_numeric_allocation_calls_after: int
    actual_scientific_calls_before: int
    actual_scientific_calls_after: int
    laboratory_wall_ms: float
    gates: Mapping[str, bool]

    @property
    def all_gates_pass(self) -> bool:
        return (
            self.primitive.all_gates_pass
            and self.query_weight.all_gates_pass
            and self.ten_card.all_gates_pass
            and self.twenty_five_card.all_gates_pass
            and all(self.gates.values())
        )


def _pair_tuple(value: FloatPair) -> tuple[float, float]:
    return value.high, value.low


def _scalar_pair_map(
    execution: PairedPopulationExecution,
) -> Mapping[str, tuple[float, float]]:
    values: dict[str, tuple[float, float]] = {
        f"forward_tile_{index}": _pair_tuple(value)
        for index, value in enumerate(execution.forward_tiles)
    }
    values.update(
        {
            "numerator": _pair_tuple(execution.numerator),
            "reach": _pair_tuple(execution.reach),
            **{
                f"transpose_tile_{index}": _pair_tuple(value)
                for index, value in enumerate(execution.transpose_tiles)
            },
            "transpose": _pair_tuple(execution.transpose),
        }
    )
    return MappingProxyType(values)


def _reporting_digest(*arrays: np.ndarray) -> str:
    digest = sha256()
    for values in arrays:
        contiguous = np.ascontiguousarray(values)
        digest.update(repr((contiguous.shape, contiguous.dtype.str)).encode("ascii"))
        digest.update(memoryview(contiguous).cast("B"))
    return digest.hexdigest()


def _pair_sequence_array(values: Sequence[FloatPair]) -> np.ndarray:
    return np.asarray([_pair_tuple(value) for value in values], dtype=np.float64)


def _execution_scalar_array(execution: PairedPopulationExecution) -> np.ndarray:
    return _pair_sequence_array(
        (
            *execution.forward_tiles,
            execution.numerator,
            execution.reach,
            *execution.transpose_tiles,
            execution.transpose,
        )
    )


def _execution_byte_identity(
    left: PairedPopulationExecution,
    right: PairedPopulationExecution,
) -> bool:
    arrays = (
        "source_samples",
        "query_samples",
        "fold_samples",
        "adjoint_samples",
        "direct_query_samples",
        "direct_fold_samples",
        "direct_adjoint_samples",
    )
    if any(
        not _pair_arrays_byte_equal(getattr(left, name), getattr(right, name))
        for name in arrays
    ):
        return False
    for name in ("full_source", "full_compatible", "full_fold", "full_adjoint"):
        left_value = getattr(left, name)
        right_value = getattr(right, name)
        if (left_value is None) != (right_value is None):
            return False
        if left_value is not None and right_value is not None:
            if not _pair_arrays_byte_equal(left_value, right_value):
                return False
    for left_parts, right_parts in (
        (left.forward_contribution_tiles, right.forward_contribution_tiles),
        (left.transpose_contribution_tiles, right.transpose_contribution_tiles),
    ):
        if any(
            not _pair_arrays_byte_equal(left_part, right_part)
            for left_part, right_part in zip(left_parts, right_parts, strict=True)
        ):
            return False
    return (
        _pair_arrays_byte_equal(
            _execution_scalar_array(left), _execution_scalar_array(right)
        )
        and left.source_tile_digests == right.source_tile_digests
        and left.compatible_tile_digests == right.compatible_tile_digests
        and left.fold_tile_digests == right.fold_tile_digests
        and left.adjoint_tile_digests == right.adjoint_tile_digests
    )


def _captured_stream(
    contribution_tiles: Sequence[np.ndarray],
) -> Fraction:
    return sum((_exact_pair_sum(values) for values in contribution_tiles), Fraction(0))


def _high_only_stream(contribution_tiles: Sequence[np.ndarray]) -> Fraction:
    return sum(
        (
            Fraction.from_float(float(high))
            for values in contribution_tiles
            for high in values[:, 0]
        ),
        Fraction(0),
    )


def _fraction_limit(config: Mapping[str, object], name: str) -> Fraction:
    limits = config.get("numerical_limits")
    if not isinstance(limits, Mapping):
        raise ValueError("paired-tile numerical limits are malformed")
    return Fraction.from_float(float(limits[name]))


def _fraction_errors_valid(values: Mapping[str, Fraction]) -> bool:
    return all(value >= 0 for value in values.values())


def _kernel_resource_report(
    cp: Any, kernels: Mapping[str, object]
) -> Mapping[str, Mapping[str, int]]:
    attributes = MappingProxyType(
        {
            "local_size_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES,
            "registers": cp.cuda.driver.CU_FUNC_ATTRIBUTE_NUM_REGS,
            "shared_size_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES,
            "maximum_threads_per_block": (
                cp.cuda.driver.CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK
            ),
        }
    )
    return MappingProxyType(
        {
            name: MappingProxyType(
                {
                    label: int(cp.cuda.driver.funcGetAttribute(attribute, kernel.ptr))
                    for label, attribute in attributes.items()
                }
            )
            for name, kernel in kernels.items()
        }
    )


def _ten_card_evidence(
    cp: Any,
    kernels: Mapping[str, object],
    config: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
) -> BoundedPairedPopulationEvidence:
    controls = config.get("bounded_device_controls")
    if not isinstance(controls, Mapping):
        raise ValueError("paired-tile bounded controls are malformed")
    exact_control = controls.get("exact_population_10")
    if not isinstance(exact_control, Mapping):
        raise ValueError("paired-tile ten-card controls are malformed")
    chunks = (
        int(exact_control["forward_query_record_chunk"]),
        int(exact_control["adjoint_query_occupancy_chunk"]),
        int(exact_control["adjoint_source_occupancy_chunk"]),
    )
    authority = _ten_card_authority(fixture)
    normal = _run_device_population(
        cp,
        kernels,
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        tile_order=LOGICAL_TILES,
        missing_label_control=True,
    )
    reverse = _run_device_population(
        cp,
        kernels,
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        tile_order=tuple(reversed(LOGICAL_TILES)),
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
        raise AssertionError("paired-tile ten-card run omitted complete rows")
    assert normal.full_source is not None
    assert normal.full_compatible is not None
    assert normal.full_fold is not None
    assert normal.full_adjoint is not None

    source_expected = tuple(
        value for row in authority.source for value in row
    )
    compatible_expected = tuple(
        authority.source[source_rank][feature]
        for source_rank in authority.compatible_source_ranks
        for feature in range(TOTAL_FEATURE_WIDTH)
    )
    fold_expected = tuple(value for row in authority.fold for value in row)
    adjoint_expected = tuple(value for row in authority.adjoint for value in row)
    source_abs, source_rel = _maximum_pair_errors(
        normal.full_source, source_expected
    )
    compatible_abs, compatible_rel = _maximum_pair_errors(
        normal.full_compatible, compatible_expected
    )
    fold_abs, fold_rel = _maximum_pair_errors(normal.full_fold, fold_expected)
    adjoint_abs, adjoint_rel = _maximum_pair_errors(
        normal.full_adjoint, adjoint_expected
    )
    scalar_expected = (
        *authority.forward_tiles,
        authority.numerator,
        authority.reach,
        *authority.transpose_tiles,
        authority.transpose,
    )
    scalar_abs, scalar_rel = _maximum_pair_errors(
        _execution_scalar_array(normal), scalar_expected
    )
    conditional_error = abs(
        normal.conditional_value - authority.numerator / authority.reach
    )

    captured_forward = _captured_stream(normal.forward_contribution_tiles)
    captured_transpose = _captured_stream(normal.transpose_contribution_tiles)
    device_forward_error = abs(normal.numerator.exact - captured_forward)
    device_transpose_error = abs(normal.transpose.exact - captured_transpose)
    captured_residual = abs(captured_forward - captured_transpose)
    captured_relative = _scale_relative(captured_residual, captured_forward)
    device_residual = abs(normal.numerator.exact - normal.transpose.exact)
    device_relative = _scale_relative(device_residual, normal.numerator.exact)
    high_only_forward = _high_only_stream(normal.forward_contribution_tiles)
    high_only_transpose = _high_only_stream(normal.transpose_contribution_tiles)
    high_only_residual = abs(high_only_forward - high_only_transpose)

    errors_fraction = MappingProxyType(
        {
            "source_absolute": source_abs,
            "source_scale_relative": source_rel,
            "forward_row_absolute": compatible_abs,
            "forward_row_scale_relative": compatible_rel,
            "fold_absolute": fold_abs,
            "fold_scale_relative": fold_rel,
            "adjoint_row_absolute": adjoint_abs,
            "adjoint_row_scale_relative": adjoint_rel,
            "scalar_absolute": scalar_abs,
            "scalar_scale_relative": scalar_rel,
            "conditional_chip_absolute": conditional_error,
            "captured_forward_transpose_absolute": captured_residual,
            "captured_forward_transpose_relative": captured_relative,
            "device_forward_transpose_absolute": device_residual,
            "device_forward_transpose_relative": device_relative,
            "device_reducer_forward_absolute": device_forward_error,
            "device_reducer_transpose_absolute": device_transpose_error,
        }
    )
    absolute = _fraction_limit(config, "bounded_transpose_dot_absolute")
    relative = _fraction_limit(config, "bounded_scale_normalized_relative")
    source_limit = _fraction_limit(config, "bounded_source_sample_absolute")
    forward_limit = _fraction_limit(config, "bounded_forward_row_absolute")
    fold_limit = _fraction_limit(config, "bounded_fold_absolute")
    adjoint_limit = _fraction_limit(config, "bounded_adjoint_row_absolute")

    low_counts = dict(normal.low_lane_counts)
    natural_required = (
        *(f"forward_{stage}_tile_{tile}" for tile in (0, 2) for stage in (
            "source", "compatible", "fold", "reduction"
        )),
        *(f"adjoint_{stage}_tile_{tile}" for tile in range(3) for stage in (
            "covector", "adjoint"
        )),
        *(f"adjoint_{stage}_tile_{tile}" for tile in (0, 2) for stage in (
            "contraction", "reduction"
        )),
    )
    structural_zero_tile = (
        authority.forward_tiles[1] == 0
        and authority.transpose_tiles[1] == 0
        and np.count_nonzero(normal.full_source[:, 64:128]) == 0
        and np.count_nonzero(normal.full_compatible[:, 64:128]) == 0
        and np.count_nonzero(normal.forward_contribution_tiles[1]) == 0
        and np.count_nonzero(normal.transpose_contribution_tiles[1]) == 0
    )
    wall_ms = normal.wall_ms + reverse.wall_ms
    scan = _merge_numeric_scans(
        (normal.stored_numeric_scan, reverse.stored_numeric_scan)
    )
    gates = MappingProxyType(
        {
            "complete_fraction_source_absolute": source_abs <= source_limit,
            "complete_fraction_source_relative": source_rel <= relative,
            "complete_fraction_forward_absolute": compatible_abs <= forward_limit,
            "complete_fraction_forward_relative": compatible_rel <= relative,
            "complete_fraction_fold_absolute": fold_abs <= fold_limit,
            "complete_fraction_fold_relative": fold_rel <= relative,
            "complete_fraction_adjoint_absolute": adjoint_abs <= adjoint_limit,
            "complete_fraction_adjoint_relative": adjoint_rel <= relative,
            "complete_fraction_scalar_absolute": scalar_abs <= absolute,
            "complete_fraction_scalar_relative": scalar_rel <= relative,
            "conditional_chip_exact_fraction": conditional_error <= absolute,
            "captured_forward_transpose_absolute": captured_residual <= absolute,
            "captured_forward_transpose_relative": captured_relative <= relative,
            "device_forward_transpose_absolute": device_residual <= absolute,
            "device_forward_transpose_relative": device_relative <= relative,
            "device_reducer_forward_absolute": device_forward_error <= absolute,
            "device_reducer_transpose_absolute": device_transpose_error <= absolute,
            "normal_reverse_tile_order_byte_identity": _execution_byte_identity(
                normal, reverse
            ),
            "repeat_snapshot_restore_byte_identity": normal.repeat_byte_identity
            and reverse.repeat_byte_identity,
            "inactive_final_tile_poison": normal.inactive_poison_pass
            and reverse.inactive_poison_pass,
            "source_global_offset_control": normal.source_offset_control_pass
            and reverse.source_offset_control_pass,
            "nonzero_query_offset": normal.nonzero_query_offset_observed,
            "nonzero_source_offset": normal.nonzero_source_offset_observed,
            "forward_release_before_adjoint": normal.forward_released_before_adjoint
            and reverse.forward_released_before_adjoint,
            "accumulator_lifecycle": normal.accumulator_lifecycle_pass
            and reverse.accumulator_lifecycle_pass,
            "missing_label_mutation_rejected": (
                normal.missing_label_changed_result is True
            ),
            "natural_structural_zero_tile_honest": structural_zero_tile,
            "low_lane_detecting_mass_where_operator_mass_exists": all(
                low_counts.get(name, 0) > 0 for name in natural_required
            ),
            "dropped_low_stream_mutation_rejected": (
                high_only_forward != captured_forward
                and high_only_transpose != captured_transpose
            ),
            "finite_stored_components": scan[0],
            "no_unexpected_stored_subnormal": scan[1] == 0,
            "pool_release": normal.released_pool_used_bytes == 0
            and normal.released_pool_total_bytes == 0
            and normal.released_pinned_blocks == 0
            and reverse.released_pool_used_bytes == 0
            and reverse.released_pool_total_bytes == 0
            and reverse.released_pinned_blocks == 0,
            "finite_two_sided_errors": _fraction_errors_valid(errors_fraction),
            "chip_units": Fraction(-10) <= normal.conditional_value <= Fraction(50),
        }
    )
    return BoundedPairedPopulationEvidence(
        available_cards=10,
        wall_ms=wall_ms,
        scalar_pairs=_scalar_pair_map(normal),
        conditional_value=float(normal.conditional_value),
        maximum_errors=MappingProxyType(
            {name: float(value) for name, value in errors_fraction.items()}
        ),
        exact_stream_diagnostics=MappingProxyType(
            {
                "captured_forward": float(captured_forward),
                "captured_transpose": float(captured_transpose),
                "high_only_forward": float(high_only_forward),
                "high_only_transpose": float(high_only_transpose),
                "high_only_residual": float(high_only_residual),
            }
        ),
        exponent_envelope=(scan[2], scan[3]),
        low_lane_counts=MappingProxyType(low_counts),
        telemetry=MappingProxyType(
            {
                "maximum_pool_total_bytes": max(
                    normal.maximum_pool_total_bytes,
                    reverse.maximum_pool_total_bytes,
                ),
                "maximum_host_numeric_bytes": max(
                    normal.maximum_host_numeric_bytes,
                    reverse.maximum_host_numeric_bytes,
                ),
                "stored_subnormal_count": scan[1],
            }
        ),
        reporting_digests=MappingProxyType(
            {
                "source": _reporting_digest(normal.full_source),
                "compatible": _reporting_digest(normal.full_compatible),
                "fold": _reporting_digest(normal.full_fold),
                "adjoint": _reporting_digest(normal.full_adjoint),
                "contribution_streams": _reporting_digest(
                    *normal.forward_contribution_tiles,
                    *normal.transpose_contribution_tiles,
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
) -> BoundedPairedPopulationEvidence:
    controls = config.get("bounded_device_controls")
    if not isinstance(controls, Mapping):
        raise ValueError("paired-tile bounded controls are malformed")
    multichunk = controls.get("multichunk_population_25")
    if not isinstance(multichunk, Mapping):
        raise ValueError("paired-tile 25-card controls are malformed")
    default_chunks = (
        int(multichunk["default_forward_query_record_chunk"]),
        int(multichunk["default_adjoint_query_occupancy_chunk"]),
        int(multichunk["default_adjoint_source_occupancy_chunk"]),
    )
    alternate_chunks = (
        int(multichunk["alternate_forward_query_record_chunk"]),
        int(multichunk["alternate_adjoint_query_occupancy_chunk"]),
        int(multichunk["alternate_adjoint_source_occupancy_chunk"]),
    )
    default = _run_device_population(
        cp,
        kernels,
        fixture,
        forward_query_chunk=default_chunks[0],
        adjoint_query_occupancy_chunk=default_chunks[1],
        adjoint_source_chunk=default_chunks[2],
        tile_order=LOGICAL_TILES,
    )
    alternate = _run_device_population(
        cp,
        kernels,
        fixture,
        forward_query_chunk=alternate_chunks[0],
        adjoint_query_occupancy_chunk=alternate_chunks[1],
        adjoint_source_chunk=alternate_chunks[2],
        tile_order=tuple(reversed(LOGICAL_TILES)),
    )

    source_ranks, _ = _sample_rows(25)
    source_expected = tuple(
        _parent._source_row_exact(fixture, rank)[feature]
        for rank in source_ranks
        for feature in _BOUNDARY_FEATURES
    )
    source_abs, source_rel = _maximum_pair_errors(
        default.source_samples, source_expected
    )
    direct_query_expected = tuple(
        _pair_from_array(pair).exact
        for pair in default.direct_query_samples.reshape(-1, 2)
    )
    query_abs, query_rel = _maximum_pair_errors(
        default.query_samples, direct_query_expected
    )
    direct_fold_expected = tuple(
        _pair_from_array(pair).exact
        for pair in default.direct_fold_samples.reshape(-1, 2)
    )
    fold_abs, fold_rel = _maximum_pair_errors(
        default.fold_samples, direct_fold_expected
    )
    direct_adjoint_expected = tuple(
        _pair_from_array(pair).exact
        for pair in default.direct_adjoint_samples.reshape(-1, 2)
    )
    adjoint_abs, adjoint_rel = _maximum_pair_errors(
        default.adjoint_samples, direct_adjoint_expected
    )

    captured_forward = _captured_stream(default.forward_contribution_tiles)
    captured_transpose = _captured_stream(default.transpose_contribution_tiles)
    device_forward_error = abs(default.numerator.exact - captured_forward)
    device_transpose_error = abs(default.transpose.exact - captured_transpose)
    captured_residual = abs(captured_forward - captured_transpose)
    captured_relative = _scale_relative(captured_residual, captured_forward)
    device_residual = abs(default.numerator.exact - default.transpose.exact)
    device_relative = _scale_relative(device_residual, default.numerator.exact)
    high_only_forward = _high_only_stream(default.forward_contribution_tiles)
    high_only_transpose = _high_only_stream(default.transpose_contribution_tiles)
    high_only_residual = abs(high_only_forward - high_only_transpose)

    errors_fraction = MappingProxyType(
        {
            "source_absolute": source_abs,
            "source_scale_relative": source_rel,
            "direct_forward_absolute": query_abs,
            "direct_forward_scale_relative": query_rel,
            "direct_fold_absolute": fold_abs,
            "direct_fold_scale_relative": fold_rel,
            "direct_adjoint_absolute": adjoint_abs,
            "direct_adjoint_scale_relative": adjoint_rel,
            "captured_forward_transpose_absolute": captured_residual,
            "captured_forward_transpose_relative": captured_relative,
            "device_forward_transpose_absolute": device_residual,
            "device_forward_transpose_relative": device_relative,
            "device_reducer_forward_absolute": device_forward_error,
            "device_reducer_transpose_absolute": device_transpose_error,
        }
    )
    absolute = _fraction_limit(config, "bounded_transpose_dot_absolute")
    relative = _fraction_limit(config, "bounded_scale_normalized_relative")
    source_limit = _fraction_limit(config, "bounded_source_sample_absolute")
    forward_limit = _fraction_limit(config, "bounded_forward_row_absolute")
    fold_limit = _fraction_limit(config, "bounded_fold_absolute")
    adjoint_limit = _fraction_limit(config, "bounded_adjoint_row_absolute")

    required_low_names = tuple(
        [
            f"forward_{stage}_tile_{tile}"
            for tile in range(3)
            for stage in ("source", "compatible", "fold", "reduction")
        ]
        + [
            f"adjoint_{stage}_tile_{tile}"
            for tile in range(3)
            for stage in ("covector", "adjoint", "contraction", "reduction")
        ]
    )
    low_counts = {
        f"default_{name}": int(value)
        for name, value in default.low_lane_counts.items()
    }
    low_counts.update(
        {
            f"alternate_{name}": int(value)
            for name, value in alternate.low_lane_counts.items()
        }
    )
    scan = _merge_numeric_scans(
        (default.stored_numeric_scan, alternate.stored_numeric_scan)
    )
    wall_ms = default.wall_ms + alternate.wall_ms
    gates = MappingProxyType(
        {
            "selected_fraction_source_absolute": source_abs <= source_limit,
            "selected_fraction_source_relative": source_rel <= relative,
            "selected_direct_forward_absolute": query_abs <= forward_limit,
            "selected_direct_forward_relative": query_rel <= relative,
            "selected_direct_fold_absolute": fold_abs <= fold_limit,
            "selected_direct_fold_relative": fold_rel <= relative,
            "selected_direct_adjoint_absolute": adjoint_abs <= adjoint_limit,
            "selected_direct_adjoint_relative": adjoint_rel <= relative,
            "captured_forward_transpose_absolute": captured_residual <= absolute,
            "captured_forward_transpose_relative": captured_relative <= relative,
            "device_forward_transpose_absolute": device_residual <= absolute,
            "device_forward_transpose_relative": device_relative <= relative,
            "device_reducer_forward_absolute": device_forward_error <= absolute,
            "device_reducer_transpose_absolute": device_transpose_error <= absolute,
            "default_alternate_chunk_and_tile_order_byte_identity": (
                _execution_byte_identity(default, alternate)
            ),
            "repeat_snapshot_restore_byte_identity": default.repeat_byte_identity
            and alternate.repeat_byte_identity,
            "inactive_final_tile_poison": default.inactive_poison_pass
            and alternate.inactive_poison_pass,
            "source_global_offset_control": default.source_offset_control_pass
            and alternate.source_offset_control_pass,
            "nonzero_query_offset": default.nonzero_query_offset_observed
            and alternate.nonzero_query_offset_observed,
            "nonzero_source_offset": default.nonzero_source_offset_observed
            and alternate.nonzero_source_offset_observed,
            "forward_release_before_adjoint": (
                default.forward_released_before_adjoint
                and alternate.forward_released_before_adjoint
            ),
            "accumulator_lifecycle": default.accumulator_lifecycle_pass
            and alternate.accumulator_lifecycle_pass,
            "low_lane_detecting_mass_every_tile_and_stage": all(
                default.low_lane_counts.get(name, 0) > 0
                and alternate.low_lane_counts.get(name, 0) > 0
                for name in required_low_names
            ),
            "dropped_low_stream_mutation_rejected": (
                high_only_forward != captured_forward
                and high_only_transpose != captured_transpose
            ),
            "finite_stored_components": scan[0],
            "no_unexpected_stored_subnormal": scan[1] == 0,
            "bounded_device_numeric_cap": max(
                default.maximum_pool_total_bytes,
                alternate.maximum_pool_total_bytes,
            )
            <= int(multichunk["maximum_device_numeric_bytes"])
            if "maximum_device_numeric_bytes" in multichunk
            else max(
                default.maximum_pool_total_bytes,
                alternate.maximum_pool_total_bytes,
            )
            <= 1_000_000_000,
            "bounded_host_numeric_cap": max(
                default.maximum_host_numeric_bytes,
                alternate.maximum_host_numeric_bytes,
            )
            <= 2_000_000_000,
            "pool_release": default.released_pool_used_bytes == 0
            and default.released_pool_total_bytes == 0
            and default.released_pinned_blocks == 0
            and alternate.released_pool_used_bytes == 0
            and alternate.released_pool_total_bytes == 0
            and alternate.released_pinned_blocks == 0,
            "population_wall": wall_ms
            <= float(multichunk["population_wall_limit_ms"]),
            "finite_two_sided_errors": _fraction_errors_valid(errors_fraction),
            "chip_units": Fraction(-10)
            <= default.conditional_value
            <= Fraction(50),
        }
    )
    return BoundedPairedPopulationEvidence(
        available_cards=25,
        wall_ms=wall_ms,
        scalar_pairs=_scalar_pair_map(default),
        conditional_value=float(default.conditional_value),
        maximum_errors=MappingProxyType(
            {name: float(value) for name, value in errors_fraction.items()}
        ),
        exact_stream_diagnostics=MappingProxyType(
            {
                "captured_forward": float(captured_forward),
                "captured_transpose": float(captured_transpose),
                "high_only_forward": float(high_only_forward),
                "high_only_transpose": float(high_only_transpose),
                "high_only_residual": float(high_only_residual),
            }
        ),
        exponent_envelope=(scan[2], scan[3]),
        low_lane_counts=MappingProxyType(low_counts),
        telemetry=MappingProxyType(
            {
                "maximum_pool_total_bytes": max(
                    default.maximum_pool_total_bytes,
                    alternate.maximum_pool_total_bytes,
                ),
                "maximum_host_numeric_bytes": max(
                    default.maximum_host_numeric_bytes,
                    alternate.maximum_host_numeric_bytes,
                ),
                "stored_subnormal_count": scan[1],
            }
        ),
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
                "contribution_streams": _reporting_digest(
                    *default.forward_contribution_tiles,
                    *default.transpose_contribution_tiles,
                ),
            }
        ),
        gates=gates,
    )


__all__ = [
    "BoundedCompensatedTileReport",
    "BoundedPairedPopulationEvidence",
    "CudaRuntimeIdentity",
    "FloatPair",
    "LOGICAL_TILES",
    "PHYSICAL_STRIDE_WIDTH",
    "PREREGISTERED_CONFIG_V1_SHA256",
    "PREREGISTERED_CONFIG_V2_SHA256",
    "PairedPopulationExecution",
    "PrimitiveEvidence",
    "QueryWeightEvidence",
    "actual_execution_call_count",
    "actual_numeric_allocation_call_count",
    "actual_scientific_call_count",
    "bounded_execution_call_count",
    "canonical_lf_sha256",
    "compile_consumer_population_fixture",
    "cupy_import_call_count",
    "load_preregistered_compensated_tile_configs",
    "population_geometry",
    "verify_preregistered_compensated_tile_contract",
]
