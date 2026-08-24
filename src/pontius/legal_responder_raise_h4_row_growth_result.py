"""Solver-free owner for ADR-0349's retained h4 row-growth result.

The ADR-0348 runner is permanently closed.  This module reads only its exact
retained JSON artifact, verifies the source-sealed closure, and rebinds the
stored signatures, Fraction rows, convergence ledger, conditioning, oracle
accounting, retained bytes, and bounded infrastructure timing.  It imports no
game, evaluator, optimizer, observer, runner, action, or write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import gcd, isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


ADR0349_INVOCATION_SOURCE_COMMIT = (
    "c80723285073288db8515f8a6fa4921920489c80"
)
ADR0349_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-row-growth-v1.json"
)
ADR0349_ARTIFACT_BYTES = 50_963
ADR0349_ARTIFACT_SHA256 = (
    "eb35843218741096f214a6c341a0762b8f1cca09a81a1fdce1db21eaa9fc60b8"
)
ADR0349_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-responder-raise-h4-row-growth-v1.json"
)
ADR0349_CONFIG_SHA256 = (
    "da6c4067cedd71504eb0c5e0c5034ffdf731839d2df71d33f0a07d12bd25cd99"
)
ADR0349_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0349_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0349_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0349_GAME_PROVENANCE_SHA256 = (
    "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
)
ADR0349_SOURCE_POLICY_SHA256 = (
    "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
)
ADR0349_FINAL_POLICY_SHA256 = (
    "0f9be1f884cb09eb8318a88a1548afb402ec256e8fa52f19118c64569fe7658b"
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/"
            "ADR-0347-retain-and-seal-the-legal-h4-coefficient-result.md"
        ),
        "expected_parent_artifact_sha256": (
            "experiments/results/"
            "legal-responder-raise-h4-coefficient-differential-v1.json"
        ),
        "expected_parent_result_owner_sha256": (
            "src/pontius/legal_responder_raise_h4_coefficient_result.py"
        ),
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_generation_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_audit_source_sha256": "src/pontius/one_seat_row_growth_audit.py",
        "expected_evaluation_sha256": "src/pontius/evaluation.py",
        "expected_exact_oracle_sha256": (
            "src/pontius/exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_implementation_sha256": (
            "src/pontius/legal_responder_raise_h4_row_growth.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_responder_raise_h4_row_growth.py"
        ),
        "expected_audit_test_sha256": "tests/test_one_seat_row_growth_audit.py",
    }
)
_EXPECTED_SOURCE_HASHES = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "d76a984978ba991e7a797f4aad292f6b80278502f14184658a3f42b34c433c63"
        ),
        "expected_parent_artifact_sha256": (
            "6dcbf8e44f1c3b2bd54694e0c1f6898082e71373846933bfaa116bc4f2c27255"
        ),
        "expected_parent_result_owner_sha256": (
            "4c67ce1e724e6196a1fff6d7d6312c7a117fd9ff5ea47c8e82d7a1f21e8e1547"
        ),
        "expected_legal_kernel_sha256": (
            "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
        ),
        "expected_legal_game_sha256": (
            "4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250"
        ),
        "expected_generation_primitive_sha256": (
            "a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231"
        ),
        "expected_audit_source_sha256": (
            "f5c6f80bc46a6b8887f9241998207bbb8828fff136a6f1a389475b1aead349eb"
        ),
        "expected_evaluation_sha256": (
            "c362fb1e294bb8bac722adf479df4d2f27ddcf8c26390c037ec88f858702cda8"
        ),
        "expected_exact_oracle_sha256": (
            "8d70297ab80055c5c77bdeefb82ff6cde817f6c57876059783046669b3a6945a"
        ),
        "expected_implementation_sha256": (
            "89f425d5bf5ddca7a1e2ef0eb343d0f34b1ce39cc9b7ee31a3fc4364905b9e58"
        ),
        "expected_control_test_sha256": (
            "14c698b38669aeeb624bf844494468856f37eb80c8278ccde6035415f59ac591"
        ),
        "expected_audit_test_sha256": (
            "14d6bb929af5167d336f8abc724558e2710748efc8b1fc905bb8c120f3a2ed1e"
        ),
    }
)
_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "audit_source_sha256",
        "axis",
        "baseline_nash_conv",
        "cap_identity_error",
        "caps",
        "conditioning",
        "config_sha256",
        "converged",
        "decision",
        "environment",
        "evaluations",
        "exact_caps",
        "exact_convergence_classification",
        "exact_duplicate_response_hits",
        "exact_feasibility_classification",
        "exact_gains_nonnegative",
        "exact_incumbent_feasible",
        "exact_row_identities",
        "final_exact_nash_conv",
        "final_policy_evaluation_ordinal",
        "final_policy_sha256",
        "final_upper_bound_exact_error",
        "fixture",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "implementation_sha256",
        "iterations",
        "limitations",
        "lower_bound",
        "maximum_conditioning_rebind_error",
        "maximum_float_exact_evaluation_error",
        "maximum_float_exact_row_error",
        "maximum_master_constraint_violation",
        "maximum_master_duality_gap",
        "maximum_realization_equivalence_error",
        "methodology",
        "optimality_gap",
        "oracle_accounting",
        "parent_artifact_sha256",
        "passed",
        "public_schema_sha256",
        "quality_rows_serialized",
        "response_rows",
        "response_rows_by_player",
        "retained_row_bytes",
        "root_public_state_sha256",
        "schema_version",
        "source_policy_sha256",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
        "timing",
        "total_seconds",
        "upper_bound",
    }
)
_EXPECTED_GATE_KEYS = frozenset(
    {
        "all_rows_retained",
        "axis_identity",
        "bound_monotonicity",
        "clean_git",
        "conditioning",
        "converged",
        "exact_convergence_classification",
        "exact_evaluation_identities",
        "exact_incumbent_feasible",
        "exact_row_identities",
        "exact_signature_dedup",
        "final_gap",
        "finite",
        "fixture_identity",
        "initial_row_counts",
        "initial_row_identities",
        "iteration_bound",
        "master_certificate_diagnostics",
        "oracle_accounting",
        "parent_pass",
        "passed",
        "realization_equivalence",
        "retained_row_bytes",
        "subject_time",
        "total_time",
    }
)
_RESPONSE_SIGNATURE_SHA256S = (
    "83b57620097d496624aabfa49fdba1ab64ccb5cd519a9daf20130ade55f7e908",
    "778a91ab318ea0c94d1baa8dcfe9481ed6155604cc964a6b014720b0b20877f8",
)
_CANDIDATE_RESPONSE_SIGNATURE_SHA256S = (
    _RESPONSE_SIGNATURE_SHA256S[0],
    "cbbf05b85462131028b75649e583df5a48f3ad680ed8109b852b161b211a7cd0",
)
_ROW_SHA256S = (
    "7be24d40786a55761142e3bfdf230f5b6ddbac5320703cd44050d4d2f345f4a5",
    "3c1b73c33f1f5ede4ea8a9ccf415c5337a3c033ae4a5549177a19324b0543d90",
)

_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0349_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0349_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0349_ARTIFACT_SHA256,
    "candidate_response_signature_sha256s": list(
        _CANDIDATE_RESPONSE_SIGNATURE_SHA256S
    ),
    "config_sha256": ADR0349_CONFIG_SHA256,
    "final_policy_sha256": ADR0349_FINAL_POLICY_SHA256,
    "game_provenance_sha256": ADR0349_GAME_PROVENANCE_SHA256,
    "game_structural_sha256": ADR0349_GAME_STRUCTURAL_SHA256,
    "invocation_source_commit": ADR0349_INVOCATION_SOURCE_COMMIT,
    "public_schema_sha256": ADR0349_PUBLIC_SCHEMA_SHA256,
    "response_signature_sha256s": list(_RESPONSE_SIGNATURE_SHA256S),
    "root_public_state_sha256": ADR0349_ROOT_PUBLIC_STATE_SHA256,
    "row_sha256s": list(_ROW_SHA256S),
    "source_hashes": dict(_EXPECTED_SOURCE_HASHES),
    "source_policy_sha256": ADR0349_SOURCE_POLICY_SHA256,
    "version": "adr0349-legal-h4-row-growth-result-protocol-v1",
}
ADR0349_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0349_RESULT_PROTOCOL_SHA256 = sha256(
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


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key in ADR-0349 artifact: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"nonfinite JSON number in ADR-0349 artifact: {token}")


def _decode_strict_object(raw: bytes, *, source: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid ADR-0349 JSON in {source}") from exc
    if not isinstance(decoded, dict):
        raise TypeError(f"ADR-0349 JSON in {source} must be an object")
    return decoded


def _raw_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"ADR-0349 required path is unavailable: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    return sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _canonical_compact_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _require_finite_numbers(value: Any, *, path: str = "result") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite_numbers(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_finite_numbers(item, path=f"{path}[{index}]")
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError(f"ADR-0349 nonfinite value at {path}")


def _require_zero(value: Any, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"ADR-0349 {field} must be numeric zero")
    if value != 0:
        raise ValueError(f"ADR-0349 {field} is not zero")


def _fraction(record: Any, *, field: str) -> Fraction:
    if not isinstance(record, dict) or set(record) != {"numerator", "denominator"}:
        raise TypeError(f"ADR-0349 {field} is not an exact fraction")
    numerator = record["numerator"]
    denominator = record["denominator"]
    if (
        isinstance(numerator, bool)
        or isinstance(denominator, bool)
        or not isinstance(numerator, int)
        or not isinstance(denominator, int)
        or denominator <= 0
        or gcd(abs(numerator), denominator) != 1
    ):
        raise ValueError(f"ADR-0349 {field} is not reduced with positive denominator")
    return Fraction(numerator, denominator)


def _hex_fraction(value: Any, *, field: str) -> Fraction:
    if not isinstance(value, str):
        raise TypeError(f"ADR-0349 {field} must be hexadecimal Float64")
    try:
        parsed = float.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"ADR-0349 {field} is not hexadecimal Float64") from exc
    if not isfinite(parsed) or parsed.hex() != value:
        raise ValueError(f"ADR-0349 {field} is not canonical finite Float64")
    return Fraction.from_float(parsed)


def _float_fraction(value: Any, *, field: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"ADR-0349 {field} must be numeric")
    parsed = float(value)
    if not isfinite(parsed):
        raise ValueError(f"ADR-0349 {field} is nonfinite")
    return Fraction.from_float(parsed)


@dataclass(frozen=True, slots=True)
class RetainedLegalH4RowGrowthResult:
    """Immutable interpretation of ADR-0349's finite retained artifact."""

    record: Mapping[str, Any]
    source_commit: str
    total_seconds: float
    response_rows: int
    generated_rows: int
    iterations: int

    def __post_init__(self) -> None:
        if not isinstance(self.record, Mapping) or not self.record:
            raise TypeError("retained h4 row-growth record must be a mapping")
        if self.source_commit != ADR0349_INVOCATION_SOURCE_COMMIT:
            raise ValueError("retained h4 row-growth source commit drifted")
        if not isfinite(self.total_seconds) or self.total_seconds < 0.0:
            raise ValueError("retained h4 row-growth timing is invalid")
        if (self.response_rows, self.generated_rows, self.iterations) != (2, 0, 1):
            raise ValueError("retained h4 row-growth dimensions drifted")


