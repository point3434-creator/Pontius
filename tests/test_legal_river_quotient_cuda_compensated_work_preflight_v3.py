from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import NamedTuple
import unittest
from unittest.mock import patch

import numpy as np

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
import pontius.legal_river_quotient_cuda_compensated_work_preflight as science
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter as adapter
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result as reader
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner as runner
from pontius.legal_river_quotient_cuda_consumer import CudaRuntimeIdentity


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v3.json"
)
_ADAPTER = (
    _ROOT
    / "src/pontius/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3_adapter.py"
)
_RUNNER = (
    _ROOT
    / "src/pontius/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3_runner.py"
)
_READER = (
    _ROOT
    / "src/pontius/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3_result.py"
)
_CONTROLS = Path(__file__)
_V1_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
_V2_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl"
)
_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl"
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


def _runtime_mapping() -> dict[str, object]:
    return {
        "device_name": "serializer-probe-device",
        "compute_capability": "00",
        "device_total_bytes": 0,
        "cuda_driver_version": 0,
        "cuda_runtime_version": 0,
        "cupy_version": "serializer-probe-no-cupy",
    }


def _scientific_probe_event() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-laboratory-v1",
        "kind": "compiler_resource_failure",
        "runtime": _runtime_mapping(),
        "stage": "kernel_compile_and_resource_inspection",
        "reason": "RuntimeError: forced_serializer_probe_compiler_failure",
        "correction_config_sha256": runner.CORRECTION_CONFIG_SHA256,
    }


def _probe_result() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-serializer-probe-v3",
        "runtime": _runtime_mapping(),
        "scientific_event": _scientific_probe_event(),
        "scientific_terminal": {
            "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
            "terminal": "compiler_or_primitive_rejection",
            "failed_population": None,
            "passed": False,
            "projection": None,
        },
        "forced_exception_reason": (
            "RuntimeError: forced_serializer_probe_compiler_failure"
        ),
        "compiler_entry_calls": 1,
        "cupy_loaded": False,
        "restoration": {
            "scientific_plain": True,
            "cupy_loader": True,
            "runtime_identity": True,
            "runtime_verifier": True,
            "kernel_compiler": True,
            "bounded_call_counter": True,
        },
        "passed": True,
    }


def _child_handshake_event(challenge_digest: str) -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-bootstrap-handshake-v3",
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


def _child_probe_event(challenge_digest: str) -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-serializer-probe-child-v3",
        "challenge_sha256": challenge_digest,
        "literal_worker_module": runner.LITERAL_WORKER_MODULE,
        "spec_name": runner.LITERAL_WORKER_MODULE,
        "runtime_name": "__main__",
        "package_name": "pontius",
        "python_no_bytecode": True,
        "argv_count": 1,
        "cupy_loaded_before": False,
        "cupy_loaded_after": False,
        "scientific_source_loaded_before": False,
        "scientific_source_loaded_after": True,
        "probe": _probe_result(),
    }


def _synthetic_handshake() -> runner.BootstrapHandshake:
    digest = sha256(b"h" * 32).hexdigest()
    return runner.BootstrapHandshake(
        event=_child_handshake_event(digest),
        expected_challenge_sha256=digest,
    )


def _synthetic_probe() -> runner.SerializerProbe:
    digest = sha256(b"p" * 32).hexdigest()
    return runner.SerializerProbe(
        event=_child_probe_event(digest),
        expected_challenge_sha256=digest,
    )


