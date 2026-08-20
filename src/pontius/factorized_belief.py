"""Exact nonnegative factorized private-card beliefs and contractions.

A belief contains a finite mixture of per-seat unary range factors and an exact
card-disjointness constraint.  Public action likelihoods multiply one seat's
unary factors, so ordinary poker Bayesian updates stay in this family.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import fsum, prod
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .river import Card, HoleCards, _canonical_hole, _validate_card

FloatArray: TypeAlias = NDArray[np.float64]
UIntArray: TypeAlias = NDArray[np.uint64]


@dataclass(frozen=True, slots=True)
class MaterializedCardBelief:
    """One normalized explicit oracle distribution over positive assignments."""

    assignments: tuple[tuple[int, ...], ...]
    probabilities: FloatArray
    unnormalized_weights: FloatArray
    partition: float
    cartesian_assignments: int
    card_compatible_assignments: int

    def as_dict(self) -> dict[tuple[int, ...], float]:
        return dict(zip(self.assignments, self.probabilities, strict=True))


@dataclass(frozen=True, slots=True)
class FactorBeliefContraction:
    """Exact normalized marginals plus auditable contraction work."""

    partition: float
    marginals: tuple[FloatArray, ...]
    cartesian_assignments: int
    card_compatible_assignments: int
    partial_records: int
    partial_numeric_bytes: int
    incidence_table_entries: int
    maximum_live_incidence_table_entries: int
    estimated_incidence_numeric_bytes: int
    split_partition_relative_error: float


@dataclass(frozen=True, slots=True)
class _PartialAssignments:
    seats: tuple[int, ...]
    masks: UIntArray
    indices: NDArray[np.int32]
    component_products: FloatArray
    cartesian_assignments: int

    @property
    def records(self) -> int:
        return len(self.masks)

    @property
    def numeric_bytes(self) -> int:
        return self.masks.nbytes + self.indices.nbytes + self.component_products.nbytes


def _card_mask(hand: HoleCards) -> int:
    return (1 << hand[0]) | (1 << hand[1])


def _subsets(mask: int) -> tuple[tuple[int, int], ...]:
    """Return every subset and its inclusion-exclusion sign."""

    result = []
    subset = mask
    while True:
        result.append((subset, -1 if subset.bit_count() % 2 else 1))
        if subset == 0:
            break
        subset = (subset - 1) & mask
    return tuple(result)


class _KahanScalar:
    __slots__ = ("correction", "value")

    def __init__(self) -> None:
        self.value = 0.0
        self.correction = 0.0

    def add(self, value: float) -> None:
        adjusted = value - self.correction
        updated = self.value + adjusted
        self.correction = (updated - self.value) - adjusted
        self.value = updated


class FactorizedCardBelief:
    """Card-compatible mixture of products with immutable contiguous storage."""

    def __init__(
        self,
        *,
        hands_by_player: tuple[tuple[HoleCards, ...], ...],
        mixture_weights: object,
        unary_weights: tuple[object, ...],
        board: tuple[Card, ...] = (),
    ) -> None:
        if not 2 <= len(hands_by_player) <= 6:
            raise ValueError("factorized belief requires two to six players")
        canonical_board = tuple(sorted(board))
        if len(set(canonical_board)) != len(canonical_board):
            raise ValueError("public board cards must be distinct")
        for card in canonical_board:
            _validate_card(card)
        board_set = set(canonical_board)

        canonical_hands = []
        hand_masks = []
        for player, supplied_hands in enumerate(hands_by_player):
            hands = tuple(_canonical_hole(hand) for hand in supplied_hands)
            if not hands or len(set(hands)) != len(hands):
                raise ValueError(f"player {player} hands must be nonempty and unique")
            if any(board_set & set(hand) for hand in hands):
                raise ValueError(f"player {player} hand overlaps the public board")
            canonical_hands.append(hands)
            masks = np.ascontiguousarray(
                [_card_mask(hand) for hand in hands],
                dtype=np.uint64,
            )
            masks.flags.writeable = False
            hand_masks.append(masks)

        coefficients = np.array(
            mixture_weights,
            dtype=np.float64,
            order="C",
            copy=True,
        )
        if coefficients.ndim != 1 or len(coefficients) == 0:
            raise ValueError("mixture weights must be a nonempty vector")
        if not np.all(np.isfinite(coefficients)) or np.any(coefficients < 0.0):
            raise ValueError("mixture weights must be finite and nonnegative")
        if float(np.sum(coefficients)) <= 0.0:
            raise ValueError("mixture weights must have positive mass")
        if len(unary_weights) != len(canonical_hands):
            raise ValueError("one unary tensor is required per player")

        factors = []
        for player, (supplied, hands) in enumerate(
            zip(unary_weights, canonical_hands, strict=True)
        ):
            values = np.array(
                supplied,
                dtype=np.float64,
                order="C",
                copy=True,
            )
            expected_shape = (len(coefficients), len(hands))
            if values.shape != expected_shape:
                raise ValueError(
                    f"player {player} unary shape {values.shape!r} != {expected_shape!r}"
                )
            if not np.all(np.isfinite(values)) or np.any(values < 0.0):
                raise ValueError("unary weights must be finite and nonnegative")
            factors.append(values)

        coefficients = coefficients.copy()
        for component in range(len(coefficients)):
            for values in factors:
                maximum = float(np.max(values[component]))
                if maximum == 0.0:
                    coefficients[component] = 0.0
                    continue
                values[component] /= maximum
                coefficients[component] *= maximum
        coefficient_total = float(np.sum(coefficients))
        if coefficient_total <= 0.0:
            raise ValueError("factorized belief assigns zero mass before compatibility")
        coefficients /= coefficient_total
        coefficients.flags.writeable = False
        for values in factors:
            values.flags.writeable = False

        self.board = canonical_board
        self.hands_by_player = tuple(canonical_hands)
        self.hand_masks = tuple(hand_masks)
        self.mixture_weights = coefficients
        self.unary_weights = tuple(factors)
        self.num_players = len(canonical_hands)
        self.component_count = len(coefficients)

    @property
    def hand_counts(self) -> tuple[int, ...]:
        return tuple(len(hands) for hands in self.hands_by_player)

    @property
    def cartesian_assignments(self) -> int:
        return prod(self.hand_counts)

    @property
    def persistent_numeric_bytes(self) -> int:
        return (
            self.mixture_weights.nbytes
            + sum(values.nbytes for values in self.unary_weights)
            + sum(values.nbytes for values in self.hand_masks)
        )

    def storage_is_contiguous_float64_and_uint64(self) -> bool:
        return (
            self.mixture_weights.dtype == np.float64
            and self.mixture_weights.flags.c_contiguous
            and all(
                values.dtype == np.float64 and values.flags.c_contiguous
                for values in self.unary_weights
            )
            and all(
                values.dtype == np.uint64 and values.flags.c_contiguous
                for values in self.hand_masks
            )
        )

    def with_likelihood(
        self,
        player: int,
        likelihood: object,
    ) -> FactorizedCardBelief:
        if player not in range(self.num_players):
            raise ValueError(f"invalid player index {player}")
        values = np.ascontiguousarray(likelihood, dtype=np.float64)
        if values.shape != (self.hand_counts[player],):
            raise ValueError("likelihood shape does not match the player's hand axis")
        if not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise ValueError("likelihoods must be finite and nonnegative")
        factors = [factor.copy() for factor in self.unary_weights]
        factors[player] *= values[None, :]
        return type(self)(
            hands_by_player=self.hands_by_player,
            mixture_weights=self.mixture_weights,
            unary_weights=tuple(factors),
            board=self.board,
        )

    def condition_on_hand(
        self,
        player: int,
        hand: HoleCards,
    ) -> FactorizedCardBelief:
        if player not in range(self.num_players):
            raise ValueError(f"invalid player index {player}")
        canonical = _canonical_hole(hand)
        try:
            selected = self.hands_by_player[player].index(canonical)
        except ValueError as error:
            raise ValueError("conditioned hand is outside the player's axis") from error
        likelihood = np.zeros(self.hand_counts[player], dtype=np.float64)
        likelihood[selected] = 1.0
        return self.with_likelihood(player, likelihood)

    def _component_product(self, indices: tuple[int, ...]) -> FloatArray:
        values = np.ones(self.component_count, dtype=np.float64)
        for player, hand_index in enumerate(indices):
            values *= self.unary_weights[player][:, hand_index]
        return values

    def assignment_weight(self, indices: tuple[int, ...]) -> float:
        if len(indices) != self.num_players:
            raise ValueError("assignment must select one hand per player")
        used_mask = 0
        for player, hand_index in enumerate(indices):
            if hand_index not in range(self.hand_counts[player]):
                raise ValueError("assignment contains an invalid hand index")
            mask = int(self.hand_masks[player][hand_index])
            if used_mask & mask:
                return 0.0
            used_mask |= mask
        return float(self.mixture_weights @ self._component_product(indices))

    def materialize(self) -> MaterializedCardBelief:
        assignments = []
        weights = []
        compatible = 0
        for indices in product(*(range(count) for count in self.hand_counts)):
            used_mask = 0
            is_compatible = True
            for player, hand_index in enumerate(indices):
                mask = int(self.hand_masks[player][hand_index])
                if used_mask & mask:
                    is_compatible = False
                    break
                used_mask |= mask
            if not is_compatible:
                continue
            compatible += 1
            weight = float(self.mixture_weights @ self._component_product(indices))
            if weight > 0.0:
                assignments.append(indices)
                weights.append(weight)
        partition = fsum(weights)
        if partition <= 0.0:
            raise ValueError("card compatibility eliminated all positive assignments")
        unnormalized = np.ascontiguousarray(weights, dtype=np.float64)
        probabilities = np.ascontiguousarray(
            unnormalized / partition,
            dtype=np.float64,
        )
        probabilities.flags.writeable = False
        unnormalized.flags.writeable = False
        return MaterializedCardBelief(
            assignments=tuple(assignments),
            probabilities=probabilities,
            unnormalized_weights=unnormalized,
            partition=partition,
            cartesian_assignments=self.cartesian_assignments,
            card_compatible_assignments=compatible,
        )

    def recursive_contract(self) -> FactorBeliefContraction:
        partition = _KahanScalar()
        marginal_values = tuple(
            tuple(_KahanScalar() for _ in hands) for hands in self.hands_by_player
        )
        compatible = 0
        selected = [0] * self.num_players

        def walk(player: int, used_mask: int, component_product: FloatArray) -> None:
            nonlocal compatible
            if player == self.num_players:
                compatible += 1
                mass = float(self.mixture_weights @ component_product)
                if mass <= 0.0:
                    return
                partition.add(mass)
                for seat, hand_index in enumerate(selected):
                    marginal_values[seat][hand_index].add(mass)
                return
            for hand_index, supplied_mask in enumerate(self.hand_masks[player]):
                mask = int(supplied_mask)
                if used_mask & mask:
                    continue
                selected[player] = hand_index
                walk(
                    player + 1,
                    used_mask | mask,
                    component_product * self.unary_weights[player][:, hand_index],
                )

        walk(0, 0, np.ones(self.component_count, dtype=np.float64))
        if partition.value <= 0.0:
            raise ValueError("recursive contraction found zero compatible mass")
        marginals = tuple(
            np.ascontiguousarray(
                [entry.value / partition.value for entry in player_values],
                dtype=np.float64,
            )
            for player_values in marginal_values
        )
        return FactorBeliefContraction(
            partition=partition.value,
            marginals=marginals,
            cartesian_assignments=self.cartesian_assignments,
            card_compatible_assignments=compatible,
            partial_records=compatible,
            partial_numeric_bytes=0,
            incidence_table_entries=0,
            maximum_live_incidence_table_entries=0,
            estimated_incidence_numeric_bytes=0,
            split_partition_relative_error=0.0,
        )

    def _partial_assignments(self, seats: tuple[int, ...]) -> _PartialAssignments:
        if not seats or len(set(seats)) != len(seats):
            raise ValueError("partial seats must be nonempty and unique")
        if any(seat not in range(self.num_players) for seat in seats):
            raise ValueError("partial seats contain an invalid player")
        masks = []
        indices = []
        component_products = []
        selected = [0] * len(seats)

        def walk(depth: int, used_mask: int, values: FloatArray) -> None:
            if depth == len(seats):
                masks.append(used_mask)
                indices.append(tuple(selected))
                component_products.append(values)
                return
            seat = seats[depth]
            for hand_index, supplied_mask in enumerate(self.hand_masks[seat]):
                mask = int(supplied_mask)
                if used_mask & mask:
                    continue
                selected[depth] = hand_index
                walk(
                    depth + 1,
                    used_mask | mask,
                    values * self.unary_weights[seat][:, hand_index],
                )

        walk(0, 0, np.ones(self.component_count, dtype=np.float64))
        mask_array = np.ascontiguousarray(masks, dtype=np.uint64)
        index_array = np.ascontiguousarray(indices, dtype=np.int32)
        product_array = np.ascontiguousarray(component_products, dtype=np.float64)
        return _PartialAssignments(
            seats=seats,
            masks=mask_array,
            indices=index_array,
            component_products=product_array,
            cartesian_assignments=prod(self.hand_counts[seat] for seat in seats),
        )

    def _incidence_table(
        self,
        partial: _PartialAssignments,
    ) -> dict[int, FloatArray]:
        table: dict[int, FloatArray] = {}
        for record, supplied_mask in enumerate(partial.masks):
            values = partial.component_products[record]
            for subset, _ in _subsets(int(supplied_mask)):
                entry = table.get(subset)
                if entry is None:
                    entry = np.zeros(self.component_count + 1, dtype=np.float64)
                    table[subset] = entry
                entry[: self.component_count] += values
                entry[-1] += 1.0
        return table

    def _compatible_query(
        self,
        table: dict[int, FloatArray],
        mask: int,
    ) -> FloatArray:
        subsets = _subsets(mask)
        result = np.empty(self.component_count + 1, dtype=np.float64)
        for component in range(self.component_count + 1):
            terms = (
                sign * entry[component]
                for subset, sign in subsets
                if (entry := table.get(subset)) is not None
            )
            value = fsum(terms)
            if value < 0.0 and abs(value) <= 1e-12 * table[0][component]:
                value = 0.0
            if value < 0.0:
                raise ArithmeticError("inclusion-exclusion produced negative mass")
            result[component] = value
        return result

    def meet_in_middle_contract(
        self,
        left_seats: tuple[int, ...] | None = None,
    ) -> FactorBeliefContraction:
        if left_seats is None:
            left_seats = tuple(range(self.num_players // 2))
        left_seats = tuple(left_seats)
        if not left_seats or len(left_seats) == self.num_players:
            raise ValueError("meet-in-the-middle split must leave two nonempty halves")
        if len(set(left_seats)) != len(left_seats):
            raise ValueError("meet-in-the-middle left seats must be unique")
        if any(seat not in range(self.num_players) for seat in left_seats):
            raise ValueError("meet-in-the-middle split contains an invalid player")
        right_seats = tuple(
            seat for seat in range(self.num_players) if seat not in set(left_seats)
        )
        left = self._partial_assignments(left_seats)
        right = self._partial_assignments(right_seats)

        partition = _KahanScalar()
        marginal_values = tuple(
            tuple(_KahanScalar() for _ in hands) for hands in self.hands_by_player
        )
        compatible_assignments = 0
        right_table = self._incidence_table(right)
        right_cache: dict[int, FloatArray] = {}
        for record, supplied_mask in enumerate(left.masks):
            mask = int(supplied_mask)
            compatible = right_cache.get(mask)
            if compatible is None:
                compatible = self._compatible_query(right_table, mask)
                right_cache[mask] = compatible
            component_mass = (
                self.mixture_weights
                * left.component_products[record]
                * compatible[: self.component_count]
            )
            mass = float(np.sum(component_mass))
            partition.add(mass)
            compatible_assignments += round(float(compatible[-1]))
            for depth, seat in enumerate(left.seats):
                marginal_values[seat][int(left.indices[record, depth])].add(mass)
        first_partition = partition.value
        right_entries = len(right_table)
        del right_table

        replay_partition = _KahanScalar()
        left_table = self._incidence_table(left)
        left_cache: dict[int, FloatArray] = {}
        for record, supplied_mask in enumerate(right.masks):
            mask = int(supplied_mask)
            compatible = left_cache.get(mask)
            if compatible is None:
                compatible = self._compatible_query(left_table, mask)
                left_cache[mask] = compatible
            component_mass = (
                self.mixture_weights
                * right.component_products[record]
                * compatible[: self.component_count]
            )
            mass = float(np.sum(component_mass))
            replay_partition.add(mass)
            for depth, seat in enumerate(right.seats):
                marginal_values[seat][int(right.indices[record, depth])].add(mass)
        left_entries = len(left_table)
        if first_partition <= 0.0 or replay_partition.value <= 0.0:
            raise ValueError("meet-in-the-middle contraction found zero mass")
        replay_error = abs(first_partition - replay_partition.value) / max(
            first_partition,
            replay_partition.value,
        )
        marginals = tuple(
            np.ascontiguousarray(
                [entry.value / first_partition for entry in player_values],
                dtype=np.float64,
            )
            for player_values in marginal_values
        )
        incidence_entries = left_entries + right_entries
        estimated_incidence_bytes = incidence_entries * (
            np.dtype(np.uint64).itemsize
            + (self.component_count + 1) * np.dtype(np.float64).itemsize
        )
        return FactorBeliefContraction(
            partition=first_partition,
            marginals=marginals,
            cartesian_assignments=self.cartesian_assignments,
            card_compatible_assignments=compatible_assignments,
            partial_records=left.records + right.records,
            partial_numeric_bytes=left.numeric_bytes + right.numeric_bytes,
            incidence_table_entries=incidence_entries,
            maximum_live_incidence_table_entries=max(left_entries, right_entries),
            estimated_incidence_numeric_bytes=estimated_incidence_bytes,
            split_partition_relative_error=replay_error,
        )
