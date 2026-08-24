"""Solver-free ADR-0345 owner for the retained responder-raise keystone.

The prospective ADR-0344 runner is permanently closed.  This module reads
only its exact retained JSON artifact, rebinds the source-sealed inputs, and
publishes the finite semantic result without constructing a game or invoking
an optimizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


ADR0345_INVOCATION_SOURCE_COMMIT = (
    "ff2b8ced243f0eb0d3a7fcffebf2287c4c102aa2"
)
ADR0345_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/responder-raise-semantics-keystone-v1.json"
)
ADR0345_ARTIFACT_BYTES = 7_400
ADR0345_ARTIFACT_SHA256 = (
    "a7cbb0efca87ad3bf9e2a2105d10aa137daf68a763b68518d68e893bfc74be11"
)
ADR0345_CONFIG_RELATIVE_PATH = (
    "experiments/configs/responder-raise-semantics-keystone-v1.json"
)
ADR0345_CONFIG_SHA256 = (
    "5a9899ea0ced855cdb6fa30183ccab9b3235470603d7d45f688355eac15dcafd"
)
ADR0345_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0345_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0345_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0345_GAME_PROVENANCE_SHA256 = (
    "8f70f4d0121979959f91f0ca308aaaa77204132e8718b0d807d7ce7c6a7498d1"
)
ADR0345_OBJECTIVE_HEX = "0x1.2aaaaaaaaaaaap+1"
ADR0345_LOWER_BOUND_HEX = "0x1.2aaaaaaaaaaacp+1"
ADR0345_MAXIMUM_REALIZATION_ERROR_HEX = "0x1.0000000000000p-50"
ADR0345_MAXIMUM_JENSEN_ERROR_HEX = "0x1.0000000000000p-53"


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/ADR-0343-retain-and-seal-the-width-three-transfer-confirmation.md"
        ),
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_sequence_form_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_legal_game_test_sha256": (
            "tests/test_legal_river_continuation.py"
        ),
        "expected_implementation_sha256": (
            "src/pontius/responder_raise_semantics_keystone.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_responder_raise_semantics_keystone.py"
        ),
    }
)
_EXPECTED_SOURCE_HASHES = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "8bc61b35d467f93d0830a7ec9bf4b33e7cb9daf8f634dc1ca09ef6df4db025da"
        ),
        "expected_legal_kernel_sha256": (
            "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
        ),
        "expected_legal_game_sha256": (
            "4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250"
        ),
        "expected_sequence_form_sha256": (
            "a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231"
        ),
        "expected_legal_game_test_sha256": (
            "0c6a6cb7d63aa7c25ec3570605c8886ceaf780dc9fff3433d52091dc5edc396e"
        ),
        "expected_implementation_sha256": (
            "201b937d351d50e072d4f8f00268b3242855abd8f32c468b3d5870fad1682978"
        ),
        "expected_control_test_sha256": (
            "06b5eb1a490694adc6b0a61f7590fdb26bf01e6183943bcc4792b59ced0acba6"
        ),
    }
)

_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "config_sha256",
        "decision",
        "environment",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "generated",
        "implementation_sha256",
        "legal_game_sha256",
        "limitations",
        "maximum_realization_equivalence_error",
        "methodology",
        "passed",
        "quality_rows_serialized",
        "retreat",
        "root_public_state_sha256",
        "root_raise_to_totals",
        "schema_version",
        "semantics",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
        "table_seats",
        "teacher",
        "topology",
        "total_seconds",
    }
)
_EXPECTED_GATE_KEYS = frozenset(
    {
        "behavioral_shortcut_rejection",
        "bound_monotonicity",
        "clean_git",
        "every_action_from_kernel",
        "exact_digest_dedup_only",
        "final_gap",
        "finite",
        "full_raise_branch",
        "generated_converged",
        "incumbent_identity",
        "legacy_short_all_in_omission_detected",
        "passed",
        "public_schema",
        "realization_equivalence",
        "repeated_actor_topology",
        "retreat_jensen",
        "short_all_in_branch",
        "short_all_in_final_response_only",
        "strategic_node_count",
        "teacher_objective_identity",
        "teacher_plan_counts",
        "terminal_node_count",
        "terminal_oracle_identity",
        "total_time",
    }
)
_EXPECTED_PUBLIC_SCHEMA = {
    "root": {
        "acting_player": 0,
        "actions": ["check", "raise-to-2", "raise-to-3", "raise-to-4"],
    },
    "p0:raise-to-2": {
        "acting_player": 1,
        "actions": ["fold", "call", "raise-to-4"],
    },
    "p0:raise-to-2/p1:raise-to-4": {
        "acting_player": 0,
        "actions": ["fold", "call"],
    },
    "p0:raise-to-3": {
        "acting_player": 1,
        "actions": ["fold", "call", "raise-to-4"],
    },
    "p0:raise-to-3/p1:raise-to-4": {
        "acting_player": 0,
        "actions": ["fold", "call"],
    },
    "p0:raise-to-4": {
        "acting_player": 1,
        "actions": ["fold", "call"],
    },
}
_EXPECTED_TERMINALS = (
    "p0:check",
    "p0:raise-to-2/p1:call",
    "p0:raise-to-2/p1:fold",
    "p0:raise-to-2/p1:raise-to-4/p0:call",
    "p0:raise-to-2/p1:raise-to-4/p0:fold",
    "p0:raise-to-3/p1:call",
    "p0:raise-to-3/p1:fold",
    "p0:raise-to-3/p1:raise-to-4/p0:call",
    "p0:raise-to-3/p1:raise-to-4/p0:fold",
    "p0:raise-to-4/p1:call",
    "p0:raise-to-4/p1:fold",
)


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0345_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0345_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0345_ARTIFACT_SHA256,
    "config_sha256": ADR0345_CONFIG_SHA256,
    "game_provenance_sha256": ADR0345_GAME_PROVENANCE_SHA256,
    "game_structural_sha256": ADR0345_GAME_STRUCTURAL_SHA256,
    "invocation_source_commit": ADR0345_INVOCATION_SOURCE_COMMIT,
    "lower_bound_hex": ADR0345_LOWER_BOUND_HEX,
    "maximum_jensen_error_hex": ADR0345_MAXIMUM_JENSEN_ERROR_HEX,
    "maximum_realization_error_hex": ADR0345_MAXIMUM_REALIZATION_ERROR_HEX,
    "objective_hex": ADR0345_OBJECTIVE_HEX,
    "public_schema_sha256": ADR0345_PUBLIC_SCHEMA_SHA256,
    "root_public_state_sha256": ADR0345_ROOT_PUBLIC_STATE_SHA256,
    "source_hashes": dict(_EXPECTED_SOURCE_HASHES),
    "version": "adr0345-responder-raise-semantics-result-protocol-v1",
}
ADR0345_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0345_RESULT_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _RESULT_PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key in ADR-0345 artifact: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"nonfinite JSON number in ADR-0345 artifact: {token}")


def _decode_strict_object(raw: bytes, *, source: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid ADR-0345 JSON in {source}") from exc
    if not isinstance(decoded, dict):
        raise TypeError(f"ADR-0345 JSON in {source} must be an object")
    return decoded


def _raw_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"ADR-0345 required path is unavailable: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256(canonical).hexdigest()


def _require_finite_numbers(value: Any, *, path: str = "result") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite_numbers(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_finite_numbers(item, path=f"{path}[{index}]")
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError(f"ADR-0345 nonfinite value at {path}")


@dataclass(frozen=True, slots=True)
class RetainedResponderRaiseSemanticsResult:
    """Immutable interpretation of the exact retained keystone artifact."""

    record: Mapping[str, Any]
    source_commit: str
    total_seconds: float
    objective: float
    lower_bound: float
    upper_bound: float

    def __post_init__(self) -> None:
        if not isinstance(self.record, Mapping) or not self.record:
            raise TypeError("retained responder-raise record must be a mapping")
        if self.source_commit != ADR0345_INVOCATION_SOURCE_COMMIT:
            raise ValueError("retained responder-raise source commit drifted")
        for name, value in (
            ("total_seconds", self.total_seconds),
            ("objective", self.objective),
            ("lower_bound", self.lower_bound),
            ("upper_bound", self.upper_bound),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"retained responder-raise {name} is invalid")


def verify_adr0345_result_source_and_dependencies() -> str:
    """Verify the read-only owner and every ADR-0344 source-sealed input."""

    from .responder_raise_semantics_keystone_result_seal import (
        ADR0345_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0345_RESULT_SOURCE_MANIFEST,
    )

    module_path = Path(__file__).resolve()
    actual_module = _canonical_lf_sha256(module_path)
    if ADR0345_RESULT_SOURCE_MANIFEST != {
        module_path.name: actual_module
    }:
        raise RuntimeError("ADR-0345 result-owner source closure drifted")
    if sealed_protocol != ADR0345_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0345 result protocol drifted")

    config_path = _ROOT / ADR0345_CONFIG_RELATIVE_PATH
    if _raw_sha256(config_path) != ADR0345_CONFIG_SHA256:
        raise RuntimeError("ADR-0345 source-sealed config drifted")
    config = _decode_strict_object(config_path.read_bytes(), source=str(config_path))
    for field, relative_path in _SOURCE_PATHS.items():
        expected = _EXPECTED_SOURCE_HASHES[field]
        if config.get(field) != expected:
            raise RuntimeError(f"ADR-0345 config identity drifted: {field}")
        if _raw_sha256(_ROOT / relative_path) != expected:
            raise RuntimeError(f"ADR-0345 source input drifted: {relative_path}")
    return actual_module


def _verify_semantics(record: dict[str, Any]) -> None:
    semantics = record["semantics"]
    if not isinstance(semantics, dict):
        raise TypeError("ADR-0345 semantics record is malformed")
    expected_scalar = {
        "every_action_from_kernel": True,
        "full_raise_branches": 1,
        "maximum_terminal_oracle_error_chips": 0.0,
        "public_schema_sha256": ADR0345_PUBLIC_SCHEMA_SHA256,
        "short_all_in_final_response_only": True,
        "short_all_in_raise_branches": 1,
        "strategic_nodes": 6,
        "terminal_nodes": 11,
    }
    for key, expected in expected_scalar.items():
        if semantics.get(key) != expected:
            raise ValueError(f"ADR-0345 semantic identity drifted: {key}")
    if semantics.get("public_schema") != _EXPECTED_PUBLIC_SCHEMA:
        raise ValueError("ADR-0345 public schema drifted")
    if tuple(semantics.get("terminal_histories", ())) != _EXPECTED_TERMINALS:
        raise ValueError("ADR-0345 terminal histories drifted")


def _verify_generated(record: dict[str, Any]) -> tuple[float, float]:
    generated = record["generated"]
    if not isinstance(generated, dict):
        raise TypeError("ADR-0345 generated record is malformed")
    if (
        generated.get("converged") is not True
        or generated.get("exact_duplicate_response_hits") != 0
        or generated.get("response_rows_by_player") != [1, 2]
        or float(generated.get("baseline_nash_conv", float("nan"))).hex()
        != "0x1.7aaaaaaaaaaaap+1"
        or tuple(float(item).hex() for item in generated.get("caps", ()))
        != ("0x1.dfffffffffffep+0", "0x1.9555555555556p+0")
    ):
        raise ValueError("ADR-0345 generated-solve identity drifted")

    lower = float(generated["lower_bound"])
    upper = float(generated["upper_bound"])
    if (
        lower.hex() != ADR0345_LOWER_BOUND_HEX
        or upper.hex() != ADR0345_OBJECTIVE_HEX
        or generated.get("optimality_gap") != 0.0
        or lower > upper + 1e-9
    ):
        raise ValueError("ADR-0345 generated bounds drifted")

    iterations = generated.get("iterations")
    if not isinstance(iterations, list) or len(iterations) != 2:
        raise ValueError("ADR-0345 iteration count drifted")
    first, second = iterations
    if (
        first.get("iteration") != 1
        or first.get("added_targets") != [1]
        or first.get("candidate_feasible") is not False
        or first.get("converged") is not False
        or first.get("incumbent_updated") is not False
        or first.get("response_rows_before") != 2
        or first.get("response_rows_added") != 1
        or second.get("iteration") != 2
        or second.get("added_targets") != []
        or second.get("candidate_feasible") is not True
        or second.get("converged") is not True
        or second.get("incumbent_updated") is not True
        or second.get("response_rows_before") != 3
        or second.get("response_rows_added") != 0
    ):
        raise ValueError("ADR-0345 generated iteration witness drifted")
    if (
        float(first["master_lower_bound"])
        > float(second["master_lower_bound"]) + 1e-9
        or float(first["incumbent_upper_bound"])
        < float(second["incumbent_upper_bound"]) - 1e-9
        or max(
            float(first["realization_equivalence_max_error"]),
            float(second["realization_equivalence_max_error"]),
        ).hex()
        != ADR0345_MAXIMUM_REALIZATION_ERROR_HEX
    ):
        raise ValueError("ADR-0345 monotone-bound or realization witness drifted")

    conditioning = generated.get("conditioning_by_player")
    if (
        not isinstance(conditioning, list)
        or len(conditioning) != 2
        or [(item.get("rows"), item.get("numerical_rank")) for item in conditioning]
        != [(1, 1), (2, 2)]
        or conditioning[0].get("minimum_normalized_separation") is not None
    ):
        raise ValueError("ADR-0345 response-row conditioning witness drifted")
    return lower, upper


def verify_adr0345_responder_raise_semantics_result_artifact(
    path: Path | None = None,
) -> RetainedResponderRaiseSemanticsResult:
    """Rebind ADR-0344's exact artifact without a game or solver call."""

    verify_adr0345_result_source_and_dependencies()
    artifact_path = (
        _ROOT / ADR0345_ARTIFACT_RELATIVE_PATH if path is None else path
    )
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0345_ARTIFACT_BYTES:
        raise ValueError("ADR-0345 artifact byte count drifted")
    if sha256(raw).hexdigest() != ADR0345_ARTIFACT_SHA256:
        raise ValueError("ADR-0345 artifact SHA-256 drifted")
    record = _decode_strict_object(raw, source=str(artifact_path))
    if set(record) != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("ADR-0345 top-level result schema drifted")
    _require_finite_numbers(record)

    environment = record["environment"]
    git = environment.get("git", {}) if isinstance(environment, dict) else {}
    if (
        record["schema_version"] != 1
        or record["status"]
        != "legal_responder_raise_semantics_keystone_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_h4_legal_responder_raise_open_axis_differential"
        or record["strategy_quality_claim"] is not None
        or record["strategy_labels_generated"] != 0
        or record["quality_rows_serialized"] != 0
        or record["config_sha256"] != ADR0345_CONFIG_SHA256
        or record["root_public_state_sha256"]
        != ADR0345_ROOT_PUBLIC_STATE_SHA256
        or record["game_structural_sha256"] != ADR0345_GAME_STRUCTURAL_SHA256
        or record["game_provenance_sha256"] != ADR0345_GAME_PROVENANCE_SHA256
        or record["implementation_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_implementation_sha256"]
        or record["legal_game_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_legal_game_sha256"]
        or record["table_seats"] != [2, 1]
        or record["root_raise_to_totals"] != [2, 3, 4]
        or git
        != {
            "commit": ADR0345_INVOCATION_SOURCE_COMMIT,
            "dirty": False,
            "strict_status": True,
        }
        or environment.get("runtime")
        != {"backend": "cpu_float64_exact_small_game"}
    ):
        raise ValueError("ADR-0345 retained identity drifted")

    methodology = record["methodology"]
    if methodology != {
        "betting_authority": "NoLimitBettingState",
        "open_axis": "one_seat_sequence_form_realization",
        "quality_rows": 0,
        "strategy_labels": 0,
        "teacher": "complete_mixed_normal_form_direct_utility_evaluation",
    }:
        raise ValueError("ADR-0345 methodology drifted")
    gates = record["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _EXPECTED_GATE_KEYS
        or any(value is not True for value in gates.values())
    ):
        raise ValueError("ADR-0345 gate vector is not an all-pass result")

    _verify_semantics(record)
    topology = record["topology"]
    if topology != {
        "behavioral_shortcut_rejected": True,
        "path_single_visit": False,
        "repeated_player": 0,
        "witness": [
            "RiverDeal(player0=(49, 51), player1=(45, 46))",
            "raise-to-2",
            "raise-to-4",
        ],
    }:
        raise ValueError("ADR-0345 repeated-actor topology drifted")

    teacher = record["teacher"]
    objective = float(teacher["objective"])
    if (
        teacher.get("acting_pure_plans") != 16
        or teacher.get("response_pure_plans") != [0, 18]
        or teacher.get("simplex_pivots") != 5
        or teacher.get("maximum_exact_error") != 0.0
        or objective.hex() != ADR0345_OBJECTIVE_HEX
        or float(teacher["exact_nash_conv"]).hex() != ADR0345_OBJECTIVE_HEX
    ):
        raise ValueError("ADR-0345 complete-teacher identity drifted")
    lower, upper = _verify_generated(record)
    if upper.hex() != objective.hex():
        raise ValueError("ADR-0345 generated/teacher objective identity drifted")

    maximum_realization_error = float(
        record["maximum_realization_equivalence_error"]
    )
    retreat = record["retreat"]
    if (
        maximum_realization_error.hex()
        != ADR0345_MAXIMUM_REALIZATION_ERROR_HEX
        or retreat.get("factor") != 0.8
        or float(retreat["maximum_jensen_error"]).hex()
        != ADR0345_MAXIMUM_JENSEN_ERROR_HEX
    ):
        raise ValueError("ADR-0345 realization or Jensen witness drifted")
    total_seconds = float(record["total_seconds"])
    if total_seconds < 0.0 or total_seconds > 60.0:
        raise ValueError("ADR-0345 finite-campaign wall gate drifted")

    return RetainedResponderRaiseSemanticsResult(
        record=_deep_freeze(record),
        source_commit=ADR0345_INVOCATION_SOURCE_COMMIT,
        total_seconds=total_seconds,
        objective=objective,
        lower_bound=lower,
        upper_bound=upper,
    )


__all__ = [
    "ADR0345_ARTIFACT_BYTES",
    "ADR0345_ARTIFACT_RELATIVE_PATH",
    "ADR0345_ARTIFACT_SHA256",
    "ADR0345_CONFIG_SHA256",
    "ADR0345_GAME_PROVENANCE_SHA256",
    "ADR0345_GAME_STRUCTURAL_SHA256",
    "ADR0345_INVOCATION_SOURCE_COMMIT",
    "ADR0345_LOWER_BOUND_HEX",
    "ADR0345_MAXIMUM_JENSEN_ERROR_HEX",
    "ADR0345_MAXIMUM_REALIZATION_ERROR_HEX",
    "ADR0345_OBJECTIVE_HEX",
    "ADR0345_PUBLIC_SCHEMA_SHA256",
    "ADR0345_RESULT_PROTOCOL",
    "ADR0345_RESULT_PROTOCOL_SHA256",
    "ADR0345_ROOT_PUBLIC_STATE_SHA256",
    "RetainedResponderRaiseSemanticsResult",
    "verify_adr0345_responder_raise_semantics_result_artifact",
    "verify_adr0345_result_source_and_dependencies",
]
