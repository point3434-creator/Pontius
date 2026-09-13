"""Behavioral checks for the Linux service launcher; no host service mutations."""

import configparser
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/run_flop_coverage_server.py"
SHA = "a" * 40


def launcher():
    spec = importlib.util.spec_from_file_location("flop_server", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FlopCoverageServerTests(unittest.TestCase):
    def test_print_unit_is_nonmutating_and_round_trips_controller_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = (Path(temporary) / "repo with spaces").resolve()
            repo.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(repo / ".." / repo.name),
                    "--run-name",
                    "coverage-1101",
                    "--reviewed-commit",
                    SHA,
                    "--print-unit",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = configparser.ConfigParser(interpolation=None)
            config.read_string(result.stdout)
            service = config["Service"]
            arguments = shlex.split(service["ExecStart"])
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import json,sys;print(json.dumps(sys.argv[1:]))",
                    *arguments,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(
                json.loads(probe.stdout),
                [
                    sys.executable,
                    str(repo / "experiments/2026-09-12-flop-coverage.py"),
                    "run",
                    "--profile",
                    "full",
                    "--run-directory",
                    str(repo / "experiments/results/runs/coverage-1101"),
                    "--reviewed-commit",
                    SHA,
                ],
            )
            self.assertEqual(service["MemoryMax"], "16G")
            self.assertEqual(service["MemorySwapMax"], "0")
            self.assertEqual(service["OOMPolicy"], "continue")
            self.assertEqual(service["KillMode"], "control-group")
            self.assertEqual(service["RuntimeMaxSec"], "21600")
            self.assertEqual(service["TimeoutStopSec"], "30")
            self.assertEqual(service["Restart"], "on-failure")
            self.assertGreater(int(service["RestartSec"]), 0)
            self.assertGreater(int(config["Unit"]["StartLimitIntervalSec"]), 21600)
            self.assertLessEqual(int(config["Unit"]["StartLimitBurst"]), 5)
            self.assertEqual(service["StandardOutput"], "journal")
            self.assertEqual(service["StandardError"], "journal")
            self.assertEqual(config["Install"]["WantedBy"], "multi-user.target")
            environment = shlex.split(service["Environment"])
            self.assertIn("PYTHONPATH=" + str(repo / "src") + ":" + str(repo), environment)
            self.assertEqual(list(repo.iterdir()), [])

    def test_invalid_identity_fails_before_render(self):
        for name, commit in [
            ("../escape", SHA),
            ("a.service", SHA),
            ("-bad", SHA),
            ("UPPER", SHA),
            ("a\nExecStart=bad", SHA),
            ("ok", "HEAD"),
        ]:
            with self.subTest(name=name, commit=commit):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--run-name",
                        name,
                        "--reviewed-commit",
                        commit,
                        "--print-unit",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("error:", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_platform_resource_gate_rejects_each_missing_requirement(self):
        module = launcher()
        valid = dict(
            platform_name="linux",
            implementation="CPython",
            version=(3, 14),
            in_venv=True,
            uid=0,
            free_bytes=100 * 1024**3,
            systemd=True,
            controllers={"memory", "cpu"},
        )
        module.validate_host(**valid)
        for change in [
            dict(platform_name="win32"),
            dict(implementation="PyPy"),
            dict(version=(3, 13)),
            dict(in_venv=False),
            dict(uid=1000),
            dict(free_bytes=100 * 1024**3 - 1),
            dict(systemd=False),
            dict(controllers={"cpu"}),
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.validate_host(**(valid | change))

    def test_existing_run_and_unit_are_never_overwritten(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run, unit = root / "run", root / "unit.service"
            module.validate_availability(run, unit, [])
            run.mkdir()
            with self.assertRaises(ValueError):
                module.validate_availability(run, unit, [])
            run.rmdir()
            unit.write_text("retained")
            with self.assertRaises(ValueError):
                module.validate_availability(run, unit, [])
            self.assertEqual(unit.read_text(), "retained")

    def test_competing_active_or_starting_units_are_rejected(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for state in ("active", "activating", "reloading", "deactivating"):
                with self.subTest(state=state), self.assertRaises(ValueError):
                    module.validate_availability(
                        root / "run",
                        root / "unit",
                        [{"unit": "pontius-flop-coverage-old.service", "active": state}],
                    )
            module.validate_availability(
                root / "run",
                root / "unit",
                [{"unit": "pontius-flop-coverage-old.service", "active": "failed"}],
            )

    def test_failed_unit_verification_does_not_install_or_enable(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            unit = Path(temporary) / "job.service"
            with patch.object(module, "run_command", side_effect=ValueError("unsupported")):
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    module.install_unit(unit, "[Service]\nExecStart=/bin/true\n")
            self.assertFalse(unit.exists())

    def test_install_publishes_verified_unit_before_enabling_and_checks_activation(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            unit = Path(temporary) / "job.service"
            text = module.unit_text(ROOT, "job", SHA)
            commands = []

            def system_boundary(arguments):
                commands.append(arguments)
                if arguments[0] == "systemd-analyze":
                    self.assertFalse(unit.exists())
                    candidate = Path(arguments[-1])
                    self.assertEqual(candidate.name, "job.service")
                    self.assertEqual(candidate.read_text(), text)
                else:
                    self.assertEqual(unit.read_text(), text)
                return subprocess.CompletedProcess(arguments, 0, "", "")

            with patch.object(module, "run_command", side_effect=system_boundary):
                module.install_unit(unit, text)
            self.assertEqual(
                commands[1:],
                [
                    ["systemctl", "daemon-reload"],
                    ["systemctl", "enable", "--now", "job.service"],
                    ["systemctl", "is-enabled", "job.service"],
                    ["systemctl", "is-active", "job.service"],
                ],
            )

    def test_unit_parser_warning_is_fatal_even_when_verify_exits_zero(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            unit = Path(temporary) / "job.service"
            result = subprocess.CompletedProcess([], 0, "", "Unknown key: MemorySwapMax")
            with patch.object(module, "run_command", return_value=result):
                with self.assertRaisesRegex(ValueError, "diagnostics"):
                    module.install_unit(unit, "[Service]\nExecStart=/bin/true\n")
            self.assertFalse(unit.exists())

    @unittest.skipIf(sys.platform == "linux", "Windows-only host rejection check")
    def test_real_install_invocation_refuses_non_linux_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    temporary,
                    "--run-name",
                    "job",
                    "--reviewed-commit",
                    SHA,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("installation requires Linux", result.stderr)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_source_identity_uses_real_git_and_rejects_modified_or_untracked_code(self):
        module = launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
                ).stdout.strip()

            git("init")
            (root / "code.py").write_text("reviewed = True\n")
            (root / "STATUS.md").write_text("before")
            git("add", ".")
            git(
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "fixture",
            )
            commit = git("rev-parse", "HEAD")
            module.validate_source(root, commit)
            (root / "STATUS.md").write_text("generated status")
            module.validate_source(root, commit)
            with self.assertRaises(ValueError):
                module.validate_source(root, "f" * 40)
            (root / "code.py").write_text("reviewed = False\n")
            with self.assertRaises(ValueError):
                module.validate_source(root, commit)
            git("checkout", "--", "code.py")
            (root / "unreviewed.py").write_text("pass\n")
            with self.assertRaises(ValueError):
                module.validate_source(root, commit)


if __name__ == "__main__":
    unittest.main()
