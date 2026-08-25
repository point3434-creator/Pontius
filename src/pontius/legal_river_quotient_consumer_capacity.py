"""Source-only capacity seal for the legal river quotient consumer.

This module implements ADR-0387's arithmetic and bounded exact seam.  It is
deliberately CuPy-free: full-width objects are represented only by typed shape
rows, and the only quotient values evaluated here use the complete ten-card
control population.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from math import comb, prod
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping, Sequence

import numpy as np

from .legal_river_quotient_bridge import (
    LegalRiverQuotientBridge,
    build_preregistered_legal_river_context,
    compile_legal_river_quotient_bridge,
)
from .occupied_card_quotient import (
    ExactQuotientCoefficients,
    OccupiedCardQuotientTopology,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/legal-river-quotient-consumer-capacity-v1.json"
)
PREREGISTERED_CONFIG_SHA256 = (
    "7cc8fec2b6cb6b7b135f2f7ea5dd74e1a5a3cd4b4a2c48d2b6f8ddde141bb71d"
)

PHASES = (
    "host_bridge",
    "device_resident",
    "forward_slice_0_source",
    "forward_slice_0_fold",
    "forward_slice_1_source",
    "forward_slice_1_fold",
    "forward_release",
    "adjoint_slice_0_query",
    "adjoint_slice_0_source",
    "adjoint_slice_1_query",
    "adjoint_slice_1_source",
    "release",
)
_PHASE_INDEX = MappingProxyType({name: index for index, name in enumerate(PHASES)})

EXPECTED_FEATURE_RANGES = ((0, 128), (128, 176))
SOURCE_STATE_FEATURES = 175
REACH_GLOBAL_FEATURE = 175
TOTAL_FEATURE_WIDTH = 176
MAXIMUM_WORKSPACE_WIDTH = 128

HOST_NUMERIC_CAP_BYTES = 48_000_000_000
DEVICE_NUMERIC_CAP_BYTES = 12_000_000_000
HOST_RESERVE_BYTES = 8_000_000_000
DEVICE_RESERVE_BYTES = 2_000_000_000
MINIMUM_HOST_PHYSICAL_BYTES = 60_000_000_000
MINIMUM_DEVICE_PHYSICAL_BYTES = 16_000_000_000
LIBRARY_SCRATCH_BYTES = 67_108_864

CLAIMS = MappingProxyType(
    {
        "full_width_quotient_value": None,
        "device_execution_result": None,
        "live_allocation_result": None,
        "resolver_iteration_result": None,
        "solve_result": None,
        "action_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "blueprint_result": None,
        "poker_strength_result": None,
    }
)
EXCLUDED_MEMORY_CLASSES = (
    "Python objects and interpreter storage",
    "allocator fragmentation and alignment outside named arrays",
    "CuPy pool retention beyond named live arrays",
    "CUDA context driver module kernel code and page tables",
    "kernel registers local memory and compiler-selected temporaries",
    "operating-system and unrelated-process activity",
)

_DEPENDENCY_PATHS = MappingProxyType(
    {
        "adr0386": _ROOT
        / "docs/decisions/ADR-0386-source-seal-the-actual-context-quotient-bridge.md",
        "bridge_config": _ROOT
        / "experiments/configs/legal-river-quotient-bridge-v1.json",
        "full_width_quotient_capacity": _ROOT
        / "src/pontius/full_width_occupied_card_quotient_capacity.py",
        "gpu_occupied_card_quotient": _ROOT
        / "src/pontius/gpu_occupied_card_quotient.py",
        "gpu_quotient_staged_scaling": _ROOT
        / "src/pontius/gpu_quotient_staged_scaling.py",
        "legal_river_quotient_bridge": _ROOT
        / "src/pontius/legal_river_quotient_bridge.py",
        "literal_45_quotient_liveness": _ROOT
        / "src/pontius/literal_45_quotient_liveness.py",
        "occupied_card_quotient": _ROOT
        / "src/pontius/occupied_card_quotient.py",
        "structured_showdown_automaton": _ROOT
        / "src/pontius/structured_showdown_automaton.py",
    }
)

Placement = Literal["host", "device"]


def _canonical_lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_consumer_capacity_config(
    path: Path = _CONFIG,
) -> dict[str, object]:
    """Load only the exact prospective ADR-0387 config."""

    if _canonical_lf_sha256(path) != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("consumer-capacity config digest differs")
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if parsed.get("schema_version") != (
        "legal-river-quotient-consumer-capacity-config-v1"
    ):
        raise ValueError("consumer-capacity config schema differs")
    if parsed.get("evidence_stage") != (
        "preregistered_after_adr0386_before_capacity_source_cupy_or_full_width_value"
    ):
        raise ValueError("consumer-capacity evidence stage differs")
    return parsed


def verify_preregistered_dependencies(config: Mapping[str, object]) -> None:
    expected = config.get("expected_sources")
    if not isinstance(expected, dict) or set(expected) != set(_DEPENDENCY_PATHS):
        raise ValueError("consumer-capacity dependency set differs")
    for label, path in _DEPENDENCY_PATHS.items():
        if _canonical_lf_sha256(path) != expected[label]:
            raise ValueError(f"consumer-capacity dependency {label} differs")


def _positive_integer(value: object, *, label: str) -> int:
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return item


@dataclass(frozen=True, slots=True)
class FeatureSlice:
    ordinal: int
    start: int
    stop: int
    global_feature_indices: tuple[int, ...]
    owns_reach_feature: bool

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int):
            raise ValueError("feature-slice ordinal must be an integer")
        if self.ordinal < 0 or self.start < 0 or self.stop <= self.start:
            raise ValueError("feature-slice range is invalid")
        if self.global_feature_indices != tuple(range(self.start, self.stop)):
            raise ValueError("feature slice uses slice-local state identity")
        if not isinstance(self.owns_reach_feature, bool):
            raise ValueError("reach ownership must be Boolean")

    @property
    def width(self) -> int:
        return self.stop - self.start

    def owns(self, feature: int) -> bool:
        return self.start <= feature < self.stop


def frozen_feature_slices() -> tuple[FeatureSlice, ...]:
    return tuple(
        FeatureSlice(
            index,
            start,
            stop,
            tuple(range(start, stop)),
            start <= REACH_GLOBAL_FEATURE < stop,
        )
        for index, (start, stop) in enumerate(EXPECTED_FEATURE_RANGES)
    )


def feature_slices_from_config(
    config: Mapping[str, object],
) -> tuple[FeatureSlice, ...]:
    raw = config.get("feature_slices")
    if not isinstance(raw, dict):
        raise ValueError("feature-slice config is malformed")
    ranges = raw.get("ordered_ranges")
    if not isinstance(ranges, list) or any(
        not isinstance(item, list) or len(item) != 2 for item in ranges
    ):
        raise ValueError("feature-slice ranges are malformed")
    result = tuple(
        FeatureSlice(
            index,
            int(pair[0]),
            int(pair[1]),
            tuple(range(int(pair[0]), int(pair[1]))),
            int(pair[0]) <= REACH_GLOBAL_FEATURE < int(pair[1]),
        )
        for index, pair in enumerate(ranges)
    )
    validated = validate_feature_slices(
        result,
        maximum_workspace_width=int(raw["maximum_workspace_width"]),
    )
    if raw.get("ordered_widths") != [item.width for item in validated]:
        raise ValueError("feature-slice logical widths differ")
    required_true = (
        "require_complete_disjoint_coverage",
        "require_global_state_identity",
        "require_reach_owned_by_exactly_one_slice",
        "require_partial_numerator_accumulation_before_normalization",
        "require_partial_reach_accumulation_before_normalization",
        "forbid_per_slice_conditional_values",
        "require_exact_recombination_in_bounded_control",
        "require_reversed_slice_order_control",
    )
    if any(raw.get(name) is not True for name in required_true):
        raise ValueError("feature-slice semantic requirement differs")
    return validated


def validate_feature_slices(
    slices: Sequence[FeatureSlice],
    *,
    total_width: int = TOTAL_FEATURE_WIDTH,
    reach_feature: int = REACH_GLOBAL_FEATURE,
    maximum_workspace_width: int = MAXIMUM_WORKSPACE_WIDTH,
) -> tuple[FeatureSlice, ...]:
    """Reject any partition or identity other than ADR-0387's global one."""

    result = tuple(slices)
    if tuple((item.start, item.stop) for item in result) != EXPECTED_FEATURE_RANGES:
        raise ValueError("feature slices are missing, overlapping, or reordered")
    if tuple(item.ordinal for item in result) != tuple(range(len(result))):
        raise ValueError("feature-slice ordinals are reordered")
    flattened = tuple(feature for item in result for feature in item.global_feature_indices)
    if flattened != tuple(range(total_width)):
        raise ValueError("feature slices do not preserve global state identity")
    if sum(item.owns_reach_feature for item in result) != 1:
        raise ValueError("reach feature must be owned by exactly one slice")
    if any(
        item.owns_reach_feature != item.owns(reach_feature) for item in result
    ):
        raise ValueError("reach ownership differs from its global feature slice")
    if max(item.width for item in result) > maximum_workspace_width:
        raise ValueError("feature slice exceeds the physical workspace width")
    if sum(item.width for item in result) != total_width:
        raise ValueError("logical feature work differs from total width")
    return result


