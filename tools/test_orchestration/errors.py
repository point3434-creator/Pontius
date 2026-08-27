"""Stable, tool-local exceptions for test orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TypeAlias


FrozenContextValue: TypeAlias = (
    str
    | int
    | bool
    | None
    | tuple["FrozenContextValue", ...]
    | frozenset["FrozenContextValue"]
    | Mapping[str, "FrozenContextValue"]
)


def _freeze_context_value(value: object) -> FrozenContextValue:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, Mapping):
        frozen_items: list[tuple[str, FrozenContextValue]] = []
        for key, nested_value in value.items():
            if type(key) is not str:
                raise TypeError("orchestration error context keys must be strings")
            frozen_items.append((key, _freeze_context_value(nested_value)))
        return MappingProxyType(dict(sorted(frozen_items)))
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_context_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_context_value(item) for item in value)
    raise TypeError("orchestration error context contains an unsupported value")


class OrchestrationError(Exception):
    """Base exception carrying stable machine-readable fields."""

    def __init__(self, code: str, message: str, *, context: Mapping[str, object]) -> None:
        if type(code) is not str or not code:
            raise ValueError("orchestration error code must be a non-empty string")
        if type(message) is not str or not message:
            raise ValueError("orchestration error message must be a non-empty string")
        frozen_context = _freeze_context_value(context)
        if not isinstance(frozen_context, Mapping):
            raise TypeError("orchestration error context must be a mapping")
        self.code = code
        self.message = message
        self.context = frozen_context
        super().__init__(message)


class EvidenceConfigurationError(OrchestrationError):
    """Profile, inventory, or command configuration is invalid."""


class EvidenceIntegrityError(OrchestrationError):
    """Evidence bytes or semantic identity do not match their contract."""


class AuthorizationPhaseError(OrchestrationError):
    """The requested authorization phase is unavailable or mixed."""


class LifecycleStateError(OrchestrationError):
    """Lifecycle state is incompatible with the selected profile."""


class RuntimeContractError(OrchestrationError):
    """A runtime collaborator violated the orchestration contract."""
