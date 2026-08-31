"""Canonical trace serialization and strict structural/digest parsing (ADR-0485).

JSON is UTF-8 without BOM, sorted keys, compact separators, finite numbers,
one LF per record. Parsing rejects duplicate, unknown, and missing keys, wrong
exact types, bad digests, invalid enums, and inconsistent cross-record
identities. Decoded arrays become immutable tuples and no executable object is
ever deserialized.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from functools import lru_cache
import json
import os
import math
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..legal_decision_spine_v2 import ActionSelectionReasonV2
from .model import (
    DecisionRecord,
    DeliveryStatus,
    EVENT_SCHEMA_VERSION,
    FailureCode,
    FailureRecord,
    HandAction,
    HandStartedEvent,
    OpponentActionEvent,
    SelectionReason,
    SettlementRecord,
    ShowdownResultEvent,
    StreetRevealedEvent,
    STREET_NAMES,
    TimingRecord,
    TimingStatus,
)

TRACE_SCHEMA_VERSION = "pontius-v0a-trace-v1"
TRACE_MODES: tuple[str, ...] = ("correctness", "rehearsal", "authorized")
CLOCK_KINDS: tuple[str, ...] = ("monotonic_ns", "deterministic_test")
RECORD_TYPES: tuple[str, ...] = ("header", "event", "decision", "failure", "terminal")

_HEADER_KEYS = frozenset(
    {
        "schema_version", "record_type", "run_id", "record_index",
        "mode", "source_commit", "source_manifest_sha256",
        "configuration_sha256", "blueprint_sha256", "clock_kind",
    }
)
_EVENT_KEYS = frozenset({"schema_version", "record_type", "run_id", "record_index", "event"})
_DECISION_KEYS = frozenset(
    {
        "schema_version", "record_type", "run_id", "record_index",
        "hand_id", "event_index", "action_index", "street_action_index", "seat", "street",
        "state_before_sha256", "state_after_sha256", "visible_cards_sha256",
        "blueprint_sha256", "selected_action", "selection_reason", "spine_reason",
        "timing", "preparation_use", "failure_reason",
    }
)
_FAILURE_KEYS = frozenset(
    {
        "schema_version", "record_type", "run_id", "record_index",
        "hand_id", "event_index", "action_index", "code",
        "delivery_status", "delivered_action", "timing",
    }
)
_TERMINAL_KEYS = frozenset(
    {
        "schema_version", "record_type", "run_id", "record_index",
        "hand_id", "complete", "passed", "failure_reason",
        "event_count", "decision_count", "interrupted_response_count",
        "accounting_complete", "settlement", "semantic_sha256",
        "trace_prefix_sha256", "preparation_compute_seconds", "post_terminal_compute_seconds",
    }
)
_TIMING_KEYS = frozenset(
    {
        "status", "interruption_reason", "wall_start_ns", "last_valid_observation_ns",
        "emission_observed_ns", "elapsed_ns", "response_compute_seconds",
        "response_uninstrumented_seconds", "work_cutoff_crossed", "deadline_crossed",
    }
)
_PREPARATION_KEYS = frozenset({"producer_status", "artifact_sha256s", "credited_seconds"})
_ACTION_KEYS = frozenset({"kind", "raise_to"})
_SETTLEMENT_KEYS = frozenset({"payouts", "final_stacks", "pots"})
_POT_KEYS = frozenset({"amount", "seats"})
_DECISION_PROJECTION_KEYS = (
    "hand_id", "event_index", "action_index", "street_action_index", "seat", "street",
    "state_before_sha256", "state_after_sha256", "visible_cards_sha256",
    "blueprint_sha256", "selected_action", "selection_reason", "spine_reason",
    "preparation_use",
)


class TraceInvalidError(ValueError):
    """A trace violated its frozen schema, ordering, or digest bindings."""


class TraceWriteError(OSError):
    """A trace destination refused creation; nothing partial is accepted."""


def canonical_json(payload: object) -> str:
    """Canonical form: sorted keys, compact separators, finite numbers only."""

    return json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)


def canonical_sha256(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


# -- serialization ---------------------------------------------------------


def event_payload(event: object) -> dict[str, object]:
    """Render one frozen event as its exact schema object."""

    if isinstance(event, HandStartedEvent):
        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "kind": "hand_started",
            "hand_id": event.hand_id,
            "event_index": event.event_index,
            "button": event.button,
            "controlled_seat": event.controlled_seat,
            "starting_stacks": list(event.starting_stacks),
            "small_blind": event.small_blind,
            "big_blind": event.big_blind,
            "private_cards": list(event.private_cards),
        }
    if isinstance(event, OpponentActionEvent):
        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "kind": "opponent_action",
            "hand_id": event.hand_id,
            "event_index": event.event_index,
            "street": event.street,
            "seat": event.seat,
            "action": action_payload(event.action),
        }
    if isinstance(event, StreetRevealedEvent):
        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "kind": "street_revealed",
            "hand_id": event.hand_id,
            "event_index": event.event_index,
            "street": event.street,
            "cards": list(event.cards),
        }
    if isinstance(event, ShowdownResultEvent):
        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "kind": "showdown_result",
            "hand_id": event.hand_id,
            "event_index": event.event_index,
            "strengths": [
                None if strength is None
                else (list(strength) if type(strength) is tuple else strength)
                for strength in event.strengths
            ],
        }
    raise TypeError("trace serialization requires an exact frozen event")


def action_payload(action: HandAction) -> dict[str, object]:
    if not isinstance(action, HandAction):
        raise TypeError("action payload requires an exact hand action")
    return {"kind": action.kind, "raise_to": action.raise_to}


def timing_payload(timing: TimingRecord | None) -> dict[str, object] | None:
    if timing is None:
        return None
    if not isinstance(timing, TimingRecord):
        raise TypeError("timing payload requires an exact timing record")
    return {
        "status": timing.status.value,
        "interruption_reason": (
            None if timing.interruption_reason is None else timing.interruption_reason.value
        ),
        "wall_start_ns": timing.wall_start_ns,
        "last_valid_observation_ns": timing.last_valid_observation_ns,
        "emission_observed_ns": timing.emission_observed_ns,
        "elapsed_ns": timing.elapsed_ns,
        "response_compute_seconds": timing.response_compute_seconds,
        "response_uninstrumented_seconds": timing.response_uninstrumented_seconds,
        "work_cutoff_crossed": timing.work_cutoff_crossed,
        "deadline_crossed": timing.deadline_crossed,
    }


def preparation_payload(preparation: object) -> dict[str, object]:
    return {
        "producer_status": preparation.producer_status,
        "artifact_sha256s": list(preparation.artifact_sha256s),
        "credited_seconds": preparation.credited_seconds,
    }


def settlement_payload(settlement: SettlementRecord | None) -> dict[str, object] | None:
    if settlement is None:
        return None
    if not isinstance(settlement, SettlementRecord):
        raise TypeError("settlement payload requires an exact settlement record")
    return {
        "payouts": list(settlement.payouts),
        "final_stacks": list(settlement.final_stacks),
        "pots": [{"amount": pot.amount, "seats": list(pot.seats)} for pot in settlement.pots],
    }


def decision_payload(record: DecisionRecord) -> dict[str, object]:
    if not isinstance(record, DecisionRecord):
        raise TypeError("decision payload requires an exact decision record")
    return {
        "hand_id": record.hand_id,
        "event_index": record.event_index,
        "action_index": record.action_index,
        "street_action_index": record.street_action_index,
        "seat": record.seat,
        "street": record.street,
        "state_before_sha256": record.state_before_sha256,
        "state_after_sha256": record.state_after_sha256,
        "visible_cards_sha256": record.visible_cards_sha256,
        "blueprint_sha256": record.blueprint_sha256,
        "selected_action": action_payload(record.selected_action),
        "selection_reason": record.selection_reason.value,
        "spine_reason": record.spine_reason,
        "timing": timing_payload(record.timing),
        "preparation_use": preparation_payload(record.preparation_use),
        "failure_reason": None if record.failure_reason is None else record.failure_reason.value,
    }


def failure_payload(record: FailureRecord) -> dict[str, object]:
    if not isinstance(record, FailureRecord):
        raise TypeError("failure payload requires an exact failure record")
    return {
        "hand_id": record.hand_id,
        "event_index": record.event_index,
        "action_index": record.action_index,
        "code": record.code.value,
        "delivery_status": record.delivery_status.value,
        "delivered_action": (
            None if record.delivered_action is None else action_payload(record.delivered_action)
        ),
        "timing": timing_payload(record.timing),
    }


def semantic_projection(
    *,
    events: tuple[object, ...],
    decisions: tuple[DecisionRecord, ...],
    settlement: SettlementRecord | None,
) -> dict[str, object]:
    """Run-independent semantics: events, decisions, settlement — no timing."""

    projected = []
    for record in decisions:
        payload = decision_payload(record)
        projected.append({key: payload[key] for key in _DECISION_PROJECTION_KEYS})
    return {
        "decisions": projected,
        "events": [event_payload(event) for event in events],
        "settlement": settlement_payload(settlement),
    }


def semantic_sha256(
    *,
    events: tuple[object, ...],
    decisions: tuple[DecisionRecord, ...],
    settlement: SettlementRecord | None,
) -> str:
    return canonical_sha256(
        semantic_projection(events=events, decisions=decisions, settlement=settlement)
    )


class TraceBuilder:
    """Accumulate exact LF-terminated rows; the terminal row closes the trace."""

    def __init__(
        self,
        *,
        run_id: str,
        mode: str,
        source_commit: str,
        source_manifest_sha256: str,
        configuration_sha256: str,
        blueprint_sha256: str,
        clock_kind: str,
    ) -> None:
        if mode not in TRACE_MODES:
            raise TraceInvalidError(f"trace mode must be one of {TRACE_MODES}")
        if mode == "authorized":
            raise TraceInvalidError(
                "authorized mode is refused until an independently verified "
                "authorization exists"
            )
        if clock_kind not in CLOCK_KINDS:
            raise TraceInvalidError(f"clock kind must be one of {CLOCK_KINDS}")
        self._rows: list[bytes] = []
        self._drained_rows = 0
        self._run_id = run_id
        self._closed = False
        self._append(
            {
                "record_type": "header",
                "mode": mode,
                "source_commit": source_commit,
                "source_manifest_sha256": source_manifest_sha256,
                "configuration_sha256": configuration_sha256,
                "blueprint_sha256": blueprint_sha256,
                "clock_kind": clock_kind,
            }
        )

    @property
    def rows(self) -> tuple[bytes, ...]:
        return tuple(self._rows)

    @property
    def content(self) -> bytes:
        return b"".join(self._rows)

    def _append(self, payload: dict[str, object]) -> None:
        if self._closed:
            raise TraceInvalidError("a closed trace accepts no further rows")
        row = dict(payload)
        row["schema_version"] = TRACE_SCHEMA_VERSION
        row["run_id"] = self._run_id
        row["record_index"] = len(self._rows)
        self._rows.append((canonical_json(row) + "\n").encode("utf-8"))

    def take_pending(self) -> bytes:
        """Drain newly serialized bytes; the writer separately establishes publication."""
        offset = self._drained_rows
        content = b"".join(self._rows[offset:])
        self._drained_rows = len(self._rows)
        return content

    def add_event(self, event: object) -> None:
        self._append({"record_type": "event", "event": event_payload(event)})

    def add_decision(self, record: DecisionRecord) -> None:
        self._append({"record_type": "decision", **decision_payload(record)})

    def add_failure(self, record: FailureRecord) -> None:
        self._append({"record_type": "failure", **failure_payload(record)})

    def prefix_sha256(self) -> str:
        return sha256(self.content).hexdigest()

    def close(
        self,
        *,
        hand_id: str | None,
        complete: bool,
        passed: bool,
        failure_reason: FailureCode | None,
        event_count: int,
        decision_count: int,
        interrupted_response_count: int,
        accounting_complete: bool,
        settlement: SettlementRecord | None,
        semantic_digest: str,
        preparation_compute_seconds: float | None,
        post_terminal_compute_seconds: float | None,
    ) -> bytes:
        prefix = self.prefix_sha256()
        self._append(
            {
                "record_type": "terminal",
                "hand_id": hand_id,
                "complete": complete,
                "passed": passed,
                "failure_reason": None if failure_reason is None else failure_reason.value,
                "event_count": event_count,
                "decision_count": decision_count,
                "interrupted_response_count": interrupted_response_count,
                "accounting_complete": accounting_complete,
                "settlement": settlement_payload(settlement),
                "semantic_sha256": semantic_digest,
                "trace_prefix_sha256": prefix,
                "preparation_compute_seconds": preparation_compute_seconds,
                "post_terminal_compute_seconds": post_terminal_compute_seconds,
            }
        )
        self._closed = True
        return self.content


# Windows native publication flags. Keep access, sharing, disposition and
# open options separate: each constrains a different part of the lifetime.
_SYNCHRONIZE = 0x00100000
_FILE_READ_ATTRIBUTES = 0x0080
_FILE_LIST_DIRECTORY = 0x0001
_FILE_TRAVERSE = 0x0020
_FILE_WRITE_DATA = 0x0002
_FILE_SHARE_READ = 0x0001
_FILE_OPEN = 0x0001
_FILE_CREATE = 0x0002
_FILE_DIRECTORY_FILE = 0x0001
_FILE_NON_DIRECTORY_FILE = 0x0040
_FILE_SYNCHRONOUS_IO_NONALERT = 0x0020
_FILE_WRITE_THROUGH = 0x0002
_OBJ_CASE_INSENSITIVE = 0x0040
_OBJ_DONT_REPARSE = 0x1000
_FILE_ATTRIBUTE_DIRECTORY = 0x0010
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_FILE_TYPE_DISK = 0x0001


class _UnicodeString(ctypes.Structure):
    _fields_ = (("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT),
                ("Buffer", wintypes.LPWSTR))


class _ObjectAttributes(ctypes.Structure):
    _fields_ = (("Length", wintypes.ULONG), ("RootDirectory", wintypes.HANDLE),
                ("ObjectName", ctypes.POINTER(_UnicodeString)), ("Attributes", wintypes.ULONG),
                ("SecurityDescriptor", wintypes.LPVOID),
                ("SecurityQualityOfService", wintypes.LPVOID))


class _IoStatus(ctypes.Structure):
    _fields_ = (("StatusOrPointer", ctypes.c_void_p), ("Information", ctypes.c_size_t))


class _FileInformation(ctypes.Structure):
    _fields_ = (("attributes", wintypes.DWORD), ("creation", wintypes.FILETIME),
                ("access", wintypes.FILETIME), ("write", wintypes.FILETIME),
                ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD))


@lru_cache(maxsize=1)
def _native_api():
    if os.name != "nt":
        raise TraceWriteError("stable trace publication requires the Windows backend")
    nt = ctypes.WinDLL("ntdll")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = nt.NtCreateFile
    create.argtypes = (ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
                       ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatus),
                       wintypes.LPVOID, wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
                       wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG)
    create.restype = wintypes.LONG
    info = kernel.GetFileInformationByHandle
    info.argtypes = (wintypes.HANDLE, ctypes.POINTER(_FileInformation))
    info.restype = wintypes.BOOL
    file_type = kernel.GetFileType
    file_type.argtypes = (wintypes.HANDLE,)
    file_type.restype = wintypes.DWORD
    write = kernel.WriteFile
    write.argtypes = (wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
                      ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID)
    write.restype = wintypes.BOOL
    flush = kernel.FlushFileBuffers
    flush.argtypes = (wintypes.HANDLE,)
    flush.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    return create, info, file_type, write, flush, close


class _NativeHandle:
    """Registered before acquisition; clearing ownership precedes the one close."""
    def __init__(self) -> None:
        self.value = wintypes.HANDLE()

    def close(self) -> None:
        value = self.value.value
        self.value.value = None
        if value not in (None, 0, ctypes.c_void_p(-1).value):
            if not _native_api()[5](wintypes.HANDLE(value)):
                raise TraceWriteError("native trace close failed", ctypes.get_last_error())


def _open_native(owner: TraceWriter, name: str, parent: _NativeHandle | None,
                 *, directory: bool) -> _NativeHandle:
    # The owner already retains this holder before NtCreateFile fills its slot.
    handle = _NativeHandle()
    owner._handles.append(handle)
    encoded = name.encode("utf-16-le")
    if len(encoded) > 0xFFFE:
        raise TraceWriteError("native path component exceeds UNICODE_STRING capacity")
    buffer = ctypes.create_unicode_buffer(name)
    string = _UnicodeString(len(encoded), len(encoded), ctypes.cast(buffer, wintypes.LPWSTR))
    attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes),
                                   None if parent is None else parent.value,
                                   ctypes.pointer(string),
                                   _OBJ_CASE_INSENSITIVE | _OBJ_DONT_REPARSE, None, None)
    status_block = _IoStatus()
    create, inspect, file_type, _, _, _ = _native_api()
    # READ sharing only denies foreign writes and deletion for the lifetime.
    access = _SYNCHRONIZE | _FILE_READ_ATTRIBUTES
    access |= (_FILE_LIST_DIRECTORY | _FILE_TRAVERSE) if directory else _FILE_WRITE_DATA
    options = _FILE_SYNCHRONOUS_IO_NONALERT
    options |= _FILE_DIRECTORY_FILE if directory else (_FILE_NON_DIRECTORY_FILE | _FILE_WRITE_THROUGH)
    status = create(ctypes.byref(handle.value), access, ctypes.byref(attributes),
                    ctypes.byref(status_block), None, 0, _FILE_SHARE_READ,
                    _FILE_OPEN if directory else _FILE_CREATE, options, None, 0)
    if status != 0:
        raise TraceWriteError("native trace open failed", status & 0xFFFFFFFF)
    if not handle.value.value or handle.value.value == ctypes.c_void_p(-1).value:
        raise TraceWriteError("native trace open returned no usable handle")
    info = _FileInformation()
    if (file_type(handle.value) != _FILE_TYPE_DISK
            or not inspect(handle.value, ctypes.byref(info))):
        raise TraceWriteError("native trace handle inspection failed", ctypes.get_last_error())
    if (info.attributes & _FILE_ATTRIBUTE_REPARSE_POINT
            or bool(info.attributes & _FILE_ATTRIBUTE_DIRECTORY) != directory):
        raise TraceWriteError("native trace handle has an unsafe file kind")
    return handle


class TraceWriter:
    """One create-new, directory-bound stream; failed writes are never retried."""
    def __init__(self, destination: Path | str, *, run_root: Path | str) -> None:
        self._destination = destination
        self._root = run_root
        self._handles: list[_NativeHandle] = []
        self._close_attempted = False
        self.close_errors: tuple[TraceWriteError, ...] = ()
        self._file: _NativeHandle | None = None
        self._state = "new"
        self._digest = sha256()

    def _open(self) -> None:
        if os.name != "nt":
            raise TraceWriteError("stable trace publication requires the Windows backend")
        root = Path(os.path.abspath(self._root))
        target = Path(self._destination)
        target = Path(os.path.abspath(target if target.is_absolute() else root / target))
        if (not root.drive or len(root.drive) != 2 or root.drive[1] != ":"
                or root.anchor != root.drive + "\\"):
            raise TraceWriteError("trace root must be a local drive path")
        try:
            relative = target.relative_to(root)
        except ValueError:
            raise TraceWriteError("trace destination escapes its run root") from None
        if not relative.parts:
            raise TraceWriteError("trace destination must name a file below its root")
        components = target.parts[1:]
        for name in components:
            if (name in (".", "..") or name.endswith((".", " "))
                    or any(character in name for character in (":", "\0"))):
                raise TraceWriteError("trace path contains an unsupported alias")
        parent = _open_native(self, "\\??\\" + root.anchor, None, directory=True)
        for name in components[:-1]:
            parent = _open_native(self, name, parent, directory=True)
        self._file = _open_native(self, components[-1], parent, directory=False)
        self._state = "open"

    def append(self, content: bytes) -> None:
        if self._state not in ("new", "open"):
            raise TraceWriteError("trace writer no longer permits append")
        try:
            if type(content) is not bytes:
                raise TypeError("trace content must be exact bytes")
            if self._state == "new":
                self._open()
            write = _native_api()[3]
            for offset in range(0, len(content), 0xFFFFFFFF):
                block = content[offset:offset + 0xFFFFFFFF]
                written = wintypes.DWORD()
                if not write(self._file.value, block, len(block), ctypes.byref(written), None):
                    raise TraceWriteError("native trace write failed", ctypes.get_last_error())
                if written.value != len(block):
                    raise TraceWriteError("native trace write was incomplete")
                self._digest.update(block)
        except BaseException:
            self._state = "failed"
            raise

    def close(self) -> None:
        if self._close_attempted:
            return
        self._close_attempted = True
        self._state = "close_attempted"
        errors = []
        for handle in reversed(self._handles):
            try:
                handle.close()
            except TraceWriteError as error:
                errors.append(error)
        self.close_errors = tuple(errors)
        if errors:
            raise errors[0]

    def finish(self) -> str:
        if self._state != "open":
            raise TraceWriteError("only a complete open trace may finish")
        try:
            if not _native_api()[4](self._file.value):
                raise TraceWriteError("native trace flush failed", ctypes.get_last_error())
            digest = self._digest.hexdigest()
            self.close()
        except BaseException:
            self._state = "failed"
            raise
        self._state = "finished"
        return digest


def write_trace(content: bytes, destination: Path, *, run_root: Path) -> str:
    """Convenience whole-buffer publication through the same stable stream."""
    writer = TraceWriter(destination, run_root=run_root)
    try:
        writer.append(content)
        return writer.finish()
    except BaseException as body:
        try:
            writer.close()
        except BaseException as cleanup:
            raise body from cleanup
        raise


# -- strict parsing --------------------------------------------------------


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise TraceInvalidError(f"duplicate JSON key {key!r}")
        seen[key] = value
    return seen


def _immutable(value: object) -> object:
    if type(value) is list:
        return tuple(_immutable(item) for item in value)
    if type(value) is dict:
        return {key: _immutable(item) for key, item in value.items()}
    return value


def _require_keys(row: dict[str, object], allowed: frozenset[str], *, label: str) -> None:
    keys = set(row)
    missing = allowed - keys
    unknown = keys - allowed
    if missing:
        raise TraceInvalidError(f"{label} row is missing keys: {sorted(missing)}")
    if unknown:
        raise TraceInvalidError(f"{label} row has unknown keys: {sorted(unknown)}")


def _require_int(value: object, *, label: str, minimum: int | None = None,
                 maximum: int | None = None) -> int:
    if type(value) is not int:
        raise TraceInvalidError(f"{label} must be an exact integer")
    if minimum is not None and value < minimum:
        raise TraceInvalidError(f"{label} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise TraceInvalidError(f"{label} must be at most {maximum}")
    return value


def _require_bool(value: object, *, label: str) -> bool:
    if type(value) is not bool:
        raise TraceInvalidError(f"{label} must be an exact boolean")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TraceInvalidError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_enum(value: object, allowed: tuple[str, ...], *, label: str) -> str:
    if type(value) is not str or value not in allowed:
        raise TraceInvalidError(f"{label} must be one of {allowed}")
    return value


def _require_text(value: object, *, label: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not str or not value or not value.isascii():
        raise TraceInvalidError(f"{label} must be a nonempty ASCII string")


def _require_seconds(value: object, *, label: str) -> float:
    if type(value) is not float or not math.isfinite(value) or value < 0.0:
        raise TraceInvalidError(f"{label} must be finite nonnegative float seconds")
    return value


def _seconds_ns_bounds(seconds: float, elapsed: int) -> tuple[int, int]:
    """Integers whose ns/1e9 conversion gives these exact ledger seconds.

    Binary searches also handle long failed responses beyond float's exact
    integer range. No invented tolerance or rounded float sum is accepted.
    """
    def converted(ns: int) -> float:
        try:
            return ns / 1_000_000_000
        except OverflowError:
            return math.inf

    bounds = []
    for strict in (False, True):
        low, high = 0, elapsed + 1
        while low < high:
            mid = (low + high) // 2
            value = converted(mid)
            if value > seconds or (not strict and value == seconds):
                high = mid
            else:
                low = mid + 1
        bounds.append(low)
    if bounds[0] > elapsed or converted(bounds[0]) != seconds:
        raise TraceInvalidError("response seconds are not an exact ledger ns conversion")
    return bounds[0], bounds[1] - 1


def _validate_timing(timing: object, *, label: str) -> None:
    if timing is None:
        return
    if type(timing) is not dict:
        raise TraceInvalidError(f"{label} timing must be an object or null")
    _require_keys(timing, _TIMING_KEYS, label=f"{label} timing")
    status = _require_enum(
        timing["status"], tuple(item.value for item in TimingStatus), label="timing status"
    )
    start = _require_int(timing["wall_start_ns"], label="wall start", minimum=0)
    last = _require_int(timing["last_valid_observation_ns"], label="last observation", minimum=0)
    if last < start:
        raise TraceInvalidError("last valid observation predates the wall start")
    observed = last - start
    if status == "completed":
        if timing["interruption_reason"] is not None:
            raise TraceInvalidError("completed timing carries no interruption reason")
        emission = _require_int(timing["emission_observed_ns"], label="emission", minimum=0)
        elapsed = _require_int(timing["elapsed_ns"], label="elapsed", minimum=0)
        if emission != last or elapsed != observed:
            raise TraceInvalidError("completed timing requires exact emission subtraction")
        intervals = [
            _seconds_ns_bounds(_require_seconds(timing[key], label=key), elapsed)
            for key in ("response_compute_seconds", "response_uninstrumented_seconds")
        ]
        if not sum(pair[0] for pair in intervals) <= elapsed <= sum(pair[1] for pair in intervals):
            raise TraceInvalidError("response compute and uninstrumented time must partition elapsed ns")
        for key in ("work_cutoff_crossed", "deadline_crossed"):
            _require_bool(timing[key], label=key)
        if timing["deadline_crossed"] != (elapsed > 15_000_000_000):
            raise TraceInvalidError("completed deadline flag disagrees with exact elapsed ns")
    else:
        _require_enum(timing["interruption_reason"], tuple(code.value for code in FailureCode),
                      label="interruption reason")
        for key in ("emission_observed_ns", "elapsed_ns", "response_compute_seconds",
                    "response_uninstrumented_seconds"):
            if timing[key] is not None:
                raise TraceInvalidError(f"interrupted timing must have null {key}")
        for key in ("work_cutoff_crossed", "deadline_crossed"):
            if timing[key] is not None and _require_bool(timing[key], label=key) is False:
                raise TraceInvalidError(f"interrupted {key} must be true or null")
    if timing["work_cutoff_crossed"] is True and observed < 14_000_000_000:
        raise TraceInvalidError("work cutoff lacks a compatible observed prefix")
    if timing["deadline_crossed"] is True and observed <= 15_000_000_000:
        raise TraceInvalidError("deadline crossing lacks a compatible observed prefix")


def _validate_action(action: object, *, label: str) -> None:
    if type(action) is not dict:
        raise TraceInvalidError(f"{label} must be an object")
    _require_keys(action, _ACTION_KEYS, label=label)
    kind = _require_enum(action["kind"], ("fold", "check", "call", "raise"), label=f"{label} kind")
    if kind == "raise":
        _require_int(action["raise_to"], label=f"{label} raise-to", minimum=1)
    elif action["raise_to"] is not None:
        raise TraceInvalidError(f"{label} carries a raise-to amount without a raise")


def _validate_preparation(preparation: object) -> None:
    if type(preparation) is not dict:
        raise TraceInvalidError("preparation use must be an object")
    _require_keys(preparation, _PREPARATION_KEYS, label="preparation use")
    if type(preparation["producer_status"]) is not str or preparation["producer_status"] != "producer_absent":
        raise TraceInvalidError("schema v1 preparation status is exactly producer_absent")
    if type(preparation["artifact_sha256s"]) is not tuple or preparation["artifact_sha256s"] != ():
        raise TraceInvalidError("schema v1 preparation artifacts are exactly empty")
    if type(preparation["credited_seconds"]) is not int or preparation["credited_seconds"] != 0:
        raise TraceInvalidError("schema v1 credited seconds are exactly zero")


def _validate_settlement(settlement: object) -> None:
    if settlement is None:
        return
    if type(settlement) is not dict:
        raise TraceInvalidError("settlement must be an object or null")
    _require_keys(settlement, _SETTLEMENT_KEYS, label="settlement")
    for key in ("payouts", "final_stacks"):
        values = settlement[key]
        if type(values) is not tuple or len(values) != 6:
            raise TraceInvalidError(f"settlement {key} must cover exactly six seats")
        for value in values:
            _require_int(value, label=f"settlement {key} entry", minimum=0)
    pots = settlement["pots"]
    if type(pots) is not tuple:
        raise TraceInvalidError("settlement pots must be an array")
    for pot in pots:
        if type(pot) is not dict:
            raise TraceInvalidError("each pot must be an object")
        _require_keys(pot, _POT_KEYS, label="pot")
        _require_int(pot["amount"], label="pot amount", minimum=1)
        seats = pot["seats"]
        if type(seats) is not tuple or not seats:
            raise TraceInvalidError("pot seats must be a nonempty array")
        for seat in seats:
            _require_int(seat, label="pot seat", minimum=0, maximum=5)
        if tuple(sorted(set(seats))) != seats:
            raise TraceInvalidError("pot seats must be sorted and unique")


_EVENT_COMMON = frozenset({"schema_version", "kind", "hand_id", "event_index"})
_EVENT_VARIANTS = {
    "hand_started": (HandStartedEvent, frozenset({
        "button", "controlled_seat", "starting_stacks", "small_blind", "big_blind",
        "private_cards",
    })),
    "opponent_action": (OpponentActionEvent, frozenset({"street", "seat", "action"})),
    "street_revealed": (StreetRevealedEvent, frozenset({"street", "cards"})),
    "showdown_result": (ShowdownResultEvent, frozenset({"strengths"})),
}


def _validate_event(event: object, index: int) -> None:
    if type(event) is not dict:
        raise TraceInvalidError("event payload must be an object")
    kind = _require_enum(event.get("kind"), tuple(_EVENT_VARIANTS), label="event kind")
    constructor, fields = _EVENT_VARIANTS[kind]
    _require_keys(event, _EVENT_COMMON | fields, label=kind)
    values = {key: value for key, value in event.items() if key != "kind"}
    try:
        if kind == "opponent_action":
            action = values["action"]
            if type(action) is not dict:
                raise TraceInvalidError("opponent action must be an object")
            _require_keys(action, _ACTION_KEYS, label="opponent action")
            values["action"] = HandAction(**action)
        # Only these known pure constructors admit event values. Raw keys remain
        # exact, while primitive types, private ordering and reveal widths have
        # one source of truth shared with runtime ingress.
        admitted = constructor(**values)
    except (TypeError, ValueError) as error:
        raise TraceInvalidError(f"invalid {kind} event value") from error
    if admitted.event_index != index:
        raise TraceInvalidError("accepted event indices must be contiguous from zero")
    if (index == 0) != (kind == "hand_started"):
        raise TraceInvalidError("the first accepted event alone starts the hand")
    if kind == "hand_started":
        if any(stack < admitted.big_blind for stack in admitted.starting_stacks):
            raise TraceInvalidError("starting stacks must cover the big blind")
    elif kind == "showdown_result":
        domains = {type(strength) for strength in admitted.strengths if strength is not None}
        if len(domains) > 1:
            raise TraceInvalidError("showdown strengths must share one comparable rank domain")


def _validate_terminal_consistency(
    terminal: dict[str, object],
    decisions: list[dict[str, object]],
    failures: list[dict[str, object]],
) -> None:
    """Apply outcome implications after exact values, counts and pairs are admitted."""

    if (terminal["interrupted_response_count"]
            or any(row["delivery_status"] == "unknown" for row in failures)):
        if any(terminal[key] for key in ("complete", "passed", "accounting_complete")):
            raise TraceInvalidError("interrupted or unknown delivery requires incomplete failure")
    if (not terminal["passed"] or not terminal["complete"]) and terminal["settlement"] is not None:
        raise TraceInvalidError("failed or incomplete terminal cannot carry settlement")
    if not terminal["passed"] and terminal["failure_reason"] is None:
        raise TraceInvalidError("failed terminal must retain its primary failure reason")
    if terminal["accounting_complete"] and any(terminal[key] is None for key in (
        "preparation_compute_seconds", "post_terminal_compute_seconds",
    )):
        raise TraceInvalidError("complete accounting requires both complete category totals")
    if failures and terminal["failure_reason"] != failures[0]["code"]:
        first = failures[0]
        timing = first["timing"]
        # A caught source fault can precede the adapter's recorded refusal. The
        # trace has no source/body chronology, so require compatibility rather
        # than inventing first-row equality. A prefailed reversed witness may
        # also refuse as clock_invalid before any runtime wall starts.
        earlier_clock = terminal["failure_reason"] in ("clock_invalid", "clock_reversed")
        interrupted_adapter = timing is not None and timing["status"] == "interrupted"
        prefailed_reversal = (terminal["failure_reason"] == "clock_reversed"
                              and first["code"] == "clock_invalid" and timing is None)
        if not (earlier_clock and interrupted_adapter or prefailed_reversal):
            raise TraceInvalidError("terminal primary reason contradicts its first failure")
    if terminal["passed"]:
        if (not terminal["complete"] or not terminal["accounting_complete"]
                or terminal["failure_reason"] is not None or failures
                or terminal["settlement"] is None
                or any(row["failure_reason"] is not None for row in decisions)):
            raise TraceInvalidError("successful terminal contradicts its records or accounting")
        if any(row["timing"]["work_cutoff_crossed"] or row["timing"]["deadline_crossed"]
               for row in decisions):
            raise TraceInvalidError("successful terminal contains an untimely response")


@dataclass(frozen=True, slots=True)
class ParsedTrace:
    header: dict[str, object]
    events: tuple[dict[str, object], ...]
    decisions: tuple[dict[str, object], ...]
    failures: tuple[dict[str, object], ...]
    terminal: dict[str, object]
    run_id: str
    records: tuple[dict[str, object], ...]


def parse_trace(content: bytes) -> ParsedTrace:
    """Validate canonical structure and digests, not successful legal replay.

    Use replay.verify_successful_trace with independently expected bindings
    before accepting a successful hand. Failed prefixes remain inspectable.
    """

    if type(content) is not bytes:
        raise TraceInvalidError("a trace is parsed from exact bytes")
    if content.startswith(b"\xef\xbb\xbf"):
        raise TraceInvalidError("a trace never carries a byte-order mark")
    if not content.endswith(b"\n"):
        raise TraceInvalidError("every trace row is LF terminated")
    if b"\r" in content:
        raise TraceInvalidError("a trace is LF-only")
    raw_rows = content.split(b"\n")[:-1]
    if not raw_rows:
        raise TraceInvalidError("a trace has at least a header and a terminal")

    rows: list[dict[str, object]] = []
    for position, raw in enumerate(raw_rows):
        try:
            decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
            if canonical_json(decoded).encode("utf-8") != raw:
                raise TraceInvalidError(f"row {position} is not canonical JSON")
        except UnicodeDecodeError as error:
            raise TraceInvalidError(f"row {position} is not UTF-8") from error
        except (ValueError, OverflowError, RecursionError) as error:
            raise TraceInvalidError(f"row {position} is not finite canonical JSON") from error
        if type(decoded) is not dict:
            raise TraceInvalidError(f"row {position} must be a JSON object")
        try:
            rows.append(_immutable(decoded))
        except RecursionError as error:
            raise TraceInvalidError("trace nesting exceeds the decoder boundary") from error

    header = rows[0]
    if header.get("record_type") != "header":
        raise TraceInvalidError("the first row must be the header")
    _require_keys(header, _HEADER_KEYS, label="header")
    _require_enum(header["mode"], TRACE_MODES, label="mode")
    if header["mode"] == "authorized":
        raise TraceInvalidError("authorized mode requires an independently verified authorization")
    _require_enum(header["clock_kind"], CLOCK_KINDS, label="clock kind")
    for key in ("source_manifest_sha256", "configuration_sha256", "blueprint_sha256"):
        _require_digest(header[key], label=key)
    commit = header["source_commit"]
    if type(commit) is not str or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise TraceInvalidError("source commit must be a lowercase 40-character Git SHA")
    run_id = header["run_id"]
    if type(run_id) is not str or not run_id or not run_id.isascii():
        raise TraceInvalidError("run id must be a nonempty ASCII string")

    events: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    terminal: dict[str, object] | None = None
    hand_ids: set[str] = set()

    for position, row in enumerate(rows):
        if row.get("schema_version") != TRACE_SCHEMA_VERSION:
            raise TraceInvalidError(f"row {position} has a foreign schema version")
        if row.get("run_id") != run_id:
            raise TraceInvalidError(f"row {position} belongs to another run")
        if _require_int(row.get("record_index"), label="record index", minimum=0) != position:
            raise TraceInvalidError(f"row {position} has a discontinuous record index")
        record_type = row.get("record_type")
        if type(record_type) is not str or record_type not in RECORD_TYPES:
            raise TraceInvalidError(f"row {position} has an unknown record type")
        if terminal is not None:
            raise TraceInvalidError("the terminal row must be last and unique")
        if position and record_type == "header":
            raise TraceInvalidError("a trace has exactly one header, first")

        if record_type == "event":
            _require_keys(row, _EVENT_KEYS, label="event")
            event = row["event"]
            _validate_event(event, len(events))
            hand_ids.add(event["hand_id"])
            events.append(event)
        elif record_type == "decision":
            _require_keys(row, _DECISION_KEYS, label="decision")
            _require_int(row["action_index"], label="action index", minimum=1)
            _require_int(row["street_action_index"], label="street action index", minimum=1)
            _require_int(row["event_index"], label="event index", minimum=0)
            _require_int(row["seat"], label="seat", minimum=0, maximum=5)
            _require_enum(row["street"], STREET_NAMES, label="street")
            for key in (
                "state_before_sha256",
                "state_after_sha256",
                "visible_cards_sha256",
                "blueprint_sha256",
            ):
                _require_digest(row[key], label=key)
            _validate_action(row["selected_action"], label="selected action")
            _require_enum(
                row["selection_reason"],
                tuple(reason.value for reason in SelectionReason),
                label="selection reason",
            )
            _require_text(row["hand_id"], label="decision hand id")
            _require_enum(row["spine_reason"], tuple(reason.value for reason in ActionSelectionReasonV2),
                          label="spine reason")
            if row["timing"] is None:
                raise TraceInvalidError("every decision has response timing")
            _validate_timing(row["timing"], label="decision")
            _validate_preparation(row["preparation_use"])
            if row["failure_reason"] is not None:
                _require_enum(
                    row["failure_reason"],
                    tuple(code.value for code in FailureCode),
                    label="failure reason",
                )
            hand_ids.add(row["hand_id"])
            decisions.append(row)
        elif record_type == "failure":
            _require_keys(row, _FAILURE_KEYS, label="failure")
            _require_text(row["hand_id"], label="failure hand id", nullable=True)
            for key, minimum in (("event_index", 0), ("action_index", 1)):
                if row[key] is not None:
                    _require_int(row[key], label=key, minimum=minimum)
            _require_enum(row["code"], tuple(code.value for code in FailureCode), label="code")
            _require_enum(
                row["delivery_status"],
                tuple(status.value for status in DeliveryStatus),
                label="delivery status",
            )
            if row["delivered_action"] is not None:
                _validate_action(row["delivered_action"], label="delivered action")
                if row["delivery_status"] != "accepted":
                    raise TraceInvalidError("a delivered action requires known acceptance")
            if (row["delivery_status"] == "accepted") != (row["delivered_action"] is not None):
                raise TraceInvalidError("known acceptance carries exactly one delivered action")
            _validate_timing(row["timing"], label="failure")
            if type(row["hand_id"]) is str:
                hand_ids.add(row["hand_id"])
            failures.append(row)
        elif record_type == "terminal":
            _require_keys(row, _TERMINAL_KEYS, label="terminal")
            _require_text(row["hand_id"], label="terminal hand id", nullable=True)
            for key in ("complete", "passed", "accounting_complete"):
                _require_bool(row[key], label=key)
            for key in ("event_count", "decision_count", "interrupted_response_count"):
                _require_int(row[key], label=key, minimum=0)
            _require_digest(row["semantic_sha256"], label="semantic digest")
            _require_digest(row["trace_prefix_sha256"], label="trace prefix digest")
            if row["failure_reason"] is not None:
                _require_enum(
                    row["failure_reason"],
                    tuple(code.value for code in FailureCode),
                    label="terminal failure reason",
                )
            _validate_settlement(row["settlement"])
            for key in ("preparation_compute_seconds", "post_terminal_compute_seconds"):
                value = row[key]
                if value is not None:
                    _require_seconds(value, label=key)
            if type(row["hand_id"]) is str:
                hand_ids.add(row["hand_id"])
            terminal = row

    if terminal is None:
        raise TraceInvalidError("a trace ends with exactly one terminal row")
    if len(hand_ids) > 1:
        raise TraceInvalidError(f"a trace binds one hand identity, found {sorted(hand_ids)}")
    if terminal["event_count"] != len(events):
        raise TraceInvalidError("terminal event count disagrees with the recorded events")
    if terminal["decision_count"] != len(decisions):
        raise TraceInvalidError("terminal accepted delivery count disagrees with decision rows")
    if [row["action_index"] for row in decisions] != list(range(1, len(decisions) + 1)):
        raise TraceInvalidError("accepted action indices must be contiguous from one")
    interrupted = {
        (row["hand_id"], row["event_index"], row["action_index"])
        for row in (*decisions, *failures)
        if row["timing"] is not None and row["timing"]["status"] == "interrupted"
    }
    if terminal["interrupted_response_count"] != len(interrupted):
        raise TraceInvalidError("terminal interrupted count disagrees with unique response rows")
    previous_observation = None
    for decision in decisions:
        timing = decision["timing"]
        if previous_observation is not None and timing["wall_start_ns"] < previous_observation:
            raise TraceInvalidError("successive response intervals reverse the monotonic clock")
        previous_observation = timing["last_valid_observation_ns"]
        if timing["status"] == "interrupted":
            expected_failure = timing["interruption_reason"]
        else:
            expected_failure = (
                "action_deadline_exceeded" if timing["deadline_crossed"]
                else "work_cutoff_exceeded" if timing["work_cutoff_crossed"] else None
            )
        if decision["failure_reason"] != expected_failure:
            raise TraceInvalidError("decision failure reason contradicts its response timing")
        if decision["blueprint_sha256"] != header["blueprint_sha256"]:
            raise TraceInvalidError("decision policy digest differs from its trace header")
        if decision["failure_reason"] is not None:
            matching = [row for row in failures if row["delivery_status"] == "accepted"
                        and all(row[key] == decision[key]
                                for key in ("hand_id", "event_index", "action_index"))]
            if len(matching) != 1:
                raise TraceInvalidError("each failed accepted decision requires one failure pair")
    for failure in failures:
        if failure["delivery_status"] == "accepted":
            matching = [row for row in decisions if all(row[key] == failure[key]
                        for key in ("hand_id", "event_index", "action_index"))]
            if len(matching) != 1 or any((
                matching[0]["selected_action"] != failure["delivered_action"],
                matching[0]["timing"] != failure["timing"],
                matching[0]["failure_reason"] != failure["code"],
            )):
                raise TraceInvalidError("accepted failure must bind one matching decision")
    _validate_terminal_consistency(terminal, decisions, failures)

    prefix_bytes = b"".join(raw + b"\n" for raw in raw_rows[:-1])
    if terminal["trace_prefix_sha256"] != sha256(prefix_bytes).hexdigest():
        raise TraceInvalidError("terminal prefix digest does not bind the preceding rows")
    parsed = ParsedTrace(
        header=header,
        events=tuple(events),
        decisions=tuple(decisions),
        failures=tuple(failures),
        terminal=terminal,
        run_id=run_id,
        records=tuple(rows),
    )
    if parsed_semantic_sha256(parsed) != terminal["semantic_sha256"]:
        raise TraceInvalidError("terminal semantic digest does not bind its own projection")
    return parsed


def parsed_semantic_sha256(parsed: ParsedTrace) -> str:
    """Recompute the semantic digest from a parsed trace's own rows."""

    projected = []
    for row in parsed.decisions:
        projection = {}
        for key in _DECISION_PROJECTION_KEYS:
            value = row[key]
            if key == "selected_action":
                value = {"kind": value["kind"], "raise_to": value["raise_to"]}
            elif key == "preparation_use":
                value = {
                    "producer_status": value["producer_status"],
                    "artifact_sha256s": list(value["artifact_sha256s"]),
                    "credited_seconds": value["credited_seconds"],
                }
            projection[key] = value
        projected.append(projection)
    events = [
        {
            key: (list(value) if type(value) is tuple else value)
            for key, value in event.items()
        }
        for event in parsed.events
    ]
    for event in events:
        if event.get("kind") == "opponent_action":
            action = event["action"]
            event["action"] = {"kind": action["kind"], "raise_to": action["raise_to"]}
        if event.get("kind") == "showdown_result":
            event["strengths"] = [
                list(item) if type(item) is tuple else item for item in event["strengths"]
            ]
    settlement = parsed.terminal["settlement"]
    if settlement is not None:
        settlement = {
            "payouts": list(settlement["payouts"]),
            "final_stacks": list(settlement["final_stacks"]),
            "pots": [
                {"amount": pot["amount"], "seats": list(pot["seats"])}
                for pot in settlement["pots"]
            ],
        }
    return canonical_sha256(
        {"decisions": projected, "events": events, "settlement": settlement}
    )


__all__ = [
    "CLOCK_KINDS",
    "ParsedTrace",
    "TRACE_MODES",
    "TRACE_SCHEMA_VERSION",
    "TraceBuilder",
    "TraceInvalidError",
    "TraceWriteError",
    "TraceWriter",
    "canonical_json",
    "canonical_sha256",
    "parse_trace",
    "parsed_semantic_sha256",
    "semantic_projection",
    "semantic_sha256",
    "write_trace",
]
