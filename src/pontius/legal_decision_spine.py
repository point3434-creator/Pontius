"""One-seat control boundary joining exact betting to the street work ledger."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum

from .no_limit_betting import (
    SEAT_COUNT,
    BettingAction,
    LegalBettingDecision,
    NoLimitBettingState,
)
from .street_deadline import (
    ACTION_EMISSION_RESERVE_SECONDS,
    STREET_WALL_SECONDS,
    StreetDeadlineLedger,
    StreetDeadlineSnapshot,
)


class ActionSelectionReason(StrEnum):
    CANDIDATE = "candidate"
    NO_CANDIDATE = "no_candidate"
    ILLEGAL_CANDIDATE = "illegal_candidate"
    WORK_BUDGET_EXHAUSTED = "work_budget_exhausted"
    STREET_DEADLINE_CROSSED = "street_deadline_crossed"


@dataclass(frozen=True, slots=True)
class ControlledDecisionTicket:
    decision: LegalBettingDecision
    deadline: StreetDeadlineSnapshot


@dataclass(frozen=True, slots=True)
class EmittedBettingAction:
    seat: int
    candidate: BettingAction | None
    fallback: BettingAction
    selected: BettingAction
    reason: ActionSelectionReason
    used_fallback: bool
    deadline: StreetDeadlineSnapshot


class LegalDecisionSpine:
    """Mutable one-seat hand controller over the immutable betting kernel.

    Opponent think/transport idle never consumes the street budget; parsing and
    applying an observed action does.  Callers must mark every foreground or
    background agent-compute interval with
    :meth:`charge_compute`; the same ledger persists until an exact street
    transition.  A caller-supplied immutable-blueprint action is mandatory for
    fail-closed emission.
    """

    def __init__(
        self,
        state: NoLimitBettingState,
        *,
        controlled_seat: int,
        ledger: StreetDeadlineLedger | None = None,
    ) -> None:
        if not isinstance(state, NoLimitBettingState):
            raise TypeError("legal decision spine requires a no-limit betting state")
        if (
            isinstance(controlled_seat, bool)
            or not isinstance(controlled_seat, int)
            or controlled_seat not in range(SEAT_COUNT)
        ):
            raise ValueError("controlled seat must identify one of six seats")
        deadline = (
            StreetDeadlineLedger(state.street.value)
            if ledger is None
            else ledger
        )
        if not isinstance(deadline, StreetDeadlineLedger):
            raise TypeError("legal decision spine requires a StreetDeadlineLedger")
        if deadline.street != state.street.value:
            raise ValueError("betting state and deadline ledger must name the same street")
        state.assert_invariants()
        if deadline.finalized and not state.is_terminal:
            raise ValueError("a live betting state cannot use a finalized deadline ledger")
        if state.is_terminal and not deadline.finalized:
            deadline.finalize()
        self._state = state
        self._controlled_seat = controlled_seat
        self._ledger = deadline
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
    ) -> LegalDecisionSpine:
        ledger = StreetDeadlineLedger("preflop", clock_ns=clock_ns)
        ledger.start_charge()
        try:
            state = NoLimitBettingState.six_max_100bb(
                button=button,
                small_blind=small_blind,
                big_blind=big_blind,
            )
            return cls(
                state,
                controlled_seat=controlled_seat,
                ledger=ledger,
            )
        finally:
            ledger.stop_charge()

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
    ) -> LegalDecisionSpine:
        ledger = StreetDeadlineLedger("preflop", clock_ns=clock_ns)
        ledger.start_charge()
        try:
            state = NoLimitBettingState.new_hand(
                button=button,
                starting_stacks=starting_stacks,
                small_blind=small_blind,
                big_blind=big_blind,
            )
            return cls(
                state,
                controlled_seat=controlled_seat,
                ledger=ledger,
            )
        finally:
            ledger.stop_charge()

    @property
    def state(self) -> NoLimitBettingState:
        return self._state

    @property
    def controlled_seat(self) -> int:
        return self._controlled_seat

    @property
    def deadline(self) -> StreetDeadlineSnapshot:
        return self._ledger.snapshot()

    @property
    def decision_open(self) -> bool:
        return self._decision_open

    @property
    def completed_street_deadlines(self) -> tuple[StreetDeadlineSnapshot, ...]:
        return self._ledger.completed_streets

    def open_controlled_decision(self) -> ControlledDecisionTicket:
        """Open exactly one on-clock decision for the controlled seat."""

        if self._decision_open:
            raise RuntimeError("a controlled decision is already open")
        if self._ledger.charging:
            raise RuntimeError("stop background compute before opening a decision")
        if self._state.acting_seat != self._controlled_seat:
            raise ValueError("the controlled seat is not currently on the clock")
        self._ledger.begin_action()
        self._ledger.start_charge()
        try:
            decision = self._state.legal_decision()
        finally:
            snapshot = self._ledger.stop_charge()
        self._decision_open = True
        return ControlledDecisionTicket(decision=decision, deadline=snapshot)

    @contextmanager
    def charge_compute(self) -> Iterator[LegalDecisionSpine]:
        """Charge agent computation, including useful work during opponent time."""

        self._ledger.start_charge()
        try:
            yield self
        finally:
            self._ledger.stop_charge()

    def admitted_work_seconds(self, requested_seconds: float) -> float:
        return self._ledger.admitted_work_seconds(requested_seconds)

    def observe_opponent_action(self, action: BettingAction) -> NoLimitBettingState:
        """Charge event processing but exclude preceding opponent/transport idle."""

        if self._decision_open:
            raise RuntimeError("finish the open controlled decision first")
        if self._ledger.charging:
            raise RuntimeError("stop charged background compute before applying an action")
        if self._state.acting_seat == self._controlled_seat:
            raise ValueError("controlled-seat actions use the fail-closed emission path")
        self._ledger.start_charge()
        try:
            observed = self._state.apply_action(action)
        finally:
            self._ledger.stop_charge()
        if observed.is_terminal:
            self._ledger.finalize()
        self._state = observed
        return self._state

    def emit_controlled_action(
        self,
        *,
        candidate: BettingAction | None,
        fallback: BettingAction,
    ) -> EmittedBettingAction:
        """Select a timely legal candidate or atomically apply the legal fallback."""

        if not self._decision_open:
            raise RuntimeError("open the controlled decision before emission")
        if self._ledger.charging:
            raise RuntimeError("stop charged resolver work before emission")

        before_emission = self._ledger.snapshot()
        work_cutoff = STREET_WALL_SECONDS - ACTION_EMISSION_RESERVE_SECONDS

        # The fallback is the only action whose availability is unconditional.
        # Charge its validation, candidate selection, and state construction to
        # the reserved emission interval rather than hiding Python overhead.
        self._ledger.start_charge()
        try:
            fallback_state = self._state.apply_action(fallback)
            candidate_state: NoLimitBettingState | None = None
            if candidate is None:
                reason = ActionSelectionReason.NO_CANDIDATE
            elif before_emission.charged_compute_seconds > work_cutoff:
                reason = ActionSelectionReason.WORK_BUDGET_EXHAUSTED
            else:
                try:
                    candidate_state = self._state.apply_action(candidate)
                except (TypeError, ValueError):
                    reason = ActionSelectionReason.ILLEGAL_CANDIDATE
                else:
                    reason = ActionSelectionReason.CANDIDATE
            used_fallback = candidate_state is None
            selected = fallback if used_fallback else candidate
            selected_state = fallback_state if used_fallback else candidate_state
        finally:
            after_emission = self._ledger.stop_charge()
        if after_emission.deadline_crossed:
            selected = fallback
            selected_state = fallback_state
            reason = ActionSelectionReason.STREET_DEADLINE_CROSSED
            used_fallback = True

        if selected_state.is_terminal:
            self._ledger.finalize()
        self._state = selected_state
        self._decision_open = False
        return EmittedBettingAction(
            seat=self._controlled_seat,
            candidate=candidate,
            fallback=fallback,
            selected=selected,
            reason=reason,
            used_fallback=used_fallback,
            deadline=after_emission,
        )

    def advance_street(self) -> NoLimitBettingState:
        """Advance the hand and reset charged time only on the exact next street."""

        if self._decision_open:
            raise RuntimeError("cannot transition with an open controlled decision")
        if self._ledger.charging:
            raise RuntimeError("stop charged compute before transitioning streets")
        if self._state.is_terminal:
            raise ValueError("a terminal hand cannot advance streets")
        prior_street = self._state.street
        self._ledger.start_charge()
        try:
            advanced = self._state.advance_street()
        finally:
            self._ledger.stop_charge()
        if advanced.street is not prior_street:
            self._ledger.transition_to(advanced.street.value)
        elif advanced.is_terminal:
            self._ledger.finalize()
        self._state = advanced
        return self._state


__all__ = [
    "ActionSelectionReason",
    "ControlledDecisionTicket",
    "EmittedBettingAction",
    "LegalDecisionSpine",
]
