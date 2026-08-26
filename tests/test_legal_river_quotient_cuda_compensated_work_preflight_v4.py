from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
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
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
import pontius.legal_river_quotient_cuda_compensated_work_preflight as science
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter as adapter
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result as reader
import pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner as runner
from pontius.legal_river_quotient_cuda_consumer import CudaRuntimeIdentity


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / runner.CONFIG_RELATIVE_PATH
_ENVELOPE_CONFIG = _ROOT / runner.ENVELOPE_CONFIG_RELATIVE_PATH
_ADAPTER = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_adapter.py"
)
_RUNNER = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_runner.py"
)
_READER = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_result.py"
)
_CONTROLS = Path(__file__)
_RESULT = _ROOT / runner.RESULT_RELATIVE_PATH
_RESERVED = _ROOT / runner.RESERVED_ACTUAL_RESULT_RELATIVE_PATH


def _git() -> dict[str, object]:
    return {"commit": "a" * 40, "dirty": False, "strict_status": True}


def _runtime(cupy: str = "14.2.0-probe") -> dict[str, object]:
    return {
        "device_name": "synthetic-device",
        "compute_capability": "00",
        "device_total_bytes": 0,
        "cuda_driver_version": 0,
        "cuda_runtime_version": 0,
        "cupy_version": cupy,
    }


def _probe_result() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-adapter-probe-v4",
        "event_kinds": [
            "repaired_executed_cubin",
            "resource_command_stream",
            "resource_command_terminal",
            "resource_command_stream",
            "resource_command_terminal",
            "resource_temporary_cleanup",
        ],
        "effective_maxima": {
            "direct_selected_adjoint_tile": {
                "registers": 30,
                "stack_plus_local_backing_bytes": 10,
            },
            "direct_selected_fold_tile": {
                "registers": 50,
                "stack_plus_local_backing_bytes": 30,
            },
            "direct_selected_queries_tile": {
                "registers": 41,
                "stack_plus_local_backing_bytes": 12,
            },
        },
        "resource_gates": {
            "register_ceiling": True,
            "local_and_stack_ceiling": True,
            "resident_thread_bound": True,
            "resident_backing_within_device_reserve": True,
        },
        "runtime": {
            "device_name": "adapter-probe-device",
            "compute_capability": "00",
            "device_total_bytes": 0,
            "cuda_driver_version": 0,
            "cuda_runtime_version": 0,
            "cupy_version": "adapter-probe-no-cupy",
        },
        "original_payload_sha256": adapter.ORIGINAL_PAYLOAD_SHA256,
        "repaired_payload_sha256": adapter.REPAIRED_PAYLOAD_SHA256,
        "cupy_loaded": False,
        "scientific_call_counter_unchanged": True,
        "identities_and_caches_restored": True,
        "passed": True,
    }


def _synthetic_handshake() -> runner.BootstrapHandshake:
    digest = sha256(b"h" * 32).hexdigest()
    return runner.BootstrapHandshake(
        expected_challenge_sha256=digest,
        event={
            "schema_version": "legal-river-work-preflight-bootstrap-handshake-v4",
            "challenge_sha256": digest,
            "literal_worker_module": runner.LITERAL_WORKER_MODULE,
            "spec_name": runner.LITERAL_WORKER_MODULE,
            "runtime_name": "__main__",
            "package_name": "pontius",
            "python_no_bytecode": True,
            "argv_count": 1,
            "cupy_loaded": False,
            "scientific_source_loaded": False,
        },
    )


def _synthetic_probe() -> runner.AdapterProbe:
    digest = sha256(b"p" * 32).hexdigest()
    return runner.AdapterProbe(
        expected_challenge_sha256=digest,
        event={
            "schema_version": "legal-river-work-preflight-adapter-probe-child-v4",
            "challenge_sha256": digest,
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
        },
    )


