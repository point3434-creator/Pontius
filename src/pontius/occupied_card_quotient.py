"""Exact bounded reference for occupied-card quotient contraction.

This module is deliberately a semantic oracle, not a full-width runtime.  A
directional pass may aggregate source records by occupied-card union only when
every source seat is closed and every open private-hand axis is on the query
side.  The resulting disjointness operator is evaluated with exact rational
containment marginals and inclusion-exclusion; its reverse is the exact
transpose at labeled-record level.

The implementation retains labeled source masks only because ADR-0367's first
keystone is bounded.  A scalable successor must generate or aggregate the same
coefficients without storing the full labeled half.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
import json
from math import comb, factorial, isfinite, prod
from typing import Iterable, Sequence


ExactRow = tuple[Fraction, ...]
ExactRows = tuple[ExactRow, ...]


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool) or not isinstance(item, int) or item < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return item


def _seat_tuple(values: Iterable[object], *, label: str) -> tuple[int, ...]:
    result = tuple(_integer(value, label=label) for value in values)
    if not result:
        raise ValueError(f"{label} must be nonempty")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must be unique")
    return result


def _mask_tuple(values: Iterable[object], *, label: str) -> tuple[int, ...]:
    result = tuple(_integer(value, label=label) for value in values)
    if not result:
        raise ValueError(f"{label} must be nonempty")
    if any(value >= 1 << 64 for value in result):
        raise ValueError(f"{label} must fit UInt64")
    return result


def _fraction(value: object) -> Fraction:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool):
        raise ValueError("exact coefficient must not be Boolean")
    if isinstance(item, float) and not isfinite(item):
        raise ValueError("exact coefficient must be finite")
    try:
        return item if isinstance(item, Fraction) else Fraction(item)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("exact coefficient must be rational") from error


def _rows(values: Sequence[Sequence[object]], *, records: int) -> ExactRows:
    if len(values) != records:
        raise ValueError("coefficient rows differ from record count")
    result = tuple(tuple(_fraction(value) for value in row) for row in values)
    if not result or not result[0]:
        raise ValueError("coefficient rows must have positive width")
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise ValueError("coefficient rows must have uniform width")
    return result


def _subsets_up_to(mask: int, maximum_cards: int) -> tuple[int, ...]:
    cards = tuple(index for index in range(mask.bit_length()) if mask & (1 << index))
    result = []
    for width in range(min(len(cards), maximum_cards) + 1):
        for selected in combinations(cards, width):
            subset = 0
            for card in selected:
                subset |= 1 << card
            result.append(subset)
    return tuple(result)


def _zero_row(width: int) -> list[Fraction]:
    return [Fraction(0) for _ in range(width)]


def _aggregate_masks(
    masks: Sequence[int],
    values: ExactRows,
) -> tuple[tuple[int, ...], ExactRows]:
    unique = tuple(sorted(set(masks)))
    ids = {mask: index for index, mask in enumerate(unique)}
    width = len(values[0])
    sums = [_zero_row(width) for _ in unique]
    for mask, row in zip(masks, values, strict=True):
        target = sums[ids[mask]]
        for feature, value in enumerate(row):
            target[feature] += value
    return unique, tuple(tuple(row) for row in sums)


def _disjoint_transform(
    source_masks: Sequence[int],
    source_rows: ExactRows,
    target_masks: Sequence[int],
) -> tuple[ExactRows, int, int]:
    """Apply the exact disjointness matrix from unique source masks."""

    width = len(source_rows[0])
    maximum_target_cards = max(mask.bit_count() for mask in target_masks)
    maximum_source_cards = max(mask.bit_count() for mask in source_masks)
    marginals: dict[int, list[Fraction]] = {}
    marginal_updates = 0
    for mask, row in zip(source_masks, source_rows, strict=True):
        for subset in _subsets_up_to(mask, maximum_target_cards):
            target = marginals.setdefault(subset, _zero_row(width))
            for feature, value in enumerate(row):
                target[feature] += value
            marginal_updates += 1

    outputs = []
    query_terms = 0
    for mask in target_masks:
        result = _zero_row(width)
        for subset in _subsets_up_to(mask, maximum_source_cards):
            sign = -1 if subset.bit_count() % 2 else 1
            marginal = marginals.get(subset)
            if marginal is not None:
                for feature, value in enumerate(marginal):
                    result[feature] += sign * value
            query_terms += 1
        outputs.append(tuple(result))
    return tuple(outputs), marginal_updates, query_terms


@dataclass(frozen=True, slots=True)
class ExactQuotientCoefficients:
    """Canonical exact coefficients indexed by occupied-card mask."""

    masks: tuple[int, ...]
    rows: ExactRows

    def __post_init__(self) -> None:
        if not self.masks or tuple(sorted(set(self.masks))) != self.masks:
            raise ValueError("coefficient masks must be unique canonical order")
        if any(
            isinstance(mask, bool) or not isinstance(mask, int) or not 0 <= mask < 1 << 64
            for mask in self.masks
        ):
            raise ValueError("coefficient masks must be UInt64 integers")
        if len(self.rows) != len(self.masks) or not self.rows or not self.rows[0]:
            raise ValueError("coefficient rows differ from masks or have zero width")
        width = len(self.rows[0])
        if any(len(row) != width for row in self.rows):
            raise ValueError("coefficient rows must have uniform width")
        if any(not isinstance(value, Fraction) for row in self.rows for value in row):
            raise ValueError("coefficient rows must be exact Fractions")

    @property
    def feature_width(self) -> int:
        return len(self.rows[0])

    def canonical_bytes(self) -> bytes:
        """Return one stable exact representation for permutation controls."""

        payload = {
            "masks": list(self.masks),
            "rows": [
                [[value.numerator, value.denominator] for value in row]
                for row in self.rows
            ],
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")


@dataclass(frozen=True, slots=True)
class OccupiedCardQuotientWork:
    """Logical exact work, with labeled and quotient quantities separated."""

    source_records: int
    unique_source_occupancies: int
    source_marginal_updates: int
    query_records: int
    signed_query_terms: int
    feature_width: int


@dataclass(frozen=True, slots=True)
class ExactOccupiedCardQuotientResult:
    coefficients: ExactQuotientCoefficients
    query_rows: ExactRows
    work: OccupiedCardQuotientWork


@dataclass(frozen=True, slots=True)
class OccupiedCardQuotientTopology:
    """One bounded direction whose source seats are all fully summed."""

    source_seats: tuple[int, ...]
    query_seats: tuple[int, ...]
    open_seats: tuple[int, ...]
    source_record_masks: tuple[int, ...]
    query_record_masks: tuple[int, ...]
    source_variable_masks: tuple[int, ...]
    query_variable_masks: tuple[int, ...]
    source_fixed_mask: int
    query_fixed_mask: int
    source_occupancy_masks: tuple[int, ...]
    source_group_ids: tuple[int, ...]
    source_multiplicities: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.source_seats or not self.query_seats:
            raise ValueError("source and query seats must be nonempty")
        if len(set(self.source_seats)) != len(self.source_seats):
            raise ValueError("source seats must be unique")
        if len(set(self.query_seats)) != len(self.query_seats):
            raise ValueError("query seats must be unique")
        if len(set(self.open_seats)) != len(self.open_seats):
            raise ValueError("open seats must be unique")
        if set(self.source_seats) & set(self.query_seats):
            raise ValueError("source and query seats must be disjoint")
        if not set(self.open_seats).issubset(self.query_seats):
            raise ValueError("every open seat must be on the query side")
        if len(self.source_record_masks) != len(self.source_variable_masks):
            raise ValueError("source projected masks differ from record masks")
        if len(self.query_record_masks) != len(self.query_variable_masks):
            raise ValueError("query projected masks differ from record masks")
        if len(self.source_group_ids) != len(self.source_record_masks):
            raise ValueError("source group IDs differ from record masks")
        if self.source_fixed_mask & self.query_fixed_mask:
            raise ValueError("source and query fixed masks must be disjoint")
        if any(
            original ^ self.source_fixed_mask != variable
            for original, variable in zip(
                self.source_record_masks,
                self.source_variable_masks,
                strict=True,
            )
        ):
            raise ValueError("source fixed-card projection is inconsistent")
        if any(
            original ^ self.query_fixed_mask != variable
            for original, variable in zip(
                self.query_record_masks,
                self.query_variable_masks,
                strict=True,
            )
        ):
            raise ValueError("query fixed-card projection is inconsistent")
        if any(mask & self.query_fixed_mask for mask in self.source_variable_masks):
            raise ValueError("query fixed card is not absent from the source")
        if any(mask & self.source_fixed_mask for mask in self.query_variable_masks):
            raise ValueError("source fixed card is not absent from the query")
        if len({mask.bit_count() for mask in self.source_variable_masks}) != 1:
            raise ValueError("source occupancy width must be fixed")
        if len({mask.bit_count() for mask in self.query_variable_masks}) != 1:
            raise ValueError("query occupancy width must be fixed")
        occupancies = tuple(sorted(set(self.source_variable_masks)))
        if occupancies != self.source_occupancy_masks:
            raise ValueError("source occupancies are not the canonical quotient")
        group_by_mask = {mask: index for index, mask in enumerate(occupancies)}
        expected_groups = tuple(
            group_by_mask[mask] for mask in self.source_variable_masks
        )
        if expected_groups != self.source_group_ids:
            raise ValueError("source group IDs do not match canonical occupancies")
        multiplicities = [0] * len(occupancies)
        for group in self.source_group_ids:
            multiplicities[group] += 1
        expected_multiplicities = tuple(multiplicities)
        if expected_multiplicities != self.source_multiplicities:
            raise ValueError("source multiplicities do not match group IDs")

    @classmethod
    def compile(
        cls,
        *,
        source_seats: Iterable[object],
        query_seats: Iterable[object],
        open_seats: Iterable[object],
        source_record_masks: Iterable[object],
        query_record_masks: Iterable[object],
        source_fixed_mask: object = 0,
        query_fixed_mask: object = 0,
    ) -> OccupiedCardQuotientTopology:
        source = _seat_tuple(source_seats, label="source seats")
        query = _seat_tuple(query_seats, label="query seats")
        opened = tuple(_integer(seat, label="open seats") for seat in open_seats)
        if len(set(opened)) != len(opened):
            raise ValueError("open seats must be unique")
        if set(source) & set(query):
            raise ValueError("source and query seats must be disjoint")
        if not set(opened).issubset(query):
            raise ValueError("every open seat must be on the query side")

        source_masks = _mask_tuple(source_record_masks, label="source record masks")
        query_masks = _mask_tuple(query_record_masks, label="query record masks")
        source_fixed = _integer(source_fixed_mask, label="source fixed mask")
        query_fixed = _integer(query_fixed_mask, label="query fixed mask")
        if source_fixed >= 1 << 64 or query_fixed >= 1 << 64:
            raise ValueError("fixed masks must fit UInt64")
        if source_fixed & query_fixed:
            raise ValueError("source and query fixed masks must be disjoint")
        if any(mask & source_fixed != source_fixed for mask in source_masks):
            raise ValueError("source record omits a declared fixed card")
        if any(mask & query_fixed != query_fixed for mask in query_masks):
            raise ValueError("query record omits a declared fixed card")

        source_variable = tuple(mask ^ source_fixed for mask in source_masks)
        query_variable = tuple(mask ^ query_fixed for mask in query_masks)
        if any(mask & query_fixed for mask in source_variable):
            raise ValueError("query fixed card is not absent from the source")
        if any(mask & source_fixed for mask in query_variable):
            raise ValueError("source fixed card is not absent from the query")
        source_cardinalities = {mask.bit_count() for mask in source_variable}
        query_cardinalities = {mask.bit_count() for mask in query_variable}
        if len(source_cardinalities) != 1 or len(query_cardinalities) != 1:
            raise ValueError("each directional half must have fixed occupancy width")

        occupancies = tuple(sorted(set(source_variable)))
        group_by_mask = {mask: index for index, mask in enumerate(occupancies)}
        group_ids = tuple(group_by_mask[mask] for mask in source_variable)
        multiplicities = [0] * len(occupancies)
        for group in group_ids:
            multiplicities[group] += 1
        return cls(
            source_seats=source,
            query_seats=query,
            open_seats=opened,
            source_record_masks=source_masks,
            query_record_masks=query_masks,
            source_variable_masks=source_variable,
            query_variable_masks=query_variable,
            source_fixed_mask=source_fixed,
            query_fixed_mask=query_fixed,
            source_occupancy_masks=occupancies,
            source_group_ids=group_ids,
            source_multiplicities=tuple(multiplicities),
        )

    @property
    def source_records(self) -> int:
        return len(self.source_record_masks)

    @property
    def query_records(self) -> int:
        return len(self.query_record_masks)

    def aggregate_exact(
        self,
        record_values: Sequence[Sequence[object]],
    ) -> ExactQuotientCoefficients:
        values = _rows(record_values, records=self.source_records)
        width = len(values[0])
        sums = [_zero_row(width) for _ in self.source_occupancy_masks]
        for group, row in zip(self.source_group_ids, values, strict=True):
            target = sums[group]
            for feature, value in enumerate(row):
                target[feature] += value
        return ExactQuotientCoefficients(
            masks=self.source_occupancy_masks,
            rows=tuple(tuple(row) for row in sums),
        )

    def refresh_one_source_seat_exact(
        self,
        previous: ExactQuotientCoefficients,
        *,
        changed_seat: object,
        refreshed_record_values: Sequence[Sequence[object]],
    ) -> ExactQuotientCoefficients:
        """Reference refresh after one seat changes, reusing only topology.

        The bounded oracle intentionally recomputes every coefficient.  A
        future delta/device refresh may optimize this work only if it remains
        canonically identical to this cold-equivalent result.
        """

        seat = _integer(changed_seat, label="changed seat")
        if seat not in self.source_seats:
            raise ValueError("changed seat is not on the closed source side")
        if previous.masks != self.source_occupancy_masks:
            raise ValueError("previous coefficients differ from quotient topology")
        refreshed = self.aggregate_exact(refreshed_record_values)
        if refreshed.feature_width != previous.feature_width:
            raise ValueError("refreshed coefficient width differs from previous width")
        return refreshed

    def apply_coefficients_exact(
        self,
        coefficients: ExactQuotientCoefficients,
    ) -> tuple[ExactRows, OccupiedCardQuotientWork]:
        if coefficients.masks != self.source_occupancy_masks:
            raise ValueError("coefficients differ from quotient topology")
        query_rows, updates, terms = _disjoint_transform(
            coefficients.masks,
            coefficients.rows,
            self.query_variable_masks,
        )
        return query_rows, OccupiedCardQuotientWork(
            source_records=self.source_records,
            unique_source_occupancies=len(self.source_occupancy_masks),
            source_marginal_updates=updates,
            query_records=self.query_records,
            signed_query_terms=terms,
            feature_width=coefficients.feature_width,
        )

    def apply_exact(
        self,
        record_values: Sequence[Sequence[object]],
    ) -> ExactOccupiedCardQuotientResult:
        coefficients = self.aggregate_exact(record_values)
        query_rows, work = self.apply_coefficients_exact(coefficients)
        return ExactOccupiedCardQuotientResult(
            coefficients=coefficients,
            query_rows=query_rows,
            work=work,
        )

    def apply_adjoint_exact(
        self,
        query_values: Sequence[Sequence[object]],
    ) -> ExactRows:
        """Apply the labeled-record transpose of this disjointness operator."""

        values = _rows(query_values, records=self.query_records)
        masks, aggregated = _aggregate_masks(self.query_variable_masks, values)
        unique_source_rows, _, _ = _disjoint_transform(
            masks,
            aggregated,
            self.source_occupancy_masks,
        )
        return tuple(unique_source_rows[group] for group in self.source_group_ids)


@dataclass(frozen=True, slots=True)
class OccupancyQuotientCombinatorics:
    """Exact complete-axis counts, independent of any runtime layout."""

    available_cards: int
    source_pairs: int
    query_pairs: int

    def __post_init__(self) -> None:
        _integer(self.available_cards, label="available cards", minimum=1)
        _integer(self.source_pairs, label="source pairs")
        _integer(self.query_pairs, label="query pairs")
        if 2 * max(self.source_pairs, self.query_pairs) > self.available_cards:
            raise ValueError("pair occupancy exceeds the available-card universe")

    @property
    def source_cards(self) -> int:
        return 2 * self.source_pairs

    @property
    def query_cards(self) -> int:
        return 2 * self.query_pairs

    @property
    def source_occupancy_masks(self) -> int:
        return comb(self.available_cards, self.source_cards)

    @property
    def query_occupancy_masks(self) -> int:
        return comb(self.available_cards, self.query_cards)

    @staticmethod
    def labeled_pairing_multiplicity(pairs: int) -> int:
        count = _integer(pairs, label="pairs")
        return factorial(2 * count) // (2**count)

    @property
    def source_pairing_multiplicity(self) -> int:
        return self.labeled_pairing_multiplicity(self.source_pairs)

    @property
    def query_pairing_multiplicity(self) -> int:
        return self.labeled_pairing_multiplicity(self.query_pairs)

    @property
    def labeled_source_assignments(self) -> int:
        return prod(
            comb(self.available_cards - 2 * index, 2)
            for index in range(self.source_pairs)
        )

    @property
    def labeled_query_assignments(self) -> int:
        return prod(
            comb(self.available_cards - 2 * index, 2)
            for index in range(self.query_pairs)
        )

    @property
    def maximum_containment_subset_cards(self) -> int:
        return min(self.source_cards, self.query_cards)

    @property
    def containment_key_universe(self) -> int:
        return sum(
            comb(self.available_cards, width)
            for width in range(self.maximum_containment_subset_cards + 1)
        )

    @property
    def marginal_updates_per_source_occupancy(self) -> int:
        return sum(
            comb(self.source_cards, width)
            for width in range(self.maximum_containment_subset_cards + 1)
        )

    @property
    def signed_terms_per_query_record(self) -> int:
        return sum(
            comb(self.query_cards, width)
            for width in range(self.maximum_containment_subset_cards + 1)
        )

    def identities_hold(self) -> bool:
        return (
            self.labeled_source_assignments
            == self.source_occupancy_masks * self.source_pairing_multiplicity
            and self.labeled_query_assignments
            == self.query_occupancy_masks * self.query_pairing_multiplicity
        )


__all__ = [
    "ExactOccupiedCardQuotientResult",
    "ExactQuotientCoefficients",
    "OccupiedCardQuotientTopology",
    "OccupiedCardQuotientWork",
    "OccupancyQuotientCombinatorics",
]
