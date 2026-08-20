from __future__ import annotations

import unittest

import numpy as np

from pontius.batched_factor_tt_contraction import (
    WeightedTensorTrainTerm,
    contract_weighted_sum,
)
from pontius.factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from pontius.tensor_train import TensorTrain
from tests.test_factor_tt_contraction import _belief


class BatchedFactorTTContractionTests(unittest.TestCase):
    def test_streamed_weighted_sum_matches_explicit_joint_and_slices_rank(self) -> None:
        belief = _belief(3)
        rng = np.random.default_rng(133)
        trains = tuple(
            TensorTrain.from_dense(
                rng.normal(size=belief.hand_counts), maximum_rank=3
            )
            for _ in range(2)
        )
        factors = tuple(
            tuple(rng.uniform(0.1, 1.0, size=count) for count in belief.hand_counts)
            for _ in trains
        )
        terms = tuple(
            WeightedTensorTrainTerm(
                train=train,
                mode_factors=term_factors,
                coefficient=coefficient,
            )
            for train, term_factors, coefficient in zip(
                trains, factors, (1.25, -0.75), strict=True
            )
        )
        workspace = FactorTTBeliefWorkspace.compile(
            FactorTTTopology.compile(belief, split_index=2), belief
        )
        streamed = contract_weighted_sum(
            workspace, terms, maximum_feature_width_per_batch=6
        )
        materialized = belief.materialize()
        assignments = np.asarray(materialized.assignments, dtype=np.int32)
        expected_values = np.zeros(len(materialized.assignments))
        indices = tuple(assignments[:, mode] for mode in range(4))
        for train, term_factors, coefficient in zip(
            trains, factors, (1.25, -0.75), strict=True
        ):
            values = train.to_dense()[indices]
            for mode in range(4):
                values = values * term_factors[mode][assignments[:, mode]]
            expected_values += coefficient * values
        expected = float(materialized.probabilities @ expected_values)
        self.assertAlmostEqual(streamed.expectation, expected, places=11)
        self.assertGreater(streamed.rank_slices, len(terms))
        self.assertGreater(streamed.batches, 1)
        self.assertLessEqual(streamed.maximum_batch_feature_width, 6)


if __name__ == "__main__":
    unittest.main()