def _synthetic_resource_laboratory() -> dict[str, object]:
    raw = """Resource usage:
 Function direct_selected_queries_tile:
  REG:32 STACK:64 SHARED:0 LOCAL:128 CONSTANT[0]:16
 Function direct_selected_fold_tile:
  REG:64 STACK:1024 SHARED:0 LOCAL:256 CONSTANT[0]:16
 Function direct_selected_adjoint_tile:
  REG:48 STACK:128 SHARED:0 LOCAL:64 CONSTANT[0]:16
"""
    parsed = science.parse_cuobjdump_resource_usage(raw)
    names = (
        "direct_selected_queries_tile",
        "direct_selected_fold_tile",
        "direct_selected_adjoint_tile",
    )
    direct = {name: parsed[name] for name in names}
    driver = {
        name: {
            "local_size_bytes": row["STACK"] + row["LOCAL"],
            "registers": row["REG"],
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        }
        for name, row in direct.items()
    }
    combined = science.combined_direct_kernel_resource_report(
        direct,
        driver,
        multiprocessor_count=84,
        maximum_threads_per_multiprocessor=1536,
    )
    return {
        "schema_version": "legal-river-work-preflight-laboratory-v1",
        "kind": "runtime_primitives_and_compiler",
        "runtime": {"cupy_version": "14.0.0"},
        "primitive_gates": {"synthetic": True},
        "direct_order_controls": {
            "gates": {"synthetic": True},
            "all_gates_pass": True,
        },
        "direct_kernel_resources": driver,
        "cubin_resource_usage": {
            "tool_path": "synthetic-cuobjdump",
            "tool_version_output": "synthetic cuobjdump 13.3",
            "raw_resource_stdout": raw,
            "cubin_sha256": "b" * 64,
            "retained_payload_format": "elf-cubin",
            "caller_supplied_nvrtc_options": list(science.CUDA_COMPILE_OPTIONS),
            "cupy_version": "14.0.0",
            "cupy_internal_options_disclosure": [
                "target_architecture",
                "device_as_default_execution_space",
                "version_dependent_precompiled_header",
            ],
            "direct": direct,
            "driver_direct": driver,
            "effective_maxima": combined["effective_maxima"],
            "runtime_residency": combined["runtime_residency"],
            "gates": combined["gates"],
            "claims": {
                "exact_spill_load_store_count": None,
                "local_and_stack_are_not_relabeled_as_spill_counts": True,
            },
        },
    }


def _synthetic_campaign(emit, _: int):
    config = science.load_preregistered_work_preflight_config()
    emit("laboratory", _synthetic_resource_laboratory())
    emit(
        "laboratory",
        {
            "schema_version": "legal-river-work-preflight-laboratory-v1",
            "kind": "complete_ten_legacy_direct_byte_identity",
            "control": {"gates": {"synthetic": True}, "all_gates_pass": True},
        },
    )
    emit(
        "laboratory",
        {
            "schema_version": "legal-river-work-preflight-laboratory-v1",
            "kind": "complete_ten_query_weight_control",
            "gates": {"synthetic": True},
        },
    )
    phase_totals: dict[int, dict[str, int]] = {}
    for cards in science.CALIBRATION_POPULATIONS:
        work = science.complete_campaign_work(cards)
        phase_totals[cards] = {phase: 0 for phase in science.PHASE_ORDER}
        observed_work: dict[str, int] = {}
        assigned_work: set[str] = set()
        for family_index, family in enumerate(science.POPULATION_FAMILIES):
            key = "default" if family_index == 0 else "alternate"
            chunks = config["chunk_contract"][str(cards)][key]
            cursor = cards * 1_000_000 + family_index * 100_000
            phases = list(science.PHASE_ORDER)
            direct_index = phases.index("direct_adjoint")
            phases.insert(direct_index + 1, "adjoint_recurrence_and_signed_sources")
            for ordinal, phase in enumerate(phases):
                start = cursor
                stop = start + 1
                cursor = stop
                row_work = (
                    {
                        name: work[name]
                        for name in science._PHASE_WORK_COUNTERS.get(phase, ())
                        if name not in assigned_work
                    }
                    if family_index == 0
                    else {}
                )
                assigned_work.update(row_work)
                emit(
                    "phase",
                    {
                        "schema_version": "legal-river-work-preflight-phase-v1",
                        "ordinal": ordinal,
                        "population": cards,
                        "family": family,
                        "repeat": ordinal % 2,
                        "tile": ordinal % 3,
                        "phase": phase,
                        "host_start_ns": start,
                        "host_stop_ns": stop,
                        "host_ns": 1,
                        "device_ns": 1,
                        "chunks": list(chunks),
                        "work": row_work,
                    },
                )
                phase_totals[cards][phase] += 1
                for name, value in row_work.items():
                    observed_work[name] = observed_work.get(name, 0) + value
        gates = {
            "semantic": True,
            "executed_work_ledger_exact": True,
            "phase_partition_exact": True,
            "population_wall": True,
        }
        emit(
            "population",
            {
                "schema_version": "legal-river-work-preflight-population-evidence-v1",
                "population": cards,
                "scalar_pairs": {},
                "conditional_value": [0, 1],
                "maximum_errors": {},
                "reporting_digests": {},
                "telemetry": {},
                "gates": gates,
                "all_gates_pass": True,
                "phase_host_ns": phase_totals[cards],
                "campaign_host_ns": sum(phase_totals[cards].values()),
                "executed_work": observed_work,
            },
        )
    projection = science.reconstruct_projection(phase_totals, config)
    emit("projection", projection)
    return {
        "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
        "terminal": (
            "completed_capacity_pass"
            if projection["passed"]
            else "completed_capacity_rejection"
        ),
        "failed_population": None,
        "passed": bool(projection["passed"]),
        "projection": projection,
    }


