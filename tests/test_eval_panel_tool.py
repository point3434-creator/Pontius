"""Plan admission, worker phases, the real supervisor, and one-run ownership of the tool."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

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
        from pontius import eval_bridge as bridge
        names = [bridge.hand_name(hand) for _, hand in TOOL.declared_sample(bridge)[:4]]
        rows = [dict(kind="preflight", label="development", board=TOOL.DEVELOPMENT_BOARD,
                     hand=name, complete=True,
                     stages=dict(production=dict(cost=dict(elapsed_seconds=0.5))))
                for name in names]
        estimate = TOOL.full_pool_estimate(rows, 1081, "declared-full")
        self.assertEqual((estimate["kind"], estimate["sample"]), ("estimate", 4))
        rows[3]["complete"] = False
        partial = TOOL.full_pool_estimate(rows, 1081, "declared-full")
        self.assertEqual(partial["kind"], "not_estimated")
        self.assertIn(names[3], partial["reason"])
        self.assertEqual(TOOL.full_pool_estimate(rows, 1081, "test-subset")["kind"],
                         "not_estimated")
        self.assertIsNone(TOOL.full_pool_estimate(rows, 1081, None))

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
            calls.append(plan["phase"])
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


if __name__ == "__main__":
    unittest.main()
