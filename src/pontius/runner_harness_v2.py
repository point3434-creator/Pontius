"""Strict, immutable, single-read inputs for successor evidence runners.

The historical :mod:`pontius.runner_harness` remains byte-pinned protocol
memory.  This module is intentionally a new boundary: JSON bytes are bounded
before allocation, decoded without duplicate keys or non-finite constants,
deep-frozen, and carried with the digest of the exact bytes that were parsed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypeAlias

DEFAULT_MAXIMUM_JSON_BYTES = 64 * 1024 * 1024
JsonSchemaValidator: TypeAlias = Callable[[Mapping[str, Any]], None]


def _validate_maximum_bytes(maximum_bytes: int) -> int:
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes <= 0
    ):
        raise ValueError("maximum JSON bytes must be a positive integer")
    return maximum_bytes


def read_bounded_file_once(
    path: Path,
    *,
    maximum_bytes: int = DEFAULT_MAXIMUM_JSON_BYTES,
) -> bytes:
    """Read one regular file through one descriptor under an allocation cap."""

    if not isinstance(path, Path):
        raise TypeError("bounded input path must be a Path")
    maximum = _validate_maximum_bytes(maximum_bytes)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"required input is not a regular file: {path}")
        if before.st_size < 0 or before.st_size > maximum:
            raise ValueError(f"required input exceeds byte limit: {path}")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > maximum:
            raise ValueError(f"required input exceeds byte limit: {path}")
        after = os.fstat(descriptor)
        stable_fields = (
            before.st_dev == after.st_dev,
            before.st_ino == after.st_ino,
            before.st_size == after.st_size == len(raw),
            getattr(before, "st_mtime_ns", None)
            == getattr(after, "st_mtime_ns", None),
        )
        if not all(stable_fields):
            raise OSError(f"required input changed while being read: {path}")
        return raw
    finally:
        os.close(descriptor)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON object repeats key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_constant(token: str) -> None:
    raise ValueError(f"JSON contains non-finite constant {token}")


def decode_strict_json_object(raw: bytes, *, source: str) -> dict[str, Any]:
    """Decode one UTF-8 JSON object with no duplicate or non-finite values."""

    try:
        text = raw.decode("utf-8", errors="strict")
        decoded = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON input: {source}") from error
    if not isinstance(decoded, dict):
        raise TypeError(f"JSON root must be an object: {source}")
    return decoded


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("decoded JSON contains a non-finite number")
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise TypeError(f"decoded JSON contains unsupported type {type(value).__name__}")


def _validate_expected_digest(expected_sha256: str | None) -> None:
    if expected_sha256 is None:
        return
    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or expected_sha256 != expected_sha256.lower()
        or any(character not in "0123456789abcdef" for character in expected_sha256)
    ):
        raise ValueError("expected input digest must be a lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class LoadedJsonDocument:
    """Immutable parsed data and the one exact byte snapshot that produced it."""

    path: Path
    payload: Mapping[str, Any]
    raw_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class LoadedConfig(LoadedJsonDocument):
    """A strict successor configuration snapshot."""


@dataclass(frozen=True, slots=True)
class LoadedArtifact(LoadedJsonDocument):
    """A strict successor evidence-artifact snapshot."""


def _load_json_document(
    kind: type[LoadedJsonDocument],
    path: Path,
    *,
    expected_sha256: str | None,
    maximum_bytes: int,
    schema_validator: JsonSchemaValidator,
) -> LoadedJsonDocument:
    if not callable(schema_validator):
        raise TypeError("successor JSON loading requires a schema validator")
    _validate_expected_digest(expected_sha256)
    raw = read_bounded_file_once(path, maximum_bytes=maximum_bytes)
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"input digest differs: {path}")
    decoded = decode_strict_json_object(raw, source=str(path))
    schema_validator(decoded)
    frozen = _deep_freeze(decoded)
    if not isinstance(frozen, Mapping):
        raise TypeError("deep-frozen JSON root stopped being a mapping")
    return kind(path=path, payload=frozen, raw_bytes=raw, sha256=digest)


def load_config(
    path: Path,
    *,
    schema_validator: JsonSchemaValidator,
    expected_sha256: str | None = None,
    maximum_bytes: int = DEFAULT_MAXIMUM_JSON_BYTES,
) -> LoadedConfig:
    """Load and validate one config from the same bytes later hashed/reported."""

    loaded = _load_json_document(
        LoadedConfig,
        path,
        expected_sha256=expected_sha256,
        maximum_bytes=maximum_bytes,
        schema_validator=schema_validator,
    )
    assert isinstance(loaded, LoadedConfig)
    return loaded


def load_artifact(
    path: Path,
    *,
    schema_validator: JsonSchemaValidator,
    expected_sha256: str | None = None,
    maximum_bytes: int = DEFAULT_MAXIMUM_JSON_BYTES,
) -> LoadedArtifact:
    """Load one artifact only after its complete typed schema validates."""

    loaded = _load_json_document(
        LoadedArtifact,
        path,
        expected_sha256=expected_sha256,
        maximum_bytes=maximum_bytes,
        schema_validator=schema_validator,
    )
    assert isinstance(loaded, LoadedArtifact)
    return loaded


def require_passing_artifact_schema(
    payload: Mapping[str, Any],
    *,
    required_paths: tuple[tuple[str, ...], ...],
) -> None:
    """Validate the pass bit plus caller-declared schema-completeness paths."""

    missing = object()
    top = payload.get("passed", missing)
    gates = payload.get("gates")
    nested = gates.get("passed", missing) if isinstance(gates, Mapping) else missing
    values = tuple(value for value in (top, nested) if value is not missing)
    if not values or any(type(value) is not bool for value in values):
        raise ValueError("artifact must expose a Boolean passed field")
    if len(values) == 2 and values[0] != values[1]:
        raise ValueError("artifact top-level and gate pass fields disagree")
    if not values[0]:
        raise ValueError("required parent artifact did not pass")
    if not required_paths:
        raise ValueError("passing artifact schema must declare required fields")
    for path in required_paths:
        if not path or any(not isinstance(key, str) or not key for key in path):
            raise ValueError("artifact required paths must be nonempty string tuples")
        value: Any = payload
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                raise ValueError(f"artifact lacks required field {'.'.join(path)}")
            value = value[key]


__all__ = [
    "DEFAULT_MAXIMUM_JSON_BYTES",
    "LoadedArtifact",
    "LoadedConfig",
    "LoadedJsonDocument",
    "decode_strict_json_object",
    "load_artifact",
    "load_config",
    "read_bounded_file_once",
    "require_passing_artifact_schema",
]
