"""Plan admission, worker phases, the real supervisor, and one-run ownership of the tool."""

from __future__ import annotations

import base64
import copy
import dis
import hashlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from pontius.execution import begin_run

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eval_panel_tool_tests", ROOT / "tools/v0a_eval_panel.py")
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
FIXTURES = ROOT / "tests/fixtures/eval_panel"
CAPACITY_RAW = (FIXTURES / "plan-capacity.json").read_bytes()
CAPACITY = json.loads(CAPACITY_RAW)
PREFLIGHT = json.loads((FIXTURES / "plan-preflight.json").read_bytes())
ROYAL = ["Ts", "Js", "Qs", "Ks", "As"]


def altered(plan, path, value):
    plan = copy.deepcopy(plan)
    target = plan
    for part in path[:-1]:
        target = target[part]
    if value is ...:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return plan


def royal_subset(seconds=600):
    plan = altered(PREFLIGHT, ("development_hands",), [["2c", "3d"]])
    plan = altered(altered(plan, ("board",), ROYAL), ("controls",), [])
    plan = altered(plan, ("coverage",), "test-subset")
    plan = altered(plan, ("resource", "seconds"), seconds)
    from pontius import eval_bridge as bridge
    universe = bridge.hero_hands(bridge.board_cards(ROYAL))
    order = bridge.strength_blind_permutation(universe, plan["pool_seed"])
    plan["hand_universe_sha256"] = bridge.hand_universe_digest(universe)
    plan["permutation"] = [bridge.hand_name(hand) for hand in order]
    return plan


def collect(plan, seconds=600):
    events = []
    TOOL.run_plan(TOOL.validate_plan(plan), events.append, time.perf_counter() + seconds)
    return events


class PlanAdmissionTests(unittest.TestCase):
    def test_declared_full_refuses_role_movement(self):
        for count in (1, 4):
            moved = copy.deepcopy(PREFLIGHT)
            moved["controls"] += [dict(board=moved["board"], hand=hand)
                                  for hand in moved["development_hands"][:count]]
            moved["development_hands"] = moved["development_hands"][count:]
            with self.subTest(moved=count), self.assertRaises(ValueError):
                TOOL.validate_plan(moved)
        rebound = royal_subset()
        rebound.update(coverage="declared-full", development_hands=[],
                       controls=[dict(board=PREFLIGHT["board"], hand=hand)
                                 for hand in PREFLIGHT["development_hands"]]
                       + [copy.deepcopy(PREFLIGHT["controls"][0])])
        with self.assertRaises(ValueError):
            TOOL.validate_plan(rebound)

    def test_parse_refuses_size_nonfinite_numbers_and_constants(self):
        TOOL.validate_plan(TOOL.parse_plan(CAPACITY_RAW))
        for raw in (b"", b"x" * (TOOL.PLAN_LIMIT + 1),
                    CAPACITY_RAW.replace(b'"seconds": 600', b'"seconds": 1e999'),
                    CAPACITY_RAW.replace(b'"seconds": 600', b'"seconds": NaN'),
                    CAPACITY_RAW.replace(b'"seconds": 600', b'"seconds": Infinity')):
            with self.assertRaises(ValueError):
                TOOL.parse_plan(raw)

    def test_validate_refuses_every_wrong_or_missing_member(self):
        TOOL.validate_plan(CAPACITY)
        TOOL.validate_plan(PREFLIGHT)
        shuffled = list(reversed(CAPACITY["permutation"]))
        duplicated = CAPACITY["permutation"][:-1] + CAPACITY["permutation"][:1]
        wrong = (
            (("version",), "pontius-eval-panel-plan-v1"), (("phase",), "export"),
            (("runtime", "python"), "3.11.15"), (("board",), list(reversed(CAPACITY["board"]))),
            (("stacks",), 3), (("stacks",), 6), (("prefix", 0), [3, "check"]),
            (("hand_universe_sha256",), "0" * 64), (("hand_count",), 1080),
            (("pool_seed",), "ab" * 31), (("permutation",), shuffled),
            (("permutation",), duplicated),
            (("permutation",), CAPACITY["permutation"][:-1]), (("resource", "seconds"), True),
            (("resource", "seconds"), 0), (("resource", "memory_mib"), 1.5),
            (("resource", "memory_mib"), TOOL.MEMORY_LIMIT_MIB + 1), (("resource",), None),
            (("seed_index_bank",), []), (("runtime",), ...), (("permutation",), ...),
        )
        for path, value in wrong:
            with self.assertRaises(ValueError, msg=path):
                TOOL.validate_plan(altered(CAPACITY, path, value))
        as_ad = [["As", "Ad"]]
        substituted = [["Ks", "Kc"], ["Qh", "Qd"], ["Jd", "8d"], ["3h", "4h"]]
        for path, value in ((("coverage",), "full"), (("development_hands",), ...),
                            (("controls",), ...), (("development_hands",), as_ad),
                            (("development_hands",), as_ad * 4),
                            (("development_hands",), substituted), (("controls",), []),
                            (("controls",), [dict(board=PREFLIGHT["board"], hand=["Ks", "Kc"])]),
                            (("controls", 0, "hand"), ["3c", "4d"]),
                            (("development_hands", 0), ["Zz", "Ad"]),
                            (("development_hands", 0), ["2c", "Ad"]),
                            (("development_hands", 0), ["As", "As"]),
                            (("development_hands", 0), "AsAd")):
            with self.assertRaises(ValueError, msg=path):
                TOOL.validate_plan(altered(PREFLIGHT, path, value))
        TOOL.validate_plan(altered(PREFLIGHT, ("development_hands", 0), ["Ad", "As"]))
        subset = altered(PREFLIGHT, ("development_hands",), as_ad)
        TOOL.validate_plan(altered(subset, ("coverage",), "test-subset"))
        with self.assertRaises(ValueError):
            TOOL.validate_plan(altered(altered(subset, ("coverage",), "test-subset"),
                                       ("development_hands",), as_ad * 2))


