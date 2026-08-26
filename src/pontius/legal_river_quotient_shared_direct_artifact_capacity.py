"""GPU-free ADR-0430 shared-direct artifact capacity assessor.

Importing this module reads no files, imports no device stack, starts no
process, and computes no projection.  Population 25 appears only in exact
integer geometry and work ratios.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import comb, gcd
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-shared-direct-artifact-capacity-v1.json"
)
INPUT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v3.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_shared_direct_artifact_capacity_v1.json"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
CONFIG_SHA256 = (
    "720049432e3e8d85680a5781769f149d249920e3519b057d6df8ef0feedbceac"
)
INPUT_SHA256 = (
    "4e19a31f45c0f79db40db8df8e2b76806d3f5c39fc3a9e191b07043ddb711f0e"
)
INPUT_BYTES = 4_340_598
INPUT_SOURCE_COMMIT = "00d29e048d88ff4ece325b2a00866ddbd084617c"
INPUT_PHASE_ROWS = 3_028
CALIBRATION_POPULATIONS = (10, 22)
TARGET_POPULATION = 25
SAFETY_NUMERATOR = 5
SAFETY_DENOMINATOR = 4
COMPONENT_GUARD_NS = 1_000_000
WALL_LIMIT_NS = 180_000_000_000

FAMILIES = (
    "default_chunks_forward_tile_order",
    "alternate_chunks_reverse_tile_order",
)
PHASE_ORDER = (
    "fixture_and_resident_birth",
    "forward_source_and_offset",
    "shared_direct_fold_and_query",
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
OUTSIDE_COMPONENT = "population_envelope_outside_phase_partition"
COMPONENT_ORDER = PHASE_ORDER + (OUTSIDE_COMPONENT,)

_PARENT_PHASE_ORDER = (
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
_UNCHANGED_PHASES = tuple(
    phase for phase in PHASE_ORDER if phase != "shared_direct_fold_and_query"
)
_FROZEN_CHUNKS = {
    10: ((17, 3, 11), (13, 2, 7)),
    22: ((32_768, 4_096, 32_768), (16_381, 2_047, 16_381)),
    25: ((65_536, 10_922, 32_768), (32_767, 4_093, 16_381)),
}
_EXPECTED_CHUNKS = {
    10: {FAMILIES[0]: (17, 3, 11), FAMILIES[1]: (13, 2, 7)},
    22: {
        FAMILIES[0]: (32_768, 4_096, 32_768),
        FAMILIES[1]: (16_381, 2_047, 16_381),
    },
}
_ALLOWED_TRANSITIONS = {
    "fixture_and_resident_birth": ("forward_source_and_offset",),
    "forward_source_and_offset": ("shared_direct_fold_and_query",),
    "shared_direct_fold_and_query": ("forward_recurrence",),
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
_PHASE_COUNTERS = {
    "forward_source_and_offset": {
        "source_pairing_visits",
        "source_weight_pair_times_float64",
    },
    "shared_direct_fold_and_query": {
        "shared_direct_source_unranks",
        "shared_direct_compatible_coefficient_pair_adds",
        "shared_direct_boundary_pair_copies",
        "shared_direct_final_feature_pair_products",
    },
    "forward_recurrence": {
        "forward_recurrence_pair_child_adds",
        "forward_pair_divides",
    },
    "forward_signed_targets": {"forward_signed_subset_pair_terms"},
    "forward_fold_and_global_tree": {
        "forward_fold_pair_times_pair",
        "forward_tree_contributions",
    },
    "adjoint_covector_and_labels": {
        "adjoint_covector_pair_times_float64",
        "adjoint_label_pair_adds",
    },
    "adjoint_recurrence_and_signed_sources": {
        "adjoint_recurrence_pair_child_adds",
        "adjoint_pair_divides",
        "adjoint_signed_subset_pair_terms",
    },
    "direct_adjoint": {
        "direct_adjoint_source_unranks",
        "direct_adjoint_query_record_visits",
        "direct_adjoint_compatible_query_weight_builds",
        "direct_adjoint_compatible_boundary_pair_adds",
    },
    "adjoint_source_contract_and_global_tree": {
        "adjoint_source_pairing_visits",
        "adjoint_source_weight_pair_times_float64",
        "adjoint_contract_pair_times_pair",
        "adjoint_tree_contributions",
    },
}
_PARENT_PHASE_COUNTERS = {
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

RESULT_CLAIM_KEYS = (
    "complete_25_numerical_value",
    "actual_45_card_value",
    "resolver_iteration_result",
    "action_result",
    "action_clock_result",
    "decision_quality_result",
    "exact_integer_result",
    "truncation_authorized",
    "blueprint_result",
    "poker_strength_result",
)


@dataclass(frozen=True, slots=True)
class Geometry:
    available_cards: int
    source_occupancies: int
    source_recurrence_rows: int
    query_occupancies: int
    labeled_query_records: int
    adjoint_recurrence_rows: int
    compatible_sources_per_query_occupancy: int
    compatible_labeled_query_records_per_source: int


@dataclass(frozen=True, slots=True)
class RawPhase:
    population: int
    family: str
    ordinal: int
    phase: str
    host_start_ns: int
    host_stop_ns: int
    host_ns: int
    work: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class EndpointObservation:
    population: int
    phase_host_ns: tuple[tuple[str, int], ...]
    campaign_host_ns: int
    population_elapsed_host_ns: int
    outside_phase_host_ns: int
    executed_work: tuple[tuple[str, int], ...]

    def phase_map(self) -> dict[str, int]:
        return dict(self.phase_host_ns)


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer at least {minimum}")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"capacity provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_config(
    path: Path = ROOT / CONFIG_RELATIVE_PATH,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("capacity config path must be a Path")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("capacity config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("capacity config differs from ADR-0430")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("capacity config must be an object")
    return value


def population_geometry(available_cards: int) -> Geometry:
    if isinstance(available_cards, bool) or available_cards not in (10, 22, 25):
        raise ValueError("capacity geometry is restricted to 10, 22, and 25")
    return Geometry(
        available_cards=available_cards,
        source_occupancies=comb(available_cards, 6),
        source_recurrence_rows=sum(comb(available_cards, k) for k in range(7)),
        query_occupancies=comb(available_cards, 4),
        labeled_query_records=6 * comb(available_cards, 4),
        adjoint_recurrence_rows=sum(comb(available_cards, k) for k in range(5)),
        compatible_sources_per_query_occupancy=comb(available_cards - 4, 6),
        compatible_labeled_query_records_per_source=(
            6 * comb(available_cards - 6, 4)
        ),
    )


def complete_campaign_work(available_cards: int) -> dict[str, int]:
    geometry = population_geometry(available_cards)
    executions = 4
    width = 176
    tiles = 3
    selected = 16
    boundary = 8
    source = geometry.source_occupancies
    query = geometry.query_occupancies
    records = geometry.labeled_query_records
    compatible_sources = geometry.compatible_sources_per_query_occupancy
    compatible_records = geometry.compatible_labeled_query_records_per_source
    work = {
        "source_pairing_visits": source * 90 * executions * tiles,
        "source_weight_pair_times_float64": source * 90 * 6 * executions * tiles,
        "forward_recurrence_pair_child_adds": executions
        * width
        * sum(comb(available_cards, k) * (available_cards - k) for k in range(6)),
        "forward_pair_divides": executions
        * width
        * sum(comb(available_cards, k) for k in range(6)),
        "forward_signed_subset_pair_terms": executions * records * width * 16,
        "forward_fold_pair_times_pair": executions * records * width,
        "forward_tree_contributions": executions * records * 4,
        "adjoint_covector_pair_times_float64": executions * records * width,
        "adjoint_label_pair_adds": executions * query * 6 * width,
        "adjoint_recurrence_pair_child_adds": executions
        * width
        * sum(comb(available_cards, k) * (available_cards - k) for k in range(4)),
        "adjoint_pair_divides": executions
        * width
        * sum(comb(available_cards, k) for k in range(4)),
        "adjoint_signed_subset_pair_terms": executions
        * source
        * width
        * sum(comb(6, k) for k in range(5)),
        "adjoint_source_pairing_visits": source * 90 * executions * tiles,
        "adjoint_source_weight_pair_times_float64": (
            source * 90 * 6 * executions * tiles
        ),
        "adjoint_contract_pair_times_pair": executions * source * width,
        "adjoint_tree_contributions": executions * source * tiles,
        "direct_query_source_unranks": selected * source * tiles * executions,
        "direct_query_compatible_boundary_pair_adds": (
            selected * compatible_sources * boundary * executions
        ),
        "direct_fold_source_unranks": selected * source * tiles * executions,
        "direct_fold_compatible_coefficient_pair_adds": (
            selected * compatible_sources * width * executions
        ),
        "direct_fold_final_feature_pair_products": selected * width * executions,
        "shared_direct_source_unranks": selected * source * tiles * executions,
        "shared_direct_compatible_coefficient_pair_adds": (
            selected * compatible_sources * width * executions
        ),
        "shared_direct_final_feature_pair_products": selected * width * executions,
        "shared_direct_boundary_pair_copies": 512,
        "direct_adjoint_source_unranks": selected * tiles * executions,
        "direct_adjoint_query_record_visits": (
            selected * records * tiles * executions
        ),
        "direct_adjoint_compatible_query_weight_builds": (
            selected * compatible_records * tiles * executions
        ),
        "direct_adjoint_compatible_boundary_pair_adds": (
            selected * compatible_records * boundary * executions
        ),
    }
    return work


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


def parent_phase_projection_constituents(
    phase: str, calibration_population: int
) -> tuple[tuple[str, int, int], ...]:
    """Independently reproduce ADR-0394's frozen constituent derivation."""

    if phase not in _PARENT_PHASE_ORDER:
        raise ValueError("unknown parent projection phase")
    if calibration_population not in CALIBRATION_POPULATIONS:
        raise ValueError("projection endpoint must be 10 or 22")
    target = population_geometry(TARGET_POPULATION)
    endpoint = population_geometry(calibration_population)
    target_work = complete_campaign_work(TARGET_POPULATION)
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
    for counter in _PARENT_PHASE_COUNTERS.get(phase, ()):
        rows.append((counter, target_work[counter], endpoint_work[counter]))
    live_fields = {
        "fixture_and_resident_birth": (
            "source_occupancies",
            "source_recurrence_rows",
            "labeled_query_records",
            "adjoint_recurrence_rows",
        ),
        "forward_source_and_offset": (
            "source_occupancies",
            "source_recurrence_rows",
        ),
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
    target_chunks = _chunk_counts(TARGET_POPULATION)
    endpoint_chunks = _chunk_counts(calibration_population)
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


def _maximum_ratio(
    rows: Sequence[tuple[str, int, int]],
) -> tuple[int, int]:
    if not rows:
        raise ValueError("projection constituent set is empty")
    _, numerator, denominator = rows[0]
    if denominator <= 0 or numerator < 0:
        raise ValueError("projection constituent ratio is invalid")
    for _, candidate_numerator, candidate_denominator in rows[1:]:
        if candidate_denominator <= 0 or candidate_numerator < 0:
            raise ValueError("projection constituent ratio is invalid")
        if candidate_numerator * denominator > numerator * candidate_denominator:
            numerator, denominator = candidate_numerator, candidate_denominator
    return numerator, denominator


def shared_component_constituents(
    calibration_population: int,
) -> tuple[tuple[str, int, int], ...]:
    if calibration_population not in CALIBRATION_POPULATIONS:
        raise ValueError("projection endpoint must be 10 or 22")
    target = population_geometry(TARGET_POPULATION)
    endpoint = population_geometry(calibration_population)
    target_work = complete_campaign_work(TARGET_POPULATION)
    endpoint_work = complete_campaign_work(calibration_population)
    names = (
        "shared_direct_source_unranks",
        "shared_direct_compatible_coefficient_pair_adds",
        "shared_direct_final_feature_pair_products",
        "shared_direct_boundary_pair_copies",
    )
    rows = [
        (
            "compatible_sources_per_query_occupancy",
            target.compatible_sources_per_query_occupancy,
            endpoint.compatible_sources_per_query_occupancy,
        )
    ]
    rows.extend(
        (name, target_work[name], endpoint_work[name]) for name in names
    )
    return tuple(rows)


def component_projection_ratio(
    component: str, calibration_population: int
) -> tuple[int, int]:
    if component == OUTSIDE_COMPONENT:
        if calibration_population not in CALIBRATION_POPULATIONS:
            raise ValueError("projection endpoint must be 10 or 22")
        return 1, 1
    if component == "shared_direct_fold_and_query":
        return _maximum_ratio(shared_component_constituents(calibration_population))
    if component not in _UNCHANGED_PHASES:
        raise ValueError("unknown projection component")
    return _maximum_ratio(
        parent_phase_projection_constituents(component, calibration_population)
    )


def verify_preregistered_contract(
    config: Mapping[str, object] | None = None,
    *,
    verify_parent_files: bool = True,
) -> None:
    frozen = load_preregistered_config() if config is None else config
    if frozen.get("schema_version") != (
        "legal-river-quotient-shared-direct-artifact-capacity-v1"
    ):
        raise ValueError("capacity config schema differs")
    retained = _mapping(frozen.get("retained_v3_contract"), label="retained V3")
    if (
        retained.get("artifact_relative_path") != INPUT_RELATIVE_PATH
        or retained.get("artifact_raw_sha256") != INPUT_SHA256
        or retained.get("artifact_bytes") != INPUT_BYTES
        or retained.get("source_commit") != INPUT_SOURCE_COMMIT
        or retained.get("terminal") != "completed_validation_pass"
        or retained.get("populations") != [10, 22]
        or retained.get("phase_rows") != INPUT_PHASE_ROWS
        or retained.get("v3_identity_permanently_consumed") is not True
    ):
        raise ValueError("capacity retained V3 identity differs")
    prospective = _mapping(
        frozen.get("prospective_identity"), label="prospective identity"
    )
    expected_prospective = {
        "assessor_relative_path": (
            "src/pontius/legal_river_quotient_shared_direct_artifact_capacity.py"
        ),
        "runner_relative_path": (
            "src/pontius/"
            "legal_river_quotient_shared_direct_artifact_capacity_runner.py"
        ),
        "reader_relative_path": (
            "src/pontius/"
            "legal_river_quotient_shared_direct_artifact_capacity_result.py"
        ),
        "controls_relative_path": (
            "tests/test_legal_river_quotient_shared_direct_artifact_capacity.py"
        ),
        "result_relative_path": RESULT_RELATIVE_PATH,
        "result_open_mode": "exclusive_xb",
        "all_source_control_and_result_paths_absent_at_preregistration": True,
    }
    if prospective != expected_prospective:
        raise ValueError("capacity prospective identity differs")
    if tuple(frozen.get("ordered_components", ())) != COMPONENT_ORDER:
        raise ValueError("capacity component order differs")
    ratios = _mapping(
        frozen.get("component_projection_ratios"), label="projection ratios"
    )
    for component in COMPONENT_ORDER:
        row = _mapping(ratios.get(component), label=f"ratio {component}")
        for population in CALIBRATION_POPULATIONS:
            if row.get(f"25_over_{population}") != list(
                component_projection_ratio(component, population)
            ):
                raise ValueError(
                    f"capacity projection ratio differs: {component}/{population}"
                )
    if (
        ratios.get("ratio_format")
        != ["target_work_numerator", "calibration_work_denominator"]
        or ratios.get("ratios_are_frozen_before_assessor_source_or_projection")
        is not True
        or ratios.get(
            "reader_must_rederive_every_device_component_ratio_"
            "from_geometry_work_chunks_and_live_shapes"
        )
        is not True
        or ratios.get("reader_rejects_any_device_ratio_below_any_constituent_ratio")
        is not True
    ):
        raise ValueError("capacity ratio contract differs")
    parent = _mapping(
        frozen.get("frozen_parent_projection_contract"), label="parent contract"
    )
    if (
        parent.get("retain_safety_multiplier_fraction") != [5, 4]
        or parent.get("retain_per_component_absolute_guard_ns")
        != COMPONENT_GUARD_NS
        or parent.get("retain_target_population_wall_limit_ns") != WALL_LIMIT_NS
        or parent.get("retain_maximum_over_10_and_22_endpoints") is not True
        or parent.get("retain_exact_constituent_work_ratio_rule") is not True
    ):
        raise ValueError("capacity parent arithmetic differs")
    projection = _mapping(
        frozen.get("projection_contract"), label="projection contract"
    )
    if (
        projection.get("target_population_wall_limit_ns") != WALL_LIMIT_NS
        or projection.get("projected_host_ns_is_sum_of_all_16_component_uppers")
        is not True
        or projection.get(
            "passed_if_and_only_if_projected_host_ns_is_at_or_below_limit"
        )
        is not True
        or projection.get("stored_pass_bit_is_not_authority") is not True
        or projection.get(
            "report_22_endpoint_only_counterfactual_separately_without_gate_authority"
        )
        is not True
    ):
        raise ValueError("capacity projection contract differs")
    outside = _mapping(
        frozen.get("outside_phase_contract"), label="outside-phase contract"
    )
    if (
        outside.get("component_value_per_endpoint")
        != "population_elapsed_host_ns_minus_campaign_host_ns"
        or outside.get("difference_must_be_nonnegative") is not True
        or outside.get("ratio_is_exactly_one_to_one_for_both_endpoints") is not True
        or outside.get("larger_endpoint_gap_still_decides_before_guard") is not True
        or outside.get(
            "component_is_not_hidden_inside_or_subtracted_from_any_device_phase"
        )
        is not True
    ):
        raise ValueError("capacity outside-phase contract differs")
    claims = _mapping(frozen.get("claims"), label="preregistered claims")
    if any(value is not None and value is not False for value in claims.values()):
        raise ValueError("capacity preregistered claim is open")
    if verify_parent_files:
        if canonical_lf_sha256(
            ROOT / str(parent.get("parent_source_relative_path"))
        ) != parent.get("parent_source_canonical_lf_sha256"):
            raise ValueError("capacity parent source differs")
        if canonical_lf_sha256(
            ROOT / str(parent.get("parent_config_relative_path"))
        ) != parent.get("parent_config_canonical_lf_sha256"):
            raise ValueError("capacity parent config differs")


def _parse_raw_phase(event: Mapping[str, object]) -> RawPhase:
    expected_fields = {
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
    }
    if set(event) != expected_fields or event.get("schema_version") != (
        "legal-river-shared-direct-phase-v1"
    ):
        raise ValueError("capacity raw phase schema differs")
    population = _integer(event.get("population"), label="phase population")
    family = event.get("family")
    ordinal = _integer(event.get("ordinal"), label="phase ordinal")
    repeat = _integer(event.get("repeat"), label="phase repeat")
    tile = _integer(event.get("tile"), label="phase tile")
    phase = event.get("phase")
    start = _integer(event.get("host_start_ns"), label="phase start")
    stop = _integer(event.get("host_stop_ns"), label="phase stop")
    elapsed = _integer(event.get("host_ns"), label="phase host")
    _integer(event.get("device_ns"), label="phase device")
    chunks = event.get("chunks")
    if (
        population not in CALIBRATION_POPULATIONS
        or not isinstance(family, str)
        or family not in FAMILIES
        or not isinstance(phase, str)
        or phase not in PHASE_ORDER
        or repeat not in (0, 1)
        or tile not in (0, 1, 2)
        or chunks != list(_EXPECTED_CHUNKS[population][family])
        or stop < start
        or elapsed != stop - start
    ):
        raise ValueError("capacity raw phase identity differs")
    work = _mapping(event.get("work"), label="phase work")
    if not set(work).issubset(_PHASE_COUNTERS.get(phase, set())):
        raise ValueError("capacity raw phase work is misplaced")
    rebound_work = tuple(
        sorted(
            (
                str(name),
                _integer(value, label=f"phase work {name}"),
            )
            for name, value in work.items()
        )
    )
    return RawPhase(
        population=population,
        family=family,
        ordinal=ordinal,
        phase=phase,
        host_start_ns=start,
        host_stop_ns=stop,
        host_ns=elapsed,
        work=rebound_work,
    )


def _validate_phase_group(rows: Sequence[RawPhase]) -> None:
    if not rows or [row.ordinal for row in rows] != list(range(len(rows))):
        raise ValueError("capacity raw phase ordinals differ")
    if rows[0].phase != PHASE_ORDER[0] or rows[-1].phase != PHASE_ORDER[-1]:
        raise ValueError("capacity raw phase endpoints differ")
    if {row.phase for row in rows} != set(PHASE_ORDER):
        raise ValueError("capacity raw phase coverage differs")
    for left, right in zip(rows, rows[1:]):
        if (
            left.population != right.population
            or left.family != right.family
            or left.host_stop_ns != right.host_start_ns
            or right.phase not in _ALLOWED_TRANSITIONS[left.phase]
        ):
            raise ValueError("capacity raw phase partition differs")
    if sum(row.host_ns for row in rows) != rows[-1].host_stop_ns - rows[0].host_start_ns:
        raise ValueError("capacity raw phase sum differs")


def _endpoint_from_raw(
    event: Mapping[str, object], rows: Sequence[RawPhase]
) -> EndpointObservation:
    expected_fields = {
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
        "population_elapsed_host_ns",
        "executed_work",
        "expected_work",
        "launch_counts",
    }
    if set(event) != expected_fields or event.get("schema_version") != (
        "legal-river-work-preflight-population-evidence-v1"
    ):
        raise ValueError("capacity raw population schema differs")
    population = _integer(event.get("population"), label="population")
    if population not in CALIBRATION_POPULATIONS or any(
        row.population != population for row in rows
    ):
        raise ValueError("capacity raw population identity differs")
    groups = {
        family: [row for row in rows if row.family == family]
        for family in FAMILIES
    }
    for family in FAMILIES:
        _validate_phase_group(groups[family])
    if [row.family for row in rows] != [
        family for family in FAMILIES for _ in groups[family]
    ]:
        raise ValueError("capacity raw family order differs")
    if groups[FAMILIES[0]][-1].host_stop_ns > groups[FAMILIES[1]][0].host_start_ns:
        raise ValueError("capacity raw family intervals overlap")
    totals = {phase: 0 for phase in PHASE_ORDER}
    work: dict[str, int] = {}
    for row in rows:
        totals[row.phase] += row.host_ns
        for name, count in row.work:
            work[name] = work.get(name, 0) + count
    expected_work = complete_campaign_work(population)
    # The raw shared owner has only the shared counters, not the retired direct pair.
    expected_work = {
        name: count
        for name, count in expected_work.items()
        if not name.startswith("direct_query_") and not name.startswith("direct_fold_")
    }
    stored_work = _mapping(event.get("executed_work"), label="executed work")
    stored_expected = _mapping(event.get("expected_work"), label="expected work")
    stored_phases = _mapping(event.get("phase_host_ns"), label="phase totals")
    campaign = _integer(event.get("campaign_host_ns"), label="campaign host")
    elapsed = _integer(
        event.get("population_elapsed_host_ns"), label="population elapsed"
    )
    if (
        work != expected_work
        or stored_work != expected_work
        or stored_expected != expected_work
        or stored_phases != totals
        or campaign != sum(totals.values())
        or elapsed < campaign
    ):
        raise ValueError("capacity raw population reconstruction differs")
    return EndpointObservation(
        population=population,
        phase_host_ns=tuple((phase, totals[phase]) for phase in PHASE_ORDER),
        campaign_host_ns=campaign,
        population_elapsed_host_ns=elapsed,
        outside_phase_host_ns=elapsed - campaign,
        executed_work=tuple(sorted(work.items())),
    )


def extract_bound_endpoints(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> tuple[EndpointObservation, EndpointObservation]:
    """Completely rebind V3, then independently reconstruct its timing rows."""

    if not isinstance(raw, bytes):
        raise TypeError("capacity input must be bytes")
    if len(raw) != INPUT_BYTES or sha256(raw).hexdigest() != INPUT_SHA256:
        raise ValueError("capacity input artifact identity differs")
    # Lazy imports preserve the import-only boundary.
    from .durable_evidence_journal import recover_journal_bytes
    from .legal_river_quotient_cuda_shared_direct_device_v3_result import (
        CAMPAIGN_SHA256,
        PROTOCOL_SHA256,
        rebind_shared_direct_device_v3_journal,
    )

    rebound = rebind_shared_direct_device_v3_journal(
        raw, rebind_current_sources=rebind_current_sources
    )
    if (
        rebound.terminal != "completed_validation_pass"
        or rebound.passed is not True
        or rebound.source_commit != INPUT_SOURCE_COMMIT
        or rebound.populations != CALIBRATION_POPULATIONS
        or rebound.phase_count != INPUT_PHASE_ROWS
        or rebound.complete_ten_control_passed is not True
    ):
        raise ValueError("capacity complete V3 rebinding differs")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(f"capacity raw journal recovery failed: {recovery.failure.reason}")
    observations = [record.body.payload for record in recovery.records[1:-1]]
    wrappers: list[tuple[str, Mapping[str, object]]] = []
    for observation in observations:
        wrapper = _mapping(observation, label="observation wrapper")
        if set(wrapper) != {"schema_version", "kind", "event", "config_sha256"}:
            raise ValueError("capacity observation wrapper fields differ")
        kind = wrapper.get("kind")
        if not isinstance(kind, str):
            raise ValueError("capacity observation kind differs")
        wrappers.append((kind, _mapping(wrapper.get("event"), label="observation event")))
    raw_phases = [_parse_raw_phase(event) for kind, event in wrappers if kind == "phase"]
    population_events = [event for kind, event in wrappers if kind == "population"]
    if len(raw_phases) != INPUT_PHASE_ROWS or len(population_events) != 2:
        raise ValueError("capacity raw population or phase cardinality differs")
    endpoints: list[EndpointObservation] = []
    for population, event in zip(CALIBRATION_POPULATIONS, population_events, strict=True):
        if event.get("population") != population:
            raise ValueError("capacity raw population order differs")
        rows = [row for row in raw_phases if row.population == population]
        endpoints.append(_endpoint_from_raw(event, rows))
    if sum(len([row for row in raw_phases if row.population == p]) for p in CALIBRATION_POPULATIONS) != len(raw_phases):
        raise ValueError("capacity raw phase population coverage differs")
    return endpoints[0], endpoints[1]


def endpoint_observation(
    population: int,
    phase_host_ns: Mapping[str, int],
    *,
    campaign_host_ns: int | None = None,
    population_elapsed_host_ns: int | None = None,
    executed_work: Mapping[str, int] | None = None,
) -> EndpointObservation:
    """Build a typed endpoint for synthetic controls without reading artifacts."""

    if population not in CALIBRATION_POPULATIONS or set(phase_host_ns) != set(PHASE_ORDER):
        raise ValueError("synthetic endpoint identity differs")
    rows = tuple(
        (phase, _integer(phase_host_ns[phase], label=f"synthetic phase {phase}"))
        for phase in PHASE_ORDER
    )
    derived_campaign = sum(value for _, value in rows)
    campaign = derived_campaign if campaign_host_ns is None else _integer(
        campaign_host_ns, label="synthetic campaign"
    )
    elapsed = campaign if population_elapsed_host_ns is None else _integer(
        population_elapsed_host_ns, label="synthetic population elapsed"
    )
    if campaign != derived_campaign or elapsed < campaign:
        raise ValueError("synthetic endpoint phase envelope differs")
    work = () if executed_work is None else tuple(
        sorted(
            (str(name), _integer(value, label=f"synthetic work {name}"))
            for name, value in executed_work.items()
        )
    )
    return EndpointObservation(
        population=population,
        phase_host_ns=rows,
        campaign_host_ns=campaign,
        population_elapsed_host_ns=elapsed,
        outside_phase_host_ns=elapsed - campaign,
        executed_work=work,
    )


def ceil_ratio(value: int, numerator: int, denominator: int) -> int:
    values = (value, numerator, denominator)
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in values) or denominator == 0:
        raise ValueError("capacity ratio values must be nonnegative integers")
    return (value * numerator + denominator - 1) // denominator


def _fraction_pair(numerator: int, denominator: int) -> list[int]:
    if denominator <= 0 or numerator < 0:
        raise ValueError("capacity reporting fraction differs")
    divisor = gcd(numerator, denominator)
    return [numerator // divisor, denominator // divisor]


def capacity_passes(projected_host_ns: int) -> bool:
    """Return the frozen inclusive integer wall classification."""

    return (
        _integer(projected_host_ns, label="projected host")
        <= WALL_LIMIT_NS
    )


def project_capacity(
    endpoints: Sequence[EndpointObservation],
    config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Apply the frozen exact projection to two already-bound endpoints."""

    frozen = load_preregistered_config() if config is None else config
    verify_preregistered_contract(frozen, verify_parent_files=False)
    if len(endpoints) != 2 or tuple(endpoint.population for endpoint in endpoints) != (
        CALIBRATION_POPULATIONS
    ):
        raise ValueError("capacity projection requires ordered 10 and 22 endpoints")
    endpoint_maps: dict[int, dict[str, int]] = {}
    for endpoint in endpoints:
        phase_map = endpoint.phase_map()
        if (
            tuple(phase_map) != PHASE_ORDER
            or endpoint.campaign_host_ns != sum(phase_map.values())
            or endpoint.population_elapsed_host_ns < endpoint.campaign_host_ns
            or endpoint.outside_phase_host_ns
            != endpoint.population_elapsed_host_ns - endpoint.campaign_host_ns
        ):
            raise ValueError("capacity endpoint envelope differs")
        endpoint_maps[endpoint.population] = phase_map
    rows: list[dict[str, object]] = []
    counterfactual_total = 0
    for component in COMPONENT_ORDER:
        observed = {
            endpoint.population: (
                endpoint.outside_phase_host_ns
                if component == OUTSIDE_COMPONENT
                else endpoint_maps[endpoint.population][component]
            )
            for endpoint in endpoints
        }
        ratios = {
            population: component_projection_ratio(component, population)
            for population in CALIBRATION_POPULATIONS
        }
        candidates = {
            population: ceil_ratio(observed[population], *ratios[population])
            for population in CALIBRATION_POPULATIONS
        }
        maximum = max(candidates.values())
        deciding = (
            "tie"
            if candidates[10] == candidates[22]
            else ("10" if candidates[10] > candidates[22] else "22")
        )
        upper = ceil_ratio(maximum, SAFETY_NUMERATOR, SAFETY_DENOMINATOR) + (
            COMPONENT_GUARD_NS
        )
        counterfactual_upper = ceil_ratio(
            candidates[22], SAFETY_NUMERATOR, SAFETY_DENOMINATOR
        ) + COMPONENT_GUARD_NS
        counterfactual_total += counterfactual_upper
        rows.append(
            {
                "component": component,
                "observed_10_ns": observed[10],
                "ratio_25_over_10": list(ratios[10]),
                "candidate_10_ns": candidates[10],
                "observed_22_ns": observed[22],
                "ratio_25_over_22": list(ratios[22]),
                "candidate_22_ns": candidates[22],
                "deciding_endpoint": deciding,
                "deciding_candidate_ns": maximum,
                "upper_ns": upper,
                "fraction_of_projected_total": None,
            }
        )
    total = sum(_integer(row["upper_ns"], label="component upper") for row in rows)
    for row in rows:
        row["fraction_of_projected_total"] = _fraction_pair(
            _integer(row["upper_ns"], label="component upper"), total
        )
    passed = capacity_passes(total)
    return {
        "schema_version": (
            "legal-river-quotient-shared-direct-artifact-capacity-projection-v1"
        ),
        "target_population_geometry_only": TARGET_POPULATION,
        "component_rows": rows,
        "projected_host_ns": total,
        "wall_limit_ns": WALL_LIMIT_NS,
        "passed": passed,
        "endpoint_22_only_counterfactual": {
            "authoritative": False,
            "projected_host_ns": counterfactual_total,
            "wall_limit_ns": WALL_LIMIT_NS,
            "would_pass": capacity_passes(counterfactual_total),
        },
    }


def result_claims(projection: Mapping[str, object]) -> dict[str, object]:
    passed = projection.get("passed")
    projected = projection.get("projected_host_ns")
    if not isinstance(passed, bool) or isinstance(projected, bool) or not isinstance(projected, int):
        raise ValueError("capacity projection claim source differs")
    claims: dict[str, object] = {
        "capacity_projection_host_ns": projected,
        "capacity_passed": passed,
    }
    claims.update({key: (False if key == "truncation_authorized" else None) for key in RESULT_CLAIM_KEYS})
    return claims


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def build_result(
    *,
    endpoints: Sequence[EndpointObservation],
    input_raw: bytes,
    source_git_commit: str,
    dependency_hashes: Mapping[str, str],
    config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if (
        len(source_git_commit) != 40
        or any(character not in "0123456789abcdef" for character in source_git_commit)
    ):
        raise ValueError("capacity source commit differs")
    if len(input_raw) != INPUT_BYTES or sha256(input_raw).hexdigest() != INPUT_SHA256:
        raise ValueError("capacity result input identity differs")
    dependencies = {str(name): _digest(value, label=f"dependency {name}") for name, value in dependency_hashes.items()}
    projection = project_capacity(endpoints, config)
    passed = bool(projection["passed"])
    return {
        "schema_version": (
            "legal-river-quotient-shared-direct-artifact-capacity-result-v1"
        ),
        "config_sha256": CONFIG_SHA256,
        "source_git_commit": source_git_commit,
        "dependency_hashes": dict(sorted(dependencies.items())),
        "input": {
            "relative_path": INPUT_RELATIVE_PATH,
            "raw_sha256": INPUT_SHA256,
            "bytes": INPUT_BYTES,
            "source_commit": INPUT_SOURCE_COMMIT,
            "terminal": "completed_validation_pass",
            "populations": [10, 22],
            "phase_rows": INPUT_PHASE_ROWS,
        },
        "projection": projection,
        "terminal": (
            "completed_capacity_pass" if passed else "completed_capacity_rejection"
        ),
        "claims": result_claims(projection),
    }


__all__ = [
    "CALIBRATION_POPULATIONS",
    "COMPONENT_ORDER",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "EndpointObservation",
    "INPUT_RELATIVE_PATH",
    "INPUT_SHA256",
    "OUTSIDE_COMPONENT",
    "PHASE_ORDER",
    "RESULT_RELATIVE_PATH",
    "WALL_LIMIT_NS",
    "build_result",
    "capacity_passes",
    "canonical_json_bytes",
    "ceil_ratio",
    "component_projection_ratio",
    "endpoint_observation",
    "extract_bound_endpoints",
    "load_preregistered_config",
    "parent_phase_projection_constituents",
    "population_geometry",
    "project_capacity",
    "shared_component_constituents",
    "verify_preregistered_contract",
]
