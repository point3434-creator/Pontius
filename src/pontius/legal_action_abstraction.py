"""Exact-legality integer action lattice and off-tree projection.

The lattice is deliberately small, but every retained action is an exact
``BettingAction`` validated against the complete six-seat no-limit state.  Raw
pot-fraction targets retain explicit clipping and deduplication provenance.
Observed off-tree raises map to adjacent retained raises with exact rational
weights; the projection never mutates public betting state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from itertools import pairwise
from math import gcd

from .immutable_blueprint import require_legal_blueprint_action
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingAction,
    BettingActionKind,
    BettingStreet,
    LegalBettingDecision,
    NoLimitBettingState,
    raise_to,
)

_ALGORITHM_VERSION = "exact-legal-pot-fraction-lattice-v1"


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


@dataclass(frozen=True, slots=True)
class PotFraction:
    """One exact positive pot fraction used only for sizing."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="pot-fraction numerator",
            positive=True,
        )
        denominator = _require_integer(
            self.denominator,
            label="pot-fraction denominator",
            positive=True,
        )
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


DEFAULT_POT_FRACTIONS: tuple[PotFraction, ...] = (
    PotFraction(1, 3),
    PotFraction(2, 3),
    PotFraction(1, 1),
    PotFraction(3, 2),
)

COLLISION_REPAIR_CORE_POT_FRACTIONS: tuple[PotFraction, ...] = (
    PotFraction(1, 4),
    PotFraction(1, 2),
    PotFraction(1, 1),
)
COLLISION_REPAIR_PRIMARY_OVERBET = PotFraction(2, 1)
COLLISION_REPAIR_FALLBACK_OVERBET = PotFraction(3, 2)


class RaiseSizeOriginKind(StrEnum):
    MINIMUM = "minimum"
    POT_FRACTION = "pot_fraction"
    COLLISION_REPAIR_OVERBET = "collision_repair_overbet"
    CAPACITY_FILLING_POT_ODDS = "capacity_filling_pot_odds"
    MAXIMUM_CONTESTABLE = "maximum_contestable"
    ALL_IN = "all_in"


