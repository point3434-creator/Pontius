from __future__ import annotations

import unittest

import numpy as np

from pontius.factor_tt_contraction import (
    FactorTTBeliefWorkspace,
    FactorTTTopology,
    enumerated_factor_tt_expectation,
    evaluate_tensor_train_assignments,
)
from pontius.factorized_belief import FactorizedCardBelief
from pontius.river import HoleCards, parse_cards
from pontius.tensor_train import TensorTrain


def _axes() -> tuple[tuple[HoleCards, ...], ...]:
    return (
        ((0, 1), (2, 3), (4, 5)),
        ((0, 6), (7, 8), (9, 10)),
        ((1, 11), (12, 13), (14, 15)),
        ((2, 16), (17, 18), (19, 20)),
    )


def _belief(components: int = 3) -> FactorizedCardBelief:
    rng = np.random.default_rng(41 + components)
    axes = _axes()
    return FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=rng.uniform(0.2, 1.0, size=components),
        unary_weights=tuple(
            rng.uniform(0.1, 1.0, size=(components, len(hands)))
            for hands in axes
        ),
        board=parse_cards("As", "Kd", "Qh", "Jc", "9s"),
    )


class FactorTTContractionTests(unittest.TestCase):
    def test_direct_signed_train_matches_explicit_compatible_joint(self) -> None:
        belief = _belief(3)
        rng = np.random.default_rng(17)
        dense = rng.normal(size=belief.hand_counts)
        train = TensorTrain.from_dense(dense, maximum_rank=3)
        topology = FactorTTTopology.compile(belief, split_index=2)
        workspace = FactorTTBeliefWorkspace.compile(
            topology,
            belief,
            query_chunk_records=2,
        )
        direct = workspace.contract(train)
        explicit = enumerated_factor_tt_expectation(belief, train)
        self.assertAlmostEqual(workspace.partition, belief.materialize().partition, places=12)
        self.assertAlmostEqual(direct.expectation, explicit.expectation, places=12)
        self.assertEqual(direct.feature_width, 3 * direct.middle_rank)
        # Tiny tensors are dominated by topology metadata; the wide audit owns
        # the meaningful compression-ratio gate.
        self.assertLess(direct.estimated_peak_total_numeric_bytes, dense.nbytes * 40)

    def test_constant_operator_returns_one_and_topology_is_reusable(self) -> None:
        first = _belief(1)
        topology = FactorTTTopology.compile(first, split_index=2)
        first_workspace = FactorTTBeliefWorkspace.compile(topology, first)
        ones = TensorTrain.from_dense(np.ones(first.hand_counts, dtype=np.float64))
        self.assertAlmostEqual(first_workspace.contract(ones).expectation, 1.0, places=12)

        second = first.with_likelihood(0, [0.2, 0.7, 1.0])
        second_workspace = FactorTTBeliefWorkspace.compile(topology, second)
        self.assertIs(second_workspace.topology, topology)
        self.assertAlmostEqual(second_workspace.contract(ones).expectation, 1.0, places=12)
        self.assertNotEqual(first_workspace.partition, second_workspace.partition)
        self.assertTrue(topology.storage_is_contiguous_fixed_dtype())

    def test_batched_assignment_evaluation_matches_dense_gather(self) -> None:
        belief = _belief(1)
        dense = np.arange(np.prod(belief.hand_counts), dtype=np.float64).reshape(
            belief.hand_counts
        )
        train = TensorTrain.from_dense(dense)
        assignments = np.asarray(((0, 0, 0, 0), (2, 1, 2, 1)), dtype=np.int32)
        expected = dense[tuple(assignments.T)]
        np.testing.assert_allclose(
            evaluate_tensor_train_assignments(train, assignments),
            expected,
            atol=1e-10,
            rtol=0.0,
        )

    def test_invalid_split_axes_assignments_and_chunk_are_rejected(self) -> None:
        belief = _belief(1)
        with self.assertRaisesRegex(ValueError, "two nonempty"):
            FactorTTTopology.compile(belief, split_index=0)
        topology = FactorTTTopology.compile(belief, split_index=2)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            FactorTTBeliefWorkspace.compile(
                topology,
                belief,
                query_chunk_records=0,
            )
        changed = FactorizedCardBelief(
            hands_by_player=tuple(tuple(reversed(axis)) for axis in _axes()),
            mixture_weights=[1.0],
            unary_weights=tuple(np.ones((1, 3)) for _ in range(4)),
            board=belief.board,
        )
        with self.assertRaisesRegex(ValueError, "hand masks"):
            FactorTTBeliefWorkspace.compile(topology, changed)
        train = TensorTrain.from_dense(np.ones(belief.hand_counts))
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            evaluate_tensor_train_assignments(train, [[0, 0, 0, 9]])


if __name__ == "__main__":
    unittest.main()
