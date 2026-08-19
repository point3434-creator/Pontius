from __future__ import annotations

import unittest

from pontius.linear_program import maximize_linear_program


class LinearProgramTests(unittest.TestCase):
    def test_bounded_program_finds_intersection_vertex(self) -> None:
        result = maximize_linear_program(
            (1.0, 1.0),
            ((1.0, 2.0), (4.0, 2.0)),
            (4.0, 12.0),
        )

        self.assertAlmostEqual(result.variables[0], 8.0 / 3.0)
        self.assertAlmostEqual(result.variables[1], 2.0 / 3.0)
        self.assertAlmostEqual(result.objective, 10.0 / 3.0)

    def test_phase_one_handles_equality_as_two_inequalities(self) -> None:
        result = maximize_linear_program(
            (2.0,),
            ((1.0,), (-1.0,)),
            (1.0, -1.0),
        )

        self.assertAlmostEqual(result.variables[0], 1.0)
        self.assertAlmostEqual(result.objective, 2.0)

    def test_infeasible_and_unbounded_programs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "infeasible"):
            maximize_linear_program(
                (1.0,),
                ((1.0,), (-1.0,)),
                (0.0, -1.0),
            )
        with self.assertRaisesRegex(ValueError, "unbounded"):
            maximize_linear_program((1.0,), (), ())

    def test_invalid_shape_and_nonfinite_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "width"):
            maximize_linear_program((1.0,), ((1.0, 2.0),), (1.0,))
        with self.assertRaisesRegex(ValueError, "finite"):
            maximize_linear_program((float("inf"),), (), ())


if __name__ == "__main__":
    unittest.main()