@dataclass(frozen=True, slots=True)
class ForwardRecordChunk:
    records: int

    def __post_init__(self) -> None:
        _positive_integer(self.records, label="forward record chunk")


@dataclass(frozen=True, slots=True)
class AdjointOccupancyChunk:
    occupancies: int

    def __post_init__(self) -> None:
        _positive_integer(self.occupancies, label="adjoint occupancy chunk")


@dataclass(frozen=True, slots=True)
class SourceOccupancyChunk:
    occupancies: int

    def __post_init__(self) -> None:
        _positive_integer(self.occupancies, label="source occupancy chunk")


@dataclass(frozen=True, slots=True)
class StreamingContract:
    forward: ForwardRecordChunk
    adjoint_query: AdjointOccupancyChunk
    adjoint_source: SourceOccupancyChunk
    query_labels_per_occupancy: int

    def __post_init__(self) -> None:
        labels = _positive_integer(
            self.query_labels_per_occupancy,
            label="query labels per occupancy",
        )
        if self.adjoint_query_records % labels:
            raise ValueError("adjoint chunk cuts a complete label group")
        if self.forward.records == self.adjoint_query_records:
            raise ValueError("forward and adjoint chunk knobs were reused")

    @property
    def adjoint_query_records(self) -> int:
        return self.adjoint_query.occupancies * self.query_labels_per_occupancy


def streaming_contract_from_config(config: Mapping[str, object]) -> StreamingContract:
    raw = config.get("streaming")
    if not isinstance(raw, dict):
        raise ValueError("streaming config is malformed")
    contract = StreamingContract(
        forward=ForwardRecordChunk(int(raw["forward_query_record_chunk"])),
        adjoint_query=AdjointOccupancyChunk(
            int(raw["adjoint_query_occupancy_chunk"])
        ),
        adjoint_source=SourceOccupancyChunk(
            int(raw["adjoint_source_occupancy_chunk"])
        ),
        query_labels_per_occupancy=int(raw["query_labels_per_occupancy"]),
    )
    if contract.forward.records != 65_536:
        raise ValueError("forward record chunk differs from ADR-0387")
    if contract.adjoint_query.occupancies != 10_922:
        raise ValueError("adjoint occupancy chunk differs from ADR-0387")
    if contract.adjoint_query_records != int(raw["adjoint_query_record_chunk"]):
        raise ValueError("adjoint record count is not occupancy-derived")
    if contract.adjoint_source.occupancies != 32_768:
        raise ValueError("source occupancy chunk differs from ADR-0387")
    return contract


def chunk_spans(total: int, chunk: int, *, group: int = 1) -> tuple[tuple[int, int], ...]:
    """Return a complete ordered partition without cutting semantic groups."""

    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("chunk total must be a nonnegative integer")
    width = _positive_integer(chunk, label="chunk width")
    alignment = _positive_integer(group, label="chunk group")
    if total % alignment or width % alignment:
        raise ValueError("chunk partition cuts a semantic group")
    return tuple(
        (start, min(start + width, total)) for start in range(0, total, width)
    )


def normalize_after_recombination(
    partial_numerators: Sequence[Fraction],
    partial_reaches: Sequence[Fraction],
    *,
    consumed_slice_ordinals: Sequence[int],
) -> Fraction:
    """Normalize only after every frozen feature slice has contributed."""

    if tuple(sorted(consumed_slice_ordinals)) != (0, 1):
        raise ValueError("per-slice conditional normalization is forbidden")
    if len(partial_numerators) != 2 or len(partial_reaches) != 2:
        raise ValueError("normalization requires both feature slices")
    reach = sum(partial_reaches, Fraction(0))
    if reach == 0:
        raise ZeroDivisionError("recombined reach is zero")
    return sum(partial_numerators, Fraction(0)) / reach


