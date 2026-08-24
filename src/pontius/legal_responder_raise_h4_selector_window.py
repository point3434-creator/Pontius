"""Prospective legal h4 selector normal-fan audit.

This is the sole public runner for ADR-0350.  It maps four source-sealed
sequence-form directions with a Fraction teacher, records production selector
tapes on an untouched dyadic schedule, and keeps total-function certificate
identity separate from reachable-support behavioral identity.
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

from .evaluation import Policy, best_response
from .exact_selector_fan import (
    ExactSelectorFanSection,
    map_exact_selector_fan_section,
    reachable_response_tape,
    realization_interpolated_policy,
)
from .exact_selector_window_oracle import (
    ExactBestResponseTrace,
    exact_best_response_trace,
    exact_fixed_response_trace,
    exact_policy_utilities,
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
from .runner_harness import assemble_environment, finalize_gates, serialize_result
from .selector_fan_controls import run_selector_fan_controls
from .selector_window import (
    conservative_affine_selector_window,
    fixed_response_selector_scores,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/legal-responder-raise-h4-selector-window-v1.json"
_OUTPUT = _ROOT / "experiments/results/legal-responder-raise-h4-selector-window-v1.json"
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": _ROOT
    / "docs/decisions/ADR-0349-retain-and-seal-the-legal-h4-row-growth-result.md",
    "expected_parent_artifact_sha256": _ROOT
    / "experiments/results/legal-responder-raise-h4-row-growth-v1.json",
    "expected_parent_result_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_row_growth_result.py",
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT / "src/pontius/legal_river_continuation.py",
    "expected_fixture_sha256": _ROOT / "src/pontius/legal_h4_selector_fixture.py",
    "expected_direction_compiler_sha256": _ROOT
    / "src/pontius/legal_h4_selector_directions.py",
    "expected_cfr_sha256": _ROOT / "src/pontius/cfr.py",
    "expected_generation_primitive_sha256": _ROOT
    / "src/pontius/one_seat_convex_generation.py",
    "expected_evaluation_sha256": _ROOT / "src/pontius/evaluation.py",
    "expected_exact_selector_oracle_sha256": _ROOT
    / "src/pontius/exact_selector_window_oracle.py",
    "expected_exact_fan_sha256": _ROOT / "src/pontius/exact_selector_fan.py",
    "expected_selector_window_sha256": _ROOT / "src/pontius/selector_window.py",
    "expected_fan_controls_sha256": _ROOT / "src/pontius/selector_fan_controls.py",
    "expected_exact_control_test_sha256": _ROOT
    / "tests/test_exact_selector_fan.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _ROOT
    / "tests/test_legal_responder_raise_h4_selector_window.py",
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
_STATES = ("fixed", "tie_unresolved", "switched")


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required legal h4 selector input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    rendered = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _action_token(action: object) -> str:
    return str(action)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _tape_record(tape: Mapping[str, Action] | tuple[tuple[str, Action], ...]) -> list[dict[str, str]]:
    items = tape.items() if isinstance(tape, Mapping) else tape
    return [
        {"information_key": key, "action": _action_token(action)}
        for key, action in sorted(items)
    ]


def _tape_sha256(tape: Mapping[str, Action] | tuple[tuple[str, Action], ...]) -> str:
    return _canonical_sha256(_tape_record(tape))


def _tie_record(trace: ExactBestResponseTrace) -> list[dict[str, object]]:
    return [
        {
            "information_key": row.key,
            "maximizing_actions": [
                _action_token(action) for action in row.maximizing_actions
            ],
        }
        for row in trace.information_sets
        if len(row.maximizing_actions) > 1
    ]


def _float_policy(
    policy: Mapping[str, Mapping[Action, Fraction | float]],
) -> Policy:
    return {
        key: {action: float(value) for action, value in row.items()}
        for key, row in policy.items()
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
        "fan_states",
        "section_coordinate",
        "total_tape_identity",
        "reachable_tape_identity",
        "certificate_identity_authority",
        "tie_measure_semantics",
        "row_envelope_direction",
        "legacy_differential_scope",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("legal h4 selector config fields differ from ADR-0350")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"legal h4 selector provenance mismatch: {field}")
    frozen = {
        "evidence_stage": "preregistered_after_adr0349_before_legal_h4_selector_run",
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
        "fan_states": list(_STATES),
        "section_coordinate": "sequence_form_realization_interpolation",
        "total_tape_identity": (
            "complete_sorted_information_key_action_total_function"
        ),
        "reachable_tape_identity": (
            "complete_sorted_positive_support_information_key_action_behavior"
        ),
        "certificate_identity_authority": "total_function_only",
        "tie_measure_semantics": (
            "exact_fraction_lebesgue_interval_measure_plus_separate_zero_measure_points"
        ),
        "row_envelope_direction": (
            "best_response_gain_is_maximum_of_fixed_tape_affine_gain_rows_"
            "with_master_epigraph_constraints_z_greater_equal_row"
        ),
        "legacy_differential_scope": (
            "every_frozen_one_public_history_ray_reproduces_exact_margin_over_"
            "closing_slope_breakpoint"
        ),
        "claims_policy": (
            "legal_h4_selector_fan_and_infrastructure_only_no_action_clock_"
            "full_width_multiway_action_quality_or_strength_claim"
        ),
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"legal h4 selector field differs from ADR-0350: {field}")
    expected_gates = {
        "expected_directions": 4,
        "expected_regret_vertex_directions": 3,
        "expected_lp_proposed_directions": 1,
        "expected_players": 2,
        "expected_schedule_points": 17,
        "expected_production_selector_calls": 136,
        "expected_changed_public_histories_per_direction": [1, 1, 1, 1],
        "maximum_float_exact_response_value_error": 1e-12,
        "maximum_zero_allowance_breakpoint_error": 1e-12,
        "maximum_subject_selector_seconds": 60.0,
        "maximum_total_seconds": 120.0,
        "maximum_scientific_payload_bytes": 16777216,
        "require_clean_git_state": True,
        "require_parent_pass": True,
        "require_direction_identities": True,
        "require_exact_three_state_partition": True,
        "require_total_and_reachable_identity_columns": True,
        "require_exact_tape_optimality": True,
        "require_unique_selector_agreement": True,
        "require_fixed_tape_value_identity": True,
        "require_affine_row_activation": True,
        "require_upper_envelope_direction": True,
        "require_legacy_breakpoint_identity": True,
        "require_conservative_total_tape_window": True,
        "require_engineered_tie_nonempty": True,
        "require_engineered_crossing_identity": True,
        "require_no_reachable_identity_gate": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("legal h4 selector gates differ from ADR-0350")
    return {
        **config,
        "direction_descriptors": tuple(config["direction_descriptors"]),
        "schedule_numerators": tuple(config["schedule_numerators"]),
        "fan_states": tuple(config["fan_states"]),
        "gates": dict(config["gates"]),
    }


def _direction_descriptor(direction: LegalH4SelectorDirection) -> dict[str, object]:
    return {
        "label": direction.label,
        "direction_class": direction.direction_class,
        "changed_public_histories": list(direction.changed_public_histories),
        "endpoint_policy_sha256": direction.endpoint_policy_sha256,
    }


def _state_at_scale(
    fan: ExactSelectorFanSection,
    scale: Fraction,
) -> tuple[str, str]:
    point = next((row for row in fan.points if row.scale == scale), None)
    if point is not None:
        return point.total_state, point.reachable_state
    segment = next(
        row for row in fan.segments if row.lower < scale < row.upper
    )
    return segment.total_state, segment.reachable_state


def _identity_columns(
    source_total: tuple[tuple[str, Action], ...],
    source_reachable: tuple[tuple[str, Action], ...],
    current_total: tuple[tuple[str, Action], ...],
    current_reachable: tuple[tuple[str, Action], ...],
) -> dict[str, object]:
    source = dict(source_total)
    current = dict(current_total)
    source_live = dict(source_reachable)
    current_live = dict(current_reachable)
    changed = {key for key in source if source[key] != current[key]}
    common_live = set(source_live) & set(current_live)
    return {
        "total_identity": source_total == current_total,
        "reachable_identity": source_reachable == current_reachable,
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


def _fan_record(fan: ExactSelectorFanSection) -> dict[str, object]:
    return {
        "source_tape_sha256": _tape_sha256(fan.source_tape),
        "source_tape": _tape_record(fan.source_tape),
        "source_cell_upper": _fraction_record(fan.source_cell_upper),
        "legacy_source_breakpoint": _fraction_record(
            fan.legacy_source_breakpoint
        ),
        "cells": [
            {
                "response_tape_sha256": _tape_sha256(cell.response_tape),
                "response_tape": _tape_record(cell.response_tape),
                "lower": _fraction_record(cell.lower),
                "upper": _fraction_record(cell.upper),
            }
            for cell in fan.cells
        ],
        "segments": [
            {
                "lower": _fraction_record(row.lower),
                "upper": _fraction_record(row.upper),
                "witness": _fraction_record(row.witness),
                "response_tape_sha256": _tape_sha256(row.response_tape),
                "reachable_tape_sha256": _tape_sha256(row.reachable_tape),
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "total_tie_information_sets": list(row.total_tie_information_sets),
                "reachable_tie_information_sets": list(
                    row.reachable_tie_information_sets
                ),
            }
            for row in fan.segments
        ],
        "points": [
            {
                "scale": _fraction_record(row.scale),
                "response_tape_sha256": _tape_sha256(row.response_tape),
                "reachable_tape_sha256": _tape_sha256(row.reachable_tape),
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "total_tie_information_sets": list(row.total_tie_information_sets),
                "reachable_tie_information_sets": list(
                    row.reachable_tie_information_sets
                ),
            }
            for row in fan.points
        ],
        "measure": {
            "total": {
                "fixed": _fraction_record(fan.total_fixed_measure),
                "tie_unresolved": _fraction_record(
                    fan.total_tie_unresolved_measure
                ),
                "switched": _fraction_record(fan.total_switched_measure),
            },
            "reachable": {
                "fixed": _fraction_record(fan.reachable_fixed_measure),
                "tie_unresolved": _fraction_record(
                    fan.reachable_tie_unresolved_measure
                ),
                "switched": _fraction_record(fan.reachable_switched_measure),
            },
        },
        "tie_points": {
            "total": [_fraction_record(value) for value in fan.total_tie_points],
            "reachable": [
                _fraction_record(value) for value in fan.reachable_tie_points
            ],
        },
    }


def _audit_direction(
    game: Any,
    source: Policy,
    direction: LegalH4SelectorDirection,
    parsed: Mapping[str, Any],
) -> tuple[dict[str, object], dict[str, object]]:
    acting_player = int(parsed["acting_player"])
    endpoint_exact = realization_interpolated_policy(
        game,
        source,
        direction.endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    source_exact = realization_interpolated_policy(
        game,
        source,
        direction.endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(0),
    )
    target_rows = []
    metrics = {
        "selector_calls": 0,
        "selector_seconds": 0.0,
        "maximum_value_error": 0.0,
        "maximum_breakpoint_error": 0.0,
        "exact_tape_optimality": True,
        "unique_selector_agreement": True,
        "fixed_tape_value_identity": True,
        "affine_row_activation": True,
        "upper_envelope_direction": True,
        "legacy_breakpoint_identity": True,
        "conservative_total_tape_window": True,
        "three_state_partition": True,
        "identity_columns": True,
    }
    for target_player in range(game.num_players):
        fan_started = time.perf_counter()
        fan = map_exact_selector_fan_section(
            game,
            source_exact,
            endpoint_exact,
            acting_player=acting_player,
            target_player=target_player,
            maximum_tapes=int(parsed["maximum_fan_tapes"]),
        )
        fan_seconds = time.perf_counter() - fan_started
        source_tape = dict(fan.source_tape)
        source_float = _float_policy(source_exact)
        endpoint_float = _float_policy(endpoint_exact)
        source_scores = fixed_response_selector_scores(
            game, source_float, target_player, source_tape
        )
        endpoint_scores = fixed_response_selector_scores(
            game, endpoint_float, target_player, source_tape
        )
        zero_window = conservative_affine_selector_window(
            source_scores,
            endpoint_scores,
            selector_margin_allowance=0.0,
        )
        conservative = conservative_affine_selector_window(
            source_scores,
            endpoint_scores,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
        )
        breakpoint_error = abs(
            zero_window.scale_limit - float(fan.source_cell_upper)
        )
        metrics["maximum_breakpoint_error"] = max(
            float(metrics["maximum_breakpoint_error"]), breakpoint_error
        )
        metrics["legacy_breakpoint_identity"] = bool(
            metrics["legacy_breakpoint_identity"]
            and fan.source_cell_upper == fan.legacy_source_breakpoint
        )
        conservative_fraction = Fraction.from_float(conservative.scale_limit)
        metrics["conservative_total_tape_window"] = bool(
            metrics["conservative_total_tape_window"]
            and conservative_fraction <= fan.source_cell_upper
        )

        source_utilities = exact_policy_utilities(game, source_exact)
        endpoint_utilities = exact_policy_utilities(game, endpoint_exact)
        profile_intercept = source_utilities[target_player]
        profile_slope = endpoint_utilities[target_player] - profile_intercept
        row_library = []
        rows_by_tape: dict[
            tuple[tuple[str, Action], ...], tuple[Fraction, Fraction]
        ] = {}
        for cell in fan.cells:
            tape = dict(cell.response_tape)
            left = exact_fixed_response_trace(
                game, source_exact, target_player, tape
            )
            right = exact_fixed_response_trace(
                game, endpoint_exact, target_player, tape
            )
            response_intercept = left.value
            response_slope = right.value - left.value
            gain_intercept = response_intercept - profile_intercept
            gain_slope = response_slope - profile_slope
            rows_by_tape[cell.response_tape] = (gain_intercept, gain_slope)
            row_library.append(
                {
                    "response_tape_sha256": _tape_sha256(cell.response_tape),
                    "response_tape": _tape_record(cell.response_tape),
                    "active_cell_lower": _fraction_record(cell.lower),
                    "active_cell_upper": _fraction_record(cell.upper),
                    "response_value_intercept": _fraction_record(
                        response_intercept
                    ),
                    "response_value_slope": _fraction_record(response_slope),
                    "profile_utility_intercept": _fraction_record(
                        profile_intercept
                    ),
                    "profile_utility_slope": _fraction_record(profile_slope),
                    "deviation_gain_row_intercept": _fraction_record(
                        gain_intercept
                    ),
                    "deviation_gain_row_slope": _fraction_record(gain_slope),
                    "envelope_role": "lower_bound_row_under_maximum_upper_envelope",
                }
            )

        schedule = []
        for numerator in parsed["schedule_numerators"]:
            scale = Fraction(int(numerator), int(parsed["schedule_denominator"]))
            exact_policy = realization_interpolated_policy(
                game,
                source_exact,
                endpoint_exact,
                acting_player=acting_player,
                scale=scale,
            )
            float_policy = _float_policy(exact_policy)
            selector_started = time.perf_counter()
            production_value, production_tape = best_response(
                game, float_policy, target_player
            )
            selector_seconds = time.perf_counter() - selector_started
            metrics["selector_calls"] = int(metrics["selector_calls"]) + 1
            metrics["selector_seconds"] = (
                float(metrics["selector_seconds"]) + selector_seconds
            )
            exact = exact_best_response_trace(game, exact_policy, target_player)
            exact_tape = tuple(sorted(exact.selected_actions.items()))
            production_exact = exact_fixed_response_trace(
                game,
                exact_policy,
                target_player,
                production_tape,
            )
            production_optimal = (
                production_exact.value == exact.value
                and all(
                    row.selected_is_maximal
                    for row in production_exact.information_sets
                )
            )
            exact_ties = _tie_record(exact)
            unique_agreement = bool(exact_ties) or tuple(
                sorted(production_tape.items())
            ) == exact_tape
            exact_fixed = exact_fixed_response_trace(
                game,
                exact_policy,
                target_player,
                exact.selected_actions,
            )
            fixed_identity = exact_fixed.value == exact.value and all(
                row.selected_is_maximal for row in exact_fixed.information_sets
            )
            value_error = abs(float(exact.value) - float(production_value))
            metrics["maximum_value_error"] = max(
                float(metrics["maximum_value_error"]), value_error
            )
            metrics["exact_tape_optimality"] = bool(
                metrics["exact_tape_optimality"] and production_optimal
            )
            metrics["unique_selector_agreement"] = bool(
                metrics["unique_selector_agreement"] and unique_agreement
            )
            metrics["fixed_tape_value_identity"] = bool(
                metrics["fixed_tape_value_identity"] and fixed_identity
            )
            utilities = exact_policy_utilities(game, exact_policy)
            exact_gain = exact.value - utilities[target_player]
            row_values = {
                tape: intercept + scale * slope
                for tape, (intercept, slope) in rows_by_tape.items()
            }
            active_identity = (
                exact_tape in row_values
                and row_values[exact_tape] == exact_gain
            )
            envelope_identity = max(row_values.values()) == exact_gain
            metrics["affine_row_activation"] = bool(
                metrics["affine_row_activation"] and active_identity
            )
            metrics["upper_envelope_direction"] = bool(
                metrics["upper_envelope_direction"]
                and envelope_identity
                and all(value <= exact_gain for value in row_values.values())
            )
            total_state, reachable_state = _state_at_scale(fan, scale)
            current_reachable = reachable_response_tape(
                game,
                exact_policy,
                target_player,
                exact.selected_actions,
            )
            source_reachable = reachable_response_tape(
                game,
                exact_policy,
                target_player,
                source_tape,
            )
            columns = _identity_columns(
                fan.source_tape,
                source_reachable,
                exact_tape,
                current_reachable,
            )
            metrics["identity_columns"] = bool(
                metrics["identity_columns"]
                and set(columns)
                == {
                    "total_identity",
                    "reachable_identity",
                    "total_entry_changes",
                    "common_reachable_action_changes",
                    "source_reachable_entries",
                    "current_reachable_entries",
                    "reachable_support_added",
                    "reachable_support_removed",
                    "current_unreachable_entry_changes",
                }
            )
            if scale < conservative_fraction:
                metrics["conservative_total_tape_window"] = bool(
                    metrics["conservative_total_tape_window"]
                    and exact_tape == fan.source_tape
                )
            schedule.append(
                {
                    "scale": _fraction_record(scale),
                    "total_state": total_state,
                    "reachable_state": reachable_state,
                    "exact_response_value": _fraction_record(exact.value),
                    "production_response_value_hex": float(production_value).hex(),
                    "float_exact_response_value_error": value_error,
                    "exact_response_tape_sha256": _tape_sha256(exact_tape),
                    "exact_response_tape": _tape_record(exact_tape),
                    "production_response_tape_sha256": _tape_sha256(
                        production_tape
                    ),
                    "production_response_tape": _tape_record(production_tape),
                    "reachable_response_tape_sha256": _tape_sha256(
                        current_reachable
                    ),
                    "reachable_response_tape": _tape_record(current_reachable),
                    "exact_ties": exact_ties,
                    "production_tape_exactly_optimal": production_optimal,
                    "unique_exact_selector_agreement": unique_agreement,
                    "fixed_tape_value_identity": fixed_identity,
                    "active_row_identity": active_identity,
                    "upper_envelope_identity": envelope_identity,
                    "identity_columns": columns,
                    "production_selector_seconds": selector_seconds,
                }
            )

        total_measure = (
            fan.total_fixed_measure
            + fan.total_tie_unresolved_measure
            + fan.total_switched_measure
        )
        reachable_measure = (
            fan.reachable_fixed_measure
            + fan.reachable_tie_unresolved_measure
            + fan.reachable_switched_measure
        )
        metrics["three_state_partition"] = bool(
            metrics["three_state_partition"]
            and total_measure == 1
            and reachable_measure == 1
        )
        target_rows.append(
            {
                "target_player": target_player,
                "fan": _fan_record(fan),
                "row_library": row_library,
                "schedule": schedule,
                "float_window": {
                    "zero_allowance_scale": zero_window.scale_limit,
                    "conservative_scale": conservative.scale_limit,
                    "selector_margin_allowance": parsed[
                        "selector_margin_allowance"
                    ],
                    "first_switch_information_key": (
                        conservative.first_switch_information_key
                    ),
                    "first_switch_source_action": (
                        None
                        if conservative.first_switch_source_action is None
                        else _action_token(conservative.first_switch_source_action)
                    ),
                    "first_switch_competing_action": (
                        None
                        if conservative.first_switch_competing_action is None
                        else _action_token(
                            conservative.first_switch_competing_action
                        )
                    ),
                    "selector_comparisons": conservative.selector_comparisons,
                    "exact_source_action_ties_float": (
                        conservative.exact_source_action_ties
                    ),
                    "zero_allowance_breakpoint_error": breakpoint_error,
                    "conservative_not_beyond_exact": (
                        conservative_fraction <= fan.source_cell_upper
                    ),
                },
                "fan_audit_seconds": fan_seconds,
            }
        )
    return (
        {
            **_direction_descriptor(direction),
            "target_rows": target_rows,
        },
        metrics,
    )


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


def _control_record(control: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in control.items():
        if isinstance(item, tuple):
            result[key] = [_fraction_record(value) for value in item]
        elif isinstance(item, Fraction):
            result[key] = _fraction_record(item)
        else:
            raise TypeError("selector-fan control output is not exact")
    return result


def _execute_selector_window(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    parent = verify_adr0349_legal_h4_row_growth_result_artifact()
    game = build_legal_h4_selector_game()
    source = legal_h4_source_policy(game)
    directions = compile_legal_h4_selector_directions(
        game,
        source,
        parent.record,
        acting_player=int(parsed["acting_player"]),
        tolerance=1e-10,
    )
    descriptors = tuple(_direction_descriptor(row) for row in directions)
    controls = run_selector_fan_controls()
    direction_rows = []
    aggregate = {
        "selector_calls": 0,
        "selector_seconds": 0.0,
        "maximum_value_error": 0.0,
        "maximum_breakpoint_error": 0.0,
        "exact_tape_optimality": True,
        "unique_selector_agreement": True,
        "fixed_tape_value_identity": True,
        "affine_row_activation": True,
        "upper_envelope_direction": True,
        "legacy_breakpoint_identity": True,
        "conservative_total_tape_window": True,
        "three_state_partition": True,
        "identity_columns": True,
    }
    for direction in directions:
        record, metrics = _audit_direction(game, source, direction, parsed)
        direction_rows.append(record)
        for key in (
            "selector_calls",
            "selector_seconds",
        ):
            aggregate[key] += metrics[key]
        for key in ("maximum_value_error", "maximum_breakpoint_error"):
            aggregate[key] = max(aggregate[key], metrics[key])
        for key in (
            "exact_tape_optimality",
            "unique_selector_agreement",
            "fixed_tape_value_identity",
            "affine_row_activation",
            "upper_envelope_direction",
            "legacy_breakpoint_identity",
            "conservative_total_tape_window",
            "three_state_partition",
            "identity_columns",
        ):
            aggregate[key] = bool(aggregate[key] and metrics[key])
    scientific_payload = {
        "directions": direction_rows,
        "engineered_controls": _control_record(controls),
    }
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
    checks = {
        "clean_git_state": (not bool(git["dirty"]))
        == gates["require_clean_git_state"],
        "parent_pass": bool(parent.record["passed"]) == gates["require_parent_pass"],
        "fixture_identity": (
            public_betting_state_sha256(game.base_state)
            == parsed["expected_root_public_state_sha256"]
            and parent.record["public_schema_sha256"]
            == parsed["expected_public_schema_sha256"]
            and game.structural_digest == parsed["expected_game_structural_sha256"]
            and game.provenance_digest == parsed["expected_game_provenance_sha256"]
            and policy_sha256(source) == parsed["expected_source_policy_sha256"]
        ),
        "direction_inventory": (
            len(directions) == gates["expected_directions"]
            and sum(row.direction_class == "one_step_dcfr_regret_vertex" for row in directions)
            == gates["expected_regret_vertex_directions"]
            and sum(
                row.direction_class == "retained_restricted_master_proposal"
                for row in directions
            )
            == gates["expected_lp_proposed_directions"]
        ),
        "direction_identities": descriptors == parsed["direction_descriptors"]
        and [len(row.changed_public_histories) for row in directions]
        == gates["expected_changed_public_histories_per_direction"]
        and gates["require_direction_identities"],
        "selector_call_sites": (
            aggregate["selector_calls"]
            == gates["expected_production_selector_calls"]
            == len(directions)
            * gates["expected_players"]
            * gates["expected_schedule_points"]
        ),
        "exact_three_state_partition": bool(aggregate["three_state_partition"])
        == gates["require_exact_three_state_partition"],
        "total_and_reachable_identity_columns": bool(aggregate["identity_columns"])
        == gates["require_total_and_reachable_identity_columns"],
        "exact_tape_optimality": bool(aggregate["exact_tape_optimality"])
        == gates["require_exact_tape_optimality"],
        "unique_selector_agreement": bool(aggregate["unique_selector_agreement"])
        == gates["require_unique_selector_agreement"],
        "fixed_tape_value_identity": bool(aggregate["fixed_tape_value_identity"])
        == gates["require_fixed_tape_value_identity"],
        "affine_row_activation": bool(aggregate["affine_row_activation"])
        == gates["require_affine_row_activation"],
        "upper_envelope_direction": bool(aggregate["upper_envelope_direction"])
        == gates["require_upper_envelope_direction"],
        "legacy_breakpoint_identity": bool(aggregate["legacy_breakpoint_identity"])
        == gates["require_legacy_breakpoint_identity"],
        "conservative_total_tape_window": bool(
            aggregate["conservative_total_tape_window"]
        )
        == gates["require_conservative_total_tape_window"],
        "float_exact_response_values": aggregate["maximum_value_error"]
        <= gates["maximum_float_exact_response_value_error"],
        "zero_allowance_breakpoint_values": aggregate["maximum_breakpoint_error"]
        <= gates["maximum_zero_allowance_breakpoint_error"],
        "engineered_tie_nonempty": (
            controls["degenerate_total_tie_measure"] == 1
            and controls["degenerate_reachable_tie_measure"] == 1
        )
        == gates["require_engineered_tie_nonempty"],
        "engineered_crossing_identity": (
            controls["crossing_breakpoint"] == Fraction(1, 2)
            and controls["crossing_legacy_breakpoint"] == Fraction(1, 2)
            and controls["crossing_tie_points"] == (Fraction(1, 2),)
        )
        == gates["require_engineered_crossing_identity"],
        "reachable_identity_is_reporting_only": gates[
            "require_no_reachable_identity_gate"
        ],
        "subject_selector_wall": aggregate["selector_seconds"]
        <= gates["maximum_subject_selector_seconds"],
        "scientific_payload_bytes": scientific_bytes
        <= gates["maximum_scientific_payload_bytes"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    payload = {
        "root_public_state_sha256": public_betting_state_sha256(game.base_state),
        "public_schema_sha256": parent.record["public_schema_sha256"],
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "source_policy_sha256": policy_sha256(source),
        "direction_descriptors": list(descriptors),
        "schedule": {
            "numerators": list(parsed["schedule_numerators"]),
            "denominator": parsed["schedule_denominator"],
            "points": len(parsed["schedule_numerators"]),
        },
        "fan_semantics": {
            "states": list(parsed["fan_states"]),
            "section_coordinate": parsed["section_coordinate"],
            "total_tape_identity": parsed["total_tape_identity"],
            "reachable_tape_identity": parsed["reachable_tape_identity"],
            "certificate_identity_authority": parsed[
                "certificate_identity_authority"
            ],
            "tie_measure_semantics": parsed["tie_measure_semantics"],
            "row_envelope_direction": parsed["row_envelope_direction"],
            "legacy_differential_scope": parsed[
                "legacy_differential_scope"
            ],
        },
        **scientific_payload,
        "aggregate": {
            **aggregate,
            "scientific_payload_bytes": scientific_bytes,
            "total_seconds": total_seconds,
        },
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    result = finalize_gates(checks)
    return {
        **payload,
        **result,
        "decision": (
            "authorize_legal_h4_selector_stable_affine_integration_preregistration"
            if result["passed"]
            else "reject_legal_h4_selector_window_boundary"
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
        runtime={"backend": "cpu_float64_production_plus_fraction_fan_teacher"},
        git=(
            {"available": False, "dirty": None, "commit": None}
            if git is None
            else git
        ),
    )


def run_legal_responder_raise_h4_selector_window(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute ADR-0350 exactly once and retain its first terminal."""

    if os.path.lexists(output_path):
        raise FileExistsError(f"h4 selector result path already exists: {output_path}")
    started = time.perf_counter()
    stage = "config"
    git: Mapping[str, Any] | None = None
    try:
        parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
        stage = "git"
        git = _strict_git_metadata()
        stage = "selector_fan"
        payload = _execute_selector_window(parsed, git=git)
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_selector_window_executed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "methodology": {
                "betting_authority": "NoLimitBettingState",
                "direction_compiler": "selector_free_regret_vertices_and_retained_master",
                "teacher": "fraction_exact_sequence_form_normal_fan",
                "subject": "production_best_response_on_untouched_dyadic_schedule",
                "certificate_identity": "total_function",
                "behavioral_identity": "reachable_support_reporting_only",
                "quality_rows": 0,
                "strategy_labels": 0,
            },
            **payload,
            "strategy_quality_claim": None,
            "limitations": [
                "This is one finite h4 checked-to heads-up river selector map.",
                "Tie-unresolved regions remain unresolved and no tolerance elects a tape.",
                "Reachable-support identity is descriptive; total tapes gate certificates.",
                "The selector wall is laboratory infrastructure, not action-clock latency.",
                "No full-width, multiway, action, strategy-quality, or poker-strength result is emitted.",
            ],
        }
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_selector_window_failed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path) if config_path.is_file() else None,
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "passed": False,
            "decision": "reject_legal_h4_selector_window_boundary",
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
    result = run_legal_responder_raise_h4_selector_window(args.config, args.output)
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
