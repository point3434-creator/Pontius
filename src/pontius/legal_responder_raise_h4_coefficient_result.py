"""Solver-free owner for ADR-0347's retained legal h4 coefficients.

The prospective ADR-0346 runner is permanently closed.  This module reads
only its exact retained JSON artifact, verifies the source-sealed inputs, and
rebinds the serialized rational coefficient, endpoint, zero-sum, and gain
identities without constructing a game or invoking an evaluator or solver.
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


ADR0347_INVOCATION_SOURCE_COMMIT = (
    "5164ad75a56b3bc3e3c76df1e4e85c8c2955f3ba"
)
ADR0347_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/"
    "legal-responder-raise-h4-coefficient-differential-v1.json"
)
ADR0347_ARTIFACT_BYTES = 100_710
ADR0347_ARTIFACT_SHA256 = (
    "6dcbf8e44f1c3b2bd54694e0c1f6898082e71373846933bfaa116bc4f2c27255"
)
ADR0347_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-responder-raise-h4-coefficient-differential-v1.json"
)
ADR0347_CONFIG_SHA256 = (
    "e511be50649a2c1c401948d31c1245f9df890f31aceb4f53a8ef4c63c62803bc"
)
ADR0347_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0347_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0347_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0347_GAME_PROVENANCE_SHA256 = (
    "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/"
            "ADR-0345-retain-and-seal-the-legal-responder-raise-keystone.md"
        ),
        "expected_parent_artifact_sha256": (
            "experiments/results/responder-raise-semantics-keystone-v1.json"
        ),
        "expected_parent_result_owner_sha256": (
            "src/pontius/responder_raise_semantics_keystone_result.py"
        ),
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_coefficient_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_evaluation_sha256": "src/pontius/evaluation.py",
        "expected_exact_oracle_sha256": (
            "src/pontius/exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_exact_oracle_test_sha256": (
            "tests/test_exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_implementation_sha256": (
            "src/pontius/"
            "legal_responder_raise_h4_coefficient_differential.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_responder_raise_h4_coefficient_differential.py"
        ),
    }
)
_EXPECTED_SOURCE_HASHES = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "cf6fbd0518d4b14702598b50335a7e068352e9731349e10410000679624efeaf"
        ),
        "expected_parent_artifact_sha256": (
            "a7cbb0efca87ad3bf9e2a2105d10aa137daf68a763b68518d68e893bfc74be11"
        ),
        "expected_parent_result_owner_sha256": (
            "757c593081d78e7823cfa680b782385ddbb33badfe70d8ef907478c1ce8791b7"
        ),
        "expected_legal_kernel_sha256": (
            "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
        ),
        "expected_legal_game_sha256": (
            "4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250"
        ),
        "expected_coefficient_primitive_sha256": (
            "a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231"
        ),
        "expected_evaluation_sha256": (
            "c362fb1e294bb8bac722adf479df4d2f27ddcf8c26390c037ec88f858702cda8"
        ),
        "expected_exact_oracle_sha256": (
            "8d70297ab80055c5c77bdeefb82ff6cde817f6c57876059783046669b3a6945a"
        ),
        "expected_exact_oracle_test_sha256": (
            "5b0aeba06437386156451a7d66687b0274a14abbb138f96f8b2c1ee2bb84a330"
        ),
        "expected_implementation_sha256": (
            "e800aa343803c27744172404e1351e564e2817ce357c59bb602bbd6cb357caee"
        ),
        "expected_control_test_sha256": (
            "cbf1386a05fe53efbe6db4b7a0b9bdb3681a015980f4bb36b60a89979dd02502"
        ),
    }
)

_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "acting_br_identity_error",
        "axis",
        "config_sha256",
        "coverage_nonzero_final_histories",
        "decision",
        "endpoint_contexts",
        "endpoint_responder_selector_calls",
        "environment",
        "exact_affine_identity_mismatches",
        "exact_gain_identity_mismatches",
        "exact_oracle_sha256",
        "exact_zero_sum",
        "fixture",
        "gain_rows",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "implementation_sha256",
        "limitations",
        "maximum_affine_value_error",
        "maximum_coefficient_error",
        "maximum_float_exact_utility_error",
        "maximum_gain_value_error",
        "maximum_realization_error",
        "methodology",
        "parent_artifact_sha256",
        "passed",
        "payoff_rows",
        "policies",
        "public_schema_sha256",
        "quality_rows_serialized",
        "root_public_state_sha256",
        "root_raise_to_totals",
        "schema_version",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
        "table_seats",
        "timing",
        "topology",
        "total_seconds",
    }
)
_EXPECTED_GATE_KEYS = frozenset(
    {
        "acting_br_identity",
        "acting_information_set_count",
        "affine_value_identity",
        "behavioral_shortcut_rejection",
        "clean_git",
        "coefficient_identity",
        "coverage_response_counts",
        "coverage_response_identity",
        "dyadic_chance_mass",
        "endpoint_count",
        "endpoint_policy_identities",
        "exact_affine_identities",
        "exact_zero_sum",
        "final_response_variable_count",
        "finite",
        "float_exact_utility_identity",
        "full_and_short_final_sequence_coverage",
        "h4_hand_counts",
        "h4_provenance_identity",
        "joint_deal_count",
        "legal_root_universe",
        "parent_pass",
        "passed",
        "public_schema_identity",
        "realization_identity",
        "repeated_actor_topology",
        "root_state_identity",
        "row_counts",
        "sequence_variable_count",
        "source_policy_identity",
        "source_response_tape_identities",
        "structural_game_identity",
        "terminal_path_count",
        "total_time",
    }
)
_ENDPOINT_LABELS = (
    "source",
    "check_fold",
    "bet2_call",
    "bet3_fold",
    "bet3_call",
    "all_in_call",
)
_ENDPOINT_POLICY_SHA256S = (
    "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a",
    "cefb10c6a919d94e711cd97ab2e9341005de4539b5bcabb2fc7396671f6e0dd9",
    "ad830331dd680c08faa9600c71780a999966896c80bb5c6385565e6690cc6c5c",
    "2bdba607ee1c0e24f7a0837585c23dea2b30d1e013869bf7e1d964bdcd623882",
    "f1eb699121434682f27b2189c03ca445b76a93f73d0ca2707e079cd86fa41ba7",
    "02d451d822ca2b6ccc8a7fe5b480a058d322c13ffe9cee32ee667d24601b99dd",
)
_CONTEXT_POLICY_SHA256S = MappingProxyType(
    {
        "profile": _ENDPOINT_POLICY_SHA256S,
        "coverage_response": (
            "05844530e86ea58a474c50d8d1cdaf2ff56cc4196b96fc11583dcb0bd2f17547",
            "d6f1782a062402a3c377b23b40e7298a340b52b2337a980faef592596907c892",
            "e89ce53919353adf8efb3a6b4d351442efb844d84474ede79eae6882308ff7c9",
            "e5dddd75201a64a3e1903a7ffe6e4327d7005472a4de6203f70c0a0e5959cacb",
            "20b27909f06d213438655418cb5afef7b9aeb49f77019ef7bcdbccac1125c2e9",
            "58f444aec6b2bff34a2d1322c052e85c0b07200a059b833053aecedd3d561b22",
        ),
        "responder_best_response": (
            "d8143b85edc3d7601f1ceb2fcc0476350837211e06c6ae76769b304edd8e487a",
            "bd0c4aef96472948c0e79b52c7bc44950ff84182d3a7afbf9805e57abc398f59",
            "2717ab475b186dca65cc04c271b9e237cf8a4b0d4cccf52851e68adc2e548a2d",
            "55d3791c8ac4ef0ff2393116ef81730853434b95046abdf375aaa61e7ff2da66",
            "a6fb7d24b36624790a42ce780ef203447d3ef9756276527ac81661d959dbb92e",
            "44cc6c994522c16dd25d10099e95105735b6213d8380b8b3af6229565bf64124",
        ),
    }
)
_ROW_SHA256S = MappingProxyType(
    {
        "profile_player0": (
            "ffc3e199218a8e657e494a0452c1b345db8c2ad23f3943925fe4d8aa6712c16b"
        ),
        "profile_player1": (
            "2c0ce325dbea30d7e4fb18b2ff592626c2bfe0bfdfb79bbcd0b43463beebabd2"
        ),
        "coverage_response_player1": (
            "61846cb3218f68e395ffbba1b4d04f0e0c6a3a78e13c60f9bcd49927bcf6d4b8"
        ),
        "best_response_player1": (
            "26dc0d9c085e81693988616145696e0db66b9e52a8e56070f464d09ae922d189"
        ),
        "acting_gain": (
            "7be24d40786a55761142e3bfdf230f5b6ddbac5320703cd44050d4d2f345f4a5"
        ),
        "responder_gain": (
            "3c1b73c33f1f5ede4ea8a9ccf415c5337a3c033ae4a5549177a19324b0543d90"
        ),
    }
)

_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0347_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0347_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0347_ARTIFACT_SHA256,
    "config_sha256": ADR0347_CONFIG_SHA256,
    "endpoint_policy_sha256s": list(_ENDPOINT_POLICY_SHA256S),
    "game_provenance_sha256": ADR0347_GAME_PROVENANCE_SHA256,
    "game_structural_sha256": ADR0347_GAME_STRUCTURAL_SHA256,
    "invocation_source_commit": ADR0347_INVOCATION_SOURCE_COMMIT,
    "public_schema_sha256": ADR0347_PUBLIC_SCHEMA_SHA256,
    "root_public_state_sha256": ADR0347_ROOT_PUBLIC_STATE_SHA256,
    "row_sha256s": dict(_ROW_SHA256S),
    "source_hashes": dict(_EXPECTED_SOURCE_HASHES),
    "version": "adr0347-legal-h4-coefficient-result-protocol-v1",
}
ADR0347_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0347_RESULT_PROTOCOL_SHA256 = sha256(
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
            raise ValueError(f"duplicate JSON key in ADR-0347 artifact: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"nonfinite JSON number in ADR-0347 artifact: {token}")


def _decode_strict_object(raw: bytes, *, source: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid ADR-0347 JSON in {source}") from exc
    if not isinstance(decoded, dict):
        raise TypeError(f"ADR-0347 JSON in {source} must be an object")
    return decoded


def _raw_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"ADR-0347 required path is unavailable: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256(canonical).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _require_finite_numbers(value: Any, *, path: str = "result") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite_numbers(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_finite_numbers(item, path=f"{path}[{index}]")
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError(f"ADR-0347 nonfinite value at {path}")


def _require_zero(value: Any, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"ADR-0347 {field} must be a numeric zero")
    if value != 0:
        raise ValueError(f"ADR-0347 {field} is not zero")


def _fraction(record: Any, *, field: str) -> Fraction:
    if not isinstance(record, dict) or set(record) != {"numerator", "denominator"}:
        raise TypeError(f"ADR-0347 {field} is not an exact fraction record")
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
        raise ValueError(f"ADR-0347 {field} is not reduced and positive")
    return Fraction(numerator, denominator)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _hex_fraction(value: Any, *, field: str) -> Fraction:
    if not isinstance(value, str):
        raise TypeError(f"ADR-0347 {field} must be a hexadecimal float string")
    try:
        parsed = float.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"ADR-0347 {field} is not hexadecimal Float64") from exc
    if not isfinite(parsed) or parsed.hex() != value:
        raise ValueError(f"ADR-0347 {field} is not canonical finite Float64")
    return Fraction.from_float(parsed)


@dataclass(frozen=True, slots=True)
class RetainedLegalH4CoefficientResult:
    """Immutable interpretation of the exact retained h4 artifact."""

    record: Mapping[str, Any]
    source_commit: str
    total_seconds: float
    coefficient_rows: int
    coefficients_per_row: int

    def __post_init__(self) -> None:
        if not isinstance(self.record, Mapping) or not self.record:
            raise TypeError("retained legal h4 record must be a mapping")
        if self.source_commit != ADR0347_INVOCATION_SOURCE_COMMIT:
            raise ValueError("retained legal h4 source commit drifted")
        if not isinstance(self.total_seconds, float) or not isfinite(
            self.total_seconds
        ):
            raise ValueError("retained legal h4 total seconds is invalid")
        if self.coefficient_rows != 6 or self.coefficients_per_row != 32:
            raise ValueError("retained legal h4 coefficient dimensions drifted")


def verify_adr0347_result_source_and_dependencies() -> str:
    """Verify the read-only owner and all ADR-0346 source-sealed inputs."""

    from .legal_responder_raise_h4_coefficient_result_seal import (
        ADR0347_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0347_RESULT_SOURCE_MANIFEST,
    )

    module_path = Path(__file__).resolve()
    actual_module = _canonical_lf_sha256(module_path)
    if ADR0347_RESULT_SOURCE_MANIFEST != {module_path.name: actual_module}:
        raise RuntimeError("ADR-0347 result-owner source closure drifted")
    if sealed_protocol != ADR0347_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0347 result protocol drifted")

    config_path = _ROOT / ADR0347_CONFIG_RELATIVE_PATH
    if _raw_sha256(config_path) != ADR0347_CONFIG_SHA256:
        raise RuntimeError("ADR-0347 source-sealed config drifted")
    config = _decode_strict_object(config_path.read_bytes(), source=str(config_path))
    for field, relative_path in _SOURCE_PATHS.items():
        expected = _EXPECTED_SOURCE_HASHES[field]
        if config.get(field) != expected:
            raise RuntimeError(f"ADR-0347 config identity drifted: {field}")
        if _raw_sha256(_ROOT / relative_path) != expected:
            raise RuntimeError(f"ADR-0347 source input drifted: {relative_path}")
    return actual_module


def _verify_fixture(record: dict[str, Any]) -> None:
    fixture = record["fixture"]
    if not isinstance(fixture, dict) or set(fixture) != {
        "chance_mass_exact",
        "chance_probabilities",
        "chance_probabilities_dyadic",
        "hand_counts",
        "joint_deals",
        "terminal_paths",
    }:
        raise ValueError("ADR-0347 fixture schema drifted")
    probabilities = tuple(
        _fraction(item, field=f"fixture.chance_probabilities[{index}]")
        for index, item in enumerate(fixture["chance_probabilities"])
    )
    if (
        fixture["chance_mass_exact"] is not True
        or fixture["chance_probabilities_dyadic"] is not True
        or fixture["hand_counts"] != [4, 4]
        or fixture["joint_deals"] != 16
        or fixture["terminal_paths"] != 176
        or len(probabilities) != 16
        or sum(probabilities, Fraction(0)) != 1
        or any(
            value.denominator & (value.denominator - 1)
            for value in probabilities
        )
    ):
        raise ValueError("ADR-0347 exact h4 fixture identity drifted")


def _verify_policies(record: dict[str, Any]) -> None:
    policies = record["policies"]
    if not isinstance(policies, dict) or set(policies) != {
        "acting_best_response_calls",
        "acting_best_response_sha256",
        "acting_best_response_value_hex",
        "coverage_response_counts",
        "coverage_response_sha256",
        "endpoint_responder_selector_calls",
        "endpoint_sha256s",
        "responder_best_response_calls",
        "responder_best_response_sha256",
        "responder_best_response_value_hex",
        "source_sha256",
    }:
        raise ValueError("ADR-0347 policy schema drifted")
    endpoints = policies["endpoint_sha256s"]
    endpoint_identity = tuple(
        (item.get("label"), item.get("sha256"))
        for item in endpoints
        if isinstance(item, dict)
    )
    if (
        policies["source_sha256"] != _ENDPOINT_POLICY_SHA256S[0]
        or endpoint_identity
        != tuple(zip(_ENDPOINT_LABELS, _ENDPOINT_POLICY_SHA256S, strict=True))
        or policies["coverage_response_sha256"]
        != "310c6206a7f7cadad277d0a76f12d2d81dd00e7fd14aa2de35ae7f80f19cc34f"
        or policies["coverage_response_counts"]
        != {"raise-to-4": 8, "fold": 2, "call": 2}
        or policies["responder_best_response_sha256"]
        != "778a91ab318ea0c94d1baa8dcfe9481ed6155604cc964a6b014720b0b20877f8"
        or _hex_fraction(
            policies["responder_best_response_value_hex"],
            field="responder best-response value",
        )
        != Fraction(1647, 512)
        or policies["acting_best_response_sha256"]
        != "83b57620097d496624aabfa49fdba1ab64ccb5cd519a9daf20130ade55f7e908"
        or _hex_fraction(
            policies["acting_best_response_value_hex"],
            field="acting best-response value",
        )
        != Fraction(-45, 64)
        or policies["responder_best_response_calls"] != 1
        or policies["acting_best_response_calls"] != 1
        or policies["endpoint_responder_selector_calls"] != 0
    ):
        raise ValueError("ADR-0347 policy identity drifted")


def _verify_endpoint_contexts(
    record: dict[str, Any],
) -> dict[str, dict[str, tuple[Fraction, Fraction]]]:
    contexts = record["endpoint_contexts"]
    if not isinstance(contexts, dict) or set(contexts) != set(
        _CONTEXT_POLICY_SHA256S
    ):
        raise ValueError("ADR-0347 endpoint-context schema drifted")
    rebound: dict[str, dict[str, tuple[Fraction, Fraction]]] = {}
    expected_keys = {
        "endpoint",
        "exact_utilities",
        "float_exact_utility_error",
        "float_utilities_hex",
        "policy_sha256",
        "realization_error",
    }
    for context, expected_digests in _CONTEXT_POLICY_SHA256S.items():
        rows = contexts[context]
        if not isinstance(rows, list) or len(rows) != len(_ENDPOINT_LABELS):
            raise ValueError(f"ADR-0347 {context} endpoint count drifted")
        rebound[context] = {}
        for index, (row, endpoint, digest) in enumerate(
            zip(rows, _ENDPOINT_LABELS, expected_digests, strict=True)
        ):
            if not isinstance(row, dict) or set(row) != expected_keys:
                raise ValueError(f"ADR-0347 {context} endpoint schema drifted")
            exact = tuple(
                _fraction(
                    item,
                    field=f"endpoint_contexts.{context}[{index}].exact",
                )
                for item in row["exact_utilities"]
            )
            floating = tuple(
                _hex_fraction(
                    item,
                    field=f"endpoint_contexts.{context}[{index}].float",
                )
                for item in row["float_utilities_hex"]
            )
            _require_zero(
                row["realization_error"],
                field=f"endpoint_contexts.{context}[{index}].realization_error",
            )
            _require_zero(
                row["float_exact_utility_error"],
                field=f"endpoint_contexts.{context}[{index}].utility_error",
            )
            if (
                row["endpoint"] != endpoint
                or row["policy_sha256"] != digest
                or len(exact) != 2
                or exact != floating
                or sum(exact, Fraction(0)) != 0
            ):
                raise ValueError(f"ADR-0347 {context} endpoint identity drifted")
            rebound[context][endpoint] = (exact[0], exact[1])
    return rebound


def _verify_axis(
    coordinates: tuple[tuple[str, str], ...],
) -> None:
    if len(coordinates) != 32 or len(set(coordinates)) != 32:
        raise ValueError("ADR-0347 sequence coordinate width drifted")
    grouped: dict[str, set[str]] = {}
    for key, action in coordinates:
        if (
            not key.startswith(
                "legal-river|structure="
                f"{ADR0347_GAME_STRUCTURAL_SHA256}|p0|hand="
            )
            or action
            not in {"check", "raise-to-2", "raise-to-3", "raise-to-4", "fold", "call"}
        ):
            raise ValueError("ADR-0347 sequence coordinate semantics drifted")
        grouped.setdefault(key, set()).add(action)
    root = [actions for key, actions in grouped.items() if key.endswith("history=root")]
    final = [actions for key, actions in grouped.items() if "p1:raise-to-4" in key]
    if (
        len(grouped) != 12
        or len(root) != 4
        or any(
            actions != {"check", "raise-to-2", "raise-to-3", "raise-to-4"}
            for actions in root
        )
        or len(final) != 8
        or any(actions != {"fold", "call"} for actions in final)
    ):
        raise ValueError("ADR-0347 repeated-actor sequence axis drifted")


def _verify_rows(
    record: dict[str, Any],
    contexts: Mapping[str, Mapping[str, tuple[Fraction, Fraction]]],
) -> dict[str, tuple[Fraction, dict[tuple[str, str], Fraction]]]:
    rows = record["payoff_rows"] + record["gain_rows"]
    if not isinstance(record["payoff_rows"], list) or not isinstance(
        record["gain_rows"], list
    ):
        raise TypeError("ADR-0347 coefficient rows must be lists")
    if len(record["payoff_rows"]) != 4 or len(record["gain_rows"]) != 2:
        raise ValueError("ADR-0347 coefficient row count drifted")
    expected_row_keys = {
        "coefficient_entries",
        "coefficients",
        "constant_exact",
        "constant_subject_hex",
        "endpoint_values",
        "exact_row_sha256",
        "label",
        "maximum_coefficient_error",
    }
    expected_coefficient_keys = {
        "absolute_error",
        "action",
        "exact",
        "information_key",
        "subject_hex",
    }
    expected_endpoint_keys = {
        "absolute_error",
        "direct_value_hex",
        "endpoint",
        "exact_identity",
        "subject_value_hex",
    }
    rebound: dict[str, tuple[Fraction, dict[tuple[str, str], Fraction]]] = {}
    shared_axis: tuple[tuple[str, str], ...] | None = None
    endpoint_fractions: dict[str, dict[str, Fraction]] = {}
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != expected_row_keys:
            raise ValueError("ADR-0347 coefficient row schema drifted")
        label = row["label"]
        if label not in _ROW_SHA256S or label in rebound:
            raise ValueError("ADR-0347 coefficient row label drifted")
        coefficients: dict[tuple[str, str], Fraction] = {}
        coordinate_order: list[tuple[str, str]] = []
        if row["coefficient_entries"] != 32 or len(row["coefficients"]) != 32:
            raise ValueError(f"ADR-0347 {label} coefficient width drifted")
        for coefficient_index, coefficient in enumerate(row["coefficients"]):
            if (
                not isinstance(coefficient, dict)
                or set(coefficient) != expected_coefficient_keys
            ):
                raise ValueError(f"ADR-0347 {label} coefficient schema drifted")
            coordinate = (
                coefficient["information_key"],
                coefficient["action"],
            )
            exact = _fraction(
                coefficient["exact"],
                field=f"{label}.coefficients[{coefficient_index}]",
            )
            _require_zero(
                coefficient["absolute_error"],
                field=f"{label}.coefficients[{coefficient_index}].error",
            )
            if (
                coordinate in coefficients
                or _hex_fraction(
                    coefficient["subject_hex"],
                    field=f"{label}.coefficients[{coefficient_index}].subject",
                )
                != exact
            ):
                raise ValueError(f"ADR-0347 {label} coefficient identity drifted")
            coefficients[coordinate] = exact
            coordinate_order.append(coordinate)
        axis = tuple(coordinate_order)
        if shared_axis is None:
            _verify_axis(axis)
            shared_axis = axis
        elif axis != shared_axis:
            raise ValueError("ADR-0347 coefficient row axes drifted")

        constant = _fraction(row["constant_exact"], field=f"{label}.constant")
        if _hex_fraction(
            row["constant_subject_hex"], field=f"{label}.constant_subject"
        ) != constant:
            raise ValueError(f"ADR-0347 {label} constant identity drifted")
        _require_zero(
            row["maximum_coefficient_error"],
            field=f"{label}.maximum_coefficient_error",
        )
        digest_payload = {
            "constant": _fraction_record(constant),
            "coefficients": [
                {
                    "information_key": key,
                    "action": action,
                    "value": _fraction_record(value),
                }
                for (key, action), value in sorted(
                    coefficients.items(), key=lambda item: item[0]
                )
            ],
        }
        if (
            row["exact_row_sha256"] != _ROW_SHA256S[label]
            or _canonical_sha256(digest_payload) != _ROW_SHA256S[label]
        ):
            raise ValueError(f"ADR-0347 {label} exact row digest drifted")

        endpoints = row["endpoint_values"]
        if not isinstance(endpoints, list) or len(endpoints) != 6:
            raise ValueError(f"ADR-0347 {label} endpoint count drifted")
        endpoint_fractions[label] = {}
        for endpoint_index, (endpoint_row, endpoint) in enumerate(
            zip(endpoints, _ENDPOINT_LABELS, strict=True)
        ):
            if (
                not isinstance(endpoint_row, dict)
                or set(endpoint_row) != expected_endpoint_keys
            ):
                raise ValueError(f"ADR-0347 {label} endpoint schema drifted")
            direct = _hex_fraction(
                endpoint_row["direct_value_hex"],
                field=f"{label}.endpoint[{endpoint_index}].direct",
            )
            subject = _hex_fraction(
                endpoint_row["subject_value_hex"],
                field=f"{label}.endpoint[{endpoint_index}].subject",
            )
            _require_zero(
                endpoint_row["absolute_error"],
                field=f"{label}.endpoint[{endpoint_index}].error",
            )
            if (
                endpoint_row["endpoint"] != endpoint
                or endpoint_row["exact_identity"] is not True
                or direct != subject
            ):
                raise ValueError(f"ADR-0347 {label} endpoint identity drifted")
            endpoint_fractions[label][endpoint] = direct
        rebound[label] = constant, coefficients

    if set(rebound) != set(_ROW_SHA256S):
        raise ValueError("ADR-0347 coefficient row inventory drifted")
    payoff_context = {
        "profile_player0": ("profile", 0),
        "profile_player1": ("profile", 1),
        "coverage_response_player1": ("coverage_response", 1),
        "best_response_player1": ("responder_best_response", 1),
    }
    for label, (context, player) in payoff_context.items():
        for endpoint in _ENDPOINT_LABELS:
            if endpoint_fractions[label][endpoint] != contexts[context][endpoint][player]:
                raise ValueError(f"ADR-0347 {label} direct endpoint drifted")
    for endpoint in _ENDPOINT_LABELS:
        acting_gain = Fraction(-45, 64) - contexts["profile"][endpoint][0]
        response_gain = (
            contexts["responder_best_response"][endpoint][1]
            - contexts["profile"][endpoint][1]
        )
        if (
            endpoint_fractions["acting_gain"][endpoint] != acting_gain
            or endpoint_fractions["responder_gain"][endpoint] != response_gain
        ):
            raise ValueError("ADR-0347 derived endpoint gain drifted")
    return rebound


def _verify_exact_row_algebra(
    rows: Mapping[str, tuple[Fraction, Mapping[tuple[str, str], Fraction]]],
) -> None:
    profile0_constant, profile0 = rows["profile_player0"]
    profile1_constant, profile1 = rows["profile_player1"]
    response_constant, response = rows["best_response_player1"]
    acting_gain_constant, acting_gain = rows["acting_gain"]
    response_gain_constant, response_gain = rows["responder_gain"]
    if (
        profile0_constant + profile1_constant != 0
        or any(profile0[key] + profile1[key] != 0 for key in profile0)
        or acting_gain_constant != Fraction(-45, 64) - profile0_constant
        or any(acting_gain[key] != -profile0[key] for key in profile0)
        or response_gain_constant != response_constant - profile1_constant
        or any(
            response_gain[key] != response[key] - profile1[key]
            for key in profile1
        )
    ):
        raise ValueError("ADR-0347 exact zero-sum or gain-row algebra drifted")


def verify_adr0347_legal_h4_coefficient_result_artifact(
    path: Path | None = None,
) -> RetainedLegalH4CoefficientResult:
    """Rebind ADR-0346's exact artifact without runner or solver calls."""

    verify_adr0347_result_source_and_dependencies()
    artifact_path = (
        _ROOT / ADR0347_ARTIFACT_RELATIVE_PATH if path is None else path
    )
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0347_ARTIFACT_BYTES:
        raise ValueError("ADR-0347 artifact byte count drifted")
    if sha256(raw).hexdigest() != ADR0347_ARTIFACT_SHA256:
        raise ValueError("ADR-0347 artifact SHA-256 drifted")
    record = _decode_strict_object(raw, source=str(artifact_path))
    if set(record) != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("ADR-0347 top-level result schema drifted")
    if (
        json.dumps(record, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
        != raw
    ):
        raise ValueError("ADR-0347 artifact is not canonical retained JSON")
    _require_finite_numbers(record)

    environment = record["environment"]
    git = environment.get("git", {}) if isinstance(environment, dict) else {}
    if (
        record["schema_version"] != 1
        or record["status"]
        != "legal_responder_raise_h4_coefficient_differential_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_legal_responder_raise_h4_row_growth_preregistration"
        or record["strategy_quality_claim"] is not None
        or record["strategy_labels_generated"] != 0
        or record["quality_rows_serialized"] != 0
        or record["endpoint_responder_selector_calls"] != 0
        or record["config_sha256"] != ADR0347_CONFIG_SHA256
        or record["implementation_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_implementation_sha256"]
        or record["exact_oracle_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_exact_oracle_sha256"]
        or record["parent_artifact_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_parent_artifact_sha256"]
        or record["root_public_state_sha256"]
        != ADR0347_ROOT_PUBLIC_STATE_SHA256
        or record["public_schema_sha256"] != ADR0347_PUBLIC_SCHEMA_SHA256
        or record["game_structural_sha256"] != ADR0347_GAME_STRUCTURAL_SHA256
        or record["game_provenance_sha256"] != ADR0347_GAME_PROVENANCE_SHA256
        or record["table_seats"] != [2, 1]
        or record["root_raise_to_totals"] != [2, 3, 4]
        or git
        != {
            "commit": ADR0347_INVOCATION_SOURCE_COMMIT,
            "dirty": False,
            "strict_status": True,
        }
        or environment.get("runtime")
        != {"backend": "cpu_float64_subject_fraction_teacher"}
    ):
        raise ValueError("ADR-0347 retained identity drifted")

    if record["methodology"] != {
        "betting_authority": "NoLimitBettingState",
        "quality_rows": 0,
        "response_tapes": "source_fixed_no_endpoint_selector_recomputation",
        "strategy_labels": 0,
        "subject": "float64_direct_sequence_form_open_axis_traversal",
        "teacher": "independent_fraction_terminal_enumerator",
    }:
        raise ValueError("ADR-0347 methodology drifted")
    if record["limitations"] != [
        "This is one h4 private-axis coefficient identity on the ADR-0345 tree.",
        "Response tapes are fixed; selector stability is not measured.",
        "Direct traversal cost is not response-row capacity or action latency.",
        "No policy is optimized and no production action or quality label is emitted.",
    ]:
        raise ValueError("ADR-0347 limitations drifted")
    gates = record["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _EXPECTED_GATE_KEYS
        or any(value is not True for value in gates.values())
    ):
        raise ValueError("ADR-0347 gate vector is not an all-pass result")

    _verify_fixture(record)
    if record["topology"] != {
        "behavioral_shortcut_rejected": True,
        "path_single_visit": False,
        "repeated_player": 0,
        "witness": [
            "RiverDeal(player0=(15, 19), player1=(26, 35))",
            "raise-to-2",
            "raise-to-4",
        ],
    }:
        raise ValueError("ADR-0347 repeated-actor topology drifted")
    if record["axis"] != {
        "acting_player": 0,
        "information_sets": 12,
        "sequence_variables": 32,
        "final_response_variables": 16,
    }:
        raise ValueError("ADR-0347 sequence-axis summary drifted")
    _verify_policies(record)
    contexts = _verify_endpoint_contexts(record)
    rows = _verify_rows(record, contexts)
    _verify_exact_row_algebra(rows)

    for field in (
        "acting_br_identity_error",
        "exact_affine_identity_mismatches",
        "exact_gain_identity_mismatches",
        "maximum_affine_value_error",
        "maximum_coefficient_error",
        "maximum_float_exact_utility_error",
        "maximum_gain_value_error",
        "maximum_realization_error",
    ):
        _require_zero(record[field], field=field)
    if (
        record["exact_zero_sum"] is not True
        or record["coverage_nonzero_final_histories"]
        != ["raise-to-2", "raise-to-3"]
    ):
        raise ValueError("ADR-0347 exact closure witness drifted")
    timing = record["timing"]
    total_seconds = float(record["total_seconds"])
    if (
        not isinstance(timing, dict)
        or set(timing)
        != {"float_subject_seconds", "fraction_oracle_seconds", "total_seconds"}
        or float(timing["total_seconds"]) != total_seconds
        or not 0.0 <= float(timing["float_subject_seconds"]) <= total_seconds
        or not 0.0 <= float(timing["fraction_oracle_seconds"]) <= total_seconds
        or not total_seconds <= 60.0
    ):
        raise ValueError("ADR-0347 infrastructure timing witness drifted")

    return RetainedLegalH4CoefficientResult(
        record=_deep_freeze(record),
        source_commit=ADR0347_INVOCATION_SOURCE_COMMIT,
        total_seconds=total_seconds,
        coefficient_rows=len(rows),
        coefficients_per_row=32,
    )


__all__ = [
    "ADR0347_ARTIFACT_BYTES",
    "ADR0347_ARTIFACT_RELATIVE_PATH",
    "ADR0347_ARTIFACT_SHA256",
    "ADR0347_CONFIG_SHA256",
    "ADR0347_GAME_PROVENANCE_SHA256",
    "ADR0347_GAME_STRUCTURAL_SHA256",
    "ADR0347_INVOCATION_SOURCE_COMMIT",
    "ADR0347_PUBLIC_SCHEMA_SHA256",
    "ADR0347_RESULT_PROTOCOL",
    "ADR0347_RESULT_PROTOCOL_SHA256",
    "ADR0347_ROOT_PUBLIC_STATE_SHA256",
    "RetainedLegalH4CoefficientResult",
    "verify_adr0347_legal_h4_coefficient_result_artifact",
    "verify_adr0347_result_source_and_dependencies",
]
