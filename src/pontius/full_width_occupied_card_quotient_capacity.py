"""Exact source-only allocation and work accounting for the quotient layout.

This module allocates nothing at full width.  It models the target-specific
six-card-source/four-card-query operator sealed algebraically by ADR-0368 and
preregistered for source-only accounting by ADR-0369.  Bytes are numeric-array
bytes only.  Logical work is never converted to time.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, factorial, prod
from typing import Literal


Placement = Literal["host", "device"]
Phase = Literal["persistent", "source", "query", "adjoint", "result"]

FLOAT64_BYTES = 8
UINT64_BYTES = 8
INT32_BYTES = 4
UINT32_BYTES = 4
UINT8_BYTES = 1

HOST_NUMERIC_CAP_BYTES = 48_000_000_000
DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
HOST_RESERVE_BYTES = 8_000_000_000
DEVICE_RESERVE_BYTES = 2_000_000_000
MINIMUM_HOST_PHYSICAL_BYTES = 60_000_000_000
MINIMUM_DEVICE_PHYSICAL_BYTES = 16_000_000_000

FROZEN_AVAILABLE_CARDS = 45
FROZEN_OPPONENT_HANDS = comb(FROZEN_AVAILABLE_CARDS, 2)
FROZEN_SOURCE_CHUNK = 32_768
FROZEN_QUERY_CHUNK = 65_536
FROZEN_FIXTURE_STATE_RANKS = (59, 117, 175, 4, 5)
FROZEN_FIXTURE_SOURCE_STATE_RANK = 175
SAFE_SOURCE_STATE_RANK = 3 * FROZEN_OPPONENT_HANDS
SAFE_AUTOMATON_STATE_RANKS = (
    FROZEN_OPPONENT_HANDS,
    2 * FROZEN_OPPONENT_HANDS,
    3 * FROZEN_OPPONENT_HANDS,
    3 * FROZEN_OPPONENT_HANDS + 4,
    4 * FROZEN_OPPONENT_HANDS + 5,
)

_EXCLUDED_NONNUMERIC_CLASSES = (
    "Python object headers and containers",
    "allocator fragmentation and alignment padding outside named arrays",
    "CuPy memory-pool retention beyond live named arrays",
    "CUDA context, driver, module, and kernel-code storage",
    "GPU registers, local memory, compiler temporaries, and occupancy effects",
    "page tables, pinned-transfer bookkeeping, filesystem caches, and OS activity",
)


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def combination_rank(cards: tuple[int, ...], *, universe_size: int) -> int:
    """Return the collision-free colexicographic combinadic rank of ``cards``."""

    _positive_int("combination universe", universe_size)
    supplied = tuple(cards)
    if supplied != tuple(sorted(set(supplied))):
        raise ValueError("combination cards must be strictly increasing and unique")
    if any(
        isinstance(card, bool)
        or not isinstance(card, int)
        or card < 0
        or card >= universe_size
        for card in supplied
    ):
        raise ValueError("combination card is outside the universe")
    return sum(comb(card, index) for index, card in enumerate(supplied, start=1))


def combination_unrank(
    rank: int,
    *,
    universe_size: int,
    cardinality: int,
) -> tuple[int, ...]:
    """Invert :func:`combination_rank` exactly within one cardinality."""

    _positive_int("combination universe", universe_size)
    _nonnegative_int("combination cardinality", cardinality)
    if cardinality > universe_size:
        raise ValueError("combination cardinality exceeds the universe")
    _nonnegative_int("combination rank", rank)
    count = comb(universe_size, cardinality)
    if rank >= count:
        raise ValueError("combination rank is outside the cardinality block")
    if cardinality == 0:
        return ()

    remaining = rank
    upper = universe_size - 1
    values = [0] * cardinality
    for index in range(cardinality, 0, -1):
        low = index - 1
        high = upper
        while low < high:
            midpoint = (low + high + 1) // 2
            if comb(midpoint, index) <= remaining:
                low = midpoint
            else:
                high = midpoint - 1
        values[index - 1] = low
        remaining -= comb(low, index)
        upper = low - 1
    if remaining != 0:
        raise AssertionError("combinadic unrank left a nonzero remainder")
    result = tuple(values)
    if combination_rank(result, universe_size=universe_size) != rank:
        raise AssertionError("combinadic rank/unrank identity failed")
    return result


def subset_table_index(
    cards: tuple[int, ...],
    *,
    universe_size: int,
    maximum_cardinality: int,
) -> int:
    """Rank one subset in cardinality-major containment-table order."""

    _nonnegative_int("maximum subset cardinality", maximum_cardinality)
    if maximum_cardinality > universe_size:
        raise ValueError("maximum subset cardinality exceeds the universe")
    if len(cards) > maximum_cardinality:
        raise ValueError("subset is wider than the containment table")
    offset = sum(comb(universe_size, width) for width in range(len(cards)))
    return offset + combination_rank(cards, universe_size=universe_size)


@dataclass(frozen=True, slots=True)
class OccupiedCardGeometry:
    """Exact combinatorics for three closed source pairs and two query pairs."""

    available_cards: int = FROZEN_AVAILABLE_CARDS
    source_pairs: int = 3
    query_pairs: int = 2

    def __post_init__(self) -> None:
        _positive_int("available cards", self.available_cards)
        _positive_int("source pairs", self.source_pairs)
        _positive_int("query pairs", self.query_pairs)
        if self.source_cards + self.query_cards > self.available_cards:
            raise ValueError("source and query occupancies exceed the card universe")

    @property
    def source_cards(self) -> int:
        return 2 * self.source_pairs

    @property
    def query_cards(self) -> int:
        return 2 * self.query_pairs

    @property
    def source_occupancies(self) -> int:
        return comb(self.available_cards, self.source_cards)

    @property
    def query_occupancies(self) -> int:
        return comb(self.available_cards, self.query_cards)

    @property
    def source_pairings_per_occupancy(self) -> int:
        return factorial(self.source_cards) // (2**self.source_pairs)

    @property
    def query_pairings_per_occupancy(self) -> int:
        return factorial(self.query_cards) // (2**self.query_pairs)

    @property
    def source_labeled_records(self) -> int:
        return self.source_occupancies * self.source_pairings_per_occupancy

    @property
    def query_labeled_records(self) -> int:
        return self.query_occupancies * self.query_pairings_per_occupancy

    @property
    def containment_maximum_cardinality(self) -> int:
        return min(self.source_cards, self.query_cards)

    @property
    def containment_keys(self) -> int:
        return sum(
            comb(self.available_cards, width)
            for width in range(self.containment_maximum_cardinality + 1)
        )

    @property
    def forward_source_subset_visits(self) -> int:
        return sum(
            comb(self.source_cards, width)
            for width in range(self.containment_maximum_cardinality + 1)
        )

    @property
    def forward_query_signed_terms(self) -> int:
        return 2**self.query_cards

    @property
    def adjoint_query_occupancy_subset_visits(self) -> int:
        return 2**self.query_cards

    @property
    def adjoint_source_occupancy_signed_terms(self) -> int:
        return self.forward_source_subset_visits


def showdown_state_rank_trace(
    strength_codes: tuple[tuple[int, ...], ...],
    *,
    target_player: int,
    contenders: tuple[int, ...],
) -> tuple[int, ...]:
    """Derive deterministic showdown bond ranks without building transition arrays."""

    if len(strength_codes) < 2 or any(not row for row in strength_codes):
        raise ValueError("showdown rank trace requires nonempty strength axes")
    players = len(strength_codes)
    if isinstance(target_player, bool) or target_player not in range(players):
        raise ValueError("showdown target is outside the player axes")
    if tuple(sorted(set(contenders))) != contenders or any(
        seat not in range(players) for seat in contenders
    ):
        raise ValueError("showdown contenders must be sorted unique player indices")
    if any(
        isinstance(code, bool) or not isinstance(code, int) or code < 0
        for row in strength_codes
        for code in row
    ):
        raise ValueError("showdown strength codes must be nonnegative integers")

    states: set[tuple[int, int, int]] = {(-1, 0, 0)}
    ranks = []
    for player, axis in enumerate(strength_codes[:-1]):
        next_states = set()
        for maximum, multiplicity, target_in_argmax in states:
            for strength in set(axis):
                if player not in contenders:
                    advanced = (maximum, multiplicity, target_in_argmax)
                elif maximum < 0 or strength > maximum:
                    advanced = (strength, 1, int(player == target_player))
                elif strength == maximum:
                    advanced = (
                        maximum,
                        multiplicity + 1,
                        int(bool(target_in_argmax or player == target_player)),
                    )
                else:
                    advanced = (maximum, multiplicity, target_in_argmax)
                next_states.add(advanced)
        states = next_states
        ranks.append(len(states))
    return tuple(ranks)


@dataclass(frozen=True, slots=True)
class NumericArray:
    """One exact named numeric-array allocation row."""

    name: str
    dtype: str
    item_bytes: int
    shape: tuple[int, ...]
    placement: Placement
    phase: Phase

    def __post_init__(self) -> None:
        if not self.name or not self.dtype:
            raise ValueError("numeric array name and dtype must be nonempty")
        _positive_int("numeric array item bytes", self.item_bytes)
        if not self.shape or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in self.shape
        ):
            raise ValueError("numeric array shape must contain nonnegative integers")

    @property
    def elements(self) -> int:
        return prod(self.shape)

    @property
    def numeric_bytes(self) -> int:
        return self.elements * self.item_bytes


@dataclass(frozen=True, slots=True)
class StructuredAutomatonAllocation:
    """Array-exact storage for one direct deterministic showdown automaton."""

    hand_counts: tuple[int, ...]
    state_ranks: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.hand_counts) < 2 or len(self.state_ranks) != len(self.hand_counts) - 1:
            raise ValueError("automaton ranks must describe every nonterminal mode")
        for index, value in enumerate(self.hand_counts):
            _positive_int(f"automaton hand count {index}", value)
        for index, value in enumerate(self.state_ranks):
            _positive_int(f"automaton state rank {index}", value)

    def rows(self, *, placement: Placement, prefix: str) -> tuple[NumericArray, ...]:
        rows: list[NumericArray] = []
        previous = 1
        for mode, (hands, rank) in enumerate(
            zip(self.hand_counts[:-1], self.state_ranks, strict=True)
        ):
            rows.append(
                NumericArray(
                    f"{prefix}_transition_{mode}",
                    "int32",
                    INT32_BYTES,
                    (previous, hands),
                    placement,
                    "persistent",
                )
            )
            rows.append(
                NumericArray(
                    f"{prefix}_bond_states_{mode}",
                    "int32",
                    INT32_BYTES,
                    (rank, 3),
                    placement,
                    "persistent",
                )
            )
            previous = rank
        rows.append(
            NumericArray(
                f"{prefix}_terminal_values",
                "float64",
                FLOAT64_BYTES,
                (self.state_ranks[-1], self.hand_counts[-1]),
                placement,
                "persistent",
            )
        )
        rows.append(
            NumericArray(
                f"{prefix}_sunk_value",
                "float64",
                FLOAT64_BYTES,
                (1,),
                placement,
                "persistent",
            )
        )
        return tuple(rows)

    @property
    def numeric_bytes(self) -> int:
        return sum(
            row.numeric_bytes for row in self.rows(placement="host", prefix="automaton")
        )

    @property
    def forbidden_dense_tensor_train_bytes(self) -> int:
        signed_ranks = (1, *(rank + 1 for rank in self.state_ranks), 1)
        return sum(
            left * hands * right * FLOAT64_BYTES
            for left, hands, right in zip(
                signed_ranks[:-1], self.hand_counts, signed_ranks[1:], strict=True
            )
        )


@dataclass(frozen=True, slots=True)
class QuotientWork:
    """Semantic logical work; fields are counts, never latency estimates."""

    source_occupancy_visits: int
    source_pairing_record_visits: int
    weighted_state_and_reach_accumulations: int
    source_coefficient_scalar_zero_writes: int
    containment_vector_updates: int
    containment_scalar_additions: int
    labeled_query_record_visits: int
    signed_query_vector_terms: int
    signed_query_scalar_additions: int
    query_payoff_state_folds: int
    query_reach_folds: int
    query_hand_scalar_reductions: int


@dataclass(frozen=True, slots=True)
class QuotientTopologyWork:
    """One-time preparation work for immutable implicit and query topology."""

    binomial_table_cells: int
    source_pairing_template_entries: int
    query_pairing_template_entries: int
    query_occupancy_visits: int
    labeled_query_records_generated: int
    labeled_query_numeric_field_writes: int


@dataclass(frozen=True, slots=True)
class QuotientAdjointWork:
    """Logical work for the exact transpose of the deployment-shaped matrix."""

    labeled_query_record_visits: int
    labeled_query_aggregation_scalar_additions: int
    query_occupancy_scalar_zero_writes: int
    containment_vector_updates: int
    containment_scalar_additions: int
    source_occupancy_visits: int
    signed_source_vector_terms: int
    signed_source_scalar_additions: int
    streamed_source_label_record_visits: int
    streamed_source_label_scalar_writes: int


@dataclass(frozen=True, slots=True)
class QuotientCapacityModel:
    """Complete proposed numeric-array layout for one target-specific pass."""

    geometry: OccupiedCardGeometry
    automata: tuple[StructuredAutomatonAllocation, ...]
    source_state_ranks: tuple[int, ...]
    component_count: int = 1
    opponent_hand_count: int = FROZEN_OPPONENT_HANDS
    target_hand_count: int = 1
    source_chunk_occupancies: int = FROZEN_SOURCE_CHUNK
    query_chunk_records: int = FROZEN_QUERY_CHUNK

    def __post_init__(self) -> None:
        _positive_int("component count", self.component_count)
        _positive_int("opponent hand count", self.opponent_hand_count)
        _positive_int("target hand count", self.target_hand_count)
        _positive_int("source chunk occupancies", self.source_chunk_occupancies)
        _positive_int("query chunk records", self.query_chunk_records)
        if not self.source_state_ranks or len(self.source_state_ranks) != len(self.automata):
            raise ValueError("one positive source state rank is required per automaton")
        for index, value in enumerate(self.source_state_ranks):
            _positive_int(f"source state rank {index}", value)
            if self.automata[index].state_ranks[2] != value:
                raise ValueError("source state rank differs from the split-three automaton rank")
        expected_counts = (
            self.opponent_hand_count,
            self.opponent_hand_count,
            self.opponent_hand_count,
            self.target_hand_count,
            self.opponent_hand_count,
            self.opponent_hand_count,
        )
        if any(automaton.hand_counts != expected_counts for automaton in self.automata):
            raise ValueError("automaton axes differ from the target-specific 3/3 ordering")
        if self.opponent_hand_count > (2**31 - 1):
            raise ValueError("opponent hand indices do not fit int32")
        if self.geometry.source_occupancies > (2**32):
            raise ValueError("source occupancy ranks do not fit uint32")

    @property
    def term_count(self) -> int:
        return len(self.source_state_ranks)

    @property
    def feature_width(self) -> int:
        return self.component_count * sum(rank + 1 for rank in self.source_state_ranks)

    @property
    def payoff_state_width(self) -> int:
        return sum(self.source_state_ranks)

    @property
    def all_axis_entries(self) -> int:
        return (5 * self.opponent_hand_count) + self.target_hand_count

    @property
    def unique_hand_entries(self) -> int:
        return self.opponent_hand_count + self.target_hand_count

    def _shared_rows(self, placement: Placement) -> tuple[NumericArray, ...]:
        records = self.geometry.query_labeled_records
        rows = [
            NumericArray("query_card_masks", "uint64", UINT64_BYTES, (records,), placement, "persistent"),
            NumericArray("query_first_hand_indices", "int32", INT32_BYTES, (records,), placement, "persistent"),
            NumericArray("query_second_hand_indices", "int32", INT32_BYTES, (records,), placement, "persistent"),
            NumericArray(
                "binomial_table",
                "uint64",
                UINT64_BYTES,
                (self.geometry.available_cards + 1, self.geometry.source_cards + 1),
                placement,
                "persistent",
            ),
            NumericArray(
                "containment_cardinality_offsets",
                "uint64",
                UINT64_BYTES,
                (self.geometry.containment_maximum_cardinality + 1,),
                placement,
                "persistent",
            ),
            NumericArray(
                "source_local_pairing_template",
                "uint8",
                UINT8_BYTES,
                (self.geometry.source_pairings_per_occupancy, self.geometry.source_cards),
                placement,
                "persistent",
            ),
            NumericArray(
                "query_local_pairing_template",
                "uint8",
                UINT8_BYTES,
                (self.geometry.query_pairings_per_occupancy, self.geometry.query_cards),
                placement,
                "persistent",
            ),
            NumericArray("unique_hand_masks", "uint64", UINT64_BYTES, (self.unique_hand_entries,), placement, "persistent"),
            NumericArray("unique_strength_codes", "int32", INT32_BYTES, (self.unique_hand_entries,), placement, "persistent"),
            NumericArray("mixture_weights", "float64", FLOAT64_BYTES, (self.component_count,), placement, "persistent"),
            NumericArray(
                "seat_unary_weights",
                "float64",
                FLOAT64_BYTES,
                (self.component_count, self.all_axis_entries),
                placement,
                "persistent",
            ),
            NumericArray(
                "term_mode_factors",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, self.all_axis_entries),
                placement,
                "persistent",
            ),
        ]
        for index, automaton in enumerate(self.automata):
            rows.extend(automaton.rows(placement=placement, prefix=f"automaton_{index}"))
        return tuple(rows)

    @property
    def host_persistent_rows(self) -> tuple[NumericArray, ...]:
        return self._shared_rows("host")

    @property
    def device_persistent_rows(self) -> tuple[NumericArray, ...]:
        return self._shared_rows("device")

    @property
    def source_phase_rows(self) -> tuple[NumericArray, ...]:
        return (
            NumericArray(
                "containment_marginals",
                "float64",
                FLOAT64_BYTES,
                (self.geometry.containment_keys, self.feature_width),
                "device",
                "source",
            ),
            NumericArray(
                "source_chunk_coefficients",
                "float64",
                FLOAT64_BYTES,
                (min(self.source_chunk_occupancies, self.geometry.source_occupancies), self.feature_width),
                "device",
                "source",
            ),
            NumericArray(
                "source_chunk_occupancy_ranks",
                "uint32",
                UINT32_BYTES,
                (min(self.source_chunk_occupancies, self.geometry.source_occupancies),),
                "device",
                "source",
            ),
        )

    @property
    def query_phase_rows(self) -> tuple[NumericArray, ...]:
        chunk = min(self.query_chunk_records, self.geometry.query_labeled_records)
        return (
            NumericArray(
                "containment_marginals",
                "float64",
                FLOAT64_BYTES,
                (self.geometry.containment_keys, self.feature_width),
                "device",
                "query",
            ),
            NumericArray(
                "query_chunk_payoff_state_rows",
                "float64",
                FLOAT64_BYTES,
                (chunk, self.payoff_state_width),
                "device",
                "query",
            ),
            NumericArray(
                "query_chunk_compatible_features",
                "float64",
                FLOAT64_BYTES,
                (chunk, self.feature_width),
                "device",
                "query",
            ),
            NumericArray(
                "query_chunk_component_products",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, chunk, self.component_count),
                "device",
                "query",
            ),
            NumericArray(
                "query_numerator_and_reach_records",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, self.geometry.query_labeled_records, 2),
                "device",
                "query",
            ),
            NumericArray(
                "target_hand_numerator_and_reach",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, self.target_hand_count, 2),
                "device",
                "query",
            ),
        )

    @property
    def host_result_rows(self) -> tuple[NumericArray, ...]:
        return (
            NumericArray(
                "host_query_numerator_and_reach_records",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, self.geometry.query_labeled_records, 2),
                "host",
                "result",
            ),
            NumericArray(
                "host_target_hand_float_fields",
                "float64",
                FLOAT64_BYTES,
                (self.term_count, self.target_hand_count, 6),
                "host",
                "result",
            ),
            NumericArray(
                "host_target_hand_positive_reach",
                "bool",
                UINT8_BYTES,
                (self.term_count, self.target_hand_count),
                "host",
                "result",
            ),
        )

    @property
    def host_adjoint_staging_rows(self) -> tuple[NumericArray, ...]:
        chunk = min(self.query_chunk_records, self.geometry.query_labeled_records)
        return (
            NumericArray(
                "host_adjoint_labeled_query_input_chunk",
                "float64",
                FLOAT64_BYTES,
                (chunk, self.feature_width),
                "host",
                "adjoint",
            ),
            NumericArray(
                "host_adjoint_source_label_output_chunk",
                "float64",
                FLOAT64_BYTES,
                (chunk, self.feature_width),
                "host",
                "adjoint",
            ),
        )

    @property
    def adjoint_phase_rows(self) -> tuple[NumericArray, ...]:
        query_chunk = min(
            self.query_chunk_records,
            self.geometry.query_labeled_records,
        )
        occupancy_chunk = min(
            (query_chunk + self.geometry.query_pairings_per_occupancy - 1)
            // self.geometry.query_pairings_per_occupancy,
            self.geometry.query_occupancies,
        )
        source_chunk = min(
            self.source_chunk_occupancies,
            self.geometry.source_occupancies,
        )
        return (
            NumericArray(
                "adjoint_containment_marginals",
                "float64",
                FLOAT64_BYTES,
                (self.geometry.containment_keys, self.feature_width),
                "device",
                "adjoint",
            ),
            NumericArray(
                "adjoint_labeled_query_input_chunk",
                "float64",
                FLOAT64_BYTES,
                (query_chunk, self.feature_width),
                "device",
                "adjoint",
            ),
            NumericArray(
                "adjoint_query_occupancy_chunk",
                "float64",
                FLOAT64_BYTES,
                (occupancy_chunk, self.feature_width),
                "device",
                "adjoint",
            ),
            NumericArray(
                "adjoint_source_occupancy_chunk",
                "float64",
                FLOAT64_BYTES,
                (source_chunk, self.feature_width),
                "device",
                "adjoint",
            ),
            NumericArray(
                "adjoint_source_label_output_chunk",
                "float64",
                FLOAT64_BYTES,
                (query_chunk, self.feature_width),
                "device",
                "adjoint",
            ),
        )

    @property
    def host_persistent_numeric_bytes(self) -> int:
        return sum(row.numeric_bytes for row in self.host_persistent_rows)

    @property
    def host_peak_numeric_bytes(self) -> int:
        return self.host_persistent_numeric_bytes + max(
            sum(row.numeric_bytes for row in self.host_result_rows),
            sum(row.numeric_bytes for row in self.host_adjoint_staging_rows),
        )

    @property
    def device_persistent_numeric_bytes(self) -> int:
        return sum(row.numeric_bytes for row in self.device_persistent_rows)

    @property
    def device_source_phase_numeric_bytes(self) -> int:
        return self.device_persistent_numeric_bytes + sum(
            row.numeric_bytes for row in self.source_phase_rows
        )

    @property
    def device_query_phase_numeric_bytes(self) -> int:
        return self.device_persistent_numeric_bytes + sum(
            row.numeric_bytes for row in self.query_phase_rows
        )

    @property
    def device_adjoint_phase_numeric_bytes(self) -> int:
        return self.device_persistent_numeric_bytes + sum(
            row.numeric_bytes for row in self.adjoint_phase_rows
        )

    @property
    def device_peak_numeric_bytes(self) -> int:
        return max(
            self.device_source_phase_numeric_bytes,
            self.device_query_phase_numeric_bytes,
            self.device_adjoint_phase_numeric_bytes,
        )

    @property
    def allocated_tensor_train_numeric_bytes(self) -> int:
        return 0

    @property
    def forbidden_dense_tensor_train_bytes(self) -> int:
        return sum(
            automaton.forbidden_dense_tensor_train_bytes for automaton in self.automata
        )

    @property
    def persistent_labeled_source_numeric_bytes(self) -> int:
        return 0

    @property
    def sparse_incidence_numeric_bytes(self) -> int:
        return 0

    @property
    def excluded_nonnumeric_classes(self) -> tuple[str, ...]:
        return _EXCLUDED_NONNUMERIC_CLASSES

    @property
    def forward_work(self) -> QuotientWork:
        geometry = self.geometry
        return QuotientWork(
            source_occupancy_visits=geometry.source_occupancies,
            source_pairing_record_visits=geometry.source_labeled_records,
            weighted_state_and_reach_accumulations=(
                geometry.source_labeled_records
                * 2
                * self.term_count
                * self.component_count
            ),
            source_coefficient_scalar_zero_writes=(
                geometry.source_occupancies * self.feature_width
            ),
            containment_vector_updates=(
                geometry.source_occupancies * geometry.forward_source_subset_visits
            ),
            containment_scalar_additions=(
                geometry.source_occupancies
                * geometry.forward_source_subset_visits
                * self.feature_width
            ),
            labeled_query_record_visits=geometry.query_labeled_records,
            signed_query_vector_terms=(
                geometry.query_labeled_records * geometry.forward_query_signed_terms
            ),
            signed_query_scalar_additions=(
                geometry.query_labeled_records
                * geometry.forward_query_signed_terms
                * self.feature_width
            ),
            query_payoff_state_folds=(
                geometry.query_labeled_records
                * self.component_count
                * self.payoff_state_width
            ),
            query_reach_folds=(
                geometry.query_labeled_records
                * self.component_count
                * self.term_count
            ),
            query_hand_scalar_reductions=(
                geometry.query_labeled_records * self.term_count * 2
            ),
        )

    @property
    def topology_preparation_work(self) -> QuotientTopologyWork:
        geometry = self.geometry
        return QuotientTopologyWork(
            binomial_table_cells=(
                (geometry.available_cards + 1) * (geometry.source_cards + 1)
            ),
            source_pairing_template_entries=(
                geometry.source_pairings_per_occupancy * geometry.source_cards
            ),
            query_pairing_template_entries=(
                geometry.query_pairings_per_occupancy * geometry.query_cards
            ),
            query_occupancy_visits=geometry.query_occupancies,
            labeled_query_records_generated=geometry.query_labeled_records,
            labeled_query_numeric_field_writes=(
                geometry.query_labeled_records * 3
            ),
        )

    @property
    def cold_forward_work(self) -> QuotientWork:
        return self.forward_work

    @property
    def source_seat_refresh_work(self) -> QuotientWork:
        return self.forward_work

    @property
    def query_only_refresh_work(self) -> QuotientWork:
        full = self.forward_work
        return QuotientWork(
            source_occupancy_visits=0,
            source_pairing_record_visits=0,
            weighted_state_and_reach_accumulations=0,
            source_coefficient_scalar_zero_writes=0,
            containment_vector_updates=0,
            containment_scalar_additions=0,
            labeled_query_record_visits=full.labeled_query_record_visits,
            signed_query_vector_terms=full.signed_query_vector_terms,
            signed_query_scalar_additions=full.signed_query_scalar_additions,
            query_payoff_state_folds=full.query_payoff_state_folds,
            query_reach_folds=full.query_reach_folds,
            query_hand_scalar_reductions=full.query_hand_scalar_reductions,
        )

    @property
    def adjoint_work(self) -> QuotientAdjointWork:
        geometry = self.geometry
        return QuotientAdjointWork(
            labeled_query_record_visits=geometry.query_labeled_records,
            labeled_query_aggregation_scalar_additions=(
                geometry.query_labeled_records * self.feature_width
            ),
            query_occupancy_scalar_zero_writes=(
                geometry.query_occupancies * self.feature_width
            ),
            containment_vector_updates=(
                geometry.query_occupancies
                * geometry.adjoint_query_occupancy_subset_visits
            ),
            containment_scalar_additions=(
                geometry.query_occupancies
                * geometry.adjoint_query_occupancy_subset_visits
                * self.feature_width
            ),
            source_occupancy_visits=geometry.source_occupancies,
            signed_source_vector_terms=(
                geometry.source_occupancies
                * geometry.adjoint_source_occupancy_signed_terms
            ),
            signed_source_scalar_additions=(
                geometry.source_occupancies
                * geometry.adjoint_source_occupancy_signed_terms
                * self.feature_width
            ),
            streamed_source_label_record_visits=geometry.source_labeled_records,
            streamed_source_label_scalar_writes=(
                geometry.source_labeled_records * self.feature_width
            ),
        )

    @property
    def admission_checks(self) -> dict[str, bool]:
        return {
            "host_persistent_within_numeric_cap": (
                self.host_persistent_numeric_bytes <= HOST_NUMERIC_CAP_BYTES
            ),
            "host_peak_within_numeric_cap": (
                self.host_peak_numeric_bytes <= HOST_NUMERIC_CAP_BYTES
            ),
            "host_peak_preserves_minimum_capacity_reserve": (
                self.host_peak_numeric_bytes + HOST_RESERVE_BYTES
                <= MINIMUM_HOST_PHYSICAL_BYTES
            ),
            "device_persistent_within_numeric_cap": (
                self.device_persistent_numeric_bytes <= DEVICE_NUMERIC_CAP_BYTES
            ),
            "device_peak_within_numeric_cap": (
                self.device_peak_numeric_bytes <= DEVICE_NUMERIC_CAP_BYTES
            ),
            "device_peak_preserves_minimum_capacity_reserve": (
                self.device_peak_numeric_bytes + DEVICE_RESERVE_BYTES
                <= MINIMUM_DEVICE_PHYSICAL_BYTES
            ),
            "persistent_labeled_source_is_absent": (
                self.persistent_labeled_source_numeric_bytes == 0
            ),
            "sparse_incidence_is_absent": self.sparse_incidence_numeric_bytes == 0,
            "allocated_tensor_train_is_absent": (
                self.allocated_tensor_train_numeric_bytes == 0
            ),
            "forbidden_tensor_train_is_priced": (
                self.forbidden_dense_tensor_train_bytes > 0
            ),
        }

    @property
    def source_only_admitted(self) -> bool:
        return all(self.admission_checks.values())


def fixture_capacity_model() -> QuotientCapacityModel:
    """Return the exact frozen one-term, one-component fixture model."""

    geometry = OccupiedCardGeometry()
    automaton = StructuredAutomatonAllocation(
        hand_counts=(
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
            1,
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
        ),
        state_ranks=FROZEN_FIXTURE_STATE_RANKS,
    )
    return QuotientCapacityModel(
        geometry=geometry,
        automata=(automaton,),
        source_state_ranks=(FROZEN_FIXTURE_SOURCE_STATE_RANK,),
    )


def safe_feature_envelope_model() -> QuotientCapacityModel:
    """Return a safe axis-width envelope, not an observed or attainable state."""

    geometry = OccupiedCardGeometry()
    automaton = StructuredAutomatonAllocation(
        hand_counts=(
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
            1,
            FROZEN_OPPONENT_HANDS,
            FROZEN_OPPONENT_HANDS,
        ),
        state_ranks=SAFE_AUTOMATON_STATE_RANKS,
    )
    return QuotientCapacityModel(
        geometry=geometry,
        automata=(automaton,),
        source_state_ranks=(SAFE_SOURCE_STATE_RANK,),
    )