def _synthetic_resource_laboratory() -> dict[str, object]:
    raw = adapter._probe_resource_stdout().decode("ascii")
    parsed = science.parse_cuobjdump_resource_usage(raw)
    direct = {name: parsed[name] for name in adapter.DIRECT_KERNEL_NAMES}
    driver = {
        "direct_selected_queries_tile": {
            "local_size_bytes": 11,
            "registers": 41,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
        "direct_selected_fold_tile": {
            "local_size_bytes": 30,
            "registers": 49,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
        "direct_selected_adjoint_tile": {
            "local_size_bytes": 8,
            "registers": 30,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
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
        "runtime": _runtime(),
        "primitive_gates": {"synthetic": True},
        "direct_order_controls": {
            "gates": {"synthetic": True},
            "all_gates_pass": True,
        },
        "direct_kernel_resources": driver,
        "cubin_resource_usage": {
            "tool_path": r"C:\frozen-probe\cuobjdump.exe",
            "tool_version_output": "Cuda compilation tools, release 13.3, V13.3.73",
            "raw_resource_stdout": raw,
            "cubin_sha256": adapter.REPAIRED_PAYLOAD_SHA256,
            "retained_payload_format": "elf-cubin",
            "caller_supplied_nvrtc_options": list(science.CUDA_COMPILE_OPTIONS),
            "cupy_version": "14.2.0-probe",
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


def _synthetic_campaign(emit, _: int) -> dict[str, object]:
    adapter.run_device_free_adapter_probe(emit)
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
    config = science.load_preregistered_work_preflight_config()
    phase_totals: dict[int, dict[str, int]] = {}
    for cards in science.CALIBRATION_POPULATIONS:
        work = science.complete_campaign_work(cards)
        phase_totals[cards] = {phase: 0 for phase in science.PHASE_ORDER}
        observed_work: dict[str, int] = {}
        assigned_work: set[str] = set()
        for family_index, family in enumerate(science.POPULATION_FAMILIES):
            chunk_key = "default" if family_index == 0 else "alternate"
            chunks = config["chunk_contract"][str(cards)][chunk_key]
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


def _compiler_failure_campaign(emit, _: int) -> dict[str, object]:
    emit(
        "laboratory",
        {
            "schema_version": "legal-river-work-preflight-laboratory-v1",
            "kind": "compiler_resource_failure",
            "runtime": _runtime("none"),
            "stage": "kernel_compile_and_resource_inspection",
            "reason": "RuntimeError: synthetic compiler failure",
            "correction_config_sha256": runner.RESOURCE_CONFIG_SHA256,
        },
    )
    return {
        "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
        "terminal": "compiler_or_primitive_rejection",
        "failed_population": None,
        "passed": False,
        "projection": None,
    }


def _execute(path: Path, *, campaign=_synthetic_campaign, **overrides):
    arguments = {
        "output_path": path,
        "git_loader": _git,
        "hashes_loader": runner.dependency_hashes,
        "retained_loader": runner.rebind_retained_artifacts,
        "handshake_executor": _synthetic_handshake,
        "adapter_probe_executor": _synthetic_probe,
        "campaign_executor": campaign,
        "reserved_path": path.parent / "reserved-absent.jsonl",
    }
    arguments.update(overrides)
    return runner.execute_owner_to_path(**arguments)


def _rewrite_journal(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
        expected_campaign_sha256=runner.WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    previous: str | None = None
    lines: list[bytes] = []
    for index, (record, payload) in enumerate(zip(recovery.records, payloads, strict=True)):
        body = build_journal_record_body(
            protocol_sha256=runner.WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
            campaign_sha256=runner.WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
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


def _event_payloads(payloads, kind: str):
    return [
        row["event"]
        for row in payloads[1:-1]
        if row.get("event_kind") == kind
    ]


class WorkPreflightV4SourceSealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory()
        cls.synthetic_path = Path(cls._temporary.name) / "synthetic-v4.jsonl"
        cls.execution = _execute(cls.synthetic_path)
        cls.synthetic_raw = cls.synthetic_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_fresh_runner_and_reader_import_without_cupy_or_science(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result; "
            "assert 'cupy' not in sys.modules; "
            "assert 'pontius.legal_river_quotient_cuda_compensated_work_preflight' "
            "not in sys.modules"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            env={**dict(__import__("os").environ), "PYTHONPATH": "src;."},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_composite_config_and_retained_authorities_rebind(self) -> None:
        loaded = runner.load_public_config()
        self.assertEqual(loaded.sha256, runner.PREREGISTERED_CONFIG_SHA256)
        self.assertEqual(loaded.correction_sha256, runner.ENVELOPE_CONFIG_SHA256)
        self.assertEqual(
            reader.canonical_lf_sha256(_CONFIG), runner.PREREGISTERED_CONFIG_SHA256
        )
        self.assertEqual(
            reader.canonical_lf_sha256(_ENVELOPE_CONFIG),
            runner.ENVELOPE_CONFIG_SHA256,
        )
        retained = runner.rebind_retained_artifacts()
        self.assertEqual(retained.v3["terminal"], "compiler_or_primitive_rejection")
        self.assertEqual(retained.suffix["terminal"], "suffix_reconstruction_pass")

    def test_sources_are_additive_and_consumed_owners_are_not_imported(self) -> None:
        forbidden = {
            "legal_river_quotient_cuda_compensated_work_preflight_runner",
            "legal_river_quotient_cuda_compensated_work_preflight_v2_runner",
            "legal_river_quotient_cuda_compensated_work_preflight_v3_runner",
            "legal_river_exact_cubin_zero_suffix_diagnostic_runner",
        }
        for path in (_ADAPTER, _RUNNER, _READER):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.rsplit(".", 1)[-1] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        imported.add(node.module.rsplit(".", 1)[-1])
                    imported.update(alias.name.rsplit(".", 1)[-1] for alias in node.names)
            self.assertTrue(forbidden.isdisjoint(imported), (path, imported & forbidden))
        self.assertEqual(
            reader.canonical_lf_sha256(
                _ROOT
                / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
            ),
            "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa",
        )

    def test_plain_serializer_exact_domain_and_unknown_dataclass_reject(self) -> None:
        runtime = CudaRuntimeIdentity(
            device_name="probe",
            compute_capability="00",
            device_total_bytes=0,
            cuda_driver_version=0,
            cuda_runtime_version=0,
            cupy_version="none",
        )
        self.assertEqual(adapter.plain_evidence_v4(runtime)["device_name"], "probe")

        @dataclass
        class Unknown:
            value: int

        with self.assertRaises(TypeError):
            adapter.plain_evidence_v4(Unknown(1))
        with self.assertRaises(ValueError):
            adapter.plain_evidence_v4(float("nan"))

    def test_device_free_adapter_probe_rebinds_repair_commands_and_restores(self) -> None:
        events: list[tuple[int, str, dict[str, object]]] = []
        before = science._BOUNDED_EXECUTION_CALLS
        result = adapter.run_device_free_adapter_probe(
            lambda kind, event: events.append((len(events), kind, dict(event)))
        )
        self.assertTrue(result["passed"])
        repaired_raw = reader._rebind_retained()[2]
        repair = next(event for _, kind, event in events if kind == "repaired_executed_cubin")
        reader._validate_repair(repair, repaired_raw)
        commands, _ = reader._reconstruct_commands(events)
        self.assertEqual([row.command_id for row in commands], [
            "cuobjdump_version",
            "cuobjdump_resource_usage",
        ])
        self.assertEqual(events[-1][1], "resource_temporary_cleanup")
        self.assertEqual(science._BOUNDED_EXECUTION_CALLS, before)
        self.assertFalse(science._KERNEL_CACHE or science._MODULE_CACHE or science._CUBIN_CACHE)

    def test_literal_minus_b_handshake_and_adapter_probe_cross_transport(self) -> None:
        handshake = runner.run_no_cuda_bootstrap_handshake(
            challenge_factory=lambda count: b"h" * count
        )
        probe = runner.run_no_cuda_adapter_probe(
            challenge_factory=lambda count: b"p" * count
        )
        self.assertEqual(handshake.event["runtime_name"], "__main__")
        self.assertEqual(probe.event["runtime_name"], "__main__")
        self.assertTrue(probe.event["probe"]["passed"])

    def test_parser_capture_payload_child_and_journal_limits_are_distinct(self) -> None:
        self.assertNotEqual(adapter.MAXIMUM_PAYLOAD_BYTES, adapter.MAXIMUM_COMBINED_VERSION_BYTES)
        self.assertNotEqual(adapter.MAXIMUM_STREAM_BYTES, adapter.MAXIMUM_RESOURCE_STDOUT_BYTES)
        self.assertNotEqual(runner.MAXIMUM_ARTIFACT_BYTES, runner.MAXIMUM_CHILD_LINE_CHARACTERS)
        self.assertEqual(
            adapter._accepted_ascii(
                b"x" * adapter.MAXIMUM_COMBINED_VERSION_BYTES,
                maximum=adapter.MAXIMUM_COMBINED_VERSION_BYTES,
                label="boundary",
            ),
            "x" * adapter.MAXIMUM_COMBINED_VERSION_BYTES,
        )
        for raw in (
            b"x" * (adapter.MAXIMUM_COMBINED_VERSION_BYTES + 1),
            b"x\0y",
            b"\xff",
        ):
            with self.assertRaises(science.CompilerResourceRejection):
                adapter._accepted_ascii(
                    raw,
                    maximum=adapter.MAXIMUM_COMBINED_VERSION_BYTES,
                    label="boundary",
                )
        with patch.object(adapter, "MAXIMUM_STREAM_BYTES", 7):
            self.assertEqual(
                len(adapter._stream_chunks("cuobjdump_version", "stdout", b"1234567")),
                1,
            )
            with self.assertRaises(ValueError):
                adapter._stream_chunks("cuobjdump_version", "stdout", b"12345678")

    def test_corrected_envelope_arithmetic_and_reader_cap_fail_closed(self) -> None:
        correction = json.loads(_ENVELOPE_CONFIG.read_text(encoding="utf-8"))
        journal = correction["corrected_journal_contract"]
        self.assertLessEqual(
            journal["encoded_stream_plus_chunk_overhead_bytes"],
            journal["maximum_journal_bytes"],
        )
        self.assertEqual(
            journal["journal_headroom_after_four_maximum_streams_and_chunk_overhead_bytes"],
            journal["maximum_journal_bytes"]
            - journal["encoded_stream_plus_chunk_overhead_bytes"],
        )
        with patch.object(reader, "MAXIMUM_ARTIFACT_BYTES", len(self.synthetic_raw) - 1):
            with self.assertRaises(ValueError):
                reader.rebind_work_preflight_v4_journal(self.synthetic_raw)

    def test_full_synthetic_owner_rebinds_all_layers(self) -> None:
        rebound = reader.rebind_work_preflight_v4_journal(self.synthetic_raw)
        self.assertEqual(rebound.terminal, self.execution.terminal["terminal"])
        self.assertIsNotNone(rebound.handshake)
        self.assertIsNotNone(rebound.adapter_probe)
        self.assertIsNotNone(rebound.repair)
        self.assertEqual(len(rebound.commands), 2)
        self.assertIsNotNone(rebound.cleanup)
        self.assertEqual(len(rebound.phases), 68)
        self.assertIsNotNone(rebound.projection)

    def test_reader_rejects_chunk_change_duplicate_and_reordering(self) -> None:
        changed = _rewrite_journal(
            self.synthetic_raw,
            lambda payloads: _event_payloads(payloads, "resource_command_stream")[0].__setitem__(
                "chunk_base64", "WA=="
            ),
        )
        with self.assertRaises(ValueError):
            reader.rebind_work_preflight_v4_journal(changed)
        events: list[tuple[int, str, dict[str, object]]] = []
        adapter.run_device_free_adapter_probe(
            lambda kind, event: events.append((len(events), kind, dict(event)))
        )
        first_chunk = next(row for row in events if row[1] == "resource_command_stream")
        duplicate = list(events)
        duplicate.insert(first_chunk[0] + 1, (first_chunk[0] + 1, first_chunk[1], first_chunk[2]))
        duplicate = [(index, kind, event) for index, (_, kind, event) in enumerate(duplicate)]
        with self.assertRaises(ValueError):
            reader._reconstruct_commands(duplicate)
        stream_rows = [
            i
            for i, (_, kind, _) in enumerate(events)
            if kind == "resource_command_stream"
        ]
        reordered = list(events)
        reordered[stream_rows[0]], reordered[stream_rows[1]] = (
            reordered[stream_rows[1]],
            reordered[stream_rows[0]],
        )
        reordered = [(index, kind, event) for index, (_, kind, event) in enumerate(reordered)]
        with self.assertRaises(ValueError):
            reader._reconstruct_commands(reordered)

    def test_reader_independently_rederives_both_resource_max_directions(self) -> None:
        rebound = reader.rebind_work_preflight_v4_journal(self.synthetic_raw)
        recovery = recover_journal_bytes(
            self.synthetic_raw,
            expected_protocol_sha256=runner.WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
            expected_campaign_sha256=runner.WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
        )
        events = [record.body.payload["event"] for record in recovery.records[1:-1]]
        runtime = next(
            event
            for event in events
            if event.get("kind") == "runtime_primitives_and_compiler"
        )
        maxima = runtime["cubin_resource_usage"]["effective_maxima"]
        self.assertEqual(maxima["direct_selected_queries_tile"]["registers"], 41)
        self.assertEqual(
            maxima["direct_selected_queries_tile"]["stack_plus_local_backing_bytes"],
            12,
        )
        self.assertEqual(maxima["direct_selected_fold_tile"]["registers"], 50)
        self.assertEqual(maxima["direct_selected_fold_tile"]["stack_plus_local_backing_bytes"], 30)
        commands = {row.command_id: row for row in rebound.commands}
        repair = rebound.repair
        assert repair is not None
        for kernel, field, wrong in (
            ("direct_selected_queries_tile", "registers", 40),
            ("direct_selected_fold_tile", "stack_plus_local_backing_bytes", 24),
        ):
            mutated = deepcopy(runtime)
            mutated["cubin_resource_usage"]["effective_maxima"][kernel][field] = wrong
            with self.assertRaises(ValueError):
                reader._validate_runtime_resource(mutated, repair, commands)
        parsed = reader._parse_resources(runtime["cubin_resource_usage"]["raw_resource_stdout"])
        self.assertEqual(parsed["direct_selected_adjoint_tile"]["STACK"], 4)
        self.assertEqual(parsed["direct_selected_adjoint_tile"]["LOCAL"], 6)

    def test_population_phase_and_partition_mutations_fail_closed(self) -> None:
        def population_25(payloads) -> None:
            _event_payloads(payloads, "population")[0]["population"] = 25

        def unknown_phase(payloads) -> None:
            _event_payloads(payloads, "phase")[0]["phase"] = "unfrozen_phase"

        def phase_sum(payloads) -> None:
            _event_payloads(payloads, "population")[0]["campaign_host_ns"] += 1

        for mutation in (population_25, unknown_phase, phase_sum):
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(ValueError):
                    reader.rebind_work_preflight_v4_journal(
                        _rewrite_journal(self.synthetic_raw, mutation)
                    )

    def test_repair_suffix_claims_and_dependency_mutations_fail_closed(self) -> None:
        def suffix(payloads) -> None:
            _event_payloads(payloads, "repaired_executed_cubin")[0]["suffix_hex"] = "0000"

        def dependency(payloads) -> None:
            _event_payloads(payloads, "provenance")[0]["dependency_hashes"]["v4_adapter"] = "0" * 64

        def claims(payloads) -> None:
            payloads[-1]["claims"]["action_result"] = "invented"

        for mutation in (suffix, dependency, claims):
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(ValueError):
                    reader.rebind_work_preflight_v4_journal(
                        _rewrite_journal(self.synthetic_raw, mutation)
                    )

    def test_probe_failure_is_terminal_and_campaign_never_starts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe-failure.jsonl"
            calls = 0

            def campaign(_emit, _wall):
                nonlocal calls
                calls += 1
                return {}

            execution = _execute(
                path,
                campaign=campaign,
                adapter_probe_executor=lambda: (_ for _ in ()).throw(
                    RuntimeError("forced probe failure")
                ),
            )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertEqual(calls, 0)
            rebound = reader.rebind_work_preflight_v4_journal(path.read_bytes())
            self.assertEqual(rebound.terminal, "infrastructure_failure")
            self.assertIsNone(rebound.adapter_probe)

    def test_compiler_rejection_has_no_phase_or_capacity_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compiler-rejection.jsonl"
            _execute(path, campaign=_compiler_failure_campaign)
            rebound = reader.rebind_work_preflight_v4_journal(path.read_bytes())
            self.assertEqual(rebound.terminal, "compiler_or_primitive_rejection")
            self.assertFalse(rebound.passed)
            self.assertEqual(rebound.phases, ())
            self.assertIsNone(rebound.projection)
            self.assertIsNone(rebound.repair)
            self.assertEqual(rebound.commands, ())

    def test_exclusive_write_torn_suffix_and_authorities_remain_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exclusive.jsonl"
            _execute(path, campaign=_compiler_failure_campaign)
            with self.assertRaises(FileExistsError):
                _execute(path, campaign=_compiler_failure_campaign)
            with self.assertRaises(ValueError):
                reader.rebind_work_preflight_v4_journal(path.read_bytes()[:-1])
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_public_owner_is_no_argument(self) -> None:
        tree = ast.parse(_RUNNER.read_text(encoding="utf-8"), filename=str(_RUNNER))
        main = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        self.assertEqual(len(main.args.args), 0)
        self.assertTrue(_CONTROLS.is_file())


if __name__ == "__main__":
    unittest.main()
