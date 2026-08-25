"""Prospective legal h4 exact directional-face diagnostic for ADR-0355.

The runner composes ADR-0354's pointwise face oracle with the retained exact
normal fan over four already-frozen one-seat directions and both players.  It
does not import the closed ADR-0352 integration runner, materialize active
response-tape products, emit an action, or claim action-clock feasibility.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
from fractions import Fraction
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping

from .exact_directional_face_oracle import (
    ExactDirectionalFace,
    ExactDirectionalFaceFanSection,
    ExactDirectionalFaceWorkLedger,
    compose_exact_directional_face_fan_section,
    exact_directional_best_response_face,
)
from .exact_directional_face_oracle_seal import ADR0354_PROTOCOL_SHA256
from .game import Action
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
from .runner_harness_v2 import load_config


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-directional-face-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-directional-face-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": _ROOT
    / "docs/decisions/ADR-0354-seal-the-exact-directional-face-oracle.md",
    "expected_parent_source_seal_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle_seal.py",
    "expected_directional_face_oracle_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle.py",
    "expected_tie_conformance_sha256": _ROOT
    / "src/pontius/tie_semantics_conformance.py",
    "expected_directional_face_controls_sha256": _ROOT
    / "tests/test_exact_directional_face_oracle.py",
    "expected_tie_conformance_controls_sha256": _ROOT
    / "tests/test_tie_semantics_conformance.py",
    "expected_source_seal_controls_sha256": _ROOT
    / "tests/test_exact_directional_face_oracle_seal.py",
    "expected_exact_fan_sha256": _ROOT / "src/pontius/exact_selector_fan.py",
    "expected_exact_selector_oracle_sha256": _ROOT
    / "src/pontius/exact_selector_window_oracle.py",
    "expected_exact_sequence_oracle_sha256": _ROOT
    / "src/pontius/exact_sequence_form_coefficient_oracle.py",
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT
    / "src/pontius/legal_river_continuation.py",
    "expected_fixture_sha256": _ROOT / "src/pontius/legal_h4_selector_fixture.py",
    "expected_direction_compiler_sha256": _ROOT
    / "src/pontius/legal_h4_selector_directions.py",
    "expected_cfr_sha256": _ROOT / "src/pontius/cfr.py",
    "expected_generation_primitive_sha256": _ROOT
    / "src/pontius/one_seat_convex_generation.py",
    "expected_parent_result_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_row_growth_result.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_strict_loader_sha256": _ROOT / "src/pontius/runner_harness_v2.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _ROOT
    / "tests/test_legal_responder_raise_h4_directional_face.py",
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
_FAN_STATES = ("fixed", "tie_unresolved", "switched")
_TARGET_OUTCOME_KEYS = (
    "active_cell_rows",
    "composition_face_samples",
    "crossings",
    "face_observations",
    "factor_sha256",
    "fan_cells",
    "fan_points",
    "fan_segments",
    "maximum_gain_slope",
    "maximum_reachable_cardinality_bit_length",
    "maximum_reachable_support_cardinality",
    "maximum_response_slope",
    "maximum_total_cardinality_bit_length",
    "maximum_total_function_cardinality",
    "minimum_gain_slope",
    "minimum_response_slope",
    "profile_utility_slope",
    "reachable_fixed_measure",
    "reachable_switched_measure",
    "reachable_tie_points",
    "reachable_tie_unresolved_measure",
    "total_fixed_measure",
    "total_logical_work_units",
    "total_switched_measure",
    "total_tie_points",
    "total_tie_unresolved_measure",
)


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required legal h4 directional-face input is absent: {path}")
    canonical = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(canonical).hexdigest()


def _canonical_sha256(value: object) -> str:
    rendered = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _strict_git_metadata() -> dict[str, Any]:
    def checked(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"strict Git metadata failed: {message}")
        return result.stdout.strip()

    commit = checked("rev-parse", "HEAD")
    status = checked("status", "--porcelain=v1", "--untracked-files=all")
    return {"commit": commit, "dirty": bool(status), "strict_status": True}


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _parse_config(config: Mapping[str, Any]) -> dict[str, Any]:
    plain = _plain(config)
    expected = {
        "evidence_stage",
        "hash_semantics",
        "expected_parent_protocol_sha256",
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
        "maximum_tree_nodes",
        "maximum_fan_pieces",
        "active_face_representation",
        "face_instrument",
        "ray_instrument",
        "cardinality_columns",
        "cardinality_authority",
        "work_ledger_semantics",
        "analysis_wall_semantics",
        "result_path_lifecycle",
        "claims_policy",
        "gates",
    }
    if set(plain) != expected:
        raise ValueError("legal h4 directional-face config fields differ")
    for field, path in _PATHS.items():
        if plain[field] != _canonical_lf_sha256(path):
            raise ValueError(f"legal h4 directional-face provenance differs: {field}")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0354_before_legal_h4_directional_face_run"
        ),
        "hash_semantics": "canonical_lf_sha256_for_all_bound_text_sources",
        "expected_parent_protocol_sha256": ADR0354_PROTOCOL_SHA256,
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
        "maximum_tree_nodes": 100_000,
        "maximum_fan_pieces": 256,
        "active_face_representation": (
            "factorized_exact_local_maximizer_sets_without_tape_product"
        ),
        "face_instrument": "two_independent_lexicographic_backward_passes",
        "ray_instrument": "exact_sequence_form_normal_fan",
        "cardinality_columns": ["total_function", "reachable_support"],
        "cardinality_authority": (
            "total_function_conservative_reachable_support_descriptive"
        ),
        "work_ledger_semantics": (
            "linear_logical_operations_plus_exact_bigint_bit_lengths"
        ),
        "analysis_wall_semantics": (
            "execute_entry_through_scientific_payload_materialization_"
            "excluding_gate_evaluation_result_render_fsync_and_process_overhead"
        ),
        "result_path_lifecycle": (
            "absent_at_source_commit_exclusive_first_terminal_no_retry"
        ),
        "claims_policy": (
            "finite_legal_h4_directional_face_diagnostic_only_no_action_clock_"
            "full_width_multiway_action_quality_or_strength_claim"
        ),
    }
    for field, expected_value in frozen.items():
        if plain[field] != expected_value:
            raise ValueError(f"legal h4 directional-face field differs: {field}")
    gates = {
        "expected_directions": 4,
        "expected_regret_vertex_directions": 3,
        "expected_lp_proposed_directions": 1,
        "expected_players": 2,
        "expected_sections": 8,
        "expected_schedule_points": 17,
        "expected_schedule_face_calls": 136,
        "maximum_subject_seconds": 180.0,
        "maximum_analysis_seconds": 240.0,
        "maximum_scientific_payload_bytes": 16_777_216,
        "maximum_result_bytes": 33_554_432,
        "require_clean_git_state": True,
        "require_parent_pass": True,
        "require_fixture_identity": True,
        "require_direction_identity": True,
        "require_complete_fan_face_seam": True,
        "require_schedule_fan_face_identity": True,
        "require_legacy_breakpoint_identity": True,
        "require_slope_order": True,
        "require_gain_identity": True,
        "require_two_independent_passes": True,
        "require_dual_cardinality_columns": True,
        "require_zero_materialized_tapes": True,
        "require_linear_logical_work": True,
        "require_exact_bit_lengths": True,
        "require_no_face_cardinality_bound": True,
        "require_no_target_outcome_gate": True,
        "require_finite": True,
    }
    if plain["gates"] != gates:
        raise ValueError("legal h4 directional-face gates differ")
    return {
        **plain,
        "direction_descriptors": tuple(plain["direction_descriptors"]),
        "schedule_numerators": tuple(plain["schedule_numerators"]),
        "cardinality_columns": tuple(plain["cardinality_columns"]),
        "gates": dict(plain["gates"]),
    }


def _direction_descriptor(direction: LegalH4SelectorDirection) -> dict[str, object]:
    return {
        "label": direction.label,
        "direction_class": direction.direction_class,
        "changed_public_histories": list(direction.changed_public_histories),
        "endpoint_policy_sha256": direction.endpoint_policy_sha256,
    }


def _action_token(action: object) -> str:
    return str(action)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _tape_record(tape: tuple[tuple[str, Action], ...]) -> list[dict[str, str]]:
    return [
        {"information_key": key, "action": _action_token(action)}
        for key, action in tape
    ]


def _work_record(work: ExactDirectionalFaceWorkLedger) -> dict[str, int]:
    return {field.name: int(getattr(work, field.name)) for field in fields(work)}


def _face_record(face: ExactDirectionalFace) -> dict[str, object]:
    factors = [
        {
            "information_key": row.key,
            "actions": [_action_token(action) for action in row.actions],
            "parent": (
                None
                if row.parent is None
                else {
                    "information_key": row.parent[0],
                    "action": _action_token(row.parent[1]),
                }
            ),
            "maximizing_actions": [
                _action_token(action) for action in row.maximizing_actions
            ],
            "positive_counterfactual_support": (
                row.positive_counterfactual_support
            ),
            "minimum_slope_action": _action_token(row.minimum_slope_action),
            "maximum_slope_action": _action_token(row.maximum_slope_action),
            "minimum_local_slope": _fraction_record(row.minimum_local_slope),
            "maximum_local_slope": _fraction_record(row.maximum_local_slope),
            "state_count": row.state_count,
        }
        for row in face.information_sets
    ]
    record: dict[str, object] = {
        "acting_player": face.acting_player,
        "target_player": face.target_player,
        "scale": _fraction_record(face.scale),
        "response_value": _fraction_record(face.response_value),
        "profile_utility": _fraction_record(face.profile_utility),
        "deviation_gain": _fraction_record(face.deviation_gain),
        "minimum_response_slope": _fraction_record(face.minimum_response_slope),
        "maximum_response_slope": _fraction_record(face.maximum_response_slope),
        "profile_utility_slope": _fraction_record(face.profile_utility_slope),
        "minimum_gain_slope": _fraction_record(face.minimum_gain_slope),
        "maximum_gain_slope": _fraction_record(face.maximum_gain_slope),
        "minimum_slope_tape": _tape_record(face.minimum_slope_tape),
        "maximum_slope_tape": _tape_record(face.maximum_slope_tape),
        "total_function_cardinality": face.total_function_cardinality,
        "reachable_support_cardinality": face.reachable_support_cardinality,
        "information_sets": factors,
        "work": _work_record(face.work),
    }
    record["factor_sha256"] = _canonical_sha256(
        {
            "total_function_cardinality": face.total_function_cardinality,
            "reachable_support_cardinality": face.reachable_support_cardinality,
            "information_sets": factors,
        }
    )
    return record


def _fan_record(section: ExactDirectionalFaceFanSection) -> dict[str, object]:
    fan = section.fan
    record: dict[str, object] = {
        "acting_player": fan.acting_player,
        "target_player": fan.target_player,
        "source_tape": _tape_record(fan.source_tape),
        "source_cell_upper": _fraction_record(fan.source_cell_upper),
        "legacy_source_breakpoint": _fraction_record(
            fan.legacy_source_breakpoint
        ),
        "cells": [
            {
                "response_tape": _tape_record(row.response_tape),
                "lower": _fraction_record(row.lower),
                "upper": _fraction_record(row.upper),
            }
            for row in fan.cells
        ],
        "segments": [
            {
                "lower": _fraction_record(row.lower),
                "upper": _fraction_record(row.upper),
                "witness": _fraction_record(row.witness),
                "response_tape": _tape_record(row.response_tape),
                "reachable_tape": _tape_record(row.reachable_tape),
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "total_tie_information_sets": list(
                    row.total_tie_information_sets
                ),
                "reachable_tie_information_sets": list(
                    row.reachable_tie_information_sets
                ),
            }
            for row in fan.segments
        ],
        "points": [
            {
                "scale": _fraction_record(row.scale),
                "response_tape": _tape_record(row.response_tape),
                "reachable_tape": _tape_record(row.reachable_tape),
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "total_tie_information_sets": list(
                    row.total_tie_information_sets
                ),
                "reachable_tie_information_sets": list(
                    row.reachable_tie_information_sets
                ),
            }
            for row in fan.points
        ],
        "measures": {
            "total_fixed": _fraction_record(fan.total_fixed_measure),
            "total_tie_unresolved": _fraction_record(
                fan.total_tie_unresolved_measure
            ),
            "total_switched": _fraction_record(fan.total_switched_measure),
            "reachable_fixed": _fraction_record(fan.reachable_fixed_measure),
            "reachable_tie_unresolved": _fraction_record(
                fan.reachable_tie_unresolved_measure
            ),
            "reachable_switched": _fraction_record(
                fan.reachable_switched_measure
            ),
        },
        "total_tie_points": [
            _fraction_record(scale) for scale in fan.total_tie_points
        ],
        "reachable_tie_points": [
            _fraction_record(scale) for scale in fan.reachable_tie_points
        ],
    }
    record["fan_sha256"] = _canonical_sha256(record)
    return record


def _section_record(section: ExactDirectionalFaceFanSection) -> dict[str, object]:
    record: dict[str, object] = {
        "fan": _fan_record(section),
        "cell_gain_rows": [
            {
                "response_tape": _tape_record(row.response_tape),
                "lower": _fraction_record(row.lower),
                "upper": _fraction_record(row.upper),
                "intercept": _fraction_record(row.intercept),
                "slope": _fraction_record(row.slope),
            }
            for row in section.cell_rows
        ],
        "samples": [
            {
                "scale": _fraction_record(row.scale),
                "sample_kind": row.sample_kind,
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "maximum_cell_gain": _fraction_record(row.maximum_cell_gain),
                "active_cell_rows": row.active_cell_rows,
                "face": _face_record(row.face),
            }
            for row in section.samples
        ],
        "crossing_scales": [
            _fraction_record(scale) for scale in section.crossing_scales
        ],
    }
    record["section_sha256"] = _canonical_sha256(record)
    return record


def _fan_location_at_scale(
    section: ExactDirectionalFaceFanSection,
    scale: Fraction,
) -> Any:
    point = next((row for row in section.fan.points if row.scale == scale), None)
    if point is not None:
        return point
    return next(
        row for row in section.fan.segments if row.lower < scale < row.upper
    )


def _reachable_face_tape(
    face: ExactDirectionalFace,
    tape: tuple[tuple[str, Action], ...],
) -> tuple[tuple[str, Action], ...]:
    selected = dict(tape)
    if set(selected) != {row.key for row in face.information_sets}:
        raise ArithmeticError("directional-face tape schema differs from factors")
    reached: dict[str, Action] = {}
    for row in face.information_sets:
        if not row.positive_counterfactual_support:
            continue
        if row.parent is not None and reached.get(row.parent[0]) != row.parent[1]:
            continue
        reached[row.key] = selected[row.key]
    return tuple(sorted(reached.items()))


def _face_invariants(face: ExactDirectionalFace) -> dict[str, bool]:
    factor_product = 1
    for row in face.information_sets:
        factor_product *= len(row.maximizing_actions)
    work = face.work
    cardinality_work = (
        work.total_cardinality_multiplications
        + work.reachable_cardinality_additions
        + work.reachable_cardinality_multiplications
    )
    per_pass = work.per_pass_linear_work_ceiling
    return {
        "slope_order": (
            face.minimum_response_slope <= face.maximum_response_slope
            and face.minimum_gain_slope <= face.maximum_gain_slope
        ),
        "gain_identity": (
            face.deviation_gain == face.response_value - face.profile_utility
            and face.minimum_gain_slope
            == face.minimum_response_slope - face.profile_utility_slope
            and face.maximum_gain_slope
            == face.maximum_response_slope - face.profile_utility_slope
        ),
        "total_cardinality_identity": (
            factor_product == face.total_function_cardinality
        ),
        "reachable_cardinality_order": (
            1
            <= face.reachable_support_cardinality
            <= face.total_function_cardinality
        ),
        "two_independent_passes": work.lexicographic_passes == 2,
        "zero_materialized_tapes": work.materialized_response_tapes == 0,
        "linear_pass_work": (
            work.minimum_continuation_node_evaluations
            + work.minimum_action_score_terms
            + work.minimum_action_choice_inspections
            == per_pass
            and work.maximum_continuation_node_evaluations
            + work.maximum_action_score_terms
            + work.maximum_action_choice_inspections
            == per_pass
        ),
        "linear_cardinality_work": (
            cardinality_work <= work.cardinality_linear_work_ceiling
            and work.total_logical_work_units == 2 * per_pass + cardinality_work
        ),
        "exact_bit_lengths": (
            work.total_cardinality_bit_length
            == face.total_function_cardinality.bit_length()
            and work.reachable_cardinality_bit_length
            == face.reachable_support_cardinality.bit_length()
        ),
    }


def _audit_section(
    game: Any,
    source: Mapping[str, Mapping[Action, float]],
    direction: LegalH4SelectorDirection,
    *,
    target_player: int,
    parsed: Mapping[str, Any],
) -> tuple[dict[str, object], dict[str, Any]]:
    started = time.perf_counter()
    section = compose_exact_directional_face_fan_section(
        game,
        source,
        direction.endpoint_policy,
        acting_player=int(parsed["acting_player"]),
        target_player=target_player,
        maximum_fan_tapes=int(parsed["maximum_fan_pieces"]),
        maximum_tree_nodes=int(parsed["maximum_tree_nodes"]),
    )
    all_faces = [sample.face for sample in section.samples]
    schedule_rows = []
    schedule_identity = True
    for numerator in parsed["schedule_numerators"]:
        scale = Fraction(int(numerator), int(parsed["schedule_denominator"]))
        face = exact_directional_best_response_face(
            game,
            source,
            direction.endpoint_policy,
            acting_player=int(parsed["acting_player"]),
            target_player=target_player,
            scale=scale,
            maximum_tree_nodes=int(parsed["maximum_tree_nodes"]),
        )
        location = _fan_location_at_scale(section, scale)
        total_state = location.total_state
        reachable_state = location.reachable_state
        maximizing = {
            row.key: set(row.maximizing_actions)
            for row in face.information_sets
        }
        location_is_face_member = (
            set(dict(location.response_tape)) == set(maximizing)
            and all(
                action in maximizing[key]
                for key, action in location.response_tape
            )
        )
        minimum_reachable = _reachable_face_tape(
            face,
            face.minimum_slope_tape,
        )
        maximum_reachable = _reachable_face_tape(
            face,
            face.maximum_slope_tape,
        )
        total_identity = (
            face.total_function_cardinality > 1
            if total_state == "tie_unresolved"
            else (
                face.total_function_cardinality == 1
                and face.minimum_slope_tape
                == face.maximum_slope_tape
                == location.response_tape
            )
        )
        reachable_identity = (
            face.reachable_support_cardinality > 1
            if reachable_state == "tie_unresolved"
            else (
                face.reachable_support_cardinality == 1
                and minimum_reachable
                == maximum_reachable
                == location.reachable_tape
            )
        )
        schedule_identity = bool(
            schedule_identity
            and location_is_face_member
            and total_identity
            and reachable_identity
        )
        schedule_rows.append(
            {
                "scale": _fraction_record(scale),
                "total_state": total_state,
                "reachable_state": reachable_state,
                "face": _face_record(face),
            }
        )
        all_faces.append(face)
    invariants = [_face_invariants(face) for face in all_faces]
    checks = {
        key: all(row[key] for row in invariants) for key in invariants[0]
    }
    checks["schedule_fan_face_identity"] = schedule_identity
    checks["legacy_breakpoint_identity"] = (
        section.fan.source_cell_upper == section.fan.legacy_source_breakpoint
    )
    record = {
        "target_player": target_player,
        "composed_section": _section_record(section),
        "schedule": schedule_rows,
        "checks": checks,
    }
    metrics = {
        "subject_seconds": time.perf_counter() - started,
        "composition_face_samples": len(section.samples),
        "schedule_face_calls": len(schedule_rows),
        "face_observations": len(all_faces),
        "fan_cells": len(section.fan.cells),
        "fan_segments": len(section.fan.segments),
        "fan_points": len(section.fan.points),
        "crossings": len(section.crossing_scales),
        "maximum_total_function_cardinality": max(
            face.total_function_cardinality for face in all_faces
        ),
        "maximum_reachable_support_cardinality": max(
            face.reachable_support_cardinality for face in all_faces
        ),
        "maximum_total_cardinality_bit_length": max(
            face.work.total_cardinality_bit_length for face in all_faces
        ),
        "maximum_reachable_cardinality_bit_length": max(
            face.work.reachable_cardinality_bit_length for face in all_faces
        ),
        "maximum_tree_nodes": max(face.work.tree_nodes for face in all_faces),
        "total_logical_work_units": sum(
            face.work.total_logical_work_units for face in all_faces
        ),
        "materialized_response_tapes": sum(
            face.work.materialized_response_tapes for face in all_faces
        ),
        "checks": checks,
    }
    return record, metrics


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _execute_directional_face(
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
    )
    descriptors = tuple(_direction_descriptor(row) for row in directions)
    direction_rows = []
    metrics_rows = []
    subject_started = time.perf_counter()
    for direction in directions:
        targets = []
        for target_player in range(game.num_players):
            row, metrics = _audit_section(
                game,
                source,
                direction,
                target_player=target_player,
                parsed=parsed,
            )
            targets.append(row)
            metrics_rows.append(metrics)
            if (
                time.perf_counter() - subject_started
                > parsed["gates"]["maximum_subject_seconds"]
            ):
                raise RuntimeError(
                    "legal h4 directional-face subject wall exceeded"
                )
        direction_rows.append(
            {
                **_direction_descriptor(direction),
                "target_rows": targets,
            }
        )
    subject_seconds = time.perf_counter() - subject_started
    aggregate_checks = {
        key: all(row["checks"][key] for row in metrics_rows)
        for key in metrics_rows[0]["checks"]
    }
    aggregate = {
        "sections": len(metrics_rows),
        "schedule_face_calls": sum(
            row["schedule_face_calls"] for row in metrics_rows
        ),
        "composition_face_samples": sum(
            row["composition_face_samples"] for row in metrics_rows
        ),
        "face_observations": sum(row["face_observations"] for row in metrics_rows),
        "fan_cells": sum(row["fan_cells"] for row in metrics_rows),
        "fan_segments": sum(row["fan_segments"] for row in metrics_rows),
        "fan_points": sum(row["fan_points"] for row in metrics_rows),
        "crossings": sum(row["crossings"] for row in metrics_rows),
        "maximum_total_function_cardinality": max(
            row["maximum_total_function_cardinality"] for row in metrics_rows
        ),
        "maximum_reachable_support_cardinality": max(
            row["maximum_reachable_support_cardinality"] for row in metrics_rows
        ),
        "maximum_total_cardinality_bit_length": max(
            row["maximum_total_cardinality_bit_length"] for row in metrics_rows
        ),
        "maximum_reachable_cardinality_bit_length": max(
            row["maximum_reachable_cardinality_bit_length"] for row in metrics_rows
        ),
        "maximum_tree_nodes": max(row["maximum_tree_nodes"] for row in metrics_rows),
        "total_logical_work_units": sum(
            row["total_logical_work_units"] for row in metrics_rows
        ),
        "materialized_response_tapes": sum(
            row["materialized_response_tapes"] for row in metrics_rows
        ),
        "subject_seconds": subject_seconds,
        "checks": aggregate_checks,
    }
    scientific_payload = {
        "directions": direction_rows,
        "aggregate": aggregate,
    }
    scientific_bytes = len(
        json.dumps(
            scientific_payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    analysis_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    fixture_identity = (
        public_betting_state_sha256(game.base_state)
        == parsed["expected_root_public_state_sha256"]
        and parent.record["public_schema_sha256"]
        == parsed["expected_public_schema_sha256"]
        and game.structural_digest == parsed["expected_game_structural_sha256"]
        and game.provenance_digest == parsed["expected_game_provenance_sha256"]
        and policy_sha256(source) == parsed["expected_source_policy_sha256"]
    )
    direction_identity = (
        descriptors == parsed["direction_descriptors"]
        and len(directions) == gates["expected_directions"]
        and sum(
            row.direction_class == "one_step_dcfr_regret_vertex"
            for row in directions
        )
        == gates["expected_regret_vertex_directions"]
        and sum(
            row.direction_class == "retained_restricted_master_proposal"
            for row in directions
        )
        == gates["expected_lp_proposed_directions"]
    )
    checks = {
        "clean_git_state": (not bool(git["dirty"]))
        == gates["require_clean_git_state"],
        "parent_pass": bool(parent.record["passed"])
        == gates["require_parent_pass"],
        "fixture_identity": fixture_identity
        == gates["require_fixture_identity"],
        "direction_identity": direction_identity
        == gates["require_direction_identity"],
        "complete_fan_face_seam": (
            aggregate["sections"] == gates["expected_sections"]
            and aggregate["composition_face_samples"] > 0
        )
        == gates["require_complete_fan_face_seam"],
        "schedule_fan_face_identity": (
            aggregate["schedule_face_calls"]
            == gates["expected_schedule_face_calls"]
            == gates["expected_directions"]
            * gates["expected_players"]
            * gates["expected_schedule_points"]
            and aggregate_checks["schedule_fan_face_identity"]
        )
        == gates["require_schedule_fan_face_identity"],
        "legacy_breakpoint_identity": aggregate_checks[
            "legacy_breakpoint_identity"
        ]
        == gates["require_legacy_breakpoint_identity"],
        "slope_order": aggregate_checks["slope_order"]
        == gates["require_slope_order"],
        "gain_identity": aggregate_checks["gain_identity"]
        == gates["require_gain_identity"],
        "two_independent_passes": aggregate_checks["two_independent_passes"]
        == gates["require_two_independent_passes"],
        "dual_cardinality_columns": (
            aggregate_checks["total_cardinality_identity"]
            and aggregate_checks["reachable_cardinality_order"]
            and tuple(parsed["cardinality_columns"])
            == ("total_function", "reachable_support")
        )
        == gates["require_dual_cardinality_columns"],
        "zero_materialized_tapes": (
            aggregate["materialized_response_tapes"] == 0
            and aggregate_checks["zero_materialized_tapes"]
        )
        == gates["require_zero_materialized_tapes"],
        "linear_logical_work": (
            aggregate_checks["linear_pass_work"]
            and aggregate_checks["linear_cardinality_work"]
        )
        == gates["require_linear_logical_work"],
        "exact_bit_lengths": aggregate_checks["exact_bit_lengths"]
        == gates["require_exact_bit_lengths"],
        "no_face_cardinality_bound": (
            "maximum_face_tapes" not in parsed
            and "maximum_face_cardinality" not in parsed
        )
        == gates["require_no_face_cardinality_bound"],
        "no_target_outcome_gate": all(
            key not in parsed
            and f"expected_{key}" not in parsed
            and key not in gates
            and f"expected_{key}" not in gates
            for key in _TARGET_OUTCOME_KEYS
        )
        == gates["require_no_target_outcome_gate"],
        "subject_wall": subject_seconds <= gates["maximum_subject_seconds"],
        "scientific_payload_bytes": scientific_bytes
        <= gates["maximum_scientific_payload_bytes"],
        "analysis_wall": analysis_seconds <= gates["maximum_analysis_seconds"],
    }
    payload: dict[str, Any] = {
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
        "face_semantics": {
            "active_face_representation": parsed["active_face_representation"],
            "face_instrument": parsed["face_instrument"],
            "ray_instrument": parsed["ray_instrument"],
            "cardinality_columns": list(parsed["cardinality_columns"]),
            "cardinality_authority": parsed["cardinality_authority"],
            "work_ledger_semantics": parsed["work_ledger_semantics"],
            "maximum_tree_nodes": parsed["maximum_tree_nodes"],
            "maximum_fan_pieces": parsed["maximum_fan_pieces"],
            "face_cardinality_bound": None,
        },
        **scientific_payload,
        "scientific_payload_bytes": scientific_bytes,
        "analysis_seconds": analysis_seconds,
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    result = finalize_gates(checks)
    return {
        **payload,
        **result,
        "decision": (
            "authorize_legal_h4_directional_face_integration_preregistration"
            if result["passed"]
            else "reject_legal_h4_directional_face_boundary"
        ),
    }


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o644)
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
        runtime={"backend": "cpu_fraction_exact_fan_plus_directional_face"},
        git=(
            {"available": False, "dirty": None, "commit": None}
            if git is None
            else git
        ),
    )


def run_legal_responder_raise_h4_directional_face(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute ADR-0355 once and retain pass, rejection, or typed failure."""

    if os.path.lexists(output_path):
        raise FileExistsError(
            f"legal h4 directional-face result path exists: {output_path}"
        )
    started = time.perf_counter()
    stage = "config"
    git: Mapping[str, Any] | None = None
    loaded = None
    parsed: Mapping[str, Any] | None = None
    try:
        loaded = load_config(
            config_path,
            schema_validator=lambda payload: _parse_config(payload),
            maximum_bytes=262_144,
        )
        parsed = _parse_config(loaded.payload)
        stage = "git"
        git = _strict_git_metadata()
        if parsed["gates"]["require_clean_git_state"] and git["dirty"]:
            raise RuntimeError(
                "legal h4 directional-face invocation requires a clean commit"
            )
        stage = "directional_face"
        payload = _execute_directional_face(parsed, git=git)
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_directional_face_executed",
            "environment": _environment(git),
            "config_sha256": loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0354_PROTOCOL_SHA256,
            "methodology": {
                "betting_authority": "NoLimitBettingState",
                "direction_source": (
                    "three_regret_vertices_plus_retained_restricted_master"
                ),
                "ray_teacher": "fraction_exact_sequence_form_normal_fan",
                "face_teacher": (
                    "two_fraction_exact_lexicographic_backward_passes"
                ),
                "active_face_materialization": "none",
                "quality_rows": 0,
                "strategy_labels": 0,
            },
            **payload,
            "strategy_quality_claim": None,
            "limitations": [
                "This is one finite h4 checked-to heads-up river diagnostic.",
                "Cardinality, slope, crossing, and tie observations are outcomes.",
                "The fan-piece bound is not an active-face-cardinality bound.",
                "Infrastructure walls are not 15-second action-clock latency.",
                "No full-width, multiway, action, quality, or strength result exists.",
            ],
        }
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_directional_face_failed",
            "environment": _environment(git),
            "config_sha256": None if loaded is None else loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0354_PROTOCOL_SHA256,
            "passed": False,
            "decision": "reject_legal_h4_directional_face_boundary",
            "failure": {
                "stage": stage,
                "type": type(error).__name__,
                "message": str(error),
            },
            "runner_elapsed_seconds": time.perf_counter() - started,
            "strategy_quality_claim": None,
        }
    rendered = serialize_result(result)
    maximum_result_bytes = (
        33_554_432
        if parsed is None
        else int(parsed["gates"]["maximum_result_bytes"])
    )
    if len(rendered.encode("utf-8")) > maximum_result_bytes:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_directional_face_failed",
            "environment": _environment(git),
            "config_sha256": None if loaded is None else loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0354_PROTOCOL_SHA256,
            "passed": False,
            "decision": "reject_legal_h4_directional_face_boundary",
            "failure": {
                "stage": "serialization",
                "type": "RuntimeError",
                "message": "legal h4 directional-face result exceeds byte bound",
            },
            "runner_elapsed_seconds": time.perf_counter() - started,
            "strategy_quality_claim": None,
        }
        rendered = serialize_result(result)
    _write_exclusive(output_path, rendered)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_legal_responder_raise_h4_directional_face(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "elapsed_seconds": result.get(
                    "analysis_seconds",
                    result.get("runner_elapsed_seconds"),
                ),
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
