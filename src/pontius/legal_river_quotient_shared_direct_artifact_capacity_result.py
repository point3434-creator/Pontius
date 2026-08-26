"""Independent standard-library reader for the ADR-0430 capacity result."""

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
CONFIG_SHA256 = (
    "720049432e3e8d85680a5781769f149d249920e3519b057d6df8ef0feedbceac"
)
INPUT_SHA256 = (
    "4e19a31f45c0f79db40db8df8e2b76806d3f5c39fc3a9e191b07043ddb711f0e"
)
INPUT_BYTES = 4_340_598
INPUT_SOURCE_COMMIT = "00d29e048d88ff4ece325b2a00866ddbd084617c"
INPUT_PHASE_ROWS = 3_028
POPULATIONS = (10, 22)
TARGET = 25
WALL_LIMIT_NS = 180_000_000_000
COMPONENT_GUARD_NS = 1_000_000
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
DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0430-preregister-the-shared-direct-artifact-capacity-assessor.md",
    "docs/decisions/ADR-0431-source-seal-the-shared-direct-artifact-capacity-assessor.md",
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity.py",
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_runner.py",
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_result.py",
    "tests/test_legal_river_quotient_shared_direct_artifact_capacity.py",
    INPUT_RELATIVE_PATH,
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_result.py",
    "src/pontius/durable_evidence_journal.py",
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v3.json",
    "docs/decisions/ADR-0429-retain-the-passing-shared-sample-plan-v3-validation.md",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json",
)
_CHUNKS = {
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
_TRANSITIONS = {
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
_PARENT_COUNTERS = {
    "forward_source_and_offset": (
        "source_pairing_visits",
        "source_weight_pair_times_float64",
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


@dataclass(frozen=True, slots=True)
class Phase:
    population: int
    family: str
    ordinal: int
    name: str
    start: int
    stop: int
    elapsed: int
    work: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class Endpoint:
    population: int
    phase_ns: tuple[tuple[str, int], ...]
    campaign_ns: int
    elapsed_ns: int
    outside_ns: int


@dataclass(frozen=True, slots=True)
class CapacityRebinding:
    terminal: str
    passed: bool
    projected_host_ns: int
    wall_limit_ns: int
    source_commit: str
    input_sha256: str
    deciding_endpoints: tuple[str, ...]


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"capacity reader {label} must be an integer at least {minimum}")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"capacity reader {label} must be an object")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"capacity reader {label} digest differs")
    return value


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
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


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"capacity reader duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_config() -> Mapping[str, object]:
    raw = (ROOT / CONFIG_RELATIVE_PATH).read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("capacity reader config hash differs")
    value = json.loads(raw, object_pairs_hook=_unique_object)
    config = _mapping(value, label="config")
    if config.get("schema_version") != (
        "legal-river-quotient-shared-direct-artifact-capacity-v1"
    ) or tuple(config.get("ordered_components", ())) != COMPONENT_ORDER:
        raise ValueError("capacity reader config identity differs")
    return config


def _geometry(cards: int) -> dict[str, int]:
    if cards not in (10, 22, 25):
        raise ValueError("capacity reader geometry population differs")
    return {
        "source_occupancies": comb(cards, 6),
        "source_recurrence_rows": sum(comb(cards, k) for k in range(7)),
        "query_occupancies": comb(cards, 4),
        "labeled_query_records": 6 * comb(cards, 4),
        "adjoint_recurrence_rows": sum(comb(cards, k) for k in range(5)),
        "compatible_sources_per_query_occupancy": comb(cards - 4, 6),
        "compatible_labeled_query_records_per_source": 6 * comb(cards - 6, 4),
    }


def _work(cards: int) -> dict[str, int]:
    geometry = _geometry(cards)
    executions, width, tiles, selected, boundary = 4, 176, 3, 16, 8
    source = geometry["source_occupancies"]
    query = geometry["query_occupancies"]
    records = geometry["labeled_query_records"]
    compatible_sources = geometry["compatible_sources_per_query_occupancy"]
    compatible_records = geometry["compatible_labeled_query_records_per_source"]
    return {
        "source_pairing_visits": source * 90 * executions * tiles,
        "source_weight_pair_times_float64": source * 90 * 6 * executions * tiles,
        "forward_recurrence_pair_child_adds": executions
        * width
        * sum(comb(cards, k) * (cards - k) for k in range(6)),
        "forward_pair_divides": executions
        * width
        * sum(comb(cards, k) for k in range(6)),
        "forward_signed_subset_pair_terms": executions * records * width * 16,
        "forward_fold_pair_times_pair": executions * records * width,
        "forward_tree_contributions": executions * records * 4,
        "adjoint_covector_pair_times_float64": executions * records * width,
        "adjoint_label_pair_adds": executions * query * 6 * width,
        "adjoint_recurrence_pair_child_adds": executions
        * width
        * sum(comb(cards, k) * (cards - k) for k in range(4)),
        "adjoint_pair_divides": executions
        * width
        * sum(comb(cards, k) for k in range(4)),
        "adjoint_signed_subset_pair_terms": executions
        * source
        * width
        * sum(comb(6, k) for k in range(5)),
        "adjoint_source_pairing_visits": source * 90 * executions * tiles,
        "adjoint_source_weight_pair_times_float64": source * 90 * 6 * executions * tiles,
        "adjoint_contract_pair_times_pair": executions * source * width,
        "adjoint_tree_contributions": executions * source * tiles,
        "shared_direct_source_unranks": selected * source * tiles * executions,
        "shared_direct_compatible_coefficient_pair_adds": selected
        * compatible_sources
        * width
        * executions,
        "shared_direct_final_feature_pair_products": selected * width * executions,
        "shared_direct_boundary_pair_copies": 512,
        "direct_adjoint_source_unranks": selected * tiles * executions,
        "direct_adjoint_query_record_visits": selected * records * tiles * executions,
        "direct_adjoint_compatible_query_weight_builds": selected
        * compatible_records
        * tiles
        * executions,
        "direct_adjoint_compatible_boundary_pair_adds": selected
        * compatible_records
        * boundary
        * executions,
    }


def _chunk_counts(cards: int) -> tuple[tuple[int, int, int], ...]:
    geometry = _geometry(cards)
    totals = (
        geometry["labeled_query_records"],
        geometry["query_occupancies"],
        geometry["source_occupancies"],
    )
    return tuple(
        tuple((total + size - 1) // size for total, size in zip(totals, family))
        for family in _CHUNKS[cards]
    )


def _maximum(rows: Sequence[tuple[str, int, int]]) -> tuple[int, int]:
    if not rows:
        raise ValueError("capacity reader ratio has no constituents")
    _, numerator, denominator = rows[0]
    for _, candidate_numerator, candidate_denominator in rows[1:]:
        if denominator <= 0 or candidate_denominator <= 0:
            raise ValueError("capacity reader ratio denominator differs")
        if candidate_numerator * denominator > numerator * candidate_denominator:
            numerator, denominator = candidate_numerator, candidate_denominator
    return numerator, denominator


def _parent_constituents(phase: str, endpoint: int) -> tuple[tuple[str, int, int], ...]:
    target_geometry, endpoint_geometry = _geometry(TARGET), _geometry(endpoint)
    target_work, endpoint_work = _work(TARGET), _work(endpoint)
    rows: list[tuple[str, int, int]] = []
    if phase == "forward_recurrence":
        name = "forward_recurrence_pair_child_adds"
        rows.append((name, target_work[name], endpoint_work[name]))
    elif phase in {
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
        "adjoint_covector_and_labels",
    }:
        rows.append(
            (
                "labeled_query_records",
                target_geometry["labeled_query_records"],
                endpoint_geometry["labeled_query_records"],
            )
        )
    elif phase == "direct_adjoint":
        rows.append(
            (
                "compatible_labeled_query_records_per_source",
                target_geometry["compatible_labeled_query_records_per_source"],
                endpoint_geometry["compatible_labeled_query_records_per_source"],
            )
        )
    else:
        rows.append(
            (
                "source_occupancies",
                target_geometry["source_occupancies"],
                endpoint_geometry["source_occupancies"],
            )
        )
    for name in _PARENT_COUNTERS.get(phase, ()):
        rows.append((name, target_work[name], endpoint_work[name]))
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
    rows.extend(
        (f"live_{field}", target_geometry[field], endpoint_geometry[field])
        for field in live_fields
    )
    target_chunks, endpoint_chunks = _chunk_counts(TARGET), _chunk_counts(endpoint)
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


def _ratio(component: str, endpoint: int) -> tuple[int, int]:
    if endpoint not in POPULATIONS:
        raise ValueError("capacity reader endpoint differs")
    if component == OUTSIDE_COMPONENT:
        return 1, 1
    if component == "shared_direct_fold_and_query":
        target_geometry, endpoint_geometry = _geometry(TARGET), _geometry(endpoint)
        target_work, endpoint_work = _work(TARGET), _work(endpoint)
        rows = [
            (
                "compatible_sources_per_query_occupancy",
                target_geometry["compatible_sources_per_query_occupancy"],
                endpoint_geometry["compatible_sources_per_query_occupancy"],
            )
        ]
        for name in (
            "shared_direct_source_unranks",
            "shared_direct_compatible_coefficient_pair_adds",
            "shared_direct_final_feature_pair_products",
            "shared_direct_boundary_pair_copies",
        ):
            rows.append((name, target_work[name], endpoint_work[name]))
        return _maximum(rows)
    if component not in PHASE_ORDER:
        raise ValueError("capacity reader component differs")
    return _maximum(_parent_constituents(component, endpoint))


def _ceil(value: int, numerator: int, denominator: int) -> int:
    if value < 0 or numerator < 0 or denominator <= 0:
        raise ValueError("capacity reader ceiling input differs")
    return (value * numerator + denominator - 1) // denominator


def _fraction(numerator: int, denominator: int) -> list[int]:
    divisor = gcd(numerator, denominator)
    return [numerator // divisor, denominator // divisor]


def _parse_phase(event: Mapping[str, object]) -> Phase:
    expected = {
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
    if set(event) != expected or event.get("schema_version") != (
        "legal-river-shared-direct-phase-v1"
    ):
        raise ValueError("capacity reader raw phase schema differs")
    population = _integer(event.get("population"), label="phase population")
    family, name = event.get("family"), event.get("phase")
    ordinal = _integer(event.get("ordinal"), label="phase ordinal")
    repeat = _integer(event.get("repeat"), label="phase repeat")
    tile = _integer(event.get("tile"), label="phase tile")
    start = _integer(event.get("host_start_ns"), label="phase start")
    stop = _integer(event.get("host_stop_ns"), label="phase stop")
    elapsed = _integer(event.get("host_ns"), label="phase elapsed")
    _integer(event.get("device_ns"), label="phase device")
    if (
        population not in POPULATIONS
        or not isinstance(family, str)
        or family not in FAMILIES
        or not isinstance(name, str)
        or name not in PHASE_ORDER
        or repeat not in (0, 1)
        or tile not in (0, 1, 2)
        or event.get("chunks") != list(_EXPECTED_CHUNKS[population][family])
        or stop < start
        or elapsed != stop - start
    ):
        raise ValueError("capacity reader raw phase identity differs")
    work = _mapping(event.get("work"), label="phase work")
    if not set(work).issubset(_PHASE_COUNTERS.get(name, set())):
        raise ValueError("capacity reader phase work is misplaced")
    return Phase(
        population,
        family,
        ordinal,
        name,
        start,
        stop,
        elapsed,
        tuple(
            sorted(
                (str(key), _integer(value, label=f"phase work {key}"))
                for key, value in work.items()
            )
        ),
    )


def _validate_group(rows: Sequence[Phase]) -> None:
    if (
        not rows
        or [row.ordinal for row in rows] != list(range(len(rows)))
        or rows[0].name != PHASE_ORDER[0]
        or rows[-1].name != PHASE_ORDER[-1]
        or {row.name for row in rows} != set(PHASE_ORDER)
    ):
        raise ValueError("capacity reader raw phase group differs")
    for left, right in zip(rows, rows[1:]):
        if (
            left.population != right.population
            or left.family != right.family
            or left.stop != right.start
            or right.name not in _TRANSITIONS[left.name]
        ):
            raise ValueError("capacity reader raw phase partition differs")
    if sum(row.elapsed for row in rows) != rows[-1].stop - rows[0].start:
        raise ValueError("capacity reader raw phase sum differs")


def _expected_shared_work(cards: int) -> dict[str, int]:
    return {
        name: value
        for name, value in _work(cards).items()
        if not name.startswith("direct_query_") and not name.startswith("direct_fold_")
    }


def _endpoint(event: Mapping[str, object], rows: Sequence[Phase]) -> Endpoint:
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
        raise ValueError("capacity reader raw population schema differs")
    population = _integer(event.get("population"), label="population")
    if population not in POPULATIONS or any(row.population != population for row in rows):
        raise ValueError("capacity reader population identity differs")
    groups = {family: [row for row in rows if row.family == family] for family in FAMILIES}
    for group in groups.values():
        _validate_group(group)
    if [row.family for row in rows] != [family for family in FAMILIES for _ in groups[family]]:
        raise ValueError("capacity reader family order differs")
    totals = {phase: 0 for phase in PHASE_ORDER}
    work: dict[str, int] = {}
    for row in rows:
        totals[row.name] += row.elapsed
        for name, value in row.work:
            work[name] = work.get(name, 0) + value
    expected_work = _expected_shared_work(population)
    campaign = _integer(event.get("campaign_host_ns"), label="campaign")
    elapsed = _integer(event.get("population_elapsed_host_ns"), label="elapsed")
    if (
        event.get("phase_host_ns") != totals
        or campaign != sum(totals.values())
        or elapsed < campaign
        or event.get("executed_work") != expected_work
        or event.get("expected_work") != expected_work
        or work != expected_work
    ):
        raise ValueError("capacity reader population reconstruction differs")
    return Endpoint(
        population,
        tuple((phase, totals[phase]) for phase in PHASE_ORDER),
        campaign,
        elapsed,
        elapsed - campaign,
    )


def _raw_endpoints(input_raw: bytes) -> tuple[Endpoint, Endpoint]:
    if len(input_raw) != INPUT_BYTES or sha256(input_raw).hexdigest() != INPUT_SHA256:
        raise ValueError("capacity reader input artifact identity differs")
    from .durable_evidence_journal import recover_journal_bytes
    from .legal_river_quotient_cuda_shared_direct_device_v3_result import (
        CAMPAIGN_SHA256,
        PROTOCOL_SHA256,
        rebind_shared_direct_device_v3_journal,
    )

    rebound = rebind_shared_direct_device_v3_journal(
        input_raw, rebind_current_sources=True
    )
    if (
        rebound.terminal != "completed_validation_pass"
        or rebound.passed is not True
        or rebound.source_commit != INPUT_SOURCE_COMMIT
        or rebound.populations != POPULATIONS
        or rebound.phase_count != INPUT_PHASE_ROWS
    ):
        raise ValueError("capacity reader complete V3 rebind differs")
    recovery = recover_journal_bytes(
        input_raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError("capacity reader raw V3 recovery differs")
    wrappers: list[tuple[str, Mapping[str, object]]] = []
    for record in recovery.records[1:-1]:
        wrapper = _mapping(record.body.payload, label="V3 wrapper")
        if set(wrapper) != {"schema_version", "kind", "event", "config_sha256"}:
            raise ValueError("capacity reader V3 wrapper differs")
        kind = wrapper.get("kind")
        if not isinstance(kind, str):
            raise ValueError("capacity reader V3 kind differs")
        wrappers.append((kind, _mapping(wrapper.get("event"), label="V3 event")))
    phases = [_parse_phase(event) for kind, event in wrappers if kind == "phase"]
    population_events = [event for kind, event in wrappers if kind == "population"]
    if len(phases) != INPUT_PHASE_ROWS or len(population_events) != 2:
        raise ValueError("capacity reader V3 row cardinality differs")
    endpoints = tuple(
        _endpoint(event, [row for row in phases if row.population == population])
        for population, event in zip(POPULATIONS, population_events, strict=True)
    )
    if tuple(endpoint.population for endpoint in endpoints) != POPULATIONS:
        raise ValueError("capacity reader endpoint order differs")
    return endpoints  # type: ignore[return-value]


def _expected_projection(endpoints: Sequence[Endpoint], config: Mapping[str, object]) -> dict[str, object]:
    if len(endpoints) != 2 or tuple(endpoint.population for endpoint in endpoints) != POPULATIONS:
        raise ValueError("capacity reader projection endpoints differ")
    ratios = _mapping(config.get("component_projection_ratios"), label="config ratios")
    for component in COMPONENT_ORDER:
        stored = _mapping(ratios.get(component), label=f"ratio {component}")
        for endpoint in POPULATIONS:
            derived = _ratio(component, endpoint)
            if stored.get(f"25_over_{endpoint}") != list(derived):
                raise ValueError(f"capacity reader config ratio differs: {component}/{endpoint}")
    endpoint_maps = {endpoint.population: dict(endpoint.phase_ns) for endpoint in endpoints}
    rows: list[dict[str, object]] = []
    counterfactual = 0
    for component in COMPONENT_ORDER:
        observations = {
            endpoint.population: (
                endpoint.outside_ns
                if component == OUTSIDE_COMPONENT
                else endpoint_maps[endpoint.population][component]
            )
            for endpoint in endpoints
        }
        endpoint_ratios = {population: _ratio(component, population) for population in POPULATIONS}
        candidates = {
            population: _ceil(observations[population], *endpoint_ratios[population])
            for population in POPULATIONS
        }
        maximum = max(candidates.values())
        upper = _ceil(maximum, 5, 4) + COMPONENT_GUARD_NS
        counterfactual += _ceil(candidates[22], 5, 4) + COMPONENT_GUARD_NS
        deciding = "tie" if candidates[10] == candidates[22] else (
            "10" if candidates[10] > candidates[22] else "22"
        )
        rows.append(
            {
                "component": component,
                "observed_10_ns": observations[10],
                "ratio_25_over_10": list(endpoint_ratios[10]),
                "candidate_10_ns": candidates[10],
                "observed_22_ns": observations[22],
                "ratio_25_over_22": list(endpoint_ratios[22]),
                "candidate_22_ns": candidates[22],
                "deciding_endpoint": deciding,
                "deciding_candidate_ns": maximum,
                "upper_ns": upper,
                "fraction_of_projected_total": None,
            }
        )
    total = sum(int(row["upper_ns"]) for row in rows)
    for row in rows:
        row["fraction_of_projected_total"] = _fraction(int(row["upper_ns"]), total)
    return {
        "schema_version": (
            "legal-river-quotient-shared-direct-artifact-capacity-projection-v1"
        ),
        "target_population_geometry_only": TARGET,
        "component_rows": rows,
        "projected_host_ns": total,
        "wall_limit_ns": WALL_LIMIT_NS,
        "passed": total <= WALL_LIMIT_NS,
        "endpoint_22_only_counterfactual": {
            "authoritative": False,
            "projected_host_ns": counterfactual,
            "wall_limit_ns": WALL_LIMIT_NS,
            "would_pass": counterfactual <= WALL_LIMIT_NS,
        },
    }


def _expected_claims(projection: Mapping[str, object]) -> dict[str, object]:
    return {
        "capacity_projection_host_ns": projection["projected_host_ns"],
        "capacity_passed": projection["passed"],
        "complete_25_numerical_value": None,
        "actual_45_card_value": None,
        "resolver_iteration_result": None,
        "action_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "exact_integer_result": None,
        "truncation_authorized": False,
        "blueprint_result": None,
        "poker_strength_result": None,
    }


def validate_capacity_result_document(
    result: Mapping[str, object],
    *,
    endpoints: Sequence[Endpoint],
    config: Mapping[str, object],
) -> CapacityRebinding:
    """Validate a parsed result against independently supplied endpoint evidence."""

    expected_fields = {
        "schema_version",
        "config_sha256",
        "source_git_commit",
        "dependency_hashes",
        "input",
        "projection",
        "terminal",
        "claims",
    }
    source_commit = result.get("source_git_commit")
    if (
        set(result) != expected_fields
        or result.get("schema_version")
        != "legal-river-quotient-shared-direct-artifact-capacity-result-v1"
        or result.get("config_sha256") != CONFIG_SHA256
        or not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in "0123456789abcdef" for character in source_commit)
    ):
        raise ValueError("capacity reader result identity differs")
    dependencies = _mapping(result.get("dependency_hashes"), label="dependencies")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("capacity reader dependency inventory differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        _digest(dependencies.get(relative), label=f"dependency {relative}")
    input_identity = _mapping(result.get("input"), label="input identity")
    if input_identity != {
        "relative_path": INPUT_RELATIVE_PATH,
        "raw_sha256": INPUT_SHA256,
        "bytes": INPUT_BYTES,
        "source_commit": INPUT_SOURCE_COMMIT,
        "terminal": "completed_validation_pass",
        "populations": [10, 22],
        "phase_rows": INPUT_PHASE_ROWS,
    }:
        raise ValueError("capacity reader stored input identity differs")
    expected_projection = _expected_projection(endpoints, config)
    projection = _mapping(result.get("projection"), label="projection")
    if projection != expected_projection:
        raise ValueError("capacity reader projection derivation differs")
    passed = bool(expected_projection["passed"])
    terminal = "completed_capacity_pass" if passed else "completed_capacity_rejection"
    if result.get("terminal") != terminal or result.get("claims") != _expected_claims(expected_projection):
        raise ValueError("capacity reader terminal or claims differ")
    rows = expected_projection["component_rows"]
    assert isinstance(rows, list)
    return CapacityRebinding(
        terminal=terminal,
        passed=passed,
        projected_host_ns=int(expected_projection["projected_host_ns"]),
        wall_limit_ns=WALL_LIMIT_NS,
        source_commit=source_commit,
        input_sha256=INPUT_SHA256,
        deciding_endpoints=tuple(str(row["deciding_endpoint"]) for row in rows),
    )


def rebind_capacity_result_bytes(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> CapacityRebinding:
    if not isinstance(raw, bytes) or not raw or len(raw) > 1_048_576:
        raise ValueError("capacity reader result byte envelope differs")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("capacity reader result JSON differs") from error
    result = _mapping(value, label="result")
    if _canonical_json_bytes(result) != raw:
        raise ValueError("capacity reader result is not canonical JSON")
    dependencies = _mapping(result.get("dependency_hashes"), label="dependencies")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("capacity reader dependency inventory differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        retained = _digest(dependencies.get(relative), label=f"dependency {relative}")
        if rebind_current_sources:
            path_raw = (ROOT / relative).read_bytes()
            if not relative.startswith("artifacts/"):
                path_raw = path_raw.replace(b"\r\n", b"\n")
            if sha256(path_raw).hexdigest() != retained:
                raise ValueError(f"capacity reader dependency differs: {relative}")
    config = _load_config()
    input_raw = (ROOT / INPUT_RELATIVE_PATH).read_bytes()
    endpoints = _raw_endpoints(input_raw)
    return validate_capacity_result_document(
        result,
        endpoints=endpoints,
        config=config,
    )


def rebind_capacity_result_file(
    path: Path = ROOT / RESULT_RELATIVE_PATH,
    *,
    rebind_current_sources: bool = True,
) -> CapacityRebinding:
    if not isinstance(path, Path):
        raise TypeError("capacity reader path must be a Path")
    return rebind_capacity_result_bytes(
        path.read_bytes(), rebind_current_sources=rebind_current_sources
    )


__all__ = [
    "CapacityRebinding",
    "DEPENDENCY_RELATIVE_PATHS",
    "RESULT_RELATIVE_PATH",
    "rebind_capacity_result_bytes",
    "rebind_capacity_result_file",
    "validate_capacity_result_document",
]
