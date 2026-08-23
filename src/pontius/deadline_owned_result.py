"""Deadline-owned result data published only by a verified completion seal."""

from __future__ import annotations

import hashlib
import math
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .campaign_deadline import (
    CampaignDeadlineSnapshot,
    CampaignDeadlineStop,
    MonotonicCampaignDeadline,
)
from .runner_harness import serialize_result
from .runner_harness_v2 import decode_strict_json_object, read_bounded_file_once

RESULT_ENVELOPE_SCHEMA = "pontius-deadline-owned-result-envelope-v2"
RESULT_SEAL_SCHEMA = "pontius-deadline-owned-result-seal-v1"
DEFAULT_MAXIMUM_RESULT_BYTES = 256 * 1024 * 1024
_ENVELOPE_KEYS = {"deadline_admission", "payload", "schema"}
_SEAL_KEYS = {
    "data_bytes",
    "data_sha256",
    "envelope_schema",
    "postcheck_completed",
    "schema",
}
_ADMISSION_KEYS = {
    "admitted_deadline",
    "conservative_publication_verification_elapsed_upper_seconds",
    "maximum_finalization_seconds",
    "unit",
}
_DEADLINE_KEYS = {
    "clock",
    "deadline_crossed",
    "elapsed_seconds",
    "maximum_seconds",
    "remaining_seconds",
}


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise TypeError("deadline-owned canonical JSON contains an unsupported value")


@dataclass(frozen=True, slots=True)
class DeadlineOwnedResultAdmission:
    """Admission evidence embedded by the helper, outside builder authority."""

    unit_name: str
    maximum_finalization_seconds: float
    admitted_deadline: CampaignDeadlineSnapshot
    conservative_publication_verification_elapsed_upper_seconds: float

    def as_record(self) -> dict[str, Any]:
        return {
            "unit": self.unit_name,
            "maximum_finalization_seconds": self.maximum_finalization_seconds,
            "admitted_deadline": self.admitted_deadline.as_record(),
            "conservative_publication_verification_elapsed_upper_seconds": (
                self.conservative_publication_verification_elapsed_upper_seconds
            ),
        }


@dataclass(frozen=True, slots=True)
class DeadlineOwnedAtomicResult:
    """Immutable payload backed by canonical data and a completion seal."""

    result: Mapping[str, Any]
    envelope: Mapping[str, Any]
    admission: DeadlineOwnedResultAdmission
    output_path: Path
    seal_path: Path
    persisted_sha256: str
    persisted_bytes: int
    seal_sha256: str


def _staging_path(output_path: Path) -> Path:
    return output_path.with_suffix(f"{output_path.suffix}.untrusted.tmp")


def _seal_path(output_path: Path) -> Path:
    return output_path.with_suffix(f"{output_path.suffix}.seal.json")


def _lock_path(output_path: Path) -> Path:
    return output_path.with_suffix(f"{output_path.suffix}.publishing.lock")


