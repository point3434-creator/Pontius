from __future__ import annotations

import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

from pontius.reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    LinearProgramObjectiveUnit,
    LinearProgramVariableUnit,
    ReducedSizingConstraintKind,
    compile_reduced_river_sizing_lp,
)
from pontius.reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ProbabilitySimplexAllowance,
    ReducedRiverSizingContext,
    solve_reduced_river_sizing,
)
from tests.test_reduced_river_sizing_oracle import _contexts


def _legacy_formula(
    context: ReducedRiverSizingContext,
    sizes: tuple[int, ...],
) -> tuple[list[float], list[list[float]], list[float]]:
    """Independent reproduction of the pre-extraction formula in commit f8936ac."""

    opener_count = len(context.opener_hands)
    responder_count = len(context.responder_hands)
    action_count = 1 + len(sizes)
    policy_variables = opener_count * action_count
    envelope_variables = responder_count * len(sizes)
    variable_count = policy_variables + envelope_variables
    objective = [0.0] * variable_count
    coefficients: list[list[float]] = []
    bounds: list[float] = []
    signs = context.showdown_signs
    half_pot = context.pot / 2.0
    maximum_stake = half_pot + context.stack

    def policy_index(opener: int, action: int) -> int:
        return opener * action_count + action

    def envelope_index(responder: int, bet_index: int) -> int:
        return policy_variables + responder * len(sizes) + bet_index

    for opener in range(opener_count):
        objective[policy_index(opener, 0)] = sum(
            float(context.joint_probabilities[opener][responder].fraction)
            * signs[opener][responder]
            * half_pot
            for responder in range(responder_count)
        )
        row = [0.0] * variable_count
        for action in range(action_count):
            row[policy_index(opener, action)] = 1.0
        coefficients.append(row)
        bounds.append(1.0)
        coefficients.append([-value for value in row])
        bounds.append(-1.0)

    for responder in range(responder_count):
        for bet_index, bet in enumerate(sizes):
            envelope = envelope_index(responder, bet_index)
            objective[envelope] = 1.0
            fold_row = [0.0] * variable_count
            call_row = [0.0] * variable_count
            fold_row[envelope] = 1.0
            call_row[envelope] = 1.0
            for opener in range(opener_count):
                probability = float(context.joint_probabilities[opener][responder].fraction)
                variable = policy_index(opener, bet_index + 1)
                fold_row[variable] = -probability * half_pot
                call_row[variable] = -probability * signs[opener][responder] * (half_pot + bet)
            coefficients.append(fold_row)
            bounds.append(maximum_stake)
            coefficients.append(call_row)
            bounds.append(maximum_stake)
    return objective, coefficients, bounds


def _float_hex(values: object) -> object:
    if isinstance(values, float):
        return values.hex()
    if isinstance(values, (list, tuple)):
        return tuple(_float_hex(value) for value in values)
    return values


def _compile(
    context: ReducedRiverSizingContext,
    sizes: tuple[int, ...],
):
    return compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=context.showdown_signs,
        bet_sizes=sizes,
    )


class _StopBeforeSolve(Exception):
    pass


