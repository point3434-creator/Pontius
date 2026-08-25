"""Tie-aware affine integration without Cartesian response-tape closure.

The exact selector normal fan is the ray authority: it supplies every affine
piece that can own a nonempty interval.  The two-pass directional-face oracle
is the point authority: at every fan boundary and open-cell witness it supplies
the complete value-optimal face, both directional slope extrema, and exact
total-function/reachable-support cardinalities.

This module joins those authorities into one typed certificate.  Exact source
ties dispatch to a factorized maximum envelope; exact singleton sources may
use selector-window v2.  No response-tape Cartesian product is formed.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Mapping, TypeAlias

from .exact_directional_face_oracle import (
    ExactDirectionalFace,
    ExactDirectionalFaceFanSample,
    ExactDirectionalFaceFanSection,
    ExactFanCellGainRow,
    compose_exact_directional_face_fan_section,
)
from .exact_selector_fan import (
    ExactPolicy,
    ResponseTape,
    realization_interpolated_policy,
)
from .game import Action, ExtensiveFormGame
from .selector_window import (
    ConservativeSelectorWindow,
    fixed_response_selector_scores,
)
from .selector_window_v2 import fail_closed_affine_selector_window


FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE = "factorized_tie_aware_maximum_envelope"
V2_SINGLE_TAPE = "v2_single_tape"
FAIL_CLOSED_SINGLE_TAPE = "fail_closed_single_tape"

FactorKey: TypeAlias = tuple[str, Action]


@dataclass(frozen=True, slots=True)
class ExactFactorizedAffinePiece:
    """One open fan interval and its exact envelope-owning affine row."""

    lower: Fraction
    upper: Fraction
    witness: Fraction
    response_tape: ResponseTape
    intercept: Fraction
    slope: Fraction
    total_state: str
    reachable_state: str
    total_function_cardinality: int
    reachable_support_cardinality: int

    def value(self, scale: Fraction) -> Fraction:
        return self.intercept + scale * self.slope


@dataclass(frozen=True, slots=True)
class ExactFactorizedAffineIntegrationWork:
    """Explicit integration work, separate from the face oracle's own ledger."""

    fan_cell_rows: int
    fan_segments: int
    fan_boundaries: int
    point_face_observations: int
    envelope_row_evaluations: int
    epigraph_residual_evaluations: int
    selector_window_v2_calls: int
    float_selector_score_calls: int
    materialized_response_tapes: int


@dataclass(frozen=True, slots=True)
class ExactFactorizedTieAwareAffineSection:
    """Typed affine authority for one target player along one exact ray."""

    mode: str
    section: ExactDirectionalFaceFanSection
    source_face: ExactDirectionalFace
    pieces: tuple[ExactFactorizedAffinePiece, ...]
    single_tape_window: ConservativeSelectorWindow | None
    exact_envelope_domain: tuple[Fraction, Fraction]
    certificate_identity_authority: str
    reachable_identity_role: str
    ray_authority: str
    point_authority: str
    epigraph_orientation: str
    work: ExactFactorizedAffineIntegrationWork


def _source_sample(
    section: ExactDirectionalFaceFanSection,
) -> ExactDirectionalFaceFanSample:
    candidates = tuple(
        sample
        for sample in section.samples
        if sample.sample_kind == "fan_boundary" and sample.scale == 0
    )
    if len(candidates) != 1:
        raise ArithmeticError("factorized affine section has no unique source face")
    return candidates[0]


def _validate_tape_against_face(face: ExactDirectionalFace, tape: ResponseTape) -> None:
    factors = {row.key: row for row in face.information_sets}
    selected = dict(tape)
    if len(selected) != len(tape) or set(selected) != set(factors):
        raise ArithmeticError("factorized affine extremal tape schema differs")
    for key, action in selected.items():
        if action not in factors[key].maximizing_actions:
            raise ArithmeticError("factorized affine extremal tape leaves active face")