class ClipDirection(StrEnum):
    NONE = "none"
    LOW = "low"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ExactPotOddsDistance:
    """One positive exact distance in the bounded responder pot-odds axis."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="pot-odds-distance numerator",
            positive=True,
        )
        denominator = _require_integer(
            self.denominator,
            label="pot-odds-distance denominator",
            positive=True,
        )
        if numerator >= denominator:
            raise ValueError("pot-odds distance must lie strictly inside (0, 1)")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class CapacityFillingSelection:
    """Exact maximin refill selected between two retained raise amounts."""

    raise_to: int
    left_raise_to: int
    right_raise_to: int
    score: ExactPotOddsDistance

    def __post_init__(self) -> None:
        raise_to_amount = _require_integer(
            self.raise_to,
            label="capacity-filling raise-to",
            positive=True,
        )
        left = _require_integer(
            self.left_raise_to,
            label="capacity-filling left bracket",
            positive=True,
        )
        right = _require_integer(
            self.right_raise_to,
            label="capacity-filling right bracket",
            positive=True,
        )
        if not left < raise_to_amount < right:
            raise ValueError("capacity-filling selection must lie inside its bracket")
        if not isinstance(self.score, ExactPotOddsDistance):
            raise TypeError("capacity-filling score must be an exact pot-odds distance")


@dataclass(frozen=True, slots=True)
class RaiseSizeOrigin:
    """One raw semantic source for a retained exact raise amount."""

    kind: RaiseSizeOriginKind
    raw_raise_to: int
    projected_raise_to: int
    clip: ClipDirection
    pot_fraction: PotFraction | None = None
    collision_repair_triggered: bool | None = None
    capacity_refill_rank: int | None = None
    capacity_refill: CapacityFillingSelection | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RaiseSizeOriginKind):
            raise TypeError("raise-size origin kind must be semantic")
        raw = _require_integer(
            self.raw_raise_to,
            label="raw raise-to",
            positive=True,
        )
        projected = _require_integer(
            self.projected_raise_to,
            label="projected raise-to",
            positive=True,
        )
        if not isinstance(self.clip, ClipDirection):
            raise TypeError("raise-size clip direction must be semantic")
        fraction_kinds = (
            RaiseSizeOriginKind.POT_FRACTION,
            RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET,
        )
        if (self.kind in fraction_kinds) != (self.pot_fraction is not None):
            raise ValueError("only a fractional raise origin may carry a fraction")
        if self.pot_fraction is not None and not isinstance(
            self.pot_fraction,
            PotFraction,
        ):
            raise TypeError("raise-size origin fraction must be exact")
        if self.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET:
            if not isinstance(self.collision_repair_triggered, bool):
                raise TypeError(
                    "collision-repair provenance requires an exact branch decision"
                )
        elif self.collision_repair_triggered is not None:
            raise ValueError(
                "only collision-repair provenance may carry a branch decision"
            )
        if self.kind is RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS:
            rank = _require_integer(
                self.capacity_refill_rank,
                label="capacity-refill rank",
                positive=True,
            )
            if not isinstance(self.capacity_refill, CapacityFillingSelection):
                raise TypeError("capacity refill requires exact selection provenance")
            if (
                raw != self.capacity_refill.raise_to
                or projected != self.capacity_refill.raise_to
                or self.clip is not ClipDirection.NONE
            ):
                raise ValueError("capacity refill changed its exact selected raise")
            object.__setattr__(self, "capacity_refill_rank", rank)
        elif self.capacity_refill_rank is not None or self.capacity_refill is not None:
            raise ValueError("only a capacity refill may carry refill provenance")
        if self.clip is ClipDirection.NONE and raw != projected:
            raise ValueError("an unclipped origin changed its raise amount")
        if self.clip is ClipDirection.LOW and raw >= projected:
            raise ValueError("a low-clipped origin did not move upward")
        if self.clip is ClipDirection.HIGH and raw <= projected:
            raise ValueError("a high-clipped origin did not move downward")


@dataclass(frozen=True, slots=True)
class AbstractRaiseSize:
    """One retained exact raise action with every deduplicated origin."""

    action: BettingAction
    origins: tuple[RaiseSizeOrigin, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.action, BettingAction):
            raise TypeError("abstract raise size requires a semantic action")
        if self.action.kind is not BettingActionKind.RAISE:
            raise ValueError("abstract raise size requires a raise action")
        if not isinstance(self.origins, tuple) or not self.origins:
            raise TypeError("abstract raise origins must be a nonempty immutable tuple")
        if any(not isinstance(origin, RaiseSizeOrigin) for origin in self.origins):
            raise TypeError("abstract raise contains a nonsemantic origin")
        assert self.action.raise_to is not None
        if any(
            origin.projected_raise_to != self.action.raise_to
            for origin in self.origins
        ):
            raise ValueError("abstract raise origin names a different exact amount")
        if len(set(self.origins)) != len(self.origins):
            raise ValueError("abstract raise repeats an identical origin")

    def has_origin(self, kind: RaiseSizeOriginKind) -> bool:
        if not isinstance(kind, RaiseSizeOriginKind):
            raise TypeError("raise-size origin query must be semantic")
        return any(origin.kind is kind for origin in self.origins)


@dataclass(frozen=True, slots=True)
class ExactProjectionWeight:
    """One reduced interpolation weight, distinct from policy probability."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="projection-weight numerator",
        )
        denominator = _require_integer(
            self.denominator,
            label="projection-weight denominator",
            positive=True,
        )
        if numerator > denominator:
            raise ValueError("projection weight must lie in [0, 1]")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class ActionProjectionAtom:
    action: BettingAction
    weight: ExactProjectionWeight

    def __post_init__(self) -> None:
        if not isinstance(self.action, BettingAction):
            raise TypeError("projection atom action must be semantic")
        if not isinstance(self.weight, ExactProjectionWeight):
            raise TypeError("projection atom weight must be semantic")
        if self.weight.numerator <= 0:
            raise ValueError("projection atoms must retain positive mass")


