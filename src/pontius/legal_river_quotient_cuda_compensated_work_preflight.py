"""Composite ADR-0394/ADR-0395 paired CUDA capacity preflight.

Importing this module is device-free.  The only numerical populations admitted
by this source are 10 and 22 cards.  Population 25 is represented solely by
integer geometry, exact work counts, and an arithmetic projection; it is never
passed to a fixture compiler, allocator, kernel, scalar reader, or gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import gc
from hashlib import sha256
import inspect
import json
import math
from math import comb
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from time import perf_counter_ns
from types import MappingProxyType
from typing import Any, Callable, Mapping, MutableMapping, Sequence

import numpy as np

from . import legal_river_quotient_cuda_compensated_tiles as _paired
from . import legal_river_quotient_cuda_consumer as _consumer
from .gpu_occupied_card_quotient import colex_unrank


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
_CORRECTION_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
_CORRECTION_ADR = (
    _ROOT
    / "docs/decisions/"
    "ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md"
)
PREREGISTERED_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
CORRECTION_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
CORRECTION_ADR_SHA256 = (
    "3a82213ac534b430de1c37c662394451b5c759037b84db0f60817a7486edab4a"
)
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)

SOURCE_CARDS = 6
QUERY_CARDS = 4
QUERY_LABELS = 6
SOURCE_RANK = 175
TOTAL_FEATURE_WIDTH = 176
PHYSICAL_STRIDE_WIDTH = 128
LOGICAL_TILES = ((0, 64), (64, 128), (128, 176))
BOUNDARY_FEATURES = (0, 1, 63, 64, 127, 128, 174, 175)
CALIBRATION_POPULATIONS = (10, 22)
PROJECTION_POPULATION = 25
POPULATION_FAMILIES = (
    "default_chunks_forward_tile_order",
    "alternate_chunks_reverse_tile_order",
)
PHASE_ORDER = (
    "fixture_and_resident_birth",
    "forward_source_and_offset",
    "direct_query",
    "direct_fold",
    "forward_recurrence",
    "forward_signed_targets",
    "forward_fold_and_global_tree",
    "forward_capture_and_digest",
    "forward_release",
    "adjoint_covector_and_labels",
    "adjoint_recurrence_and_signed_sources",
    "direct_adjoint",
    "adjoint_source_contract_and_global_tree",
    "adjoint_capture_digest_and_exact_stream",
    "mutations_and_lifecycle",
    "final_release",
)
CUDA_COMPILE_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)
DIRECT_KERNEL_REGISTER_LIMIT = 255
DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES = 4096
MAXIMUM_RESIDENT_THREAD_BOUND = 131_072
MAXIMUM_RESIDENT_BACKING_BYTES = 536_870_912
FROZEN_DEVICE_RESERVE_BYTES = 2_000_000_000
ELF_MAGIC = b"\x7fELF"

_CUPY_IMPORT_CALLS = 0
_BOUNDED_EXECUTION_CALLS = 0


class CompilerResourceRejection(RuntimeError):
    """A typed pre-calibration compiler/resource contract rejection."""


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_work_preflight_config(
    path: Path = _CONFIG,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("work-preflight config path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("work-preflight config exceeds its byte ceiling")
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight config differs from ADR-0394")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-config-v1"
    ):
        raise ValueError("work-preflight config schema differs")
    return parsed


def load_work_preflight_resource_correction(
    path: Path = _CORRECTION_CONFIG,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("work-preflight correction path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("work-preflight correction exceeds its byte ceiling")
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != CORRECTION_CONFIG_SHA256:
        raise ValueError("work-preflight resource correction differs from ADR-0395")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-resource-correction-v2"
    ):
        raise ValueError("work-preflight resource correction schema differs")
    return parsed


@dataclass(frozen=True, slots=True)
class PopulationGeometry:
    available_cards: int
    hand_width: int
    source_occupancies: int
    source_recurrence_rows: int
    query_occupancies: int
    labeled_query_records: int
    adjoint_recurrence_rows: int
    compatible_sources_per_query_occupancy: int
    compatible_labeled_query_records_per_source: int


def population_geometry(available_cards: int) -> PopulationGeometry:
    """Return pure integer geometry for 10, 22, or projection-only 25."""

    if isinstance(available_cards, bool) or available_cards not in (10, 22, 25):
        raise ValueError("work-preflight population must be 10, 22, or 25")
    return PopulationGeometry(
        available_cards=available_cards,
        hand_width=comb(45, 2),
        source_occupancies=comb(available_cards, SOURCE_CARDS),
        source_recurrence_rows=sum(
            comb(available_cards, level) for level in range(SOURCE_CARDS + 1)
        ),
        query_occupancies=comb(available_cards, QUERY_CARDS),
        labeled_query_records=QUERY_LABELS * comb(available_cards, QUERY_CARDS),
        adjoint_recurrence_rows=sum(
            comb(available_cards, level) for level in range(QUERY_CARDS + 1)
        ),
        compatible_sources_per_query_occupancy=comb(
            available_cards - QUERY_CARDS, SOURCE_CARDS
        ),
        compatible_labeled_query_records_per_source=(
            QUERY_LABELS * comb(available_cards - SOURCE_CARDS, QUERY_CARDS)
        ),
    )


def complete_campaign_work(available_cards: int) -> dict[str, int]:
    """Re-derive every complete two-family/two-repeat work counter."""

    geometry = population_geometry(available_cards)
    executions = len(POPULATION_FAMILIES) * 2
    tile_count = len(LOGICAL_TILES)
    width = TOTAL_FEATURE_WIDTH
    source = geometry.source_occupancies
    query = geometry.query_occupancies
    records = geometry.labeled_query_records
    compatible_sources = geometry.compatible_sources_per_query_occupancy
    compatible_records = geometry.compatible_labeled_query_records_per_source
    selected = 16
    boundary = len(BOUNDARY_FEATURES)
    forward_subset_terms = 1 << QUERY_CARDS
    adjoint_subset_terms = sum(comb(SOURCE_CARDS, level) for level in range(5))
    return {
        "source_pairing_visits": source * 90 * executions * tile_count,
        "source_weight_pair_times_float64": (
            source * 90 * SOURCE_CARDS * executions * tile_count
        ),
        "forward_recurrence_pair_child_adds": (
            executions
            * width
            * sum(comb(available_cards, level) * (available_cards - level)
                  for level in range(SOURCE_CARDS))
        ),
        "forward_pair_divides": (
            executions
            * width
            * sum(comb(available_cards, level) for level in range(SOURCE_CARDS))
        ),
        "forward_signed_subset_pair_terms": (
            executions * records * width * forward_subset_terms
        ),
        "forward_fold_pair_times_pair": executions * records * width,
        "forward_tree_contributions": (
            executions * records * (tile_count + 1)
        ),
        "adjoint_covector_pair_times_float64": executions * records * width,
        "adjoint_label_pair_adds": (
            executions * query * QUERY_LABELS * width
        ),
        "adjoint_recurrence_pair_child_adds": (
            executions
            * width
            * sum(comb(available_cards, level) * (available_cards - level)
                  for level in range(QUERY_CARDS))
        ),
        "adjoint_pair_divides": (
            executions
            * width
            * sum(comb(available_cards, level) for level in range(QUERY_CARDS))
        ),
        "adjoint_signed_subset_pair_terms": (
            executions * source * width * adjoint_subset_terms
        ),
        "adjoint_source_pairing_visits": source * 90 * executions * tile_count,
        "adjoint_source_weight_pair_times_float64": (
            source * 90 * SOURCE_CARDS * executions * tile_count
        ),
        "adjoint_contract_pair_times_pair": executions * source * width,
        "adjoint_tree_contributions": executions * source * tile_count,
        "direct_query_source_unranks": (
            selected * source * tile_count * executions
        ),
        "direct_query_compatible_boundary_pair_adds": (
            selected * compatible_sources * boundary * executions
        ),
        "direct_fold_source_unranks": (
            selected * source * tile_count * executions
        ),
        "direct_fold_compatible_coefficient_pair_adds": (
            selected * compatible_sources * width * executions
        ),
        "direct_fold_final_feature_pair_products": (
            selected * width * executions
        ),
        "direct_adjoint_source_unranks": (
            selected * tile_count * executions
        ),
        "direct_adjoint_query_record_visits": (
            selected * records * tile_count * executions
        ),
        "direct_adjoint_compatible_query_weight_builds": (
            selected * compatible_records * tile_count * executions
        ),
        "direct_adjoint_compatible_boundary_pair_adds": (
            selected * compatible_records * boundary * executions
        ),
    }


_FROZEN_CHUNKS = MappingProxyType(
    {
        10: ((17, 3, 11), (13, 2, 7)),
        22: ((32768, 4096, 32768), (16381, 2047, 16381)),
        25: ((65536, 10922, 32768), (32767, 4093, 16381)),
    }
)

_PHASE_WORK_COUNTERS = MappingProxyType(
    {
        "forward_source_and_offset": (
            "source_pairing_visits",
            "source_weight_pair_times_float64",
        ),
        "direct_query": (
            "direct_query_compatible_boundary_pair_adds",
            "direct_query_source_unranks",
        ),
        "direct_fold": (
            "direct_fold_compatible_coefficient_pair_adds",
            "direct_fold_source_unranks",
            "direct_fold_final_feature_pair_products",
        ),
        "forward_recurrence": (
            "forward_recurrence_pair_child_adds",
            "forward_pair_divides",
        ),
        "forward_signed_targets": ("forward_signed_subset_pair_terms",),
        "forward_fold_and_global_tree": (
            "forward_fold_pair_times_pair",
            "forward_tree_contributions",
        ),
        "adjoint_covector_and_labels": (
            "adjoint_covector_pair_times_float64",
            "adjoint_label_pair_adds",
        ),
        "adjoint_recurrence_and_signed_sources": (
            "adjoint_recurrence_pair_child_adds",
            "adjoint_pair_divides",
            "adjoint_signed_subset_pair_terms",
        ),
        "direct_adjoint": (
            "direct_adjoint_compatible_query_weight_builds",
            "direct_adjoint_compatible_boundary_pair_adds",
            "direct_adjoint_query_record_visits",
            "direct_adjoint_source_unranks",
        ),
        "adjoint_source_contract_and_global_tree": (
            "adjoint_source_pairing_visits",
            "adjoint_source_weight_pair_times_float64",
            "adjoint_contract_pair_times_pair",
            "adjoint_tree_contributions",
        ),
    }
)

_ALLOWED_PHASE_TRANSITIONS = MappingProxyType(
    {
        "fixture_and_resident_birth": ("forward_source_and_offset",),
        "forward_source_and_offset": ("direct_query",),
        "direct_query": ("direct_fold",),
        "direct_fold": ("forward_recurrence",),
        "forward_recurrence": ("forward_signed_targets",),
        "forward_signed_targets": ("forward_fold_and_global_tree",),
        "forward_fold_and_global_tree": (
            "forward_signed_targets",
            "forward_capture_and_digest",
        ),
        "forward_capture_and_digest": (
            "forward_source_and_offset",
            "forward_release",
        ),
        "forward_release": ("adjoint_covector_and_labels",),
        "adjoint_covector_and_labels": (
            "adjoint_recurrence_and_signed_sources",
        ),
        "adjoint_recurrence_and_signed_sources": (
            "direct_adjoint",
            "adjoint_source_contract_and_global_tree",
        ),
        "direct_adjoint": ("adjoint_recurrence_and_signed_sources",),
        "adjoint_source_contract_and_global_tree": (
            "adjoint_recurrence_and_signed_sources",
            "adjoint_capture_digest_and_exact_stream",
        ),
        "adjoint_capture_digest_and_exact_stream": (
            "adjoint_covector_and_labels",
            "mutations_and_lifecycle",
        ),
        "mutations_and_lifecycle": ("final_release",),
        "final_release": (),
    }
)


def _chunk_counts(available_cards: int) -> tuple[tuple[int, int, int], ...]:
    geometry = population_geometry(available_cards)
    totals = (
        geometry.labeled_query_records,
        geometry.query_occupancies,
        geometry.source_occupancies,
    )
    return tuple(
        tuple((total + size - 1) // size for total, size in zip(totals, family))
        for family in _FROZEN_CHUNKS[available_cards]
    )


def phase_projection_constituents(
    phase: str, calibration_population: int
) -> tuple[tuple[str, int, int], ...]:
    """List every frozen work, live-shape, and relevant segment-count ratio."""

    if phase not in PHASE_ORDER:
        raise ValueError("unknown work-preflight phase")
    if calibration_population not in CALIBRATION_POPULATIONS:
        raise ValueError("projection endpoint must be 10 or 22")
    target = population_geometry(PROJECTION_POPULATION)
    endpoint = population_geometry(calibration_population)
    target_work = complete_campaign_work(PROJECTION_POPULATION)
    endpoint_work = complete_campaign_work(calibration_population)
    rows: list[tuple[str, int, int]] = []

    if phase in {"direct_query", "direct_fold"}:
        rows.append(
            (
                "compatible_sources_per_query_occupancy",
                target.compatible_sources_per_query_occupancy,
                endpoint.compatible_sources_per_query_occupancy,
            )
        )
    elif phase == "forward_recurrence":
        rows.append(
            (
                "forward_recurrence_pair_child_adds",
                target_work["forward_recurrence_pair_child_adds"],
                endpoint_work["forward_recurrence_pair_child_adds"],
            )
        )
    elif phase in {
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
        "adjoint_covector_and_labels",
    }:
        rows.append(
            (
                "labeled_query_records",
                target.labeled_query_records,
                endpoint.labeled_query_records,
            )
        )
    elif phase == "direct_adjoint":
        rows.append(
            (
                "compatible_labeled_query_records_per_source",
                target.compatible_labeled_query_records_per_source,
                endpoint.compatible_labeled_query_records_per_source,
            )
        )
    else:
        rows.append(
            (
                "source_occupancies",
                target.source_occupancies,
                endpoint.source_occupancies,
            )
        )

    for counter in _PHASE_WORK_COUNTERS.get(phase, ()):  # type: ignore[arg-type]
        rows.append((counter, target_work[counter], endpoint_work[counter]))

    live_fields = {
        "fixture_and_resident_birth": (
            "source_occupancies",
            "source_recurrence_rows",
            "labeled_query_records",
            "adjoint_recurrence_rows",
        ),
        "forward_source_and_offset": ("source_occupancies", "source_recurrence_rows"),
        "forward_recurrence": ("source_recurrence_rows",),
        "forward_signed_targets": ("labeled_query_records",),
        "forward_fold_and_global_tree": ("labeled_query_records",),
        "forward_capture_and_digest": ("labeled_query_records",),
        "forward_release": (
            "source_occupancies",
            "source_recurrence_rows",
            "labeled_query_records",
            "adjoint_recurrence_rows",
        ),
        "adjoint_covector_and_labels": (
            "labeled_query_records",
            "query_occupancies",
        ),
        "adjoint_recurrence_and_signed_sources": (
            "source_occupancies",
            "adjoint_recurrence_rows",
        ),
        "adjoint_source_contract_and_global_tree": ("source_occupancies",),
        "adjoint_capture_digest_and_exact_stream": ("source_occupancies",),
        "mutations_and_lifecycle": (
            "source_occupancies",
            "labeled_query_records",
        ),
        "final_release": (
            "source_occupancies",
            "source_recurrence_rows",
            "labeled_query_records",
            "adjoint_recurrence_rows",
        ),
    }.get(phase, ())
    for field in live_fields:
        rows.append((f"live_{field}", getattr(target, field), getattr(endpoint, field)))

    target_chunks = _chunk_counts(PROJECTION_POPULATION)
    endpoint_chunks = _chunk_counts(calibration_population)
    chunk_axes: tuple[int, ...]
    if phase in {
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
    }:
        chunk_axes = (0,)
    elif phase == "adjoint_covector_and_labels":
        chunk_axes = (1,)
    elif phase in {
        "adjoint_recurrence_and_signed_sources",
        "adjoint_source_contract_and_global_tree",
        "adjoint_capture_digest_and_exact_stream",
    }:
        chunk_axes = (2,)
    elif phase == "mutations_and_lifecycle":
        chunk_axes = (0, 1, 2)
    else:
        chunk_axes = ()
    for family in range(2):
        for axis in chunk_axes:
            rows.append(
                (
                    f"chunk_count_family_{family}_axis_{axis}",
                    target_chunks[family][axis],
                    endpoint_chunks[family][axis],
                )
            )
    return tuple(rows)


def phase_projection_ratio(
    phase: str, calibration_population: int
) -> tuple[int, int]:
    """Select the largest frozen constituent ratio without reducing it."""

    constituents = phase_projection_constituents(phase, calibration_population)
    label, numerator, denominator = constituents[0]
    del label
    for _, candidate_numerator, candidate_denominator in constituents[1:]:
        if candidate_numerator * denominator > numerator * candidate_denominator:
            numerator, denominator = candidate_numerator, candidate_denominator
    return numerator, denominator


def _config_geometry_key(available_cards: int) -> str:
    return str(available_cards) if available_cards != 25 else "25_projection_only"


def _config_work_key(available_cards: int) -> str:
    return (
        f"complete_campaign_work_{available_cards}"
        if available_cards != 25
        else "complete_campaign_work_25_projection_only"
    )


_EXPECTED_SOURCE_PATHS = MappingProxyType(
    {
        "adr0393": _ROOT
        / "docs/decisions/ADR-0393-retain-the-paired-tile-wall-rejection.md",
        "paired_base_config": _ROOT
        / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json",
        "paired_correction_config": _ROOT
        / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
        "paired_source": _ROOT
        / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
        "paired_controls": _ROOT
        / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
        "gitattributes": _ROOT / ".gitattributes",
        "artifact_marker": _ROOT / "artifacts/README.md",
        "work_preflight_gitattributes": (
            _ROOT / "artifacts/work_preflight/.gitattributes"
        ),
        "work_preflight_artifact_marker": (
            _ROOT / "artifacts/work_preflight/README.md"
        ),
    }
)


def verify_preregistered_work_preflight_contract(
    config: Mapping[str, object] | None = None,
    correction: Mapping[str, object] | None = None,
) -> None:
    frozen = (
        load_preregistered_work_preflight_config() if config is None else config
    )
    resource_correction = (
        load_work_preflight_resource_correction()
        if correction is None
        else correction
    )
    sources = frozen.get("expected_sources")
    if not isinstance(sources, Mapping) or set(sources) != set(_EXPECTED_SOURCE_PATHS):
        raise ValueError("work-preflight dependency set differs")
    for label, path in _EXPECTED_SOURCE_PATHS.items():
        if sources[label] != canonical_lf_sha256(path):
            raise ValueError(f"work-preflight dependency differs: {label}")

    geometry_section = frozen.get("population_geometry")
    ratios = frozen.get("phase_projection_ratios")
    claims = frozen.get("claims")
    if not all(isinstance(value, Mapping) for value in (geometry_section, ratios, claims)):
        raise ValueError("work-preflight typed contract is malformed")
    assert isinstance(geometry_section, Mapping)
    assert isinstance(ratios, Mapping)
    assert isinstance(claims, Mapping)
    for cards in (10, 22, 25):
        geometry = population_geometry(cards)
        expected_geometry = {
            "source_occupancies": geometry.source_occupancies,
            "query_occupancies": geometry.query_occupancies,
            "labeled_query_records": geometry.labeled_query_records,
            "source_recurrence_rows": geometry.source_recurrence_rows,
            "adjoint_recurrence_rows": geometry.adjoint_recurrence_rows,
            "compatible_sources_per_query_occupancy": (
                geometry.compatible_sources_per_query_occupancy
            ),
            "compatible_labeled_query_records_per_source": (
                geometry.compatible_labeled_query_records_per_source
            ),
        }
        if geometry_section.get(_config_geometry_key(cards)) != expected_geometry:
            raise ValueError(f"work-preflight {cards}-card geometry differs")
        stored_work = frozen.get(_config_work_key(cards))
        if not isinstance(stored_work, Mapping):
            raise ValueError(f"work-preflight {cards}-card work is malformed")
        derived_work = complete_campaign_work(cards)
        if any(stored_work.get(name) != count for name, count in derived_work.items()):
            raise ValueError(f"work-preflight {cards}-card work differs")

    chunks = frozen.get("chunk_contract")
    if not isinstance(chunks, Mapping):
        raise ValueError("work-preflight chunk contract is malformed")
    for cards in (10, 22, 25):
        key = str(cards) if cards != 25 else "25_projection_only"
        default_key = "default" if cards != 25 else "default_inherited"
        alternate_key = "alternate" if cards != 25 else "alternate_inherited"
        section = chunks.get(key)
        if not isinstance(section, Mapping) or (
            tuple(section.get(default_key, ())),
            tuple(section.get(alternate_key, ())),
        ) != _FROZEN_CHUNKS[cards]:
            raise ValueError(f"work-preflight {cards}-card chunks differ")

    for phase in PHASE_ORDER:
        entry = ratios.get(phase)
        if not isinstance(entry, Mapping):
            raise ValueError(f"work-preflight phase ratio is absent: {phase}")
        for cards in CALIBRATION_POPULATIONS:
            if entry.get(f"25_over_{cards}") != list(
                phase_projection_ratio(phase, cards)
            ):
                raise ValueError(f"work-preflight phase ratio differs: {phase}/{cards}")
    if ratios.get("ratios_are_frozen_not_selected_from_observed_timing") is not True:
        raise ValueError("work-preflight ratio freeze differs")
    if tuple(frozen["phase_timing_contract"]["phase_order"]) != PHASE_ORDER:  # type: ignore[index]
        raise ValueError("work-preflight phase order differs")
    if any(value is not None and value is not False for value in claims.values()):
        raise ValueError("work-preflight preregistered claims are open")
    if canonical_lf_sha256(_CORRECTION_ADR) != CORRECTION_ADR_SHA256:
        raise ValueError("work-preflight correction ADR differs")
    parent = resource_correction.get("parent_identity")
    composite = resource_correction.get("composite_authority")
    instrument = resource_correction.get("corrected_resource_contract")
    reserve = resource_correction.get("reserve_arithmetic")
    correction_claims = resource_correction.get("claims")
    if not all(
        isinstance(value, Mapping)
        for value in (parent, composite, instrument, reserve, correction_claims)
    ):
        raise ValueError("work-preflight correction sections are malformed")
    assert isinstance(parent, Mapping)
    assert isinstance(composite, Mapping)
    assert isinstance(instrument, Mapping)
    assert isinstance(reserve, Mapping)
    assert isinstance(correction_claims, Mapping)
    if (
        parent.get("adr0394_canonical_lf_sha256")
        != "362f21a4f246f8598adc5445f3323088c1e38b389f4f07b3ae600c831c57de44"
        or parent.get("v1_config_canonical_lf_sha256")
        != PREREGISTERED_CONFIG_SHA256
        or parent.get("v1_preregistration_commit")
        != "fc1892e15522eed4b9935de0404131646820c451"
    ):
        raise ValueError("work-preflight correction parent identity differs")
    if (
        composite.get(
            "all_v1_arithmetic_population_phase_ratio_wall_lifecycle_"
            "and_claim_fields_remain_binding"
        )
        is not True
        or composite.get(
            "v2_may_not_relax_remove_or_reinterpret_any_v1_numerical_"
            "semantic_timing_or_claim_gate"
        )
        is not True
        or composite.get(
            "future_source_owner_and_reader_must_load_verify_and_report_"
            "both_config_hashes"
        )
        is not True
    ):
        raise ValueError("work-preflight composite authority differs")
    if (
        tuple(instrument.get("caller_supplied_nvrtc_options_unchanged", ()))
        != CUDA_COMPILE_OPTIONS
        or instrument.get("register_limit_per_thread")
        != DIRECT_KERNEL_REGISTER_LIMIT
        or instrument.get("stack_plus_local_backing_limit_bytes_per_thread")
        != DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
        or instrument.get("exact_spill_load_store_count") is not None
        or instrument.get("spill_traffic_is_structurally_unavailable_and_must_not_be_invented")
        is not True
        or instrument.get("retained_payload_must_begin_with_elf_magic_before_module_load")
        is not True
        or instrument.get("cupy_free_reader_must_independently_parse_raw_resource_stdout")
        is not True
    ):
        raise ValueError("work-preflight corrected resource contract differs")
    if (
        reserve.get("frozen_device_reserve_bytes") != FROZEN_DEVICE_RESERVE_BYTES
        or reserve.get("maximum_resident_thread_bound")
        != MAXIMUM_RESIDENT_THREAD_BOUND
        or reserve.get("maximum_resident_backing_at_4096_bytes_per_thread")
        != MAXIMUM_RESIDENT_BACKING_BYTES
        or DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
        * MAXIMUM_RESIDENT_THREAD_BOUND
        != MAXIMUM_RESIDENT_BACKING_BYTES
        or MAXIMUM_RESIDENT_BACKING_BYTES > FROZEN_DEVICE_RESERVE_BYTES
    ):
        raise ValueError("work-preflight resource reserve arithmetic differs")
    if any(
        value is not None and value is not False
        for value in correction_claims.values()
    ):
        raise ValueError("work-preflight correction claims are open")
    if (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists():
        raise ValueError("work-preflight reserved actual artifact exists")
    if _paired.actual_execution_call_count() != 0:
        raise ValueError("work-preflight actual execution counter is nonzero")
    if _paired.actual_numeric_allocation_call_count() != 0:
        raise ValueError("work-preflight actual allocation counter is nonzero")
    if _paired.actual_scientific_call_count() != 0:
        raise ValueError("work-preflight actual scientific counter is nonzero")


def _ceil_ratio(value: int, numerator: int, denominator: int) -> int:
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0
           for item in (value, numerator, denominator)) or denominator == 0:
        raise ValueError("projection values must be nonnegative integers")
    return (value * numerator + denominator - 1) // denominator


def reconstruct_projection(
    phase_host_ns: Mapping[int, Mapping[str, int]],
    config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Recompute all phase candidates and the deciding 25-card projection."""

    frozen = (
        load_preregistered_work_preflight_config() if config is None else config
    )
    if set(phase_host_ns) != set(CALIBRATION_POPULATIONS):
        raise ValueError("projection requires exactly the 10 and 22 endpoints")
    rows: list[dict[str, object]] = []
    total = 0
    for phase in PHASE_ORDER:
        candidates: dict[str, int] = {}
        for cards in CALIBRATION_POPULATIONS:
            endpoint = phase_host_ns[cards]
            if set(endpoint) != set(PHASE_ORDER):
                raise ValueError("projection endpoint phase set differs")
            observed = endpoint[phase]
            if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
                raise ValueError("projection endpoint timing must be nonnegative")
            numerator, denominator = phase_projection_ratio(phase, cards)
            candidates[str(cards)] = _ceil_ratio(observed, numerator, denominator)
        maximum = max(candidates.values())
        upper = _ceil_ratio(maximum, 5, 4) + 1_000_000
        total += upper
        rows.append(
            {
                "phase": phase,
                "candidate_10_ns": candidates["10"],
                "candidate_22_ns": candidates["22"],
                "upper_ns": upper,
            }
        )
    limit = int(
        frozen["projection_contract"]["target_population_wall_limit_ns"]  # type: ignore[index]
    )
    return {
        "schema_version": "legal-river-work-preflight-projection-v1",
        "target_population": PROJECTION_POPULATION,
        "phase_rows": rows,
        "projected_host_ns": total,
        "wall_limit_ns": limit,
        "passed": total <= limit,
    }