@dataclass(frozen=True, slots=True)
class NumericLifetimeRow:
    name: str
    placement: Placement
    semantic_category: str
    dtype: str
    shape: tuple[int, ...]
    born: str
    last_live: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.isidentifier():
            raise ValueError("lifetime row name must be an identifier")
        if self.placement not in ("host", "device"):
            raise ValueError("lifetime row placement is invalid")
        if not self.semantic_category:
            raise ValueError("lifetime row semantic category is empty")
        np.dtype(self.dtype)
        if not self.shape or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in self.shape
        ):
            raise ValueError("lifetime row shape must be positive integers")
        if self.born not in _PHASE_INDEX or self.last_live not in _PHASE_INDEX:
            raise ValueError("lifetime row names an unknown phase")
        if _PHASE_INDEX[self.born] > _PHASE_INDEX[self.last_live]:
            raise ValueError("lifetime row dies before birth")

    @property
    def elements(self) -> int:
        return prod(self.shape)

    @property
    def numeric_bytes(self) -> int:
        return self.elements * np.dtype(self.dtype).itemsize

    def live_at(self, phase: str) -> bool:
        if phase not in _PHASE_INDEX:
            raise ValueError("unknown lifetime phase")
        return _PHASE_INDEX[self.born] <= _PHASE_INDEX[phase] <= _PHASE_INDEX[
            self.last_live
        ]


def _row(
    name: str,
    placement: Placement,
    semantic_category: str,
    values_or_dtype: np.ndarray | str | np.dtype[object],
    shape: Sequence[int] | None,
    born: str,
    last_live: str,
) -> NumericLifetimeRow:
    if isinstance(values_or_dtype, np.ndarray):
        dtype = values_or_dtype.dtype.str
        resolved_shape = tuple(int(value) for value in values_or_dtype.shape)
    else:
        dtype = np.dtype(values_or_dtype).str
        if shape is None:
            raise ValueError("shape is required when no array is supplied")
        resolved_shape = tuple(int(value) for value in shape)
    return NumericLifetimeRow(
        name=name,
        placement=placement,
        semantic_category=semantic_category,
        dtype=dtype,
        shape=resolved_shape,
        born=born,
        last_live=last_live,
    )


def _automaton_runtime_rows(
    bridge: LegalRiverQuotientBridge,
    *,
    prefix: str,
    placement: Placement,
    category: str,
    born: str,
    last_live: str,
) -> list[NumericLifetimeRow]:
    automaton = bridge.fixture.automaton
    rows = [
        _row(
            f"{prefix}_transition_{index}",
            placement,
            category,
            values,
            None,
            born,
            last_live,
        )
        for index, values in enumerate(automaton.transitions)
    ]
    rows.append(
        _row(
            f"{prefix}_terminal_winner_values",
            placement,
            category,
            automaton.terminal_winner_values,
            None,
            born,
            last_live,
        )
    )
    rows.append(
        _row(
            f"{prefix}_sunk_scalar",
            placement,
            category,
            "float64",
            (1,),
            born,
            last_live,
        )
    )
    return rows


def _bridge_consumer_rows(
    bridge: LegalRiverQuotientBridge,
    *,
    prefix: str,
    placement: Placement,
    born: str,
    last_live: str,
) -> tuple[NumericLifetimeRow, ...]:
    category = "bridge_resident" if placement == "host" else "consumer_resident"
    rows = _automaton_runtime_rows(
        bridge,
        prefix=f"{prefix}_automaton",
        placement=placement,
        category=category,
        born=born,
        last_live=last_live,
    )
    fixture = bridge.fixture
    arrays = (
        ("mixture_weights", fixture.mixture_weights),
        ("unary_weights", fixture.unary_weights),
        ("mode_factors", fixture.mode_factors),
        ("pair_to_hand", fixture.pair_to_hand),
        ("source_pairing_template", fixture.source_pair_positions),
        ("query_masks", fixture.query_masks),
        ("query_hand_indices", fixture.query_hand_indices),
        ("unary_offsets", fixture.unary_offsets),
    )
    rows.extend(
        _row(
            f"{prefix}_{name}",
            placement,
            category,
            values,
            None,
            born,
            last_live,
        )
        for name, values in arrays
    )
    return tuple(rows)


def _bridge_validation_rows(
    bridge: LegalRiverQuotientBridge,
) -> tuple[NumericLifetimeRow, ...]:
    rows: list[NumericLifetimeRow] = []
    for index, values in enumerate(bridge.fixture.automaton.bond_states):
        rows.append(
            _row(
                f"host_validation_automaton_bond_states_{index}",
                "host",
                "bridge_validation",
                values,
                None,
                "host_bridge",
                "release",
            )
        )
    belief = bridge.factorized_belief
    rows.append(
        _row(
            "host_validation_factorized_mixture_weights",
            "host",
            "bridge_validation",
            belief.mixture_weights,
            None,
            "host_bridge",
            "release",
        )
    )
    for index, values in enumerate(belief.unary_weights):
        rows.append(
            _row(
                f"host_validation_factorized_unary_weights_{index}",
                "host",
                "bridge_validation",
                values,
                None,
                "host_bridge",
                "release",
            )
        )
    for index, values in enumerate(belief.hand_masks):
        rows.append(
            _row(
                f"host_validation_factorized_hand_masks_{index}",
                "host",
                "bridge_validation",
                values,
                None,
                "host_bridge",
                "release",
            )
        )
    return tuple(rows)


def _source_geometry(bridge: LegalRiverQuotientBridge) -> dict[str, int]:
    fixture = bridge.fixture
    cards = fixture.available_cards
    source_cards = 6
    query_cards = 4
    query_occupancies = comb(cards, query_cards)
    if len(fixture.query_masks) != query_occupancies * 6:
        raise ValueError("bridge query records are not six complete labels per occupancy")
    return {
        "available_cards": cards,
        "source_cards": source_cards,
        "query_cards": query_cards,
        "source_occupancies": comb(cards, source_cards),
        "source_recurrence_rows": sum(comb(cards, width) for width in range(7)),
        "source_pairings_per_occupancy": len(fixture.source_pair_positions),
        "query_occupancies": query_occupancies,
        "query_pairings_per_occupancy": 6,
        "labeled_query_records": len(fixture.query_masks),
        "adjoint_recurrence_rows": sum(comb(cards, width) for width in range(5)),
        "source_rank": fixture.source_rank,
        "source_state_feature_count": fixture.source_rank,
        "reach_global_feature_index": fixture.source_rank,
        "total_feature_width": fixture.feature_width,
        "component_count": fixture.components,
    }


