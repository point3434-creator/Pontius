"""Exact, range-sensitive heads-up no-limit river microgame.

The game intentionally has one betting decision: player 0 may check or make a
fixed bet, after which player 1 may fold or call.  Its small tree is suitable
for exact best-response and normal-form oracles while retaining the poker
features that matter for range work: real cards, exact card removal, joint
ranges, private information, and showdown hand strength.

The joint deal distribution is part of game provenance, but not part of an
information-state key.  This separation lets the laboratory measure policy or
cache reuse across ranges without accidentally declaring two different ranges
to be the same solved object.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
from math import isfinite
from typing import TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER

CHECK = "check"
BET = "bet"
FOLD = "fold"
CALL = "call"

RANKS = "23456789TJQKA"
SUITS = "cdhs"

Card: TypeAlias = int
HoleCards: TypeAlias = tuple[Card, Card]
HandRank: TypeAlias = tuple[int, ...]


def parse_card(text: str) -> Card:
    """Parse a two-character card such as ``"As"`` into an integer."""

    if not isinstance(text, str) or len(text) != 2:
        raise ValueError(f"card must have rank and suit, got {text!r}")
    rank = text[0].upper()
    suit = text[1].lower()
    if rank not in RANKS or suit not in SUITS:
        raise ValueError(f"invalid card {text!r}")
    return RANKS.index(rank) * len(SUITS) + SUITS.index(suit)


def format_card(card: Card) -> str:
    """Return the canonical two-character representation of a card."""

    _validate_card(card)
    rank_index, suit_index = divmod(card, len(SUITS))
    return f"{RANKS[rank_index]}{SUITS[suit_index]}"


def make_hole(first: str | Card, second: str | Card) -> HoleCards:
    """Create a canonical two-card private hand."""

    cards = tuple(
        parse_card(card) if isinstance(card, str) else card
        for card in (first, second)
    )
    return _canonical_hole(cards)


def parse_cards(*cards: str) -> tuple[Card, ...]:
    """Convenience parser for a sequence of card strings."""

    parsed = tuple(parse_card(card) for card in cards)
    if len(set(parsed)) != len(parsed):
        raise ValueError("cards must be distinct")
    return parsed


def _validate_card(card: Card) -> None:
    if isinstance(card, bool) or not isinstance(card, int) or card not in range(52):
        raise ValueError(f"invalid card integer {card!r}")


def _canonical_hole(cards: Iterable[Card]) -> HoleCards:
    result = tuple(sorted(cards))
    if len(result) != 2:
        raise ValueError("a private hand must contain exactly two cards")
    for card in result:
        _validate_card(card)
    if result[0] == result[1]:
        raise ValueError("private cards must be distinct")
    return result


def _straight_high(ranks: set[int]) -> int | None:
    augmented = set(ranks)
    if 14 in augmented:
        augmented.add(1)
    for high in range(14, 4, -1):
        if all(rank in augmented for rank in range(high - 4, high + 1)):
            return high
    return None


@lru_cache(maxsize=200_000)
def _evaluate_five_cached(cards: tuple[Card, ...]) -> HandRank:
    ranks = [card // len(SUITS) + 2 for card in cards]
    suits = [card % len(SUITS) for card in cards]
    counts = Counter(ranks)
    groups = sorted(
        ((count, rank) for rank, count in counts.items()),
        reverse=True,
    )
    flush = len(set(suits)) == 1
    straight_high = _straight_high(set(ranks))

    if flush and straight_high is not None:
        return (8, straight_high)
    if groups[0][0] == 4:
        four_rank = groups[0][1]
        kicker = max(rank for rank in ranks if rank != four_rank)
        return (7, four_rank, kicker)
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *sorted(ranks, reverse=True))
    if straight_high is not None:
        return (4, straight_high)
    if groups[0][0] == 3:
        trip_rank = groups[0][1]
        kickers = sorted(
            (rank for rank in ranks if rank != trip_rank), reverse=True
        )
        return (3, trip_rank, *kickers)
    pair_ranks = sorted(
        (rank for rank, count in counts.items() if count == 2), reverse=True
    )
    if len(pair_ranks) == 2:
        kicker = max(rank for rank in ranks if rank not in pair_ranks)
        return (2, *pair_ranks, kicker)
    if len(pair_ranks) == 1:
        pair_rank = pair_ranks[0]
        kickers = sorted(
            (rank for rank in ranks if rank != pair_rank), reverse=True
        )
        return (1, pair_rank, *kickers)
    return (0, *sorted(ranks, reverse=True))


def evaluate_five(cards: Iterable[Card]) -> HandRank:
    """Return an exactly comparable rank tuple for five cards."""

    canonical = tuple(sorted(cards))
    if len(canonical) != 5 or len(set(canonical)) != 5:
        raise ValueError("five distinct cards are required")
    for card in canonical:
        _validate_card(card)
    return _evaluate_five_cached(canonical)


@lru_cache(maxsize=200_000)
def _evaluate_seven_cached(cards: tuple[Card, ...]) -> HandRank:
    return max(_evaluate_five_cached(combo) for combo in combinations(cards, 5))


def evaluate_seven(cards: Iterable[Card]) -> HandRank:
    """Return the best-five rank from seven distinct cards."""

    canonical = tuple(sorted(cards))
    if len(canonical) != 7 or len(set(canonical)) != 7:
        raise ValueError("seven distinct cards are required")
    for card in canonical:
        _validate_card(card)
    return _evaluate_seven_cached(canonical)


@dataclass(frozen=True, slots=True, order=True)
class RiverDeal:
    """A compatible pair of private hands, one for each player."""

    player0: HoleCards
    player1: HoleCards

    def __post_init__(self) -> None:
        player0 = _canonical_hole(self.player0)
        player1 = _canonical_hole(self.player1)
        if set(player0) & set(player1):
            raise ValueError("players' private hands overlap")
        object.__setattr__(self, "player0", player0)
        object.__setattr__(self, "player1", player1)

    def hand(self, player: int) -> HoleCards:
        if player == 0:
            return self.player0
        if player == 1:
            return self.player1
        raise ValueError(f"invalid player index {player}")


def _normalized_joint_weights(
    board: tuple[Card, ...],
    joint_weights: Mapping[RiverDeal, float],
) -> tuple[tuple[RiverDeal, float], ...]:
    if not joint_weights:
        raise ValueError("joint range must contain at least one deal")
    accumulated: dict[RiverDeal, float] = {}
    board_cards = set(board)
    for deal, supplied_weight in joint_weights.items():
        if not isinstance(deal, RiverDeal):
            raise TypeError("joint range keys must be RiverDeal instances")
        if board_cards & (set(deal.player0) | set(deal.player1)):
            raise ValueError("private cards overlap the public board")
        weight = float(supplied_weight)
        if not isfinite(weight) or weight < 0.0:
            raise ValueError("joint weights must be finite and nonnegative")
        if weight > 0.0:
            accumulated[deal] = accumulated.get(deal, 0.0) + weight
    total = sum(accumulated.values())
    if total <= 0.0 or not isfinite(total):
        raise ValueError("joint range must have positive finite mass")
    return tuple(
        (deal, weight / total)
        for deal, weight in sorted(accumulated.items())
    )


def _validate_marginal_weights(
    weights: Mapping[HoleCards, float],
    board: tuple[Card, ...],
    label: str,
) -> tuple[tuple[HoleCards, float], ...]:
    if not weights:
        raise ValueError(f"{label} range must not be empty")
    canonical_weights: dict[HoleCards, float] = {}
    for supplied_hand, supplied_weight in weights.items():
        hand = _canonical_hole(supplied_hand)
        if set(hand) & set(board):
            raise ValueError(f"{label} hand overlaps the public board")
        weight = float(supplied_weight)
        if not isfinite(weight) or weight < 0.0:
            raise ValueError(f"{label} weights must be finite and nonnegative")
        if weight > 0.0:
            canonical_weights[hand] = canonical_weights.get(hand, 0.0) + weight
    if not canonical_weights:
        raise ValueError(f"{label} range must have positive mass")
    return tuple(sorted(canonical_weights.items()))


def distribution_total_variation(
    first: Mapping[object, float],
    second: Mapping[object, float],
) -> float:
    """Return total-variation distance between normalized distributions."""

    first_mass = sum(first.values())
    second_mass = sum(second.values())
    if abs(first_mass - 1.0) > 1e-12 or abs(second_mass - 1.0) > 1e-12:
        raise ValueError("total variation requires normalized distributions")
    return 0.5 * sum(
        abs(first.get(outcome, 0.0) - second.get(outcome, 0.0))
        for outcome in set(first) | set(second)
    )


@dataclass(frozen=True, slots=True)
class RiverHoldem:
    """Exact heads-up river game with a fixed bet size and joint range."""

    board: tuple[Card, ...]
    pot: float
    stacks: tuple[float, float]
    bet_size: float
    deals: tuple[tuple[RiverDeal, float], ...]
    num_players: int = 2

    def __post_init__(self) -> None:
        board = tuple(self.board)
        if len(board) != 5 or len(set(board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in board:
            _validate_card(card)
        if self.num_players != 2:
            raise ValueError("the exact river microgame is heads-up")
        pot = float(self.pot)
        stacks = tuple(float(stack) for stack in self.stacks)
        bet_size = float(self.bet_size)
        if not isfinite(pot) or pot <= 0.0:
            raise ValueError("pot must be positive and finite")
        if len(stacks) != 2 or any(not isfinite(stack) or stack < 0.0 for stack in stacks):
            raise ValueError("two finite nonnegative stacks are required")
        if not isfinite(bet_size) or bet_size <= 0.0:
            raise ValueError("bet size must be positive and finite")
        if bet_size > min(stacks):
            raise ValueError("bet size cannot exceed either remaining stack")

        raw_weights: dict[RiverDeal, float] = {}
        for deal, probability in self.deals:
            raw_weights[deal] = raw_weights.get(deal, 0.0) + float(probability)
        normalized = _normalized_joint_weights(board, raw_weights)

        object.__setattr__(self, "board", board)
        object.__setattr__(self, "pot", pot)
        object.__setattr__(self, "stacks", stacks)
        object.__setattr__(self, "bet_size", bet_size)
        object.__setattr__(self, "deals", normalized)

    @classmethod
    def from_joint_weights(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: tuple[float, float],
        bet_size: float,
        joint_weights: Mapping[RiverDeal, float],
    ) -> RiverHoldem:
        """Build a game from an explicit joint distribution over deals."""

        canonical_board = tuple(sorted(board))
        deals = _normalized_joint_weights(canonical_board, joint_weights)
        return cls(canonical_board, pot, stacks, bet_size, deals)

    @classmethod
    def from_independent_ranges(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: tuple[float, float],
        bet_size: float,
        player0_weights: Mapping[HoleCards, float],
        player1_weights: Mapping[HoleCards, float],
    ) -> RiverHoldem:
        """Multiply marginal weights, remove blocked deals, and renormalize."""

        canonical_board = tuple(sorted(board))
        if len(canonical_board) != 5 or len(set(canonical_board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in canonical_board:
            _validate_card(card)
        player0 = _validate_marginal_weights(
            player0_weights, canonical_board, "player 0"
        )
        player1 = _validate_marginal_weights(
            player1_weights, canonical_board, "player 1"
        )
        joint_weights = {
            RiverDeal(hand0, hand1): weight0 * weight1
            for hand0, weight0 in player0
            for hand1, weight1 in player1
            if not set(hand0) & set(hand1)
        }
        if not joint_weights:
            raise ValueError("card removal eliminated every joint deal")
        return cls.from_joint_weights(
            board=canonical_board,
            pot=pot,
            stacks=stacks,
            bet_size=bet_size,
            joint_weights=joint_weights,
        )

    def initial_state(self) -> RiverState:
        return RiverState(game=self)

    def joint_distribution(self) -> dict[RiverDeal, float]:
        return dict(self.deals)

    def marginal_distribution(self, player: int) -> dict[HoleCards, float]:
        if player not in (0, 1):
            raise ValueError(f"invalid player index {player}")
        result: dict[HoleCards, float] = {}
        for deal, probability in self.deals:
            hand = deal.hand(player)
            result[hand] = result.get(hand, 0.0) + probability
        return dict(sorted(result.items()))

    def conditional_opponent_distribution(
        self,
        player: int,
        own_hand: HoleCards,
    ) -> dict[HoleCards, float]:
        """Return the exact opponent range conditional on a private hand."""

        if player not in (0, 1):
            raise ValueError(f"invalid player index {player}")
        canonical_hand = _canonical_hole(own_hand)
        opponent_weights: dict[HoleCards, float] = {}
        own_mass = 0.0
        for deal, probability in self.deals:
            if deal.hand(player) == canonical_hand:
                opponent = deal.hand(1 - player)
                opponent_weights[opponent] = (
                    opponent_weights.get(opponent, 0.0) + probability
                )
                own_mass += probability
        if own_mass <= 0.0:
            raise ValueError("private hand has zero probability under this range")
        return {
            hand: probability / own_mass
            for hand, probability in sorted(opponent_weights.items())
        }

    @property
    def structural_digest(self) -> str:
        payload = "|".join(
            (
                "river-v1",
                ",".join(format_card(card) for card in self.board),
                self.pot.hex(),
                self.stacks[0].hex(),
                self.stacks[1].hex(),
                self.bet_size.hex(),
            )
        )
        return sha256(payload.encode("ascii")).hexdigest()

    @property
    def provenance_digest(self) -> str:
        range_payload = ";".join(
            f"{_format_hole(deal.player0)}/{_format_hole(deal.player1)}={probability.hex()}"
            for deal, probability in self.deals
        )
        payload = f"{self.structural_digest}|{range_payload}"
        return sha256(payload.encode("ascii")).hexdigest()

    def total_variation(self, other: RiverHoldem) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.joint_distribution(), other.joint_distribution()
        )

    def conditional_opponent_total_variation(
        self,
        other: RiverHoldem,
        *,
        player: int,
        own_hand: HoleCards,
    ) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.conditional_opponent_distribution(player, own_hand),
            other.conditional_opponent_distribution(player, own_hand),
        )

    @property
    def payoff_span(self) -> float:
        """Maximum minus minimum terminal utility for either player."""

        return self.pot + 2.0 * self.bet_size

    def fixed_policy_value_bound(self, other: RiverHoldem) -> float:
        """Bound value movement for one fixed policy under a range change.

        This does not certify equilibrium-policy reuse.  It only applies to the
        value of an unchanged behavioral policy in structurally identical games.
        """

        return self.payoff_span * self.total_variation(other)

    def _require_same_structure(self, other: RiverHoldem) -> None:
        if not isinstance(other, RiverHoldem):
            raise TypeError("range comparison requires another RiverHoldem game")
        if self.structural_digest != other.structural_digest:
            raise ValueError("range comparison requires identical game structure")


def _format_hole(hand: HoleCards) -> str:
    return "".join(format_card(card) for card in hand)


@dataclass(frozen=True, slots=True)
class RiverState:
    """Immutable state in :class:`RiverHoldem`."""

    game: RiverHoldem
    deal: RiverDeal | None = None
    history: tuple[tuple[int, str], ...] = ()
    terminal: bool = False

    @property
    def current_player(self) -> int:
        if self.deal is None:
            return CHANCE_PLAYER
        if self.terminal:
            return TERMINAL_PLAYER
        if not self.history:
            return 0
        if self.history == ((0, BET),):
            return 1
        raise ValueError(f"invalid nonterminal river history {self.history!r}")

    def legal_actions(self) -> tuple[str, ...]:
        player = self.current_player
        if player == 0:
            return (CHECK, BET)
        if player == 1:
            return (FOLD, CALL)
        return ()

    def chance_outcomes(self) -> tuple[tuple[RiverDeal, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        return self.game.deals

    def apply_action(self, action: Action) -> RiverState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if player == CHANCE_PLAYER:
            if not isinstance(action, RiverDeal) or action not in dict(self.game.deals):
                raise ValueError(f"invalid river deal {action!r}")
            return RiverState(game=self.game, deal=action)

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, str)
        history = self.history + ((player, action),)
        return RiverState(
            game=self.game,
            deal=self.deal,
            history=history,
            terminal=action in (CHECK, FOLD, CALL),
        )

    def information_state_key(self, player: int) -> str:
        if self.deal is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player not in (0, 1):
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        history = "root" if not self.history else "/".join(
            f"p{seat}:{action}" for seat, action in self.history
        )
        return (
            f"river|structure={self.game.structural_digest}|p{player}|"
            f"hand={_format_hole(self.deal.hand(player))}|history={history}"
        )

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER or self.deal is None:
            raise ValueError("returns are available only at terminal states")
        if self.history[-1][1] == FOLD:
            utility0 = self.game.pot / 2.0
            return (utility0, -utility0)

        rank0 = evaluate_seven((*self.game.board, *self.deal.player0))
        rank1 = evaluate_seven((*self.game.board, *self.deal.player1))
        if rank0 == rank1:
            return (0.0, 0.0)
        showdown_stake = self.game.pot / 2.0
        if self.history[-1][1] == CALL:
            showdown_stake += self.game.bet_size
        utility0 = showdown_stake if rank0 > rank1 else -showdown_stake
        return (utility0, -utility0)