def _rederive_face_cardinalities(face: ExactDirectionalFace) -> tuple[int, int]:
    factors = {row.key: row for row in face.information_sets}
    if len(factors) != len(face.information_sets):
        raise ArithmeticError("factorized affine face repeats an information key")

    total = 1
    children: dict[FactorKey, list[str]] = {}
    roots: list[str] = []
    position = {row.key: offset for offset, row in enumerate(face.information_sets)}
    for row in face.information_sets:
        if not row.actions or not row.maximizing_actions:
            raise ArithmeticError("factorized affine face contains an empty action set")
        if len(set(row.actions)) != len(row.actions) or len(
            set(row.maximizing_actions)
        ) != len(row.maximizing_actions):
            raise ArithmeticError("factorized affine face repeats an action")
        if any(action not in row.actions for action in row.maximizing_actions):
            raise ArithmeticError("factorized affine maximizer is not a legal action")
        if row.minimum_slope_action not in row.maximizing_actions or (
            row.maximum_slope_action not in row.maximizing_actions
        ):
            raise ArithmeticError("factorized affine local slope action is not active")
        if row.minimum_local_slope > row.maximum_local_slope:
            raise ArithmeticError("factorized affine local slope interval is reversed")
        total *= len(row.maximizing_actions)
        if row.parent is None:
            roots.append(row.key)
            continue
        parent_key, parent_action = row.parent
        parent = factors.get(parent_key)
        if parent is None or parent_action not in parent.actions:
            raise ArithmeticError("factorized affine face has an invalid parent sequence")
        if position[parent_key] >= position[row.key]:
            raise ArithmeticError("factorized affine factors are not parent-first")
        children.setdefault((parent_key, parent_action), []).append(row.key)

    counts: dict[str, int] = {}
    for row in reversed(face.information_sets):
        if not row.positive_counterfactual_support:
            counts[row.key] = 1
            continue
        count = 0
        for action in row.maximizing_actions:
            branch = 1
            for child in children.get((row.key, action), ()):
                branch *= counts[child]
            count += branch
        counts[row.key] = count
    reachable = 1
    for key in roots:
        reachable *= counts[key]
    return total, reachable


def _validate_face(face: ExactDirectionalFace) -> None:
    total, reachable = _rederive_face_cardinalities(face)
    if total != face.total_function_cardinality:
        raise ArithmeticError("factorized affine total cardinality differs")
    if reachable != face.reachable_support_cardinality or reachable > total:
        raise ArithmeticError("factorized affine reachable cardinality differs")
    if face.response_value - face.profile_utility != face.deviation_gain:
        raise ArithmeticError("factorized affine gain identity differs")
    if face.minimum_response_slope > face.maximum_response_slope:
        raise ArithmeticError("factorized affine response slope interval is reversed")
    if face.minimum_gain_slope > face.maximum_gain_slope:
        raise ArithmeticError("factorized affine gain slope interval is reversed")
    if (
        face.minimum_response_slope - face.profile_utility_slope
        != face.minimum_gain_slope
        or face.maximum_response_slope - face.profile_utility_slope
        != face.maximum_gain_slope
    ):
        raise ArithmeticError("factorized affine response/profile slope algebra differs")
    _validate_tape_against_face(face, face.minimum_slope_tape)
    _validate_tape_against_face(face, face.maximum_slope_tape)
    if face.work.lexicographic_passes != 2:
        raise ArithmeticError("factorized affine point authority did not use two passes")
    if face.work.materialized_response_tapes != 0:
        raise ArithmeticError("factorized affine point authority materialized tapes")