def _runtime_rows(
    bridge: LegalRiverQuotientBridge,
    streaming: StreamingContract,
) -> tuple[NumericLifetimeRow, ...]:
    geometry = _source_geometry(bridge)
    width = MAXIMUM_WORKSPACE_WIDTH
    forward_records = min(
        geometry["labeled_query_records"], streaming.forward.records
    )
    adjoint_records = min(
        geometry["labeled_query_records"], streaming.adjoint_query_records
    )
    source_records = min(
        geometry["source_occupancies"], streaming.adjoint_source.occupancies
    )
    return (
        _row(
            "device_cardinality_offsets",
            "device",
            "consumer_resident",
            "int64",
            (geometry["source_cards"] + 1,),
            "device_resident",
            "adjoint_slice_1_source",
        ),
        _row(
            "device_library_scratch_allowance",
            "device",
            "shared_scratch",
            "uint8",
            (LIBRARY_SCRATCH_BYTES,),
            "device_resident",
            "adjoint_slice_1_source",
        ),
        _row(
            "device_result_accumulators",
            "device",
            "forward_result",
            "float64",
            (2,),
            "forward_slice_0_source",
            "release",
        ),
        _row(
            "device_forward_recurrence_workspace",
            "device",
            "forward_operator",
            "float64",
            (geometry["source_recurrence_rows"], width),
            "forward_slice_0_source",
            "forward_slice_1_fold",
        ),
        _row(
            "device_forward_compatible_chunk",
            "device",
            "forward_operator",
            "float64",
            (forward_records, width),
            "forward_slice_0_source",
            "forward_slice_1_fold",
        ),
        _row(
            "device_forward_numerator_chunk",
            "device",
            "forward_fold",
            "float64",
            (forward_records,),
            "forward_slice_0_source",
            "forward_slice_1_fold",
        ),
        _row(
            "device_forward_reach_chunk",
            "device",
            "forward_fold",
            "float64",
            (forward_records,),
            "forward_slice_0_source",
            "forward_slice_1_fold",
        ),
        _row(
            "device_adjoint_query_covector_chunk",
            "device",
            "adjoint_operator",
            "float64",
            (adjoint_records, width),
            "adjoint_slice_0_query",
            "adjoint_slice_1_source",
        ),
        _row(
            "device_adjoint_recurrence_workspace",
            "device",
            "adjoint_operator",
            "float64",
            (geometry["adjoint_recurrence_rows"], width),
            "adjoint_slice_0_query",
            "adjoint_slice_1_source",
        ),
        _row(
            "device_unique_source_adjoint_chunk",
            "device",
            "adjoint_operator",
            "float64",
            (source_records, width),
            "adjoint_slice_0_source",
            "adjoint_slice_1_source",
        ),
    )


def legal_river_consumer_lifetime_rows(
    bridge: LegalRiverQuotientBridge,
    streaming: StreamingContract,
) -> tuple[NumericLifetimeRow, ...]:
    rows = (
        *_bridge_consumer_rows(
            bridge,
            prefix="host_bridge",
            placement="host",
            born="host_bridge",
            last_live="release",
        ),
        *_bridge_validation_rows(bridge),
        *_bridge_consumer_rows(
            bridge,
            prefix="device_bridge",
            placement="device",
            born="device_resident",
            last_live="adjoint_slice_1_source",
        ),
        *_runtime_rows(bridge, streaming),
    )
    names = tuple(row.name for row in rows)
    if len(names) != len(set(names)):
        raise ValueError("lifetime rows contain a duplicate name")
    return rows


def _category_bytes(
    rows: Sequence[NumericLifetimeRow],
    *,
    placement: Placement,
    category: str,
) -> int:
    return sum(
        row.numeric_bytes
        for row in rows
        if row.placement == placement and row.semantic_category == category
    )


def _bridge_numeric_arrays(
    bridge: LegalRiverQuotientBridge,
) -> tuple[np.ndarray, ...]:
    fixture = bridge.fixture
    belief = bridge.factorized_belief
    return (
        *fixture.automaton.transitions,
        *fixture.automaton.bond_states,
        fixture.automaton.terminal_winner_values,
        fixture.mixture_weights,
        fixture.unary_weights,
        fixture.mode_factors,
        fixture.pair_to_hand,
        fixture.source_pair_positions,
        fixture.query_masks,
        fixture.query_hand_indices,
        fixture.unary_offsets,
        belief.mixture_weights,
        *belief.unary_weights,
        *belief.hand_masks,
    )


def _bridge_semantic_signature(bridge: LegalRiverQuotientBridge) -> tuple[object, ...]:
    fixture = bridge.fixture
    automaton = fixture.automaton
    belief = bridge.factorized_belief
    return (
        bridge.cards,
        bridge.cards.public_digest,
        bridge.betting,
        bridge.terminal_betting,
        bridge.belief.digest,
        fixture.available_cards,
        fixture.hands,
        automaton.shape,
        automaton.contenders,
        automaton.target_player,
        automaton.contributed,
        automaton.final_pot,
        automaton.sunk_value,
        automaton.constant_winner_shortcut,
        belief.board,
        belief.hands_by_player,
        belief.num_players,
        belief.component_count,
    )


