from __future__ import annotations

import unittest

from pontius.matrix_game import solve_zero_sum_matrix_game


class MatrixGameTests(unittest.TestCase):
    def test_matching_pennies_has_uniform_zero_value_solution(self) -> None:
        result = solve_zero_sum_matrix_game(((1.0, -1.0), (-1.0, 1.0)))

        self.assertAlmostEqual(result.value, 0.0)
        self.assertAlmostEqual(result.row_strategy[0], 0.5)
        self.assertAlmostEqual(result.column_strategy[0], 0.5)
        self.assertLessEqual(result.duality_gap, 1e-10)

    def test_dominated_column_is_never_selected(self) -> None:
        result = solve_zero_sum_matrix_game(((2.0, 0.0), (1.0, -1.0)))

        self.assertAlmostEqual(result.value, 1.0)
        self.assertAlmostEqual(result.column_strategy[0], 1.0)
        self.assertAlmostEqual(result.column_strategy[1], 0.0)
        self.assertAlmostEqual(result.row_strategy[1], 1.0)

    def test_rectangular_game_matches_declared_saddle_point(self) -> None:
        result = solve_zero_sum_matrix_game(
            ((3.0, 1.0, 2.0), (4.0, 2.0, 5.0))
        )

        self.assertAlmostEqual(result.value, 3.0)
        self.assertAlmostEqual(result.row_strategy[0], 1.0)
        self.assertAlmostEqual(result.column_strategy[0], 1.0)

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            solve_zero_sum_matrix_game(())
        with self.assertRaisesRegex(ValueError, "rectangular"):
            solve_zero_sum_matrix_game(((1.0,), (1.0, 2.0)))
        with self.assertRaisesRegex(ValueError, "finite"):
            solve_zero_sum_matrix_game(((float("nan"),),))


if __name__ == "__main__":
    unittest.main()
