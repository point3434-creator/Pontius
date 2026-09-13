"""Bounded six-seat preflop/flop game with explicit diagnostic continuations.

This action-abstracted reference is not full no-limit hold'em or a solved leaf
model. All cards are sampled together; folds never return blockers to the deck.
The continuation policies use only the acting hand and the currently public
board. They are sensitivity controls, not equilibrium value estimates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from itertools import combinations, permutations
import json
import random

from .game import TERMINAL_PLAYER
from .holdem_cards import SixSeatHoldemDeal
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingAction,
    BettingActionKind,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from .river import HoleCards, RANKS, evaluate_five, evaluate_seven, make_hole


def preflop_class(hole: HoleCards) -> str:
    """Return one of the 169 rank/pair/suited classes, independent of suit name."""
    first, second = make_hole(*hole)
    low, high = first // 4, second // 4
    ranks = RANKS[high] + RANKS[low]
    return ranks if low == high else ranks + ("s" if first % 4 == second % 4 else "o")


def canonical_flop(hole: HoleCards, board: tuple[int, ...]) -> tuple[int, ...]:
    """Exact joint private/flop representation modulo suit and card ordering.

    Hole and flop roles remain separate. The flop is a simultaneous reveal, so
    its card order carries no information. Its canonical form retains the
    preflop class and every rank and suit relationship available on the flop.
    """
    hole = make_hole(*hole)
    if len(board) != 3 or len(set((*hole, *board))) != 5:
        raise ValueError("canonical flop requires five distinct private/public cards")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in board
    ):
        raise ValueError("invalid flop card")
    return min(
        (
            *sorted(4 * (card // 4) + permutation[card % 4] for card in hole),
            *sorted(4 * (card // 4) + permutation[card % 4] for card in board),
        )
        for permutation in permutations(range(4))
    )


def structural_flop(hole: HoleCards, board: tuple[int, ...]) -> tuple[int, int, int]:
    """Diagnostic v1 label of the five observed cards, independent of suit names.

    Components are made category (0..8), maximum suit multiplicity (0 for <=2,
    then 1/2/3 for 3/4/5), and straight potential (0/1/2 for zero/one/at least
    two distinct unseen completion ranks; 3 for an existing straight). The
    ace-low window is included. This deliberately merges strategically distinct
    boards and is not a production abstraction or an equity estimate.
    """
    hole = make_hole(*hole)
    if len(board) != 3 or any(type(card) is not int or card not in range(52) for card in board):
        raise ValueError("structural flop requires three valid public cards")
    cards = (*hole, *board)
    if len(set(cards)) != 5:
        raise ValueError("structural flop requires five distinct private/public cards")
    made = evaluate_five(cards)[0]
    flush = max(0, max(sum(card % 4 == suit for card in cards) for suit in range(4)) - 2)
    ranks = {card // 4 for card in cards}
    windows = [set(range(low, low + 5)) for low in range(9)]
    windows.append({12, 0, 1, 2, 3})
    missing = [window - ranks for window in windows]
    straight = (3 if any(not gap for gap in missing) else
                min(2, len({next(iter(gap)) for gap in missing if len(gap) == 1})))
    return made, flush, straight


def _raise_count(betting: NoLimitBettingState) -> int:
    return sum(
        record.street == betting.street and record.action.kind == BettingActionKind.RAISE
        for record in betting.history
    )


def _menu(betting: NoLimitBettingState, max_raises: int) -> tuple[BettingAction, ...]:
    decision = betting.legal_decision()
    actions = [FOLD, CALL] if decision.can_call else [CHECK]
    bounds = decision.raise_bounds
    if bounds is None or _raise_count(betting) >= max_raises:
        return tuple(actions)
    # A pot-sized raise first calls, then raises by the pot after that call.
    pot_raise = decision.current_bet + betting.pot + decision.to_call
    if betting.street == BettingStreet.PREFLOP:
        sizes = (5 * betting.big_blind // 2, pot_raise)
    else:
        sizes = (decision.current_bet + (betting.pot + decision.to_call + 1) // 2, pot_raise)
    # Named sizes outside the legal interval are omitted, never translated.
    legal_sizes = {
        amount for amount in sizes if bounds.minimum_raise_to <= amount <= bounds.maximum_raise_to
    }
    legal_sizes.add(bounds.maximum_raise_to)
    actions.extend(raise_to(amount) for amount in sorted(legal_sizes))
    return tuple(actions)


def continuation_action(
    policy: str,
    betting: NoLimitBettingState,
    hole: HoleCards,
    board: tuple[int, ...],
) -> BettingAction:
    """Frozen diagnostic policy; its API cannot receive others' or future cards.

    ``check_call`` always checks/calls. ``showdown_betting`` bets half pot with
    two pair or better when no wager exists, allows at most one bet per street,
    and calls a wager with a pair or better, folding high-card hands. The hand
    category includes board-made hands. No equity or solved-value claim applies.
    """
    if betting.street not in (BettingStreet.TURN, BettingStreet.RIVER):
        raise ValueError("continuation decisions require turn or river")
    if len(board) != (4 if betting.street == BettingStreet.TURN else 5):
        raise ValueError("continuation requires exactly the currently visible board")
    if policy not in ("check_call", "showdown_betting"):
        raise ValueError("unknown diagnostic continuation")
    decision = betting.legal_decision()
    passive = CHECK if decision.can_check else CALL
    if policy == "check_call":
        return passive
    cards = (*make_hole(*hole), *board)
    strength = (
        evaluate_seven(cards)
        if len(cards) == 7
        else max(evaluate_five(combo) for combo in combinations(cards, 5))
    )
    if decision.can_call:
        return CALL if strength[0] >= 1 else FOLD
    if strength[0] >= 2:
        raises = [action for action in _menu(betting, 1) if action.raise_to is not None]
        if raises:
            return raises[0]
    return passive


@dataclass(frozen=True, slots=True)
class EarlyHoldemGame:
    """Sampled six-player game in half-big-blind chips, with no rake.

    ``max_raises`` counts all aggressive actions per early street, including
    the opening bet and short all-ins. At the cap only fold/check/call remain.
    Exact public ledgers allow mixed stacks through ``state_for``; ``sample_root``
    starts equal stacks with button zero. Seats retain their absolute identity.
    """

    stack_bb: int = 20
    max_raises: int = 1
    continuation: str = "check_call"
    flop_representation: str = "exact"
    game_id: str = field(init=False)
    num_players: int = field(default=6, init=False)

    def __post_init__(self) -> None:
        if (
            isinstance(self.stack_bb, bool)
            or not isinstance(self.stack_bb, int)
            or self.stack_bb < 1
        ):
            raise ValueError("stack_bb must be a positive integer")
        if (
            isinstance(self.max_raises, bool)
            or not isinstance(self.max_raises, int)
            or self.max_raises < 0
        ):
            raise ValueError("max_raises must be a nonnegative integer")
        if self.continuation not in ("check_call", "showdown_betting"):
            raise ValueError("unknown diagnostic continuation")
        if self.flop_representation not in ("exact", "structural"):
            raise ValueError("flop_representation must be exact or structural")
        identity = {
            "schema": "early-holdem-v2",
            "stack_bb": self.stack_bb,
            "max_raises": self.max_raises,
            "continuation": self.continuation,
            "chips_per_bb": 2,
            "players": 6,
            "button": 0,
            "menu": "2.5bb-pot-preflop-halfpot-pot-flop-allin-v1",
            "cards": ("169-preflop-exact-suit-canonical-flop-v1"
                      if self.flop_representation == "exact" else
                      "169-preflop-structural-made-flush-straight-flop-v1"),
            "continuation_version": 1,
        }
        object.__setattr__(
            self, "game_id", sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        )

    def sample_root(self, rng: random.Random) -> EarlyHoldemState:
        cards = rng.sample(range(52), 17)
        deal = SixSeatHoldemDeal(
            tuple(tuple(cards[seat * 2 : seat * 2 + 2]) for seat in range(6)), tuple(cards[12:])
        )
        betting = NoLimitBettingState.new_hand(
            button=0, starting_stacks=(2 * self.stack_bb,) * 6, small_blind=1, big_blind=2
        )
        return self.state_for(deal, betting)

    def state_for(self, deal: SixSeatHoldemDeal, betting: NoLimitBettingState) -> EarlyHoldemState:
        if not isinstance(deal, SixSeatHoldemDeal) or not isinstance(betting, NoLimitBettingState):
            raise TypeError("state_for requires exact deal and betting state")
        while not betting.is_terminal:
            if betting.round_complete:
                betting = betting.advance_street()
            elif betting.street in (BettingStreet.PREFLOP, BettingStreet.FLOP):
                break
            else:
                action = continuation_action(
                    self.continuation,
                    betting,
                    deal.hand(betting.acting_seat),
                    deal.public_cards(betting.street),
                )
                betting = betting.apply_action(action)
        return EarlyHoldemState(self, deal, betting)


@dataclass(frozen=True, slots=True)
class EarlyHoldemState:
    game: EarlyHoldemGame
    deal: SixSeatHoldemDeal
    betting: NoLimitBettingState

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if self.betting.is_terminal else self.betting.acting_seat

    def legal_actions(self) -> tuple[str, ...]:
        return (
            ()
            if self.betting.is_terminal
            else tuple(str(action) for action in _menu(self.betting, self.game.max_raises))
        )

    def chance_outcomes(self) -> tuple[tuple[str, float], ...]:
        return ()  # All true chance is sampled once at the root.

    def apply_action(self, action: str) -> EarlyHoldemState:
        if self.betting.is_terminal:
            raise ValueError("cannot act at a terminal state")
        menu = {
            str(candidate): candidate for candidate in _menu(self.betting, self.game.max_raises)
        }
        if not isinstance(action, str) or action not in menu:
            raise ValueError("action is outside the explicit legal menu")
        return self.game.state_for(self.deal, self.betting.apply_action(menu[action]))

    def information_state_key(self, player: int) -> str:
        if player != self.current_player or self.betting.is_terminal:
            raise ValueError("information keys require the current early-street actor")
        hole = self.deal.hand(player)
        private = {"preflop": preflop_class(hole)}
        if self.betting.street == BettingStreet.FLOP:
            encoder = (
                canonical_flop if self.game.flop_representation == "exact" else structural_flop
            )
            private["flop"] = encoder(hole, self.deal.public_cards(BettingStreet.FLOP))
        # Every ledger field is public, including full ordered action history,
        # action reopening rights, starting stacks, contributions and position.
        return json.dumps(
            {
                "game": self.game.game_id,
                "actor": player,
                "private": private,
                "public": asdict(self.betting),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def returns(self) -> tuple[float, ...]:
        if not self.betting.is_terminal:
            raise ValueError("returns require a terminal hand")
        strengths = (
            self.deal.showdown_strengths(self.betting.live_seats)
            if self.betting.showdown_ready
            else None
        )
        return tuple(
            value / self.betting.big_blind for value in self.betting.settle(strengths).net_returns
        )