def validate_parent_and_geometry(
    config: Mapping[str, object],
    bridge: LegalRiverQuotientBridge,
    *,
    reference_bridge: LegalRiverQuotientBridge | None = None,
) -> None:
    parent = config.get("parent_identity")
    expected_geometry = config.get("geometry")
    if not isinstance(parent, dict) or not isinstance(expected_geometry, dict):
        raise ValueError("parent identity or geometry is malformed")
    if bridge.bridge_digest != parent.get("bridge_sha256"):
        raise ValueError("parent bridge identity differs")
    if bridge.topology_digest != parent.get("topology_sha256"):
        raise ValueError("parent topology identity differs")
    reference = (
        compile_legal_river_quotient_bridge(
            build_preregistered_legal_river_context()
        )
        if reference_bridge is None
        else reference_bridge
    )
    identity_fields = (
        "bridge_digest",
        "topology_digest",
        "axis_table_seats",
        "source_axes",
        "query_axes",
        "target_axis",
        "local_to_physical_cards",
        "physical_hands",
        "policy_digest",
    )
    if any(getattr(bridge, name) != getattr(reference, name) for name in identity_fields):
        raise ValueError("parent bridge semantics differ from independent replay")
    if _bridge_semantic_signature(bridge) != _bridge_semantic_signature(reference):
        raise ValueError("parent bridge semantic payload differs from independent replay")
    observed_arrays = _bridge_numeric_arrays(bridge)
    expected_arrays = _bridge_numeric_arrays(reference)
    if len(observed_arrays) != len(expected_arrays) or any(
        observed.shape != expected.shape
        or observed.dtype != expected.dtype
        or not observed.flags.c_contiguous
        or observed.flags.writeable
        or not np.array_equal(observed, expected)
        for observed, expected in zip(observed_arrays, expected_arrays, strict=True)
    ):
        raise ValueError("parent bridge numeric payload differs from independent replay")
    geometry = _source_geometry(bridge)
    if geometry != expected_geometry:
        raise ValueError("source-derived geometry differs from ADR-0387")
    ownership = bridge.ownership
    if ownership.consumer_resident_numeric_bytes != int(
        parent["consumer_resident_numeric_bytes"]
    ):
        raise ValueError("parent consumer payload differs")
    if ownership.retained_host_validation_numeric_bytes != int(
        parent["retained_host_validation_numeric_bytes"]
    ):
        raise ValueError("parent validation payload differs")
    if ownership.warm_mutable_numeric_bytes != int(
        parent["warm_mutable_numeric_bytes_nonadditive"]
    ):
        raise ValueError("parent warm nonadditive view differs")


def _proposal_by_name(config: Mapping[str, object]) -> dict[str, dict[str, object]]:
    lifetime = config.get("lifetime_model")
    if not isinstance(lifetime, dict) or lifetime.get("ordered_phases") != list(PHASES):
        raise ValueError("lifetime phases differ from ADR-0387")
    raw_rows = lifetime.get("rows")
    if not isinstance(raw_rows, list) or not all(isinstance(row, dict) for row in raw_rows):
        raise ValueError("lifetime row proposal is malformed")
    names = [str(row.get("name")) for row in raw_rows]
    if len(names) != len(set(names)):
        raise ValueError("lifetime proposal contains a duplicated row")
    return {name: row for name, row in zip(names, raw_rows, strict=True)}


def validate_lifetime_proposal(
    config: Mapping[str, object],
    rows: Sequence[NumericLifetimeRow],
) -> None:
    """Cross-check every proposed class against independently expanded rows."""

    proposals = _proposal_by_name(config)
    derived = {
        "host_bridge_consumer_resident": (
            "host",
            "bridge_resident",
            _category_bytes(rows, placement="host", category="bridge_resident"),
        ),
        "host_bridge_retained_validation": (
            "host",
            "bridge_validation",
            _category_bytes(rows, placement="host", category="bridge_validation"),
        ),
        "device_bridge_consumer_resident": (
            "device",
            "consumer_resident",
            sum(
                row.numeric_bytes
                for row in rows
                if row.name.startswith("device_bridge_")
            ),
        ),
    }
    runtime = {
        row.name: row for row in rows if not row.name.startswith("host_bridge_")
        and not row.name.startswith("host_validation_")
        and not row.name.startswith("device_bridge_")
    }
    expected_names = set(derived) | set(runtime)
    if set(proposals) != expected_names:
        raise ValueError("lifetime proposal omitted or added a semantic class")
    for name, (placement, category, numeric_bytes) in derived.items():
        proposal = proposals[name]
        if (
            proposal.get("placement") != placement
            or proposal.get("semantic_category") != category
            or proposal.get("dtype") != "derived_named_arrays"
            or proposal.get("shape") != [numeric_bytes]
            or proposal.get("unit") != "numeric_bytes"
        ):
            raise ValueError(f"derived lifetime class {name} differs")
        actual_rows = (
            [row for row in rows if row.placement == "host" and row.semantic_category == category]
            if placement == "host"
            else [row for row in rows if row.name.startswith("device_bridge_")]
        )
        if any(
            row.born != proposal.get("born")
            or row.last_live != proposal.get("last_live")
            for row in actual_rows
        ):
            raise ValueError(f"derived lifetime class {name} lifetime differs")
    for name, row in runtime.items():
        proposal = proposals[name]
        if (
            proposal.get("placement") != row.placement
            or proposal.get("semantic_category") != row.semantic_category
            or proposal.get("dtype") != np.dtype(row.dtype).name
            or proposal.get("shape") != list(row.shape)
            or proposal.get("unit") != "elements"
            or proposal.get("born") != row.born
            or proposal.get("last_live") != row.last_live
        ):
            raise ValueError(f"lifetime row {name} differs")


def validate_claims_and_allocation_config(config: Mapping[str, object]) -> None:
    allocation = config.get("allocation")
    claims = config.get("claims")
    if not isinstance(allocation, dict) or not isinstance(claims, dict):
        raise ValueError("allocation or claims config is malformed")
    expected_allocation = {
        "host_numeric_cap_bytes": HOST_NUMERIC_CAP_BYTES,
        "device_numeric_cap_bytes": DEVICE_NUMERIC_CAP_BYTES,
        "host_reserve_bytes": HOST_RESERVE_BYTES,
        "device_reserve_bytes": DEVICE_RESERVE_BYTES,
        "minimum_host_physical_bytes": MINIMUM_HOST_PHYSICAL_BYTES,
        "minimum_device_physical_bytes": MINIMUM_DEVICE_PHYSICAL_BYTES,
    }
    if any(allocation.get(name) != value for name, value in expected_allocation.items()):
        raise ValueError("allocation cap or reserve differs from ADR-0387")
    if allocation.get("excluded_memory_classes") != list(EXCLUDED_MEMORY_CLASSES):
        raise ValueError("excluded memory classes differ from ADR-0387")
    if allocation.get("future_live_host_admission_required") is not True or allocation.get(
        "future_live_device_admission_required"
    ) is not True:
        raise ValueError("future live admission requirement differs")
    if allocation.get("source_only_cap_result") is not None:
        raise ValueError("prospective config improperly contains a source result")
    if claims != dict(CLAIMS):
        raise ValueError("claims boundary differs from ADR-0387")


