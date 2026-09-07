"""Visible-state transitions, blueprint selection, and emission (ADR-0485).

The runtime consumes one public event at a time plus the controlled seat's
own cards. It never receives the dealer's complete deal, the future
schedule, an event iterator, or the replay host. The outer
``ActionClockLedger`` is the sole response authority; the V2 spine's ledger
remains controller diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace

from ..blueprint_preparation.lookup import PreparedBlueprint
from ..decision_provider.model import DecisionObservation, ProviderDecisionRecord, ProviderIdentity
from ..decision_provider.providers import make_provider
from ..decision_provider.selection import Selection, resolve_proposal

from ..action_clock import ActionClockLedger
from ..holdem_cards import OneSeatCardState
from ..immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    BlueprintSelection,
    ImmutableBlueprintActionSource,
    passive_blueprint_action,
    require_legal_blueprint_action,
)
from ..legal_decision_spine_v2 import LegalDecisionSpineV2, public_betting_state_sha256
from ..no_limit_betting import (
    BettingAction,
    BettingActionKind,
    BettingActionRecord,
    RaiseBounds,
    BettingStreet,
    LegalBettingDecision,
    NoLimitBettingState,
    TerminalReason,
)
from .clock import ClockInvalidError, ClockReversedError, MonotonicWitness
from .model import (
    ActionEnvelope,
    DecisionRecord,
    DeliveryReceipt,
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
    admit_event,
    admit_receipt,
)


class OperationFailed(RuntimeError):
    """An owned operation failed; its typed cause is already journalled."""


class InvalidDecisionContextError(RuntimeError):
    """The decision context failed validation before any lookup."""


class InvalidBlueprintEntryError(RuntimeError):
    """A matching blueprint entry is illegal in the exact betting state."""



_POLICY_RECORD_TYPES = (
    ImmutableBlueprintActionSource, BlueprintActionEntry, BlueprintDecisionKey,
    BettingAction, BettingActionRecord, OneSeatCardState, NoLimitBettingState,
    LegalBettingDecision, RaiseBounds,
)
_POLICY_ENUM_TYPES = (BettingStreet, BettingActionKind, TerminalReason)


def _copy_exact_policy_value(value: object) -> object:
    """Rebuild an immutable graph without invoking caller-defined behavior."""
    kind = type(value)
    if value is None or kind is int or kind is bool or kind is str:
        return value
    if any(kind is enum for enum in _POLICY_ENUM_TYPES):
        return value
    if kind is tuple:
        return tuple(_copy_exact_policy_value(item) for item in value)
    if any(kind is record for record in _POLICY_RECORD_TYPES):
        # kind is now one of our fixed exact dataclass types, never a caller type.
        values = {
            field.name: _copy_exact_policy_value(getattr(value, field.name))
            for field in fields(kind)
        }
        return kind(**values)
    raise TypeError("policy/context graph requires exact immutable values")


def _admit_blueprint(source: object) -> ImmutableBlueprintActionSource:
    """Own a fully validated exact policy before identity, hashing or lookup."""
    if type(source) is not ImmutableBlueprintActionSource:
        raise TypeError("runtime requires an exact immutable blueprint source")
    try:
        return _copy_exact_policy_value(source)
    except (TypeError, ValueError, AttributeError, RecursionError):
        raise TypeError("immutable blueprint contains an invalid value graph") from None


def _same_exact_value(left: object, right: object) -> bool:
    """Value equality after exact typing, including dataclasses without validators."""
    kind = type(right)
    if type(left) is not kind:
        return False
    if kind is tuple:
        return len(left) == len(right) and all(
            _same_exact_value(a, b) for a, b in zip(left, right)
        )
    if any(kind is record for record in _POLICY_RECORD_TYPES):
        return all(_same_exact_value(getattr(left, field.name), getattr(right, field.name))
                   for field in fields(kind))
    return left == right


def select_blueprint_action(
    source: object,
    cards: OneSeatCardState,
    betting: NoLimitBettingState,
    decision: LegalBettingDecision,
) -> BlueprintSelection:
    """Admit four visible inputs, then use the unchanged sealed lookup."""
    try:
        admitted = _admit_blueprint(source)
    except (TypeError, ValueError):
        raise InvalidDecisionContextError("invalid immutable blueprint source") from None
    return _select_admitted_blueprint_action(admitted, cards, betting, decision)


def _select_admitted_blueprint_action(
    source: ImmutableBlueprintActionSource,
    cards: OneSeatCardState,
    betting: NoLimitBettingState,
    decision: LegalBettingDecision,
    *,
    prepared: PreparedBlueprint | None = None,
) -> BlueprintSelection:
    """Select from a runtime-owned policy; no repeated table admission or extra hash."""
    try:
        if (type(cards) is not OneSeatCardState or type(betting) is not NoLimitBettingState
                or type(decision) is not LegalBettingDecision):
            raise TypeError("context requires exact values")
        cards = _copy_exact_policy_value(cards)
        betting = _copy_exact_policy_value(betting)
        expected = betting.legal_decision()
        # Traverse only the kernel-derived shape. A tuple in a scalar field is
        # refused before descending, regardless of its caller-chosen depth.
        if not _same_exact_value(decision, expected):
            raise ValueError("decision disagrees with the exact betting state")
        decision = expected
        key = BlueprintDecisionKey.from_state(cards=cards, betting=betting, decision=decision)
    except (TypeError, ValueError, AttributeError, AssertionError, RecursionError):
        raise InvalidDecisionContextError("invalid exact legal decision context") from None
    try:
        if prepared is None:
            selection = ImmutableBlueprintActionSource.action_for(
                source, cards=cards, betting=betting, decision=decision
            )
        elif type(prepared) is PreparedBlueprint:
            selection = PreparedBlueprint.action_for(
                prepared, cards=cards, betting=betting, decision=decision
            )
        else:
            raise TypeError("runtime preparation requires an exact prepared blueprint")
    except (ClockInvalidError, ClockReversedError):
        raise
    except (TypeError, ValueError, AssertionError):
        if _has_illegal_matching_entry(source, key, decision):
            raise InvalidBlueprintEntryError("matching blueprint entry is illegal") from None
        raise InvalidDecisionContextError("immutable blueprint lookup failed") from None
    if type(selection) is not BlueprintSelection:
        raise InvalidDecisionContextError("blueprint lookup returned a foreign value")
    try:
        require_legal_blueprint_action(selection.action, decision)
    except (TypeError, ValueError):
        raise InvalidBlueprintEntryError("selected blueprint entry is illegal") from None
    return selection


def _has_illegal_matching_entry(
    source: ImmutableBlueprintActionSource,
    key: BlueprintDecisionKey,
    decision: LegalBettingDecision,
) -> bool:
    """Classify using only owned exact entries, never the caller's source."""
    for entry in source.entries:
        if entry.key != key:
            continue
        try:
            require_legal_blueprint_action(entry.action, decision)
        except (TypeError, ValueError):
            return True
    return False

