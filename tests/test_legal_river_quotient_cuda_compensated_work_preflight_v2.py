from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    recover_journal_bytes,
)
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result as reader
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner as runner
from tests import test_legal_river_quotient_cuda_compensated_work_preflight as legacy


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json"
)
_RUNNER = (
    _ROOT
    / "src/pontius/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py"
)
_READER = (
    _ROOT
    / "src/pontius/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2_result.py"
)
_CONTROLS = Path(__file__)
_V1_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl"
)
_RESERVED = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


def _git() -> dict[str, object]:
    return {
        "commit": "a" * 40,
        "dirty": False,
        "strict_status": True,
        "result_is_only_untracked_path": True,
        "tracked_prerequisites": True,
    }


def _child_handshake_event(challenge_digest: str) -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-bootstrap-handshake-v2",
        "challenge_sha256": challenge_digest,
        "literal_worker_module": runner.LITERAL_WORKER_MODULE,
        "spec_name": runner.LITERAL_WORKER_MODULE,
        "runtime_name": "__main__",
        "package_name": "pontius",
        "python_no_bytecode": True,
        "argv_count": 1,
        "cupy_loaded": False,
        "scientific_source_loaded": False,
    }


def _synthetic_handshake() -> runner.BootstrapHandshake:
    digest = sha256(b"h" * 32).hexdigest()
    return runner.BootstrapHandshake(
        event=_child_handshake_event(digest),
        expected_challenge_sha256=digest,
    )


def _synthetic_campaign(emit, _: int):
    return legacy._synthetic_events()(emit)


def _execute_synthetic(path: Path, **overrides):
    arguments = {
        "output_path": path,
        "git_loader": _git,
        "hashes_loader": runner.dependency_hashes,
        "v1_loader": runner.rebind_retained_v1,
        "handshake_executor": _synthetic_handshake,
        "campaign_executor": _synthetic_campaign,
        "reserved_path": path.parent / "reserved-absent.jsonl",
    }
    arguments.update(overrides)
    return runner.execute_owner_to_path(**arguments)


