from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius import legal_river_quotient_cuda_shared_direct_device_result as v1_reader
from pontius import legal_river_quotient_cuda_shared_direct_device_v2_result as reader
from tests import test_legal_river_quotient_cuda_shared_direct_device as v1_controls


_ROOT = Path(__file__).parents[1]
_V1_RESULT = _ROOT / reader.V1_RESULT_RELATIVE_PATH


def _semantic(payload: dict[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _journal(
    payloads: list[tuple[JournalRecordKind, dict[str, object]]]
) -> bytes:
    previous: str | None = None
    lines: list[bytes] = []
    for sequence, (kind, payload) in enumerate(payloads):
        body = build_journal_record_body(
            protocol_sha256=reader.PROTOCOL_SHA256,
            campaign_sha256=reader.CAMPAIGN_SHA256,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=_semantic(payload),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


def _v2_journal(parent_raw: bytes) -> bytes:
    recovery = recover_journal_bytes(
        parent_raw,
        expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
        expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    header = payloads[0]
    header.update(
        {
            "schema_version": "legal-river-shared-direct-owner-header-v2",
            "config_sha256": reader.CONFIG_SHA256,
            "preregistration_commit": reader.PREREGISTRATION_COMMIT,
            "dependency_hashes": {
                relative: "6" * 64
                for relative in reader.DEPENDENCY_RELATIVE_PATHS
            },
            "result_relative_path": reader.RESULT_RELATIVE_PATH,
        }
    )
    for payload in payloads[1:-1]:
        payload["config_sha256"] = reader.CONFIG_SHA256
        if payload.get("kind") == "bootstrap_handshake":
            event = payload["event"]
            event["literal_module"] = reader.LITERAL_WORKER_MODULE
            event["spec_name"] = reader.LITERAL_WORKER_MODULE
    return _journal(
        [
            (record.body.kind, payload)
            for record, payload in zip(
                recovery.records, payloads, strict=True
            )
        ]
    )


def _rewrite(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=reader.PROTOCOL_SHA256,
        expected_campaign_sha256=reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    return _journal(
        [
            (record.body.kind, payload)
            for record, payload in zip(
                recovery.records, payloads, strict=True
            )
        ]
    )


class SharedDirectV2ReaderTests(unittest.TestCase):

    def test_reader_is_cupy_owner_and_adapter_free(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device_v2_result; "
            "print(int('cupy' in sys.modules)); "
            "print(int(any(name.endswith('_v2_runner') for name in sys.modules))); "
            "print(int('pontius.legal_river_quotient_cuda_shared_direct_device' "
            "in sys.modules))"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = f"{_ROOT / 'src'}{os.pathsep}{_ROOT}"
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=15.0,
        )
        self.assertEqual(completed.stdout.splitlines(), ["0", "0", "0"])


    def test_minimal_infrastructure_journal_transduces(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "infrastructure_failure")
        self.assertFalse(rebound.passed)
        self.assertEqual(rebound.event_count, 1)
        self.assertEqual(rebound.populations, ())

    def test_lifecycle_allowlist_is_literal_and_complete(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(
            rebound.lifecycle_allowlist,
            (
                "journal.protocol_sha256",
                "journal.campaign_sha256",
                "header.schema_version",
                "header.config_sha256",
                "header.preregistration_commit",
                "header.dependency_hashes",
                "header.result_relative_path",
                "observations[*].config_sha256",
                "bootstrap.literal_module",
                "bootstrap.spec_name",
            ),
        )

    def test_complete_synthetic_science_transduces_without_payload_edits(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.populations, (10, 22))
        self.assertEqual(rebound.phase_count, 64)
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        self.assertIsNone(recovery.failure)
        translated = reader._translated_journal(recovery.records)
        parent = recover_journal_bytes(
            translated,
            expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
            expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
        )
        self.assertIsNone(parent.failure)
        for v2_record, v1_record in zip(
            recovery.records[2:-1], parent.records[2:-1], strict=True
        ):
            self.assertEqual(
                v2_record.body.payload["event"],
                v1_record.body.payload["event"],
            )
        self.assertEqual(
            recovery.records[-1].body.payload,
            parent.records[-1].body.payload,
        )

    def test_bootstrap_projection_changes_exactly_two_event_fields(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        translated = recover_journal_bytes(
            reader._translated_journal(recovery.records),
            expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
            expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
        )
        before = recovery.records[1].body.payload["event"]
        after = translated.records[1].body.payload["event"]
        changed = {key for key in before if before[key] != after[key]}
        self.assertEqual(changed, {"literal_module", "spec_name"})

    def test_duplicate_bootstrap_is_rejected_before_parent_projection(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        payloads = [
            deepcopy(record.body.payload) for record in recovery.records
        ]
        payloads.insert(2, deepcopy(payloads[1]))
        kinds = [
            JournalRecordKind.HEADER,
            JournalRecordKind.OBSERVATION,
            JournalRecordKind.OBSERVATION,
            JournalRecordKind.TERMINAL,
        ]
        duplicated = _journal(list(zip(kinds, payloads, strict=True)))
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_v2_journal(
                duplicated, rebind_current_sources=False
            )

    def test_lifecycle_mutations_fail_closed(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())

        def corrupt_bootstrap(payloads, field, value) -> None:
            event = payloads[1]["event"]
            event[field] = value

        for field, value in (
            ("challenge_sha256", "0"),
            ("runtime_name", "pontius"),
            ("cupy_imported", True),
            ("literal_module", "pontius.wrong"),
        ):
            broken = _rewrite(
                raw,
                lambda payloads, field=field, value=value: corrupt_bootstrap(
                    payloads, field, value
                ),
            )
            with self.assertRaises(ValueError):
                reader.rebind_shared_direct_device_v2_journal(
                    broken, rebind_current_sources=False
                )

    def test_post_bootstrap_and_outer_mutations_fail_closed(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())

        def corrupt_runtime(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "runtime"
            )
            event["built_cuda_source_sha256"] = "0" * 64

        def corrupt_phase(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "phase"
            )
            event["host_ns"] += 1

        def corrupt_population(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "population"
            )
            event["gates"]["chip_units"] = False

        def corrupt_outer(payloads) -> None:
            payloads[-1]["capacity_projection"] = [1, 1]

        for mutation in (
            corrupt_runtime,
            corrupt_phase,
            corrupt_population,
            corrupt_outer,
        ):
            with self.assertRaises(ValueError):
                reader.rebind_shared_direct_device_v2_journal(
                    _rewrite(raw, mutation), rebind_current_sources=False
                )

    def test_reader_never_reads_absent_v1_result(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        original = Path.read_bytes
        opened: list[Path] = []

        def recording(path: Path) -> bytes:
            opened.append(path)
            return original(path)

        with patch.object(Path, "read_bytes", recording):
            reader.rebind_shared_direct_device_v2_journal(
                raw, rebind_current_sources=False
            )
        self.assertNotIn(_V1_RESULT, opened)


if __name__ == "__main__":
    unittest.main()
