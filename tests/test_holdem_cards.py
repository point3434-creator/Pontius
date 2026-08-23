from __future__ import annotations

import random
import unittest

from pontius.holdem_cards import (
    DECK,
    OneSeatCardState,
    SixSeatHoldemDeal,
    evaluate_seven,
    make_hole,
    parse_cards,
)
from pontius.no_limit_betting import BettingStreet


def _fixture_deal() -> SixSeatHoldemDeal:
    return SixSeatHoldemDeal(
        private_hands=(
            make_hole("As", "Ad"),
            make_hole("Kh", "Kd"),
            make_hole("Ts", "8s"),
            make_hole("Ks", "Td"),
            make_hole("Ah", "3h"),
            make_hole("4s", "5s"),
        ),
        board_runout=parse_cards("2c", "7d", "9h", "Js", "Qc"),
    )


def _future_variant_deal(*, reverse: bool) -> SixSeatHoldemDeal:
    own_hand = make_hole("As", "Ad")
    flop = parse_cards("2c", "7d", "9h")
    blocked = {*own_hand, *flop}
    remaining = [card for card in DECK if card not in blocked]
    if reverse:
        remaining.reverse()
    cursor = iter(remaining)
    hands = []
    for seat in range(6):
        if seat == 3:
            hands.append(own_hand)
        else:
            hands.append((next(cursor), next(cursor)))
    board = (*flop, next(cursor), next(cursor))
    return SixSeatHoldemDeal(tuple(hands), board)


class SixSeatHoldemDealTests(unittest.TestCase):
    def test_explicit_deal_has_seventeen_distinct_cards_and_stable_digest(self) -> None:
        deal = _fixture_deal()
        playable = (
            *deal.board_runout,
            *(card for hand in deal.private_hands for card in hand),
        )
        self.assertEqual(len(playable), 17)
        self.assertEqual(len(set(playable)), 17)
        self.assertEqual(deal.digest, _fixture_deal().digest)
        self.assertEqual(deal.public_cards(BettingStreet.PREFLOP), ())
        self.assertEqual(len(deal.public_cards(BettingStreet.FLOP)), 3)
        self.assertEqual(len(deal.public_cards(BettingStreet.TURN)), 4)
        self.assertEqual(len(deal.public_cards(BettingStreet.RIVER)), 5)
        self.assertEqual(len(deal.reveal_for(BettingStreet.FLOP)), 3)
        self.assertEqual(len(deal.reveal_for(BettingStreet.TURN)), 1)
        self.assertEqual(len(deal.reveal_for(BettingStreet.RIVER)), 1)

    def test_invalid_and_mutable_deal_shapes_fail_closed(self) -> None:
        deal = _fixture_deal()
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            SixSeatHoldemDeal(  # type: ignore[arg-type]
                private_hands=list(deal.private_hands),
                board_runout=deal.board_runout,
            )
        with self.assertRaisesRegex(ValueError, "six private hands"):
            SixSeatHoldemDeal(deal.private_hands[:-1], deal.board_runout)
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            SixSeatHoldemDeal(  # type: ignore[arg-type]
                deal.private_hands,
                list(deal.board_runout),
            )
        with self.assertRaisesRegex(ValueError, "17 playable"):
            SixSeatHoldemDeal(
                deal.private_hands,
                (*deal.board_runout[:-1], deal.private_hands[0][0]),
            )
        with self.assertRaisesRegex(ValueError, "only flop"):
            deal.reveal_for(BettingStreet.PREFLOP)

    def test_showdown_strengths_reveal_only_live_seats(self) -> None:
        deal = _fixture_deal()
        strengths = deal.showdown_strengths((0, 3))
        self.assertIsNotNone(strengths[0])
        self.assertIsNotNone(strengths[3])
        self.assertTrue(all(strengths[seat] is None for seat in (1, 2, 4, 5)))
        with self.assertRaisesRegex(ValueError, "unique"):
            deal.showdown_strengths((0, 0))


