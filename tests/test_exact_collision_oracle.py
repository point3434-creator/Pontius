from __future__ import annotations

import random
import unittest
from fractions import Fraction
from math import prod

import numpy as np

from pontius.exact_collision_oracle import (
    enumerate_exact_collision_belief,
    independently_normalized_marginals,
    marginal_total_variation,
)
from pontius.factorized_belief import FactorizedCardBelief
from pontius.holdem_cards import OneSeatCardState, make_hole


def _assert_matches_production(
    test: unittest.TestCase,
    axes: tuple[tuple[tuple[int, int], ...], ...],
    weights: tuple[tuple[Fraction, ...], ...],
) -> None:
    maximum_work = prod(len(axis) for axis in axes)
    oracle = enumerate_exact_collision_belief(
        hands_by_player=axes,
        weights_by_player=weights,
        maximum_cartesian_assignments=maximum_work,
    )
    production = FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=np.asarray([1.0]),
        unary_weights=tuple(
            np.asarray([[float(weight) for weight in player]], dtype=np.float64)
            for player in weights
        ),
    )
    materialized = production.materialize()
    contraction = production.recursive_contract()
    test.assertEqual(materialized.assignments, oracle.assignments)
    test.assertEqual(
        materialized.card_compatible_assignments,
        oracle.card_compatible_assignments,
    )
    test.assertAlmostEqual(materialized.partition, float(oracle.partition), delta=1e-12)
    np.testing.assert_allclose(
        materialized.probabilities,
        np.asarray([float(value) for value in oracle.probabilities]),
        atol=1e-12,
        rtol=0.0,
    )
    for production_marginal, exact_marginal in zip(
        contraction.marginals,
        oracle.marginals,
        strict=True,
    ):
        np.testing.assert_allclose(
            production_marginal,
            np.asarray([float(value) for value in exact_marginal]),
            atol=1e-12,
            rtol=0.0,
        )


class ExactCollisionOracleTests(unittest.TestCase):
    def test_blocker_stress_matches_production_and_defeats_independent_marginals(self) -> None:
        axes = (
            (make_hole(0, 1), make_hole(2, 3), make_hole(4, 5)),
            (make_hole(0, 6), make_hole(7, 8), make_hole(9, 10)),
            (make_hole(1, 7), make_hole(11, 12), make_hole(13, 14)),
        )
        weights = (
            (Fraction(1), Fraction(1, 2), Fraction(1, 3)),
            (Fraction(2, 5), Fraction(1), Fraction(3, 5)),
            (Fraction(3, 4), Fraction(1, 4), Fraction(1)),
        )
        _assert_matches_production(self, axes, weights)
        oracle = enumerate_exact_collision_belief(
            hands_by_player=axes,
            weights_by_player=weights,
            maximum_cartesian_assignments=27,
        )
        independent = independently_normalized_marginals(weights)
        self.assertTrue(
            any(
                marginal_total_variation(exact, blind) > 0
                for exact, blind in zip(oracle.marginals, independent, strict=True)
            )
        )
        production = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=[1.0],
            unary_weights=tuple(
                np.asarray([[float(value) for value in player]])
                for player in weights
            ),
        )
        self.assertEqual(production.assignment_weight((0, 0, 0)), 0.0)

    def test_seeded_full_axis_projections_match_for_two_through_five_players(self) -> None:
        generator = random.Random(289)
        full_axis = OneSeatCardState.preflop(
            controlled_seat=3,
            private_hand=make_hole("Ks", "Td"),
        ).compatible_opponent_hands()
        remaining = tuple(sorted({card for hand in full_axis for card in hand}))
        for case in range(60):
            players = 2 + case % 4
            shuffled = list(remaining)
            generator.shuffle(shuffled)
            axes = []
            weights = []
            for player in range(players):
                width = generator.randint(2, 5)
                hands = {make_hole(shuffled[2 * player], shuffled[2 * player + 1])}
                while len(hands) < width:
                    hands.add(full_axis[generator.randrange(len(full_axis))])
                axis = tuple(sorted(hands))
                raw = [generator.randint(1, 11) for _ in axis]
                maximum = max(raw)
                axes.append(axis)
                weights.append(tuple(Fraction(value, maximum) for value in raw))
            with self.subTest(case=case, players=players):
                _assert_matches_production(self, tuple(axes), tuple(weights))

    def test_overwork_mutability_bad_weights_and_zero_joint_fail_closed(self) -> None:
        axes = (
            (make_hole(0, 1), make_hole(2, 3)),
            (make_hole(4, 5), make_hole(6, 7)),
        )
        weights = ((Fraction(1), Fraction(1)),) * 2
        with self.assertRaisesRegex(ValueError, "exceeds"):
            enumerate_exact_collision_belief(
                hands_by_player=axes,
                weights_by_player=weights,
                maximum_cartesian_assignments=3,
            )
        with self.assertRaisesRegex(TypeError, "immutable"):
            enumerate_exact_collision_belief(
                hands_by_player=(list(axes[0]), axes[1]),  # type: ignore[arg-type]
                weights_by_player=weights,
                maximum_cartesian_assignments=4,
            )
        with self.assertRaisesRegex(TypeError, "Fractions"):
            enumerate_exact_collision_belief(
                hands_by_player=axes,
                weights_by_player=((Fraction(1), 1.0), weights[1]),  # type: ignore[arg-type]
                maximum_cartesian_assignments=4,
            )
        colliding = ((make_hole(0, 1),), (make_hole(0, 2),))
        with self.assertRaisesRegex(ValueError, "eliminated all"):
            enumerate_exact_collision_belief(
                hands_by_player=colliding,
                weights_by_player=((Fraction(1),),) * 2,
                maximum_cartesian_assignments=1,
            )
        with self.assertRaisesRegex(ValueError, "positive integer"):
            enumerate_exact_collision_belief(
                hands_by_player=axes,
                weights_by_player=weights,
                maximum_cartesian_assignments=True,  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
