"""Provenance-bound, externally sealed pre-bet affine-row cache.

V2 is deliberately incompatible with the historical cache.  Callers cannot
construct cache identity fields, supply rows or the acting best-response
scalar, or feed the writer's returned hash directly to replay.  Population is
derived from independently checked affine contexts; replay requires a typed
seal loaded from separately persisted bytes.
"""

from __future__ import annotations

import hashlib
import math
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from . import pre_bet_initial_row_cache as _v1
from .cross_payoff_adjoint_result import _layout_numeric_digest
from .evaluation import Policy
from .factorized_belief import FactorizedCardBelief
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape, compile_policy_probability_tape
from .public_node_open_axis import (
    PublicNodeAffineSourceContext,
    public_node_open_axis_payoff_row,
)
from .runner_harness_v2 import load_artifact, read_bounded_file_once
from .sequence_form_open_axis import (
    splice_fixed_response_probability_tape_for_axes,
)

PreBetRowRole = _v1.PreBetRowRole
PreBetInitialRowSource = _v1.PreBetInitialRowSource
PreBetInitialRow = _v1.PreBetInitialRow
PreBetRestrictedMasterPreparation = _v1.PreBetRestrictedMasterPreparation

probability_tape_digest = _v1.probability_tape_digest
exact_policy_digest = _v1.exact_policy_digest
factorized_belief_digest = _v1.factorized_belief_digest
hand_axes_digest = _v1.hand_axes_digest
layout_topology_digest = _v1.layout_topology_digest
action_schema_digest = _v1.action_schema_digest
fixed_continuation_digest = _v1.fixed_continuation_digest
cpu_h2_control_row_primitive_digest = _v1.cpu_h2_control_row_primitive_digest

CACHE_SCHEMA = "pontius-pre-bet-initial-row-cache-v2"
LEGACY_CACHE_SCHEMA = _v1.CACHE_SCHEMA
SEAL_SCHEMA = "pontius-pre-bet-initial-row-cache-seal-v1"
SOURCE_IDENTITY_ATOL = _v1.SOURCE_IDENTITY_ATOL
_CACHE_TOP_LEVEL_KEYS = {
    "acting_best_response_value_f64le",
    "identity",
    "rows",
    "schema",
}
_SEAL_KEYS = {"cache_bytes", "cache_sha256", "identity_sha256", "schema"}
_CONTEXT_FACTORY_TOKEN = object()
_POPULATION_FACTORY_TOKEN = object()
_SEAL_FACTORY_TOKEN = object()


def numerical_contract_digest() -> str:
    """Return the hardened v2 numerical/provenance contract."""

    return _v1._json_digest(
        {
            "schema": "pontius-pre-bet-row-numerical-contract-v2-hardened",
            "dtype": "Float64",
            "byte_order": "little",
            "array_order": "C",
            "source_identity_atol_f64le": _v1._f64le_hex(SOURCE_IDENTITY_ATOL),
            "all_coefficients_finite": True,
            "all_probability_rows_finite_simplexes": True,
            "population_authority": (
                "factory-only provenance-bound affine contexts checked against "
                "independent dense root coefficients"
            ),
            "acting_best_response_value": (
                "derived by exact layout evaluation and hash-bound with rows"
            ),
            "replay_authority": "typed separately-persisted external seal",
            "bounded_read_before_decode": True,
        }
    )


def _freeze_policy(
    policy: Mapping[str, Mapping[object, float]],
) -> Mapping[str, Mapping[object, float]]:
    return MappingProxyType(
        {
            key: MappingProxyType(
                {action: float(value) for action, value in distribution.items()}
            )
            for key, distribution in policy.items()
        }
    )


def _identity_digest(identity: _v1.PreBetRowCacheIdentity) -> str:
    return _v1._json_digest(identity.to_record())