def verify_adr0349_result_source_and_dependencies() -> str:
    """Verify this read-only owner and all ADR-0348 source-sealed inputs."""

    from .legal_responder_raise_h4_row_growth_result_seal import (
        ADR0349_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0349_RESULT_SOURCE_MANIFEST,
    )

    module_path = Path(__file__).resolve()
    actual_module = _canonical_lf_sha256(module_path)
    if ADR0349_RESULT_SOURCE_MANIFEST != {module_path.name: actual_module}:
        raise RuntimeError("ADR-0349 result-owner source closure drifted")
    if sealed_protocol != ADR0349_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0349 result protocol drifted")
    config_path = _ROOT / ADR0349_CONFIG_RELATIVE_PATH
    if _raw_sha256(config_path) != ADR0349_CONFIG_SHA256:
        raise RuntimeError("ADR-0349 source-sealed config drifted")
    config = _decode_strict_object(config_path.read_bytes(), source=str(config_path))
    for field, relative_path in _SOURCE_PATHS.items():
        expected = _EXPECTED_SOURCE_HASHES[field]
        if config.get(field) != expected:
            raise RuntimeError(f"ADR-0349 config identity drifted: {field}")
        if _raw_sha256(_ROOT / relative_path) != expected:
            raise RuntimeError(f"ADR-0349 source input drifted: {relative_path}")
    return actual_module


