"""Pure, unit-tagged compiler for the reduced river sizing linear program.

This module constructs inputs only.  It deliberately imports no LP backend and
owns no solve, certificate, policy reconstruction, or strategy decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from itertools import pairwise
from math import isfinite


class LinearProgramConstraintUnit(StrEnum):
    """Physical unit carried by one inequality row."""

    DIMENSIONLESS = "dimensionless"
    CHIPS = "chips"


class LinearProgramVariableUnit(StrEnum):
    """Semantic unit carried by one nonnegative LP variable."""

    DIMENSIONLESS_GENERIC = "dimensionless-generic"
    POLICY_PROBABILITY = "dimensionless-policy-probability"
    SHIFTED_ENVELOPE_CHIPS = "shifted-envelope-chips"


class LinearProgramObjectiveUnit(StrEnum):
    """Physical unit of the maximization objective."""

    DIMENSIONLESS = "dimensionless"
    CHIPS = "chips"


class ReducedSizingConstraintKind(StrEnum):
    POLICY_MASS_UPPER = "policy-mass-upper"
    POLICY_MASS_LOWER = "policy-mass-lower"
    FOLD_ENVELOPE = "fold-envelope"
    CALL_ENVELOPE = "call-envelope"


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


def validate_reduced_river_bet_sizes(
    *,
    minimum_bet: int,
    stack: int,
    bet_sizes: object,
) -> tuple[int, ...]:
    """Return the exact increasing legal bet tuple used by the compact LP."""

    minimum = _require_integer(minimum_bet, label="minimum reduced bet", positive=True)
    effective_stack = _require_integer(stack, label="reduced stack", positive=True)
    if minimum > effective_stack:
        raise ValueError("minimum reduced bet exceeds the effective stack")
    if not isinstance(bet_sizes, tuple) or not bet_sizes:
        raise TypeError("reduced bet sizes must be a nonempty immutable tuple")
    sizes = tuple(
        _require_integer(value, label="reduced bet size", positive=True) for value in bet_sizes
    )
    if any(left >= right for left, right in pairwise(sizes)):
        raise ValueError("reduced bet sizes must increase strictly")
    if sizes[0] < minimum or sizes[-1] > effective_stack:
        raise ValueError("reduced bet size lies outside the exact legal interval")
    return sizes


@dataclass(frozen=True, slots=True)
class ReducedSizingLpLayout:
    opener_count: int
    responder_count: int
    bet_count: int
    action_count: int
    policy_variable_count: int
    envelope_variable_count: int
    variable_count: int

    def __post_init__(self) -> None:
        opener = _require_integer(self.opener_count, label="LP opener count", positive=True)
        responder = _require_integer(
            self.responder_count,
            label="LP responder count",
            positive=True,
        )
        bets = _require_integer(self.bet_count, label="LP bet count", positive=True)
        action_count = _require_integer(
            self.action_count,
            label="LP action count",
            positive=True,
        )
        policy_variables = _require_integer(
            self.policy_variable_count,
            label="LP policy-variable count",
            positive=True,
        )
        envelope_variables = _require_integer(
            self.envelope_variable_count,
            label="LP envelope-variable count",
            positive=True,
        )
        variable_count = _require_integer(
            self.variable_count,
            label="LP variable count",
            positive=True,
        )
        if action_count != 1 + bets:
            raise ValueError("LP action count differs from check plus bets")
        if policy_variables != opener * action_count:
            raise ValueError("LP policy-variable count differs from its semantic axes")
        if envelope_variables != responder * bets:
            raise ValueError("LP envelope-variable count differs from its semantic axes")
        if variable_count != policy_variables + envelope_variables:
            raise ValueError("LP variable count differs from its semantic blocks")

    def policy_index(self, opener: int, action: int) -> int:
        _require_integer(opener, label="policy opener index")
        _require_integer(action, label="policy action index")
        if opener not in range(self.opener_count) or action not in range(self.action_count):
            raise IndexError("policy coordinate lies outside the semantic LP layout")
        return opener * self.action_count + action

    def envelope_index(self, responder: int, bet_index: int) -> int:
        _require_integer(responder, label="envelope responder index")
        _require_integer(bet_index, label="envelope bet index")
        if responder not in range(self.responder_count) or bet_index not in range(self.bet_count):
            raise IndexError("envelope coordinate lies outside the semantic LP layout")
        return self.policy_variable_count + responder * self.bet_count + bet_index


@dataclass(frozen=True, slots=True)
class ReducedSizingLpRow:
    coefficients: tuple[float, ...]
    bound: float
    kind: ReducedSizingConstraintKind
    unit: LinearProgramConstraintUnit
    opener_index: int | None = None
    responder_index: int | None = None
    bet_index: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.coefficients, tuple) or not self.coefficients:
            raise TypeError("LP row coefficients must be a nonempty immutable tuple")
        if any(not isinstance(value, float) or not isfinite(value) for value in self.coefficients):
            raise ValueError("LP row coefficients must be finite floats")
        if not isinstance(self.bound, float) or not isfinite(self.bound):
            raise ValueError("LP row bound must be a finite float")
        if not isinstance(self.kind, ReducedSizingConstraintKind):
            raise TypeError("LP row kind must be semantic")
        if not isinstance(self.unit, LinearProgramConstraintUnit):
            raise TypeError("LP row unit must be semantic")
        for label, value in (
            ("opener", self.opener_index),
            ("responder", self.responder_index),
            ("bet", self.bet_index),
        ):
            if value is not None:
                _require_integer(value, label=f"LP row {label} index")
        if self.kind in {
            ReducedSizingConstraintKind.POLICY_MASS_UPPER,
            ReducedSizingConstraintKind.POLICY_MASS_LOWER,
        }:
            if self.unit is not LinearProgramConstraintUnit.DIMENSIONLESS:
                raise ValueError("policy-mass LP rows must be dimensionless")
            if (
                self.opener_index is None
                or self.responder_index is not None
                or self.bet_index is not None
            ):
                raise ValueError("policy-mass LP row coordinates are malformed")
        else:
            if self.unit is not LinearProgramConstraintUnit.CHIPS:
                raise ValueError("responder-envelope LP rows must be chip-valued")
            if (
                self.opener_index is not None
                or self.responder_index is None
                or self.bet_index is None
            ):
                raise ValueError("responder-envelope LP row coordinates are malformed")


@dataclass(frozen=True, slots=True)
class ReducedRiverSizingLinearProgram:
    """Immutable compiled LP with explicit semantic axes and physical units."""

    bet_sizes: tuple[int, ...]
    layout: ReducedSizingLpLayout
    objective: tuple[float, ...]
    rows: tuple[ReducedSizingLpRow, ...]
    variable_units: tuple[LinearProgramVariableUnit, ...]
    trusted_box_lower_bounds: tuple[float, ...]
    trusted_box_upper_bounds: tuple[float, ...]
    objective_unit: LinearProgramObjectiveUnit
    objective_offset_chips: float
    maximum_stake_chips: float
    payoff_span_chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.layout, ReducedSizingLpLayout):
            raise TypeError("compiled LP layout must be semantic")
        if (
            not isinstance(self.bet_sizes, tuple)
            or len(self.bet_sizes) != self.layout.bet_count
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.bet_sizes
            )
        ):
            raise TypeError("compiled LP bet sizes must align with its semantic layout")
        if any(left >= right for left, right in pairwise(self.bet_sizes)):
            raise ValueError("compiled LP bet sizes must increase strictly")
        if (
            not isinstance(self.objective, tuple)
            or len(self.objective) != self.layout.variable_count
        ):
            raise TypeError("compiled LP objective has the wrong immutable width")
        if any(not isinstance(value, float) or not isfinite(value) for value in self.objective):
            raise ValueError("compiled LP objective must contain finite floats")
        expected_rows = (
            2 * self.layout.opener_count + 2 * self.layout.responder_count * self.layout.bet_count
        )
        if not isinstance(self.rows, tuple) or len(self.rows) != expected_rows:
            raise TypeError("compiled LP has the wrong immutable row count")
        if any(not isinstance(row, ReducedSizingLpRow) for row in self.rows):
            raise TypeError("compiled LP contains a nonsemantic row")
        if any(len(row.coefficients) != self.layout.variable_count for row in self.rows):
            raise ValueError("compiled LP row width differs from its layout")
        if (
            not isinstance(self.variable_units, tuple)
            or len(self.variable_units) != self.layout.variable_count
        ):
            raise TypeError("compiled LP variable units have the wrong immutable width")
        expected_variable_units = (
            *(
                LinearProgramVariableUnit.POLICY_PROBABILITY
                for _ in range(self.layout.policy_variable_count)
            ),
            *(
                LinearProgramVariableUnit.SHIFTED_ENVELOPE_CHIPS
                for _ in range(self.layout.envelope_variable_count)
            ),
        )
        if self.variable_units != expected_variable_units:
            raise ValueError("compiled LP variable units differ from its semantic blocks")
        for label, values in (
            ("trusted lower", self.trusted_box_lower_bounds),
            ("trusted upper", self.trusted_box_upper_bounds),
        ):
            if not isinstance(values, tuple) or len(values) != self.layout.variable_count:
                raise TypeError(f"compiled LP {label} bounds have the wrong immutable width")
            if any(not isinstance(value, float) or not isfinite(value) for value in values):
                raise ValueError(f"compiled LP {label} bounds must be finite floats")
        if any(
            lower > upper
            for lower, upper in zip(
                self.trusted_box_lower_bounds,
                self.trusted_box_upper_bounds,
                strict=True,
            )
        ):
            raise ValueError("compiled LP trusted box is inverted")
        if self.trusted_box_lower_bounds != (0.0,) * self.layout.variable_count:
            raise ValueError("compiled LP trusted lower box must be nonnegative")
        for label, value in (
            ("objective offset", self.objective_offset_chips),
            ("maximum stake", self.maximum_stake_chips),
            ("payoff span", self.payoff_span_chips),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"compiled LP {label} must be a finite float")
        if self.maximum_stake_chips <= 0.0 or self.payoff_span_chips <= 0.0:
            raise ValueError("compiled LP chip bounds must be positive")
        expected_upper = (
            *(1.0 for _ in range(self.layout.policy_variable_count)),
            *(self.payoff_span_chips for _ in range(self.layout.envelope_variable_count)),
        )
        if self.trusted_box_upper_bounds != expected_upper:
            raise ValueError("compiled LP trusted upper box differs from semantic bounds")
        if not isinstance(self.objective_unit, LinearProgramObjectiveUnit):
            raise TypeError("reduced sizing LP objective unit must be semantic")
        if self.objective_unit is not LinearProgramObjectiveUnit.CHIPS:
            raise ValueError("reduced sizing LP objective must be chip-valued")
        if self.objective_offset_chips != (
            -self.layout.envelope_variable_count * self.maximum_stake_chips
        ):
            raise ValueError("compiled LP objective offset differs from its envelope shift")

        expected_row_semantics: list[
            tuple[
                ReducedSizingConstraintKind,
                LinearProgramConstraintUnit,
                int | None,
                int | None,
                int | None,
            ]
        ] = []
        for opener in range(self.layout.opener_count):
            expected_row_semantics.extend(
                (
                    (
                        ReducedSizingConstraintKind.POLICY_MASS_UPPER,
                        LinearProgramConstraintUnit.DIMENSIONLESS,
                        opener,
                        None,
                        None,
                    ),
                    (
                        ReducedSizingConstraintKind.POLICY_MASS_LOWER,
                        LinearProgramConstraintUnit.DIMENSIONLESS,
                        opener,
                        None,
                        None,
                    ),
                )
            )
        for responder in range(self.layout.responder_count):
            for bet_index in range(self.layout.bet_count):
                expected_row_semantics.extend(
                    (
                        (
                            ReducedSizingConstraintKind.FOLD_ENVELOPE,
                            LinearProgramConstraintUnit.CHIPS,
                            None,
                            responder,
                            bet_index,
                        ),
                        (
                            ReducedSizingConstraintKind.CALL_ENVELOPE,
                            LinearProgramConstraintUnit.CHIPS,
                            None,
                            responder,
                            bet_index,
                        ),
                    )
                )
        actual_row_semantics = [
            (row.kind, row.unit, row.opener_index, row.responder_index, row.bet_index)
            for row in self.rows
        ]
        if actual_row_semantics != expected_row_semantics:
            raise ValueError("compiled LP row semantics or ordering drifted")

    @property
    def coefficients(self) -> tuple[tuple[float, ...], ...]:
        return tuple(row.coefficients for row in self.rows)

    @property
    def bounds(self) -> tuple[float, ...]:
        return tuple(row.bound for row in self.rows)

    @property
    def row_units(self) -> tuple[LinearProgramConstraintUnit, ...]:
        return tuple(row.unit for row in self.rows)

    @property
    def digest(self) -> str:
        payload = {
            "bet_sizes": self.bet_sizes,
            "bounds_hex": tuple(value.hex() for value in self.bounds),
            "coefficient_hex": tuple(
                tuple(value.hex() for value in row) for row in self.coefficients
            ),
            "layout": {
                "action_count": self.layout.action_count,
                "bet_count": self.layout.bet_count,
                "envelope_variable_count": self.layout.envelope_variable_count,
                "opener_count": self.layout.opener_count,
                "policy_variable_count": self.layout.policy_variable_count,
                "responder_count": self.layout.responder_count,
                "variable_count": self.layout.variable_count,
            },
            "maximum_stake_chips_hex": self.maximum_stake_chips.hex(),
            "objective_hex": tuple(value.hex() for value in self.objective),
            "objective_offset_chips_hex": self.objective_offset_chips.hex(),
            "objective_unit": self.objective_unit.value,
            "payoff_span_chips_hex": self.payoff_span_chips.hex(),
            "row_semantics": tuple(
                (
                    row.kind.value,
                    row.unit.value,
                    row.opener_index,
                    row.responder_index,
                    row.bet_index,
                )
                for row in self.rows
            ),
            "trusted_box_lower_hex": tuple(value.hex() for value in self.trusted_box_lower_bounds),
            "trusted_box_upper_hex": tuple(value.hex() for value in self.trusted_box_upper_bounds),
            "variable_units": tuple(unit.value for unit in self.variable_units),
            "version": "semantic-reduced-river-sizing-lp-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def compile_reduced_river_sizing_lp(
    *,
    pot: int,
    stack: int,
    minimum_bet: int,
    joint_probabilities: tuple[tuple[Fraction, ...], ...],
    showdown_signs: tuple[tuple[int, ...], ...],
    bet_sizes: tuple[int, ...],
) -> ReducedRiverSizingLinearProgram:
    """Compile the exact legacy compact formulation without invoking a backend."""

    exact_pot = _require_integer(pot, label="reduced pot", positive=True)
    effective_stack = _require_integer(stack, label="reduced stack", positive=True)
    if exact_pot % 2:
        raise ValueError("reduced zero-sum pot must split into integer half-pot units")
    sizes = validate_reduced_river_bet_sizes(
        minimum_bet=minimum_bet,
        stack=effective_stack,
        bet_sizes=bet_sizes,
    )
    if not isinstance(joint_probabilities, tuple) or not joint_probabilities:
        raise TypeError("joint probabilities must have a nonempty immutable opener axis")
    opener_count = len(joint_probabilities)
    if any(not isinstance(row, tuple) or not row for row in joint_probabilities):
        raise TypeError("joint probabilities must have nonempty immutable rows")
    responder_count = len(joint_probabilities[0])
    if any(len(row) != responder_count for row in joint_probabilities):
        raise TypeError("joint-probability rows must share one responder width")
    if any(
        not isinstance(probability, Fraction) or probability <= 0
        for row in joint_probabilities
        for probability in row
    ):
        raise TypeError("joint probabilities must be positive exact fractions")
    if (
        sum(
            (probability for row in joint_probabilities for probability in row),
            start=Fraction(0),
        )
        != 1
    ):
        raise ValueError("joint probabilities must sum exactly to one")
    if (
        not isinstance(showdown_signs, tuple)
        or len(showdown_signs) != opener_count
        or any(not isinstance(row, tuple) or len(row) != responder_count for row in showdown_signs)
    ):
        raise TypeError("showdown signs must align with the exact joint range")
    if any(
        isinstance(sign, bool) or not isinstance(sign, int) or sign not in (-1, 0, 1)
        for row in showdown_signs
        for sign in row
    ):
        raise ValueError("showdown signs must lie in {-1, 0, 1}")

    action_count = 1 + len(sizes)
    policy_variables = opener_count * action_count
    envelope_variables = responder_count * len(sizes)
    variable_count = policy_variables + envelope_variables
    layout = ReducedSizingLpLayout(
        opener_count=opener_count,
        responder_count=responder_count,
        bet_count=len(sizes),
        action_count=action_count,
        policy_variable_count=policy_variables,
        envelope_variable_count=envelope_variables,
        variable_count=variable_count,
    )
    objective = [0.0] * variable_count
    rows: list[ReducedSizingLpRow] = []
    half_pot = exact_pot / 2.0
    maximum_stake = half_pot + effective_stack

    for opener in range(opener_count):
        objective[layout.policy_index(opener, 0)] = sum(
            float(joint_probabilities[opener][responder])
            * showdown_signs[opener][responder]
            * half_pot
            for responder in range(responder_count)
        )
        coefficients = [0.0] * variable_count
        for action in range(action_count):
            coefficients[layout.policy_index(opener, action)] = 1.0
        rows.append(
            ReducedSizingLpRow(
                coefficients=tuple(coefficients),
                bound=1.0,
                kind=ReducedSizingConstraintKind.POLICY_MASS_UPPER,
                unit=LinearProgramConstraintUnit.DIMENSIONLESS,
                opener_index=opener,
            )
        )
        rows.append(
            ReducedSizingLpRow(
                coefficients=tuple(-value for value in coefficients),
                bound=-1.0,
                kind=ReducedSizingConstraintKind.POLICY_MASS_LOWER,
                unit=LinearProgramConstraintUnit.DIMENSIONLESS,
                opener_index=opener,
            )
        )

    for responder in range(responder_count):
        for bet_index, bet in enumerate(sizes):
            envelope = layout.envelope_index(responder, bet_index)
            objective[envelope] = 1.0
            fold_coefficients = [0.0] * variable_count
            call_coefficients = [0.0] * variable_count
            fold_coefficients[envelope] = 1.0
            call_coefficients[envelope] = 1.0
            for opener in range(opener_count):
                probability = float(joint_probabilities[opener][responder])
                variable = layout.policy_index(opener, bet_index + 1)
                fold_coefficients[variable] = -probability * half_pot
                call_coefficients[variable] = (
                    -probability * showdown_signs[opener][responder] * (half_pot + bet)
                )
            rows.append(
                ReducedSizingLpRow(
                    coefficients=tuple(fold_coefficients),
                    bound=float(maximum_stake),
                    kind=ReducedSizingConstraintKind.FOLD_ENVELOPE,
                    unit=LinearProgramConstraintUnit.CHIPS,
                    responder_index=responder,
                    bet_index=bet_index,
                )
            )
            rows.append(
                ReducedSizingLpRow(
                    coefficients=tuple(call_coefficients),
                    bound=float(maximum_stake),
                    kind=ReducedSizingConstraintKind.CALL_ENVELOPE,
                    unit=LinearProgramConstraintUnit.CHIPS,
                    responder_index=responder,
                    bet_index=bet_index,
                )
            )

    payoff_span = float(exact_pot + 2 * effective_stack)
    return ReducedRiverSizingLinearProgram(
        bet_sizes=sizes,
        layout=layout,
        objective=tuple(objective),
        rows=tuple(rows),
        variable_units=(
            *(LinearProgramVariableUnit.POLICY_PROBABILITY for _ in range(policy_variables)),
            *(LinearProgramVariableUnit.SHIFTED_ENVELOPE_CHIPS for _ in range(envelope_variables)),
        ),
        trusted_box_lower_bounds=(0.0,) * variable_count,
        trusted_box_upper_bounds=(
            *(1.0 for _ in range(policy_variables)),
            *(payoff_span for _ in range(envelope_variables)),
        ),
        objective_unit=LinearProgramObjectiveUnit.CHIPS,
        objective_offset_chips=float(-envelope_variables * maximum_stake),
        maximum_stake_chips=float(maximum_stake),
        payoff_span_chips=payoff_span,
    )


__all__ = [
    "LinearProgramConstraintUnit",
    "LinearProgramObjectiveUnit",
    "LinearProgramVariableUnit",
    "ReducedRiverSizingLinearProgram",
    "ReducedSizingConstraintKind",
    "ReducedSizingLpLayout",
    "ReducedSizingLpRow",
    "compile_reduced_river_sizing_lp",
    "validate_reduced_river_bet_sizes",
]
