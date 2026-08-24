from __future__ import annotations

import os
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.durable_evidence_journal as journal
from pontius.durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL,
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    parse_journal_record_line,
    recover_journal_bytes,
    recover_journal_file,
)


_CAMPAIGN = sha256(b"durable-journal-test-campaign").hexdigest()


def _record(
    *,
    kind: JournalRecordKind,
    sequence: int,
    previous: str | None,
    payload: dict[str, object],
) -> JournalRecordEnvelope:
    semantic = sha256(
        canonical_journal_json_bytes(
            {"kind": kind.value, "payload": payload, "sequence": sequence}
        )
    ).hexdigest()
    return JournalRecordEnvelope(
        build_journal_record_body(
            protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
            campaign_sha256=_CAMPAIGN,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=semantic,
            payload=payload,
        )
    )


def _three_record_chain() -> tuple[JournalRecordEnvelope, ...]:
    header = _record(
        kind=JournalRecordKind.HEADER,
        sequence=0,
        previous=None,
        payload={"record": "header"},
    )
    observation = _record(
        kind=JournalRecordKind.OBSERVATION,
        sequence=1,
        previous=header.line_sha256,
        payload={"exact_value": "0x1.0000000000000p-1", "record": "observation"},
    )
    terminal = _record(
        kind=JournalRecordKind.TERMINAL,
        sequence=2,
        previous=observation.line_sha256,
        payload={"record": "terminal"},
    )
    return header, observation, terminal