def _phase_sweep(
    rows: Sequence[NumericLifetimeRow], placement: Placement
) -> Mapping[str, int]:
    return MappingProxyType(
        {
            phase: sum(
                row.numeric_bytes
                for row in rows
                if row.placement == placement and row.live_at(phase)
            )
            for phase in PHASES
        }
    )


def validate_lifetime_schedule(rows: Sequence[NumericLifetimeRow]) -> None:
    """Enforce the non-overlap and forbidden-allocation parts of the seal."""

    names = tuple(row.name for row in rows)
    if len(names) != len(set(names)):
        raise ValueError("lifetime schedule contains a duplicated row")
    forbidden_fragments = (
        "full_compatible",
        "full_query_covector",
        "full_unique_source",
        "record_expanded_source",
        "source_coefficients_allocation",
        "adjoint_aggregates_allocation",
    )
    if any(fragment in row.name for row in rows for fragment in forbidden_fragments):
        raise ValueError("lifetime schedule contains a forbidden full or subview array")
    adjoint_phases = PHASES[_PHASE_INDEX["adjoint_slice_0_query"] : -1]
    if any(
        row.semantic_category in ("forward_operator", "forward_fold")
        and any(row.live_at(phase) for phase in adjoint_phases)
        for row in rows
    ):
        raise ValueError("forward and adjoint workspaces are co-resident")
    if any(
        row.semantic_category == "adjoint_operator"
        and row.live_at("forward_release")
        for row in rows
    ):
        raise ValueError("adjoint workspace is born before forward release")


def require_fixed_allocation_admission(
    rows: Sequence[NumericLifetimeRow],
) -> tuple[Mapping[str, int], Mapping[str, int]]:
    """Reject source arithmetic before any future device import or allocation."""

    validate_lifetime_schedule(rows)
    host = _phase_sweep(rows, "host")
    device = _phase_sweep(rows, "device")
    host_peak = max(host.values())
    device_peak = max(device.values())
    if host_peak > HOST_NUMERIC_CAP_BYTES:
        raise MemoryError("host numeric cap fails before device entry")
    if device_peak > DEVICE_NUMERIC_CAP_BYTES:
        raise MemoryError("device numeric cap fails before device entry")
    if host_peak + HOST_RESERVE_BYTES > MINIMUM_HOST_PHYSICAL_BYTES:
        raise MemoryError("host physical reserve fails before device entry")
    if device_peak + DEVICE_RESERVE_BYTES > MINIMUM_DEVICE_PHYSICAL_BYTES:
        raise MemoryError("device physical reserve fails before device entry")
    return host, device


@dataclass(frozen=True, slots=True)
class LegalRiverConsumerCapacityReport:
    bridge_sha256: str
    topology_sha256: str
    geometry: Mapping[str, int]
    feature_slices: tuple[FeatureSlice, ...]
    streaming: StreamingContract
    rows: tuple[NumericLifetimeRow, ...]
    host_phase_bytes: Mapping[str, int]
    device_phase_bytes: Mapping[str, int]
    host_peak_phase: str
    host_peak_bytes: int
    device_peak_phase: str
    device_peak_bytes: int
    host_numeric_cap_pass: bool
    device_numeric_cap_pass: bool
    host_physical_reserve_pass: bool
    device_physical_reserve_pass: bool
    logical_feature_work: int
    physical_workspace_width: int
    warm_mutable_numeric_bytes_nonadditive: int
    live_host_free_bytes: None
    live_device_free_bytes: None
    live_admission_pass: None
    claims: Mapping[str, object]
    excluded_memory_classes: tuple[str, ...]

    @property
    def all_source_gates_pass(self) -> bool:
        return (
            self.host_numeric_cap_pass
            and self.device_numeric_cap_pass
            and self.host_physical_reserve_pass
            and self.device_physical_reserve_pass
            and self.logical_feature_work == TOTAL_FEATURE_WIDTH
            and self.physical_workspace_width == MAXIMUM_WORKSPACE_WIDTH
            and self.live_admission_pass is None
        )


def build_legal_river_consumer_capacity_report(
    *,
    bridge: LegalRiverQuotientBridge | None = None,
) -> LegalRiverConsumerCapacityReport:
    """Recompile provenance and sweep the source-only full-width schedule."""

    config = load_preregistered_consumer_capacity_config()
    verify_preregistered_dependencies(config)
    replayed = compile_legal_river_quotient_bridge(
        build_preregistered_legal_river_context()
    )
    compiled = replayed if bridge is None else bridge
    validate_parent_and_geometry(
        config,
        compiled,
        reference_bridge=replayed,
    )
    slices = feature_slices_from_config(config)
    streaming = streaming_contract_from_config(config)
    rows = legal_river_consumer_lifetime_rows(compiled, streaming)
    validate_lifetime_proposal(config, rows)
    validate_claims_and_allocation_config(config)

    parent = config["parent_identity"]
    assert isinstance(parent, dict)
    if _category_bytes(rows, placement="host", category="bridge_resident") != int(
        parent["consumer_resident_numeric_bytes"]
    ):
        raise ValueError("expanded host consumer rows differ from parent")
    if _category_bytes(rows, placement="host", category="bridge_validation") != int(
        parent["retained_host_validation_numeric_bytes"]
    ):
        raise ValueError("expanded validation rows differ from parent")
    device_bridge_bytes = sum(
        row.numeric_bytes for row in rows if row.name.startswith("device_bridge_")
    )
    if device_bridge_bytes != int(parent["consumer_resident_numeric_bytes"]):
        raise ValueError("expanded device mirror differs from parent")

    host, device = require_fixed_allocation_admission(rows)
    host_peak = max(host, key=host.__getitem__)
    device_peak = max(device, key=device.__getitem__)
    host_bytes = host[host_peak]
    device_bytes = device[device_peak]
    return LegalRiverConsumerCapacityReport(
        bridge_sha256=compiled.bridge_digest,
        topology_sha256=compiled.topology_digest,
        geometry=MappingProxyType(_source_geometry(compiled)),
        feature_slices=slices,
        streaming=streaming,
        rows=rows,
        host_phase_bytes=host,
        device_phase_bytes=device,
        host_peak_phase=host_peak,
        host_peak_bytes=host_bytes,
        device_peak_phase=device_peak,
        device_peak_bytes=device_bytes,
        host_numeric_cap_pass=host_bytes <= HOST_NUMERIC_CAP_BYTES,
        device_numeric_cap_pass=device_bytes <= DEVICE_NUMERIC_CAP_BYTES,
        host_physical_reserve_pass=(
            host_bytes + HOST_RESERVE_BYTES <= MINIMUM_HOST_PHYSICAL_BYTES
        ),
        device_physical_reserve_pass=(
            device_bytes + DEVICE_RESERVE_BYTES <= MINIMUM_DEVICE_PHYSICAL_BYTES
        ),
        logical_feature_work=sum(item.width for item in slices),
        physical_workspace_width=max(item.width for item in slices),
        warm_mutable_numeric_bytes_nonadditive=compiled.ownership.warm_mutable_numeric_bytes,
        live_host_free_bytes=None,
        live_device_free_bytes=None,
        live_admission_pass=None,
        claims=CLAIMS,
        excluded_memory_classes=EXCLUDED_MEMORY_CLASSES,
    )


