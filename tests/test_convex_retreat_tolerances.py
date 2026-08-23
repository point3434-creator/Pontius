from __future__ import annotations

import copy
import math
import unittest

from pontius.convex_retreat_tolerances import (
    H32_V1_NUMERICALLY_EQUIVALENT_TOLERANCES,
    AbsoluteReversalAllowance,
    AbsoluteULGapAllowance,
    ConvexRetreatTolerances,
    EpigraphSeparationAllowance,
    InterceptIdentityAllowance,
    RelativeReversalAllowance,
    ResidentPrimalResidualAllowance,
    SelectorMarginAllowance,
    absolute_u_l_gap_is_accepted,
    bounded_minimization_gap,
    epigraph_separation_is_required,
    intercept_identity_is_accepted,
    parse_convex_retreat_tolerances,
    resident_primal_residual_is_accepted,
    selector_margin_is_conservative,
)
from pontius.h32_one_round_convex_master import bounded_gap as frozen_bounded_gap


def _config() -> dict[str, float]:
    return {
        "relative_reversal_allowance": 1e-3,
        "absolute_reversal_allowance": 1e-6,
        "absolute_u_l_gap_allowance": 0.1,
        "selector_margin_allowance": 0.01,
        "intercept_identity_allowance": 0.02,
        "epigraph_separation_allowance": 0.03,
        "resident_primal_residual_allowance": 0.04,
    }


