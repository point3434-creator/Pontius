"""Behavioral checks for journal-derived status; no ADR freshness rules."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pontius.status_generation import append_run, render_status


class JournalStatusTests(unittest.TestCase):
    def test_empty_journal_reports_no_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn("No runs recorded", render_status(Path(directory)))

    def test_status_uses_observed_outcomes_and_escapes_table_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            append_run(
                root,
                {
                    "timestamp": "2026-09-08T00:00:00Z",
                    "command": "benchmark | trial",
                    "status": "failed",
                    "summary": "18 complete; 322 unattempted",
                    "duration_seconds": 3604.31,
                },
            )
            rendered = render_status(root)
            self.assertIn("failed", rendered)
            self.assertIn("18 complete; 322 unattempted", rendered)
            self.assertIn(r"benchmark \| trial", rendered)
            self.assertIn("3604.310", rendered)

    def test_append_preserves_prior_run_and_outputs_recent_first(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("first", "second"):
                append_run(
                    root,
                    {
                        "timestamp": "2026-09-08T00:00:00Z",
                        "command": name,
                        "status": "passed",
                        "summary": name,
                    },
                )
            rows = (root / "execution_journal.jsonl").read_text().splitlines()
            self.assertEqual([json.loads(row)["command"] for row in rows], ["first", "second"])
            rendered = render_status(root)
            self.assertLess(rendered.index("second"), rendered.index("first"))

    def test_truncated_journal_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "execution_journal.jsonl").write_text('{"timestamp":', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1"):
                render_status(root)

    def test_invalid_row_is_rejected_before_append(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                append_run(root, {"status": "passed"})
            self.assertFalse((root / "execution_journal.jsonl").exists())
