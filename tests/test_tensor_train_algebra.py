from __future__ import annotations

import unittest

import numpy as np

from pontius.tensor_train import TensorTrain
from pontius.tensor_train_algebra import (
    add_tensor_trains,
    multiply_mode_vector,
    round_tensor_train,
    sum_tensor_trains,
)


class TensorTrainAlgebraTests(unittest.TestCase):
    def test_mode_multiplier_and_direct_sum_are_dense_exact(self) -> None:
        rng = np.random.default_rng(11)
        first_dense = rng.normal(size=(3, 4, 2, 3))
        second_dense = rng.normal(size=(3, 4, 2, 3))
        first = TensorTrain.from_dense(first_dense, maximum_rank=3)
        second = TensorTrain.from_dense(second_dense, maximum_rank=2)
        vector = np.asarray([0.2, 0.7], dtype=np.float64)
        scaled = multiply_mode_vector(first, 2, vector)
        expected_scaled = first.to_dense() * vector[None, None, :, None]
        np.testing.assert_allclose(scaled.to_dense(), expected_scaled, atol=1e-12, rtol=0.0)
        combined = add_tensor_trains(scaled, second)
        np.testing.assert_allclose(
            combined.to_dense(),
            expected_scaled + second.to_dense(),
            atol=1e-12,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            sum_tensor_trains((first, second, scaled)).to_dense(),
            first.to_dense() + second.to_dense() + expected_scaled,
            atol=1e-12,
            rtol=0.0,
        )

    def test_tolerance_only_rounding_is_exact_and_rank_cap_compresses(self) -> None:
        rng = np.random.default_rng(13)
        dense = rng.normal(size=(4, 4, 4, 4, 4))
        train = TensorTrain.from_dense(dense)
        exact = round_tensor_train(train, relative_tolerance=1e-13)
        capped = round_tensor_train(train, relative_tolerance=1e-13, maximum_rank=3)
        np.testing.assert_allclose(exact.train.to_dense(), dense, atol=1e-10, rtol=0.0)
        self.assertTrue(all(rank <= 3 for rank in capped.output_ranks[1:-1]))
        self.assertLess(capped.train.storage_bytes, exact.train.storage_bytes)
        self.assertGreater(capped.relative_discarded_bound, 0.0)

    def test_zero_train_rounds_to_unit_bonds(self) -> None:
        zero = TensorTrain.from_dense(np.zeros((3, 3, 3, 3), dtype=np.float64))
        rounded = round_tensor_train(zero, relative_tolerance=1e-12)
        self.assertEqual(rounded.output_ranks, (1, 1, 1, 1, 1))
        self.assertEqual(float(np.max(np.abs(rounded.train.to_dense()))), 0.0)

    def test_invalid_shapes_modes_tolerances_and_empty_sum_are_rejected(self) -> None:
        train = TensorTrain.from_dense(np.ones((2, 3, 2), dtype=np.float64))
        with self.assertRaisesRegex(ValueError, "mode"):
            multiply_mode_vector(train, 3, [1.0, 1.0])
        with self.assertRaisesRegex(ValueError, "matching finite"):
            multiply_mode_vector(train, 1, [1.0, 1.0])
        with self.assertRaisesRegex(ValueError, "identical"):
            add_tensor_trains(train, TensorTrain.from_dense(np.ones((2, 2, 2))))
        with self.assertRaisesRegex(ValueError, "at least one"):
            sum_tensor_trains(())
        with self.assertRaisesRegex(ValueError, "tolerance"):
            round_tensor_train(train, relative_tolerance=1.0)
        with self.assertRaisesRegex(ValueError, "maximum rank"):
            round_tensor_train(train, relative_tolerance=0.0, maximum_rank=0)


if __name__ == "__main__":
    unittest.main()
