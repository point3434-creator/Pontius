"""Complete six-seat TT ordering screens from dense small-axis root tensors."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations, product
import math

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SeatOrderCandidate:
    first_half: tuple[int, int, int]
    order: tuple[int, ...]
    numerical_ranks: tuple[int, ...]
    estimated_storage_bytes: int
    middle_rank: int


@dataclass(frozen=True, slots=True)
class SeatOrderScreen:
    selected: SeatOrderCandidate
    partition_best: tuple[SeatOrderCandidate, ...]
    subset_numerical_ranks: tuple[tuple[tuple[int, ...], int], ...]
    maximum_partition_singular_value_relative_error: float
    orders_screened: int


def unordered_three_three_partitions() -> tuple[tuple[int, int, int], ...]:
    """Return the ten unordered six-seat partitions, oriented through seat zero."""

    return tuple((0, *others) for others in combinations(range(1, 6), 2))


def screen_six_seat_orders(
    tensor: object,
    *,
    first_halves: tuple[tuple[int, int, int], ...],
    relative_threshold: float,
) -> SeatOrderScreen:
    """Screen every 3/3 partition and within-half order without value labels."""

    values = np.ascontiguousarray(tensor, dtype=np.float64)
    if values.ndim != 6 or any(size <= 0 for size in values.shape):
        raise ValueError("seat-order screen requires a six-mode tensor")
    if not np.all(np.isfinite(values)):
        raise ValueError("seat-order tensor must be finite")
    if (
        not math.isfinite(relative_threshold)
        or not 0.0 <= relative_threshold < 1.0
    ):
        raise ValueError("seat-order rank threshold must lie in [0, 1)")
    expected = unordered_three_three_partitions()
    if first_halves != expected:
        raise ValueError("seat-order partitions must be the ten canonical 3/3 splits")

    subsets = [
        *(tuple(combination) for combination in combinations(range(6), 1)),
        *(tuple(combination) for combination in combinations(range(6), 2)),
        *first_halves,
    ]
    spectra: dict[tuple[int, ...], FloatArray] = {}
    ranks: dict[tuple[int, ...], int] = {}
    for subset in subsets:
        singular = _subset_singular_values(values, subset)
        spectra[subset] = singular
        threshold = relative_threshold * singular[0] if len(singular) else 0.0
        ranks[subset] = max(1, int(np.count_nonzero(singular > threshold)))

    partition_best = []
    maximum_spectrum_error = 0.0
    all_seats = frozenset(range(6))
    orders_screened = 0
    for first_half in first_halves:
        second_half = tuple(sorted(all_seats - frozenset(first_half)))
        candidates = []
        for left_order, right_order in product(
            permutations(first_half),
            permutations(second_half),
        ):
            order = (*left_order, *right_order)
            order_ranks = _order_ranks(order, ranks)
            storage = _tt_storage_bytes(values.shape, order, order_ranks)
            candidates.append(
                SeatOrderCandidate(
                    first_half=first_half,
                    order=order,
                    numerical_ranks=order_ranks,
                    estimated_storage_bytes=storage,
                    middle_rank=order_ranks[3],
                )
            )
            orders_screened += 1
        best = min(
            candidates,
            key=lambda candidate: (
                candidate.estimated_storage_bytes,
                candidate.middle_rank,
                candidate.order,
            ),
        )
        partition_best.append(best)

        selected_singular = _ordered_middle_singular_values(values, best.order)
        canonical = spectra[first_half]
        denominator = max(1.0, float(canonical[0]) if len(canonical) else 0.0)
        maximum_spectrum_error = max(
            maximum_spectrum_error,
            float(np.max(np.abs(selected_singular - canonical))) / denominator,
        )

    selected = min(
        partition_best,
        key=lambda candidate: (
            candidate.estimated_storage_bytes,
            candidate.middle_rank,
            candidate.order,
        ),
    )
    return SeatOrderScreen(
        selected=selected,
        partition_best=tuple(partition_best),
        subset_numerical_ranks=tuple(
            (subset, ranks[subset]) for subset in sorted(ranks, key=lambda row: (len(row), row))
        ),
        maximum_partition_singular_value_relative_error=maximum_spectrum_error,
        orders_screened=orders_screened,
    )


def transpose_seat_tensor(tensor: object, order: tuple[int, ...]) -> FloatArray:
    """Transpose one six-mode tensor into a validated seat order."""

    values = np.ascontiguousarray(tensor, dtype=np.float64)
    if values.ndim != 6 or tuple(sorted(order)) != tuple(range(6)):
        raise ValueError("seat transpose requires one permutation of six modes")
    return np.ascontiguousarray(np.transpose(values, order), dtype=np.float64)


def _subset_singular_values(values: FloatArray, subset: tuple[int, ...]) -> FloatArray:
    complement = tuple(seat for seat in range(6) if seat not in subset)
    ordered = np.transpose(values, (*subset, *complement))
    left = math.prod(values.shape[seat] for seat in subset)
    return np.ascontiguousarray(
        np.linalg.svd(ordered.reshape(left, -1), compute_uv=False),
        dtype=np.float64,
    )


def _ordered_middle_singular_values(
    values: FloatArray,
    order: tuple[int, ...],
) -> FloatArray:
    ordered = np.transpose(values, order)
    left = math.prod(values.shape[seat] for seat in order[:3])
    return np.ascontiguousarray(
        np.linalg.svd(ordered.reshape(left, -1), compute_uv=False),
        dtype=np.float64,
    )


def _canonical_rank_key(subset: tuple[int, ...]) -> tuple[int, ...]:
    ordered = tuple(sorted(subset))
    if len(ordered) <= 2:
        return ordered
    if len(ordered) != 3:
        raise ValueError("seat-order rank key must have one to three seats")
    if 0 in ordered:
        return ordered
    return tuple(seat for seat in range(6) if seat not in ordered)


def _order_ranks(
    order: tuple[int, ...],
    ranks: dict[tuple[int, ...], int],
) -> tuple[int, ...]:
    if tuple(sorted(order)) != tuple(range(6)):
        raise ValueError("seat order must be a permutation of six modes")
    return (
        1,
        ranks[_canonical_rank_key(order[:1])],
        ranks[_canonical_rank_key(order[:2])],
        ranks[_canonical_rank_key(order[:3])],
        ranks[_canonical_rank_key(order[4:])],
        ranks[_canonical_rank_key(order[5:])],
        1,
    )


def _tt_storage_bytes(
    shape: tuple[int, ...],
    order: tuple[int, ...],
    ranks: tuple[int, ...],
) -> int:
    return sum(
        ranks[mode]
        * shape[seat]
        * ranks[mode + 1]
        * np.dtype(np.float64).itemsize
        for mode, seat in enumerate(order)
    )
