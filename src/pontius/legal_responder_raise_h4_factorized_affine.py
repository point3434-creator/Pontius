"""Prospective one-shot legal h4 factorized affine integration for ADR-0358.

The exact normal fan owns each complete ray and the two-pass factorized face
owns each point.  Exact source ties enter the factorized maximum envelope;
exact singleton sources alone invoke selector-window v2.  The owner never
materializes a Cartesian response-tape product and never emits an action.
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
)
from .factorized_tie_aware_affine import (
    FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
    FAIL_CLOSED_SINGLE_TAPE,
    V2_SINGLE_TAPE,
    ExactFactorizedTieAwareAffineSection,
    build_factorized_tie_aware_affine_section,
)
from .factorized_tie_aware_affine_seal import ADR0357_PROTOCOL_SHA256
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
from .legal_responder_raise_h4_directional_face_result import (
    ADR0356_ARTIFACT_BYTES,
    ADR0356_ARTIFACT_SHA256,
    ADR0356_RESULT_PROTOCOL_SHA256,
    verify_adr0356_legal_h4_directional_face_result_artifact,
)
from .legal_responder_raise_h4_row_growth_result import (
    verify_adr0349_legal_h4_row_growth_result_artifact,
)
from .runner_harness import assemble_environment, finalize_gates, serialize_result
from .runner_harness_v2 import load_config


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-factorized-affine-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-factorized-affine-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": _ROOT
    / "docs/decisions/ADR-0357-seal-the-factorized-tie-aware-affine-integration.md",
    "expected_parent_source_seal_sha256": _ROOT
    / "src/pontius/factorized_tie_aware_affine_seal.py",
    "expected_factorized_affine_sha256": _ROOT
    / "src/pontius/factorized_tie_aware_affine.py",
    "expected_tie_conformance_v2_sha256": _ROOT
    / "src/pontius/tie_semantics_conformance_v2.py",
    "expected_factorized_affine_controls_sha256": _ROOT
    / "tests/test_factorized_tie_aware_affine.py",
    "expected_tie_conformance_v2_controls_sha256": _ROOT
    / "tests/test_tie_semantics_conformance_v2.py",
    "expected_factorized_source_seal_controls_sha256": _ROOT
    / "tests/test_factorized_tie_aware_affine_seal.py",
    "expected_directional_face_oracle_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle.py",
    "expected_directional_face_source_seal_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle_seal.py",
    "expected_exact_fan_sha256": _ROOT / "src/pontius/exact_selector_fan.py",
    "expected_exact_selector_oracle_sha256": _ROOT
    / "src/pontius/exact_selector_window_oracle.py",
    "expected_exact_sequence_oracle_sha256": _ROOT
    / "src/pontius/exact_sequence_form_coefficient_oracle.py",
    "expected_selector_window_sha256": _ROOT / "src/pontius/selector_window.py",
    "expected_selector_window_v2_sha256": _ROOT
    / "src/pontius/selector_window_v2.py",
    "expected_evaluation_sha256": _ROOT / "src/pontius/evaluation.py",
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT
    / "src/pontius/legal_river_continuation.py",
    "expected_fixture_sha256": _ROOT / "src/pontius/legal_h4_selector_fixture.py",
    "expected_direction_compiler_sha256": _ROOT
    / "src/pontius/legal_h4_selector_directions.py",
    "expected_cfr_sha256": _ROOT / "src/pontius/cfr.py",
    "expected_generation_primitive_sha256": _ROOT
    / "src/pontius/one_seat_convex_generation.py",
    "expected_row_growth_result_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_row_growth_result.py",
    "expected_parent_result_owner_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_directional_face_result.py",
    "expected_parent_result_owner_seal_sha256": _ROOT
    / "src/pontius/legal_responder_raise_h4_directional_face_result_seal.py",
    "expected_parent_result_controls_sha256": _ROOT
    / "tests/test_legal_responder_raise_h4_directional_face_result.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_strict_loader_sha256": _ROOT / "src/pontius/runner_harness_v2.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _ROOT
    / "tests/test_legal_responder_raise_h4_factorized_affine.py",
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
_TARGET_OUTCOME_KEYS = frozenset(
    {
        "exact_source_ties",
        "fail_closed_singletons",
        "factorized_modes",
        "maximum_reachable_support_cardinality",
        "maximum_total_function_cardinality",
        "mode_counts",
        "piece_counts",
        "selector_window_scale_limits",
        "subject_seconds",
        "v2_singletons",
    }
)


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required legal h4 factorized-affine input is absent: {path}")
    canonical = path.read_bytes().replace(bytes((13, 10)), bytes((10,)))
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
        "expected_parent_result_protocol_sha256",
        "expected_parent_artifact_sha256",
        "expected_parent_artifact_bytes",
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
        "selector_margin_allowance",
        "maximum_tree_nodes",
        "maximum_fan_pieces",
        "source_tie_mode",
        "singleton_positive_mode",
        "singleton_closed_mode",
        "ray_authority",
        "point_authority",
        "epigraph_orientation",
        "cardinality_columns",
        "cardinality_authority",
        "analysis_wall_semantics",
        "subject_wall_semantics",
        "result_path_lifecycle",
        "claims_policy",
        "gates",
    }
    if set(plain) != expected:
        raise ValueError("legal h4 factorized-affine config fields differ")
    for field, path in _PATHS.items():
        if plain[field] != _canonical_lf_sha256(path):
            raise ValueError(f"legal h4 factorized-affine provenance differs: {field}")

    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0357_before_legal_h4_factorized_affine_run"
        ),
        "hash_semantics": "canonical_lf_sha256_for_all_bound_text_sources",
        "expected_parent_protocol_sha256": ADR0357_PROTOCOL_SHA256,
        "expected_parent_result_protocol_sha256": ADR0356_RESULT_PROTOCOL_SHA256,
        "expected_parent_artifact_sha256": ADR0356_ARTIFACT_SHA256,
        "expected_parent_artifact_bytes": ADR0356_ARTIFACT_BYTES,
        "board": list(BOARD),
        "root_hands": [list(hand) for hand in ROOT_HANDS],
        "responder_hands": [list(hand) for hand in RESPONDER_HANDS],
        "joint_weight_numerators": [
            list(row) for row in JOINT_WEIGHT_NUMERATORS
        ],
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
        "selector_margin_allowance": 1e-12,
        "maximum_tree_nodes": 100_000,
        "maximum_fan_pieces": 256,
        "source_tie_mode": FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
        "singleton_positive_mode": V2_SINGLE_TAPE,
        "singleton_closed_mode": FAIL_CLOSED_SINGLE_TAPE,
        "ray_authority": "exact_selector_normal_fan",
        "point_authority": "two_pass_factorized_directional_face",
        "epigraph_orientation": "z_greater_than_or_equal_to_every_row",
        "cardinality_columns": ["total_function", "reachable_support"],
        "cardinality_authority": (
            "total_function_conservative_reachable_support_reporting_only"
        ),
        "analysis_wall_semantics": (
            "execute_entry_through_scientific_payload_materialization_"
            "excluding_gate_evaluation_result_render_fsync_and_process_overhead"
        ),
        "subject_wall_semantics": (
            "eight_live_factorized_integration_builds_only_excluding_parent_rebind_"
            "fixture_direction_compilation_gate_evaluation_and_serialization"
        ),
        "result_path_lifecycle": (
            "absent_at_source_commit_exclusive_first_terminal_no_retry_no_overwrite"
        ),
        "claims_policy": (
            "finite_same_fixture_legal_h4_development_integration_only_no_untouched_"
            "confirmation_action_clock_full_width_multiway_quality_or_strength_claim"
        ),
    }
    for field, value in frozen.items():
        if plain[field] != value:
            raise ValueError(f"legal h4 factorized-affine field differs: {field}")

    expected_gates = {
        "expected_directions": 4,
        "expected_regret_vertex_directions": 3,
        "expected_lp_proposed_directions": 1,
        "expected_players": 2,
        "expected_sections": 8,
        "maximum_subject_seconds": 180.0,
        "maximum_analysis_seconds": 240.0,
        "maximum_parent_rebind_seconds": 10.0,
        "maximum_scientific_payload_bytes": 4_194_304,
        "maximum_result_bytes": 8_388_608,
        "require_clean_git_state": True,
        "require_parent_pass": True,
        "require_parent_artifact_identity": True,
        "require_fixture_identity": True,
        "require_direction_identity": True,
        "require_section_identity": True,
        "require_parent_section_identity": True,
        "require_typed_source_dispatch": True,
        "require_complete_exact_envelope": True,
        "require_epigraph_orientation": True,
        "require_dual_cardinality_columns": True,
        "require_zero_materialized_tapes": True,
        "require_integration_work_identity": True,
        "require_no_face_cardinality_bound": True,
        "require_no_target_outcome_gate": True,
        "require_zero_actions_and_quality_rows": True,
        "require_finite": True,
    }
    if plain["gates"] != expected_gates:
        raise ValueError("legal h4 factorized-affine gates differ")
    if set(plain["gates"]) & _TARGET_OUTCOME_KEYS:
        raise ValueError("legal h4 factorized-affine outcome entered its gates")
    return {
        **plain,
        "direction_descriptors": tuple(plain["direction_descriptors"]),
        "cardinality_columns": tuple(plain["cardinality_columns"]),
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
            "positive_counterfactual_support": row.positive_counterfactual_support,
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
        "legacy_source_breakpoint": _fraction_record(fan.legacy_source_breakpoint),
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
                "response_tape": _tape_record(row.response_tape),
                "reachable_tape": _tape_record(row.reachable_tape),
                "total_state": row.total_state,
                "reachable_state": row.reachable_state,
                "total_tie_information_sets": list(row.total_tie_information_sets),
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
            "reachable_switched": _fraction_record(fan.reachable_switched_measure),
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


def _window_record(result: ExactFactorizedTieAwareAffineSection) -> object:
    window = result.single_tape_window
    if window is None:
        return None
    return {
        "scale_limit": window.scale_limit,
        "scale_limit_hex": window.scale_limit.hex(),
        "first_switch_information_key": window.first_switch_information_key,
        "first_switch_source_action": (
            None
            if window.first_switch_source_action is None
            else _action_token(window.first_switch_source_action)
        ),
        "first_switch_competing_action": (
            None
            if window.first_switch_competing_action is None
            else _action_token(window.first_switch_competing_action)
        ),
        "selector_comparisons": window.selector_comparisons,
        "exact_source_action_ties": window.exact_source_action_ties,
    }


def _integration_record(
    result: ExactFactorizedTieAwareAffineSection,
    *,
    parent_section_sha256: str,
) -> dict[str, object]:
    section = result.section
    reproduced = _section_record(section)
    source_face = _face_record(result.source_face)
    record: dict[str, object] = {
        "acting_player": result.source_face.acting_player,
        "target_player": result.source_face.target_player,
        "mode": result.mode,
        "parent_section_sha256": parent_section_sha256,
        "reproduced_section_sha256": reproduced["section_sha256"],
        "parent_section_identity": (
            reproduced["section_sha256"] == parent_section_sha256
        ),
        "source_face": source_face,
        "source_cell_upper": _fraction_record(section.fan.source_cell_upper),
        "legacy_source_breakpoint": _fraction_record(
            section.fan.legacy_source_breakpoint
        ),
        "crossing_scales": [
            _fraction_record(scale) for scale in section.crossing_scales
        ],
        "fan_counts": {
            "cells": len(section.fan.cells),
            "segments": len(section.fan.segments),
            "boundaries": len(section.fan.points),
            "point_face_observations": len(section.samples),
        },
        "pieces": [
            {
                "lower": _fraction_record(piece.lower),
                "upper": _fraction_record(piece.upper),
                "witness": _fraction_record(piece.witness),
                "response_tape": _tape_record(piece.response_tape),
                "intercept": _fraction_record(piece.intercept),
                "slope": _fraction_record(piece.slope),
                "total_state": piece.total_state,
                "reachable_state": piece.reachable_state,
                "total_function_cardinality": piece.total_function_cardinality,
                "reachable_support_cardinality": (
                    piece.reachable_support_cardinality
                ),
            }
            for piece in result.pieces
        ],
        "point_summary": [
            {
                "scale": _fraction_record(sample.scale),
                "sample_kind": sample.sample_kind,
                "total_state": sample.total_state,
                "reachable_state": sample.reachable_state,
                "deviation_gain": _fraction_record(sample.face.deviation_gain),
                "minimum_gain_slope": _fraction_record(
                    sample.face.minimum_gain_slope
                ),
                "maximum_gain_slope": _fraction_record(
                    sample.face.maximum_gain_slope
                ),
                "total_function_cardinality": (
                    sample.face.total_function_cardinality
                ),
                "reachable_support_cardinality": (
                    sample.face.reachable_support_cardinality
                ),
                "active_cell_rows": sample.active_cell_rows,
                "factor_sha256": _face_record(sample.face)["factor_sha256"],
            }
            for sample in section.samples
        ],
        "single_tape_window": _window_record(result),
        "exact_envelope_domain": [
            _fraction_record(scale) for scale in result.exact_envelope_domain
        ],
        "certificate_identity_authority": result.certificate_identity_authority,
        "reachable_identity_role": result.reachable_identity_role,
        "ray_authority": result.ray_authority,
        "point_authority": result.point_authority,
        "epigraph_orientation": result.epigraph_orientation,
        "work": {
            field.name: int(getattr(result.work, field.name))
            for field in fields(result.work)
        },
    }
    record["integration_sha256"] = _canonical_sha256(record)
    return record


def _integration_checks(
    record: Mapping[str, Any],
    *,
    expected_acting_player: int,
    expected_target_player: int,
) -> dict[str, bool]:
    source = record["source_face"]
    source_work = source["work"]
    total = int(source["total_function_cardinality"])
    mode = str(record["mode"])
    window = record["single_tape_window"]
    work = record["work"]
    singleton_window_mode = False
    if isinstance(window, Mapping):
        scale_limit = float(window["scale_limit"])
        singleton_window_mode = (
            isfinite(scale_limit)
            and 0.0 <= scale_limit <= 1.0
            and float.fromhex(str(window["scale_limit_hex"])) == scale_limit
            and (
                (scale_limit > 0.0 and mode == V2_SINGLE_TAPE)
                or (scale_limit == 0.0 and mode == FAIL_CLOSED_SINGLE_TAPE)
            )
        )
    typed_dispatch = (
        (
            total > 1
            and mode == FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE
            and window is None
            and work["selector_window_v2_calls"] == 0
            and work["float_selector_score_calls"] == 0
        )
        or (
            total == 1
            and isinstance(window, Mapping)
            and singleton_window_mode
            and work["selector_window_v2_calls"] == 1
            and work["float_selector_score_calls"] == 2
        )
    )
    pieces = record["pieces"]
    piece_coverage = bool(pieces) and pieces[0]["lower"] == {
        "numerator": 0,
        "denominator": 1,
    } and pieces[-1]["upper"] == {"numerator": 1, "denominator": 1}
    return {
        "section_identity": (
            record["acting_player"] == expected_acting_player
            and record["target_player"] == expected_target_player
            and source["acting_player"] == expected_acting_player
            and source["target_player"] == expected_target_player
            and source["scale"] == {"numerator": 0, "denominator": 1}
        ),
        "parent_section_identity": bool(record["parent_section_identity"]),
        "typed_source_dispatch": typed_dispatch,
        "complete_exact_envelope": (
            record["exact_envelope_domain"]
            == [
                {"numerator": 0, "denominator": 1},
                {"numerator": 1, "denominator": 1},
            ]
            and piece_coverage
            and record["ray_authority"] == "exact_selector_normal_fan"
            and record["point_authority"]
            == "two_pass_factorized_directional_face"
        ),
        "epigraph_orientation": (
            record["epigraph_orientation"]
            == "z_greater_than_or_equal_to_every_row"
        ),
        "dual_cardinality_columns": (
            total >= int(source["reachable_support_cardinality"]) >= 1
            and record["certificate_identity_authority"] == "total_function_only"
            and record["reachable_identity_role"] == "reporting_only"
        ),
        "zero_materialized_tapes": (
            source_work["materialized_response_tapes"] == 0
            and work["materialized_response_tapes"] == 0
        ),
        "integration_work_identity": (
            source_work["materialized_response_tapes"] == 0
            and len(record["point_summary"])
            == record["fan_counts"]["point_face_observations"]
            and work["fan_cell_rows"] == record["fan_counts"]["cells"]
            and work["fan_segments"] == record["fan_counts"]["segments"]
            and work["fan_boundaries"] == record["fan_counts"]["boundaries"]
            and work["point_face_observations"]
            == record["fan_counts"]["point_face_observations"]
            and work["envelope_row_evaluations"]
            == work["epigraph_residual_evaluations"]
            == record["fan_counts"]["cells"]
            * record["fan_counts"]["point_face_observations"]
        ),
    }


def _parent_section_index(record: Mapping[str, Any]) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}
    for direction in record["directions"]:
        label = str(direction["label"])
        for target in direction["target_rows"]:
            key = (label, int(target["target_player"]))
            if key in result:
                raise ArithmeticError("parent directional-face section repeats")
            result[key] = str(target["composed_section"]["section_sha256"])
    return result


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _finite_tree(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _execute_factorized_affine(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, Any]:
    analysis_started = time.perf_counter()
    parent_started = time.perf_counter()
    parent = verify_adr0356_legal_h4_directional_face_result_artifact()
    row_growth = verify_adr0349_legal_h4_row_growth_result_artifact()
    parent_rebind_seconds = time.perf_counter() - parent_started
    parent_index = _parent_section_index(parent.record)

    game = build_legal_h4_selector_game()
    source = legal_h4_source_policy(game)
    directions = compile_legal_h4_selector_directions(
        game,
        source,
        row_growth.record,
        acting_player=int(parsed["acting_player"]),
    )
    descriptors = tuple(_direction_descriptor(row) for row in directions)

    direction_rows = []
    flat_records = []
    section_checks = []
    section_subject_seconds = []
    for direction in directions:
        target_rows = []
        for target_player in range(game.num_players):
            section_started = time.perf_counter()
            integrated = build_factorized_tie_aware_affine_section(
                game,
                source,
                direction.endpoint_policy,
                acting_player=int(parsed["acting_player"]),
                target_player=target_player,
                selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                maximum_fan_pieces=int(parsed["maximum_fan_pieces"]),
                maximum_tree_nodes=int(parsed["maximum_tree_nodes"]),
            )
            elapsed = time.perf_counter() - section_started
            section_subject_seconds.append(elapsed)
            if (
                sum(section_subject_seconds)
                > parsed["gates"]["maximum_subject_seconds"]
            ):
                raise RuntimeError("legal h4 factorized-affine subject wall exceeded")
            key = (direction.label, target_player)
            if key not in parent_index:
                raise ArithmeticError("parent directional-face section is absent")
            record = _integration_record(
                integrated,
                parent_section_sha256=parent_index[key],
            )
            checks = _integration_checks(
                record,
                expected_acting_player=int(parsed["acting_player"]),
                expected_target_player=target_player,
            )
            target_rows.append(
                {
                    "target_player": target_player,
                    "subject_seconds": elapsed,
                    "integration": record,
                    "checks": checks,
                }
            )
            flat_records.append(record)
            section_checks.append(checks)
        direction_rows.append(
            {
                **_direction_descriptor(direction),
                "target_rows": target_rows,
            }
        )
    subject_seconds = sum(section_subject_seconds)

    mode_counts = {
        name: sum(record["mode"] == name for record in flat_records)
        for name in (
            FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
            V2_SINGLE_TAPE,
            FAIL_CLOSED_SINGLE_TAPE,
        )
    }
    aggregate_checks = {
        key: all(checks[key] for checks in section_checks)
        for key in section_checks[0]
    }
    aggregate = {
        "sections": len(flat_records),
        "mode_counts": mode_counts,
        "piece_counts": [len(record["pieces"]) for record in flat_records],
        "selector_window_scale_limits": [
            (
                None
                if record["single_tape_window"] is None
                else record["single_tape_window"]["scale_limit"]
            )
            for record in flat_records
        ],
        "maximum_total_function_cardinality": max(
            int(record["source_face"]["total_function_cardinality"])
            for record in flat_records
        ),
        "maximum_reachable_support_cardinality": max(
            int(record["source_face"]["reachable_support_cardinality"])
            for record in flat_records
        ),
        "fan_cells": sum(record["fan_counts"]["cells"] for record in flat_records),
        "fan_segments": sum(
            record["fan_counts"]["segments"] for record in flat_records
        ),
        "fan_boundaries": sum(
            record["fan_counts"]["boundaries"] for record in flat_records
        ),
        "point_face_observations": sum(
            record["fan_counts"]["point_face_observations"]
            for record in flat_records
        ),
        "float_selector_score_calls": sum(
            record["work"]["float_selector_score_calls"] for record in flat_records
        ),
        "selector_window_v2_calls": sum(
            record["work"]["selector_window_v2_calls"] for record in flat_records
        ),
        "materialized_response_tapes": sum(
            record["work"]["materialized_response_tapes"] for record in flat_records
        ),
        "parent_rebind_seconds": parent_rebind_seconds,
        "section_subject_seconds": section_subject_seconds,
        "subject_seconds": subject_seconds,
        "checks": aggregate_checks,
    }
    scientific_payload = {"directions": direction_rows, "aggregate": aggregate}
    scientific_bytes = len(
        json.dumps(
            scientific_payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    analysis_seconds = time.perf_counter() - analysis_started

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
        "parent_pass": bool(parent.record["passed"]) == gates["require_parent_pass"],
        "parent_artifact_identity": (
            parent.artifact_sha256 == parsed["expected_parent_artifact_sha256"]
            and parent.artifact_bytes == parsed["expected_parent_artifact_bytes"]
            and ADR0356_RESULT_PROTOCOL_SHA256
            == parsed["expected_parent_result_protocol_sha256"]
        )
        == gates["require_parent_artifact_identity"],
        "fixture_identity": fixture_identity == gates["require_fixture_identity"],
        "direction_identity": direction_identity
        == gates["require_direction_identity"],
        "section_identity": aggregate_checks["section_identity"]
        == gates["require_section_identity"],
        "parent_section_identity": (
            len(parent_index) == gates["expected_sections"]
            and aggregate["sections"]
            == gates["expected_directions"] * gates["expected_players"]
            == gates["expected_sections"]
            and aggregate_checks["parent_section_identity"]
        )
        == gates["require_parent_section_identity"],
        "typed_source_dispatch": aggregate_checks["typed_source_dispatch"]
        == gates["require_typed_source_dispatch"],
        "complete_exact_envelope": aggregate_checks["complete_exact_envelope"]
        == gates["require_complete_exact_envelope"],
        "epigraph_orientation": aggregate_checks["epigraph_orientation"]
        == gates["require_epigraph_orientation"],
        "dual_cardinality_columns": (
            aggregate_checks["dual_cardinality_columns"]
            and parsed["cardinality_columns"]
            == ("total_function", "reachable_support")
        )
        == gates["require_dual_cardinality_columns"],
        "zero_materialized_tapes": (
            aggregate_checks["zero_materialized_tapes"]
            and aggregate["materialized_response_tapes"] == 0
        )
        == gates["require_zero_materialized_tapes"],
        "integration_work_identity": aggregate_checks["integration_work_identity"]
        == gates["require_integration_work_identity"],
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
        "parent_rebind_wall": (
            parent_rebind_seconds <= gates["maximum_parent_rebind_seconds"]
        ),
        "subject_wall": subject_seconds <= gates["maximum_subject_seconds"],
        "analysis_wall": analysis_seconds <= gates["maximum_analysis_seconds"],
        "scientific_payload_bytes": (
            scientific_bytes <= gates["maximum_scientific_payload_bytes"]
        ),
    }
    emission = {
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
        "actions_emitted": 0,
        "strategy_quality_claim": None,
    }
    checks["zero_actions_and_quality_rows"] = (
        emission
        == {
            "quality_rows_serialized": 0,
            "strategy_labels_generated": 0,
            "actions_emitted": 0,
            "strategy_quality_claim": None,
        }
    ) == gates["require_zero_actions_and_quality_rows"]
    payload: dict[str, Any] = {
        "parent_artifact_sha256": parent.artifact_sha256,
        "parent_artifact_bytes": parent.artifact_bytes,
        "root_public_state_sha256": public_betting_state_sha256(game.base_state),
        "public_schema_sha256": parent.record["public_schema_sha256"],
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "source_policy_sha256": policy_sha256(source),
        "direction_descriptors": list(descriptors),
        "integration_semantics": {
            "source_tie_mode": parsed["source_tie_mode"],
            "singleton_positive_mode": parsed["singleton_positive_mode"],
            "singleton_closed_mode": parsed["singleton_closed_mode"],
            "selector_margin_allowance": parsed["selector_margin_allowance"],
            "ray_authority": parsed["ray_authority"],
            "point_authority": parsed["point_authority"],
            "epigraph_orientation": parsed["epigraph_orientation"],
            "cardinality_columns": list(parsed["cardinality_columns"]),
            "cardinality_authority": parsed["cardinality_authority"],
            "maximum_tree_nodes": parsed["maximum_tree_nodes"],
            "maximum_fan_pieces": parsed["maximum_fan_pieces"],
            "face_cardinality_bound": None,
        },
        **scientific_payload,
        "scientific_payload_bytes": scientific_bytes,
        "analysis_seconds": analysis_seconds,
        **emission,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    finalized = finalize_gates(checks)
    return {
        **payload,
        **finalized,
        "decision": (
            "authorize_untouched_factorized_tie_aware_affine_confirmation_"
            "preregistration"
            if finalized["passed"]
            else "reject_legal_h4_factorized_affine_integration_boundary"
        ),
    }


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _environment(git: Mapping[str, Any] | None) -> dict[str, Any]:
    return assemble_environment(
        runtime={"backend": "cpu_fraction_exact_fan_face_factorized_affine"},
        git=(
            {"available": False, "dirty": None, "commit": None}
            if git is None
            else git
        ),
    )


def run_legal_responder_raise_h4_factorized_affine(
    *,
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Consume exactly one legal h4 factorized-affine terminal path."""

    if output_path.exists():
        raise FileExistsError(
            f"legal h4 factorized-affine result path exists: {output_path}"
        )
    loaded = None
    parsed = None
    git: Mapping[str, Any] | None = None
    stage = "config"
    try:
        loaded = load_config(
            config_path,
            schema_validator=lambda payload: _parse_config(payload),
        )
        parsed = _parse_config(loaded.payload)
        stage = "git_precondition"
        git = _strict_git_metadata()
        if bool(git["dirty"]):
            raise RuntimeError(
                "legal h4 factorized-affine invocation requires a clean commit"
            )
        stage = "factorized_affine"
        payload = _execute_factorized_affine(parsed, git=git)
        result = {
            "schema_version": "legal-responder-raise-h4-factorized-affine-v1",
            "status": "legal_responder_raise_h4_factorized_affine_executed",
            "config_sha256": loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0357_PROTOCOL_SHA256,
            "environment": _environment(git),
            "methodology": {
                "ray_source": "exact_selector_normal_fan",
                "point_source": "two_pass_factorized_directional_face",
                "source_tie_dispatch": FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
                "singleton_dispatch": "selector_window_v2_or_typed_fail_closed",
                "target_invocations": 8,
                "result_path_lifecycle": parsed["result_path_lifecycle"],
                "analysis_wall_semantics": parsed["analysis_wall_semantics"],
                "subject_wall_semantics": parsed["subject_wall_semantics"],
                "claims_policy": parsed["claims_policy"],
            },
            "limitations": [
                "same_fixture_legal_h4_development_integration_only",
                "not_untouched_confirmation",
                "not_full_width_capacity_or_action_clock_latency",
                "not_multiway_response_closure_or_cross_street_handoff",
                "no_action_quality_or_poker_strength_claim",
            ],
            **payload,
        }
    except BaseException as exc:
        result = {
            "schema_version": "legal-responder-raise-h4-factorized-affine-v1",
            "status": "legal_responder_raise_h4_factorized_affine_failed",
            "config_sha256": None if loaded is None else loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0357_PROTOCOL_SHA256,
            "environment": _environment(git),
            "decision": "reject_legal_h4_factorized_affine_integration_boundary",
            "passed": False,
            "gates": {"first_terminal_failure": True, "passed": False},
            "failure": {
                "stage": stage,
                "type": type(exc).__name__,
                "message": str(exc),
            },
            "strategy_quality_claim": None,
            "actions_emitted": 0,
            "quality_rows_serialized": 0,
            "strategy_labels_generated": 0,
        }

    rendered = serialize_result(result)
    maximum_result_bytes = (
        8_388_608
        if parsed is None
        else int(parsed["gates"]["maximum_result_bytes"])
    )
    if len(rendered.encode("utf-8")) > maximum_result_bytes:
        result = {
            "schema_version": "legal-responder-raise-h4-factorized-affine-v1",
            "status": "legal_responder_raise_h4_factorized_affine_failed",
            "config_sha256": None if loaded is None else loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0357_PROTOCOL_SHA256,
            "environment": _environment(git),
            "decision": "reject_legal_h4_factorized_affine_integration_boundary",
            "passed": False,
            "gates": {"result_bytes": False, "passed": False},
            "failure": {
                "stage": "result_bytes",
                "type": "RuntimeError",
                "message": "legal h4 factorized-affine result exceeds byte bound",
            },
            "strategy_quality_claim": None,
            "actions_emitted": 0,
            "quality_rows_serialized": 0,
            "strategy_labels_generated": 0,
        }
        rendered = serialize_result(result)
    _write_exclusive(output_path, rendered)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_legal_responder_raise_h4_factorized_affine(
        config_path=arguments.config,
        output_path=arguments.output,
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if bool(result.get("passed")) else 1)


if __name__ == "__main__":
    main()


__all__ = [
    "run_legal_responder_raise_h4_factorized_affine",
]
