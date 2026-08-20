from __future__ import annotations

import unittest

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius.river import HoleCards, parse_cards


def _axes(players: int, hands: int) -> tuple[tuple[HoleCards, ...], ...]:
    board = set(parse_cards("2c", "7d", "9h", "Js", "Qc"))
    available = tuple(card for card in range(52) if card not in board)
    if players * hands * 2 > len(available):
        raise ValueError("test axes require more private cards than are available")
    return tuple(
        tuple(
            tuple(
                sorted(
                    available[
                        2 * (player * hands + index) :
                        2 * (player * hands + index + 1)
                    ]
                )
            )
            for index in range(hands)
        )
        for player in range(players)
    )


def _belief(players: int = 3, hands: int = 3, components: int = 2) -> FactorizedCardBelief:
    axes = _axes(players, hands)
    unaries = tuple(
        np.asarray(
            [
                [1.0 + player + component + hand for hand in range(hands)]
                for component in range(components)
            ],
            dtype=np.float64,
        )
        for player in range(players)
    )
    return FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=np.arange(1, components + 1, dtype=np.float64),
        unary_weights=unaries,
        board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
    )


class FactorizedCardBeliefTests(unittest.TestCase):
    def test_materialization_is_normalized_and_card_incompatible_assignments_are_zero(self) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        available = tuple(card for card in range(52) if card not in set(board))
        axes = (
            ((available[0], available[1]), (available[2], available[3])),
            ((available[0], available[4]), (available[5], available[6])),
        )
        belief = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=[1.0],
            unary_weights=(
                np.asarray([[1.0, 2.0]]),
                np.asarray([[3.0, 4.0]]),
            ),
            board=board,
        )
        materialized = belief.materialize()
        self.assertAlmostEqual(sum(materialized.probabilities), 1.0)
        self.assertEqual(materialized.cartesian_assignments, 4)
        self.assertEqual(materialized.card_compatible_assignments, 3)
        self.assertEqual(belief.assignment_weight((0, 0)), 0.0)
        self.assertGreater(belief.assignment_weight((0, 1)), 0.0)

    def test_public_likelihood_and_private_conditioning_are_exactly_closed(self) -> None:
        belief = _belief()
        initial = belief.materialize().as_dict()
        likelihood = np.asarray([0.2, 1.0, 0.6])
        updated = belief.with_likelihood(1, likelihood)
        expected_unnormalized = {
            assignment: probability * likelihood[assignment[1]]
            for assignment, probability in initial.items()
        }
        expected_total = sum(expected_unnormalized.values())
        expected = {
            assignment: weight / expected_total
            for assignment, weight in expected_unnormalized.items()
        }
        actual = updated.materialize().as_dict()
        self.assertEqual(set(actual), set(expected))
        self.assertLessEqual(
            max(abs(actual[key] - expected[key]) for key in expected),
            1e-15,
        )

        conditioned = updated.condition_on_hand(0, updated.hands_by_player[0][1])
        self.assertTrue(
            all(assignment[0] == 1 for assignment in conditioned.materialize().assignments)
        )

    def test_recursive_and_two_meet_in_middle_splits_match(self) -> None:
        belief = _belief(players=4, hands=3, components=3)
        recursive = belief.recursive_contract()
        contiguous = belief.meet_in_middle_contract((0, 1))
        alternating = belief.meet_in_middle_contract((0, 2))
        self.assertAlmostEqual(recursive.partition, contiguous.partition, places=12)
        self.assertAlmostEqual(recursive.partition, alternating.partition, places=12)
        self.assertEqual(
            recursive.card_compatible_assignments,
            contiguous.card_compatible_assignments,
        )
        for reference, first, second in zip(
            recursive.marginals,
            contiguous.marginals,
            alternating.marginals,
            strict=True,
        ):
            np.testing.assert_allclose(first, reference, atol=1e-12, rtol=0.0)
            np.testing.assert_allclose(second, reference, atol=1e-12, rtol=0.0)
            self.assertAlmostEqual(float(np.sum(first)), 1.0)

    def test_storage_is_defensive_contiguous_and_compact(self) -> None:
        axes = _axes(3, 2)
        supplied = np.asarray([[1.0, 3.0], [2.0, 4.0]])
        belief = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=[1.0, 2.0],
            unary_weights=(supplied, supplied, supplied),
            board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
        )
        supplied[0, 0] = 999.0
        self.assertNotEqual(belief.unary_weights[0][0, 0], 999.0)
        self.assertTrue(belief.storage_is_contiguous_float64_and_uint64())
        self.assertEqual(belief.persistent_numeric_bytes, 2 * 8 + 3 * 2 * 2 * 8 + 3 * 2 * 8)
        with self.assertRaises(ValueError):
            belief.unary_weights[0][0, 0] = 1.0

    def test_invalid_shapes_weights_likelihoods_and_splits_are_rejected(self) -> None:
        axes = _axes(2, 2)
        with self.assertRaisesRegex(ValueError, "unary shape"):
            FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=[1.0],
                unary_weights=(np.ones((1, 3)), np.ones((1, 2))),
            )
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=[1.0],
                unary_weights=(np.asarray([[1.0, -1.0]]), np.ones((1, 2))),
            )
        belief = _belief(players=3, hands=2, components=1)
        with self.assertRaisesRegex(ValueError, "likelihood shape"):
            belief.with_likelihood(0, [1.0])
        with self.assertRaisesRegex(ValueError, "two nonempty halves"):
            belief.meet_in_middle_contract((0, 1, 2))


if __name__ == "__main__":
    unittest.main()
