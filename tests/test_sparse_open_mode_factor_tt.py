from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.factor_tt_contraction_audit import _synthetic_train
from pontius.open_mode_factor_tt import contract_open_mode_batch
from pontius.sparse_incidence_open_mode import SparseBidirectionalIncidence
from pontius.sparse_open_mode_factor_tt import contract_sparse_open_mode_batch
from tests.test_open_mode_factor_tt import _belief, _compile


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class SparseOpenModeFactorTTTests(unittest.TestCase):
    def test_generic_tt_batch_matches_numpy_with_rank_slicing_and_weights(self) -> None:
        belief = _belief(components=3)
        _, _, workspace = _compile(belief)
        sparse = SparseBidirectionalIncidence.compile(workspace)
        trains = (
            _synthetic_train(hand_count=3, players=4, rank=4, seed=101),
            _synthetic_train(hand_count=3, players=4, rank=5, seed=202),
        )
        factors = (
            np.asarray((0.2, 1.0, 0.4)),
            np.asarray((1.0, 0.3, 0.7)),
            np.asarray((0.9, 0.4, 0.8)),
            np.asarray((0.5, 1.0, 0.6)),
        )
        expected = contract_open_mode_batch(
            workspace,
            trains,
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )
        actual = contract_sparse_open_mode_batch(
            workspace,
            sparse,
            trains,
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )

        self.assertEqual(actual.middle_ranks, expected.middle_ranks)
        self.assertGreater(len(actual.directions), 1)
        self.assertGreater(actual.sparse_operator_numeric_bytes, 0)
        for train_index in range(len(trains)):
            for target in range(4):
                first = actual.for_train(train_index).for_seat(target)
                second = expected.for_train(train_index).for_seat(target)
                np.testing.assert_allclose(
                    first.root_normalized_reaches,
                    second.root_normalized_reaches,
                    atol=5e-14,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    first.root_normalized_numerators,
                    second.root_normalized_numerators,
                    atol=5e-13,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    first.conditional_values,
                    second.conditional_values,
                    atol=5e-13,
                    rtol=0.0,
                )

    def test_generic_tt_contract_rejects_wrong_topology_and_empty_batch(self) -> None:
        belief = _belief(components=1)
        _, _, workspace = _compile(belief)
        sparse = SparseBidirectionalIncidence.compile(workspace)
        with self.assertRaisesRegex(ValueError, "at least one"):
            contract_sparse_open_mode_batch(workspace, sparse, ())

        _, _, other = _compile(belief)
        train = _synthetic_train(hand_count=3, players=4, rank=2, seed=303)
        with self.assertRaisesRegex(ValueError, "another topology"):
            contract_sparse_open_mode_batch(other, sparse, (train,))


if __name__ == "__main__":
    unittest.main()
