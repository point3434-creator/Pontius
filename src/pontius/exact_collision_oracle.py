"""Independent exact rational oracle for reduced card-collision beliefs."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import prod

from .holdem_cards import HoleCards, make_hole


@dataclass(frozen=True, slots=True)
class ExactCollisionOracleResult:
    assignments: tuple[tuple[int, ...], ...]
    probabilities: tuple[Fraction, ...]
    partition: Fraction
    marginals: tuple[tuple[Fraction, ...], ...]
    cartesian_assignments: int
    card_compatible_assignments: int
    positive_assignments: int

    def as_dict(self) -> dict[tuple[int, ...], Fraction]:
        return dict(zip(self.assignments, self.probabilities, strict=True))


def independently_normalized_marginals(
    weights_by_player: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    """Return the collision-blind product marginals as an explicit diagnostic."""

    if not isinstance(weights_by_player, tuple) or not weights_by_player:
        raise TypeError("independent marginal weights must be an immutable tuple")
    marginals = []
    for weights in weights_by_player:
        if not isinstance(weights, tuple) or not weights:
            raise TypeError("each independent weight axis must be immutable and nonempty")
        if any(not isinstance(weight, Fraction) or weight < 0 for weight in weights):
            raise TypeError("independent weights must be nonnegative Fractions")
        total = sum(weights, start=Fraction(0))
        if total <= 0:
            raise ValueError("each independent weight axis must have positive mass")
        marginals.append(tuple(weight / total for weight in weights))
    return tuple(marginals)


def marginal_total_variation(
    first: tuple[Fraction, ...],
    second: tuple[Fraction, ...],
) -> Fraction:
    if not isinstance(first, tuple) or not isinstance(second, tuple):
        raise TypeError("marginal vectors must be immutable tuples")
    if len(first) != len(second):
        raise ValueError("marginal vectors must have equal width")
    if any(not isinstance(value, Fraction) for value in (*first, *second)):
        raise TypeError("marginal values must be exact Fractions")
    return sum(
        (abs(left - right) for left, right in zip(first, second, strict=True)),
        start=Fraction(0),
    ) / 2


def enumerate_exact_collision_belief(
    *,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    weights_by_player: tuple[tuple[Fraction, ...], ...],
    maximum_cartesian_assignments: int,
) -> ExactCollisionOracleResult:
    """Enumerate a bounded reduced joint with exact rational arithmetic."""

    if not isinstance(hands_by_player, tuple) or not 2 <= len(hands_by_player) <= 5:
        raise ValueError("collision oracle requires two through five immutable axes")
    if not isinstance(weights_by_player, tuple) or len(weights_by_player) != len(
        hands_by_player
    ):
        raise ValueError("collision oracle requires one weight axis per hand axis")
    if (
        isinstance(maximum_cartesian_assignments, bool)
        or not isinstance(maximum_cartesian_assignments, int)
        or maximum_cartesian_assignments <= 0
    ):
        raise ValueError("collision oracle work bound must be a positive integer")

    canonical_axes = []
    for player, (hands, weights) in enumerate(
        zip(hands_by_player, weights_by_player, strict=True)
    ):
        if not isinstance(hands, tuple) or not hands:
            raise TypeError("collision-oracle hand axes must be immutable and nonempty")
        canonical = tuple(make_hole(*hand) for hand in hands)
        if canonical != hands or len(set(canonical)) != len(canonical):
            raise ValueError(f"collision-oracle player {player} hands are not canonical")
        if not isinstance(weights, tuple) or len(weights) != len(hands):
            raise ValueError("collision-oracle weight axis has the wrong width")
        if any(not isinstance(weight, Fraction) or weight < 0 for weight in weights):
            raise TypeError("collision-oracle weights must be nonnegative Fractions")
        if not any(weight > 0 for weight in weights):
            raise ValueError("collision-oracle weight axis has zero mass")
        canonical_axes.append(canonical)

    cartesian = prod(len(hands) for hands in canonical_axes)
    if cartesian > maximum_cartesian_assignments:
        raise ValueError("collision oracle Cartesian work exceeds its explicit bound")

    assignments = []
    masses = []
    marginal_masses = [
        [Fraction(0) for _ in hands]
        for hands in canonical_axes
    ]
    compatible = 0
    for indices in product(*(range(len(hands)) for hands in canonical_axes)):
        used_cards: set[int] = set()
        collision = False
        for player, hand_index in enumerate(indices):
            hand = canonical_axes[player][hand_index]
            if used_cards.intersection(hand):
                collision = True
                break
            used_cards.update(hand)
        if collision:
            continue
        compatible += 1
        mass = prod(
            weights_by_player[player][hand_index]
            for player, hand_index in enumerate(indices)
        )
        if mass <= 0:
            continue
        assignments.append(indices)
        masses.append(mass)
        for player, hand_index in enumerate(indices):
            marginal_masses[player][hand_index] += mass

    partition = sum(masses, start=Fraction(0))
    if partition <= 0:
        raise ValueError("card compatibility eliminated all positive assignments")
    probabilities = tuple(mass / partition for mass in masses)
    marginals = tuple(
        tuple(mass / partition for mass in player_masses)
        for player_masses in marginal_masses
    )
    return ExactCollisionOracleResult(
        assignments=tuple(assignments),
        probabilities=probabilities,
        partition=partition,
        marginals=marginals,
        cartesian_assignments=cartesian,
        card_compatible_assignments=compatible,
        positive_assignments=len(assignments),
    )


__all__ = [
    "ExactCollisionOracleResult",
    "enumerate_exact_collision_belief",
    "independently_normalized_marginals",
    "marginal_total_variation",
]
