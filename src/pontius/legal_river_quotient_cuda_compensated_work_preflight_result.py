"""Standard-library reader for the composite ADR-0394/ADR-0395 preflight."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import re
from typing import Mapping, Sequence

from .durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_bytes,
    recover_journal_file,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
_CORRECTION_CONFIG = _ROOT / CORRECTION_CONFIG_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
PREREGISTERED_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
CORRECTION_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
PREREGISTRATION_COMMIT = "fc1892e15522eed4b9935de0404131646820c451"
WORK_PREFLIGHT_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0394-work-preflight-exclusive-journal-v1"
).hexdigest()
WORK_PREFLIGHT_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0394-work-preflight-one-shot-campaign-v1"
).hexdigest()
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
FAMILIES = (
    "default_chunks_forward_tile_order",
    "alternate_chunks_reverse_tile_order",
)
CALIBRATION_POPULATIONS = (10, 22)
DIRECT_KERNEL_NAMES = {
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
}
CUDA_COMPILE_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)
DIRECT_KERNEL_REGISTER_LIMIT = 255
DIRECT_KERNEL_BACKING_LIMIT_BYTES = 4096
MAXIMUM_RESIDENT_THREAD_BOUND = 131_072
FROZEN_DEVICE_RESERVE_BYTES = 2_000_000_000
CLAIMS = {
    "complete_25_numerical_value": None,
    "actual_45_card_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "action_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}


_DEPENDENCY_PATHS = {
    "config": _CONFIG,
    "resource_correction_config": _CORRECTION_CONFIG,
    "resource_correction_adr": _ROOT
    / "docs/decisions/"
    "ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md",
    "source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
    "runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py",
    "reader": Path(__file__),
    "parent_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "parent_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
}


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"work-preflight reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer at least {minimum}")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _load_config() -> dict[str, object]:
    raw = _CONFIG.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight reader config differs from ADR-0394")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-config-v1"
    ):
        raise ValueError("work-preflight reader config schema differs")
    return value


def _load_resource_correction() -> dict[str, object]:
    raw = _CORRECTION_CONFIG.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != CORRECTION_CONFIG_SHA256:
        raise ValueError("work-preflight reader correction differs from ADR-0395")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-resource-correction-v2"
    ):
        raise ValueError("work-preflight reader correction schema differs")
    return value


def geometry(available_cards: int) -> dict[str, int]:
    if available_cards not in (10, 22, 25):
        raise ValueError("work-preflight reader geometry is restricted")
    return {
        "source_occupancies": comb(available_cards, 6),
        "query_occupancies": comb(available_cards, 4),
        "labeled_query_records": 6 * comb(available_cards, 4),
        "source_recurrence_rows": sum(comb(available_cards, k) for k in range(7)),
        "adjoint_recurrence_rows": sum(comb(available_cards, k) for k in range(5)),
        "compatible_sources_per_query_occupancy": comb(available_cards - 4, 6),
        "compatible_labeled_query_records_per_source": 6 * comb(available_cards - 6, 4),
    }


def complete_campaign_work(available_cards: int) -> dict[str, int]:
    values = geometry(available_cards)
    executions = 4
    width = 176
    source = values["source_occupancies"]
    query = values["query_occupancies"]
    records = values["labeled_query_records"]
    compatible_sources = values["compatible_sources_per_query_occupancy"]
    compatible_records = values["compatible_labeled_query_records_per_source"]
    return {
        "source_pairing_visits": source * 90 * executions * 3,
        "source_weight_pair_times_float64": source * 90 * 6 * executions * 3,
        "forward_recurrence_pair_child_adds": executions * width * sum(
            comb(available_cards, level) * (available_cards - level)
            for level in range(6)
        ),
        "forward_pair_divides": executions * width * sum(
            comb(available_cards, level) for level in range(6)
        ),
        "forward_signed_subset_pair_terms": executions * records * width * 16,
        "forward_fold_pair_times_pair": executions * records * width,
        "forward_tree_contributions": executions * records * 4,
        "adjoint_covector_pair_times_float64": executions * records * width,
        "adjoint_label_pair_adds": executions * query * 6 * width,
        "adjoint_recurrence_pair_child_adds": executions * width * sum(
            comb(available_cards, level) * (available_cards - level)
            for level in range(4)
        ),
        "adjoint_pair_divides": executions * width * sum(
            comb(available_cards, level) for level in range(4)
        ),
        "adjoint_signed_subset_pair_terms": executions * source * width * 57,
        "adjoint_source_pairing_visits": source * 90 * executions * 3,
        "adjoint_source_weight_pair_times_float64": source * 90 * 6 * executions * 3,
        "adjoint_contract_pair_times_pair": executions * source * width,
        "adjoint_tree_contributions": executions * source * 3,
        "direct_query_source_unranks": 16 * source * 3 * executions,
        "direct_query_compatible_boundary_pair_adds": (
            16 * compatible_sources * 8 * executions
        ),
        "direct_fold_source_unranks": 16 * source * 3 * executions,
        "direct_fold_compatible_coefficient_pair_adds": (
            16 * compatible_sources * width * executions
        ),
        "direct_fold_final_feature_pair_products": 16 * width * executions,
        "direct_adjoint_source_unranks": 16 * 3 * executions,
        "direct_adjoint_query_record_visits": 16 * records * 3 * executions,
        "direct_adjoint_compatible_query_weight_builds": (
            16 * compatible_records * 3 * executions
        ),
        "direct_adjoint_compatible_boundary_pair_adds": (
            16 * compatible_records * 8 * executions
        ),
    }


_FROZEN_CHUNKS = {
    10: ((17, 3, 11), (13, 2, 7)),
    22: ((32768, 4096, 32768), (16381, 2047, 16381)),
    25: ((65536, 10922, 32768), (32767, 4093, 16381)),
}

_PHASE_WORK_COUNTERS = {
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

_ALLOWED_PHASE_TRANSITIONS = {
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
    "adjoint_covector_and_labels": ("adjoint_recurrence_and_signed_sources",),
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


def _chunk_counts(cards: int) -> tuple[tuple[int, int, int], ...]:
    shapes = geometry(cards)
    totals = (
        shapes["labeled_query_records"],
        shapes["query_occupancies"],
        shapes["source_occupancies"],
    )
    return tuple(
        tuple((total + size - 1) // size for total, size in zip(totals, family))
        for family in _FROZEN_CHUNKS[cards]
    )


def phase_constituents(phase: str, cards: int) -> tuple[tuple[str, int, int], ...]:
    if phase not in PHASE_ORDER or cards not in CALIBRATION_POPULATIONS:
        raise ValueError("reader projection constituent identity differs")
    target = geometry(25)
    endpoint = geometry(cards)
    target_work = complete_campaign_work(25)
    endpoint_work = complete_campaign_work(cards)
    rows: list[tuple[str, int, int]] = []
    if phase in {"direct_query", "direct_fold"}:
        field = "compatible_sources_per_query_occupancy"
    elif phase == "forward_recurrence":
        rows.append(
            (
                "forward_recurrence_pair_child_adds",
                target_work["forward_recurrence_pair_child_adds"],
                endpoint_work["forward_recurrence_pair_child_adds"],
            )
        )
        field = ""
    elif phase in {
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
        "adjoint_covector_and_labels",
    }:
        field = "labeled_query_records"
    elif phase == "direct_adjoint":
        field = "compatible_labeled_query_records_per_source"
    else:
        field = "source_occupancies"
    if field:
        rows.append((field, target[field], endpoint[field]))
    for counter in _PHASE_WORK_COUNTERS.get(phase, ()):
        rows.append((counter, target_work[counter], endpoint_work[counter]))
    live_fields = {
        "fixture_and_resident_birth": (
            "source_occupancies", "source_recurrence_rows",
            "labeled_query_records", "adjoint_recurrence_rows",
        ),
        "forward_source_and_offset": ("source_occupancies", "source_recurrence_rows"),
        "forward_recurrence": ("source_recurrence_rows",),
        "forward_signed_targets": ("labeled_query_records",),
        "forward_fold_and_global_tree": ("labeled_query_records",),
        "forward_capture_and_digest": ("labeled_query_records",),
        "forward_release": (
            "source_occupancies", "source_recurrence_rows",
            "labeled_query_records", "adjoint_recurrence_rows",
        ),
        "adjoint_covector_and_labels": ("labeled_query_records", "query_occupancies"),
        "adjoint_recurrence_and_signed_sources": (
            "source_occupancies", "adjoint_recurrence_rows",
        ),
        "adjoint_source_contract_and_global_tree": ("source_occupancies",),
        "adjoint_capture_digest_and_exact_stream": ("source_occupancies",),
        "mutations_and_lifecycle": ("source_occupancies", "labeled_query_records"),
        "final_release": (
            "source_occupancies", "source_recurrence_rows",
            "labeled_query_records", "adjoint_recurrence_rows",
        ),
    }.get(phase, ())
    rows.extend((f"live_{field}", target[field], endpoint[field]) for field in live_fields)
    if phase in {
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
    }:
        axes = (0,)
    elif phase == "adjoint_covector_and_labels":
        axes = (1,)
    elif phase in {
        "adjoint_recurrence_and_signed_sources",
        "adjoint_source_contract_and_global_tree",
        "adjoint_capture_digest_and_exact_stream",
    }:
        axes = (2,)
    elif phase == "mutations_and_lifecycle":
        axes = (0, 1, 2)
    else:
        axes = ()
    target_chunks = _chunk_counts(25)
    endpoint_chunks = _chunk_counts(cards)
    for family in range(2):
        for axis in axes:
            rows.append(
                (
                    f"chunk_count_family_{family}_axis_{axis}",
                    target_chunks[family][axis],
                    endpoint_chunks[family][axis],
                )
            )
    return tuple(rows)


def phase_ratio(phase: str, cards: int) -> tuple[int, int]:
    rows = phase_constituents(phase, cards)
    _, numerator, denominator = rows[0]
    for _, candidate_numerator, candidate_denominator in rows[1:]:
        if candidate_numerator * denominator > numerator * candidate_denominator:
            numerator, denominator = candidate_numerator, candidate_denominator
    return numerator, denominator


def _ceil_ratio(value: int, numerator: int, denominator: int) -> int:
    return (value * numerator + denominator - 1) // denominator


def reconstruct_projection(
    phase_host_ns: Mapping[int, Mapping[str, int]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    total = 0
    for phase in PHASE_ORDER:
        candidates = {
            cards: _ceil_ratio(
                phase_host_ns[cards][phase], *phase_ratio(phase, cards)
            )
            for cards in CALIBRATION_POPULATIONS
        }
        upper = _ceil_ratio(max(candidates.values()), 5, 4) + 1_000_000
        total += upper
        rows.append(
            {
                "phase": phase,
                "candidate_10_ns": candidates[10],
                "candidate_22_ns": candidates[22],
                "upper_ns": upper,
            }
        )
    return {
        "schema_version": "legal-river-work-preflight-projection-v1",
        "target_population": 25,
        "phase_rows": rows,
        "projected_host_ns": total,
        "wall_limit_ns": 180_000_000_000,
        "passed": total <= 180_000_000_000,
    }


@dataclass(frozen=True, slots=True)
class ReboundPhase:
    population: int
    family: str
    ordinal: int
    phase: str
    host_start_ns: int
    host_stop_ns: int
    host_ns: int
    work: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class WorkPreflightRebinding:
    terminal: str
    passed: bool
    event_count: int
    phases: tuple[ReboundPhase, ...]
    projection: Mapping[str, object] | None
    journal_byte_count: int


def _validate_config_arithmetic(config: Mapping[str, object]) -> None:
    geometry_section = _mapping(config.get("population_geometry"), label="geometry")
    ratios = _mapping(config.get("phase_projection_ratios"), label="ratios")
    for cards, key in ((10, "10"), (22, "22"), (25, "25_projection_only")):
        if geometry_section.get(key) != geometry(cards):
            raise ValueError(f"reader {cards}-card geometry differs")
        work_key = (
            f"complete_campaign_work_{cards}"
            if cards != 25
            else "complete_campaign_work_25_projection_only"
        )
        stored = _mapping(config.get(work_key), label=f"{cards}-card work")
        if any(stored.get(name) != value for name, value in complete_campaign_work(cards).items()):
            raise ValueError(f"reader {cards}-card work ledger differs")
    chunks = _mapping(config.get("chunk_contract"), label="chunks")
    for cards in (10, 22, 25):
        key = str(cards) if cards != 25 else "25_projection_only"
        default_key = "default" if cards != 25 else "default_inherited"
        alternate_key = "alternate" if cards != 25 else "alternate_inherited"
        section = _mapping(chunks.get(key), label=f"{cards}-card chunks")
        if (
            tuple(section.get(default_key, ())),
            tuple(section.get(alternate_key, ())),
        ) != _FROZEN_CHUNKS[cards]:
            raise ValueError(f"reader {cards}-card chunks differ")
    for phase in PHASE_ORDER:
        entry = _mapping(ratios.get(phase), label=f"ratio {phase}")
        for cards in CALIBRATION_POPULATIONS:
            if entry.get(f"25_over_{cards}") != list(phase_ratio(phase, cards)):
                raise ValueError(f"reader phase ratio differs: {phase}/{cards}")


def _validate_resource_correction(correction: Mapping[str, object]) -> None:
    parent = _mapping(correction.get("parent_identity"), label="correction parent")
    composite = _mapping(
        correction.get("composite_authority"), label="correction composite"
    )
    resource = _mapping(
        correction.get("corrected_resource_contract"), label="correction resource"
    )
    reserve = _mapping(
        correction.get("reserve_arithmetic"), label="correction reserve"
    )
    if (
        parent.get("v1_config_canonical_lf_sha256")
        != PREREGISTERED_CONFIG_SHA256
        or composite.get(
            "future_source_owner_and_reader_must_load_verify_and_report_both_config_hashes"
        )
        is not True
        or tuple(resource.get("caller_supplied_nvrtc_options_unchanged", ()))
        != CUDA_COMPILE_OPTIONS
        or resource.get("register_limit_per_thread")
        != DIRECT_KERNEL_REGISTER_LIMIT
        or resource.get("stack_plus_local_backing_limit_bytes_per_thread")
        != DIRECT_KERNEL_BACKING_LIMIT_BYTES
        or resource.get("exact_spill_load_store_count") is not None
        or reserve.get("maximum_resident_thread_bound")
        != MAXIMUM_RESIDENT_THREAD_BOUND
        or reserve.get("frozen_device_reserve_bytes")
        != FROZEN_DEVICE_RESERVE_BYTES
        or reserve.get("maximum_resident_backing_at_4096_bytes_per_thread")
        != DIRECT_KERNEL_BACKING_LIMIT_BYTES * MAXIMUM_RESIDENT_THREAD_BOUND
    ):
        raise ValueError("reader resource correction differs")


def _parse_cuobjdump_resource_usage(output: object) -> dict[str, dict[str, int]]:
    if not isinstance(output, str) or not output:
        raise ValueError("reader cuobjdump resource output is absent")
    result: dict[str, dict[str, int]] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        function = re.fullmatch(r"Function\s+([^:]+):", line)
        if function:
            current = function.group(1)
            if current in result:
                raise ValueError("reader cuobjdump function repeats")
            result[current] = {}
            continue
        if current is None or not line:
            continue
        for label, raw_value in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in result[current]:
                raise ValueError("reader cuobjdump field repeats")
            result[current][label] = int(raw_value)
    if not DIRECT_KERNEL_NAMES.issubset(result):
        raise ValueError("reader cuobjdump direct kernel is absent")
    for name in DIRECT_KERNEL_NAMES:
        if not {"REG", "STACK", "LOCAL"}.issubset(result[name]):
            raise ValueError("reader cuobjdump direct resource row is incomplete")
    return result


def _validate_resource_laboratory(event: Mapping[str, object]) -> bool:
    driver = _mapping(event.get("direct_kernel_resources"), label="driver resources")
    cubin = _mapping(event.get("cubin_resource_usage"), label="cubin resources")
    if set(driver) != DIRECT_KERNEL_NAMES:
        raise ValueError("reader driver resource kernel set differs")
    expected_cubin_fields = {
        "tool_path",
        "tool_version_output",
        "raw_resource_stdout",
        "cubin_sha256",
        "retained_payload_format",
        "caller_supplied_nvrtc_options",
        "cupy_version",
        "cupy_internal_options_disclosure",
        "direct",
        "driver_direct",
        "effective_maxima",
        "runtime_residency",
        "gates",
        "claims",
    }
    if set(cubin) != expected_cubin_fields:
        raise ValueError("reader cubin resource field set differs")
    if (
        not isinstance(cubin.get("tool_path"), str)
        or not cubin["tool_path"]
        or not isinstance(cubin.get("tool_version_output"), str)
        or not cubin["tool_version_output"]
        or re.search(r"(?<!\d)13\.3(?!\d)", str(cubin["tool_version_output"]))
        is None
        or cubin.get("retained_payload_format") != "elf-cubin"
        or cubin.get("caller_supplied_nvrtc_options") != list(CUDA_COMPILE_OPTIONS)
        or cubin.get("cupy_internal_options_disclosure")
        != [
            "target_architecture",
            "device_as_default_execution_space",
            "version_dependent_precompiled_header",
        ]
    ):
        raise ValueError("reader executed-binary compiler contract differs")
    cubin_sha = cubin.get("cubin_sha256")
    if (
        not isinstance(cubin_sha, str)
        or len(cubin_sha) != 64
        or any(character not in "0123456789abcdef" for character in cubin_sha)
    ):
        raise ValueError("reader cubin identity is malformed")
    parsed_all = _parse_cuobjdump_resource_usage(cubin.get("raw_resource_stdout"))
    parsed = {name: parsed_all[name] for name in DIRECT_KERNEL_NAMES}
    stored_direct = _mapping(cubin.get("direct"), label="stored cubin direct")
    if stored_direct != parsed:
        raise ValueError("reader cuobjdump reparse differs")
    stored_driver = _mapping(cubin.get("driver_direct"), label="stored driver direct")
    if stored_driver != driver:
        raise ValueError("reader driver resource copies differ")
    expected_driver_fields = {
        "local_size_bytes",
        "registers",
        "shared_size_bytes",
        "maximum_threads_per_block",
    }
    maxima: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        driver_row = _mapping(driver[name], label="driver resource row")
        cubin_row = parsed[name]
        if set(driver_row) != expected_driver_fields:
            raise ValueError("reader driver resource row field set differs")
        checked_driver = {
            field: _integer(value, label=f"driver resource {field}")
            for field, value in driver_row.items()
        }
        maxima[name] = {
            "registers": max(checked_driver["registers"], cubin_row["REG"]),
            "stack_plus_local_backing_bytes": max(
                checked_driver["local_size_bytes"],
                cubin_row["STACK"] + cubin_row["LOCAL"],
            ),
        }
    if cubin.get("effective_maxima") != maxima:
        raise ValueError("reader effective resource maxima differ")
    residency = _mapping(cubin.get("runtime_residency"), label="runtime residency")
    if set(residency) != {
        "multiprocessor_count",
        "maximum_threads_per_multiprocessor",
        "maximum_resident_threads",
        "backing_ceiling_bytes_per_thread",
        "maximum_resident_backing_bytes",
        "frozen_device_reserve_bytes",
    }:
        raise ValueError("reader runtime residency field set differs")
    multiprocessors = _integer(
        residency.get("multiprocessor_count"), label="multiprocessor count", minimum=1
    )
    threads_per = _integer(
        residency.get("maximum_threads_per_multiprocessor"),
        label="threads per multiprocessor",
        minimum=1,
    )
    resident_threads = multiprocessors * threads_per
    resident_backing = resident_threads * DIRECT_KERNEL_BACKING_LIMIT_BYTES
    if (
        residency.get("maximum_resident_threads") != resident_threads
        or residency.get("backing_ceiling_bytes_per_thread")
        != DIRECT_KERNEL_BACKING_LIMIT_BYTES
        or residency.get("maximum_resident_backing_bytes") != resident_backing
        or residency.get("frozen_device_reserve_bytes")
        != FROZEN_DEVICE_RESERVE_BYTES
    ):
        raise ValueError("reader runtime residency arithmetic differs")
    gates = {
        "register_ceiling": all(
            row["registers"] <= DIRECT_KERNEL_REGISTER_LIMIT
            for row in maxima.values()
        ),
        "local_and_stack_ceiling": all(
            row["stack_plus_local_backing_bytes"]
            <= DIRECT_KERNEL_BACKING_LIMIT_BYTES
            for row in maxima.values()
        ),
        "resident_thread_bound": resident_threads <= MAXIMUM_RESIDENT_THREAD_BOUND,
        "resident_backing_within_device_reserve": (
            resident_threads <= MAXIMUM_RESIDENT_THREAD_BOUND
            and resident_backing <= FROZEN_DEVICE_RESERVE_BYTES
        ),
    }
    if cubin.get("gates") != gates:
        raise ValueError("reader resource gate reconstruction differs")
    if cubin.get("claims") != {
        "exact_spill_load_store_count": None,
        "local_and_stack_are_not_relabeled_as_spill_counts": True,
    }:
        raise ValueError("reader spill-traffic claim differs")
    runtime = _mapping(event.get("runtime"), label="runtime identity")
    if cubin.get("cupy_version") != runtime.get("cupy_version"):
        raise ValueError("reader compiler/runtime CuPy identity differs")
    primitive = _mapping(event.get("primitive_gates"), label="primitive gates")
    if not primitive or not all(isinstance(value, bool) for value in primitive.values()):
        raise ValueError("reader primitive gate vector differs")
    order = _mapping(event.get("direct_order_controls"), label="direct order controls")
    order_gates = _mapping(order.get("gates"), label="direct order gates")
    if (
        not order_gates
        or not all(isinstance(value, bool) for value in order_gates.values())
        or order.get("all_gates_pass") is not all(order_gates.values())
    ):
        raise ValueError("reader direct-order gate vector differs")
    return all(primitive.values()) and all(order_gates.values()) and all(gates.values())


def _parse_phase(
    event: Mapping[str, object], config: Mapping[str, object]
) -> ReboundPhase:
    if event.get("schema_version") != "legal-river-work-preflight-phase-v1":
        raise ValueError("phase schema differs")
    if set(event) != {
        "schema_version",
        "ordinal",
        "population",
        "family",
        "repeat",
        "tile",
        "phase",
        "host_start_ns",
        "host_stop_ns",
        "host_ns",
        "device_ns",
        "chunks",
        "work",
    }:
        raise ValueError("phase field set differs")
    population = _integer(event.get("population"), label="phase population")
    if population not in CALIBRATION_POPULATIONS:
        raise ValueError("25-card or unknown numerical phase is forbidden")
    family = event.get("family")
    if family not in FAMILIES:
        raise ValueError("phase family differs")
    ordinal = _integer(event.get("ordinal"), label="phase ordinal")
    repeat = _integer(event.get("repeat"), label="phase repeat")
    tile = _integer(event.get("tile"), label="phase tile")
    if repeat not in (0, 1) or tile not in (0, 1, 2):
        raise ValueError("phase repeat/tile differs")
    phase = event.get("phase")
    if phase not in PHASE_ORDER:
        raise ValueError("phase name differs")
    start = _integer(event.get("host_start_ns"), label="phase start")
    stop = _integer(event.get("host_stop_ns"), label="phase stop")
    host = _integer(event.get("host_ns"), label="phase host")
    _integer(event.get("device_ns"), label="phase device")
    if stop < start or host != stop - start:
        raise ValueError("phase wall identity differs")
    chunks_value = event.get("chunks")
    if not isinstance(chunks_value, Sequence) or isinstance(chunks_value, str):
        raise ValueError("phase chunks are malformed")
    chunks = tuple(_integer(value, label="phase chunk", minimum=1) for value in chunks_value)
    key = "default" if family == FAMILIES[0] else "alternate"
    expected_chunks = tuple(config["chunk_contract"][str(population)][key])  # type: ignore[index]
    if chunks != expected_chunks:
        raise ValueError("phase chunks differ from the frozen family")
    work_value = _mapping(event.get("work"), label="phase work")
    work = {
        name: _integer(value, label=f"phase work {name}")
        for name, value in work_value.items()
    }
    unknown = set(work) - set(complete_campaign_work(population))
    if unknown:
        raise ValueError("phase contains an unknown work counter")
    misplaced = set(work) - set(_PHASE_WORK_COUNTERS.get(str(phase), ()))
    if misplaced:
        raise ValueError("phase contains a work counter from another semantic phase")
    return ReboundPhase(
        population=population,
        family=str(family),
        ordinal=ordinal,
        phase=str(phase),
        host_start_ns=start,
        host_stop_ns=stop,
        host_ns=host,
        work=work,
    )


def rebind_work_preflight_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> WorkPreflightRebinding:
    if not isinstance(raw, bytes):
        raise TypeError("work-preflight journal must be immutable bytes")
    config = _load_config()
    correction = _load_resource_correction()
    _validate_config_arithmetic(config)
    _validate_resource_correction(correction)
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=WORK_PREFLIGHT_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight journal is incomplete: {recovery.failure.reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("work-preflight journal omits header or terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("work-preflight first record is not a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("work-preflight last record is not a terminal")
    if any(record.body.kind is JournalRecordKind.TERMINAL for record in records[:-1]):
        raise ValueError("work-preflight journal has a suffix after a terminal")
    for record in records:
        if _semantic_digest(record.body.payload) != record.body.semantic_identity_sha256:
            raise ValueError("work-preflight semantic identity differs")

    header = records[0].body.payload
    if (
        header.get("schema_version") != "legal-river-work-preflight-owner-header-v1"
        or header.get("owner_protocol_sha256") != WORK_PREFLIGHT_PROTOCOL_SHA256
        or header.get("config_relative_path") != CONFIG_RELATIVE_PATH
        or header.get("correction_config_relative_path")
        != CORRECTION_CONFIG_RELATIVE_PATH
        or header.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or header.get("calibration_populations") != [10, 22]
        or header.get("projection_population_integer_only") != 25
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight header contract differs")

    observations = records[1:-1]
    phases: list[ReboundPhase] = []
    population_events: dict[int, Mapping[str, object]] = {}
    projection_event: Mapping[str, object] | None = None
    terminal_evidence: Mapping[str, object] | None = None
    provenance_seen = False
    laboratory_kinds_seen: set[str] = set()
    compiler_contract_pass: bool | None = None
    calibration_control_passes: list[bool] = []
    calibration_failure_populations: set[int] = set()
    bound_source_commit: str | None = None
    for index, record in enumerate(observations):
        if record.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("work-preflight middle record is not an observation")
        observation = record.body.payload
        if observation.get("schema_version") != (
            "legal-river-work-preflight-owner-observation-v1"
        ):
            raise ValueError("work-preflight observation schema differs")
        if set(observation) != {
            "schema_version",
            "event_index",
            "event_kind",
            "config_sha256",
            "correction_config_sha256",
            "source_commit",
            "event",
        }:
            raise ValueError("work-preflight observation field set differs")
        if observation.get("event_index") != index:
            raise ValueError("work-preflight event index differs")
        if observation.get("config_sha256") != PREREGISTERED_CONFIG_SHA256:
            raise ValueError("work-preflight observation config differs")
        if observation.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256:
            raise ValueError("work-preflight observation correction differs")
        source_commit = observation.get("source_commit")
        if (
            not isinstance(source_commit, str)
            or len(source_commit) != 40
            or any(character not in "0123456789abcdef" for character in source_commit)
        ):
            raise ValueError("work-preflight observation commit is malformed")
        if bound_source_commit is None:
            bound_source_commit = source_commit
        elif source_commit != bound_source_commit:
            raise ValueError("work-preflight observation commit changes")
        kind = observation.get("event_kind")
        event = _mapping(observation.get("event"), label="event")
        if kind == "provenance":
            if index != 0 or provenance_seen:
                raise ValueError("work-preflight provenance placement differs")
            provenance_seen = True
            if event.get("schema_version") != "legal-river-work-preflight-provenance-v1":
                raise ValueError("work-preflight provenance schema differs")
            if set(event) != {
                "schema_version",
                "config_sha256",
                "correction_config_sha256",
                "source_commit",
                "source_dirty",
                "dependency_hashes",
                "reserved_actual_result_absent",
            }:
                raise ValueError("work-preflight provenance field set differs")
            if event.get("config_sha256") != PREREGISTERED_CONFIG_SHA256:
                raise ValueError("work-preflight provenance config differs")
            if event.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256:
                raise ValueError("work-preflight provenance correction differs")
            if event.get("source_commit") != bound_source_commit:
                raise ValueError("work-preflight provenance commit differs")
            if event.get("source_dirty") is not False:
                raise ValueError("work-preflight provenance is dirty")
            hashes = _mapping(event.get("dependency_hashes"), label="dependency hashes")
            if set(hashes) != set(_DEPENDENCY_PATHS):
                raise ValueError("work-preflight dependency set differs")
            if rebind_current_sources:
                for label, path in _DEPENDENCY_PATHS.items():
                    if hashes.get(label) != canonical_lf_sha256(path):
                        raise ValueError(f"work-preflight dependency differs: {label}")
            if event.get("reserved_actual_result_absent") is not True:
                raise ValueError("reserved actual result was not absent")
        elif kind == "phase":
            phases.append(_parse_phase(event, config))
        elif kind == "population":
            if event.get("schema_version") != (
                "legal-river-work-preflight-population-evidence-v1"
            ):
                raise ValueError("population evidence schema differs")
            if set(event) != {
                "schema_version",
                "population",
                "scalar_pairs",
                "conditional_value",
                "maximum_errors",
                "reporting_digests",
                "telemetry",
                "gates",
                "all_gates_pass",
                "phase_host_ns",
                "campaign_host_ns",
                "executed_work",
            }:
                raise ValueError("population evidence field set differs")
            population = _integer(event.get("population"), label="population evidence")
            if population not in CALIBRATION_POPULATIONS or population in population_events:
                raise ValueError("population evidence identity differs")
            population_events[population] = event
        elif kind == "projection":
            if projection_event is not None:
                raise ValueError("work-preflight projection repeats")
            projection_event = event
        elif kind == "terminal_evidence":
            if terminal_evidence is not None or index != len(observations) - 1:
                raise ValueError("terminal evidence placement differs")
            terminal_evidence = event
        elif kind == "laboratory":
            if event.get("schema_version") != "legal-river-work-preflight-laboratory-v1":
                raise ValueError("laboratory event schema differs")
            lab_kind = event.get("kind")
            allowed_lab_fields = {
                "runtime_primitives_and_compiler": {
                    "schema_version",
                    "kind",
                    "runtime",
                    "primitive_gates",
                    "direct_order_controls",
                    "direct_kernel_resources",
                    "cubin_resource_usage",
                },
                "compiler_resource_failure": {
                    "schema_version",
                    "kind",
                    "runtime",
                    "stage",
                    "reason",
                    "correction_config_sha256",
                },
                "calibration_population_wall_failure": {
                    "schema_version",
                    "kind",
                    "population",
                    "family",
                    "elapsed_ns",
                    "limit_ns",
                    "reason",
                },
                "complete_ten_query_weight_control": {
                    "schema_version",
                    "kind",
                    "gates",
                },
                "complete_ten_legacy_direct_byte_identity": {
                    "schema_version",
                    "kind",
                    "control",
                },
            }
            if lab_kind not in allowed_lab_fields:
                raise ValueError("laboratory event kind differs")
            if lab_kind in laboratory_kinds_seen:
                raise ValueError("laboratory event kind repeats")
            laboratory_kinds_seen.add(str(lab_kind))
            if set(event) != allowed_lab_fields[lab_kind]:  # type: ignore[index]
                raise ValueError("laboratory event field set differs")
            if lab_kind == "runtime_primitives_and_compiler":
                compiler_contract_pass = _validate_resource_laboratory(event)
            elif lab_kind == "compiler_resource_failure":
                if (
                    event.get("stage") != "kernel_compile_and_resource_inspection"
                    or not isinstance(event.get("reason"), str)
                    or not event["reason"]
                    or event.get("correction_config_sha256")
                    != CORRECTION_CONFIG_SHA256
                    or not isinstance(event.get("runtime"), Mapping)
                ):
                    raise ValueError("compiler resource failure evidence differs")
            elif lab_kind == "complete_ten_query_weight_control":
                query_gates = _mapping(
                    event.get("gates"), label="complete-ten query-weight gates"
                )
                if not query_gates or not all(
                    isinstance(value, bool) for value in query_gates.values()
                ):
                    raise ValueError("complete-ten query-weight gate vector differs")
                calibration_control_passes.append(all(query_gates.values()))
                if not all(query_gates.values()):
                    calibration_failure_populations.add(10)
            elif lab_kind == "complete_ten_legacy_direct_byte_identity":
                legacy = _mapping(
                    event.get("control"), label="complete-ten legacy control"
                )
                legacy_gates = _mapping(
                    legacy.get("gates"), label="complete-ten legacy gates"
                )
                if (
                    not legacy_gates
                    or not all(
                        isinstance(value, bool) for value in legacy_gates.values()
                    )
                    or legacy.get("all_gates_pass")
                    is not all(legacy_gates.values())
                ):
                    raise ValueError("complete-ten legacy gate vector differs")
                calibration_control_passes.append(all(legacy_gates.values()))
                if not all(legacy_gates.values()):
                    calibration_failure_populations.add(10)
            elif lab_kind == "calibration_population_wall_failure":
                wall_population = _integer(
                    event.get("population"), label="wall-failure population"
                )
                elapsed = _integer(
                    event.get("elapsed_ns"), label="wall-failure elapsed"
                )
                limit = _integer(event.get("limit_ns"), label="wall-failure limit")
                if (
                    wall_population not in CALIBRATION_POPULATIONS
                    or event.get("family") not in FAMILIES
                    or limit != 90_000_000_000
                    or elapsed <= limit
                    or not isinstance(event.get("reason"), str)
                    or not event["reason"]
                ):
                    raise ValueError("calibration population wall evidence differs")
                calibration_failure_populations.add(wall_population)
        else:
            raise ValueError("work-preflight event kind differs")
    if observations and not provenance_seen:
        raise ValueError("work-preflight provenance is absent")

    by_group: dict[tuple[int, str], list[ReboundPhase]] = {}
    for phase in phases:
        by_group.setdefault((phase.population, phase.family), []).append(phase)
    phase_totals: dict[int, dict[str, int]] = {
        cards: {phase: 0 for phase in PHASE_ORDER}
        for cards in CALIBRATION_POPULATIONS
    }
    work_totals: dict[int, dict[str, int]] = {
        cards: {} for cards in CALIBRATION_POPULATIONS
    }
    for (cards, family), rows in by_group.items():
        if [row.ordinal for row in rows] != list(range(len(rows))):
            raise ValueError("phase ordinal sequence differs")
        if rows[0].phase != "fixture_and_resident_birth":
            raise ValueError("phase family does not start at fixture birth")
        if any(
            right.phase not in _ALLOWED_PHASE_TRANSITIONS[left.phase]
            for left, right in zip(rows, rows[1:])
        ):
            raise ValueError("phase semantic transition differs")
        if any(left.host_stop_ns != right.host_start_ns for left, right in zip(rows, rows[1:])):
            raise ValueError("phase partition has a gap or overlap")
        if sum(row.host_ns for row in rows) != rows[-1].host_stop_ns - rows[0].host_start_ns:
            raise ValueError("phase sum does not equal family wall")
        for row in rows:
            phase_totals[cards][row.phase] += row.host_ns
            for name, count in row.work.items():
                work_totals[cards][name] = work_totals[cards].get(name, 0) + count

    complete_populations = set(population_events)
    for cards in complete_populations:
        if set((cards, family) for family in FAMILIES) - set(by_group):
            raise ValueError("population evidence omits a family partition")
        if any(
            set(row.phase for row in by_group[(cards, family)]) != set(PHASE_ORDER)
            for family in FAMILIES
        ):
            raise ValueError("phase family does not cover all 16 phases")
        if any(
            by_group[(cards, family)][-1].phase != "final_release"
            for family in FAMILIES
        ):
            raise ValueError("phase family does not end at final release")
        if work_totals[cards] != complete_campaign_work(cards):
            raise ValueError("executed work ledger differs")
        event = population_events[cards]
        if event.get("phase_host_ns") != phase_totals[cards]:
            raise ValueError("stored phase aggregation differs")
        if event.get("campaign_host_ns") != sum(phase_totals[cards].values()):
            raise ValueError("stored campaign wall differs")
        if event.get("executed_work") != work_totals[cards]:
            raise ValueError("stored executed work differs")
        gates = _mapping(event.get("gates"), label="population gates")
        if not all(isinstance(value, bool) for value in gates.values()):
            raise ValueError("population gate is not boolean")
        if event.get("all_gates_pass") is not all(gates.values()):
            raise ValueError("stored population pass bit differs")

    reconstructed_projection: Mapping[str, object] | None = None
    if projection_event is not None:
        if complete_populations != set(CALIBRATION_POPULATIONS):
            raise ValueError("projection exists without both populations")
        if not all(population_events[cards].get("all_gates_pass") is True
                   for cards in CALIBRATION_POPULATIONS):
            raise ValueError("projection exists after a population rejection")
        reconstructed_projection = reconstruct_projection(phase_totals)
        if projection_event != reconstructed_projection:
            raise ValueError("stored projection differs from raw phase rows")

    terminal_record = records[-1].body.payload
    if terminal_record.get("schema_version") != (
        "legal-river-work-preflight-owner-terminal-v1"
    ):
        raise ValueError("journal terminal schema differs")
    if set(terminal_record) != {
        "schema_version",
        "terminal",
        "reason",
        "passed",
        "event_count",
        "last_event_semantic_identity_sha256",
        "claims",
    }:
        raise ValueError("journal terminal field set differs")
    if not isinstance(terminal_record.get("reason"), str) or not terminal_record["reason"]:
        raise ValueError("journal terminal reason differs")
    terminal = terminal_record.get("terminal")
    allowed = {
        "completed_capacity_pass",
        "completed_capacity_rejection",
        "calibration_scientific_rejection",
        "compiler_or_primitive_rejection",
        "laboratory_wall_rejection",
        "infrastructure_failure",
    }
    if terminal not in allowed:
        raise ValueError("journal terminal class differs")
    if (
        terminal == "laboratory_wall_rejection"
        and "laboratory_wall_crossed" not in terminal_record["reason"]
    ):
        raise ValueError("laboratory wall terminal reason differs")
    if terminal_record.get("claims") != CLAIMS:
        raise ValueError("journal terminal claims differ")
    if terminal_record.get("event_count") != len(observations):
        raise ValueError("journal terminal event count differs")
    expected_last = observations[-1].body.semantic_identity_sha256 if observations else None
    if terminal_record.get("last_event_semantic_identity_sha256") != expected_last:
        raise ValueError("journal terminal last-event identity differs")
    passed = terminal == "completed_capacity_pass"
    if terminal_record.get("passed") is not passed:
        raise ValueError("stored journal pass bit differs")
    if terminal_evidence is not None:
        if terminal_evidence.get("schema_version") != (
            "legal-river-work-preflight-terminal-evidence-v1"
        ):
            raise ValueError("terminal evidence schema differs")
        if set(terminal_evidence) != {
            "schema_version",
            "terminal",
            "failed_population",
            "passed",
            "projection",
        }:
            raise ValueError("terminal evidence field set differs")
        if terminal_evidence.get("terminal") != terminal:
            raise ValueError("terminal evidence and journal terminal disagree")
        if terminal_evidence.get("passed") is not passed:
            raise ValueError("terminal evidence pass bit differs")
        if terminal in {"completed_capacity_pass", "completed_capacity_rejection"}:
            if terminal_evidence.get("failed_population") is not None:
                raise ValueError("completed terminal names a failed population")
            if reconstructed_projection is None:
                raise ValueError("completed terminal omits projection")
            if terminal_evidence.get("projection") != reconstructed_projection:
                raise ValueError("terminal projection differs")
        elif terminal == "compiler_or_primitive_rejection":
            if (
                terminal_evidence.get("failed_population") is not None
                or terminal_evidence.get("projection") is not None
                or projection_event is not None
            ):
                raise ValueError("compiler rejection boundary differs")
        elif terminal == "calibration_scientific_rejection":
            if (
                terminal_evidence.get("failed_population")
                not in CALIBRATION_POPULATIONS
                or terminal_evidence.get("projection") is not None
                or projection_event is not None
            ):
                raise ValueError("calibration rejection boundary differs")
    elif terminal not in {"laboratory_wall_rejection", "infrastructure_failure"}:
        raise ValueError("scientific terminal omits terminal evidence")
    if terminal not in {"laboratory_wall_rejection", "infrastructure_failure"} and not (
        laboratory_kinds_seen
        & {"runtime_primitives_and_compiler", "compiler_resource_failure"}
    ):
        raise ValueError("scientific terminal omits compiler resource evidence")
    if (
        "compiler_resource_failure" in laboratory_kinds_seen
        and terminal != "compiler_or_primitive_rejection"
    ):
        raise ValueError("compiler resource failure has the wrong terminal")
    if terminal == "compiler_or_primitive_rejection":
        if (
            "compiler_resource_failure" not in laboratory_kinds_seen
            and compiler_contract_pass is not False
        ):
            raise ValueError("compiler rejection disagrees with compiler gates")
    elif terminal not in {"laboratory_wall_rejection", "infrastructure_failure"}:
        if compiler_contract_pass is not True:
            raise ValueError("scientific terminal follows a false compiler gate")
    calibration_failure_populations.update(
        cards
        for cards, event in population_events.items()
        if event.get("all_gates_pass") is False
    )
    if terminal in {"completed_capacity_pass", "completed_capacity_rejection"}:
        if (
            not {
                "complete_ten_query_weight_control",
                "complete_ten_legacy_direct_byte_identity",
            }.issubset(laboratory_kinds_seen)
            or not calibration_control_passes
            or not all(calibration_control_passes)
        ):
            raise ValueError("completed terminal omits a passing calibration control")
    elif terminal == "calibration_scientific_rejection":
        assert terminal_evidence is not None
        if terminal_evidence.get("failed_population") not in calibration_failure_populations:
            raise ValueError("calibration rejection has no false gate witness")
    return WorkPreflightRebinding(
        terminal=str(terminal),
        passed=passed,
        event_count=len(observations),
        phases=tuple(phases),
        projection=reconstructed_projection,
        journal_byte_count=len(raw),
    )


def rebind_work_preflight_file(
    path: Path = _RESULT,
) -> WorkPreflightRebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=WORK_PREFLIGHT_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"work-preflight result is incomplete: {recovery.failure.reason}")
    return rebind_work_preflight_journal(path.read_bytes())


__all__ = [
    "CALIBRATION_POPULATIONS",
    "PHASE_ORDER",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "ReboundPhase",
    "WORK_PREFLIGHT_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_PROTOCOL_SHA256",
    "WorkPreflightRebinding",
    "complete_campaign_work",
    "geometry",
    "phase_ratio",
    "phase_constituents",
    "rebind_work_preflight_file",
    "rebind_work_preflight_journal",
    "reconstruct_projection",
]
