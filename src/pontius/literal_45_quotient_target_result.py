"""Standard-library rebinder for the literal-45 quotient owner journal.

The reader is deliberately independent of NumPy, CuPy, and the target
mechanism.  It reconstructs admission, lifecycle, numerical, and release
gates from raw journal fields; stored terminal labels never decide their own
validity.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import comb, isfinite
from pathlib import Path
from typing import Mapping, Sequence

from .durable_evidence_journal import (
    JournalRecordKind,
    recover_journal_bytes,
)


OWNER_PROTOCOL_SHA256 = (
    "a03746c48c4c1e2736d423654219681e27565243663c78fe1763ff3297769efc"
)
RESULT_RELATIVE_PATH = "artifacts/literal_45_quotient_target_v1.jsonl"
SOURCE_SEAL_PARENT_COMMIT = "9fc8b69ee81759b8cf83593adddeb36a47019a14"
CAMPAIGN_SHA256 = sha256(
    (
        OWNER_PROTOCOL_SHA256
        + "|"
        + RESULT_RELATIVE_PATH
        + "|"
        + SOURCE_SEAL_PARENT_COMMIT
    ).encode("ascii")
).hexdigest()
MAXIMUM_ARTIFACT_BYTES = 1_048_576

AVAILABLE_CARDS = 45
SOURCE_CARDS = 6
QUERY_CARDS = 4
SOURCE_LABELS = 90
QUERY_LABELS = 6
SOURCE_RANK = 127
FEATURE_WIDTH = 128
VALIDATION_CHUNK_BYTES = 67_108_864
HOST_NUMERIC_CAP_BYTES = 48_000_000_000
DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
HOST_RESERVE_BYTES = 8_000_000_000
DEVICE_RESERVE_BYTES = 2_000_000_000
HOST_PEAK_BYTES = 9_353_336_216
DEVICE_PEAK_BYTES = 11_755_029_796
SOURCE_REFERENCE_BYTES = 8_340_541_440
COMPATIBLE_REFERENCE_BYTES = 915_425_280
TARGET_WALL_LIMIT_MS = 600_000.0
DEVICE_FREE_RECOVERY_ALLOWANCE_BYTES = 16_777_216
PROCESS_PRIVATE_RECOVERY_ALLOWANCE_BYTES = 268_435_456
HOST_AVAILABLE_RECOVERY_ALLOWANCE_BYTES = 536_870_912

REQUIRED_RUNTIME = {
    "compute_capability": "120",
    "cuda_driver_version": 13_030,
    "cuda_runtime_version": 13_020,
    "cupy_version": "14.2.0",
    "device_name": "NVIDIA GeForce RTX 5080",
    "device_total_bytes": 17_094_475_776,
}

SOURCE_SAMPLE_RANKS = (
    0,
    8_145_059,
    5_342_038,
    4_228_481,
    2_201_283,
    4_711_753,
    6_939_721,
    5_807_274,
    2_769_721,
    2_288_776,
    7_476_024,
    272_683,
    1_670_744,
    2_715_388,
    5_176_110,
    6_960_326,
)
QUERY_SAMPLE_RANKS = (
    0,
    148_994,
    23_812,
    83_359,
    148_110,
    22_497,
    10_679,
    116_159,
)
QUERY_SAMPLE_FEATURES = (0, 1, 2, 31, 63, 95, 126, 127)

TELEMETRY_TRANSITIONS = (
    "before_allocation",
    "forward_allocated",
    "cold_reference_copied",
    "warm_validated",
    "refresh_reference_rebound",
    "refresh_validated",
    "query_reference_rebound",
    "query_validated",
    "direct_validated",
    "query_covector_allocated",
    "forward_dot_complete",
    "forward_released",
    "adjoint_allocated",
    "adjoint_complete",
    "adjoint_reference_rebound",
    "adjoint_repeat_validated",
    "released",
)

_FORWARD_LIMIT = 10_772_495_644
_DIRECT_LIMIT = 10_772_512_764
_FORWARD_DOT_LIMIT = DEVICE_PEAK_BYTES
_FORWARD_RELEASE_LIMIT = 984_015_756
_ADJOINT_LIMIT = 9_645_290_380
PHASE_POOL_LIMITS = {
    "before_allocation": 0,
    "forward_allocated": _FORWARD_LIMIT,
    "cold_reference_copied": _FORWARD_LIMIT,
    "warm_validated": _FORWARD_LIMIT,
    "refresh_reference_rebound": _FORWARD_LIMIT,
    "refresh_validated": _FORWARD_LIMIT,
    "query_reference_rebound": _FORWARD_LIMIT,
    "query_validated": _FORWARD_LIMIT,
    "direct_validated": _DIRECT_LIMIT,
    "query_covector_allocated": _FORWARD_DOT_LIMIT,
    "forward_dot_complete": _FORWARD_DOT_LIMIT,
    "forward_released": _FORWARD_RELEASE_LIMIT,
    "adjoint_allocated": _ADJOINT_LIMIT,
    "adjoint_complete": _ADJOINT_LIMIT,
    "adjoint_reference_rebound": _ADJOINT_LIMIT,
    "adjoint_repeat_validated": _ADJOINT_LIMIT,
    "released": 0,
}

_FORWARD_OWNED = (
    "source_recurrence",
    "compatible",
    "numerator",
    "reach",
    "query_topology",
    "forward_automaton",
    "active_unary",
    "cardinality_offsets",
)
_FORWARD_DOT_OWNED = (*_FORWARD_OWNED, "query_covector")
_ADJOINT_OWNED = (
    "query_covector",
    "cardinality_offsets",
    "adjoint_aggregated",
    "adjoint_recurrence",
    "unique_adjoint",
)
EXPECTED_OWNERSHIP = {
    "before_allocation": (),
    "forward_allocated": _FORWARD_OWNED,
    "cold_reference_copied": _FORWARD_OWNED,
    "warm_validated": _FORWARD_OWNED,
    "refresh_reference_rebound": _FORWARD_OWNED,
    "refresh_validated": _FORWARD_OWNED,
    "query_reference_rebound": _FORWARD_OWNED,
    "query_validated": _FORWARD_OWNED,
    "direct_validated": _FORWARD_OWNED,
    "query_covector_allocated": _FORWARD_DOT_OWNED,
    "forward_dot_complete": _FORWARD_DOT_OWNED,
    "forward_released": ("query_covector", "cardinality_offsets"),
    "adjoint_allocated": _ADJOINT_OWNED,
    "adjoint_complete": _ADJOINT_OWNED,
    "adjoint_reference_rebound": _ADJOINT_OWNED,
    "adjoint_repeat_validated": _ADJOINT_OWNED,
    "released": (),
}

EXPECTED_INVOCATIONS = {
    "source_build_invocations": 4,
    "signed_query_invocations": 6,
    "affine_fold_invocations": 6,
    "adjoint_invocations": 2,
    "direct_scan_invocations": 1,
    "active_unary_allocations": 1,
    "active_unary_overwrites": 2,
}
EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS = 35
EXPECTED_TARGET_SCIENTIFIC_CALLS = sum(
    EXPECTED_INVOCATIONS[field]
    for field in (
        "source_build_invocations",
        "signed_query_invocations",
        "affine_fold_invocations",
        "adjoint_invocations",
        "direct_scan_invocations",
    )
)

ALLOCATION_BIRTH_ORDER = (
    "host_fixture",
    "host_refreshed_unary",
    "host_query_unary",
    "device_source_recurrence",
    "device_compatible_queries",
    "device_query_numerator",
    "device_query_reach",
    "device_source_pairings",
    "device_pair_to_hand",
    "device_active_unary",
    "device_mode_factors",
    "device_unary_offsets",
    "device_cardinality_offsets",
    *(f"device_automaton_transition_{index}" for index in range(5)),
    "device_automaton_terminal_values",
    "device_mixture",
    "device_query_masks",
    "device_query_hand_indices",
    "host_large_reference_buffer",
    "host_compatible_reference_buffer",
    "host_scalar_reference_buffer",
    "host_validation_staging",
    "device_direct_source_ranks",
    "device_sample_workspace",
    "device_direct_query_masks",
    "device_direct_features",
    "device_direct_outputs",
    "device_query_covectors",
    "device_adjoint_recurrence",
    "device_adjoint_aggregated_queries",
    "device_unique_adjoint",
)
if len(ALLOCATION_BIRTH_ORDER) != EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS:
    raise AssertionError("literal-45 allocation-birth order drifted")

_ZERO_INVOCATIONS = {field: 0 for field in EXPECTED_INVOCATIONS}
_FORWARD_READY_INVOCATIONS = {
    **_ZERO_INVOCATIONS,
    "active_unary_allocations": 1,
}
_QUERY_VALIDATED_INVOCATIONS = {
    **EXPECTED_INVOCATIONS,
    "adjoint_invocations": 0,
    "direct_scan_invocations": 0,
}
_DIRECT_VALIDATED_INVOCATIONS = {
    **_QUERY_VALIDATED_INVOCATIONS,
    "direct_scan_invocations": 1,
}

ALLOCATION_BIRTH_LAST_TRANSITION = {
    **{birth: "before_allocation" for birth in ALLOCATION_BIRTH_ORDER[:22]},
    **{birth: "forward_allocated" for birth in ALLOCATION_BIRTH_ORDER[22:26]},
    **{birth: "query_validated" for birth in ALLOCATION_BIRTH_ORDER[26:31]},
    "device_query_covectors": "direct_validated",
    **{birth: "forward_released" for birth in ALLOCATION_BIRTH_ORDER[32:]},
}
ALLOCATION_BIRTH_INVOCATIONS = {
    **{birth: _ZERO_INVOCATIONS for birth in ALLOCATION_BIRTH_ORDER[:22]},
    **{
        birth: _FORWARD_READY_INVOCATIONS
        for birth in ALLOCATION_BIRTH_ORDER[22:26]
    },
    **{
        birth: _QUERY_VALIDATED_INVOCATIONS
        for birth in ALLOCATION_BIRTH_ORDER[26:31]
    },
    "device_query_covectors": _DIRECT_VALIDATED_INVOCATIONS,
    **{
        birth: _DIRECT_VALIDATED_INVOCATIONS
        for birth in ALLOCATION_BIRTH_ORDER[32:]
    },
}
ALLOCATION_BIRTH_ATTEMPTS = {
    birth: index + 1 for index, birth in enumerate(ALLOCATION_BIRTH_ORDER)
}

ERROR_LIMITS = {
    "source_sample_absolute": 2e-12,
    "direct_query_absolute": 2e-8,
    "direct_query_relative": 2e-11,
    "affine_sample_absolute": 2e-10,
    "dot_product_absolute": 2e-8,
    "dot_product_relative": 1e-10,
}

CLAIMS = {
    "action_clock_result": None,
    "action_result": None,
    "decision_quality_result": None,
    "literal_45_card_result": "journal_terminal_only",
    "poker_strength_result": None,
    "solver_iteration_result": None,
    "truncation_authorized": False,
}

_TARGET_FIELDS = {
    "schema_version",
    "protocol_sha256",
    "claims",
    "geometry",
    "model",
    "runtime",
    "admission",
    "telemetry",
    "work",
    "observed_invocations",
    "counters",
    "identities",
    "errors_hex",
    "timings_hex",
    "wall_hex",
    "chunks",
    "digests",
    "allocation_failure",
}


def _blank_scientific_payload_matches(
    target: Mapping[str, object],
    *,
    invocations: Mapping[str, int],
) -> bool:
    return (
        target["work"] == target_work()
        and target["observed_invocations"] == invocations
        and target["identities"]
        == {
            "warm_byte_identity": None,
            "source_refresh_byte_identity": None,
            "query_only_byte_identity": None,
            "query_only_source_preserved": None,
            "query_only_compatible_preserved": None,
            "adjoint_byte_identity": None,
            "forward_dot_left": None,
            "forward_dot_right": None,
            "transpose_dot_left": None,
            "transpose_dot_right": None,
        }
        and target["errors_hex"] == {field: None for field in ERROR_LIMITS}
        and target["timings_hex"] == {}
        and target["chunks"] == {}
        and target["digests"] == {}
    )


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            dict(payload),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


def _digest(value: object, *, label: str, length: int = 64) -> str:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is not a lowercase hexadecimal digest")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} is not an integer at or above {minimum}")
    return value


def _float_hex(value: object, *, label: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"{label} is not hexadecimal Float64 text")
    try:
        parsed = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is invalid hexadecimal Float64 text") from error
    if not isfinite(parsed) or parsed.hex() != value:
        raise ValueError(f"{label} is nonfinite or noncanonical")
    return parsed


def target_geometry() -> dict[str, int]:
    return {
        "available_cards": AVAILABLE_CARDS,
        "hand_width": comb(AVAILABLE_CARDS, 2),
        "source_occupancies": comb(AVAILABLE_CARDS, SOURCE_CARDS),
        "query_occupancies": comb(AVAILABLE_CARDS, QUERY_CARDS),
        "labeled_query_records": comb(AVAILABLE_CARDS, QUERY_CARDS)
        * QUERY_LABELS,
        "source_recurrence_rows": sum(
            comb(AVAILABLE_CARDS, width) for width in range(SOURCE_CARDS + 1)
        ),
        "adjoint_recurrence_rows": sum(
            comb(AVAILABLE_CARDS, width) for width in range(QUERY_CARDS + 1)
        ),
        "source_rank": SOURCE_RANK,
        "feature_width": FEATURE_WIDTH,
    }


def target_work() -> dict[str, int]:
    geometry = target_geometry()
    source = geometry["source_occupancies"]
    queries = geometry["labeled_query_records"]
    source_edges = sum(
        comb(AVAILABLE_CARDS, level) * (AVAILABLE_CARDS - level)
        for level in range(SOURCE_CARDS)
    )
    adjoint_edges = sum(
        comb(AVAILABLE_CARDS, level) * (AVAILABLE_CARDS - level)
        for level in range(QUERY_CARDS)
    )
    signed_terms = queries * (1 << QUERY_CARDS)
    return {
        "source_pairing_visits_per_build": source * SOURCE_LABELS,
        "source_zero_writes_per_build": source * FEATURE_WIDTH,
        "recurrence_edges_per_build": source_edges,
        "recurrence_scalar_additions_per_build": source_edges * FEATURE_WIDTH,
        "signed_terms_per_query": signed_terms,
        "signed_scalar_additions_per_query": signed_terms * FEATURE_WIDTH,
        "affine_state_folds_per_query": queries * SOURCE_RANK,
        "adjoint_label_additions_per_pass": (
            geometry["query_occupancies"] * (QUERY_LABELS - 1) * FEATURE_WIDTH
        ),
        "adjoint_recurrence_additions_per_pass": adjoint_edges * FEATURE_WIDTH,
        "adjoint_signed_additions_per_pass": (
            source
            * sum(comb(AVAILABLE_CARDS, level) for level in range(QUERY_CARDS + 1))
            * FEATURE_WIDTH
        ),
        **EXPECTED_INVOCATIONS,
    }


def chunk_spans(total_bytes: int) -> tuple[tuple[int, int], ...]:
    _integer(total_bytes, label="chunked byte count")
    return tuple(
        (start, min(total_bytes, start + VALIDATION_CHUNK_BYTES))
        for start in range(0, total_bytes, VALIDATION_CHUNK_BYTES)
    )


def _spans(value: object, *, label: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, list):
        raise TypeError(f"{label} spans are not a list")
    result: list[tuple[int, int]] = []
    for index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError(f"{label} span {index} is malformed")
        result.append(
            (
                _integer(row[0], label=f"{label} span start"),
                _integer(row[1], label=f"{label} span stop"),
            )
        )
    return tuple(result)


def _telemetry_rows(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("target telemetry is empty or not a list")
    expected_fields = {
        "transition",
        "owned_arrays",
        "pool_used_bytes",
        "pool_total_bytes",
        "pinned_free_blocks",
        "device_free_bytes",
        "device_total_bytes",
        "host_available_physical_bytes",
        "process_working_set_bytes",
        "process_private_bytes",
        "modeled_pool_limit_bytes",
    }
    rows: list[dict[str, object]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or set(raw) != expected_fields:
            raise ValueError(f"target telemetry row {index} has wrong fields")
        transition = raw["transition"]
        if not isinstance(transition, str) or transition not in TELEMETRY_TRANSITIONS:
            raise ValueError(f"target telemetry row {index} has unknown transition")
        owned = raw["owned_arrays"]
        if not isinstance(owned, list) or any(
            not isinstance(item, str) or not item for item in owned
        ):
            raise ValueError(f"target telemetry row {index} has invalid ownership")
        row = {"transition": transition, "owned_arrays": list(owned)}
        for field in expected_fields - {"transition", "owned_arrays"}:
            row[field] = _integer(raw[field], label=f"telemetry {field}")
        rows.append(row)
    return tuple(rows)


def _release_gate(rows: Sequence[Mapping[str, object]]) -> bool:
    if not rows or rows[-1]["transition"] != "released":
        return False
    before = rows[0]
    after = rows[-1]
    return (
        after["pool_used_bytes"] == 0
        and after["pool_total_bytes"] == 0
        and after["pinned_free_blocks"] == 0
        and after["device_total_bytes"] == before["device_total_bytes"]
        and int(after["device_free_bytes"])
        + DEVICE_FREE_RECOVERY_ALLOWANCE_BYTES
        >= int(before["device_free_bytes"])
        and int(after["process_private_bytes"])
        <= int(before["process_private_bytes"])
        + PROCESS_PRIVATE_RECOVERY_ALLOWANCE_BYTES
        and int(after["host_available_physical_bytes"])
        + HOST_AVAILABLE_RECOVERY_ALLOWANCE_BYTES
        >= int(before["host_available_physical_bytes"])
    )


@dataclass(frozen=True, slots=True)
class TargetObservationRebinding:
    terminal: str
    reason: str
    passed: bool
    gates: Mapping[str, bool]


def reconstruct_target_observation(
    target: Mapping[str, object],
) -> TargetObservationRebinding:
    """Rebuild the target terminal from primitive observations only."""

    if not isinstance(target, Mapping) or set(target) != _TARGET_FIELDS:
        raise ValueError("literal-45 target fields differ from the source seal")
    if target["schema_version"] != "literal-45-quotient-target-observation-v1":
        raise ValueError("literal-45 target schema drifted")
    if target["protocol_sha256"] != OWNER_PROTOCOL_SHA256:
        raise ValueError("literal-45 target protocol drifted")
    if target["claims"] != CLAIMS:
        raise ValueError("literal-45 target claims widened")
    if target["geometry"] != target_geometry():
        raise ValueError("literal-45 target geometry drifted")

    model = target["model"]
    expected_model = {
        "host_numeric_cap_bytes": HOST_NUMERIC_CAP_BYTES,
        "device_numeric_cap_bytes": DEVICE_NUMERIC_CAP_BYTES,
        "host_reserve_bytes": HOST_RESERVE_BYTES,
        "device_reserve_bytes": DEVICE_RESERVE_BYTES,
        "host_peak_bytes": HOST_PEAK_BYTES,
        "device_peak_bytes": DEVICE_PEAK_BYTES,
        "source_reference_bytes": SOURCE_REFERENCE_BYTES,
        "compatible_reference_bytes": COMPATIBLE_REFERENCE_BYTES,
        "source_reference_chunks": 125,
        "compatible_reference_chunks": 14,
        "phase_pool_limits": PHASE_POOL_LIMITS,
    }
    if model != expected_model:
        raise ValueError("literal-45 allocation model drifted")

    runtime = target["runtime"]
    if not isinstance(runtime, dict) or set(runtime) != set(REQUIRED_RUNTIME):
        raise ValueError("literal-45 runtime fields drifted")
    runtime_identity = runtime == REQUIRED_RUNTIME

    admission = target["admission"]
    admission_fields = {
        "host_total_physical_bytes",
        "host_available_physical_bytes",
        "process_working_set_bytes",
        "process_private_bytes",
        "device_free_bytes",
        "device_total_bytes",
        "pool_used_bytes",
        "pool_total_bytes",
        "pinned_free_blocks",
        "target_numeric_allocation_calls",
        "target_scientific_call_count",
    }
    if not isinstance(admission, dict) or set(admission) != admission_fields:
        raise ValueError("literal-45 admission fields drifted")
    admission_values = {
        key: _integer(value, label=f"admission {key}")
        for key, value in admission.items()
    }
    admission_gates = {
        "fixed_host_model": HOST_PEAK_BYTES <= HOST_NUMERIC_CAP_BYTES,
        "fixed_device_model": DEVICE_PEAK_BYTES <= DEVICE_NUMERIC_CAP_BYTES,
        "live_host_reserve": (
            HOST_PEAK_BYTES + HOST_RESERVE_BYTES
            <= admission_values["host_available_physical_bytes"]
        ),
        "live_device_reserve": (
            DEVICE_PEAK_BYTES + DEVICE_RESERVE_BYTES
            <= admission_values["device_free_bytes"]
        ),
        "runtime_identity": runtime_identity
        and admission_values["device_total_bytes"]
        == REQUIRED_RUNTIME["device_total_bytes"],
        "empty_default_pool": admission_values["pool_used_bytes"] == 0
        and admission_values["pool_total_bytes"] == 0,
        "empty_pinned_pool": admission_values["pinned_free_blocks"] == 0,
        "zero_pre_admission_target_allocations": (
            admission_values["target_numeric_allocation_calls"] == 0
        ),
        "zero_pre_admission_scientific_calls": (
            admission_values["target_scientific_call_count"] == 0
        ),
    }
    admission_pass = all(admission_gates.values())
    rows = _telemetry_rows(target["telemetry"])
    if rows[0]["transition"] != "before_allocation":
        raise ValueError("literal-45 telemetry does not begin before allocation")
    if rows[0]["owned_arrays"] != []:
        raise ValueError("literal-45 pre-allocation telemetry owns target arrays")
    before_matches_admission = all(
        rows[0][field] == admission_values[field]
        for field in (
            "pool_used_bytes",
            "pool_total_bytes",
            "pinned_free_blocks",
            "device_free_bytes",
            "device_total_bytes",
            "host_available_physical_bytes",
            "process_working_set_bytes",
            "process_private_bytes",
        )
    )

    counters = target["counters"]
    counter_fields = {
        "target_execution_calls",
        "target_numeric_allocation_calls",
        "target_scientific_call_count",
    }
    if not isinstance(counters, dict) or set(counters) != counter_fields:
        raise ValueError("literal-45 counter fields drifted")
    counters = {
        key: _integer(value, label=f"target counter {key}")
        for key, value in counters.items()
    }
    if counters["target_execution_calls"] != 1:
        raise ValueError("literal-45 owner did not make exactly one target call")

    wall = _float_hex(target["wall_hex"], label="literal-45 target wall")
    common_gates = {
        **admission_gates,
        "before_telemetry_matches_admission": before_matches_admission,
        "before_ownership_empty": rows[0]["owned_arrays"] == [],
        "target_wall": 0.0 <= wall <= TARGET_WALL_LIMIT_MS,
    }
    if not admission_pass:
        blank_after_rejection = _blank_scientific_payload_matches(
            target,
            invocations=_ZERO_INVOCATIONS,
        )
        zero_after_rejection = (
            counters["target_numeric_allocation_calls"] == 0
            and counters["target_scientific_call_count"] == 0
            and len(rows) == 1
            and target["allocation_failure"] is None
            and blank_after_rejection
        )
        gates = {
            **common_gates,
            "stop_after_live_rejection": zero_after_rejection,
        }
        if not zero_after_rejection:
            raise ValueError("literal-45 owner continued after live rejection")
        failed = sorted(name for name, passed in admission_gates.items() if not passed)
        terminal = (
            "live_admission_rejected"
            if common_gates["target_wall"]
            else "infrastructure_failure"
        )
        return TargetObservationRebinding(
            terminal=terminal,
            reason=(
                "admission:" + ",".join(failed)
                if terminal == "live_admission_rejected"
                else "laboratory_wall_guard_crossed"
            ),
            passed=False,
            gates=gates,
        )

    allocation_failure = target["allocation_failure"]
    if allocation_failure is not None:
        expected_fields = {
            "birth",
            "failure_type",
            "message",
            "last_completed_transition",
        }
        if not isinstance(allocation_failure, dict) or set(allocation_failure) != expected_fields:
            raise ValueError("literal-45 allocation failure is malformed")
        for field in ("birth", "failure_type", "message"):
            if not isinstance(allocation_failure[field], str) or not allocation_failure[field]:
                raise ValueError("literal-45 allocation failure text is empty")
        last = allocation_failure["last_completed_transition"]
        if not isinstance(last, str) or last not in TELEMETRY_TRANSITIONS:
            raise ValueError("literal-45 allocation failure transition is invalid")
        birth = allocation_failure["birth"]
        if birth not in ALLOCATION_BIRTH_LAST_TRANSITION:
            raise ValueError("literal-45 allocation failure birth is not frozen")
        if last != ALLOCATION_BIRTH_LAST_TRANSITION[birth]:
            raise ValueError("literal-45 allocation failure birth/transition drifted")
        names = tuple(row["transition"] for row in rows)
        prefix_stop = TELEMETRY_TRANSITIONS.index(last) + 1
        prefix = TELEMETRY_TRANSITIONS[:prefix_stop]
        lifecycle = names == prefix or names == (*prefix, "released")
        partial_telemetry = all(
            tuple(row["owned_arrays"])
            == EXPECTED_OWNERSHIP[row["transition"]]
            and row["modeled_pool_limit_bytes"]
            == PHASE_POOL_LIMITS[row["transition"]]
            and int(row["pool_used_bytes"])
            <= PHASE_POOL_LIMITS[row["transition"]]
            and int(row["pool_total_bytes"]) <= DEVICE_PEAK_BYTES
            for row in rows
        )
        expected_partial_invocations = ALLOCATION_BIRTH_INVOCATIONS[birth]
        partial_work = _blank_scientific_payload_matches(
            target,
            invocations=expected_partial_invocations,
        )
        expected_partial_scientific_calls = sum(
            expected_partial_invocations[field]
            for field in (
                "source_build_invocations",
                "signed_query_invocations",
                "affine_fold_invocations",
                "adjoint_invocations",
                "direct_scan_invocations",
            )
        )
        partial_counter_identity = (
            counters["target_numeric_allocation_calls"]
            == ALLOCATION_BIRTH_ATTEMPTS[birth]
            and counters["target_scientific_call_count"]
            == expected_partial_scientific_calls
        )
        release = _release_gate(rows)
        gates = {
            **common_gates,
            "allocation_prefix": lifecycle and partial_telemetry,
            "allocation_cleanup": release,
            "allocation_attempt_identity": partial_counter_identity,
            "partial_invocations_exact_and_future_blank": partial_work,
        }
        terminal = (
            "allocation_rejected"
            if lifecycle
            and partial_telemetry
            and partial_work
            and partial_counter_identity
            and release
            and common_gates["target_wall"]
            else "infrastructure_failure"
        )
        return TargetObservationRebinding(
            terminal=terminal,
            reason=f"allocation:{allocation_failure['birth']}",
            passed=False,
            gates=gates,
        )

    names = tuple(row["transition"] for row in rows)
    complete_telemetry = names == TELEMETRY_TRANSITIONS
    telemetry_model = complete_telemetry and all(
        row["modeled_pool_limit_bytes"] == PHASE_POOL_LIMITS[row["transition"]]
        and int(row["pool_used_bytes"])
        <= PHASE_POOL_LIMITS[row["transition"]]
        and int(row["pool_total_bytes"]) <= DEVICE_PEAK_BYTES
        and int(row["device_total_bytes"])
        == REQUIRED_RUNTIME["device_total_bytes"]
        for row in rows
    )
    ownership_identity = complete_telemetry and all(
        tuple(row["owned_arrays"]) == EXPECTED_OWNERSHIP[row["transition"]]
        for row in rows
    )
    release = _release_gate(rows)

    if target["work"] != target_work():
        raise ValueError("literal-45 independent work ledger drifted")
    if target["observed_invocations"] != EXPECTED_INVOCATIONS:
        invocation_identity = False
    else:
        invocation_identity = True

    identities = target["identities"]
    expected_identity_fields = {
        "warm_byte_identity",
        "source_refresh_byte_identity",
        "query_only_byte_identity",
        "query_only_source_preserved",
        "query_only_compatible_preserved",
        "adjoint_byte_identity",
        "forward_dot_left",
        "forward_dot_right",
        "transpose_dot_left",
        "transpose_dot_right",
    }
    if not isinstance(identities, dict) or set(identities) != expected_identity_fields:
        raise ValueError("literal-45 identity observations drifted")
    byte_identities = all(
        identities[field] is True
        for field in expected_identity_fields
        if field.endswith("identity") or field.endswith("preserved")
    )
    operand_roles = (
        identities["forward_dot_left"],
        identities["forward_dot_right"],
        identities["transpose_dot_left"],
        identities["transpose_dot_right"],
    ) == (
        "host_compatible_reference",
        "device_query_covector",
        "host_source_reference",
        "device_unique_adjoint",
    )

    errors = target["errors_hex"]
    if not isinstance(errors, dict) or set(errors) != set(ERROR_LIMITS):
        raise ValueError("literal-45 error fields drifted")
    parsed_errors = {
        field: _float_hex(value, label=f"literal-45 {field}")
        for field, value in errors.items()
    }
    numerical = all(
        0.0 <= parsed_errors[field] <= limit
        for field, limit in ERROR_LIMITS.items()
    )

    timings = target["timings_hex"]
    expected_timing_fields = {
        "cold",
        "warm",
        "source_refresh",
        "source_refresh_repeat",
        "query_only",
        "query_only_repeat",
        "direct",
        "adjoint",
        "adjoint_repeat",
    }
    if not isinstance(timings, dict) or set(timings) != expected_timing_fields:
        raise ValueError("literal-45 timing fields drifted")
    timings_finite = all(
        _float_hex(value, label=f"literal-45 timing {field}") >= 0.0
        for field, value in timings.items()
    )

    chunks = target["chunks"]
    if not isinstance(chunks, dict) or set(chunks) != {
        "source_reference",
        "compatible_forward_dot",
        "source_transpose_dot",
    }:
        raise ValueError("literal-45 chunk fields drifted")
    chunk_identity = (
        _spans(chunks["source_reference"], label="source reference")
        == chunk_spans(SOURCE_REFERENCE_BYTES)
        and _spans(chunks["compatible_forward_dot"], label="compatible dot")
        == chunk_spans(COMPATIBLE_REFERENCE_BYTES)
        and _spans(chunks["source_transpose_dot"], label="source transpose")
        == chunk_spans(SOURCE_REFERENCE_BYTES)
    )

    digests = target["digests"]
    expected_digest_fields = {
        "source_before_adjoint",
        "compatible",
        "query_covector",
        "unique_adjoint",
    }
    if not isinstance(digests, dict) or set(digests) != expected_digest_fields:
        raise ValueError("literal-45 reporting digests drifted")
    for field, value in digests.items():
        _digest(value, label=f"literal-45 reporting digest {field}")

    gates = {
        **common_gates,
        "complete_telemetry": complete_telemetry,
        "telemetry_within_model": telemetry_model,
        "ownership_identity": ownership_identity,
        "release_complete": release,
        "exact_work_identity": target["work"] == target_work(),
        "invocation_identity": invocation_identity,
        "one_active_unary": (
            target["observed_invocations"].get("active_unary_allocations") == 1
            and target["observed_invocations"].get("active_unary_overwrites") == 2
        ),
        "byte_identities": byte_identities,
        "dot_operand_roles": operand_roles,
        "numerical_thresholds": numerical,
        "chunk_cover_and_counts": chunk_identity,
        "all_numeric_finite": timings_finite,
        "scientific_calls_recorded": counters["target_scientific_call_count"] > 0,
        "target_allocation_call_identity": (
            counters["target_numeric_allocation_calls"]
            == EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS
        ),
        "target_scientific_call_identity": (
            counters["target_scientific_call_count"]
            == EXPECTED_TARGET_SCIENTIFIC_CALLS
        ),
    }
    if not release or not common_gates["target_wall"]:
        terminal = "infrastructure_failure"
        reason = (
            "release_gate_rejected"
            if not release
            else "laboratory_wall_guard_crossed"
        )
    elif all(gates.values()):
        terminal = "completed_pass"
        reason = "all_literal_45_target_gates_passed"
    else:
        terminal = "scientific_rejected"
        reason = "scientific_conjunct_rejected"
    return TargetObservationRebinding(
        terminal=terminal,
        reason=reason,
        passed=terminal == "completed_pass",
        gates=gates,
    )


@dataclass(frozen=True, slots=True)
class Literal45JournalRebinding:
    terminal: str
    reason: str
    passed: bool
    source_commit: str | None
    config_sha256: str | None
    target: TargetObservationRebinding | None
    journal_sha256: str
    journal_byte_count: int


def rebind_literal_45_quotient_target_journal(
    raw: bytes,
    *,
    expected_config_sha256: str | None = None,
) -> Literal45JournalRebinding:
    if not isinstance(raw, bytes):
        raise TypeError("literal-45 journal must be immutable bytes")
    if len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("literal-45 journal exceeds the artifact ceiling")
    if expected_config_sha256 is not None:
        _digest(expected_config_sha256, label="expected literal-45 config")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=OWNER_PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete:
        reason = recovery.failure.reason if recovery.failure else "missing terminal"
        raise ValueError(f"literal-45 journal is incomplete: {reason}")
    records = recovery.records
    if len(records) not in (2, 3):
        raise ValueError("literal-45 journal must be header/terminal or header/observation/terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("literal-45 journal does not begin with a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("literal-45 journal does not end with a terminal")

    header = records[0].body.payload
    expected_header = {
        "schema_version": "literal-45-quotient-owner-header-v1",
        "owner_protocol_sha256": OWNER_PROTOCOL_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "source_seal_parent_commit": SOURCE_SEAL_PARENT_COMMIT,
        "claims": CLAIMS,
    }
    if header != expected_header:
        raise ValueError("literal-45 durable header drifted")
    if records[0].body.semantic_identity_sha256 != _semantic_digest(header):
        raise ValueError("literal-45 header semantic identity drifted")

    target_rebinding: TargetObservationRebinding | None = None
    source_commit: str | None = None
    config_sha256: str | None = None
    observation_identity: str | None = None
    if len(records) == 3:
        if records[1].body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("literal-45 middle record is not an observation")
        observation = records[1].body.payload
        expected_fields = {
            "schema_version",
            "config_sha256",
            "source_commit",
            "source_dirty",
            "target",
        }
        if not isinstance(observation, dict) or set(observation) != expected_fields:
            raise ValueError("literal-45 owner observation fields drifted")
        if observation["schema_version"] != "literal-45-quotient-owner-observation-v1":
            raise ValueError("literal-45 owner observation schema drifted")
        config_sha256 = _digest(
            observation["config_sha256"], label="literal-45 observation config"
        )
        source_commit = _digest(
            observation["source_commit"],
            label="literal-45 observation commit",
            length=40,
        )
        if observation["source_dirty"] is not False:
            raise ValueError("literal-45 observation was not made from a clean source")
        if expected_config_sha256 is not None and config_sha256 != expected_config_sha256:
            raise ValueError("literal-45 observation config differs from expected")
        target_rebinding = reconstruct_target_observation(observation["target"])
        observation_identity = _semantic_digest(observation)
        if records[1].body.semantic_identity_sha256 != observation_identity:
            raise ValueError("literal-45 observation semantic identity drifted")

    terminal = records[-1].body.payload
    terminal_fields = {
        "schema_version",
        "terminal",
        "reason",
        "passed",
        "observation_semantic_identity_sha256",
        "claims",
    }
    if not isinstance(terminal, dict) or set(terminal) != terminal_fields:
        raise ValueError("literal-45 terminal fields drifted")
    if terminal["schema_version"] != "literal-45-quotient-owner-terminal-v1":
        raise ValueError("literal-45 terminal schema drifted")
    if terminal["claims"] != CLAIMS:
        raise ValueError("literal-45 terminal claims widened")
    if records[-1].body.semantic_identity_sha256 != _semantic_digest(terminal):
        raise ValueError("literal-45 terminal semantic identity drifted")
    if terminal["observation_semantic_identity_sha256"] != observation_identity:
        raise ValueError("literal-45 terminal observation binding drifted")
    allowed = {
        "completed_pass",
        "live_admission_rejected",
        "allocation_rejected",
        "scientific_rejected",
        "infrastructure_failure",
    }
    if terminal["terminal"] not in allowed:
        raise ValueError("literal-45 terminal class is unknown")
    if not isinstance(terminal["reason"], str) or not terminal["reason"]:
        raise ValueError("literal-45 terminal reason is empty")
    if terminal["passed"] is not (terminal["terminal"] == "completed_pass"):
        raise ValueError("literal-45 terminal pass flag drifted")
    if target_rebinding is None:
        if terminal["terminal"] != "infrastructure_failure":
            raise ValueError("literal-45 pre-observation terminal is not infrastructure failure")
    elif (
        terminal["terminal"] != target_rebinding.terminal
        or terminal["reason"] != target_rebinding.reason
        or terminal["passed"] is not target_rebinding.passed
    ):
        raise ValueError("literal-45 stored terminal differs from reconstructed authority")

    return Literal45JournalRebinding(
        terminal=str(terminal["terminal"]),
        reason=str(terminal["reason"]),
        passed=bool(terminal["passed"]),
        source_commit=source_commit,
        config_sha256=config_sha256,
        target=target_rebinding,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
    )


def rebind_literal_45_quotient_target_file(
    path: Path,
    *,
    expected_config_sha256: str | None = None,
) -> Literal45JournalRebinding:
    if not isinstance(path, Path):
        raise TypeError("literal-45 result path must be a Path")
    return rebind_literal_45_quotient_target_journal(
        path.read_bytes(), expected_config_sha256=expected_config_sha256
    )


__all__ = [
    "ALLOCATION_BIRTH_ATTEMPTS",
    "ALLOCATION_BIRTH_INVOCATIONS",
    "ALLOCATION_BIRTH_ORDER",
    "CLAIMS",
    "CAMPAIGN_SHA256",
    "ALLOCATION_BIRTH_LAST_TRANSITION",
    "EXPECTED_INVOCATIONS",
    "EXPECTED_OWNERSHIP",
    "EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS",
    "EXPECTED_TARGET_SCIENTIFIC_CALLS",
    "Literal45JournalRebinding",
    "MAXIMUM_ARTIFACT_BYTES",
    "OWNER_PROTOCOL_SHA256",
    "PHASE_POOL_LIMITS",
    "QUERY_SAMPLE_FEATURES",
    "QUERY_SAMPLE_RANKS",
    "RESULT_RELATIVE_PATH",
    "SOURCE_SAMPLE_RANKS",
    "TELEMETRY_TRANSITIONS",
    "TargetObservationRebinding",
    "chunk_spans",
    "rebind_literal_45_quotient_target_file",
    "rebind_literal_45_quotient_target_journal",
    "reconstruct_target_observation",
    "target_geometry",
    "target_work",
]