def _build_identity(
    layout: Any,
    belief: FactorizedCardBelief,
    hands_by_player: tuple[tuple[Any, ...], ...],
    policy: Mapping[str, Mapping[object, float]],
    source_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    public_node: int,
    row_primitive_sha256: str,
) -> _v1.PreBetRowCacheIdentity:
    if not _v1._is_sha256(row_primitive_sha256):
        raise ValueError("row primitive identity must be a lowercase SHA-256 digest")
    if len(hands_by_player) != layout.num_players:
        raise ValueError("pre-bet row cache requires one hand axis per player")
    if tuple(hands_by_player) != tuple(layout.hands_by_player):
        raise ValueError("pre-bet row cache hand axes differ from the layout")
    if tuple(hands_by_player) != belief.hands_by_player:
        raise ValueError("pre-bet row cache hand axes differ from the belief")
    if belief.num_players != layout.num_players or belief.board != layout.game.board:
        raise ValueError("pre-bet row cache belief differs from the game context")
    if (
        isinstance(acting_player, bool)
        or acting_player not in range(layout.num_players)
        or isinstance(public_node, bool)
        or public_node not in range(layout.public_node_count)
    ):
        raise ValueError("pre-bet row cache role or node is invalid")
    node = layout.nodes[public_node]
    if node.player == TERMINAL_PLAYER or node.player != acting_player:
        raise ValueError("pre-bet row cache current node belongs to another player")
    schema = layout.information_schema()
    if set(policy) != set(schema) or any(
        set(policy[key]) != set(actions) for key, actions in schema.items()
    ):
        raise ValueError("pre-bet row cache policy is not schema-complete")
    compiled = compile_policy_probability_tape(layout, hands_by_player, policy)
    if probability_tape_digest(compiled) != probability_tape_digest(
        source_probabilities
    ):
        raise ValueError("pre-bet row cache source tape differs from the full policy")
    structural = getattr(layout.game, "structural_digest", None)
    provenance = getattr(layout.game, "provenance_digest", None)
    if not _v1._is_sha256(structural) or not _v1._is_sha256(provenance):
        raise ValueError("pre-bet row cache game lacks exact provenance digests")
    return _v1.PreBetRowCacheIdentity(
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


@dataclass(frozen=True, slots=True, init=False)
class PreBetRowCacheContext:
    """Factory-only live game, policy, source, and exact-value snapshot."""

    layout: Any
    belief: FactorizedCardBelief
    hands_by_player: tuple[tuple[Any, ...], ...]
    policy: Mapping[str, Mapping[object, float]]
    source_probabilities: PolicyProbabilityTape
    identity: _v1.PreBetRowCacheIdentity
    sources: tuple[PreBetInitialRowSource, ...]
    acting_best_response_value: float
    layout_numeric_sha256: str

    def __init__(
        self,
        *,
        layout: Any,
        belief: FactorizedCardBelief,
        hands_by_player: tuple[tuple[Any, ...], ...],
        policy: Mapping[str, Mapping[object, float]],
        source_probabilities: PolicyProbabilityTape,
        identity: _v1.PreBetRowCacheIdentity,
        sources: tuple[PreBetInitialRowSource, ...],
        acting_best_response_value: float,
        layout_numeric_sha256: str,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _CONTEXT_FACTORY_TOKEN:
            raise TypeError(
                "pre-bet cache contexts are factory-only; use "
                "build_pre_bet_row_cache_context"
            )
        object.__setattr__(self, "layout", layout)
        object.__setattr__(self, "belief", belief)
        object.__setattr__(self, "hands_by_player", hands_by_player)
        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "source_probabilities", source_probabilities)
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(
            self,
            "acting_best_response_value",
            acting_best_response_value,
        )
        object.__setattr__(self, "layout_numeric_sha256", layout_numeric_sha256)


def build_pre_bet_row_cache_context(
    layout: Any,
    belief: FactorizedCardBelief,
    hands_by_player: tuple[tuple[Any, ...], ...],
    policy: Mapping[str, Mapping[object, float]],
    source_probabilities: PolicyProbabilityTape,
    *,
    acting_player: int,
    public_node: int,
    row_primitive_sha256: str,
) -> PreBetRowCacheContext:
    """Derive identity, every source tape/value, and actor BR internally."""

    frozen_policy = _freeze_policy(policy)
    compiled = compile_policy_probability_tape(layout, hands_by_player, frozen_policy)
    identity = _build_identity(
        layout,
        belief,
        hands_by_player,
        frozen_policy,
        compiled,
        acting_player=acting_player,
        public_node=public_node,
        row_primitive_sha256=row_primitive_sha256,
    )
    if probability_tape_digest(compiled) != probability_tape_digest(
        source_probabilities
    ):
        raise ValueError("pre-bet supplied source tape differs after snapshot")
    evaluated = layout.evaluate(frozen_policy)
    evaluation = evaluated.evaluation
    values = tuple(float(value) for value in evaluation.utilities)
    best_responses = tuple(float(value) for value in evaluation.best_response_values)
    if (
        len(values) != layout.num_players
        or len(best_responses) != layout.num_players
        or any(not math.isfinite(value) for value in values + best_responses)
    ):
        raise FloatingPointError("pre-bet exact source evaluation is invalid")
    sources: list[PreBetInitialRowSource] = [
        PreBetInitialRowSource("profile", player, compiled, values[player])
        for player in range(layout.num_players)
    ]
    for player in range(layout.num_players):
        if player == acting_player:
            continue
        response = splice_fixed_response_probability_tape_for_axes(
            layout,
            compiled,
            evaluated.best_response_actions[player],
            responding_player=player,
            hands_by_player=hands_by_player,
        )
        sources.append(
            PreBetInitialRowSource(
                "fixed_response",
                player,
                response,
                best_responses[player],
            )
        )
    checked_sources = _v1._validate_sources(identity, tuple(sources))
    return PreBetRowCacheContext(
        layout=layout,
        belief=belief,
        hands_by_player=hands_by_player,
        policy=frozen_policy,
        source_probabilities=compiled,
        identity=identity,
        sources=checked_sources,
        acting_best_response_value=best_responses[acting_player],
        layout_numeric_sha256=_layout_numeric_digest(layout),
        _factory_token=_CONTEXT_FACTORY_TOKEN,
    )


def _require_live_context(context: PreBetRowCacheContext) -> None:
    if not isinstance(context, PreBetRowCacheContext):
        raise TypeError("v2 pre-bet cache requires a live cache context")
    current = _build_identity(
        context.layout,
        context.belief,
        context.hands_by_player,
        context.policy,
        context.source_probabilities,
        acting_player=context.identity.acting_player,
        public_node=context.identity.public_node,
        row_primitive_sha256=context.identity.row_primitive_sha256,
    )
    if current != context.identity:
        raise ValueError("pre-bet live context changed after construction")
    if _layout_numeric_digest(context.layout) != context.layout_numeric_sha256:
        raise ValueError("pre-bet live layout numerics changed after construction")
    evaluated = context.layout.evaluate(context.policy)
    values = tuple(float(value) for value in evaluated.evaluation.utilities)
    best_responses = tuple(
        float(value) for value in evaluated.evaluation.best_response_values
    )
    if any(not math.isfinite(value) for value in values + best_responses):
        raise FloatingPointError("pre-bet live exact evaluation is invalid")
    rebuilt: list[PreBetInitialRowSource] = [
        PreBetInitialRowSource(
            "profile",
            player,
            context.source_probabilities,
            values[player],
        )
        for player in range(context.identity.num_players)
    ]
    for player in range(context.identity.num_players):
        if player == context.identity.acting_player:
            continue
        response = splice_fixed_response_probability_tape_for_axes(
            context.layout,
            context.source_probabilities,
            evaluated.best_response_actions[player],
            responding_player=player,
            hands_by_player=context.hands_by_player,
        )
        rebuilt.append(
            PreBetInitialRowSource(
                "fixed_response",
                player,
                response,
                best_responses[player],
            )
        )
    checked = _v1._validate_sources(context.identity, tuple(rebuilt))
    if len(checked) != len(context.sources):
        raise ValueError("pre-bet live source bundle changed")
    for original, fresh in zip(context.sources, checked, strict=True):
        if (
            (original.role, original.payoff_player)
            != (fresh.role, fresh.payoff_player)
            or probability_tape_digest(original.probabilities)
            != probability_tape_digest(fresh.probabilities)
            or abs(original.source_value - fresh.source_value) > SOURCE_IDENTITY_ATOL
        ):
            raise ValueError("pre-bet live source bundle changed")
    if abs(context.acting_best_response_value - best_responses[
        context.identity.acting_player
    ]) > SOURCE_IDENTITY_ATOL:
        raise ValueError("pre-bet acting best-response value changed")


@dataclass(frozen=True, slots=True, init=False)
class PreBetRowCachePopulation:
    """Factory-only complete rows plus the internally derived actor BR."""

    identity_sha256: str
    sources: tuple[PreBetInitialRowSource, ...]
    rows: tuple[PreBetInitialRow, ...]
    acting_best_response_value: float

    def __init__(
        self,
        *,
        identity_sha256: str,
        sources: tuple[PreBetInitialRowSource, ...],
        rows: tuple[PreBetInitialRow, ...],
        acting_best_response_value: float,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _POPULATION_FACTORY_TOKEN:
            raise TypeError(
                "pre-bet cache populations are factory-only; use "
                "populate_pre_bet_initial_row_cache"
            )
        object.__setattr__(self, "identity_sha256", identity_sha256)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self,
            "acting_best_response_value",
            acting_best_response_value,
        )


def populate_pre_bet_initial_row_cache(
    context: PreBetRowCacheContext,
    affine_contexts: Sequence[PublicNodeAffineSourceContext],
) -> PreBetRowCachePopulation:
    """Build the complete cache bundle only from validated affine contexts."""

    _require_live_context(context)
    supplied = tuple(affine_contexts)
    if len(supplied) != len(context.sources) or any(
        not isinstance(item, PublicNodeAffineSourceContext) for item in supplied
    ):
        raise ValueError("pre-bet population requires every bound affine context")
    rows = []
    for expected, affine in zip(context.sources, supplied, strict=True):
        if (
            affine.layout is not context.layout
            or affine.acting_player != context.identity.acting_player
            or affine.payoff_player != expected.payoff_player
            or affine.public_node != context.identity.public_node
            or probability_tape_digest(affine.probabilities)
            != probability_tape_digest(expected.probabilities)
            or abs(affine.source_value - expected.source_value) > SOURCE_IDENTITY_ATOL
        ):
            raise ValueError("pre-bet affine population context has stale provenance")
        item = PreBetInitialRow(
            expected.role,
            expected.payoff_player,
            public_node_open_axis_payoff_row(affine),
        )
        _v1._validate_row(context.identity, expected, item)
        rows.append(item)
    return PreBetRowCachePopulation(
        identity_sha256=_identity_digest(context.identity),
        sources=context.sources,
        rows=tuple(rows),
        acting_best_response_value=context.acting_best_response_value,
        _factory_token=_POPULATION_FACTORY_TOKEN,
    )


@dataclass(frozen=True, slots=True)
class UnsealedPreBetCacheWrite:
    """Writer telemetry that is deliberately not accepted by replay APIs."""

    output_path: Path
    persisted_sha256: str
    persisted_bytes: int


def _write_all_exclusive(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise OSError("pre-bet cache write made no progress")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def write_pre_bet_initial_row_cache(
    path: Path,
    context: PreBetRowCacheContext,
    population: PreBetRowCachePopulation,
) -> UnsealedPreBetCacheWrite:
    """Persist a complete population without creating replay authority."""

    _require_live_context(context)
    if not isinstance(population, PreBetRowCachePopulation):
        raise TypeError("v2 cache writer requires a factory population")
    if population.identity_sha256 != _identity_digest(context.identity):
        raise ValueError("pre-bet population belongs to another live context")
    for source, row in zip(population.sources, population.rows, strict=True):
        _v1._validate_row(context.identity, source, row)
    if population.sources is not context.sources:
        raise ValueError("pre-bet population source bundle differs")
    payload = {
        "schema": CACHE_SCHEMA,
        "identity": context.identity.to_record(),
        "acting_best_response_value_f64le": _v1._f64le_hex(
            population.acting_best_response_value
        ),
        "rows": [
            {
                "role": source.role,
                "payoff_player": source.payoff_player,
                "probability_tape_sha256": probability_tape_digest(
                    source.probabilities
                ),
                "source_value_f64le": _v1._f64le_hex(source.source_value),
                "row": _v1._serialize_row(item.row),
            }
            for source, item in zip(
                population.sources,
                population.rows,
                strict=True,
            )
        ],
    }
    rendered = _v1._json_bytes(payload)
    maximum = _v1._maximum_serialized_cache_bytes(context.identity, context.sources)
    if len(rendered) > maximum:
        raise ValueError("serialized pre-bet cache exceeds its safety cap")
    if not isinstance(path, Path):
        raise TypeError("pre-bet cache output path must be a Path")
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(f"pre-bet cache output already exists: {path}")
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{time.monotonic_ns()}.untrusted.tmp"
    )
    try:
        _write_all_exclusive(temporary, rendered)
        staged = read_bounded_file_once(temporary, maximum_bytes=maximum)
        if staged != rendered:
            raise OSError("persisted pre-bet cache staging bytes differ")
        os.link(temporary, path)
        persisted = read_bounded_file_once(path, maximum_bytes=maximum)
        if persisted != rendered:
            raise OSError("persisted pre-bet cache bytes differ")
        temporary.unlink()
        _fsync_directory(path.parent)
    except BaseException:
        if os.path.lexists(temporary):
            temporary.unlink()
        raise
    return UnsealedPreBetCacheWrite(
        output_path=path,
        persisted_sha256=hashlib.sha256(persisted).hexdigest(),
        persisted_bytes=len(persisted),
    )


@dataclass(frozen=True, slots=True, init=False)
class SealedPreBetCacheEntry:
    """Replay authority obtained only by loading external manifest bytes."""

    cache_sha256: str
    cache_bytes: int
    identity_sha256: str
    seal_sha256: str
    seal_path: Path

    def __init__(
        self,
        *,
        cache_sha256: str,
        cache_bytes: int,
        identity_sha256: str,
        seal_sha256: str,
        seal_path: Path,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _SEAL_FACTORY_TOKEN:
            raise TypeError(
                "pre-bet cache seals are factory-only; use "
                "load_pre_bet_cache_seal"
            )
        object.__setattr__(self, "cache_sha256", cache_sha256)
        object.__setattr__(self, "cache_bytes", cache_bytes)
        object.__setattr__(self, "identity_sha256", identity_sha256)
        object.__setattr__(self, "seal_sha256", seal_sha256)
        object.__setattr__(self, "seal_path", seal_path)


def load_pre_bet_cache_seal(
    path: Path,
    *,
    expected_seal_sha256: str,
) -> SealedPreBetCacheEntry:
    """Load a separately persisted exact seal; no cache writer returns this type."""

    def validate(payload: Mapping[str, Any]) -> None:
        if set(payload) != _SEAL_KEYS or payload.get("schema") != SEAL_SCHEMA:
            raise ValueError("pre-bet cache seal schema differs")
        for field in ("cache_sha256", "identity_sha256"):
            if not _v1._is_sha256(payload.get(field)):
                raise ValueError(f"pre-bet cache seal {field} is malformed")
        size = payload.get("cache_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ValueError("pre-bet cache seal byte count is invalid")

    loaded = load_artifact(
        path,
        expected_sha256=expected_seal_sha256,
        maximum_bytes=65_536,
        schema_validator=validate,
    )
    return SealedPreBetCacheEntry(
        cache_sha256=str(loaded.payload["cache_sha256"]),
        cache_bytes=int(loaded.payload["cache_bytes"]),
        identity_sha256=str(loaded.payload["identity_sha256"]),
        seal_sha256=loaded.sha256,
        seal_path=path,
        _factory_token=_SEAL_FACTORY_TOKEN,
    )


@dataclass(frozen=True, slots=True)
class PreBetRowCacheLookup:
    hit: bool
    reason: str
    rows: tuple[PreBetInitialRow, ...] | None
    acting_best_response_value: float | None
    sealed_persisted_sha256: str
    observed_persisted_sha256: str | None
    lookup_validation_ms: float


def _lookup_result(
    *,
    hit: bool,
    reason: str,
    rows: tuple[PreBetInitialRow, ...] | None,
    acting_best_response_value: float | None,
    expected: str,
    observed: str | None,
    started_ns: int,
) -> PreBetRowCacheLookup:
    if not hit and (rows is not None or acting_best_response_value is not None):
        raise AssertionError("v2 cache miss exposed trusted data")
    return PreBetRowCacheLookup(
        hit=hit,
        reason=reason,
        rows=rows,
        acting_best_response_value=acting_best_response_value,
        sealed_persisted_sha256=expected,
        observed_persisted_sha256=observed,
        lookup_validation_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
    )


def _miss(
    reason: str,
    *,
    seal: SealedPreBetCacheEntry | None,
    observed: str | None,
    started_ns: int,
) -> PreBetRowCacheLookup:
    return _lookup_result(
        hit=False,
        reason=reason,
        rows=None,
        acting_best_response_value=None,
        expected="" if seal is None else seal.cache_sha256,
        observed=observed,
        started_ns=started_ns,
    )


def lookup_pre_bet_initial_row_cache(
    path: Path,
    seal: SealedPreBetCacheEntry,
    context: PreBetRowCacheContext,
) -> PreBetRowCacheLookup:
    """Validate sealed bytes against a freshly rederived live context."""

    started_ns = time.perf_counter_ns()
    if not isinstance(seal, SealedPreBetCacheEntry):
        return _miss(
            "external_seal_required",
            seal=None,
            observed=None,
            started_ns=started_ns,
        )
    try:
        _require_live_context(context)
    except (ArithmeticError, TypeError, ValueError):
        return _miss(
            "current_context_contract_mismatch",
            seal=seal,
            observed=None,
            started_ns=started_ns,
        )
    if seal.identity_sha256 != _identity_digest(context.identity):
        return _miss(
            "sealed_identity_mismatch",
            seal=seal,
            observed=None,
            started_ns=started_ns,
        )
    maximum = _v1._maximum_serialized_cache_bytes(context.identity, context.sources)
    if seal.cache_bytes > maximum:
        return _miss(
            "cache_size_safety_cap_exceeded",
            seal=seal,
            observed=None,
            started_ns=started_ns,
        )
    try:
        persisted = read_bounded_file_once(path, maximum_bytes=maximum)
    except ValueError:
        return _miss(
            "cache_size_safety_cap_exceeded",
            seal=seal,
            observed=None,
            started_ns=started_ns,
        )
    except OSError:
        return _miss(
            "cache_unavailable",
            seal=seal,
            observed=None,
            started_ns=started_ns,
        )
    observed = hashlib.sha256(persisted).hexdigest()
    if observed != seal.cache_sha256 or len(persisted) != seal.cache_bytes:
        return _miss(
            "persisted_byte_identity_mismatch",
            seal=seal,
            observed=observed,
            started_ns=started_ns,
        )
    try:
        decoded = _v1._decode_cache(persisted)
        if isinstance(decoded, dict) and decoded.get("schema") == LEGACY_CACHE_SCHEMA:
            return _miss(
                "legacy_v1_cache_rejected",
                seal=seal,
                observed=observed,
                started_ns=started_ns,
            )
        root = _v1._require_exact_keys(decoded, _CACHE_TOP_LEVEL_KEYS, "root")
        if root["schema"] != CACHE_SCHEMA:
            return _miss(
                "cache_schema_mismatch",
                seal=seal,
                observed=observed,
                started_ns=started_ns,
            )
        if not _v1._identity_record_matches(root["identity"], context.identity):
            return _miss(
                "full_provenance_identity_mismatch",
                seal=seal,
                observed=observed,
                started_ns=started_ns,
            )
        acting_value = _v1._parse_f64le_hex(
            root["acting_best_response_value_f64le"]
        )
        if abs(acting_value - context.acting_best_response_value) > (
            SOURCE_IDENTITY_ATOL
        ):
            return _miss(
                "acting_best_response_identity_mismatch",
                seal=seal,
                observed=observed,
                started_ns=started_ns,
            )
        serialized_rows = root["rows"]
        if not isinstance(serialized_rows, list) or len(serialized_rows) != len(
            context.sources
        ):
            raise ValueError("cached row bundle count differs")
        loaded_rows = []
        for source, serialized in zip(
            context.sources,
            serialized_rows,
            strict=True,
        ):
            record = _v1._require_exact_keys(
                serialized,
                _v1._CACHE_ROW_KEYS,
                "row record",
            )
            role = record["role"]
            payoff_player = _v1._parse_int(record["payoff_player"], "payoff player")
            if (role, payoff_player) != (source.role, source.payoff_player):
                raise ValueError("cached row role order differs")
            if record["probability_tape_sha256"] != probability_tape_digest(
                source.probabilities
            ):
                return _miss(
                    "row_probability_tape_mismatch",
                    seal=seal,
                    observed=observed,
                    started_ns=started_ns,
                )
            stored_source = _v1._parse_f64le_hex(record["source_value_f64le"])
            if abs(stored_source - source.source_value) > SOURCE_IDENTITY_ATOL:
                return _miss(
                    "source_value_identity_mismatch",
                    seal=seal,
                    observed=observed,
                    started_ns=started_ns,
                )
            current = source.probabilities[context.identity.public_node]
            if current is None:
                raise ValueError("cached current source row is absent")
            item = PreBetInitialRow(
                source.role,
                source.payoff_player,
                _v1._deserialize_row(
                    record["row"],
                    identity=context.identity,
                    expected_shape=current.shape,
                ),
            )
            _v1._validate_row(context.identity, source, item)
            loaded_rows.append(item)
    except ArithmeticError:
        return _miss(
            "current_source_numerical_mismatch",
            seal=seal,
            observed=observed,
            started_ns=started_ns,
        )
    except (KeyError, TypeError, UnicodeError, ValueError):
        return _miss(
            "malformed_cache",
            seal=seal,
            observed=observed,
            started_ns=started_ns,
        )
    return _lookup_result(
        hit=True,
        reason="exact_sealed_hit",
        rows=tuple(loaded_rows),
        acting_best_response_value=acting_value,
        expected=seal.cache_sha256,
        observed=observed,
        started_ns=started_ns,
    )


def _miss_preparation(
    *,
    reason: str,
    external_policy: Policy,
    started_ns: int,
    lookup_validation_ms: float = 0.0,
) -> PreBetRestrictedMasterPreparation:
    return PreBetRestrictedMasterPreparation(
        cache_hit=False,
        reason=reason,
        initial_rows=None,
        gain_rows=None,
        external_policy=external_policy,
        lookup_validation_ms=lookup_validation_ms,
        on_clock_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
        warm_steps=0,
        master_solves=0,
        candidate_emissions=0,
        strategy_quality_rows=0,
    )


def prepare_pre_bet_restricted_master_successor(
    path: Path,
    seal: SealedPreBetCacheEntry,
    context: PreBetRowCacheContext,
    immutable_blueprint: Mapping[str, Mapping[object, float]],
) -> PreBetRestrictedMasterPreparation:
    """Prepare gain rows only from a sealed lookup and the bound live context."""

    started_ns = time.perf_counter_ns()
    external_policy = _v1._defensive_policy_copy(immutable_blueprint)
    try:
        _require_live_context(context)
    except (ArithmeticError, TypeError, ValueError):
        return _miss_preparation(
            reason="current_context_contract_mismatch",
            external_policy=external_policy,
            started_ns=started_ns,
        )
    if exact_policy_digest(external_policy) != context.identity.policy_sha256:
        return _miss_preparation(
            reason="immutable_blueprint_identity_mismatch",
            external_policy=external_policy,
            started_ns=started_ns,
        )
    lookup = lookup_pre_bet_initial_row_cache(path, seal, context)
    if (
        not lookup.hit
        or lookup.rows is None
        or lookup.acting_best_response_value is None
    ):
        return _miss_preparation(
            reason=lookup.reason,
            external_policy=external_policy,
            started_ns=started_ns,
            lookup_validation_ms=lookup.lookup_validation_ms,
        )
    try:
        gains = _v1.assemble_pre_bet_gain_rows(
            context.identity,
            context.sources,
            lookup.rows,
            acting_best_response_value=lookup.acting_best_response_value,
        )
    except (ArithmeticError, KeyError, TypeError, ValueError):
        return _miss_preparation(
            reason="gain_row_assembly_mismatch",
            external_policy=external_policy,
            started_ns=started_ns,
            lookup_validation_ms=lookup.lookup_validation_ms,
        )
    return PreBetRestrictedMasterPreparation(
        cache_hit=True,
        reason="exact_sealed_hit",
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


__all__ = [
    "CACHE_SCHEMA",
    "LEGACY_CACHE_SCHEMA",
    "SEAL_SCHEMA",
    "SOURCE_IDENTITY_ATOL",
    "PreBetInitialRow",
    "PreBetRestrictedMasterPreparation",
    "PreBetRowCacheContext",
    "PreBetRowCacheLookup",
    "PreBetRowCachePopulation",
    "SealedPreBetCacheEntry",
    "UnsealedPreBetCacheWrite",
    "build_pre_bet_row_cache_context",
    "cpu_h2_control_row_primitive_digest",
    "exact_policy_digest",
    "load_pre_bet_cache_seal",
    "lookup_pre_bet_initial_row_cache",
    "numerical_contract_digest",
    "populate_pre_bet_initial_row_cache",
    "prepare_pre_bet_restricted_master_successor",
    "probability_tape_digest",
    "write_pre_bet_initial_row_cache",
]