def _rewrite_journal(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        expected_campaign_sha256=runner.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    previous: str | None = None
    lines: list[bytes] = []
    for index, (record, payload) in enumerate(zip(recovery.records, payloads)):
        body = build_journal_record_body(
            protocol_sha256=runner.WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
            campaign_sha256=runner.WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
            kind=record.body.kind,
            sequence=index,
            previous_record_sha256=previous,
            semantic_identity_sha256=sha256(
                json.dumps(
                    payload,
                    allow_nan=False,
                    ensure_ascii=True,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("ascii")
            ).hexdigest(),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout: str,
        stderr: str = "",
        return_code: int | None = 0,
    ) -> None:
        self.stdout = io.StringIO(stdout)
        self.stderr = io.StringIO(stderr)
        self._return_code = return_code
        self._killed = False

    def poll(self):
        return -9 if self._killed else self._return_code

    def wait(self, timeout=None):
        del timeout
        if self._killed:
            return -9
        if self._return_code is None:
            raise subprocess.TimeoutExpired("fake", 0)
        return self._return_code

    def kill(self):
        self._killed = True


class WorkPreflightV2SourceSealTests(unittest.TestCase):
    def test_fresh_import_is_device_free_and_parent_rebinds(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner as r; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result; "
            "v=r.rebind_retained_v1(); "
            "print(int('cupy' in sys.modules), v.terminal, v.phase_count)"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="ascii",
        )
        self.assertEqual(completed.stdout.strip(), "0 infrastructure_failure 0")

    def test_config_and_additive_paths_rebind(self) -> None:
        loaded = runner.load_public_config()
        self.assertEqual(loaded.sha256, runner.PREREGISTERED_CONFIG_SHA256)
        self.assertEqual(reader.PREREGISTERED_CONFIG_SHA256, loaded.sha256)
        self.assertTrue(_RUNNER.is_file())
        self.assertTrue(_READER.is_file())
        self.assertTrue(_CONTROLS.is_file())
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())
        self.assertEqual(
            sha256(_V1_RESULT.read_bytes()).hexdigest(),
            "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830",
        )

    def test_source_is_additive_and_child_command_is_literal(self) -> None:
        source = _RUNNER.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn(
            "from .legal_river_quotient_cuda_compensated_work_preflight_runner",
            source,
        )
        self.assertNotIn('[sys.executable, "-B", "-m", __name__]', source)
        self.assertIn(
            '[sys.executable, "-B", "-m", LITERAL_WORKER_MODULE]', source
        )
        self.assertEqual(
            runner.LITERAL_WORKER_MODULE,
            "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner",
        )

    def test_real_no_cuda_handshake_crosses_literal_subprocess_seam(self) -> None:
        self.assertFalse(_RESULT.exists())
        handshake = runner.run_no_cuda_bootstrap_handshake()
        self.assertEqual(len(handshake.expected_challenge_sha256), 64)
        self.assertTrue(
            all(
                character in "0123456789abcdef"
                for character in handshake.expected_challenge_sha256
            )
        )
        self.assertEqual(
            handshake.event["challenge_sha256"],
            handshake.expected_challenge_sha256,
        )
        self.assertFalse(handshake.event["cupy_loaded"])
        self.assertFalse(handshake.event["scientific_source_loaded"])
        self.assertEqual(handshake.event["runtime_name"], "__main__")
        self.assertEqual(handshake.event["spec_name"], runner.LITERAL_WORKER_MODULE)
        self.assertFalse(_RESULT.exists())

    def test_handshake_rejects_wrong_challenge_and_import_claims(self) -> None:
        def wrong_challenge(mode, challenge, emit, wall):
            del mode, challenge, wall
            emit("bootstrap_handshake", _child_handshake_event("0" * 64))
            return {
                "schema_version": "legal-river-work-preflight-bootstrap-terminal-v2",
                "terminal": "bootstrap_handshake_pass",
                "passed": True,
            }

        with self.assertRaisesRegex(ValueError, "handshake contract differs"):
            runner.run_no_cuda_bootstrap_handshake(
                challenge_factory=lambda _: b"x" * 32,
                process_executor=wrong_challenge,
            )

        def imported(mode, challenge, emit, wall):
            del mode, wall
            assert challenge is not None
            event = _child_handshake_event(sha256(bytes.fromhex(challenge)).hexdigest())
            event["cupy_loaded"] = True
            emit("bootstrap_handshake", event)
            return {
                "schema_version": "legal-river-work-preflight-bootstrap-terminal-v2",
                "terminal": "bootstrap_handshake_pass",
                "passed": True,
            }

        with self.assertRaisesRegex(ValueError, "handshake contract differs"):
            runner.run_no_cuda_bootstrap_handshake(
                challenge_factory=lambda _: b"y" * 32,
                process_executor=imported,
            )

        def source_imported(mode, challenge, emit, wall):
            del mode, wall
            assert challenge is not None
            event = _child_handshake_event(sha256(bytes.fromhex(challenge)).hexdigest())
            event["scientific_source_loaded"] = True
            emit("bootstrap_handshake", event)
            return {
                "schema_version": "legal-river-work-preflight-bootstrap-terminal-v2",
                "terminal": "bootstrap_handshake_pass",
                "passed": True,
            }

        with self.assertRaisesRegex(ValueError, "handshake contract differs"):
            runner.run_no_cuda_bootstrap_handshake(
                challenge_factory=lambda _: b"z" * 32,
                process_executor=source_imported,
            )

    def test_transport_rejects_unframed_stdout_and_uses_literal_command(self) -> None:
        fake = _FakeProcess(stdout="unframed\n")
        with patch.object(runner.subprocess, "Popen", return_value=fake) as popen:
            with self.assertRaisesRegex(RuntimeError, "unframed"):
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1_000_000)
        command = popen.call_args.args[0]
        self.assertEqual(
            command,
            [sys.executable, "-B", "-m", runner.LITERAL_WORKER_MODULE],
        )

    def test_transport_bounds_stderr_and_types_timeout(self) -> None:
        fake = _FakeProcess(stdout="", stderr="z" * 10000, return_code=3)
        with patch.object(runner.subprocess, "Popen", return_value=fake):
            with self.assertRaises(RuntimeError) as captured:
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1_000_000)
        message = str(captured.exception)
        self.assertIn("exited 3", message)
        self.assertLessEqual(message.count("z"), runner.MAXIMUM_STDERR_CHARACTERS)

        hanging = _FakeProcess(stdout="", return_code=None)
        with (
            patch.object(runner.subprocess, "Popen", return_value=hanging),
            patch.object(runner, "perf_counter_ns", side_effect=[0, 2]),
        ):
            with self.assertRaisesRegex(TimeoutError, "child_wall_crossed"):
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1)

    def test_transport_rejects_malformed_and_post_terminal_events(self) -> None:
        malformed = _FakeProcess(stdout=runner._EVENT_PREFIX + "{}\n")
        with patch.object(runner.subprocess, "Popen", return_value=malformed):
            with self.assertRaisesRegex(RuntimeError, "event is malformed"):
                runner._run_child_process(
                    "handshake", "0" * 64, lambda *_: None, 1_000_000
                )

        terminal = json.dumps(
            {
                "kind": "child_terminal",
                "payload": {
                    "schema_version": (
                        "legal-river-work-preflight-bootstrap-terminal-v2"
                    ),
                    "terminal": "bootstrap_handshake_pass",
                    "passed": True,
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        event = json.dumps(
            {
                "kind": "bootstrap_handshake",
                "payload": _child_handshake_event("0" * 64),
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        post_terminal = _FakeProcess(
            stdout=(
                runner._EVENT_PREFIX
                + terminal
                + "\n"
                + runner._EVENT_PREFIX
                + event
                + "\n"
            )
        )
        with patch.object(runner.subprocess, "Popen", return_value=post_terminal):
            with self.assertRaisesRegex(RuntimeError, "event follows terminal"):
                runner._run_child_process(
                    "handshake", "0" * 64, lambda *_: None, 1_000_000
                )

    def test_synthetic_complete_owner_rebinds_through_v1_science(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.jsonl"
            execution = _execute_synthetic(path)
            self.assertEqual(execution.terminal["terminal"], "completed_capacity_pass")
            rebound = reader.rebind_work_preflight_v2_journal(path.read_bytes())
            self.assertTrue(rebound.passed)
            self.assertEqual(rebound.terminal, "completed_capacity_pass")
            self.assertIsNotNone(rebound.handshake)
            self.assertEqual(len(rebound.phases), 68)
            self.assertIsNotNone(rebound.projection)
            self.assertEqual(
                rebound.scientific_rebinding.terminal,
                "completed_capacity_pass",
            )

    def test_handshake_failure_is_durable_infrastructure_terminal(self) -> None:
        def fail_handshake():
            raise RuntimeError("synthetic bootstrap failure")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.jsonl"
            execution = _execute_synthetic(path, handshake_executor=fail_handshake)
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertFalse(execution.terminal["handshake_passed"])
            rebound = reader.rebind_work_preflight_v2_journal(path.read_bytes())
            self.assertEqual(rebound.terminal, "infrastructure_failure")
            self.assertIsNone(rebound.handshake)
            self.assertFalse(rebound.phases)
            self.assertIsNone(rebound.projection)

    def test_campaign_failure_stops_after_journaled_handshake(self) -> None:
        def fail_campaign(emit, wall):
            del emit, wall
            raise RuntimeError("synthetic campaign failure")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.jsonl"
            execution = _execute_synthetic(path, campaign_executor=fail_campaign)
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertTrue(execution.terminal["handshake_passed"])
            rebound = reader.rebind_work_preflight_v2_journal(path.read_bytes())
            self.assertIsNotNone(rebound.handshake)
            self.assertEqual(rebound.event_count, 2)

    def test_reader_rejects_rehashed_handshake_and_dependency_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.jsonl"
            _execute_synthetic(path)
            raw = path.read_bytes()

            def change_challenge(payloads):
                payloads[2]["event"]["child"]["challenge_sha256"] = "0" * 64

            with self.assertRaisesRegex(ValueError, "child-handshake contract differs"):
                reader.rebind_work_preflight_v2_journal(
                    _rewrite_journal(raw, change_challenge)
                )

            def change_dependency(payloads):
                payloads[1]["event"]["dependency_hashes"]["v2_runner"] = "0" * 64

            with self.assertRaisesRegex(ValueError, "dependency differs: v2_runner"):
                reader.rebind_work_preflight_v2_journal(
                    _rewrite_journal(raw, change_dependency)
                )

    def test_reader_rejects_science_before_handshake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.jsonl"
            _execute_synthetic(path)
            raw = path.read_bytes()

            def swap_handshake_and_science(payloads):
                left = payloads[2]
                right = payloads[3]
                left["event_kind"], right["event_kind"] = (
                    right["event_kind"],
                    left["event_kind"],
                )
                left["event"], right["event"] = right["event"], left["event"]

            with self.assertRaisesRegex(ValueError, "science precedes handshake"):
                reader.rebind_work_preflight_v2_journal(
                    _rewrite_journal(raw, swap_handshake_and_science)
                )

    def test_exclusive_replay_and_retained_v1_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "v2.jsonl"
            _execute_synthetic(path)
            with self.assertRaises(FileExistsError):
                _execute_synthetic(path)

            drifted = root / "v1.jsonl"
            drifted.write_bytes(_V1_RESULT.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "artifact differs"):
                runner.rebind_retained_v1(drifted)

    def test_torn_suffix_and_reserved_actual_presence_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "v2.jsonl"
            _execute_synthetic(path)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                reader.rebind_work_preflight_v2_journal(path.read_bytes() + b"{")

            reserved = root / "reserved.jsonl"
            reserved.write_bytes(b"reserved")
            called = 0

            def forbidden_handshake():
                nonlocal called
                called += 1
                return _synthetic_handshake()

            second = root / "reserved-breach.jsonl"
            execution = _execute_synthetic(
                second,
                reserved_path=reserved,
                handshake_executor=forbidden_handshake,
            )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertFalse(execution.terminal["handshake_passed"])
            self.assertEqual(called, 0)

    def test_public_owner_is_no_argument_and_real_result_remains_absent(self) -> None:
        tree = ast.parse(_RUNNER.read_text(encoding="utf-8"))
        main_functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        ]
        self.assertEqual(len(main_functions), 1)
        self.assertEqual(len(main_functions[0].args.args), 0)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())


if __name__ == "__main__":
    unittest.main()
