"""Independent reader for the ADR-0449/ADR-0450 projection result.

This module deliberately does not import the projector.  It rebinds the raw
parent journal and independently reconstructs every retained observation,
integer work count, rational ratio, guarded phase upper, class total, arm
conjunct, and terminal.
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
import subprocess
from typing import Any


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
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
INPUT_PATH = ROOT / INPUT_RELATIVE_PATH

POSITIONAL = "positional"
BATCHED_RRNS = "batched_five_then_four_RRNS"
ARMS = (POSITIONAL, BATCHED_RRNS)
POPULATIONS = ("complete_10", "signed_12")
TARGET = "literal_45"
COMPONENT_CEILING_NS = 14_000_000_000
SAFETY_NUMERATOR = 5
SAFETY_DENOMINATOR = 4
PHASE_GUARD_NS = 1_000_000
VALIDATION_PHASE = "verification_output_transfer_and_exact_differential"

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
    VALIDATION_PHASE,
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
    VALIDATION_PHASE,
    "candidate_cleanup",
)
PHASES = {POSITIONAL: POSITIONAL_PHASES, BATCHED_RRNS: BATCHED_PHASES}
RUNTIME_PHASES = {
    arm: tuple(phase for phase in phases if phase != VALIDATION_PHASE)
    for arm, phases in PHASES.items()
}
MEMORY = {
    POSITIONAL: (13_265_364_040, 1_829_111_736, True),
    BATCHED_RRNS: (13_275_877_664, 1_818_598_112, True),
}
CLAIMS = {
    "actual_45_component_exponent_admission": None,
    "action_clock_result": None,
    "action_result": None,
    "blueprint_result": None,
    "candidate_selected": None,
    "decision_quality_result": None,
    "literal_45_live_allocation": None,
    "literal_45_numeric_value": None,
    "poker_strength_result": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "truncation_authorized": False,
}
DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    CORRECTION_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0448-retain-the-passing-split-runtime-fixed-width-device-preflight.md",
    "docs/decisions/ADR-0449-preregister-the-two-arm-literal-45-fit-projection.md",
    "docs/decisions/ADR-0450-correct-the-fit-projection-runtime-accounting-before-source.md",
    "docs/decisions/ADR-0451-source-seal-the-corrected-literal-45-fit-projector.md",
    "run_legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_result.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_outcome.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_result.py",
    "src/pontius/durable_evidence_journal.py",
    "tests/test_legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "artifacts/work_preflight/.gitattributes",
)
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"


@dataclass(frozen=True, slots=True)
class IndependentSnapshot:
    phase_maxima_ns: Mapping[str, Mapping[str, Mapping[str, int]]]
    phase_observations_ns: Mapping[
        str,
        Mapping[str, Mapping[str, tuple[tuple[str, int, int], ...]]],
    ]
    memory: Mapping[str, tuple[int, int, bool]]


@dataclass(frozen=True, slots=True)
class ProjectionRebinding:
    source_commit: str
    terminal: str
    eligible_arms: tuple[str, ...]
    candidate_selected: None


def _canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(raw):
        if raw[cursor : cursor + 2] == bytes((13, 10)):
            output.append(10)
            cursor += 2
        else:
            output.append(raw[cursor])
            cursor += 1
    return bytes(output)


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"projection reader duplicate JSON key: {key}")
        output[key] = value
    return output


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"projection reader {label} must be an object")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(
            f"projection reader {label} must be an integer at least {minimum}"
        )
    return value


def _digest(value: object, *, label: str, width: int = 64) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(rf"[0-9a-f]{{{width}}}", value) is None
    ):
        raise ValueError(f"projection reader {label} digest differs")
    return value


def _load_config(relative: str, expected_hash: str, schema: str) -> dict[str, object]:
    raw = (ROOT / relative).read_bytes()
    if len(raw) > 1_048_576 or sha256(_canonical_lf(raw)).hexdigest() != expected_hash:
        raise ValueError("projection reader config identity differs")
    parsed = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != schema:
        raise ValueError("projection reader config schema differs")
    return parsed


def _configs() -> tuple[dict[str, object], dict[str, object]]:
    base = _load_config(
        CONFIG_RELATIVE_PATH,
        CONFIG_SHA256,
        "legal-river-quotient-fixed-width-actual45-fit-projection-config-v1",
    )
    correction = _load_config(
        CORRECTION_CONFIG_RELATIVE_PATH,
        CORRECTION_CONFIG_SHA256,
        "legal-river-quotient-fixed-width-actual45-fit-projection-accounting-correction-v2",
    )
    return base, correction


def _constituents(cards: int, width: int, tiles: int) -> dict[str, int]:
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


def _frozen_counts(base: Mapping[str, object]) -> dict[str, dict[str, int]]:
    expected = {
        "complete_10": _constituents(10, 176, 1),
        "signed_12": _constituents(12, 5, 1),
        TARGET: _constituents(45, 176, 3),
    }
    raw = _mapping(base.get("projection_constituent_counts"), label="counts")
    for population, row in expected.items():
        observed = _mapping(raw.get(population), label=f"{population} counts")
        if {key: observed.get(key) for key in row} != row:
            raise ValueError(f"projection reader {population} counts differ")
    return expected


def _drivers(base: Mapping[str, object]) -> dict[str, tuple[str, ...]]:
    raw = _mapping(base.get("phase_driver_contract"), label="drivers")
    output: dict[str, tuple[str, ...]] = {}
    for phase in set(POSITIONAL_PHASES) | set(BATCHED_PHASES):
        names = raw.get(phase)
        if (
            not isinstance(names, list)
            or not names
            or any(not isinstance(name, str) or not name for name in names)
        ):
            raise ValueError(f"projection reader {phase} drivers differ")
        output[phase] = tuple(names)
    return output


def verify_independent_contract() -> None:
    base, correction = _configs()
    counts = _frozen_counts(base)
    drivers = _drivers(base)
    if any(
        any(constituent not in counts[TARGET] for constituent in names)
        for names in drivers.values()
    ):
        raise ValueError("projection reader unknown phase constituent")
    phase_classification = _mapping(
        correction.get("phase_classification"), label="phase classification"
    )
    runtime = _mapping(
        phase_classification.get("runtime_component_phases"), label="runtime phases"
    )
    laboratory = _mapping(
        phase_classification.get("laboratory_validation_phases"),
        label="laboratory phases",
    )
    for arm in ARMS:
        runtime_row = tuple(runtime.get(arm, ()))
        laboratory_row = tuple(laboratory.get(arm, ()))
        if runtime_row != RUNTIME_PHASES[arm] or laboratory_row != (VALIDATION_PHASE,):
            raise ValueError(f"projection reader {arm} phase classes differ")
        membership = Counter((*runtime_row, *laboratory_row))
        if membership != Counter(PHASES[arm]):
            raise ValueError(f"projection reader {arm} phase partition differs")
    action = _mapping(base.get("action_clock_contract"), label="action clock")
    if (
        action.get("controlled_action_wall_ns") != 15_000_000_000
        or action.get("emission_reserve_ns") != 1_000_000_000
        or action.get("maximum_charged_component_work_ns") != COMPONENT_CEILING_NS
    ):
        raise ValueError("projection reader action clock differs")
    calibration = _mapping(base.get("calibration_contract"), label="calibration")
    guarded = _mapping(base.get("guarded_projection"), label="guarded projection")
    corrected = _mapping(
        correction.get("corrected_projection_contract"),
        label="corrected projection",
    )
    if (
        calibration.get("timed_observations_per_arm_population") != 6
        or calibration.get("warmup_observations_per_arm_population") != 1
        or calibration.get("positional_phase_count") != len(POSITIONAL_PHASES)
        or calibration.get("batched_phase_count") != len(BATCHED_PHASES)
        or guarded.get("safety_multiplier_fraction")
        != [SAFETY_NUMERATOR, SAFETY_DENOMINATOR]
        or guarded.get("per_phase_absolute_guard_ns") != PHASE_GUARD_NS
        or corrected.get("maximum_charged_runtime_component_ns")
        != COMPONENT_CEILING_NS
        or corrected.get("laboratory_validation_has_no_action_clock_gate") is not True
    ):
        raise ValueError("projection reader calibration or guard contract differs")
    memory_contract = _mapping(
        base.get("memory_and_width_contract"), label="memory contract"
    )
    peaks = _mapping(memory_contract.get("retained_symbolic_peaks"), label="peaks")
    headrooms = _mapping(
        memory_contract.get("retained_symbolic_headroom_after_reserve"),
        label="headrooms",
    )
    for arm, (peak, headroom, _) in MEMORY.items():
        if peaks.get(arm) != peak or headrooms.get(arm) != headroom:
            raise ValueError(f"projection reader {arm} memory contract differs")


def _phase_elapsed(event: Mapping[str, object], expected: Sequence[str]) -> dict[str, int]:
    partition = _mapping(event.get("phase_partition"), label="phase partition")
    rows = partition.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("projection reader phase count differs")
    output: dict[str, int] = {}
    previous_end: int | None = None
    for name, raw in zip(expected, rows, strict=True):
        row = _mapping(raw, label="phase row")
        if set(row) != {"name", "start_ns", "end_ns", "elapsed_ns"}:
            raise ValueError("projection reader phase fields differ")
        start = _integer(row.get("start_ns"), label="phase start")
        end = _integer(row.get("end_ns"), label="phase end")
        elapsed = _integer(row.get("elapsed_ns"), label="phase elapsed")
        if row.get("name") != name or end - start != elapsed:
            raise ValueError("projection reader phase row differs")
        if previous_end is not None and start != previous_end:
            raise ValueError("projection reader phase partition is not gap-free")
        output[name] = elapsed
        previous_end = end
    if sum(output.values()) != _integer(partition.get("total_ns"), label="phase total"):
        raise ValueError("projection reader phase sum differs")
    return output


def independent_snapshot_from_events(
    candidate_events: Sequence[Mapping[str, object]],
    memory: Mapping[str, tuple[int, int, bool]],
) -> IndependentSnapshot:
    groups: dict[tuple[str, str], list[Mapping[str, object]]] = {
        (arm, population): [] for arm in ARMS for population in POPULATIONS
    }
    for event in candidate_events:
        key = (event.get("arm"), event.get("population"))
        if key not in groups or event.get("exact_verified") is not True:
            raise ValueError("projection reader candidate domain differs")
        groups[(str(key[0]), str(key[1]))].append(event)
    if any(len(rows) != 7 for rows in groups.values()):
        raise ValueError("projection reader candidate cardinality differs")

    maxima: dict[str, dict[str, dict[str, int]]] = {
        arm: {population: {} for population in POPULATIONS} for arm in ARMS
    }
    observations: dict[
        str,
        dict[str, dict[str, tuple[tuple[str, int, int], ...]]],
    ] = {arm: {population: {} for population in POPULATIONS} for arm in ARMS}
    expected_schedule = tuple(
        (direction, repeat)
        for direction in ("ascending_colex", "descending_colex")
        for repeat in range(3)
    )
    for (arm, population), rows in groups.items():
        warmups = [row for row in rows if row.get("schedule_kind") == "warmup"]
        timed = [row for row in rows if row.get("schedule_kind") == "timed"]
        if (
            len(warmups) != 1
            or len(timed) != 6
            or warmups[0].get("traversal_order") != "ascending_colex"
            or warmups[0].get("repeat_index") != 0
        ):
            raise ValueError("projection reader warmup/timed schedule differs")
        if Counter(
            (row.get("traversal_order"), row.get("repeat_index")) for row in timed
        ) != Counter(expected_schedule):
            raise ValueError("projection reader timed schedule differs")
        _phase_elapsed(warmups[0], PHASES[arm])
        ordered = sorted(
            timed,
            key=lambda row: (
                0 if row.get("traversal_order") == "ascending_colex" else 1,
                int(row.get("repeat_index", -1)),
            ),
        )
        parsed = [_phase_elapsed(event, PHASES[arm]) for event in ordered]
        for phase in PHASES[arm]:
            values = tuple(
                (
                    str(event["traversal_order"]),
                    int(event["repeat_index"]),
                    phase_rows[phase],
                )
                for event, phase_rows in zip(ordered, parsed, strict=True)
            )
            if tuple((direction, repeat) for direction, repeat, _ in values) != expected_schedule:
                raise ValueError("projection reader normalized schedule differs")
            observations[arm][population][phase] = values
            maxima[arm][population][phase] = max(value for _, _, value in values)

    normalized_memory: dict[str, tuple[int, int, bool]] = {}
    if set(memory) != set(ARMS):
        raise ValueError("projection reader memory domain differs")
    for arm, row in memory.items():
        if not isinstance(row, tuple) or len(row) != 3 or not isinstance(row[2], bool):
            raise ValueError("projection reader memory row differs")
        normalized_memory[arm] = (
            _integer(row[0], label="memory peak"),
            _integer(row[1], label="memory headroom"),
            row[2],
        )
    return IndependentSnapshot(maxima, observations, normalized_memory)


def extract_independent_snapshot(raw: bytes) -> IndependentSnapshot:
    if type(raw) is not bytes or len(raw) != INPUT_BYTES or sha256(raw).hexdigest() != INPUT_SHA256:
        raise ValueError("projection reader parent artifact identity differs")
    from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes
    from .legal_river_quotient_fixed_width_device_preflight_v3_outcome import (
        assess_device_preflight_v3_outcome_bytes,
    )
    from .legal_river_quotient_fixed_width_device_preflight_v3_result import (
        CAMPAIGN_SHA256,
        PROTOCOL_SHA256,
    )

    outcome = assess_device_preflight_v3_outcome_bytes(raw)
    if outcome.eligible_arms != ARMS or outcome.candidate_selected is not None:
        raise ValueError("projection reader parent outcome differs")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("projection reader parent lifecycle differs")
    payloads = [
        record.body.payload
        for record in recovery.records
        if record.body.kind is JournalRecordKind.OBSERVATION
    ]
    events = [
        _mapping(payload.get("event"), label="candidate event")
        for payload in payloads
        if payload.get("kind") == "candidate_observation"
        and _mapping(payload.get("event"), label="candidate event").get("arm") in ARMS
    ]
    memory_events = [
        _mapping(payload.get("event"), label="memory event")
        for payload in payloads
        if payload.get("kind") == "symbolic_literal_45_memory_liveness"
    ]
    if len(memory_events) != 1:
        raise ValueError("projection reader parent memory event differs")
    memory: dict[str, tuple[int, int, bool]] = {}
    for arm in ARMS:
        row = _mapping(memory_events[0].get(arm), label=f"{arm} memory")
        liveness = _mapping(row.get("liveness"), label=f"{arm} liveness")
        peak = _integer(liveness.get("peak_live_bytes"), label="memory peak")
        total = _integer(liveness.get("device_total_bytes"), label="device total")
        reserve = _integer(liveness.get("device_reserve_bytes"), label="device reserve")
        memory[arm] = (peak, total - reserve - peak, liveness.get("eligible") is True)
    snapshot = independent_snapshot_from_events(events, memory)
    if snapshot.memory != MEMORY:
        raise ValueError("projection reader parent memory receipts differ")
    return snapshot


def _ratio(
    phase: str,
    population: str,
    counts: Mapping[str, Mapping[str, int]],
    drivers: Mapping[str, tuple[str, ...]],
) -> tuple[Fraction, str]:
    rows: list[tuple[Fraction, str]] = []
    for constituent in drivers[phase]:
        target = counts[TARGET][constituent]
        calibration = counts[population][constituent]
        if target and not calibration:
            raise ValueError("projection reader has an unprojectable constituent")
        if target == calibration == 0:
            continue
        rows.append((Fraction(target, calibration), constituent))
    if not rows:
        raise ValueError("projection reader phase has no constituent")
    maximum = max(value for value, _ in rows)
    names = "+".join(sorted(name for value, name in rows if value == maximum))
    return maximum, names


def _ceil_scaled(value: int, ratio: Fraction) -> int:
    return (value * ratio.numerator + ratio.denominator - 1) // ratio.denominator


def _guard(value: int) -> int:
    return (
        value * SAFETY_NUMERATOR + SAFETY_DENOMINATOR - 1
    ) // SAFETY_DENOMINATOR + PHASE_GUARD_NS


def independent_projection(snapshot: IndependentSnapshot) -> dict[str, object]:
    base, _ = _configs()
    counts = _frozen_counts(base)
    drivers = _drivers(base)
    arm_results: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        if set(snapshot.phase_maxima_ns.get(arm, {})) != set(POPULATIONS):
            raise ValueError("projection reader snapshot population domain differs")
        phase_results: list[dict[str, object]] = []
        for phase in PHASES[arm]:
            endpoints: dict[str, dict[str, object]] = {}
            for population in POPULATIONS:
                maxima = snapshot.phase_maxima_ns[arm][population]
                samples = snapshot.phase_observations_ns[arm][population]
                if set(maxima) != set(PHASES[arm]) or set(samples) != set(PHASES[arm]):
                    raise ValueError("projection reader snapshot phase domain differs")
                timed = samples[phase]
                maximum = maxima[phase]
                if len(timed) != 6 or max(value for _, _, value in timed) != maximum:
                    raise ValueError("projection reader snapshot maximum differs")
                ratio, driver = _ratio(phase, population, counts, drivers)
                endpoints[population] = {
                    "timed_observations_ns": [
                        {
                            "traversal_order": direction,
                            "repeat_index": repeat,
                            "elapsed_ns": value,
                        }
                        for direction, repeat, value in timed
                    ],
                    "maximum_timed_elapsed_ns": maximum,
                    "maximum_constituent": driver,
                    "phase_ratio": [ratio.numerator, ratio.denominator],
                    "endpoint_candidate_ns": _ceil_scaled(maximum, ratio),
                }
            endpoint_values = {
                population: int(endpoints[population]["endpoint_candidate_ns"])
                for population in POPULATIONS
            }
            deciding_value = max(endpoint_values.values())
            phase_results.append(
                {
                    "phase": phase,
                    "classification": (
                        "laboratory_validation"
                        if phase == VALIDATION_PHASE
                        else "runtime_component"
                    ),
                    "endpoints": endpoints,
                    "deciding_endpoints": [
                        population
                        for population in POPULATIONS
                        if endpoint_values[population] == deciding_value
                    ],
                    "phase_upper_ns": _guard(deciding_value),
                }
            )
        runtime_total = sum(
            int(row["phase_upper_ns"])
            for row in phase_results
            if row["classification"] == "runtime_component"
        )
        validation_total = sum(
            int(row["phase_upper_ns"])
            for row in phase_results
            if row["classification"] == "laboratory_validation"
        )
        complete_total = runtime_total + validation_total
        for row in phase_results:
            phase_upper = int(row["phase_upper_ns"])
            class_total = (
                runtime_total
                if row["classification"] == "runtime_component"
                else validation_total
            )
            class_fraction = Fraction(phase_upper, class_total)
            complete_fraction = Fraction(phase_upper, complete_total)
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
                _guard(int(row["endpoints"][population]["endpoint_candidate_ns"]))
                for row in phase_results
                if row["classification"] == "runtime_component"
            )
            validation_counterfactual = sum(
                _guard(int(row["endpoints"][population]["endpoint_candidate_ns"]))
                for row in phase_results
                if row["classification"] == "laboratory_validation"
            )
            counterfactuals[population] = {
                "runtime_component_projection_ns": runtime_counterfactual,
                "laboratory_validation_projection_ns": validation_counterfactual,
                "complete_laboratory_projection_ns": (
                    runtime_counterfactual + validation_counterfactual
                ),
            }
        peak, headroom, memory_eligible = snapshot.memory[arm]
        wall_passed = runtime_total <= COMPONENT_CEILING_NS
        arm_results[arm] = {
            "phase_projections": phase_results,
            "reporting_only_endpoint_counterfactuals": counterfactuals,
            "runtime_component_projection_ns": runtime_total,
            "laboratory_validation_projection_ns": validation_total,
            "complete_laboratory_projection_ns": complete_total,
            "component_ceiling_ns": COMPONENT_CEILING_NS,
            "component_wall_passed": wall_passed,
            "symbolic_memory": {
                "peak_live_bytes": peak,
                "headroom_after_reserve_bytes": headroom,
                "eligible": memory_eligible,
                "live_allocation": None,
            },
            "projection_eligible": memory_eligible and wall_passed,
        }
    eligible = [arm for arm in ARMS if arm_results[arm]["projection_eligible"] is True]
    terminal = {
        0: "projection_rejected_before_target_allocation",
        1: "projection_admits_one_arm_for_separate_live_screen",
        2: "projection_admits_two_arms_for_separate_live_screen",
    }[len(eligible)]
    return {
        "schema_version": "legal-river-quotient-fixed-width-actual45-fit-projection-v1",
        "arms": arm_results,
        "projection_eligible_arms": eligible,
        "candidate_selected": None,
        "terminal": terminal,
    }


def _validate_dependencies(source_commit: str, observed: Mapping[str, object]) -> None:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise ValueError("projection reader Git identity differs")
    if set(observed) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("projection reader dependency domain differs")
    resolved = subprocess.run(
        [str(GIT_PATH), "rev-parse", f"{source_commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != source_commit:
        raise ValueError("projection reader source commit differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        expected = _digest(observed.get(relative), label=f"{relative} hash")
        raw = subprocess.run(
            [str(GIT_PATH), "show", f"{source_commit}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        if sha256(_canonical_lf(raw)).hexdigest() != expected:
            raise ValueError(f"projection reader dependency differs: {relative}")


def validate_projection_document(
    document: Mapping[str, object],
    snapshot: IndependentSnapshot,
    *,
    validate_dependencies: bool,
) -> ProjectionRebinding:
    if set(document) != {
        "schema_version",
        "source_commit",
        "config_sha256",
        "correction_config_sha256",
        "dependency_hashes",
        "input",
        "projection",
        "claims",
    }:
        raise ValueError("projection reader result fields differ")
    source_commit = _digest(document.get("source_commit"), label="source commit", width=40)
    if (
        document.get("schema_version")
        != "legal-river-quotient-fixed-width-actual45-fit-projection-result-v1"
        or document.get("config_sha256") != CONFIG_SHA256
        or document.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256
    ):
        raise ValueError("projection reader result identity differs")
    input_row = _mapping(document.get("input"), label="input")
    if dict(input_row) != {
        "relative_path": INPUT_RELATIVE_PATH,
        "bytes": INPUT_BYTES,
        "raw_sha256": INPUT_SHA256,
        "consumed": True,
    }:
        raise ValueError("projection reader input binding differs")
    dependencies = _mapping(document.get("dependency_hashes"), label="dependencies")
    if validate_dependencies:
        _validate_dependencies(source_commit, dependencies)
    else:
        if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS) or any(
            not isinstance(value, str)
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in dependencies.values()
        ):
            raise ValueError("projection reader synthetic dependency domain differs")
    if _mapping(document.get("claims"), label="claims") != CLAIMS:
        raise ValueError("projection reader claims differ")
    expected_projection = independent_projection(snapshot)
    if _mapping(document.get("projection"), label="projection") != expected_projection:
        raise ValueError("projection reader projected evidence differs")
    return ProjectionRebinding(
        source_commit,
        str(expected_projection["terminal"]),
        tuple(expected_projection["projection_eligible_arms"]),
        None,
    )


def rebind_projection_result_bytes(
    result_raw: bytes,
    input_raw: bytes,
) -> ProjectionRebinding:
    if type(result_raw) is not bytes or type(input_raw) is not bytes:
        raise TypeError("projection reader requires immutable bytes")
    document = json.loads(result_raw, object_pairs_hook=_unique_object)
    if not isinstance(document, dict) or _canonical_json_bytes(document) != result_raw:
        raise ValueError("projection reader result is not canonical JSON plus LF")
    verify_independent_contract()
    snapshot = extract_independent_snapshot(input_raw)
    return validate_projection_document(document, snapshot, validate_dependencies=True)


def rebind_projection_result_file(path: Path = RESULT_PATH) -> ProjectionRebinding:
    if not isinstance(path, Path) or path != RESULT_PATH:
        raise ValueError("projection reader result path differs")
    return rebind_projection_result_bytes(path.read_bytes(), INPUT_PATH.read_bytes())


__all__ = [
    "ARMS",
    "BATCHED_PHASES",
    "CLAIMS",
    "DEPENDENCY_RELATIVE_PATHS",
    "IndependentSnapshot",
    "MEMORY",
    "PHASES",
    "POPULATIONS",
    "POSITIONAL_PHASES",
    "ProjectionRebinding",
    "RESULT_PATH",
    "extract_independent_snapshot",
    "independent_projection",
    "independent_snapshot_from_events",
    "rebind_projection_result_bytes",
    "rebind_projection_result_file",
    "validate_projection_document",
    "verify_independent_contract",
]
