"""Reconstruction-complete evidence records for factorized affine sections."""

from __future__ import annotations

from dataclasses import fields
from fractions import Fraction
from hashlib import sha256
import json
from typing import Any

from .exact_directional_face_oracle import (
    ExactDirectionalFace,
    ExactDirectionalFaceWorkLedger,
)
from .factorized_tie_aware_affine import ExactFactorizedTieAwareAffineSection
from .game import Action


def canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def fraction_record(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def action_token(action: object) -> str:
    return str(action)


def tape_record(
    tape: tuple[tuple[str, Action], ...],
) -> list[dict[str, str]]:
    return [
        {"action": action_token(action), "information_key": key}
        for key, action in tape
    ]


def tape_sha256(tape: tuple[tuple[str, Action], ...]) -> str:
    return canonical_sha256(tape_record(tape))


def work_record(work: ExactDirectionalFaceWorkLedger) -> dict[str, int]:
    return {field.name: int(getattr(work, field.name)) for field in fields(work)}


def face_record(face: ExactDirectionalFace) -> dict[str, object]:
    factors = [
        {
            "actions": [action_token(action) for action in factor.actions],
            "information_key": factor.key,
            "maximum_local_slope": fraction_record(factor.maximum_local_slope),
            "maximum_slope_action": action_token(factor.maximum_slope_action),
            "maximizing_actions": [
                action_token(action) for action in factor.maximizing_actions
            ],
            "minimum_local_slope": fraction_record(factor.minimum_local_slope),
            "minimum_slope_action": action_token(factor.minimum_slope_action),
            "parent": (
                None
                if factor.parent is None
                else {
                    "action": action_token(factor.parent[1]),
                    "information_key": factor.parent[0],
                }
            ),
            "positive_counterfactual_support": (
                factor.positive_counterfactual_support
            ),
            "state_count": factor.state_count,
        }
        for factor in face.information_sets
    ]
    record: dict[str, object] = {
        "acting_player": face.acting_player,
        "deviation_gain": fraction_record(face.deviation_gain),
        "information_sets": factors,
        "maximum_gain_slope": fraction_record(face.maximum_gain_slope),
        "maximum_response_slope": fraction_record(face.maximum_response_slope),
        "maximum_slope_tape": tape_record(face.maximum_slope_tape),
        "minimum_gain_slope": fraction_record(face.minimum_gain_slope),
        "minimum_response_slope": fraction_record(face.minimum_response_slope),
        "minimum_slope_tape": tape_record(face.minimum_slope_tape),
        "profile_utility": fraction_record(face.profile_utility),
        "profile_utility_slope": fraction_record(face.profile_utility_slope),
        "reachable_support_cardinality": face.reachable_support_cardinality,
        "response_value": fraction_record(face.response_value),
        "scale": fraction_record(face.scale),
        "target_player": face.target_player,
        "total_function_cardinality": face.total_function_cardinality,
        "work": work_record(face.work),
    }
    record["factor_sha256"] = canonical_sha256(
        {
            "information_sets": factors,
            "reachable_support_cardinality": face.reachable_support_cardinality,
            "total_function_cardinality": face.total_function_cardinality,
        }
    )
    record["face_sha256"] = canonical_sha256(record)
    return record


def _fan_record(result: ExactFactorizedTieAwareAffineSection) -> dict[str, object]:
    fan = result.section.fan
    record: dict[str, object] = {
        "acting_player": fan.acting_player,
        "cells": [
            {
                "lower": fraction_record(cell.lower),
                "response_tape": tape_record(cell.response_tape),
                "response_tape_sha256": tape_sha256(cell.response_tape),
                "upper": fraction_record(cell.upper),
            }
            for cell in fan.cells
        ],
        "legacy_source_breakpoint": fraction_record(
            fan.legacy_source_breakpoint
        ),
        "measures": {
            "reachable_fixed": fraction_record(fan.reachable_fixed_measure),
            "reachable_switched": fraction_record(fan.reachable_switched_measure),
            "reachable_tie_unresolved": fraction_record(
                fan.reachable_tie_unresolved_measure
            ),
            "total_fixed": fraction_record(fan.total_fixed_measure),
            "total_switched": fraction_record(fan.total_switched_measure),
            "total_tie_unresolved": fraction_record(
                fan.total_tie_unresolved_measure
            ),
        },
        "points": [
            {
                "reachable_state": point.reachable_state,
                "reachable_tape": tape_record(point.reachable_tape),
                "reachable_tape_sha256": tape_sha256(point.reachable_tape),
                "reachable_tie_information_sets": list(
                    point.reachable_tie_information_sets
                ),
                "response_tape": tape_record(point.response_tape),
                "response_tape_sha256": tape_sha256(point.response_tape),
                "scale": fraction_record(point.scale),
                "total_state": point.total_state,
                "total_tie_information_sets": list(
                    point.total_tie_information_sets
                ),
            }
            for point in fan.points
        ],
        "reachable_tie_points": [
            fraction_record(scale) for scale in fan.reachable_tie_points
        ],
        "segments": [
            {
                "lower": fraction_record(segment.lower),
                "reachable_state": segment.reachable_state,
                "reachable_tape": tape_record(segment.reachable_tape),
                "reachable_tape_sha256": tape_sha256(segment.reachable_tape),
                "reachable_tie_information_sets": list(
                    segment.reachable_tie_information_sets
                ),
                "response_tape": tape_record(segment.response_tape),
                "response_tape_sha256": tape_sha256(segment.response_tape),
                "total_state": segment.total_state,
                "total_tie_information_sets": list(
                    segment.total_tie_information_sets
                ),
                "upper": fraction_record(segment.upper),
                "witness": fraction_record(segment.witness),
            }
            for segment in fan.segments
        ],
        "source_cell_upper": fraction_record(fan.source_cell_upper),
        "source_tape": tape_record(fan.source_tape),
        "source_tape_sha256": tape_sha256(fan.source_tape),
        "target_player": fan.target_player,
        "total_tie_points": [
            fraction_record(scale) for scale in fan.total_tie_points
        ],
    }
    record["fan_sha256"] = canonical_sha256(record)
    return record


def _cell_row_records(
    result: ExactFactorizedTieAwareAffineSection,
) -> list[dict[str, object]]:
    records = []
    for ordinal, row in enumerate(result.section.cell_rows):
        record: dict[str, object] = {
            "intercept": fraction_record(row.intercept),
            "lower": fraction_record(row.lower),
            "ordinal": ordinal,
            "response_tape": tape_record(row.response_tape),
            "response_tape_sha256": tape_sha256(row.response_tape),
            "slope": fraction_record(row.slope),
            "upper": fraction_record(row.upper),
        }
        record["row_sha256"] = canonical_sha256(record)
        records.append(record)
    return records


def _sample_records(
    result: ExactFactorizedTieAwareAffineSection,
) -> list[dict[str, object]]:
    return [
        {
            "active_cell_rows": sample.active_cell_rows,
            "face": face_record(sample.face),
            "maximum_cell_gain": fraction_record(sample.maximum_cell_gain),
            "ordinal": ordinal,
            "reachable_state": sample.reachable_state,
            "sample_kind": sample.sample_kind,
            "scale": fraction_record(sample.scale),
            "total_state": sample.total_state,
        }
        for ordinal, sample in enumerate(result.section.samples)
    ]


def _raw_section_record(
    result: ExactFactorizedTieAwareAffineSection,
) -> dict[str, object]:
    record: dict[str, object] = {
        "cell_gain_rows": _cell_row_records(result),
        "crossing_scales": [
            fraction_record(scale) for scale in result.section.crossing_scales
        ],
        "fan": _fan_record(result),
        "samples": _sample_records(result),
    }
    record["section_sha256"] = canonical_sha256(record)
    return record


def _window_record(result: ExactFactorizedTieAwareAffineSection) -> object:
    window = result.single_tape_window
    if window is None:
        return None
    return {
        "exact_source_action_ties": window.exact_source_action_ties,
        "first_switch_competing_action": (
            None
            if window.first_switch_competing_action is None
            else action_token(window.first_switch_competing_action)
        ),
        "first_switch_information_key": window.first_switch_information_key,
        "first_switch_source_action": (
            None
            if window.first_switch_source_action is None
            else action_token(window.first_switch_source_action)
        ),
        "scale_limit": window.scale_limit,
        "scale_limit_hex": window.scale_limit.hex(),
        "selector_comparisons": window.selector_comparisons,
    }


def _piece_records(
    result: ExactFactorizedTieAwareAffineSection,
) -> list[dict[str, object]]:
    return [
        {
            "intercept": fraction_record(piece.intercept),
            "lower": fraction_record(piece.lower),
            "ordinal": ordinal,
            "reachable_state": piece.reachable_state,
            "reachable_support_cardinality": piece.reachable_support_cardinality,
            "response_tape": tape_record(piece.response_tape),
            "response_tape_sha256": tape_sha256(piece.response_tape),
            "slope": fraction_record(piece.slope),
            "total_function_cardinality": piece.total_function_cardinality,
            "total_state": piece.total_state,
            "upper": fraction_record(piece.upper),
            "witness": fraction_record(piece.witness),
        }
        for ordinal, piece in enumerate(result.pieces)
    ]


def _epigraph_records(
    result: ExactFactorizedTieAwareAffineSection,
) -> list[dict[str, object]]:
    records = []
    for sample_ordinal, sample in enumerate(result.section.samples):
        rows = []
        for row_ordinal, row in enumerate(result.section.cell_rows):
            row_value = row.value(sample.scale)
            residual = sample.face.deviation_gain - row_value
            rows.append(
                {
                    "active": residual == 0,
                    "residual": fraction_record(residual),
                    "response_tape_sha256": tape_sha256(row.response_tape),
                    "row_ordinal": row_ordinal,
                    "row_value": fraction_record(row_value),
                }
            )
        records.append(
            {
                "active_rows": sum(bool(row["active"]) for row in rows),
                "envelope_value": fraction_record(sample.face.deviation_gain),
                "rows": rows,
                "sample_ordinal": sample_ordinal,
                "scale": fraction_record(sample.scale),
            }
        )
    return records


def complete_factorized_affine_record(
    result: ExactFactorizedTieAwareAffineSection,
) -> dict[str, object]:
    """Serialize every raw face/fan row needed by an independent owner."""

    raw_section = _raw_section_record(result)
    source_face = face_record(result.source_face)
    pieces = _piece_records(result)
    epigraph = _epigraph_records(result)
    work = {
        field.name: int(getattr(result.work, field.name))
        for field in fields(result.work)
    }
    record: dict[str, object] = {
        "acting_player": result.source_face.acting_player,
        "certificate_identity_authority": result.certificate_identity_authority,
        "epigraph_orientation": result.epigraph_orientation,
        "epigraph_residual_matrix": epigraph,
        "exact_envelope_domain": [
            fraction_record(scale) for scale in result.exact_envelope_domain
        ],
        "mode": result.mode,
        "pieces": pieces,
        "point_authority": result.point_authority,
        "raw_section": raw_section,
        "ray_authority": result.ray_authority,
        "reachable_identity_role": result.reachable_identity_role,
        "single_tape_window": _window_record(result),
        "source_face": source_face,
        "target_player": result.source_face.target_player,
        "work": work,
    }
    record["complete_section_sha256"] = canonical_sha256(record)
    return record


def complete_factorized_affine_record_checks(
    result: ExactFactorizedTieAwareAffineSection,
    record: dict[str, object],
) -> dict[str, bool]:
    """Check live-to-record completeness without treating digests as semantics."""

    raw = record["raw_section"]
    assert isinstance(raw, dict)
    samples = raw["samples"]
    rows = raw["cell_gain_rows"]
    fan = raw["fan"]
    epigraph = record["epigraph_residual_matrix"]
    pieces = record["pieces"]
    assert isinstance(samples, list)
    assert isinstance(rows, list)
    assert isinstance(fan, dict)
    assert isinstance(epigraph, list)
    assert isinstance(pieces, list)
    residuals_complete = (
        len(epigraph) == len(samples) == len(result.section.samples)
        and all(
            len(sample_record["rows"]) == len(rows)  # type: ignore[index]
            for sample_record in epigraph
        )
    )
    residuals_oriented = residuals_complete and all(
        all(
            Fraction(
                row["residual"]["numerator"],  # type: ignore[index]
                row["residual"]["denominator"],  # type: ignore[index]
            )
            >= 0
            for row in sample_record["rows"]  # type: ignore[index]
        )
        and sample_record["active_rows"]  # type: ignore[index]
        == samples[sample_record["sample_ordinal"]]["active_cell_rows"]  # type: ignore[index]
        for sample_record in epigraph
    )
    complete_factors = (
        record["source_face"] == face_record(result.source_face)
        and all(
            sample_record["face"] == face_record(sample.face)
            for sample_record, sample in zip(
                samples, result.section.samples, strict=True
            )
        )
    )
    piece_partition = bool(pieces)
    cursor = {"denominator": 1, "numerator": 0}
    previous_slope: Fraction | None = None
    for piece in pieces:
        piece_partition &= piece["lower"] == cursor
        slope = Fraction(
            piece["slope"]["numerator"],
            piece["slope"]["denominator"],
        )
        if previous_slope is not None:
            piece_partition &= previous_slope <= slope
        previous_slope = slope
        cursor = piece["upper"]
    piece_partition &= cursor == {"denominator": 1, "numerator": 1}
    work = record["work"]
    assert isinstance(work, dict)
    return {
        "complete_live_record_identity": (
            record == complete_factorized_affine_record(result)
        ),
        "complete_raw_factors": complete_factors,
        "complete_raw_fan_rows": (
            len(fan["cells"]) == len(rows) == len(result.section.cell_rows)
            and len(fan["segments"]) == len(result.section.fan.segments)
            and len(fan["points"]) == len(result.section.fan.points)
        ),
        "complete_raw_section_identity": (
            record["complete_section_sha256"]
            == canonical_sha256(
                {
                    key: value
                    for key, value in record.items()
                    if key != "complete_section_sha256"
                }
            )
            and raw["section_sha256"]
            == canonical_sha256(
                {
                    key: value
                    for key, value in raw.items()
                    if key != "section_sha256"
                }
            )
        ),
        "dual_cardinality_semantics": (
            result.certificate_identity_authority == "total_function_only"
            and result.reachable_identity_role == "reporting_only"
            and all(
                sample.face.total_function_cardinality
                >= sample.face.reachable_support_cardinality
                >= 1
                for sample in result.section.samples
            )
        ),
        "epigraph_residual_matrix_complete": residuals_complete,
        "epigraph_residual_orientation": residuals_oriented,
        "exact_authority_and_domain": (
            record["ray_authority"] == "exact_selector_normal_fan"
            and record["point_authority"]
            == "two_pass_factorized_directional_face"
            and record["epigraph_orientation"]
            == "z_greater_than_or_equal_to_every_row"
            and record["exact_envelope_domain"]
            == [
                {"denominator": 1, "numerator": 0},
                {"denominator": 1, "numerator": 1},
            ]
        ),
        "integration_work_identity": (
            work["fan_cell_rows"] == len(rows)
            and work["fan_segments"] == len(fan["segments"])
            and work["fan_boundaries"] == len(fan["points"])
            and work["point_face_observations"] == len(samples)
            and work["envelope_row_evaluations"]
            == work["epigraph_residual_evaluations"]
            == len(rows) * len(samples)
        ),
        "piece_partition_and_convexity": piece_partition,
        "zero_materialized_tapes": (
            work["materialized_response_tapes"] == 0
            and all(
                sample.face.work.materialized_response_tapes == 0
                for sample in result.section.samples
            )
        ),
    }


__all__ = [
    "action_token",
    "canonical_sha256",
    "complete_factorized_affine_record",
    "complete_factorized_affine_record_checks",
    "face_record",
    "fraction_record",
    "tape_record",
    "tape_sha256",
    "work_record",
]
