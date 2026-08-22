"""Fail-closed exact cache for pre-bet current-node affine rows.

The cache stores only the 2N-1 initial affine rows consumed by the restricted
master: one fixed-profile row per payoff seat and one fixed-response row per
nonacting payoff seat.  It stores no strategy, candidate, certificate, or
quality label.  Lookup requires a trusted digest of the literal persisted
bytes plus complete current provenance, then rechecks every row at its current
source probability tape before admitting the all-or-nothing bundle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import struct
import time
from typing import Any, Literal

import numpy as np

from .evaluation import Policy
from .factorized_belief import FactorizedCardBelief
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import (
    PolicyProbabilityTape,
    compile_policy_probability_tape,
)
from .river_multi_size import BetAction
from .sequence_form_open_axis import (
    OpenAxisNodeCoefficients,
    SequenceFormAffineRow,
    constant_minus_affine_row,
    subtract_affine_rows,
)


PreBetRowRole = Literal["profile", "fixed_response"]

CACHE_SCHEMA = "pontius-pre-bet-initial-row-cache-v1"
SOURCE_IDENTITY_ATOL = 2e-11
_SHA256_LENGTH = 64
_CACHE_TOP_LEVEL_KEYS = {"identity", "rows", "schema"}
_CACHE_ROW_KEYS = {
    "payoff_player",
    "probability_tape_sha256",
    "role",
    "row",
    "source_value_f64le",
}
_SERIALIZED_ROW_KEYS = {"acting_player", "constant_f64le", "nodes"}
_SERIALIZED_NODE_KEYS = {"node_index", "shape", "values_f64le"}
_CACHE_FIXED_OVERHEAD_BYTES = 65_536


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_LENGTH
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_digest(value: object) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _f64le_hex(value: float) -> str:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("cached Float64 values must be finite")
    return struct.pack("<d", numeric).hex()


def _parse_f64le_hex(value: object) -> float:
    if (
        not isinstance(value, str)
        or len(value) != 16
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("cached Float64 bytes are malformed")
    result = struct.unpack("<d", bytes.fromhex(value))[0]
    if not math.isfinite(result):
        raise ValueError("cached Float64 values must be finite")
    return result


def _action_token(action: object) -> tuple[str, str]:
    if isinstance(action, BetAction):
        return ("bet", action.amount.hex())
    if isinstance(action, str):
        return ("literal", action)
    raise TypeError(f"unsupported action identity {action!r}")


def _array_record(values: np.ndarray) -> dict[str, object]:
    if (
        not isinstance(values, np.ndarray)
        or values.dtype != np.float64
        or not values.flags.c_contiguous
    ):
        raise ValueError("cache arrays must be contiguous Float64")
    if not np.all(np.isfinite(values)):
        raise ValueError("cache arrays must be finite")
    little = np.ascontiguousarray(values, dtype="<f8")
    return {
        "shape": list(values.shape),
        "values_f64le": little.tobytes(order="C").hex(),
    }


def _validate_probability_tape(probabilities: PolicyProbabilityTape) -> None:
    if not isinstance(probabilities, tuple) or not probabilities:
        raise ValueError("probability tape must be a nonempty tuple")
    for values in probabilities:
        if values is None:
            continue
        if (
            not isinstance(values, np.ndarray)
            or values.dtype != np.float64
            or values.ndim != 2
            or not values.flags.c_contiguous
            or values.flags.writeable
        ):
            raise ValueError("probability tape arrays must be immutable contiguous Float64")
        if (
            not np.all(np.isfinite(values))
            or np.any(values < 0.0)
            or np.any(values > 1.0)
            or not np.allclose(
                np.sum(values, axis=1),
                1.0,
                rtol=0.0,
                atol=1e-12,
            )
        ):
            raise ValueError("probability tape rows must be finite simplices")


def probability_tape_digest(probabilities: PolicyProbabilityTape) -> str:
    """Return an exact shape-, terminal-, and Float64-byte-bound tape digest."""

    _validate_probability_tape(probabilities)
    return _json_digest(
        {
            "schema": "pontius-policy-probability-tape-f64le-v1",
            "nodes": [
                None if values is None else _array_record(values)
                for values in probabilities
            ],
        }
    )


def exact_policy_digest(policy: Mapping[str, Mapping[object, float]]) -> str:
    """Return a type-safe digest over every information set and Float64 bit."""

    rows = []
    for key in sorted(policy):
        if not isinstance(key, str) or not key:
            raise ValueError("policy information keys must be nonempty strings")
        distribution = policy[key]
        actions = []
        for action, probability in sorted(
            distribution.items(),
            key=lambda item: _action_token(item[0]),
        ):
            actions.append(
                {
                    "action": _action_token(action),
                    "probability_f64le": _f64le_hex(float(probability)),
                }
            )
        if not actions:
            raise ValueError("policy rows must be nonempty")
        total = math.fsum(float(probability) for probability in distribution.values())
        if (
            any(
                not math.isfinite(float(probability)) or float(probability) < 0.0
                for probability in distribution.values()
            )
            or abs(total - 1.0) > 1e-12
        ):
            raise ValueError("policy rows must be finite normalized distributions")
        rows.append({"information_key": key, "actions": actions})
    if not rows:
        raise ValueError("exact policy identity requires a complete nonempty policy")
    return _json_digest({"schema": "pontius-exact-policy-f64le-v1", "rows": rows})


def factorized_belief_digest(belief: FactorizedCardBelief) -> str:
    """Return a digest over normalized belief factors and literal hand axes."""

    if not isinstance(belief, FactorizedCardBelief):
        raise TypeError("pre-bet row cache requires a factorized card belief")
    if not belief.storage_is_contiguous_float64_and_uint64():
        raise ValueError("factorized belief storage differs from the Float64 contract")
    return _json_digest(
        {
            "schema": "pontius-factorized-belief-exact-v1",
            "board": list(belief.board),
            "hands_by_player": [
                [list(hand) for hand in hands] for hands in belief.hands_by_player
            ],
            "mixture_weights": _array_record(belief.mixture_weights),
            "unary_weights": [_array_record(values) for values in belief.unary_weights],
            "hand_masks_u64le": [
                {
                    "shape": list(values.shape),
                    "values_u64le": np.ascontiguousarray(values, dtype="<u8")
                    .tobytes(order="C")
                    .hex(),
                }
                for values in belief.hand_masks
            ],
        }
    )


def hand_axes_digest(hands_by_player: tuple[tuple[Any, ...], ...]) -> str:
    """Bind player ordering and every literal private-hand axis."""

    if not hands_by_player or any(not hands for hands in hands_by_player):
        raise ValueError("hand-axis identity requires one nonempty axis per player")
    return _json_digest(
        {
            "schema": "pontius-hand-axes-v1",
            "hands_by_player": [
                [list(hand) for hand in hands] for hands in hands_by_player
            ],
        }
    )


def layout_topology_digest(layout: Any) -> str:
    """Bind every compiled public node, edge, history, and role."""

    return _json_digest(
        {
            "schema": "pontius-compiled-public-topology-v1",
            "layout_type": f"{type(layout).__module__}.{type(layout).__qualname__}",
            "num_players": int(layout.num_players),
            "nodes": [
                {
                    "node_index": node_index,
                    "player": int(node.player),
                    "actions": [_action_token(action) for action in node.actions],
                    "children": list(node.children),
                    "terminal_slot": int(node.terminal_slot),
                    "history": [
                        [int(player), _action_token(action)]
                        for player, action in node.history
                    ],
                }
                for node_index, node in enumerate(layout.nodes)
            ],
        }
    )


def action_schema_digest(layout: Any) -> str:
    """Bind every information key to its action types and ordering."""

    schema = layout.information_schema()
    return _json_digest(
        {
            "schema": "pontius-information-action-schema-v1",
            "rows": [
                {
                    "information_key": key,
                    "actions": [_action_token(action) for action in schema[key]],
                }
                for key in sorted(schema)
            ],
        }
    )


def fixed_continuation_digest(
    probabilities: PolicyProbabilityTape,
    *,
    public_node: int,
) -> str:
    """Bind every fixed policy row outside the current-node optimizer axis."""

    _validate_probability_tape(probabilities)
    if isinstance(public_node, bool) or public_node not in range(len(probabilities)):
        raise ValueError("current public node is outside the probability tape")
    return _json_digest(
        {
            "schema": "pontius-fixed-current-node-continuation-v1",
            "public_node": public_node,
            "nodes": [
                {"open_current_node": True}
                if node_index == public_node
                else (None if values is None else _array_record(values))
                for node_index, values in enumerate(probabilities)
            ],
        }
    )


def numerical_contract_digest() -> str:
    """Return the frozen numerical contract used for cache admission."""

    return _json_digest(
        {
            "schema": "pontius-pre-bet-row-numerical-contract-v1",
            "dtype": "Float64",
            "byte_order": "little",
            "array_order": "C",
            "relative_tolerance_f64le": _f64le_hex(0.0),
            "source_identity_atol_f64le": _f64le_hex(SOURCE_IDENTITY_ATOL),
            "all_coefficients_finite": True,
            "all_probability_rows_finite_simplexes": True,
            "row_evaluation": "SequenceFormAffineRow.value/einsum-optimize",
        }
    )


def cpu_h2_control_row_primitive_digest() -> str:
    """Hash the complete source-file set used by the literal CPU/h2 control."""

    package = Path(__file__).resolve().parent
    names = (
        "dense_root_cross_payoff_control.py",
        "public_node_open_axis.py",
        "sequence_form_open_axis.py",
    )
    records = []
    for name in names:
        payload = (package / name).read_bytes()
        records.append(
            {
                "path": f"src/pontius/{name}",
                "byte_length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return _json_digest(
        {"schema": "pontius-cpu-h2-row-primitive-manifest-v1", "files": records}
    )


@dataclass(frozen=True, slots=True)
class PreBetRowCacheIdentity:
    """Complete provenance required before any cached coefficient is visible."""

    num_players: int
    public_node_count: int
    acting_player: int
    public_node: int
    policy_sha256: str
    source_probability_sha256: str
    belief_sha256: str
    hand_axes_sha256: str
    game_structural_sha256: str
    game_provenance_sha256: str
    topology_sha256: str
    fixed_continuation_sha256: str
    action_schema_sha256: str
    row_primitive_sha256: str
    numerical_contract_sha256: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.num_players, bool)
            or self.num_players < 2
            or isinstance(self.public_node_count, bool)
            or self.public_node_count <= 0
            or isinstance(self.acting_player, bool)
            or self.acting_player not in range(self.num_players)
            or isinstance(self.public_node, bool)
            or self.public_node not in range(self.public_node_count)
        ):
            raise ValueError("pre-bet row cache role identity is invalid")
        for field in fields(self):
            if field.name.endswith("_sha256") and not _is_sha256(
                getattr(self, field.name)
            ):
                raise ValueError(f"{field.name} must be a lowercase SHA-256 digest")

    def to_record(self) -> dict[str, object]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


def build_pre_bet_row_cache_identity(
    layout: Any,
    belief: FactorizedCardBelief,
    hands_by_player: tuple[tuple[Any, ...], ...],
    policy: Mapping[str, Mapping[object, float]],
    source_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    public_node: int,
    row_primitive_sha256: str,
) -> PreBetRowCacheIdentity:
    """Derive the complete identity and reject caller-supplied tape drift."""

    if not _is_sha256(row_primitive_sha256):
        raise ValueError("row primitive identity must be a lowercase SHA-256 digest")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("pre-bet row cache requires one hand axis per player")
    if tuple(hands_by_player) != tuple(layout.hands_by_player):
        raise ValueError("pre-bet row cache hand axes differ from the layout")
    if tuple(hands_by_player) != belief.hands_by_player:
        raise ValueError("pre-bet row cache hand axes differ from the belief")
    if belief.num_players != layout.num_players or belief.board != layout.game.board:
        raise ValueError("pre-bet row cache belief differs from the game context")
    if isinstance(public_node, bool) or public_node not in range(layout.public_node_count):
        raise ValueError("pre-bet row cache public node is outside the layout")
    node = layout.nodes[public_node]
    if node.player == TERMINAL_PLAYER or node.player != acting_player:
        raise ValueError("pre-bet row cache current node belongs to another player")
    schema = layout.information_schema()
    if set(policy) != set(schema) or any(
        set(policy[key]) != set(actions) for key, actions in schema.items()
    ):
        raise ValueError("pre-bet row cache policy is not schema-complete")
    compiled = compile_policy_probability_tape(layout, hands_by_player, policy)
    if probability_tape_digest(compiled) != probability_tape_digest(source_probabilities):
        raise ValueError("pre-bet row cache source tape differs from the full policy")
    structural = getattr(layout.game, "structural_digest", None)
    provenance = getattr(layout.game, "provenance_digest", None)
    if not _is_sha256(structural) or not _is_sha256(provenance):
        raise ValueError("pre-bet row cache game lacks exact provenance digests")
    return PreBetRowCacheIdentity(
        num_players=int(layout.num_players),
        public_node_count=int(layout.public_node_count),
        acting_player=int(acting_player),
        public_node=int(public_node),
        policy_sha256=exact_policy_digest(policy),
        source_probability_sha256=probability_tape_digest(source_probabilities),
        belief_sha256=factorized_belief_digest(belief),
        hand_axes_sha256=hand_axes_digest(hands_by_player),
        game_structural_sha256=structural,
        game_provenance_sha256=provenance,
        topology_sha256=layout_topology_digest(layout),
        fixed_continuation_sha256=fixed_continuation_digest(
            source_probabilities,
            public_node=public_node,
        ),
        action_schema_sha256=action_schema_digest(layout),
        row_primitive_sha256=row_primitive_sha256,
        numerical_contract_sha256=numerical_contract_digest(),
    )


@dataclass(frozen=True, slots=True)
class PreBetInitialRowSource:
    """Current source oracle input against which one cached row is checked."""

    role: PreBetRowRole
    payoff_player: int
    probabilities: PolicyProbabilityTape
    source_value: float

    def __post_init__(self) -> None:
        if self.role not in ("profile", "fixed_response"):
            raise ValueError("pre-bet row source has an unknown role")
        if isinstance(self.payoff_player, bool) or self.payoff_player < 0:
            raise ValueError("pre-bet row source payoff role is invalid")
        if not math.isfinite(float(self.source_value)):
            raise ValueError("pre-bet row source value must be finite")


@dataclass(frozen=True, slots=True)
class PreBetInitialRow:
    """One role-labelled affine row in the initial restricted-master bundle."""

    role: PreBetRowRole
    payoff_player: int
    row: SequenceFormAffineRow


@dataclass(frozen=True, slots=True)
class PreBetRowCacheLookup:
    """All-or-nothing lookup result with on-clock validation telemetry."""

    hit: bool
    reason: str
    rows: tuple[PreBetInitialRow, ...] | None
    expected_persisted_sha256: str
    observed_persisted_sha256: str | None
    lookup_validation_ms: float


@dataclass(frozen=True, slots=True)
class PreBetRestrictedMasterPreparation:
    """Warm-free successor preparation; external policy stays the blueprint."""

    cache_hit: bool
    reason: str
    initial_rows: tuple[PreBetInitialRow, ...] | None
    gain_rows: tuple[SequenceFormAffineRow, ...] | None
    external_policy: Policy
    lookup_validation_ms: float
    on_clock_ms: float
    warm_steps: int
    master_solves: int
    candidate_emissions: int
    strategy_quality_rows: int


def _expected_roles(identity: PreBetRowCacheIdentity) -> tuple[tuple[str, int], ...]:
    return tuple(("profile", player) for player in range(identity.num_players)) + tuple(
        ("fixed_response", player)
        for player in range(identity.num_players)
        if player != identity.acting_player
    )


def _validate_sources(
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
) -> tuple[PreBetInitialRowSource, ...]:
    supplied = tuple(sources)
    expected = _expected_roles(identity)
    if tuple((source.role, source.payoff_player) for source in supplied) != expected:
        raise ValueError("pre-bet row sources differ from the complete role schema")
    source_current: np.ndarray | None = None
    for source in supplied:
        _validate_probability_tape(source.probabilities)
        if len(source.probabilities) != identity.public_node_count:
            raise ValueError("pre-bet row source tape differs from the public tree")
        current = source.probabilities[identity.public_node]
        if current is None:
            raise ValueError("pre-bet row source current node has no policy probabilities")
        digest = probability_tape_digest(source.probabilities)
        if source.role == "profile":
            if digest != identity.source_probability_sha256:
                raise ValueError("pre-bet profile source tape differs from identity")
            if source_current is None:
                source_current = current
        elif source_current is None or not np.array_equal(current, source_current):
            raise ValueError("fixed response changes the current acting-node policy")
    return supplied


def _validate_row(
    identity: PreBetRowCacheIdentity,
    source: PreBetInitialRowSource,
    item: PreBetInitialRow,
) -> float:
    if (item.role, item.payoff_player) != (source.role, source.payoff_player):
        raise ValueError("cached affine row differs from its payoff role")
    row = item.row
    if row.acting_player != identity.acting_player:
        raise ValueError("cached affine row belongs to another acting player")
    if not math.isfinite(float(row.constant)):
        raise ValueError("cached affine row constant is not finite")
    if len(row.nodes) != 1 or row.nodes[0].node_index != identity.public_node:
        raise ValueError("cached affine row does not cover exactly the current node")
    probabilities = source.probabilities[identity.public_node]
    values = row.nodes[0].values
    if (
        probabilities is None
        or not isinstance(values, np.ndarray)
        or values.dtype != np.float64
        or not values.flags.c_contiguous
        or values.flags.writeable
        or values.shape != probabilities.shape
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("cached affine coefficient storage differs from the source axis")
    error = abs(row.value(source.probabilities) - float(source.source_value))
    if error > SOURCE_IDENTITY_ATOL:
        raise ArithmeticError("cached affine row fails current source identity")
    return error


def _serialize_row(row: SequenceFormAffineRow) -> dict[str, object]:
    return {
        "acting_player": row.acting_player,
        "constant_f64le": _f64le_hex(row.constant),
        "nodes": [
            {
                "node_index": node.node_index,
                **_array_record(node.values),
            }
            for node in row.nodes
        ],
    }


def write_pre_bet_initial_row_cache(
    path: Path,
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
    rows: Sequence[PreBetInitialRow],
) -> str:
    """Atomically persist one validated bundle and return its byte-truth hash."""

    checked_sources = _validate_sources(identity, sources)
    supplied_rows = tuple(rows)
    if tuple((item.role, item.payoff_player) for item in supplied_rows) != _expected_roles(
        identity
    ):
        raise ValueError("pre-bet cached rows differ from the complete role schema")
    for source, item in zip(checked_sources, supplied_rows, strict=True):
        _validate_row(identity, source, item)
    payload = {
        "schema": CACHE_SCHEMA,
        "identity": identity.to_record(),
        "rows": [
            {
                "role": source.role,
                "payoff_player": source.payoff_player,
                "probability_tape_sha256": probability_tape_digest(
                    source.probabilities
                ),
                "source_value_f64le": _f64le_hex(source.source_value),
                "row": _serialize_row(item.row),
            }
            for source, item in zip(checked_sources, supplied_rows, strict=True)
        ],
    }
    rendered = _json_bytes(payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_bytes(rendered)
    temporary.replace(path)
    persisted = path.read_bytes()
    if persisted != rendered:
        raise OSError("persisted pre-bet row cache bytes differ from serialized bytes")
    return hashlib.sha256(persisted).hexdigest()


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("cached JSON contains a duplicate key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"cached JSON contains invalid constant {value}")


def _decode_cache(payload: bytes) -> object:
    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_strict_json_object,
        parse_constant=_reject_json_constant,
    )


def _require_exact_keys(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"cached {label} schema differs")
    return value


def _parse_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"cached {label} is not an integer")
    return value


def _identity_record_matches(
    value: object,
    identity: PreBetRowCacheIdentity,
) -> bool:
    expected = identity.to_record()
    record = _require_exact_keys(value, set(expected), "identity")
    for key, expected_value in expected.items():
        actual = record[key]
        if type(actual) is not type(expected_value):
            raise ValueError("cached identity field type differs")
        if actual != expected_value:
            return False
    return True


def _maximum_serialized_cache_bytes(
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
) -> int:
    current_numeric_bytes = 0
    for source in sources:
        values = source.probabilities[identity.public_node]
        if values is None:
            raise ValueError("pre-bet row source current node has no probabilities")
        current_numeric_bytes += values.nbytes + np.dtype(np.float64).itemsize
    return _CACHE_FIXED_OVERHEAD_BYTES + 4 * current_numeric_bytes


def _deserialize_row(
    value: object,
    *,
    identity: PreBetRowCacheIdentity,
    expected_shape: tuple[int, ...],
) -> SequenceFormAffineRow:
    record = _require_exact_keys(value, _SERIALIZED_ROW_KEYS, "affine row")
    acting_player = _parse_int(record["acting_player"], "acting player")
    if acting_player != identity.acting_player:
        raise ValueError("cached affine row acting role differs")
    nodes = record["nodes"]
    if not isinstance(nodes, list) or len(nodes) != 1:
        raise ValueError("cached affine row node count differs")
    node = _require_exact_keys(nodes[0], _SERIALIZED_NODE_KEYS, "affine node")
    node_index = _parse_int(node["node_index"], "affine node index")
    if node_index != identity.public_node:
        raise ValueError("cached affine row current node differs")
    shape = node["shape"]
    if (
        not isinstance(shape, list)
        or any(isinstance(value, bool) or not isinstance(value, int) for value in shape)
        or tuple(shape) != expected_shape
    ):
        raise ValueError("cached affine row shape differs")
    encoded = node["values_f64le"]
    expected_hex_length = math.prod(expected_shape) * 16
    if (
        not isinstance(encoded, str)
        or len(encoded) != expected_hex_length
        or encoded != encoded.lower()
        or any(character not in "0123456789abcdef" for character in encoded)
    ):
        raise ValueError("cached affine coefficient bytes are malformed")
    raw = bytes.fromhex(encoded)
    values = np.frombuffer(raw, dtype="<f8").reshape(expected_shape).astype(
        np.float64,
        order="C",
        copy=True,
    )
    if not np.all(np.isfinite(values)):
        raise ValueError("cached affine coefficient is not finite")
    values.flags.writeable = False
    return SequenceFormAffineRow(
        acting_player=acting_player,
        constant=_parse_f64le_hex(record["constant_f64le"]),
        nodes=(OpenAxisNodeCoefficients(node_index, values),),
    )


def _lookup_result(
    *,
    hit: bool,
    reason: str,
    rows: tuple[PreBetInitialRow, ...] | None,
    expected: str,
    observed: str | None,
    started_ns: int,
) -> PreBetRowCacheLookup:
    return PreBetRowCacheLookup(
        hit=hit,
        reason=reason,
        rows=rows,
        expected_persisted_sha256=expected,
        observed_persisted_sha256=observed,
        lookup_validation_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
    )


def lookup_pre_bet_initial_row_cache(
    path: Path,
    expected_persisted_sha256: str,
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
) -> PreBetRowCacheLookup:
    """Read, hash, parse, and numerically validate a complete bundle on-clock."""

    started_ns = time.perf_counter_ns()
    observed: str | None = None
    if not _is_sha256(expected_persisted_sha256):
        return _lookup_result(
            hit=False,
            reason="invalid_expected_persisted_sha256",
            rows=None,
            expected=expected_persisted_sha256,
            observed=None,
            started_ns=started_ns,
        )
    try:
        checked_sources = _validate_sources(identity, sources)
    except (ArithmeticError, TypeError, ValueError):
        return _lookup_result(
            hit=False,
            reason="current_source_contract_mismatch",
            rows=None,
            expected=expected_persisted_sha256,
            observed=None,
            started_ns=started_ns,
        )
    try:
        persisted = Path(path).read_bytes()
    except OSError:
        return _lookup_result(
            hit=False,
            reason="cache_unavailable",
            rows=None,
            expected=expected_persisted_sha256,
            observed=None,
            started_ns=started_ns,
        )
    observed = hashlib.sha256(persisted).hexdigest()
    if observed != expected_persisted_sha256:
        return _lookup_result(
            hit=False,
            reason="persisted_byte_identity_mismatch",
            rows=None,
            expected=expected_persisted_sha256,
            observed=observed,
            started_ns=started_ns,
        )
    if len(persisted) > _maximum_serialized_cache_bytes(identity, checked_sources):
        return _lookup_result(
            hit=False,
            reason="cache_size_safety_cap_exceeded",
            rows=None,
            expected=expected_persisted_sha256,
            observed=observed,
            started_ns=started_ns,
        )
    try:
        root = _require_exact_keys(_decode_cache(persisted), _CACHE_TOP_LEVEL_KEYS, "root")
        if root["schema"] != CACHE_SCHEMA:
            raise ValueError("cached root version differs")
        if not _identity_record_matches(root["identity"], identity):
            return _lookup_result(
                hit=False,
                reason="full_provenance_identity_mismatch",
                rows=None,
                expected=expected_persisted_sha256,
                observed=observed,
                started_ns=started_ns,
            )
        serialized_rows = root["rows"]
        if not isinstance(serialized_rows, list) or len(serialized_rows) != len(
            checked_sources
        ):
            raise ValueError("cached row bundle count differs")
        loaded = []
        for source, serialized in zip(
            checked_sources,
            serialized_rows,
            strict=True,
        ):
            record = _require_exact_keys(serialized, _CACHE_ROW_KEYS, "row record")
            role = record["role"]
            payoff_player = _parse_int(record["payoff_player"], "payoff player")
            if not isinstance(role, str) or (role, payoff_player) != (
                source.role,
                source.payoff_player,
            ):
                raise ValueError("cached row role order differs")
            tape_digest = record["probability_tape_sha256"]
            if not _is_sha256(tape_digest):
                raise ValueError("cached row probability digest is malformed")
            if tape_digest != probability_tape_digest(source.probabilities):
                return _lookup_result(
                    hit=False,
                    reason="row_probability_tape_mismatch",
                    rows=None,
                    expected=expected_persisted_sha256,
                    observed=observed,
                    started_ns=started_ns,
                )
            stored_source_value = _parse_f64le_hex(record["source_value_f64le"])
            if abs(stored_source_value - float(source.source_value)) > SOURCE_IDENTITY_ATOL:
                return _lookup_result(
                    hit=False,
                    reason="source_value_identity_mismatch",
                    rows=None,
                    expected=expected_persisted_sha256,
                    observed=observed,
                    started_ns=started_ns,
                )
            current = source.probabilities[identity.public_node]
            if current is None:
                raise ValueError("cached current source row is absent")
            row = PreBetInitialRow(
                role=source.role,
                payoff_player=source.payoff_player,
                row=_deserialize_row(
                    record["row"],
                    identity=identity,
                    expected_shape=current.shape,
                ),
            )
            _validate_row(identity, source, row)
            if abs(row.row.value(source.probabilities) - stored_source_value) > (
                SOURCE_IDENTITY_ATOL
            ):
                return _lookup_result(
                    hit=False,
                    reason="stored_source_numerical_mismatch",
                    rows=None,
                    expected=expected_persisted_sha256,
                    observed=observed,
                    started_ns=started_ns,
                )
            loaded.append(row)
    except ArithmeticError:
        return _lookup_result(
            hit=False,
            reason="current_source_numerical_mismatch",
            rows=None,
            expected=expected_persisted_sha256,
            observed=observed,
            started_ns=started_ns,
        )
    except (KeyError, TypeError, UnicodeError, ValueError, json.JSONDecodeError):
        return _lookup_result(
            hit=False,
            reason="malformed_cache",
            rows=None,
            expected=expected_persisted_sha256,
            observed=observed,
            started_ns=started_ns,
        )
    return _lookup_result(
        hit=True,
        reason="exact_hit",
        rows=tuple(loaded),
        expected=expected_persisted_sha256,
        observed=observed,
        started_ns=started_ns,
    )


def assemble_pre_bet_gain_rows(
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
    rows: Sequence[PreBetInitialRow],
    *,
    acting_best_response_value: float,
) -> tuple[SequenceFormAffineRow, ...]:
    """Reconstruct the N master gain rows from one admitted 2N-1 bundle."""

    if not math.isfinite(float(acting_best_response_value)):
        raise ValueError("acting best-response value must be finite")
    checked_sources = _validate_sources(identity, sources)
    supplied_rows = tuple(rows)
    if tuple((item.role, item.payoff_player) for item in supplied_rows) != _expected_roles(
        identity
    ):
        raise ValueError("pre-bet gain rows require the complete role schema")
    for source, item in zip(checked_sources, supplied_rows, strict=True):
        _validate_row(identity, source, item)
    profiles = {
        item.payoff_player: item.row
        for item in supplied_rows
        if item.role == "profile"
    }
    responses = {
        item.payoff_player: item.row
        for item in supplied_rows
        if item.role == "fixed_response"
    }
    profile_sources = {
        source.payoff_player: source
        for source in checked_sources
        if source.role == "profile"
    }
    response_sources = {
        source.payoff_player: source
        for source in checked_sources
        if source.role == "fixed_response"
    }
    base_probabilities = profile_sources[0].probabilities
    gains = []
    for payoff_player in range(identity.num_players):
        profile = profiles[payoff_player]
        profile_value = float(profile_sources[payoff_player].source_value)
        if payoff_player == identity.acting_player:
            response_value = float(acting_best_response_value)
            gain = constant_minus_affine_row(response_value, profile)
        else:
            response_value = float(response_sources[payoff_player].source_value)
            gain = subtract_affine_rows(responses[payoff_player], profile)
        expected_gain = response_value - profile_value
        if abs(gain.value(base_probabilities) - expected_gain) > SOURCE_IDENTITY_ATOL:
            raise ArithmeticError("pre-bet gain row fails current source identity")
        gains.append(gain)
    return tuple(gains)


def _defensive_policy_copy(
    blueprint: Mapping[str, Mapping[object, float]],
) -> Policy:
    exact_policy_digest(blueprint)
    return {key: dict(distribution) for key, distribution in blueprint.items()}


def prepare_pre_bet_restricted_master_successor(
    path: Path,
    expected_persisted_sha256: str,
    identity: PreBetRowCacheIdentity,
    sources: Sequence[PreBetInitialRowSource],
    immutable_blueprint: Mapping[str, Mapping[object, float]],
    *,
    acting_best_response_value: float,
) -> PreBetRestrictedMasterPreparation:
    """Prepare cached gain rows with no warm step and blueprint-only output.

    Cache lookup, byte hashing, parsing, source validation, and gain assembly
    are all included in ``on_clock_ms``.  A miss or any assembly failure admits
    no row and returns a defensive copy of the immutable blueprint.
    """

    started_ns = time.perf_counter_ns()
    external_policy = _defensive_policy_copy(immutable_blueprint)
    lookup = lookup_pre_bet_initial_row_cache(
        path,
        expected_persisted_sha256,
        identity,
        sources,
    )
    if not lookup.hit or lookup.rows is None:
        return PreBetRestrictedMasterPreparation(
            cache_hit=False,
            reason=lookup.reason,
            initial_rows=None,
            gain_rows=None,
            external_policy=external_policy,
            lookup_validation_ms=lookup.lookup_validation_ms,
            on_clock_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
            warm_steps=0,
            master_solves=0,
            candidate_emissions=0,
            strategy_quality_rows=0,
        )
    try:
        gains = assemble_pre_bet_gain_rows(
            identity,
            sources,
            lookup.rows,
            acting_best_response_value=acting_best_response_value,
        )
    except (ArithmeticError, KeyError, TypeError, ValueError):
        return PreBetRestrictedMasterPreparation(
            cache_hit=False,
            reason="gain_row_assembly_mismatch",
            initial_rows=None,
            gain_rows=None,
            external_policy=external_policy,
            lookup_validation_ms=lookup.lookup_validation_ms,
            on_clock_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
            warm_steps=0,
            master_solves=0,
            candidate_emissions=0,
            strategy_quality_rows=0,
        )
    return PreBetRestrictedMasterPreparation(
        cache_hit=True,
        reason="exact_hit",
        initial_rows=lookup.rows,
        gain_rows=gains,
        external_policy=external_policy,
        lookup_validation_ms=lookup.lookup_validation_ms,
        on_clock_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
        warm_steps=0,
        master_solves=0,
        candidate_emissions=0,
        strategy_quality_rows=0,
    )