@dataclass(frozen=True, slots=True)
class OffTreeActionProjection:
    """Exact one- or two-atom projection of one legal public action."""

    exact_action: BettingAction
    abstraction_digest: str
    source_digest: str
    atoms: tuple[ActionProjectionAtom, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.exact_action, BettingAction):
            raise TypeError("off-tree projection requires a semantic exact action")
        _require_digest(self.abstraction_digest, label="action abstraction digest")
        _require_digest(self.source_digest, label="action-abstraction source digest")
        if not isinstance(self.atoms, tuple) or len(self.atoms) not in (1, 2):
            raise ValueError("off-tree projection requires one or two immutable atoms")
        if any(not isinstance(atom, ActionProjectionAtom) for atom in self.atoms):
            raise TypeError("off-tree projection contains a nonsemantic atom")
        if len({atom.action for atom in self.atoms}) != len(self.atoms):
            raise ValueError("off-tree projection repeats an action")
        if sum((atom.weight.fraction for atom in self.atoms), start=Fraction(0)) != 1:
            raise ValueError("off-tree projection weights do not sum exactly to one")

        if self.exact_action.kind is not BettingActionKind.RAISE:
            if len(self.atoms) != 1:
                raise ValueError("a non-raise action cannot have a two-point projection")
            atom = self.atoms[0]
            if atom.action != self.exact_action or atom.weight.fraction != 1:
                raise ValueError("a non-raise action must project exactly to itself")
            return

        if any(atom.action.kind is not BettingActionKind.RAISE for atom in self.atoms):
            raise ValueError("an exact raise may project only to retained raises")
        exact_raise_to = self.exact_action.raise_to
        assert exact_raise_to is not None
        ordered = tuple(sorted(self.atoms, key=lambda atom: atom.action.raise_to or 0))
        if ordered != self.atoms:
            raise ValueError("off-tree raise atoms must be ordered by raise-to")
        expected = sum(
            (
                atom.weight.fraction * int(atom.action.raise_to)
                for atom in self.atoms
            ),
            start=Fraction(0),
        )
        if expected != exact_raise_to:
            raise ValueError("off-tree projection does not preserve exact chip expectation")

    @property
    def digest(self) -> str:
        payload = {
            "abstraction_digest": self.abstraction_digest,
            "atoms": tuple(
                {
                    "kind": atom.action.kind.value,
                    "raise_to": atom.action.raise_to,
                    "weight": (atom.weight.numerator, atom.weight.denominator),
                }
                for atom in self.atoms
            ),
            "exact_action": {
                "kind": self.exact_action.kind.value,
                "raise_to": self.exact_action.raise_to,
            },
            "source_digest": self.source_digest,
            "version": "off-tree-action-projection-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class LegalActionAbstractionSnapshot:
    street: BettingStreet
    acting_seat: int
    pot: int
    exact_action_count: int
    abstract_action_count: int
    abstract_raise_count: int
    clipped_origin_count: int
    merged_origin_count: int
    digest: str


def _action_for_kind(kind: BettingActionKind) -> BettingAction:
    if kind is BettingActionKind.FOLD:
        return FOLD
    if kind is BettingActionKind.CHECK:
        return CHECK
    if kind is BettingActionKind.CALL:
        return CALL
    raise ValueError("raise actions require an exact amount")


def _public_betting_payload(state: NoLimitBettingState) -> dict[str, object]:
    return {
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
        "total_contributions": state.total_contributions,
        "terminal_reason": (
            None if state.terminal_reason is None else state.terminal_reason.value
        ),
    }


@dataclass(frozen=True, slots=True)
class LegalActionAbstraction:
    """One immutable exact legal action lattice at one public decision."""

    betting: NoLimitBettingState
    decision: LegalBettingDecision
    source_digest: str
    pot_fractions: tuple[PotFraction, ...]
    actions: tuple[BettingAction, ...]
    raise_sizes: tuple[AbstractRaiseSize, ...]
    capacity_filling_parent_source_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.betting, NoLimitBettingState):
            raise TypeError("action abstraction requires exact public betting state")
        if not isinstance(self.decision, LegalBettingDecision):
            raise TypeError("action abstraction requires an exact legal decision")
        if self.decision != self.betting.legal_decision():
            raise ValueError("action abstraction decision is stale or belongs elsewhere")
        _require_digest(self.source_digest, label="action-abstraction source digest")
        if not isinstance(self.pot_fractions, tuple) or not self.pot_fractions:
            raise TypeError("action-abstraction fractions must be immutable and nonempty")
        if any(not isinstance(value, PotFraction) for value in self.pot_fractions):
            raise TypeError("action abstraction contains a nonsemantic pot fraction")
        if not isinstance(self.actions, tuple) or not self.actions:
            raise TypeError("abstract actions must be a nonempty immutable tuple")
        if any(not isinstance(action, BettingAction) for action in self.actions):
            raise TypeError("action abstraction contains a nonsemantic action")
        if len(set(self.actions)) != len(self.actions):
            raise ValueError("action abstraction repeats an exact action")
        if not isinstance(self.raise_sizes, tuple):
            raise TypeError("abstract raise sizes must be an immutable tuple")
        if any(not isinstance(value, AbstractRaiseSize) for value in self.raise_sizes):
            raise TypeError("action abstraction contains a nonsemantic raise size")
        if self.capacity_filling_parent_source_digest is not None:
            _require_digest(
                self.capacity_filling_parent_source_digest,
                label="capacity-filling parent source digest",
            )
            if self.capacity_filling_parent_source_digest == self.source_digest:
                raise ValueError("capacity-filling source cannot name itself as parent")

        nonraises = tuple(
            _action_for_kind(kind)
            for kind in self.decision.action_kinds
            if kind is not BettingActionKind.RAISE
        )
        raises = tuple(value.action for value in self.raise_sizes)
        if raises != tuple(sorted(raises, key=lambda action: int(action.raise_to))):
            raise ValueError("abstract raises must be strictly ordered by exact amount")
        if self.actions != (*nonraises, *raises):
            raise ValueError("abstract action ordering or schema is not canonical")
        for action in self.actions:
            require_legal_blueprint_action(action, self.decision)

        bounds = self.decision.raise_bounds
        if bounds is None:
            if self.raise_sizes:
                raise ValueError("non-raising decision contains abstract raises")
        else:
            by_amount = {int(value.action.raise_to): value for value in self.raise_sizes}
            if bounds.minimum_raise_to not in by_amount:
                raise ValueError("action abstraction omitted the exact minimum raise")
            if bounds.maximum_raise_to not in by_amount:
                raise ValueError("action abstraction omitted the exact all-in raise")
            origins = tuple(
                origin for value in self.raise_sizes for origin in value.origins
            )
            anchor_counts = {
                kind: sum(origin.kind is kind for origin in origins)
                for kind in (
                    RaiseSizeOriginKind.MINIMUM,
                    RaiseSizeOriginKind.MAXIMUM_CONTESTABLE,
                    RaiseSizeOriginKind.ALL_IN,
                )
            }
            if any(count != 1 for count in anchor_counts.values()):
                raise ValueError("action abstraction lost or repeated a semantic raise anchor")
            fraction_origins = tuple(
                origin.pot_fraction
                for origin in origins
                if origin.kind is RaiseSizeOriginKind.POT_FRACTION
            )
            if fraction_origins != self.pot_fractions:
                raise ValueError("action abstraction lost or reordered a pot-fraction origin")
            adaptive_origins = tuple(
                origin
                for origin in origins
                if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
            )
            if len(adaptive_origins) > 1:
                raise ValueError("action abstraction repeats collision-repair provenance")
            refill_origins = tuple(
                origin
                for origin in origins
                if origin.kind is RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
            )
            if (
                self.capacity_filling_parent_source_digest is None
                and refill_origins
            ):
                raise ValueError("capacity refill lacks a bound parent source")

            base_raise_to = self.decision.street_contribution + self.decision.call_amount
            pot_after_call = self.betting.pot + self.decision.call_amount
            for origin in origins:
                if origin.kind is RaiseSizeOriginKind.MINIMUM:
                    expected_raw = bounds.minimum_raise_to
                elif origin.kind is RaiseSizeOriginKind.MAXIMUM_CONTESTABLE:
                    expected_raw = bounds.maximum_contestable_raise_to
                elif origin.kind is RaiseSizeOriginKind.ALL_IN:
                    expected_raw = bounds.maximum_raise_to
                elif origin.kind is RaiseSizeOriginKind.POT_FRACTION:
                    assert origin.pot_fraction is not None
                    expected_raw = base_raise_to + _round_half_up(
                        origin.pot_fraction.fraction * pot_after_call
                    )
                elif origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET:
                    assert origin.pot_fraction is not None
                    expected_fraction, expected_collided = (
                        select_collision_repair_overbet(
                            betting=self.betting,
                            decision=self.decision,
                        )
                    )
                    if origin.pot_fraction != expected_fraction:
                        raise ValueError(
                            "action abstraction contains the wrong collision-repair branch"
                        )
                    if origin.collision_repair_triggered is not expected_collided:
                        raise ValueError(
                            "action abstraction contains the wrong collision decision"
                        )
                    expected_raw = base_raise_to + _round_half_up(
                        expected_fraction.fraction * pot_after_call
                    )
                else:
                    assert origin.kind is RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
                    assert origin.capacity_refill is not None
                    expected_raw = origin.capacity_refill.raise_to
                expected_projected, expected_clip = _project_to_bounds(
                    expected_raw,
                    bounds.minimum_raise_to,
                    bounds.maximum_raise_to,
                )
                if (
                    origin.raw_raise_to != expected_raw
                    or origin.projected_raise_to != expected_projected
                    or origin.clip is not expected_clip
                ):
                    raise ValueError("action abstraction contains mismatched raise provenance")
            if self.capacity_filling_parent_source_digest is not None:
                if len(adaptive_origins) != 1:
                    raise ValueError(
                        "capacity-filling abstraction lacks its collision-repair parent"
                    )
                parent_amounts = tuple(
                    sorted(
                        {
                            origin.projected_raise_to
                            for origin in origins
                            if origin.kind
                            is not RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
                        }
                    )
                )
                ordered_refills = tuple(
                    sorted(
                        refill_origins,
                        key=lambda origin: int(origin.capacity_refill_rank),
                    )
                )
                if tuple(
                    origin.capacity_refill_rank for origin in ordered_refills
                ) != tuple(range(1, len(ordered_refills) + 1)):
                    raise ValueError("capacity-refill ranks must be contiguous")
                retained = parent_amounts
                for origin in ordered_refills:
                    expected_selection = select_capacity_filling_pot_odds_refill(
                        betting=self.betting,
                        decision=self.decision,
                        retained_raise_to=retained,
                    )
                    if origin.capacity_refill != expected_selection:
                        raise ValueError("capacity-refill provenance is not maximin")
                    retained = tuple(
                        sorted((*retained, expected_selection.raise_to))
                    )
                exact_raise_count = (
                    bounds.maximum_raise_to - bounds.minimum_raise_to + 1
                )
                target_raise_count = min(7, exact_raise_count)
                if len(self.raise_sizes) != target_raise_count:
                    raise ValueError("capacity-filling abstraction left a slot unused")
                if tuple(
                    int(value.action.raise_to) for value in self.raise_sizes
                ) != retained:
                    raise ValueError("capacity refills differ from retained raises")
            if len(self.raise_sizes) > 7 or len(self.actions) > 9:
                raise ValueError("action abstraction exceeds its frozen width")

    @property
    def exact_action_count(self) -> int:
        nonraises = sum(
            kind is not BettingActionKind.RAISE
            for kind in self.decision.action_kinds
        )
        bounds = self.decision.raise_bounds
        raises = (
            0
            if bounds is None
            else bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        )
        return nonraises + raises

    @property
    def digest(self) -> str:
        payload = {
            "actions": tuple(
                {"kind": action.kind.value, "raise_to": action.raise_to}
                for action in self.actions
            ),
            "betting": _public_betting_payload(self.betting),
            "origins": tuple(
                {
                    "action_raise_to": value.action.raise_to,
                    "origins": tuple(
                        {
                            "clip": origin.clip.value,
                            "kind": origin.kind.value,
                            "pot_fraction": (
                                None
                                if origin.pot_fraction is None
                                else (
                                    origin.pot_fraction.numerator,
                                    origin.pot_fraction.denominator,
                                )
                            ),
                            "projected_raise_to": origin.projected_raise_to,
                            "raw_raise_to": origin.raw_raise_to,
                            **(
                                {
                                    "collision_repair_triggered": (
                                        origin.collision_repair_triggered
                                    )
                                }
                                if origin.kind
                                is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
                                else {}
                            ),
                            **(
                                {
                                    "capacity_refill": {
                                        "left_raise_to": (
                                            origin.capacity_refill.left_raise_to
                                        ),
                                        "raise_to": origin.capacity_refill.raise_to,
                                        "right_raise_to": (
                                            origin.capacity_refill.right_raise_to
                                        ),
                                        "score": (
                                            origin.capacity_refill.score.numerator,
                                            origin.capacity_refill.score.denominator,
                                        ),
                                    },
                                    "capacity_refill_rank": (
                                        origin.capacity_refill_rank
                                    ),
                                }
                                if origin.kind
                                is RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
                                and origin.capacity_refill is not None
                                else {}
                            ),
                        }
                        for origin in value.origins
                    ),
                }
                for value in self.raise_sizes
            ),
            "pot_fractions": tuple(
                (value.numerator, value.denominator)
                for value in self.pot_fractions
            ),
            "source_digest": self.source_digest,
            **(
                {
                    "capacity_filling_parent_source_digest": (
                        self.capacity_filling_parent_source_digest
                    )
                }
                if self.capacity_filling_parent_source_digest is not None
                else {}
            ),
            "version": "legal-action-abstraction-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def project(self, action: BettingAction) -> OffTreeActionProjection:
        require_legal_blueprint_action(action, self.decision)
        if action in self.actions:
            atoms = (
                ActionProjectionAtom(
                    action=action,
                    weight=ExactProjectionWeight(1, 1),
                ),
            )
        elif action.kind is BettingActionKind.RAISE:
            target = int(action.raise_to)
            lower = max(
                (
                    value.action
                    for value in self.raise_sizes
                    if int(value.action.raise_to) < target
                ),
                key=lambda candidate: int(candidate.raise_to),
            )
            upper = min(
                (
                    value.action
                    for value in self.raise_sizes
                    if int(value.action.raise_to) > target
                ),
                key=lambda candidate: int(candidate.raise_to),
            )
            lower_to = int(lower.raise_to)
            upper_to = int(upper.raise_to)
            width = upper_to - lower_to
            atoms = (
                ActionProjectionAtom(
                    action=lower,
                    weight=ExactProjectionWeight(upper_to - target, width),
                ),
                ActionProjectionAtom(
                    action=upper,
                    weight=ExactProjectionWeight(target - lower_to, width),
                ),
            )
        else:
            raise AssertionError("every exact legal non-raise must be retained")
        return OffTreeActionProjection(
            exact_action=action,
            abstraction_digest=self.digest,
            source_digest=self.source_digest,
            atoms=atoms,
        )

    def snapshot(self) -> LegalActionAbstractionSnapshot:
        origins = tuple(
            origin for value in self.raise_sizes for origin in value.origins
        )
        return LegalActionAbstractionSnapshot(
            street=self.decision.street,
            acting_seat=self.decision.acting_seat,
            pot=self.betting.pot,
            exact_action_count=self.exact_action_count,
            abstract_action_count=len(self.actions),
            abstract_raise_count=len(self.raise_sizes),
            clipped_origin_count=sum(
                origin.clip is not ClipDirection.NONE for origin in origins
            ),
            merged_origin_count=len(origins) - len(self.raise_sizes),
            digest=self.digest,
        )


def _round_half_up(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + int(2 * remainder >= value.denominator)


def _project_to_bounds(raw: int, minimum: int, maximum: int) -> tuple[int, ClipDirection]:
    if raw < minimum:
        return minimum, ClipDirection.LOW
    if raw > maximum:
        return maximum, ClipDirection.HIGH
    return raw, ClipDirection.NONE


def _capacity_filling_pot_odds(
    *,
    pot_after_call: int,
    base_raise_to: int,
    raise_to_amount: int,
) -> Fraction:
    increment = raise_to_amount - base_raise_to
    if increment <= 0:
        raise ValueError("capacity-filling raise must exceed the exact call base")
    return Fraction(increment, pot_after_call + 2 * increment)


def select_capacity_filling_pot_odds_refill(
    *,
    betting: NoLimitBettingState,
    decision: LegalBettingDecision,
    retained_raise_to: tuple[int, ...],
) -> CapacityFillingSelection:
    """Select one exact maximin pot-odds refill without scanning chip depth."""

    if not isinstance(betting, NoLimitBettingState):
        raise TypeError("capacity filling requires exact betting state")
    if not isinstance(decision, LegalBettingDecision):
        raise TypeError("capacity filling requires an exact legal decision")
    if decision != betting.legal_decision():
        raise ValueError("capacity filling received a stale decision")
    bounds = decision.raise_bounds
    if bounds is None:
        raise ValueError("capacity filling requires a legal raise interval")
    if not isinstance(retained_raise_to, tuple) or len(retained_raise_to) < 2:
        raise TypeError("capacity filling requires immutable minimum/all-in bounds")
    if any(
        isinstance(amount, bool) or not isinstance(amount, int)
        for amount in retained_raise_to
    ):
        raise TypeError("capacity-filling retained raises must be integers")
    if tuple(sorted(set(retained_raise_to))) != retained_raise_to:
        raise ValueError("capacity-filling retained raises must increase strictly")
    if (
        retained_raise_to[0] != bounds.minimum_raise_to
        or retained_raise_to[-1] != bounds.maximum_raise_to
    ):
        raise ValueError("capacity filling requires exact minimum/all-in anchors")
    exact_raise_count = bounds.maximum_raise_to - bounds.minimum_raise_to + 1
    if len(retained_raise_to) >= exact_raise_count:
        raise ValueError("capacity-filling raise interval has no unretained integer")

    base_raise_to = decision.street_contribution + decision.call_amount
    pot_after_call = betting.pot + decision.call_amount
    best: CapacityFillingSelection | None = None
    for left, right in pairwise(retained_raise_to):
        if right - left <= 1:
            continue
        left_coordinate = _capacity_filling_pot_odds(
            pot_after_call=pot_after_call,
            base_raise_to=base_raise_to,
            raise_to_amount=left,
        )
        right_coordinate = _capacity_filling_pot_odds(
            pot_after_call=pot_after_call,
            base_raise_to=base_raise_to,
            raise_to_amount=right,
        )
        midpoint = (left_coordinate + right_coordinate) / 2
        ideal_increment = Fraction(pot_after_call) * midpoint / (1 - 2 * midpoint)
        ideal_raise_to = Fraction(base_raise_to) + ideal_increment
        floor_raise_to = ideal_raise_to.numerator // ideal_raise_to.denominator
        ceiling_raise_to = -(
            -ideal_raise_to.numerator // ideal_raise_to.denominator
        )
        candidates = {
            min(right - 1, max(left + 1, floor_raise_to)),
            min(right - 1, max(left + 1, ceiling_raise_to)),
        }
        for candidate in candidates:
            coordinate = _capacity_filling_pot_odds(
                pot_after_call=pot_after_call,
                base_raise_to=base_raise_to,
                raise_to_amount=candidate,
            )
            score_fraction = min(
                coordinate - left_coordinate,
                right_coordinate - coordinate,
            )
            selection = CapacityFillingSelection(
                raise_to=candidate,
                left_raise_to=left,
                right_raise_to=right,
                score=ExactPotOddsDistance(
                    score_fraction.numerator,
                    score_fraction.denominator,
                ),
            )
            if (
                best is None
                or selection.score.fraction > best.score.fraction
                or (
                    selection.score.fraction == best.score.fraction
                    and selection.raise_to < best.raise_to
                )
            ):
                best = selection
    if best is None:
        raise AssertionError("capacity-filling anchors hid an unretained integer")
    return best


def select_collision_repair_overbet(
    *,
    betting: NoLimitBettingState,
    decision: LegalBettingDecision,
) -> tuple[PotFraction, bool]:
    """Select two-pot unless its exact clipped action is already mandatory."""

    if not isinstance(betting, NoLimitBettingState):
        raise TypeError("collision repair requires exact betting state")
    if not isinstance(decision, LegalBettingDecision):
        raise TypeError("collision repair requires an exact legal decision")
    if decision != betting.legal_decision():
        raise ValueError("collision repair received a stale decision")
    bounds = decision.raise_bounds
    if bounds is None:
        raise ValueError("collision repair requires a legal raise interval")
    base_raise_to = decision.street_contribution + decision.call_amount
    pot_after_call = betting.pot + decision.call_amount
    primary_raw = base_raise_to + _round_half_up(
        COLLISION_REPAIR_PRIMARY_OVERBET.fraction * pot_after_call
    )
    primary_projected, _primary_clip = _project_to_bounds(
        primary_raw,
        bounds.minimum_raise_to,
        bounds.maximum_raise_to,
    )
    contestable, _contestable_clip = _project_to_bounds(
        bounds.maximum_contestable_raise_to,
        bounds.minimum_raise_to,
        bounds.maximum_raise_to,
    )
    mandatory = {
        bounds.minimum_raise_to,
        contestable,
        bounds.maximum_raise_to,
    }
    collided = primary_projected in mandatory
    selected = (
        COLLISION_REPAIR_FALLBACK_OVERBET
        if collided
        else COLLISION_REPAIR_PRIMARY_OVERBET
    )
    return selected, collided


@dataclass(frozen=True, slots=True)
class ImmutableActionAbstractionSource:
    """Digest-bound exact integer sizing algorithm with no mutable table."""

    source_id: str
    pot_fractions: tuple[PotFraction, ...] = DEFAULT_POT_FRACTIONS

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("action-abstraction source id must be nonempty")
        if not isinstance(self.pot_fractions, tuple) or not self.pot_fractions:
            raise TypeError("action-abstraction pot fractions must be immutable")
        if any(not isinstance(value, PotFraction) for value in self.pot_fractions):
            raise TypeError("action-abstraction source has a nonsemantic fraction")
        exact = tuple(value.fraction for value in self.pot_fractions)
        if any(left >= right for left, right in pairwise(exact)):
            raise ValueError("action-abstraction pot fractions must increase strictly")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "algorithm_version": _ALGORITHM_VERSION,
            "anchors": ("minimum", "maximum_contestable", "all_in"),
            "fraction_base": "pot_after_call",
            "fractions": tuple(
                (value.numerator, value.denominator)
                for value in self.pot_fractions
            ),
            "integer_rounding": "nearest_ties_up",
            "projection": "adjacent_raise_to_exact_barycentric",
            "source_id": self.source_id,
        }
        return json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()

    def build(
        self,
        *,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> LegalActionAbstraction:
        if not isinstance(betting, NoLimitBettingState):
            raise TypeError("action-abstraction source requires exact betting state")
        if not isinstance(decision, LegalBettingDecision):
            raise TypeError("action-abstraction source requires exact legal decision")
        if decision != betting.legal_decision():
            raise ValueError("action-abstraction source received a stale decision")

        nonraises = tuple(
            _action_for_kind(kind)
            for kind in decision.action_kinds
            if kind is not BettingActionKind.RAISE
        )
        bounds = decision.raise_bounds
        raise_sizes: tuple[AbstractRaiseSize, ...] = ()
        if bounds is not None:
            raw_origins = [
                RaiseSizeOrigin(
                    kind=RaiseSizeOriginKind.MINIMUM,
                    raw_raise_to=bounds.minimum_raise_to,
                    projected_raise_to=bounds.minimum_raise_to,
                    clip=ClipDirection.NONE,
                )
            ]
            base_raise_to = decision.street_contribution + decision.call_amount
            pot_after_call = betting.pot + decision.call_amount
            for fraction in self.pot_fractions:
                raw = base_raise_to + _round_half_up(
                    fraction.fraction * pot_after_call
                )
                projected, clip = _project_to_bounds(
                    raw,
                    bounds.minimum_raise_to,
                    bounds.maximum_raise_to,
                )
                raw_origins.append(
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.POT_FRACTION,
                        raw_raise_to=raw,
                        projected_raise_to=projected,
                        clip=clip,
                        pot_fraction=fraction,
                    )
                )
            contestable, contestable_clip = _project_to_bounds(
                bounds.maximum_contestable_raise_to,
                bounds.minimum_raise_to,
                bounds.maximum_raise_to,
            )
            raw_origins.extend(
                (
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.MAXIMUM_CONTESTABLE,
                        raw_raise_to=bounds.maximum_contestable_raise_to,
                        projected_raise_to=contestable,
                        clip=contestable_clip,
                    ),
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.ALL_IN,
                        raw_raise_to=bounds.maximum_raise_to,
                        projected_raise_to=bounds.maximum_raise_to,
                        clip=ClipDirection.NONE,
                    ),
                )
            )
            grouped: dict[int, list[RaiseSizeOrigin]] = {}
            for origin in raw_origins:
                grouped.setdefault(origin.projected_raise_to, []).append(origin)
            raise_sizes = tuple(
                AbstractRaiseSize(
                    action=raise_to(amount),
                    origins=tuple(grouped[amount]),
                )
                for amount in sorted(grouped)
            )

        return LegalActionAbstraction(
            betting=betting,
            decision=decision,
            source_digest=self.digest,
            pot_fractions=self.pot_fractions,
            actions=(*nonraises, *(value.action for value in raise_sizes)),
            raise_sizes=raise_sizes,
        )


__all__ = [
    "COLLISION_REPAIR_CORE_POT_FRACTIONS",
    "COLLISION_REPAIR_FALLBACK_OVERBET",
    "COLLISION_REPAIR_PRIMARY_OVERBET",
    "DEFAULT_POT_FRACTIONS",
    "AbstractRaiseSize",
    "ActionProjectionAtom",
    "CapacityFillingSelection",
    "ClipDirection",
    "ExactPotOddsDistance",
    "ExactProjectionWeight",
    "ImmutableActionAbstractionSource",
    "LegalActionAbstraction",
    "LegalActionAbstractionSnapshot",
    "OffTreeActionProjection",
    "PotFraction",
    "RaiseSizeOrigin",
    "RaiseSizeOriginKind",
    "select_capacity_filling_pot_odds_refill",
    "select_collision_repair_overbet",
]
