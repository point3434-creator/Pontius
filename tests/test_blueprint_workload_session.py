"""Run-boundary identity, per-cell grants, and persistent-worker cleanup."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pontius.execution import begin_run, child_context, CONTEXT_ENV, finish_run

ROOT = Path(__file__).resolve().parents[1]
GIT = os.environ.get("PONTIUS_GIT") or shutil.which("git")
if GIT is None or not Path(GIT).is_absolute():
    raise RuntimeError("an absolute Git executable is required for these fixtures")
SPEC = importlib.util.spec_from_file_location(
    "workload_controller_tests", ROOT / "tools/v0a_blueprint_workload.py"
)
CONTROLLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROLLER)


class SourceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "src").mkdir()
        (self.root / "src/example.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests/test_example.py").write_text("assert False\n", encoding="utf-8")
        (self.root / "tests/cases.json").write_text('["test_example"]\n', encoding="utf-8")
        for args in (
            ("init", "-q"),
            ("add", "."),
            (
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ),
        ):
            subprocess.run([GIT, "-C", str(self.root), *args], check=True, capture_output=True)

    def test_reviewed_source_matches_and_drift_is_rejected(self):
        context = begin_run(self.root)
        self.assertTrue(context["verified"])
        (self.root / "src/example.py").write_text("value = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs"):
            begin_run(self.root)
        self.assertFalse(begin_run(self.root, allow_working_tree=True)["verified"])

    def test_extra_and_missing_source_files_are_rejected(self):
        (self.root / "src/extra.py").write_text("pass\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            begin_run(self.root)
        (self.root / "src/extra.py").unlink()
        (self.root / "src/example.py").unlink()
        with self.assertRaises(ValueError):
            begin_run(self.root)

    def test_changed_assertions_and_manifest_change_run_identity(self):
        original = begin_run(self.root)
        for name, changed in (("test_example.py", "assert True\n"), ("cases.json", "[]\n")):
            with self.subTest(name=name):
                path = self.root / "tests" / name
                previous = path.read_bytes()
                path.write_text(changed, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "differs"):
                    begin_run(self.root)
                candidate = begin_run(self.root, allow_working_tree=True)
                self.assertNotEqual(original["source_sha256"], candidate["source_sha256"])
                path.write_bytes(previous)

    def test_staged_source_additions_are_not_hidden_by_the_index(self):
        original = begin_run(self.root)
        (self.root / "src/extra.py").write_text("value = 2\n", encoding="utf-8")
        subprocess.run([GIT, "-C", str(self.root), "add", "src/extra.py"], check=True)
        with self.assertRaisesRegex(ValueError, "differs"):
            begin_run(self.root)
        candidate = begin_run(self.root, allow_working_tree=True)
        self.assertNotEqual(original["source_sha256"], candidate["source_sha256"])
    def test_inherited_context_performs_no_git_or_file_reads(self):
        context = begin_run(self.root)
        with (
            patch("pontius.execution.git", side_effect=AssertionError("rechecked Git")),
            patch.object(Path, "read_bytes", side_effect=AssertionError("reread source")),
        ):
            inherited = begin_run(self.root, inherited=child_context(context))
        self.assertTrue(inherited["inherited"])
        self.assertEqual(inherited["source_sha256"], context["source_sha256"])

    def test_one_final_output_and_journal_line_no_child_write(self):
        context = begin_run(self.root)
        finish_run(dict(context, inherited=True), "child", {"status": "completed"}, 0.1)
        self.assertFalse((self.root / "execution_journal.jsonl").exists())
        finish_run(context, "fixture", {"status": "completed", "summary": "three cells"}, 0.1)
        lines = (self.root / "execution_journal.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(
            record["output_sha256"],
            hashlib.sha256((self.root / record["output"]).read_bytes()).hexdigest(),
        )


@unittest.skipUnless(os.name == "nt", "native Windows worker job")
class PersistentWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "artifacts").mkdir()
        population = CONTROLLER.load_tool("blueprint_workload_population")
        seed = json.loads((ROOT / "tests/fixtures/blueprint_workload/control.json").read_bytes())[
            "seed"
        ]
        trajectory = population.trajectory(population.factors("table", 0), seed=seed)
        raw, metadata = population.artifact([])
        (self.root / "artifacts/0.json").write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        metadata["file"] = dict(path="artifacts/0.json", sha256=digest, bytes=len(raw))
        self.request = dict(
            population_root=str(self.root),
            population={"artifacts": [metadata]},
            selections={"first_context": trajectory["contexts"][0]},
            input_hashes={"artifacts/0.json": digest},
            cells=[
                dict(
                    id=f"control-{index}",
                    runtime=f"{sys.version_info.major}.{sys.version_info.minor}",
                    kind="construction",
                    size=0,
                    parameters={"observation": index},
                    argv=[],
                )
                for index in range(2)
            ],
        )
        self.context = json.loads(os.environ[CONTEXT_ENV])

    def supervise(self, seconds=15, *, close_error=False):
        processes = []
        real_popen = subprocess.Popen

        def observe(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            if kwargs.get("creationflags", 0) & CONTROLLER.load_tool("table_host").CREATE_SUSPENDED:
                processes.append(process)
                for stream in (process.stdin, process.stdout, process.stderr):
                    self.addCleanup(stream.close)
                if close_error:
                    real_close = process.stdout.close

                    def close_then_fail():
                        real_close()
                        raise OSError("injected post-close failure")

                    closer = patch.object(process.stdout, "close", side_effect=close_then_fail)
                    closer.start()
                    self.addCleanup(closer.stop)
                    self.addCleanup(real_close)
            return process

        with patch.object(CONTROLLER.subprocess, "Popen", side_effect=observe):
            report = CONTROLLER.supervise(
                self.request, self.context, seconds, 3072 * 1024 * 1024
            )
        self.assertEqual(len(processes), 1)
        process = processes[0]
        self.assertIsNotNone(process.poll(), "real worker survived supervision")
        self.assertTrue(
            all(getattr(process, name).closed for name in ("stdin", "stdout", "stderr")),
            "supervision returned with an open real worker pipe",
        )
        return report

    def test_pipe_close_error_withholds_cleanup_certificate(self):
        report = self.supervise(close_error=True)
        self.assertEqual(report["status"], "failed", report)
        self.assertFalse(report["cleanup_verified"])
        self.assertEqual(report["completed"], 2)
        self.assertTrue(any("injected post-close failure" in error for error in report["errors"]))

    def test_two_cells_use_one_worker_and_two_in_memory_grants(self):
        report = self.supervise()
        self.assertEqual(report["status"], "completed", report)
        self.assertEqual(report["completed"], 2)
        self.assertEqual(report["grants"], 2)
        self.assertEqual(report["worker_count"], 1)
        self.assertTrue(report["cleanup_verified"])
        self.assertGreater(report["peak_job_memory_bytes"], 0)
        self.assertEqual(list(self.root.iterdir()), [self.root / "artifacts"])

    def test_changed_cell_input_is_refused_before_grant(self):
        (self.root / "artifacts/0.json").write_bytes(b"{}")
        report = self.supervise()
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["grants"], 0)
        self.assertEqual(report["completed"], 0)
        self.assertTrue(report["cleanup_verified"])
        self.assertTrue(any("cell input changed" in error for error in report["errors"]))

    def test_stderr_drained_after_exit_prevents_success(self):
        class DelayedStderrThread(CONTROLLER.threading.Thread):
            def start(self):
                self.delayed = self._target.__name__ == "receive_errors"
                if not self.delayed:
                    super().start()

            def join(self, timeout=None):
                if self.delayed:
                    self._target(io.StringIO("late worker error\n"))
                else:
                    super().join(timeout)

        with patch.object(CONTROLLER.threading, "Thread", DelayedStderrThread):
            report = self.supervise()
        self.assertEqual(report["completed"], 2)
        self.assertEqual(report["worker_exit_code"], 0)
        self.assertTrue(report["cleanup_verified"])
        self.assertIn("late worker error", report["errors"])
        self.assertEqual(report["status"], "failed")

    def test_budget_stops_worker_during_startup_and_cleans_job(self):
        report = self.supervise(0.01)
        self.assertEqual(report["status"], "budget_exhausted")
        self.assertTrue(report["cleanup_verified"])
        self.assertLess(report["completed"], 2)

    def test_assignment_failure_does_not_leave_suspended_worker(self):
        host = CONTROLLER.load_tool("table_host")
        with patch.object(host.Job, "assign", side_effect=OSError("assignment failed")):
            report = self.supervise()
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["cleanup_verified"])
        self.assertIsNotNone(report["worker_exit_code"])

    def test_expired_input_check_does_not_grant_a_cell(self):
        def slow_head(*args, **kwargs):
            time.sleep(1)
            return self.context["head"].encode()

        with patch.object(CONTROLLER, "git", side_effect=slow_head):
            report = self.supervise(0.8)
        self.assertEqual(report["status"], "budget_exhausted")
        self.assertEqual(report["grants"], 0)
        self.assertTrue(report["cleanup_verified"])

    def test_session_admissions_reuse_loaded_host_without_reading_it(self):
        session_tool = CONTROLLER.load_tool("table_session")
        first = session_tool.Admission(ROOT)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("reread host")):
            second = session_tool.Admission(ROOT)
        self.assertIs(first.host, second.host)

    def test_closed_stdout_still_retains_session_outcome(self):
        session_tool = CONTROLLER.load_tool("table_session")
        report = {"status": "completed", "failure_reason": None, "stop_reason": None}
        session = SimpleNamespace(
            run=lambda: report,
            admission=SimpleNamespace(source=SimpleNamespace(context=self.context)),
        )
        with (
            patch.object(session_tool, "arguments", return_value=SimpleNamespace(format="json")),
            patch.object(session_tool, "Session", return_value=session),
            patch.object(session_tool.os, "write", side_effect=BrokenPipeError()),
            patch("pontius.execution.finish_run") as retain,
        ):
            self.assertEqual(session_tool.main([]), 1)
        retain.assert_called_once()
        self.assertIs(retain.call_args.args[2], report)

    def test_worker_rejects_wrong_nonce(self):
        request = (
            json.dumps(self.request)
            + "\n"
            + json.dumps({"id": "control-0", "nonce": "wrong", "granted": True})
            + "\n"
        )
        with (
            patch.object(sys, "stdin", io.StringIO(request)),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaisesRegex(ValueError, "grant"):
                CONTROLLER.worker()
