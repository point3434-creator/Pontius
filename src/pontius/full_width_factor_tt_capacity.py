"""Exact allocation accounting for the current full-width FactorTT lineage.

The production FactorTT topology stores every compatible assignment inside
each side of its split.  That representation is exact and effective at h32,
but its allocation must be admitted before a literal full-combo construction.
This module computes the numeric-array bill without allocating those arrays.

The formulas are representation facts, not latency extrapolations.  Python
container overhead, temporary construction objects, tensor-train storage,
sparse operators, and contraction scratch are deliberately excluded, so the
reported bytes are lower bounds on a live process rather than peak estimates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, prod

UINT64_BYTES = 8
INT32_BYTES = 4
INT8_BYTES = 1
FLOAT64_BYTES = 8


def _require_positive_integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def labeled_disjoint_pair_assignments(
    *,
    available_cards: int,
    opponent_axes: int,
) -> int:
    """Count labeled disjoint two-card assignments over complete equal axes."""

    available = _require_positive_integer(
        available_cards,
        label="available cards",
    )
    if (
        isinstance(opponent_axes, bool)
        or not isinstance(opponent_axes, int)
        or opponent_axes < 0
    ):
        raise ValueError("opponent axes must be a nonnegative integer")
    if 2 * opponent_axes > available:
        return 0
    return prod(comb(available - 2 * index, 2) for index in range(opponent_axes))


@dataclass(frozen=True, slots=True)
class FactorTTHalfAllocation:
    """Exact persistent numeric-array accounting for one topology half."""

    seats: int
    records: int

    def __post_init__(self) -> None:
        _require_positive_integer(self.seats, label="half seats")
        _require_positive_integer(self.records, label="half records")

    @property
    def subset_count(self) -> int:
        return 1 << (2 * self.seats)

    @property
    def masks_numeric_bytes(self) -> int:
        return self.records * UINT64_BYTES

    @property
    def indices_numeric_bytes(self) -> int:
        return self.records * self.seats * INT32_BYTES

    @property
    def half_numeric_bytes(self) -> int:
        return self.masks_numeric_bytes + self.indices_numeric_bytes

    @property
    def source_ids_numeric_bytes(self) -> int:
        return self.records * self.subset_count * INT32_BYTES

    @property
    def query_ids_numeric_bytes(self) -> int:
        return self.records * self.subset_count * INT32_BYTES

    @property
    def query_signs_numeric_bytes(self) -> int:
        return self.records * self.subset_count * INT8_BYTES


@dataclass(frozen=True, slots=True)
class FactorTTPersistentAllocation:
    """Persistent arrays owned by the current base and open-mode topology."""

    hand_counts: tuple[int, ...]
    split_index: int
    left: FactorTTHalfAllocation
    right: FactorTTHalfAllocation
    component_count: int = 1
    forward_incidence_entries: int | None = None
    reverse_incidence_entries: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.hand_counts, tuple) or len(self.hand_counts) < 2:
            raise ValueError("FactorTT allocation requires immutable hand counts")
        for count in self.hand_counts:
            _require_positive_integer(count, label="hand count")
        if (
            isinstance(self.split_index, bool)
            or not isinstance(self.split_index, int)
            or self.split_index <= 0
            or self.split_index >= len(self.hand_counts)
        ):
            raise ValueError("split index must leave two nonempty halves")
        if self.left.seats != self.split_index:
            raise ValueError("left half seat count differs from split index")
        if self.right.seats != len(self.hand_counts) - self.split_index:
            raise ValueError("right half seat count differs from split index")
        _require_positive_integer(self.component_count, label="component count")
        for label, entries in (
            ("forward incidence entries", self.forward_incidence_entries),
            ("reverse incidence entries", self.reverse_incidence_entries),
        ):
            if entries is not None and (
                isinstance(entries, bool)
                or not isinstance(entries, int)
                or entries <= 0
            ):
                raise ValueError(f"{label} must be positive when supplied")

    @property
    def axis_masks_numeric_bytes(self) -> int:
        return sum(self.hand_counts) * UINT64_BYTES

    @property
    def base_topology_numeric_bytes(self) -> int:
        """Exact ``FactorTTTopology.numeric_bytes`` from frozen record counts."""

        return (
            self.axis_masks_numeric_bytes
            + self.left.half_numeric_bytes
            + self.right.half_numeric_bytes
            + self.right.source_ids_numeric_bytes
            + self.left.query_ids_numeric_bytes
            + self.left.query_signs_numeric_bytes
        )

    @property
    def reverse_topology_numeric_bytes(self) -> int:
        return (
            self.left.source_ids_numeric_bytes
            + self.right.query_ids_numeric_bytes
            + self.right.query_signs_numeric_bytes
        )

    @property
    def bidirectional_topology_numeric_bytes(self) -> int:
        """Exact ``BidirectionalFactorTTTopology.numeric_bytes`` lower layer."""

        return self.base_topology_numeric_bytes + self.reverse_topology_numeric_bytes

    @property
    def resident_belief_numeric_bytes(self) -> int:
        """Exact ``CuPyResidentBeliefCache.numeric_bytes`` for the workspace."""

        product_bytes = (
            self.left.records + self.right.records
        ) * self.component_count * FLOAT64_BYTES
        index_bytes = (
            self.left.records * self.left.seats
            + self.right.records * self.right.seats
        ) * INT32_BYTES
        mixture_bytes = self.component_count * FLOAT64_BYTES
        return mixture_bytes + product_bytes + index_bytes

    @property
    def base_workspace_numeric_bytes(self) -> int | None:
        """Exact workspace bytes when the forward incidence cardinality is known."""

        if self.forward_incidence_entries is None:
            return None
        component = self.component_count * FLOAT64_BYTES
        return (
            component
            + (self.left.records + self.right.records) * component
            + (self.forward_incidence_entries + 1) * component
        )

    @property
    def open_workspace_numeric_bytes(self) -> int | None:
        """Exact open-mode workspace bytes when both incidence counts are known."""

        base = self.base_workspace_numeric_bytes
        if base is None or self.reverse_incidence_entries is None:
            return None
        return base + (
            (self.reverse_incidence_entries + 1)
            * self.component_count
            * FLOAT64_BYTES
        )

    def as_record(self) -> dict[str, object]:
        return {
            "hand_counts": list(self.hand_counts),
            "split_index": self.split_index,
            "component_count": self.component_count,
            "axis_masks_numeric_bytes": self.axis_masks_numeric_bytes,
            "left": {
                "seats": self.left.seats,
                "records": self.left.records,
                "subset_count": self.left.subset_count,
                "half_numeric_bytes": self.left.half_numeric_bytes,
                "source_ids_numeric_bytes": self.left.source_ids_numeric_bytes,
                "query_ids_numeric_bytes": self.left.query_ids_numeric_bytes,
                "query_signs_numeric_bytes": self.left.query_signs_numeric_bytes,
            },
            "right": {
                "seats": self.right.seats,
                "records": self.right.records,
                "subset_count": self.right.subset_count,
                "half_numeric_bytes": self.right.half_numeric_bytes,
                "source_ids_numeric_bytes": self.right.source_ids_numeric_bytes,
                "query_ids_numeric_bytes": self.right.query_ids_numeric_bytes,
                "query_signs_numeric_bytes": self.right.query_signs_numeric_bytes,
            },
            "base_topology_numeric_bytes": self.base_topology_numeric_bytes,
            "reverse_topology_numeric_bytes": self.reverse_topology_numeric_bytes,
            "bidirectional_topology_numeric_bytes": (
                self.bidirectional_topology_numeric_bytes
            ),
            "resident_belief_numeric_bytes": self.resident_belief_numeric_bytes,
            "base_workspace_numeric_bytes": self.base_workspace_numeric_bytes,
            "open_workspace_numeric_bytes": self.open_workspace_numeric_bytes,
            "excluded_from_numeric_lower_bound": [
                "python_container_overhead",
                "construction_temporaries",
                "incidence_key_sets",
                "workspace_when_incidence_cardinality_is_unavailable",
                "sparse_cpu_and_gpu_operators",
                "showdown_automata_and_tensor_trains",
                "contraction_products_results_and_scratch",
            ],
        }


def canonical_six_seat_river_allocation(
    *,
    controlled_seat: int,
    opponent_hand_count: int,
    available_cards: int,
    split_index: int = 3,
    component_count: int = 1,
) -> FactorTTPersistentAllocation:
    """Account for one singleton hero plus five complete opponent axes."""

    if (
        isinstance(controlled_seat, bool)
        or not isinstance(controlled_seat, int)
        or controlled_seat not in range(6)
    ):
        raise ValueError("controlled seat must identify one of six seats")
    width = _require_positive_integer(opponent_hand_count, label="opponent width")
    available = _require_positive_integer(available_cards, label="available cards")
    if width != comb(available, 2):
        raise ValueError("opponent width is not the complete two-card domain")
    if split_index != 3:
        raise ValueError("the current six-seat FactorTT lineage requires split index 3")

    hand_counts = tuple(1 if seat == controlled_seat else width for seat in range(6))
    left_opponents = sum(seat != controlled_seat for seat in range(split_index))
    right_opponents = 5 - left_opponents
    left_records = labeled_disjoint_pair_assignments(
        available_cards=available,
        opponent_axes=left_opponents,
    )
    right_records = labeled_disjoint_pair_assignments(
        available_cards=available,
        opponent_axes=right_opponents,
    )
    return FactorTTPersistentAllocation(
        hand_counts=hand_counts,
        split_index=split_index,
        left=FactorTTHalfAllocation(split_index, left_records),
        right=FactorTTHalfAllocation(6 - split_index, right_records),
        component_count=component_count,
    )


def minimum_scalar_topology_numeric_bytes(
    *,
    opponent_hand_count: int,
    available_cards: int,
    component_count: int = 1,
) -> int:
    """Best base-topology bill over putting the singleton in either half.

    This is intentionally more favorable than the frozen seat order.  It rules
    out the numerical coincidence that one unfortunate hero position alone
    caused a representation rejection.
    """

    candidates = (
        canonical_six_seat_river_allocation(
            controlled_seat=seat,
            opponent_hand_count=opponent_hand_count,
            available_cards=available_cards,
            component_count=component_count,
        ).base_topology_numeric_bytes
        for seat in (0, 3)
    )
    return min(candidates)


__all__ = [
    "FLOAT64_BYTES",
    "INT8_BYTES",
    "INT32_BYTES",
    "UINT64_BYTES",
    "FactorTTHalfAllocation",
    "FactorTTPersistentAllocation",
    "canonical_six_seat_river_allocation",
    "labeled_disjoint_pair_assignments",
    "minimum_scalar_topology_numeric_bytes",
]
