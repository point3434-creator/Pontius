from __future__ import annotations

import unittest

import numpy as np

from pontius.batched_factor_tt_contraction import (
    WeightedTensorTrainTerm,
    contract_weighted_sum,
)
from pontius.factor_tt_contraction import (
    FactorTTBeliefWorkspace,
    FactorTTTopology,
    evaluate_tensor_train_assignments,
)
from pontius.factorized_belief import FactorizedCardBelief
from pontius.open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
    contract_open_mode_batch,
    contract_open_modes,
)
from pontius.open_mode_showdown import contract_open_mode_showdown_batch
from pontius.structured_showdown_automaton import build_structured_showdown_automaton
from pontius.tensor_train import TensorTrain


def _axes() -> tuple[tuple[tuple[int, int], ...], ...]:
    return (
        ((0, 1), (2, 3), (4, 5)),
        ((0, 6), (7, 8), (9, 10)),
        ((1, 11), (12, 13), (14, 15)),
        ((2, 16), (17, 18), (19, 20)),
    )


def _belief(*, components: int = 3) -> FactorizedCardBelief:
    rng = np.random.default_rng(730 + components)
    axes = _axes()
    return FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=rng.uniform(0.1, 1.0, size=components),
        unary_weights=tuple(
            rng.uniform(0.05, 1.0, size=(components, len(axis)))
            for axis in axes
        ),
    )


def _compile(
    belief: FactorizedCardBelief,
) -> tuple[
    FactorTTBeliefWorkspace,
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
]:
    base_topology = FactorTTTopology.compile(belief, split_index=2)
    base_workspace = FactorTTBeliefWorkspace.compile(
        base_topology,
        belief,
        query_chunk_records=2,
    )
    topology = BidirectionalFactorTTTopology.compile(base_topology)
    workspace = OpenModeFactorTTWorkspace.compile(topology, base_workspace)
    return base_workspace, topology, workspace


def _literal_vectors(
    belief: FactorizedCardBelief,
    train: TensorTrain,
    factors: tuple[np.ndarray, ...],
    target: int,
    *,
    zero_reach_value: float,
) -> dict[str, np.ndarray | float | None]:
    materialized = belief.materialize()
    assignments = np.ascontiguousarray(materialized.assignments, dtype=np.int32)
    values = evaluate_tensor_train_assignments(train, assignments)
    multipliers = np.ones(len(assignments), dtype=np.float64)
    for seat, factor in enumerate(factors):
        multipliers *= factor[assignments[:, seat]]
    weights = materialized.unnormalized_weights * multipliers
    reaches = np.bincount(
        assignments[:, target],
        weights=weights,
        minlength=belief.hand_counts[target],
    )
    numerators = np.bincount(
        assignments[:, target],
        weights=weights * values,
        minlength=belief.hand_counts[target],
    )
    positive = reaches > 0.0
    conditional = np.full(len(reaches), zero_reach_value, dtype=np.float64)
    np.divide(numerators, reaches, out=conditional, where=positive)
    total_reach = float(np.sum(reaches))
    distribution = (
        reaches / total_reach if total_reach > 0.0 else np.zeros_like(reaches)
    )
    total_numerator = float(np.sum(numerators))
    return {
        "reaches": reaches,
        "numerators": numerators,
        "positive": positive,
        "conditional": conditional,
        "distribution": distribution,
        "total_reach": total_reach,
        "total_numerator": total_numerator,
        "conditioned": (
            total_numerator / total_reach if total_reach > 0.0 else None
        ),
    }


