"""Exact heads-up river continuations backed by the six-seat betting kernel.

This module is an additive bridge between the authoritative integer-chip
betting state and the generic extensive-form evaluators.  It deliberately
models only a checked-to river continuation with exactly two live seats.  The
restricted entry condition makes a root check terminal while retaining every
kernel-legal opening bet, responder raise, short all-in, and final response.

The bridge is a small-game semantic control, not a scalable production tree.
It enumerates every legal integer raise-to amount returned by the kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import fsum

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER
from .legal_decision_spine_v2 import public_betting_state_sha256
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    BettingActionKind,
    BettingStreet,
    NoLimitBettingState,
    TerminalReason,
    raise_to,
)
from .river import (
    Card,
    RiverDeal,
    _format_hole,
    _normalized_joint_weights,
    _validate_card,
    evaluate_seven,
    format_card,
)


def _legal_actions(state: NoLimitBettingState) -> tuple[BettingAction, ...]:
    """Enumerate the kernel's complete finite action set in semantic order."""

    decision = state.legal_decision()
    actions: list[BettingAction] = []
    if decision.can_fold:
        actions.append(FOLD)
    if decision.can_check:
        actions.append(CHECK)
    if decision.can_call:
        actions.append(CALL)
    bounds = decision.raise_bounds
    if bounds is not None:
        actions.extend(
            raise_to(amount)
            for amount in range(
                bounds.minimum_raise_to,
                bounds.maximum_raise_to + 1,
            )
        )
    if not actions or len(actions) != len(set(actions)):
        raise AssertionError("kernel continuation produced an invalid action set")
    return tuple(actions)


def _action_token(action: BettingAction) -> str:
    if action.kind is BettingActionKind.RAISE:
        return f"raise-to-{action.raise_to}"
    return action.kind.value


@dataclass(frozen=True, slots=True)
class LegalHeadsUpRiverContinuation:
    """Two-player exact-card game over one checked-to legal river state.

    Logical player zero is the root table seat and logical player one is the
    other live table seat.  All omitted table seats must already be folded and
    must have committed zero chips, so the two returned utilities remain an
    exact zero-sum slice of the six-seat settlement.
    """

    board: tuple[Card, ...]
    base_state: NoLimitBettingState
    deals: tuple[tuple[RiverDeal, float], ...]
    num_players: int = 2

    def __post_init__(self) -> None:
        board = tuple(sorted(self.board))
        if len(board) != 5 or len(set(board)) != 5:
            raise ValueError("the legal continuation requires a five-card river board")
        for card in board:
            _validate_card(card)
        if self.num_players != 2:
            raise ValueError("the legal river continuation has exactly two players")
        if not isinstance(self.base_state, NoLimitBettingState):
            raise TypeError("the legal continuation requires an exact betting state")
        self.base_state.assert_invariants()
        self._validate_base_state(self.base_state)

        raw_weights: dict[RiverDeal, float] = {}
        for deal, probability in self.deals:
            raw_weights[deal] = raw_weights.get(deal, 0.0) + float(probability)
        normalized = _normalized_joint_weights(board, raw_weights)
        object.__setattr__(self, "board", board)
        object.__setattr__(self, "deals", normalized)

    @staticmethod
    def _validate_base_state(state: NoLimitBettingState) -> None:
        if state.street is not BettingStreet.RIVER:
            raise ValueError("the legal continuation must begin on the river")
        if state.is_terminal or state.round_complete:
            raise ValueError("the legal continuation must begin at a live decision")
        if len(state.live_seats) != 2:
            raise ValueError("the legal continuation requires exactly two live seats")
        root = state.acting_seat
        if root is None or state.pending_seats != (root,):
            raise ValueError("the legal continuation must begin after the other seat checked")
        other = next(seat for seat in state.live_seats if seat != root)
        omitted = tuple(seat for seat in range(SEAT_COUNT) if seat not in (root, other))
        if any(not state.folded[seat] for seat in omitted):
            raise ValueError("every omitted table seat must already be folded")
        if any(state.total_contributions[seat] != 0 for seat in omitted):
            raise ValueError("omitted table seats must have zero committed chips")
        if state.current_bet != 0 or any(state.street_contributions):
            raise ValueError("the checked-to continuation must have no river wager")
        river_records = tuple(
            record for record in state.history if record.street is BettingStreet.RIVER
        )
        if (
            len(river_records) != 1
            or river_records[0].seat != other
            or river_records[0].action != CHECK
        ):
            raise ValueError("the continuation must follow exactly one live river check")
        decision = state.legal_decision()
        if decision.action_kinds != (
            BettingActionKind.CHECK,
            BettingActionKind.RAISE,
        ):
            raise ValueError("the continuation root must be an exact check-or-bet decision")

    @property
    def table_seats(self) -> tuple[int, int]:
        root = self.base_state.acting_seat
        if root is None:
            raise AssertionError("validated legal continuation lost its root actor")
        other = next(seat for seat in self.base_state.live_seats if seat != root)
        return root, other

    @property
    def structural_digest(self) -> str:
        payload = "|".join(
            (
                "legal-heads-up-river-continuation-v1",
                ",".join(format_card(card) for card in self.board),
                public_betting_state_sha256(self.base_state),
                ",".join(str(seat) for seat in self.table_seats),
            )
        )
        return sha256(payload.encode("ascii")).hexdigest()

    @property
    def provenance_digest(self) -> str:
        range_payload = ";".join(
            f"{_format_hole(deal.player0)}/{_format_hole(deal.player1)}={probability.hex()}"
            for deal, probability in self.deals
        )
        return sha256(
            f"{self.structural_digest}|{range_payload}".encode("ascii")
        ).hexdigest()

    def initial_state(self) -> LegalHeadsUpRiverState:
        return LegalHeadsUpRiverState(game=self, betting=self.base_state)


