"""Shared topology/automaton residency with target-specific response contexts."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Mapping

from .incremental_leaf_adjoint_response import (
    LeafAdjointResponseSeatCache,
    compile_leaf_adjoint_response_caches,
)
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)


@dataclass(frozen=True, slots=True)
class SharedResidentAutomatonBundle:
    """One immutable device automaton payload reusable across belief shifts."""

    topology: Any
    terminal_automata: tuple[Mapping[str, Any], ...]
    automaton_caches: tuple[CuPyResidentAutomatonCache, ...]
    compile_ms: float
    numeric_bytes: int

    @classmethod
    def compile(
        cls,
        workspace: Any,
        terminal_automata: tuple[Mapping[str, Any], ...],
    ) -> SharedResidentAutomatonBundle:
        players = len(workspace.topology.base.hand_counts)
        if len(terminal_automata) != players:
            raise ValueError("shared bundle requires one automaton library per seat")
        started = time.perf_counter()
        caches = tuple(
            CuPyResidentAutomatonCache.compile(
                workspace,
                terminal_automata[seat],
                target_seat=seat,
            )
            for seat in range(players)
        )
        return cls(
            topology=workspace.topology,
            terminal_automata=tuple(terminal_automata),
            automaton_caches=caches,
            compile_ms=(time.perf_counter() - started) * 1000.0,
            numeric_bytes=sum(cache.numeric_bytes for cache in caches),
        )

    def validate_workspace(self, workspace: Any) -> None:
        if workspace.topology is not self.topology:
            raise ValueError("shared automaton bundle belongs to another topology")


@dataclass(frozen=True, slots=True)
class ResidentResponseContext:
    """Target-belief state bound to one shared resident automaton bundle."""

    workspace: Any
    hands_by_player: tuple[tuple[Any, ...], ...]
    belief_cache: CuPyResidentBeliefCache
    response_caches: tuple[LeafAdjointResponseSeatCache, ...]
    belief_compile_ms: float
    response_compile_ms: float
    numeric_bytes: int


def bind_resident_response_context(
    bundle: SharedResidentAutomatonBundle,
    *,
    layout: Any,
    workspace: Any,
    sparse: Any,
    source_policy: dict[str, dict[str, float]],
    hands_by_player: tuple[tuple[Any, ...], ...],
    cupy_sparse: Any,
    maximum_feature_width_per_batch: int = 384,
) -> ResidentResponseContext:
    """Bind one belief and source-response overlay without duplicating automata."""

    bundle.validate_workspace(workspace)
    if sparse.topology is not workspace.topology:
        raise ValueError("resident response sparse operator belongs to another topology")
    belief_started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    belief_ms = (time.perf_counter() - belief_started) * 1000.0
    response_started = time.perf_counter()
    response_caches = compile_leaf_adjoint_response_caches(
        layout,
        workspace,
        sparse,
        source_policy,
        bundle.terminal_automata,
        hands_by_player=hands_by_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        belief_cache=belief_cache,
        automaton_caches=bundle.automaton_caches,
        cupy_sparse=cupy_sparse,
    )
    response_ms = (time.perf_counter() - response_started) * 1000.0
    return ResidentResponseContext(
        workspace=workspace,
        hands_by_player=hands_by_player,
        belief_cache=belief_cache,
        response_caches=response_caches,
        belief_compile_ms=belief_ms,
        response_compile_ms=response_ms,
        numeric_bytes=belief_cache.numeric_bytes,
    )


def unique_response_numeric_bytes(
    contexts: tuple[ResidentResponseContext, ...],
) -> int:
    """Count identity-unique host numeric arrays across bound response contexts."""

    arrays: dict[int, Any] = {}
    for context in contexts:
        for cache in context.response_caches:
            for values in (
                cache.parents,
                cache.parent_actions,
                *cache.source_probabilities,
                *cache.terminal_values,
            ):
                if values is not None:
                    arrays.setdefault(id(values), values)
    return sum(int(values.nbytes) for values in arrays.values())


def shared_device_numeric_bytes(
    bundle: SharedResidentAutomatonBundle,
    contexts: tuple[ResidentResponseContext, ...],
) -> int:
    """Count the explicit shared automaton payload plus bound belief payloads."""

    if any(context.workspace.topology is not bundle.topology for context in contexts):
        raise ValueError("resident response context belongs to another topology")
    return bundle.numeric_bytes + sum(context.numeric_bytes for context in contexts)
