"""GPU-free ADR-0449/ADR-0450 literal-45 fit projection.

Importing this module does not read the retained result or artifact, spawn a
process, or import a device package.  The one-shot runner supplies immutable
artifact bytes explicitly after the source seal.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import re
from typing import Any

from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-actual45-fit-projection-v1.json"
)
CONFIG_SHA256 = "8cfa35eb3188bfeeacd1bae7df39cbae55b98153d13cc24fc8d47a5b6bd92e8e"
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-actual45-fit-projection-v2-accounting.json"
)
CORRECTION_CONFIG_SHA256 = (
    "38cb2ba3a0de28698911024ab645a1ba3cd873e58f466fb86b281b3d7d28c24f"
)
INPUT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v3.jsonl"
)
INPUT_BYTES = 4_175_066
INPUT_SHA256 = "6f0b53f95a5d538f7a3673fe411de4b40724fbf00cfc56c62360352cab3770bb"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_actual45_fit_projection_v1.jsonl"
)

POSITIONAL = "positional"
BATCHED_RRNS = "batched_five_then_four_RRNS"
ARMS = (POSITIONAL, BATCHED_RRNS)
POPULATIONS = ("complete_10", "signed_12")
TARGET = "literal_45"
COMPONENT_CEILING_NS = 14_000_000_000
SAFETY_NUMERATOR = 5
SAFETY_DENOMINATOR = 4
PHASE_GUARD_NS = 1_000_000

POSITIONAL_PHASES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "family_admission_pair_encoding_and_label_aggregation",
    "forward_recurrence",
    "forward_selective_queries",
    "forward_streamed_global_scan_and_scalar_contract",
    "adjoint_recurrence",
    "adjoint_selective_queries",
    "adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)
BATCHED_PHASES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "first_batch_family_admission_pair_encoding_and_label_aggregation",
    "first_batch_forward_recurrence",
    "first_batch_forward_selective_queries",
    "first_batch_forward_streamed_global_scan_and_scalar_contract",
    "first_batch_adjoint_recurrence",
    "first_batch_adjoint_selective_queries",
    "first_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "first_batch_output_drain_and_workspace_reuse_boundary",
    "second_batch_family_admission_pair_encoding_and_label_aggregation",
    "second_batch_forward_recurrence",
    "second_batch_forward_selective_queries",
    "second_batch_forward_streamed_global_scan_and_scalar_contract",
    "second_batch_adjoint_recurrence",
    "second_batch_adjoint_selective_queries",
    "second_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)
PHASES = {POSITIONAL: POSITIONAL_PHASES, BATCHED_RRNS: BATCHED_PHASES}
VALIDATION_PHASE = "verification_output_transfer_and_exact_differential"
RUNTIME_PHASES = {
    arm: tuple(name for name in phases if name != VALIDATION_PHASE)
    for arm, phases in PHASES.items()
}

MEMORY = {
    POSITIONAL: (13_265_364_040, 1_829_111_736, True),
    BATCHED_RRNS: (13_275_877_664, 1_818_598_112, True),
}

CLAIM_KEYS = (
    "actual_45_component_exponent_admission",
    "action_clock_result",
    "action_result",
    "blueprint_result",
    "candidate_selected",
    "decision_quality_result",
    "literal_45_live_allocation",
    "literal_45_numeric_value",
    "poker_strength_result",
    "resolver_iteration_result",
    "solve_result",
    "truncation_authorized",
)


@dataclass(frozen=True, slots=True)
class CalibrationSnapshot:
    phase_maxima_ns: Mapping[str, Mapping[str, Mapping[str, int]]]
    phase_observations_ns: Mapping[
        str,
        Mapping[str, Mapping[str, tuple[tuple[str, int, int], ...]]],
    ]
    memory: Mapping[str, tuple[int, int, bool]]


def _canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index : index + 2] == bytes((13, 10)):
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("projection dependency is absent")
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise TypeError(f"{label} must be an integer at or above {minimum}")
    return value


def _load_config(path: Path, expected_hash: str, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or sha256(_canonical_lf(raw)).hexdigest() != expected_hash:
        raise ValueError("fit-projection config identity differs")
    parsed = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != schema:
        raise ValueError("fit-projection config schema differs")
    return parsed


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_preregistered_configs() -> tuple[dict[str, object], dict[str, object]]:
    return (
        _load_config(
            ROOT / CONFIG_RELATIVE_PATH,
            CONFIG_SHA256,
            "legal-river-quotient-fixed-width-actual45-fit-projection-config-v1",
        ),
        _load_config(
            ROOT / CORRECTION_CONFIG_RELATIVE_PATH,
            CORRECTION_CONFIG_SHA256,
            "legal-river-quotient-fixed-width-actual45-fit-projection-accounting-correction-v2",
        ),
    )


def projection_constituents(cards: int, width: int, tiles: int) -> dict[str, int]:
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (cards, width, tiles)):
        raise TypeError("projection geometry must be positive integers")
    source = comb(cards, 6)
    query = comb(cards, 4)
    labeled = 6 * query
    forward_edges = sum(comb(cards, level) * (cards - level) for level in range(6))
    adjoint_edges = sum(comb(cards, level) * (cards - level) for level in range(4))
    label_additions = 5 * query
    return {
        "captured_pair_components": 2 * source * width + 2 * labeled * width + 2 * labeled,
        "family_encoding_entries": source * width + labeled * width + labeled,
        "forward_recurrence_vector_entries": forward_edges * width,
        "forward_recurrence_launches": 6 * tiles,
        "forward_selective_subset_entries": 16 * width,
        "forward_selective_scalar_products": width,
        "forward_global_subset_entries": query * 16 * width,
        "forward_global_scalar_and_reach_products": query * width + query,
        "forward_stream_chunks": ((query + 4095) // 4096) * tiles,
        "adjoint_recurrence_and_label_vector_entries": (adjoint_edges + label_additions) * width,
        "adjoint_label_scalar_additions": label_additions,
        "adjoint_recurrence_launches": 4 * tiles,
        "adjoint_selective_subset_entries": 57 * width,
        "adjoint_selective_scalar_products": width,
        "adjoint_global_subset_entries": source * 57 * width,
        "adjoint_global_scalar_products": source * width,
        "adjoint_stream_chunks": ((source + 4095) // 4096) * tiles,
        "feature_tiles": tiles,
        "fixed_scalar_sites": 3 * tiles,
    }


def _config_constituents(base: Mapping[str, object]) -> dict[str, dict[str, int]]:
    raw = _mapping(base.get("projection_constituent_counts"), label="constituent counts")
    output: dict[str, dict[str, int]] = {}
    for label in (*POPULATIONS, TARGET):
        row = _mapping(raw.get(label), label=f"{label} constituent row")
        output[label] = {
            key: _integer(value, label=f"{label} {key}", minimum=1)
            for key, value in row.items()
            if isinstance(value, int) and not isinstance(value, bool)
        }
    return output


def _phase_drivers(base: Mapping[str, object]) -> dict[str, tuple[str, ...]]:
    raw = _mapping(base.get("phase_driver_contract"), label="phase drivers")
    rows: dict[str, tuple[str, ...]] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            names = tuple(value)
            if not names or any(not isinstance(name, str) or not name for name in names):
                raise ValueError("phase driver list differs")
            rows[key] = names
    if set(rows) != set(POSITIONAL_PHASES) | set(BATCHED_PHASES):
        raise ValueError("phase driver domain differs")
    return rows


def verify_preregistered_contract() -> None:
    base, correction = load_preregistered_configs()
    parent = _mapping(base.get("retained_parent"), label="retained parent")
    bound_paths = {
        "outcome_adr_canonical_lf_sha256": parent.get("outcome_adr_relative_path"),
        "outcome_assessor_canonical_lf_sha256": parent.get("outcome_assessor_relative_path"),
        "fixed_width_work_source_canonical_lf_sha256": parent.get("fixed_width_work_source_relative_path"),
        "device_source_canonical_lf_sha256": parent.get("device_source_relative_path"),
        "action_clock_canonical_lf_sha256": parent.get("action_clock_relative_path"),
    }
    for digest_field, relative in bound_paths.items():
        if not isinstance(relative, str) or canonical_lf_sha256(ROOT / relative) != parent.get(digest_field):
            raise ValueError(f"fit-projection parent differs: {digest_field}")
    correction_parent = _mapping(correction.get("parent_config"), label="correction parent")
    if correction_parent.get("relative_path") != CONFIG_RELATIVE_PATH or correction_parent.get("canonical_lf_sha256") != CONFIG_SHA256:
        raise ValueError("fit-projection correction parent differs")

    expected_counts = {
        "complete_10": projection_constituents(10, 176, 1),
        "signed_12": projection_constituents(12, 5, 1),
        TARGET: projection_constituents(45, 176, 3),
    }
    if _config_constituents(base) != expected_counts:
        raise ValueError("fit-projection constituent counts differ")
    drivers = _phase_drivers(base)
    if any(any(name not in expected_counts[TARGET] for name in names) for names in drivers.values()):
        raise ValueError("fit-projection driver references an unknown constituent")

    calibration = _mapping(base.get("calibration_contract"), label="calibration")
    if (
        calibration.get("timed_observations_per_arm_population") != 6
        or calibration.get("warmup_observations_per_arm_population") != 1
        or calibration.get("positional_phase_count") != len(POSITIONAL_PHASES)
        or calibration.get("batched_phase_count") != len(BATCHED_PHASES)
    ):
        raise ValueError("fit-projection calibration schedule differs")
    guarded = _mapping(base.get("guarded_projection"), label="guarded projection")
    if (
        guarded.get("safety_multiplier_fraction")
        != [SAFETY_NUMERATOR, SAFETY_DENOMINATOR]
        or guarded.get("per_phase_absolute_guard_ns") != PHASE_GUARD_NS
    ):
        raise ValueError("fit-projection guard constants differ")

    classes = _mapping(correction.get("phase_classification"), label="phase classification")
    runtime = _mapping(classes.get("runtime_component_phases"), label="runtime phases")
    validation = _mapping(classes.get("laboratory_validation_phases"), label="validation phases")
    for arm in ARMS:
        runtime_names = tuple(runtime.get(arm, ()))
        validation_names = tuple(validation.get(arm, ()))
        if runtime_names != RUNTIME_PHASES[arm] or validation_names != (VALIDATION_PHASE,):
            raise ValueError(f"fit-projection phase classification differs: {arm}")
        rebuilt = tuple(name for name in PHASES[arm] if name in set(runtime_names) | set(validation_names))
        if set(runtime_names) & set(validation_names) or rebuilt != PHASES[arm]:
            raise ValueError(f"fit-projection phase partition differs: {arm}")

    action = _mapping(base.get("action_clock_contract"), label="action clock")
    if (
        action.get("controlled_action_wall_ns") != 15_000_000_000
        or action.get("emission_reserve_ns") != 1_000_000_000
        or action.get("maximum_charged_component_work_ns") != COMPONENT_CEILING_NS
    ):
        raise ValueError("fit-projection action clock differs")
    corrected_projection = _mapping(
        correction.get("corrected_projection_contract"),
        label="corrected projection",
    )
    if (
        corrected_projection.get("maximum_charged_runtime_component_ns")
        != COMPONENT_CEILING_NS
        or corrected_projection.get("runtime_component_passes_if_and_only_if_at_or_below_14000000000ns")
        is not True
        or corrected_projection.get("laboratory_validation_has_no_action_clock_gate")
        is not True
    ):
        raise ValueError("fit-projection corrected wall contract differs")
    memory = _mapping(base.get("memory_and_width_contract"), label="memory contract")
    peaks = _mapping(memory.get("retained_symbolic_peaks"), label="symbolic peaks")
    headrooms = _mapping(memory.get("retained_symbolic_headroom_after_reserve"), label="symbolic headroom")
    for arm, (peak, headroom, _) in MEMORY.items():
        if peaks.get(arm) != peak or headrooms.get(arm) != headroom:
            raise ValueError(f"fit-projection memory binding differs: {arm}")

    identity = _mapping(correction.get("corrected_prospective_identity"), label="corrected identity")
    if (
        identity.get("result_relative_path") != RESULT_RELATIVE_PATH
        or identity.get("launcher_relative_path")
        != "run_legal_river_quotient_fixed_width_actual45_fit_projection.py"
        or identity.get("assessor_relative_path")
        != "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection.py"
        or identity.get("runner_relative_path")
        != "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_runner.py"
        or identity.get("reader_relative_path")
        != "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_result.py"
        or identity.get("controls_relative_path")
        != "tests/test_legal_river_quotient_fixed_width_actual45_fit_projection.py"
    ):
        raise ValueError("fit-projection result identity differs")
    attributes = (ROOT / "artifacts/work_preflight/.gitattributes").read_text(encoding="ascii").splitlines()
    if "*.jsonl -text" not in attributes or not RESULT_RELATIVE_PATH.endswith(".jsonl"):
        raise ValueError("fit-projection result path is not covered by -text")


def _phase_elapsed(event: Mapping[str, object], expected: Sequence[str]) -> dict[str, int]:
    partition = _mapping(event.get("phase_partition"), label="phase partition")
    raw_rows = partition.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(expected):
        raise ValueError("candidate phase count differs")
    rows: dict[str, int] = {}
    prior_end: int | None = None
    for expected_name, raw in zip(expected, raw_rows, strict=True):
        row = _mapping(raw, label="phase row")
        if set(row) != {"name", "start_ns", "end_ns", "elapsed_ns"} or row.get("name") != expected_name:
            raise ValueError("candidate phase row differs")
        start = _integer(row.get("start_ns"), label="phase start")
        end = _integer(row.get("end_ns"), label="phase end")
        elapsed = _integer(row.get("elapsed_ns"), label="phase elapsed")
        if end - start != elapsed or (prior_end is not None and start != prior_end):
            raise ValueError("candidate phase partition has a gap or overlap")
        prior_end = end
        rows[expected_name] = elapsed
    if sum(rows.values()) != _integer(partition.get("total_ns"), label="phase total"):
        raise ValueError("candidate phase total differs")
    return rows


def calibration_snapshot_from_events(
    candidate_events: Sequence[Mapping[str, object]],
    memory: Mapping[str, tuple[int, int, bool]],
) -> CalibrationSnapshot:
    events = tuple(candidate_events)
    expected_groups = {(arm, population) for arm in ARMS for population in POPULATIONS}
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = {key: [] for key in expected_groups}
    for event in events:
        arm = event.get("arm")
        population = event.get("population")
        if (arm, population) not in grouped:
            raise ValueError("candidate event arm or population differs")
        if event.get("exact_verified") is not True:
            raise ValueError("candidate event is not exactly verified")
        grouped[(str(arm), str(population))].append(event)
    if set(grouped) != expected_groups or any(len(rows) != 7 for rows in grouped.values()):
        raise ValueError("candidate event group cardinality differs")

    maxima: dict[str, dict[str, dict[str, int]]] = {
        arm: {population: {} for population in POPULATIONS} for arm in ARMS
    }
    observations: dict[
        str,
        dict[str, dict[str, tuple[tuple[str, int, int], ...]]],
    ] = {arm: {population: {} for population in POPULATIONS} for arm in ARMS}
    for (arm, population), rows in grouped.items():
        warmups = [row for row in rows if row.get("schedule_kind") == "warmup"]
        timed = [row for row in rows if row.get("schedule_kind") == "timed"]
        if len(warmups) != 1 or len(timed) != 6:
            raise ValueError("candidate warmup/timed split differs")
        if (
            warmups[0].get("traversal_order") != "ascending_colex"
            or warmups[0].get("repeat_index") != 0
        ):
            raise ValueError("candidate warmup schedule differs")
        schedule = Counter(
            (row.get("traversal_order"), row.get("repeat_index")) for row in timed
        )
        if schedule != Counter(
            {
                (direction, repeat): 1
                for direction in ("ascending_colex", "descending_colex")
                for repeat in range(3)
            }
        ):
            raise ValueError("candidate timed traversal schedule differs")
        _phase_elapsed(warmups[0], PHASES[arm])
        timed_ordered = sorted(
            timed,
            key=lambda row: (
                0 if row.get("traversal_order") == "ascending_colex" else 1,
                int(row.get("repeat_index", -1)),
            ),
        )
        timed_parsed = [_phase_elapsed(row, PHASES[arm]) for row in timed_ordered]
        for name in PHASES[arm]:
            maxima[arm][population][name] = max(
                row[name] for row in timed_parsed
            )
            observations[arm][population][name] = tuple(
                (
                    str(event["traversal_order"]),
                    int(event["repeat_index"]),
                    parsed[name],
                )
                for event, parsed in zip(timed_ordered, timed_parsed, strict=True)
            )

    normalized_memory: dict[str, tuple[int, int, bool]] = {}
    if set(memory) != set(ARMS):
        raise ValueError("projection memory arm domain differs")
    for arm, raw in memory.items():
        if not isinstance(raw, tuple) or len(raw) != 3 or not isinstance(raw[2], bool):
            raise TypeError("projection memory row differs")
        normalized_memory[arm] = (
            _integer(raw[0], label="memory peak"),
            _integer(raw[1], label="memory headroom"),
            raw[2],
        )
    return CalibrationSnapshot(maxima, observations, normalized_memory)


def extract_calibration_snapshot(raw: bytes) -> CalibrationSnapshot:
    if type(raw) is not bytes or len(raw) != INPUT_BYTES or sha256(raw).hexdigest() != INPUT_SHA256:
        raise ValueError("fit-projection parent artifact identity differs")
    from .legal_river_quotient_fixed_width_device_preflight_v3_outcome import (
        assess_device_preflight_v3_outcome_bytes,
    )
    from .legal_river_quotient_fixed_width_device_preflight_v3_result import (
        CAMPAIGN_SHA256,
        PROTOCOL_SHA256,
    )

    outcome = assess_device_preflight_v3_outcome_bytes(raw)
    if outcome.eligible_arms != ARMS or outcome.candidate_selected is not None:
        raise ValueError("fit-projection parent outcome differs")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("fit-projection parent lifecycle differs")
    observations = [
        record.body.payload
        for record in recovery.records
        if record.body.kind is JournalRecordKind.OBSERVATION
    ]
    candidate_events = [
        _mapping(row.get("event"), label="candidate event")
        for row in observations
        if row.get("kind") == "candidate_observation"
        and _mapping(row.get("event"), label="candidate event").get("arm") in ARMS
    ]
    memory_events = [
        _mapping(row.get("event"), label="memory event")
        for row in observations
        if row.get("kind") == "symbolic_literal_45_memory_liveness"
    ]
    if len(memory_events) != 1:
        raise ValueError("fit-projection parent memory event differs")
    memory_rows: dict[str, tuple[int, int, bool]] = {}
    for arm in ARMS:
        row = _mapping(memory_events[0].get(arm), label=f"{arm} memory")
        live = _mapping(row.get("liveness"), label=f"{arm} liveness")
        peak = _integer(live.get("peak_live_bytes"), label="memory peak")
        total = _integer(live.get("device_total_bytes"), label="device total")
        reserve = _integer(live.get("device_reserve_bytes"), label="device reserve")
        memory_rows[arm] = (peak, total - reserve - peak, live.get("eligible") is True)
    snapshot = calibration_snapshot_from_events(candidate_events, memory_rows)
    if snapshot.memory != MEMORY:
        raise ValueError("fit-projection parent memory receipts differ")
    return snapshot


def _ceil_fraction(value: int, ratio: Fraction) -> int:
    item = _integer(value, label="projection elapsed")
    return (item * ratio.numerator + ratio.denominator - 1) // ratio.denominator


def component_projection_passes(value: int) -> bool:
    return _integer(value, label="component projection") <= COMPONENT_CEILING_NS


def _ratio_for_phase(
    phase: str,
    population: str,
    counts: Mapping[str, Mapping[str, int]],
    drivers: Mapping[str, tuple[str, ...]],
) -> tuple[Fraction, str]:
    candidates: list[tuple[Fraction, str]] = []
    for name in drivers[phase]:
        target = counts[TARGET][name]
        calibration = counts[population][name]
        if target > 0 and calibration == 0:
            raise ValueError("positive target work has zero calibration work")
        if target == calibration == 0:
            continue
        candidates.append((Fraction(target, calibration), name))
    if not candidates:
        raise ValueError("phase has no projectable constituent")
    maximum = max(value for value, _ in candidates)
    names = sorted(name for value, name in candidates if value == maximum)
    return maximum, "+".join(names)


def _outcome(arms: Mapping[str, Mapping[str, object]]) -> tuple[str, list[str]]:
    eligible = [arm for arm in ARMS if arms[arm].get("projection_eligible") is True]
    if not eligible:
        return "projection_rejected_before_target_allocation", []
    if len(eligible) == 1:
        return "projection_admits_one_arm_for_separate_live_screen", eligible
    return "projection_admits_two_arms_for_separate_live_screen", eligible


def project_snapshot(snapshot: CalibrationSnapshot) -> dict[str, object]:
    base, _ = load_preregistered_configs()
    counts = _config_constituents(base)
    drivers = _phase_drivers(base)
    arms: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        if set(snapshot.phase_maxima_ns.get(arm, {})) != set(POPULATIONS):
            raise ValueError("projection snapshot population domain differs")
        phase_rows: list[dict[str, object]] = []
        for phase in PHASES[arm]:
            endpoint_rows: dict[str, dict[str, object]] = {}
            for population in POPULATIONS:
                phases = snapshot.phase_maxima_ns[arm][population]
                if set(phases) != set(PHASES[arm]):
                    raise ValueError("projection snapshot phase domain differs")
                observation_phases = snapshot.phase_observations_ns[arm][population]
                if set(observation_phases) != set(PHASES[arm]):
                    raise ValueError("projection snapshot observation domain differs")
                elapsed = _integer(phases[phase], label="phase maximum")
                timed_observations = observation_phases[phase]
                expected_schedule = tuple(
                    (direction, repeat)
                    for direction in ("ascending_colex", "descending_colex")
                    for repeat in range(3)
                )
                if (
                    tuple((direction, repeat) for direction, repeat, _ in timed_observations)
                    != expected_schedule
                    or max(value for _, _, value in timed_observations) != elapsed
                ):
                    raise ValueError("projection snapshot timed observations differ")
                ratio, driver = _ratio_for_phase(phase, population, counts, drivers)
                candidate = _ceil_fraction(elapsed, ratio)
                endpoint_rows[population] = {
                    "timed_observations_ns": [
                        {
                            "traversal_order": direction,
                            "repeat_index": repeat,
                            "elapsed_ns": value,
                        }
                        for direction, repeat, value in timed_observations
                    ],
                    "maximum_timed_elapsed_ns": elapsed,
                    "maximum_constituent": driver,
                    "phase_ratio": [ratio.numerator, ratio.denominator],
                    "endpoint_candidate_ns": candidate,
                }
            candidates = {
                population: int(row["endpoint_candidate_ns"])
                for population, row in endpoint_rows.items()
            }
            deciding_value = max(candidates.values())
            deciding = [name for name in POPULATIONS if candidates[name] == deciding_value]
            upper = (
                deciding_value * SAFETY_NUMERATOR + SAFETY_DENOMINATOR - 1
            ) // SAFETY_DENOMINATOR + PHASE_GUARD_NS
            phase_rows.append(
                {
                    "phase": phase,
                    "classification": "laboratory_validation" if phase == VALIDATION_PHASE else "runtime_component",
                    "endpoints": endpoint_rows,
                    "deciding_endpoints": deciding,
                    "phase_upper_ns": upper,
                }
            )
        runtime_total = sum(
            int(row["phase_upper_ns"])
            for row in phase_rows
            if row["classification"] == "runtime_component"
        )
        validation_total = sum(
            int(row["phase_upper_ns"])
            for row in phase_rows
            if row["classification"] == "laboratory_validation"
        )
        peak, headroom, memory_eligible = snapshot.memory[arm]
        projection_eligible = memory_eligible and component_projection_passes(runtime_total)
        for row in phase_rows:
            denominator = runtime_total if row["classification"] == "runtime_component" else validation_total
            class_fraction = Fraction(int(row["phase_upper_ns"]), denominator)
            complete_fraction = Fraction(
                int(row["phase_upper_ns"]), runtime_total + validation_total
            )
            row["fraction_of_class_total"] = [
                class_fraction.numerator,
                class_fraction.denominator,
            ]
            row["fraction_of_complete_laboratory_total"] = [
                complete_fraction.numerator,
                complete_fraction.denominator,
            ]
        counterfactuals: dict[str, dict[str, int]] = {}
        for population in POPULATIONS:
            runtime_counterfactual = sum(
                (
                    int(row["endpoints"][population]["endpoint_candidate_ns"])
                    * SAFETY_NUMERATOR
                    + SAFETY_DENOMINATOR
                    - 1
                )
                // SAFETY_DENOMINATOR
                + PHASE_GUARD_NS
                for row in phase_rows
                if row["classification"] == "runtime_component"
            )
            validation_counterfactual = sum(
                (
                    int(row["endpoints"][population]["endpoint_candidate_ns"])
                    * SAFETY_NUMERATOR
                    + SAFETY_DENOMINATOR
                    - 1
                )
                // SAFETY_DENOMINATOR
                + PHASE_GUARD_NS
                for row in phase_rows
                if row["classification"] == "laboratory_validation"
            )
            counterfactuals[population] = {
                "runtime_component_projection_ns": runtime_counterfactual,
                "laboratory_validation_projection_ns": validation_counterfactual,
                "complete_laboratory_projection_ns": (
                    runtime_counterfactual + validation_counterfactual
                ),
            }
        arms[arm] = {
            "phase_projections": phase_rows,
            "reporting_only_endpoint_counterfactuals": counterfactuals,
            "runtime_component_projection_ns": runtime_total,
            "laboratory_validation_projection_ns": validation_total,
            "complete_laboratory_projection_ns": runtime_total + validation_total,
            "component_ceiling_ns": COMPONENT_CEILING_NS,
            "component_wall_passed": component_projection_passes(runtime_total),
            "symbolic_memory": {
                "peak_live_bytes": peak,
                "headroom_after_reserve_bytes": headroom,
                "eligible": memory_eligible,
                "live_allocation": None,
            },
            "projection_eligible": projection_eligible,
        }
    terminal, eligible = _outcome(arms)
    return {
        "schema_version": "legal-river-quotient-fixed-width-actual45-fit-projection-v1",
        "arms": arms,
        "projection_eligible_arms": eligible,
        "candidate_selected": None,
        "terminal": terminal,
    }


def result_claims() -> dict[str, object]:
    claims = {key: None for key in CLAIM_KEYS}
    claims["candidate_selected"] = None
    claims["truncation_authorized"] = False
    return claims


def build_result(
    input_raw: bytes,
    *,
    source_commit: str,
    dependency_hashes: Mapping[str, str],
) -> dict[str, object]:
    verify_preregistered_contract()
    if (
        not isinstance(source_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
    ):
        raise ValueError("projection source commit differs")
    if not dependency_hashes or any(
        not isinstance(path, str)
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        for path, digest in dependency_hashes.items()
    ):
        raise ValueError("projection dependency hashes differ")
    projection = project_snapshot(extract_calibration_snapshot(input_raw))
    return {
        "schema_version": "legal-river-quotient-fixed-width-actual45-fit-projection-result-v1",
        "source_commit": source_commit,
        "config_sha256": CONFIG_SHA256,
        "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        "dependency_hashes": dict(sorted(dependency_hashes.items())),
        "input": {
            "relative_path": INPUT_RELATIVE_PATH,
            "bytes": INPUT_BYTES,
            "raw_sha256": INPUT_SHA256,
            "consumed": True,
        },
        "projection": projection,
        "claims": result_claims(),
    }


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


__all__ = [
    "ARMS",
    "BATCHED_PHASES",
    "COMPONENT_CEILING_NS",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CORRECTION_CONFIG_RELATIVE_PATH",
    "CORRECTION_CONFIG_SHA256",
    "CalibrationSnapshot",
    "INPUT_BYTES",
    "INPUT_RELATIVE_PATH",
    "INPUT_SHA256",
    "MEMORY",
    "PHASES",
    "POPULATIONS",
    "POSITIONAL_PHASES",
    "RESULT_RELATIVE_PATH",
    "RUNTIME_PHASES",
    "VALIDATION_PHASE",
    "build_result",
    "calibration_snapshot_from_events",
    "canonical_json_bytes",
    "component_projection_passes",
    "extract_calibration_snapshot",
    "load_preregistered_configs",
    "project_snapshot",
    "projection_constituents",
    "result_claims",
    "verify_preregistered_contract",
]