@dataclass(frozen=True, slots=True)
class LegalHeadsUpRiverState:
    """Immutable extensive-form state over a legal betting continuation."""

    game: LegalHeadsUpRiverContinuation
    betting: NoLimitBettingState
    deal: RiverDeal | None = None
    continuation_history: tuple[tuple[int, BettingAction], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.game, LegalHeadsUpRiverContinuation):
            raise TypeError("legal river state requires its canonical game")
        if not isinstance(self.betting, NoLimitBettingState):
            raise TypeError("legal river state requires an exact betting state")
        self.betting.assert_invariants()
        if self.deal is not None and (
            not isinstance(self.deal, RiverDeal) or self.deal not in dict(self.game.deals)
        ):
            raise ValueError("legal river state contains an off-range deal")
        expected = self.game.base_state
        for player, action in self.continuation_history:
            if player not in (0, 1) or not isinstance(action, BettingAction):
                raise ValueError("legal river continuation history is not semantic")
            if expected.is_terminal:
                raise ValueError("legal river continuation history extends a terminal")
            if expected.acting_seat != self.game.table_seats[player]:
                raise ValueError("legal river continuation history actor is inconsistent")
            expected = expected.apply_action(action)
        if self.betting != expected:
            raise ValueError("legal river betting state is not the exact history replay")
        if self.deal is None and self.continuation_history:
            raise ValueError("chance must resolve before legal continuation actions")

    @property
    def current_player(self) -> int:
        if self.deal is None:
            return CHANCE_PLAYER
        if self.betting.is_terminal:
            return TERMINAL_PLAYER
        seat = self.betting.acting_seat
        if seat is None:
            raise ValueError("live legal continuation has no acting seat")
        try:
            return self.game.table_seats.index(seat)
        except ValueError as error:
            raise ValueError("an omitted table seat became active") from error

    def legal_actions(self) -> tuple[BettingAction, ...]:
        if self.current_player < 0:
            return ()
        return _legal_actions(self.betting)

    def chance_outcomes(self) -> tuple[tuple[RiverDeal, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        return self.game.deals

    def apply_action(self, action: Action) -> LegalHeadsUpRiverState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal legal continuation")
        if player == CHANCE_PLAYER:
            if not isinstance(action, RiverDeal) or action not in dict(self.game.deals):
                raise ValueError(f"invalid legal-continuation deal {action!r}")
            return LegalHeadsUpRiverState(
                game=self.game,
                betting=self.betting,
                deal=action,
                continuation_history=self.continuation_history,
            )
        if not isinstance(action, BettingAction) or action not in self.legal_actions():
            raise ValueError(
                f"illegal continuation action {action!r}; "
                f"legal actions are {self.legal_actions()!r}"
            )
        seat = self.game.table_seats[player]
        if seat != self.betting.acting_seat:
            raise AssertionError("logical player and exact betting actor disagree")
        advanced = self.betting.apply_action(action)
        if advanced.round_complete and not advanced.is_terminal:
            raise AssertionError("a completed river continuation did not become terminal")
        return LegalHeadsUpRiverState(
            game=self.game,
            betting=advanced,
            deal=self.deal,
            continuation_history=(*self.continuation_history, (player, action)),
        )

    def information_state_key(self, player: int) -> str:
        if self.deal is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player not in (0, 1):
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        history = (
            "root"
            if not self.continuation_history
            else "/".join(
                f"p{actor}:{_action_token(action)}"
                for actor, action in self.continuation_history
            )
        )
        return (
            f"legal-river|structure={self.game.structural_digest}|p{player}|"
            f"hand={_format_hole(self.deal.hand(player))}|history={history}"
        )

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER or self.deal is None:
            raise ValueError("returns are available only at a terminal continuation")
        if self.betting.terminal_reason is TerminalReason.FOLD:
            settlement = self.betting.settle()
        elif self.betting.terminal_reason is TerminalReason.SHOWDOWN:
            strengths: list[tuple[int, ...] | None] = [None] * SEAT_COUNT
            for player, seat in enumerate(self.game.table_seats):
                strengths[seat] = evaluate_seven(
                    (*self.game.board, *self.deal.hand(player))
                )
            settlement = self.betting.settle(strengths)
        else:
            raise AssertionError("terminal legal continuation has no terminal reason")
        result = tuple(
            float(settlement.net_returns[seat]) for seat in self.game.table_seats
        )
        if abs(fsum(result)) > 0.0:
            raise AssertionError("two-seat legal continuation is not exactly zero-sum")
        return result


__all__ = [
    "LegalHeadsUpRiverContinuation",
    "LegalHeadsUpRiverState",
]
