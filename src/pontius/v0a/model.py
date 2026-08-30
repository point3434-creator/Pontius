"""Frozen event, envelope, receipt, record, and outcome values for v0a.

Every value validates exactly on construction (ADR-0485): exact types,
`bool` never satisfies an integer field, and no event can carry a clock
timestamp. Schema identity is the literal ``pontius-v0a-event-v1``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from enum import StrEnum
from hashlib import sha256

from ..holdem_cards import OneSeatCardState
from ..legal_decision_spine_v2 import ActionSelectionReasonV2
from ..no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    BettingActionKind,
)

EVENT_SCHEMA_VERSION = "pontius-v0a-event-v1"
STREET_NAMES: tuple[str, ...] = ("preflop", "flop", "turn", "river")
REVEAL_COUNTS: dict[str, int] = {"flop": 3, "turn": 1, "river": 1}
_ACTION_KINDS: tuple[str, ...] = ("fold", "check", "call", "raise")
_CARD_COUNT = 52
# Decision records quote the unchanged V2 reason enum, never free text.
SPINE_REASONS: tuple[str, ...] = tuple(reason.value for reason in ActionSelectionReasonV2)


class FailureCode(StrEnum):
    INVALID_EVENT = "invalid_event"
    EVENT_ORDER = "event_order"
    INVALID_DECISION_CONTEXT = "invalid_decision_context"
    INVALID_BLUEPRINT_ENTRY = "invalid_blueprint_entry"
    CLOCK_INVALID = "clock_invalid"
    CLOCK_REVERSED = "clock_reversed"
    WORK_CUTOFF_EXCEEDED = "work_cutoff_exceeded"
    ACTION_DEADLINE_EXCEEDED = "action_deadline_exceeded"
    DELIVERY_REJECTED = "delivery_rejected"
    DELIVERY_AMBIGUOUS = "delivery_ambiguous"
    TRACE_WRITE_FAILED = "trace_write_failed"
    TRACE_INVALID = "trace_invalid"
    SETTLEMENT_MISMATCH = "settlement_mismatch"
    SOURCE_BINDING_MISMATCH = "source_binding_mismatch"
    AUTHORITY_ABSENT = "authority_absent"


class DeliveryStatus(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    UNKNOWN = "unknown"


class SelectionReason(StrEnum):
    TABLE_HIT = "table_hit"
    PASSIVE_DEFAULT = "passive_default"


class TimingStatus(StrEnum):
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class MailboxRejectionError(RuntimeError):
    """The host mailbox refused an envelope before acceptance."""


def _require_exact_int(value: object, *, name: str, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _require_seat(value: object, *, name: str) -> int:
    seat = _require_exact_int(value, name=name, minimum=0)
    if seat >= SEAT_COUNT:
        raise ValueError(f"{name} must identify one of six seats")
    return seat


def _require_ascii_id(value: object, *, name: str) -> str:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be a nonempty ASCII string")
    if not value.isascii():
        raise ValueError(f"{name} must be ASCII")
    return value


def _require_street(value: object, *, name: str = "street") -> str:
    if type(value) is not str or value not in STREET_NAMES:
        raise ValueError(f"{name} must be one of {STREET_NAMES}")
    return value


def _require_card(value: object, *, name: str) -> int:
    card = _require_exact_int(value, name=name, minimum=0)
    if card >= _CARD_COUNT:
        raise ValueError(f"{name} must be an integer card in 0..51")
    return card


def _require_schema(value: object) -> str:
    if type(value) is not str or value != EVENT_SCHEMA_VERSION:
        raise ValueError(f"event schema version must be exactly {EVENT_SCHEMA_VERSION!r}")
    return EVENT_SCHEMA_VERSION


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _require_strength(value: object, *, name: str) -> int | tuple[int, ...]:
    if type(value) is int:
        return value
    if type(value) is tuple and value and all(type(part) is int for part in value):
        return value
    raise TypeError(f"{name} must be an exact integer or integer-tuple hand strength")


@dataclass(frozen=True, slots=True)
class HandAction:
    """One semantic action; ``raise_to`` is total street contribution."""

    kind: str
    raise_to: int | None

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in _ACTION_KINDS:
            raise ValueError(f"action kind must be one of {_ACTION_KINDS}")
        if self.kind == "raise":
            _require_exact_int(self.raise_to, name="raise-to amount", minimum=1)
        elif self.raise_to is not None:
            raise ValueError("only a raise action may carry a raise-to amount")

    def to_betting_action(self) -> BettingAction:
        if self.kind == "fold":
            return FOLD
        if self.kind == "check":
            return CHECK
        if self.kind == "call":
            return CALL
        assert self.raise_to is not None
        return BettingAction(BettingActionKind.RAISE, self.raise_to)

    @classmethod
    def from_betting_action(cls, action: BettingAction) -> HandAction:
        if not isinstance(action, BettingAction):
            raise TypeError("hand action requires an exact betting action")
        return cls(kind=action.kind.value, raise_to=action.raise_to)


@dataclass(frozen=True, slots=True)
class HandStartedEvent:
    hand_id: str
    event_index: int
    button: int
    controlled_seat: int
    starting_stacks: tuple[int, ...]
    small_blind: int
    big_blind: int
    private_cards: tuple[int, int]
    schema_version: str = EVENT_SCHEMA_VERSION
    kind = "hand_started"

    def __post_init__(self) -> None:
        _require_schema(self.schema_version)
        _require_ascii_id(self.hand_id, name="hand id")
        index = _require_exact_int(self.event_index, name="event index", minimum=0)
        if index != 0:
            raise ValueError("hand_started must carry event index zero")
        _require_seat(self.button, name="button")
        _require_seat(self.controlled_seat, name="controlled seat")
        if type(self.starting_stacks) is not tuple or len(self.starting_stacks) != SEAT_COUNT:
            raise ValueError("hand_started requires exactly six starting stacks")
        for seat, stack in enumerate(self.starting_stacks):
            _require_exact_int(stack, name=f"starting stack for seat {seat}", minimum=1)
        small = _require_exact_int(self.small_blind, name="small blind", minimum=1)
        big = _require_exact_int(self.big_blind, name="big blind", minimum=1)
        if small >= big:
            raise ValueError("small blind must be smaller than big blind")
        if type(self.private_cards) is not tuple or len(self.private_cards) != 2:
            raise ValueError("hand_started carries exactly the controlled two cards")
        first = _require_card(self.private_cards[0], name="first private card")
        second = _require_card(self.private_cards[1], name="second private card")
        if first >= second:
            raise ValueError("private cards must be two distinct ascending cards")


@dataclass(frozen=True, slots=True)
class OpponentActionEvent:
    hand_id: str
    event_index: int
    street: str
    seat: int
    action: HandAction
    schema_version: str = EVENT_SCHEMA_VERSION
    kind = "opponent_action"

    def __post_init__(self) -> None:
        _require_schema(self.schema_version)
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.event_index, name="event index", minimum=0)
        _require_street(self.street)
        _require_seat(self.seat, name="acting seat")
        if not isinstance(self.action, HandAction):
            raise TypeError("opponent action must be an exact hand action")


@dataclass(frozen=True, slots=True)
class StreetRevealedEvent:
    hand_id: str
    event_index: int
    street: str
    cards: tuple[int, ...]
    schema_version: str = EVENT_SCHEMA_VERSION
    kind = "street_revealed"

    def __post_init__(self) -> None:
        _require_schema(self.schema_version)
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.event_index, name="event index", minimum=0)
        if type(self.street) is not str or self.street not in REVEAL_COUNTS:
            raise ValueError("street reveal must name flop, turn, or river")
        expected = REVEAL_COUNTS[self.street]
        if type(self.cards) is not tuple or len(self.cards) != expected:
            raise ValueError(f"{self.street} reveals exactly {expected} new public cards")
        cards = tuple(
            _require_card(card, name=f"revealed card {position}")
            for position, card in enumerate(self.cards)
        )
        if len(set(cards)) != len(cards):
            raise ValueError("revealed cards must be distinct")


@dataclass(frozen=True, slots=True)
class ShowdownResultEvent:
    hand_id: str
    event_index: int
    strengths: tuple[int | tuple[int, ...] | None, ...]
    schema_version: str = EVENT_SCHEMA_VERSION
    kind = "showdown_result"

    def __post_init__(self) -> None:
        _require_schema(self.schema_version)
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.event_index, name="event index", minimum=0)
        if type(self.strengths) is not tuple or len(self.strengths) != SEAT_COUNT:
            raise ValueError("showdown result carries exactly six strength entries")
        for seat, strength in enumerate(self.strengths):
            if strength is not None:
                _require_strength(strength, name=f"strength for seat {seat}")


Event = HandStartedEvent | OpponentActionEvent | StreetRevealedEvent | ShowdownResultEvent


@dataclass(frozen=True, slots=True)
class ActionEnvelope:
    """Prebuilt immutable action the mailbox accepts at most once."""

    hand_id: str
    action_index: int
    seat: int
    street: str
    action: HandAction

    def __post_init__(self) -> None:
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.action_index, name="action index", minimum=1)
        _require_seat(self.seat, name="acting seat")
        _require_street(self.street)
        if not isinstance(self.action, HandAction):
            raise TypeError("envelope action must be an exact hand action")


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    hand_id: str
    action_index: int

    def __post_init__(self) -> None:
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.action_index, name="action index", minimum=1)


_EVENT_TYPES = (HandStartedEvent, OpponentActionEvent, StreetRevealedEvent, ShowdownResultEvent)
_INGRESS_RECORD_TYPES = (*_EVENT_TYPES, HandAction, ActionEnvelope, DeliveryReceipt)


def _copy_ingress_value(value: object) -> object:
    """Own a closed exact graph before any consumer can produce effects."""
    kind = type(value)
    if value is None or kind is int or kind is str:
        return value
    if kind is tuple:
        return tuple(_copy_ingress_value(item) for item in value)
    if any(kind is allowed for allowed in _INGRESS_RECORD_TYPES):
        return kind(**{field.name: _copy_ingress_value(getattr(value, field.name))
                       for field in fields(kind)})
    raise TypeError("ingress requires an exact immutable value graph")


def admit_event(value: object) -> Event:
    if not any(type(value) is kind for kind in _EVENT_TYPES):
        raise TypeError("unsupported event type")
    return _copy_ingress_value(value)


def admit_envelope(value: object) -> ActionEnvelope:
    if type(value) is not ActionEnvelope:
        raise TypeError("unsupported envelope type")
    return _copy_ingress_value(value)


def admit_receipt(value: object) -> DeliveryReceipt:
    if type(value) is not DeliveryReceipt:
        raise TypeError("unsupported acknowledgement type")
    return _copy_ingress_value(value)


class ActionMailbox:
    """Host-owned value-only mailbox; one acceptance per (hand, action)."""

    def __init__(self) -> None:
        self._accepted: dict[tuple[str, int], ActionEnvelope] = {}

    @property
    def accepted(self) -> dict[tuple[str, int], ActionEnvelope]:
        return dict(self._accepted)

    def deliver(self, envelope: ActionEnvelope) -> DeliveryReceipt:
        try:
            envelope = admit_envelope(envelope)
            receipt = DeliveryReceipt(hand_id=envelope.hand_id, action_index=envelope.action_index)
        except (TypeError, ValueError):
            raise MailboxRejectionError("mailbox requires a valid exact envelope") from None
        key = (envelope.hand_id, envelope.action_index)
        if key in self._accepted:
            raise MailboxRejectionError(
                f"action {key[1]} of hand {key[0]!r} was already accepted"
            )
        self._accepted[key] = envelope
        return receipt


@dataclass(frozen=True, slots=True)
class PreparationUseRecord:
    """Schema-v1 honest absence: no producer, no artifacts, zero credit."""

    producer_status: str = "producer_absent"
    artifact_sha256s: tuple[str, ...] = ()
    credited_seconds: int = 0

    def __post_init__(self) -> None:
        if self.producer_status != "producer_absent":
            raise ValueError("schema v1 preparation status is exactly producer_absent")
        if self.artifact_sha256s != ():
            raise ValueError("schema v1 preparation artifacts are exactly empty")
        if type(self.credited_seconds) is not int or self.credited_seconds != 0:
            raise ValueError("schema v1 credited seconds are exactly zero")


def _require_seconds(value: object, *, name: str) -> float:
    if type(value) is not float or value < 0.0 or value != value or value in (
        float("inf"),
    ):
        raise ValueError(f"{name} must be a finite nonnegative float")
    return value


@dataclass(frozen=True, slots=True)
class TimingRecord:
    status: TimingStatus
    interruption_reason: FailureCode | None
    wall_start_ns: int
    last_valid_observation_ns: int
    emission_observed_ns: int | None
    elapsed_ns: int | None
    response_compute_seconds: float | None
    response_uninstrumented_seconds: float | None
    work_cutoff_crossed: bool | None
    deadline_crossed: bool | None

    def __post_init__(self) -> None:
        if not isinstance(self.status, TimingStatus):
            raise TypeError("timing status must be exact")
        _require_exact_int(self.wall_start_ns, name="wall start", minimum=0)
        _require_exact_int(self.last_valid_observation_ns, name="last valid observation", minimum=0)
        if self.last_valid_observation_ns < self.wall_start_ns:
            raise ValueError("last valid observation predates the wall start")
        if self.status is TimingStatus.COMPLETED:
            if self.interruption_reason is not None:
                raise ValueError("completed timing carries no interruption reason")
            emission = _require_exact_int(
                self.emission_observed_ns, name="emission observation", minimum=0
            )
            if self.last_valid_observation_ns != emission:
                raise ValueError("completed last valid observation equals the emission")
            elapsed = _require_exact_int(self.elapsed_ns, name="elapsed nanoseconds", minimum=0)
            if elapsed != emission - self.wall_start_ns:
                raise ValueError("elapsed nanoseconds are exact integer subtraction")
            _require_seconds(self.response_compute_seconds, name="response compute seconds")
            _require_seconds(
                self.response_uninstrumented_seconds, name="response uninstrumented seconds"
            )
            for flag in (self.work_cutoff_crossed, self.deadline_crossed):
                if type(flag) is not bool:
                    raise TypeError("completed timing flags must be exact booleans")
            return
        if not isinstance(self.interruption_reason, FailureCode):
            raise TypeError("interrupted timing names its typed failure")
        for name, value in (
            ("emission observation", self.emission_observed_ns),
            ("elapsed nanoseconds", self.elapsed_ns),
            ("response compute seconds", self.response_compute_seconds),
            ("response uninstrumented seconds", self.response_uninstrumented_seconds),
        ):
            if value is not None:
                raise ValueError(f"interrupted timing has null {name}")
        for name, flag in (
            ("work-cutoff flag", self.work_cutoff_crossed),
            ("deadline flag", self.deadline_crossed),
        ):
            if flag is not None and type(flag) is not bool:
                raise TypeError(f"interrupted {name} is an exact boolean or null")
            if flag is False:
                raise ValueError(f"interrupted {name} is never a false claim; use null")


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    hand_id: str
    event_index: int
    action_index: int
    street_action_index: int
    seat: int
    street: str
    state_before_sha256: str
    state_after_sha256: str
    visible_cards_sha256: str
    blueprint_sha256: str
    selected_action: HandAction
    selection_reason: SelectionReason
    spine_reason: str
    timing: TimingRecord
    preparation_use: PreparationUseRecord
    failure_reason: FailureCode | None

    def __post_init__(self) -> None:
        _require_ascii_id(self.hand_id, name="hand id")
        _require_exact_int(self.event_index, name="event index", minimum=0)
        _require_exact_int(self.action_index, name="action index", minimum=1)
        _require_exact_int(self.street_action_index, name="street action index", minimum=1)
        _require_seat(self.seat, name="acting seat")
        _require_street(self.street)
        for name, digest in (
            ("before-state digest", self.state_before_sha256),
            ("after-state digest", self.state_after_sha256),
            ("visible-cards digest", self.visible_cards_sha256),
            ("blueprint digest", self.blueprint_sha256),
        ):
            _require_sha256(digest, name=name)
        if not isinstance(self.selected_action, HandAction):
            raise TypeError("selected action must be an exact hand action")
        if not isinstance(self.selection_reason, SelectionReason):
            raise TypeError("selection reason must be exact")
        if self.spine_reason not in SPINE_REASONS:
            raise ValueError(f"spine reason must be one of {SPINE_REASONS}")
        if not isinstance(self.timing, TimingRecord):
            raise TypeError("decision timing must be an exact timing record")
        if not isinstance(self.preparation_use, PreparationUseRecord):
            raise TypeError("preparation use must be an exact record")
        if self.failure_reason is not None and not isinstance(self.failure_reason, FailureCode):
            raise TypeError("failure reason must be a typed code or null")


@dataclass(frozen=True, slots=True)
class FailureRecord:
    hand_id: str | None
    event_index: int | None
    action_index: int | None
    code: FailureCode
    delivery_status: DeliveryStatus
    delivered_action: HandAction | None
    timing: TimingRecord | None

    def __post_init__(self) -> None:
        if self.hand_id is not None:
            _require_ascii_id(self.hand_id, name="hand id")
        if self.event_index is not None:
            _require_exact_int(self.event_index, name="event index", minimum=0)
        if self.action_index is not None:
            _require_exact_int(self.action_index, name="action index", minimum=1)
        if not isinstance(self.code, FailureCode):
            raise TypeError("failure code must be typed")
        if not isinstance(self.delivery_status, DeliveryStatus):
            raise TypeError("delivery status must be exact")
        if self.delivered_action is not None:
            if not isinstance(self.delivered_action, HandAction):
                raise TypeError("delivered action must be an exact hand action")
            if self.delivery_status is not DeliveryStatus.ACCEPTED:
                raise ValueError("delivered action requires known acceptance")
        if self.timing is not None and not isinstance(self.timing, TimingRecord):
            raise TypeError("failure timing must be an exact timing record or null")


@dataclass(frozen=True, slots=True)
class PotRecord:
    amount: int
    seats: tuple[int, ...]

    def __post_init__(self) -> None:
        _require_exact_int(self.amount, name="pot amount", minimum=1)
        if (
            type(self.seats) is not tuple
            or not self.seats
            or tuple(sorted(set(self.seats))) != self.seats
        ):
            raise ValueError("pot seats must be sorted unique eligible seats")
        for seat in self.seats:
            _require_seat(seat, name="pot seat")


@dataclass(frozen=True, slots=True)
class SettlementRecord:
    payouts: tuple[int, ...]
    final_stacks: tuple[int, ...]
    pots: tuple[PotRecord, ...]

    def __post_init__(self) -> None:
        for name, values in (("payouts", self.payouts), ("final stacks", self.final_stacks)):
            if type(values) is not tuple or len(values) != SEAT_COUNT:
                raise ValueError(f"settlement {name} must cover exactly six seats")
            for seat, value in enumerate(values):
                _require_exact_int(value, name=f"{name} for seat {seat}", minimum=0)
        if type(self.pots) is not tuple:
            raise TypeError("settlement pots must be an immutable tuple")
        for pot in self.pots:
            if not isinstance(pot, PotRecord):
                raise TypeError("settlement pots must be exact pot records")


def visible_cards_sha256(cards: OneSeatCardState) -> str:
    """Canonical visible-card identity: controlled view only, never hidden cards."""

    if not isinstance(cards, OneSeatCardState):
        raise TypeError("visible-card digest requires a one-seat card state")
    payload = {
        "board": list(cards.board),
        "controlled_seat": cards.controlled_seat,
        "private_cards": list(cards.private_hand),
        "street": cards.street.value,
    }
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("ascii")).hexdigest()