def _validate_section_and_build_pieces(
    section: ExactDirectionalFaceFanSection,
) -> tuple[tuple[ExactFactorizedAffinePiece, ...], int]:
    fan = section.fan
    rows = section.cell_rows
    if not rows:
        raise ArithmeticError("factorized affine section has no fan rows")
    if len(rows) != len(fan.cells):
        raise ArithmeticError("factorized affine fan cell and row counts differ")
    rows_by_tape: dict[ResponseTape, ExactFanCellGainRow] = {}
    cells_by_tape = {cell.response_tape: cell for cell in fan.cells}
    if len(cells_by_tape) != len(fan.cells):
        raise ArithmeticError("factorized affine fan repeats a cell tape")
    for row in rows:
        if row.response_tape in rows_by_tape:
            raise ArithmeticError("factorized affine fan repeats an affine row tape")
        cell = cells_by_tape.get(row.response_tape)
        if cell is None or (row.lower, row.upper) != (cell.lower, cell.upper):
            raise ArithmeticError("factorized affine row is detached from its fan cell")
        if row.lower > row.upper:
            raise ArithmeticError("factorized affine row has an empty cell")
        rows_by_tape[row.response_tape] = row

    expected_specs = {
        (point.scale, "fan_boundary") for point in fan.points
    } | {(segment.witness, "open_segment") for segment in fan.segments}
    actual_specs = {(sample.scale, sample.sample_kind) for sample in section.samples}
    if len(actual_specs) != len(section.samples) or actual_specs != expected_specs:
        raise ArithmeticError("factorized affine face samples do not cover the fan")

    envelope_evaluations = 0
    sample_by_spec = {
        (sample.scale, sample.sample_kind): sample for sample in section.samples
    }
    for sample in section.samples:
        _validate_face(sample.face)
        if (
            sample.face.acting_player != fan.acting_player
            or sample.face.target_player != fan.target_player
            or sample.face.scale != sample.scale
        ):
            raise ArithmeticError("factorized affine face identity differs from fan")
        values = tuple(row.value(sample.scale) for row in rows)
        envelope_evaluations += len(values)
        maximum = max(values)
        active = tuple(
            row for row, value in zip(rows, values, strict=True) if value == maximum
        )
        if maximum != sample.maximum_cell_gain or maximum != sample.face.deviation_gain:
            raise ArithmeticError("factorized affine maximum envelope value differs")
        if any(value > sample.face.deviation_gain for value in values):
            raise ArithmeticError("factorized affine row exceeds point authority")
        if len(active) != sample.active_cell_rows or not active:
            raise ArithmeticError("factorized affine active fan-row count differs")

        # The exact face supplies the full subgradient interval.  The fan must
        # expose both extremes among rows that are active at this point; this
        # is the seam check that turns point and ray instruments into one
        # complete affine certificate.
        active_slopes = tuple(row.slope for row in active)
        if sample.scale == 0:
            # The ray has no negative-scale neighbor.  The right derivative is
            # the largest slope on the source face; smaller tied slopes remain
            # represented by the point authority even when they never own a
            # positive-width cell inside [0, 1].
            slope_seam = (
                max(active_slopes) == sample.face.maximum_gain_slope
                and min(active_slopes) >= sample.face.minimum_gain_slope
            )
        elif sample.scale == 1:
            # Symmetrically, only the smallest active slope can own the
            # one-sided neighborhood immediately to the left of the endpoint.
            slope_seam = (
                min(active_slopes) == sample.face.minimum_gain_slope
                and max(active_slopes) <= sample.face.maximum_gain_slope
            )
        else:
            slope_seam = (
                min(active_slopes) == sample.face.minimum_gain_slope
                and max(active_slopes) == sample.face.maximum_gain_slope
            )
        if not slope_seam:
            raise ArithmeticError("factorized affine fan/face slope seam differs")
        if (sample.total_state == "tie_unresolved") != (
            sample.face.total_function_cardinality > 1
        ):
            raise ArithmeticError("factorized affine total tie state differs")
        if (sample.reachable_state == "tie_unresolved") != (
            sample.face.reachable_support_cardinality > 1
        ):
            raise ArithmeticError("factorized affine reachable tie state differs")

        # A minimized epigraph uses z >= row.  At z equal to the exact
        # envelope every residual is nonnegative and at least one is zero;
        # therefore any exact positive lowering violates an active row.
        residuals = tuple(sample.face.deviation_gain - value for value in values)
        if any(residual < 0 for residual in residuals) or 0 not in residuals:
            raise ArithmeticError("factorized affine epigraph orientation differs")

    pieces: list[ExactFactorizedAffinePiece] = []
    cursor = Fraction(0)
    previous: ExactFactorizedAffinePiece | None = None
    for segment in fan.segments:
        if segment.lower != cursor or not segment.lower < segment.upper:
            raise ArithmeticError("factorized affine pieces do not partition the ray")
        row = rows_by_tape.get(segment.response_tape)
        sample = sample_by_spec.get((segment.witness, "open_segment"))
        if row is None or sample is None:
            raise ArithmeticError("factorized affine open segment lacks an authority")
        if row.lower > segment.lower or row.upper < segment.upper:
            raise ArithmeticError("factorized affine fan row does not cover its piece")
        if sample.face.minimum_gain_slope != sample.face.maximum_gain_slope:
            raise ArithmeticError("factorized affine open piece has nonunique slope")
        if row.slope != sample.face.minimum_gain_slope:
            raise ArithmeticError("factorized affine piece slope differs from face")
        piece = ExactFactorizedAffinePiece(
            lower=segment.lower,
            upper=segment.upper,
            witness=segment.witness,
            response_tape=segment.response_tape,
            intercept=row.intercept,
            slope=row.slope,
            total_state=segment.total_state,
            reachable_state=segment.reachable_state,
            total_function_cardinality=sample.face.total_function_cardinality,
            reachable_support_cardinality=sample.face.reachable_support_cardinality,
        )
        if previous is not None:
            boundary = segment.lower
            if previous.value(boundary) != piece.value(boundary):
                raise ArithmeticError("factorized affine envelope is discontinuous")
            if previous.slope > piece.slope:
                raise ArithmeticError("factorized affine maximum envelope is not convex")
        pieces.append(piece)
        previous = piece
        cursor = segment.upper
    if cursor != 1 or not pieces:
        raise ArithmeticError("factorized affine pieces do not cover [0, 1]")
    return tuple(pieces), envelope_evaluations


