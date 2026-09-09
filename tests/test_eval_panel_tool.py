"""Plan refusal, worker phases, budget stop, and one-run ownership of the panel tool."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eval_panel_tool_tests", ROOT / "tools/v0a_eval_panel.py")
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
FIXTURES = ROOT / "tests/fixtures/eval_panel"
CAPACITY = json.loads((FIXTURES / "plan-capacity.json").read_text(encoding="utf-8"))
PREFLIGHT = json.loads((FIXTURES / "plan-preflight.json").read_text(encoding="utf-8"))
ROYAL = ["Ts", "Js", "Qs", "Ks", "As"]


def collect(plan, seconds=600):
    events = []
    TOOL.run_plan(TOOL.validate_plan(plan), events.append, time.perf_counter() + seconds)
    return events


def altered(plan, path, value):
    plan = copy.deepcopy(plan)
    target = plan
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    return plan


class PlanTests(unittest.TestCase):
    def test_every_mandatory_input_is_refused_when_missing_or_wrong(self):
        TOOL.validate_plan(CAPACITY)
        TOOL.validate_plan(PREFLIGHT)
        wrong = (
            (("version",), "other"), (("phase",), "export"), (("stacks",), 1),
            (("board",), list(reversed(CAPACITY["board"]))), (("pool_seed",), "ab" * 31),
            (("resource", "seconds"), 0), (("resource",), None),
        )
        for path, value in wrong:
            with self.assertRaises(ValueError, msg=path):
                TOOL.validate_plan(altered(CAPACITY, path, value))
        for field in ("development_hands", "controls"):
            plan = copy.deepcopy(PREFLIGHT)
            del plan[field]
            with self.assertRaises(ValueError, msg=field):
                TOOL.validate_plan(plan)


class WorkerTests(unittest.TestCase):
    def test_capacity_phase_reports_the_frozen_permutation(self):
        events = collect(CAPACITY)
        self.assertEqual([event["event"] for event in events], ["ready", "observation"])
        observation = events[1]
        self.assertEqual(len(observation["permutation"]), 1081)
        self.assertEqual(len(set(observation["permutation"])), 1081)
        self.assertEqual(observation["probe"]["cap"], 1048576)
        self.assertTrue(0 < observation["probe"]["largest_fitting"] <= 1081)

    def test_preflight_control_passes_and_reports_separate_costs(self):
        plan = altered(PREFLIGHT, ("development_hands",), [["2c", "3d"]])
        plan = altered(altered(plan, ("board",), ROYAL), ("controls",), [])
        events = collect(plan)
        self.assertEqual([event["event"] for event in events], ["ready", "observation"])
        observation = events[1]
        self.assertTrue(observation["comparison"]["passed"], observation["comparison"])
        for name in ("production_cost", "reference_construction_cost", "forced_values_cost",
                     "best_response_cost", "comparison_cost"):
            self.assertIn("elapsed_seconds", observation[name], name)
        self.assertIn("hits", observation["cache_before"])

    def test_exhausted_budget_stops_before_the_next_hand(self):
        events = collect(PREFLIGHT, seconds=0)
        self.assertEqual([event["event"] for event in events], ["ready", "failed"])
        self.assertIn("budget exhausted", events[1]["error"])


class OwnershipTests(unittest.TestCase):
    def test_run_records_once_with_an_output_directory(self):
        calls = []
        context = dict(commit="c" * 40, source_sha256="s" * 64, verified=True, root=str(ROOT))
        supervised = dict(status="completed", observations=[], errors=[])
        with patch.object(TOOL, "begin_run", return_value=context), \
                patch.object(TOOL, "supervise", return_value=supervised), \
                patch.object(TOOL, "finish_run", side_effect=lambda *args: calls.append(args)), \
                patch.object(Path, "mkdir"), patch.object(Path, "write_text"):
            code = TOOL.main(["run", "--plan", str(FIXTURES / "plan-capacity.json")])
        self.assertEqual((code, len(calls)), (0, 1))
        recorded_context, command, report, _ = calls[0]
        output_directory = recorded_context["output_directory"]
        self.assertTrue(output_directory.startswith("experiments/results/runs/"))
        self.assertEqual((command, report["status"], report["phase"]),
                         ("v0a_eval_panel run", "completed", "capacity"))


if __name__ == "__main__":
    unittest.main()