class ReducedRiverSizingLpTests(unittest.TestCase):
    def test_compiler_is_bit_exact_to_the_independent_legacy_formula(self) -> None:
        for context in _contexts():
            for sizes in (
                (context.minimum_bet, context.stack),
                tuple(range(context.minimum_bet, context.stack + 1)),
            ):
                expected_objective, expected_coefficients, expected_bounds = _legacy_formula(
                    context, sizes
                )
                compiled = _compile(context, sizes)
                self.assertEqual(
                    _float_hex(compiled.objective),
                    _float_hex(expected_objective),
                )
                self.assertEqual(
                    _float_hex(compiled.coefficients),
                    _float_hex(expected_coefficients),
                )
                self.assertEqual(
                    _float_hex(compiled.bounds),
                    _float_hex(expected_bounds),
                )
                self.assertEqual(
                    compiled.objective_offset_chips,
                    -compiled.layout.envelope_variable_count * compiled.maximum_stake_chips,
                )

    def test_live_oracle_passes_the_compiled_matrix_to_the_frozen_backend(self) -> None:
        context = _contexts()[1]
        sizes = (context.minimum_bet, context.stack)
        compiled = _compile(context, sizes)
        with patch(
            "pontius.reduced_river_sizing_oracle.maximize_linear_program",
            side_effect=_StopBeforeSolve,
        ) as backend, self.assertRaises(_StopBeforeSolve):
            solve_reduced_river_sizing(
                context,
                sizes,
                probability_allowance=ProbabilitySimplexAllowance(1e-9),
                chip_allowance=ChipObjectiveAllowance(1e-9),
                solver_tolerance=1e-11,
                max_pivots=4096,
            )
        objective, coefficients, bounds = backend.call_args.args
        self.assertEqual(_float_hex(objective), _float_hex(compiled.objective))
        self.assertEqual(_float_hex(coefficients), _float_hex(compiled.coefficients))
        self.assertEqual(_float_hex(bounds), _float_hex(compiled.bounds))
        self.assertEqual(
            backend.call_args.kwargs,
            {"tolerance": 1e-11, "max_pivots": 4096},
        )

    def test_units_layout_and_trusted_boxes_are_semantic(self) -> None:
        context = _contexts()[0]
        compiled = _compile(context, (2, 20))
        layout = compiled.layout
        self.assertEqual(layout.action_count, 3)
        self.assertEqual(layout.policy_variable_count, 9)
        self.assertEqual(layout.envelope_variable_count, 6)
        self.assertEqual(layout.variable_count, 15)
        self.assertEqual(
            tuple(row.kind for row in compiled.rows[:6]),
            (
                ReducedSizingConstraintKind.POLICY_MASS_UPPER,
                ReducedSizingConstraintKind.POLICY_MASS_LOWER,
            )
            * 3,
        )
        self.assertEqual(
            compiled.row_units[:6],
            (LinearProgramConstraintUnit.DIMENSIONLESS,) * 6,
        )
        self.assertEqual(
            compiled.row_units[6:],
            (LinearProgramConstraintUnit.CHIPS,) * 12,
        )
        self.assertEqual(
            compiled.variable_units[:9],
            (LinearProgramVariableUnit.POLICY_PROBABILITY,) * 9,
        )
        self.assertEqual(
            compiled.variable_units[9:],
            (LinearProgramVariableUnit.SHIFTED_ENVELOPE_CHIPS,) * 6,
        )
        self.assertEqual(compiled.trusted_box_lower_bounds, (0.0,) * 15)
        self.assertEqual(compiled.trusted_box_upper_bounds[:9], (1.0,) * 9)
        self.assertEqual(
            compiled.trusted_box_upper_bounds[9:],
            (float(context.payoff_span),) * 6,
        )
        self.assertIs(compiled.objective_unit, LinearProgramObjectiveUnit.CHIPS)
        self.assertEqual(compiled.digest, _compile(context, (2, 20)).digest)

    def test_malformed_units_shapes_and_exact_inputs_fail_closed(self) -> None:
        context = _contexts()[0]
        compiled = _compile(context, (2, 20))
        with self.assertRaisesRegex(ValueError, "policy-mass"):
            replace(
                compiled.rows[0],
                unit=LinearProgramConstraintUnit.CHIPS,
            )
        with self.assertRaisesRegex(ValueError, "semantic blocks"):
            replace(
                compiled,
                variable_units=(
                    LinearProgramVariableUnit.DIMENSIONLESS_GENERIC,
                    *compiled.variable_units[1:],
                ),
            )
        with self.assertRaisesRegex(ValueError, "trusted upper"):
            replace(
                compiled,
                trusted_box_upper_bounds=(2.0, *compiled.trusted_box_upper_bounds[1:]),
            )
        probabilities = tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        )
        with self.assertRaisesRegex(TypeError, "exact fractions"):
            compile_reduced_river_sizing_lp(
                pot=context.pot,
                stack=context.stack,
                minimum_bet=context.minimum_bet,
                joint_probabilities=(
                    (0.1, *probabilities[0][1:]),  # type: ignore[arg-type]
                    *probabilities[1:],
                ),
                showdown_signs=context.showdown_signs,
                bet_sizes=(2, 20),
            )
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            compile_reduced_river_sizing_lp(
                pot=context.pot,
                stack=context.stack,
                minimum_bet=context.minimum_bet,
                joint_probabilities=tuple(
                    tuple(Fraction(1, 10) for _ in row) for row in probabilities
                ),
                showdown_signs=context.showdown_signs,
                bet_sizes=(2, 20),
            )


if __name__ == "__main__":
    unittest.main()
