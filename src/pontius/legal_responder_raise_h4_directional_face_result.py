"""Solver-free owner for ADR-0356's retained directional-face result.

The ADR-0355 runner is permanently closed.  This module reads only its exact
JSON artifact and committed text inputs.  It reconstructs every serialized
Fraction, factor product, reachable-support quotient, logical-work identity,
normal-fan partition, affine maximum envelope, point/fan seam, aggregate, and
gate without importing a game, evaluator, selector, optimizer, runner, or
write path.
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


ADR0356_INVOCATION_SOURCE_COMMIT = (
    "5331d0a6e142a97be10678d59e76aa7f1cc9a63e"
)
ADR0356_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-directional-face-v1.json"
)
ADR0356_ARTIFACT_BYTES = 3_888_072
ADR0356_ARTIFACT_SHA256 = (
    "5e3473639e67e0a24e21f3c516239c35d4bb7ccb17a6de8d74a5320428af1b49"
)
ADR0356_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-responder-raise-h4-directional-face-v1.json"
)
ADR0356_CONFIG_SHA256 = (
    "5305d2fa43b386d1a7b58bf2dc96943d581013e80ad5f9966438bf11b3289fa7"
)
ADR0356_RUNNER_SHA256 = (
    "c7196eb26081c136da37b6ef0098c9ad9813bc78205ab4ea2f6b491a93848c5f"
)
ADR0356_PARENT_PROTOCOL_SHA256 = (
    "cfd37e22b4e3e09321b20f6d6f3bef93f4b8fd35af6ecd13d2166ba3aee7dabf"
)
ADR0356_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0356_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0356_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0356_GAME_PROVENANCE_SHA256 = (
    "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
)
ADR0356_SOURCE_POLICY_SHA256 = (
    "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
)


_ROOT = Path(__file__).resolve().parents[2]
_MODULE = Path(__file__)
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/ADR-0354-seal-the-exact-directional-face-oracle.md"
        ),
        "expected_parent_source_seal_sha256": (
            "src/pontius/exact_directional_face_oracle_seal.py"
        ),
        "expected_directional_face_oracle_sha256": (
            "src/pontius/exact_directional_face_oracle.py"
        ),
        "expected_tie_conformance_sha256": (
            "src/pontius/tie_semantics_conformance.py"
        ),
        "expected_directional_face_controls_sha256": (
            "tests/test_exact_directional_face_oracle.py"
        ),
        "expected_tie_conformance_controls_sha256": (
            "tests/test_tie_semantics_conformance.py"
        ),
        "expected_source_seal_controls_sha256": (
            "tests/test_exact_directional_face_oracle_seal.py"
        ),
        "expected_exact_fan_sha256": "src/pontius/exact_selector_fan.py",
        "expected_exact_selector_oracle_sha256": (
            "src/pontius/exact_selector_window_oracle.py"
        ),
        "expected_exact_sequence_oracle_sha256": (
            "src/pontius/exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": (
            "src/pontius/legal_river_continuation.py"
        ),
        "expected_fixture_sha256": "src/pontius/legal_h4_selector_fixture.py",
        "expected_direction_compiler_sha256": (
            "src/pontius/legal_h4_selector_directions.py"
        ),
        "expected_cfr_sha256": "src/pontius/cfr.py",
        "expected_generation_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_parent_result_owner_sha256": (
            "src/pontius/legal_responder_raise_h4_row_growth_result.py"
        ),
        "expected_runner_harness_sha256": "src/pontius/runner_harness.py",
        "expected_strict_loader_sha256": "src/pontius/runner_harness_v2.py",
        "expected_implementation_sha256": (
            "src/pontius/legal_responder_raise_h4_directional_face.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_responder_raise_h4_directional_face.py"
        ),
    }
)
_TOP_KEYS = frozenset(
    {
        "aggregate",
        "analysis_seconds",
        "config_sha256",
        "decision",
        "direction_descriptors",
        "directions",
        "environment",
        "face_semantics",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "implementation_sha256",
        "limitations",
        "methodology",
        "parent_protocol_sha256",
        "passed",
        "public_schema_sha256",
        "quality_rows_serialized",
        "root_public_state_sha256",
        "schedule",
        "schema_version",
        "scientific_payload_bytes",
        "source_policy_sha256",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
    }
)
_FACE_KEYS = frozenset(
    {
        "acting_player",
        "deviation_gain",
        "factor_sha256",
        "information_sets",
        "maximum_gain_slope",
        "maximum_response_slope",
        "maximum_slope_tape",
        "minimum_gain_slope",
        "minimum_response_slope",
        "minimum_slope_tape",
        "profile_utility",
        "profile_utility_slope",
        "reachable_support_cardinality",
        "response_value",
        "scale",
        "target_player",
        "total_function_cardinality",
        "work",
    }
)
_FACTOR_KEYS = frozenset(
    {
        "actions",
        "information_key",
        "maximizing_actions",
        "maximum_local_slope",
        "maximum_slope_action",
        "minimum_local_slope",
        "minimum_slope_action",
        "parent",
        "positive_counterfactual_support",
        "state_count",
    }
)
_WORK_KEYS = frozenset(
    {
        "cardinality_linear_work_ceiling",
        "information_sets",
        "lexicographic_passes",
        "materialized_response_tapes",
        "maximum_action_choice_inspections",
        "maximum_action_score_terms",
        "maximum_continuation_node_evaluations",
        "minimum_action_choice_inspections",
        "minimum_action_score_terms",
        "minimum_continuation_node_evaluations",
        "per_pass_linear_work_ceiling",
        "reachable_cardinality_additions",
        "reachable_cardinality_bit_length",
        "reachable_cardinality_multiplications",
        "sequence_variables",
        "target_action_edges",
        "total_cardinality_bit_length",
        "total_cardinality_multiplications",
        "total_logical_work_units",
        "tree_edges",
        "tree_nodes",
    }
)
_CHECK_KEYS = frozenset(
    {
        "exact_bit_lengths",
        "gain_identity",
        "legacy_breakpoint_identity",
        "linear_cardinality_work",
        "linear_pass_work",
        "reachable_cardinality_order",
        "schedule_fan_face_identity",
        "slope_order",
        "total_cardinality_identity",
        "two_independent_passes",
        "zero_materialized_tapes",
    }
)
_GATE_KEYS = frozenset(
    {
        "analysis_wall",
        "clean_git_state",
        "complete_fan_face_seam",
        "direction_identity",
        "dual_cardinality_columns",
        "exact_bit_lengths",
        "finite",
        "fixture_identity",
        "gain_identity",
        "legacy_breakpoint_identity",
        "linear_logical_work",
        "no_face_cardinality_bound",
        "no_target_outcome_gate",
        "parent_pass",
        "passed",
        "schedule_fan_face_identity",
        "scientific_payload_bytes",
        "slope_order",
        "subject_wall",
        "two_independent_passes",
        "zero_materialized_tapes",
    }
)
_FAN_STATES = frozenset({"fixed", "tie_unresolved", "switched"})
_LIMITATIONS = (
    "This is one finite h4 checked-to heads-up river diagnostic.",
    "Cardinality, slope, crossing, and tie observations are outcomes.",
    "The fan-piece bound is not an active-face-cardinality bound.",
    "Infrastructure walls are not 15-second action-clock latency.",
    "No full-width, multiway, action, quality, or strength result exists.",
)
_EXPECTED_AGGREGATE = MappingProxyType(
    {
        "composition_face_samples": 28,
        "crossings": 2,
        "face_observations": 164,
        "fan_cells": 12,
        "fan_points": 18,
        "fan_segments": 10,
        "materialized_response_tapes": 0,
        "maximum_reachable_cardinality_bit_length": 2,
        "maximum_reachable_support_cardinality": 2,
        "maximum_total_cardinality_bit_length": 17,
        "maximum_total_function_cardinality": 104_976,
        "maximum_tree_nodes": 273,
        "schedule_face_calls": 136,
        "sections": 8,
        "total_logical_work_units": 147_418,
    }
)


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0356_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0356_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0356_ARTIFACT_SHA256,
    "authority": "development_diagnostic_only_successor_requires_preregistration",
    "config_sha256": ADR0356_CONFIG_SHA256,
    "expected_aggregate": tuple(sorted(_EXPECTED_AGGREGATE.items())),
    "invocation_source_commit": ADR0356_INVOCATION_SOURCE_COMMIT,
    "parent_protocol_sha256": ADR0356_PARENT_PROTOCOL_SHA256,
    "runner_sha256": ADR0356_RUNNER_SHA256,
    "version": "adr0356-legal-h4-directional-face-result-v1",
}
ADR0356_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0356_RESULT_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _RESULT_PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


@dataclass(frozen=True, slots=True)
class VerifiedLegalH4DirectionalFaceResult:
    """Read-only, solver-free verification of the sole ADR-0355 artifact."""

    record: Mapping[str, Any]
    source_commit: str
    artifact_sha256: str
    artifact_bytes: int


@dataclass(frozen=True, slots=True)
class _FaceView:
    scale: Fraction
    total_cardinality: int
    reachable_cardinality: int
    minimum_tape: tuple[tuple[str, str], ...]
    maximum_tape: tuple[tuple[str, str], ...]
    factors: Mapping[str, Mapping[str, Any]]
    tree_nodes: int
    total_work: int
    materialized_tapes: int


def _canonical_hash(value: object) -> str:
    rendered = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(rendered.encode("utf-8")).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"directional-face JSON duplicates key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"directional-face JSON contains non-finite token {token}")


def _load_json(raw: bytes) -> dict[str, Any]:
    try:
        record = json.loads(
            raw,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("directional-face artifact is not strict UTF-8 JSON") from error
    if not isinstance(record, dict):
        raise ValueError("directional-face artifact root is not an object")
    return record


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} is not an object")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} contains a non-string key")
    return value


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} is not a list")
    return value


def _keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} fields differ")


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} is not an integer at least {minimum}")
    return value


def _finite_float(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} is not numerical")
    result = float(value)
    if not isfinite(result) or result < minimum:
        raise ValueError(f"{label} is not finite and bounded")
    return result


def _signed_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} is not an integer")
    return value


def _exact_fraction(value: Any, label: str) -> Fraction:
    row = _mapping(value, label)
    _keys(row, frozenset({"numerator", "denominator"}), label)
    numerator = _signed_integer(row["numerator"], f"{label}.numerator")
    denominator = _integer(row["denominator"], f"{label}.denominator", minimum=1)
    if gcd(abs(numerator), denominator) != 1:
        raise ValueError(f"{label} is not reduced")
    return Fraction(numerator, denominator)


def _tape(value: Any, label: str) -> tuple[tuple[str, str], ...]:
    result = []
    for index, item in enumerate(_sequence(value, label)):
        row = _mapping(item, f"{label}[{index}]")
        _keys(row, frozenset({"information_key", "action"}), label)
        key = row["information_key"]
        action = row["action"]
        if not isinstance(key, str) or not key or not isinstance(action, str):
            raise ValueError(f"{label} contains a malformed tape entry")
        result.append((key, action))
    tape = tuple(result)
    if tape != tuple(sorted(tape)) or len(dict(tape)) != len(tape):
        raise ValueError(f"{label} is not a sorted total function")
    return tape


def _state(value: Any, label: str) -> str:
    if value not in _FAN_STATES:
        raise ValueError(f"{label} is not a frozen fan state")
    return str(value)


def _project_tape(
    tape: tuple[tuple[str, str], ...],
    factors: Mapping[str, Mapping[str, Any]],
) -> tuple[tuple[str, str], ...]:
    selected = dict(tape)
    if set(selected) != set(factors):
        raise ValueError("directional-face tape schema differs from factors")
    active: dict[str, bool] = {}
    visiting: set[str] = set()

    def reached(key: str) -> bool:
        if key in active:
            return active[key]
        if key in visiting:
            raise ValueError("directional-face parent graph contains a cycle")
        visiting.add(key)
        row = factors[key]
        parent = row["parent_pair"]
        result = bool(row["support"]) and (
            parent is None
            or (reached(parent[0]) and selected[parent[0]] == parent[1])
        )
        visiting.remove(key)
        active[key] = result
        return result

    return tuple(sorted((key, selected[key]) for key in factors if reached(key)))


def _reachable_cardinality(
    factors: Mapping[str, Mapping[str, Any]],
) -> tuple[int, int, int]:
    children: dict[tuple[str, str], list[str]] = {}
    roots = []
    for key, row in factors.items():
        parent = row["parent_pair"]
        if parent is None:
            roots.append(key)
        else:
            children.setdefault(parent, []).append(key)
    memo: dict[str, int] = {}
    visiting: set[str] = set()
    additions = 0
    multiplications = 0

    def count(key: str) -> int:
        nonlocal additions, multiplications
        if key in memo:
            return memo[key]
        if key in visiting:
            raise ValueError("directional-face cardinality graph contains a cycle")
        visiting.add(key)
        row = factors[key]
        if not row["support"]:
            result = 1
        else:
            result = 0
            for action in row["maximizers"]:
                branch = 1
                for child in children.get((key, action), ()):  # pragma: no branch
                    branch *= count(child)
                    multiplications += 1
                result += branch
                additions += 1
        visiting.remove(key)
        memo[key] = result
        return result

    for key in factors:
        count(key)
    result = 1
    for key in roots:
        result *= memo[key]
        multiplications += 1
    if len(memo) != len(factors):
        raise ValueError("directional-face factor graph has no rooted path")
    return result, additions, multiplications


def _verify_face(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
    scale: Fraction,
) -> _FaceView:
    face = _mapping(record, "face")
    _keys(face, _FACE_KEYS, "face")
    if (
        face["acting_player"] != acting_player
        or face["target_player"] != target_player
    ):
        raise ValueError("directional-face player identity differs")
    if _exact_fraction(face["scale"], "face.scale") != scale:
        raise ValueError("directional-face scale differs")
    response = _exact_fraction(face["response_value"], "face.response_value")
    profile = _exact_fraction(face["profile_utility"], "face.profile_utility")
    gain = _exact_fraction(face["deviation_gain"], "face.deviation_gain")
    minimum_response = _exact_fraction(
        face["minimum_response_slope"], "face.minimum_response_slope"
    )
    maximum_response = _exact_fraction(
        face["maximum_response_slope"], "face.maximum_response_slope"
    )
    profile_slope = _exact_fraction(
        face["profile_utility_slope"], "face.profile_utility_slope"
    )
    minimum_gain = _exact_fraction(
        face["minimum_gain_slope"], "face.minimum_gain_slope"
    )
    maximum_gain = _exact_fraction(
        face["maximum_gain_slope"], "face.maximum_gain_slope"
    )
    if (
        gain != response - profile
        or minimum_gain != minimum_response - profile_slope
        or maximum_gain != maximum_response - profile_slope
        or minimum_response > maximum_response
        or minimum_gain > maximum_gain
    ):
        raise ValueError("directional-face value or slope algebra differs")

    factors: dict[str, Mapping[str, Any]] = {}
    raw_factors = _sequence(face["information_sets"], "face.information_sets")
    for index, item in enumerate(raw_factors):
        row = _mapping(item, f"face.information_sets[{index}]")
        _keys(row, _FACTOR_KEYS, "directional-face factor")
        key = row["information_key"]
        if not isinstance(key, str) or not key or key in factors:
            raise ValueError("directional-face factor key is malformed or duplicated")
        actions = tuple(_sequence(row["actions"], "factor.actions"))
        maximizers = tuple(
            _sequence(row["maximizing_actions"], "factor.maximizing_actions")
        )
        if (
            not actions
            or any(not isinstance(action, str) for action in actions)
            or len(set(actions)) != len(actions)
            or not maximizers
            or len(set(maximizers)) != len(maximizers)
            or not set(maximizers).issubset(actions)
        ):
            raise ValueError("directional-face factor actions differ")
        minimum_action = row["minimum_slope_action"]
        maximum_action = row["maximum_slope_action"]
        if minimum_action not in maximizers or maximum_action not in maximizers:
            raise ValueError("directional-face extremal action is not a maximizer")
        minimum_local = _exact_fraction(
            row["minimum_local_slope"], "factor.minimum_local_slope"
        )
        maximum_local = _exact_fraction(
            row["maximum_local_slope"], "factor.maximum_local_slope"
        )
        if minimum_local > maximum_local:
            raise ValueError("directional-face local slope interval is reversed")
        parent_raw = row["parent"]
        parent_pair = None
        if parent_raw is not None:
            parent = _mapping(parent_raw, "factor.parent")
            _keys(parent, frozenset({"information_key", "action"}), "factor.parent")
            if not isinstance(parent["information_key"], str) or not isinstance(
                parent["action"], str
            ):
                raise ValueError("directional-face parent is malformed")
            parent_pair = (parent["information_key"], parent["action"])
        if not isinstance(row["positive_counterfactual_support"], bool):
            raise ValueError("directional-face support flag is not Boolean")
        factors[key] = {
            "actions": actions,
            "maximizers": maximizers,
            "minimum_action": minimum_action,
            "maximum_action": maximum_action,
            "parent_pair": parent_pair,
            "support": row["positive_counterfactual_support"],
            "state_count": _integer(
                row["state_count"],
                "factor.state_count",
                minimum=1,
            ),
        }

    if not factors:
        raise ValueError("directional-face factor set is empty")
    for row in factors.values():
        parent = row["parent_pair"]
        if parent is not None and (
            parent[0] not in factors or parent[1] not in factors[parent[0]]["actions"]
        ):
            raise ValueError("directional-face parent sequence differs")

    minimum_tape = _tape(face["minimum_slope_tape"], "face.minimum_slope_tape")
    maximum_tape = _tape(face["maximum_slope_tape"], "face.maximum_slope_tape")
    if set(dict(minimum_tape)) != set(factors) or set(
        dict(maximum_tape)
    ) != set(factors):
        raise ValueError("directional-face extremal tape schema differs")
    for key, row in factors.items():
        if (
            dict(minimum_tape)[key] != row["minimum_action"]
            or dict(maximum_tape)[key] != row["maximum_action"]
        ):
            raise ValueError("directional-face extremal tape selection differs")

    total = _integer(
        face["total_function_cardinality"],
        "face.total_function_cardinality",
        minimum=1,
    )
    factor_product = 1
    for row in factors.values():
        factor_product *= len(row["maximizers"])
    if total != factor_product:
        raise ValueError("directional-face total cardinality differs")
    reachable, reachable_additions, reachable_multiplications = (
        _reachable_cardinality(factors)
    )
    if reachable != _integer(
        face["reachable_support_cardinality"],
        "face.reachable_support_cardinality",
        minimum=1,
    ) or reachable > total:
        raise ValueError("directional-face reachable cardinality differs")
    factor_payload = {
        "total_function_cardinality": total,
        "reachable_support_cardinality": reachable,
        "information_sets": raw_factors,
    }
    if face["factor_sha256"] != _canonical_hash(factor_payload):
        raise ValueError("directional-face factor digest differs")

    work = _mapping(face["work"], "face.work")
    _keys(work, _WORK_KEYS, "face.work")
    numbers = {
        key: _integer(value, f"face.work.{key}") for key, value in work.items()
    }
    information_sets = len(factors)
    sequence_variables = sum(len(row["actions"]) for row in factors.values())
    target_action_edges = sum(
        row["state_count"] * len(row["actions"])
        for row in factors.values()
    )
    if (
        numbers["information_sets"] != information_sets
        or numbers["sequence_variables"] != sequence_variables
        or numbers["target_action_edges"] != target_action_edges
        or numbers["lexicographic_passes"] != 2
        or numbers["materialized_response_tapes"] != 0
        or numbers["total_cardinality_multiplications"] != information_sets
        or numbers["reachable_cardinality_additions"] != reachable_additions
        or numbers["reachable_cardinality_multiplications"]
        != reachable_multiplications
        or numbers["total_cardinality_bit_length"] != total.bit_length()
        or numbers["reachable_cardinality_bit_length"] != reachable.bit_length()
    ):
        raise ValueError("directional-face exact work identity differs")
    expected_per_pass = (
        numbers["tree_nodes"]
        + numbers["target_action_edges"]
        + sequence_variables
    )
    if numbers["per_pass_linear_work_ceiling"] != expected_per_pass:
        raise ValueError("directional-face per-pass ceiling differs")
    for prefix in ("minimum", "maximum"):
        if (
            numbers[f"{prefix}_continuation_node_evaluations"]
            != numbers["tree_nodes"]
            or numbers[f"{prefix}_action_score_terms"]
            != numbers["target_action_edges"]
            or numbers[f"{prefix}_action_choice_inspections"]
            != sequence_variables
        ):
            raise ValueError("directional-face pass work differs")
    cardinality_work = (
        information_sets + reachable_additions + reachable_multiplications
    )
    if (
        numbers["cardinality_linear_work_ceiling"]
        != sequence_variables + 2 * information_sets
        or cardinality_work > numbers["cardinality_linear_work_ceiling"]
        or numbers["total_logical_work_units"]
        != 2 * expected_per_pass + cardinality_work
        or numbers["target_action_edges"] > numbers["tree_edges"]
        or numbers["tree_edges"] + 1 != numbers["tree_nodes"]
    ):
        raise ValueError("directional-face linear work algebra differs")
    _project_tape(minimum_tape, factors)
    _project_tape(maximum_tape, factors)
    return _FaceView(
        scale=scale,
        total_cardinality=total,
        reachable_cardinality=reachable,
        minimum_tape=minimum_tape,
        maximum_tape=maximum_tape,
        factors=MappingProxyType(factors),
        tree_nodes=numbers["tree_nodes"],
        total_work=numbers["total_logical_work_units"],
        materialized_tapes=numbers["materialized_response_tapes"],
    )


def _verify_fan(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
) -> dict[str, Any]:
    fan = _mapping(record, "fan")
    expected = frozenset(
        {
            "acting_player",
            "cells",
            "fan_sha256",
            "legacy_source_breakpoint",
            "measures",
            "points",
            "reachable_tie_points",
            "segments",
            "source_cell_upper",
            "source_tape",
            "target_player",
            "total_tie_points",
        }
    )
    _keys(fan, expected, "fan")
    if (
        fan["acting_player"] != acting_player
        or fan["target_player"] != target_player
    ):
        raise ValueError("directional-face fan player identity differs")
    source_tape = _tape(fan["source_tape"], "fan.source_tape")
    cells = []
    cell_tapes = set()
    for index, item in enumerate(_sequence(fan["cells"], "fan.cells")):
        row = _mapping(item, f"fan.cells[{index}]")
        _keys(row, frozenset({"response_tape", "lower", "upper"}), "fan cell")
        tape = _tape(row["response_tape"], "fan cell tape")
        lower = _exact_fraction(row["lower"], "fan cell lower")
        upper = _exact_fraction(row["upper"], "fan cell upper")
        if not Fraction(0) <= lower <= upper <= Fraction(1) or tape in cell_tapes:
            raise ValueError("directional-face fan cell differs")
        cell_tapes.add(tape)
        cells.append({"tape": tape, "lower": lower, "upper": upper})
    if not cells or len(cells) > 256 or source_tape not in cell_tapes:
        raise ValueError("directional-face fan cell inventory differs")
    intervals = sorted((row["lower"], row["upper"]) for row in cells)
    cursor = Fraction(0)
    for lower, upper in intervals:
        if lower > cursor:
            raise ValueError("directional-face fan cells leave a gap")
        cursor = max(cursor, upper)
    if cursor != 1:
        raise ValueError("directional-face fan cells do not cover the ray")
    source_upper = _exact_fraction(
        fan["source_cell_upper"], "fan.source_cell_upper"
    )
    legacy = _exact_fraction(
        fan["legacy_source_breakpoint"], "fan.legacy_source_breakpoint"
    )
    source_cell = next(row for row in cells if row["tape"] == source_tape)
    if source_upper != legacy or source_upper != source_cell["upper"]:
        raise ValueError("directional-face source breakpoint differs")
    boundaries = tuple(
        sorted(
            {
                Fraction(0),
                Fraction(1),
                *(row["lower"] for row in cells),
                *(row["upper"] for row in cells),
            }
        )
    )
    points = []
    for index, item in enumerate(_sequence(fan["points"], "fan.points")):
        row = _mapping(item, f"fan.points[{index}]")
        _keys(
            row,
            frozenset(
                {
                    "reachable_state",
                    "reachable_tape",
                    "reachable_tie_information_sets",
                    "response_tape",
                    "scale",
                    "total_state",
                    "total_tie_information_sets",
                }
            ),
            "fan point",
        )
        points.append(
            {
                "scale": _exact_fraction(row["scale"], "fan point scale"),
                "response_tape": _tape(row["response_tape"], "fan point tape"),
                "reachable_tape": _tape(
                    row["reachable_tape"], "fan point reachable tape"
                ),
                "total_state": _state(row["total_state"], "fan point total state"),
                "reachable_state": _state(
                    row["reachable_state"], "fan point reachable state"
                ),
                "total_ties": tuple(
                    _sequence(
                        row["total_tie_information_sets"], "fan point total ties"
                    )
                ),
                "reachable_ties": tuple(
                    _sequence(
                        row["reachable_tie_information_sets"],
                        "fan point reachable ties",
                    )
                ),
            }
        )
    if tuple(row["scale"] for row in points) != boundaries:
        raise ValueError("directional-face fan boundary inventory differs")
    segments = []
    raw_segments = _sequence(fan["segments"], "fan.segments")
    if len(raw_segments) != len(boundaries) - 1:
        raise ValueError("directional-face fan segment count differs")
    for index, item in enumerate(raw_segments):
        row = _mapping(item, f"fan.segments[{index}]")
        _keys(
            row,
            frozenset(
                {
                    "lower",
                    "reachable_state",
                    "reachable_tape",
                    "reachable_tie_information_sets",
                    "response_tape",
                    "total_state",
                    "total_tie_information_sets",
                    "upper",
                    "witness",
                }
            ),
            "fan segment",
        )
        lower = _exact_fraction(row["lower"], "fan segment lower")
        upper = _exact_fraction(row["upper"], "fan segment upper")
        witness = _exact_fraction(row["witness"], "fan segment witness")
        if (
            lower != boundaries[index]
            or upper != boundaries[index + 1]
            or witness != (lower + upper) / 2
        ):
            raise ValueError("directional-face fan segment geometry differs")
        segments.append(
            {
                "lower": lower,
                "upper": upper,
                "witness": witness,
                "response_tape": _tape(row["response_tape"], "fan segment tape"),
                "reachable_tape": _tape(
                    row["reachable_tape"], "fan segment reachable tape"
                ),
                "total_state": _state(
                    row["total_state"], "fan segment total state"
                ),
                "reachable_state": _state(
                    row["reachable_state"], "fan segment reachable state"
                ),
                "total_ties": tuple(
                    _sequence(
                        row["total_tie_information_sets"], "fan segment total ties"
                    )
                ),
                "reachable_ties": tuple(
                    _sequence(
                        row["reachable_tie_information_sets"],
                        "fan segment reachable ties",
                    )
                ),
            }
        )
    measures = _mapping(fan["measures"], "fan.measures")
    measure_keys = frozenset(
        {
            "reachable_fixed",
            "reachable_switched",
            "reachable_tie_unresolved",
            "total_fixed",
            "total_switched",
            "total_tie_unresolved",
        }
    )
    _keys(measures, measure_keys, "fan.measures")
    parsed_measures = {
        key: _exact_fraction(value, f"fan.measures.{key}")
        for key, value in measures.items()
    }
    for prefix, state_field in (
        ("total", "total_state"),
        ("reachable", "reachable_state"),
    ):
        rebuilt = {state: Fraction(0) for state in _FAN_STATES}
        for segment in segments:
            rebuilt[segment[state_field]] += segment["upper"] - segment["lower"]
        for state in _FAN_STATES:
            if parsed_measures[f"{prefix}_{state}"] != rebuilt[state]:
                raise ValueError("directional-face fan measure differs")
        if sum(rebuilt.values(), Fraction(0)) != 1:
            raise ValueError("directional-face fan measures do not partition")
    total_tie_points = tuple(
        _exact_fraction(value, "fan total tie point")
        for value in _sequence(fan["total_tie_points"], "fan.total_tie_points")
    )
    reachable_tie_points = tuple(
        _exact_fraction(value, "fan reachable tie point")
        for value in _sequence(
            fan["reachable_tie_points"], "fan.reachable_tie_points"
        )
    )
    if total_tie_points != tuple(
        row["scale"] for row in points if row["total_state"] == "tie_unresolved"
    ) or reachable_tie_points != tuple(
        row["scale"]
        for row in points
        if row["reachable_state"] == "tie_unresolved"
    ):
        raise ValueError("directional-face fan tie-point inventory differs")
    payload = dict(fan)
    digest = payload.pop("fan_sha256")
    if digest != _canonical_hash(payload):
        raise ValueError("directional-face fan digest differs")
    return {
        "raw": fan,
        "source_tape": source_tape,
        "cells": cells,
        "points": points,
        "segments": segments,
        "boundaries": boundaries,
    }


def _location(fan: Mapping[str, Any], scale: Fraction) -> Mapping[str, Any]:
    for point in fan["points"]:
        if point["scale"] == scale:
            return point
    for segment in fan["segments"]:
        if segment["lower"] < scale < segment["upper"]:
            return segment
    raise ValueError("directional-face scale is outside the fan partition")


def _verify_face_location(
    face_record: Any,
    *,
    fan: Mapping[str, Any],
    rows: tuple[Mapping[str, Any], ...],
    acting_player: int,
    target_player: int,
    scale: Fraction,
    total_state: str,
    reachable_state: str,
) -> _FaceView:
    location = _location(fan, scale)
    if (
        total_state != location["total_state"]
        or reachable_state != location["reachable_state"]
    ):
        raise ValueError("directional-face location state differs")
    face = _verify_face(
        face_record,
        acting_player=acting_player,
        target_player=target_player,
        scale=scale,
    )
    factors = face.factors
    selected = dict(location["response_tape"])
    if set(selected) != set(factors) or any(
        selected[key] not in row["maximizers"] for key, row in factors.items()
    ):
        raise ValueError("directional-face fan tape is not an active-face member")
    projected = _project_tape(location["response_tape"], factors)
    source_projected = _project_tape(fan["source_tape"], factors)
    if projected != location["reachable_tape"]:
        raise ValueError("directional-face reachable tape projection differs")
    total_ties = tuple(
        key for key, row in factors.items() if len(row["maximizers"]) > 1
    )
    reachable_keys = {key for key, _ in projected}
    reachable_ties = tuple(key for key in total_ties if key in reachable_keys)
    if (
        tuple(location["total_ties"]) != total_ties
        or tuple(location["reachable_ties"]) != reachable_ties
    ):
        raise ValueError("directional-face fan tie-factor identity differs")
    expected_total_state = (
        "tie_unresolved"
        if total_ties
        else (
            "fixed"
            if location["response_tape"] == fan["source_tape"]
            else "switched"
        )
    )
    expected_reachable_state = (
        "tie_unresolved"
        if reachable_ties
        else (
            "fixed" if projected == source_projected else "switched"
        )
    )
    if total_state != expected_total_state or reachable_state != expected_reachable_state:
        raise ValueError("directional-face three-valued state differs")
    if (total_state == "tie_unresolved") != (face.total_cardinality > 1):
        raise ValueError("directional-face total tie/cardinality differs")
    if (reachable_state == "tie_unresolved") != (
        face.reachable_cardinality > 1
    ):
        raise ValueError("directional-face reachable tie/cardinality differs")
    if total_state != "tie_unresolved" and not (
        face.minimum_tape == face.maximum_tape == location["response_tape"]
    ):
        raise ValueError("directional-face unique total tape differs")
    if reachable_state != "tie_unresolved" and not (
        _project_tape(face.minimum_tape, factors)
        == _project_tape(face.maximum_tape, factors)
        == projected
    ):
        raise ValueError("directional-face unique reachable tape differs")
    values = tuple(row["intercept"] + scale * row["slope"] for row in rows)
    maximum = max(values)
    raw_face = _mapping(face_record, "face")
    if maximum != _exact_fraction(raw_face["deviation_gain"], "face.deviation_gain"):
        raise ValueError("directional-face maximum envelope direction differs")
    return face


def _verify_section(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
    schedule_scales: tuple[Fraction, ...],
) -> dict[str, Any]:
    target = _mapping(record, "target row")
    _keys(
        target,
        frozenset({"checks", "composed_section", "schedule", "target_player"}),
        "target row",
    )
    if target["target_player"] != target_player:
        raise ValueError("directional-face target-row player differs")
    section = _mapping(target["composed_section"], "composed section")
    _keys(
        section,
        frozenset(
            {
                "cell_gain_rows",
                "crossing_scales",
                "fan",
                "samples",
                "section_sha256",
            }
        ),
        "composed section",
    )
    fan = _verify_fan(
        section["fan"],
        acting_player=acting_player,
        target_player=target_player,
    )
    rows = []
    for index, item in enumerate(
        _sequence(section["cell_gain_rows"], "section.cell_gain_rows")
    ):
        row = _mapping(item, f"section.cell_gain_rows[{index}]")
        _keys(
            row,
            frozenset({"response_tape", "lower", "upper", "intercept", "slope"}),
            "cell gain row",
        )
        rows.append(
            {
                "tape": _tape(row["response_tape"], "cell gain tape"),
                "lower": _exact_fraction(row["lower"], "cell gain lower"),
                "upper": _exact_fraction(row["upper"], "cell gain upper"),
                "intercept": _exact_fraction(
                    row["intercept"], "cell gain intercept"
                ),
                "slope": _exact_fraction(row["slope"], "cell gain slope"),
            }
        )
    row_tuple = tuple(rows)
    if len(rows) != len(fan["cells"]) or {row["tape"] for row in rows} != {
        cell["tape"] for cell in fan["cells"]
    }:
        raise ValueError("directional-face cell-row inventory differs")
    for cell in fan["cells"]:
        row = next(item for item in rows if item["tape"] == cell["tape"])
        if row["lower"] != cell["lower"] or row["upper"] != cell["upper"]:
            raise ValueError("directional-face cell-row interval differs")
    for segment in fan["segments"]:
        row = next(
            (item for item in rows if item["tape"] == segment["response_tape"]),
            None,
        )
        if row is None or row["lower"] > segment["lower"] or row["upper"] < segment["upper"]:
            raise ValueError(
                "directional-face cell-row seam drops a segment"
            )

    expected_specs = sorted(
        [
            (point["scale"], "fan_boundary", point)
            for point in fan["points"]
        ]
        + [
            (segment["witness"], "open_segment", segment)
            for segment in fan["segments"]
        ],
        key=lambda item: (item[0], item[1]),
    )
    raw_samples = _sequence(section["samples"], "section.samples")
    if len(raw_samples) != len(expected_specs):
        raise ValueError("directional-face composed sample count differs")
    faces = []
    for index, (item, spec) in enumerate(zip(raw_samples, expected_specs, strict=True)):
        sample = _mapping(item, f"section.samples[{index}]")
        _keys(
            sample,
            frozenset(
                {
                    "active_cell_rows",
                    "face",
                    "maximum_cell_gain",
                    "reachable_state",
                    "sample_kind",
                    "scale",
                    "total_state",
                }
            ),
            "composed sample",
        )
        scale = _exact_fraction(sample["scale"], "composed sample scale")
        if scale != spec[0] or sample["sample_kind"] != spec[1]:
            raise ValueError("directional-face composed sample schedule differs")
        total_state = _state(sample["total_state"], "sample total state")
        reachable_state = _state(
            sample["reachable_state"], "sample reachable state"
        )
        face = _verify_face_location(
            sample["face"],
            fan=fan,
            rows=row_tuple,
            acting_player=acting_player,
            target_player=target_player,
            scale=scale,
            total_state=total_state,
            reachable_state=reachable_state,
        )
        values = tuple(row["intercept"] + scale * row["slope"] for row in rows)
        maximum = max(values)
        if (
            _exact_fraction(sample["maximum_cell_gain"], "sample maximum gain")
            != maximum
            or _integer(sample["active_cell_rows"], "sample active rows", minimum=1)
            != sum(value == maximum for value in values)
        ):
            raise ValueError("directional-face sample envelope differs")
        faces.append(face)

    crossings = tuple(
        left["upper"]
        for left, right in zip(fan["segments"], fan["segments"][1:])
        if left["response_tape"] != right["response_tape"]
    )
    recorded_crossings = tuple(
        _exact_fraction(value, "section crossing scale")
        for value in _sequence(section["crossing_scales"], "section.crossing_scales")
    )
    if recorded_crossings != crossings:
        raise ValueError("directional-face crossing inventory differs")
    for scale in crossings:
        face = next(item for item in faces if item.scale == scale)
        raw_face = _mapping(
            next(
                sample["face"]
                for sample in raw_samples
                if _exact_fraction(sample["scale"], "sample scale") == scale
                and sample["sample_kind"] == "fan_boundary"
            ),
            "crossing face",
        )
        if (
            face.total_cardinality <= 1
            or _exact_fraction(raw_face["minimum_gain_slope"], "minimum gain slope")
            >= _exact_fraction(raw_face["maximum_gain_slope"], "maximum gain slope")
        ):
            raise ValueError("directional-face crossing lost its active face")

    raw_schedule = _sequence(target["schedule"], "target.schedule")
    if len(raw_schedule) != len(schedule_scales):
        raise ValueError("directional-face point schedule count differs")
    for index, (item, scale) in enumerate(zip(raw_schedule, schedule_scales, strict=True)):
        row = _mapping(item, f"target.schedule[{index}]")
        _keys(
            row,
            frozenset({"face", "reachable_state", "scale", "total_state"}),
            "schedule row",
        )
        if _exact_fraction(row["scale"], "schedule scale") != scale:
            raise ValueError("directional-face point schedule differs")
        faces.append(
            _verify_face_location(
                row["face"],
                fan=fan,
                rows=row_tuple,
                acting_player=acting_player,
                target_player=target_player,
                scale=scale,
                total_state=_state(row["total_state"], "schedule total state"),
                reachable_state=_state(
                    row["reachable_state"], "schedule reachable state"
                ),
            )
        )
    checks = _mapping(target["checks"], "target.checks")
    _keys(checks, _CHECK_KEYS, "target.checks")
    if any(value is not True for value in checks.values()):
        raise ValueError("directional-face target check is not literally true")
    section_payload = dict(section)
    section_digest = section_payload.pop("section_sha256")
    if section_digest != _canonical_hash(section_payload):
        raise ValueError("directional-face section digest differs")
    return {
        "checks": dict(checks),
        "composition_face_samples": len(raw_samples),
        "crossings": len(crossings),
        "face_observations": len(faces),
        "fan_cells": len(fan["cells"]),
        "fan_points": len(fan["points"]),
        "fan_segments": len(fan["segments"]),
        "materialized_response_tapes": sum(
            face.materialized_tapes for face in faces
        ),
        "maximum_reachable_cardinality_bit_length": max(
            face.reachable_cardinality.bit_length() for face in faces
        ),
        "maximum_reachable_support_cardinality": max(
            face.reachable_cardinality for face in faces
        ),
        "maximum_total_cardinality_bit_length": max(
            face.total_cardinality.bit_length() for face in faces
        ),
        "maximum_total_function_cardinality": max(
            face.total_cardinality for face in faces
        ),
        "maximum_tree_nodes": max(face.tree_nodes for face in faces),
        "schedule_face_calls": len(raw_schedule),
        "total_logical_work_units": sum(face.total_work for face in faces),
    }


def _verify_config() -> Mapping[str, Any]:
    path = _ROOT / ADR0356_CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != ADR0356_CONFIG_SHA256:
        raise ValueError("ADR-0356 config bytes differ")
    config = _load_json(raw)
    for field, relative in _SOURCE_PATHS.items():
        if config.get(field) != _canonical_lf_sha256(_ROOT / relative):
            raise ValueError(f"ADR-0356 config source differs: {field}")
    if (
        config.get("expected_parent_protocol_sha256")
        != ADR0356_PARENT_PROTOCOL_SHA256
        or config.get("expected_implementation_sha256") != ADR0356_RUNNER_SHA256
        or config.get("hash_semantics")
        != "canonical_lf_sha256_for_all_bound_text_sources"
    ):
        raise ValueError("ADR-0356 config protocol differs")
    return MappingProxyType(config)


def _verify_record(record: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    _keys(record, _TOP_KEYS, "directional-face artifact")
    identities = {
        "config_sha256": ADR0356_CONFIG_SHA256,
        "implementation_sha256": ADR0356_RUNNER_SHA256,
        "parent_protocol_sha256": ADR0356_PARENT_PROTOCOL_SHA256,
        "root_public_state_sha256": ADR0356_ROOT_PUBLIC_STATE_SHA256,
        "public_schema_sha256": ADR0356_PUBLIC_SCHEMA_SHA256,
        "game_structural_sha256": ADR0356_GAME_STRUCTURAL_SHA256,
        "game_provenance_sha256": ADR0356_GAME_PROVENANCE_SHA256,
        "source_policy_sha256": ADR0356_SOURCE_POLICY_SHA256,
    }
    if any(record[key] != value for key, value in identities.items()):
        raise ValueError("directional-face retained identity differs")
    if (
        record["schema_version"] != 1
        or record["status"] != "legal_responder_raise_h4_directional_face_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_legal_h4_directional_face_integration_preregistration"
        or record["strategy_quality_claim"] is not None
        or record["quality_rows_serialized"] != 0
        or record["strategy_labels_generated"] != 0
        or tuple(record["limitations"]) != _LIMITATIONS
    ):
        raise ValueError("directional-face terminal or claim boundary differs")
    environment = _mapping(record["environment"], "environment")
    _keys(environment, frozenset({"git", "platform", "python", "runtime"}), "environment")
    git = _mapping(environment["git"], "environment.git")
    _keys(git, frozenset({"commit", "dirty", "strict_status"}), "environment.git")
    if git != {
        "commit": ADR0356_INVOCATION_SOURCE_COMMIT,
        "dirty": False,
        "strict_status": True,
    }:
        raise ValueError("directional-face invocation Git identity differs")
    runtime = _mapping(environment["runtime"], "environment.runtime")
    if runtime != {"backend": "cpu_fraction_exact_fan_plus_directional_face"}:
        raise ValueError("directional-face runtime backend differs")
    if not isinstance(environment["platform"], str) or not isinstance(
        environment["python"], str
    ):
        raise ValueError("directional-face environment labels differ")
    methodology = _mapping(record["methodology"], "methodology")
    if methodology != {
        "active_face_materialization": "none",
        "betting_authority": "NoLimitBettingState",
        "direction_source": "three_regret_vertices_plus_retained_restricted_master",
        "face_teacher": "two_fraction_exact_lexicographic_backward_passes",
        "quality_rows": 0,
        "ray_teacher": "fraction_exact_sequence_form_normal_fan",
        "strategy_labels": 0,
    }:
        raise ValueError("directional-face methodology differs")
    semantics = _mapping(record["face_semantics"], "face_semantics")
    if semantics != {
        "active_face_representation": (
            "factorized_exact_local_maximizer_sets_without_tape_product"
        ),
        "cardinality_authority": (
            "total_function_conservative_reachable_support_descriptive"
        ),
        "cardinality_columns": ["total_function", "reachable_support"],
        "face_cardinality_bound": None,
        "face_instrument": "two_independent_lexicographic_backward_passes",
        "maximum_fan_pieces": 256,
        "maximum_tree_nodes": 100_000,
        "ray_instrument": "exact_sequence_form_normal_fan",
        "work_ledger_semantics": (
            "linear_logical_operations_plus_exact_bigint_bit_lengths"
        ),
    }:
        raise ValueError("directional-face semantics differ")
    schedule = _mapping(record["schedule"], "schedule")
    if schedule != {"numerators": list(range(17)), "denominator": 16, "points": 17}:
        raise ValueError("directional-face schedule differs")
    schedule_scales = tuple(Fraction(index, 16) for index in range(17))
    descriptors = _sequence(record["direction_descriptors"], "direction descriptors")
    if descriptors != config["direction_descriptors"]:
        raise ValueError("directional-face descriptor inventory differs")
    directions = _sequence(record["directions"], "directions")
    if len(directions) != 4:
        raise ValueError("directional-face direction count differs")
    metrics = []
    for index, item in enumerate(directions):
        direction = _mapping(item, f"directions[{index}]")
        _keys(
            direction,
            frozenset(
                {
                    "changed_public_histories",
                    "direction_class",
                    "endpoint_policy_sha256",
                    "label",
                    "target_rows",
                }
            ),
            "direction",
        )
        descriptor = {key: direction[key] for key in direction if key != "target_rows"}
        if descriptor != descriptors[index]:
            raise ValueError("directional-face direction descriptor differs")
        target_rows = _sequence(direction["target_rows"], "direction.target_rows")
        if len(target_rows) != 2:
            raise ValueError("directional-face target-player count differs")
        for target_player, target_row in enumerate(target_rows):
            metrics.append(
                _verify_section(
                    target_row,
                    acting_player=0,
                    target_player=target_player,
                    schedule_scales=schedule_scales,
                )
            )
    aggregate = _mapping(record["aggregate"], "aggregate")
    aggregate_keys = frozenset(
        {
            "checks",
            "composition_face_samples",
            "crossings",
            "face_observations",
            "fan_cells",
            "fan_points",
            "fan_segments",
            "materialized_response_tapes",
            "maximum_reachable_cardinality_bit_length",
            "maximum_reachable_support_cardinality",
            "maximum_total_cardinality_bit_length",
            "maximum_total_function_cardinality",
            "maximum_tree_nodes",
            "schedule_face_calls",
            "sections",
            "subject_seconds",
            "total_logical_work_units",
        }
    )
    _keys(aggregate, aggregate_keys, "aggregate")
    rebuilt = {
        "composition_face_samples": sum(
            row["composition_face_samples"] for row in metrics
        ),
        "crossings": sum(row["crossings"] for row in metrics),
        "face_observations": sum(row["face_observations"] for row in metrics),
        "fan_cells": sum(row["fan_cells"] for row in metrics),
        "fan_points": sum(row["fan_points"] for row in metrics),
        "fan_segments": sum(row["fan_segments"] for row in metrics),
        "materialized_response_tapes": sum(
            row["materialized_response_tapes"] for row in metrics
        ),
        "maximum_reachable_cardinality_bit_length": max(
            row["maximum_reachable_cardinality_bit_length"] for row in metrics
        ),
        "maximum_reachable_support_cardinality": max(
            row["maximum_reachable_support_cardinality"] for row in metrics
        ),
        "maximum_total_cardinality_bit_length": max(
            row["maximum_total_cardinality_bit_length"] for row in metrics
        ),
        "maximum_total_function_cardinality": max(
            row["maximum_total_function_cardinality"] for row in metrics
        ),
        "maximum_tree_nodes": max(row["maximum_tree_nodes"] for row in metrics),
        "schedule_face_calls": sum(row["schedule_face_calls"] for row in metrics),
        "sections": len(metrics),
        "total_logical_work_units": sum(
            row["total_logical_work_units"] for row in metrics
        ),
    }
    if rebuilt != dict(_EXPECTED_AGGREGATE) or any(
        aggregate[key] != value for key, value in rebuilt.items()
    ):
        raise ValueError("directional-face aggregate differs")
    aggregate_checks = _mapping(aggregate["checks"], "aggregate.checks")
    _keys(aggregate_checks, _CHECK_KEYS, "aggregate.checks")
    if any(value is not True for value in aggregate_checks.values()):
        raise ValueError("directional-face aggregate check differs")
    subject = _finite_float(aggregate["subject_seconds"], "subject seconds")
    analysis = _finite_float(record["analysis_seconds"], "analysis seconds")
    if subject > analysis or subject > 180.0 or analysis > 240.0:
        raise ValueError("directional-face infrastructure wall differs")
    scientific = {
        "directions": directions,
        "aggregate": aggregate,
    }
    scientific_bytes = len(
        json.dumps(
            scientific,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    if (
        record["scientific_payload_bytes"] != scientific_bytes
        or scientific_bytes > 16_777_216
    ):
        raise ValueError("directional-face scientific payload bytes differ")
    gates = _mapping(record["gates"], "gates")
    _keys(gates, _GATE_KEYS, "gates")
    if any(value is not True for value in gates.values()):
        raise ValueError("directional-face frozen gate is not literally true")


def _verify_source_seal() -> None:
    from .legal_responder_raise_h4_directional_face_result_seal import (
        ADR0356_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0356_RESULT_SOURCE_MANIFEST,
    )

    actual = _canonical_lf_sha256(_MODULE)
    if ADR0356_RESULT_SOURCE_MANIFEST != {_MODULE.name: actual}:
        raise ValueError("ADR-0356 result owner source seal differs")
    if sealed_protocol != ADR0356_RESULT_PROTOCOL_SHA256:
        raise ValueError("ADR-0356 result owner protocol seal differs")


def verify_adr0356_legal_h4_directional_face_result_artifact(
    path: Path | None = None,
) -> VerifiedLegalH4DirectionalFaceResult:
    """Verify the sole retained artifact without executing scientific code."""

    _verify_source_seal()
    config = _verify_config()
    artifact_path = (
        _ROOT / ADR0356_ARTIFACT_RELATIVE_PATH if path is None else path
    )
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0356_ARTIFACT_BYTES:
        raise ValueError("ADR-0356 artifact byte count differs")
    digest = sha256(raw).hexdigest()
    if digest != ADR0356_ARTIFACT_SHA256:
        raise ValueError("ADR-0356 artifact digest differs")
    if not raw.endswith(b"\n") or b"\r\n" in raw:
        raise ValueError("ADR-0356 artifact newline contract differs")
    record = _load_json(raw)
    _verify_record(record, config)
    return VerifiedLegalH4DirectionalFaceResult(
        record=MappingProxyType(record),
        source_commit=ADR0356_INVOCATION_SOURCE_COMMIT,
        artifact_sha256=digest,
        artifact_bytes=len(raw),
    )


__all__ = [
    "ADR0356_ARTIFACT_BYTES",
    "ADR0356_ARTIFACT_RELATIVE_PATH",
    "ADR0356_ARTIFACT_SHA256",
    "ADR0356_CONFIG_SHA256",
    "ADR0356_GAME_PROVENANCE_SHA256",
    "ADR0356_GAME_STRUCTURAL_SHA256",
    "ADR0356_INVOCATION_SOURCE_COMMIT",
    "ADR0356_PARENT_PROTOCOL_SHA256",
    "ADR0356_PUBLIC_SCHEMA_SHA256",
    "ADR0356_RESULT_PROTOCOL",
    "ADR0356_RESULT_PROTOCOL_SHA256",
    "ADR0356_ROOT_PUBLIC_STATE_SHA256",
    "ADR0356_RUNNER_SHA256",
    "ADR0356_SOURCE_POLICY_SHA256",
    "VerifiedLegalH4DirectionalFaceResult",
    "verify_adr0356_legal_h4_directional_face_result_artifact",
]
