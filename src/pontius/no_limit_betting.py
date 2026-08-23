"""Exact integer-chip betting state for one six-max no-limit hold'em hand.

The module deliberately separates public betting semantics from cards, beliefs,
and solving.  It is a reference kernel: actions use total chips committed on the
current street (``raise-to``), all chip arithmetic is integral, and every state
transition checks conservation and action-order invariants.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

SEAT_COUNT = 6


class BettingStreet(StrEnum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


BETTING_STREETS: tuple[BettingStreet, ...] = tuple(BettingStreet)


class BettingActionKind(StrEnum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"


class TerminalReason(StrEnum):
    FOLD = "fold"
    SHOWDOWN = "showdown"


def _require_chip_count(value: object, *, name: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer chip count")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be {qualifier}")
    return value


@dataclass(frozen=True, slots=True)
class BettingAction:
    """A semantic player action; raises name the total street contribution."""

    kind: BettingActionKind
    raise_to: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, BettingActionKind):
            raise TypeError("betting action kind must be a BettingActionKind")
        if self.kind is BettingActionKind.RAISE:
            _require_chip_count(self.raise_to, name="raise-to amount", positive=True)
        elif self.raise_to is not None:
            raise ValueError("only a raise action may carry a raise-to amount")

    def __str__(self) -> str:
        if self.kind is BettingActionKind.RAISE:
            return f"raise-to-{self.raise_to}"
        return self.kind.value


FOLD = BettingAction(BettingActionKind.FOLD)
CHECK = BettingAction(BettingActionKind.CHECK)
CALL = BettingAction(BettingActionKind.CALL)


def raise_to(amount: int) -> BettingAction:
    """Construct a raise whose amount is total chips committed this street."""

    return BettingAction(BettingActionKind.RAISE, amount)


@dataclass(frozen=True, slots=True)
class RaiseBounds:
    """Exact legal raise-to interval and the strategically contestable ceiling."""

    minimum_raise_to: int
    maximum_raise_to: int
    minimum_full_raise_to: int
    maximum_contestable_raise_to: int
    all_in_only: bool


@dataclass(frozen=True, slots=True)
class LegalBettingDecision:
    """The complete legal action contract for the seat currently on the clock."""

    street: BettingStreet
    acting_seat: int
    stack: int
    street_contribution: int
    current_bet: int
    to_call: int
    call_amount: int
    action_kinds: tuple[BettingActionKind, ...]
    raise_bounds: RaiseBounds | None

    @property
    def can_fold(self) -> bool:
        return BettingActionKind.FOLD in self.action_kinds

    @property
    def can_check(self) -> bool:
        return BettingActionKind.CHECK in self.action_kinds

    @property
    def can_call(self) -> bool:
        return BettingActionKind.CALL in self.action_kinds

    @property
    def can_raise(self) -> bool:
        return self.raise_bounds is not None


@dataclass(frozen=True, slots=True)
class BettingActionRecord:
    street: BettingStreet
    seat: int
    action: BettingAction
    chips_committed: int
    full_raise: bool
    uncalled_return_seat: int | None
    uncalled_return_chips: int

    def __post_init__(self) -> None:
        if not isinstance(self.street, BettingStreet):
            raise TypeError("betting history street must be canonical")
        if (
            isinstance(self.seat, bool)
            or not isinstance(self.seat, int)
            or self.seat not in range(SEAT_COUNT)
        ):
            raise ValueError("betting history seat must identify one of six seats")
        if not isinstance(self.action, BettingAction):
            raise TypeError("betting history action must be semantic")
        _require_chip_count(self.chips_committed, name="history chips committed")
        if not isinstance(self.full_raise, bool):
            raise TypeError("betting history full-raise flag must be boolean")
        if self.full_raise and self.action.kind is not BettingActionKind.RAISE:
            raise ValueError("only a raise action may be recorded as a full raise")
        if self.action.kind in (BettingActionKind.FOLD, BettingActionKind.CHECK):
            if self.chips_committed != 0:
                raise ValueError("fold and check records cannot commit chips")
        elif self.chips_committed <= 0:
            raise ValueError("call and raise records must commit chips")
        if self.uncalled_return_seat is not None and (
            isinstance(self.uncalled_return_seat, bool)
            or not isinstance(self.uncalled_return_seat, int)
            or self.uncalled_return_seat not in range(SEAT_COUNT)
        ):
            raise ValueError("uncalled-return seat must identify one of six seats")
        _require_chip_count(
            self.uncalled_return_chips,
            name="history uncalled-return chips",
        )
        if (self.uncalled_return_seat is None) != (
            self.uncalled_return_chips == 0
        ):
            raise ValueError("uncalled-return seat and chips must be present together")


@dataclass(frozen=True, slots=True)
class ContributionLayer:
    """One interval induced by a distinct committed-contribution threshold."""

    lower_contribution_exclusive: int
    upper_contribution_inclusive: int
    amount: int
    contributors: tuple[int, ...]
    eligible_seats: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class SidePot:
    """One separately awarded pot, possibly merging folded-only thresholds."""

    amount: int
    eligible_seats: tuple[int, ...]
    contribution_layers: tuple[ContributionLayer, ...]

    @property
    def contributors(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    seat
                    for layer in self.contribution_layers
                    for seat in layer.contributors
                }
            )
        )

    @property
    def lower_contribution_exclusive(self) -> int:
        return self.contribution_layers[0].lower_contribution_exclusive

    @property
    def upper_contribution_inclusive(self) -> int:
        return self.contribution_layers[-1].upper_contribution_inclusive


HandStrength: TypeAlias = int | tuple[int, ...]


@dataclass(frozen=True, slots=True)
class HandSettlement:
    reason: TerminalReason
    side_pots: tuple[SidePot, ...]
    payouts: tuple[int, ...]
    net_returns: tuple[int, ...]
    final_stacks: tuple[int, ...]


def _clockwise_after(seat: int) -> tuple[int, ...]:
    return tuple((seat + offset) % SEAT_COUNT for offset in range(1, SEAT_COUNT + 1))


@dataclass(frozen=True, slots=True)
class NoLimitBettingState:
    """Immutable exact betting ledger for a six-seat no-limit hold'em hand."""

    button: int
    small_blind: int
    big_blind: int
    street: BettingStreet
    starting_stacks: tuple[int, ...]
    stacks: tuple[int, ...]
    total_contributions: tuple[int, ...]
    street_contributions: tuple[int, ...]
    folded: tuple[bool, ...]
    pending_seats: tuple[int, ...]
    last_full_raise_size: int
    acted_at_bet: tuple[int | None, ...]
    history: tuple[BettingActionRecord, ...] = ()
    round_complete: bool = False
    terminal_reason: TerminalReason | None = None

    def __post_init__(self) -> None:
        self.assert_invariants()

    @classmethod
    def new_hand(
        cls,
        *,
        button: int,
        starting_stacks: Sequence[int],
        small_blind: int,
        big_blind: int,
    ) -> NoLimitBettingState:
        """Post the blinds and return the first preflop decision state."""

        if isinstance(button, bool) or not isinstance(button, int) or button not in range(SEAT_COUNT):
            raise ValueError("button must identify one of six seats")
        small = _require_chip_count(small_blind, name="small blind", positive=True)
        big = _require_chip_count(big_blind, name="big blind", positive=True)
        if small >= big:
            raise ValueError("small blind must be smaller than big blind")
        stacks = tuple(
            _require_chip_count(value, name=f"starting stack for seat {seat}", positive=True)
            for seat, value in enumerate(starting_stacks)
        )
        if len(stacks) != SEAT_COUNT:
            raise ValueError("six-max betting requires exactly six starting stacks")
        if any(stack < big for stack in stacks):
            raise ValueError("each starting stack must cover the full big blind")

        small_blind_seat = (button + 1) % SEAT_COUNT
        big_blind_seat = (button + 2) % SEAT_COUNT
        remaining = list(stacks)
        total = [0] * SEAT_COUNT
        street_total = [0] * SEAT_COUNT
        for seat, amount in ((small_blind_seat, small), (big_blind_seat, big)):
            remaining[seat] -= amount
            total[seat] += amount
            street_total[seat] += amount

        pending = tuple(
            seat
            for seat in _clockwise_after(big_blind_seat)
            if remaining[seat] > 0
        )
        state = cls(
            button=button,
            small_blind=small,
            big_blind=big,
            street=BettingStreet.PREFLOP,
            starting_stacks=stacks,
            stacks=tuple(remaining),
            total_contributions=tuple(total),
            street_contributions=tuple(street_total),
            folded=(False,) * SEAT_COUNT,
            pending_seats=pending,
            last_full_raise_size=big,
            acted_at_bet=(None,) * SEAT_COUNT,
        )
        return state

    @classmethod
    def six_max_100bb(
        cls,
        *,
        button: int,
        small_blind: int = 1,
        big_blind: int = 2,
    ) -> NoLimitBettingState:
        """Construct the charter's equal-stack 100-big-blind cash-game hand."""

        big = _require_chip_count(big_blind, name="big blind", positive=True)
        return cls.new_hand(
            button=button,
            starting_stacks=(100 * big,) * SEAT_COUNT,
            small_blind=small_blind,
            big_blind=big,
        )

    @property
    def acting_seat(self) -> int | None:
        return self.pending_seats[0] if self.pending_seats else None

    @property
    def current_bet(self) -> int:
        return max(self.street_contributions, default=0)

    @property
    def pot(self) -> int:
        return sum(self.total_contributions)

    @property
    def live_seats(self) -> tuple[int, ...]:
        return tuple(seat for seat, folded in enumerate(self.folded) if not folded)

    @property
    def all_in_seats(self) -> tuple[int, ...]:
        return tuple(
            seat
            for seat in self.live_seats
            if self.stacks[seat] == 0
        )

    @property
    def is_terminal(self) -> bool:
        return self.terminal_reason is not None

    @property
    def showdown_ready(self) -> bool:
        return self.terminal_reason is TerminalReason.SHOWDOWN

    def legal_decision(self) -> LegalBettingDecision:
        """Return exact legal actions and raise bounds for the acting seat."""

        if self.is_terminal:
            raise ValueError("a terminal hand has no legal decision")
        if self.round_complete or self.acting_seat is None:
            raise ValueError("the betting round is complete")
        seat = self.acting_seat
        contribution = self.street_contributions[seat]
        stack = self.stacks[seat]
        to_call = self.current_bet - contribution
        if to_call < 0:
            raise AssertionError("acting contribution exceeds the current bet")

        kinds: list[BettingActionKind]
        if to_call:
            kinds = [BettingActionKind.FOLD, BettingActionKind.CALL]
        else:
            kinds = [BettingActionKind.CHECK]

        raise_bounds = self._raise_bounds(seat)
        if raise_bounds is not None:
            kinds.append(BettingActionKind.RAISE)
        return LegalBettingDecision(
            street=self.street,
            acting_seat=seat,
            stack=stack,
            street_contribution=contribution,
            current_bet=self.current_bet,
            to_call=to_call,
            call_amount=min(to_call, stack),
            action_kinds=tuple(kinds),
            raise_bounds=raise_bounds,
        )

    def _raise_bounds(self, seat: int) -> RaiseBounds | None:
        contribution = self.street_contributions[seat]
        maximum = contribution + self.stacks[seat]
        if maximum <= self.current_bet:
            return None

        opponent_caps = tuple(
            self.street_contributions[opponent] + self.stacks[opponent]
            for opponent in self.live_seats
            if opponent != seat and self.stacks[opponent] > 0
        )
        if not opponent_caps or max(opponent_caps) <= self.current_bet:
            return None

        last_action = self.acted_at_bet[seat]
        betting_reopened = (
            last_action is None
            or self.current_bet - last_action >= self.last_full_raise_size
        )
        if not betting_reopened:
            return None

        minimum_full = self.current_bet + self.last_full_raise_size
        all_in_only = maximum < minimum_full
        return RaiseBounds(
            minimum_raise_to=maximum if all_in_only else minimum_full,
            maximum_raise_to=maximum,
            minimum_full_raise_to=minimum_full,
            maximum_contestable_raise_to=min(maximum, max(opponent_caps)),
            all_in_only=all_in_only,
        )

    def apply_action(self, action: BettingAction) -> NoLimitBettingState:
        """Apply one in-turn action and return a separately validated state."""

        if not isinstance(action, BettingAction):
            raise TypeError("betting actions must use BettingAction")
        decision = self.legal_decision()
        seat = decision.acting_seat
        old_current_bet = self.current_bet
        stacks = list(self.stacks)
        total = list(self.total_contributions)
        street_total = list(self.street_contributions)
        folded = list(self.folded)
        acted_at = list(self.acted_at_bet)
        last_full_raise_size = self.last_full_raise_size
        chips_committed = 0
        full_raise = False

        if action.kind is BettingActionKind.FOLD:
            if not decision.can_fold:
                raise ValueError("fold is legal only while facing a wager")
            folded[seat] = True
        elif action.kind is BettingActionKind.CHECK:
            if not decision.can_check:
                raise ValueError("check is legal only with nothing to call")
            acted_at[seat] = old_current_bet
        elif action.kind is BettingActionKind.CALL:
            if not decision.can_call:
                raise ValueError("call is legal only while facing a wager")
            chips_committed = decision.call_amount
            stacks[seat] -= chips_committed
            total[seat] += chips_committed
            street_total[seat] += chips_committed
            acted_at[seat] = old_current_bet
        else:
            bounds = decision.raise_bounds
            if bounds is None or action.raise_to is None:
                raise ValueError("raising is not currently legal")
            amount = action.raise_to
            if amount < bounds.minimum_raise_to or amount > bounds.maximum_raise_to:
                raise ValueError(
                    "raise-to amount is outside the legal range "
                    f"[{bounds.minimum_raise_to}, {bounds.maximum_raise_to}]"
                )
            chips_committed = amount - street_total[seat]
            if chips_committed <= 0 or chips_committed > stacks[seat]:
                raise AssertionError("validated raise commits an invalid chip amount")
            stacks[seat] -= chips_committed
            total[seat] += chips_committed
            street_total[seat] = amount
            increment = amount - old_current_bet
            full_raise = increment >= self.last_full_raise_size
            if full_raise:
                last_full_raise_size = increment
            acted_at[seat] = amount

        remaining = self.pending_seats[1:]
        live = tuple(index for index in range(SEAT_COUNT) if not folded[index])
        terminal_reason: TerminalReason | None = None
        if len(live) == 1:
            pending: tuple[int, ...] = ()
            terminal_reason = TerminalReason.FOLD
        elif action.kind is BettingActionKind.RAISE:
            new_current_bet = max(street_total)
            remaining_set = set(remaining)
            pending = tuple(
                opponent
                for opponent in _clockwise_after(seat)
                if opponent != seat
                and not folded[opponent]
                and stacks[opponent] > 0
                and (
                    full_raise
                    or opponent in remaining_set
                    or street_total[opponent] < new_current_bet
                )
            )
        else:
            pending = tuple(
                opponent
                for opponent in remaining
                if not folded[opponent] and stacks[opponent] > 0
            )

        current_after = max(street_total)
        actionable = tuple(
            player
            for player in live
            if stacks[player] > 0
        )
        if terminal_reason is None and len(actionable) <= 1:
            if not actionable or street_total[actionable[0]] >= current_after:
                pending = ()
            else:
                pending = (actionable[0],)

        round_complete = not pending
        refund_seat: int | None = None
        refund_chips = 0
        if round_complete:
            refund_seat, refund_chips = self._refund_uncalled(
                stacks=stacks,
                total_contributions=total,
                street_contributions=street_total,
            )
            if terminal_reason is None and self.street is BettingStreet.RIVER:
                terminal_reason = TerminalReason.SHOWDOWN

        record = BettingActionRecord(
            street=self.street,
            seat=seat,
            action=action,
            chips_committed=chips_committed,
            full_raise=full_raise,
            uncalled_return_seat=refund_seat,
            uncalled_return_chips=refund_chips,
        )
        result = NoLimitBettingState(
            button=self.button,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            street=self.street,
            starting_stacks=self.starting_stacks,
            stacks=tuple(stacks),
            total_contributions=tuple(total),
            street_contributions=tuple(street_total),
            folded=tuple(folded),
            pending_seats=pending,
            last_full_raise_size=last_full_raise_size,
            acted_at_bet=tuple(acted_at),
            history=(*self.history, record),
            round_complete=round_complete,
            terminal_reason=terminal_reason,
        )
        return result

    @staticmethod
    def _refund_uncalled(
        *,
        stacks: list[int],
        total_contributions: list[int],
        street_contributions: list[int],
    ) -> tuple[int | None, int]:
        maximum = max(street_contributions)
        leaders = [
            seat
            for seat, contribution in enumerate(street_contributions)
            if contribution == maximum
        ]
        if len(leaders) != 1:
            return None, 0
        seat = leaders[0]
        second = max(
            contribution
            for other, contribution in enumerate(street_contributions)
            if other != seat
        )
        refund = maximum - second
        if refund <= 0:
            return None, 0
        street_contributions[seat] -= refund
        total_contributions[seat] -= refund
        stacks[seat] += refund
        return seat, refund

    def advance_street(self) -> NoLimitBettingState:
        """Advance exactly one street, or move a completed river to showdown."""

        if self.is_terminal:
            raise ValueError("a terminal hand cannot advance streets")
        if not self.round_complete:
            raise ValueError("cannot advance before the current betting round completes")
        if self.street is BettingStreet.RIVER:
            result = NoLimitBettingState(
                button=self.button,
                small_blind=self.small_blind,
                big_blind=self.big_blind,
                street=self.street,
                starting_stacks=self.starting_stacks,
                stacks=self.stacks,
                total_contributions=self.total_contributions,
                street_contributions=self.street_contributions,
                folded=self.folded,
                pending_seats=(),
                last_full_raise_size=self.last_full_raise_size,
                acted_at_bet=self.acted_at_bet,
                history=self.history,
                round_complete=True,
                terminal_reason=TerminalReason.SHOWDOWN,
            )
            return result


        next_street = BETTING_STREETS[BETTING_STREETS.index(self.street) + 1]
        street_total = (0,) * SEAT_COUNT
        actionable = tuple(
            seat
            for seat in _clockwise_after(self.button)
            if not self.folded[seat] and self.stacks[seat] > 0
        )
        pending = actionable if len(actionable) >= 2 else ()
        result = NoLimitBettingState(
            button=self.button,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            street=next_street,
            starting_stacks=self.starting_stacks,
            stacks=self.stacks,
            total_contributions=self.total_contributions,
            street_contributions=street_total,
            folded=self.folded,
            pending_seats=pending,
            last_full_raise_size=self.big_blind,
            acted_at_bet=(None,) * SEAT_COUNT,
            history=self.history,
            round_complete=not pending,
        )
        return result

    def contribution_layers(self) -> tuple[ContributionLayer, ...]:
        """Partition committed chips at every distinct contribution threshold."""

        levels = sorted(set(self.total_contributions) - {0})
        lower = 0
        layers: list[ContributionLayer] = []
        for upper in levels:
            contributors = tuple(
                seat
                for seat, contribution in enumerate(self.total_contributions)
                if contribution >= upper
            )
            amount = (upper - lower) * len(contributors)
            eligible = tuple(seat for seat in contributors if not self.folded[seat])
            if amount <= 0 or not eligible:
                raise AssertionError("reachable contribution layer has no live claimant")
            layers.append(
                ContributionLayer(
                    lower_contribution_exclusive=lower,
                    upper_contribution_inclusive=upper,
                    amount=amount,
                    contributors=contributors,
                    eligible_seats=eligible,
                )
            )
            lower = upper
        if sum(layer.amount for layer in layers) != self.pot:
            raise AssertionError("contribution layers do not conserve committed chips")
        return tuple(layers)

    def side_pots(self) -> tuple[SidePot, ...]:
        """Return separately awarded pots with folded-only boundaries merged."""

        pots: list[SidePot] = []
        for layer in self.contribution_layers():
            if pots and pots[-1].eligible_seats == layer.eligible_seats:
                prior = pots[-1]
                pots[-1] = SidePot(
                    amount=prior.amount + layer.amount,
                    eligible_seats=prior.eligible_seats,
                    contribution_layers=(*prior.contribution_layers, layer),
                )
            else:
                pots.append(
                    SidePot(
                        amount=layer.amount,
                        eligible_seats=layer.eligible_seats,
                        contribution_layers=(layer,),
                    )
                )
        if sum(pot.amount for pot in pots) != self.pot:
            raise AssertionError("side pots do not conserve committed chips")
        return tuple(pots)

    def settle(self, strengths: Sequence[HandStrength | None] | None = None) -> HandSettlement:
        """Award every pot at a fold terminal or showdown and return chip EVs."""

        if self.terminal_reason is None:
            raise ValueError("settlement requires a terminal hand")
        if self.terminal_reason is TerminalReason.SHOWDOWN:
            if strengths is None or len(strengths) != SEAT_COUNT:
                raise ValueError("showdown requires one strength entry for every seat")
            for seat in self.live_seats:
                if strengths[seat] is None:
                    raise ValueError("every live showdown seat requires a strength")
        elif strengths is not None:
            raise ValueError("fold settlement does not accept showdown strengths")

        payouts = [0] * SEAT_COUNT
        pots = self.side_pots()
        odd_chip_order = _clockwise_after(self.button)
        for pot in pots:
            if self.terminal_reason is TerminalReason.FOLD:
                winners = pot.eligible_seats
            else:
                assert strengths is not None
                best = max(strengths[seat] for seat in pot.eligible_seats)
                winners = tuple(
                    seat
                    for seat in pot.eligible_seats
                    if strengths[seat] == best
                )
            if not winners:
                raise AssertionError("a side pot has no winner")
            share, odd = divmod(pot.amount, len(winners))
            for winner in winners:
                payouts[winner] += share
            ordered_winners = tuple(seat for seat in odd_chip_order if seat in winners)
            for winner in ordered_winners[:odd]:
                payouts[winner] += 1

        if sum(payouts) != self.pot:
            raise AssertionError("settlement does not conserve the pot")
        net_returns = tuple(
            payouts[seat] - self.total_contributions[seat]
            for seat in range(SEAT_COUNT)
        )
        final_stacks = tuple(
            self.stacks[seat] + payouts[seat]
            for seat in range(SEAT_COUNT)
        )
        if sum(net_returns) != 0 or sum(final_stacks) != sum(self.starting_stacks):
            raise AssertionError("settlement does not conserve table chips")
        return HandSettlement(
            reason=self.terminal_reason,
            side_pots=pots,
            payouts=tuple(payouts),
            net_returns=net_returns,
            final_stacks=final_stacks,
        )

    def assert_invariants(self) -> None:
        """Fail closed on every structural, action-order, or chip-ledger defect."""

        if (
            isinstance(self.button, bool)
            or not isinstance(self.button, int)
            or self.button not in range(SEAT_COUNT)
        ):
            raise AssertionError("button is outside the six-seat table")
        if not isinstance(self.street, BettingStreet):
            raise TypeError("state street is not canonical")
        if not isinstance(self.round_complete, bool):
            raise TypeError("round-complete flag must be boolean")
        if self.terminal_reason is not None and not isinstance(
            self.terminal_reason,
            TerminalReason,
        ):
            raise AssertionError("terminal reason is not canonical")
        for name, values in (
            ("starting stacks", self.starting_stacks),
            ("stacks", self.stacks),
            ("total contributions", self.total_contributions),
            ("street contributions", self.street_contributions),
            ("fold flags", self.folded),
            ("acted-at-bet", self.acted_at_bet),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be an immutable tuple")
            if len(values) != SEAT_COUNT:
                raise AssertionError(f"{name} must contain exactly six seats")
        if not isinstance(self.pending_seats, tuple):
            raise TypeError("pending action order must be an immutable tuple")
        if not isinstance(self.history, tuple):
            raise TypeError("betting history must be an immutable tuple")
        if (
            isinstance(self.small_blind, bool)
            or not isinstance(self.small_blind, int)
            or isinstance(self.big_blind, bool)
            or not isinstance(self.big_blind, int)
            or self.small_blind <= 0
            or self.big_blind <= self.small_blind
        ):
            raise AssertionError("blind structure is invalid")
        if (
            isinstance(self.last_full_raise_size, bool)
            or not isinstance(self.last_full_raise_size, int)
            or self.last_full_raise_size < self.big_blind
        ):
            raise AssertionError("minimum full raise fell below the big blind")

        for seat in range(SEAT_COUNT):
            for name, value in (
                ("starting stack", self.starting_stacks[seat]),
                ("stack", self.stacks[seat]),
                ("total contribution", self.total_contributions[seat]),
                ("street contribution", self.street_contributions[seat]),
            ):
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise AssertionError(f"seat {seat} {name} is not a nonnegative integer")
            if self.starting_stacks[seat] <= 0:
                raise AssertionError("starting stacks must be positive")
            if not isinstance(self.folded[seat], bool):
                raise TypeError("fold flags must be boolean")
            if self.street_contributions[seat] > self.total_contributions[seat]:
                raise AssertionError("street contribution exceeds hand contribution")
            if self.stacks[seat] + self.total_contributions[seat] != self.starting_stacks[seat]:
                raise AssertionError("per-seat chip conservation failed")
            acted = self.acted_at_bet[seat]
            if acted is not None and (
                isinstance(acted, bool) or not isinstance(acted, int) or acted < 0
            ):
                raise AssertionError("acted-at-bet entries must be chip counts or None")
            if acted is not None and not self.round_complete and acted > self.current_bet:
                raise AssertionError("active round remembers action above the current bet")

        if any(isinstance(seat, bool) or not isinstance(seat, int) for seat in self.pending_seats):
            raise AssertionError("pending action order contains a non-integer seat")
        if len(set(self.pending_seats)) != len(self.pending_seats):
            raise AssertionError("pending action order contains a duplicate seat")
        if any(
            seat not in range(SEAT_COUNT)
            or self.folded[seat]
            or self.stacks[seat] == 0
            for seat in self.pending_seats
        ):
            raise AssertionError("pending action order contains an ineligible seat")
        if self.round_complete != (not self.pending_seats):
            raise AssertionError("round-complete flag disagrees with pending action")
        if self.terminal_reason is not None and not self.round_complete:
            raise AssertionError("terminal hand still has pending action")
        if self.terminal_reason is TerminalReason.FOLD and len(self.live_seats) != 1:
            raise AssertionError("fold terminal must have exactly one live seat")
        if self.terminal_reason is TerminalReason.SHOWDOWN and len(self.live_seats) < 2:
            raise AssertionError("showdown must have at least two live seats")

        actionable = tuple(
            seat for seat in self.live_seats if self.stacks[seat] > 0
        )
        if self.pending_seats and len(actionable) == 1:
            lone = actionable[0]
            if self.pending_seats != (lone,) or self.street_contributions[lone] >= self.current_bet:
                raise AssertionError("a lone actionable seat may act only to answer a wager")
        if sum(self.stacks) + self.pot != sum(self.starting_stacks):
            raise AssertionError("table chip conservation failed")
        for record in self.history:
            if not isinstance(record, BettingActionRecord):
                raise TypeError("betting history contains an invalid record")
        # This also proves that every committed chip belongs to a layer with a
        # live claimant.  It catches forged states that conserve numerically but
        # cannot arise from legal poker action.
        self.side_pots()


__all__ = [
    "BETTING_STREETS",
    "CALL",
    "CHECK",
    "FOLD",
    "SEAT_COUNT",
    "BettingAction",
    "BettingActionKind",
    "BettingActionRecord",
    "BettingStreet",
    "ContributionLayer",
    "HandSettlement",
    "HandStrength",
    "LegalBettingDecision",
    "NoLimitBettingState",
    "RaiseBounds",
    "SidePot",
    "TerminalReason",
    "raise_to",
]
