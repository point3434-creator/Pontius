"""Read-only owner for ADR-0359's retained factorized-affine result.

The ADR-0358 writer is permanently consumed.  This module imports only the
standard library and reads committed bytes.  It independently rebinds the
source-face factorization, exact affine envelope, point/ray seams, nominal
dispatch, work and aggregate arithmetic, provenance, claims and gates.

ADR-0358 intentionally serialized point summaries, not every non-source face
factor.  Consequently non-source point factor/cardinality/active-face fields
and the live ``reproduced_section_sha256`` are authenticated to the sealed
runner and its outer artifact bytes.  Endpoint-only/non-quotient fan rows and
their individual epigraph residuals are likewise counted but not serialized.
They are not independently reconstructible here.  The compact point gain
envelope and inward fan/face slope seams are rederived.
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


ADR0359_INVOCATION_SOURCE_COMMIT = (
    "23c7f023e686b8b84bc1145381c5fe7ba99dc8d4"
)
ADR0359_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-factorized-affine-v1.json"
)
ADR0359_ARTIFACT_BYTES = 259_550
ADR0359_ARTIFACT_SHA256 = (
    "301f7c9c865b8ae2cfcc39e6c6ebca32db68d4fd15e8e6255976ace587c35eea"
)
ADR0359_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-responder-raise-h4-factorized-affine-v1.json"
)
ADR0359_CONFIG_SHA256 = (
    "e77f22b739ac714d952f0575735b5705c0b17913cf7930705dfb1588f307263c"
)
ADR0359_RUNNER_SHA256 = (
    "b2b14500aa52a25025c78d4dbcfe42378e0a74e69c3b9c1e9d5bd62c266159f0"
)
ADR0359_PARENT_PROTOCOL_SHA256 = (
    "8a5b053e1b792ae879f5d10cd8c7614ae69e33fe2033db0d0337388375e83d6a"
)
ADR0359_PARENT_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-directional-face-v1.json"
)
ADR0359_PARENT_ARTIFACT_BYTES = 3_888_072
ADR0359_PARENT_ARTIFACT_SHA256 = (
    "5e3473639e67e0a24e21f3c516239c35d4bb7ccb17a6de8d74a5320428af1b49"
)
ADR0359_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0359_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0359_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0359_GAME_PROVENANCE_SHA256 = (
    "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
)
ADR0359_SOURCE_POLICY_SHA256 = (
    "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/ADR-0357-seal-the-factorized-tie-aware-affine-integration.md"
        ),
        "expected_parent_source_seal_sha256": (
            "src/pontius/factorized_tie_aware_affine_seal.py"
        ),
        "expected_factorized_affine_sha256": (
            "src/pontius/factorized_tie_aware_affine.py"
        ),
        "expected_tie_conformance_v2_sha256": (
            "src/pontius/tie_semantics_conformance_v2.py"
        ),
        "expected_factorized_affine_controls_sha256": (
            "tests/test_factorized_tie_aware_affine.py"
        ),
        "expected_tie_conformance_v2_controls_sha256": (
            "tests/test_tie_semantics_conformance_v2.py"
        ),
        "expected_factorized_source_seal_controls_sha256": (
            "tests/test_factorized_tie_aware_affine_seal.py"
        ),
        "expected_directional_face_oracle_sha256": (
            "src/pontius/exact_directional_face_oracle.py"
        ),
        "expected_directional_face_source_seal_sha256": (
            "src/pontius/exact_directional_face_oracle_seal.py"
        ),
        "expected_exact_fan_sha256": "src/pontius/exact_selector_fan.py",
        "expected_exact_selector_oracle_sha256": (
            "src/pontius/exact_selector_window_oracle.py"
        ),
        "expected_exact_sequence_oracle_sha256": (
            "src/pontius/exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_selector_window_sha256": "src/pontius/selector_window.py",
        "expected_selector_window_v2_sha256": "src/pontius/selector_window_v2.py",
        "expected_evaluation_sha256": "src/pontius/evaluation.py",
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_fixture_sha256": "src/pontius/legal_h4_selector_fixture.py",
        "expected_direction_compiler_sha256": (
            "src/pontius/legal_h4_selector_directions.py"
        ),
        "expected_cfr_sha256": "src/pontius/cfr.py",
        "expected_generation_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_row_growth_result_owner_sha256": (
            "src/pontius/legal_responder_raise_h4_row_growth_result.py"
        ),
        "expected_parent_result_owner_sha256": (
            "src/pontius/legal_responder_raise_h4_directional_face_result.py"
        ),
        "expected_parent_result_owner_seal_sha256": (
            "src/pontius/legal_responder_raise_h4_directional_face_result_seal.py"
        ),
        "expected_parent_result_controls_sha256": (
            "tests/test_legal_responder_raise_h4_directional_face_result.py"
        ),
        "expected_runner_harness_sha256": "src/pontius/runner_harness.py",
        "expected_strict_loader_sha256": "src/pontius/runner_harness_v2.py",
        "expected_implementation_sha256": (
            "src/pontius/legal_responder_raise_h4_factorized_affine.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_responder_raise_h4_factorized_affine.py"
        ),
    }
)
_DIRECTION_DESCRIPTORS = (
    {
        "label": "regret_vertex::p0:raise-to-2/p1:raise-to-4",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["p0:raise-to-2/p1:raise-to-4"],
        "endpoint_policy_sha256": (
            "bd9533ae86809b0cbcaeb643c3b1503794f6e7812c0b48950849bb976a7e4f9d"
        ),
    },
    {
        "label": "regret_vertex::p0:raise-to-3/p1:raise-to-4",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["p0:raise-to-3/p1:raise-to-4"],
        "endpoint_policy_sha256": (
            "e849f04dbc967c6422a719cf430d4e5a646ba59a6bb00a0c9b9e17ff27892209"
        ),
    },
    {
        "label": "regret_vertex::root",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["root"],
        "endpoint_policy_sha256": (
            "3372dd9b65180afdbb2c3260d43f559366c77017bfd9c498371406aa7d001e2e"
        ),
    },
    {
        "label": "lp_proposed::adr0349_restricted_master",
        "direction_class": "retained_restricted_master_proposal",
        "changed_public_histories": ["root"],
        "endpoint_policy_sha256": (
            "0f9be1f884cb09eb8318a88a1548afb402ec256e8fa52f19118c64569fe7658b"
        ),
    },
)
_TOP_KEYS = frozenset(
    {
        "actions_emitted",
        "aggregate",
        "analysis_seconds",
        "config_sha256",
        "decision",
        "direction_descriptors",
        "directions",
        "environment",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "implementation_sha256",
        "integration_semantics",
        "limitations",
        "methodology",
        "parent_artifact_bytes",
        "parent_artifact_sha256",
        "parent_protocol_sha256",
        "passed",
        "public_schema_sha256",
        "quality_rows_serialized",
        "root_public_state_sha256",
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
_FACE_WORK_KEYS = frozenset(
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
_INTEGRATION_KEYS = frozenset(
    {
        "acting_player",
        "certificate_identity_authority",
        "crossing_scales",
        "epigraph_orientation",
        "exact_envelope_domain",
        "fan_counts",
        "integration_sha256",
        "legacy_source_breakpoint",
        "mode",
        "parent_section_identity",
        "parent_section_sha256",
        "pieces",
        "point_authority",
        "point_summary",
        "ray_authority",
        "reachable_identity_role",
        "reproduced_section_sha256",
        "single_tape_window",
        "source_cell_upper",
        "source_face",
        "target_player",
        "work",
    }
)
_INTEGRATION_WORK_KEYS = frozenset(
    {
        "envelope_row_evaluations",
        "epigraph_residual_evaluations",
        "fan_boundaries",
        "fan_cell_rows",
        "fan_segments",
        "float_selector_score_calls",
        "materialized_response_tapes",
        "point_face_observations",
        "selector_window_v2_calls",
    }
)
_SECTION_CHECK_KEYS = frozenset(
    {
        "complete_exact_envelope",
        "dual_cardinality_columns",
        "epigraph_orientation",
        "integration_work_identity",
        "parent_section_identity",
        "section_identity",
        "typed_source_dispatch",
        "zero_materialized_tapes",
    }
)
_GATE_KEYS = frozenset(
    {
        "analysis_wall",
        "clean_git_state",
        "complete_exact_envelope",
        "direction_identity",
        "dual_cardinality_columns",
        "epigraph_orientation",
        "finite",
        "fixture_identity",
        "integration_work_identity",
        "no_face_cardinality_bound",
        "no_target_outcome_gate",
        "parent_artifact_identity",
        "parent_pass",
        "parent_rebind_wall",
        "parent_section_identity",
        "passed",
        "scientific_payload_bytes",
        "section_identity",
        "subject_wall",
        "typed_source_dispatch",
        "zero_actions_and_quality_rows",
        "zero_materialized_tapes",
    }
)
_STATES = frozenset({"fixed", "tie_unresolved", "switched"})
_LIMITATIONS = (
    "same_fixture_legal_h4_development_integration_only",
    "not_untouched_confirmation",
    "not_full_width_capacity_or_action_clock_latency",
    "not_multiway_response_closure_or_cross_street_handoff",
    "no_action_quality_or_poker_strength_claim",
)
_EXPECTED_OBSERVATIONS = MappingProxyType(
    {
        "compact_envelope_pieces": 10,
        "fan_boundaries": 18,
        "fan_cells": 12,
        "fan_rows_without_distinct_interval_piece": 2,
        "fan_segments": 10,
        "factorized_modes": 4,
        "maximum_serialized_point_reachable_support_cardinality": 2,
        "maximum_serialized_point_total_function_cardinality": 104_976,
        "maximum_reachable_support_cardinality": 2,
        "maximum_total_function_cardinality": 2,
        "point_face_observations": 28,
        "sections": 8,
        "v2_singletons": 4,
        "zero_materialized_tapes": 0,
    }
)


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0359_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0359_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0359_ARTIFACT_SHA256,
    "authority": (
        "same_fixture_development_integration_only_untouched_confirmation_"
        "requires_separate_preregistration"
    ),
    "authenticated_only_fields": (
        "non_source_point_factor_cardinality_and_active_face_fields",
        "non_quotient_fan_rows_and_individual_epigraph_residuals",
        "reproduced_section_sha256",
    ),
    "config_sha256": ADR0359_CONFIG_SHA256,
    "expected_observations": tuple(sorted(_EXPECTED_OBSERVATIONS.items())),
    "invocation_source_commit": ADR0359_INVOCATION_SOURCE_COMMIT,
    "parent_protocol_sha256": ADR0359_PARENT_PROTOCOL_SHA256,
    "runner_sha256": ADR0359_RUNNER_SHA256,
    "version": "adr0359-legal-h4-factorized-affine-result-v1",
}
ADR0359_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0359_RESULT_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _RESULT_PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


@dataclass(frozen=True, slots=True)
class VerifiedLegalH4FactorizedAffineResult:
    """Independent read-only verification of the sole ADR-0358 terminal."""

    record: Mapping[str, Any]
    source_commit: str
    artifact_sha256: str
    artifact_bytes: int
    authenticated_only_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _FaceView:
    gain: Fraction
    minimum_gain_slope: Fraction
    maximum_gain_slope: Fraction
    total_cardinality: int
    reachable_cardinality: int
    factor_keys: frozenset[str]
    materialized_tapes: int


@dataclass(frozen=True, slots=True)
class _IntegrationView:
    mode: str
    pieces: int
    fan_cells: int
    points: int
    boundaries: int
    segments: int
    total_cardinality: int
    reachable_cardinality: int
    maximum_point_total_cardinality: int
    maximum_point_reachable_cardinality: int
    float_scores: int
    window_calls: int
    materialized_tapes: int
    window_scale: float | None


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
            raise ValueError(f"factorized-affine JSON duplicates key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"factorized-affine JSON contains non-finite token {token}")


def _load_json(raw: bytes) -> dict[str, Any]:
    try:
        record = json.loads(
            raw,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("factorized-affine input is not strict UTF-8 JSON") from error
    if not isinstance(record, dict):
        raise ValueError("factorized-affine JSON root is not an object")
    return record


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(
        isinstance(key, str) for key in value
    ):
        raise ValueError(f"{label} is not a string-keyed object")
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


def _signed_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} is not an integer")
    return value


def _finite_float(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} is not numerical")
    result = float(value)
    if not isfinite(result) or result < minimum:
        raise ValueError(f"{label} is not finite and bounded")
    return result


def _exact_fraction(value: Any, label: str) -> Fraction:
    row = _mapping(value, label)
    _keys(row, frozenset({"numerator", "denominator"}), label)
    numerator = _signed_integer(row["numerator"], f"{label}.numerator")
    denominator = _integer(row["denominator"], f"{label}.denominator", minimum=1)
    if gcd(abs(numerator), denominator) != 1:
        raise ValueError(f"{label} is not reduced")
    return Fraction(numerator, denominator)


def _digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is not a lowercase SHA-256")
    return value


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
            raise ValueError("factorized-affine cardinality graph contains a cycle")
        visiting.add(key)
        row = factors[key]
        if not row["support"]:
            result = 1
        else:
            result = 0
            for action in row["maximizers"]:
                branch = 1
                for child in children.get((key, action), ()):
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
        raise ValueError("factorized-affine factor graph has no rooted path")
    return result, additions, multiplications


def _verify_source_face(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
) -> _FaceView:
    face = _mapping(record, "source face")
    _keys(face, _FACE_KEYS, "source face")
    if face["acting_player"] != acting_player or face["target_player"] != target_player:
        raise ValueError("factorized-affine source-face player identity differs")
    if _exact_fraction(face["scale"], "source face scale") != 0:
        raise ValueError("factorized-affine source face is not at scale zero")
    response = _exact_fraction(face["response_value"], "source response")
    profile = _exact_fraction(face["profile_utility"], "source profile")
    gain = _exact_fraction(face["deviation_gain"], "source gain")
    minimum_response = _exact_fraction(
        face["minimum_response_slope"], "source minimum response slope"
    )
    maximum_response = _exact_fraction(
        face["maximum_response_slope"], "source maximum response slope"
    )
    profile_slope = _exact_fraction(
        face["profile_utility_slope"], "source profile slope"
    )
    minimum_gain = _exact_fraction(
        face["minimum_gain_slope"], "source minimum gain slope"
    )
    maximum_gain = _exact_fraction(
        face["maximum_gain_slope"], "source maximum gain slope"
    )
    if (
        gain != response - profile
        or minimum_gain != minimum_response - profile_slope
        or maximum_gain != maximum_response - profile_slope
        or minimum_response > maximum_response
        or minimum_gain > maximum_gain
    ):
        raise ValueError("factorized-affine source-face algebra differs")

    factors: dict[str, Mapping[str, Any]] = {}
    raw_factors = _sequence(face["information_sets"], "source information sets")
    for index, item in enumerate(raw_factors):
        row = _mapping(item, f"source factor {index}")
        _keys(row, _FACTOR_KEYS, "source factor")
        key = row["information_key"]
        actions = tuple(_sequence(row["actions"], "source factor actions"))
        maximizers = tuple(
            _sequence(row["maximizing_actions"], "source factor maximizers")
        )
        if (
            not isinstance(key, str)
            or not key
            or key in factors
            or not actions
            or any(not isinstance(action, str) for action in actions)
            or len(set(actions)) != len(actions)
            or not maximizers
            or len(set(maximizers)) != len(maximizers)
            or not set(maximizers).issubset(actions)
        ):
            raise ValueError("factorized-affine source factor differs")
        minimum_action = row["minimum_slope_action"]
        maximum_action = row["maximum_slope_action"]
        if minimum_action not in maximizers or maximum_action not in maximizers:
            raise ValueError("factorized-affine extremal action is not active")
        if _exact_fraction(
            row["minimum_local_slope"], "source minimum local slope"
        ) > _exact_fraction(
            row["maximum_local_slope"], "source maximum local slope"
        ):
            raise ValueError("factorized-affine local slope interval is reversed")
        parent_pair = None
        if row["parent"] is not None:
            parent = _mapping(row["parent"], "source factor parent")
            _keys(
                parent,
                frozenset({"information_key", "action"}),
                "source factor parent",
            )
            if not isinstance(parent["information_key"], str) or not isinstance(
                parent["action"], str
            ):
                raise ValueError("factorized-affine source parent differs")
            parent_pair = (parent["information_key"], parent["action"])
        if not isinstance(row["positive_counterfactual_support"], bool):
            raise ValueError("factorized-affine support flag is not Boolean")
        factors[key] = {
            "actions": actions,
            "maximizers": maximizers,
            "minimum_action": minimum_action,
            "maximum_action": maximum_action,
            "parent_pair": parent_pair,
            "support": row["positive_counterfactual_support"],
            "state_count": _integer(row["state_count"], "factor state count", minimum=1),
        }
    if not factors:
        raise ValueError("factorized-affine source factor set is empty")
    for row in factors.values():
        parent = row["parent_pair"]
        if parent is not None and (
            parent[0] not in factors or parent[1] not in factors[parent[0]]["actions"]
        ):
            raise ValueError("factorized-affine source parent sequence differs")

    minimum_tape = dict(_tape(face["minimum_slope_tape"], "minimum source tape"))
    maximum_tape = dict(_tape(face["maximum_slope_tape"], "maximum source tape"))
    if set(minimum_tape) != set(factors) or set(maximum_tape) != set(factors):
        raise ValueError("factorized-affine extremal tape schema differs")
    for key, row in factors.items():
        if (
            minimum_tape[key] != row["minimum_action"]
            or maximum_tape[key] != row["maximum_action"]
        ):
            raise ValueError("factorized-affine extremal tape selection differs")

    total = _integer(
        face["total_function_cardinality"], "source total cardinality", minimum=1
    )
    factor_product = 1
    for row in factors.values():
        factor_product *= len(row["maximizers"])
    reachable, reachable_additions, reachable_multiplications = (
        _reachable_cardinality(factors)
    )
    recorded_reachable = _integer(
        face["reachable_support_cardinality"],
        "source reachable cardinality",
        minimum=1,
    )
    if (
        total != factor_product
        or recorded_reachable != reachable
        or reachable > total
    ):
        raise ValueError("factorized-affine source cardinality differs")
    if face["factor_sha256"] != _canonical_hash(
        {
            "total_function_cardinality": total,
            "reachable_support_cardinality": reachable,
            "information_sets": raw_factors,
        }
    ):
        raise ValueError("factorized-affine source factor digest differs")

    work = _mapping(face["work"], "source face work")
    _keys(work, _FACE_WORK_KEYS, "source face work")
    numbers = {
        key: _integer(value, f"source work {key}") for key, value in work.items()
    }
    information_sets = len(factors)
    sequence_variables = sum(len(row["actions"]) for row in factors.values())
    target_action_edges = sum(
        row["state_count"] * len(row["actions"]) for row in factors.values()
    )
    expected_per_pass = (
        numbers["tree_nodes"] + target_action_edges + sequence_variables
    )
    cardinality_work = (
        information_sets + reachable_additions + reachable_multiplications
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
        or numbers["per_pass_linear_work_ceiling"] != expected_per_pass
        or numbers["cardinality_linear_work_ceiling"]
        != sequence_variables + 2 * information_sets
        or cardinality_work > numbers["cardinality_linear_work_ceiling"]
        or numbers["total_logical_work_units"]
        != 2 * expected_per_pass + cardinality_work
        or numbers["target_action_edges"] > numbers["tree_edges"]
        or numbers["tree_edges"] + 1 != numbers["tree_nodes"]
    ):
        raise ValueError("factorized-affine source work identity differs")
    for prefix in ("minimum", "maximum"):
        if (
            numbers[f"{prefix}_continuation_node_evaluations"]
            != numbers["tree_nodes"]
            or numbers[f"{prefix}_action_score_terms"] != target_action_edges
            or numbers[f"{prefix}_action_choice_inspections"]
            != sequence_variables
        ):
            raise ValueError("factorized-affine source pass work differs")
    return _FaceView(
        gain=gain,
        minimum_gain_slope=minimum_gain,
        maximum_gain_slope=maximum_gain,
        total_cardinality=total,
        reachable_cardinality=reachable,
        factor_keys=frozenset(factors),
        materialized_tapes=numbers["materialized_response_tapes"],
    )


def _parent_section_index() -> Mapping[tuple[str, int], str]:
    path = _ROOT / ADR0359_PARENT_ARTIFACT_RELATIVE_PATH
    raw = path.read_bytes()
    if (
        len(raw) != ADR0359_PARENT_ARTIFACT_BYTES
        or sha256(raw).hexdigest() != ADR0359_PARENT_ARTIFACT_SHA256
    ):
        raise ValueError("ADR-0359 parent artifact bytes differ")
    record = _load_json(raw)
    if record.get("passed") is not True:
        raise ValueError("ADR-0359 parent artifact did not pass")
    result: dict[tuple[str, int], str] = {}
    for direction in _sequence(record.get("directions"), "parent directions"):
        row = _mapping(direction, "parent direction")
        label = row.get("label")
        if not isinstance(label, str):
            raise ValueError("ADR-0359 parent direction label differs")
        for target in _sequence(row.get("target_rows"), "parent target rows"):
            target_row = _mapping(target, "parent target row")
            target_player = _integer(
                target_row.get("target_player"), "parent target player"
            )
            section = _mapping(target_row.get("composed_section"), "parent section")
            digest = _digest(section.get("section_sha256"), "parent section digest")
            key = (label, target_player)
            if key in result:
                raise ValueError("ADR-0359 parent section repeats")
            result[key] = digest
    if len(result) != 8:
        raise ValueError("ADR-0359 parent section inventory differs")
    return MappingProxyType(result)


def _verify_integration(
    record: Any,
    *,
    label: str,
    acting_player: int,
    target_player: int,
    parent_section_sha256: str,
) -> _IntegrationView:
    integration = _mapping(record, "integration")
    _keys(integration, _INTEGRATION_KEYS, "integration")
    if (
        integration["acting_player"] != acting_player
        or integration["target_player"] != target_player
        or integration["certificate_identity_authority"] != "total_function_only"
        or integration["reachable_identity_role"] != "reporting_only"
        or integration["ray_authority"] != "exact_selector_normal_fan"
        or integration["point_authority"]
        != "two_pass_factorized_directional_face"
        or integration["epigraph_orientation"]
        != "z_greater_than_or_equal_to_every_row"
    ):
        raise ValueError(f"{label} integration authority differs")
    if [
        _exact_fraction(row, "envelope domain")
        for row in _sequence(integration["exact_envelope_domain"], "envelope domain")
    ] != [Fraction(0), Fraction(1)]:
        raise ValueError(f"{label} envelope domain differs")
    if (
        integration["parent_section_sha256"] != parent_section_sha256
        or integration["reproduced_section_sha256"] != parent_section_sha256
        or integration["parent_section_identity"] is not True
    ):
        raise ValueError(f"{label} authenticated parent-section identity differs")
    source = _verify_source_face(
        integration["source_face"],
        acting_player=acting_player,
        target_player=target_player,
    )
    source_upper = _exact_fraction(
        integration["source_cell_upper"], "source cell upper"
    )
    legacy = _exact_fraction(
        integration["legacy_source_breakpoint"], "legacy source breakpoint"
    )
    if source_upper != legacy or not Fraction(0) <= source_upper <= Fraction(1):
        raise ValueError(f"{label} source breakpoint differs")

    raw_pieces = _sequence(integration["pieces"], "integration pieces")
    pieces = []
    for index, item in enumerate(raw_pieces):
        piece = _mapping(item, f"piece {index}")
        _keys(
            piece,
            frozenset(
                {
                    "intercept",
                    "lower",
                    "reachable_state",
                    "reachable_support_cardinality",
                    "response_tape",
                    "slope",
                    "total_function_cardinality",
                    "total_state",
                    "upper",
                    "witness",
                }
            ),
            "piece",
        )
        lower = _exact_fraction(piece["lower"], "piece lower")
        upper = _exact_fraction(piece["upper"], "piece upper")
        witness = _exact_fraction(piece["witness"], "piece witness")
        tape = _tape(piece["response_tape"], "piece tape")
        if (
            not Fraction(0) <= lower < witness < upper <= Fraction(1)
            or frozenset(dict(tape)) != source.factor_keys
            or piece["total_state"] not in _STATES
            or piece["reachable_state"] not in _STATES
        ):
            raise ValueError(f"{label} piece geometry or identity differs")
        total = _integer(piece["total_function_cardinality"], "piece total", minimum=1)
        reachable = _integer(
            piece["reachable_support_cardinality"], "piece reachable", minimum=1
        )
        if reachable > total:
            raise ValueError(f"{label} piece cardinality order differs")
        pieces.append(
            {
                "lower": lower,
                "upper": upper,
                "witness": witness,
                "intercept": _exact_fraction(piece["intercept"], "piece intercept"),
                "slope": _exact_fraction(piece["slope"], "piece slope"),
                "total": total,
                "reachable": reachable,
                "total_state": piece["total_state"],
                "reachable_state": piece["reachable_state"],
            }
        )
    if not pieces or len(pieces) > 256 or pieces[0]["lower"] != 0:
        raise ValueError(f"{label} piece inventory differs")
    for before, after in zip(pieces, pieces[1:], strict=False):
        boundary = before["upper"]
        if (
            boundary != after["lower"]
            or before["slope"] > after["slope"]
            or before["intercept"] + before["slope"] * boundary
            != after["intercept"] + after["slope"] * boundary
        ):
            raise ValueError(f"{label} convex piece seam differs")
    if pieces[-1]["upper"] != 1 or pieces[0]["upper"] != source_upper:
        raise ValueError(f"{label} piece coverage or source cell differs")
    crossings = tuple(
        _exact_fraction(row, "crossing scale")
        for row in _sequence(integration["crossing_scales"], "crossing scales")
    )
    if crossings != tuple(piece["upper"] for piece in pieces[:-1]):
        raise ValueError(f"{label} crossing inventory differs")

    raw_points = _sequence(integration["point_summary"], "point summary")
    points = []
    for index, item in enumerate(raw_points):
        point = _mapping(item, f"point {index}")
        _keys(
            point,
            frozenset(
                {
                    "active_cell_rows",
                    "deviation_gain",
                    "factor_sha256",
                    "maximum_gain_slope",
                    "minimum_gain_slope",
                    "reachable_state",
                    "reachable_support_cardinality",
                    "sample_kind",
                    "scale",
                    "total_function_cardinality",
                    "total_state",
                }
            ),
            "point summary",
        )
        scale = _exact_fraction(point["scale"], "point scale")
        gain = _exact_fraction(point["deviation_gain"], "point gain")
        minimum_slope = _exact_fraction(
            point["minimum_gain_slope"], "point minimum slope"
        )
        maximum_slope = _exact_fraction(
            point["maximum_gain_slope"], "point maximum slope"
        )
        total = _integer(point["total_function_cardinality"], "point total", minimum=1)
        reachable = _integer(
            point["reachable_support_cardinality"], "point reachable", minimum=1
        )
        if (
            not Fraction(0) <= scale <= Fraction(1)
            or minimum_slope > maximum_slope
            or reachable > total
            or point["sample_kind"] not in {"fan_boundary", "open_segment"}
            or point["total_state"] not in _STATES
            or point["reachable_state"] not in _STATES
        ):
            raise ValueError(f"{label} point semantics differ")
        _digest(point["factor_sha256"], "point factor digest")
        values = [piece["intercept"] + piece["slope"] * scale for piece in pieces]
        maximum = max(values)
        active_slopes = [
            piece["slope"]
            for piece, value in zip(pieces, values, strict=True)
            if value == maximum
        ]
        active_rows = _integer(
            point["active_cell_rows"], "active cell rows", minimum=1
        )
        if (
            gain != maximum
            or active_rows < len(active_slopes)
            or (
                scale not in {Fraction(0), Fraction(1)}
                and active_rows != len(active_slopes)
            )
            or any(gain - value < 0 for value in values)
        ):
            raise ValueError(f"{label} maximum epigraph differs")
        if point["sample_kind"] == "open_segment":
            containing = [
                piece for piece in pieces if piece["lower"] < scale < piece["upper"]
            ]
            if (
                len(containing) != 1
                or scale != containing[0]["witness"]
                or minimum_slope != maximum_slope
                or minimum_slope != containing[0]["slope"]
                or total != containing[0]["total"]
                or reachable != containing[0]["reachable"]
                or point["total_state"] != containing[0]["total_state"]
                or point["reachable_state"] != containing[0]["reachable_state"]
            ):
                raise ValueError(f"{label} open-piece slope differs")
        elif scale == 0:
            if max(active_slopes) != maximum_slope:
                raise ValueError(f"{label} source inward slope differs")
        elif scale == 1:
            if min(active_slopes) != minimum_slope:
                raise ValueError(f"{label} endpoint inward slope differs")
        elif min(active_slopes) != minimum_slope or max(active_slopes) != maximum_slope:
            raise ValueError(f"{label} interior face slope seam differs")
        points.append(
            {
                "scale": scale,
                "kind": point["sample_kind"],
                "gain": gain,
                "minimum_slope": minimum_slope,
                "maximum_slope": maximum_slope,
                "total": total,
                "reachable": reachable,
                "factor_sha256": point["factor_sha256"],
                "active_rows": active_rows,
                "total_state": point["total_state"],
                "reachable_state": point["reachable_state"],
            }
        )
    if [point["scale"] for point in points] != sorted(
        point["scale"] for point in points
    ) or len({point["scale"] for point in points}) != len(points):
        raise ValueError(f"{label} point schedule differs")
    source_point = points[0]
    if (
        source_point["scale"] != 0
        or source_point["gain"] != source.gain
        or source_point["minimum_slope"] != source.minimum_gain_slope
        or source_point["maximum_slope"] != source.maximum_gain_slope
        or source_point["total"] != source.total_cardinality
        or source_point["reachable"] != source.reachable_cardinality
        or source_point["factor_sha256"] != integration["source_face"]["factor_sha256"]
        or source_point["total_state"]
        != ("tie_unresolved" if source.total_cardinality > 1 else "fixed")
        or source_point["reachable_state"]
        != ("tie_unresolved" if source.reachable_cardinality > 1 else "fixed")
    ):
        raise ValueError(f"{label} source point differs")

    mode = integration["mode"]
    window = integration["single_tape_window"]
    work = _mapping(integration["work"], "integration work")
    _keys(work, _INTEGRATION_WORK_KEYS, "integration work")
    numbers = {
        key: _integer(value, f"integration work {key}") for key, value in work.items()
    }
    window_scale = None
    if source.total_cardinality > 1:
        if (
            mode != "factorized_tie_aware_maximum_envelope"
            or window is not None
            or numbers["selector_window_v2_calls"] != 0
            or numbers["float_selector_score_calls"] != 0
        ):
            raise ValueError(f"{label} exact source-tie dispatch differs")
    else:
        window_row = _mapping(window, "singleton window")
        _keys(
            window_row,
            frozenset(
                {
                    "exact_source_action_ties",
                    "first_switch_competing_action",
                    "first_switch_information_key",
                    "first_switch_source_action",
                    "scale_limit",
                    "scale_limit_hex",
                    "selector_comparisons",
                }
            ),
            "singleton window",
        )
        window_scale = _finite_float(window_row["scale_limit"], "window scale")
        if (
            window_scale > 1.0
            or float.fromhex(window_row["scale_limit_hex"]) != window_scale
            or Fraction.from_float(window_scale) > source_upper
            or numbers["selector_window_v2_calls"] != 1
            or numbers["float_selector_score_calls"] != 2
            or (window_scale > 0.0 and mode != "v2_single_tape")
            or (window_scale == 0.0 and mode != "fail_closed_single_tape")
        ):
            raise ValueError(f"{label} singleton dispatch differs")
        _integer(window_row["selector_comparisons"], "selector comparisons")
        _integer(window_row["exact_source_action_ties"], "source action ties")
    boundary_count = sum(point["kind"] == "fan_boundary" for point in points)
    segment_count = sum(point["kind"] == "open_segment" for point in points)
    if (
        segment_count != len(pieces)
        or {
            point["scale"] for point in points if point["kind"] == "fan_boundary"
        }
        != {Fraction(0), Fraction(1), *crossings}
    ):
        raise ValueError(f"{label} point/fan partition differs")
    fan_counts = _mapping(integration["fan_counts"], "fan counts")
    fan_cells = _integer(fan_counts.get("cells"), "fan cells", minimum=1)
    if fan_counts != {
        "cells": fan_cells,
        "segments": segment_count,
        "boundaries": boundary_count,
        "point_face_observations": len(points),
    } or not len(pieces) <= fan_cells <= 256 or any(
        point["active_rows"] > fan_cells for point in points
    ):
        raise ValueError(f"{label} fan counts differ")
    if (
        numbers["fan_cell_rows"] != fan_cells
        or numbers["fan_segments"] != segment_count
        or numbers["fan_boundaries"] != boundary_count
        or numbers["point_face_observations"] != len(points)
        or numbers["materialized_response_tapes"] != 0
        or numbers["envelope_row_evaluations"]
        != numbers["epigraph_residual_evaluations"]
        or numbers["envelope_row_evaluations"] != fan_cells * len(points)
        or source.materialized_tapes != 0
    ):
        raise ValueError(f"{label} integration work differs")
    payload = dict(integration)
    recorded_digest = payload.pop("integration_sha256")
    if recorded_digest != _canonical_hash(payload):
        raise ValueError(f"{label} integration digest differs")
    return _IntegrationView(
        mode=str(mode),
        pieces=len(pieces),
        fan_cells=fan_cells,
        points=len(points),
        boundaries=boundary_count,
        segments=segment_count,
        total_cardinality=source.total_cardinality,
        reachable_cardinality=source.reachable_cardinality,
        maximum_point_total_cardinality=max(point["total"] for point in points),
        maximum_point_reachable_cardinality=max(
            point["reachable"] for point in points
        ),
        float_scores=numbers["float_selector_score_calls"],
        window_calls=numbers["selector_window_v2_calls"],
        materialized_tapes=numbers["materialized_response_tapes"],
        window_scale=window_scale,
    )


def _verify_config() -> Mapping[str, Any]:
    path = _ROOT / ADR0359_CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != ADR0359_CONFIG_SHA256:
        raise ValueError("ADR-0359 config bytes differ")
    config = _load_json(raw)
    for field, relative in _SOURCE_PATHS.items():
        if config.get(field) != _canonical_lf_sha256(_ROOT / relative):
            raise ValueError(f"ADR-0359 config source differs: {field}")
    if (
        config.get("expected_parent_protocol_sha256")
        != ADR0359_PARENT_PROTOCOL_SHA256
        or config.get("expected_parent_artifact_sha256")
        != ADR0359_PARENT_ARTIFACT_SHA256
        or config.get("expected_parent_artifact_bytes")
        != ADR0359_PARENT_ARTIFACT_BYTES
        or config.get("expected_implementation_sha256") != ADR0359_RUNNER_SHA256
        or config.get("hash_semantics")
        != "canonical_lf_sha256_for_all_bound_text_sources"
    ):
        raise ValueError("ADR-0359 config protocol differs")
    return MappingProxyType(config)


def _verify_record(record: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    _keys(record, _TOP_KEYS, "factorized-affine artifact")
    identities = {
        "config_sha256": ADR0359_CONFIG_SHA256,
        "implementation_sha256": ADR0359_RUNNER_SHA256,
        "parent_artifact_sha256": ADR0359_PARENT_ARTIFACT_SHA256,
        "parent_artifact_bytes": ADR0359_PARENT_ARTIFACT_BYTES,
        "parent_protocol_sha256": ADR0359_PARENT_PROTOCOL_SHA256,
        "root_public_state_sha256": ADR0359_ROOT_PUBLIC_STATE_SHA256,
        "public_schema_sha256": ADR0359_PUBLIC_SCHEMA_SHA256,
        "game_structural_sha256": ADR0359_GAME_STRUCTURAL_SHA256,
        "game_provenance_sha256": ADR0359_GAME_PROVENANCE_SHA256,
        "source_policy_sha256": ADR0359_SOURCE_POLICY_SHA256,
    }
    if any(record[key] != value for key, value in identities.items()):
        raise ValueError("factorized-affine retained identity differs")
    if (
        record["schema_version"]
        != "legal-responder-raise-h4-factorized-affine-v1"
        or record["status"]
        != "legal_responder_raise_h4_factorized_affine_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_untouched_factorized_tie_aware_affine_confirmation_preregistration"
        or record["actions_emitted"] != 0
        or record["quality_rows_serialized"] != 0
        or record["strategy_labels_generated"] != 0
        or record["strategy_quality_claim"] is not None
        or tuple(record["limitations"]) != _LIMITATIONS
    ):
        raise ValueError("factorized-affine terminal or claims differ")
    environment = _mapping(record["environment"], "environment")
    _keys(environment, frozenset({"git", "platform", "python", "runtime"}), "environment")
    git = _mapping(environment["git"], "environment git")
    if git != {
        "commit": ADR0359_INVOCATION_SOURCE_COMMIT,
        "dirty": False,
        "strict_status": True,
    }:
        raise ValueError("factorized-affine invocation Git identity differs")
    if environment["runtime"] != {
        "backend": "cpu_fraction_exact_fan_face_factorized_affine"
    } or not isinstance(environment["platform"], str) or not isinstance(
        environment["python"], str
    ):
        raise ValueError("factorized-affine environment differs")
    if record["methodology"] != {
        "analysis_wall_semantics": (
            "execute_entry_through_scientific_payload_materialization_excluding_"
            "gate_evaluation_result_render_fsync_and_process_overhead"
        ),
        "claims_policy": (
            "finite_same_fixture_legal_h4_development_integration_only_no_"
            "untouched_confirmation_action_clock_full_width_multiway_quality_or_"
            "strength_claim"
        ),
        "point_source": "two_pass_factorized_directional_face",
        "ray_source": "exact_selector_normal_fan",
        "result_path_lifecycle": (
            "absent_at_source_commit_exclusive_first_terminal_no_retry_no_overwrite"
        ),
        "singleton_dispatch": "selector_window_v2_or_typed_fail_closed",
        "source_tie_dispatch": "factorized_tie_aware_maximum_envelope",
        "subject_wall_semantics": (
            "eight_live_factorized_integration_builds_only_excluding_parent_"
            "rebind_fixture_direction_compilation_gate_evaluation_and_serialization"
        ),
        "target_invocations": 8,
    }:
        raise ValueError("factorized-affine methodology differs")
    if record["integration_semantics"] != {
        "cardinality_authority": (
            "total_function_conservative_reachable_support_reporting_only"
        ),
        "cardinality_columns": ["total_function", "reachable_support"],
        "epigraph_orientation": "z_greater_than_or_equal_to_every_row",
        "face_cardinality_bound": None,
        "maximum_fan_pieces": 256,
        "maximum_tree_nodes": 100_000,
        "point_authority": "two_pass_factorized_directional_face",
        "ray_authority": "exact_selector_normal_fan",
        "selector_margin_allowance": 1e-12,
        "singleton_closed_mode": "fail_closed_single_tape",
        "singleton_positive_mode": "v2_single_tape",
        "source_tie_mode": "factorized_tie_aware_maximum_envelope",
    }:
        raise ValueError("factorized-affine integration semantics differ")
    descriptors = _sequence(record["direction_descriptors"], "direction descriptors")
    if descriptors != list(_DIRECTION_DESCRIPTORS) or descriptors != config[
        "direction_descriptors"
    ]:
        raise ValueError("factorized-affine descriptor inventory differs")
    parent_index = _parent_section_index()
    directions = _sequence(record["directions"], "directions")
    if len(directions) != 4:
        raise ValueError("factorized-affine direction count differs")
    views = []
    section_times = []
    for direction_index, item in enumerate(directions):
        direction = _mapping(item, f"direction {direction_index}")
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
        if descriptor != descriptors[direction_index]:
            raise ValueError("factorized-affine direction descriptor differs")
        targets = _sequence(direction["target_rows"], "target rows")
        if len(targets) != 2:
            raise ValueError("factorized-affine target-player count differs")
        for target_player, target_item in enumerate(targets):
            target = _mapping(target_item, "target row")
            _keys(
                target,
                frozenset({"checks", "integration", "subject_seconds", "target_player"}),
                "target row",
            )
            if target["target_player"] != target_player:
                raise ValueError("factorized-affine target identity differs")
            checks = _mapping(target["checks"], "section checks")
            _keys(checks, _SECTION_CHECK_KEYS, "section checks")
            if any(value is not True for value in checks.values()):
                raise ValueError("factorized-affine section check differs")
            views.append(
                _verify_integration(
                    target["integration"],
                    label=f"{direction['label']} target {target_player}",
                    acting_player=0,
                    target_player=target_player,
                    parent_section_sha256=parent_index[(
                        str(direction["label"]),
                        target_player,
                    )],
                )
            )
            section_times.append(
                _finite_float(target["subject_seconds"], "section subject seconds")
            )
    aggregate = _mapping(record["aggregate"], "aggregate")
    expected_aggregate_keys = frozenset(
        {
            "checks",
            "fan_boundaries",
            "fan_cells",
            "fan_segments",
            "float_selector_score_calls",
            "materialized_response_tapes",
            "maximum_reachable_support_cardinality",
            "maximum_total_function_cardinality",
            "mode_counts",
            "parent_rebind_seconds",
            "piece_counts",
            "point_face_observations",
            "section_subject_seconds",
            "sections",
            "selector_window_scale_limits",
            "selector_window_v2_calls",
            "subject_seconds",
        }
    )
    _keys(aggregate, expected_aggregate_keys, "aggregate")
    rebuilt = {
        "sections": len(views),
        "mode_counts": {
            name: sum(view.mode == name for view in views)
            for name in (
                "factorized_tie_aware_maximum_envelope",
                "v2_single_tape",
                "fail_closed_single_tape",
            )
        },
        "piece_counts": [view.pieces for view in views],
        "selector_window_scale_limits": [view.window_scale for view in views],
        "maximum_total_function_cardinality": max(
            view.total_cardinality for view in views
        ),
        "maximum_reachable_support_cardinality": max(
            view.reachable_cardinality for view in views
        ),
        "fan_cells": sum(view.fan_cells for view in views),
        "fan_segments": sum(view.segments for view in views),
        "fan_boundaries": sum(view.boundaries for view in views),
        "point_face_observations": sum(view.points for view in views),
        "float_selector_score_calls": sum(view.float_scores for view in views),
        "selector_window_v2_calls": sum(view.window_calls for view in views),
        "materialized_response_tapes": sum(
            view.materialized_tapes for view in views
        ),
        "section_subject_seconds": section_times,
        "subject_seconds": sum(section_times),
    }
    if any(aggregate[key] != value for key, value in rebuilt.items()):
        raise ValueError("factorized-affine aggregate differs")
    observations = {
        "compact_envelope_pieces": sum(view.pieces for view in views),
        "fan_boundaries": rebuilt["fan_boundaries"],
        "fan_cells": rebuilt["fan_cells"],
        "fan_rows_without_distinct_interval_piece": rebuilt["fan_cells"]
        - sum(view.pieces for view in views),
        "fan_segments": rebuilt["fan_segments"],
        "factorized_modes": rebuilt["mode_counts"][
            "factorized_tie_aware_maximum_envelope"
        ],
        "maximum_reachable_support_cardinality": rebuilt[
            "maximum_reachable_support_cardinality"
        ],
        "maximum_serialized_point_reachable_support_cardinality": max(
            view.maximum_point_reachable_cardinality for view in views
        ),
        "maximum_serialized_point_total_function_cardinality": max(
            view.maximum_point_total_cardinality for view in views
        ),
        "maximum_total_function_cardinality": rebuilt[
            "maximum_total_function_cardinality"
        ],
        "point_face_observations": rebuilt["point_face_observations"],
        "sections": rebuilt["sections"],
        "v2_singletons": rebuilt["mode_counts"]["v2_single_tape"],
        "zero_materialized_tapes": rebuilt["materialized_response_tapes"],
    }
    if observations != dict(_EXPECTED_OBSERVATIONS):
        raise ValueError("factorized-affine retained observations differ")
    aggregate_checks = _mapping(aggregate["checks"], "aggregate checks")
    _keys(aggregate_checks, _SECTION_CHECK_KEYS, "aggregate checks")
    if any(value is not True for value in aggregate_checks.values()):
        raise ValueError("factorized-affine aggregate check differs")
    parent_rebind = _finite_float(
        aggregate["parent_rebind_seconds"], "parent rebind seconds"
    )
    subject = _finite_float(aggregate["subject_seconds"], "subject seconds")
    analysis = _finite_float(record["analysis_seconds"], "analysis seconds")
    if parent_rebind > 10.0 or subject > 180.0 or analysis > 240.0 or subject > analysis:
        raise ValueError("factorized-affine infrastructure wall differs")
    scientific_bytes = len(
        json.dumps(
            {"directions": directions, "aggregate": aggregate},
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    if record["scientific_payload_bytes"] != scientific_bytes or scientific_bytes > 4_194_304:
        raise ValueError("factorized-affine scientific bytes differ")
    gates = _mapping(record["gates"], "gates")
    _keys(gates, _GATE_KEYS, "gates")
    if any(value is not True for value in gates.values()):
        raise ValueError("factorized-affine frozen gate is not literally true")


def verify_adr0359_legal_h4_factorized_affine_result_artifact(
    path: Path | None = None,
) -> VerifiedLegalH4FactorizedAffineResult:
    """Verify and return the exact retained ADR-0359 result without writing."""

    artifact_path = (
        _ROOT / ADR0359_ARTIFACT_RELATIVE_PATH if path is None else Path(path)
    )
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0359_ARTIFACT_BYTES:
        raise ValueError("ADR-0359 artifact byte count differs")
    digest = sha256(raw).hexdigest()
    if digest != ADR0359_ARTIFACT_SHA256:
        raise ValueError("ADR-0359 artifact SHA-256 differs")
    config = _verify_config()
    record = _load_json(raw)
    _verify_record(record, config)
    return VerifiedLegalH4FactorizedAffineResult(
        record=MappingProxyType(record),
        source_commit=ADR0359_INVOCATION_SOURCE_COMMIT,
        artifact_sha256=digest,
        artifact_bytes=len(raw),
        authenticated_only_fields=(
            "non_source_point_factor_cardinality_and_active_face_fields",
            "non_quotient_fan_rows_and_individual_epigraph_residuals",
            "reproduced_section_sha256",
        ),
    )


__all__ = [
    "ADR0359_ARTIFACT_BYTES",
    "ADR0359_ARTIFACT_RELATIVE_PATH",
    "ADR0359_ARTIFACT_SHA256",
    "ADR0359_CONFIG_SHA256",
    "ADR0359_INVOCATION_SOURCE_COMMIT",
    "ADR0359_RESULT_PROTOCOL",
    "ADR0359_RESULT_PROTOCOL_SHA256",
    "VerifiedLegalH4FactorizedAffineResult",
    "verify_adr0359_legal_h4_factorized_affine_result_artifact",
]
