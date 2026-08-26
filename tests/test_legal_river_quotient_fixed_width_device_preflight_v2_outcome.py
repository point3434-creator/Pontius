from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import subprocess
import unittest

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius.legal_river_quotient_fixed_width_device_preflight_v2_outcome import (
    CAMPAIGN_SHA256,
    PROTOCOL_SHA256,
    RESULT_PATH,
    RESULT_SHA256,
    assess_device_preflight_v2_outcome_bytes,
    assess_device_preflight_v2_outcome_file,
)
from pontius.legal_river_quotient_fixed_width_device_preflight_v2_result import (
    assess_device_preflight_v2_bytes,
)


ROOT = Path(__file__).parents[1]


def _replace_terminal(raw: bytes, **changes: object) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    header = recovery.records[0]
    payload = recovery.records[1].body.payload
    payload.update(changes)
    body = build_journal_record_body(
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
        kind=JournalRecordKind.TERMINAL,
        sequence=1,
        previous_record_sha256=header.line_sha256,
        semantic_identity_sha256=sha256(
            canonical_journal_json_bytes(payload)
        ).hexdigest(),
        payload=payload,
    )
    return header.line_bytes + JournalRecordEnvelope(body=body).line_bytes


class FixedWidthDevicePreflightV2OutcomeTests(unittest.TestCase):
    def test_exact_retained_zero_event_terminal_is_independently_assessed(self) -> None:
        self.assertEqual(
            asdict(assess_device_preflight_v2_outcome_file()),
            {
                "terminal": "infrastructure_failure",
                "passed": False,
                "source_commit": "3cf5d1d8f5667f7bf48102ed130f92fce33c9516",
                "record_count": 2,
                "event_count": 0,
                "eligible_arms": (),
                "candidate_selected": None,
                "laboratory_elapsed_ns": None,
                "outside_laboratory_elapsed_ns": None,
                "public_elapsed_ns": 2_614_814_700,
            },
        )

    def test_retained_raw_identity_and_unfiltered_path(self) -> None:
        raw = RESULT_PATH.read_bytes()
        self.assertEqual(len(raw), 10_557)
        self.assertEqual(sha256(raw).hexdigest(), RESULT_SHA256)
        relative = RESULT_PATH.relative_to(ROOT).as_posix()
        completed = subprocess.run(
            ["git", "check-attr", "text", "--", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), f"{relative}: text: unset")

    def test_source_sealed_reader_exposes_the_zero_event_schema_defect(self) -> None:
        with self.assertRaisesRegex(ValueError, "observations are absent"):
            assess_device_preflight_v2_bytes(RESULT_PATH.read_bytes())

    def test_zero_event_terminal_mutations_reject(self) -> None:
        raw = RESULT_PATH.read_bytes()
        for change in (
            {"event_count": 1},
            {"passed": True},
            {"terminal": "completed_device_preflight"},
            {"laboratory_elapsed_ns": 0},
            {"outside_laboratory_elapsed_ns": 0},
            {"public_elapsed_ns": 2_614_814_701},
        ):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    assess_device_preflight_v2_outcome_bytes(
                        _replace_terminal(raw, **change)
                    )

    def test_torn_or_extended_lifecycle_rejects(self) -> None:
        raw = RESULT_PATH.read_bytes()
        for mutated in (raw[:-1], raw + b"{}\n", raw.splitlines(keepends=True)[0]):
            with self.subTest(size=len(mutated)):
                with self.assertRaises(ValueError):
                    assess_device_preflight_v2_outcome_bytes(mutated)


if __name__ == "__main__":
    unittest.main()