class WorkerTests(unittest.TestCase):
    def test_capacity_phase_emits_boundary_bytes(self):
        events = collect(CAPACITY)
        self.assertEqual([event["event"] for event in events], ["ready", "observation"])
        observation = events[1]
        self.assertEqual(observation["probe"]["cap"], 1048576)
        self.assertTrue(0 < observation["probe"]["largest_fitting"] <= 1081)
        self.assertEqual(len(observation["boundary_base64"]),
                         1 if observation["probe"]["all_fit"] else 2)
        with tempfile.TemporaryDirectory() as directory:
            report = dict(observations=[copy.deepcopy(observation)])
            TOOL.retain_boundaries(report, Path(directory))
            row = report["observations"][0]
            self.assertEqual(row["boundary_retention"], "complete")
            self.assertNotIn("boundary_base64", row)
            for count, binding in row["boundary_artifacts"].items():
                raw = (Path(directory) / binding["path"]).read_bytes()
                self.assertEqual(raw, base64.b64decode(observation["boundary_base64"][count]))
                self.assertEqual(binding["sha256"], hashlib.sha256(raw).hexdigest())

    def test_retention_failure_keeps_bound_artifacts_and_unwritten_encodings(self):
        encodings = {"7": b"seven" * 3, "8": b"eight" * 5}
        row = dict(kind="capacity", boundary_base64={
            count: base64.b64encode(raw).decode("ascii") for count, raw in encodings.items()})
        report, writes, original = dict(observations=[row]), [], Path.write_bytes

        def failing_second_write(path, data):
            writes.append(path.name)
            if len(writes) == 2:
                raise OSError("disk full")
            return original(path, data)

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path, "write_bytes", failing_second_write):
                with self.assertRaises(OSError):
                    TOOL.retain_boundaries(report, Path(directory))
            self.assertEqual(list(row["boundary_artifacts"]), ["7"])
            self.assertEqual(row["boundary_artifacts"]["7"]["sha256"],
                             hashlib.sha256(encodings["7"]).hexdigest())
            self.assertEqual(list(row["boundary_base64"]), ["8"])
            self.assertTrue(row["boundary_retention"].startswith("incomplete"))
            self.assertEqual([path.name for path in Path(directory).iterdir()],
                             ["capacity-boundary-7.blueprint.json"])
            TOOL.retain_boundaries(report, Path(directory))
            self.assertEqual(row["boundary_retention"], "complete")
            self.assertEqual(sorted(row["boundary_artifacts"]), ["7", "8"])
            self.assertEqual((Path(directory) / "capacity-boundary-8.blueprint.json").read_bytes(),
                             encodings["8"])

    def test_full_pool_estimate_needs_every_declared_hand_complete(self):
        admitted = TOOL.validate_plan(PREFLIGHT)
        rows = []  # Labeled estimator fixtures; real five-hand integration is tested separately.
        for unit in admitted.schedule:
            role, board, hand = unit.record_key
            stages = {name: {} for name in TOOL.STAGES}
            stages["production"] = dict(cost=dict(elapsed_seconds=0.5))
            stages["comparison"] = dict(comparison=dict(passed=True))
            rows.append(dict(kind="preflight", label=role, board=list(board), hand=hand,
                             complete=True, stages=stages))
        estimate = TOOL.full_pool_estimate(rows, 1081, admitted)
        self.assertEqual((estimate["kind"], estimate["sample"]), ("estimate", 4))
        rows[3]["complete"] = False
        partial = TOOL.full_pool_estimate(rows, 1081, admitted)
        self.assertEqual(partial["kind"], "not_estimated")
        rows[3]["complete"] = True
        self.assertEqual(TOOL.full_pool_estimate(rows[:-1], 1081, admitted)["kind"],
                         "not_estimated")
        rows[-1]["stages"]["comparison"]["comparison"]["passed"] = False
        self.assertEqual(TOOL.full_pool_estimate(rows, 1081, admitted)["kind"], "not_estimated")
        self.assertEqual(TOOL.full_pool_estimate(
            rows, 1081, TOOL.validate_plan(royal_subset()))["kind"],
                         "not_estimated")
        self.assertIsNone(TOOL.full_pool_estimate(rows, 1081, TOOL.validate_plan(CAPACITY)))

    def test_preflight_emits_one_stage_per_measured_step(self):
        events = collect(royal_subset())
        kinds = [event["event"] for event in events]
        self.assertEqual(kinds, ["ready"] + ["stage"] * len(TOOL.STAGES) + ["hand_completed"])
        self.assertEqual([event["stage"] for event in events[1:-1]], list(TOOL.STAGES))
        self.assertTrue(events[-2]["comparison"]["passed"], events[-2]["comparison"])
        self.assertTrue(events[2]["repeat_matches"])
        for event in events[1:-1]:
            self.assertIn("elapsed_seconds", event["cost"])
            self.assertIn("hits", event["cache_after"])

    def test_exhausted_budget_stops_before_the_next_hand(self):
        events = collect(PREFLIGHT, seconds=0)
        self.assertEqual([event["event"] for event in events], ["ready", "failed"])
        self.assertIn("budget exhausted", events[1]["error"])

    def test_json_safe_tags_nonfinite_values(self):
        safe = TOOL.json_safe(dict(a=float("inf"), b=[float("nan"), 1.5], c="x"))
        self.assertEqual(safe, dict(a={"nonfinite": "inf"}, b=[{"nonfinite": "nan"}, 1.5], c="x"))
        json.dumps(safe, allow_nan=False)


