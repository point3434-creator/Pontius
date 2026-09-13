"""Behavioral contracts for the bounded four-arm experiment controller."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/2026-09-12-flop-coverage.py"


def experiment_module():
    spec = importlib.util.spec_from_file_location("flop_coverage_experiment", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FlopCoverageExperimentTests(unittest.TestCase):
    def test_calibration_repeats_real_save_when_an_earlier_reference_exists(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            experiment.atomic_json(run / "manifest.json", {"settings": experiment.SMOKE})
            trainer = experiment.make_trainer("A", 1101, experiment.SMOKE)
            for _ in range(experiment.SMOKE["calibration_iterations"]):
                trainer.step()
            earlier = run / "controls/resume-A"
            experiment.save_trainer(run, earlier, trainer, "live-reference")
            retained = {path: path.read_bytes() for path in earlier.rglob("checkpoint.json")}
            self.assertTrue(retained)
            environment = {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
            with patch.dict(os.environ, environment):
                experiment.calibration_worker(run)
            controls = experiment.read_json(run / "controls.json")
            self.assertTrue(controls["passed"])
            resume = controls["resumes"][0]
            self.assertGreater(resume["checkpoint_write_seconds"], 0)
            self.assertNotEqual(run / resume["checkpoint_directory"], earlier)
            for path, original in retained.items():
                self.assertEqual(path.read_bytes(), original)

    def test_exited_leader_still_receives_owned_group_cleanup(self):
        experiment = experiment_module()
        class ExitedLeader:
            pid = 987654

            def poll(self):
                return 0

        signals = []
        with patch.object(experiment.os, "name", "posix"), patch.object(
            experiment.os, "killpg", side_effect=lambda pid, sig: signals.append((pid, sig)),
            create=True,
        ):
            experiment.kill_group(ExitedLeader(), False)
        self.assertEqual(signals, [(987654, experiment.signal.SIGTERM)])

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires actual Linux process groups")
    def test_monitored_job_removes_helper_after_leader_exits(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            helper_pid = run / "helper.pid"
            leader = run / "leader.py"
            leader.write_text(
                "import subprocess, sys, pathlib, time\n"
                "child = subprocess.Popen([sys.executable, '-c', "
                "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "time.sleep(60)'])\n"
                f"pathlib.Path({str(helper_pid)!r}).write_text(str(child.pid))\n"
                "time.sleep(0.3)\n",
                encoding="utf-8",
            )
            experiment.atomic_json(run / "manifest.json", dict(
                settings=experiment.SMOKE | {"shutdown_seconds": 0.2},
                deadline_utc=time.time() + 30,
            ))
            try:
                with patch.object(experiment, "__file__", str(leader)):
                    outcome = experiment.monitored_job(run, "orphan", "calibrate", [], 20)
                self.assertEqual(outcome["returncode"], 0)
                pid = int(helper_pid.read_text())
                status = Path(f"/proc/{pid}/stat")
                self.assertTrue(not status.exists() or status.read_text().split(") ")[1][0] == "Z")
            finally:
                if helper_pid.exists():
                    try:
                        os.kill(int(helper_pid.read_text()), experiment.signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_calibration_node_cap_is_retained_and_controller_does_not_train(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            manifest = dict(settings=experiment.SMOKE | {"max_nodes": 1},
                            deadline_utc=time.time() + 120, started_utc=time.time())
            experiment.atomic_json(run / "manifest.json", manifest)
            try:
                with patch.dict(os.environ, {"PYTHONPATH": ""}):
                    experiment.calibration_worker(run)
            except experiment.SamplingLimit as error:
                self.fail(f"resource cap escaped without structured calibration outcome: {error}")
            controls = experiment.read_json(run / "controls.json")
            self.assertEqual(controls.get("status"), "capped")
            self.assertFalse(controls["passed"])
            self.assertIn("max_nodes", controls["stop"])
            self.assertEqual(controls["active"]["arms"], ["A", "B"])
            self.assertEqual(controls["active"]["common_iterations"], 0)
            self.assertEqual(controls["active"]["rows"], [0, 0])
            with patch.object(experiment, "ensure_run", return_value=(manifest, {})), patch.object(
                experiment, "finalize", side_effect=lambda run, report, *_: experiment.atomic_json(
                    run / "result.json", report
                )
            ):
                experiment.run_controller(run, "smoke", True)
            report = experiment.read_json(run / "result.json")
            self.assertEqual(report["status"], "capped")
            self.assertEqual(report["cells"], [])
            self.assertEqual(report["controls"], controls)

    def test_calibration_stop_is_structured_before_training(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            experiment.atomic_json(run / "manifest.json", {"settings": experiment.SMOKE})
            with patch.object(experiment, "STOP_REQUESTED", True):
                experiment.calibration_worker(run)
            controls = experiment.read_json(run / "controls.json")
            self.assertEqual(controls["status"], "capped")
            self.assertEqual(controls["stop"], "supervisor_stop")
            self.assertFalse(controls["passed"])

    def test_calibration_retains_row_time_memory_and_disk_limits(self):
        experiment = experiment_module()
        cases = [({"max_rows": 1}, None, "max_rows"),
                 ({}, time.time() - 1, "time_budget"),
                 ({"soft_memory_bytes": 1}, None, "soft_memory_budget"),
                 ({"disk_bytes": 2 * 1024 * 1024}, None, "disk_budget")]
        for overrides, deadline, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temporary:
                run = Path(temporary)
                manifest = {"settings": experiment.SMOKE | overrides}
                if deadline is not None:
                    manifest["deadline_utc"] = deadline
                experiment.atomic_json(run / "manifest.json", manifest)
                experiment.calibration_worker(run)
                controls = experiment.read_json(run / "controls.json")
                self.assertEqual(controls["status"], "capped")
                self.assertIn(reason, controls["stop"])

    def test_calibration_correctness_mismatch_is_failed_not_capped(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            experiment.atomic_json(run / "manifest.json", {"settings": experiment.SMOKE})
            with patch.object(experiment, "regret_state", side_effect=[{"changed": 1}, {}]):
                with self.assertRaisesRegex(AssertionError, "changed the regret path"):
                    experiment.calibration_worker(run)
            controls = experiment.read_json(run / "controls.json")
            self.assertEqual(controls["status"], "failed")
            self.assertFalse(controls["passed"])

    def test_costly_coverage_gain_is_not_practical_improvement(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            settings = experiment.SMOKE | {"seeds": [1, 2, 3]}
            for seed in settings["seeds"]:
                for arm, covered, cost in (("A", 10, 1), ("D", 20, 100)):
                    experiment.atomic_json(
                        run / "cells" / f"{arm}-{seed}" / "milestone-000100.json",
                        dict(iterations=100, coverage={"all": {
                            "repeat_averaged_rate": covered / 100, "repeat_averaged": covered}},
                            timers={"cpu_seconds": cost}, peak_self_rss_bytes=cost * experiment.GIB,
                            wall_seconds=cost),
                    )
            decision = experiment.coverage_decision(run, settings)
            self.assertTrue(decision["contrasts"]["D"]["coverage_gate_passed"])
            self.assertEqual(decision["contrasts"]["D"].get("practical_outcome"),
                             "no_practical_improvement")
            self.assertEqual(decision.get("practical_outcome"), "no_practical_improvement")
            for metric in ("cpu", "memory"):
                for seed in settings["seeds"]:
                    path = run / "cells" / f"D-{seed}" / "milestone-000100.json"
                    record = experiment.read_json(path)
                    record.update(timers={"cpu_seconds": 100 if metric == "cpu" else 1},
                                  peak_self_rss_bytes=(100 if metric == "memory" else 1)
                                  * experiment.GIB)
                    experiment.atomic_json(path, record)
                self.assertEqual(experiment.coverage_decision(run, settings)["practical_outcome"],
                                 "no_practical_improvement")
            # Complete cheap measurements support an engineering-only result.
            for seed in settings["seeds"]:
                path = run / "cells" / f"D-{seed}" / "milestone-000100.json"
                record = experiment.read_json(path)
                record.update(timers={"cpu_seconds": 1}, peak_self_rss_bytes=experiment.GIB)
                experiment.atomic_json(path, record)
            self.assertEqual(experiment.coverage_decision(run, settings)["practical_outcome"],
                             "useful_engineering_progress")
            for arm in ("A", "D"):
                path = run / "cells" / f"{arm}-3" / "milestone-000100.json"
                record = experiment.read_json(path)
                record["iterations"] = 50
                experiment.atomic_json(path, record)
                path.rename(path.with_name("milestone-000050.json"))
            self.assertEqual(experiment.coverage_decision(run, settings)["practical_outcome"],
                             "insufficient_measurements")
            for arm in ("A", "D"):
                path = run / "cells" / f"{arm}-3" / "milestone-000050.json"
                record = experiment.read_json(path)
                record["iterations"] = 100
                experiment.atomic_json(path, record)
                path.rename(path.with_name("milestone-000100.json"))
            path = run / "cells/D-3/milestone-000100.json"
            record = experiment.read_json(path)
            record["timers"]["incomplete_after_restart"] = True
            experiment.atomic_json(path, record)
            decision = experiment.coverage_decision(run, settings)
            self.assertTrue(decision["contrasts"]["D"]["coverage_gate_passed"])
            self.assertEqual(decision["practical_outcome"], "insufficient_measurements")
            record.pop("timers")
            experiment.atomic_json(path, record)
            self.assertEqual(experiment.coverage_decision(run, settings)["practical_outcome"],
                             "insufficient_measurements")
            path.unlink()
            self.assertEqual(experiment.coverage_decision(run, settings)["practical_outcome"],
                             "insufficient_measurements")

    def test_twenty_sample_distribution_keeps_iteration_spread_and_visit_weights(self):
        from pontius.sampled_cfr import RegretRow

        experiment = experiment_module()
        rows = {key: RegretRow(0, ("check",), [0.0], [1.0], average_visits=visits,
                              average_samples=20)
                for key, visits in (("narrow", 3), ("wide", 20))}
        observations = [dict(profile="passive", live=6, keys={"exact": key}, actions=["check"])
                        for key in ("narrow", "narrow", "wide")]
        result = experiment.coverage_summary(rows, observations, "exact")
        for group in ("all", "passive", "four_to_six", "passive/four_to_six"):
            self.assertEqual(result[group].get("at_least_20_samples_iteration_histogram"),
                             {"3": 2, "20": 1})
        self.assertEqual(result["heads_up"].get("at_least_20_samples_iteration_histogram"), {})

    def test_expired_run_cannot_spend_a_new_budget_building_panels_after_restart(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            experiment.atomic_json(
                run / "manifest.json",
                {"settings": experiment.SMOKE, "deadline_utc": time.time() - 1},
            )
            with self.assertRaises(experiment.ExperimentLimit):
                experiment.prepare_panels(run, experiment.SMOKE)
            self.assertFalse((run / "panels.json").exists())

    def test_key_timing_adapter_preserves_complete_training_state(self):
        experiment = experiment_module()
        game = experiment.game_for("D")
        timing = experiment.KeyTimer(game)
        timed = experiment.make_trainer("D", 1101, experiment.SMOKE, timing.sample_root)
        ordinary = experiment.make_trainer("D", 1101, experiment.SMOKE)
        for _ in range(3):
            timed.step()
            ordinary.step()
        self.assertEqual(timed.state_dict(), ordinary.state_dict())
        self.assertGreater(timing.calls, 0)

    def test_second_controller_is_rejected_until_first_releases_the_run(self):
        experiment = experiment_module()
        self.assertTrue(hasattr(experiment, "controller_lock"), "exclusive controller is absent")
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            with experiment.controller_lock(run):
                with self.assertRaises(RuntimeError):
                    with experiment.controller_lock(run):
                        self.fail("second writer entered the same run")
            with experiment.controller_lock(run):
                self.assertTrue((run / ".controller.lock").exists())

    def test_panel_metadata_recovers_after_panel_publication_before_metadata(self):
        experiment = experiment_module()
        self.assertTrue(hasattr(experiment, "prepare_panels"), "panel recovery is absent")
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            experiment.atomic_json(run / "manifest.json", {"settings": experiment.SMOKE})
            panels = experiment.make_panels(experiment.SMOKE)
            experiment.atomic_json(run / "panels.json", panels, immutable=True)
            before = (run / "panels.json").read_bytes()
            metadata = experiment.prepare_panels(run, experiment.SMOKE)
            self.assertEqual(metadata["sha256"], experiment.file_digest(run / "panels.json"))
            self.assertEqual((run / "panels.json").read_bytes(), before)

    def test_bootstrap_keeps_deal_block_means_as_sampling_units(self):
        experiment = experiment_module()
        result = experiment.bootstrap_interval([2.0] * 8, seed=7, repetitions=100)
        self.assertEqual(result["mean_bb_per_hand"], 2.0)
        self.assertEqual(result["ci95_bb_per_hand"], [2.0, 2.0])
        self.assertEqual(result["independent_deal_blocks"], 8)
        with self.assertRaises(ValueError):
            experiment.bootstrap_interval([1.0], seed=7, repetitions=100)

    def test_disk_reservation_fails_before_writing_an_oversized_artifact(self):
        experiment = experiment_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "retained").write_bytes(b"old milestone")
            with self.assertRaises(experiment.ExperimentLimit):
                experiment.atomic_json(
                    root / "large.json", {"value": "x" * 1000}, budget_root=root, disk_limit=100
                )
            self.assertFalse((root / "large.json").exists())
            self.assertEqual((root / "retained").read_bytes(), b"old milestone")

    def test_fixed_panel_counts_repeated_iterations_separately_from_samples(self):
        from pontius.sampled_cfr import RegretRow

        experiment = experiment_module()
        rows = {
            "one": RegretRow(
                0,
                ("check",),
                [0.0],
                [1.0],
                average_visits=1,
                average_samples=8,
                regret_visits=0,
                average_regret_samples=0,
            ),
            "two": RegretRow(
                0,
                ("check",),
                [1.0],
                [2.0],
                average_visits=2,
                average_samples=20,
                regret_visits=1,
                average_regret_samples=10,
            ),
        }
        observations = [
            {"profile": "passive", "live": 6, "keys": {"exact": key}, "actions": ["check"]}
            for key in ("missing", "one", "two", "two")
        ]
        result = experiment.coverage_summary(rows, observations, "exact")
        total = result["all"]
        self.assertEqual(total["observations"], 4)
        self.assertEqual(total["missing"], 1)
        self.assertEqual(total["averaged"], 3)
        self.assertEqual(total["repeat_averaged"], 2)
        self.assertEqual(total["at_least_20_samples"], 2)
        self.assertEqual(total["repeat_averaged_rate"], 0.5)

    def test_tiny_four_arm_run_retains_panels_and_does_not_retrain_terminal_run(self):
        # Reduced settings exercise the same controller, worker and evaluation paths.
        self.assertTrue(SCRIPT.is_file(), "Four-arm experiment driver is not implemented")
        with tempfile.TemporaryDirectory(dir=ROOT / "experiments/results") as temporary:
            run = Path(temporary) / "smoke"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            command = [
                sys.executable,
                str(SCRIPT),
                "run",
                "--profile",
                "smoke",
                "--development",
                "--run-directory",
                str(run),
            ]
            first = subprocess.run(
                command, env=environment, cwd=ROOT, capture_output=True, text=True, timeout=180
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            report = json.loads((run / "result.json").read_text())
            self.assertEqual(report["status"], "passed")
            self.assertEqual({cell["arm"] for cell in report["cells"]}, set("ABCD"))
            self.assertEqual(len({cell["identity"] for cell in report["cells"]}), 4)
            self.assertTrue(report["controls"]["passed"])
            for resume in report["controls"]["resumes"]:
                for phase in ("save", "load"):
                    self.assertIn(phase + "_seconds", resume)
                    self.assertGreaterEqual(resume[phase + "_seconds"], 0)
                    measurement = resume[phase + "_memory"]
                    self.assertGreater(measurement["sampled_peak_rss_bytes"], 0)
                    self.assertGreater(measurement["samples"], 0)
                    self.assertGreater(measurement["sample_interval_seconds"], 0)
                self.assertNotEqual(resume["load_memory"]["observed_pid"],
                                    resume["save_memory"]["observed_pid"])
            self.assertTrue(report["evaluation"]["complete"])
            self.assertFalse(report["production_promotion"])
            retained = {
                str(path.relative_to(run)): path.read_bytes()
                for path in run.rglob("checkpoint.json")
            }
            self.assertGreaterEqual(len(retained), 12)
            panel_hash = report["panels_sha256"]
            second = subprocess.run(
                command, env=environment, cwd=ROOT, capture_output=True, text=True, timeout=15
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(
                json.loads((run / "result.json").read_text())["panels_sha256"], panel_hash
            )
            for relative, before in retained.items():
                self.assertEqual((run / relative).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