def integrate_factorized_tie_aware_affine_section(
    section: ExactDirectionalFaceFanSection,
    *,
    single_tape_window: ConservativeSelectorWindow | None,
    selector_window_v2_calls: int,
    float_selector_score_calls: int,
) -> ExactFactorizedTieAwareAffineSection:
    """Validate and type one already-composed fan/face section."""

    if (
        isinstance(selector_window_v2_calls, bool)
        or not isinstance(selector_window_v2_calls, int)
        or selector_window_v2_calls < 0
    ):
        raise ValueError("factorized affine v2 call count must be nonnegative")
    if (
        isinstance(float_selector_score_calls, bool)
        or not isinstance(float_selector_score_calls, int)
        or float_selector_score_calls < 0
    ):
        raise ValueError("factorized affine score call count must be nonnegative")

    pieces, envelope_evaluations = _validate_section_and_build_pieces(section)
    source_sample = _source_sample(section)
    source_face = source_sample.face
    source_tied = source_face.total_function_cardinality > 1
    if source_tied:
        if single_tape_window is not None:
            raise ArithmeticError("factorized affine source tie received a v2 window")
        if selector_window_v2_calls != 0 or float_selector_score_calls != 0:
            raise ArithmeticError("factorized affine source tie invoked single-tape work")
        if source_sample.total_state != "tie_unresolved":
            raise ArithmeticError("factorized affine exact source tie was elected")
        mode = FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE
    else:
        if source_face.total_function_cardinality != 1:
            raise ArithmeticError("factorized affine source cardinality is invalid")
        if single_tape_window is None:
            raise ArithmeticError("factorized affine singleton lacks selector-window v2")
        if selector_window_v2_calls != 1 or float_selector_score_calls != 2:
            raise ArithmeticError("factorized affine singleton call ledger differs")
        if not isfinite(single_tape_window.scale_limit) or not (
            0.0 <= single_tape_window.scale_limit <= 1.0
        ):
            raise ArithmeticError("factorized affine v2 scale is invalid")
        if source_sample.total_state != "fixed":
            raise ArithmeticError("factorized affine singleton source is not fixed")
        if (
            source_face.minimum_slope_tape != source_face.maximum_slope_tape
            or source_face.minimum_slope_tape != section.fan.source_tape
        ):
            raise ArithmeticError("factorized affine singleton tape identity differs")
        if Fraction.from_float(single_tape_window.scale_limit) > (
            section.fan.source_cell_upper
        ):
            raise ArithmeticError("factorized affine v2 window exceeds exact source cell")
        mode = (
            V2_SINGLE_TAPE
            if single_tape_window.scale_limit > 0.0
            else FAIL_CLOSED_SINGLE_TAPE
        )

    residual_evaluations = len(section.cell_rows) * len(section.samples)
    work = ExactFactorizedAffineIntegrationWork(
        fan_cell_rows=len(section.cell_rows),
        fan_segments=len(section.fan.segments),
        fan_boundaries=len(section.fan.points),
        point_face_observations=len(section.samples),
        envelope_row_evaluations=envelope_evaluations,
        epigraph_residual_evaluations=residual_evaluations,
        selector_window_v2_calls=selector_window_v2_calls,
        float_selector_score_calls=float_selector_score_calls,
        materialized_response_tapes=0,
    )
    return ExactFactorizedTieAwareAffineSection(
        mode=mode,
        section=section,
        source_face=source_face,
        pieces=pieces,
        single_tape_window=single_tape_window,
        exact_envelope_domain=(Fraction(0), Fraction(1)),
        certificate_identity_authority="total_function_only",
        reachable_identity_role="reporting_only",
        ray_authority="exact_selector_normal_fan",
        point_authority="two_pass_factorized_directional_face",
        epigraph_orientation="z_greater_than_or_equal_to_every_row",
        work=work,
    )


