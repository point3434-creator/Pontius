from __future__ import annotations

import random
import unittest
from fractions import Fraction

from pontius.linear_program import maximize_linear_program
from pontius.linear_program_certificate import (
    certify_bounded_minimization_lower_bound,
    certify_negated_bounded_maximization_lower_bound,
)


class LinearProgramCertificateTests(unittest.TestCase):
    def test_minimization_residual_correction_repairs_unsafe_raw_dual(self) -> None:
        # min x subject to -x <= -1/2 and 0 <= x <= 1 has optimum 1/2.
        # lambda=-1.1 gives the unsafe uncorrected constant 0.55, but its
        # reduced-cost residual contributes -0.1 over the trusted box.
        certificate = certify_bounded_minimization_lower_bound(
            (1.0,),
            ((-1.0,),),
            (-0.5,),
            (-1.1,),
            variable_lower_bounds=(0.0,),
            variable_upper_bounds=(1.0,),
        )

        self.assertGreater(certificate.lagrangian_constant_lower_bound, 0.5)
        self.assertLess(certificate.box_residual_correction_lower_bound, -0.09)
        self.assertLessEqual(certificate.lower_bound, 0.45)
        self.assertAlmostEqual(certificate.nominal_lagrangian_value, 0.45)

    def test_wrong_sign_minimization_multiplier_is_clipped(self) -> None:
        certificate = certify_bounded_minimization_lower_bound(
            (1.0,),
            ((-1.0,),),
            (-0.5,),
            (0.2,),
            variable_lower_bounds=(0.0,),
            variable_upper_bounds=(1.0,),
        )

        self.assertEqual(certificate.inequality_multiplier_sign_clips, 1)
        self.assertEqual(certificate.lower_bound, 0.0)

    def test_unrestricted_equality_multiplier_remains_safe(self) -> None:
        # min x subject to x=1/2.  nu=2 is not stationary, so the box term
        # exactly cancels its over-large constant.
        certificate = certify_bounded_minimization_lower_bound(
            (1.0,),
            (),
            (),
            (),
            equality_coefficients=((1.0,),),
            equality_bounds=(0.5,),
            equality_multipliers=(2.0,),
            variable_lower_bounds=(0.0,),
            variable_upper_bounds=(1.0,),
        )

        self.assertLessEqual(certificate.lower_bound, 0.0)
        self.assertAlmostEqual(certificate.nominal_lagrangian_value, 0.0)

    def test_negated_maximum_adapter_uses_opposite_dual_sign(self) -> None:
        # max -t subject to -t<=-1/2, 0<=t<=1 is the negation of min t.
        certificate = certify_negated_bounded_maximization_lower_bound(
            (-1.0,),
            ((-1.0,),),
            (-0.5,),
            (1.1,),
            variable_lower_bounds=(0.0,),
            variable_upper_bounds=(1.0,),
        )

        self.assertGreater(certificate.lagrangian_constant_lower_bound, 0.5)
        self.assertLess(certificate.box_residual_correction_lower_bound, -0.09)
        self.assertLessEqual(certificate.lower_bound, 0.45)
        self.assertAlmostEqual(certificate.nominal_lagrangian_value, 0.45)

    def test_in_house_simplex_duals_certify_the_negated_objective(self) -> None:
        objective = (-1.0,)
        matrix = ((-1.0,), (1.0,))
        rhs = (-0.5, 1.0)
        solved = maximize_linear_program(objective, matrix, rhs)
        certificate = certify_negated_bounded_maximization_lower_bound(
            objective,
            matrix,
            rhs,
            solved.dual_variables,
            variable_lower_bounds=(0.0,),
            variable_upper_bounds=(1.0,),
        )

        self.assertAlmostEqual(solved.objective, -0.5)
        self.assertLessEqual(certificate.lower_bound, 0.5)
        self.assertAlmostEqual(certificate.lower_bound, 0.5)

    def test_nonfinite_or_untrusted_bounds_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            certify_bounded_minimization_lower_bound(
                (1.0,),
                (),
                (),
                (),
                variable_lower_bounds=(0.0,),
                variable_upper_bounds=(float("inf"),),
            )
        with self.assertRaisesRegex(ValueError, "reversed"):
            certify_bounded_minimization_lower_bound(
                (1.0,),
                (),
                (),
                (),
                variable_lower_bounds=(1.0,),
                variable_upper_bounds=(0.0,),
            )

    def test_outward_result_is_below_exact_float_lagrangian(self) -> None:
        rng = random.Random(0xC3A71F1C)
        values = (-1.3, -0.7, -0.1, 0.0, 0.2, 0.6, 1.1)
        for case in range(100):
            width = rng.randint(1, 4)
            row_count = rng.randint(0, 4)
            equality_count = rng.randint(0, 3)
            objective = tuple(rng.choice(values) for _ in range(width))
            matrix = tuple(
                tuple(rng.choice(values) for _ in range(width))
                for _ in range(row_count)
            )
            rhs = tuple(rng.choice(values) for _ in range(row_count))
            raw_dual = tuple(rng.choice(values) for _ in range(row_count))
            equality_matrix = tuple(
                tuple(rng.choice(values) for _ in range(width))
                for _ in range(equality_count)
            )
            equality_rhs = tuple(rng.choice(values) for _ in range(equality_count))
            equality_dual = tuple(
                rng.choice(values) for _ in range(equality_count)
            )
            lower = tuple(rng.choice((-1.3, -0.1, 0.0)) for _ in range(width))
            upper = tuple(
                rng.choice(tuple(value for value in values if value >= left))
                for left in lower
            )
            certificate = certify_bounded_minimization_lower_bound(
                objective,
                matrix,
                rhs,
                raw_dual,
                equality_coefficients=equality_matrix,
                equality_bounds=equality_rhs,
                equality_multipliers=equality_dual,
                variable_lower_bounds=lower,
                variable_upper_bounds=upper,
            )

            signed_dual = tuple(min(value, 0.0) for value in raw_dual)
            exact_constant = sum(
                (
                    Fraction.from_float(bound) * Fraction.from_float(multiplier)
                    for bound, multiplier in zip(rhs, signed_dual, strict=True)
                ),
                Fraction(0),
            ) + sum(
                (
                    Fraction.from_float(bound) * Fraction.from_float(multiplier)
                    for bound, multiplier in zip(
                        equality_rhs, equality_dual, strict=True
                    )
                ),
                Fraction(0),
            )
            exact_residuals = []
            for column, coefficient in enumerate(objective):
                residual = Fraction.from_float(coefficient)
                residual -= sum(
                    (
                        Fraction.from_float(matrix[row][column])
                        * Fraction.from_float(signed_dual[row])
                        for row in range(row_count)
                    ),
                    Fraction(0),
                )
                residual -= sum(
                    (
                        Fraction.from_float(equality_matrix[row][column])
                        * Fraction.from_float(equality_dual[row])
                        for row in range(equality_count)
                    ),
                    Fraction(0),
                )
                exact_residuals.append(residual)
            exact_lagrangian = exact_constant + sum(
                (
                    min(
                        Fraction.from_float(left) * residual,
                        Fraction.from_float(right) * residual,
                    )
                    for left, right, residual in zip(
                        lower, upper, exact_residuals, strict=True
                    )
                ),
                Fraction(0),
            )
            with self.subTest(case=case):
                self.assertLessEqual(
                    Fraction.from_float(certificate.lower_bound),
                    exact_lagrangian,
                )


if __name__ == "__main__":
    unittest.main()