def _verify_signature(signature: Any, expected_sha256: str, *, field: str) -> None:
    if not isinstance(signature, list) or len(signature) != 12:
        raise ValueError(f"ADR-0349 {field} signature width drifted")
    keys = []
    for item in signature:
        if not isinstance(item, dict) or set(item) != {"information_key", "action"}:
            raise TypeError(f"ADR-0349 {field} signature item drifted")
        if not all(isinstance(item[name], str) and item[name] for name in item):
            raise ValueError(f"ADR-0349 {field} signature text drifted")
        keys.append(item["information_key"])
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ValueError(f"ADR-0349 {field} signature ordering drifted")
    if _canonical_sha256(signature) != expected_sha256:
        raise ValueError(f"ADR-0349 {field} signature digest drifted")


def _verify_rows(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    rows = record["response_rows"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("ADR-0349 response-row inventory drifted")
    expected_bytes = (10_889, 10_802)
    axes: list[tuple[tuple[str, str], ...]] = []
    for index, row in enumerate(rows):
        expected_keys = {
            "after_iteration",
            "coefficients",
            "constant_exact",
            "constant_subject_hex",
            "exact_float_identity",
            "exact_row_sha256",
            "maximum_coefficient_error",
            "ordinal",
            "phase",
            "retained_bytes",
            "signature",
            "signature_sha256",
            "target_player",
        }
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise ValueError(f"ADR-0349 response row {index} schema drifted")
        semantic = {key: value for key, value in row.items() if key != "retained_bytes"}
        if (
            row["ordinal"] != index
            or row["phase"] != "initial"
            or row["after_iteration"] is not None
            or row["target_player"] != index
            or row["retained_bytes"] != expected_bytes[index]
            or len(_canonical_compact_bytes(semantic)) != expected_bytes[index]
            or row["signature_sha256"] != _RESPONSE_SIGNATURE_SHA256S[index]
            or row["exact_row_sha256"] != _ROW_SHA256S[index]
            or row["exact_float_identity"] is not True
        ):
            raise ValueError(f"ADR-0349 response row {index} identity drifted")
        _verify_signature(
            row["signature"],
            _RESPONSE_SIGNATURE_SHA256S[index],
            field=f"row[{index}]",
        )
        _require_zero(
            row["maximum_coefficient_error"],
            field=f"row[{index}].maximum_coefficient_error",
        )
        constant = _fraction(row["constant_exact"], field=f"row[{index}].constant")
        if _hex_fraction(
            row["constant_subject_hex"], field=f"row[{index}].constant_subject"
        ) != constant:
            raise ValueError(f"ADR-0349 response row {index} constant drifted")
        coefficients = row["coefficients"]
        if not isinstance(coefficients, list) or len(coefficients) != 32:
            raise ValueError(f"ADR-0349 response row {index} width drifted")
        exact_payload = []
        axis = []
        for coefficient_index, coefficient in enumerate(coefficients):
            if not isinstance(coefficient, dict) or set(coefficient) != {
                "absolute_error",
                "action",
                "exact",
                "information_key",
                "subject_hex",
            }:
                raise ValueError("ADR-0349 coefficient schema drifted")
            key = coefficient["information_key"]
            action = coefficient["action"]
            if not isinstance(key, str) or not isinstance(action, str):
                raise TypeError("ADR-0349 coefficient identity must be text")
            token = (key, action)
            axis.append(token)
            exact = _fraction(
                coefficient["exact"],
                field=f"row[{index}].coefficient[{coefficient_index}]",
            )
            if _hex_fraction(
                coefficient["subject_hex"],
                field=f"row[{index}].coefficient[{coefficient_index}].subject",
            ) != exact:
                raise ValueError("ADR-0349 coefficient Float64/Fraction drifted")
            _require_zero(
                coefficient["absolute_error"],
                field=f"row[{index}].coefficient[{coefficient_index}].error",
            )
            exact_payload.append(
                {
                    "information_key": key,
                    "action": action,
                    "value": coefficient["exact"],
                }
            )
        if len(axis) != len(set(axis)):
            raise ValueError("ADR-0349 response row axis repeats a coordinate")
        digest_payload = {
            "constant": row["constant_exact"],
            "coefficients": sorted(
                exact_payload,
                key=lambda item: (item["information_key"], item["action"]),
            ),
        }
        if _canonical_sha256(digest_payload) != _ROW_SHA256S[index]:
            raise ValueError(f"ADR-0349 response row {index} exact digest drifted")
        axes.append(tuple(axis))
    if axes[0] != axes[1]:
        raise ValueError("ADR-0349 response row axes differ")
    if record["response_rows_by_player"] != [1, 1]:
        raise ValueError("ADR-0349 response-row counts drifted")
    if record["retained_row_bytes"] != sum(expected_bytes):
        raise ValueError("ADR-0349 retained-row byte total drifted")
    return axes[0]


def _verify_evaluations(record: dict[str, Any]) -> None:
    evaluations = record["evaluations"]
    if not isinstance(evaluations, list) or len(evaluations) != 2:
        raise ValueError("ADR-0349 evaluation inventory drifted")
    expected = (
        {
            "policy": ADR0349_SOURCE_POLICY_SHA256,
            "signatures": _RESPONSE_SIGNATURE_SHA256S,
            "utilities": (Fraction(-2739, 2048), Fraction(2739, 2048)),
            "responses": (Fraction(-45, 64), Fraction(1647, 512)),
            "gains": (Fraction(1299, 2048), Fraction(3849, 2048)),
            "nash_conv": Fraction(1287, 512),
        },
        {
            "policy": ADR0349_FINAL_POLICY_SHA256,
            "signatures": _CANDIDATE_RESPONSE_SIGNATURE_SHA256S,
            "utilities": (Fraction(-9, 8), Fraction(9, 8)),
            "responses": (Fraction(-45, 64), Fraction(9, 8)),
            "gains": (Fraction(27, 64), Fraction(0)),
            "nash_conv": Fraction(27, 64),
        },
    )
    for index, (evaluation, frozen) in enumerate(zip(evaluations, expected, strict=True)):
        keys = {
            "best_response_values_exact",
            "deviation_gains_exact",
            "exact_gains_nonnegative",
            "maximum_float_exact_error",
            "nash_conv_exact",
            "ordinal",
            "policy_sha256",
            "response_signature_sha256s",
            "response_signatures",
            "utilities_exact",
        }
        if not isinstance(evaluation, dict) or set(evaluation) != keys:
            raise ValueError(f"ADR-0349 evaluation {index} schema drifted")
        if (
            evaluation["ordinal"] != index
            or evaluation["policy_sha256"] != frozen["policy"]
            or tuple(evaluation["response_signature_sha256s"])
            != frozen["signatures"]
            or evaluation["exact_gains_nonnegative"] is not True
        ):
            raise ValueError(f"ADR-0349 evaluation {index} identity drifted")
        signatures = evaluation["response_signatures"]
        if not isinstance(signatures, list) or len(signatures) != 2:
            raise ValueError("ADR-0349 evaluation response tapes drifted")
        for player in range(2):
            _verify_signature(
                signatures[player],
                frozen["signatures"][player],
                field=f"evaluation[{index}].response[{player}]",
            )
        utilities = tuple(
            _fraction(value, field=f"evaluation[{index}].utility")
            for value in evaluation["utilities_exact"]
        )
        responses = tuple(
            _fraction(value, field=f"evaluation[{index}].response_value")
            for value in evaluation["best_response_values_exact"]
        )
        gains = tuple(
            _fraction(value, field=f"evaluation[{index}].gain")
            for value in evaluation["deviation_gains_exact"]
        )
        nash_conv = _fraction(
            evaluation["nash_conv_exact"],
            field=f"evaluation[{index}].nash_conv",
        )
        if (
            utilities != frozen["utilities"]
            or responses != frozen["responses"]
            or gains != frozen["gains"]
            or nash_conv != frozen["nash_conv"]
            or sum(utilities, Fraction(0)) != 0
            or tuple(response - utility for response, utility in zip(responses, utilities))
            != gains
            or sum(gains, Fraction(0)) != nash_conv
            or any(gain < 0 for gain in gains)
        ):
            raise ValueError(f"ADR-0349 evaluation {index} exact algebra drifted")
        _require_zero(
            evaluation["maximum_float_exact_error"],
            field=f"evaluation[{index}].maximum_float_exact_error",
        )
    if evaluations[0]["response_signatures"][0] != evaluations[1][
        "response_signatures"
    ][0]:
        raise ValueError("ADR-0349 invariant acting response tape drifted")
    if evaluations[0]["response_signatures"][1] == evaluations[1][
        "response_signatures"
    ][1]:
        raise ValueError("ADR-0349 observed responder tape change disappeared")


def _verify_iteration_and_summary(record: dict[str, Any]) -> None:
    baseline = Fraction(1287, 512)
    exact_caps = (Fraction(1811, 2048), Fraction(4361, 2048))
    final = Fraction(27, 64)
    if (
        _float_fraction(record["baseline_nash_conv"], field="baseline_nash_conv")
        != baseline
        or record["source_policy_sha256"] != ADR0349_SOURCE_POLICY_SHA256
        or record["final_policy_sha256"] != ADR0349_FINAL_POLICY_SHA256
        or record["final_policy_evaluation_ordinal"] != 1
        or tuple(
            _fraction(value, field="exact_caps") for value in record["exact_caps"]
        )
        != exact_caps
        or tuple(
            _float_fraction(value, field="caps") for value in record["caps"]
        )
        != exact_caps
        or _fraction(record["final_exact_nash_conv"], field="final_exact_nash_conv")
        != final
        or _float_fraction(record["upper_bound"], field="upper_bound") != final
    ):
        raise ValueError("ADR-0349 exact summary drifted")
    for field in (
        "cap_identity_error",
        "final_upper_bound_exact_error",
        "maximum_conditioning_rebind_error",
        "maximum_float_exact_evaluation_error",
        "maximum_float_exact_row_error",
        "maximum_master_duality_gap",
        "maximum_realization_equivalence_error",
    ):
        _require_zero(record[field], field=field)
    if (
        float(record["lower_bound"]).hex() != "0x1.afffffffffffep-2"
        or float(record["upper_bound"]).hex() != "0x1.b000000000000p-2"
        or float(record["optimality_gap"]).hex() != "0x1.0000000000000p-53"
        or record["converged"] is not True
        or record["exact_duplicate_response_hits"] != 0
        or any(
            record[field] is not True
            for field in (
                "exact_convergence_classification",
                "exact_feasibility_classification",
                "exact_gains_nonnegative",
                "exact_incumbent_feasible",
                "exact_row_identities",
            )
        )
    ):
        raise ValueError("ADR-0349 convergence summary drifted")
    iterations = record["iterations"]
    if not isinstance(iterations, list) or len(iterations) != 1:
        raise ValueError("ADR-0349 iteration inventory drifted")
    iteration = iterations[0]
    if (
        iteration["iteration"] != 1
        or iteration["response_rows_before"] != 2
        or iteration["response_rows_added"] != 0
        or iteration["added_targets"] != []
        or iteration["candidate_feasible"] is not True
        or iteration["incumbent_updated"] is not True
        or iteration["converged"] is not True
        or iteration["exact_candidate_feasible"] is not True
        or iteration["exact_converged"] is not True
        or tuple(iteration["response_signature_sha256s"])
        != _CANDIDATE_RESPONSE_SIGNATURE_SHA256S
        or iteration["epigraph_hex"]
        != ["0x1.afffffffffffdp-2", "0x0.0p+0"]
        or float(iteration["candidate_nash_conv"]).hex()
        != "0x1.b000000000000p-2"
        or float(iteration["master_lower_bound"]).hex()
        != "0x1.afffffffffffep-2"
        or float(iteration["incumbent_upper_bound"]).hex()
        != "0x1.b000000000000p-2"
        or float(iteration["optimality_gap"]).hex() != "0x1.0000000000000p-53"
        or float(iteration["maximum_epigraph_violation"]).hex()
        != "0x1.8000000000000p-53"
    ):
        raise ValueError("ADR-0349 sole iteration drifted")
    for field in ("maximum_cap_violation", "realization_equivalence_max_error"):
        _require_zero(iteration[field], field=f"iteration.{field}")
    if (
        _fraction(
            iteration["maximum_exact_cap_violation"],
            field="iteration.maximum_exact_cap_violation",
        )
        != Fraction(-947, 2048)
        or _fraction(
            iteration["maximum_exact_epigraph_violation"],
            field="iteration.maximum_exact_epigraph_violation",
        )
        != Fraction(3, 18014398509481984)
    ):
        raise ValueError("ADR-0349 exact iteration residual drifted")
    master = iteration["master"]
    if master != {
        "dual_objective_hex": "-0x1.b000000000000p-2",
        "duality_gap": 0.0,
        "maximum_constraint_violation": record[
            "maximum_master_constraint_violation"
        ],
        "objective_hex": "-0x1.afffffffffffep-2",
        "pivots": 18,
    }:
        raise ValueError("ADR-0349 restricted master witness drifted")
    maximum_constraint = float(record["maximum_master_constraint_violation"])
    if (
        maximum_constraint.hex() != "0x1.5c92492492492p-52"
        or maximum_constraint > 1e-8
    ):
        raise ValueError("ADR-0349 master constraint diagnostic drifted")
    for field in (
        "cut_extraction_seconds",
        "exact_oracle_seconds",
        "master_solve_seconds",
    ):
        value = float(iteration[field])
        if not 0.0 <= value <= float(record["total_seconds"]):
            raise ValueError(f"ADR-0349 iteration timing drifted: {field}")


def _verify_conditioning_and_accounting(record: dict[str, Any]) -> None:
    expected_condition = {
        "effective_condition_number": 1.0,
        "minimum_normalized_separation": None,
        "numerical_rank": 1,
        "rows": 1,
    }
    conditioning = record["conditioning"]
    if (
        not isinstance(conditioning, list)
        or len(conditioning) != 2
        or any(
            row
            != {
                "player": player,
                "production": expected_condition,
                "rebound": expected_condition,
            }
            for player, row in enumerate(conditioning)
        )
    ):
        raise ValueError("ADR-0349 conditioning witness drifted")
    expected_oracles = {
        "best_response_calls": 5,
        "evaluation_calls": 2,
        "expected_utilities_calls": 3,
        "master_calls": 1,
        "open_axis_coefficient_calls": 3,
        "response_row_calls": 2,
    }
    if record["oracle_accounting"] != {
        "expected_from_call_graph": expected_oracles,
        "identity": True,
        "observed": expected_oracles,
    }:
        raise ValueError("ADR-0349 oracle accounting drifted")


def verify_adr0349_legal_h4_row_growth_record(
    record: dict[str, Any],
) -> Mapping[str, Any]:
    """Semantically rebind a decoded ADR-0349 record without outer hashing."""

    if not isinstance(record, dict) or set(record) != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("ADR-0349 top-level result schema drifted")
    _require_finite_numbers(record)
    environment = record["environment"]
    git = environment.get("git", {}) if isinstance(environment, dict) else {}
    if (
        record["schema_version"] != 1
        or record["status"] != "legal_responder_raise_h4_row_growth_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_legal_responder_raise_selector_stability_preregistration"
        or record["strategy_quality_claim"] is not None
        or record["strategy_labels_generated"] != 0
        or record["quality_rows_serialized"] != 0
        or record["config_sha256"] != ADR0349_CONFIG_SHA256
        or record["implementation_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_implementation_sha256"]
        or record["audit_source_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_audit_source_sha256"]
        or record["parent_artifact_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_parent_artifact_sha256"]
        or record["root_public_state_sha256"] != ADR0349_ROOT_PUBLIC_STATE_SHA256
        or record["public_schema_sha256"] != ADR0349_PUBLIC_SCHEMA_SHA256
        or record["game_structural_sha256"] != ADR0349_GAME_STRUCTURAL_SHA256
        or record["game_provenance_sha256"] != ADR0349_GAME_PROVENANCE_SHA256
        or git
        != {
            "commit": ADR0349_INVOCATION_SOURCE_COMMIT,
            "dirty": False,
            "strict_status": True,
        }
        or environment.get("runtime")
        != {"backend": "cpu_float64_generation_fraction_audit"}
    ):
        raise ValueError("ADR-0349 retained identity drifted")
    if record["fixture"] != {
        "hand_counts": [4, 4],
        "joint_deals": 16,
        "root_raise_to_totals": [2, 3, 4],
        "table_seats": [2, 1],
        "terminal_paths": 176,
    } or record["axis"] != {
        "acting_player": 0,
        "information_sets": 12,
        "sequence_variables": 32,
    }:
        raise ValueError("ADR-0349 fixture or axis drifted")
    if record["methodology"] != {
        "betting_authority": "NoLimitBettingState",
        "deduplication": (
            "exact_target_player_plus_complete_sorted_information_key_action_tuple"
        ),
        "observer": "single_threaded_read_only_boundary_instrumentation",
        "quality_rows": 0,
        "retained_row_bytes": (
            "canonical_compact_utf8_semantic_row_record_excluding_retained_bytes"
        ),
        "strategy_labels": 0,
        "subject": "production_one_seat_sequence_form_row_generation",
        "teacher": "independent_fraction_terminal_and_coefficient_enumerator",
    } or record["limitations"] != [
        "This is one h4 legal checked-to heads-up river infrastructure audit.",
        "Response signatures identify generated rows; selector stability is not claimed.",
        "The bounded subject wall is campaign infrastructure time, not action latency.",
        "No preparation-bank, full-width, action, or strategy-quality result is emitted.",
    ]:
        raise ValueError("ADR-0349 methodology or limitations drifted")
    gates = record["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _EXPECTED_GATE_KEYS
        or any(value is not True for value in gates.values())
    ):
        raise ValueError("ADR-0349 gate vector is not an all-pass result")
    _verify_rows(record)
    _verify_evaluations(record)
    _verify_iteration_and_summary(record)
    _verify_conditioning_and_accounting(record)
    timing = record["timing"]
    if not isinstance(timing, dict) or set(timing) != {
        "exact_audit_and_plumbing_seconds",
        "subject_generation_seconds",
        "total_infrastructure_seconds",
    }:
        raise ValueError("ADR-0349 timing schema drifted")
    subject = float(timing["subject_generation_seconds"])
    audit = float(timing["exact_audit_and_plumbing_seconds"])
    total = float(timing["total_infrastructure_seconds"])
    if (
        float(record["total_seconds"]) != total
        or not 0.0 <= subject <= 60.0
        or not 0.0 <= audit <= 120.0
        or subject + audit != total
        or total > 120.0
    ):
        raise ValueError("ADR-0349 infrastructure timing drifted")
    return _deep_freeze(record)


def verify_adr0349_legal_h4_row_growth_result_artifact(
    path: Path | None = None,
) -> RetainedLegalH4RowGrowthResult:
    """Rebind ADR-0348's exact artifact without runner or solver calls."""

    verify_adr0349_result_source_and_dependencies()
    artifact_path = _ROOT / ADR0349_ARTIFACT_RELATIVE_PATH if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0349_ARTIFACT_BYTES:
        raise ValueError("ADR-0349 artifact byte count drifted")
    if sha256(raw).hexdigest() != ADR0349_ARTIFACT_SHA256:
        raise ValueError("ADR-0349 artifact SHA-256 drifted")
    record = _decode_strict_object(raw, source=str(artifact_path))
    if (
        json.dumps(record, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
        != raw
    ):
        raise ValueError("ADR-0349 artifact is not canonical retained JSON")
    frozen = verify_adr0349_legal_h4_row_growth_record(record)
    return RetainedLegalH4RowGrowthResult(
        record=frozen,
        source_commit=ADR0349_INVOCATION_SOURCE_COMMIT,
        total_seconds=float(record["total_seconds"]),
        response_rows=len(record["response_rows"]),
        generated_rows=sum(
            row["phase"] == "generated" for row in record["response_rows"]
        ),
        iterations=len(record["iterations"]),
    )


__all__ = [
    "ADR0349_ARTIFACT_BYTES",
    "ADR0349_ARTIFACT_RELATIVE_PATH",
    "ADR0349_ARTIFACT_SHA256",
    "ADR0349_CONFIG_SHA256",
    "ADR0349_FINAL_POLICY_SHA256",
    "ADR0349_GAME_PROVENANCE_SHA256",
    "ADR0349_GAME_STRUCTURAL_SHA256",
    "ADR0349_INVOCATION_SOURCE_COMMIT",
    "ADR0349_PUBLIC_SCHEMA_SHA256",
    "ADR0349_RESULT_PROTOCOL",
    "ADR0349_RESULT_PROTOCOL_SHA256",
    "ADR0349_ROOT_PUBLIC_STATE_SHA256",
    "ADR0349_SOURCE_POLICY_SHA256",
    "RetainedLegalH4RowGrowthResult",
    "verify_adr0349_legal_h4_row_growth_record",
    "verify_adr0349_legal_h4_row_growth_result_artifact",
    "verify_adr0349_result_source_and_dependencies",
]
