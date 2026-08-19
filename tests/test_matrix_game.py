from __future__ import annotations

import unittest
from unittest.mock import patch

from pontius.matrix_game import _PackingSimplexStalled, solve_zero_sum_matrix_game


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
        with self.assertRaisesRegex(ValueError, "max_pivots"):
            solve_zero_sum_matrix_game(((0.0,),), max_pivots=0)

    def test_degenerate_duplicate_strategies_are_verified(self) -> None:
        base_columns = (
            (3.0, -1.0, 2.0),
            (-2.0, 4.0, 0.0),
            (1.0, 2.0, -3.0),
        )
        payoffs = tuple(
            tuple(value for value in row for _ in range(32))
            for row in base_columns
        )

        result = solve_zero_sum_matrix_game(payoffs)

        self.assertLessEqual(result.duality_gap, 1e-10)
        self.assertAlmostEqual(sum(result.row_strategy), 1.0)
        self.assertAlmostEqual(sum(result.column_strategy), 1.0)
        self.assertIn(result.simplex_backend, {"packing", "two_phase_fallback"})

    def test_stalled_packing_tableau_uses_verified_two_phase_fallback(self) -> None:
        with patch(
            "pontius.matrix_game._packing_simplex",
            side_effect=_PackingSimplexStalled("synthetic stall"),
        ):
            result = solve_zero_sum_matrix_game(
                ((1.0, -1.0), (-1.0, 1.0))
            )

        self.assertEqual(result.simplex_backend, "two_phase_fallback")
        self.assertLessEqual(result.duality_gap, 1e-10)


if __name__ == "__main__":
    unittest.main()