class OpenModeFactorTTTests(unittest.TestCase):
    def test_sparse_showdown_path_matches_direct_tt_and_shortcut_without_dense_payoff(self) -> None:
        belief = _belief(components=2)
        _, _, workspace = _compile(belief)
        codes = tuple(
            np.asarray((0, 1, 2), dtype=np.int32) for _ in belief.hand_counts
        )
        automata = (
            build_structured_showdown_automaton(
                strength_codes=codes,
                contenders=(0, 1, 2, 3),
                target_player=1,
                contributed=True,
                pot=12.0,
                bet_size=3.0,
            ),
            build_structured_showdown_automaton(
                strength_codes=codes,
                contenders=(0, 1),
                target_player=3,
                contributed=False,
                pot=12.0,
                bet_size=3.0,
            ),
        )
        factors = (
            np.asarray((0.2, 1.0, 0.4)),
            np.asarray((1.0, 0.3, 0.7)),
            np.asarray((0.9, 0.4, 0.8)),
            np.asarray((0.5, 1.0, 0.6)),
        )

        sparse = contract_open_mode_showdown_batch(
            workspace,
            automata,
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )
        direct = contract_open_mode_batch(
            workspace,
            tuple(automaton.to_tensor_train() for automaton in automata),
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )

        self.assertTrue(automata[1].constant_winner_shortcut)
        self.assertEqual(sparse.middle_ranks, direct.middle_ranks)
        self.assertEqual(
            sparse.referenced_automaton_numeric_bytes,
            sum(automaton.numeric_bytes for automaton in automata),
        )
        for index in range(2):
            for target in range(4):
                actual = sparse.for_automaton(index).for_seat(target)
                expected = direct.for_train(index).for_seat(target)
                np.testing.assert_allclose(
                    actual.root_normalized_numerators,
                    expected.root_normalized_numerators,
                    atol=3e-13,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    actual.root_normalized_reaches,
                    expected.root_normalized_reaches,
                    atol=3e-14,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    actual.conditional_values,
                    expected.conditional_values,
                    atol=3e-13,
                    rtol=0.0,
                )

    def test_rank_sliced_child_batch_matches_independent_literal_vectors(self) -> None:
        belief = _belief(components=3)
        _, _, workspace = _compile(belief)
        rng = np.random.default_rng(733)
        trains = (
            TensorTrain.from_dense(
                rng.normal(size=belief.hand_counts), maximum_rank=3
            ),
            TensorTrain.from_dense(
                rng.normal(size=belief.hand_counts), maximum_rank=2
            ),
        )
        factors = tuple(
            rng.uniform(0.0, 1.0, size=size).astype(np.float64)
            for size in belief.hand_counts
        )

        batched = contract_open_mode_batch(
            workspace,
            trains,
            target_seats=(3, 1),
            mode_factors=factors,
            maximum_feature_width_per_batch=3,
        )

        self.assertEqual(batched.middle_ranks, (3, 2))
        self.assertEqual(batched.total_middle_rank, 5)
        self.assertEqual(len(batched.directions), 2)
        self.assertTrue(all(work.rank_slices == 5 for work in batched.directions))
        self.assertTrue(all(work.batches == 5 for work in batched.directions))
        self.assertTrue(
            all(
                work.maximum_observed_batch_feature_width == 3
                for work in batched.directions
            )
        )
        for train_index, train in enumerate(trains):
            for target in (3, 1):
                expected = _literal_vectors(
                    belief,
                    train,
                    factors,
                    target,
                    zero_reach_value=0.0,
                )
                actual = batched.for_train(train_index).for_seat(target)
                np.testing.assert_allclose(
                    actual.root_normalized_numerators,
                    np.asarray(expected["numerators"]) / workspace.base.partition,
                    atol=3e-14,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    actual.root_normalized_reaches,
                    np.asarray(expected["reaches"]) / workspace.base.partition,
                    atol=3e-14,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    actual.conditional_values,
                    expected["conditional"],
                    atol=3e-14,
                    rtol=0.0,
                )
        with self.assertRaisesRegex(ValueError, "at least one"):
            contract_open_mode_batch(workspace, ())
        with self.assertRaisesRegex(ValueError, "smaller"):
            contract_open_mode_batch(
                workspace,
                trains,
                maximum_feature_width_per_batch=2,
            )
        with self.assertRaises(KeyError):
            batched.for_train(2)

    def test_two_directions_reproduce_all_seat_vectors_and_scalar_contract(self) -> None:
        belief = _belief(components=3)
        base, topology, workspace = _compile(belief)
        rng = np.random.default_rng(731)
        train = TensorTrain.from_dense(
            rng.normal(size=belief.hand_counts),
            maximum_rank=3,
        )

        result = contract_open_modes(workspace, train)
        factors = tuple(np.ones(size, dtype=np.float64) for size in train.shape)

        self.assertEqual(result.target_seats, (0, 1, 2, 3))
        self.assertEqual(len(result.directions), 2)
        self.assertEqual(
            {direction.direction for direction in result.directions},
            {"right_to_left", "left_to_right"},
        )
        self.assertTrue(result.mode_factors_are_identity)
        self.assertTrue(topology.storage_is_contiguous_fixed_dtype())
        for target in range(4):
            expected = _literal_vectors(
                belief,
                train,
                factors,
                target,
                zero_reach_value=0.0,
            )
            actual = result.for_seat(target)
            np.testing.assert_allclose(
                actual.unnormalized_reaches,
                expected["reaches"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.unnormalized_numerators,
                expected["numerators"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.root_normalized_reaches,
                np.asarray(expected["reaches"]) / base.partition,
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.root_normalized_numerators,
                np.asarray(expected["numerators"]) / base.partition,
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.reached_hand_distribution,
                expected["distribution"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.conditional_values,
                expected["conditional"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_array_equal(actual.positive_reach, expected["positive"])
            self.assertAlmostEqual(
                actual.total_unnormalized_numerator,
                float(expected["total_numerator"]),
                places=12,
            )
            self.assertAlmostEqual(
                actual.total_unnormalized_reach,
                float(expected["total_reach"]),
                places=12,
            )
            self.assertAlmostEqual(
                actual.total_root_reach_probability,
                1.0,
                places=12,
            )
            self.assertAlmostEqual(
                actual.total_unnormalized_numerator / base.partition,
                base.contract(train).expectation,
                places=12,
            )

    def test_weighted_reach_matches_literal_and_weighted_scalar_with_zero_hand(self) -> None:
        belief = _belief(components=2)
        base, _, workspace = _compile(belief)
        rng = np.random.default_rng(732)
        train = TensorTrain.from_dense(
            rng.normal(size=belief.hand_counts),
            maximum_rank=2,
        )
        factors = (
            np.asarray((0.0, 0.4, 1.1), dtype=np.float64),
            np.asarray((0.3, 1.0, 0.2), dtype=np.float64),
            np.asarray((0.8, 0.0, 0.5), dtype=np.float64),
            np.asarray((1.0, 0.7, 0.1), dtype=np.float64),
        )
        fallback = -7.25

        result = contract_open_modes(
            workspace,
            train,
            mode_factors=factors,
            zero_reach_value=fallback,
        )
        scalar = contract_weighted_sum(
            base,
            (
                WeightedTensorTrainTerm(
                    train=train,
                    mode_factors=factors,
                    coefficient=1.0,
                ),
            ),
            maximum_feature_width_per_batch=64,
        )

        self.assertFalse(result.mode_factors_are_identity)
        self.assertEqual(len(result.directions), 2)
        self.assertTrue(all(not work.denominator_incidence_cached for work in result.directions))
        for target in range(4):
            expected = _literal_vectors(
                belief,
                train,
                factors,
                target,
                zero_reach_value=fallback,
            )
            actual = result.for_seat(target)
            np.testing.assert_allclose(
                actual.unnormalized_reaches,
                expected["reaches"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.unnormalized_numerators,
                expected["numerators"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.conditional_values,
                expected["conditional"],
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_array_equal(actual.positive_reach, expected["positive"])
            self.assertAlmostEqual(
                actual.total_unnormalized_numerator / base.partition,
                scalar.expectation,
                places=12,
            )
        self.assertFalse(result.for_seat(0).positive_reach[0])
        self.assertEqual(result.for_seat(0).conditional_values[0], fallback)
        self.assertFalse(result.for_seat(2).positive_reach[1])
        self.assertEqual(result.for_seat(2).conditional_values[1], fallback)

    def test_requested_half_uses_one_direction_and_validation_is_explicit(self) -> None:
        belief = _belief(components=1)
        base, topology, workspace = _compile(belief)
        train = TensorTrain.from_dense(np.ones(belief.hand_counts, dtype=np.float64))

        left = contract_open_modes(workspace, train, target_seats=(1, 0))
        self.assertEqual(left.target_seats, (1, 0))
        self.assertEqual(len(left.directions), 1)
        self.assertEqual(left.directions[0].direction, "right_to_left")
        self.assertEqual(left.directions[0].query_seats, (0, 1))
        with self.assertRaises(KeyError):
            left.for_seat(2)
        with self.assertRaisesRegex(ValueError, "nonempty and unique"):
            contract_open_modes(workspace, train, target_seats=())
        with self.assertRaisesRegex(ValueError, "nonempty and unique"):
            contract_open_modes(workspace, train, target_seats=(0, 0))
        with self.assertRaisesRegex(ValueError, "outside"):
            contract_open_modes(workspace, train, target_seats=(4,))
        with self.assertRaisesRegex(ValueError, "outside"):
            contract_open_modes(workspace, train, target_seats=(True,))
        with self.assertRaisesRegex(ValueError, "one factor"):
            contract_open_modes(workspace, train, mode_factors=(np.ones(3),))
        bad_factors = tuple(np.ones(3) for _ in range(4))
        bad_factors[0][0] = -1.0
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            contract_open_modes(workspace, train, mode_factors=bad_factors)
        with self.assertRaisesRegex(ValueError, "fallback"):
            contract_open_modes(workspace, train, zero_reach_value=np.nan)

        other_base_topology = FactorTTTopology.compile(belief, split_index=2)
        other_bidirectional = BidirectionalFactorTTTopology.compile(other_base_topology)
        with self.assertRaisesRegex(ValueError, "differ"):
            OpenModeFactorTTWorkspace.compile(other_bidirectional, base)
        self.assertGreater(topology.reverse_incidence_entries, 0)


if __name__ == "__main__":
    unittest.main()