@dataclass(frozen=True, slots=True)
class AccountingTotals:
    """Ordered sums of public ledger intervals through the pre-publication cut.

    Each is null when its category's measurement could not be completed —
    never zero, and never a prefix presented as a complete total.
    """

    preparation_compute_seconds: float | None
    post_terminal_compute_seconds: float | None
    interrupted_response_count: int
    complete: bool


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
        clock_error: BaseException | None = None,
    ) -> None:
        super().__init__(code.value)
        self.code = code
        self.delivery_status = delivery_status
        self.delivered_action = delivered_action
        self.timing = timing
        self.decision = decision
        self.clock_error = clock_error


class _OwnedInterval:
    """One owner for entry, body failure, and exit of non-response work.

    A normal class keeps arbitrary body exceptions out of contextlib's generator
    protocol. The caller's exception is never rendered, queried, or re-raised.
    """

    def __init__(self, runtime: HandRuntime, body_failure: FailureCode,
                 publication: list[float] | None = None, *,
                 required: bool = False, cleanup=None) -> None:
        self._runtime = runtime
        self._body_failure = body_failure
        self._publication = publication
        self._required = required
        self._cleanup = cleanup
        self._opened = False
        self._terminal_at_entry = False

    def __enter__(self) -> _OwnedInterval:
        runtime = self._runtime
        runtime._retain_witness_failure()
        if not runtime.measurable:
            runtime._accounting_complete = False
            if self._required:
                raise OperationFailed("required measurement could not start")
            return self
        outer = runtime._outer
        assert outer is not None
        self._terminal_at_entry = runtime.betting_terminal
        try:
            outer.start_preparation_work()
        except (ClockInvalidError, ClockReversedError, RuntimeError) as error:
            runtime._record_closure_failure(error)
        else:
            self._opened = True
        if self._required and not self._opened:
            raise OperationFailed("required measurement could not start")
        return self

    def __exit__(self, error_type: object, error: BaseException | None,
                 traceback: object) -> bool:
        runtime = self._runtime
        # A body may catch the witness's exception. The occurrence still precedes
        # a later body error, even if no clock exception escaped the callback.
        runtime._retain_witness_failure()
        if error is not None:
            runtime._retain_error(error, otherwise=self._body_failure)
        cleanup_failed = False
        if self._cleanup is not None:
            try:
                cleanup_errors = self._cleanup()
                if cleanup_errors is not None:
                    if type(cleanup_errors) is not tuple:
                        raise TypeError("owned cleanup must return an exact error tuple")
                    for cleanup_error in cleanup_errors:
                        if not issubclass(type(cleanup_error), BaseException):
                            raise TypeError("owned cleanup must return actual exceptions")
                        # finish may already have raised the first close error
                        # as this same body's cause. Other equal codes stand.
                        if cleanup_error is error:
                            continue
                        cleanup_failed = True
                        runtime._retain_error(cleanup_error, otherwise=self._body_failure)
            except BaseException as cleanup_error:
                cleanup_failed = True
                runtime._retain_error(cleanup_error, otherwise=self._body_failure)
        if self._opened:
            outer = runtime._outer
            assert outer is not None
            try:
                interval = outer.stop_preparation_work()
            except (ClockInvalidError, ClockReversedError, RuntimeError) as closing_error:
                runtime._record_closure_failure(closing_error)
            else:
                if self._publication is None:
                    runtime._charge_interval(interval, terminal_at_entry=self._terminal_at_entry)
                else:
                    self._publication.append(float(interval.compute_seconds))
        if error is not None or cleanup_failed or (self._required and not runtime.measurable):
            # Only a trusted constant exception crosses the host handler. No
            # caller str/__class__/__traceback__ hook participates in transfer.
            raise OperationFailed("owned operation failed") from None
        return False