def _sample_axis(total: int, *, available_cards: int, role: str) -> tuple[int, ...]:
    if total < 16:
        raise ValueError("sample axis is too small")
    selected = {0, total - 1}
    nonce = 0
    while len(selected) < 16:
        digest = sha256(
            f"pontius-adr0394:{available_cards}:{role}:{nonce}".encode("ascii")
        ).digest()
        selected.add(int.from_bytes(digest, "big") % total)
        nonce += 1
    return tuple(sorted(selected))


def sample_rows(available_cards: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if available_cards not in CALIBRATION_POPULATIONS:
        raise ValueError("sample rows exist only for calibration populations")
    geometry = population_geometry(available_cards)
    return (
        _sample_axis(
            geometry.source_occupancies,
            available_cards=available_cards,
            role="source-occupancy",
        ),
        _sample_axis(
            geometry.labeled_query_records,
            available_cards=available_cards,
            role="labeled-query-record",
        ),
    )


_ORDER_CONTROL_VALUES = tuple(
    _paired.FloatPair(float.fromhex(value), 0.0)
    for value in (
        "0x1.e927924c9a23ep-825",
        "0x1.79f357ee35f00p+82",
        "0x1.b5d8b382e141ap+613",
        "0x1.19e3ae668e2acp-705",
        "0x1.62f8c224775c8p+587",
        "-0x1.2acead8259041p+667",
        "0x1.7dcae9693914dp-480",
        "-0x1.32d88d56e3f0bp+580",
    )
)


def _ordered_pair_digest(order: Sequence[int]) -> str:
    if tuple(sorted(order)) != tuple(range(len(_ORDER_CONTROL_VALUES))):
        raise ValueError("direct-order control must be a permutation")
    value = _paired.FloatPair(0.0, 0.0)
    trace = bytearray()
    for index in order:
        value = _paired._pair_add_host(value, _ORDER_CONTROL_VALUES[index])
        trace.extend(struct.pack(">dd", value.high, value.low))
    return sha256(bytes(trace)).hexdigest()


def run_direct_order_controls() -> dict[str, object]:
    """Exercise the canonical source/query/feature order and named mutations."""

    canonical = tuple(range(len(_ORDER_CONTROL_VALUES)))
    reversed_order = tuple(reversed(canonical))
    source_digest = _ordered_pair_digest(canonical)
    query_digest = _ordered_pair_digest(canonical)
    feature_digest = _ordered_pair_digest(canonical)
    source_mutation = _ordered_pair_digest(reversed_order)
    query_mutation = _ordered_pair_digest(reversed_order)
    feature_mutation = _ordered_pair_digest(reversed_order)
    canonical_unranks = len(canonical)
    feature_major_unranks = len(canonical) * len(canonical)
    gates = {
        "source_rank_permutation_changes_digest": source_mutation != source_digest,
        "query_record_permutation_changes_adjoint_digest": (
            query_mutation != query_digest
        ),
        "boundary_feature_permutation_changes_fold_digest": (
            feature_mutation != feature_digest
        ),
        "source_rank_major_unrank_counter": canonical_unranks == 8,
        "feature_major_unrank_counter_mutation_rejected": (
            feature_major_unranks != canonical_unranks
        ),
    }
    return {
        "schema_version": "legal-river-work-preflight-direct-order-control-v1",
        "canonical_order": list(canonical),
        "canonical_digests": {
            "source": source_digest,
            "query": query_digest,
            "feature": feature_digest,
        },
        "mutation_digests": {
            "source": source_mutation,
            "query": query_mutation,
            "feature": feature_mutation,
        },
        "unrank_counts": {
            "source_rank_major": canonical_unranks,
            "feature_major_mutation": feature_major_unranks,
        },
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


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


def compile_calibration_fixture(
    available_cards: int,
    *,
    bridge: Any | None = None,
) -> ConsumerPopulationFixture:
    """Compile only 10 or 22; the projection population is rejected first."""

    if available_cards not in CALIBRATION_POPULATIONS:
        raise ValueError("fixture compilation is restricted to 10 and 22 cards")
    geometry = population_geometry(available_cards)
    compiled = (
        _consumer.compile_legal_river_quotient_bridge(
            _consumer.build_preregistered_legal_river_context()
        )
        if bridge is None
        else bridge
    )
    reference = _consumer.compile_legal_river_quotient_bridge(
        _consumer.build_preregistered_legal_river_context()
    )
    if compiled.bridge_digest != reference.bridge_digest:
        raise ValueError("work-preflight bridge differs from independent replay")
    capacity = _consumer.build_legal_river_consumer_capacity_report(bridge=compiled)
    if (
        capacity.bridge_sha256 != compiled.bridge_digest
        or capacity.topology_sha256 != compiled.topology_digest
        or not capacity.all_source_gates_pass
    ):
        raise ValueError("work-preflight source-capacity parent did not rebind")

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
            h4 = int(parent.pair_to_hand[occupancy[pairing[0]], occupancy[pairing[1]]])
            h5 = int(parent.pair_to_hand[occupancy[pairing[2]], occupancy[pairing[3]]])
            if h4 < 0 or h5 < 0:
                raise AssertionError("work-preflight query compiler produced an invalid hand")
            query_masks[cursor] = mask
            query_hands[cursor] = (h4, h5)
            cursor += 1
    if cursor != geometry.labeled_query_records:
        raise AssertionError("work-preflight query compiler omitted a label")
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
        terminal_winner_values=_readonly(parent.automaton.terminal_winner_values, np.float64),
        sunk_value=float(parent.automaton.sunk_value),
    )


_DIRECT_QUERY_KERNEL = r'''extern "C" __global__ void direct_selected_queries_tile(
    const double *source, long long source_level_offset,
    long long source_rows, int n, int physical_stride,
    const unsigned long long *query_masks, int query_count,
    const int *global_features, int feature_count,
    int global_feature_start, int logical_width, double *output
) {
    int query = blockDim.x * blockIdx.x + threadIdx.x;
    if (query >= query_count) return;
    DD values[8];
    for (int feature_index = 0; feature_index < feature_count; ++feature_index)
        values[feature_index] = make_dd(0.0, 0.0);
    unsigned long long query_mask = query_masks[query];
    for (long long row = 0; row < source_rows; ++row) {
        unsigned long long source_mask = unrank_mask(row, n, 6);
        if (source_mask & query_mask) continue;
        for (int feature_index = 0; feature_index < feature_count; ++feature_index) {
            int logical = global_features[feature_index] - global_feature_start;
            if (logical >= 0 && logical < logical_width)
                values[feature_index] = pair_add(
                    values[feature_index],
                    load_pair(source + (source_level_offset + row)
                              * physical_stride, logical)
                );
        }
    }
    for (int feature_index = 0; feature_index < feature_count; ++feature_index) {
        int index = query * feature_count + feature_index;
        output[2 * index] = values[feature_index].high;
        output[2 * index + 1] = values[feature_index].low;
    }
}'''


_DIRECT_FOLD_KERNEL = r'''extern "C" __global__ void direct_selected_fold_tile(
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


_DIRECT_ADJOINT_KERNEL = r'''extern "C" __global__ void direct_selected_adjoint_tile(
    const long long *source_ranks, int source_count,
    const int *global_features, int feature_count,
    int global_feature_start, int logical_width, int n,
    const unsigned long long *query_masks, long long query_records,
    int source_rank, const int *query_hands, const double *unary,
    const double *factors, const int *unary_offsets, const double *mixture,
    const int *transition3, const int *transition4, const double *terminal,
    int hand_width, double sunk, double *output
) {
    int source_index = blockDim.x * blockIdx.x + threadIdx.x;
    if (source_index >= source_count) return;
    unsigned long long source_mask = unrank_mask(source_ranks[source_index], n, 6);
    DD values[8];
    for (int feature_index = 0; feature_index < feature_count; ++feature_index)
        values[feature_index] = make_dd(0.0, 0.0);
    for (long long record = 0; record < query_records; ++record) {
        if (source_mask & query_masks[record]) continue;
        int h4, h5;
        DD weight = query_weight_pair(
            record, query_hands, unary, factors, unary_offsets,
            mixture, &h4, &h5
        );
        for (int feature_index = 0; feature_index < feature_count; ++feature_index) {
            int global_feature = global_features[feature_index];
            int logical = global_feature - global_feature_start;
            if (logical < 0 || logical >= logical_width) continue;
            double payoff;
            if (global_feature == source_rank) payoff = sunk;
            else {
                int state3 = transition3[global_feature];
                int state4 = transition4[state3 * hand_width + h4];
                payoff = terminal[state4 * hand_width + h5];
            }
            values[feature_index] = pair_add(
                values[feature_index], pair_times_float64(weight, payoff)
            );
        }
    }
    for (int feature_index = 0; feature_index < feature_count; ++feature_index) {
        int index = source_index * feature_count + feature_index;
        output[2 * index] = values[feature_index].high;
        output[2 * index + 1] = values[feature_index].low;
    }
}'''


def _kernel_span(source: str, name: str) -> tuple[int, int]:
    marker = f'extern "C" __global__ void {name}('
    start = source.find(marker)
    if start < 0 or source.find(marker, start + 1) >= 0:
        raise AssertionError(f"parent CUDA kernel occurrence differs: {name}")
    next_start = source.find('\nextern "C" __global__ void ', start + len(marker))
    return start, len(source) if next_start < 0 else next_start


def build_cuda_source(parent_source: str = _paired._CUDA_SOURCE) -> str:
    """Replace exactly the three direct controls in the hash-bound parent."""

    replacements = (
        ("direct_selected_queries_tile", _DIRECT_QUERY_KERNEL),
        ("direct_selected_fold_tile", _DIRECT_FOLD_KERNEL),
        ("direct_selected_adjoint_tile", _DIRECT_ADJOINT_KERNEL),
    )
    result = parent_source
    for name, replacement in replacements:
        start, stop = _kernel_span(result, name)
        result = result[:start] + replacement + result[stop:]
    if result.count("unrank_mask(row, n, 6)") < 2:
        raise AssertionError("source-rank-major direct unranking is absent")
    return result


CUDA_SOURCE = build_cuda_source()
KERNEL_NAMES = _paired._KERNEL_NAMES
_KERNEL_CACHE: dict[int, Mapping[str, object]] = {}
_MODULE_CACHE: dict[int, object] = {}
_CUBIN_CACHE: dict[int, bytes] = {}


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def bounded_execution_call_count() -> int:
    return _BOUNDED_EXECUTION_CALLS


def actual_execution_call_count() -> int:
    return _paired.actual_execution_call_count()


def actual_numeric_allocation_call_count() -> int:
    return _paired.actual_numeric_allocation_call_count()


def actual_scientific_call_count() -> int:
    return _paired.actual_scientific_call_count()


def cuda_compile_options() -> tuple[str, ...]:
    return CUDA_COMPILE_OPTIONS


def _kernels(cp: Any) -> Mapping[str, object]:
    device = int(cp.cuda.Device().id)
    cached = _KERNEL_CACHE.get(device)
    if cached is not None:
        return cached
    binary, _ = cp.cuda.compiler.compile_using_nvrtc(
        CUDA_SOURCE,
        options=CUDA_COMPILE_OPTIONS,
        cache_in_memory=True,
    )
    retained = bytes(binary)
    if not retained.startswith(ELF_MAGIC):
        raise CompilerResourceRejection(
            "work-preflight retained compiler payload is not ELF"
        )
    module = cp.cuda.function.Module()
    module.load(retained)
    result = MappingProxyType({name: module.get_function(name) for name in KERNEL_NAMES})
    _MODULE_CACHE[device] = module
    _CUBIN_CACHE[device] = retained
    _KERNEL_CACHE[device] = result
    return result


def parse_cuobjdump_resource_usage(output: str) -> dict[str, dict[str, int]]:
    """Parse exact-cubin resource rows without interpreting them as spill counts."""

    if not isinstance(output, str):
        raise TypeError("cuobjdump resource output must be text")
    result: dict[str, dict[str, int]] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = re.fullmatch(r"Function\s+([^:]+):", line)
        if match:
            current = match.group(1)
            if current in result:
                raise ValueError("cuobjdump resource output repeats a function")
            result[current] = {}
            continue
        if current is None or not line:
            continue
        fields = re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line)
        for label, value in fields:
            if label in result[current]:
                raise ValueError("cuobjdump resource output repeats a field")
            result[current][label] = int(value)
    required = {
        "direct_selected_queries_tile",
        "direct_selected_fold_tile",
        "direct_selected_adjoint_tile",
    }
    if not required.issubset(result):
        raise ValueError("cuobjdump resource output omits a direct kernel")
    for name in required:
        if not {"REG", "STACK", "LOCAL"}.issubset(result[name]):
            raise ValueError("cuobjdump direct resource row is incomplete")
    return result


def direct_kernel_resource_gates(
    direct: Mapping[str, Mapping[str, int]],
) -> dict[str, bool]:
    required = {
        "direct_selected_queries_tile",
        "direct_selected_fold_tile",
        "direct_selected_adjoint_tile",
    }
    if set(direct) != required:
        raise ValueError("direct resource gate kernel set differs")
    for row in direct.values():
        if not {"REG", "STACK", "LOCAL"}.issubset(row):
            raise ValueError("direct resource gate row is incomplete")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0
               for value in row.values()):
            raise ValueError("direct resource gate value is invalid")
    return {
        "register_ceiling": all(
            row["REG"] <= DIRECT_KERNEL_REGISTER_LIMIT
            for row in direct.values()
        ),
        "local_and_stack_ceiling": all(
            row["LOCAL"] + row["STACK"]
            <= DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
            for row in direct.values()
        ),
    }


def combined_direct_kernel_resource_report(
    cubin_direct: Mapping[str, Mapping[str, int]],
    driver_direct: Mapping[str, Mapping[str, int]],
    *,
    multiprocessor_count: int,
    maximum_threads_per_multiprocessor: int,
) -> dict[str, object]:
    """Conservatively combine independent exact-binary resource instruments."""

    required = {
        "direct_selected_queries_tile",
        "direct_selected_fold_tile",
        "direct_selected_adjoint_tile",
    }
    if set(cubin_direct) != required or set(driver_direct) != required:
        raise ValueError("combined direct resource kernel set differs")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in (multiprocessor_count, maximum_threads_per_multiprocessor)
    ):
        raise ValueError("combined direct resource residency is malformed")
    direct_kernel_resource_gates(cubin_direct)
    expected_driver_fields = {
        "local_size_bytes",
        "registers",
        "shared_size_bytes",
        "maximum_threads_per_block",
    }
    maxima: dict[str, dict[str, int]] = {}
    for name in sorted(required):
        driver = driver_direct[name]
        if set(driver) != expected_driver_fields or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in driver.values()
        ):
            raise ValueError("combined direct driver resource row differs")
        cubin = cubin_direct[name]
        maxima[name] = {
            "registers": max(driver["registers"], cubin["REG"]),
            "stack_plus_local_backing_bytes": max(
                driver["local_size_bytes"], cubin["STACK"] + cubin["LOCAL"]
            ),
        }
    resident_threads = multiprocessor_count * maximum_threads_per_multiprocessor
    resident_backing = resident_threads * DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
    gates = {
        "register_ceiling": all(
            row["registers"] <= DIRECT_KERNEL_REGISTER_LIMIT
            for row in maxima.values()
        ),
        "local_and_stack_ceiling": all(
            row["stack_plus_local_backing_bytes"]
            <= DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
            for row in maxima.values()
        ),
        "resident_thread_bound": resident_threads <= MAXIMUM_RESIDENT_THREAD_BOUND,
        "resident_backing_within_device_reserve": (
            resident_threads <= MAXIMUM_RESIDENT_THREAD_BOUND
            and resident_backing <= FROZEN_DEVICE_RESERVE_BYTES
        ),
    }
    return {
        "effective_maxima": maxima,
        "runtime_residency": {
            "multiprocessor_count": multiprocessor_count,
            "maximum_threads_per_multiprocessor": (
                maximum_threads_per_multiprocessor
            ),
            "maximum_resident_threads": resident_threads,
            "backing_ceiling_bytes_per_thread": (
                DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES
            ),
            "maximum_resident_backing_bytes": resident_backing,
            "frozen_device_reserve_bytes": FROZEN_DEVICE_RESERVE_BYTES,
        },
        "gates": gates,
    }


def _cuobjdump_path() -> Path:
    discovered = shutil.which("cuobjdump")
    candidates = [
        Path(
            r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
        ),
        Path(discovered) if discovered is not None else None,
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise CompilerResourceRejection("CUDA 13.3 cuobjdump is unavailable")


def _compiled_cubin_resource_usage(
    cp: Any,
    driver_direct: Mapping[str, Mapping[str, int]],
) -> dict[str, object]:
    device = int(cp.cuda.Device().id)
    binary = _CUBIN_CACHE.get(device)
    if binary is None:
        raise CompilerResourceRejection("work-preflight cubin was not retained")
    if not binary.startswith(ELF_MAGIC):
        raise CompilerResourceRejection(
            "work-preflight retained compiler payload is not ELF"
        )
    tool = _cuobjdump_path()
    temporary_path: Path | None = None
    try:
        version = subprocess.run(
            [str(tool), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        version_output = "\n".join(
            value.strip() for value in (version.stdout, version.stderr) if value.strip()
        )
        if not version_output:
            raise CompilerResourceRejection("cuobjdump version output is absent")
        if re.search(r"(?<!\d)13\.3(?!\d)", version_output) is None:
            raise CompilerResourceRejection("cuobjdump is not the frozen CUDA 13.3 tool")
        with tempfile.NamedTemporaryFile(suffix=".cubin", delete=False) as handle:
            handle.write(binary)
            handle.flush()
            temporary_path = Path(handle.name)
        completed = subprocess.run(
            [str(tool), "--dump-resource-usage", str(temporary_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        raw_resource_stdout = completed.stdout
        parsed = parse_cuobjdump_resource_usage(raw_resource_stdout)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    direct = {
        name: parsed[name]
        for name in (
            "direct_selected_queries_tile",
            "direct_selected_fold_tile",
            "direct_selected_adjoint_tile",
        )
    }
    properties = cp.cuda.runtime.getDeviceProperties(device)
    combined = combined_direct_kernel_resource_report(
        direct,
        driver_direct,
        multiprocessor_count=int(properties["multiProcessorCount"]),
        maximum_threads_per_multiprocessor=int(
            properties["maxThreadsPerMultiProcessor"]
        ),
    )
    return {
        "tool_path": str(tool),
        "tool_version_output": version_output,
        "raw_resource_stdout": raw_resource_stdout,
        "cubin_sha256": sha256(binary).hexdigest(),
        "retained_payload_format": "elf-cubin",
        "caller_supplied_nvrtc_options": list(CUDA_COMPILE_OPTIONS),
        "cupy_version": str(cp.__version__),
        "cupy_internal_options_disclosure": [
            "target_architecture",
            "device_as_default_execution_space",
            "version_dependent_precompiled_header",
        ],
        "direct": direct,
        "driver_direct": {name: dict(row) for name, row in driver_direct.items()},
        "effective_maxima": combined["effective_maxima"],
        "runtime_residency": combined["runtime_residency"],
        "gates": combined["gates"],
        "claims": {
            "exact_spill_load_store_count": None,
            "local_and_stack_are_not_relabeled_as_spill_counts": True,
        },
    }


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("work-preflight evidence contains a nonfinite float")
        return value.hex()
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value).hex()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(item) for item in value]
    if hasattr(value, "__dict__"):
        return _plain(vars(value))
    raise TypeError(f"unsupported work-preflight evidence type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class PhaseRow:
    ordinal: int
    population: int
    family: str
    repeat: int
    tile: int
    phase: str
    host_start_ns: int
    host_stop_ns: int
    host_ns: int
    device_ns: int
    chunks: tuple[int, int, int]
    work: Mapping[str, int]

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": "legal-river-work-preflight-phase-v1",
            "ordinal": self.ordinal,
            "population": self.population,
            "family": self.family,
            "repeat": self.repeat,
            "tile": self.tile,
            "phase": self.phase,
            "host_start_ns": self.host_start_ns,
            "host_stop_ns": self.host_stop_ns,
            "host_ns": self.host_ns,
            "device_ns": self.device_ns,
            "chunks": list(self.chunks),
            "work": dict(self.work),
        }


class PhaseLedger:
    """One exact, contiguous host-time partition with per-row work deltas."""

    def __init__(
        self,
        *,
        population: int,
        family: str,
        chunks: tuple[int, int, int],
        clock_ns: Callable[[], int] = perf_counter_ns,
        device_terminal: Callable[[], int] | None = None,
        emit: Callable[[PhaseRow], None] | None = None,
        wall_deadline_ns: int | None = None,
    ) -> None:
        if population not in CALIBRATION_POPULATIONS:
            raise ValueError("phase ledger population must be 10 or 22")
        if family not in POPULATION_FAMILIES:
            raise ValueError("phase ledger family differs")
        if len(chunks) != 3 or any(value <= 0 for value in chunks):
            raise ValueError("phase ledger chunks must be positive")
        self.population = population
        self.family = family
        self.chunks = chunks
        self._clock = clock_ns
        self._device_terminal = device_terminal or (lambda: 0)
        self._emit = emit
        self._deadline = wall_deadline_ns
        self._rows: list[PhaseRow] = []
        self._current_phase: str | None = None
        self._repeat = 0
        self._tile = 0
        self._start_ns: int | None = None
        self._work: dict[str, int] = {}
        self.direction = "fixture"
        self.mutation_mode = False

    @property
    def rows(self) -> tuple[PhaseRow, ...]:
        return tuple(self._rows)

    def start(self, *, repeat: int, tile: int) -> None:
        if self._start_ns is not None:
            raise RuntimeError("phase ledger already started")
        self._repeat = repeat
        self._tile = tile
        self._current_phase = PHASE_ORDER[0]
        self._start_ns = self._clock()

    def add_work(self, name: str, count: int) -> None:
        if self._start_ns is None or self._current_phase is None:
            raise RuntimeError("phase work arrived outside a live phase")
        if not isinstance(name, str) or not name:
            raise ValueError("phase work name must be nonempty")
        allowed = _PHASE_WORK_COUNTERS.get(self._current_phase, ())
        if name not in allowed:
            raise ValueError("work counter belongs to another semantic phase")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("phase work count must be nonnegative")
        self._work[name] = self._work.get(name, 0) + count

    def _close(self, stop_ns: int, device_ns: int) -> None:
        assert self._start_ns is not None
        assert self._current_phase is not None
        if stop_ns < self._start_ns:
            raise RuntimeError("phase clock moved backwards")
        row = PhaseRow(
            ordinal=len(self._rows),
            population=self.population,
            family=self.family,
            repeat=self._repeat,
            tile=self._tile,
            phase=self._current_phase,
            host_start_ns=self._start_ns,
            host_stop_ns=stop_ns,
            host_ns=stop_ns - self._start_ns,
            device_ns=device_ns,
            chunks=self.chunks,
            work=MappingProxyType(dict(self._work)),
        )
        self._rows.append(row)
        if self._emit is not None:
            self._emit(row)
        self._work.clear()
        self._start_ns = stop_ns

    def switch(self, phase: str, *, repeat: int, tile: int) -> None:
        if phase not in PHASE_ORDER:
            raise ValueError("phase ledger switch names an unknown phase")
        if self._start_ns is None or self._current_phase is None:
            raise RuntimeError("phase ledger was not started")
        if (phase, repeat, tile) == (self._current_phase, self._repeat, self._tile):
            return
        if phase not in _ALLOWED_PHASE_TRANSITIONS[self._current_phase]:
            raise ValueError("phase ledger semantic transition differs")
        device_ns = self._device_terminal()
        stop = self._clock()
        self._close(stop, device_ns)
        if self._deadline is not None and stop > self._deadline:
            raise TimeoutError("calibration_population_wall_crossed")
        self._current_phase = phase
        self._repeat = repeat
        self._tile = tile

    def finish(self) -> tuple[PhaseRow, ...]:
        if self._start_ns is None or self._current_phase is None:
            raise RuntimeError("phase ledger was not started")
        device_ns = self._device_terminal()
        stop = self._clock()
        self._close(stop, device_ns)
        if self._deadline is not None and stop > self._deadline:
            raise TimeoutError("calibration_population_wall_crossed")
        for left, right in zip(self._rows, self._rows[1:]):
            if left.host_stop_ns != right.host_start_ns:
                raise AssertionError("phase ledger is not contiguous")
        if sum(row.host_ns for row in self._rows) != (
            self._rows[-1].host_stop_ns - self._rows[0].host_start_ns
        ):
            raise AssertionError("phase ledger does not reconstruct its wall")
        self._current_phase = None
        self._start_ns = None
        return tuple(self._rows)


class _CudaBoundaryClock:
    def __init__(self, cp: Any) -> None:
        self._cp = cp
        self._start = cp.cuda.Event()
        self._start.record()

    def terminal(self) -> int:
        stop = self._cp.cuda.Event()
        stop.record()
        stop.synchronize()
        milliseconds = float(self._cp.cuda.get_elapsed_time(self._start, stop))
        self._start = self._cp.cuda.Event()
        self._start.record()
        return int(math.ceil(milliseconds * 1_000_000.0))


class _KernelProxy:
    def __init__(self, name: str, target: Any, tracker: "_CampaignTracker") -> None:
        self.name = name
        self.target = target
        self.tracker = tracker

    @property
    def ptr(self) -> Any:
        return self.target.ptr

    def linear_launch(self, total: int, arguments: tuple[object, ...], **kwargs: Any) -> Any:
        self.tracker.before_kernel(self.name, arguments)
        result = self.target.linear_launch(total, arguments, **kwargs)
        self.tracker.after_kernel(self.name, arguments)
        return result


def _integer_argument(arguments: tuple[object, ...], index: int) -> int:
    value = arguments[index]
    if isinstance(value, np.generic):
        return int(value.item())
    return int(value)  # type: ignore[arg-type]


class _CampaignTracker:
    def __init__(self, ledger: PhaseLedger, available_cards: int) -> None:
        self.ledger = ledger
        self.available_cards = available_cards
        self.geometry = population_geometry(available_cards)
        self.repeat = 0
        self.tile = 0

    def set_context(self, direction: str, *, repeat: int, tile: int) -> None:
        self.ledger.direction = direction
        self.repeat = repeat
        self.tile = tile

    def switch(self, phase: str) -> None:
        self.ledger.switch(phase, repeat=self.repeat, tile=self.tile)

    def before_kernel(self, name: str, arguments: tuple[object, ...]) -> None:
        if self.ledger.mutation_mode:
            self.switch("mutations_and_lifecycle")
            return
        direction = self.ledger.direction
        if name == "source_coefficients_tile":
            phase = "forward_source_and_offset"
        elif name == "direct_selected_queries_tile":
            phase = "direct_query"
        elif name == "direct_selected_fold_tile":
            phase = "direct_fold"
        elif name == "zeta_level_tile":
            phase = (
                "forward_recurrence"
                if direction == "forward"
                else "adjoint_recurrence_and_signed_sources"
            )
        elif name == "signed_targets_tile":
            phase = (
                "forward_signed_targets"
                if _integer_argument(arguments, 4) == 0
                else "adjoint_recurrence_and_signed_sources"
            )
        elif name in {"fold_query_tile", "reduce_contiguous_pairs"}:
            phase = "forward_fold_and_global_tree"
        elif name in {"build_numerator_covector_tile", "aggregate_query_labels_tile"}:
            phase = "adjoint_covector_and_labels"
        elif name == "direct_selected_adjoint_tile":
            phase = "direct_adjoint"
        elif name == "source_adjoint_contract_tile":
            phase = "adjoint_source_contract_and_global_tree"
        elif name in {"reduce_strided_pairs", "finalize_pair_result"}:
            phase = (
                "forward_fold_and_global_tree"
                if direction == "forward"
                else "adjoint_source_contract_and_global_tree"
            )
        else:
            return
        self.switch(phase)

    def after_kernel(self, name: str, arguments: tuple[object, ...]) -> None:
        if self.ledger.mutation_mode:
            return
        add = self.ledger.add_work
        if name == "source_coefficients_tile":
            rank_start = _integer_argument(arguments, 2)
            records = _integer_argument(arguments, 3)
            if rank_start == 0 and records == self.geometry.source_occupancies:
                add("source_pairing_visits", records * 90)
                add("source_weight_pair_times_float64", records * 90 * 6)
        elif name == "zeta_level_tile":
            rows = _integer_argument(arguments, 3)
            n = _integer_argument(arguments, 4)
            level = _integer_argument(arguments, 5)
            logical = _integer_argument(arguments, 7)
            prefix = "forward" if self.ledger.direction == "forward" else "adjoint"
            add(f"{prefix}_recurrence_pair_child_adds", rows * logical * (n - level))
            add(f"{prefix}_pair_divides", rows * logical)
        elif name == "signed_targets_tile":
            source_cards = _integer_argument(arguments, 2)
            target_cards = _integer_argument(arguments, 5)
            records = _integer_argument(arguments, 7)
            logical = _integer_argument(arguments, 9)
            terms = sum(comb(target_cards, level) for level in range(source_cards + 1))
            prefix = "forward" if _integer_argument(arguments, 4) == 0 else "adjoint"
            add(f"{prefix}_signed_subset_pair_terms", records * logical * terms)
        elif name == "fold_query_tile":
            add(
                "forward_fold_pair_times_pair",
                _integer_argument(arguments, 2) * _integer_argument(arguments, 4),
            )
        elif name == "build_numerator_covector_tile":
            add(
                "adjoint_covector_pair_times_float64",
                _integer_argument(arguments, 2) * _integer_argument(arguments, 4),
            )
        elif name == "aggregate_query_labels_tile":
            add(
                "adjoint_label_pair_adds",
                _integer_argument(arguments, 2)
                * _integer_argument(arguments, 3)
                * _integer_argument(arguments, 4),
            )
        elif name == "source_adjoint_contract_tile":
            records = _integer_argument(arguments, 2)
            logical = _integer_argument(arguments, 4)
            add("adjoint_source_pairing_visits", records * 90)
            add("adjoint_source_weight_pair_times_float64", records * 90 * 6)
            add("adjoint_contract_pair_times_pair", records * logical)
        elif name == "reduce_contiguous_pairs":
            add("forward_tree_contributions", _integer_argument(arguments, 2))
        elif name == "reduce_strided_pairs":
            counter = (
                "forward_tree_contributions"
                if self.ledger.direction == "forward"
                else "adjoint_tree_contributions"
            )
            add(counter, _integer_argument(arguments, 4))
        elif name == "direct_selected_queries_tile":
            rows = _integer_argument(arguments, 2)
            n = _integer_argument(arguments, 3)
            queries = _integer_argument(arguments, 6)
            features = _integer_argument(arguments, 8)
            add("direct_query_source_unranks", queries * rows)
            add(
                "direct_query_compatible_boundary_pair_adds",
                queries * comb(n - 4, 6) * features,
            )
        elif name == "direct_selected_fold_tile":
            rows = _integer_argument(arguments, 2)
            n = _integer_argument(arguments, 3)
            queries = _integer_argument(arguments, 7)
            logical = _integer_argument(arguments, 9)
            add("direct_fold_source_unranks", queries * rows)
            add(
                "direct_fold_compatible_coefficient_pair_adds",
                queries * comb(n - 4, 6) * logical,
            )
            add("direct_fold_final_feature_pair_products", queries * logical)
        elif name == "direct_selected_adjoint_tile":
            sources = _integer_argument(arguments, 1)
            features = _integer_argument(arguments, 3)
            n = _integer_argument(arguments, 6)
            records = _integer_argument(arguments, 8)
            compatible = 6 * comb(n - 6, 4)
            add("direct_adjoint_source_unranks", sources)
            add("direct_adjoint_query_record_visits", sources * records)
            add("direct_adjoint_compatible_query_weight_builds", sources * compatible)
            add(
                "direct_adjoint_compatible_boundary_pair_adds",
                sources * compatible * features,
            )


def _instrumented_kernels(
    kernels: Mapping[str, object], tracker: _CampaignTracker
) -> Mapping[str, object]:
    return MappingProxyType(
        {name: _KernelProxy(name, kernel, tracker) for name, kernel in kernels.items()}
    )


def _generated_population_runner(
    tracker: _CampaignTracker,
) -> Callable[..., _paired.PairedPopulationExecution]:
    """Clone the hash-bound outer orchestration and inject only phase seams."""

    source = inspect.getsource(_paired._run_device_population)
    replacements = (
        ("collect_direct = fixture.available_cards == 25", "collect_direct = True"),
        (
            "    del table, compatible, numerator_high, numerator_low",
            "    _phase_hook(\"forward_release\")\n"
            "    del table, compatible, numerator_high, numerator_low",
        ),
        (
            "    if missing_label_control:",
            "    _phase_hook(\"mutations_and_lifecycle\")\n"
            "    if missing_label_control:",
        ),
        (
            "    del table, covector, unique, resident",
            "    _phase_hook(\"final_release\")\n"
            "    del table, covector, unique, resident",
        ),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise AssertionError(f"parent population seam differs: {old}")
        source = source.replace(old, new)

    forward_counts: dict[int, int] = {}
    adjoint_counts: dict[int, int] = {}

    def tile_index(start: int) -> int:
        return tuple(value for value, _ in LOGICAL_TILES).index(start)

    def forward_once(*args: Any, **kwargs: Any) -> dict[str, object]:
        tile = tile_index(int(kwargs["global_start"]))
        repeat = forward_counts.get(tile, 0)
        forward_counts[tile] = repeat + 1
        tracker.set_context("forward", repeat=repeat, tile=tile)
        tracker.switch("forward_source_and_offset")
        result = _paired._forward_once(*args, **kwargs)
        tracker.switch("forward_capture_and_digest")
        return result

    def adjoint_once(*args: Any, **kwargs: Any) -> dict[str, object]:
        if tracker.ledger.mutation_mode:
            return _paired._adjoint_once(*args, **kwargs)
        tile = tile_index(int(kwargs["global_start"]))
        repeat = adjoint_counts.get(tile, 0)
        adjoint_counts[tile] = repeat + 1
        tracker.set_context("adjoint", repeat=repeat, tile=tile)
        tracker.switch("adjoint_covector_and_labels")
        result = _paired._adjoint_once(*args, **kwargs)
        tracker.switch("adjoint_capture_digest_and_exact_stream")
        return result

    def phase_hook(phase: str) -> None:
        if phase == "mutations_and_lifecycle":
            tracker.ledger.mutation_mode = True
        tracker.switch(phase)

    namespace = dict(vars(_paired))
    namespace.update(
        {
            "ConsumerPopulationFixture": ConsumerPopulationFixture,
            "_sample_rows": sample_rows,
            "_forward_once": forward_once,
            "_adjoint_once": adjoint_once,
            "_phase_hook": phase_hook,
        }
    )
    exec(compile(source, "<adr0394-generated-population-runner>", "exec"), namespace)
    generated = namespace["_run_device_population"]
    if not callable(generated):
        raise AssertionError("generated population runner is not callable")
    return generated


def _sum_work(rows: Sequence[PhaseRow]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        for name, value in row.work.items():
            result[name] = result.get(name, 0) + int(value)
    return result


def _phase_totals(rows: Sequence[PhaseRow]) -> dict[str, int]:
    result = {phase: 0 for phase in PHASE_ORDER}
    for row in rows:
        result[row.phase] += row.host_ns
    return result


def _run_family(
    cp: Any,
    kernels: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
    *,
    family: str,
    chunks: tuple[int, int, int],
    tile_order: tuple[tuple[int, int], ...],
    missing_label_control: bool,
    population_deadline_ns: int,
    emit_phase: Callable[[PhaseRow], None] | None,
) -> tuple[_paired.PairedPopulationExecution, tuple[PhaseRow, ...]]:
    device_clock = _CudaBoundaryClock(cp)
    ledger = PhaseLedger(
        population=fixture.available_cards,
        family=family,
        chunks=chunks,
        device_terminal=device_clock.terminal,
        emit=emit_phase,
        wall_deadline_ns=population_deadline_ns,
    )
    first_tile = tile_order[0][0]
    ledger.start(repeat=0, tile=tuple(start for start, _ in LOGICAL_TILES).index(first_tile))
    tracker = _CampaignTracker(ledger, fixture.available_cards)
    instrumented = _instrumented_kernels(kernels, tracker)
    runner = _generated_population_runner(tracker)
    execution = runner(
        cp,
        instrumented,
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        tile_order=tile_order,
        missing_label_control=missing_label_control,
    )
    rows = ledger.finish()
    return execution, rows


def _ten_card_legacy_direct_control(
    cp: Any,
    successor_kernels: Mapping[str, object],
    fixture: ConsumerPopulationFixture,
) -> dict[str, object]:
    """Compare canonical rank-major direct rows with the untouched parent."""

    if fixture.available_cards != 10:
        raise ValueError("legacy direct control is restricted to ten cards")
    parent_kernels = _paired._kernels(cp)
    resident = _paired._allocate_resident(cp, fixture)
    geometry = fixture.geometry
    table = cp.empty(
        (geometry.source_recurrence_rows, PHYSICAL_STRIDE_WIDTH),
        dtype=cp.float64,
    )
    source_offset = _paired.cardinality_offsets(10, SOURCE_CARDS)[SOURCE_CARDS]
    source_ranks, query_records = sample_rows(10)
    parent_digests: list[str] = []
    successor_digests: list[str] = []
    gates: dict[str, bool] = {}
    try:
        for tile, (global_start, stop) in enumerate(LOGICAL_TILES):
            logical_width = stop - global_start
            table.fill(_paired._POISON)
            _paired._launch_source_tile(
                successor_kernels,
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
            parent_query, parent_fold, parent_features = (
                _paired._direct_forward_samples(
                    cp,
                    parent_kernels,
                    resident,
                    fixture,
                    table,
                    query_records,
                    global_start,
                    logical_width,
                )
            )
            successor_query, successor_fold, successor_features = (
                _paired._direct_forward_samples(
                    cp,
                    successor_kernels,
                    resident,
                    fixture,
                    table,
                    query_records,
                    global_start,
                    logical_width,
                )
            )
            parent_adjoint, parent_adjoint_features = (
                _paired._direct_adjoint_samples(
                    cp,
                    parent_kernels,
                    resident,
                    fixture,
                    source_ranks,
                    global_start,
                    logical_width,
                )
            )
            successor_adjoint, successor_adjoint_features = (
                _paired._direct_adjoint_samples(
                    cp,
                    successor_kernels,
                    resident,
                    fixture,
                    source_ranks,
                    global_start,
                    logical_width,
                )
            )
            gates[f"tile_{tile}_feature_identity"] = (
                parent_features == successor_features == parent_adjoint_features
                == successor_adjoint_features
            )
            gates[f"tile_{tile}_query_byte_identity"] = (
                parent_query.tobytes() == successor_query.tobytes()
            )
            gates[f"tile_{tile}_fold_byte_identity"] = (
                parent_fold.tobytes() == successor_fold.tobytes()
            )
            gates[f"tile_{tile}_adjoint_byte_identity"] = (
                parent_adjoint.tobytes() == successor_adjoint.tobytes()
            )
            parent_digests.append(
                _paired._reporting_digest(
                    parent_query, parent_fold, parent_adjoint
                )
            )
            successor_digests.append(
                _paired._reporting_digest(
                    successor_query, successor_fold, successor_adjoint
                )
            )
    finally:
        del table, resident
        gc.collect()
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
    gates["all_tile_digests_identical"] = parent_digests == successor_digests
    gates["absolute_pool_release"] = (
        int(cp.get_default_memory_pool().used_bytes()) == 0
        and int(cp.get_default_memory_pool().total_bytes()) == 0
        and int(cp.get_default_pinned_memory_pool().n_free_blocks()) == 0
    )
    return {
        "schema_version": "legal-river-work-preflight-legacy-direct-control-v1",
        "population": 10,
        "parent_digests": parent_digests,
        "successor_digests": successor_digests,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def _pair_error_evidence(
    available_cards: int,
    normal: _paired.PairedPopulationExecution,
    alternate: _paired.PairedPopulationExecution,
    fixture: ConsumerPopulationFixture,
) -> dict[str, object]:
    source_ranks, _ = sample_rows(available_cards)
    source_expected = tuple(
        _consumer._source_row_exact(fixture, rank)[feature]
        for rank in source_ranks
        for feature in BOUNDARY_FEATURES
    )
    source_abs, source_rel = _paired._maximum_pair_errors(
        normal.source_samples, source_expected
    )
    direct_query_expected = tuple(
        _paired._pair_from_array(pair).exact
        for pair in normal.direct_query_samples.reshape(-1, 2)
    )
    query_abs, query_rel = _paired._maximum_pair_errors(
        normal.query_samples, direct_query_expected
    )
    direct_fold_expected = tuple(
        _paired._pair_from_array(pair).exact
        for pair in normal.direct_fold_samples.reshape(-1, 2)
    )
    fold_abs, fold_rel = _paired._maximum_pair_errors(
        normal.fold_samples, direct_fold_expected
    )
    direct_adjoint_expected = tuple(
        _paired._pair_from_array(pair).exact
        for pair in normal.direct_adjoint_samples.reshape(-1, 2)
    )
    adjoint_abs, adjoint_rel = _paired._maximum_pair_errors(
        normal.adjoint_samples, direct_adjoint_expected
    )
    captured_forward = _paired._captured_stream(normal.forward_contribution_tiles)
    captured_transpose = _paired._captured_stream(normal.transpose_contribution_tiles)
    captured_residual = abs(captured_forward - captured_transpose)
    captured_relative = _paired._scale_relative(captured_residual, captured_forward)
    device_residual = abs(normal.numerator.exact - normal.transpose.exact)
    device_relative = _paired._scale_relative(device_residual, normal.numerator.exact)
    device_forward_error = abs(normal.numerator.exact - captured_forward)
    device_transpose_error = abs(normal.transpose.exact - captured_transpose)
    errors = {
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
    v1, _ = _paired.load_preregistered_compensated_tile_configs()
    absolute = _paired._fraction_limit(v1, "bounded_transpose_dot_absolute")
    relative = _paired._fraction_limit(v1, "bounded_scale_normalized_relative")
    source_limit = _paired._fraction_limit(v1, "bounded_source_sample_absolute")
    forward_limit = _paired._fraction_limit(v1, "bounded_forward_row_absolute")
    fold_limit = _paired._fraction_limit(v1, "bounded_fold_absolute")
    adjoint_limit = _paired._fraction_limit(v1, "bounded_adjoint_row_absolute")
    gates = {
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
        "default_alternate_byte_identity": _paired._execution_byte_identity(
            normal, alternate
        ),
        "repeat_snapshot_restore_byte_identity": (
            normal.repeat_byte_identity and alternate.repeat_byte_identity
        ),
        "inactive_final_tile_poison": (
            normal.inactive_poison_pass and alternate.inactive_poison_pass
        ),
        "source_global_offset_control": (
            normal.source_offset_control_pass and alternate.source_offset_control_pass
        ),
        "nonzero_query_offset": (
            normal.nonzero_query_offset_observed
            and alternate.nonzero_query_offset_observed
        ),
        "nonzero_source_offset": (
            normal.nonzero_source_offset_observed
            and alternate.nonzero_source_offset_observed
        ),
        "forward_release_before_adjoint": (
            normal.forward_released_before_adjoint
            and alternate.forward_released_before_adjoint
        ),
        "accumulator_lifecycle": (
            normal.accumulator_lifecycle_pass and alternate.accumulator_lifecycle_pass
        ),
        "missing_label_mutation_rejected": (
            normal.missing_label_changed_result is True
        ),
        "pool_release": all(
            value == 0
            for value in (
                normal.released_pool_used_bytes,
                normal.released_pool_total_bytes,
                normal.released_pinned_blocks,
                alternate.released_pool_used_bytes,
                alternate.released_pool_total_bytes,
                alternate.released_pinned_blocks,
            )
        ),
        "chip_units": Fraction(-10) <= normal.conditional_value <= Fraction(50),
    }
    if available_cards == 10:
        authority = _paired._ten_card_authority(fixture)
        if any(
            value is None
            for value in (
                normal.full_source,
                normal.full_compatible,
                normal.full_fold,
                normal.full_adjoint,
            )
        ):
            raise AssertionError("ten-card execution omitted complete arrays")
        assert normal.full_source is not None
        assert normal.full_compatible is not None
        assert normal.full_fold is not None
        assert normal.full_adjoint is not None
        exact_cases = {
            "complete_fraction_source": (
                normal.full_source,
                tuple(value for row in authority.source for value in row),
                source_limit,
            ),
            "complete_fraction_forward": (
                normal.full_compatible,
                tuple(
                    authority.source[source_rank][feature]
                    for source_rank in authority.compatible_source_ranks
                    for feature in range(TOTAL_FEATURE_WIDTH)
                ),
                forward_limit,
            ),
            "complete_fraction_fold": (
                normal.full_fold,
                tuple(value for row in authority.fold for value in row),
                fold_limit,
            ),
            "complete_fraction_adjoint": (
                normal.full_adjoint,
                tuple(value for row in authority.adjoint for value in row),
                adjoint_limit,
            ),
        }
        for label, (actual, expected, limit) in exact_cases.items():
            error_abs, error_rel = _paired._maximum_pair_errors(actual, expected)
            errors[f"{label}_absolute"] = error_abs
            errors[f"{label}_relative"] = error_rel
            gates[f"{label}_absolute"] = error_abs <= limit
            gates[f"{label}_relative"] = error_rel <= relative
    return {
        "schema_version": "legal-river-work-preflight-population-evidence-v1",
        "population": available_cards,
        "scalar_pairs": _paired._scalar_pair_map(normal),
        "conditional_value": normal.conditional_value,
        "maximum_errors": errors,
        "reporting_digests": {
            "source_samples": _paired._reporting_digest(normal.source_samples),
            "query_samples": _paired._reporting_digest(normal.query_samples),
            "fold_samples": _paired._reporting_digest(normal.fold_samples),
            "adjoint_samples": _paired._reporting_digest(normal.adjoint_samples),
            "direct_samples": _paired._reporting_digest(
                normal.direct_query_samples,
                normal.direct_fold_samples,
                normal.direct_adjoint_samples,
            ),
            "contribution_streams": _paired._reporting_digest(
                *normal.forward_contribution_tiles,
                *normal.transpose_contribution_tiles,
            ),
        },
        "telemetry": {
            "maximum_pool_total_bytes": max(
                normal.maximum_pool_total_bytes, alternate.maximum_pool_total_bytes
            ),
            "maximum_host_numeric_bytes": max(
                normal.maximum_host_numeric_bytes, alternate.maximum_host_numeric_bytes
            ),
        },
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def _chunk_tuple(
    config: Mapping[str, object], available_cards: int, family: str
) -> tuple[int, int, int]:
    section = config["chunk_contract"][str(available_cards)]  # type: ignore[index]
    key = "default" if family == POPULATION_FAMILIES[0] else "alternate"
    values = section[key]  # type: ignore[index]
    return tuple(int(value) for value in values)  # type: ignore[arg-type,return-value]


def run_calibration_preflight(
    emit: Callable[[str, Mapping[str, object]], None] | None = None,
) -> dict[str, object]:
    """Run the one bounded 10/22 calibration; never constructs population 25."""

    global _BOUNDED_EXECUTION_CALLS
    _BOUNDED_EXECUTION_CALLS += 1
    if _BOUNDED_EXECUTION_CALLS != 1:
        raise RuntimeError("work-preflight bounded execution is one-shot per process")
    config = load_preregistered_work_preflight_config()
    verify_preregistered_work_preflight_contract(config)

    def send(kind: str, payload: Mapping[str, object]) -> None:
        if emit is not None:
            emit(kind, _plain(payload))

    cp = _cupy_module()
    runtime = _paired._runtime_identity(cp)
    _paired._verify_runtime(runtime, config)
    try:
        kernels = _kernels(cp)
        resources = _paired._kernel_resource_report(cp, kernels)
        direct_resources = {
            name: dict(resources[name])
            for name in (
                "direct_selected_queries_tile",
                "direct_selected_fold_tile",
                "direct_selected_adjoint_tile",
            )
        }
        cubin_resources = _compiled_cubin_resource_usage(cp, direct_resources)
    except Exception as error:  # first compiler/resource failure is typed evidence
        send(
            "laboratory",
            {
                "schema_version": "legal-river-work-preflight-laboratory-v1",
                "kind": "compiler_resource_failure",
                "runtime": runtime,
                "stage": "kernel_compile_and_resource_inspection",
                "reason": (
                    f"{type(error).__name__}: "
                    f"{(str(error) or 'exception carried no message')[:4096]}"
                ),
                "correction_config_sha256": CORRECTION_CONFIG_SHA256,
            },
        )
        return {
            "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
            "terminal": "compiler_or_primitive_rejection",
            "failed_population": None,
            "passed": False,
            "projection": None,
        }
    primitive = _paired._run_primitive_controls(cp, kernels)
    direct_order = run_direct_order_controls()
    all_rows: dict[int, list[PhaseRow]] = {10: [], 22: []}
    population_evidence: dict[int, dict[str, object]] = {}
    population_limit = int(
        config["one_shot_lifecycle"]["calibration_population_wall_limit_ns"]  # type: ignore[index]
    )

    send(
        "laboratory",
        {
            "schema_version": "legal-river-work-preflight-laboratory-v1",
            "kind": "runtime_primitives_and_compiler",
            "runtime": runtime,
            "primitive_gates": primitive.gates,
            "direct_order_controls": direct_order,
            "direct_kernel_resources": direct_resources,
            "cubin_resource_usage": cubin_resources,
        },
    )
    resource_gates = cubin_resources["gates"]
    if (
        not primitive.all_gates_pass
        or direct_order["all_gates_pass"] is not True
        or not all(resource_gates.values())  # type: ignore[union-attr]
    ):
        return {
            "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
            "terminal": "compiler_or_primitive_rejection",
            "failed_population": None,
            "passed": False,
            "projection": None,
        }
    for cards in CALIBRATION_POPULATIONS:
        fixture = compile_calibration_fixture(cards)
        if cards == 10:
            legacy_direct = _ten_card_legacy_direct_control(
                cp, kernels, fixture
            )
            send(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "complete_ten_legacy_direct_byte_identity",
                    "control": legacy_direct,
                },
            )
            if legacy_direct["all_gates_pass"] is not True:
                return {
                    "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                    "terminal": "calibration_scientific_rejection",
                    "failed_population": 10,
                    "passed": False,
                    "projection": None,
                }
            resident = _paired._allocate_resident(cp, fixture)
            query_weight = _paired._query_weight_evidence(cp, kernels, resident, fixture)
            del resident
            gc.collect()
            cp.get_default_memory_pool().free_all_blocks()
            cp.get_default_pinned_memory_pool().free_all_blocks()
            send(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "complete_ten_query_weight_control",
                    "gates": query_weight.gates,
                },
            )
            if not query_weight.all_gates_pass:
                return {
                    "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                    "terminal": "calibration_scientific_rejection",
                    "failed_population": 10,
                    "passed": False,
                    "projection": None,
                }
        population_started = perf_counter_ns()
        deadline = population_started + population_limit
        executions: list[_paired.PairedPopulationExecution] = []
        for family in POPULATION_FAMILIES:
            chunks = _chunk_tuple(config, cards, family)
            reverse = family == POPULATION_FAMILIES[1]

            def emit_phase(row: PhaseRow) -> None:
                all_rows[cards].append(row)
                send("phase", row.payload())

            try:
                execution, _ = _run_family(
                    cp,
                    kernels,
                    fixture,
                    family=family,
                    chunks=chunks,
                    tile_order=(
                        tuple(reversed(LOGICAL_TILES)) if reverse else LOGICAL_TILES
                    ),
                    missing_label_control=not reverse,
                    population_deadline_ns=deadline,
                    emit_phase=emit_phase,
                )
                executions.append(execution)
                if perf_counter_ns() > deadline:
                    raise TimeoutError("calibration_population_wall_crossed")
            except TimeoutError as error:
                elapsed = perf_counter_ns() - population_started
                send(
                    "laboratory",
                    {
                        "schema_version": "legal-river-work-preflight-laboratory-v1",
                        "kind": "calibration_population_wall_failure",
                        "population": cards,
                        "family": family,
                        "elapsed_ns": elapsed,
                        "limit_ns": population_limit,
                        "reason": str(error),
                    },
                )
                return {
                    "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                    "terminal": "calibration_scientific_rejection",
                    "failed_population": cards,
                    "passed": False,
                    "projection": None,
                }
        work = _sum_work(all_rows[cards])
        expected_work = complete_campaign_work(cards)
        if work != expected_work:
            raise RuntimeError(
                f"executed work ledger differs for population {cards}: "
                f"observed={work!r} expected={expected_work!r}"
            )
        evidence = _pair_error_evidence(cards, executions[0], executions[1], fixture)
        phase_totals = _phase_totals(all_rows[cards])
        campaign_wall = sum(phase_totals.values())
        gates = dict(evidence["gates"])  # type: ignore[arg-type]
        gates["executed_work_ledger_exact"] = True
        gates["phase_partition_exact"] = all(
            left.host_stop_ns == right.host_start_ns
            for family in POPULATION_FAMILIES
            for left, right in zip(
                [row for row in all_rows[cards] if row.family == family],
                [row for row in all_rows[cards] if row.family == family][1:],
            )
        )
        gates["population_wall"] = campaign_wall <= population_limit
        evidence["gates"] = gates
        evidence["all_gates_pass"] = all(gates.values())
        evidence["phase_host_ns"] = phase_totals
        evidence["campaign_host_ns"] = campaign_wall
        evidence["executed_work"] = work
        population_evidence[cards] = evidence
        send("population", evidence)
        if not evidence["all_gates_pass"]:
            return {
                "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                "terminal": "calibration_scientific_rejection",
                "failed_population": cards,
                "passed": False,
                "projection": None,
            }
    projection = reconstruct_projection(
        {
            cards: population_evidence[cards]["phase_host_ns"]  # type: ignore[dict-item]
            for cards in CALIBRATION_POPULATIONS
        },
        config,
    )
    send("projection", projection)
    return {
        "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
        "terminal": (
            "completed_capacity_pass"
            if projection["passed"]
            else "completed_capacity_rejection"
        ),
        "failed_population": None,
        "passed": bool(projection["passed"]),
        "projection": projection,
    }


__all__ = [
    "BOUNDARY_FEATURES",
    "CALIBRATION_POPULATIONS",
    "CORRECTION_ADR_SHA256",
    "CORRECTION_CONFIG_RELATIVE_PATH",
    "CORRECTION_CONFIG_SHA256",
    "CONFIG_RELATIVE_PATH",
    "CUDA_COMPILE_OPTIONS",
    "CUDA_SOURCE",
    "ConsumerPopulationFixture",
    "DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES",
    "DIRECT_KERNEL_REGISTER_LIMIT",
    "LOGICAL_TILES",
    "PHASE_ORDER",
    "PREREGISTERED_CONFIG_SHA256",
    "PROJECTION_POPULATION",
    "PhaseLedger",
    "PhaseRow",
    "PopulationGeometry",
    "RESERVED_ACTUAL_RESULT_RELATIVE_PATH",
    "RESULT_RELATIVE_PATH",
    "actual_execution_call_count",
    "actual_numeric_allocation_call_count",
    "actual_scientific_call_count",
    "bounded_execution_call_count",
    "build_cuda_source",
    "canonical_lf_sha256",
    "compile_calibration_fixture",
    "combined_direct_kernel_resource_report",
    "complete_campaign_work",
    "cuda_compile_options",
    "cupy_import_call_count",
    "direct_kernel_resource_gates",
    "load_preregistered_work_preflight_config",
    "load_work_preflight_resource_correction",
    "phase_projection_constituents",
    "phase_projection_ratio",
    "parse_cuobjdump_resource_usage",
    "population_geometry",
    "reconstruct_projection",
    "run_direct_order_controls",
    "run_calibration_preflight",
    "sample_rows",
    "verify_preregistered_work_preflight_contract",
]
