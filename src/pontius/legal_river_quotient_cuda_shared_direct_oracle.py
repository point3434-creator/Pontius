"""Source-only shared selected query/fold oracle from ADR-0417.

This module builds and validates CUDA source text but never imports CuPy,
compiles, loads, launches, owns a result, or opens population 25.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import struct
from types import MappingProxyType
from typing import Mapping, Sequence

from . import legal_river_quotient_cuda_compensated_tiles as _paired
from . import legal_river_quotient_cuda_compensated_work_preflight as _v4


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-oracle-v1.json"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
PREREGISTERED_CONFIG_SHA256 = (
    "48ad381d36767bdce973c464fb3bfc0d925cac4e45a790129b50324098a9dab7"
)
PREREGISTRATION_ADR_RELATIVE_PATH = (
    "docs/decisions/ADR-0417-preregister-the-shared-selected-direct-oracle.md"
)
PREREGISTRATION_ADR_SHA256 = (
    "27320cb4f5cd9ec1972ffdd9d2e4e9e95a4398fdee3347b37cdeb3286fa77372"
)
PARENT_V4_SOURCE_SHA256 = (
    "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa"
)
PARENT_PAIRED_SOURCE_SHA256 = (
    "03a7efb35243b8d13d495a7f80838170055096c8e9ae73d2cc723e3d29f1020d"
)
PROSPECTIVE_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_quotient_cuda_shared_direct_oracle_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)

FloatPair = _paired.FloatPair
_pair_add = _paired._pair_add_host
_ZERO = FloatPair(0.0, 0.0)
_BOUNDARY_FEATURES = (0, 1, 63, 64, 127, 128, 174, 175)
_LOGICAL_TILES = ((0, 64), (64, 128), (128, 176))


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct source path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_shared_direct_config(
    path: Path = _CONFIG,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("shared-direct config path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("shared-direct config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != (
        PREREGISTERED_CONFIG_SHA256
    ):
        raise ValueError("shared-direct config differs from ADR-0417")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != (
        "legal-river-quotient-cuda-shared-direct-oracle-preregistration-v1"
    ):
        raise ValueError("shared-direct config schema differs")
    return parsed


@dataclass(frozen=True, slots=True)
class SharedDirectWork:
    available_cards: int
    source_occupancies: int
    compatible_sources_per_query: int
    eliminated_query_source_unranks: int
    eliminated_query_compatible_boundary_pair_adds: int
    replacement_boundary_pair_copies: int
    retained_fold_source_unranks: int
    retained_fold_compatible_coefficient_pair_adds: int


def derive_shared_direct_work(available_cards: int) -> SharedDirectWork:
    if isinstance(available_cards, bool) or available_cards not in (10, 22, 25):
        raise ValueError("shared-direct work population must be 10, 22, or 25")
    selected = 16
    executions = 4
    tiles = 3
    width = 176
    boundary = 8
    source = comb(available_cards, 6)
    compatible = comb(available_cards - 4, 6)
    return SharedDirectWork(
        available_cards=available_cards,
        source_occupancies=source,
        compatible_sources_per_query=compatible,
        eliminated_query_source_unranks=selected * source * tiles * executions,
        eliminated_query_compatible_boundary_pair_adds=(
            selected * compatible * boundary * executions
        ),
        replacement_boundary_pair_copies=selected * boundary * executions,
        retained_fold_source_unranks=selected * source * tiles * executions,
        retained_fold_compatible_coefficient_pair_adds=(
            selected * compatible * width * executions
        ),
    )


def verify_preregistered_shared_direct_contract(
    config: Mapping[str, object] | None = None,
) -> None:
    value = load_preregistered_shared_direct_config() if config is None else config
    parent = value.get("parent_identity")
    if not isinstance(parent, Mapping):
        raise ValueError("shared-direct parent identity is malformed")
    expected_sources = {
        PREREGISTRATION_ADR_RELATIVE_PATH: PREREGISTRATION_ADR_SHA256,
        "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py": (
            PARENT_V4_SOURCE_SHA256
        ),
        "src/pontius/legal_river_quotient_cuda_compensated_tiles.py": (
            PARENT_PAIRED_SOURCE_SHA256
        ),
    }
    for relative, expected in expected_sources.items():
        if canonical_lf_sha256(_ROOT / relative) != expected:
            raise ValueError(f"shared-direct parent differs: {relative}")
    if (_ROOT / PROSPECTIVE_RESULT_RELATIVE_PATH).exists():
        raise ValueError("shared-direct prospective result must remain absent")
    if (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists():
        raise ValueError("shared-direct reserved actual result must remain absent")

    work = value.get("exact_work_reduction")
    if not isinstance(work, Mapping):
        raise ValueError("shared-direct work config is malformed")
    keys = {
        10: "population_10",
        22: "population_22",
        25: "population_25_geometry_only",
    }
    for cards, key in keys.items():
        stored = work.get(key)
        if not isinstance(stored, Mapping):
            raise ValueError("shared-direct population work is malformed")
        derived = derive_shared_direct_work(cards)
        expected = {
            "source_occupancies": derived.source_occupancies,
            "compatible_sources_per_query": derived.compatible_sources_per_query,
            "eliminated_query_source_unranks": (
                derived.eliminated_query_source_unranks
            ),
            "eliminated_query_compatible_boundary_pair_adds": (
                derived.eliminated_query_compatible_boundary_pair_adds
            ),
            "retained_fold_source_unranks": derived.retained_fold_source_unranks,
            "retained_fold_compatible_coefficient_pair_adds": (
                derived.retained_fold_compatible_coefficient_pair_adds
            ),
        }
        if any(stored.get(name) != number for name, number in expected.items()):
            raise ValueError(f"shared-direct work differs for population {cards}")
        if work.get("replacement_boundary_pair_copies_per_complete_campaign") != (
            derived.replacement_boundary_pair_copies
        ):
            raise ValueError("shared-direct boundary-copy work differs")


def _kernel_span(source: str, name: str) -> tuple[int, int]:
    if not isinstance(source, str):
        raise TypeError("shared-direct CUDA source must be text")
    marker = f'extern "C" __global__ void {name}('
    start = source.find(marker)
    if start < 0 or source.find(marker, start + len(marker)) >= 0:
        raise ValueError(f"shared-direct CUDA kernel occurrence differs: {name}")
    stop = source.find('\nextern "C" __global__ void ', start + len(marker))
    return start, len(source) if stop < 0 else stop


def _balanced_block_stop(source: str, open_brace: int) -> int:
    if open_brace < 0 or open_brace >= len(source) or source[open_brace] != "{":
        raise ValueError("shared-direct CUDA block opening differs")
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("shared-direct CUDA block is unterminated")


_FUSED_FOLD_KERNEL = r'''extern "C" __global__ void direct_selected_fold_tile(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *selected_query_masks,
    const long long *selected_query_records, int query_count,
    const int *global_features, int feature_count,
    int global_feature_start, int logical_width, int source_rank,
    const int *query_hands, const double *unary, const double *factors,
    const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *query_output, double *output
) {
    int query = blockDim.x * blockIdx.x + threadIdx.x;
    if (query >= query_count) return;
    long long record = selected_query_records[query];
    int h4, h5;
    DD weight = query_weight_pair(
        record, query_hands, unary, factors, unary_offsets, mixture, &h4, &h5
    );
    unsigned long long query_mask = selected_query_masks[query];
    double coefficients[128];
    for (int column = 0; column < 2 * logical_width; ++column)
        coefficients[column] = 0.0;
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_mask(row, n, 6);
        if (source_mask & query_mask) continue;
        for (int logical = 0; logical < logical_width; ++logical) {
            DD prior = load_pair(coefficients, logical);
            DD term = load_pair(
                source + (source_level_offset + row) * physical_stride, logical
            );
            store_pair(coefficients, logical, pair_add(prior, term));
        }
    }
    for (int feature_index = 0; feature_index < feature_count; ++feature_index) {
        int logical = global_features[feature_index] - global_feature_start;
        DD value = (logical >= 0 && logical < logical_width)
            ? load_pair(coefficients, logical)
            : make_dd(0.0, 0.0);
        int index = query * feature_count + feature_index;
        query_output[2 * index] = value.high;
        query_output[2 * index + 1] = value.low;
    }
    DD numerator = make_dd(0.0, 0.0);
    DD reach = make_dd(0.0, 0.0);
    for (int logical = 0; logical < logical_width; ++logical) {
        int global_feature = global_feature_start + logical;
        double payoff;
        if (global_feature == source_rank) payoff = sunk;
        else {
            int state3 = transition3[global_feature];
            int state4 = transition4[state3 * hand_width + h4];
            payoff = terminal[state4 * hand_width + h5];
        }
        DD coefficient = load_pair(coefficients, logical);
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
}'''


def build_shared_direct_cuda_source(
    parent_source: str = _v4.CUDA_SOURCE,
) -> str:
    start, stop = _kernel_span(parent_source, "direct_selected_fold_tile")
    result = parent_source[:start] + _FUSED_FOLD_KERNEL + parent_source[stop:]
    verify_shared_direct_cuda_source(result, parent_source=parent_source)
    return result


def verify_shared_direct_cuda_source(
    source: str,
    *,
    parent_source: str = _v4.CUDA_SOURCE,
) -> None:
    parent_fold_start, parent_fold_stop = _kernel_span(
        parent_source, "direct_selected_fold_tile"
    )
    fold_start, fold_stop = _kernel_span(source, "direct_selected_fold_tile")
    if source[:fold_start] != parent_source[:parent_fold_start] or (
        source[fold_stop:] != parent_source[parent_fold_stop:]
    ):
        raise ValueError("shared-direct source changes more than the fold kernel")
    parent_query = parent_source[slice(*_kernel_span(
        parent_source, "direct_selected_queries_tile"
    ))]
    query = source[slice(*_kernel_span(source, "direct_selected_queries_tile"))]
    if sha256(query.encode("utf-8")).digest() != sha256(
        parent_query.encode("utf-8")
    ).digest():
        raise ValueError("shared-direct reference query kernel differs")
    fold = source[fold_start:fold_stop]
    required = (
        "double *query_output, double *output",
        "for (long long row = 0; row < source_rows; ++row)",
        "unsigned long long source_mask = unrank_mask(row, n, 6);",
        "store_pair(coefficients, logical, pair_add(prior, term));",
        "int logical = global_features[feature_index] - global_feature_start;",
        "query_output[2 * index] = value.high;",
        "query_output[2 * index + 1] = value.low;",
        "numerator = pair_add(",
    )
    if any(fold.count(fragment) != 1 for fragment in required):
        raise ValueError("shared-direct fused fold contract differs")
    if fold.count("unrank_mask(row, n, 6)") != 1:
        raise ValueError("shared-direct fused fold unrank count differs")
    row_marker = "for (long long row = 0; row < source_rows; ++row)"
    row_start = fold.index(row_marker)
    row_open = fold.index("{", row_start + len(row_marker))
    row_stop = _balanced_block_stop(fold, row_open)
    copy_start = fold.index(
        "for (int feature_index = 0; feature_index < feature_count; ++feature_index)"
    )
    numerator_start = fold.index("DD numerator = make_dd(0.0, 0.0);")
    if not row_stop <= copy_start < numerator_start:
        raise ValueError("shared-direct boundary copy is not after source traversal")
    copy_open = fold.index("{", copy_start)
    copy_stop = _balanced_block_stop(fold, copy_open)
    copy = fold[copy_start:copy_stop]
    if "pair_add(" in copy or "store_pair(" in copy:
        raise ValueError("shared-direct boundary copy performs pair arithmetic")


CUDA_SOURCE = build_shared_direct_cuda_source()


def _validate_sequence_inputs(
    source_rows: Sequence[Sequence[FloatPair]],
    compatible: Sequence[bool],
    boundary_features: Sequence[int],
) -> int:
    if not source_rows:
        raise ValueError("shared-direct sequence requires source rows")
    width = len(source_rows[0])
    if width <= 0 or any(len(row) != width for row in source_rows):
        raise ValueError("shared-direct sequence row width differs")
    if len(compatible) != len(source_rows) or any(
        not isinstance(value, bool) for value in compatible
    ):
        raise ValueError("shared-direct compatibility mask differs")
    if not boundary_features or any(
        isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < width
        for index in boundary_features
    ):
        raise ValueError("shared-direct boundary features differ")
    if any(not isinstance(value, FloatPair) for row in source_rows for value in row):
        raise TypeError("shared-direct source values must be FloatPair")
    return width


def reference_selected_query_pairs(
    source_rows: Sequence[Sequence[FloatPair]],
    compatible: Sequence[bool],
    boundary_features: Sequence[int],
) -> tuple[FloatPair, ...]:
    _validate_sequence_inputs(source_rows, compatible, boundary_features)
    values = [_ZERO for _ in boundary_features]
    for include, row in zip(compatible, source_rows):
        if not include:
            continue
        for local, feature in enumerate(boundary_features):
            values[local] = _pair_add(values[local], row[feature])
    return tuple(values)


def shared_fold_coefficients_and_query_pairs(
    source_rows: Sequence[Sequence[FloatPair]],
    compatible: Sequence[bool],
    boundary_features: Sequence[int],
) -> tuple[tuple[FloatPair, ...], tuple[FloatPair, ...]]:
    width = _validate_sequence_inputs(source_rows, compatible, boundary_features)
    coefficients = [_ZERO for _ in range(width)]
    for include, row in zip(compatible, source_rows):
        if not include:
            continue
        for logical in range(width):
            coefficients[logical] = _pair_add(coefficients[logical], row[logical])
    query = tuple(coefficients[feature] for feature in boundary_features)
    return tuple(coefficients), query


def _pair_bytes(values: Sequence[FloatPair]) -> bytes:
    return b"".join(struct.pack("<dd", value.high, value.low) for value in values)


def run_shared_direct_sequence_controls() -> Mapping[str, object]:
    leading = (3.14159, -1.0, -1e100, -0.0, -(2.0**53))
    rows = tuple(
        tuple(
            FloatPair(
                float(value * (feature + 1)),
                float(((-1.0) ** (row + feature)) * 2.0 ** (-70 - feature)),
            )
            for feature in range(8)
        )
        for row, value in enumerate(leading)
    )
    compatible = (True, True, True, True, True)
    boundary = (0, 1, 3, 7)
    reference = reference_selected_query_pairs(rows, compatible, boundary)
    coefficients, shared = shared_fold_coefficients_and_query_pairs(
        rows, compatible, boundary
    )
    early = shared_fold_coefficients_and_query_pairs(
        rows[:-1], compatible[:-1], boundary
    )[1]
    reversed_shared = shared_fold_coefficients_and_query_pairs(
        tuple(reversed(rows)), compatible, boundary
    )[1]
    shifted = tuple(coefficients[(feature + 1) % len(coefficients)] for feature in boundary)
    reference_bytes = _pair_bytes(reference)
    shared_bytes = _pair_bytes(shared)
    gates = {
        "shared_query_byte_identity": shared_bytes == reference_bytes,
        "shared_query_exact_identity": all(
            left.exact == right.exact for left, right in zip(reference, shared)
        ),
        "early_copy_mutation_rejected": _pair_bytes(early) != reference_bytes,
        "source_reverse_mutation_rejected": (
            _pair_bytes(reversed_shared) != reference_bytes
        ),
        "boundary_shift_mutation_rejected": _pair_bytes(shifted) != reference_bytes,
        "nonzero_low_lane_control": any(value.low != 0.0 for value in shared),
    }
    return MappingProxyType(
        {
            "schema_version": "legal-river-shared-direct-sequence-control-v1",
            "reference_sha256": sha256(reference_bytes).hexdigest(),
            "shared_sha256": sha256(shared_bytes).hexdigest(),
            "coefficient_sha256": sha256(_pair_bytes(coefficients)).hexdigest(),
            "gates": MappingProxyType(gates),
            "all_gates_pass": all(gates.values()),
        }
    )


def source_seal_report() -> Mapping[str, object]:
    config = load_preregistered_shared_direct_config()
    verify_preregistered_shared_direct_contract(config)
    verify_shared_direct_cuda_source(CUDA_SOURCE)
    sequence = run_shared_direct_sequence_controls()
    work = {cards: derive_shared_direct_work(cards) for cards in (10, 22, 25)}
    gates = {
        "sequence_controls": bool(sequence["all_gates_pass"]),
        "reference_query_span_unchanged": (
            _v4.CUDA_SOURCE[slice(*_kernel_span(
                _v4.CUDA_SOURCE, "direct_selected_queries_tile"
            ))]
            == CUDA_SOURCE[slice(*_kernel_span(
                CUDA_SOURCE, "direct_selected_queries_tile"
            ))]
        ),
        "one_fold_span_replaced": CUDA_SOURCE != _v4.CUDA_SOURCE,
        "population_25_geometry_only": work[25].available_cards == 25,
        "prospective_result_absent": not (
            _ROOT / PROSPECTIVE_RESULT_RELATIVE_PATH
        ).exists(),
        "reserved_actual_absent": not (
            _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ).exists(),
    }
    return MappingProxyType(
        {
            "schema_version": "legal-river-shared-direct-source-seal-report-v1",
            "config_sha256": PREREGISTERED_CONFIG_SHA256,
            "cuda_source_sha256": sha256(CUDA_SOURCE.encode("utf-8")).hexdigest(),
            "sequence": sequence,
            "work": MappingProxyType(work),
            "gates": MappingProxyType(gates),
            "all_gates_pass": all(gates.values()),
        }
    )


__all__ = [
    "CONFIG_RELATIVE_PATH",
    "CUDA_SOURCE",
    "FloatPair",
    "PREREGISTERED_CONFIG_SHA256",
    "PROSPECTIVE_RESULT_RELATIVE_PATH",
    "RESERVED_ACTUAL_RESULT_RELATIVE_PATH",
    "SharedDirectWork",
    "build_shared_direct_cuda_source",
    "canonical_lf_sha256",
    "derive_shared_direct_work",
    "load_preregistered_shared_direct_config",
    "reference_selected_query_pairs",
    "run_shared_direct_sequence_controls",
    "shared_fold_coefficients_and_query_pairs",
    "source_seal_report",
    "verify_preregistered_shared_direct_contract",
    "verify_shared_direct_cuda_source",
]
