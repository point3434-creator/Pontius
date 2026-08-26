from __future__ import annotations

import ast
import copy
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pontius import legal_river_exact_cubin_inspector_diagnostic as diagnostic
from pontius import legal_river_exact_cubin_inspector_diagnostic_result as reader
from pontius import legal_river_exact_cubin_inspector_diagnostic_runner as runner


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / runner.RESULT_RELATIVE_PATH
_RESERVED = _ROOT / runner.RESERVED_ACTUAL_RESULT_RELATIVE_PATH


def _collect_protocol_events() -> tuple[list[tuple[str, dict[str, object]]], dict[str, object]]:
    events: list[tuple[str, dict[str, object]]] = []

    def emit(kind: str, event: object) -> None:
        if not isinstance(event, dict):
            event = dict(event)  # type: ignore[arg-type]
        events.append((kind, copy.deepcopy(event)))

    terminal = dict(runner.run_device_free_protocol_probe(emit))
    return events, terminal


def _execute_synthetic(
    events: list[tuple[str, dict[str, object]]],
    terminal: dict[str, object],
) -> tuple[runner.OwnerExecution, bytes]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagnostic.jsonl"

        def campaign(emit, _wall):
            for kind, event in copy.deepcopy(events):
                emit(kind, event)
            return copy.deepcopy(terminal)

        execution = runner.execute_owner_to_path(
            output_path=path,
            git_loader=lambda: {
                "commit": "a" * 40,
                "dirty": False,
                "strict_status": True,
            },
            campaign_executor=campaign,
            reserved_path=_RESERVED,
        )
        return execution, path.read_bytes()


class ExactCubinInspectorDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol_events, cls.protocol_terminal = _collect_protocol_events()

    def test_preregistered_contract_and_source_seal_paths(self) -> None:
        config_path = _ROOT / diagnostic.CONFIG_RELATIVE_PATH
        raw = config_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(sha256(raw).hexdigest(), diagnostic.CONFIG_SHA256)
        config = json.loads(raw)
        self.assertEqual(len(config["candidate_commands_in_order"]), 5)
        self.assertIsNone(
            config["candidate_interpretation_contract"]["selected_inspector"]
        )
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())
        self.assertEqual(len(inspect.signature(runner.main).parameters), 0)

    def test_fresh_import_is_cupy_and_science_free(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_exact_cubin_inspector_diagnostic_runner; "
            "import pontius.legal_river_exact_cubin_inspector_diagnostic_result; "
            "print(int('cupy' in sys.modules)); "
            "print(int('pontius.legal_river_quotient_cuda_compensated_work_preflight' in sys.modules))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
            env={**dict(__import__("os").environ), "PYTHONPATH": f"{_ROOT / 'src'};{_ROOT}"},
        )
        self.assertEqual(completed.stdout.splitlines(), ["0", "0"])

    def test_static_call_graph_forbids_calibration_and_consumed_owners(self) -> None:
        paths = (
            _ROOT / "src/pontius/legal_river_exact_cubin_inspector_diagnostic.py",
            _ROOT / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_runner.py",
        )
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = {
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
            }
            self.assertNotIn("run_calibration_preflight", calls)
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            self.assertFalse(
                any("work_preflight_v" in name and "diagnostic" not in name for name in imports)
            )
        diagnostic_tree = ast.parse(paths[0].read_text(encoding="utf-8"))
        attrs = {
            node.attr for node in ast.walk(diagnostic_tree) if isinstance(node, ast.Attribute)
        }
        self.assertIn("_kernels", attrs)
        self.assertNotIn("compile_using_nvrtc", attrs)

    def test_binary_envelope_is_lossless_for_non_utf8_and_nul(self) -> None:
        raw = b"\x00\xff\xfe\x80binary\x00"
        encoded = diagnostic.encode_binary(raw)
        decoded = reader.decode_binary(encoded, label="control")
        self.assertEqual(decoded.raw, raw)
        self.assertEqual(decoded.sha256, sha256(raw).hexdigest())
        for field, replacement in (
            ("byte_count", len(raw) + 1),
            ("sha256", "0" * 64),
            ("base64", encoded["base64"] + "A"),
            ("encoding", "utf8"),
        ):
            mutated = dict(encoded)
            mutated[field] = replacement
            with self.assertRaises((TypeError, ValueError)):
                reader.decode_binary(mutated, label="mutated")

    def test_bounded_command_retains_nonzero_binary_streams(self) -> None:
        code = (
            "import os,sys;"
            "os.write(sys.stdout.fileno(),b'\\x00\\xffout');"
            "os.write(sys.stderr.fileno(),b'\\xfe\\x00err');"
            "raise SystemExit(7)"
        )
        capture = diagnostic.run_bounded_binary_command(
            [sys.executable, "-B", "-c", code], wall_limit_ns=5_000_000_000
        )
        self.assertEqual(capture.status, "completed")
        self.assertEqual(capture.return_code, 7)
        self.assertEqual(capture.stdout, b"\x00\xffout")
        self.assertEqual(capture.stderr, b"\xfe\x00err")

    def test_bounded_command_timeout_and_output_limit_are_typed(self) -> None:
        timeout = diagnostic.run_bounded_binary_command(
            [sys.executable, "-B", "-c", "import time; time.sleep(1)"],
            wall_limit_ns=50_000_000,
            stream_limit=64,
        )
        self.assertEqual(timeout.status, "timeout")
        output = diagnostic.run_bounded_binary_command(
            [
                sys.executable,
                "-B",
                "-c",
                "import os,sys; os.write(sys.stdout.fileno(),b'x'*4096); os.write(sys.stderr.fileno(),b'y'*4096)",
            ],
            wall_limit_ns=5_000_000_000,
            stream_limit=64,
        )
        self.assertEqual(output.status, "output_limit")
        self.assertLessEqual(len(output.stdout), 64)
        self.assertLessEqual(len(output.stderr), 64)

    def test_literal_protocol_probe_crosses_ack_transport_without_cuda(self) -> None:
        kinds = [kind for kind, _ in self.protocol_events]
        self.assertEqual(
            kinds,
            [
                "bootstrap_handshake",
                "compiler_capture",
                *(["candidate_command"] * 5),
                "cleanup",
                "terminal_evidence",
            ],
        )
        handshake = self.protocol_events[0][1]
        self.assertFalse(handshake["cupy_loaded"])
        self.assertFalse(handshake["scientific_source_loaded"])
        self.assertTrue(self.protocol_terminal["passed"])
        returns = [event["return_code"] for kind, event in self.protocol_events if kind == "candidate_command"]
        self.assertEqual(returns, [1, 2, 3, 4, 5])
        self.assertFalse(_RESULT.exists())

    def test_literal_child_deadline_survives_silent_open_stdout(self) -> None:
        events: list[tuple[str, object]] = []
        with self.assertRaises(TimeoutError):
            runner.run_child_process(
                mode="protocol_hang_after_handshake",
                emit=lambda kind, event: events.append((kind, event)),
                wall_limit_ns=1_000_000_000,
            )
        self.assertEqual([kind for kind, _ in events], ["bootstrap_handshake"])

    def test_literal_child_post_terminal_frame_is_rejected(self) -> None:
        events: list[tuple[str, object]] = []
        with self.assertRaisesRegex(RuntimeError, "after terminal"):
            runner.run_child_process(
                mode="protocol_emit_after_terminal",
                emit=lambda kind, event: events.append((kind, event)),
                wall_limit_ns=5_000_000_000,
            )
        self.assertEqual(
            [kind for kind, _ in events],
            ["bootstrap_handshake", "terminal_evidence"],
        )

    def test_complete_synthetic_journal_rebinds_and_selects_nothing(self) -> None:
        execution, raw = _execute_synthetic(
            self.protocol_events, self.protocol_terminal
        )
        self.assertEqual(execution.terminal["terminal"], "capture_complete")
        rebound = reader.rebind_exact_cubin_diagnostic_journal(raw)
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.event_count, 10)
        self.assertIsNotNone(rebound.cubin)
        self.assertEqual(len(rebound.candidates), 5)
        self.assertEqual(
            [candidate.return_code for candidate in rebound.candidates],
            [1, 2, 3, 4, 5],
        )
        self.assertTrue(all(candidate.status == "completed" for candidate in rebound.candidates))

    def test_worker_failure_before_compiler_is_durable_and_rebinds(self) -> None:
        handshake = copy.deepcopy(self.protocol_events[0])
        failure = (
            "worker_failure",
            {
                "schema_version": "legal-river-exact-cubin-diagnostic-worker-failure-v1",
                "reason": "RuntimeError: synthetic compile failure",
            },
        )
        terminal = {
            "schema_version": "legal-river-exact-cubin-diagnostic-terminal-evidence-v1",
            "terminal": "diagnostic_failure",
            "passed": False,
            "reason": "synthetic failure retained",
            "candidate_events_retained": 0,
            "selected_inspector": None,
            "resource_gate_result": None,
            "calibration_result": None,
            "capacity_projection": None,
        }
        execution, raw = _execute_synthetic(
            [handshake, failure, ("terminal_evidence", terminal)], terminal
        )
        self.assertEqual(execution.terminal["terminal"], "diagnostic_failure")
        rebound = reader.rebind_exact_cubin_diagnostic_journal(raw)
        self.assertFalse(rebound.passed)
        self.assertIsNone(rebound.cubin)
        self.assertEqual(rebound.candidates, ())

    def test_semantic_binary_and_candidate_mutations_fail_closed(self) -> None:
        cases: list[list[tuple[str, dict[str, object]]]] = []
        bad_cubin = copy.deepcopy(self.protocol_events)
        bad_cubin[1][1]["cubin"]["sha256"] = "0" * 64  # type: ignore[index]
        cases.append(bad_cubin)
        bad_runtime = copy.deepcopy(self.protocol_events)
        bad_runtime[1][1]["runtime"]["device_total_bytes"] = "0"  # type: ignore[index]
        cases.append(bad_runtime)
        bad_order = copy.deepcopy(self.protocol_events)
        bad_order[2], bad_order[3] = bad_order[3], bad_order[2]
        cases.append(bad_order)
        bad_cleanup = copy.deepcopy(self.protocol_events)
        bad_cleanup[-2][1]["temporary_cubin_removed"] = False
        cases.append(bad_cleanup)
        bad_status = copy.deepcopy(self.protocol_events)
        bad_status[2][1]["status"] = "timeout"
        cases.append(bad_status)
        for events in cases:
            _, raw = _execute_synthetic(events, self.protocol_terminal)
            with self.assertRaises((TypeError, ValueError)):
                reader.rebind_exact_cubin_diagnostic_journal(raw)

    def test_torn_suffix_and_post_terminal_bytes_fail_closed(self) -> None:
        _, raw = _execute_synthetic(self.protocol_events, self.protocol_terminal)
        for mutated in (raw[:-1], raw + b"{}\n"):
            with self.assertRaises(ValueError):
                reader.rebind_exact_cubin_diagnostic_journal(mutated)

    def test_exclusive_owner_path_cannot_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exclusive.jsonl"

            def campaign(emit, _wall):
                for kind, event in copy.deepcopy(self.protocol_events):
                    emit(kind, event)
                return copy.deepcopy(self.protocol_terminal)

            kwargs = {
                "output_path": path,
                "git_loader": lambda: {
                    "commit": "b" * 40,
                    "dirty": False,
                    "strict_status": True,
                },
                "campaign_executor": campaign,
                "reserved_path": _RESERVED,
            }
            runner.execute_owner_to_path(**kwargs)
            with self.assertRaises(FileExistsError):
                runner.execute_owner_to_path(**kwargs)

    def test_reader_source_is_standard_library_and_has_no_producer_import(self) -> None:
        path = _ROOT / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(any("cupy" in name for name in imported))
        self.assertFalse(any("work_preflight" in name for name in imported))
        self.assertFalse(any(name.endswith("inspector_diagnostic") for name in imported))
        self.assertFalse(any(name.endswith("inspector_diagnostic_runner") for name in imported))


if __name__ == "__main__":
    unittest.main()
