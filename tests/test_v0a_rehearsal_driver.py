"""CLI integration controls; every execution uses a correctness identity."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "tools/v0a_rehearsal_driver.py"
PREFIX = "pontius-v0a-hand-replay-v1-correctness-"
SEAL = "af90155ebd970d0be6fe26969b121bd213a7f1f2"


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.run_id = PREFIX + "unit"
        self.root = Path(self.scratch.name) / self.run_id
        self.root.mkdir()

    def cli(self, *extra, mode="correctness", run_id=None, root=None, fixture="control-A"):
        return subprocess.run(
            [sys.executable, "-B", "-P", str(DRIVER), "--mode", mode,
             "--run-id", run_id or self.run_id, "--run-root", str(root or self.root),
             "--fixture", fixture, *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )

    def load_driver(self):
        self.assertTrue(DRIVER.is_file(), "the approved CLI driver is missing")
        spec = importlib.util.spec_from_file_location("driver_under_test", DRIVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_both_controls_publish_complete_independently_verified_traces(self):
        # Catches omitted host execution, wrong fixture, or success without a persisted trace.
        for fixture, payouts in (("control-A", [0, 0, 0, 12, 0, 0]),
                                 ("control-B", [16, 10, 24, 30, 0, 0])):
            with self.subTest(fixture=fixture):
                run_id = PREFIX + fixture
                root = Path(self.scratch.name) / run_id
                root.mkdir()
                result = self.cli(fixture=fixture, root=root, run_id=run_id)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertTrue(receipt["passed"])
                self.assertFalse(receipt["evidentiary"])
                self.assertEqual(receipt["source_commit"], SEAL)
                raw = (root / "trace.jsonl").read_bytes()
                rows = [json.loads(line) for line in raw.splitlines()]
                self.assertEqual(rows[0]["mode"], "correctness")
                self.assertEqual(rows[0]["clock_kind"], "monotonic_ns")
                self.assertEqual(rows[0]["run_id"], run_id)
                self.assertTrue(rows[-1]["passed"])
                self.assertEqual(receipt["trace_sha256"], hashlib.sha256(raw).hexdigest())
                if payouts is not None:
                    self.assertEqual(receipt["payouts"], payouts)

    def test_wrong_mode_namespace_refuses_without_writes(self):
        result = self.cli(mode="rehearsal")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("IDENTITY", result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_authorized_mode_is_not_an_option(self):
        result = self.cli(mode="authorized")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_wrong_root_and_missing_root_refuse_without_writes(self):
        for root in (Path(self.scratch.name), self.root / "missing"):
            with self.subTest(root=root):
                result = self.cli(root=root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ROOT", result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_existing_trace_is_retained_and_never_overwritten(self):
        trace = self.root / "trace.jsonl"
        trace.write_bytes(b"retained failure\n")
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(trace.read_bytes(), b"retained failure\n")

    def test_unsafe_suffix_refuses(self):
        for suffix in ("", "../escape", "x.y", "x "):
            with self.subTest(suffix=suffix):
                result = self.cli(run_id=PREFIX + suffix)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("IDENTITY", result.stderr)

    def test_changed_source_refuses_before_import_and_publication(self):
        # Only mutate the disposable snapshot, restoring exact bytes in finally.
        source = ROOT / "src/pontius/v0a/replay.py"
        original = source.read_bytes()
        try:
            source.write_bytes(original + b"\n# correctness fault injection\n")
            result = self.cli()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SOURCE", result.stderr)
            self.assertEqual(list(self.root.iterdir()), [])
        finally:
            source.write_bytes(original)

    def test_import_shadow_refuses_before_publication(self):
        shadow = ROOT / "src/pontius/v0a/replay.pyd"
        self.assertFalse(shadow.exists())
        try:
            shadow.write_bytes(b"not a library")
            result = self.cli()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SOURCE", result.stderr)
        finally:
            shadow.unlink()

    def test_missing_git_is_typed_refusal(self):
        with patch.dict(os.environ, {"PONTIUS_GIT": ""}):
            result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE", result.stderr)

    def test_failed_host_receipt_cannot_earn_success(self):
        driver = self.load_driver()
        from types import SimpleNamespace
        for passed, complete in ((False, True), (True, False)):
            with self.subTest(passed=passed, accounting_complete=complete):
                receipt = SimpleNamespace(passed=passed, accounting_complete=complete)
                outcome = SimpleNamespace(receipt=receipt)
                with self.assertRaisesRegex(driver.DriverRefusal, "HOST"):
                    driver.accept_trace(outcome, self.root / "trace.jsonl", None, None,
                                        self.run_id, "correctness", "0" * 64)

    def test_corrupt_persisted_trace_cannot_earn_success(self):
        driver = self.load_driver()
        from types import SimpleNamespace
        path = self.root / "trace.jsonl"
        path.write_bytes(b"damaged\n")
        original = b"original\n"
        receipt = SimpleNamespace(passed=True, accounting_complete=True,
                                  trace_sha256=hashlib.sha256(original).hexdigest())
        outcome = SimpleNamespace(receipt=receipt, trace=original)
        with self.assertRaisesRegex(driver.DriverRefusal, "READBACK"):
            driver.accept_trace(outcome, path, None, None,
                                self.run_id, "correctness", "0" * 64)

    def test_matching_hashes_do_not_replace_independent_replay(self):
        driver = self.load_driver()
        from types import SimpleNamespace
        path = self.root / "trace.jsonl"
        content = b'{}\n'
        path.write_bytes(content)
        receipt = SimpleNamespace(passed=True, accounting_complete=True,
                                  trace_sha256=hashlib.sha256(content).hexdigest())
        outcome = SimpleNamespace(receipt=receipt, trace=content)
        with self.assertRaisesRegex(driver.DriverRefusal, "VERIFY"):
            driver.accept_trace(outcome, path, None, None,
                                self.run_id, "correctness", "0" * 64)


if __name__ == "__main__":
    unittest.main()
