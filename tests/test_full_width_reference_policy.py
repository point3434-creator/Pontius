from __future__ import annotations

import unittest
from dataclasses import replace
from fractions import Fraction

from pontius.full_width_reference_policy import (
    BlueprintActionLikelihood,
    ImmutableFullWidthReferencePolicy,
    RationalActionProbability,
)
from pontius.holdem_cards import OneSeatCardState, make_hole
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingActionKind,
    NoLimitBettingState,
    raise_to,
)


def _initial_context(
    *,
    stack: int = 200,
) -> tuple[OneSeatCardState, NoLimitBettingState]:
    cards = OneSeatCardState.preflop(
        controlled_seat=3,
        private_hand=make_hole("Ks", "Td"),
    )
    betting = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(stack,) * 6,
        small_blind=1,
        big_blind=2,
    )
    return cards, betting


class FullWidthReferencePolicyTests(unittest.TestCase):
    def test_distribution_covers_every_exact_raise_and_sums_exactly(self) -> None:
        cards, betting = _initial_context()
        decision = betting.legal_decision()
        source = ImmutableFullWidthReferencePolicy("policy-exact-support-v1")
        distribution = source.distribution_for(
            cards=cards,
            betting=betting,
            decision=decision,
        )
        bounds = decision.raise_bounds
        assert bounds is not None

        actions = [FOLD, CALL]
        actions.extend(
            raise_to(amount)
            for amount in range(
                bounds.minimum_raise_to,
                bounds.maximum_raise_to + 1,
            )
        )
        self.assertEqual(distribution.exact_action_count, len(actions))
        self.assertEqual(
            sum(distribution.weight(action) for action in actions),
            distribution.total_weight,
        )
        self.assertEqual(
            sum(
                (
                    Fraction(
                        distribution.probability(action).numerator,
                        distribution.probability(action).denominator,
                    )
                    for action in actions
                ),
                start=Fraction(0),
            ),
            Fraction(1),
        )
        for amount in (
            bounds.minimum_raise_to,
            (bounds.minimum_raise_to + bounds.maximum_raise_to) // 2,
            bounds.maximum_raise_to,
        ):
            self.assertGreater(distribution.weight(raise_to(amount)), 0)
        self.assertEqual(distribution.selected_action, CALL)
        self.assertGreater(
            distribution.weight(CALL),
            max(distribution.weight(action) for action in actions if action != CALL),
        )

    def test_closed_form_raise_sum_handles_a_billion_chip_interval(self) -> None:
        cards, betting = _initial_context(stack=1_000_000_000)
        distribution = ImmutableFullWidthReferencePolicy(
            "policy-billion-interval-v1"
        ).distribution_for(
            cards=cards,
            betting=betting,
            decision=betting.legal_decision(),
        )
        bounds = distribution.decision.raise_bounds
        assert bounds is not None
        count = bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        cycles, remainder = divmod(count, 5)
        expected = count * distribution.raise_base_weight
        expected += cycles * 10 + remainder * (remainder - 1) // 2
        self.assertEqual(distribution.raise_support_count, count)
        self.assertEqual(distribution.total_raise_weight, expected)
        self.assertEqual(distribution.exact_action_count, count + 2)

    def test_full_axis_likelihood_is_exact_actor_bound_and_future_blind(self) -> None:
        visible_cards, initial = _initial_context()
        betting = initial.apply_action(CALL)
        decision = betting.legal_decision()
        self.assertEqual(decision.acting_seat, 4)
        hand_axis = visible_cards.compatible_opponent_hands()
        source = ImmutableFullWidthReferencePolicy("policy-likelihood-v1")
        likelihood = source.likelihood_for_axis(
            visible_cards=visible_cards,
            actor_seat=4,
            hand_axis=hand_axis,
            betting=betting,
            decision=decision,
            observed_action=CALL,
        )
        self.assertEqual(len(likelihood.hand_axis), 1_225)
        self.assertEqual(len(likelihood.probabilities), 1_225)
        self.assertTrue(all(value.numerator > 0 for value in likelihood.probabilities))
        self.assertGreater(len(set(likelihood.probabilities)), 1)
        self.assertEqual(likelihood.source_digest, source.digest)

        probe = 731
        hypothetical = OneSeatCardState.preflop(
            controlled_seat=4,
            private_hand=hand_axis[probe],
        )
        expected = source.distribution_for(
            cards=hypothetical,
            betting=betting,
            decision=decision,
        )
        self.assertEqual(likelihood.probabilities[probe], expected.probability(CALL))
        self.assertEqual(likelihood.key_digests[probe], expected.key.digest)
        self.assertEqual(expected.key.private_hand, hand_axis[probe])
        self.assertEqual(expected.key.board, ())
        self.assertFalse(hasattr(expected.key, "deal"))
        self.assertEqual(likelihood.as_float64().shape, (1_225,))
        with self.assertRaisesRegex(ValueError, "zero probability"):
            BlueprintActionLikelihood(
                actor_seat=likelihood.actor_seat,
                street=likelihood.street,
                observed_action=likelihood.observed_action,
                hand_axis=likelihood.hand_axis,
                probabilities=(RationalActionProbability(0, 1),) * len(hand_axis),
                key_digests=likelihood.key_digests,
                source_digest=likelihood.source_digest,
            )

    def test_stale_decisions_wrong_actors_and_illegal_actions_fail_closed(self) -> None:
        cards, betting = _initial_context()
        source = ImmutableFullWidthReferencePolicy("policy-adversaries-v1")
        decision = betting.legal_decision()
        with self.assertRaisesRegex(ValueError, "disagrees"):
            source.distribution_for(
                cards=cards,
                betting=betting,
                decision=replace(decision, stack=decision.stack - 1),
            )
        with self.assertRaisesRegex(ValueError, "public acting seat"):
            source.likelihood_for_axis(
                visible_cards=cards,
                actor_seat=4,
                hand_axis=cards.compatible_opponent_hands(),
                betting=betting,
                decision=decision,
                observed_action=CALL,
            )
        with self.assertRaisesRegex(ValueError, "unavailable action kind"):
            source.likelihood_for_axis(
                visible_cards=cards,
                actor_seat=3,
                hand_axis=cards.compatible_opponent_hands(),
                betting=betting,
                decision=decision,
                observed_action=CHECK,
            )
        with self.assertRaisesRegex(ValueError, "raise-to amount is not legal"):
            distribution = source.distribution_for(
                cards=cards,
                betting=betting,
                decision=decision,
            )
            bounds = decision.raise_bounds
            assert bounds is not None
            distribution.probability(raise_to(bounds.maximum_raise_to + 1))

    def test_rational_probability_and_source_reject_numerical_aliases(self) -> None:
        self.assertEqual(RationalActionProbability(2, 4), RationalActionProbability(1, 2))
        for numerator, denominator in ((True, 1), (1, False), (-1, 2), (3, 2), (1, 0)):
            with self.subTest(numerator=numerator, denominator=denominator), self.assertRaises(
                (TypeError, ValueError)
            ):
                RationalActionProbability(numerator, denominator)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "nonempty"):
            ImmutableFullWidthReferencePolicy("   ")
        cards, betting = _initial_context()
        distribution = ImmutableFullWidthReferencePolicy("modal-v1").distribution_for(
            cards=cards,
            betting=betting,
            decision=betting.legal_decision(),
        )
        self.assertNotIn(BettingActionKind.CHECK, distribution.decision.action_kinds)


if __name__ == "__main__":
    unittest.main()
