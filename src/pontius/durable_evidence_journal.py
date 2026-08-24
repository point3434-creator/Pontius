"""Canonical append-and-fsync evidence journal for one-shot research.

Record digests hash a self-free semantic body.  The outer envelope adds that
digest, and successor bodies chain the SHA-256 of the preceding complete line.
Readers never repair input: they return the exact verified prefix and untouched
invalid or torn suffix.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import BinaryIO


_BODY_KEYS = frozenset(
    {
        "campaign_sha256",
        "kind",
        "payload",
        "payload_sha256",
        "previous_record_sha256",
        "protocol_sha256",
        "semantic_identity_sha256",
        "sequence",
        "version",
    }
)
_ENVELOPE_KEYS = frozenset({"body", "record_sha256"})
_BODY_VERSION = "durable-evidence-journal-body-v1"
_UINT64_LIMIT = 1 << 64
_WRITER_CREATION_TOKEN = object()

_DURABLE_EVIDENCE_JOURNAL_PROTOCOL_PAYLOAD = {
    "body_digest_preimage": "canonical-self-free-body-bytes",
    "body_version": _BODY_VERSION,
    "canonical_encoding": "ascii-json-sort-keys-compact-final-lf-v1",
    "chain_preimage": "preceding-complete-envelope-line-including-lf",
    "exclusive_create": True,
    "next_append_authority": "post-flush-post-fsync-receipt-only",
    "reader_mutation": "forbidden",
    "recovery_partition": "exact-valid-prefix-plus-untouched-suffix",
    "version": "durable-evidence-journal-protocol-v1",
}
DURABLE_EVIDENCE_JOURNAL_PROTOCOL = MappingProxyType(
    _DURABLE_EVIDENCE_JOURNAL_PROTOCOL_PAYLOAD
)
DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _DURABLE_EVIDENCE_JOURNAL_PROTOCOL_PAYLOAD,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
).hexdigest()


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_sequence(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0 or value >= _UINT64_LIMIT:
        raise ValueError(f"{label} must be in the uint64 range")
    return value


def _canonical_json_value(value: object, *, path: str = "$") -> object:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} has a non-string object key")
            if key in normalized:
                raise ValueError(f"{path} repeats object key {key!r}")
            normalized[key] = _canonical_json_value(item, path=f"{path}.{key}")
        return normalized
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray, memoryview),
    ):
        return [
            _canonical_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise TypeError(f"{path} contains a noncanonical JSON value {type(value).__name__}")


def canonical_journal_json_bytes(value: object) -> bytes:
    """Encode the deliberately small canonical JSON domain used by journals."""

    return json.dumps(
        _canonical_json_value(value),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"journal JSON repeats object key {key!r}")
        result[key] = value
    return result


def _reject_float(_: str) -> object:
    raise ValueError("journal JSON forbids floating-point numerals; use exact strings")


def _reject_constant(value: str) -> object:
    raise ValueError(f"journal JSON forbids non-finite constant {value}")


def _strict_json_object(raw: bytes, *, label: str) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError(f"{label} bytes must be immutable")
    try:
        decoded = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} is not canonical ASCII JSON") from error
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_object_without_duplicates,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError(f"{label} is not valid strict JSON") from error
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    if canonical_journal_json_bytes(value) != raw:
        raise ValueError(f"{label} is not in canonical JSON form")
    return value


class JournalRecordKind(StrEnum):
    HEADER = "header"
    OBSERVATION = "observation"
    TERMINAL = "terminal"


@dataclass(frozen=True, slots=True)
class JournalRecordBody:
    protocol_sha256: str
    campaign_sha256: str
    kind: JournalRecordKind
    sequence: int
    previous_record_sha256: str | None
    semantic_identity_sha256: str
    payload_canonical_json: bytes

    def __post_init__(self) -> None:
        _require_digest(self.protocol_sha256, label="journal protocol")
        _require_digest(self.campaign_sha256, label="journal campaign")
        if not isinstance(self.kind, JournalRecordKind):
            raise TypeError("journal record kind must be semantic")
        sequence = _require_sequence(self.sequence, label="journal sequence")
        if sequence == 0:
            if self.kind is not JournalRecordKind.HEADER:
                raise ValueError("journal sequence zero must be the header")
            if self.previous_record_sha256 is not None:
                raise ValueError("journal header cannot name a previous record")
        else:
            if self.kind is JournalRecordKind.HEADER:
                raise ValueError("journal header cannot appear after sequence zero")
            _require_digest(
                self.previous_record_sha256,
                label="journal previous record",
            )
        _require_digest(
            self.semantic_identity_sha256,
            label="journal semantic identity",
        )
        if not isinstance(self.payload_canonical_json, bytes):
            raise TypeError("journal payload bytes must be immutable")
        _strict_json_object(
            self.payload_canonical_json,
            label="journal record payload",
        )

    @property
    def payload(self) -> dict[str, object]:
        return _strict_json_object(
            self.payload_canonical_json,
            label="journal record payload",
        )

    @property
    def payload_sha256(self) -> str:
        return sha256(self.payload_canonical_json).hexdigest()

    @property
    def canonical_object(self) -> dict[str, object]:
        return {
            "campaign_sha256": self.campaign_sha256,
            "kind": self.kind.value,
            "payload": self.payload,
            "payload_sha256": self.payload_sha256,
            "previous_record_sha256": self.previous_record_sha256,
            "protocol_sha256": self.protocol_sha256,
            "semantic_identity_sha256": self.semantic_identity_sha256,
            "sequence": self.sequence,
            "version": _BODY_VERSION,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_journal_json_bytes(self.canonical_object)

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


def build_journal_record_body(
    *,
    protocol_sha256: str,
    campaign_sha256: str,
    kind: JournalRecordKind,
    sequence: int,
    previous_record_sha256: str | None,
    semantic_identity_sha256: str,
    payload: Mapping[str, object],
) -> JournalRecordBody:
    if not isinstance(payload, Mapping):
        raise TypeError("journal record payload must be a mapping")
    return JournalRecordBody(
        protocol_sha256=protocol_sha256,
        campaign_sha256=campaign_sha256,
        kind=kind,
        sequence=sequence,
        previous_record_sha256=previous_record_sha256,
        semantic_identity_sha256=semantic_identity_sha256,
        payload_canonical_json=canonical_journal_json_bytes(payload),
    )


@dataclass(frozen=True, slots=True)
class JournalRecordEnvelope:
    body: JournalRecordBody
    record_sha256: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.body, JournalRecordBody):
            raise TypeError("journal envelope requires a semantic body")
        if self.record_sha256 == "":
            object.__setattr__(self, "record_sha256", self.body.digest)
        elif self.record_sha256 != self.body.digest:
            raise ValueError("journal envelope digest differs from its self-free body")

    @property
    def canonical_object(self) -> dict[str, object]:
        return {
            "body": self.body.canonical_object,
            "record_sha256": self.record_sha256,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_journal_json_bytes(self.canonical_object)

    @property
    def line_bytes(self) -> bytes:
        return self.canonical_bytes + b"\n"

    @property
    def line_sha256(self) -> str:
        return sha256(self.line_bytes).hexdigest()


def _require_exact_keys(
    value: dict[str, object],
    expected: frozenset[str],
    *,
    label: str,
) -> None:
    if frozenset(value) != expected:
        raise ValueError(f"{label} has missing or extra fields")


def parse_journal_record_line(line: bytes) -> JournalRecordEnvelope:
    """Parse and canonically rebind one complete LF-terminated line."""

    if not isinstance(line, bytes):
        raise TypeError("journal line must be immutable bytes")
    if not line.endswith(b"\n") or line.endswith(b"\r\n"):
        raise ValueError("journal record must end in exactly one LF")
    raw = line[:-1]
    root = _strict_json_object(raw, label="journal envelope")
    _require_exact_keys(root, _ENVELOPE_KEYS, label="journal envelope")
    body_value = root["body"]
    if not isinstance(body_value, dict):
        raise TypeError("journal envelope body must be an object")
    _require_exact_keys(body_value, _BODY_KEYS, label="journal body")
    if body_value["version"] != _BODY_VERSION:
        raise ValueError("journal body version drifted")
    payload = body_value["payload"]
    if not isinstance(payload, dict):
        raise TypeError("journal body payload must be an object")
    try:
        kind = JournalRecordKind(body_value["kind"])
    except (TypeError, ValueError) as error:
        raise ValueError("journal body has an unknown record kind") from error
    body = build_journal_record_body(
        protocol_sha256=body_value["protocol_sha256"],
        campaign_sha256=body_value["campaign_sha256"],
        kind=kind,
        sequence=body_value["sequence"],
        previous_record_sha256=body_value["previous_record_sha256"],
        semantic_identity_sha256=body_value["semantic_identity_sha256"],
        payload=payload,
    )
    if body_value["payload_sha256"] != body.payload_sha256:
        raise ValueError("journal payload digest drifted")
    envelope = JournalRecordEnvelope(
        body=body,
        record_sha256=root["record_sha256"],
    )
    if envelope.line_bytes != line:
        raise ValueError("journal record line differs from canonical bytes")
    return envelope


@dataclass(frozen=True, slots=True)
class JournalAppendReceipt:
    sequence: int
    kind: JournalRecordKind
    record_sha256: str
    line_sha256: str
    line_byte_count: int

    def __post_init__(self) -> None:
        _require_sequence(self.sequence, label="journal receipt sequence")
        if not isinstance(self.kind, JournalRecordKind):
            raise TypeError("journal receipt kind must be semantic")
        _require_digest(self.record_sha256, label="journal receipt record")
        _require_digest(self.line_sha256, label="journal receipt line")
        if (
            isinstance(self.line_byte_count, bool)
            or not isinstance(self.line_byte_count, int)
            or self.line_byte_count <= 1
        ):
            raise ValueError("journal receipt byte count must be positive")


class DurableEvidenceJournalWriter:
    """Exclusive writer that returns only post-fsync append receipts."""

    __slots__ = (
        "_campaign_sha256",
        "_closed",
        "_failed",
        "_next_sequence",
        "_path",
        "_previous_line_sha256",
        "_protocol_sha256",
        "_stream",
        "_terminal_written",
    )

    def __init__(
        self,
        *,
        path: Path,
        protocol_sha256: str,
        campaign_sha256: str,
        stream: BinaryIO,
        _creation_token: object,
    ) -> None:
        if _creation_token is not _WRITER_CREATION_TOKEN:
            raise RuntimeError("journal writers must use exclusive create")
        if not isinstance(path, Path):
            raise TypeError("journal path must be a Path")
        _require_digest(protocol_sha256, label="journal writer protocol")
        _require_digest(campaign_sha256, label="journal writer campaign")
        self._path = path
        self._protocol_sha256 = protocol_sha256
        self._campaign_sha256 = campaign_sha256
        self._stream = stream
        self._next_sequence = 0
        self._previous_line_sha256: str | None = None
        self._terminal_written = False
        self._failed = False
        self._closed = False

    @classmethod
    def create(
        cls,
        *,
        path: Path,
        protocol_sha256: str,
        campaign_sha256: str,
    ) -> DurableEvidenceJournalWriter:
        if not isinstance(path, Path):
            raise TypeError("journal path must be a Path")
        _require_digest(protocol_sha256, label="journal writer protocol")
        _require_digest(campaign_sha256, label="journal writer campaign")
        if not path.parent.is_dir():
            raise FileNotFoundError("journal parent directory does not exist")
        stream = path.open("xb")
        return cls(
            path=path,
            protocol_sha256=protocol_sha256,
            campaign_sha256=campaign_sha256,
            stream=stream,
            _creation_token=_WRITER_CREATION_TOKEN,
        )

    @property
    def path(self) -> Path:
        return self._path

    @property
    def next_sequence(self) -> int:
        return self._next_sequence

    @property
    def failed(self) -> bool:
        return self._failed

    def append(
        self,
        *,
        kind: JournalRecordKind,
        semantic_identity_sha256: str,
        payload: Mapping[str, object],
    ) -> JournalAppendReceipt:
        if self._closed:
            raise RuntimeError("journal writer is closed")
        if self._failed:
            raise RuntimeError("journal writer is poisoned by a failed append")
        if self._terminal_written:
            raise RuntimeError("journal terminal record is already durable")
        if not isinstance(kind, JournalRecordKind):
            raise TypeError("journal append kind must be semantic")
        if self._next_sequence == 0 and kind is not JournalRecordKind.HEADER:
            raise ValueError("journal first append must be the header")
        if self._next_sequence > 0 and kind is JournalRecordKind.HEADER:
            raise ValueError("journal cannot append a second header")
        body = build_journal_record_body(
            protocol_sha256=self._protocol_sha256,
            campaign_sha256=self._campaign_sha256,
            kind=kind,
            sequence=self._next_sequence,
            previous_record_sha256=self._previous_line_sha256,
            semantic_identity_sha256=semantic_identity_sha256,
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        line = envelope.line_bytes
        try:
            written = self._stream.write(line)
            if written != len(line):
                raise OSError("journal append was short")
            self._stream.flush()
            os.fsync(self._stream.fileno())
        except BaseException:
            self._failed = True
            raise
        self._next_sequence += 1
        self._previous_line_sha256 = envelope.line_sha256
        if kind is JournalRecordKind.TERMINAL:
            self._terminal_written = True
        return JournalAppendReceipt(
            sequence=body.sequence,
            kind=kind,
            record_sha256=envelope.record_sha256,
            line_sha256=envelope.line_sha256,
            line_byte_count=len(line),
        )

    def close(self) -> None:
        if not self._closed:
            self._stream.close()
            self._closed = True

    def __enter__(self) -> DurableEvidenceJournalWriter:
        if self._closed:
            raise RuntimeError("journal writer is already closed")
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class JournalRecoveryFailure:
    record_index: int
    byte_offset: int
    reason: str

    def __post_init__(self) -> None:
        _require_sequence(self.record_index, label="journal failure record index")
        _require_sequence(self.byte_offset, label="journal failure byte offset")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("journal recovery failure reason must be nonempty")


@dataclass(frozen=True, slots=True)
class JournalRecovery:
    records: tuple[JournalRecordEnvelope, ...]
    verified_prefix_bytes: bytes
    invalid_suffix_bytes: bytes
    failure: JournalRecoveryFailure | None

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple) or any(
            not isinstance(record, JournalRecordEnvelope) for record in self.records
        ):
            raise TypeError("journal recovery records must be semantic")
        if not isinstance(self.verified_prefix_bytes, bytes) or not isinstance(
            self.invalid_suffix_bytes,
            bytes,
        ):
            raise TypeError("journal recovery byte partitions must be immutable")
        if self.verified_prefix_bytes != b"".join(
            record.line_bytes for record in self.records
        ):
            raise ValueError("journal recovery prefix differs from its records")
        if self.failure is not None and not isinstance(
            self.failure,
            JournalRecoveryFailure,
        ):
            raise TypeError("journal recovery failure must be semantic")
        if self.failure is None and self.invalid_suffix_bytes:
            raise ValueError("journal recovery suffix lacks a failure")

    @property
    def is_complete(self) -> bool:
        return (
            bool(self.records)
            and self.records[-1].body.kind is JournalRecordKind.TERMINAL
            and not self.invalid_suffix_bytes
            and self.failure is None
        )

    @property
    def raw_bytes(self) -> bytes:
        return self.verified_prefix_bytes + self.invalid_suffix_bytes


def _failure(
    *,
    records: list[JournalRecordEnvelope],
    raw: bytes,
    offset: int,
    reason: str,
) -> JournalRecovery:
    return JournalRecovery(
        records=tuple(records),
        verified_prefix_bytes=raw[:offset],
        invalid_suffix_bytes=raw[offset:],
        failure=JournalRecoveryFailure(
            record_index=len(records),
            byte_offset=offset,
            reason=reason,
        ),
    )


def recover_journal_bytes(
    raw: bytes,
    *,
    expected_protocol_sha256: str | None = None,
    expected_campaign_sha256: str | None = None,
) -> JournalRecovery:
    """Return the exact valid prefix and untouched suffix without mutation."""

    if not isinstance(raw, bytes):
        raise TypeError("journal recovery requires immutable bytes")
    if expected_protocol_sha256 is not None:
        _require_digest(expected_protocol_sha256, label="expected journal protocol")
    if expected_campaign_sha256 is not None:
        _require_digest(expected_campaign_sha256, label="expected journal campaign")

    records: list[JournalRecordEnvelope] = []
    offset = 0
    previous_line_sha256: str | None = None
    observed_protocol = expected_protocol_sha256
    observed_campaign = expected_campaign_sha256
    terminal_seen = False
    while offset < len(raw):
        newline = raw.find(b"\n", offset)
        if newline < 0:
            return _failure(
                records=records,
                raw=raw,
                offset=offset,
                reason="torn non-LF journal tail",
            )
        line = raw[offset : newline + 1]
        if terminal_seen:
            return _failure(
                records=records,
                raw=raw,
                offset=offset,
                reason="record follows terminal",
            )
        try:
            envelope = parse_journal_record_line(line)
            body = envelope.body
            if body.sequence != len(records):
                raise ValueError("journal sequence is not contiguous")
            if body.previous_record_sha256 != previous_line_sha256:
                raise ValueError("journal previous-record chain drifted")
            if observed_protocol is None:
                observed_protocol = body.protocol_sha256
            if observed_campaign is None:
                observed_campaign = body.campaign_sha256
            if body.protocol_sha256 != observed_protocol:
                raise ValueError("journal protocol identity drifted")
            if body.campaign_sha256 != observed_campaign:
                raise ValueError("journal campaign identity drifted")
        except (TypeError, ValueError) as error:
            return _failure(
                records=records,
                raw=raw,
                offset=offset,
                reason=str(error),
            )
        records.append(envelope)
        previous_line_sha256 = envelope.line_sha256
        terminal_seen = body.kind is JournalRecordKind.TERMINAL
        offset = newline + 1

    return JournalRecovery(
        records=tuple(records),
        verified_prefix_bytes=raw,
        invalid_suffix_bytes=b"",
        failure=None,
    )


def recover_journal_file(
    path: Path,
    *,
    expected_protocol_sha256: str | None = None,
    expected_campaign_sha256: str | None = None,
) -> JournalRecovery:
    if not isinstance(path, Path):
        raise TypeError("journal recovery path must be a Path")
    return recover_journal_bytes(
        path.read_bytes(),
        expected_protocol_sha256=expected_protocol_sha256,
        expected_campaign_sha256=expected_campaign_sha256,
    )


__all__ = [
    "DURABLE_EVIDENCE_JOURNAL_PROTOCOL",
    "DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256",
    "DurableEvidenceJournalWriter",
    "JournalAppendReceipt",
    "JournalRecordBody",
    "JournalRecordEnvelope",
    "JournalRecordKind",
    "JournalRecovery",
    "JournalRecoveryFailure",
    "build_journal_record_body",
    "canonical_journal_json_bytes",
    "parse_journal_record_line",
    "recover_journal_bytes",
    "recover_journal_file",
]