def _execute_synthetic(path: Path, **overrides):
    arguments = {
        "output_path": path,
        "git_loader": _git,
        "hashes_loader": runner.dependency_hashes,
        "retained_loader": runner.rebind_retained_artifacts,
        "handshake_executor": _synthetic_handshake,
        "serializer_probe_executor": _synthetic_probe,
        "campaign_executor": _synthetic_campaign,
        "reserved_path": path.parent / "reserved-absent.jsonl",
    }
    arguments.update(overrides)
    return runner.execute_owner_to_path(**arguments)


def _rewrite_journal(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
        expected_campaign_sha256=runner.WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    previous: str | None = None
    lines: list[bytes] = []
    for index, (record, payload) in enumerate(zip(recovery.records, payloads)):
        body = build_journal_record_body(
            protocol_sha256=runner.WORK_PREFLIGHT_V3_PROTOCOL_SHA256,
            campaign_sha256=runner.WORK_PREFLIGHT_V3_CAMPAIGN_SHA256,
            kind=record.body.kind,
            sequence=index,
            previous_record_sha256=previous,
            semantic_identity_sha256=sha256(
                canonical_journal_json_bytes(payload)
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


class WorkPreflightV3SourceSealTests(unittest.TestCase):
    def test_fresh_runner_and_reader_imports_are_device_and_science_free(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result; "
            "print(int('cupy' in sys.modules), "
            "int('pontius.legal_river_quotient_cuda_compensated_work_preflight' in sys.modules))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="ascii",
        )
        self.assertEqual(completed.stdout.strip(), "0 0")

    def test_config_paths_dependencies_and_retained_artifacts_rebind(self) -> None:
        loaded = runner.load_public_config()
        self.assertEqual(loaded.sha256, runner.PREREGISTERED_CONFIG_SHA256)
        self.assertEqual(reader.PREREGISTERED_CONFIG_SHA256, loaded.sha256)
        self.assertEqual(
            sha256(_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            loaded.sha256,
        )
        self.assertTrue(_ADAPTER.is_file())
        self.assertTrue(_RUNNER.is_file())
        self.assertTrue(_READER.is_file())
        self.assertTrue(_CONTROLS.is_file())
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())
        retained = runner.rebind_retained_artifacts()
        self.assertEqual(retained.v1["sha256"], runner.V1_RESULT_SHA256)
        self.assertEqual(retained.v2["sha256"], runner.V2_RESULT_SHA256)
        self.assertEqual(set(runner.dependency_hashes()), set(reader._DEPENDENCY_PATHS))

    def test_sources_are_additive_and_no_consumed_runner_is_imported(self) -> None:
        runner_text = _RUNNER.read_text(encoding="utf-8")
        reader_text = _READER.read_text(encoding="utf-8")
        adapter_text = _ADAPTER.read_text(encoding="utf-8")
        for text in (runner_text, reader_text, adapter_text):
            ast.parse(text)
        imports = {
            node.module
            for tree in (ast.parse(runner_text), ast.parse(reader_text), ast.parse(adapter_text))
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertNotIn(
            "pontius.legal_river_quotient_cuda_compensated_work_preflight_runner",
            imports,
        )
        self.assertNotIn(
            "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner",
            imports,
        )
        adapter_tree = ast.parse(adapter_text)
        called_names = {
            node.func.id
            for node in ast.walk(adapter_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"vars", "asdict"}.isdisjoint(called_names))
        self.assertNotIn('[sys.executable, "-B", "-m", __name__]', runner_text)
        self.assertIn(
            '[sys.executable, "-B", "-m", LITERAL_WORKER_MODULE]', runner_text
        )

    def test_legacy_success_domain_is_byte_identical(self) -> None:
        complete_events: list[tuple[str, object]] = []
        complete_terminal = _synthetic_campaign(
            lambda kind, payload: complete_events.append((kind, payload)),
            1,
        )
        corpus = {
            "none": None,
            "bool": True,
            "string": "river",
            "integer": 17,
            "float": 1.25,
            "fraction": Fraction(7, 13),
            "numpy_integer": np.int64(19),
            "numpy_float": np.float64(2.5),
            "mapping": {1: (False, Fraction(-3, 11))},
            "sequence": ["x", (2, 3)],
            "complete_synthetic_events": complete_events,
            "complete_synthetic_terminal": complete_terminal,
        }
        legacy = science._plain(corpus)
        successor = adapter.plain_evidence_v3(corpus)
        self.assertEqual(successor, legacy)
        self.assertEqual(
            canonical_journal_json_bytes(successor),
            canonical_journal_json_bytes(legacy),
        )
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    science._plain(value)
                with self.assertRaises(ValueError):
                    adapter.plain_evidence_v3(value)

    def test_exact_runtime_type_is_admitted_and_legacy_failure_is_reproduced(self) -> None:
        runtime = CudaRuntimeIdentity(
            "device", "120", 1, 2, 3, "14.0.0"
        )
        with self.assertRaisesRegex(TypeError, "CudaRuntimeIdentity"):
            science._plain(runtime)
        self.assertEqual(
            adapter.plain_evidence_v3(runtime),
            {
                "device_name": "device",
                "compute_capability": "120",
                "device_total_bytes": 1,
                "cuda_driver_version": 2,
                "cuda_runtime_version": 3,
                "cupy_version": "14.0.0",
            },
        )

    def test_unknown_dataclass_subclass_namedtuple_slots_and_dict_reject(self) -> None:
        @dataclass(frozen=True, slots=True)
        class UnknownDataclass:
            value: int

        class RuntimeSubclass(CudaRuntimeIdentity):
            pass

        class TupleObject(NamedTuple):
            value: int

        class SlotsObject:
            __slots__ = ("value",)

            def __init__(self) -> None:
                self.value = 1

        class DictObject:
            def __init__(self) -> None:
                self.value = 1

        values = (
            UnknownDataclass(1),
            RuntimeSubclass("device", "120", 1, 2, 3, "14.0.0"),
            TupleObject(1),
            SlotsObject(),
            DictObject(),
        )
        for value in values:
            with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(
                TypeError, "unsupported work-preflight evidence type"
            ):
                adapter.plain_evidence_v3(value)

    def test_adapter_restores_exact_plain_on_success_exception_and_thread_rejection(self) -> None:
        original = science._plain
        with adapter.installed_scientific_plain():
            self.assertIs(science._plain, adapter.plain_evidence_v3)
        self.assertIs(science._plain, original)
        with self.assertRaisesRegex(RuntimeError, "synthetic adapter body"):
            with adapter.installed_scientific_plain():
                raise RuntimeError("synthetic adapter body")
        self.assertIs(science._plain, original)
        with (
            patch.object(adapter.threading, "active_count", return_value=2),
            self.assertRaisesRegex(RuntimeError, "another live thread"),
        ):
            with adapter.installed_scientific_plain():
                pass
        self.assertIs(science._plain, original)

    def test_direct_forced_probe_uses_scientific_send_and_restores_every_identity(self) -> None:
        original_plain = science._plain
        original_loader = science._cupy_module
        original_runtime = science._paired._runtime_identity
        original_verifier = science._paired._verify_runtime
        original_kernels = science._kernels
        original_counter = science._BOUNDED_EXECUTION_CALLS
        emitted: list[tuple[str, object]] = []
        result = adapter.run_forced_serializer_probe(
            lambda kind, payload: emitted.append((kind, payload))
        )
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["scientific_event"]["reason"],
            "RuntimeError: forced_serializer_probe_compiler_failure",
        )
        self.assertEqual(emitted, [("laboratory", result["scientific_event"])])
        self.assertIs(science._plain, original_plain)
        self.assertIs(science._cupy_module, original_loader)
        self.assertIs(science._paired._runtime_identity, original_runtime)
        self.assertIs(science._paired._verify_runtime, original_verifier)
        self.assertIs(science._kernels, original_kernels)
        self.assertEqual(science._BOUNDED_EXECUTION_CALLS, original_counter)

    def test_real_handshake_and_serializer_probe_cross_the_literal_shared_transport(self) -> None:
        self.assertFalse(_RESULT.exists())
        handshake = runner.run_no_cuda_bootstrap_handshake(
            challenge_factory=lambda count: b"h" * count
        )
        probe = runner.run_no_cuda_serializer_probe(
            challenge_factory=lambda count: b"p" * count
        )
        self.assertFalse(handshake.event["cupy_loaded"])
        self.assertFalse(handshake.event["scientific_source_loaded"])
        self.assertFalse(probe.event["cupy_loaded_before"])
        self.assertFalse(probe.event["cupy_loaded_after"])
        self.assertEqual(
            probe.event["probe"]["scientific_event"]["reason"],
            "RuntimeError: forced_serializer_probe_compiler_failure",
        )
        self.assertFalse(_RESULT.exists())

    def test_transport_rejects_unframed_malformed_and_post_terminal_output(self) -> None:
        fake = _FakeProcess(stdout="unframed\n")
        with patch.object(runner.subprocess, "Popen", return_value=fake) as popen:
            with self.assertRaisesRegex(RuntimeError, "unframed"):
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1_000_000)
        self.assertEqual(
            popen.call_args.args[0],
            [sys.executable, "-B", "-m", runner.LITERAL_WORKER_MODULE],
        )

        malformed = _FakeProcess(stdout=runner._EVENT_PREFIX + "{}\n")
        with patch.object(runner.subprocess, "Popen", return_value=malformed):
            with self.assertRaisesRegex(RuntimeError, "event is malformed"):
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1_000_000)

        terminal = json.dumps(
            {
                "kind": "child_terminal",
                "payload": {
                    "schema_version": "legal-river-work-preflight-bootstrap-terminal-v3",
                    "terminal": "bootstrap_handshake_pass",
                    "passed": True,
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        event = json.dumps(
            {"kind": "bootstrap_handshake", "payload": _child_handshake_event("0" * 64)},
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
                runner._run_child_process("handshake", "0" * 64, lambda *_: None, 1_000_000)

    def test_transport_bounds_stderr_and_deadline_survives_stdout_eof(self) -> None:
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

    def test_synthetic_complete_owner_rebinds_through_v2_and_v1_science(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.jsonl"
            execution = _execute_synthetic(path)
            self.assertEqual(execution.terminal["terminal"], "completed_capacity_pass")
            rebound = reader.rebind_work_preflight_v3_journal(path.read_bytes())
            self.assertTrue(rebound.passed)
            self.assertEqual(rebound.terminal, "completed_capacity_pass")
            self.assertIsNotNone(rebound.handshake)
            self.assertIsNotNone(rebound.serializer_probe)
            self.assertEqual(len(rebound.phases), 68)
            self.assertIsNotNone(rebound.projection)
            self.assertTrue(rebound.v2_rebinding.passed)
            self.assertTrue(rebound.v2_rebinding.scientific_rebinding.passed)

    def test_probe_failure_is_durable_and_campaign_never_starts(self) -> None:
        campaign_calls = 0

        def fail_probe():
            raise RuntimeError("synthetic serializer probe failure")

        def forbidden_campaign(emit, wall):
            nonlocal campaign_calls
            del emit, wall
            campaign_calls += 1
            raise AssertionError("campaign must remain closed")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.jsonl"
            execution = _execute_synthetic(
                path,
                serializer_probe_executor=fail_probe,
                campaign_executor=forbidden_campaign,
            )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertTrue(execution.terminal["handshake_passed"])
            self.assertFalse(execution.terminal["serializer_probe_passed"])
            self.assertEqual(campaign_calls, 0)
            rebound = reader.rebind_work_preflight_v3_journal(path.read_bytes())
            self.assertIsNotNone(rebound.handshake)
            self.assertIsNone(rebound.serializer_probe)
            self.assertFalse(rebound.phases)

    def test_reader_rejects_rehashed_probe_dependency_order_and_terminal_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.jsonl"
            _execute_synthetic(path)
            raw = path.read_bytes()

            def change_reason(payloads):
                payloads[3]["event"]["child"]["probe"]["scientific_event"][
                    "reason"
                ] = "RuntimeError: changed"

            with self.assertRaisesRegex(ValueError, "serializer-probe semantics differ"):
                reader.rebind_work_preflight_v3_journal(
                    _rewrite_journal(raw, change_reason)
                )

            def change_runtime(payloads):
                del payloads[3]["event"]["child"]["probe"]["runtime"][
                    "cupy_version"
                ]

            with self.assertRaisesRegex(ValueError, "serializer-probe semantics differ"):
                reader.rebind_work_preflight_v3_journal(
                    _rewrite_journal(raw, change_runtime)
                )

            def change_dependency(payloads):
                payloads[1]["event"]["dependency_hashes"]["v3_adapter"] = "0" * 64

            with self.assertRaisesRegex(ValueError, "dependency differs: v3_adapter"):
                reader.rebind_work_preflight_v3_journal(
                    _rewrite_journal(raw, change_dependency)
                )

            def put_science_before_probe(payloads):
                left = payloads[3]
                right = payloads[4]
                left["event_kind"], right["event_kind"] = (
                    right["event_kind"],
                    left["event_kind"],
                )
                left["event"], right["event"] = right["event"], left["event"]

            with self.assertRaisesRegex(ValueError, "science precedes lifecycle seals"):
                reader.rebind_work_preflight_v3_journal(
                    _rewrite_journal(raw, put_science_before_probe)
                )

            def flip_terminal_probe(payloads):
                payloads[-1]["serializer_probe_passed"] = False

            with self.assertRaisesRegex(ValueError, "serializer-probe bit differs"):
                reader.rebind_work_preflight_v3_journal(
                    _rewrite_journal(raw, flip_terminal_probe)
                )

    def test_exclusive_replay_torn_suffix_and_reserved_authority_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "v3.jsonl"
            _execute_synthetic(path)
            with self.assertRaises(FileExistsError):
                _execute_synthetic(path)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                reader.rebind_work_preflight_v3_journal(path.read_bytes() + b"{")

            reserved = root / "reserved.jsonl"
            reserved.write_bytes(b"reserved")
            handshake_calls = 0

            def forbidden_handshake():
                nonlocal handshake_calls
                handshake_calls += 1
                return _synthetic_handshake()

            second = root / "reserved-breach.jsonl"
            execution = _execute_synthetic(
                second,
                reserved_path=reserved,
                handshake_executor=forbidden_handshake,
            )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertFalse(execution.terminal["handshake_passed"])
            self.assertEqual(handshake_calls, 0)

    def test_public_owner_is_no_argument_and_real_authorities_remain_absent(self) -> None:
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
        self.assertEqual(sha256(_V1_RESULT.read_bytes()).hexdigest(), runner.V1_RESULT_SHA256)
        self.assertEqual(sha256(_V2_RESULT.read_bytes()).hexdigest(), runner.V2_RESULT_SHA256)


if __name__ == "__main__":
    unittest.main()
