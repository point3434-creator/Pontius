"""Full-width five-opponent belief for one controlled hold'em seat.

The compact state is rank-one unary range weight per opponent multiplied by
the exact hard card-disjointness constraint implemented by
``FactorizedCardBelief``.  Exact rational weights and likelihood digests retain
provenance; Float64 is only the existing contraction backend representation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
from math import comb, gcd, prod

import numpy as np

from .factorized_belief import FactorizedCardBelief
from .full_width_reference_policy import (
    BlueprintActionLikelihood,
    RationalActionProbability,
)
from .holdem_cards import HoleCards, OneSeatCardState
from .no_limit_betting import SEAT_COUNT, BettingStreet


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class ExactRangeWeight:
    """One nonnegative exact unary range weight, distinct from a probability."""

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            ("range-weight numerator", self.numerator),
            ("range-weight denominator", self.denominator),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.numerator < 0:
            raise ValueError("range-weight numerator must be nonnegative")
        if self.denominator <= 0:
            raise ValueError("range-weight denominator must be positive")
        common = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // common)
        object.__setattr__(self, "denominator", self.denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)

    @property
    def as_float(self) -> float:
        return self.numerator / self.denominator

    def times_probability(
        self,
        probability: RationalActionProbability,
    ) -> ExactRangeWeight:
        if not isinstance(probability, RationalActionProbability):
            raise TypeError("range updates require a rational action probability")
        return ExactRangeWeight(
            self.numerator * probability.numerator,
            self.denominator * probability.denominator,
        )


@dataclass(frozen=True, slots=True)
class FullWidthBeliefSnapshot:
    street: BettingStreet
    opponent_seats: tuple[int, ...]
    opponent_hand_counts: tuple[int, ...]
    cartesian_assignments: int
    compatible_assignments: int
    persistent_numeric_bytes: int
    likelihood_updates: int
    digest: str


def _card_mask(hand: HoleCards) -> int:
    return (1 << hand[0]) | (1 << hand[1])


def _has_compatible_positive_assignment(
    hand_axis: tuple[HoleCards, ...],
    weights_by_opponent: tuple[tuple[ExactRangeWeight, ...], ...],
) -> bool:
    options = []
    for weights in weights_by_opponent:
        masks = tuple(
            _card_mask(hand)
            for hand, weight in zip(hand_axis, weights, strict=True)
            if weight.numerator > 0
        )
        if not masks:
            return False
        options.append(masks)
    ordered = tuple(sorted(options, key=len))

    def search(depth: int, used_mask: int) -> bool:
        if depth == len(ordered):
            return True
        for mask in ordered[depth]:
            if used_mask & mask == 0 and search(depth + 1, used_mask | mask):
                return True
        return False

    return search(0, 0)


@dataclass(frozen=True, slots=True)
class FullWidthOneSeatBelief:
    """Immutable five-opponent full-combo belief for one visible card state."""

    cards: OneSeatCardState
    opponent_seats: tuple[int, ...]
    hand_axis: tuple[HoleCards, ...]
    weights_by_opponent: tuple[tuple[ExactRangeWeight, ...], ...]
    likelihood_digests: tuple[str, ...] = ()
    _factorized: FactorizedCardBelief = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.cards, OneSeatCardState):
            raise TypeError("full-width belief requires a one-seat card state")
        expected_seats = tuple(
            seat for seat in range(SEAT_COUNT) if seat != self.cards.controlled_seat
        )
        if not isinstance(self.opponent_seats, tuple):
            raise TypeError("opponent seats must be an immutable tuple")
        if self.opponent_seats != expected_seats:
            raise ValueError("full-width belief must contain all five opponents in order")
        if not isinstance(self.hand_axis, tuple):
            raise TypeError("full-width hand axis must be an immutable tuple")
        expected_axis = self.cards.compatible_opponent_hands()
        if self.hand_axis != expected_axis:
            raise ValueError("full-width hand axis is not the exact visible-card domain")
        if not isinstance(self.weights_by_opponent, tuple) or len(
            self.weights_by_opponent
        ) != len(self.opponent_seats):
            raise ValueError("one immutable weight axis is required per opponent")
        for weights in self.weights_by_opponent:
            if not isinstance(weights, tuple) or len(weights) != len(self.hand_axis):
                raise ValueError("opponent range weights have the wrong hand width")
            if any(not isinstance(weight, ExactRangeWeight) for weight in weights):
                raise TypeError("opponent range contains a nonsemantic weight")
            if not any(weight.numerator > 0 for weight in weights):
                raise ValueError("every opponent range must retain positive mass")
        if not isinstance(self.likelihood_digests, tuple):
            raise TypeError("likelihood provenance must be an immutable tuple")
        for digest in self.likelihood_digests:
            _require_digest(digest, label="belief likelihood digest")
        if not _has_compatible_positive_assignment(
            self.hand_axis,
            self.weights_by_opponent,
        ):
            raise ValueError("full-width belief has no compatible positive assignment")

        unary_weights = []
        for weights in self.weights_by_opponent:
            maximum = max(weight.fraction for weight in weights)
            values = []
            for weight in weights:
                scaled = float(weight.fraction / maximum)
                if weight.numerator > 0 and scaled == 0.0:
                    raise ArithmeticError("positive exact range weight underflowed")
                values.append(scaled)
            array = np.ascontiguousarray([values], dtype=np.float64)
            if not np.all(np.isfinite(array)):
                raise ArithmeticError("exact range weight converted to nonfinite Float64")
            unary_weights.append(array)
        factorized = FactorizedCardBelief(
            hands_by_player=(self.hand_axis,) * len(self.opponent_seats),
            mixture_weights=np.asarray([1.0], dtype=np.float64),
            unary_weights=tuple(unary_weights),
            board=self.cards.board,
        )
        object.__setattr__(self, "_factorized", factorized)

    @classmethod
    def uniform(cls, cards: OneSeatCardState) -> FullWidthOneSeatBelief:
        if not isinstance(cards, OneSeatCardState):
            raise TypeError("uniform full-width belief requires visible cards")
        seats = tuple(seat for seat in range(SEAT_COUNT) if seat != cards.controlled_seat)
        axis = cards.compatible_opponent_hands()
        uniform_axis = (ExactRangeWeight(1),) * len(axis)
        return cls(
            cards=cards,
            opponent_seats=seats,
            hand_axis=axis,
            weights_by_opponent=(uniform_axis,) * len(seats),
        )

    @property
    def factorized(self) -> FactorizedCardBelief:
        return self._factorized

    @property
    def opponent_hand_counts(self) -> tuple[int, ...]:
        return (len(self.hand_axis),) * len(self.opponent_seats)

    @property
    def cartesian_assignments(self) -> int:
        return len(self.hand_axis) ** len(self.opponent_seats)

    @property
    def compatible_assignments(self) -> int:
        remaining_cards = 52 - len(self.cards.known_cards)
        return prod(
            comb(remaining_cards - 2 * opponent, 2)
            for opponent in range(len(self.opponent_seats))
        )

    @property
    def persistent_numeric_bytes(self) -> int:
        return self.factorized.persistent_numeric_bytes

    def opponent_index(self, seat: int) -> int:
        if isinstance(seat, bool) or not isinstance(seat, int):
            raise TypeError("opponent seat must be semantic")
        try:
            return self.opponent_seats.index(seat)
        except ValueError as error:
            raise ValueError("controlled seat is not an opponent range") from error

    def weights_for(self, seat: int) -> tuple[ExactRangeWeight, ...]:
        return self.weights_by_opponent[self.opponent_index(seat)]

    def with_action_likelihood(
        self,
        likelihood: BlueprintActionLikelihood,
    ) -> FullWidthOneSeatBelief:
        if not isinstance(likelihood, BlueprintActionLikelihood):
            raise TypeError("full-width update requires blueprint likelihood provenance")
        index = self.opponent_index(likelihood.actor_seat)
        if likelihood.street is not self.cards.street:
            raise ValueError("action likelihood belongs to a different street")
        if likelihood.hand_axis != self.hand_axis:
            raise ValueError("action likelihood belongs to a stale or partial hand axis")
        updated = tuple(
            weight.times_probability(probability)
            for weight, probability in zip(
                self.weights_by_opponent[index],
                likelihood.probabilities,
                strict=True,
            )
        )
        weights = list(self.weights_by_opponent)
        weights[index] = updated
        return FullWidthOneSeatBelief(
            cards=self.cards,
            opponent_seats=self.opponent_seats,
            hand_axis=self.hand_axis,
            weights_by_opponent=tuple(weights),
            likelihood_digests=(*self.likelihood_digests, likelihood.digest),
        )

    def advance_to(self, cards: OneSeatCardState) -> FullWidthOneSeatBelief:
        if not isinstance(cards, OneSeatCardState):
            raise TypeError("belief board transition requires visible cards")
        if cards.controlled_seat != self.cards.controlled_seat:
            raise ValueError("belief board transition changed the controlled seat")
        if cards.private_hand != self.cards.private_hand:
            raise ValueError("belief board transition changed the private hand")
        revealed = cards.board[len(self.cards.board) :]
        expected = self.cards.advance_to(cards.street, revealed)
        if expected != cards:
            raise ValueError("belief board transition is not the exact next reveal")
        old_indices = {hand: index for index, hand in enumerate(self.hand_axis)}
        new_axis = cards.compatible_opponent_hands()
        weights = tuple(
            tuple(opponent_weights[old_indices[hand]] for hand in new_axis)
            for opponent_weights in self.weights_by_opponent
        )
        return FullWidthOneSeatBelief(
            cards=cards,
            opponent_seats=self.opponent_seats,
            hand_axis=new_axis,
            weights_by_opponent=weights,
            likelihood_digests=self.likelihood_digests,
        )

    @property
    def digest(self) -> str:
        numeric = sha256()
        numeric.update(self.factorized.mixture_weights.tobytes(order="C"))
        for unary in self.factorized.unary_weights:
            numeric.update(unary.tobytes(order="C"))
        payload = {
            "card_state_digest": self.cards.public_digest,
            "factorized_numeric_digest": numeric.hexdigest(),
            "hand_axis": self.hand_axis,
            "likelihood_digests": self.likelihood_digests,
            "opponent_seats": self.opponent_seats,
            "version": "full-width-one-seat-belief-v1",
            "weights": tuple(
                tuple((weight.numerator, weight.denominator) for weight in weights)
                for weights in self.weights_by_opponent
            ),
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def snapshot(self) -> FullWidthBeliefSnapshot:
        return FullWidthBeliefSnapshot(
            street=self.cards.street,
            opponent_seats=self.opponent_seats,
            opponent_hand_counts=self.opponent_hand_counts,
            cartesian_assignments=self.cartesian_assignments,
            compatible_assignments=self.compatible_assignments,
            persistent_numeric_bytes=self.persistent_numeric_bytes,
            likelihood_updates=len(self.likelihood_digests),
            digest=self.digest,
        )


__all__ = [
    "ExactRangeWeight",
    "FullWidthBeliefSnapshot",
    "FullWidthOneSeatBelief",
]
