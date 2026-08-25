"""Independent read-only owner for ADR-0361's retained first terminal.

The ADR-0361 writer is permanently consumed and must never be replayed.  Its
sole artifact recorded a rejection because a Python chained comparison made
the zero-emission gate false even though all four serialized emission fields
have their frozen zero/null values.  This module does not repair, rewrite, or
relabel that terminal.  It imports only the standard library, reads committed
bytes, independently rebinds the reconstruction-complete scientific payload,
and reports the recorded and corrected gate interpretations separately.

Game-derived coefficients, policies, and selector-window score tables are not
re-executed here.  They remain authenticated to the sealed invocation source.
All evidence that *was* serialized is checked independently: strict JSON,
provenance, row-growth algebra, fan coverage, exact face/cardinality/work
identities, every epigraph residual, compact-envelope seams, typed dispatch,
coordinates, timing aggregates, emissions, and the recorded gate vector.
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


ADR0362_INVOCATION_SOURCE_COMMIT = (
    "8bcf00662f2903686d91311afe1d36a2669b97d6"
)
ADR0362_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-h4-factorized-affine-confirmation-v1.json"
)
ADR0362_ARTIFACT_BYTES = 7_361_728
ADR0362_ARTIFACT_SHA256 = (
    "afa0459542cbdbf99be3d30a8902dcadf24e160e3b81f2eb671dea8a6c0ae33c"
)
ADR0362_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-h4-factorized-affine-confirmation-v1.json"
)
ADR0362_CONFIG_SHA256 = (
    "07047abf345d5278023cc6820d4ce196249bf8aa8668a0457a871af50169e638"
)
ADR0362_RUNNER_SHA256 = (
    "65875f914b75ca282f3c785daee71bb1c7ba39909ae1298c1353368739d0b573"
)
ADR0362_PARENT_PROTOCOL_SHA256 = (
    "c75ef3f8eb5011775049080b98302fec0d3f6c72bf6cf58bacfa1146fe0752fa"
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/ADR-0360-source-seal-the-fresh-legal-h4-"
            "factorized-affine-confirmation-population.md"
        ),
        "expected_population_source_sha256": (
            "src/pontius/legal_h4_factorized_affine_confirmation_population.py"
        ),
        "expected_population_seal_sha256": (
            "src/pontius/legal_h4_factorized_affine_confirmation_population_seal.py"
        ),
        "expected_population_controls_sha256": (
            "tests/test_legal_h4_factorized_affine_confirmation_population.py"
        ),
        "expected_direction_compiler_sha256": (
            "src/pontius/legal_h4_factorized_affine_confirmation_directions.py"
        ),
        "expected_direction_controls_sha256": (
            "tests/test_legal_h4_factorized_affine_confirmation_directions.py"
        ),
        "expected_complete_evidence_sha256": (
            "src/pontius/complete_factorized_affine_evidence.py"
        ),
        "expected_complete_evidence_controls_sha256": (
            "tests/test_complete_factorized_affine_evidence.py"
        ),
        "expected_factorized_affine_sha256": (
            "src/pontius/factorized_tie_aware_affine.py"
        ),
        "expected_factorized_affine_seal_sha256": (
            "src/pontius/factorized_tie_aware_affine_seal.py"
        ),
        "expected_factorized_affine_controls_sha256": (
            "tests/test_factorized_tie_aware_affine.py"
        ),
        "expected_tie_conformance_sha256": (
            "src/pontius/tie_semantics_conformance_v2.py"
        ),
        "expected_tie_conformance_controls_sha256": (
            "tests/test_tie_semantics_conformance_v2.py"
        ),
        "expected_directional_face_oracle_sha256": (
            "src/pontius/exact_directional_face_oracle.py"
        ),
        "expected_directional_face_seal_sha256": (
            "src/pontius/exact_directional_face_oracle_seal.py"
        ),
        "expected_exact_fan_sha256": "src/pontius/exact_selector_fan.py",
        "expected_exact_selector_oracle_sha256": (
            "src/pontius/exact_selector_window_oracle.py"
        ),
        "expected_exact_sequence_oracle_sha256": (
            "src/pontius/exact_sequence_form_coefficient_oracle.py"
        ),
        "expected_selector_window_v2_sha256": "src/pontius/selector_window_v2.py",
        "expected_selector_window_sha256": "src/pontius/selector_window.py",
        "expected_cfr_sha256": "src/pontius/cfr.py",
        "expected_row_growth_audit_sha256": (
            "src/pontius/one_seat_row_growth_audit.py"
        ),
        "expected_generation_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_lp_sha256": "src/pontius/linear_program.py",
        "expected_evaluation_sha256": "src/pontius/evaluation.py",
        "expected_game_sha256": "src/pontius/game.py",
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_legal_spine_sha256": "src/pontius/legal_decision_spine_v2.py",
        "expected_river_sha256": "src/pontius/river.py",
        "expected_runner_harness_sha256": "src/pontius/runner_harness.py",
        "expected_strict_loader_sha256": "src/pontius/runner_harness_v2.py",
        "expected_implementation_sha256": (
            "src/pontius/legal_h4_factorized_affine_confirmation.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_h4_factorized_affine_confirmation.py"
        ),
    }
)

_EXPECTED_CONTEXT_IDS = tuple(
    f"adr0360-legal-h4-confirmation-{ordinal:02d}" for ordinal in range(4)
)
_REGRET_HISTORIES = (
    "p0:raise-to-2/p1:raise-to-4",
    "p0:raise-to-3/p1:raise-to-4",
    "root",
)
_DIRECTION_CLASSES = (
    "one_step_dcfr_regret_vertex_per_public_history",
    "one_step_dcfr_regret_vertex_per_public_history",
    "one_step_dcfr_regret_vertex_per_public_history",
    "converged_one_seat_row_growth_proposal",
)
_LIMITATIONS = (
    "finite_fresh_h4_mechanism_confirmation_only",
    "not_full_width_capacity_or_action_clock_latency",
    "not_multiway_response_closure_or_cross_street_handoff",
    "not_action_quality_strategy_strength_or_complete_bot_evidence",
)
_AUTHENTICATED_ONLY_FIELDS = (
    "game_derived_policy_and_affine_coefficient_generation",
    "selector_window_underlying_float_score_tables",
    "live_game_reexecution_and_wall_clock_remeasurement",
)

_TOP_KEYS = frozenset(
    {
        "actions_emitted",
        "campaign_seconds",
        "config_sha256",
        "contexts",
        "decision",
        "environment",
        "gates",
        "implementation_sha256",
        "limitations",
        "methodology",
        "observations",
        "parent_protocol_sha256",
        "passed",
        "population",
        "quality_rows_serialized",
        "schema_version",
        "section_coordinates_sha256",
        "section_count",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
        "subject_seconds",
    }
)
_CONTEXT_KEYS = frozenset(
    {
        "candidate_ordinal",
        "context_id",
        "direction_generation_seconds",
        "directions",
        "game_provenance_sha256",
        "game_structural_sha256",
        "public_state_sha256",
        "row_growth",
        "semantic_sha256",
        "source_policy_sha256",
    }
)
_DIRECTION_KEYS = frozenset(
    {
        "changed_public_histories",
        "context_id",
        "direction_class",
        "endpoint_policy_sha256",
        "label",
        "targets",
    }
)
_TARGET_KEYS = frozenset(
    {
        "complete_evidence",
        "complete_evidence_checks",
        "context_id",
        "direction_label",
        "exact_authorities",
        "section_passed",
        "section_subject_seconds",
        "target_player",
        "typed_dispatch",
    }
)
_COMPLETE_KEYS = frozenset(
    {
        "acting_player",
        "certificate_identity_authority",
        "complete_section_sha256",
        "epigraph_orientation",
        "epigraph_residual_matrix",
        "exact_envelope_domain",
        "mode",
        "pieces",
        "point_authority",
        "raw_section",
        "ray_authority",
        "reachable_identity_role",
        "single_tape_window",
        "source_face",
        "target_player",
        "work",
    }
)
_RAW_KEYS = frozenset(
    {"cell_gain_rows", "crossing_scales", "fan", "samples", "section_sha256"}
)
_FAN_KEYS = frozenset(
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
        "source_tape_sha256",
        "target_player",
        "total_tie_points",
    }
)
_FACE_KEYS = frozenset(
    {
        "acting_player",
        "deviation_gain",
        "face_sha256",
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
        "complete_live_record_identity",
        "complete_raw_factors",
        "complete_raw_fan_rows",
        "complete_raw_section_identity",
        "dual_cardinality_semantics",
        "epigraph_residual_matrix_complete",
        "epigraph_residual_orientation",
        "exact_authority_and_domain",
        "integration_work_identity",
        "piece_partition_and_convexity",
        "zero_materialized_tapes",
    }
)
_GATE_KEYS = frozenset(
    {
        "all_or_nothing_coordinates",
        "campaign_wall",
        "clean_git_state",
        "complete_section_evidence",
        "context_identity",
        "direction_inventory",
        "dual_cardinality_semantics",
        "exact_authorities",
        "finite",
        "no_target_outcome_gate",
        "passed",
        "population_identity",
        "row_growth_exact_acceptance",
        "section_subject_wall",
        "subject_wall",
        "typed_dispatch",
        "zero_actions_and_quality_rows",
        "zero_materialized_tapes",
    }
)
_STATES = frozenset({"fixed", "tie_unresolved", "switched"})


@dataclass(frozen=True, slots=True)
class VerifiedLegalH4FactorizedAffineConfirmation:
    """Independent assessment of the sole ADR-0361 terminal."""

    record: Mapping[str, Any]
    artifact_sha256: str
    artifact_bytes: int
    source_commit: str
    recorded_passed: bool
    recorded_decision: str
    scientific_payload_rebound: bool
    intended_zero_emission_predicate: bool
    corrected_gate_vector: Mapping[str, bool]
    authenticated_only_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _FaceView:
    gain: Fraction
    minimum_gain_slope: Fraction
    maximum_gain_slope: Fraction
    total_cardinality: int
    reachable_cardinality: int
    minimum_tape: tuple[tuple[str, str], ...]
    maximum_tape: tuple[tuple[str, str], ...]
    materialized_tapes: int


@dataclass(frozen=True, slots=True)
class _SectionView:
    mode: str
    pieces: int
    source_total_cardinality: int
    source_reachable_cardinality: int
    window_scale: float | None
    materialized_tapes: int


@dataclass(frozen=True, slots=True)
class _FanView:
    source_tape: tuple[tuple[str, str], ...]
    source_cell_upper: Fraction
    cells: tuple[Mapping[str, Any], ...]
    cell_tapes: tuple[tuple[tuple[str, str], ...], ...]
    boundaries: tuple[Fraction, ...]
    segments: tuple[Mapping[str, Any], ...]
    points: tuple[Mapping[str, Any], ...]


def _canonical_hash(value: object) -> str:
    rendered = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
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
            raise ValueError(f"ADR-0362 JSON duplicates key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"ADR-0362 JSON contains non-finite token {token}")


def _load_json(raw: bytes) -> dict[str, Any]:
    try:
        record = json.loads(
            raw,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ADR-0362 input is not strict UTF-8 JSON") from error
    if not isinstance(record, dict):
        raise ValueError("ADR-0362 JSON root is not an object")
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
        raise ValueError(f"{label} is not a sorted function")
    return tape


def _tape_digest(raw: Any, label: str) -> tuple[tuple[str, str], ...]:
    tape = _tape(raw, label)
    return tape


def _reachable_cardinality(
    factors: Mapping[str, Mapping[str, Any]],
) -> tuple[int, int, int]:
    children: dict[tuple[str, str], list[str]] = {}
    roots: list[str] = []
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
            raise ValueError("factor graph contains a cycle")
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
        raise ValueError("factor graph has no rooted path")
    return result, additions, multiplications


def _verify_face(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
    expected_scale: Fraction,
    label: str,
) -> _FaceView:
    face = _mapping(record, label)
    _keys(face, _FACE_KEYS, label)
    if face["acting_player"] != acting_player or face["target_player"] != target_player:
        raise ValueError(f"{label} player identity differs")
    if _exact_fraction(face["scale"], f"{label} scale") != expected_scale:
        raise ValueError(f"{label} scale differs")
    response = _exact_fraction(face["response_value"], f"{label} response")
    profile = _exact_fraction(face["profile_utility"], f"{label} profile")
    gain = _exact_fraction(face["deviation_gain"], f"{label} gain")
    minimum_response = _exact_fraction(
        face["minimum_response_slope"], f"{label} minimum response slope"
    )
    maximum_response = _exact_fraction(
        face["maximum_response_slope"], f"{label} maximum response slope"
    )
    profile_slope = _exact_fraction(
        face["profile_utility_slope"], f"{label} profile slope"
    )
    minimum_gain = _exact_fraction(
        face["minimum_gain_slope"], f"{label} minimum gain slope"
    )
    maximum_gain = _exact_fraction(
        face["maximum_gain_slope"], f"{label} maximum gain slope"
    )
    if (
        gain != response - profile
        or minimum_gain != minimum_response - profile_slope
        or maximum_gain != maximum_response - profile_slope
        or minimum_response > maximum_response
        or minimum_gain > maximum_gain
    ):
        raise ValueError(f"{label} affine algebra differs")

    factors: dict[str, Mapping[str, Any]] = {}
    raw_factors = _sequence(face["information_sets"], f"{label} factors")
    factor_position: dict[str, int] = {}
    for index, item in enumerate(raw_factors):
        row = _mapping(item, f"{label} factor {index}")
        _keys(row, _FACTOR_KEYS, f"{label} factor")
        key = row["information_key"]
        actions = tuple(_sequence(row["actions"], f"{label} actions"))
        maximizers = tuple(
            _sequence(row["maximizing_actions"], f"{label} maximizers")
        )
        if (
            not isinstance(key, str)
            or not key
            or key in factors
            or not actions
            or any(not isinstance(action, str) for action in actions)
            or len(set(actions)) != len(actions)
            or not maximizers
            or any(not isinstance(action, str) for action in maximizers)
            or len(set(maximizers)) != len(maximizers)
            or not set(maximizers).issubset(actions)
        ):
            raise ValueError(f"{label} factor schema differs")
        minimum_action = row["minimum_slope_action"]
        maximum_action = row["maximum_slope_action"]
        if minimum_action not in maximizers or maximum_action not in maximizers:
            raise ValueError(f"{label} extremal action is not active")
        if _exact_fraction(
            row["minimum_local_slope"], f"{label} local minimum"
        ) > _exact_fraction(row["maximum_local_slope"], f"{label} local maximum"):
            raise ValueError(f"{label} local slope interval is reversed")
        parent_pair = None
        if row["parent"] is not None:
            parent = _mapping(row["parent"], f"{label} parent")
            _keys(parent, frozenset({"information_key", "action"}), f"{label} parent")
            if not isinstance(parent["information_key"], str) or not isinstance(
                parent["action"], str
            ):
                raise ValueError(f"{label} parent is malformed")
            parent_pair = (parent["information_key"], parent["action"])
        if not isinstance(row["positive_counterfactual_support"], bool):
            raise ValueError(f"{label} support flag is not Boolean")
        factors[key] = {
            "actions": actions,
            "maximizers": maximizers,
            "minimum_action": minimum_action,
            "maximum_action": maximum_action,
            "parent_pair": parent_pair,
            "support": row["positive_counterfactual_support"],
            "state_count": _integer(
                row["state_count"], f"{label} factor state count", minimum=1
            ),
        }
        factor_position[key] = index
    if not factors:
        raise ValueError(f"{label} factor set is empty")
    for key, row in factors.items():
        parent = row["parent_pair"]
        if parent is not None and (
            parent[0] not in factors
            or parent[1] not in factors[parent[0]]["actions"]
            or factor_position[parent[0]] >= factor_position[key]
        ):
            raise ValueError(f"{label} parent sequence differs")

    minimum_tape = _tape(face["minimum_slope_tape"], f"{label} minimum tape")
    maximum_tape = _tape(face["maximum_slope_tape"], f"{label} maximum tape")
    if set(dict(minimum_tape)) != set(factors) or set(dict(maximum_tape)) != set(
        factors
    ):
        raise ValueError(f"{label} extremal tape schema differs")
    for key, row in factors.items():
        if (
            dict(minimum_tape)[key] != row["minimum_action"]
            or dict(maximum_tape)[key] != row["maximum_action"]
        ):
            raise ValueError(f"{label} extremal tape selection differs")

    total = _integer(
        face["total_function_cardinality"], f"{label} total cardinality", minimum=1
    )
    factor_product = 1
    for row in factors.values():
        factor_product *= len(row["maximizers"])
    reachable, reachable_additions, reachable_multiplications = (
        _reachable_cardinality(factors)
    )
    recorded_reachable = _integer(
        face["reachable_support_cardinality"],
        f"{label} reachable cardinality",
        minimum=1,
    )
    if total != factor_product or recorded_reachable != reachable or reachable > total:
        raise ValueError(f"{label} cardinality differs")
    if face["factor_sha256"] != _canonical_hash(
        {
            "information_sets": raw_factors,
            "reachable_support_cardinality": reachable,
            "total_function_cardinality": total,
        }
    ):
        raise ValueError(f"{label} factor digest differs")

    work = _mapping(face["work"], f"{label} work")
    _keys(work, _FACE_WORK_KEYS, f"{label} work")
    numbers = {key: _integer(value, f"{label} work {key}") for key, value in work.items()}
    information_sets = len(factors)
    sequence_variables = sum(len(row["actions"]) for row in factors.values())
    target_action_edges = sum(
        row["state_count"] * len(row["actions"]) for row in factors.values()
    )
    expected_per_pass = numbers["tree_nodes"] + target_action_edges + sequence_variables
    cardinality_work = information_sets + reachable_additions + reachable_multiplications
    if (
        numbers["information_sets"] != information_sets
        or numbers["sequence_variables"] != sequence_variables
        or numbers["target_action_edges"] != target_action_edges
        or numbers["lexicographic_passes"] != 2
        or numbers["materialized_response_tapes"] != 0
        or numbers["total_cardinality_multiplications"] != information_sets
        or numbers["reachable_cardinality_additions"] != reachable_additions
        or numbers["reachable_cardinality_multiplications"] != reachable_multiplications
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
        raise ValueError(f"{label} work identity differs")
    for prefix in ("minimum", "maximum"):
        if (
            numbers[f"{prefix}_continuation_node_evaluations"]
            != numbers["tree_nodes"]
            or numbers[f"{prefix}_action_score_terms"] != target_action_edges
            or numbers[f"{prefix}_action_choice_inspections"] != sequence_variables
        ):
            raise ValueError(f"{label} pass work differs")
    expected_face_digest = _canonical_hash(
        {key: value for key, value in face.items() if key != "face_sha256"}
    )
    if _digest(face["face_sha256"], f"{label} digest") != expected_face_digest:
        raise ValueError(f"{label} digest differs")
    return _FaceView(
        gain=gain,
        minimum_gain_slope=minimum_gain,
        maximum_gain_slope=maximum_gain,
        total_cardinality=total,
        reachable_cardinality=reachable,
        minimum_tape=minimum_tape,
        maximum_tape=maximum_tape,
        materialized_tapes=numbers["materialized_response_tapes"],
    )


def _verify_tape_with_digest(
    raw: Any,
    digest: Any,
    label: str,
) -> tuple[tuple[str, str], ...]:
    tape = _tape(raw, label)
    if _digest(digest, f"{label} digest") != _canonical_hash(raw):
        raise ValueError(f"{label} digest differs")
    return tape


def _tie_keys(value: Any, label: str) -> tuple[str, ...]:
    rows = tuple(_sequence(value, label))
    if any(not isinstance(key, str) or not key for key in rows):
        raise ValueError(f"{label} contains a malformed information key")
    if rows != tuple(sorted(rows)) or len(set(rows)) != len(rows):
        raise ValueError(f"{label} is not a sorted unique key set")
    return rows


def _verify_fan(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
) -> _FanView:
    fan = _mapping(record, "fan")
    _keys(fan, _FAN_KEYS, "fan")
    if fan["acting_player"] != acting_player or fan["target_player"] != target_player:
        raise ValueError("fan player identity differs")
    source_tape = _verify_tape_with_digest(
        fan["source_tape"], fan["source_tape_sha256"], "fan source tape"
    )

    cells: list[Mapping[str, Any]] = []
    cell_tapes: list[tuple[tuple[str, str], ...]] = []
    cell_by_tape: dict[tuple[tuple[str, str], ...], Mapping[str, Any]] = {}
    for ordinal, item in enumerate(_sequence(fan["cells"], "fan cells")):
        cell = _mapping(item, f"fan cell {ordinal}")
        _keys(
            cell,
            frozenset({"lower", "response_tape", "response_tape_sha256", "upper"}),
            "fan cell",
        )
        lower = _exact_fraction(cell["lower"], "fan cell lower")
        upper = _exact_fraction(cell["upper"], "fan cell upper")
        if not Fraction(0) <= lower <= upper <= Fraction(1):
            raise ValueError("fan cell interval differs")
        tape = _verify_tape_with_digest(
            cell["response_tape"], cell["response_tape_sha256"], "fan cell tape"
        )
        if tape in cell_by_tape:
            raise ValueError("fan repeats a cell tape")
        cells.append(cell)
        cell_tapes.append(tape)
        cell_by_tape[tape] = cell
    if not cells or source_tape not in cell_by_tape:
        raise ValueError("fan has no source cell")
    ordering = [
        (
            _exact_fraction(cell["lower"], "fan cell lower"),
            _exact_fraction(cell["upper"], "fan cell upper"),
            tape,
        )
        for cell, tape in zip(cells, cell_tapes, strict=True)
    ]
    if ordering != sorted(ordering):
        raise ValueError("fan cells are not canonically ordered")
    source_upper = _exact_fraction(fan["source_cell_upper"], "source cell upper")
    if source_upper != _exact_fraction(
        cell_by_tape[source_tape]["upper"], "source cell recorded upper"
    ) or source_upper != _exact_fraction(
        fan["legacy_source_breakpoint"], "legacy source breakpoint"
    ):
        raise ValueError("fan source breakpoint identity differs")

    boundaries = tuple(
        sorted(
            {
                Fraction(0),
                Fraction(1),
                *(
                    _exact_fraction(cell[key], f"fan cell {key}")
                    for cell in cells
                    for key in ("lower", "upper")
                ),
            }
        )
    )
    cursor = Fraction(0)
    for lower, upper in sorted(
        (
            _exact_fraction(cell["lower"], "fan coverage lower"),
            _exact_fraction(cell["upper"], "fan coverage upper"),
        )
        for cell in cells
    ):
        if lower > cursor:
            raise ValueError("fan cells leave a coverage gap")
        cursor = max(cursor, upper)
    if cursor != 1:
        raise ValueError("fan cells do not cover the ray")

    segments: list[Mapping[str, Any]] = []
    segment_keys = frozenset(
        {
            "lower",
            "reachable_state",
            "reachable_tape",
            "reachable_tape_sha256",
            "reachable_tie_information_sets",
            "response_tape",
            "response_tape_sha256",
            "total_state",
            "total_tie_information_sets",
            "upper",
            "witness",
        }
    )
    measures = {
        "total": {state: Fraction(0) for state in _STATES},
        "reachable": {state: Fraction(0) for state in _STATES},
    }
    for ordinal, item in enumerate(_sequence(fan["segments"], "fan segments")):
        segment = _mapping(item, f"fan segment {ordinal}")
        _keys(segment, segment_keys, "fan segment")
        if ordinal >= len(boundaries) - 1:
            raise ValueError("fan has too many segments")
        lower = _exact_fraction(segment["lower"], "fan segment lower")
        upper = _exact_fraction(segment["upper"], "fan segment upper")
        witness = _exact_fraction(segment["witness"], "fan segment witness")
        if (
            (lower, upper) != (boundaries[ordinal], boundaries[ordinal + 1])
            or not lower < upper
            or witness != (lower + upper) / 2
        ):
            raise ValueError("fan segment partition differs")
        response_tape = _verify_tape_with_digest(
            segment["response_tape"],
            segment["response_tape_sha256"],
            "fan segment response tape",
        )
        _verify_tape_with_digest(
            segment["reachable_tape"],
            segment["reachable_tape_sha256"],
            "fan segment reachable tape",
        )
        cell = cell_by_tape.get(response_tape)
        if cell is None or _exact_fraction(cell["lower"], "cell lower") > lower or (
            _exact_fraction(cell["upper"], "cell upper") < upper
        ):
            raise ValueError("fan segment is detached from its owning cell")
        total_state = segment["total_state"]
        reachable_state = segment["reachable_state"]
        if total_state not in _STATES or reachable_state not in _STATES:
            raise ValueError("fan segment state differs")
        total_ties = _tie_keys(
            segment["total_tie_information_sets"], "fan segment total ties"
        )
        reachable_ties = _tie_keys(
            segment["reachable_tie_information_sets"], "fan segment reachable ties"
        )
        if not set(reachable_ties).issubset(total_ties):
            raise ValueError("fan reachable ties exceed total ties")
        expected_total = (
            "tie_unresolved"
            if total_ties
            else ("fixed" if response_tape == source_tape else "switched")
        )
        if total_state != expected_total or (reachable_state == "tie_unresolved") != bool(
            reachable_ties
        ):
            raise ValueError("fan segment tie-state semantics differ")
        width = upper - lower
        measures["total"][str(total_state)] += width
        measures["reachable"][str(reachable_state)] += width
        segments.append(segment)
    if len(segments) != len(boundaries) - 1:
        raise ValueError("fan segments do not cover every open interval")

    points: list[Mapping[str, Any]] = []
    point_keys = frozenset(
        {
            "reachable_state",
            "reachable_tape",
            "reachable_tape_sha256",
            "reachable_tie_information_sets",
            "response_tape",
            "response_tape_sha256",
            "scale",
            "total_state",
            "total_tie_information_sets",
        }
    )
    for ordinal, item in enumerate(_sequence(fan["points"], "fan points")):
        point = _mapping(item, f"fan point {ordinal}")
        _keys(point, point_keys, "fan point")
        if ordinal >= len(boundaries) or _exact_fraction(
            point["scale"], "fan point scale"
        ) != boundaries[ordinal]:
            raise ValueError("fan point boundary inventory differs")
        response_tape = _verify_tape_with_digest(
            point["response_tape"], point["response_tape_sha256"], "fan point tape"
        )
        _verify_tape_with_digest(
            point["reachable_tape"],
            point["reachable_tape_sha256"],
            "fan point reachable tape",
        )
        total_ties = _tie_keys(
            point["total_tie_information_sets"], "fan point total ties"
        )
        reachable_ties = _tie_keys(
            point["reachable_tie_information_sets"], "fan point reachable ties"
        )
        if not set(reachable_ties).issubset(total_ties):
            raise ValueError("fan point reachable ties exceed total ties")
        total_state = point["total_state"]
        reachable_state = point["reachable_state"]
        expected_total = (
            "tie_unresolved"
            if total_ties
            else ("fixed" if response_tape == source_tape else "switched")
        )
        if (
            total_state not in _STATES
            or reachable_state not in _STATES
            or total_state != expected_total
            or (reachable_state == "tie_unresolved") != bool(reachable_ties)
        ):
            raise ValueError("fan point tie-state semantics differ")
        points.append(point)
    if len(points) != len(boundaries):
        raise ValueError("fan points do not cover every boundary")

    recorded_measures = _mapping(fan["measures"], "fan measures")
    expected_measure_keys = frozenset(
        f"{identity}_{state}"
        for identity in ("total", "reachable")
        for state in _STATES
    )
    _keys(recorded_measures, expected_measure_keys, "fan measures")
    for identity in ("total", "reachable"):
        if sum(measures[identity].values(), Fraction(0)) != 1:
            raise ValueError("fan measures do not partition one")
        for state in _STATES:
            if _exact_fraction(
                recorded_measures[f"{identity}_{state}"],
                f"fan {identity} {state} measure",
            ) != measures[identity][state]:
                raise ValueError("fan measure differs")
    for field, identity in (
        ("total_tie_points", "total"),
        ("reachable_tie_points", "reachable"),
    ):
        expected = [
            point["scale"]
            for point in points
            if point[f"{identity}_state"] == "tie_unresolved"
        ]
        if fan[field] != expected:
            raise ValueError(f"fan {identity} tie-point inventory differs")
    expected_fan_digest = _canonical_hash(
        {key: value for key, value in fan.items() if key != "fan_sha256"}
    )
    if _digest(fan["fan_sha256"], "fan digest") != expected_fan_digest:
        raise ValueError("fan digest differs")
    return _FanView(
        source_tape=source_tape,
        source_cell_upper=source_upper,
        cells=tuple(cells),
        cell_tapes=tuple(cell_tapes),
        boundaries=boundaries,
        segments=tuple(segments),
        points=tuple(points),
    )


def _verify_window(value: Any, *, source_cell_upper: Fraction) -> float:
    window = _mapping(value, "single-tape window")
    _keys(
        window,
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
        "single-tape window",
    )
    scale = _finite_float(window["scale_limit"], "selector-window scale")
    if scale > 1 or not isinstance(window["scale_limit_hex"], str):
        raise ValueError("selector-window scale differs")
    try:
        decoded = float.fromhex(window["scale_limit_hex"])
    except ValueError as error:
        raise ValueError("selector-window hex scalar differs") from error
    if decoded != scale or Fraction.from_float(scale) > source_cell_upper:
        raise ValueError("selector-window exceeds its exact fan cell")
    ties = _integer(
        window["exact_source_action_ties"], "selector-window exact ties"
    )
    comparisons = _integer(
        window["selector_comparisons"], "selector-window comparisons", minimum=1
    )
    if ties != 0 or comparisons < 1:
        raise ValueError("singleton selector-window accounting differs")
    for key in (
        "first_switch_competing_action",
        "first_switch_information_key",
        "first_switch_source_action",
    ):
        if window[key] is not None and not isinstance(window[key], str):
            raise ValueError("selector-window switch witness differs")
    if scale == 1 and any(
        window[key] is not None
        for key in (
            "first_switch_competing_action",
            "first_switch_information_key",
            "first_switch_source_action",
        )
    ):
        raise ValueError("full selector-window unexpectedly records a switch")
    return scale


def _verify_complete_section(
    record: Any,
    *,
    acting_player: int,
    target_player: int,
) -> _SectionView:
    complete = _mapping(record, "complete section")
    _keys(complete, _COMPLETE_KEYS, "complete section")
    if (
        complete["acting_player"] != acting_player
        or complete["target_player"] != target_player
        or complete["certificate_identity_authority"] != "total_function_only"
        or complete["reachable_identity_role"] != "reporting_only"
        or complete["ray_authority"] != "exact_selector_normal_fan"
        or complete["point_authority"] != "two_pass_factorized_directional_face"
        or complete["epigraph_orientation"]
        != "z_greater_than_or_equal_to_every_row"
        or [
            _exact_fraction(item, "envelope domain")
            for item in _sequence(complete["exact_envelope_domain"], "envelope domain")
        ]
        != [Fraction(0), Fraction(1)]
    ):
        raise ValueError("complete-section authority differs")

    raw = _mapping(complete["raw_section"], "raw section")
    _keys(raw, _RAW_KEYS, "raw section")
    fan = _verify_fan(
        raw["fan"], acting_player=acting_player, target_player=target_player
    )
    if [
        _exact_fraction(value, "crossing scale")
        for value in _sequence(raw["crossing_scales"], "crossing scales")
    ] != list(fan.boundaries[1:-1]):
        raise ValueError("raw crossing-scale inventory differs")

    row_keys = frozenset(
        {
            "intercept",
            "lower",
            "ordinal",
            "response_tape",
            "response_tape_sha256",
            "row_sha256",
            "slope",
            "upper",
        }
    )
    rows: list[Mapping[str, Any]] = []
    rows_by_tape: dict[tuple[tuple[str, str], ...], Mapping[str, Any]] = {}
    for ordinal, item in enumerate(_sequence(raw["cell_gain_rows"], "cell rows")):
        row = _mapping(item, f"cell row {ordinal}")
        _keys(row, row_keys, "cell row")
        if _integer(row["ordinal"], "cell row ordinal") != ordinal:
            raise ValueError("cell-row ordinal differs")
        tape = _verify_tape_with_digest(
            row["response_tape"], row["response_tape_sha256"], "cell row tape"
        )
        if tape in rows_by_tape:
            raise ValueError("cell rows repeat a response tape")
        if _digest(row["row_sha256"], "cell-row digest") != _canonical_hash(
            {key: value for key, value in row.items() if key != "row_sha256"}
        ):
            raise ValueError("cell-row digest differs")
        lower = _exact_fraction(row["lower"], "cell row lower")
        upper = _exact_fraction(row["upper"], "cell row upper")
        cell_index = fan.cell_tapes.index(tape) if tape in fan.cell_tapes else -1
        if cell_index < 0 or (
            lower
            != _exact_fraction(fan.cells[cell_index]["lower"], "fan-cell lower")
            or upper
            != _exact_fraction(fan.cells[cell_index]["upper"], "fan-cell upper")
        ):
            raise ValueError("cell row is detached from its fan cell")
        _exact_fraction(row["intercept"], "cell-row intercept")
        _exact_fraction(row["slope"], "cell-row slope")
        rows.append(row)
        rows_by_tape[tape] = row
    if len(rows) != len(fan.cells):
        raise ValueError("cell-row and fan-cell counts differ")

    expected_specs: list[tuple[Fraction, str]] = []
    for ordinal, boundary in enumerate(fan.boundaries):
        expected_specs.append((boundary, "fan_boundary"))
        if ordinal < len(fan.segments):
            expected_specs.append(
                (
                    _exact_fraction(
                        fan.segments[ordinal]["witness"], "segment witness"
                    ),
                    "open_segment",
                )
            )
    sample_keys = frozenset(
        {
            "active_cell_rows",
            "face",
            "maximum_cell_gain",
            "ordinal",
            "reachable_state",
            "sample_kind",
            "scale",
            "total_state",
        }
    )
    samples: list[Mapping[str, Any]] = []
    face_views: list[_FaceView] = []
    active_rows_by_sample: list[list[int]] = []
    for ordinal, item in enumerate(_sequence(raw["samples"], "raw samples")):
        sample = _mapping(item, f"raw sample {ordinal}")
        _keys(sample, sample_keys, "raw sample")
        if ordinal >= len(expected_specs):
            raise ValueError("raw section has too many samples")
        scale = _exact_fraction(sample["scale"], "sample scale")
        if (
            _integer(sample["ordinal"], "sample ordinal") != ordinal
            or (scale, sample["sample_kind"]) != expected_specs[ordinal]
        ):
            raise ValueError("raw sample schedule differs")
        if sample["sample_kind"] == "fan_boundary":
            fan_row = fan.points[fan.boundaries.index(scale)]
        else:
            fan_row = fan.segments[
                next(
                    index
                    for index, segment in enumerate(fan.segments)
                    if _exact_fraction(segment["witness"], "segment witness") == scale
                )
            ]
        if (
            sample["total_state"] != fan_row["total_state"]
            or sample["reachable_state"] != fan_row["reachable_state"]
        ):
            raise ValueError("raw sample fan state differs")
        face = _verify_face(
            sample["face"],
            acting_player=acting_player,
            target_player=target_player,
            expected_scale=scale,
            label=f"sample face {ordinal}",
        )
        row_values = [
            _exact_fraction(row["intercept"], "row intercept")
            + scale * _exact_fraction(row["slope"], "row slope")
            for row in rows
        ]
        maximum = max(row_values)
        active = [index for index, value in enumerate(row_values) if value == maximum]
        if (
            maximum != _exact_fraction(sample["maximum_cell_gain"], "sample maximum")
            or maximum != face.gain
            or _integer(sample["active_cell_rows"], "sample active rows", minimum=1)
            != len(active)
        ):
            raise ValueError("raw sample maximum-envelope identity differs")
        active_slopes = [
            _exact_fraction(rows[index]["slope"], "active row slope")
            for index in active
        ]
        if scale == 0:
            seam = (
                max(active_slopes) == face.maximum_gain_slope
                and min(active_slopes) >= face.minimum_gain_slope
            )
        elif scale == 1:
            seam = (
                min(active_slopes) == face.minimum_gain_slope
                and max(active_slopes) <= face.maximum_gain_slope
            )
        else:
            seam = (
                min(active_slopes) == face.minimum_gain_slope
                and max(active_slopes) == face.maximum_gain_slope
            )
        if not seam:
            raise ValueError("fan/face slope seam differs")
        if (sample["total_state"] == "tie_unresolved") != (
            face.total_cardinality > 1
        ) or (sample["reachable_state"] == "tie_unresolved") != (
            face.reachable_cardinality > 1
        ):
            raise ValueError("sample tie/cardinality semantics differ")
        samples.append(sample)
        face_views.append(face)
        active_rows_by_sample.append(active)
    if len(samples) != len(expected_specs):
        raise ValueError("raw samples do not cover the complete fan")

    if _digest(raw["section_sha256"], "raw-section digest") != _canonical_hash(
        {key: value for key, value in raw.items() if key != "section_sha256"}
    ):
        raise ValueError("raw-section digest differs")
    source_ordinals = [
        index
        for index, sample in enumerate(samples)
        if sample["sample_kind"] == "fan_boundary"
        and _exact_fraction(sample["scale"], "source sample scale") == 0
    ]
    if source_ordinals != [0] or complete["source_face"] != samples[0]["face"]:
        raise ValueError("complete section has no unique identical source face")
    source_face = _verify_face(
        complete["source_face"],
        acting_player=acting_player,
        target_player=target_player,
        expected_scale=Fraction(0),
        label="complete source face",
    )

    epigraph = _sequence(
        complete["epigraph_residual_matrix"], "epigraph residual matrix"
    )
    if len(epigraph) != len(samples):
        raise ValueError("epigraph matrix sample count differs")
    epigraph_sample_keys = frozenset(
        {"active_rows", "envelope_value", "rows", "sample_ordinal", "scale"}
    )
    epigraph_row_keys = frozenset(
        {
            "active",
            "residual",
            "response_tape_sha256",
            "row_ordinal",
            "row_value",
        }
    )
    for sample_ordinal, item in enumerate(epigraph):
        sample_record = _mapping(item, f"epigraph sample {sample_ordinal}")
        _keys(sample_record, epigraph_sample_keys, "epigraph sample")
        scale = _exact_fraction(sample_record["scale"], "epigraph scale")
        envelope = _exact_fraction(sample_record["envelope_value"], "epigraph envelope")
        if (
            _integer(sample_record["sample_ordinal"], "epigraph sample ordinal")
            != sample_ordinal
            or scale
            != _exact_fraction(samples[sample_ordinal]["scale"], "raw sample scale")
            or envelope != face_views[sample_ordinal].gain
        ):
            raise ValueError("epigraph sample identity differs")
        residual_rows = _sequence(sample_record["rows"], "epigraph rows")
        if len(residual_rows) != len(rows):
            raise ValueError("epigraph row count differs")
        active_count = 0
        for row_ordinal, residual_item in enumerate(residual_rows):
            residual_row = _mapping(residual_item, "epigraph row")
            _keys(residual_row, epigraph_row_keys, "epigraph row")
            if _integer(residual_row["row_ordinal"], "epigraph row ordinal") != row_ordinal:
                raise ValueError("epigraph row ordinal differs")
            row_value = _exact_fraction(residual_row["row_value"], "epigraph row value")
            expected_value = _exact_fraction(rows[row_ordinal]["intercept"], "intercept") + (
                scale * _exact_fraction(rows[row_ordinal]["slope"], "slope")
            )
            residual = _exact_fraction(residual_row["residual"], "epigraph residual")
            expected_residual = envelope - expected_value
            active = residual_row["active"]
            if (
                not isinstance(active, bool)
                or row_value != expected_value
                or residual != expected_residual
                or residual < 0
                or active != (residual == 0)
                or residual_row["response_tape_sha256"]
                != rows[row_ordinal]["response_tape_sha256"]
            ):
                raise ValueError("epigraph residual orientation differs")
            active_count += int(active)
        if (
            active_count != _integer(sample_record["active_rows"], "active rows")
            or active_count != len(active_rows_by_sample[sample_ordinal])
        ):
            raise ValueError("epigraph active-row count differs")

    pieces = _sequence(complete["pieces"], "compact pieces")
    if len(pieces) != len(fan.segments) or not pieces:
        raise ValueError("compact-piece count differs from fan segments")
    piece_keys = frozenset(
        {
            "intercept",
            "lower",
            "ordinal",
            "reachable_state",
            "reachable_support_cardinality",
            "response_tape",
            "response_tape_sha256",
            "slope",
            "total_function_cardinality",
            "total_state",
            "upper",
            "witness",
        }
    )
    previous_value: tuple[Fraction, Fraction, Fraction] | None = None
    for ordinal, (item, segment) in enumerate(zip(pieces, fan.segments, strict=True)):
        piece = _mapping(item, f"piece {ordinal}")
        _keys(piece, piece_keys, "piece")
        lower = _exact_fraction(piece["lower"], "piece lower")
        upper = _exact_fraction(piece["upper"], "piece upper")
        witness = _exact_fraction(piece["witness"], "piece witness")
        tape = _verify_tape_with_digest(
            piece["response_tape"], piece["response_tape_sha256"], "piece tape"
        )
        if (
            _integer(piece["ordinal"], "piece ordinal") != ordinal
            or lower != _exact_fraction(segment["lower"], "segment lower")
            or upper != _exact_fraction(segment["upper"], "segment upper")
            or witness != _exact_fraction(segment["witness"], "segment witness")
            or tape != _tape(segment["response_tape"], "segment response tape")
            or piece["total_state"] != segment["total_state"]
            or piece["reachable_state"] != segment["reachable_state"]
        ):
            raise ValueError("compact piece differs from its fan segment")
        sample_ordinal = expected_specs.index((witness, "open_segment"))
        face = face_views[sample_ordinal]
        row = rows_by_tape[tape]
        intercept = _exact_fraction(piece["intercept"], "piece intercept")
        slope = _exact_fraction(piece["slope"], "piece slope")
        if (
            intercept != _exact_fraction(row["intercept"], "row intercept")
            or slope != _exact_fraction(row["slope"], "row slope")
            or face.minimum_gain_slope != face.maximum_gain_slope
            or slope != face.minimum_gain_slope
            or _integer(
                piece["total_function_cardinality"], "piece total cardinality", minimum=1
            )
            != face.total_cardinality
            or _integer(
                piece["reachable_support_cardinality"],
                "piece reachable cardinality",
                minimum=1,
            )
            != face.reachable_cardinality
        ):
            raise ValueError("compact piece authority differs")
        if previous_value is not None:
            previous_intercept, previous_slope, previous_upper = previous_value
            if (
                previous_upper != lower
                or previous_intercept + lower * previous_slope
                != intercept + lower * slope
                or previous_slope > slope
            ):
                raise ValueError("compact envelope is discontinuous or nonconvex")
        previous_value = (intercept, slope, upper)
    if _exact_fraction(pieces[0]["lower"], "first piece lower") != 0 or _exact_fraction(
        pieces[-1]["upper"], "last piece upper"
    ) != 1:
        raise ValueError("compact pieces do not cover [0, 1]")

    work = _mapping(complete["work"], "integration work")
    _keys(work, _INTEGRATION_WORK_KEYS, "integration work")
    work_values = {
        key: _integer(value, f"integration work {key}") for key, value in work.items()
    }
    expected_evaluations = len(rows) * len(samples)
    if (
        work_values["fan_cell_rows"] != len(rows)
        or work_values["fan_segments"] != len(fan.segments)
        or work_values["fan_boundaries"] != len(fan.points)
        or work_values["point_face_observations"] != len(samples)
        or work_values["envelope_row_evaluations"] != expected_evaluations
        or work_values["epigraph_residual_evaluations"] != expected_evaluations
        or work_values["materialized_response_tapes"] != 0
        or any(view.materialized_tapes != 0 for view in face_views)
    ):
        raise ValueError("integration work identity differs")

    mode = complete["mode"]
    window_scale: float | None = None
    if source_face.total_cardinality > 1:
        if (
            mode != "factorized_tie_aware_maximum_envelope"
            or complete["single_tape_window"] is not None
            or work_values["selector_window_v2_calls"] != 0
            or work_values["float_selector_score_calls"] != 0
            or samples[0]["total_state"] != "tie_unresolved"
        ):
            raise ValueError("factorized source-tie dispatch differs")
    elif source_face.total_cardinality == 1:
        window_scale = _verify_window(
            complete["single_tape_window"], source_cell_upper=fan.source_cell_upper
        )
        expected_mode = "v2_single_tape" if window_scale > 0 else "fail_closed_single_tape"
        if (
            mode != expected_mode
            or work_values["selector_window_v2_calls"] != 1
            or work_values["float_selector_score_calls"] != 2
            or samples[0]["total_state"] != "fixed"
            or source_face.minimum_tape != source_face.maximum_tape
            or source_face.minimum_tape != fan.source_tape
        ):
            raise ValueError("singleton source dispatch differs")
    else:
        raise ValueError("source cardinality is invalid")

    expected_complete_digest = _canonical_hash(
        {key: value for key, value in complete.items() if key != "complete_section_sha256"}
    )
    if _digest(
        complete["complete_section_sha256"], "complete-section digest"
    ) != expected_complete_digest:
        raise ValueError("complete-section digest differs")
    return _SectionView(
        mode=str(mode),
        pieces=len(pieces),
        source_total_cardinality=source_face.total_cardinality,
        source_reachable_cardinality=source_face.reachable_cardinality,
        window_scale=window_scale,
        materialized_tapes=work_values["materialized_response_tapes"],
    )


def _float_hex(value: Any, label: str) -> float:
    if not isinstance(value, str):
        raise ValueError(f"{label} is not a hexadecimal float string")
    try:
        result = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not a hexadecimal float string") from error
    if not isfinite(result):
        raise ValueError(f"{label} is not finite")
    return result


def _signature(value: Any, label: str) -> tuple[tuple[str, str], ...]:
    return _tape(value, label)


def _row_growth_semantic_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload.pop("row_growth_semantic_sha256", None)
    semantic_iterations = []
    for item in _sequence(payload.get("iterations"), "row-growth iterations"):
        iteration = dict(_mapping(item, "row-growth iteration"))
        for key in (
            "cut_extraction_seconds",
            "exact_oracle_seconds",
            "master_solve_seconds",
        ):
            iteration.pop(key, None)
        semantic_iterations.append(iteration)
    payload["iterations"] = semantic_iterations
    return payload


def _verify_row_growth(
    value: Any,
    *,
    context_id: str,
    source_policy_sha256: str,
    endpoint_policy_sha256: str,
) -> None:
    record = _mapping(value, "row-growth record")
    expected_keys = frozenset(
        {
            "acting_player",
            "baseline_nash_conv",
            "cap_identity_error",
            "caps_exact",
            "context_id",
            "endpoint_evaluation_ordinal",
            "endpoint_policy_sha256",
            "evaluations",
            "exact_duplicate_response_hits",
            "final_exact_nash_conv",
            "gates",
            "guard",
            "iterations",
            "max_iterations",
            "maximum_float_exact_evaluation_error",
            "maximum_float_exact_row_error",
            "maximum_master_constraint_violation",
            "maximum_master_duality_gap",
            "oracle_accounting",
            "passed",
            "response_rows",
            "response_rows_by_player",
            "row_growth_semantic_sha256",
            "source_policy_sha256",
            "tolerance",
        }
    )
    _keys(record, expected_keys, "row-growth record")
    if (
        record["acting_player"] != 0
        or record["context_id"] != context_id
        or _digest(record["source_policy_sha256"], "row-growth source policy")
        != source_policy_sha256
        or _digest(record["endpoint_policy_sha256"], "row-growth endpoint policy")
        != endpoint_policy_sha256
        or _finite_float(record["guard"], "row-growth guard") != 0.25
        or _integer(record["max_iterations"], "row-growth max iterations", minimum=1)
        != 128
        or _finite_float(record["tolerance"], "row-growth tolerance") != 1e-10
    ):
        raise ValueError("row-growth frozen identity differs")

    evaluation_keys = frozenset(
        {
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
    )
    evaluations = _sequence(record["evaluations"], "row-growth evaluations")
    if len(evaluations) < 2:
        raise ValueError("row-growth evaluation inventory is incomplete")
    evaluation_gains: list[tuple[Fraction, ...]] = []
    evaluation_errors: list[float] = []
    policy_index: dict[str, int] = {}
    for ordinal, item in enumerate(evaluations):
        evaluation = _mapping(item, f"row-growth evaluation {ordinal}")
        _keys(evaluation, evaluation_keys, "row-growth evaluation")
        if _integer(evaluation["ordinal"], "evaluation ordinal") != ordinal:
            raise ValueError("row-growth evaluation ordinal differs")
        policy = _digest(evaluation["policy_sha256"], "evaluation policy")
        if policy in policy_index:
            raise ValueError("row-growth evaluations repeat a policy")
        policy_index[policy] = ordinal
        utilities = tuple(
            _exact_fraction(row, "evaluation utility")
            for row in _sequence(evaluation["utilities_exact"], "evaluation utilities")
        )
        responses = tuple(
            _exact_fraction(row, "evaluation response")
            for row in _sequence(
                evaluation["best_response_values_exact"], "evaluation responses"
            )
        )
        gains = tuple(
            _exact_fraction(row, "evaluation gain")
            for row in _sequence(evaluation["deviation_gains_exact"], "evaluation gains")
        )
        if (
            len(utilities) != len(responses) != 0
            or len(utilities) != len(gains)
            or len(utilities) != 2
            or sum(utilities, Fraction(0)) != 0
            or gains != tuple(
                response - utility
                for response, utility in zip(responses, utilities, strict=True)
            )
            or _exact_fraction(evaluation["nash_conv_exact"], "evaluation NashConv")
            != sum(gains, Fraction(0))
            or evaluation["exact_gains_nonnegative"]
            is not all(gain >= 0 for gain in gains)
        ):
            raise ValueError("row-growth evaluation algebra differs")
        signatures = _sequence(
            evaluation["response_signatures"], "evaluation response signatures"
        )
        signature_digests = _sequence(
            evaluation["response_signature_sha256s"],
            "evaluation response signature digests",
        )
        if len(signatures) != 2 or len(signature_digests) != 2:
            raise ValueError("row-growth response signature inventory differs")
        for player, (signature, digest) in enumerate(
            zip(signatures, signature_digests, strict=True)
        ):
            _signature(signature, f"evaluation {ordinal} player {player} signature")
            if _digest(digest, "evaluation signature digest") != _canonical_hash(
                signature
            ):
                raise ValueError("row-growth response signature digest differs")
        evaluation_errors.append(
            _finite_float(
                evaluation["maximum_float_exact_error"], "evaluation float error"
            )
        )
        evaluation_gains.append(gains)
    if evaluations[0]["policy_sha256"] != source_policy_sha256:
        raise ValueError("row-growth first evaluation is not the source")
    if _finite_float(record["baseline_nash_conv"], "baseline NashConv") != float(
        sum(evaluation_gains[0], Fraction(0))
    ):
        raise ValueError("row-growth baseline NashConv differs")

    endpoint_ordinal = _integer(
        record["endpoint_evaluation_ordinal"], "endpoint evaluation ordinal"
    )
    if (
        endpoint_ordinal >= len(evaluations)
        or evaluations[endpoint_ordinal]["policy_sha256"] != endpoint_policy_sha256
        or _exact_fraction(record["final_exact_nash_conv"], "final exact NashConv")
        != sum(evaluation_gains[endpoint_ordinal], Fraction(0))
    ):
        raise ValueError("row-growth endpoint evaluation identity differs")

    guard = Fraction.from_float(float(record["guard"]))
    caps = tuple(
        _exact_fraction(row, "row-growth cap")
        for row in _sequence(record["caps_exact"], "row-growth caps")
    )
    expected_caps = tuple(gain + guard for gain in evaluation_gains[0])
    if caps != expected_caps or _finite_float(
        record["cap_identity_error"], "cap identity error"
    ) != 0:
        raise ValueError("row-growth cap identity differs")

    response_row_keys = frozenset(
        {
            "after_iteration",
            "coefficients",
            "constant_exact",
            "constant_subject_hex",
            "exact_float_identity",
            "exact_row_sha256",
            "maximum_absolute_error",
            "ordinal",
            "phase",
            "signature",
            "signature_sha256",
            "target_player",
        }
    )
    coefficient_keys = frozenset(
        {"absolute_error", "action", "exact", "information_key", "subject_hex"}
    )
    response_rows = _sequence(record["response_rows"], "row-growth response rows")
    seen_responses: set[tuple[int, tuple[tuple[str, str], ...]]] = set()
    rows_by_player = [0, 0]
    row_errors: list[float] = []
    variable_axis: tuple[tuple[str, str], ...] | None = None
    for ordinal, item in enumerate(response_rows):
        row = _mapping(item, f"response row {ordinal}")
        _keys(row, response_row_keys, "response row")
        player = _integer(row["target_player"], "response-row target player")
        if player not in (0, 1) or _integer(row["ordinal"], "response-row ordinal") != ordinal:
            raise ValueError("response-row identity differs")
        if row["phase"] == "initial":
            if row["after_iteration"] is not None:
                raise ValueError("initial response row has an iteration")
        elif row["phase"] == "generated":
            _integer(
                row["after_iteration"], "generated response-row iteration", minimum=1
            )
        else:
            raise ValueError("response-row phase differs")
        signature = _signature(row["signature"], "response-row signature")
        if _digest(row["signature_sha256"], "response-row signature digest") != (
            _canonical_hash(row["signature"])
        ):
            raise ValueError("response-row signature digest differs")
        response_key = (player, signature)
        if response_key in seen_responses:
            raise ValueError("row-growth response rows repeat exactly")
        seen_responses.add(response_key)
        rows_by_player[player] += 1
        constant = _exact_fraction(row["constant_exact"], "response-row constant")
        constant_subject = _float_hex(
            row["constant_subject_hex"], "response-row subject constant"
        )
        coefficients = _sequence(row["coefficients"], "response-row coefficients")
        exact_coefficients = []
        variables = []
        errors = [abs(constant_subject - float(constant))]
        exact_float_identity = Fraction.from_float(constant_subject) == constant
        for coefficient in coefficients:
            item_record = _mapping(coefficient, "response-row coefficient")
            _keys(item_record, coefficient_keys, "response-row coefficient")
            key = item_record["information_key"]
            action = item_record["action"]
            if not isinstance(key, str) or not key or not isinstance(action, str):
                raise ValueError("response-row coefficient axis differs")
            exact = _exact_fraction(item_record["exact"], "response-row exact coefficient")
            subject = _float_hex(item_record["subject_hex"], "response-row subject coefficient")
            error = _finite_float(item_record["absolute_error"], "coefficient error")
            if error != abs(subject - float(exact)):
                raise ValueError("response-row coefficient error differs")
            exact_float_identity &= Fraction.from_float(subject) == exact
            errors.append(error)
            variables.append((key, action))
            exact_coefficients.append(
                {"action": action, "information_key": key, "value": item_record["exact"]}
            )
        axis = tuple(variables)
        if len(set(axis)) != len(axis) or (variable_axis is not None and axis != variable_axis):
            raise ValueError("response-row exact axis differs")
        variable_axis = axis
        if (
            row["exact_float_identity"] is not exact_float_identity
            or exact_float_identity is not True
            or _finite_float(row["maximum_absolute_error"], "response-row maximum error")
            != max(errors, default=0.0)
            or _digest(row["exact_row_sha256"], "exact response-row digest")
            != _canonical_hash(
                {"coefficients": exact_coefficients, "constant": row["constant_exact"]}
            )
        ):
            raise ValueError("response-row exact rebound differs")
        row_errors.append(max(errors, default=0.0))
    if (
        _integer(record["exact_duplicate_response_hits"], "duplicate response hits")
        != 0
        or _sequence(record["response_rows_by_player"], "response rows by player")
        != rows_by_player
        or _finite_float(record["maximum_float_exact_row_error"], "maximum row error")
        != max(row_errors, default=0.0)
    ):
        raise ValueError("row-growth response-row aggregate differs")

    iteration_keys = frozenset(
        {
            "added_targets",
            "candidate_feasible",
            "candidate_nash_conv",
            "converged",
            "cut_extraction_seconds",
            "epigraph_hex",
            "exact_candidate_feasible",
            "exact_converged",
            "exact_oracle_seconds",
            "incumbent_updated",
            "incumbent_upper_bound",
            "iteration",
            "master",
            "master_lower_bound",
            "master_solve_seconds",
            "maximum_cap_violation",
            "maximum_epigraph_violation",
            "maximum_exact_cap_violation",
            "maximum_exact_epigraph_violation",
            "optimality_gap",
            "realization_equivalence_max_error",
            "response_rows_added",
            "response_rows_before",
        }
    )
    master_keys = frozenset(
        {
            "dual_objective_hex",
            "duality_gap",
            "maximum_constraint_violation",
            "objective_hex",
            "pivots",
        }
    )
    iterations = _sequence(record["iterations"], "row-growth iterations")
    if len(iterations) != len(evaluations) - 1 or not iterations:
        raise ValueError("row-growth iteration/evaluation inventory differs")
    threshold = Fraction.from_float(100.0 * float(record["tolerance"]))
    duality_gaps = []
    constraint_violations = []
    for index, item in enumerate(iterations):
        iteration = _mapping(item, f"row-growth iteration {index}")
        _keys(iteration, iteration_keys, "row-growth iteration")
        if _integer(iteration["iteration"], "iteration number", minimum=1) != index + 1:
            raise ValueError("row-growth iteration number differs")
        for timing in (
            "cut_extraction_seconds",
            "exact_oracle_seconds",
            "master_solve_seconds",
        ):
            _finite_float(iteration[timing], f"row-growth {timing}")
        gains = evaluation_gains[index + 1]
        cap_violations = tuple(
            gain - cap for gain, cap in zip(gains, caps, strict=True)
        )
        epigraph = tuple(
            _float_hex(row, "row-growth epigraph")
            for row in _sequence(iteration["epigraph_hex"], "row-growth epigraph")
        )
        if len(epigraph) != len(gains):
            raise ValueError("row-growth epigraph width differs")
        epigraph_violations = tuple(
            gain - Fraction.from_float(bound)
            for gain, bound in zip(gains, epigraph, strict=True)
        )
        exact_feasible = max(cap_violations, default=Fraction(0)) <= threshold
        exact_converged = max(epigraph_violations, default=Fraction(0)) <= threshold
        if (
            _exact_fraction(
                iteration["maximum_exact_cap_violation"], "exact cap violation"
            )
            != max(cap_violations, default=Fraction(0))
            or _exact_fraction(
                iteration["maximum_exact_epigraph_violation"],
                "exact epigraph violation",
            )
            != max(epigraph_violations, default=Fraction(0))
            or iteration["exact_candidate_feasible"] is not exact_feasible
            or iteration["exact_converged"] is not exact_converged
            or iteration["candidate_feasible"] is not exact_feasible
            or iteration["converged"] is not exact_converged
        ):
            raise ValueError("row-growth exact iteration classification differs")
        master = _mapping(iteration["master"], "row-growth master")
        _keys(master, master_keys, "row-growth master")
        _float_hex(master["objective_hex"], "master objective")
        _float_hex(master["dual_objective_hex"], "master dual objective")
        gap = _finite_float(master["duality_gap"], "master duality gap")
        violation = _finite_float(
            master["maximum_constraint_violation"], "master constraint violation"
        )
        _integer(master["pivots"], "master pivots")
        if gap > 1e-8 or violation > 1e-8:
            raise ValueError("row-growth master numerical gate differs")
        duality_gaps.append(gap)
        constraint_violations.append(violation)
    if (
        _finite_float(
            record["maximum_float_exact_evaluation_error"], "maximum evaluation error"
        )
        != max(evaluation_errors, default=0.0)
        or _finite_float(record["maximum_master_duality_gap"], "maximum duality gap")
        != max(duality_gaps)
        or _finite_float(
            record["maximum_master_constraint_violation"],
            "maximum master constraint violation",
        )
        != max(constraint_violations)
    ):
        raise ValueError("row-growth numerical aggregate differs")

    accounting = _mapping(record["oracle_accounting"], "row-growth accounting")
    _keys(
        accounting,
        frozenset(
            {
                "best_response_calls",
                "evaluation_calls",
                "expected_utilities_calls",
                "master_calls",
                "open_axis_coefficient_calls",
                "response_row_calls",
            }
        ),
        "row-growth accounting",
    )
    counts = {key: _integer(value, f"row-growth accounting {key}") for key, value in accounting.items()}
    if (
        counts["evaluation_calls"] != len(evaluations)
        or counts["master_calls"] != len(iterations)
        or counts["response_row_calls"] != len(response_rows)
        or counts["best_response_calls"] != 2 * len(evaluations) + 1
        or counts["open_axis_coefficient_calls"] != len(response_rows) + 1
    ):
        raise ValueError("row-growth oracle accounting differs")

    gates = _mapping(record["gates"], "row-growth gates")
    expected_gate_keys = frozenset(
        {
            "all_response_rows_exactly_rebound",
            "candidate_feasible",
            "converged",
            "exact_candidate_feasible",
            "exact_cap_identity",
            "exact_converged",
            "exact_duplicate_response_free",
            "exact_float_classifications",
            "maximum_master_constraint_violation_at_most_1e-8",
            "maximum_master_duality_gap_at_most_1e-8",
            "nontrivial_endpoint",
        }
    )
    _keys(gates, expected_gate_keys, "row-growth gates")
    if any(value is not True for value in gates.values()) or record["passed"] is not True:
        raise ValueError("row-growth exact acceptance differs")
    if endpoint_policy_sha256 == source_policy_sha256:
        raise ValueError("row-growth endpoint is trivial")
    if _digest(
        record["row_growth_semantic_sha256"], "row-growth semantic digest"
    ) != _canonical_hash(_row_growth_semantic_payload(record)):
        raise ValueError("row-growth semantic digest differs")


_TARGET_OUTCOME_KEYS = frozenset(
    {
        "active_cell_rows",
        "complete_section_sha256",
        "direction_generation_seconds",
        "endpoint_policy_sha256",
        "exact_source_ties",
        "fan_cells",
        "fan_points",
        "fan_segments",
        "maximum_reachable_support_cardinality",
        "maximum_total_function_cardinality",
        "mode",
        "mode_counts",
        "piece_counts",
        "row_growth_semantic_sha256",
        "section_subject_seconds",
        "selector_window_scale_limits",
        "source_face_cardinality",
        "subject_seconds",
    }
)


def _contains_outcome_key(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _TARGET_OUTCOME_KEYS or _contains_outcome_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_outcome_key(item) for item in value)
    return False


def _finite_tree(value: object) -> bool:
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_tree(item) for item in value)
    return True


def _verify_config() -> Mapping[str, Any]:
    path = _ROOT / ADR0362_CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != ADR0362_CONFIG_SHA256:
        raise ValueError("ADR-0362 config bytes differ")
    config = _load_json(raw)
    required = {
        "schema_version",
        "evidence_stage",
        "hash_semantics",
        "expected_parent_protocol_sha256",
        "expected_population_sha256",
        "expected_population_canonical_bytes",
        "expected_context_sha256s",
        "expected_policy_sha256s",
        "expected_game_provenance_sha256s",
        "expected_public_state_sha256",
        *_SOURCE_PATHS,
        "acting_player",
        "target_players",
        "direction_classes_in_order",
        "direction_regret_public_histories_in_order",
        "row_growth_guard",
        "row_growth_max_iterations",
        "row_growth_tolerance",
        "selector_margin_allowance",
        "maximum_tree_nodes",
        "maximum_fan_pieces",
        "ray_authority",
        "point_authority",
        "identity_authority",
        "reachable_identity_role",
        "epigraph_orientation",
        "direction_generation_stage",
        "section_subject_wall_semantics",
        "subject_wall_semantics",
        "campaign_wall_semantics",
        "result_path_lifecycle",
        "failure_interpretation",
        "claims_policy",
        "gates",
    }
    if set(config) != required:
        raise ValueError("ADR-0362 config schema differs")
    for field, relative in _SOURCE_PATHS.items():
        # The prospective owner control is intentionally successor-edited
        # after the one-shot path became present. Its invocation identity
        # remains sealed in the immutable config and source commit; it is not
        # a scientific/runtime dependency of the retained payload.
        if field == "expected_control_test_sha256":
            continue
        if config[field] != _canonical_lf_sha256(_ROOT / relative):
            raise ValueError(f"ADR-0362 source provenance differs: {field}")
    if (
        config["schema_version"]
        != "legal-h4-factorized-affine-confirmation-config-v1"
        or config["evidence_stage"]
        != "preregistered_after_adr0360_before_any_fresh_confirmation_target_call"
        or config["hash_semantics"]
        != "canonical_lf_sha256_for_all_bound_text_sources"
        or config["expected_parent_protocol_sha256"]
        != ADR0362_PARENT_PROTOCOL_SHA256
        or config["acting_player"] != 0
        or config["target_players"] != [0, 1]
        or tuple(config["direction_classes_in_order"]) != _DIRECTION_CLASSES
        or tuple(config["direction_regret_public_histories_in_order"])
        != _REGRET_HISTORIES
        or config["row_growth_guard"] != 0.25
        or config["row_growth_max_iterations"] != 128
        or config["row_growth_tolerance"] != 1e-10
        or config["selector_margin_allowance"] != 1e-12
        or config["maximum_tree_nodes"] != 100_000
        or config["maximum_fan_pieces"] != 256
        or config["ray_authority"] != "exact_selector_normal_fan"
        or config["point_authority"] != "two_pass_factorized_directional_face"
        or config["identity_authority"] != "total_function_only"
        or config["reachable_identity_role"] != "reporting_only"
        or config["epigraph_orientation"]
        != "z_greater_than_or_equal_to_every_row"
        or config["expected_control_test_sha256"]
        != "38913f8cd1aeb541dc52facb7ea587287ae967cb4d5d22f1bf58edda069ff220"
    ):
        raise ValueError("ADR-0362 frozen config semantics differ")
    gates = _mapping(config["gates"], "confirmation config gates")
    expected_gates = {
        "expected_contexts": 4,
        "expected_directions_per_context": 4,
        "expected_regret_directions_per_context": 3,
        "expected_row_growth_directions_per_context": 1,
        "expected_targets_per_direction": 2,
        "expected_sections": 32,
        "maximum_section_subject_seconds": 60.0,
        "maximum_subject_seconds": 360.0,
        "maximum_campaign_seconds": 600.0,
        "maximum_result_bytes": 8_388_608,
        "require_clean_git_state": True,
        "require_population_identity": True,
        "require_context_identity": True,
        "require_direction_inventory": True,
        "require_row_growth_exact_acceptance": True,
        "require_complete_section_evidence": True,
        "require_typed_dispatch": True,
        "require_exact_authorities": True,
        "require_dual_cardinality_semantics": True,
        "require_zero_materialized_tapes": True,
        "require_all_or_nothing_coordinates": True,
        "require_no_target_outcome_gate": True,
        "require_zero_actions_and_quality_rows": True,
        "require_finite": True,
    }
    if gates != expected_gates or _contains_outcome_key(config):
        raise ValueError("ADR-0362 config gates or outcome barrier differ")
    return MappingProxyType(config)


def _verify_record(
    record: Mapping[str, Any],
    config: Mapping[str, Any],
) -> Mapping[str, bool]:
    _keys(record, _TOP_KEYS, "confirmation result")
    if (
        record["schema_version"]
        != "legal-h4-factorized-affine-confirmation-result-v1"
        or record["status"] != "legal_h4_factorized_affine_confirmation_executed"
        or record["config_sha256"] != ADR0362_CONFIG_SHA256
        or record["implementation_sha256"] != ADR0362_RUNNER_SHA256
        or record["parent_protocol_sha256"] != ADR0362_PARENT_PROTOCOL_SHA256
    ):
        raise ValueError("confirmation result provenance differs")
    environment = _mapping(record["environment"], "confirmation environment")
    _keys(environment, frozenset({"git", "platform", "python", "runtime"}), "environment")
    git = _mapping(environment["git"], "confirmation Git environment")
    if git != {
        "commit": ADR0362_INVOCATION_SOURCE_COMMIT,
        "dirty": False,
        "strict_status": True,
    }:
        raise ValueError("confirmation invocation Git identity differs")
    runtime = _mapping(environment["runtime"], "confirmation runtime")
    if runtime != {"backend": "cpu_fraction_exact_fan_factorized_face"}:
        raise ValueError("confirmation runtime identity differs")
    if not isinstance(environment["platform"], str) or not isinstance(
        environment["python"], str
    ):
        raise ValueError("confirmation environment strings differ")

    population = _mapping(record["population"], "confirmation population")
    _keys(
        population,
        frozenset(
            {"canonical_bytes", "context_sha256s", "population_sha256", "protocol_sha256"}
        ),
        "confirmation population",
    )
    if (
        population["canonical_bytes"] != config["expected_population_canonical_bytes"]
        or population["context_sha256s"] != config["expected_context_sha256s"]
        or population["population_sha256"] != config["expected_population_sha256"]
        or population["protocol_sha256"] != config["expected_parent_protocol_sha256"]
    ):
        raise ValueError("confirmation population identity differs")

    methodology = _mapping(record["methodology"], "confirmation methodology")
    expected_methodology = {
        "campaign_wall_semantics": config["campaign_wall_semantics"],
        "claims_policy": config["claims_policy"],
        "contexts": 4,
        "direction_generation_stage": config["direction_generation_stage"],
        "directions_per_context": 4,
        "failure_interpretation": config["failure_interpretation"],
        "result_path_lifecycle": config["result_path_lifecycle"],
        "section_subject_wall_semantics": config["section_subject_wall_semantics"],
        "sections": 32,
        "subject_wall_semantics": config["subject_wall_semantics"],
        "targets_per_direction": 2,
    }
    if methodology != expected_methodology or tuple(record["limitations"]) != _LIMITATIONS:
        raise ValueError("confirmation claims boundary differs")

    contexts = _sequence(record["contexts"], "confirmation contexts")
    if len(contexts) != 4:
        raise ValueError("confirmation context count differs")
    coordinates: list[tuple[str, str, int]] = []
    section_times: list[float] = []
    modes: dict[str, int] = {}
    piece_counts: list[int] = []
    window_scales: list[float] = []
    maximum_total = 0
    maximum_reachable = 0
    for context_ordinal, item in enumerate(contexts):
        context = _mapping(item, f"confirmation context {context_ordinal}")
        _keys(context, _CONTEXT_KEYS, "confirmation context")
        context_id = _EXPECTED_CONTEXT_IDS[context_ordinal]
        source_policy = config["expected_policy_sha256s"][context_ordinal]
        if (
            context["candidate_ordinal"] != context_ordinal
            or context["context_id"] != context_id
            or context["semantic_sha256"]
            != config["expected_context_sha256s"][context_ordinal]
            or context["source_policy_sha256"] != source_policy
            or context["game_provenance_sha256"]
            != config["expected_game_provenance_sha256s"][context_ordinal]
            or context["public_state_sha256"] != config["expected_public_state_sha256"]
        ):
            raise ValueError("confirmation context identity differs")
        _digest(context["game_structural_sha256"], "context structural digest")
        _finite_float(
            context["direction_generation_seconds"], "direction-generation seconds"
        )
        directions = _sequence(context["directions"], "confirmation directions")
        if len(directions) != 4:
            raise ValueError("confirmation direction count differs")
        endpoint_digests = []
        for direction_ordinal, direction_item in enumerate(directions):
            direction = _mapping(direction_item, "confirmation direction")
            _keys(direction, _DIRECTION_KEYS, "confirmation direction")
            if (
                direction["context_id"] != context_id
                or direction["direction_class"] != _DIRECTION_CLASSES[direction_ordinal]
            ):
                raise ValueError("confirmation direction identity differs")
            endpoint = _digest(
                direction["endpoint_policy_sha256"], "direction endpoint policy"
            )
            endpoint_digests.append(endpoint)
            histories = _sequence(
                direction["changed_public_histories"], "changed public histories"
            )
            if direction_ordinal < 3:
                expected_history = _REGRET_HISTORIES[direction_ordinal]
                if (
                    direction["label"] != f"regret_vertex::{expected_history}"
                    or histories != [expected_history]
                ):
                    raise ValueError("confirmation regret direction differs")
            elif (
                direction["label"] != f"row_growth_proposal::{context_id}"
                or not histories
                or histories != sorted(set(histories))
                or any(not isinstance(history, str) or not history for history in histories)
            ):
                raise ValueError("confirmation row-growth direction descriptor differs")
            targets = _sequence(direction["targets"], "confirmation targets")
            if len(targets) != 2:
                raise ValueError("confirmation target count differs")
            for target_ordinal, target_item in enumerate(targets):
                target = _mapping(target_item, "confirmation target")
                _keys(target, _TARGET_KEYS, "confirmation target")
                if (
                    target["context_id"] != context_id
                    or target["direction_label"] != direction["label"]
                    or target["target_player"] != target_ordinal
                    or target["section_passed"] is not True
                    or target["typed_dispatch"] is not True
                    or target["exact_authorities"] is not True
                ):
                    raise ValueError("confirmation target identity differs")
                checks = _mapping(
                    target["complete_evidence_checks"], "complete evidence checks"
                )
                _keys(checks, _SECTION_CHECK_KEYS, "complete evidence checks")
                if any(value is not True for value in checks.values()):
                    raise ValueError("recorded complete-evidence check differs")
                section = _verify_complete_section(
                    target["complete_evidence"],
                    acting_player=0,
                    target_player=target_ordinal,
                )
                seconds = _finite_float(
                    target["section_subject_seconds"], "section subject seconds"
                )
                if seconds > config["gates"]["maximum_section_subject_seconds"]:
                    raise ValueError("confirmation section subject wall failed")
                coordinates.append((context_id, str(direction["label"]), target_ordinal))
                section_times.append(seconds)
                modes[section.mode] = modes.get(section.mode, 0) + 1
                piece_counts.append(section.pieces)
                maximum_total = max(maximum_total, section.source_total_cardinality)
                maximum_reachable = max(
                    maximum_reachable, section.source_reachable_cardinality
                )
                if section.window_scale is not None:
                    window_scales.append(section.window_scale)
        if len(set(endpoint_digests)) != 4:
            raise ValueError("confirmation direction endpoints are not unique")
        _verify_row_growth(
            context["row_growth"],
            context_id=context_id,
            source_policy_sha256=source_policy,
            endpoint_policy_sha256=endpoint_digests[-1],
        )

    if len(coordinates) != 32 or len(set(coordinates)) != 32:
        raise ValueError("confirmation coordinate inventory differs")
    if _digest(
        record["section_coordinates_sha256"], "section-coordinate digest"
    ) != _canonical_hash(coordinates) or record["section_count"] != 32:
        raise ValueError("confirmation coordinate digest differs")
    subject_seconds = _finite_float(record["subject_seconds"], "subject seconds")
    campaign_seconds = _finite_float(record["campaign_seconds"], "campaign seconds")
    if (
        sum(section_times) != subject_seconds
        or subject_seconds > config["gates"]["maximum_subject_seconds"]
        or campaign_seconds > config["gates"]["maximum_campaign_seconds"]
        or campaign_seconds < subject_seconds
    ):
        raise ValueError("confirmation timing aggregate differs")

    observations = _mapping(record["observations"], "confirmation observations")
    expected_observations = {
        "maximum_reachable_support_cardinality": maximum_reachable,
        "maximum_total_function_cardinality": maximum_total,
        "mode_counts": dict(sorted(modes.items())),
        "piece_counts": piece_counts,
        "selector_window_scale_limits": window_scales,
    }
    if observations != expected_observations:
        raise ValueError("confirmation observations differ from complete sections")

    emissions = {
        "actions_emitted": record["actions_emitted"],
        "quality_rows_serialized": record["quality_rows_serialized"],
        "strategy_labels_generated": record["strategy_labels_generated"],
        "strategy_quality_claim": record["strategy_quality_claim"],
    }
    intended_zero_emission = emissions == {
        "actions_emitted": 0,
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
        "strategy_quality_claim": None,
    }
    if not intended_zero_emission:
        raise ValueError("confirmation artifact emitted a forbidden output")
    gates = _mapping(record["gates"], "confirmation gates")
    _keys(gates, _GATE_KEYS, "confirmation gates")
    expected_true = _GATE_KEYS - {"passed", "zero_actions_and_quality_rows"}
    if (
        any(gates[key] is not True for key in expected_true)
        or gates["zero_actions_and_quality_rows"] is not False
        or gates["passed"] is not False
        or record["passed"] is not False
        or record["decision"]
        != "reject_untouched_legal_h4_factorized_affine_confirmation"
        or not _finite_tree(record)
    ):
        raise ValueError("confirmation recorded terminal semantics differ")
    corrected = {
        key: bool(value) for key, value in gates.items() if key != "passed"
    }
    corrected["zero_actions_and_quality_rows"] = intended_zero_emission
    corrected["passed"] = all(corrected.values())
    if corrected["passed"] is not True:
        raise ValueError("confirmation corrected gate vector is not all true")
    return MappingProxyType(corrected)


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0362_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0362_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0362_ARTIFACT_SHA256,
    "authenticated_only_fields": _AUTHENTICATED_ONLY_FIELDS,
    "authority": (
        "retain_recorded_adr0361_rejection_while_independently_rebinding_"
        "the_complete_scientific_payload"
    ),
    "config_sha256": ADR0362_CONFIG_SHA256,
    "invocation_source_commit": ADR0362_INVOCATION_SOURCE_COMMIT,
    "parent_protocol_sha256": ADR0362_PARENT_PROTOCOL_SHA256,
    "recorded_decision": "reject_untouched_legal_h4_factorized_affine_confirmation",
    "runner_sha256": ADR0362_RUNNER_SHA256,
    "version": "adr0362-legal-h4-factorized-affine-confirmation-result-v1",
}
ADR0362_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0362_RESULT_PROTOCOL_SHA256 = _canonical_hash(_RESULT_PROTOCOL_PAYLOAD)


def verify_adr0362_legal_h4_factorized_affine_confirmation_artifact(
    path: Path | None = None,
) -> VerifiedLegalH4FactorizedAffineConfirmation:
    """Verify the retained bytes without importing or rerunning their writer."""

    artifact_path = (
        _ROOT / ADR0362_ARTIFACT_RELATIVE_PATH if path is None else path.resolve()
    )
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0362_ARTIFACT_BYTES or sha256(raw).hexdigest() != (
        ADR0362_ARTIFACT_SHA256
    ):
        raise ValueError("ADR-0362 artifact bytes differ")
    config = _verify_config()
    record = _load_json(raw)
    corrected = _verify_record(record, config)
    return VerifiedLegalH4FactorizedAffineConfirmation(
        record=MappingProxyType(record),
        artifact_sha256=ADR0362_ARTIFACT_SHA256,
        artifact_bytes=ADR0362_ARTIFACT_BYTES,
        source_commit=ADR0362_INVOCATION_SOURCE_COMMIT,
        recorded_passed=False,
        recorded_decision="reject_untouched_legal_h4_factorized_affine_confirmation",
        scientific_payload_rebound=True,
        intended_zero_emission_predicate=True,
        corrected_gate_vector=corrected,
        authenticated_only_fields=_AUTHENTICATED_ONLY_FIELDS,
    )


__all__ = [
    "ADR0362_ARTIFACT_BYTES",
    "ADR0362_ARTIFACT_RELATIVE_PATH",
    "ADR0362_ARTIFACT_SHA256",
    "ADR0362_CONFIG_SHA256",
    "ADR0362_INVOCATION_SOURCE_COMMIT",
    "ADR0362_RESULT_PROTOCOL",
    "ADR0362_RESULT_PROTOCOL_SHA256",
    "ADR0362_RUNNER_SHA256",
    "VerifiedLegalH4FactorizedAffineConfirmation",
    "verify_adr0362_legal_h4_factorized_affine_confirmation_artifact",
]
