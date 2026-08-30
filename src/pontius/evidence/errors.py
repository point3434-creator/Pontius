"""Stable exceptions for the evidence boundary."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TypeAlias


FrozenContextValue: TypeAlias = str | int | bool | None | tuple["FrozenContextValue", ...] | frozenset["FrozenContextValue"] | Mapping[str, "FrozenContextValue"]


def _freeze_context_value(value: object) -> FrozenContextValue:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Mapping):
        frozen_items: list[tuple[str, FrozenContextValue]] = []
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise TypeError("evidence error context keys must be strings")
            frozen_items.append((key, _freeze_context_value(nested_value)))
        return MappingProxyType(dict(sorted(frozen_items)))
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_context_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_context_value(item) for item in value)
    raise TypeError("evidence error context contains an unsupported value")


class EvidenceError(Exception):
    """Base class carrying a stable machine-readable failure code."""

    def __init__(self, code: str, message: str, *, context: Mapping[str, object]) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("evidence error code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("evidence error message must be a non-empty string")
        frozen_context = _freeze_context_value(context)
        if not isinstance(frozen_context, Mapping):
            raise TypeError("evidence error context must be a mapping")
        self.code = code
        self.message = message
        self.context = frozen_context
        super().__init__(message)


class EvidenceConfigurationError(EvidenceError):
    """Configuration is malformed or violates its contract."""


class EvidenceIntegrityError(EvidenceError):
    """Evidence content does not match its claimed identity or invariants."""


class AuthorizationPhaseError(EvidenceError):
    """Repository state cannot satisfy the requested authorization phase."""


class LifecycleStateError(EvidenceError):
    """Lifecycle state is incompatible with the requested operation."""


class RuntimeContractError(EvidenceError):
    """A supplied runtime collaborator violated its contract."""