def _path_entry_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _write_exclusive(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        _write_descriptor(descriptor, payload)
    finally:
        os.close(descriptor)


def _write_descriptor(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(descriptor, view[offset:])
        if written <= 0:
            raise OSError("deadline-owned write made no progress")
        offset += written
    os.fsync(descriptor)


def _overwrite_lock(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        os.ftruncate(descriptor, 0)
        _write_descriptor(descriptor, payload)
        after = os.fstat(descriptor)
        if before.st_dev != after.st_dev or before.st_ino != after.st_ino:
            raise OSError("deadline-owned publishing lock changed during write")
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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_result(path: Path, maximum_bytes: int) -> bytes:
    return read_bounded_file_once(path, maximum_bytes=maximum_bytes)


def _decode_envelope(raw: bytes, *, source: str) -> Mapping[str, Any]:
    decoded = decode_strict_json_object(raw, source=source)
    if set(decoded) != _ENVELOPE_KEYS or decoded.get("schema") != RESULT_ENVELOPE_SCHEMA:
        raise ValueError("deadline-owned result envelope schema differs")
    if not isinstance(decoded["deadline_admission"], dict):
        raise TypeError("deadline-owned admission record is malformed")
    if not isinstance(decoded["payload"], dict):
        raise TypeError("deadline-owned result payload must be an object")
    frozen = _deep_freeze(decoded)
    if not isinstance(frozen, Mapping):
        raise TypeError("deadline-owned envelope stopped being a mapping")
    return frozen


def _admission_from_record(record: Mapping[str, Any]) -> DeadlineOwnedResultAdmission:
    if set(record) != _ADMISSION_KEYS:
        raise ValueError("deadline-owned admission schema differs")
    unit = record["unit"]
    admitted = record["admitted_deadline"]
    if not isinstance(unit, str) or not unit.strip() or not isinstance(admitted, Mapping):
        raise ValueError("deadline-owned admission record is malformed")
    if set(admitted) != _DEADLINE_KEYS or admitted["clock"] != "monotonic_ns":
        raise ValueError("deadline-owned admitted deadline schema differs")
    if type(admitted["deadline_crossed"]) is not bool:
        raise ValueError("deadline-owned deadline-crossed flag is malformed")
    numeric = (
        record["maximum_finalization_seconds"],
        record["conservative_publication_verification_elapsed_upper_seconds"],
        admitted["maximum_seconds"],
        admitted["elapsed_seconds"],
        admitted["remaining_seconds"],
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in numeric
    ):
        raise ValueError("deadline-owned admission numbers are malformed")
    maximum_finalization = float(numeric[0])
    conservative_upper = float(numeric[1])
    maximum = float(numeric[2])
    elapsed = float(numeric[3])
    remaining = float(numeric[4])
    if maximum_finalization <= 0.0 or maximum <= 0.0:
        raise ValueError("deadline-owned admission maxima must be positive")
    if admitted["deadline_crossed"] or elapsed < 0.0 or remaining < 0.0:
        raise ValueError("deadline-owned result was not admitted before the wall")
    if remaining < maximum_finalization:
        raise ValueError("deadline-owned result lacked its complete admitted bound")
    if not math.isclose(
        remaining,
        maximum - elapsed,
        rel_tol=0.0,
        abs_tol=1.1e-9,
    ):
        raise ValueError("deadline-owned admitted snapshot is internally inconsistent")
    if conservative_upper != math.fsum((elapsed, maximum_finalization)):
        raise ValueError("deadline-owned conservative elapsed bound is inconsistent")
    return DeadlineOwnedResultAdmission(
        unit_name=unit,
        maximum_finalization_seconds=maximum_finalization,
        admitted_deadline=CampaignDeadlineSnapshot(
            maximum_seconds=maximum,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
            deadline_crossed=admitted["deadline_crossed"],
        ),
        conservative_publication_verification_elapsed_upper_seconds=(
            conservative_upper
        ),
    )


def _validate_maximum_bytes(maximum_bytes: int) -> int:
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes <= 0
    ):
        raise ValueError("deadline-owned maximum bytes must be a positive integer")
    return maximum_bytes


def _require_non_reparse_output_parent(path: Path) -> None:
    candidate = path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    for ancestor in (candidate, *candidate.parents):
        attributes = getattr(ancestor.stat(), "st_file_attributes", 0)
        if ancestor.is_symlink() or attributes & 0x400:
            raise ValueError(
                "deadline-owned live publication requires a local non-reparse path"
            )


def _check_snapshot_after_postcheck(
    deadline: MonotonicCampaignDeadline,
    *,
    unit_name: str,
    maximum_unit_seconds: float,
) -> CampaignDeadlineSnapshot:
    snapshot = deadline.snapshot()
    if snapshot.deadline_crossed:
        raise CampaignDeadlineStop(
            reason="deadline_crossed",
            unit_name=unit_name,
            maximum_unit_seconds=maximum_unit_seconds,
            snapshot=snapshot,
        )
    return snapshot


def finalize_deadline_owned_atomic_result(
    *,
    deadline: MonotonicCampaignDeadline,
    unit_name: str,
    maximum_finalization_seconds: float,
    maximum_seal_seconds: float,
    checkpoint: Callable[[], object],
    output_path: Path,
    build_result: Callable[[DeadlineOwnedResultAdmission], Mapping[str, Any]],
    maximum_result_bytes: int = DEFAULT_MAXIMUM_RESULT_BYTES,
) -> DeadlineOwnedAtomicResult:
    """Publish canonical bytes; make them trusted only by a postcheck seal.

    The data phase builds the helper-owned envelope, writes and verifies a
    no-clobber canonical data file, removes its writable staging link, and then
    passes the deadline postcheck.  A separately admitted seal phase rewrites
    the exclusive publishing lock with hash/length authority, hard-links that
    inode to the seal path, and passes a second postcheck while the lock still
    makes the pair unconsumable.  Removing the lock is the final atomic
    publication event.  A crash or exception before that point leaves either
    no seal or a seal plus lock; the loader rejects both states.
    """

    if not isinstance(output_path, Path):
        raise TypeError("deadline-owned result output path must be a Path")
    if not callable(build_result):
        raise TypeError("deadline-owned result builder must be callable")
    maximum_bytes = _validate_maximum_bytes(maximum_result_bytes)
    _require_non_reparse_output_parent(output_path)
    staged_path = _staging_path(output_path)
    seal_path = _seal_path(output_path)
    lock_path = _lock_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for path in (output_path, staged_path, seal_path, lock_path):
        if _path_entry_exists(path):
            raise FileExistsError(f"deadline-owned path already exists: {path}")
    _write_exclusive(lock_path, b"deadline-owned publication in progress\n")
    _fsync_directory(output_path.parent)

    admission: DeadlineOwnedResultAdmission
    rendered: bytes
    persisted_sha256: str
    envelope: Mapping[str, Any]
    try:
        with deadline.bounded_unit(
            unit_name,
            maximum_finalization_seconds,
            checkpoint=checkpoint,
        ) as admitted_deadline:
            finalization_maximum = float(maximum_finalization_seconds)
            admission = DeadlineOwnedResultAdmission(
                unit_name=unit_name,
                maximum_finalization_seconds=finalization_maximum,
                admitted_deadline=admitted_deadline,
                conservative_publication_verification_elapsed_upper_seconds=(
                    math.fsum((admitted_deadline.elapsed_seconds, finalization_maximum))
                ),
            )
            built = build_result(admission)
            if not isinstance(built, Mapping):
                raise TypeError("deadline-owned result builder must return a mapping")
            envelope_record = {
                "schema": RESULT_ENVELOPE_SCHEMA,
                "deadline_admission": admission.as_record(),
                "payload": dict(built),
            }
            rendered = serialize_result(envelope_record).encode("utf-8")
            if len(rendered) > maximum_bytes:
                raise ValueError("deadline-owned result exceeds its byte cap")
            _write_exclusive(staged_path, rendered)
            staged = _read_result(staged_path, maximum_bytes)
            if staged != rendered:
                raise OSError("persisted deadline-owned staging bytes differ")
            os.link(staged_path, output_path)
            canonical = _read_result(output_path, maximum_bytes)
            if canonical != rendered:
                raise OSError("persisted deadline-owned canonical bytes differ")
            persisted_sha256 = _sha256_bytes(canonical)
            staged_path.unlink()
            _fsync_directory(output_path.parent)
            envelope = _decode_envelope(canonical, source=str(output_path))

        _check_snapshot_after_postcheck(
            deadline,
            unit_name=unit_name,
            maximum_unit_seconds=maximum_finalization_seconds,
        )
        seal_unit = f"{unit_name}/completion-seal"
        with deadline.bounded_unit(
            seal_unit,
            maximum_seal_seconds,
            checkpoint=lambda: None,
        ):
            canonical = _read_result(output_path, maximum_bytes)
            if (
                canonical != rendered
                or _sha256_bytes(canonical) != persisted_sha256
            ):
                raise OSError("deadline-owned canonical bytes changed before sealing")
            seal_record = {
                "schema": RESULT_SEAL_SCHEMA,
                "envelope_schema": RESULT_ENVELOPE_SCHEMA,
                "data_sha256": persisted_sha256,
                "data_bytes": len(canonical),
                "postcheck_completed": True,
            }
            seal_bytes = serialize_result(seal_record).encode("utf-8")
            _overwrite_lock(lock_path, seal_bytes)
            persisted_lock = _read_result(lock_path, 65_536)
            if persisted_lock != seal_bytes:
                raise OSError("deadline-owned seal staging bytes differ")
            os.link(lock_path, seal_path)
            persisted_seal = _read_result(seal_path, 65_536)
            if persisted_seal != seal_bytes:
                raise OSError("deadline-owned completion seal bytes differ")
            canonical = _read_result(output_path, maximum_bytes)
            if _sha256_bytes(canonical) != persisted_sha256:
                raise OSError("deadline-owned canonical bytes changed during sealing")
            _fsync_directory(output_path.parent)

        _check_snapshot_after_postcheck(
            deadline,
            unit_name=seal_unit,
            maximum_unit_seconds=maximum_seal_seconds,
        )
        frozen_payload = envelope["payload"]
        if not isinstance(frozen_payload, Mapping):
            raise TypeError("deadline-owned frozen payload is not a mapping")
        completed = DeadlineOwnedAtomicResult(
            result=frozen_payload,
            envelope=envelope,
            admission=admission,
            output_path=output_path,
            seal_path=seal_path,
            persisted_sha256=persisted_sha256,
            persisted_bytes=len(rendered),
            seal_sha256=_sha256_bytes(persisted_seal),
        )
        lock_path.unlink()
        try:
            final_canonical = _read_result(output_path, maximum_bytes)
            final_seal = _read_result(seal_path, 65_536)
            if (
                _sha256_bytes(final_canonical) != persisted_sha256
                or final_seal != persisted_seal
            ):
                raise OSError("deadline-owned publication changed during unlock")
            _check_snapshot_after_postcheck(
                deadline,
                unit_name=seal_unit,
                maximum_unit_seconds=maximum_seal_seconds,
            )
        except BaseException:
            if not _path_entry_exists(lock_path) and _path_entry_exists(seal_path):
                os.link(seal_path, lock_path)
            raise
        return completed
    except BaseException:  # noqa: TRY203 - preserve fail-closed state deliberately
        # Deliberately preserve an unsealed or lock-marked diagnostic.  Never
        # remove a possibly raced path after failure, and never expose it as a
        # successful result through the loader below.
        raise


def load_deadline_owned_atomic_result(
    output_path: Path,
    *,
    maximum_result_bytes: int = DEFAULT_MAXIMUM_RESULT_BYTES,
) -> DeadlineOwnedAtomicResult:
    """Load only the state ``data + seal + no publishing lock``."""

    maximum_bytes = _validate_maximum_bytes(maximum_result_bytes)
    seal_path = _seal_path(output_path)
    lock_path = _lock_path(output_path)
    if _path_entry_exists(lock_path):
        raise ValueError("deadline-owned result publication is incomplete")
    seal_raw = read_bounded_file_once(seal_path, maximum_bytes=65_536)
    seal = decode_strict_json_object(seal_raw, source=str(seal_path))
    if set(seal) != _SEAL_KEYS or seal.get("schema") != RESULT_SEAL_SCHEMA:
        raise ValueError("deadline-owned completion seal schema differs")
    if (
        seal.get("envelope_schema") != RESULT_ENVELOPE_SCHEMA
        or seal.get("postcheck_completed") is not True
        or not isinstance(seal.get("data_bytes"), int)
        or isinstance(seal.get("data_bytes"), bool)
        or seal["data_bytes"] <= 0
        or not isinstance(seal.get("data_sha256"), str)
        or len(seal["data_sha256"]) != 64
    ):
        raise ValueError("deadline-owned completion seal is malformed")
    canonical = read_bounded_file_once(output_path, maximum_bytes=maximum_bytes)
    digest = _sha256_bytes(canonical)
    if digest != seal["data_sha256"] or len(canonical) != seal["data_bytes"]:
        raise ValueError("deadline-owned canonical bytes differ from completion seal")
    envelope = _decode_envelope(canonical, source=str(output_path))
    payload = envelope["payload"]
    if not isinstance(payload, Mapping):
        raise TypeError("deadline-owned frozen payload is not a mapping")
    admission_record = envelope["deadline_admission"]
    if not isinstance(admission_record, Mapping):
        raise TypeError("deadline-owned admission record is malformed")
    admission = _admission_from_record(admission_record)
    if _path_entry_exists(lock_path):
        raise ValueError("deadline-owned result publication changed while loading")
    return DeadlineOwnedAtomicResult(
        result=payload,
        envelope=envelope,
        admission=admission,
        output_path=output_path,
        seal_path=seal_path,
        persisted_sha256=digest,
        persisted_bytes=len(canonical),
        seal_sha256=_sha256_bytes(seal_raw),
    )


__all__ = [
    "DEFAULT_MAXIMUM_RESULT_BYTES",
    "RESULT_ENVELOPE_SCHEMA",
    "RESULT_SEAL_SCHEMA",
    "DeadlineOwnedAtomicResult",
    "DeadlineOwnedResultAdmission",
    "finalize_deadline_owned_atomic_result",
    "load_deadline_owned_atomic_result",
]
