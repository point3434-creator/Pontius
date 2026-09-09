"""Immutable future-blind action lookup for the complete-hand reference gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from secrets import randbelow

from .holdem_cards import Card, HoleCards, OneSeatCardState
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    BettingActionKind,
    BettingActionRecord,
    BettingStreet,
    LegalBettingDecision,
    NoLimitBettingState,
)

_HistoryAtom = tuple[str, int, str, int | None, int, bool, int | None, int]


@dataclass(frozen=True, slots=True)
class BlueprintDecisionKey:
    """Exact one-seat information key with no future or opponent-private cards."""

    controlled_seat: int
    private_hand: HoleCards
    board: tuple[Card, ...]
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
    public_history: tuple[_HistoryAtom, ...]

    @classmethod
    def from_state(
        cls,
        *,
        cards: OneSeatCardState,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> BlueprintDecisionKey:
        if not isinstance(cards, OneSeatCardState):
            raise TypeError("blueprint key requires a one-seat card state")
        if not isinstance(betting, NoLimitBettingState):
            raise TypeError("blueprint key requires exact no-limit betting state")
        if not isinstance(decision, LegalBettingDecision):
            raise TypeError("blueprint key requires an exact legal decision")
        if cards.street is not betting.street or decision.street is not betting.street:
            raise ValueError("card, betting, and decision streets must agree")
        if betting.acting_seat != cards.controlled_seat:
            raise ValueError("blueprint key may be built only for the controlled actor")
        if decision.acting_seat != cards.controlled_seat:
            raise ValueError("legal decision belongs to a different seat")
        if decision != betting.legal_decision():
            raise ValueError(
                "legal decision disagrees with the complete public betting state"
            )

        history = tuple(
            (
                record.street.value,
                record.seat,
                record.action.kind.value,
                record.action.raise_to,
                record.chips_committed,
                record.full_raise,
                record.uncalled_return_seat,
                record.uncalled_return_chips,
            )
            for record in betting.history
        )
        return cls(
            controlled_seat=cards.controlled_seat,
            private_hand=cards.private_hand,
            board=cards.board,
            button=betting.button,
            small_blind=betting.small_blind,
            big_blind=betting.big_blind,
            street=betting.street,
            starting_stacks=betting.starting_stacks,
            stacks=betting.stacks,
            total_contributions=betting.total_contributions,
            street_contributions=betting.street_contributions,
            folded=betting.folded,
            pending_seats=betting.pending_seats,
            last_full_raise_size=betting.last_full_raise_size,
            acted_at_bet=betting.acted_at_bet,
            public_history=history,
        )

    def __post_init__(self) -> None:
        if (
            isinstance(self.controlled_seat, bool)
            or not isinstance(self.controlled_seat, int)
            or self.controlled_seat not in range(SEAT_COUNT)
        ):
            raise ValueError("blueprint controlled seat must identify one of six seats")
        if not isinstance(self.street, BettingStreet):
            raise TypeError("blueprint street must be canonical")
        visible = OneSeatCardState(
            controlled_seat=self.controlled_seat,
            private_hand=self.private_hand,
            street=self.street,
            board=self.board,
        )
        object.__setattr__(self, "private_hand", visible.private_hand)
        object.__setattr__(self, "board", visible.board)
        for name, seat in (("button", self.button),):
            if (
                isinstance(seat, bool)
                or not isinstance(seat, int)
                or seat not in range(SEAT_COUNT)
            ):
                raise ValueError(f"blueprint {name} must identify one of six seats")
        for name, chips in (
            ("small blind", self.small_blind),
            ("big blind", self.big_blind),
            ("last full raise size", self.last_full_raise_size),
        ):
            if isinstance(chips, bool) or not isinstance(chips, int) or chips <= 0:
                raise ValueError(f"blueprint {name} must be a positive chip count")
        if self.small_blind >= self.big_blind:
            raise ValueError("blueprint small blind must be smaller than big blind")
        for name, values, expected in (
            ("starting stacks", self.starting_stacks, SEAT_COUNT),
            ("stacks", self.stacks, SEAT_COUNT),
            ("total contributions", self.total_contributions, SEAT_COUNT),
            ("street contributions", self.street_contributions, SEAT_COUNT),
            ("fold flags", self.folded, SEAT_COUNT),
            ("acted-at-bet", self.acted_at_bet, SEAT_COUNT),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"blueprint {name} must be an immutable tuple")
            if len(values) != expected:
                raise ValueError(f"blueprint {name} has the wrong width")
        for name, values in (
            ("board", self.board),
            ("pending seats", self.pending_seats),
            ("public history", self.public_history),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"blueprint {name} must be an immutable tuple")
        for name, values, positive in (
            ("starting stacks", self.starting_stacks, True),
            ("stacks", self.stacks, False),
            ("total contributions", self.total_contributions, False),
            ("street contributions", self.street_contributions, False),
        ):
            lower_bound = 1 if positive else 0
            if any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < lower_bound
                for value in values
            ):
                qualifier = "positive" if positive else "nonnegative"
                raise ValueError(f"blueprint {name} must be {qualifier} chip counts")
        if any(not isinstance(value, bool) for value in self.folded):
            raise TypeError("blueprint fold flags must be boolean")
        if len(set(self.pending_seats)) != len(self.pending_seats) or any(
            isinstance(seat, bool)
            or not isinstance(seat, int)
            or seat not in range(SEAT_COUNT)
            for seat in self.pending_seats
        ):
            raise ValueError("blueprint pending seats must be unique canonical seats")
        if any(
            value is not None
            and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            )
            for value in self.acted_at_bet
        ):
            raise ValueError("blueprint acted-at-bet values must be nonnegative or null")
        for atom in self.public_history:
            if not isinstance(atom, tuple):
                raise TypeError("blueprint public-history atoms must be immutable tuples")
            if len(atom) != 8:
                raise ValueError("blueprint public-history atom has the wrong width")
            (
                street,
                seat,
                kind,
                raise_amount,
                chips_committed,
                full_raise,
                return_seat,
                return_chips,
            ) = atom
            try:
                semantic_street = BettingStreet(street)
                semantic_kind = BettingActionKind(kind)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "blueprint public history contains a nonsemantic label"
                ) from error
            BettingActionRecord(
                street=semantic_street,
                seat=seat,
                action=BettingAction(semantic_kind, raise_amount),
                chips_committed=chips_committed,
                full_raise=full_raise,
                uncalled_return_seat=return_seat,
                uncalled_return_chips=return_chips,
            )

    def canonical_bytes(self) -> bytes:
        payload = {
            "acted_at_bet": self.acted_at_bet,
            "big_blind": self.big_blind,
            "board": self.board,
            "button": self.button,
            "controlled_seat": self.controlled_seat,
            "folded": self.folded,
            "last_full_raise_size": self.last_full_raise_size,
            "pending_seats": self.pending_seats,
            "private_hand": self.private_hand,
            "public_history": self.public_history,
            "small_blind": self.small_blind,
            "stacks": self.stacks,
            "starting_stacks": self.starting_stacks,
            "street": self.street.value,
            "street_contributions": self.street_contributions,
            "total_contributions": self.total_contributions,
            "version": "blueprint-decision-key-v1",
        }
        return json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class WeightedBlueprintAction:
    """Exact positive integer masses over distinct semantic actions.

    Total mass is the denominator. Zero-probability actions are omitted.
    Sorting makes selection order and serialization independent of input order.
    """

    choices: tuple[tuple[BettingAction, int], ...]

    def __post_init__(self) -> None:
        if type(self.choices) is not tuple or not self.choices:
            raise ValueError("weighted blueprint choices must be a nonempty tuple")
        for choice in self.choices:
            if type(choice) is not tuple or len(choice) != 2:
                raise TypeError("weighted choice must be an action/weight pair")
            action, weight = choice
            if type(action) is not BettingAction:
                raise TypeError("weighted choice requires an exact semantic action")
            if type(weight) is not int or weight <= 0:
                raise ValueError("weighted choice requires a positive integer weight")
        if len({action for action, _ in self.choices}) != len(self.choices):
            raise ValueError("weighted blueprint contains duplicate actions")
        if sum(weight for _, weight in self.choices) >= 2**63:
            raise ValueError("weighted blueprint total must be smaller than 2**63")
        ordered = tuple(sorted(self.choices, key=lambda pair: (
            pair[0].kind.value, pair[0].raise_to or 0)))
        object.__setattr__(self, "choices", ordered)

    def sample(self) -> BettingAction:
        """Draw once per selection; system randomness is never derived from cards."""
        if len(self.choices) == 1:
            return self.choices[0][0]
        total = sum(weight for _, weight in self.choices)
        ticket = randbelow(total)
        if type(ticket) is not int or not 0 <= ticket < total:
            raise ValueError("random ticket is outside the weighted distribution")
        for action, weight in self.choices:
            if ticket < weight:
                return action
            ticket -= weight
        raise AssertionError("weighted selection exhausted a validated distribution")


@dataclass(frozen=True, slots=True)
class BlueprintActionEntry:
    key: BlueprintDecisionKey
    action: BettingAction | WeightedBlueprintAction

    def __post_init__(self) -> None:
        if not isinstance(self.key, BlueprintDecisionKey):
            raise TypeError("blueprint entry key must be exact and future-blind")
        if not isinstance(self.action, (BettingAction, WeightedBlueprintAction)):
            raise TypeError("blueprint entry action must be semantic")


@dataclass(frozen=True, slots=True)
class BlueprintSelection:
    key: BlueprintDecisionKey
    action: BettingAction
    table_hit: bool
    source_digest: str


def passive_blueprint_action(decision: LegalBettingDecision) -> BettingAction:
    """Return the deliberately weak total passive action for one decision."""

    if decision.can_check:
        return CHECK
    if decision.can_call:
        return CALL
    if decision.can_fold:
        return FOLD
    raise AssertionError("an on-clock legal decision has no passive action")


def require_legal_blueprint_action(
    action: BettingAction | WeightedBlueprintAction,
    decision: LegalBettingDecision,
) -> None:
    """Fail closed unless one semantic action is inside the exact decision."""

    if isinstance(action, WeightedBlueprintAction):
        for candidate, _ in action.choices:
            require_legal_blueprint_action(candidate, decision)
        return
    if action.kind not in decision.action_kinds:
        raise ValueError("immutable blueprint selected an unavailable action kind")
    if action.kind is BettingActionKind.RAISE:
        bounds = decision.raise_bounds
        assert action.raise_to is not None
        if (
            bounds is None
            or action.raise_to < bounds.minimum_raise_to
            or action.raise_to > bounds.maximum_raise_to
        ):
            raise ValueError("immutable blueprint raise-to amount is not legal")


@dataclass(frozen=True, slots=True)
class ImmutableBlueprintActionSource:
    """Digest-bound exact table with a deliberately weak passive default."""

    source_id: str
    entries: tuple[BlueprintActionEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("immutable blueprint source id must be nonempty")
        if not isinstance(self.entries, tuple):
            raise TypeError("immutable blueprint entries must be an immutable tuple")
        if any(not isinstance(entry, BlueprintActionEntry) for entry in self.entries):
            raise TypeError("immutable blueprint contains a non-entry value")
        keys = tuple(entry.key for entry in self.entries)
        if len(set(keys)) != len(keys):
            raise ValueError("immutable blueprint contains a duplicate decision key")

    @property
    def uses_mixed_actions(self) -> bool:
        return any(isinstance(entry.action, WeightedBlueprintAction) for entry in self.entries)

    def canonical_bytes(self) -> bytes:
        if self.uses_mixed_actions:
            rows = []
            for entry in self.entries:
                choices = (entry.action.choices if isinstance(entry.action, WeightedBlueprintAction)
                           else ((entry.action, 1),))
                rows.append((entry.key.digest, tuple(
                    (action.kind.value, action.raise_to, weight) for action, weight in choices)))
            return json.dumps(dict(entries=sorted(rows), source_id=self.source_id,
                                   version="immutable-reference-blueprint-v2"),
                              allow_nan=False, separators=(",", ":"),
                              sort_keys=True).encode("ascii")
        entries = sorted(
            (
                entry.key.digest,
                entry.action.kind.value,
                entry.action.raise_to,
            )
            for entry in self.entries
        )
        payload = {
            "entries": entries,
            "source_id": self.source_id,
            "version": "immutable-reference-blueprint-v1",
        }
        return json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

    def action_for(
        self,
        *,
        cards: OneSeatCardState,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> BlueprintSelection:
        key = BlueprintDecisionKey.from_state(
            cards=cards,
            betting=betting,
            decision=decision,
        )
        matching = tuple(entry for entry in self.entries if entry.key == key)
        if len(matching) > 1:
            raise AssertionError("validated blueprint lookup is not unique")
        table_hit = bool(matching)
        action = (
            matching[0].action
            if table_hit
            else passive_blueprint_action(decision)
        )
        require_legal_blueprint_action(action, decision)
        if isinstance(action, WeightedBlueprintAction):
            action = action.sample()
        return BlueprintSelection(
            key=key,
            action=action,
            table_hit=table_hit,
            source_digest=self.digest,
        )


__all__ = [
    "BlueprintActionEntry",
    "BlueprintDecisionKey",
    "BlueprintSelection",
    "ImmutableBlueprintActionSource",
    "WeightedBlueprintAction",
    "passive_blueprint_action",
    "require_legal_blueprint_action",
]