class HandRuntime:
    """One complete blueprint-only hand behind a strict public event boundary."""

    def __init__(self, *, blueprint: object, mailbox: object, clock: object | None = None,
                 strategy: str = "blueprint-v1", source_manifest_sha256: str | None = None) -> None:
        admitted_blueprint = _admit_blueprint(blueprint)
        if type(strategy) is not str or strategy not in ("blueprint-v1", "baseline-rules-v1"):
            raise ValueError("unknown fixed strategy")
        if strategy != "blueprint-v1" and (type(source_manifest_sha256) is not str
                or len(source_manifest_sha256) != 64
                or any(c not in "0123456789abcdef" for c in source_manifest_sha256)):
            raise ValueError("baseline requires admitted source manifest")
        self.strategy = strategy
        self.source_manifest_sha256 = source_manifest_sha256
        self._provider = None if strategy == "blueprint-v1" else make_provider(
            strategy, admitted_blueprint)
        self._provider_identity = None if self._provider is None else self._provider.identity
        self._provider_binding = None if self._provider_identity is None else (
            self._provider_identity.provider, self._provider_identity.config_sha256)
        self._provider_type = type(self._provider)
        self._provider_source = source_manifest_sha256
        self._provider_context = None
        if not hasattr(mailbox, "deliver"):
            raise TypeError("runtime requires a host mailbox")
        witness = clock if isinstance(clock, MonotonicWitness) else MonotonicWitness(clock)
        self._witness = witness
        self._blueprint = admitted_blueprint
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
        self._pre_terminal_ns = 0
        self._post_terminal_ns = 0
        self._interrupted_responses = 0
        self._accounting_complete = True
        self._finalized = False
        self._complete = False
        self._boundary_open = False
        self._blueprint_digest: str | None = None
        self._prepared_blueprint: PreparedBlueprint | None = None
        self._known_cutoff: bool | None = None
        self._known_deadline: bool | None = None
        self._accepted_deliveries = 0
        self._clock_dead = False
        self._closure_failures: list[FailureCode] = []
        self._retained_witness_failure: BaseException | None = None

    # -- public observation ------------------------------------------------

    @property
    def provider_identity(self) -> ProviderIdentity | None:
        return self._provider_identity

    @property
    def blueprint_sha256(self) -> str:
        """Header identity comes from the same owned policy used for decisions."""
        return (self._blueprint.digest if self._blueprint_digest is None
                else self._blueprint_digest)

    @property
    def betting_terminal(self) -> bool:
        return self._spine is not None and self._spine.state.is_terminal

    @property
    def hand_complete(self) -> bool:
        """True once the hand is irreversibly finished; no event is accepted after."""

        return self._complete and not self._dead

    @property
    def accepted_delivery_count(self) -> int:
        """Deliveries the mailbox acknowledged, late or interrupted included."""

        return self._accepted_deliveries

    @property
    def state(self) -> NoLimitBettingState | None:
        return None if self._spine is None else self._spine.state

    # -- public ledger accounting -----------------------------------------

    def _record_established(self, snapshot: object) -> None:
        """Latch cutoff/deadline truths from one valid outer snapshot."""

        if getattr(snapshot, "deadline_crossed", False):
            self._known_deadline = True
        remaining = getattr(snapshot, "work_remaining_seconds", None)
        if type(remaining) is float and remaining <= 0.0:
            self._known_cutoff = True

    def _charge_interval(self, interval: object, *, terminal_at_entry: bool) -> None:
        """Classify one public interval exactly once, by terminal-at-entry."""

        nanoseconds = int(round(float(interval.compute_seconds) * 1_000_000_000))
        if terminal_at_entry:
            self._post_terminal_ns += nanoseconds
        else:
            self._pre_terminal_ns += nanoseconds

    @property
    def closure_failures(self) -> tuple[FailureCode, ...]:
        """Typed causes of closure faults, in the order they occurred."""

        self._retain_witness_failure()
        return tuple(self._closure_failures)


    def _retain_witness_failure(self) -> None:
        """Drain one source occurrence, including one caught inside a callback."""
        occurrence = self._witness.failure
        if occurrence is None or occurrence is self._retained_witness_failure:
            return
        self._retained_witness_failure = occurrence
        self._clock_dead = True
        self._accounting_complete = False
        self._closure_failures.append(
            self.classify(occurrence, otherwise=FailureCode.CLOCK_INVALID)
        )

    def record(self, code: FailureCode) -> None:
        """Retain each genuine cause in order, without deduplicating its code."""
        if type(code) is not FailureCode:
            raise TypeError("only a typed failure code may be journalled")
        self._retain_witness_failure()
        self._closure_failures.append(code)

    def _retain_error(self, error: BaseException, *, otherwise: FailureCode) -> None:
        self._retain_witness_failure()
        if self._witness.owns_failure(error):
            # This same source occurrence was retained above or at an earlier
            # boundary. Equal codes on independent exceptions are still distinct.
            return
        self.record(self.classify(error, otherwise=otherwise))

    def _record_closure_failure(self, error: BaseException) -> None:
        self._clock_dead = True
        self._accounting_complete = False
        self._retain_witness_failure()
        if issubclass(type(error), (ClockInvalidError, ClockReversedError)):
            self._retain_error(error, otherwise=FailureCode.CLOCK_INVALID)
        # A ledger-state refusal makes accounting incomplete but does not invent
        # a clock occurrence or a failure code absent from the frozen vocabulary.

    @property
    def measurable(self) -> bool:
        """False once a clock fault makes further public intervals impossible."""

        return not (
            self._clock_dead
            or self._finalized
            or self._outer is None
            or self._witness.failed
        )


    def begin_host_accounting(self) -> None:
        """Initialize the public outer ledger before required host preparation.

        Direct runtime users may still initialize it with the first dispatch.
        Host setup does not bind policy or initialize private/betting state.
        """
        self._retain_witness_failure()
        if self._outer is None and not self._clock_dead and not self._finalized:
            try:
                self._outer = ActionClockLedger("preflop", clock_ns=self._witness)
            except (ClockInvalidError, ClockReversedError, RuntimeError) as error:
                self._record_closure_failure(error)
        if not self.measurable:
            self._accounting_complete = False
            raise OperationFailed("host accounting could not start")

    def owned_bookkeeping(self, *, body_failure: FailureCode,
                          required: bool = False, cleanup=None) -> _OwnedInterval:
        """Own non-response work; required entry gates ordinary host behavior."""
        return _OwnedInterval(self, body_failure, required=required, cleanup=cleanup)

    def owned_publication(self, sink: list[float], *,
                          body_failure: FailureCode, cleanup=None) -> _OwnedInterval:
        """Own final-publication work without adding it to pre-publication totals."""
        return _OwnedInterval(self, body_failure, sink, cleanup=cleanup)

    @staticmethod
    def classify(error: BaseException, *, otherwise: FailureCode) -> FailureCode:
        """Classify actual type ancestry, without executing exception metadata."""
        if issubclass(type(error), ClockReversedError):
            return FailureCode.CLOCK_REVERSED
        if issubclass(type(error), ClockInvalidError):
            return FailureCode.CLOCK_INVALID
        return otherwise

    def accounting(self) -> AccountingTotals:
        """Report the two public totals through the pre-publication cut."""

        complete = self._accounting_complete and not self._dead
        return AccountingTotals(
            preparation_compute_seconds=(
                self._pre_terminal_ns / 1_000_000_000 if self._accounting_complete else None
            ),
            post_terminal_compute_seconds=(
                self._post_terminal_ns / 1_000_000_000 if self._accounting_complete else None
            ),
            interrupted_response_count=self._interrupted_responses,
            complete=complete,
        )

    def finalize_accounting(self) -> None:
        """Close the outer ledger after the final publication interval."""

        self._retain_witness_failure()
        outer = self._outer
        if outer is None or self._finalized:
            return
        if self._clock_dead or self._witness.failed:
            self._accounting_complete = False
            self._finalized = True
            return
        try:
            outer.finalize()
        except (ClockInvalidError, ClockReversedError, RuntimeError) as error:
            self._record_closure_failure(error)
        self._finalized = True

    # -- dispatch ----------------------------------------------------------

    def dispatch(self, event: Event) -> DispatchOutcome:
        """Process exactly one public host event under one response wall.

        The outer boundary opens as the first runtime operation, before input
        validation, visible-card construction, V2 transition work, or policy
        work, so every adapter cost is inside the measured interval.
        """

        if self._dead or self._complete:
            return self._reject(FailureCode.EVENT_ORDER)
        if self._outer is None:
            try:
                self._outer = ActionClockLedger("preflop", clock_ns=self._witness)
            except (ClockInvalidError, ClockReversedError) as error:
                return self._clock_reject(
                    error, wall_start_ns=None
                )

        try:
            boundary = self._outer.start_transition_boundary()
        except (ClockInvalidError, ClockReversedError) as error:
            return self._clock_reject(
                error, wall_start_ns=None
            )
        except RuntimeError:
            return self._reject(FailureCode.EVENT_ORDER)

        wall_start_ns = boundary.started_ns
        terminal_at_entry = self.betting_terminal
        self._boundary_open = True
        self._known_cutoff = None
        self._known_deadline = None
        admitted = None
        try:
            try:
                admitted = admit_event(event)
            except (TypeError, ValueError):
                raise _HandFailure(FailureCode.INVALID_EVENT) from None
            return self._process(admitted, boundary, wall_start_ns, terminal_at_entry)
        except _HandFailure as failure:
            # The initiating cause is journalled before its own cleanup so a
            # cleanup fault can never be ordered ahead of what caused it.
            if failure.clock_error is None:
                self.record(failure.code)
            else:
                self._retain_error(failure.clock_error, otherwise=failure.code)
            self._release_boundary(boundary, terminal_at_entry)
            return self._from_failure(failure, admitted)

    def _release_boundary(self, boundary: object, terminal_at_entry: bool) -> None:
        """Close a still-open boundary so no interval escapes accounting."""

        if not self._boundary_open or self._outer is None:
            return
        self._boundary_open = False
        try:
            aborted = self._outer.abort_transition_boundary(boundary)
        except (
            ClockInvalidError,
            ClockReversedError,
            RuntimeError,
            ValueError,
        ) as error:
            self._record_closure_failure(error)
            return
        self._charge_interval(aborted, terminal_at_entry=terminal_at_entry)

    def _process(
        self,
        event: Event,
        boundary: object,
        wall_start_ns: int,
        terminal_at_entry: bool,
    ) -> DispatchOutcome:
        if isinstance(event, HandStartedEvent):
            return self._process_hand_started(
                event, boundary, wall_start_ns, terminal_at_entry
            )
        if self._spine is None:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if isinstance(event, OpponentActionEvent):
            return self._process_opponent_action(
                event, boundary, wall_start_ns, terminal_at_entry
            )
        if isinstance(event, StreetRevealedEvent):
            return self._process_street_revealed(
                event, boundary, wall_start_ns, terminal_at_entry
            )
        return self._process_showdown_result(
            event, boundary, wall_start_ns, terminal_at_entry
        )

    # -- event handlers ----------------------------------------------------

    def _process_hand_started(
        self,
        event: HandStartedEvent,
        boundary: object,
        wall_start_ns: int,
        terminal_at_entry: bool,
    ) -> DispatchOutcome:
        if self._spine is not None:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        try:
            prepared = PreparedBlueprint(self._blueprint)
            digest = prepared.digest
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except Exception as error:
            raise _HandFailure(FailureCode.SOURCE_BINDING_MISMATCH) from error
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise _HandFailure(FailureCode.SOURCE_BINDING_MISMATCH)
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
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError) as error:
            raise _HandFailure(FailureCode.INVALID_EVENT) from error

        self._spine = spine
        self._cards = cards
        self._hand_id = event.hand_id
        self._controlled_seat = event.controlled_seat
        self._blueprint_digest = digest
        self._prepared_blueprint = prepared
        self._next_event_index = 1
        return self._finish_boundary(
            boundary, event, wall_start_ns, terminal_at_entry=terminal_at_entry
        )

    def _process_opponent_action(
        self,
        event: OpponentActionEvent,
        boundary: object,
        wall_start_ns: int,
        terminal_at_entry: bool,
    ) -> DispatchOutcome:
        self._check_common(event)
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal or state.round_complete:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if event.street != state.street.value:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if event.seat == self._controlled_seat:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if event.seat != state.acting_seat:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        try:
            spine.observe_opponent_action(event.action.to_betting_action())
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError) as error:
            raise _HandFailure(FailureCode.INVALID_EVENT) from error
        self._next_event_index += 1
        return self._finish_boundary(
            boundary, event, wall_start_ns, terminal_at_entry=terminal_at_entry
        )

    def _process_street_revealed(
        self,
        event: StreetRevealedEvent,
        boundary: object,
        wall_start_ns: int,
        terminal_at_entry: bool,
    ) -> DispatchOutcome:
        self._check_common(event)
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal or not state.round_complete:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        streets = tuple(street.value for street in BettingStreet)
        current = streets.index(state.street.value)
        if current + 1 >= len(streets) or streets[current + 1] != event.street:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        assert self._cards is not None
        try:
            cards = self._cards.advance_to(BettingStreet(event.street), event.cards)
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError) as error:
            raise _HandFailure(FailureCode.INVALID_EVENT) from error
        try:
            spine.advance_street()
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError) as error:
            raise _HandFailure(FailureCode.INVALID_EVENT) from error
        self._cards = cards
        self._street = event.street
        self._street_action_index = 0
        self._next_event_index += 1
        return self._finish_boundary(
            boundary,
            event,
            wall_start_ns,
            next_street=event.street,
            terminal_at_entry=terminal_at_entry,
        )

    def _process_showdown_result(
        self,
        event: ShowdownResultEvent,
        boundary: object,
        wall_start_ns: int,
        terminal_at_entry: bool,
    ) -> DispatchOutcome:
        self._check_common(event)
        spine = self._spine
        assert spine is not None
        state = spine.state
        if state.is_terminal and state.terminal_reason is TerminalReason.FOLD:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if not state.is_terminal:
            if state.street is not BettingStreet.RIVER or not state.round_complete:
                raise _HandFailure(FailureCode.EVENT_ORDER)
        live = state.live_seats
        for seat, strength in enumerate(event.strengths):
            if (seat in live) != (strength is not None):
                raise _HandFailure(FailureCode.INVALID_EVENT)
        rank_types = {type(event.strengths[seat]) for seat in live}
        if len(rank_types) != 1:
            raise _HandFailure(FailureCode.INVALID_EVENT)
        if not state.is_terminal:
            # Policy selection is permanently disabled before terminal
            # strengths enter the separate settlement path.
            self._policy_disabled = True
            try:
                spine.advance_street()
            except (ClockInvalidError, ClockReversedError) as error:
                raise self._clock_hand_failure(error, wall_start_ns) from error
            except (TypeError, ValueError) as error:
                raise _HandFailure(FailureCode.INVALID_EVENT) from error
        self._policy_disabled = True

        self._strengths = event.strengths
        self._next_event_index += 1
        self._complete = True
        try:
            closed = self._outer.finish_transition_boundary(
                boundary, starts_controlled_action=False
            )
        except (ClockInvalidError, ClockReversedError) as error:
            self._boundary_open = False
            self._accounting_complete = False
            raise self._clock_hand_failure(error, wall_start_ns) from error
        self._boundary_open = False
        self._charge_interval(closed, terminal_at_entry=terminal_at_entry)
        return DispatchOutcome(status="accepted")

    # -- boundary and decision --------------------------------------------

    def _check_common(self, event: Event) -> None:
        if event.hand_id != self._hand_id:
            raise _HandFailure(FailureCode.EVENT_ORDER)
        if event.event_index != self._next_event_index:
            raise _HandFailure(FailureCode.EVENT_ORDER)

    def _finish_boundary(
        self,
        boundary: object,
        event: Event,
        wall_start_ns: int,
        *,
        next_street: str | None = None,
        terminal_at_entry: bool = False,
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
            closed = outer.finish_transition_boundary(
                boundary,
                starts_controlled_action=starts_action,
                controlled_action_public_state_sha256=(
                    public_betting_state_sha256(state) if starts_action else None
                ),
                next_street=next_street,
            )
        except (ClockInvalidError, ClockReversedError) as error:
            self._boundary_open = False
            self._accounting_complete = False
            raise self._clock_hand_failure(error, wall_start_ns) from error
        self._boundary_open = False
        if starts_action:
            # `closed` is this response's first valid outer snapshot; record
            # any violation it already establishes before the next fallible read.
            self._record_established(closed)
        if not starts_action:
            self._charge_interval(closed, terminal_at_entry=terminal_at_entry)
            if state.is_terminal and state.terminal_reason is TerminalReason.FOLD:
                self._complete = True
            return DispatchOutcome(status="accepted")
        return self._decide(event, wall_start_ns)

    def _decide(self, event: Event, wall_start_ns: int) -> DispatchOutcome:
        self._action_index += 1
        self._street_action_index += 1
        self._provider_context = None
        try:
            record = self._decide_inner(event, wall_start_ns, self._action_index)
        except _HandFailure as failure:
            if self._provider_context is not None and failure.decision is None:
                failure.decision = self._provider_record(
                    event, failure.timing, failure.code, failure.delivery_status)
            raise
        spine = self._spine
        assert spine is not None
        if spine.state.is_terminal and spine.state.terminal_reason is TerminalReason.FOLD:
            self._complete = True
        return DispatchOutcome(status="decided", decision=record)

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
            selection = _select_admitted_blueprint_action(
                source=self._blueprint,
                cards=cards,
                betting=state_before,
                decision=ticket.decision,
                prepared=self._prepared_blueprint,
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

        self._require_bound_selection(selection, cards, state_before, ticket.decision,
                                      wall_start_ns)

        action = selection.action
        if self._provider_binding is not None:
            action = self._select_provider(selection, cards, state_before, ticket.decision,
                                           action_index, wall_start_ns)
        selected = HandAction.from_betting_action(action)
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
        self._record_established(ready)
        work_cutoff_crossed = bool(self._known_cutoff) or ready.work_remaining_seconds <= 0.0
        if self._provider_binding is not None:
            self._require_provider_binding(wall_start_ns)
        if self._provider_context is not None and work_cutoff_crossed:
            self._provider_late()
            action = selection.action
            selected = HandAction.from_betting_action(action)
            envelope = replace(envelope, action=selected)

        try:
            emitted = spine.emit_controlled_action(
                candidate=None,
                fallback=action,
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
        receipt = self._publish(envelope, wall_start_ns)

        try:
            closing = outer.finish_action()
            emission_observed_ns = self._witness.last_returned_ns
        except (ClockInvalidError, ClockReversedError) as error:
            code = (
                FailureCode.CLOCK_REVERSED
                if issubclass(type(error), ClockReversedError)
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
                clock_error=error,
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

    def _require_provider_binding(self, wall_start_ns: int) -> None:
        try:
            identity = self._provider.identity
            valid = (type(self._provider) is self._provider_type
                     and type(identity) is ProviderIdentity
                     and type(identity.provider) is str and type(identity.config_sha256) is str
                     and (identity.provider, identity.config_sha256) == self._provider_binding
                     and type(self.strategy) is str and self.strategy == identity.provider
                     and type(self.source_manifest_sha256) is str
                     and self.source_manifest_sha256 == self._provider_source)
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except Exception:
            valid = False
        if not valid:
            raise _HandFailure(FailureCode.SOURCE_BINDING_MISMATCH,
                timing=self._interrupted_timing(FailureCode.SOURCE_BINDING_MISMATCH, wall_start_ns))

    def _select_provider(self, fallback, cards, betting, decision, action_index, wall_start_ns):
        self._require_provider_binding(wall_start_ns)
        try:
            observation = DecisionObservation(
                "pontius-decision-observation-v1", self._hand_id, action_index,
                cards, betting, decision, 0)
            ready = self._outer.snapshot()
            self._record_established(ready)
            observation = replace(observation, remaining_work_ns=max(
                0, min(14_000_000_000, int(ready.work_remaining_seconds * 1_000_000_000))))
            offered = replace(observation)
        except (ClockInvalidError, ClockReversedError) as error:
            raise self._clock_hand_failure(error, wall_start_ns) from error
        except (TypeError, ValueError, AttributeError, RecursionError) as error:
            raise _HandFailure(FailureCode.INVALID_DECISION_CONTEXT,
                timing=self._interrupted_timing(FailureCode.INVALID_DECISION_CONTEXT,
                                                wall_start_ns)) from error
        reason = "table_hit" if fallback.table_hit else "passive_default"
        result = Selection(None, "not_called", "provider_skipped_cutoff",
                           "blueprint_fallback", fallback.action)
        self._provider_context = (observation, fallback, result)
        if not self._known_cutoff:
            try:
                proposal = self._provider.propose(offered)
            except (ClockInvalidError, ClockReversedError) as error:
                self._provider_context = (observation, fallback, Selection(
                    None, "error", "provider_error", "blueprint_fallback", fallback.action))
                raise self._clock_hand_failure(error, wall_start_ns) from error
            except Exception:
                result = Selection(None, "error", "provider_error",
                                   "blueprint_fallback", fallback.action)
            else:
                try:
                    result = resolve_proposal(observation, proposal, fallback.action, reason)
                except (ClockInvalidError, ClockReversedError) as error:
                    raise self._clock_hand_failure(error, wall_start_ns) from error
                except (TypeError, ValueError, AttributeError, RecursionError) as error:
                    self._provider_context = None
                    raise _HandFailure(FailureCode.INVALID_DECISION_CONTEXT,
                        timing=self._interrupted_timing(FailureCode.INVALID_DECISION_CONTEXT,
                                                        wall_start_ns)) from error
            self._provider_context = (observation, fallback, result)
            self._require_provider_binding(wall_start_ns)
        return result.selected_action

    def _provider_late(self):
        observation, fallback, result = self._provider_context
        if result.provider_outcome != "not_called":
            result = replace(result, selection_reason="provider_late",
                             selection_origin="blueprint_fallback", selected_action=fallback.action)
            self._provider_context = (observation, fallback, result)

    def _provider_record(self, event, timing, failure_reason,
                         delivery_status=DeliveryStatus.ACCEPTED):
        observation, fallback, result = self._provider_context
        after = self._spine.state
        applied = after is not observation.betting and after != observation.betting
        selected = HandAction.from_betting_action(result.selected_action)
        return ProviderDecisionRecord(
            schema_version="pontius-provider-decision-v1", hand_id=self._hand_id,
            event_index=event.event_index, action_index=self._action_index,
            street_action_index=self._street_action_index, seat=self._controlled_seat,
            street=observation.betting.street.value,
            state_before_sha256=public_betting_state_sha256(observation.betting),
            state_after_sha256=public_betting_state_sha256(after) if applied else None,
            visible_cards_sha256=visible_cards_sha256(observation.cards),
            decision_sha256=observation.decision_sha256,
            source_manifest_sha256=self._provider_source,
            provider=self._provider_binding[0],
            config_sha256=self._provider_binding[1],
            fallback_blueprint_sha256=fallback.source_digest,
            fallback_action=HandAction.from_betting_action(fallback.action),
            fallback_reason="table_hit" if fallback.table_hit else "passive_default",
            proposal=result.proposal, provider_outcome=result.provider_outcome,
            selection_reason=result.selection_reason, selection_origin=result.selection_origin,
            selected_action=selected, applied_action=selected if applied else None,
            delivery_status=delivery_status,
            delivered_action=selected if delivery_status is DeliveryStatus.ACCEPTED else None,
            timing=timing, preparation_use=PreparationUseRecord(), failure_reason=failure_reason)

    def _require_bound_selection(
        self,
        selection: BlueprintSelection,
        cards: OneSeatCardState,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
        wall_start_ns: int,
    ) -> None:
        """The bound immutable policy is the only one permitted to answer.

        The canonical digest is captured once at hand start; comparing the
        digest the source reports for this selection catches a delegating
        source that swapped policies, without a second full-policy rehash.
        """

        def refuse() -> _HandFailure:
            return _HandFailure(
                FailureCode.SOURCE_BINDING_MISMATCH,
                timing=self._interrupted_timing(
                    FailureCode.SOURCE_BINDING_MISMATCH, wall_start_ns
                ),
            )

        if selection.source_digest != self._blueprint_digest:
            raise refuse()
        try:
            expected_key = BlueprintDecisionKey.from_state(
                cards=cards, betting=betting, decision=decision
            )
        except (TypeError, ValueError) as error:
            raise refuse() from error
        if selection.key != expected_key:
            raise refuse()
        if type(selection.table_hit) is not bool:
            raise refuse()
        if not selection.table_hit:
            if selection.action != passive_blueprint_action(decision):
                raise refuse()

    def _publish(self, envelope: ActionEnvelope, wall_start_ns: int) -> DeliveryReceipt:
        """Deliver once and require an exact acknowledgement, or fail closed."""

        try:
            receipt = self._mailbox.deliver(envelope)
        except MailboxRejectionError as error:
            raise _HandFailure(
                FailureCode.DELIVERY_REJECTED,
                delivery_status=DeliveryStatus.REJECTED,
                timing=self._interrupted_timing(FailureCode.DELIVERY_REJECTED, wall_start_ns),
            ) from error
        except BaseException as error:
            # The call began: no exception class can establish that
            # publication never happened, and it is never retried.
            raise _HandFailure(
                FailureCode.DELIVERY_AMBIGUOUS,
                delivery_status=DeliveryStatus.UNKNOWN,
                timing=self._interrupted_timing(FailureCode.DELIVERY_AMBIGUOUS, wall_start_ns),
            ) from error
        try:
            receipt = admit_receipt(receipt)
        except (TypeError, ValueError):
            receipt = None
        if (
            receipt is None
            or receipt.hand_id != envelope.hand_id
            or receipt.action_index != envelope.action_index
        ):
            raise _HandFailure(
                FailureCode.DELIVERY_AMBIGUOUS,
                delivery_status=DeliveryStatus.UNKNOWN,
                timing=self._interrupted_timing(FailureCode.DELIVERY_AMBIGUOUS, wall_start_ns),
            )
        self._accepted_deliveries += 1
        return receipt

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
        if self._provider_context is not None:
            return self._provider_record(event, timing, failure_reason)
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
            work_cutoff_crossed=self._known_cutoff,
            deadline_crossed=self._known_deadline,
        )

    def _clock_hand_failure(self, error: BaseException, wall_start_ns: int | None) -> _HandFailure:
        self._clock_dead = True
        self._accounting_complete = False
        code = (
            FailureCode.CLOCK_REVERSED
            if issubclass(type(error), ClockReversedError)
            else FailureCode.CLOCK_INVALID
        )
        return _HandFailure(code, timing=self._interrupted_timing(code, wall_start_ns),
                            clock_error=error)

    def _from_failure(self, failure: _HandFailure, event: Event | None) -> DispatchOutcome:
        self._dead = True
        if failure.timing is not None and failure.timing.status is TimingStatus.INTERRUPTED:
            self._interrupted_responses += 1
            self._accounting_complete = False
        return DispatchOutcome(
            status="failed",
            decision=failure.decision,
            failure=FailureRecord(
                hand_id=self._hand_id,
                event_index=None if event is None else event.event_index,
                action_index=(
                    self._action_index
                    if failure.timing is not None and self._action_index
                    else None
                ),
                code=failure.code,
                delivery_status=failure.delivery_status,
                delivered_action=failure.delivered_action,
                timing=failure.timing,
            ),
        )

    def _clock_reject(
        self,
        error: BaseException,
        *,
        wall_start_ns: int | None,
    ) -> DispatchOutcome:
        failure = self._clock_hand_failure(error, wall_start_ns)
        self._retain_error(error, otherwise=failure.code)
        return self._from_failure(failure, None)

    def _reject(self, code: FailureCode) -> DispatchOutcome:
        self._dead = True
        self.record(code)
        return DispatchOutcome(
            status="failed",
            failure=FailureRecord(
                hand_id=self._hand_id,
                event_index=None,
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
    "OperationFailed",
    "HandRuntime",
    "InvalidBlueprintEntryError",
    "InvalidDecisionContextError",
    "select_blueprint_action",
]
