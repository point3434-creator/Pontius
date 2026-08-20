from __future__ import annotations

import unittest

import numpy as np

from pontius.tensor_train import TensorTrain, tensor_errors, unfolding_numerical_ranks


class TensorTrainTests(unittest.TestCase):
    def test_untruncated_tt_svd_reconstructs_dense_tensor(self) -> None:
        tensor = np.arange(2 * 3 * 4 * 2, dtype=np.float64).reshape(2, 3, 4, 2)
        train = TensorTrain.from_dense(tensor)
        reconstruction = train.to_dense()
        self.assertEqual(reconstruction.shape, tensor.shape)
        self.assertLessEqual(
            tensor_errors(tensor, reconstruction)["maximum_absolute_error"],
            1e-12,
        )
        self.assertEqual(train.ranks[0], 1)
        self.assertEqual(train.ranks[-1], 1)
        self.assertTrue(all(core.flags.c_contiguous for core in train.cores))

    def test_rank_cap_compresses_and_reports_nonzero_error(self) -> None:
        rng = np.random.default_rng(7)
        tensor = rng.normal(size=(4, 4, 4, 4))
        full = TensorTrain.from_dense(tensor)
        rank_one = TensorTrain.from_dense(tensor, maximum_rank=1)
        self.assertLess(rank_one.storage_bytes, full.storage_bytes)
        self.assertGreater(
            tensor_errors(tensor, rank_one.to_dense())["relative_frobenius_error"],
            0.1,
        )

    def test_outer_product_has_unit_numerical_tt_ranks(self) -> None:
        factors = (
            np.asarray([1.0, 2.0]),
            np.asarray([3.0, 4.0, 5.0]),
            np.asarray([6.0, 7.0]),
        )
        tensor = np.einsum("i,j,k->ijk", *factors)
        self.assertEqual(
            unfolding_numerical_ranks(tensor, relative_threshold=1e-12),
            (1, 1, 1, 1),
        )

    def test_invalid_tensor_rank_and_threshold_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least two"):
            TensorTrain.from_dense([1.0, 2.0])
        with self.assertRaisesRegex(ValueError, "positive integer"):
            TensorTrain.from_dense(np.ones((2, 2)), maximum_rank=0)
        with self.assertRaisesRegex(ValueError, "threshold"):
            unfolding_numerical_ranks(np.ones((2, 2)), relative_threshold=1.0)


if __name__ == "__main__":
    unittest.main()
