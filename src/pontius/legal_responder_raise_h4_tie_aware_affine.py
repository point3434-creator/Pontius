"""Prospective legal-h4 tie-aware affine-envelope integration audit.

ADR-0352 source-seals this one-shot runner after ADR-0351 rejected the v1
single-tape certificate.  The runner enriches the already-open h4 normal-fan
family with every exact local maximizing tape, validates the maximum affine
gain envelope and ``z >= row`` epigraph direction, uses selector-window v2
only for exact singleton sources, and serializes both source and current
reachable-pruned tapes.  It emits no action or strategy-quality result.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import time
from typing import Any, Mapping

from .exact_selector_fan import reachable_response_tape, realization_interpolated_policy
from .exact_selector_window_oracle import (
    exact_best_response_trace,
    exact_policy_utilities,
)
from .exact_tie_aware_affine_envelope import (
    ExactTieAwareAffineSection,
    ResponseTape,
    build_exact_tie_aware_affine_section,
    enumerate_exact_local_maximizer_tapes,
)
from .game import Action
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_h4_selector_directions import (
    LegalH4SelectorDirection,
    compile_legal_h4_selector_directions,
    policy_sha256,
)
from .legal_h4_selector_fixture import (
    BOARD,
    JOINT_WEIGHT_DENOMINATOR,
    JOINT_WEIGHT_NUMERATORS,
    RESPONDER_HANDS,
    ROOT_HANDS,
    build_legal_h4_selector_game,
    legal_h4_source_policy,
)
from .legal_responder_raise_h4_row_growth_result import (
    verify_adr0349_legal_h4_row_growth_result_artifact,
)
from .legal_responder_raise_h4_selector_fan_result import (
    verify_adr0351_legal_h4_selector_fan_result_artifact,
)
from .runner_harness import assemble_environment, finalize_gates, serialize_result
from .selector_window import fixed_response_selector_scores
from .tie_aware_affine_adapter import choose_tie_aware_affine_mode


_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-tie-aware-affine-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-tie-aware-affine-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": _ROOT
    / "docs/decisions/ADR-0351-retain-the-legal-h4-fan-map-and-reject-certificate-authority.md",
    "expected_parent_artifact_sha256": _ROOT
    / "experiments/results/legal-responder-raise-h4-selector-window-v1.json",
    "expected_parent_result_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_selector_fan_result.py",
    "expected_parent_result_seal_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_selector_fan_result_seal.py",
    "expected_row_parent_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_row_growth_result.py",
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT / "src/pontius/legal_river_continuation.py",
    "expected_fixture_sha256": _ROOT / "src/pontius/legal_h4_selector_fixture.py",
    "expected_direction_compiler_sha256": _ROOT
    / "src/pontius/legal_h4_selector_directions.py",
    "expected_exact_selector_oracle_sha256": _ROOT
    / "src/pontius/exact_selector_window_oracle.py",
    "expected_exact_fan_sha256": _ROOT / "src/pontius/exact_selector_fan.py",
    "expected_exact_tie_envelope_sha256": _ROOT
    / "src/pontius/exact_tie_aware_affine_envelope.py",
    "expected_selector_window_v2_sha256": _ROOT
    / "src/pontius/selector_window_v2.py",
    "expected_tie_adapter_sha256": _ROOT / "src/pontius/tie_aware_affine_adapter.py",
    "expected_fixed_score_primitive_sha256": _ROOT / "src/pontius/selector_window.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _ROOT
    / "tests/test_exact_tie_aware_affine_envelope.py",
    "expected_runner_test_sha256": _ROOT
    / "tests/test_legal_responder_raise_h4_tie_aware_affine.py",
}

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
_SCHEDULE_NUMERATORS = tuple(range(17))
_SCHEDULE_DENOMINATOR = 16


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required tie-aware affine input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    rendered = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _tape_record(tape: ResponseTape | Mapping[str, Action]) -> list[dict[str, str]]:
    items = tape.items() if isinstance(tape, Mapping) else tape
    return [
        {"information_key": key, "action": str(action)}
        for key, action in sorted(items)
    ]


def _tape_sha256(tape: ResponseTape | Mapping[str, Action]) -> str:
    return _canonical_sha256(_tape_record(tape))


def _float_policy(
    policy: Mapping[str, Mapping[Action, Fraction | float]],
) -> dict[str, dict[Action, float]]:
    return {
        key: {action: float(value) for action, value in row.items()}
        for key, row in policy.items()
    }


def _direction_descriptor(
    direction: LegalH4SelectorDirection,
) -> dict[str, object]:
    return {
        "label": direction.label,
        "direction_class": direction.direction_class,
        "changed_public_histories": list(direction.changed_public_histories),
        "endpoint_policy_sha256": direction.endpoint_policy_sha256,
    }


def _identity_comparison(
    source_total: ResponseTape,
    source_pruned: ResponseTape,
    current_total: ResponseTape,
    current_pruned: ResponseTape,
) -> dict[str, object]:
    source = dict(source_total)
    current = dict(current_total)
    if set(source) != set(current):
        raise ValueError("tie-aware total-tape schemas differ")
    source_live = dict(source_pruned)
    current_live = dict(current_pruned)
    changed = {key for key in source if source[key] != current[key]}
    common_live = set(source_live) & set(current_live)
    return {
        "source_total_tape_sha256": _tape_sha256(source_total),
        "source_total_tape": _tape_record(source_total),
        "source_pruned_tape_sha256": _tape_sha256(source_pruned),
        "source_pruned_tape": _tape_record(source_pruned),
        "current_total_tape_sha256": _tape_sha256(current_total),
        "current_total_tape": _tape_record(current_total),
        "current_pruned_tape_sha256": _tape_sha256(current_pruned),
        "current_pruned_tape": _tape_record(current_pruned),
        "total_identity": source_total == current_total,
        "reachable_identity": source_pruned == current_pruned,
        "total_entry_changes": len(changed),
        "common_reachable_action_changes": sum(
            source[key] != current[key] for key in common_live
        ),
        "source_reachable_entries": len(source_live),
        "current_reachable_entries": len(current_live),
        "reachable_support_added": len(set(current_live) - set(source_live)),
        "reachable_support_removed": len(set(source_live) - set(current_live)),
        "current_unreachable_entry_changes": len(changed - set(current_live)),
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "board",
        "root_hands",
        "responder_hands",
        "joint_weight_numerators",
        "joint_weight_denominator",
        "acting_player",
        "expected_root_public_state_sha256",
        "expected_public_schema_sha256",
        "expected_game_structural_sha256",
        "expected_game_provenance_sha256",
        "expected_source_policy_sha256",
        "direction_descriptors",
        "schedule_numerators",
        "schedule_denominator",
        "selector_margin_allowance",
        "maximum_fan_tapes",
        "maximum_active_tapes_per_sample",
        "maximum_affine_rows",
        "section_coordinate",
        "active_set_semantics",
        "certificate_identity_authority",
        "reachable_identity_role",
        "row_envelope_direction",
        "same_fixture_evidence_scope",
        "reconnaissance_disclosure",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("tie-aware affine config fields differ from ADR-0352")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"tie-aware affine provenance mismatch: {field}")
    frozen = {
        "evidence_stage": "preregistered_after_adr0351_before_tie_aware_h4_run",
        "board": list(BOARD),
        "root_hands": [list(hand) for hand in ROOT_HANDS],
        "responder_hands": [list(hand) for hand in RESPONDER_HANDS],
        "joint_weight_numerators": [list(row) for row in JOINT_WEIGHT_NUMERATORS],
        "joint_weight_denominator": JOINT_WEIGHT_DENOMINATOR,
        "acting_player": 0,
        "expected_root_public_state_sha256": (
            "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
        ),
        "expected_public_schema_sha256": (
            "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
        ),
        "expected_game_structural_sha256": (
            "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
        ),
        "expected_game_provenance_sha256": (
            "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
        ),
        "expected_source_policy_sha256": (
            "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
        ),
        "direction_descriptors": list(_DIRECTION_DESCRIPTORS),
        "schedule_numerators": list(_SCHEDULE_NUMERATORS),
        "schedule_denominator": _SCHEDULE_DENOMINATOR,
        "selector_margin_allowance": 1e-12,
        "maximum_fan_tapes": 256,
        "maximum_active_tapes_per_sample": 256,
        "maximum_affine_rows": 1024,
        "section_coordinate": "sequence_form_realization_interpolation",
        "active_set_semantics": (
            "cartesian_closure_of_fraction_exact_local_maximizing_actions"
        ),
        "certificate_identity_authority": "total_function_only",
        "reachable_identity_role": "reporting_only",
        "row_envelope_direction": (
            "best_response_gain_is_maximum_of_all_retained_fixed_tape_rows_"
            "and_master_epigraph_is_z_greater_equal_each_row"
        ),
        "same_fixture_evidence_scope": (
            "development_integration_only_not_untouched_confirmation"
        ),
        "reconnaissance_disclosure": (
            "alternate_source_tape_endpoint_equivalence_was_observed_before_"
            "source_seal_and_is_excluded_from_pass_conditions"
        ),
        "claims_policy": (
            "legal_h4_tie_aware_integration_and_infrastructure_only_no_action_"
            "clock_full_width_multiway_action_quality_or_strength_claim"
        ),
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"tie-aware affine field differs from ADR-0352: {field}")
    expected_gates = {
        "expected_directions": 4,
        "expected_players": 2,
        "expected_schedule_points": 17,
        "maximum_float_exact_row_error": 1e-12,
        "maximum_fixed_score_calls": 256,
        "maximum_subject_seconds": 60.0,
        "maximum_total_seconds": 120.0,
        "maximum_scientific_payload_bytes": 16777216,
        "require_clean_git_state": True,
        "require_parent_map_retained_and_certificate_rejected": True,
        "require_fixture_and_direction_identity": True,
        "require_complete_active_tape_closure": True,
        "require_v2_only_for_exact_singletons": True,
        "require_ties_fail_closed_before_envelope": True,
        "require_maximum_envelope_identity": True,
        "require_epigraph_z_greater_equal_rows": True,
        "require_source_and_current_pruned_tapes": True,
        "require_total_function_certificate_authority": True,
        "require_zero_production_best_response_calls": True,
        "require_fraction_exact": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("tie-aware affine gates differ from ADR-0352")
    return {
        **config,
        "direction_descriptors": tuple(config["direction_descriptors"]),
        "schedule_numerators": tuple(config["schedule_numerators"]),
        "gates": dict(config["gates"]),
    }


def _row_record(row: Any) -> dict[str, object]:
    return {
        "response_tape_sha256": _tape_sha256(row.response_tape),
        "response_tape": _tape_record(row.response_tape),
        "response_value_intercept": _fraction_record(row.response_value_intercept),
        "response_value_slope": _fraction_record(row.response_value_slope),
        "profile_utility_intercept": _fraction_record(row.profile_utility_intercept),
        "profile_utility_slope": _fraction_record(row.profile_utility_slope),
        "deviation_gain_intercept": _fraction_record(row.deviation_gain_intercept),
        "deviation_gain_slope": _fraction_record(row.deviation_gain_slope),
        "epigraph_constraint": "z_greater_equal_row",
    }


def _critical_sample_record(sample: Any) -> dict[str, object]:
    return {
        "scale": _fraction_record(sample.scale),
        "sample_kind": sample.sample_kind,
        "response_value": _fraction_record(sample.response_value),
        "profile_utility": _fraction_record(sample.profile_utility),
        "deviation_gain": _fraction_record(sample.deviation_gain),
        "active_tape_sha256s": [_tape_sha256(tape) for tape in sample.active_tapes],
        "active_tapes": [_tape_record(tape) for tape in sample.active_tapes],
    }


def _audit_section(
    game: Any,
    source: Mapping[str, Mapping[Action, float]],
    endpoint: Mapping[str, Mapping[Action, float]],
    *,
    acting_player: int,
    target_player: int,
    parsed: Mapping[str, Any],
) -> tuple[dict[str, object], dict[str, object]]:
    started = time.perf_counter()
    section = build_exact_tie_aware_affine_section(
        game,
        source,
        endpoint,
        acting_player=acting_player,
        target_player=target_player,
        maximum_fan_tapes=int(parsed["maximum_fan_tapes"]),
        maximum_active_tapes_per_sample=int(
            parsed["maximum_active_tapes_per_sample"]
        ),
        maximum_affine_rows=int(parsed["maximum_affine_rows"]),
    )
    source_exact = realization_interpolated_policy(
        game,
        source,
        endpoint,
        acting_player=acting_player,
        scale=Fraction(0),
    )
    endpoint_exact = realization_interpolated_policy(
        game,
        source,
        endpoint,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    source_float = _float_policy(source_exact)
    endpoint_float = _float_policy(endpoint_exact)
    float_rows: dict[ResponseTape, tuple[float, float]] = {}
    score_endpoints = {}
    maximum_row_error = 0.0
    fixed_score_calls = 0
    for row in section.rows:
        left = fixed_response_selector_scores(
            game,
            source_float,
            target_player,
            dict(row.response_tape),
        )
        right = fixed_response_selector_scores(
            game,
            endpoint_float,
            target_player,
            dict(row.response_tape),
        )
        fixed_score_calls += 2
        float_rows[row.response_tape] = (left.value, right.value - left.value)
        maximum_row_error = max(
            maximum_row_error,
            abs(left.value - float(row.response_value_intercept)),
            abs(right.value - float(row.response_value_intercept + row.response_value_slope)),
        )
        if row.response_tape in section.source_active_tapes:
            score_endpoints[row.response_tape] = (left, right)
    adapter = choose_tie_aware_affine_mode(
        section,
        score_endpoints,
        selector_margin_allowance=float(parsed["selector_margin_allowance"]),
    )
    rows_by_tape = {row.response_tape: row for row in section.rows}
    schedule = []
    active_closure = True
    envelope_identity = True
    epigraph_direction = True
    pruned_tapes_complete = True
    for numerator in parsed["schedule_numerators"]:
        scale = Fraction(int(numerator), int(parsed["schedule_denominator"]))
        policy = realization_interpolated_policy(
            game,
            source,
            endpoint,
            acting_player=acting_player,
            scale=scale,
        )
        trace = exact_best_response_trace(game, policy, target_player)
        active_tapes = enumerate_exact_local_maximizer_tapes(
            trace,
            maximum_tapes=int(parsed["maximum_active_tapes_per_sample"]),
        )
        active_closure = bool(
            active_closure
            and set(active_tapes) <= set(rows_by_tape)
            and all(
                rows_by_tape[tape].response_value(scale) == trace.value
                for tape in active_tapes
            )
        )
        profile = exact_policy_utilities(game, policy)[target_player]
        exact_gain = trace.value - profile
        exact_values = {
            tape: row.deviation_gain(scale) for tape, row in rows_by_tape.items()
        }
        z = max(exact_values.values())
        residuals = {tape: z - value for tape, value in exact_values.items()}
        envelope_identity = bool(
            envelope_identity
            and z == exact_gain
            and all(value <= exact_gain for value in exact_values.values())
        )
        epigraph_direction = bool(
            epigraph_direction
            and all(value >= 0 for value in residuals.values())
            and any(value == 0 for value in residuals.values())
            and any((z - Fraction(1, 10**9)) < value for value in exact_values.values())
        )
        float_response = max(
            intercept + float(scale) * slope
            for intercept, slope in float_rows.values()
        )
        maximum_row_error = max(
            maximum_row_error,
            abs(float_response - float(trace.value)),
        )
        comparisons = []
        for current_tape in active_tapes:
            current_pruned = reachable_response_tape(
                game,
                policy,
                target_player,
                dict(current_tape),
            )
            for source_tape in section.source_active_tapes:
                source_pruned = reachable_response_tape(
                    game,
                    policy,
                    target_player,
                    dict(source_tape),
                )
                comparison = _identity_comparison(
                    source_tape,
                    source_pruned,
                    current_tape,
                    current_pruned,
                )
                pruned_tapes_complete = bool(
                    pruned_tapes_complete
                    and comparison["source_pruned_tape"]
                    == _tape_record(source_pruned)
                    and comparison["current_pruned_tape"]
                    == _tape_record(current_pruned)
                )
                comparisons.append(comparison)
        schedule.append(
            {
                "scale": _fraction_record(scale),
                "response_value": _fraction_record(trace.value),
                "profile_utility": _fraction_record(profile),
                "deviation_gain": _fraction_record(exact_gain),
                "maximum_envelope_value": _fraction_record(z),
                "active_tape_sha256s": [_tape_sha256(tape) for tape in active_tapes],
                "active_tapes": [_tape_record(tape) for tape in active_tapes],
                "identity_comparisons": comparisons,
                "epigraph_residuals": [
                    {
                        "response_tape_sha256": _tape_sha256(tape),
                        "z_minus_row": _fraction_record(residual),
                    }
                    for tape, residual in sorted(residuals.items(), key=lambda item: repr(item[0]))
                ],
                "float_exact_response_value_error": abs(
                    float_response - float(trace.value)
                ),
            }
        )
    tie_mode_honest = (
        (
            len(section.source_active_tapes) == 1
            and adapter.mode in {"v2_single_tape", "fail_closed"}
        )
        or (
            len(section.source_active_tapes) > 1
            and adapter.mode == "tie_aware_maximum_envelope"
            and all(window.scale_limit == 0.0 for _, window in adapter.v2_windows)
        )
    )
    metrics = {
        "active_closure": active_closure,
        "tie_mode_honest": tie_mode_honest,
        "tie_fail_closed": all(
            window.scale_limit == 0.0 for _, window in adapter.v2_windows
        )
        if len(section.source_active_tapes) > 1
        else True,
        "envelope_identity": envelope_identity,
        "epigraph_direction": epigraph_direction,
        "pruned_tapes_complete": pruned_tapes_complete,
        "maximum_row_error": maximum_row_error,
        "fixed_score_calls": fixed_score_calls,
        "subject_seconds": time.perf_counter() - started,
    }
    record = {
        "target_player": target_player,
        "integration_mode": adapter.mode,
        "single_tape_scale_limit": adapter.single_tape_scale_limit,
        "certificate_identity_authority": adapter.certificate_identity_authority,
        "source_active_tape_sha256s": [
            _tape_sha256(tape) for tape in section.source_active_tapes
        ],
        "source_active_tapes": [
            _tape_record(tape) for tape in section.source_active_tapes
        ],
        "affine_equivalence_classes": [
            [_tape_sha256(tape) for tape in group]
            for group in section.affine_equivalence_classes
        ],
        "v2_windows": [
            {
                "response_tape_sha256": _tape_sha256(tape),
                "scale_limit": window.scale_limit,
                "selector_comparisons": window.selector_comparisons,
                "exact_source_action_ties": window.exact_source_action_ties,
                "first_switch_information_key": window.first_switch_information_key,
                "first_switch_source_action": (
                    None
                    if window.first_switch_source_action is None
                    else str(window.first_switch_source_action)
                ),
                "first_switch_competing_action": (
                    None
                    if window.first_switch_competing_action is None
                    else str(window.first_switch_competing_action)
                ),
            }
            for tape, window in adapter.v2_windows
        ],
        "rows": [_row_record(row) for row in section.rows],
        "critical_samples": [
            _critical_sample_record(sample) for sample in section.samples
        ],
        "schedule": schedule,
        "metrics": metrics,
    }
    return record, metrics


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _execute_tie_aware_affine(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    parent = verify_adr0351_legal_h4_selector_fan_result_artifact()
    row_parent = verify_adr0349_legal_h4_row_growth_result_artifact()
    game = build_legal_h4_selector_game()
    source = legal_h4_source_policy(game)
    directions = compile_legal_h4_selector_directions(
        game,
        source,
        row_parent.record,
        acting_player=int(parsed["acting_player"]),
        tolerance=1e-10,
    )
    descriptors = tuple(_direction_descriptor(row) for row in directions)
    direction_records = []
    section_metrics = []
    for direction in directions:
        targets = []
        for target_player in range(game.num_players):
            record, metrics = _audit_section(
                game,
                source,
                direction.endpoint_policy,
                acting_player=int(parsed["acting_player"]),
                target_player=target_player,
                parsed=parsed,
            )
            targets.append(record)
            section_metrics.append(metrics)
        direction_records.append(
            {**_direction_descriptor(direction), "target_rows": targets}
        )
    aggregate = {
        "sections": len(section_metrics),
        "fixed_score_calls": sum(int(row["fixed_score_calls"]) for row in section_metrics),
        "production_best_response_calls": 0,
        "maximum_float_exact_row_error": max(
            float(row["maximum_row_error"]) for row in section_metrics
        ),
        "subject_seconds": sum(float(row["subject_seconds"]) for row in section_metrics),
        "active_closure": all(bool(row["active_closure"]) for row in section_metrics),
        "tie_mode_honest": all(bool(row["tie_mode_honest"]) for row in section_metrics),
        "tie_fail_closed": all(bool(row["tie_fail_closed"]) for row in section_metrics),
        "envelope_identity": all(bool(row["envelope_identity"]) for row in section_metrics),
        "epigraph_direction": all(bool(row["epigraph_direction"]) for row in section_metrics),
        "pruned_tapes_complete": all(
            bool(row["pruned_tapes_complete"]) for row in section_metrics
        ),
    }
    scientific_payload = {"directions": direction_records}
    scientific_bytes = len(
        json.dumps(
            scientific_payload,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    fixture_identity = (
        public_betting_state_sha256(game.base_state)
        == parsed["expected_root_public_state_sha256"]
        and row_parent.record["public_schema_sha256"]
        == parsed["expected_public_schema_sha256"]
        and game.structural_digest == parsed["expected_game_structural_sha256"]
        and game.provenance_digest == parsed["expected_game_provenance_sha256"]
        and policy_sha256(source) == parsed["expected_source_policy_sha256"]
        and descriptors == parsed["direction_descriptors"]
    )
    checks = {
        "clean_git_state": (not bool(git["dirty"]))
        == gates["require_clean_git_state"],
        "parent_map_retained_and_certificate_rejected": (
            parent.sections == 8
            and parent.source_tie_sections == 4
            and not parent.corrected_certificate_pass
            and not parent.successor_authorized
        )
        == gates["require_parent_map_retained_and_certificate_rejected"],
        "fixture_and_direction_identity": (
            fixture_identity
            and len(directions) == gates["expected_directions"]
            and game.num_players == gates["expected_players"]
        )
        == gates["require_fixture_and_direction_identity"],
        "complete_active_tape_closure": bool(aggregate["active_closure"])
        == gates["require_complete_active_tape_closure"],
        "v2_only_for_exact_singletons": bool(aggregate["tie_mode_honest"])
        == gates["require_v2_only_for_exact_singletons"],
        "ties_fail_closed_before_envelope": bool(aggregate["tie_fail_closed"])
        == gates["require_ties_fail_closed_before_envelope"],
        "maximum_envelope_identity": bool(aggregate["envelope_identity"])
        == gates["require_maximum_envelope_identity"],
        "epigraph_z_greater_equal_rows": bool(aggregate["epigraph_direction"])
        == gates["require_epigraph_z_greater_equal_rows"],
        "source_and_current_pruned_tapes": bool(aggregate["pruned_tapes_complete"])
        == gates["require_source_and_current_pruned_tapes"],
        "total_function_certificate_authority": (
            parsed["certificate_identity_authority"] == "total_function_only"
            and parsed["reachable_identity_role"] == "reporting_only"
        )
        == gates["require_total_function_certificate_authority"],
        "zero_production_best_response_calls": (
            aggregate["production_best_response_calls"] == 0
        )
        == gates["require_zero_production_best_response_calls"],
        "fraction_exact": all(
            record["metrics"]["envelope_identity"]
            and record["metrics"]["epigraph_direction"]
            for direction in direction_records
            for record in direction["target_rows"]
        )
        == gates["require_fraction_exact"],
        "float_exact_rows": aggregate["maximum_float_exact_row_error"]
        <= gates["maximum_float_exact_row_error"],
        "fixed_score_calls": aggregate["fixed_score_calls"]
        <= gates["maximum_fixed_score_calls"],
        "schedule_width": all(
            len(record["schedule"]) == gates["expected_schedule_points"]
            for direction in direction_records
            for record in direction["target_rows"]
        ),
        "subject_wall": aggregate["subject_seconds"]
        <= gates["maximum_subject_seconds"],
        "scientific_payload_bytes": scientific_bytes
        <= gates["maximum_scientific_payload_bytes"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    payload = {
        "root_public_state_sha256": public_betting_state_sha256(game.base_state),
        "public_schema_sha256": row_parent.record["public_schema_sha256"],
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "source_policy_sha256": policy_sha256(source),
        "direction_descriptors": list(descriptors),
        "schedule": {
            "numerators": list(parsed["schedule_numerators"]),
            "denominator": parsed["schedule_denominator"],
            "points": len(parsed["schedule_numerators"]),
        },
        "integration_semantics": {
            "section_coordinate": parsed["section_coordinate"],
            "active_set_semantics": parsed["active_set_semantics"],
            "certificate_identity_authority": parsed[
                "certificate_identity_authority"
            ],
            "reachable_identity_role": parsed["reachable_identity_role"],
            "row_envelope_direction": parsed["row_envelope_direction"],
            "same_fixture_evidence_scope": parsed["same_fixture_evidence_scope"],
            "reconnaissance_disclosure": parsed["reconnaissance_disclosure"],
        },
        **scientific_payload,
        "aggregate": {
            **aggregate,
            "scientific_payload_bytes": scientific_bytes,
            "total_seconds": total_seconds,
        },
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
        "production_actions_emitted": 0,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    result = finalize_gates(checks)
    return {
        **payload,
        **result,
        "decision": (
            "authorize_fresh_tie_aware_affine_confirmation_preregistration"
            if result["passed"]
            else "reject_legal_h4_tie_aware_affine_integration"
        ),
        "total_seconds": total_seconds,
    }


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _environment(git: Mapping[str, Any] | None) -> dict[str, Any]:
    return assemble_environment(
        runtime={"backend": "cpu_float64_fixed_rows_plus_fraction_active_set"},
        git=(
            {"available": False, "dirty": None, "commit": None}
            if git is None
            else git
        ),
    )


def run_legal_responder_raise_h4_tie_aware_affine(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute ADR-0352 exactly once and retain its first terminal."""

    if os.path.lexists(output_path):
        raise FileExistsError(f"tie-aware affine result path exists: {output_path}")
    started = time.perf_counter()
    stage = "config"
    git: Mapping[str, Any] | None = None
    try:
        parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
        stage = "git"
        git = _strict_git_metadata()
        stage = "tie_aware_affine"
        payload = _execute_tie_aware_affine(parsed, git=git)
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_tie_aware_affine_executed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "methodology": {
                "betting_authority": "NoLimitBettingState",
                "teacher": "fraction_exact_active_tape_closure",
                "subject": "float64_fixed_tape_maximum_affine_envelope",
                "single_tape_certificate": "selector_window_v2_only",
                "certificate_identity": "total_function",
                "behavioral_identity": "reachable_support_reporting_only",
                "production_best_response_calls": 0,
                "quality_rows": 0,
                "strategy_labels": 0,
            },
            **payload,
            "strategy_quality_claim": None,
            "limitations": [
                "This is same-fixture h4 development integration, not untouched confirmation.",
                "Pre-seal alternate-tape reconnaissance is disclosed and is not a pass condition.",
                "Local exact maximizer closure is bounded small-game evidence, not a width prior.",
                (
                    "Reachable-support identity is descriptive; total-function "
                    "identity gates certificates."
                ),
                "Infrastructure walls are not action-clock latency.",
                (
                    "No full-width, multiway, action, strategy-quality, or "
                    "poker-strength result is emitted."
                ),
            ],
        }
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_tie_aware_affine_failed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path) if config_path.is_file() else None,
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "passed": False,
            "decision": "reject_legal_h4_tie_aware_affine_integration",
            "failure": {
                "stage": stage,
                "type": type(error).__name__,
                "message": str(error),
            },
            "total_seconds": time.perf_counter() - started,
            "strategy_quality_claim": None,
        }
    _write_exclusive(output_path, serialize_result(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_legal_responder_raise_h4_tie_aware_affine(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "total_seconds": result["total_seconds"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