def _mask(cards: Sequence[int]) -> int:
    return sum(1 << card for card in cards)


def _bounded_topology() -> OccupiedCardQuotientTopology:
    source_masks = tuple(sorted(_mask(cards) for cards in combinations(range(10), 6)))
    query_occupancies = tuple(
        sorted(_mask(cards) for cards in combinations(range(10), 4))
    )
    return OccupiedCardQuotientTopology.compile(
        source_seats=(0, 1, 2),
        query_seats=(3, 4, 5),
        open_seats=(3, 4, 5),
        source_record_masks=source_masks,
        query_record_masks=tuple(
            mask for mask in query_occupancies for _ in range(6)
        ),
    )


def _source_payload(masks: Sequence[int]) -> tuple[tuple[Fraction, ...], ...]:
    rows = []
    for record, _ in enumerate(masks):
        row = []
        for feature in range(TOTAL_FEATURE_WIDTH):
            if feature == REACH_GLOBAL_FEATURE:
                value = Fraction((record % 11) + 1, (record % 5) + 1)
            else:
                value = Fraction(
                    ((record + 3) * (feature + 5)) % 23 - 11,
                    (record % 7) + 1,
                )
            row.append(value)
        rows.append(tuple(row))
    return tuple(rows)


def _query_covectors(records: int) -> tuple[tuple[Fraction, ...], ...]:
    rows = []
    for record in range(records):
        occupancy, label = divmod(record, 6)
        query_weight = Fraction((record % 7) + 1, 5)
        row = tuple(
            query_weight
            * (
                Fraction(-3, 2)
                if feature == REACH_GLOBAL_FEATURE
                else Fraction(
                    ((label + 2) * (feature + 1) + occupancy % 13) % 17 - 8,
                    7,
                )
            )
            for feature in range(TOTAL_FEATURE_WIDTH)
        )
        rows.append(row)
    return tuple(rows)


def _literal_disjoint_forward(
    source_masks: Sequence[int],
    source_rows: Sequence[Sequence[Fraction]],
    query_masks: Sequence[int],
) -> tuple[tuple[Fraction, ...], ...]:
    """Independent monolithic oracle: direct mask scan, no quotient helper."""

    outputs = []
    for query_mask in query_masks:
        compatible = [
            row
            for source_mask, row in zip(source_masks, source_rows, strict=True)
            if source_mask & query_mask == 0
        ]
        outputs.append(
            tuple(
                sum((row[feature] for row in compatible), Fraction(0))
                for feature in range(TOTAL_FEATURE_WIDTH)
            )
        )
    return tuple(outputs)


def _sliced_forward(
    topology: OccupiedCardQuotientTopology,
    source_rows: Sequence[Sequence[Fraction]],
    slices: Sequence[FeatureSlice],
) -> tuple[tuple[Fraction, ...], ...]:
    outputs = [
        [Fraction(0) for _ in range(TOTAL_FEATURE_WIDTH)]
        for _ in range(topology.query_records)
    ]
    for item in slices:
        coefficients = ExactQuotientCoefficients(
            masks=topology.source_occupancy_masks,
            rows=tuple(tuple(row[item.start : item.stop]) for row in source_rows),
        )
        partial, _ = topology.apply_coefficients_exact(coefficients)
        for record, row in enumerate(partial):
            outputs[record][item.start : item.stop] = row
    return tuple(tuple(row) for row in outputs)