class ConvexRetreatToleranceTests(unittest.TestCase):
    def test_parser_requires_seven_distinct_semantic_fields(self) -> None:
        parsed = parse_convex_retreat_tolerances(_config())
        self.assertIs(type(parsed.relative_reversal), RelativeReversalAllowance)
        self.assertIs(type(parsed.absolute_reversal), AbsoluteReversalAllowance)
        self.assertIs(type(parsed.absolute_u_l_gap), AbsoluteULGapAllowance)
        self.assertIs(type(parsed.selector_margin), SelectorMarginAllowance)
        self.assertIs(type(parsed.intercept_identity), InterceptIdentityAllowance)
        self.assertIs(type(parsed.epigraph_separation), EpigraphSeparationAllowance)
        self.assertIs(
            type(parsed.resident_primal_residual),
            ResidentPrimalResidualAllowance,
        )

        aliased = _config()
        del aliased["absolute_u_l_gap_allowance"]
        aliased["bound_tolerance"] = 0.1
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            parse_convex_retreat_tolerances(aliased)

        missing_identity = _config()
        del missing_identity["intercept_identity_allowance"]
        with self.assertRaisesRegex(ValueError, "intercept_identity_allowance"):
            parse_convex_retreat_tolerances(missing_identity)

    def test_typed_gate_apis_reject_equal_valued_cross_use(self) -> None:
        same = 1e-8
        relative = RelativeReversalAllowance(same)
        absolute_reversal = AbsoluteReversalAllowance(same)
        absolute = AbsoluteULGapAllowance(same)
        selector = SelectorMarginAllowance(same)
        identity = InterceptIdentityAllowance(same)
        separation = EpigraphSeparationAllowance(same)
        resident = ResidentPrimalResidualAllowance(same)

        with self.assertRaisesRegex(TypeError, "RelativeReversalAllowance"):
            bounded_minimization_gap(
                1.0,
                1.0,
                reversal_allowance=absolute,  # type: ignore[arg-type]
                absolute_reversal_allowance=absolute_reversal,
            )
        with self.assertRaisesRegex(TypeError, "AbsoluteReversalAllowance"):
            bounded_minimization_gap(
                1.0,
                1.0,
                reversal_allowance=relative,
                absolute_reversal_allowance=absolute,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "AbsoluteULGapAllowance"):
            absolute_u_l_gap_is_accepted(0.0, gap_allowance=relative)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "SelectorMarginAllowance"):
            selector_margin_is_conservative(
                0.0,
                margin_allowance=identity,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "InterceptIdentityAllowance"):
            intercept_identity_is_accepted(
                0.0,
                identity_allowance=selector,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "EpigraphSeparationAllowance"):
            epigraph_separation_is_required(
                0.0,
                separation_allowance=resident,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "ResidentPrimalResidualAllowance"):
            resident_primal_residual_is_accepted(
                0.0,
                residual_allowance=separation,  # type: ignore[arg-type]
            )

    def test_relative_reversal_and_absolute_gap_mutate_independently(self) -> None:
        base = parse_convex_retreat_tolerances(_config())
        self.assertEqual(
            bounded_minimization_gap(
                1.0,
                1.0005,
                reversal_allowance=base.relative_reversal,
                absolute_reversal_allowance=base.absolute_reversal,
            ),
            0.0,
        )
        self.assertTrue(
            absolute_u_l_gap_is_accepted(
                0.05,
                gap_allowance=base.absolute_u_l_gap,
            )
        )

        changed_relative = _config()
        changed_relative["relative_reversal_allowance"] = 1e-4
        relative = parse_convex_retreat_tolerances(changed_relative)
        with self.assertRaisesRegex(ArithmeticError, "lower bound"):
            bounded_minimization_gap(
                1.0,
                1.0005,
                reversal_allowance=relative.relative_reversal,
                absolute_reversal_allowance=relative.absolute_reversal,
            )
        self.assertTrue(
            absolute_u_l_gap_is_accepted(
                0.05,
                gap_allowance=relative.absolute_u_l_gap,
            )
        )

        changed_absolute = _config()
        changed_absolute["absolute_u_l_gap_allowance"] = 0.01
        absolute = parse_convex_retreat_tolerances(changed_absolute)
        self.assertEqual(
            bounded_minimization_gap(
                1.0,
                1.0005,
                reversal_allowance=absolute.relative_reversal,
                absolute_reversal_allowance=absolute.absolute_reversal,
            ),
            0.0,
        )
        self.assertFalse(
            absolute_u_l_gap_is_accepted(
                0.05,
                gap_allowance=absolute.absolute_u_l_gap,
            )
        )

    def test_selector_and_intercept_mutate_independently(self) -> None:
        base = parse_convex_retreat_tolerances(_config())
        self.assertTrue(
            selector_margin_is_conservative(
                -0.005,
                margin_allowance=base.selector_margin,
            )
        )
        self.assertTrue(
            intercept_identity_is_accepted(
                0.015,
                identity_allowance=base.intercept_identity,
            )
        )

        changed_selector = _config()
        changed_selector["selector_margin_allowance"] = 0.001
        selector = parse_convex_retreat_tolerances(changed_selector)
        self.assertFalse(
            selector_margin_is_conservative(
                -0.005,
                margin_allowance=selector.selector_margin,
            )
        )
        self.assertTrue(
            intercept_identity_is_accepted(
                0.015,
                identity_allowance=selector.intercept_identity,
            )
        )

        changed_identity = _config()
        changed_identity["intercept_identity_allowance"] = 0.01
        identity = parse_convex_retreat_tolerances(changed_identity)
        self.assertTrue(
            selector_margin_is_conservative(
                -0.005,
                margin_allowance=identity.selector_margin,
            )
        )
        self.assertFalse(
            intercept_identity_is_accepted(
                0.015,
                identity_allowance=identity.intercept_identity,
            )
        )

    def test_epigraph_separation_and_resident_primal_mutate_independently(self) -> None:
        base = parse_convex_retreat_tolerances(_config())
        self.assertTrue(
            epigraph_separation_is_required(
                0.035,
                separation_allowance=base.epigraph_separation,
            )
        )
        self.assertTrue(
            resident_primal_residual_is_accepted(
                0.035,
                residual_allowance=base.resident_primal_residual,
            )
        )

        changed_separation = _config()
        changed_separation["epigraph_separation_allowance"] = 0.04
        separation = parse_convex_retreat_tolerances(changed_separation)
        self.assertFalse(
            epigraph_separation_is_required(
                0.035,
                separation_allowance=separation.epigraph_separation,
            )
        )
        self.assertTrue(
            resident_primal_residual_is_accepted(
                0.035,
                residual_allowance=separation.resident_primal_residual,
            )
        )

        changed_resident = _config()
        changed_resident["resident_primal_residual_allowance"] = 0.03
        resident = parse_convex_retreat_tolerances(changed_resident)
        self.assertTrue(
            epigraph_separation_is_required(
                0.035,
                separation_allowance=resident.epigraph_separation,
            )
        )
        self.assertFalse(
            resident_primal_residual_is_accepted(
                0.035,
                residual_allowance=resident.resident_primal_residual,
            )
        )

    def test_current_frozen_values_are_preserved_without_aliasing_types(self) -> None:
        tolerances = H32_V1_NUMERICALLY_EQUIVALENT_TOLERANCES
        self.assertEqual(tolerances.relative_reversal.relative_fraction, 1e-8)
        self.assertEqual(tolerances.absolute_reversal.absolute_error, 1e-8)
        self.assertEqual(tolerances.absolute_u_l_gap.absolute_gap, 1e-8)
        self.assertEqual(tolerances.selector_margin.absolute_margin, 2e-11)
        self.assertEqual(tolerances.intercept_identity.absolute_error, 2e-11)
        self.assertEqual(tolerances.epigraph_separation.absolute_residual, 1e-9)
        self.assertEqual(
            tolerances.resident_primal_residual.absolute_residual,
            1e-8,
        )
        self.assertIsNot(
            type(tolerances.relative_reversal),
            type(tolerances.absolute_u_l_gap),
        )
        self.assertIsNot(
            type(tolerances.selector_margin),
            type(tolerances.intercept_identity),
        )
        self.assertIsNot(
            type(tolerances.epigraph_separation),
            type(tolerances.resident_primal_residual),
        )

    def test_successor_gates_reproduce_the_current_frozen_outcomes(self) -> None:
        tolerances = H32_V1_NUMERICALLY_EQUIVALENT_TOLERANCES
        for upper, lower in (
            (2.0, 1.5),
            (1.0, 1.0 + 5e-9),
            (0.0, 0.0),
            (1_000.0, 1_000.0 + 5e-6),
        ):
            with self.subTest(upper=upper, lower=lower):
                frozen = frozen_bounded_gap(
                    upper,
                    lower,
                    tolerance=1e-8,
                )
                successor = bounded_minimization_gap(
                    upper,
                    lower,
                    reversal_allowance=tolerances.relative_reversal,
                    absolute_reversal_allowance=tolerances.absolute_reversal,
                )
                self.assertEqual(successor, frozen)
                self.assertEqual(
                    absolute_u_l_gap_is_accepted(
                        successor,
                        gap_allowance=tolerances.absolute_u_l_gap,
                    ),
                    frozen <= 1e-8,
                )

        with self.assertRaises(ArithmeticError):
            frozen_bounded_gap(1.0, 1.001, tolerance=1e-8)
        with self.assertRaises(ArithmeticError):
            bounded_minimization_gap(
                1.0,
                1.001,
                reversal_allowance=tolerances.relative_reversal,
                absolute_reversal_allowance=tolerances.absolute_reversal,
            )

        for margin in (-3e-11, -1e-11, 0.0, 1e-9):
            self.assertEqual(
                selector_margin_is_conservative(
                    margin,
                    margin_allowance=tolerances.selector_margin,
                ),
                margin >= -2e-11,
            )
        for identity_error in (0.0, 1e-11, 3e-11):
            self.assertEqual(
                intercept_identity_is_accepted(
                    identity_error,
                    identity_allowance=tolerances.intercept_identity,
                ),
                identity_error <= max(1e-12, 2e-11),
            )
        for residual in (0.0, 2e-9, 2e-8):
            self.assertEqual(
                epigraph_separation_is_required(
                    residual,
                    separation_allowance=tolerances.epigraph_separation,
                ),
                residual > 1e-9,
            )
            self.assertEqual(
                resident_primal_residual_is_accepted(
                    residual,
                    residual_allowance=tolerances.resident_primal_residual,
                ),
                residual <= 1e-8,
            )

    def test_contract_constructor_rejects_a_cross_wired_field(self) -> None:
        values = H32_V1_NUMERICALLY_EQUIVALENT_TOLERANCES
        with self.assertRaisesRegex(TypeError, "absolute_u_l_gap"):
            ConvexRetreatTolerances(
                relative_reversal=values.relative_reversal,
                absolute_reversal=values.absolute_reversal,
                absolute_u_l_gap=values.relative_reversal,  # type: ignore[arg-type]
                selector_margin=values.selector_margin,
                intercept_identity=values.intercept_identity,
                epigraph_separation=values.epigraph_separation,
                resident_primal_residual=values.resident_primal_residual,
            )

    def test_parser_is_fail_closed_on_non_json_numbers(self) -> None:
        for bad in (True, math.inf, math.nan, -1.0, "1e-8"):
            with self.subTest(bad=bad):
                config = copy.deepcopy(_config())
                config["relative_reversal_allowance"] = bad  # type: ignore[assignment]
                with self.assertRaises((TypeError, ValueError)):
                    parse_convex_retreat_tolerances(config)

    def test_near_zero_reversal_does_not_receive_an_implicit_unit_scale(self) -> None:
        with self.assertRaisesRegex(ArithmeticError, "lower bound"):
            bounded_minimization_gap(
                1e-20,
                5e-11,
                reversal_allowance=RelativeReversalAllowance(1e-10),
                absolute_reversal_allowance=AbsoluteReversalAllowance(1e-12),
            )


if __name__ == "__main__":
    unittest.main()