class RealSupervisorTests(unittest.TestCase):
    """Each case launches the actual worker inside the actual Job; nothing is mocked."""

    @classmethod
    def setUpClass(cls):
        cls.context = begin_run(ROOT, allow_working_tree=True)

    def test_capacity_runs_to_completion_under_containment(self):
        report = TOOL.supervise(CAPACITY, self.context, 600, 2048 * 1024 * 1024)
        self.assertEqual((report["status"], report["errors"]), ("completed", []), report)
        self.assertTrue(report["cleanup_verified"])
        self.assertEqual(report["worker_exit_code"], 0)
        self.assertEqual([row["kind"] for row in report["observations"]], ["capacity"])
        self.assertGreater(report["peak_job_memory_bytes"], 0)
        self.assertEqual(set(report["cleanup"].values()), {"ok"}, report["cleanup"])

    def test_cleanup_faults_do_not_skip_later_releases_or_retained_stages(self):
        host = TOOL.load_host()

        def failing_query(self):
            raise host.HostRefusal("cleanup_failed")

        def failing_join(self, timeout=None):
            raise OSError("join refused")

        with patch.object(host.Job, "active", failing_query), \
                patch.object(threading.Thread, "join", failing_join):
            report = TOOL.supervise(royal_subset(seconds=6), self.context, 6, 2048 * 1024 * 1024)
        cleanup = report["cleanup"]
        self.assertEqual(report["status"], "budget_exhausted", report)
        self.assertFalse(report["cleanup_verified"])
        self.assertIsNotNone(report["worker_exit_code"])
        self.assertTrue(cleanup["terminate job"].startswith("HostRefusal"), cleanup)
        self.assertTrue(cleanup["verify"].startswith("HostRefusal"), cleanup)
        self.assertEqual([cleanup[f"join thread {index}"][:7] for index in range(3)],
                         ["OSError"] * 3)
        for name in ("kill process", "wait", "close stdin", "close stdout", "close stderr",
                     "drain", "close job"):
            self.assertEqual(cleanup[name], "ok", (name, cleanup))
        self.assertTrue(any(error.startswith("cleanup verify: HostRefusal")
                            for error in report["errors"]), report["errors"])
        self.assertIn("production", report["observations"][0]["stages"])

    def test_interrupt_during_cleanup_keeps_the_partial_report(self):
        def interrupted_wait(self, timeout=None):
            raise KeyboardInterrupt

        with patch.object(subprocess.Popen, "wait", interrupted_wait):
            report = TOOL.supervise(royal_subset(seconds=6), self.context, 6, 2048 * 1024 * 1024)
        self.assertEqual(report["status"], "interrupted")
        self.assertEqual(report["cleanup"]["wait"], "interrupted")
        self.assertFalse(report["cleanup_verified"])
        for name in ("close stdin", "close stdout", "close stderr", "drain", "verify", "close job"):
            self.assertEqual(report["cleanup"][name], "ok", report["cleanup"])
        self.assertIn("production", report["observations"][0]["stages"])

    def test_assignment_refusal_kills_the_suspended_worker_and_keeps_the_cause(self):
        host = TOOL.load_host()

        def refuse_assignment(self, process):
            raise host.HostRefusal("containment_failed")

        with patch.object(host.Job, "assign", refuse_assignment):
            report = TOOL.supervise(CAPACITY, self.context, 60, 2048 * 1024 * 1024)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("containment_failed" in error for error in report["errors"]), report)
        self.assertIsNotNone(report["worker_exit_code"])
        self.assertTrue(report["cleanup_verified"])
        self.assertEqual(report["observations"], [])

    def test_budget_kill_during_reference_keeps_the_completed_production_stage(self):
        report = TOOL.supervise(royal_subset(seconds=6), self.context, 6, 2048 * 1024 * 1024)
        self.assertEqual(report["status"], "budget_exhausted", report)
        self.assertTrue(report["cleanup_verified"])
        self.assertEqual(len(report["observations"]), 1)
        record = report["observations"][0]
        self.assertFalse(record["complete"])
        self.assertIn("production", record["stages"])
        self.assertIn("comparison", record["missing_stages"])
        self.assertEqual(record["stages"]["production"]["production"]["action"], "check")


