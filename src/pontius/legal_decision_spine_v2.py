"""Exact one-seat controller for ADR-0307 action clocks and preparation."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from .action_clock import (
    ACTION_EMISSION_RESERVE_SECONDS,
    ACTION_RESPONSE_WALL_SECONDS,
    ActionClockLedger,
    ActionClockSnapshot,
    CompletedStreetActionTiming,
)
from .no_limit_betting import (
    SEAT_COUNT,
    BettingAction,
    LegalBettingDecision,
    NoLimitBettingState,
)
from .preparation_bank import PreparationBank, PreparationUse


def public_betting_state_sha256(state: NoLimitBettingState) -> str:
    """Bind the complete exact public betting state without cards or strategy."""

    if not isinstance(state, NoLimitBettingState):
        raise TypeError("public betting digest requires an exact betting state")
    payload = {
        "acted_at_bet": state.acted_at_bet,
        "big_blind": state.big_blind,
        "button": state.button,
        "folded": state.folded,
        "history": tuple(
            {
                "action": {
                    "kind": record.action.kind.value,
                    "raise_to": record.action.raise_to,
                },
                "chips_committed": record.chips_committed,
                "full_raise": record.full_raise,
                "seat": record.seat,
                "street": record.street.value,
                "uncalled_return_chips": record.uncalled_return_chips,
                "uncalled_return_seat": record.uncalled_return_seat,
            }
            for record in state.history
        ),
        "last_full_raise_size": state.last_full_raise_size,
        "pending_seats": state.pending_seats,
        "round_complete": state.round_complete,
        "small_blind": state.small_blind,
        "stacks": state.stacks,
        "starting_stacks": state.starting_stacks,
        "street": state.street.value,
        "street_contributions": state.street_contributions,
        "terminal_reason": (None if state.terminal_reason is None else state.terminal_reason.value),
        "total_contributions": state.total_contributions,
    }
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


class ActionSelectionReasonV2(StrEnum):
    CANDIDATE = "candidate"
    NO_CANDIDATE = "no_candidate"
    ILLEGAL_CANDIDATE = "illegal_candidate"
    WORK_BUDGET_EXHAUSTED = "work_budget_exhausted"
    ACTION_DEADLINE_CROSSED = "action_deadline_crossed"


@dataclass(frozen=True, slots=True)
class ControlledDecisionTicketV2:
    decision: LegalBettingDecision
    deadline: ActionClockSnapshot


@dataclass(frozen=True, slots=True)
class EmittedBettingActionV2:
    seat: int
    candidate: BettingAction | None
    fallback: BettingAction
    selected: BettingAction
    reason: ActionSelectionReasonV2
    used_fallback: bool
    deadline: ActionClockSnapshot


class LegalDecisionSpineV2:
    """One-seat exact controller whose hard deadline resets per controlled turn."""

    def __init__(
        self,
        state: NoLimitBettingState,
        *,
        controlled_seat: int,
        action_clock: ActionClockLedger | None = None,
        preparation_bank: PreparationBank | None = None,
    ) -> None:
        if not isinstance(state, NoLimitBettingState):
            raise TypeError("legal decision spine v2 requires a no-limit betting state")
        if (
            isinstance(controlled_seat, bool)
            or not isinstance(controlled_seat, int)
            or controlled_seat not in range(SEAT_COUNT)
        ):
            raise ValueError("controlled seat must identify one of six seats")
        timing = ActionClockLedger(state.street.value) if action_clock is None else action_clock
        if not isinstance(timing, ActionClockLedger):
            raise TypeError("legal decision spine v2 requires an action clock ledger")
        if timing.street != state.street.value:
            raise ValueError("betting state and action clock must name the same street")
        if timing.charging or timing.transition_active:
            raise ValueError("legal decision spine v2 received unfinished timing work")
        state.assert_invariants()

        if preparation_bank is None:
            bank = PreparationBank(action_clock=timing)
        else:
            bank = preparation_bank
            if not isinstance(bank, PreparationBank):
                raise TypeError("legal decision spine v2 requires a preparation bank")
            if bank.action_clock is not timing:
                raise ValueError("preparation bank belongs to another action clock")

        controlled_is_actor = (
            not state.is_terminal
            and not state.round_complete
            and state.acting_seat == controlled_seat
        )
        state_digest = public_betting_state_sha256(state)
        if controlled_is_actor and not timing.action_active:
            raise ValueError("a controlled actor requires a boundary-started action clock")
        elif controlled_is_actor != timing.action_active:
            raise ValueError("betting actor and active action clock disagree")
        elif (
            controlled_is_actor
            and timing.current_action is not None
            and timing.current_action.public_state_sha256 != state_digest
        ):
            raise ValueError("betting state and active action clock disagree")
        if state.is_terminal:
            if not timing.finalized:
                timing.finalize()
        elif timing.finalized:
            raise ValueError("a live betting state cannot use a finalized action clock")

        self._state = state
        self._controlled_seat = controlled_seat
        self._clock = timing
        self._bank = bank
        self._decision_open = False

    @classmethod
    def six_max_100bb(
        cls,
        *,
        button: int,
        controlled_seat: int,
        small_blind: int = 1,
        big_blind: int = 2,
        clock_ns: Callable[[], int] | None = None,
    ) -> LegalDecisionSpineV2:
        return cls.new_hand(
            button=button,
            controlled_seat=controlled_seat,
            starting_stacks=(100 * big_blind,) * SEAT_COUNT,
            small_blind=small_blind,
            big_blind=big_blind,
            clock_ns=clock_ns,
        )

    @classmethod
    def new_hand(
        cls,
        *,
        button: int,
        controlled_seat: int,
        starting_stacks: Sequence[int],
        small_blind: int,
        big_blind: int,
        clock_ns: Callable[[], int] | None = None,
    ) -> LegalDecisionSpineV2:
        timing = ActionClockLedger("preflop", clock_ns=clock_ns)
        boundary = timing.start_transition_boundary()
        try:
            state = NoLimitBettingState.new_hand(
                button=button,
                starting_stacks=starting_stacks,
                small_blind=small_blind,
                big_blind=big_blind,
            )
        except BaseException:
            timing.abort_transition_boundary(boundary)
            raise
        starts_action = state.acting_seat == controlled_seat
        timing.finish_transition_boundary(
            boundary,
            starts_controlled_action=starts_action,
            controlled_action_public_state_sha256=(
                public_betting_state_sha256(state) if starts_action else None
            ),
        )
        bank = PreparationBank(action_clock=timing)
        return cls(
            state,
            controlled_seat=controlled_seat,
            action_clock=timing,
            preparation_bank=bank,
        )

    @property
    def state(self) -> NoLimitBettingState:
        return self._state

    @property
    def controlled_seat(self) -> int:
        return self._controlled_seat

    @property
    def decision_open(self) -> bool:
        return self._decision_open

    @property
    def action_clock(self) -> ActionClockLedger:
        return self._clock

    @property
    def preparation_bank(self) -> PreparationBank:
        return self._bank

    @property
    def deadline(self) -> ActionClockSnapshot | None:
        return self._clock.snapshot() if self._clock.action_active else None

    @property
    def completed_action_deadlines(self) -> tuple[ActionClockSnapshot, ...]:
        return self._clock.completed_actions

    @property
    def completed_street_timings(self) -> tuple[CompletedStreetActionTiming, ...]:
        return self._clock.completed_streets

    @property
    def public_state_sha256(self) -> str:
        return public_betting_state_sha256(self._state)

    def open_controlled_decision(self) -> ControlledDecisionTicketV2:
        if self._decision_open:
            raise RuntimeError("a controlled decision is already open")
        if not self._clock.action_active:
            raise RuntimeError("the controlled action clock is not active")
        if self._state.acting_seat != self._controlled_seat:
            raise ValueError("the controlled seat is not currently on the clock")
        self._clock.start_response_work()
        try:
            decision = self._state.legal_decision()
        finally:
            snapshot = self._clock.stop_response_work()
        self._decision_open = True
        return ControlledDecisionTicketV2(decision=decision, deadline=snapshot)

    @contextmanager
    def charge_compute(self) -> Iterator[LegalDecisionSpineV2]:
        """Measure agent work while the continuous response wall keeps running."""

        self._clock.start_response_work()
        try:
            yield self
        finally:
            self._clock.stop_response_work()

    @contextmanager
    def charge_unbanked_preparation(self) -> Iterator[LegalDecisionSpineV2]:
        """Measure pre-action work that creates no creditable artifact."""

        self._clock.start_preparation_work()
        try:
            yield self
        finally:
            self._clock.stop_preparation_work()

    def claim_preparation(
        self,
        *,
        artifact_bytes: bytes,
        semantic_context_sha256: str,
        source_sha256: str,
    ) -> PreparationUse:
        return self._bank.claim(
            artifact_bytes=artifact_bytes,
            semantic_context_sha256=semantic_context_sha256,
            source_sha256=source_sha256,
        )

    def admitted_work_seconds(self, requested_seconds: float) -> float:
        return self._clock.admitted_work_seconds(requested_seconds)

    def observe_opponent_action(self, action: BettingAction) -> NoLimitBettingState:
        """Classify event processing at the exact boundary that may start our turn."""

        if self._decision_open:
            raise RuntimeError("finish the open controlled decision first")
        if self._clock.action_active:
            raise RuntimeError("controlled-seat actions use the emission path")
        if self._state.acting_seat == self._controlled_seat:
            raise ValueError("controlled-seat actions use the emission path")
        boundary = self._clock.start_transition_boundary()
        try:
            observed = self._state.apply_action(action)
        except BaseException:
            self._clock.abort_transition_boundary(boundary)
            raise
        starts_action = (
            not observed.is_terminal
            and not observed.round_complete
            and observed.acting_seat == self._controlled_seat
        )
        self._clock.finish_transition_boundary(
            boundary,
            starts_controlled_action=starts_action,
            controlled_action_public_state_sha256=(
                public_betting_state_sha256(observed) if starts_action else None
            ),
        )
        self._state = observed
        if observed.is_terminal:
            self._clock.finalize()
        return self._state

    def emit_controlled_action(
        self,
        *,
        candidate: BettingAction | None,
        fallback: BettingAction,
    ) -> EmittedBettingActionV2:
        """Apply a timely legal candidate or the exact legal fallback."""

        if not self._decision_open:
            raise RuntimeError("open the controlled decision before emission")
        if not self._clock.action_active:
            raise RuntimeError("controlled action clock ended before emission")
        if self._clock.charging:
            raise RuntimeError("stop resolver work before emission")

        before_emission = self._clock.snapshot()
        work_cutoff = ACTION_RESPONSE_WALL_SECONDS - ACTION_EMISSION_RESERVE_SECONDS
        self._clock.start_response_work()
        try:
            fallback_state = self._state.apply_action(fallback)
            candidate_state: NoLimitBettingState | None = None
            if candidate is None:
                reason = ActionSelectionReasonV2.NO_CANDIDATE
            elif before_emission.action_wall_elapsed_seconds > work_cutoff:
                reason = ActionSelectionReasonV2.WORK_BUDGET_EXHAUSTED
            else:
                try:
                    candidate_state = self._state.apply_action(candidate)
                except (TypeError, ValueError):
                    reason = ActionSelectionReasonV2.ILLEGAL_CANDIDATE
                else:
                    reason = ActionSelectionReasonV2.CANDIDATE
            used_fallback = candidate_state is None
            selected = fallback if used_fallback else candidate
            selected_state = fallback_state if used_fallback else candidate_state
        finally:
            self._clock.stop_response_work()

        final_deadline = self._clock.finish_action()
        if final_deadline.deadline_crossed:
            selected = fallback
            selected_state = fallback_state
            reason = ActionSelectionReasonV2.ACTION_DEADLINE_CROSSED
            used_fallback = True
        assert isinstance(selected, BettingAction)
        assert isinstance(selected_state, NoLimitBettingState)

        self._state = selected_state
        self._decision_open = False
        if selected_state.is_terminal:
            self._clock.finalize()
        return EmittedBettingActionV2(
            seat=self._controlled_seat,
            candidate=candidate,
            fallback=fallback,
            selected=selected,
            reason=reason,
            used_fallback=used_fallback,
            deadline=final_deadline,
        )

    def advance_street(self) -> NoLimitBettingState:
        """Classify public-transition work before the next exact actor is known."""

        if self._decision_open:
            raise RuntimeError("cannot transition with an open controlled decision")
        if self._clock.action_active:
            raise RuntimeError("finish the controlled response before transitioning")
        if self._state.is_terminal:
            raise ValueError("a terminal hand cannot advance streets")
        prior_street = self._state.street
        boundary = self._clock.start_transition_boundary()
        try:
            advanced = self._state.advance_street()
        except BaseException:
            self._clock.abort_transition_boundary(boundary)
            raise
        starts_action = (
            not advanced.is_terminal
            and not advanced.round_complete
            and advanced.acting_seat == self._controlled_seat
        )
        next_street = advanced.street.value if advanced.street is not prior_street else None
        self._clock.finish_transition_boundary(
            boundary,
            starts_controlled_action=starts_action,
            controlled_action_public_state_sha256=(
                public_betting_state_sha256(advanced) if starts_action else None
            ),
            next_street=next_street,
        )
        self._state = advanced
        if advanced.is_terminal:
            self._clock.finalize()
        return self._state


__all__ = [
    "ActionSelectionReasonV2",
    "ControlledDecisionTicketV2",
    "EmittedBettingActionV2",
    "LegalDecisionSpineV2",
    "public_betting_state_sha256",
]
