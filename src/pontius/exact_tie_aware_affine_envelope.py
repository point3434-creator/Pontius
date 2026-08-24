"""Exact active-row closure for one-dimensional affine response envelopes.

The selector fan records one legal-order maximizer at a tie.  That is enough
to map value geometry, but it is not enough to integrate a tied source into a
single-tape certificate.  This module enumerates every locally maximizing
total tape at each exact fan point and open-cell witness, validates each tape
against a fixed-response trace, and retains the complete maximum affine
envelope.  It is deliberately a bounded small-game oracle, not a production
claim about arbitrary response-set width.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Mapping, TypeAlias

from .exact_selector_fan import (
    ExactSelectorFanSection,
    map_exact_selector_fan_section,
    realization_interpolated_policy,
)
from .exact_selector_window_oracle import (
    ExactBestResponseTrace,
    exact_best_response_trace,
    exact_fixed_response_trace,
    exact_policy_utilities,
)
from .game import Action, ExtensiveFormGame


ExactPolicy: TypeAlias = Mapping[str, Mapping[Action, Fraction | float]]
ResponseTape: TypeAlias = tuple[tuple[str, Action], ...]


@dataclass(frozen=True, slots=True)
class ExactAffineResponseRow:
    """One immutable total response tape and its exact gain row."""

    response_tape: ResponseTape
    response_value_intercept: Fraction
    response_value_slope: Fraction
    profile_utility_intercept: Fraction
    profile_utility_slope: Fraction
    deviation_gain_intercept: Fraction
    deviation_gain_slope: Fraction

    def response_value(self, scale: Fraction) -> Fraction:
        return self.response_value_intercept + scale * self.response_value_slope

    def deviation_gain(self, scale: Fraction) -> Fraction:
        return self.deviation_gain_intercept + scale * self.deviation_gain_slope


@dataclass(frozen=True, slots=True)
class ExactActiveRowSample:
    """Complete locally maximizing tape set at one exact section coordinate."""

    scale: Fraction
    sample_kind: str
    response_value: Fraction
    profile_utility: Fraction
    deviation_gain: Fraction
    active_tapes: tuple[ResponseTape, ...]


@dataclass(frozen=True, slots=True)
class ExactTieAwareAffineSection:
    """A fan section enriched with exact active tapes and affine rows."""

    acting_player: int
    target_player: int
    fan: ExactSelectorFanSection
    rows: tuple[ExactAffineResponseRow, ...]
    samples: tuple[ExactActiveRowSample, ...]
    source_active_tapes: tuple[ResponseTape, ...]
    affine_equivalence_classes: tuple[tuple[ResponseTape, ...], ...]
    single_tape_exact_eligible: bool


def enumerate_exact_local_maximizer_tapes(
    trace: ExactBestResponseTrace,
    *,
    maximum_tapes: int,
) -> tuple[ResponseTape, ...]:
    """Enumerate the Cartesian closure of exact local maximizing actions."""

    if (
        isinstance(maximum_tapes, bool)
        or not isinstance(maximum_tapes, int)
        or maximum_tapes <= 0
    ):
        raise ValueError("exact active-tape bound must be a positive integer")
    keys = []
    choices = []
    count = 1
    for row in trace.information_sets:
        if not row.maximizing_actions:
            raise ArithmeticError("exact selector trace has no maximizing action")
        keys.append(row.key)
        choices.append(row.maximizing_actions)
        count *= len(row.maximizing_actions)
        if count > maximum_tapes:
            raise RuntimeError("exact active-tape closure exceeds its frozen bound")
    tapes = tuple(
        tuple(sorted(zip(keys, selected, strict=True)))
        for selected in product(*choices)
    )
    if len(tapes) != count or len(set(tapes)) != count:
        raise ArithmeticError("exact active-tape closure is not one-to-one")
    return tuple(sorted(tapes, key=repr))


def _row_for_tape(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    target_player: int,
    response_tape: ResponseTape,
    profile_intercept: Fraction,
    profile_slope: Fraction,
) -> ExactAffineResponseRow:
    source = exact_fixed_response_trace(
        game,
        source_policy,
        target_player,
        dict(response_tape),
    )
    endpoint = exact_fixed_response_trace(
        game,
        endpoint_policy,
        target_player,
        dict(response_tape),
    )
    response_intercept = source.value
    response_slope = endpoint.value - source.value
    gain_intercept = response_intercept - profile_intercept
    gain_slope = response_slope - profile_slope
    return ExactAffineResponseRow(
        response_tape=response_tape,
        response_value_intercept=response_intercept,
        response_value_slope=response_slope,
        profile_utility_intercept=profile_intercept,
        profile_utility_slope=profile_slope,
        deviation_gain_intercept=gain_intercept,
        deviation_gain_slope=gain_slope,
    )


def _sample_specs(
    fan: ExactSelectorFanSection,
) -> tuple[tuple[Fraction, str], ...]:
    specs = {
        *((row.scale, "point") for row in fan.points),
        *((row.witness, "open_segment") for row in fan.segments),
    }
    return tuple(sorted(specs, key=lambda item: (item[0], item[1])))


def build_exact_tie_aware_affine_section(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    maximum_fan_tapes: int = 256,
    maximum_active_tapes_per_sample: int = 256,
    maximum_affine_rows: int = 1024,
) -> ExactTieAwareAffineSection:
    """Build and independently validate one exact maximum affine envelope."""

    if (
        isinstance(maximum_affine_rows, bool)
        or not isinstance(maximum_affine_rows, int)
        or maximum_affine_rows <= 0
    ):
        raise ValueError("exact affine-row bound must be a positive integer")
    fan = map_exact_selector_fan_section(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        target_player=target_player,
        maximum_tapes=maximum_fan_tapes,
    )
    source_exact = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(0),
    )
    endpoint_exact = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    source_utilities = exact_policy_utilities(game, source_exact)
    endpoint_utilities = exact_policy_utilities(game, endpoint_exact)
    profile_intercept = source_utilities[target_player]
    profile_slope = endpoint_utilities[target_player] - profile_intercept

    active_by_spec: list[
        tuple[
            Fraction,
            str,
            ExactBestResponseTrace,
            tuple[ResponseTape, ...],
            Fraction,
        ]
    ] = []
    all_tapes: set[ResponseTape] = set()
    for scale, sample_kind in _sample_specs(fan):
        policy = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=scale,
        )
        trace = exact_best_response_trace(game, policy, target_player)
        tapes = enumerate_exact_local_maximizer_tapes(
            trace,
            maximum_tapes=maximum_active_tapes_per_sample,
        )
        for tape in tapes:
            fixed = exact_fixed_response_trace(
                game,
                policy,
                target_player,
                dict(tape),
            )
            if fixed.value != trace.value or not all(
                row.selected_is_maximal for row in fixed.information_sets
            ):
                raise ArithmeticError(
                    "exact local-maximizer Cartesian closure is not self-consistent"
                )
        all_tapes.update(tapes)
        if len(all_tapes) > maximum_affine_rows:
            raise RuntimeError("exact affine-row library exceeds its frozen bound")
        profile = exact_policy_utilities(game, policy)[target_player]
        active_by_spec.append((scale, sample_kind, trace, tapes, profile))

    rows = tuple(
        _row_for_tape(
            game,
            source_exact,
            endpoint_exact,
            target_player=target_player,
            response_tape=tape,
            profile_intercept=profile_intercept,
            profile_slope=profile_slope,
        )
        for tape in sorted(all_tapes, key=repr)
    )
    rows_by_tape = {row.response_tape: row for row in rows}
    samples = []
    for scale, sample_kind, trace, tapes, profile in active_by_spec:
        exact_gain = trace.value - profile
        row_values = tuple(row.deviation_gain(scale) for row in rows)
        if (
            not row_values
            or max(row_values) != exact_gain
            or any(value > exact_gain for value in row_values)
            or any(rows_by_tape[tape].deviation_gain(scale) != exact_gain for tape in tapes)
        ):
            raise ArithmeticError("exact active rows do not form the maximum envelope")
        samples.append(
            ExactActiveRowSample(
                scale=scale,
                sample_kind=sample_kind,
                response_value=trace.value,
                profile_utility=profile,
                deviation_gain=exact_gain,
                active_tapes=tapes,
            )
        )

    source_sample = next(
        row
        for row in samples
        if row.scale == 0 and row.sample_kind == "point"
    )
    classes: dict[tuple[Fraction, Fraction], list[ResponseTape]] = {}
    for row in rows:
        classes.setdefault(
            (row.deviation_gain_intercept, row.deviation_gain_slope), []
        ).append(row.response_tape)
    equivalence_classes = tuple(
        tuple(sorted(tapes, key=repr))
        for _, tapes in sorted(classes.items(), key=lambda item: item[0])
    )
    return ExactTieAwareAffineSection(
        acting_player=acting_player,
        target_player=target_player,
        fan=fan,
        rows=rows,
        samples=tuple(samples),
        source_active_tapes=source_sample.active_tapes,
        affine_equivalence_classes=equivalence_classes,
        single_tape_exact_eligible=len(source_sample.active_tapes) == 1,
    )


__all__ = [
    "ExactActiveRowSample",
    "ExactAffineResponseRow",
    "ExactTieAwareAffineSection",
    "ResponseTape",
    "build_exact_tie_aware_affine_section",
    "enumerate_exact_local_maximizer_tapes",
]