class DurableEvidenceJournalTests(unittest.TestCase):
    def test_protocol_and_self_free_body_digest_are_exact(self) -> None:
        records = _three_record_chain()
        header = records[0]
        self.assertEqual(
            DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
            sha256(canonical_journal_json_bytes(dict(DURABLE_EVIDENCE_JOURNAL_PROTOCOL))).hexdigest(),
        )
        self.assertEqual(header.body.digest, header.record_sha256)
        self.assertNotIn(b'"record_sha256":', header.body.canonical_bytes)
        self.assertEqual(header, parse_journal_record_line(header.line_bytes))
        self.assertEqual(
            sha256(header.line_bytes).hexdigest(),
            records[1].body.previous_record_sha256,
        )
        with self.assertRaises(TypeError):
            DURABLE_EVIDENCE_JOURNAL_PROTOCOL["reader_mutation"] = "allowed"  # type: ignore[index]

    def test_strict_canonical_parser_rejects_ambiguous_encodings(self) -> None:
        line = _three_record_chain()[0].line_bytes
        digest = _three_record_chain()[0].record_sha256.encode("ascii")
        duplicate = line[:-2] + b',"record_sha256":"' + digest + b'"}\n'
        with self.assertRaisesRegex(ValueError, "valid strict JSON"):
            parse_journal_record_line(duplicate)
        with self.assertRaisesRegex(ValueError, "exactly one LF"):
            parse_journal_record_line(line[:-1] + b"\r\n")
        with self.assertRaisesRegex(ValueError, "canonical"):
            parse_journal_record_line(line.replace(b'{"body":', b'{ "body":', 1))
        with self.assertRaisesRegex(ValueError, "valid strict JSON"):
            parse_journal_record_line(line.replace(b'"record":"header"', b'"record":1.0'))
        with self.assertRaises(TypeError):
            canonical_journal_json_bytes({"bad": 0.5})
        with self.assertRaises(TypeError):
            canonical_journal_json_bytes({1: "bad"})

    def test_record_shape_and_digest_corruption_fail_closed(self) -> None:
        header = _three_record_chain()[0]
        extra_object = header.canonical_object
        extra_object["unexpected"] = 0
        extra = canonical_journal_json_bytes(extra_object) + b"\n"
        with self.assertRaisesRegex(ValueError, "missing or extra"):
            parse_journal_record_line(extra)
        corrupted = header.line_bytes.replace(b'"record":"header"', b'"record":"headeq"')
        with self.assertRaisesRegex(ValueError, "payload digest"):
            parse_journal_record_line(corrupted)
        with self.assertRaises(ValueError):
            _record(
                kind=JournalRecordKind.OBSERVATION,
                sequence=0,
                previous=None,
                payload={"bad": True},
            )

    def test_recovery_preserves_every_complete_prefix_and_every_torn_suffix(self) -> None:
        records = _three_record_chain()
        lines = tuple(record.line_bytes for record in records)
        full = b"".join(lines)
        offset = 0
        for count in range(len(records) + 1):
            prefix = b"".join(lines[:count])
            recovered = recover_journal_bytes(
                prefix,
                expected_protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                expected_campaign_sha256=_CAMPAIGN,
            )
            self.assertEqual(prefix, recovered.raw_bytes)
            self.assertEqual(prefix, recovered.verified_prefix_bytes)
            self.assertEqual(b"", recovered.invalid_suffix_bytes)
            self.assertIsNone(recovered.failure)
            self.assertEqual(count, len(recovered.records))
            self.assertEqual(count == len(records), recovered.is_complete)
            offset += len(lines[count - 1]) if count else 0

        prior = lines[0]
        for cut in (1, len(lines[1]) // 2, len(lines[1]) - 1):
            raw = prior + lines[1][:cut]
            recovered = recover_journal_bytes(raw)
            self.assertEqual(prior, recovered.verified_prefix_bytes)
            self.assertEqual(lines[1][:cut], recovered.invalid_suffix_bytes)
            self.assertEqual(raw, recovered.raw_bytes)
            self.assertIsNotNone(recovered.failure)

        after_terminal = full + lines[1]
        recovered = recover_journal_bytes(after_terminal)
        self.assertEqual(full, recovered.verified_prefix_bytes)
        self.assertEqual(lines[1], recovered.invalid_suffix_bytes)
        self.assertIn("follows terminal", recovered.failure.reason if recovered.failure else "")

    def test_recovery_rejects_chain_identity_and_same_count_corruption_at_first_line(self) -> None:
        header, observation, terminal = _three_record_chain()
        wrong_previous = _record(
            kind=JournalRecordKind.OBSERVATION,
            sequence=1,
            previous="0" * 64,
            payload=observation.body.payload,
        )
        raw = header.line_bytes + wrong_previous.line_bytes + terminal.line_bytes
        recovered = recover_journal_bytes(raw)
        self.assertEqual(header.line_bytes, recovered.verified_prefix_bytes)
        self.assertEqual(wrong_previous.line_bytes + terminal.line_bytes, recovered.invalid_suffix_bytes)
        self.assertIn("chain drifted", recovered.failure.reason if recovered.failure else "")

        wrong_campaign_body = build_journal_record_body(
            protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
            campaign_sha256="1" * 64,
            kind=JournalRecordKind.OBSERVATION,
            sequence=1,
            previous_record_sha256=header.line_sha256,
            semantic_identity_sha256=observation.body.semantic_identity_sha256,
            payload=observation.body.payload,
        )
        wrong_campaign = JournalRecordEnvelope(wrong_campaign_body)
        recovered = recover_journal_bytes(
            header.line_bytes + wrong_campaign.line_bytes,
            expected_campaign_sha256=_CAMPAIGN,
        )
        self.assertEqual(1, len(recovered.records))
        self.assertIn("campaign identity", recovered.failure.reason if recovered.failure else "")

        altered = bytearray(observation.line_bytes)
        position = observation.line_bytes.index(b"observation")
        altered[position] = ord("p")
        raw = header.line_bytes + bytes(altered) + terminal.line_bytes
        recovered = recover_journal_bytes(raw)
        self.assertEqual(header.line_bytes, recovered.verified_prefix_bytes)
        self.assertEqual(raw[len(header.line_bytes) :], recovered.invalid_suffix_bytes)

    def test_writer_orders_write_flush_fsync_before_receipt(self) -> None:
        events: list[str] = []

        class Stream:
            def write(self, raw: bytes) -> int:
                events.append("write")
                return len(raw)

            def flush(self) -> None:
                events.append("flush")

            def fileno(self) -> int:
                events.append("fileno")
                return 19

            def close(self) -> None:
                events.append("close")

        with patch.object(Path, "open", return_value=Stream()):
            writer = DurableEvidenceJournalWriter.create(
                path=Path("synthetic.jsonl"),
                protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                campaign_sha256=_CAMPAIGN,
            )

        def fsync(descriptor: int) -> None:
            self.assertEqual(19, descriptor)
            events.append("fsync")

        with patch.object(journal.os, "fsync", side_effect=fsync) as mocked:
            receipt = writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256="2" * 64,
                payload={"synthetic": True},
            )
        self.assertEqual(["write", "flush", "fileno", "fsync"], events)
        self.assertEqual(0, receipt.sequence)
        mocked.assert_called_once_with(19)

    def test_writer_poisoning_no_clobber_and_actual_file_recovery(self) -> None:
        class FailingStream:
            def write(self, raw: bytes) -> int:
                return len(raw) - 1

            def flush(self) -> None:
                raise AssertionError("short write must fail before flush")

            def fileno(self) -> int:
                return 1

            def close(self) -> None:
                return None

        with patch.object(Path, "open", return_value=FailingStream()):
            writer = DurableEvidenceJournalWriter.create(
                path=Path("failure.jsonl"),
                protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                campaign_sha256=_CAMPAIGN,
            )
        with self.assertRaisesRegex(OSError, "short"):
            writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256="3" * 64,
                payload={"synthetic": True},
            )
        self.assertTrue(writer.failed)
        with self.assertRaisesRegex(RuntimeError, "poisoned"):
            writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256="3" * 64,
                payload={"synthetic": True},
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            with DurableEvidenceJournalWriter.create(
                path=path,
                protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                campaign_sha256=_CAMPAIGN,
            ) as actual:
                receipt = actual.append(
                    kind=JournalRecordKind.HEADER,
                    semantic_identity_sha256="4" * 64,
                    payload={"synthetic": True},
                )
                self.assertEqual(os.path.getsize(path), receipt.line_byte_count)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                DurableEvidenceJournalWriter.create(
                    path=path,
                    protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                    campaign_sha256=_CAMPAIGN,
                )
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(before, recover_journal_file(path).raw_bytes)

            invalid_path = Path(directory) / "invalid.jsonl"
            with self.assertRaises(ValueError):
                DurableEvidenceJournalWriter.create(
                    path=invalid_path,
                    protocol_sha256="bad",
                    campaign_sha256=_CAMPAIGN,
                )
            self.assertFalse(invalid_path.exists())

    def test_terminal_is_final_and_header_is_unique(self) -> None:
        class Sink:
            def write(self, raw: bytes) -> int:
                return len(raw)

            def flush(self) -> None:
                return None

            def fileno(self) -> int:
                return 5

            def close(self) -> None:
                return None

        with patch.object(Path, "open", return_value=Sink()):
            writer = DurableEvidenceJournalWriter.create(
                path=Path("sink.jsonl"),
                protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                campaign_sha256=_CAMPAIGN,
            )
        with self.assertRaises(ValueError):
            writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256="5" * 64,
                payload={"bad": True},
            )
        with patch.object(journal.os, "fsync"):
            writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256="5" * 64,
                payload={"header": True},
            )
            with self.assertRaises(ValueError):
                writer.append(
                    kind=JournalRecordKind.HEADER,
                    semantic_identity_sha256="5" * 64,
                    payload={"bad": True},
                )
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256="6" * 64,
                payload={"terminal": True},
            )
            with self.assertRaises(RuntimeError):
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256="7" * 64,
                    payload={"bad": True},
                )


if __name__ == "__main__":
    unittest.main()
