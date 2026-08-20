from __future__ import annotations

import unittest

import numpy as np

from pontius.seat_order_tt import (
    screen_six_seat_orders,
    transpose_seat_tensor,
    unordered_three_three_partitions,
)


class SeatOrderTTTests(unittest.TestCase):
    def test_screen_covers_all_orders_and_selects_deterministically(self) -> None:
        rng = np.random.default_rng(17)
        tensor = rng.normal(size=(2, 2, 2, 2, 2, 2))
        first = screen_six_seat_orders(
            tensor,
            first_halves=unordered_three_three_partitions(),
            relative_threshold=1e-12,
        )
        second = screen_six_seat_orders(
            tensor,
            first_halves=unordered_three_three_partitions(),
            relative_threshold=1e-12,
        )
        self.assertEqual(first.orders_screened, 360)
        self.assertEqual(len(first.partition_best), 10)
        self.assertEqual(first.selected, second.selected)
        self.assertEqual(tuple(sorted(first.selected.order)), tuple(range(6)))
        self.assertLess(
            first.maximum_partition_singular_value_relative_error,
            1e-12,
        )

    def test_rank_one_tensor_selects_unit_bonds_and_exact_storage(self) -> None:
        vectors = tuple(np.asarray([1.0, 2.0 + seat]) for seat in range(6))
        tensor = np.einsum("a,b,c,d,e,f->abcdef", *vectors)
        result = screen_six_seat_orders(
            tensor,
            first_halves=unordered_three_three_partitions(),
            relative_threshold=1e-12,
        )
        self.assertEqual(result.selected.numerical_ranks, (1, 1, 1, 1, 1, 1, 1))
        self.assertEqual(result.selected.estimated_storage_bytes, 6 * 2 * 8)
        np.testing.assert_array_equal(
            transpose_seat_tensor(tensor, tuple(range(6))),
            tensor,
        )

    def test_invalid_partition_and_order_are_rejected(self) -> None:
        tensor = np.ones((2,) * 6)
        with self.assertRaisesRegex(ValueError, "partitions"):
            screen_six_seat_orders(
                tensor,
                first_halves=((0, 1, 2),),
                relative_threshold=1e-12,
            )
        with self.assertRaisesRegex(ValueError, "permutation"):
            transpose_seat_tensor(tensor, (0, 1, 2, 3, 4, 4))


if __name__ == "__main__":
    unittest.main()
