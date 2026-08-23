"""Exact explicit-deal and one-seat card state for full-hand reference replay.

The agent-visible state deliberately contains only one private hand and the
currently revealed public board.  The complete six-seat deal is a separate
oracle/replay object and is never needed to construct a blueprint decision key.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from math import comb

from .no_limit_betting import BETTING_STREETS, SEAT_COUNT, BettingStreet
from .river import (
    Card,
    HandRank,
    HoleCards,
    _canonical_hole,
    _validate_card,
    evaluate_five,
    evaluate_seven,
    format_card,
    make_hole,
    parse_card,
    parse_cards,
)

DECK: tuple[Card, ...] = tuple(range(52))
_PUBLIC_CARD_COUNTS: dict[BettingStreet, int] = {
    BettingStreet.PREFLOP: 0,
    BettingStreet.FLOP: 3,
    BettingStreet.TURN: 4,
    BettingStreet.RIVER: 5,
}
_REVEAL_COUNTS: dict[BettingStreet, int] = {
    BettingStreet.FLOP: 3,
    BettingStreet.TURN: 1,
    BettingStreet.RIVER: 1,
}


def _require_seat(seat: object, *, label: str = "seat") -> int:
    if (
        isinstance(seat, bool)
        or not isinstance(seat, int)
        or seat not in range(SEAT_COUNT)
    ):
        raise ValueError(f"{label} must identify one of six seats")
    return seat


def _canonical_board(cards: tuple[Card, ...], *, expected: int) -> tuple[Card, ...]:
    if not isinstance(cards, tuple):
        raise TypeError("public cards must be an immutable tuple")
    if len(cards) != expected:
        raise ValueError(f"public board must contain exactly {expected} cards")
    for card in cards:
        _validate_card(card)
    if len(set(cards)) != len(cards):
        raise ValueError("public board cards must be distinct")
    return cards


@dataclass(frozen=True, slots=True)
class SixSeatHoldemDeal:
    """One explicit six-seat private deal and ordered five-card board runout."""

    private_hands: tuple[HoleCards, ...]
    board_runout: tuple[Card, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.private_hands, tuple):
            raise TypeError("private hands must be an immutable tuple")
        if len(self.private_hands) != SEAT_COUNT:
            raise ValueError("an explicit hold'em deal requires six private hands")
        hands = tuple(_canonical_hole(hand) for hand in self.private_hands)
        board = _canonical_board(self.board_runout, expected=5)
        playable = (*board, *(card for hand in hands for card in hand))
        if len(playable) != 17 or len(set(playable)) != 17:
            raise ValueError("all 17 playable deal cards must be distinct")
        object.__setattr__(self, "private_hands", hands)
        object.__setattr__(self, "board_runout", board)

    def hand(self, seat: int) -> HoleCards:
        return self.private_hands[_require_seat(seat)]

    def public_cards(self, street: BettingStreet) -> tuple[Card, ...]:
        if not isinstance(street, BettingStreet):
            raise TypeError("public-card lookup requires a canonical betting street")
        return self.board_runout[: _PUBLIC_CARD_COUNTS[street]]

    def reveal_for(self, street: BettingStreet) -> tuple[Card, ...]:
        """Return only the newly revealed cards for a postflop street."""

        if street not in _REVEAL_COUNTS:
            raise ValueError("only flop, turn, and river reveal public cards")
        previous = BETTING_STREETS[BETTING_STREETS.index(street) - 1]
        return self.public_cards(street)[len(self.public_cards(previous)) :]

    def showdown_strengths(
        self,
        live_seats: tuple[int, ...],
    ) -> tuple[HandRank | None, ...]:
        if not isinstance(live_seats, tuple):
            raise TypeError("live seats must be an immutable tuple")
        if len(set(live_seats)) != len(live_seats):
            raise ValueError("live showdown seats must be unique")
        live = {_require_seat(seat, label="live showdown seat") for seat in live_seats}
        return tuple(
            evaluate_seven((*self.board_runout, *self.private_hands[seat]))
            if seat in live
            else None
            for seat in range(SEAT_COUNT)
        )

    @property
    def digest(self) -> str:
        payload = "|".join(
            (
                "six-seat-explicit-deal-v1",
                "/".join(
                    "".join(format_card(card) for card in hand)
                    for hand in self.private_hands
                ),
                "".join(format_card(card) for card in self.board_runout),
            )
        )
        return sha256(payload.encode("ascii")).hexdigest()


@dataclass(frozen=True, slots=True)
class OneSeatCardState:
    """Future-blind agent view of one private hand and the public board."""

    controlled_seat: int
    private_hand: HoleCards
    street: BettingStreet
    board: tuple[Card, ...] = ()

    def __post_init__(self) -> None:
        seat = _require_seat(self.controlled_seat, label="controlled seat")
        hand = _canonical_hole(self.private_hand)
        if not isinstance(self.street, BettingStreet):
            raise TypeError("card state street must be canonical")
        board = _canonical_board(
            self.board,
            expected=_PUBLIC_CARD_COUNTS[self.street],
        )
        if set(hand) & set(board):
            raise ValueError("controlled private hand overlaps the public board")
        object.__setattr__(self, "controlled_seat", seat)
        object.__setattr__(self, "private_hand", hand)
        object.__setattr__(self, "board", board)

    @classmethod
    def preflop(cls, *, controlled_seat: int, private_hand: HoleCards) -> OneSeatCardState:
        return cls(
            controlled_seat=controlled_seat,
            private_hand=private_hand,
            street=BettingStreet.PREFLOP,
        )

    @property
    def known_cards(self) -> tuple[Card, ...]:
        return (*self.private_hand, *self.board)

    @property
    def remaining_deck(self) -> tuple[Card, ...]:
        blocked = set(self.known_cards)
        return tuple(card for card in DECK if card not in blocked)

    @property
    def compatible_opponent_hand_count(self) -> int:
        return comb(len(self.remaining_deck), 2)

    def compatible_opponent_hands(self) -> tuple[HoleCards, ...]:
        return tuple(combinations(self.remaining_deck, 2))

    def advance_to(
        self,
        street: BettingStreet,
        revealed_cards: tuple[Card, ...],
    ) -> OneSeatCardState:
        if not isinstance(street, BettingStreet):
            raise TypeError("card-state transition requires a canonical street")
        current_index = BETTING_STREETS.index(self.street)
        if current_index + 1 >= len(BETTING_STREETS) or BETTING_STREETS[
            current_index + 1
        ] is not street:
            raise ValueError("card-state transitions must advance exactly one street")
        reveal = _canonical_board(
            revealed_cards,
            expected=_REVEAL_COUNTS[street],
        )
        if set(reveal) & set(self.known_cards):
            raise ValueError("new public cards overlap already known cards")
        return OneSeatCardState(
            controlled_seat=self.controlled_seat,
            private_hand=self.private_hand,
            street=street,
            board=(*self.board, *reveal),
        )

    def require_compatible_deal(self, deal: SixSeatHoldemDeal) -> None:
        if not isinstance(deal, SixSeatHoldemDeal):
            raise TypeError("card-state compatibility requires an explicit deal")
        if deal.hand(self.controlled_seat) != self.private_hand:
            raise ValueError("explicit deal disagrees with the controlled private hand")
        if deal.public_cards(self.street) != self.board:
            raise ValueError("explicit deal disagrees with the revealed public board")

    @property
    def public_digest(self) -> str:
        payload = "|".join(
            (
                "one-seat-card-state-v1",
                str(self.controlled_seat),
                self.street.value,
                "".join(format_card(card) for card in self.private_hand),
                "".join(format_card(card) for card in self.board),
            )
        )
        return sha256(payload.encode("ascii")).hexdigest()


__all__ = [
    "DECK",
    "Card",
    "HandRank",
    "HoleCards",
    "OneSeatCardState",
    "SixSeatHoldemDeal",
    "evaluate_five",
    "evaluate_seven",
    "format_card",
    "make_hole",
    "parse_card",
    "parse_cards",
]
