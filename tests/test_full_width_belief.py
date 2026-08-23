from __future__ import annotations

import unittest
from dataclasses import replace
from itertools import combinations
from math import comb, prod

from pontius.full_width_belief import ExactRangeWeight, FullWidthOneSeatBelief
from pontius.full_width_reference_policy import ImmutableFullWidthReferencePolicy
from pontius.holdem_cards import OneSeatCardState, make_hole, parse_cards
from pontius.no_limit_betting import CALL, BettingStreet, NoLimitBettingState


def _cards() -> OneSeatCardState:
    return OneSeatCardState.preflop(
        controlled_seat=3,
        private_hand=make_hole("Ks", "Td"),
    )


def _first_opponent_likelihood(belief: FullWidthOneSeatBelief):
    betting = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(200,) * 6,
        small_blind=1,
        big_blind=2,
    ).apply_action(CALL)
    source = ImmutableFullWidthReferencePolicy("belief-update-policy-v1")
    return source.likelihood_for_axis(
        visible_cards=belief.cards,
        actor_seat=4,
        hand_axis=belief.hand_axis,
        betting=betting,
        decision=betting.legal_decision(),
        observed_action=CALL,
    )


class FullWidthBeliefTests(unittest.TestCase):
    def test_uniform_belief_has_all_five_full_axes_and_exact_counts(self) -> None:
        belief = FullWidthOneSeatBelief.uniform(_cards())
        self.assertEqual(belief.opponent_seats, (0, 1, 2, 4, 5))
        self.assertEqual(belief.opponent_hand_counts, (1_225,) * 5)
        self.assertEqual(belief.factorized.hand_counts, (1_225,) * 5)
        self.assertEqual(
            belief.hand_axis,
            tuple(combinations(belief.cards.remaining_deck, 2)),
        )
        self.assertEqual(belief.cartesian_assignments, 1_225**5)
        self.assertEqual(
            belief.compatible_assignments,
            prod(comb(50 - 2 * opponent, 2) for opponent in range(5)),
        )
        self.assertEqual(belief.persistent_numeric_bytes, 8 + 5 * 1_225 * 8 * 2)
        self.assertTrue(belief.factorized.storage_is_contiguous_float64_and_uint64())
        self.assertEqual(len(belief.digest), 64)
        masks = tuple((1 << hand[0]) | (1 << hand[1]) for hand in belief.hand_axis)
        pairwise_compatible = sum(
            left & right == 0 for left in masks for right in masks
        )
        self.assertEqual(pairwise_compatible, comb(50, 2) * comb(48, 2))

    def test_action_update_changes_only_the_actor_and_retains_provenance(self) -> None:
        belief = FullWidthOneSeatBelief.uniform(_cards())
        likelihood = _first_opponent_likelihood(belief)
        updated = belief.with_action_likelihood(likelihood)
        actor = belief.opponent_index(4)
        self.assertNotEqual(updated.weights_by_opponent[actor], belief.weights_by_opponent[actor])
        for opponent in range(5):
            if opponent != actor:
                self.assertIs(
                    updated.weights_by_opponent[opponent],
                    belief.weights_by_opponent[opponent],
                )
        self.assertEqual(updated.likelihood_digests, (likelihood.digest,))
        self.assertNotEqual(updated.digest, belief.digest)
        self.assertTrue(all(weight.numerator > 0 for weight in updated.weights_for(4)))
        probe = 731
        probability = likelihood.probabilities[probe]
        self.assertEqual(
            updated.weights_for(4)[probe],
            ExactRangeWeight(probability.numerator, probability.denominator),
        )

    def test_board_filter_preserves_exact_weights_and_removes_every_blocker(self) -> None:
        belief = FullWidthOneSeatBelief.uniform(_cards())
        updated = belief.with_action_likelihood(_first_opponent_likelihood(belief))
        flop = belief.cards.advance_to(
            BettingStreet.FLOP,
            parse_cards("2c", "7d", "9h"),
        )
        filtered = updated.advance_to(flop)
        self.assertEqual(filtered.opponent_hand_counts, (1_081,) * 5)
        self.assertEqual(filtered.likelihood_digests, updated.likelihood_digests)
        self.assertTrue(
            all(not set(hand).intersection(flop.board) for hand in filtered.hand_axis)
        )
        old_index = {hand: index for index, hand in enumerate(updated.hand_axis)}
        for seat in filtered.opponent_seats:
            expected = tuple(
                updated.weights_for(seat)[old_index[hand]] for hand in filtered.hand_axis
            )
            self.assertEqual(filtered.weights_for(seat), expected)

    def test_all_four_street_widths_and_analytic_support_are_exact(self) -> None:
        current = FullWidthOneSeatBelief.uniform(_cards())
        expected = (
            (BettingStreet.PREFLOP, 1_225, 50),
            (BettingStreet.FLOP, 1_081, 47),
            (BettingStreet.TURN, 1_035, 46),
            (BettingStreet.RIVER, 990, 45),
        )
        reveals = {
            BettingStreet.FLOP: parse_cards("2c", "7d", "9h"),
            BettingStreet.TURN: parse_cards("Js"),
            BettingStreet.RIVER: parse_cards("Qc"),
        }
        for index, (street, width, remaining) in enumerate(expected):
            if index:
                cards = current.cards.advance_to(street, reveals[street])
                current = current.advance_to(cards)
            self.assertEqual(current.cards.street, street)
            self.assertEqual(current.opponent_hand_counts, (width,) * 5)
            self.assertEqual(
                current.compatible_assignments,
                prod(comb(remaining - 2 * opponent, 2) for opponent in range(5)),
            )

    def test_wrong_actor_stale_axis_mutability_and_board_regression_fail_closed(self) -> None:
        belief = FullWidthOneSeatBelief.uniform(_cards())
        likelihood = _first_opponent_likelihood(belief)
        with self.assertRaisesRegex(ValueError, "not an opponent"):
            belief.with_action_likelihood(replace(likelihood, actor_seat=3))
        with self.assertRaisesRegex(ValueError, "stale or partial"):
            belief.with_action_likelihood(
                replace(
                    likelihood,
                    hand_axis=likelihood.hand_axis[:-1],
                    probabilities=likelihood.probabilities[:-1],
                    key_digests=likelihood.key_digests[:-1],
                )
            )
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            replace(belief, hand_axis=list(belief.hand_axis))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "advance exactly one street"):
            belief.advance_to(belief.cards)

    def test_zero_compatible_support_and_positive_underflow_fail_closed(self) -> None:
        belief = FullWidthOneSeatBelief.uniform(_cards())
        first_only = (
            ExactRangeWeight(1),
            *((ExactRangeWeight(0),) * (len(belief.hand_axis) - 1)),
        )
        with self.assertRaisesRegex(ValueError, "no compatible positive assignment"):
            replace(belief, weights_by_opponent=(first_only,) * 5)

        underflow = list(belief.weights_by_opponent)
        tiny_axis = [ExactRangeWeight(1, 10**1000)] * len(belief.hand_axis)
        tiny_axis[0] = ExactRangeWeight(1)
        underflow[0] = tuple(tiny_axis)
        with self.assertRaisesRegex(ArithmeticError, "underflowed"):
            replace(belief, weights_by_opponent=tuple(underflow))

    def test_exact_range_weight_is_distinct_reduced_and_rejects_aliases(self) -> None:
        self.assertEqual(ExactRangeWeight(6, 9), ExactRangeWeight(2, 3))
        for numerator, denominator in ((True, 1), (1, False), (-1, 1), (1, 0)):
            with self.subTest(numerator=numerator, denominator=denominator), self.assertRaises(
                (TypeError, ValueError)
            ):
                ExactRangeWeight(numerator, denominator)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