def _fold_parts(
    compatible: Sequence[Sequence[Fraction]],
    covectors: Sequence[Sequence[Fraction]],
    slices: Sequence[FeatureSlice],
    *,
    query_chunk: int,
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    spans = chunk_spans(len(compatible), query_chunk)
    numerators: list[Fraction] = []
    reaches: list[Fraction] = []
    for item in slices:
        numerator = Fraction(0)
        reach = Fraction(0)
        for start, stop in spans:
            for record in range(start, stop):
                numerator += sum(
                    (
                        compatible[record][feature] * covectors[record][feature]
                        for feature in item.global_feature_indices
                    ),
                    Fraction(0),
                )
                if item.owns_reach_feature:
                    query_weight = Fraction((record % 7) + 1, 5)
                    reach += query_weight * compatible[record][REACH_GLOBAL_FEATURE]
        numerators.append(numerator)
        reaches.append(reach)
    return tuple(numerators), tuple(reaches)


def _literal_disjoint_adjoint(
    source_masks: Sequence[int],
    query_masks: Sequence[int],
    query_rows: Sequence[Sequence[Fraction]],
) -> tuple[tuple[Fraction, ...], ...]:
    outputs = []
    for source_mask in source_masks:
        compatible = [
            row
            for query_mask, row in zip(query_masks, query_rows, strict=True)
            if source_mask & query_mask == 0
        ]
        outputs.append(
            tuple(
                sum((row[feature] for row in compatible), Fraction(0))
                for feature in range(TOTAL_FEATURE_WIDTH)
            )
        )
    return tuple(outputs)


def _stream_complete_query_groups(
    rows: Sequence[Sequence[Fraction]], occupancy_chunk: int
) -> tuple[tuple[Fraction, ...], ...]:
    group = 6
    result = []
    for start, stop in chunk_spans(
        len(rows), occupancy_chunk * group, group=group
    ):
        result.extend(tuple(row) for row in rows[start:stop])
    return tuple(result)


def _sliced_adjoint(
    topology: OccupiedCardQuotientTopology,
    query_rows: Sequence[Sequence[Fraction]],
    slices: Sequence[FeatureSlice],
    *,
    query_occupancy_chunk: int,
    source_occupancy_chunk: int,
) -> tuple[tuple[Fraction, ...], ...]:
    streamed = _stream_complete_query_groups(query_rows, query_occupancy_chunk)
    outputs = [
        [Fraction(0) for _ in range(TOTAL_FEATURE_WIDTH)]
        for _ in range(topology.source_records)
    ]
    source_spans = chunk_spans(topology.source_records, source_occupancy_chunk)
    for item in slices:
        partial = topology.apply_adjoint_exact(
            tuple(tuple(row[item.start : item.stop]) for row in streamed)
        )
        for start, stop in source_spans:
            for record in range(start, stop):
                outputs[record][item.start : item.stop] = partial[record]
    return tuple(tuple(row) for row in outputs)


def _exact_rows_sha256(rows: Sequence[Sequence[Fraction]]) -> str:
    digest = sha256()
    for row in rows:
        for value in row:
            digest.update(str(value.numerator).encode("ascii"))
            digest.update(b"/")
            digest.update(str(value.denominator).encode("ascii"))
            digest.update(b";")
        digest.update(b"\n")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class BoundedConsumerDifferentialReport:
    source_occupancies: int
    query_occupancies: int
    labeled_query_records: int
    source_rank: int
    feature_width: int
    forward_sha256: str
    adjoint_sha256: str
    monolithic_numerator: Fraction
    monolithic_reach: Fraction
    conditional_value: Fraction
    transpose_dot: Fraction
    exact_forward_pass: bool
    exact_reverse_slice_order_pass: bool
    exact_fold_pass: bool
    exact_adjoint_pass: bool
    exact_transpose_pass: bool
    forward_chunk_partition_pass: bool
    adjoint_group_partition_pass: bool
    source_chunk_partition_pass: bool
    normalize_after_recombination_pass: bool
    boundary_detecting_mass_pass: bool
    maximum_float64_recombination_absolute_error: float

    @property
    def all_gates_pass(self) -> bool:
        return (
            self.exact_forward_pass
            and self.exact_reverse_slice_order_pass
            and self.exact_fold_pass
            and self.exact_adjoint_pass
            and self.exact_transpose_pass
            and self.forward_chunk_partition_pass
            and self.adjoint_group_partition_pass
            and self.source_chunk_partition_pass
            and self.normalize_after_recombination_pass
            and self.boundary_detecting_mass_pass
            and self.maximum_float64_recombination_absolute_error <= 2e-11
        )


def run_bounded_consumer_differential() -> BoundedConsumerDifferentialReport:
    """Run the complete exact ten-card rank-175 seam differential."""

    slices = validate_feature_slices(frozen_feature_slices())
    topology = _bounded_topology()
    source_masks = topology.source_occupancy_masks
    query_masks = topology.query_variable_masks
    source_rows = _source_payload(source_masks)
    covectors = _query_covectors(topology.query_records)

    monolithic_forward = _literal_disjoint_forward(
        source_masks, source_rows, query_masks
    )
    sliced_forward = _sliced_forward(topology, source_rows, slices)
    reversed_forward = _sliced_forward(topology, source_rows, tuple(reversed(slices)))

    monolithic_parts = _fold_parts(
        monolithic_forward, covectors, slices, query_chunk=topology.query_records
    )
    sliced_parts = _fold_parts(sliced_forward, covectors, slices, query_chunk=17)
    alternate_parts = _fold_parts(sliced_forward, covectors, slices, query_chunk=19)
    numerator = sum(monolithic_parts[0], Fraction(0))
    reach = sum(monolithic_parts[1], Fraction(0))
    conditional = numerator / reach
    sliced_conditional = normalize_after_recombination(
        sliced_parts[0], sliced_parts[1], consumed_slice_ordinals=(0, 1)
    )

    monolithic_adjoint = _literal_disjoint_adjoint(
        source_masks, query_masks, covectors
    )
    sliced_adjoint = _sliced_adjoint(
        topology,
        covectors,
        slices,
        query_occupancy_chunk=3,
        source_occupancy_chunk=11,
    )
    alternate_adjoint = _sliced_adjoint(
        topology,
        covectors,
        slices,
        query_occupancy_chunk=5,
        source_occupancy_chunk=13,
    )

    forward_dot = sum(
        (
            monolithic_forward[record][feature] * covectors[record][feature]
            for record in range(topology.query_records)
            for feature in range(TOTAL_FEATURE_WIDTH)
        ),
        Fraction(0),
    )
    adjoint_dot = sum(
        (
            source_rows[record][feature] * monolithic_adjoint[record][feature]
            for record in range(topology.source_records)
            for feature in range(TOTAL_FEATURE_WIDTH)
        ),
        Fraction(0),
    )
    boundary_features = (0, 127, 128, 174, 175)
    boundary_detecting = all(
        any(row[feature] != 0 for row in source_rows)
        and any(row[feature] != 0 for row in covectors)
        and any(row[feature] != 0 for row in monolithic_forward)
        for feature in boundary_features
    )
    float_partial_numerator = sum(float(value) for value in sliced_parts[0])
    float_partial_reach = sum(float(value) for value in sliced_parts[1])
    float_error = abs(float_partial_numerator / float_partial_reach - float(conditional))

    return BoundedConsumerDifferentialReport(
        source_occupancies=len(source_masks),
        query_occupancies=len(set(query_masks)),
        labeled_query_records=len(query_masks),
        source_rank=SOURCE_STATE_FEATURES,
        feature_width=TOTAL_FEATURE_WIDTH,
        forward_sha256=_exact_rows_sha256(monolithic_forward),
        adjoint_sha256=_exact_rows_sha256(monolithic_adjoint),
        monolithic_numerator=numerator,
        monolithic_reach=reach,
        conditional_value=conditional,
        transpose_dot=forward_dot,
        exact_forward_pass=sliced_forward == monolithic_forward,
        exact_reverse_slice_order_pass=reversed_forward == monolithic_forward,
        exact_fold_pass=sliced_parts == monolithic_parts,
        exact_adjoint_pass=sliced_adjoint == monolithic_adjoint,
        exact_transpose_pass=forward_dot == adjoint_dot,
        forward_chunk_partition_pass=alternate_parts == sliced_parts,
        adjoint_group_partition_pass=(
            _stream_complete_query_groups(covectors, 3)
            == _stream_complete_query_groups(covectors, 5)
            == covectors
        ),
        source_chunk_partition_pass=alternate_adjoint == sliced_adjoint,
        normalize_after_recombination_pass=sliced_conditional == conditional,
        boundary_detecting_mass_pass=boundary_detecting,
        maximum_float64_recombination_absolute_error=float_error,
    )