class OwnershipTests(unittest.TestCase):
    """main through the real result and journal writers in a disposable repository."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative, text in (("src/example.py", "value = 1\n"), ("tools/tool.py", "pass\n"),
                               ("tests/cases.json", "[]\n"), ("STATUS.md", "# Status\n")):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            (self.root / relative).write_text(text, encoding="utf-8")
        git = os.environ.get("PONTIUS_GIT") or shutil.which("git")  # as execution.git resolves it
        for args in (("init", "-q"), ("add", "."),
                     ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                      "commit", "-qm", "fixture")):
            subprocess.run([git, "-C", str(self.root), *args], check=True, capture_output=True)

    def journal_lines(self):
        journal = self.root / "execution_journal.jsonl"
        return journal.read_text(encoding="utf-8").splitlines() if journal.exists() else []

    def run_main(self, raw, supervised):
        plan_path = self.root / "plan.json"
        plan_path.write_bytes(raw)
        calls = []

        def fake_supervise(plan, context, seconds, memory_bytes, report):
            calls.append(plan.document["phase"])
            report.update({key: value for key, value in supervised.items() if key != "raise"})
            if "raise" in supervised:
                raise supervised["raise"]
            return report

        with patch.object(TOOL, "ROOT", self.root), patch.object(TOOL, "supervise", fake_supervise):
            code = TOOL.main(["run", "--plan", str(plan_path)])
        return code, calls

    def test_completed_run_records_exactly_once_with_its_result_directory(self):
        supervised = dict(status="completed", observations=[], errors=[], cleanup_verified=True)
        code, calls = self.run_main(CAPACITY_RAW, supervised)
        lines = self.journal_lines()
        self.assertEqual((code, calls, len(lines)), (0, ["capacity"], 1))
        record = json.loads(lines[0])
        self.assertEqual((record["status"], record["command"]), ("completed", "v0a_eval_panel run"))
        self.assertTrue(record["output"].startswith("experiments/results/runs/"))
        self.assertTrue((self.root / record["output"]).exists())
        self.assertIn("runtimes_sha256", record)

    def test_nonfinite_plan_starts_no_worker_and_still_records_one_failure(self):
        raw = CAPACITY_RAW.replace(b'"seconds": 600', b'"seconds": 1e999')
        code, calls = self.run_main(raw, dict(status="completed", observations=[], errors=[]))
        lines = self.journal_lines()
        self.assertEqual((code, calls, len(lines)), (1, [], 1))
        record = json.loads(lines[0])
        self.assertEqual(record["status"], "failed")
        result = json.loads((self.root / record["output"]).read_text(encoding="utf-8"))
        self.assertIn("nonfinite", json.dumps(result))

    def test_interrupted_supervisor_still_records_its_drained_observations(self):
        drained = [dict(kind="preflight", label="development", board=TOOL.DEVELOPMENT_BOARD,
                        hand="AsAd", stages={}, complete=False)]
        code, calls = self.run_main(CAPACITY_RAW, {"observations": drained, "errors": [],
                                                   "raise": KeyboardInterrupt()})
        lines = self.journal_lines()
        self.assertEqual((code, calls, len(lines)), (1, ["capacity"], 1))
        record = json.loads(lines[0])
        self.assertEqual(record["status"], "interrupted")
        result = json.loads((self.root / record["output"]).read_text(encoding="utf-8"))
        self.assertEqual(len(result["observations"]), 1)


class RealRunOwnershipTests(unittest.TestCase):
    """Real worker, native cleanup, publication and result owner in a disposable clone."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "snapshot"
        git = os.environ["PONTIUS_GIT"]
        commit = subprocess.run([git, "-C", str(ROOT), "rev-parse", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run([git, "clone", "--shared", "--no-checkout", str(ROOT), str(self.root)],
                       check=True, capture_output=True)
        subprocess.run([git, "-C", str(self.root), "checkout", "--detach", commit],
                       check=True, capture_output=True)
        name = "eval_panel_disposable_owner"
        spec = importlib.util.spec_from_file_location(name, self.root / "tools/v0a_eval_panel.py")
        self.tool = importlib.util.module_from_spec(spec)
        sys.modules[name] = self.tool
        self.addCleanup(sys.modules.pop, name, None)
        spec.loader.exec_module(self.tool)

    def run_and_read(self, plan):
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        before = self.root / "execution_journal.jsonl"
        old_lines = before.read_text().splitlines() if before.exists() else []
        with redirect_stdout(io.StringIO()):
            code = self.tool.main(["run", "--plan", str(plan_path)])
        lines = before.read_text().splitlines()
        self.assertEqual(len(lines), len(old_lines) + 1)
        entry = json.loads(lines[-1])
        self.assertTrue(entry["source_verified"])
        result_path = self.root / entry["output"]
        result = json.loads(result_path.read_text())
        self.assertEqual(entry["output_sha256"],
                         hashlib.sha256(result_path.read_bytes()).hexdigest())
        return code, result, result_path.parent

    def test_failed_last_release_cannot_certify_cleanup(self):
        host = self.tool.load_host()
        close = host.Job.close
        released = []

        def close_then_fail(job):
            close(job)  # Native close remains real; control the reported failure after release.
            released.append(job.handle is None)
            raise OSError("controlled post-release failure")

        with patch.object(host.Job, "close", close_then_fail):
            code, result, _ = self.run_and_read(CAPACITY)
        self.assertEqual(released, [True])
        self.assertEqual((code, result["status"]), (1, "failed"))
        self.assertFalse(result["cleanup_verified"], result["cleanup"])
        self.assertTrue(result["cleanup"]["close job"].startswith("OSError"))
        self.assertIsNotNone(result["worker_exit_code"])

    def test_declared_full_real_worker_and_estimator_use_the_same_roles(self):
        code, result, _ = self.run_and_read(PREFLIGHT)
        self.assertEqual((code, result["status"]), (0, "completed"), result)
        rows = result["observations"]
        development = [row for row in rows if row["label"] == "development"]
        controls = [row for row in rows if row["label"] == "control"]
        self.assertEqual({row["hand"] for row in development}, {"AdAs", "KdKh", "8dTd", "3c4d"})
        self.assertEqual(len(development), 4)
        self.assertTrue(all(row["board"] == ["2c", "7d", "9h", "Js", "Qc"]
                            and row["complete"] and not row["missing_stages"]
                            and row["stages"]["comparison"]["comparison"]["passed"]
                            for row in development))
        self.assertEqual([(row["board"], row["hand"]) for row in controls], [(ROYAL, "2c3d")])
        self.assertTrue(controls[0]["complete"])
        self.assertEqual((result["full_pool_estimate"]["kind"],
                          result["full_pool_estimate"]["sample"]), ("estimate", 4))

    def test_interrupt_after_cleanup_retains_real_drained_stages(self):
        host = self.tool.load_host()
        close = host.Job.close
        closed, interrupted = [], []

        def close_and_arm(job):
            close(job)
            closed.append(True)

        def interrupt_after_release(frame, event, arg):
            if (event == "line" and closed and not interrupted
                    and frame.f_code.co_name == "supervise"
                    and frame.f_code.co_filename == self.tool.__file__):
                interrupted.append(True)
                raise KeyboardInterrupt
            return interrupt_after_release

        previous = sys.gettrace()
        try:
            with patch.object(host.Job, "close", close_and_arm):
                sys.settrace(interrupt_after_release)
                code, result, _ = self.run_and_read(royal_subset(seconds=6))
        finally:
            sys.settrace(previous)
        self.assertEqual(interrupted, [True])
        self.assertEqual((code, result["status"]), (1, "interrupted"))
        rows = [row for row in result["observations"] if row["kind"] == "preflight"]
        self.assertEqual(len(rows), 1, result)
        self.assertIn("production", rows[0]["stages"])
        self.assertEqual(rows[0]["stages"]["production"]["production"]["check_total"], 0)

    def test_console_interrupt_cannot_race_a_true_cleanup_certificate(self):
        lines, first = inspect.getsourcelines(self.tool.supervise)
        assignment = first + next(index for index, line in enumerate(lines)
                                  if 'report["cleanup_verified"] = (' in line)
        stores = {item.offset for item in dis.get_instructions(self.tool.supervise)
                  if item.opname == "STORE_SUBSCR" and item.positions.lineno == assignment}
        # CPython can duplicate a finally body along normal and exceptional paths.
        self.assertTrue(stores, "cleanup certificate assignment was not located")
        interrupted = []

        def interrupt_at_store(frame, event, arg):
            if (frame.f_code.co_name == "supervise"
                    and frame.f_code.co_filename == self.tool.__file__):
                frame.f_trace_opcodes = True
                if event == "opcode" and frame.f_lasti in stores and not interrupted:
                    interrupted.append(True)
                    signal.raise_signal(signal.SIGINT)
            return interrupt_at_store

        previous = sys.gettrace()
        try:
            sys.settrace(interrupt_at_store)
            code, result, _ = self.run_and_read(CAPACITY)
        finally:
            sys.settrace(previous)
        self.assertEqual(interrupted, [True])
        self.assertEqual((code, result["status"]), (1, "interrupted"))
        self.assertFalse(result["cleanup_verified"], result["cleanup"])

    def test_interrupt_at_native_job_acquisition_still_releases_the_job(self):
        host = self.tool.load_host()
        native_job = host.Job
        acquired = []

        def acquire_then_interrupt(*args, **kwargs):
            job = native_job(*args, **kwargs)
            acquired.append(job)
            signal.raise_signal(signal.SIGINT)
            return job

        try:
            with patch.object(host, "Job", acquire_then_interrupt):
                code, result, _ = self.run_and_read(CAPACITY)
            released = [job.handle is None for job in acquired]
        finally:
            for job in acquired:
                if job.handle is not None:
                    job.close()  # Fixture owns any leak; never replay a raw native handle.
        self.assertEqual((code, result["status"]), (1, "interrupted"))
        self.assertEqual(released, [True], "acquired native Job escaped cleanup protection")
        self.assertEqual(result["cleanup"]["close job"], "ok")
        self.assertFalse(result["cleanup_verified"])

    def test_interrupt_after_native_rename_keeps_final_file_bound(self):
        replace = os.replace
        published = []

        def publish_then_interrupt(source, destination):
            replace(source, destination)
            if Path(destination).name.startswith("capacity-boundary-") and not published:
                published.append(Path(destination))
                raise KeyboardInterrupt

        with patch.object(os, "replace", publish_then_interrupt):
            code, result, directory = self.run_and_read(CAPACITY)
        self.assertEqual((code, result["status"]), (1, "interrupted"))
        self.assertEqual(len(published), 1)
        row = result["observations"][0]
        bindings = {value["path"]: value for value in row["boundary_artifacts"].values()}
        files = list(directory.glob("capacity-boundary-*.blueprint.json"))
        self.assertEqual(files, published)
        for path in files:
            self.assertIn(path.name, bindings)
            self.assertEqual(bindings[path.name]["bytes"], path.stat().st_size)
            self.assertEqual(bindings[path.name]["sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest())

    def test_pipe_close_is_bounded_while_a_real_writer_holds_the_lock(self):
        read_fd, write_fd = os.pipe()
        reader, writer = os.fdopen(read_fd, "rb"), os.fdopen(write_fd, "wb")
        entered, finished, drained = threading.Event(), threading.Event(), []
        payload = b"x" * 1_048_576

        def write():
            entered.set()
            try:
                writer.write(payload)
            finally:
                finished.set()

        writing = threading.Thread(target=write, daemon=True)
        writing.start()
        self.assertTrue(entered.wait(2))
        reading = threading.Thread(target=lambda: drained.append(reader.read()), daemon=True)
        try:
            with self.assertRaises(TimeoutError):
                self.tool.close_stream(writer, 0.02)
        finally:
            reading.start()  # Release actual pipe backpressure; the existing closer finishes.
            writing.join(timeout=5)
            reading.join(timeout=5)
            reader.close()
        self.assertTrue(finished.is_set())
        self.assertFalse(writing.is_alive() or reading.is_alive())
        self.assertTrue(writer.closed)
        self.assertEqual(drained, [payload])


if __name__ == "__main__":
    unittest.main()