class OneSeatCardStateTests(unittest.TestCase):
    def test_exact_card_removal_counts_and_domains_on_every_street(self) -> None:
        deal = _fixture_deal()
        cards = OneSeatCardState.preflop(
            controlled_seat=3,
            private_hand=deal.hand(3),
        )
        expected = (
            (BettingStreet.PREFLOP, 0, 1_225),
            (BettingStreet.FLOP, 3, 1_081),
            (BettingStreet.TURN, 4, 1_035),
            (BettingStreet.RIVER, 5, 990),
        )
        for index, (street, board_size, combo_count) in enumerate(expected):
            deal_cards = set(cards.known_cards)
            compatible = cards.compatible_opponent_hands()
            self.assertEqual(cards.street, street)
            self.assertEqual(len(cards.board), board_size)
            self.assertEqual(cards.compatible_opponent_hand_count, combo_count)
            self.assertEqual(len(compatible), combo_count)
            self.assertEqual(len(set(compatible)), combo_count)
            self.assertTrue(
                all(not (set(hand) & deal_cards) for hand in compatible)
            )
            cards.require_compatible_deal(deal)
            if index + 1 < len(expected):
                next_street = expected[index + 1][0]
                cards = cards.advance_to(
                    next_street,
                    deal.reveal_for(next_street),
                )

    def test_agent_view_is_blind_to_opponents_and_future_runout(self) -> None:
        first = _future_variant_deal(reverse=False)
        second = _future_variant_deal(reverse=True)
        preflop = OneSeatCardState.preflop(
            controlled_seat=3,
            private_hand=first.hand(3),
        )
        preflop.require_compatible_deal(first)
        preflop.require_compatible_deal(second)
        first_flop = preflop.advance_to(
            BettingStreet.FLOP,
            first.reveal_for(BettingStreet.FLOP),
        )
        second_flop = preflop.advance_to(
            BettingStreet.FLOP,
            second.reveal_for(BettingStreet.FLOP),
        )
        self.assertEqual(first_flop, second_flop)
        self.assertEqual(first_flop.public_digest, second_flop.public_digest)
        first_flop.require_compatible_deal(first)
        second_flop.require_compatible_deal(second)
        self.assertNotEqual(first.board_runout[3:], second.board_runout[3:])
        self.assertNotEqual(first.private_hands[:3], second.private_hands[:3])

    def test_future_and_overlapping_reveals_fail_closed(self) -> None:
        deal = _fixture_deal()
        cards = OneSeatCardState.preflop(
            controlled_seat=3,
            private_hand=deal.hand(3),
        )
        with self.assertRaisesRegex(ValueError, "exactly one street"):
            cards.advance_to(BettingStreet.TURN, deal.public_cards(BettingStreet.TURN))
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            cards.advance_to(BettingStreet.FLOP, deal.reveal_for(BettingStreet.TURN))
        with self.assertRaisesRegex(ValueError, "already known"):
            cards.advance_to(
                BettingStreet.FLOP,
                (deal.hand(3)[0], *deal.reveal_for(BettingStreet.FLOP)[:2]),
            )
        mismatched = OneSeatCardState.preflop(
            controlled_seat=2,
            private_hand=deal.hand(3),
        )
        with self.assertRaisesRegex(ValueError, "private hand"):
            mismatched.require_compatible_deal(deal)

    def test_seeded_explicit_deals_preserve_visibility_and_evaluator_determinism(self) -> None:
        for seed in range(200):
            deck = list(DECK)
            random.Random(seed).shuffle(deck)
            deal = SixSeatHoldemDeal(
                private_hands=tuple(
                    (deck[2 * seat], deck[2 * seat + 1])
                    for seat in range(6)
                ),
                board_runout=tuple(deck[12:17]),
            )
            controlled = seed % 6
            cards = OneSeatCardState.preflop(
                controlled_seat=controlled,
                private_hand=deal.hand(controlled),
            )
            for street, expected_count in (
                (BettingStreet.PREFLOP, 1_225),
                (BettingStreet.FLOP, 1_081),
                (BettingStreet.TURN, 1_035),
                (BettingStreet.RIVER, 990),
            ):
                if cards.street is not street:
                    cards = cards.advance_to(street, deal.reveal_for(street))
                cards.require_compatible_deal(deal)
                self.assertEqual(cards.compatible_opponent_hand_count, expected_count)
                self.assertEqual(
                    len(set(cards.known_cards)),
                    len(cards.known_cards),
                )
            seven = (*deal.board_runout, *deal.hand(controlled))
            self.assertEqual(evaluate_seven(seven), evaluate_seven(seven))


if __name__ == "__main__":
    unittest.main()
