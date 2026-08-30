"""Visible-state transitions, blueprint selection, and emission (ADR-0485).

The runtime consumes one public event at a time plus the controlled seat's
own cards. It never receives the dealer's complete deal, the future
schedule, an event iterator, or the replay host. The outer
``ActionClockLedger`` is the sole response authority; the V2 spine's ledger
remains controller diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..action_clock import ActionClockLedger
from ..holdem_cards import OneSeatCardState
from ..immutable_blueprint import (
    BlueprintDecisionKey,
    BlueprintSelection,
    require_legal_blueprint_action,
)
from ..legal_decision_spine_v2 import LegalDecisionSpineV2, public_betting_state_sha256
from ..no_limit_betting import (
    BettingStreet,
    LegalBettingDecision,
    NoLimitBettingState,
    TerminalReason,
)
from .clock import ClockInvalidError, ClockReversedError, MonotonicWitness
from .model import (
    ActionEnvelope,
    DecisionRecord,
    DeliveryStatus,
    Event,
    FailureCode,
    FailureRecord,
    HandAction,
    HandStartedEvent,
    MailboxRejectionError,
    OpponentActionEvent,
    PotRecord,
    PreparationUseRecord,
    SelectionReason,
    SettlementRecord,
    ShowdownResultEvent,
    StreetRevealedEvent,
    TimingRecord,
    TimingStatus,
    visible_cards_sha256,
)


class InvalidDecisionContextError(RuntimeError):
    """The decision context failed validation before any lookup."""


class InvalidBlueprintEntryError(RuntimeError):
    """A matching blueprint entry is illegal in the exact betting state."""


def select_blueprint_action(
    source: object,
    cards: OneSeatCardState,
    betting: NoLimitBettingState,
    decision: LegalBettingDecision,
) -> BlueprintSelection:
    """Look up one action from exactly four inputs and nothing else.

    The policy surface receives the immutable blueprint, the controlled
    seat's card state, the public betting state, and the exact legal
    decision — never an event iterator, seed, host, mailbox, runtime, or
    complete deal.
    """

    try:
        key = BlueprintDecisionKey.from_state(
            cards=cards,
            betting=betting,
            decision=decision,
        )
    except (TypeError, ValueError) as error:
        raise InvalidDecisionContextError(str(error)) from error

    try:
        selection = source.action_for(cards=cards, betting=betting, decision=decision)
    except (ClockInvalidError, ClockReversedError):
        raise
    except (TypeError, ValueError, AssertionError) as error:
        if _has_illegal_matching_entry(source, key, decision):
            raise InvalidBlueprintEntryError(str(error)) from error
        raise InvalidDecisionContextError(str(error)) from error

    if not isinstance(selection, BlueprintSelection):
        raise InvalidDecisionContextError("blueprint lookup returned a foreign value")
    try:
        require_legal_blueprint_action(selection.action, decision)
    except (TypeError, ValueError) as error:
        raise InvalidBlueprintEntryError(str(error)) from error
    return selection


def _has_illegal_matching_entry(
    source: object,
    key: BlueprintDecisionKey,
    decision: LegalBettingDecision,
) -> bool:
    """Classify a lookup refusal by the real table, never by message text."""

    entries = getattr(source, "entries", ())
    if not isinstance(entries, tuple):
        return False
    for entry in entries:
        if getattr(entry, "key", None) != key:
            continue
        try:
            require_legal_blueprint_action(entry.action, decision)
        except (TypeError, ValueError):
            return True
    return False


@dataclass(frozen=True, slots=True)
class DispatchOutcome:
    """What one host event produced: acceptance, a decision, or a failure."""

    status: str
    decision: DecisionRecord | None = None
    failure: FailureRecord | None = None


class _HandFailure(Exception):
    def __init__(
        self,
        code: FailureCode,
        *,
        delivery_status: DeliveryStatus = DeliveryStatus.NOT_ATTEMPTED,
        delivered_action: HandAction | None = None,
        timing: TimingRecord | None = None,
        decision: DecisionRecord | None = None,
    ) -> None:
        super().__init__(code.value)
        self.code = code
        self.delivery_status = delivery_status
        self.delivered_action = delivered_action
        self.timing = timing
        self.decision = decision


class HandRuntime:
    """One complete blueprint-only hand behind a strict public event boundary."""

    def __init__(self, *, blueprint: object, mailbox: object, clock: object | None = None) -> None:
        if not hasattr(blueprint, "action_for") or not hasattr(blueprint, "digest"):
            raise TypeError("runtime requires an immutable blueprint action source")
        if not hasattr(mailbox, "deliver"):
            raise TypeError("runtime requires a host mailbox")
        witness = clock if isinstance(clock, MonotonicWitness) else MonotonicWitness(clock)
        self._witness = witness
        self._blueprint = blueprint
        self._mailbox = mailbox
        self._outer: ActionClockLedger | None = None
        self._spine: LegalDecisionSpineV2 | None = None
        self._cards: OneSeatCardState | None = None
        self._hand_id: str | None = None
        self._controlled_seat: int | None = None
        self._next_event_index = 0
        self._action_index = 0
        self._street_action_index = 0
        self._street = "preflop"
        self._strengths: tuple[object, ...] | None = None
        self._dead = False
        self._policy_disabled = False

    # -- public observation ------------------------------------------------

    @property
    def betting_terminal(self) -> bool:
        return self._spine is not None and self._spine.state.is_terminal

    @property
    def hand_complete(self) -> bool:
        return self.betting_terminal and not self._dead

    @property
    def state(self) -> NoLimitBettingState | None:
        return None if self._spine is None else self._spine.state

    # -- dispatch ----------------------------------------------------------

    def dispatch(self, event: Event) -> DispatchOutcome:
        """Process exactly one public host event under one response wall."""

        if self._dead:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="no further input after a terminated hand",
            )
        if isinstance(event, HandStartedEvent):
            return self._dispatch_hand_started(event)
        if self._spine is None:
            return self._fail(FailureCode.EVENT_ORDER, event=event, message="hand not started")
        if isinstance(event, OpponentActionEvent):
            return self._dispatch_opponent_action(event)
        if isinstance(event, StreetRevealedEvent):
            return self._dispatch_street_revealed(event)
        if isinstance(event, ShowdownResultEvent):
            return self._dispatch_showdown_result(event)
        return self._fail(FailureCode.INVALID_EVENT, event=event, message="unknown event kind")

    # -- event handlers ----------------------------------------------------

    def _dispatch_hand_started(self, event: HandStartedEvent) -> DispatchOutcome:
        if self._spine is not None:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="a new hand requires a fresh runtime",
            )
        outer = ActionClockLedger("preflop", clock_ns=self._witness)
        boundary = outer.start_transition_boundary()
        wall_start_ns = boundary.started_ns
        try:
            spine = LegalDecisionSpineV2.new_hand(
                button=event.button,
                controlled_seat=event.controlled_seat,
                starting_stacks=event.starting_stacks,
                small_blind=event.small_blind,
                big_blind=event.big_blind,
                clock_ns=self._witness,
            )
            cards = OneSeatCardState.preflop(
                controlled_seat=event.controlled_seat,
                private_hand=event.private_cards,
            )
        except (ClockInvalidError, ClockReversedError) as error:
            return self._clock_failure(error, event=event, wall_start_ns=None)
        except (TypeError, ValueError) as error:
            outer.abort_transition_boundary(boundary)
            return self._fail(FailureCode.INVALID_EVENT, event=event, message=str(error))

        self._outer = outer
        self._spine = spine
        self._cards = cards
        self._hand_id = event.hand_id
        self._controlled_seat = event.controlled_seat
        self._next_event_index = 1
        return self._finish_boundary(boundary, event, wall_start_ns)

    def _dispatch_opponent_action(self, event: OpponentActionEvent) -> DispatchOutcome:
        order = self._check_common(event)
        if order is not None:
            return order
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal or state.round_complete:
            return self._fail(
                FailureCode.EVENT_ORDER, event=event, message="betting round is closed"
            )
        if event.street != state.street.value:
            return self._fail(FailureCode.EVENT_ORDER, event=event, message="wrong street")
        if event.seat == self._controlled_seat:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="controlled-seat actions use the emission path",
            )
        if event.seat != state.acting_seat:
            return self._fail(FailureCode.EVENT_ORDER, event=event, message="wrong actor")

        outer = self._outer
        assert outer is not None
        boundary = outer.start_transition_boundary()
        wall_start_ns = boundary.started_ns
        try:
            spine.observe_opponent_action(event.action.to_betting_action())
        except (ClockInvalidError, ClockReversedError) as error:
            return self._clock_failure(error, event=event, wall_start_ns=wall_start_ns)
        except (TypeError, ValueError) as error:
            outer.abort_transition_boundary(boundary)
            return self._fail(FailureCode.INVALID_EVENT, event=event, message=str(error))
        self._next_event_index += 1
        return self._finish_boundary(boundary, event, wall_start_ns)

    def _dispatch_street_revealed(self, event: StreetRevealedEvent) -> DispatchOutcome:
        order = self._check_common(event)
        if order is not None:
            return order
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal or not state.round_complete:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="a reveal requires a completed betting round",
            )
        streets = tuple(street.value for street in BettingStreet)
        current = streets.index(state.street.value)
        if current + 1 >= len(streets) or streets[current + 1] != event.street:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="reveals advance exactly one street",
            )
        assert self._cards is not None
        try:
            cards = self._cards.advance_to(BettingStreet(event.street), event.cards)
        except (TypeError, ValueError) as error:
            return self._fail(FailureCode.INVALID_EVENT, event=event, message=str(error))

        outer = self._outer
        assert outer is not None
        boundary = outer.start_transition_boundary()
        wall_start_ns = boundary.started_ns
        try:
            spine.advance_street()
        except (ClockInvalidError, ClockReversedError) as error:
            return self._clock_failure(error, event=event, wall_start_ns=wall_start_ns)
        except (TypeError, ValueError) as error:
            outer.abort_transition_boundary(boundary)
            return self._fail(FailureCode.INVALID_EVENT, event=event, message=str(error))
        self._cards = cards
        self._street = event.street
        self._street_action_index = 0
        self._next_event_index += 1
        return self._finish_boundary(boundary, event, wall_start_ns, next_street=event.street)

    def _dispatch_showdown_result(self, event: ShowdownResultEvent) -> DispatchOutcome:
        order = self._check_common(event)
        if order is not None:
            return order
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal and state.terminal_reason is TerminalReason.FOLD:
            return self._fail(
                FailureCode.EVENT_ORDER,
                event=event,
                message="a fold terminal accepts no showdown result",
            )
        if not state.is_terminal:
            if state.street is not BettingStreet.RIVER or not state.round_complete:
                return self._fail(
                    FailureCode.EVENT_ORDER,
                    event=event,
                    message="showdown follows a completed river",
                )
            outer = self._outer
            assert outer is not None
            boundary = outer.start_transition_boundary()
            try:
                spine.advance_street()
            except (ClockInvalidError, ClockReversedError) as error:
                return self._clock_failure(
                    error, event=event, wall_start_ns=boundary.started_ns
                )
            except (TypeError, ValueError) as error:
                outer.abort_transition_boundary(boundary)
                return self._fail(FailureCode.INVALID_EVENT, event=event, message=str(error))
            outer.finish_transition_boundary(boundary, starts_controlled_action=False)

        live = spine.state.live_seats
        for seat in live:
            if event.strengths[seat] is None:
                return self._fail(
                    FailureCode.INVALID_EVENT,
                    event=event,
                    message="every live showdown seat requires a strength",
                )
        for seat in range(len(event.strengths)):
            if seat not in live and event.strengths[seat] is not None:
                return self._fail(
                    FailureCode.INVALID_EVENT,
                    event=event,
                    message="folded seats carry a null strength",
                )
        self._policy_disabled = True
        self._strengths = event.strengths
        self._next_event_index += 1
        return DispatchOutcome(status="accepted")

    # -- boundary and decision --------------------------------------------

    def _check_common(self, event: Event) -> DispatchOutcome | None:
        if event.hand_id != self._hand_id:
            return self._fail(FailureCode.EVENT_ORDER, event=event, message="wrong hand id")
        if event.event_index != self._next_event_index:
            return self._fail(
                FailureCode.EVENT_ORDER, event=event, message="non-contiguous event index"
            )
        return None

    def _finish_boundary(
        self,
        boundary: object,
        event: Event,
        wall_start_ns: int,
        *,
        next_street: str | None = None,
    ) -> DispatchOutcome:
        outer = self._outer
        spine = self._spine
        assert outer is not None and spine is not None
        state = spine.state
        starts_action = (
            not self._policy_disabled
            and not state.is_terminal
            and not state.round_complete
            and state.acting_seat == self._controlled_seat
        )
        try:
            outer.finish_transition_boundary(
                boundary,
                starts_controlled_action=starts_action,
                controlled_action_public_state_sha256=(
                    public_betting_state_sha256(state) if starts_action else None
                ),
                next_street=next_street,
            )
        except (ClockInvalidError, ClockReversedError) as error:
            return self._clock_failure(error, event=event, wall_start_ns=wall_start_ns)
        if not starts_action:
            return DispatchOutcome(status="accepted")
        return self._decide(event, wall_start_ns)

    def _decide(self, event: Event, wall_start_ns: int) -> DispatchOutcome:
        outer = self._outer
        spine = self._spine
        cards = self._cards
        assert outer is not None and spine is not None and cards is not None
        state_before = spine.state
        self._action_index += 1
        self._street_action_index += 1
        action_index = self._action_index
        try:
            record = self._decide_inner(event, wall_start_ns, action_index)
        except _HandFailure as failure:
            self._dead = True
            return DispatchOutcome(
                status="failed",
                decision=failure.decision,
                failure=FailureRecord(
                    hand_id=self._hand_id,
                    event_index=event.event_index,
                    action_index=action_index,
                    code=failure.code,
                    delivery_status=failure.delivery_status,
                    delivered_action=failure.delivered_action,
                    timing=failure.timing,
                ),
            )
        self._next_event_index_after_decision()
        return DispatchOutcome(status="decided", decision=record)

    def _next_event_index_after_decision(self) -> None:
        """A controlled action consumes no host event index."""

    def _decide_inner(
        self,
        event: Event,
        wall_start_ns: int,
        action_index: int,
    ) -> DecisionRecord:
        outer = self._outer
        spine = self._spine
        cards = self._cards
        assert outer is not None and spine is not None and cards is not None
        state_before = spine.state

        try:
            ticket = spine.open_controlled_decision()
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError, RuntimeError) as error:
            raise _HandFailure(
                FailureCode.INVALID_DECISION_CONTEXT,
                timing=self._interrupted_timing(
                    FailureCode.INVALID_DECISION_CONTEXT, wall_start_ns
                ),
            ) from error

        try:
            selection = select_blueprint_action(
                source=self._blueprint,
                cards=cards,
                betting=state_before,
                decision=ticket.decision,
            )
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except InvalidBlueprintEntryError as error:
            raise _HandFailure(
                FailureCode.INVALID_BLUEPRINT_ENTRY,
                timing=self._interrupted_timing(
                    FailureCode.INVALID_BLUEPRINT_ENTRY, wall_start_ns
                ),
            ) from error
        except InvalidDecisionContextError as error:
            raise _HandFailure(
                FailureCode.INVALID_DECISION_CONTEXT,
                timing=self._interrupted_timing(
                    FailureCode.INVALID_DECISION_CONTEXT, wall_start_ns
                ),
            ) from error

        selected = HandAction.from_betting_action(selection.action)
        envelope = ActionEnvelope(
            hand_id=self._hand_id,
            action_index=action_index,
            seat=self._controlled_seat,
            street=state_before.street.value,
            action=selected,
        )

        # Ready-to-emit checkpoint: all decision work is complete.
        try:
            ready = outer.snapshot()
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        work_cutoff_crossed = ready.work_remaining_seconds <= 0.0

        try:
            emitted = spine.emit_controlled_action(
                candidate=None,
                fallback=selection.action,
            )
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError, RuntimeError) as error:
            raise _HandFailure(
                FailureCode.INVALID_BLUEPRINT_ENTRY,
                timing=self._interrupted_timing(
                    FailureCode.INVALID_BLUEPRINT_ENTRY, wall_start_ns
                ),
            ) from error

        state_after = spine.state
        try:
            self._mailbox.deliver(envelope)
        except MailboxRejectionError as error:
            raise _HandFailure(
                FailureCode.DELIVERY_REJECTED,
                delivery_status=DeliveryStatus.REJECTED,
                timing=self._interrupted_timing(FailureCode.DELIVERY_REJECTED, wall_start_ns),
            ) from error
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except BaseException as error:
            raise _HandFailure(
                FailureCode.DELIVERY_AMBIGUOUS,
                delivery_status=DeliveryStatus.UNKNOWN,
                timing=self._interrupted_timing(FailureCode.DELIVERY_AMBIGUOUS, wall_start_ns),
            ) from error

        try:
            closing = outer.finish_action()
            emission_observed_ns = self._witness.last_returned_ns
        except (ClockInvalidError, ClockReversedError) as error:
            code = (
                FailureCode.CLOCK_REVERSED
                if isinstance(error, ClockReversedError)
                else FailureCode.CLOCK_INVALID
            )
            timing = self._interrupted_timing(code, wall_start_ns)
            record = self._decision_record(
                event=event,
                action_index=action_index,
                state_before=state_before,
                state_after=state_after,
                selection=selection,
                selected=selected,
                spine_reason=emitted.reason.value,
                timing=timing,
                failure_reason=code,
            )
            raise _HandFailure(
                code,
                delivery_status=DeliveryStatus.ACCEPTED,
                delivered_action=selected,
                timing=timing,
                decision=record,
            ) from error

        assert emission_observed_ns is not None
        elapsed_ns = emission_observed_ns - wall_start_ns
        if elapsed_ns / 1_000_000_000 != closing.action_wall_elapsed_seconds:
            raise _HandFailure(
                FailureCode.CLOCK_INVALID,
                delivery_status=DeliveryStatus.ACCEPTED,
                delivered_action=selected,
                timing=self._interrupted_timing(FailureCode.CLOCK_INVALID, wall_start_ns),
            )

        deadline_crossed = bool(closing.deadline_crossed)
        failure_code: FailureCode | None = None
        if deadline_crossed:
            failure_code = FailureCode.ACTION_DEADLINE_EXCEEDED
        elif work_cutoff_crossed:
            failure_code = FailureCode.WORK_CUTOFF_EXCEEDED

        timing = TimingRecord(
            status=TimingStatus.COMPLETED,
            interruption_reason=None,
            wall_start_ns=wall_start_ns,
            last_valid_observation_ns=emission_observed_ns,
            emission_observed_ns=emission_observed_ns,
            elapsed_ns=elapsed_ns,
            response_compute_seconds=float(closing.response_compute_seconds),
            response_uninstrumented_seconds=float(closing.response_uninstrumented_seconds),
            work_cutoff_crossed=bool(work_cutoff_crossed),
            deadline_crossed=deadline_crossed,
        )
        record = self._decision_record(
            event=event,
            action_index=action_index,
            state_before=state_before,
            state_after=state_after,
            selection=selection,
            selected=selected,
            spine_reason=emitted.reason.value,
            timing=timing,
            failure_reason=failure_code,
        )
        if failure_code is not None:
            raise _HandFailure(
                failure_code,
                delivery_status=DeliveryStatus.ACCEPTED,
                delivered_action=selected,
                timing=timing,
                decision=record,
            )
        return record

    def _decision_record(
        self,
        *,
        event: Event,
        action_index: int,
        state_before: NoLimitBettingState,
        state_after: NoLimitBettingState,
        selection: BlueprintSelection,
        selected: HandAction,
        spine_reason: str,
        timing: TimingRecord,
        failure_reason: FailureCode | None,
    ) -> DecisionRecord:
        assert self._cards is not None and self._hand_id is not None
        assert self._controlled_seat is not None
        return DecisionRecord(
            hand_id=self._hand_id,
            event_index=event.event_index,
            action_index=action_index,
            street_action_index=self._street_action_index,
            seat=self._controlled_seat,
            street=state_before.street.value,
            state_before_sha256=public_betting_state_sha256(state_before),
            state_after_sha256=public_betting_state_sha256(state_after),
            visible_cards_sha256=visible_cards_sha256(self._cards),
            blueprint_sha256=selection.source_digest,
            selected_action=selected,
            selection_reason=(
                SelectionReason.TABLE_HIT
                if selection.table_hit
                else SelectionReason.PASSIVE_DEFAULT
            ),
            spine_reason=spine_reason,
            timing=timing,
            preparation_use=PreparationUseRecord(),
            failure_reason=failure_reason,
        )

    # -- failure helpers ---------------------------------------------------

    def _interrupted_timing(
        self,
        code: FailureCode,
        wall_start_ns: int | None,
    ) -> TimingRecord | None:
        if wall_start_ns is None:
            return None
        last = self._witness.last_returned_ns
        if last is None or last < wall_start_ns:
            last = wall_start_ns
        return TimingRecord(
            status=TimingStatus.INTERRUPTED,
            interruption_reason=code,
            wall_start_ns=wall_start_ns,
            last_valid_observation_ns=last,
            emission_observed_ns=None,
            elapsed_ns=None,
            response_compute_seconds=None,
            response_uninstrumented_seconds=None,
            work_cutoff_crossed=None,
            deadline_crossed=None,
        )

    def _clock_hand_failure(self, error: BaseException, wall_start_ns: int | None) -> _HandFailure:
        code = (
            FailureCode.CLOCK_REVERSED
            if isinstance(error, ClockReversedError)
            else FailureCode.CLOCK_INVALID
        )
        return _HandFailure(code, timing=self._interrupted_timing(code, wall_start_ns))

    def _clock_failure(
        self,
        error: BaseException,
        *,
        event: Event,
        wall_start_ns: int | None,
    ) -> DispatchOutcome:
        code = (
            FailureCode.CLOCK_REVERSED
            if isinstance(error, ClockReversedError)
            else FailureCode.CLOCK_INVALID
        )
        self._dead = True
        return DispatchOutcome(
            status="failed",
            failure=FailureRecord(
                hand_id=self._hand_id,
                event_index=getattr(event, "event_index", None),
                action_index=None,
                code=code,
                delivery_status=DeliveryStatus.NOT_ATTEMPTED,
                delivered_action=None,
                timing=self._interrupted_timing(code, wall_start_ns),
            ),
        )

    def _fail(self, code: FailureCode, *, event: Event, message: str) -> DispatchOutcome:
        self._dead = True
        return DispatchOutcome(
            status="failed",
            failure=FailureRecord(
                hand_id=self._hand_id,
                event_index=getattr(event, "event_index", None),
                action_index=None,
                code=code,
                delivery_status=DeliveryStatus.NOT_ATTEMPTED,
                delivered_action=None,
                timing=None,
            ),
        )

    # -- settlement --------------------------------------------------------

    def settle(self) -> SettlementRecord:
        """Produce the runtime's settlement; the host oracle judges it."""

        spine = self._spine
        if spine is None or not spine.state.is_terminal:
            raise RuntimeError("settlement requires a terminal hand")
        state = spine.state
        if state.terminal_reason is TerminalReason.SHOWDOWN:
            if self._strengths is None:
                raise RuntimeError("showdown settlement requires accepted strengths")
            settlement = state.settle(list(self._strengths))
        else:
            settlement = state.settle()
        return SettlementRecord(
            payouts=tuple(int(value) for value in settlement.payouts),
            final_stacks=tuple(int(value) for value in settlement.final_stacks),
            pots=tuple(
                PotRecord(
                    amount=int(pot.amount),
                    seats=tuple(sorted(int(seat) for seat in pot.eligible_seats)),
                )
                for pot in settlement.side_pots
            ),
        )


__all__ = [
    "DispatchOutcome",
    "HandRuntime",
    "InvalidBlueprintEntryError",
    "InvalidDecisionContextError",
    "select_blueprint_action",
]