def build_factorized_tie_aware_affine_section(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    selector_margin_allowance: float,
    maximum_fan_pieces: int = 256,
    maximum_tree_nodes: int = 100_000,
) -> ExactFactorizedTieAwareAffineSection:
    """Build the exact fan/face composition and its typed affine integration."""

    if not isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("factorized affine selector allowance must be nonnegative")
    section = compose_exact_directional_face_fan_section(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        target_player=target_player,
        maximum_fan_tapes=maximum_fan_pieces,
        maximum_tree_nodes=maximum_tree_nodes,
    )
    source_face = _source_sample(section).face
    window: ConservativeSelectorWindow | None = None
    window_calls = 0
    score_calls = 0
    if source_face.total_function_cardinality == 1:
        source = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=Fraction(0),
        )
        endpoint = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=Fraction(1),
        )
        tape = dict(source_face.minimum_slope_tape)
        source_scores = fixed_response_selector_scores(
            game,
            source,
            target_player,
            tape,
        )
        endpoint_scores = fixed_response_selector_scores(
            game,
            endpoint,
            target_player,
            tape,
        )
        score_calls = 2
        window = fail_closed_affine_selector_window(
            source_scores,
            endpoint_scores,
            selector_margin_allowance=selector_margin_allowance,
        )
        window_calls = 1
    return integrate_factorized_tie_aware_affine_section(
        section,
        single_tape_window=window,
        selector_window_v2_calls=window_calls,
        float_selector_score_calls=score_calls,
    )


__all__ = [
    "FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE",
    "FAIL_CLOSED_SINGLE_TAPE",
    "V2_SINGLE_TAPE",
    "ExactFactorizedAffineIntegrationWork",
    "ExactFactorizedAffinePiece",
    "ExactFactorizedTieAwareAffineSection",
    "build_factorized_tie_aware_affine_section",
    "integrate_factorized_tie_aware_affine_section",
]
