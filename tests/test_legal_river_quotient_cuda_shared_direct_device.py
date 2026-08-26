from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
from math import comb
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius import legal_river_quotient_cuda_shared_direct_device as device
from pontius import legal_river_quotient_cuda_shared_direct_device_result as reader
from pontius import legal_river_quotient_cuda_shared_direct_device_runner as runner


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / reader.CONFIG_RELATIVE_PATH
_RESULT = _ROOT / reader.RESULT_RELATIVE_PATH
_RESERVED = _ROOT / reader.RESERVED_ACTUAL_RESULT_RELATIVE_PATH


def _semantic(payload: dict[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _journal(payloads: list[tuple[JournalRecordKind, dict[str, object]]]) -> bytes:
    previous: str | None = None
    lines: list[bytes] = []
    for sequence, (kind, payload) in enumerate(payloads):
        body = build_journal_record_body(
            protocol_sha256=reader.PROTOCOL_SHA256,
            campaign_sha256=reader.CAMPAIGN_SHA256,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=_semantic(payload),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


def _minimal_infrastructure_journal() -> bytes:
    header = {
        "schema_version": "legal-river-shared-direct-owner-header-v1",
        "config_sha256": reader.CONFIG_SHA256,
        "preregistration_commit": "a457f8f73d2f69a66ac3d52361d1e96ddf0f02ac",
        "source_seal_git": {
            "commit": "1" * 40,
            "dirty": False,
            "strict_status": True,
        },
        "dependency_hashes": {
            relative: "2" * 64 for relative in reader.DEPENDENCY_RELATIVE_PATHS
        },
        "result_relative_path": reader.RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": (
            reader.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ),
        "claims": dict(reader.CLAIMS),
    }
    handshake = {
        "schema_version": "legal-river-shared-direct-owner-observation-v1",
        "kind": "bootstrap_handshake",
        "event": {
            "schema_version": "legal-river-shared-direct-handshake-v1",
            "challenge_sha256": "3" * 64,
            "literal_module": reader.LITERAL_WORKER_MODULE,
            "spec_name": reader.LITERAL_WORKER_MODULE,
            "runtime_name": "__main__",
            "cupy_imported": False,
        },
        "config_sha256": reader.CONFIG_SHA256,
    }
    claims = dict(reader.CLAIMS)
    claims.update(
        {
            "device_differential_result": False,
            "complete_10_result": False,
            "complete_22_result": False,
        }
    )
    terminal = {
        "schema_version": "legal-river-shared-direct-owner-terminal-v1",
        "terminal": "infrastructure_failure",
        "passed": False,
        "reason": "synthetic source-seal control",
        "event_count": 0,
        "handshake_passed": True,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
        "claims": claims,
    }
    return _journal(
        [
            (JournalRecordKind.HEADER, header),
            (JournalRecordKind.OBSERVATION, handshake),
            (JournalRecordKind.TERMINAL, terminal),
        ]
    )


def _observation(kind: str, event: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "legal-river-shared-direct-owner-observation-v1",
        "kind": kind,
        "event": event,
        "config_sha256": reader.CONFIG_SHA256,
    }


def _synthetic_phases(
    population: int, *, host_start: int
) -> tuple[list[dict[str, object]], int, dict[str, int]]:
    path = (
        "fixture_and_resident_birth",
        "forward_source_and_offset",
        "shared_direct_fold_and_query",
        "forward_recurrence",
        "forward_signed_targets",
        "forward_fold_and_global_tree",
        "forward_capture_and_digest",
        "forward_release",
        "adjoint_covector_and_labels",
        "adjoint_recurrence_and_signed_sources",
        "direct_adjoint",
        "adjoint_recurrence_and_signed_sources",
        "adjoint_source_contract_and_global_tree",
        "adjoint_capture_digest_and_exact_stream",
        "mutations_and_lifecycle",
        "final_release",
    )
    expected = reader.expected_shared_campaign_work(population)
    events: list[dict[str, object]] = []
    phase_totals = {phase: 0 for phase in reader.PHASE_ORDER}
    current = host_start
    for family in reader.FAMILIES:
        assigned: set[str] = set()
        chunks = list(reader._expected_chunks(population, family))
        for ordinal, phase in enumerate(path):
            work: dict[str, int] = {}
            for counter in reader._PHASE_COUNTERS.get(phase, set()):
                if counter not in assigned:
                    total = expected[counter]
                    if total % 2:
                        raise AssertionError(f"synthetic work is not divisible: {counter}")
                    work[counter] = total // 2
                    assigned.add(counter)
            event = {
                "schema_version": "legal-river-shared-direct-phase-v1",
                "ordinal": ordinal,
                "population": population,
                "family": family,
                "repeat": 0,
                "tile": 0,
                "phase": phase,
                "host_start_ns": current,
                "host_stop_ns": current + 1,
                "host_ns": 1,
                "device_ns": 1,
                "chunks": chunks,
                "work": work,
            }
            events.append(event)
            phase_totals[phase] += 1
            current += 1
    return events, current, phase_totals


def _synthetic_population(
    population: int,
    phases: list[dict[str, object]],
    phase_totals: dict[str, int],
) -> dict[str, object]:
    errors = {name: [0, 1] for name in reader._ERROR_LIMITS}
    if population == 10:
        errors.update(
            {
                name: [0, 1]
                for name in (
                    "complete_fraction_source_absolute",
                    "complete_fraction_source_relative",
                    "complete_fraction_forward_absolute",
                    "complete_fraction_forward_relative",
                    "complete_fraction_fold_absolute",
                    "complete_fraction_fold_relative",
                    "complete_fraction_adjoint_absolute",
                    "complete_fraction_adjoint_relative",
                )
            }
        )
    gates = {name: True for name in reader._ERROR_TO_GATE.values()}
    if population == 10:
        gates.update({name: True for name in errors if name.startswith("complete_")})
    gates.update(
        {
            "default_alternate_byte_identity": True,
            "repeat_snapshot_restore_byte_identity": True,
            "inactive_final_tile_poison": True,
            "source_global_offset_control": True,
            "nonzero_query_offset": True,
            "nonzero_source_offset": True,
            "forward_release_before_adjoint": True,
            "accumulator_lifecycle": True,
            "missing_label_mutation_rejected": True,
            "pool_release": True,
            "chip_units": True,
            "executed_work_ledger_exact": True,
            "phase_partition_exact": True,
            "all_fifteen_phases_observed": True,
            "population_reference_query_launches_zero": True,
            "shared_fold_launch_count": True,
            "population_wall": True,
        }
    )
    expected = reader.expected_shared_campaign_work(population)
    return {
        "schema_version": "legal-river-work-preflight-population-evidence-v1",
        "population": population,
        "scalar_pairs": {"numerator": ["0x0.0p+0", "0x0.0p+0"]},
        "conditional_value": [0, 1],
        "maximum_errors": errors,
        "reporting_digests": {
            name: "4" * 64
            for name in (
                "source_samples",
                "query_samples",
                "fold_samples",
                "adjoint_samples",
                "direct_samples",
                "contribution_streams",
            )
        },
        "telemetry": {
            "maximum_pool_total_bytes": 1,
            "maximum_host_numeric_bytes": 1,
        },
        "gates": gates,
        "all_gates_pass": True,
        "phase_host_ns": phase_totals,
        "campaign_host_ns": len(phases),
        "population_elapsed_host_ns": len(phases) + 8,
        "executed_work": expected,
        "expected_work": expected,
        "launch_counts": [
            {"direct_selected_fold_tile": 6},
            {"direct_selected_fold_tile": 6},
        ],
    }


def _complete_synthetic_journal() -> bytes:
    header = {
        "schema_version": "legal-river-shared-direct-owner-header-v1",
        "config_sha256": reader.CONFIG_SHA256,
        "preregistration_commit": "a457f8f73d2f69a66ac3d52361d1e96ddf0f02ac",
        "source_seal_git": {
            "commit": "5" * 40,
            "dirty": False,
            "strict_status": True,
        },
        "dependency_hashes": {
            relative: "6" * 64 for relative in reader.DEPENDENCY_RELATIVE_PATHS
        },
        "result_relative_path": reader.RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": (
            reader.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ),
        "claims": dict(reader.CLAIMS),
    }
    events: list[tuple[str, dict[str, object]]] = [
        (
            "bootstrap_handshake",
            {
                "schema_version": "legal-river-shared-direct-handshake-v1",
                "challenge_sha256": "7" * 64,
                "literal_module": reader.LITERAL_WORKER_MODULE,
                "spec_name": reader.LITERAL_WORKER_MODULE,
                "runtime_name": "__main__",
                "cupy_imported": False,
            },
        ),
        (
            "runtime",
            {
                "schema_version": "legal-river-shared-direct-runtime-v1",
                "runtime": {
                    "device_name": "synthetic",
                    "compute_capability": "00",
                    "device_total_bytes": 1,
                    "cuda_driver_version": 1,
                    "cuda_runtime_version": 1,
                    "cupy_version": "synthetic",
                },
                "built_cuda_source_sha256": reader.BUILT_CUDA_SOURCE_SHA256,
            },
        ),
    ]
    payload = device.reference_repaired_cubin()
    device._emit_raw_chunks(
        lambda kind, event: events.append((kind, dict(event))),
        kind="compiler_payload_chunk",
        stream_id="shared_nvrtc_payload",
        raw=payload,
    )
    container = device.classify_compiler_payload(payload)
    events.extend(
        [
            (
                "compiler_payload_terminal",
                {
                    "schema_version": "legal-river-shared-direct-compiler-payload-v1",
                    "stream_id": "shared_nvrtc_payload",
                    "byte_count": len(payload),
                    "sha256": sha256(payload).hexdigest(),
                    "built_cuda_source_sha256": reader.BUILT_CUDA_SOURCE_SHA256,
                    "caller_supplied_nvrtc_options": [
                        "--std=c++14",
                        "--ftz=false",
                        "--prec-div=true",
                        "--prec-sqrt=true",
                        "--fmad=false",
                    ],
                },
            ),
            (
                "container",
                {
                    "schema_version": "legal-river-shared-direct-container-v1",
                    "mode": container.mode,
                    "raw_sha256": container.raw_sha256,
                    "raw_bytes": container.raw_bytes,
                    "loaded_sha256": container.loaded_sha256,
                    "loaded_bytes": container.loaded_bytes,
                    "appended_suffix_hex": "",
                    "header": dict(container.header),
                    "program_header_count": container.program_header_count,
                    "section_header_count": container.section_header_count,
                    "section_table_sha256": container.section_table_sha256,
                },
            ),
            (
                "module",
                {
                    "schema_version": "legal-river-shared-direct-module-v1",
                    "loaded_sha256": sha256(payload).hexdigest(),
                    "loaded_bytes": len(payload),
                    "retained_object_is_loaded_object": True,
                    "resolved_function_names": list(device._v4.KERNEL_NAMES),
                },
            ),
        ]
    )
    version = b"Cuda compilation tools, release 13.3"
    resource_text = (
        "Function direct_selected_queries_tile:\n REG:20 STACK:0 LOCAL:8\n"
        "Function direct_selected_fold_tile:\n REG:30 STACK:16 LOCAL:8\n"
        "Function direct_selected_adjoint_tile:\n REG:40 STACK:0 LOCAL:32\n"
    ).encode("ascii")
    for command_id, role, stdout in (
        ("cuobjdump_version", "cuobjdump --version", version),
        (
            "cuobjdump_resource_usage",
            "cuobjdump --dump-resource-usage shared-payload",
            resource_text,
        ),
    ):
        device._emit_raw_chunks(
            lambda kind, event: events.append((kind, dict(event))),
            kind="resource_command_chunk",
            stream_id=f"{command_id}:stdout",
            raw=stdout,
        )
        events.append(
            (
                "resource_command_terminal",
                {
                    "schema_version": "legal-river-shared-direct-command-v1",
                    "command_id": command_id,
                    "argv_role": role,
                    "status": "completed",
                    "return_code": 0,
                    "stdout_bytes": len(stdout),
                    "stdout_sha256": sha256(stdout).hexdigest(),
                    "stderr_bytes": 0,
                    "stderr_sha256": sha256(b"").hexdigest(),
                    "elapsed_ns": 1,
                },
            )
        )
    direct = reader._parse_resources(resource_text.decode("ascii"))
    driver = {
        name: {
            "local_size_bytes": 0,
            "registers": 10,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        }
        for name in reader.DIRECT_KERNEL_NAMES
    }
    maxima = {
        name: {
            "registers": direct[name]["REG"],
            "stack_plus_local_backing_bytes": direct[name]["STACK"] + direct[name]["LOCAL"],
        }
        for name in reader.DIRECT_KERNEL_NAMES
    }
    events.extend(
        [
            (
                "resource_cleanup",
                {
                    "schema_version": "legal-river-shared-direct-cleanup-v1",
                    "temporary_created": True,
                    "temporary_removed": True,
                },
            ),
            (
                "resource",
                {
                    "schema_version": "legal-river-shared-direct-resource-v1",
                    "tool_version": version.decode("ascii"),
                    "shared_cubin_sha256": sha256(payload).hexdigest(),
                    "shared_cubin_bytes": len(payload),
                    "direct": direct,
                    "driver_direct": driver,
                    "effective_maxima": maxima,
                    "runtime_residency": {
                        "multiprocessor_count": 84,
                        "maximum_threads_per_multiprocessor": 1536,
                        "maximum_resident_threads": 129024,
                        "backing_ceiling_bytes_per_thread": 4096,
                        "maximum_resident_backing_bytes": 528482304,
                        "frozen_device_reserve_bytes": 2000000000,
                    },
                    "gates": {
                        "register_ceiling": True,
                        "local_and_stack_ceiling": True,
                        "resident_thread_bound": True,
                        "resident_backing_within_device_reserve": True,
                    },
                    "exact_spill_load_store_count": None,
                },
            ),
            (
                "primitive",
                {
                    "schema_version": "legal-river-shared-direct-primitive-v1",
                    "operation_count": 1,
                    "maximum_absolute_errors": {"pair": "0x0.0p+0"},
                    "low_lane_nonzero_counts": {"pair": 1},
                    "reporting_digest": "8" * 64,
                    "gates": {"primitive": True},
                    "direct_order_controls": {
                        "gates": {"order": True},
                        "all_gates_pass": True,
                    },
                },
            ),
            (
                "reference_module",
                {
                    "schema_version": "legal-river-shared-direct-reference-module-v1",
                    "reference_repaired_cubin_sha256": (
                        reader.REFERENCE_REPAIRED_CUBIN_SHA256
                    ),
                    "reference_repaired_cubin_bytes": 514040,
                    "allowed_function_names": [
                        "direct_selected_queries_tile",
                        "direct_selected_fold_tile",
                    ],
                },
            ),
            (
                "complete_ten_control",
                {
                    "schema_version": (
                        "legal-river-shared-direct-complete-ten-control-v1"
                    ),
                    "population": 10,
                    "reference_query_launches": 3,
                    "reference_fold_launches": 3,
                    "shared_primary_launches": 3,
                    "shared_repeat_launches": 3,
                    "reference_digests": ["9" * 64] * 3,
                    "shared_digests": ["9" * 64] * 3,
                    "gates": {"identity": True},
                    "all_gates_pass": True,
                },
            ),
            (
                "reference_release",
                {
                    "schema_version": "legal-river-shared-direct-reference-release-v1",
                    "reference_functions_unreachable": True,
                },
            ),
            (
                "query_weight",
                {
                    "schema_version": "legal-river-shared-direct-query-weight-v1",
                    "records": [0],
                    "maximum_absolute_error": "0x0.0p+0",
                    "nonzero_low_count": 1,
                    "reporting_digest": "a" * 64,
                    "gates": {"query_weight": True},
                },
            ),
        ]
    )
    host = 100
    for population in (10, 22):
        phases, host, totals = _synthetic_phases(population, host_start=host)
        events.extend(("phase", phase) for phase in phases)
        events.append(
            (
                "population",
                _synthetic_population(population, phases, totals),
            )
        )
    terminal_evidence = {
        "schema_version": "legal-river-shared-direct-terminal-evidence-v1",
        "terminal": "completed_validation_pass",
        "passed": True,
        "reason": "synthetic complete pass",
        "failed_population": None,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
    }
    events.append(("terminal_evidence", terminal_evidence))
    claims = dict(reader.CLAIMS)
    claims.update(
        {
            "device_differential_result": True,
            "complete_10_result": True,
            "complete_22_result": True,
        }
    )
    outer = {
        "schema_version": "legal-river-shared-direct-owner-terminal-v1",
        "terminal": "completed_validation_pass",
        "passed": True,
        "reason": "synthetic complete pass",
        "event_count": len(events) - 1,
        "handshake_passed": True,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
        "claims": claims,
    }
    payloads: list[tuple[JournalRecordKind, dict[str, object]]] = [
        (JournalRecordKind.HEADER, header)
    ]
    payloads.extend(
        (JournalRecordKind.OBSERVATION, _observation(kind, event))
        for kind, event in events
    )
    payloads.append((JournalRecordKind.TERMINAL, outer))
    return _journal(payloads)


def _commandless_cleanup_journal() -> bytes:
    recovery = recover_journal_bytes(
        _complete_synthetic_journal(),
        expected_protocol_sha256=reader.PROTOCOL_SHA256,
        expected_campaign_sha256=reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    header = deepcopy(recovery.records[0].body.payload)
    observations: list[dict[str, object]] = []
    retained_kinds = {
        "bootstrap_handshake",
        "runtime",
        "compiler_payload_chunk",
        "compiler_payload_terminal",
        "container",
        "module",
        "resource_cleanup",
    }
    for record in recovery.records[1:-1]:
        payload = deepcopy(record.body.payload)
        kind = payload.get("kind")
        event = payload.get("event")
        if kind in retained_kinds:
            observations.append(payload)
        elif kind == "resource_command_chunk" and isinstance(event, dict):
            if str(event.get("stream_id", "")).startswith("cuobjdump_version:"):
                observations.append(payload)
        elif kind == "resource_command_terminal" and isinstance(event, dict):
            if event.get("command_id") == "cuobjdump_version":
                observations.append(payload)
    reason = "synthetic commandless cleanup"
    observations.append(
        _observation(
            "terminal_evidence",
            {
                "schema_version": "legal-river-shared-direct-terminal-evidence-v1",
                "terminal": "resource_rejection",
                "passed": False,
                "reason": reason,
                "failed_population": None,
                "capacity_projection": None,
                "complete_25_numerical_value": None,
            },
        )
    )
    claims = dict(reader.CLAIMS)
    claims.update(
        {
            "device_differential_result": False,
            "complete_10_result": False,
            "complete_22_result": False,
        }
    )
    outer = {
        "schema_version": "legal-river-shared-direct-owner-terminal-v1",
        "terminal": "resource_rejection",
        "passed": False,
        "reason": reason,
        "event_count": len(observations) - 1,
        "handshake_passed": True,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
        "claims": claims,
    }
    return _journal(
        [(JournalRecordKind.HEADER, header)]
        + [
            (JournalRecordKind.OBSERVATION, observation)
            for observation in observations
        ]
        + [(JournalRecordKind.TERMINAL, outer)]
    )


def _rewrite(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=reader.PROTOCOL_SHA256,
        expected_campaign_sha256=reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    return _journal(
        [
            (record.body.kind, payload)
            for record, payload in zip(recovery.records, payloads, strict=True)
        ]
    )


class _WorkLedger:
    def __init__(self) -> None:
        self.mutation_mode = False
        self.direction = "forward"
        self.work: dict[str, int] = {}

    def add_work(self, name: str, count: int) -> None:
        self.work[name] = self.work.get(name, 0) + count


class SharedDirectDeviceSourceSealTests(unittest.TestCase):
    def test_config_source_seal_and_result_absence(self) -> None:
        self.assertEqual(device.canonical_lf_sha256(_CONFIG), reader.CONFIG_SHA256)
        self.assertTrue(device.source_seal_report()["all_gates_pass"])
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_fresh_imports_are_cupy_free_and_do_not_execute_device_work(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device as d; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device_runner; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device_result; "
            "assert 'cupy' not in sys.modules; "
            "assert d.cupy_import_call_count() == 0"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            env={**os.environ, "PYTHONPATH": "src;."},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_reader_is_owner_adapter_and_cupy_independent(self) -> None:
        path = _ROOT / "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        self.assertTrue(
            {
                "cupy",
                "legal_river_quotient_cuda_shared_direct_device",
                "legal_river_quotient_cuda_shared_direct_device_runner",
            }.isdisjoint({name.rsplit(".", 1)[-1] for name in imported})
        )

    def test_complete_and_one_zero_elf_modes_are_exactly_equivalent(self) -> None:
        complete = device.reference_repaired_cubin()
        device_complete = device.classify_compiler_payload(complete)
        device_one_zero = device.classify_compiler_payload(complete[:-1])
        reader_complete = reader._classify_payload(complete)
        reader_one_zero = reader._classify_payload(complete[:-1])
        self.assertEqual(device_complete.mode, "complete_elf_without_edit")
        self.assertEqual(
            device_one_zero.mode,
            "one_zero_final_program_alignment_completion",
        )
        self.assertEqual(device_complete.loaded, device_one_zero.loaded)
        self.assertEqual(reader_complete[1], reader_one_zero[1])
        self.assertEqual(reader_complete[1], complete)
        self.assertEqual(reader_complete[2]["header"], dict(device_complete.header))

    def test_elf_admission_rejects_every_nonfrozen_nearby_mutation(self) -> None:
        complete = device.reference_repaired_cubin()
        mutations = (
            complete[:-2],
            complete[:-1] + b"\x01",
            b"NOTELF" + complete[6:],
        )
        for raw in mutations:
            with self.subTest(size=len(raw), prefix=raw[:8]):
                with self.assertRaises(ValueError):
                    device.classify_compiler_payload(raw)
                with self.assertRaises(ValueError):
                    reader._classify_payload(raw)

    def test_generated_sources_make_only_the_frozen_substitutions(self) -> None:
        forward, population = device.generated_function_sources()
        report = device.source_seal_report()
        self.assertEqual(forward.count("_shared_direct_forward_samples("), 1)
        self.assertNotIn("_direct_forward_samples(", forward.replace(
            "_shared_direct_forward_samples(", ""
        ))
        self.assertEqual(population.count("collect_direct = True"), 1)
        self.assertEqual(population.count("_phase_hook("), 3)
        self.assertNotIn("fixture.available_cards == 25", population)
        self.assertEqual(
            sha256(forward.encode()).hexdigest(), report["generated_forward_sha256"]
        )
        self.assertEqual(
            sha256(population.encode()).hexdigest(),
            report["generated_population_sha256"],
        )

    def test_fake_compiler_retains_before_interpretation_and_loads_same_bytes(self) -> None:
        payload = device.reference_repaired_cubin()[:-1]
        modules: list[object] = []

        class FakeModule:
            def __init__(self) -> None:
                self.loaded: bytes | None = None
                modules.append(self)

            def load(self, raw: bytes) -> None:
                self.loaded = raw

            def get_function(self, name: str) -> str:
                return name

        fake = SimpleNamespace(
            cuda=SimpleNamespace(
                compiler=SimpleNamespace(
                    compile_using_nvrtc=lambda *_args, **_kwargs: (payload, None)
                ),
                function=SimpleNamespace(Module=FakeModule),
            )
        )
        events: list[tuple[str, dict[str, object]]] = []
        rebound = device.compile_and_load_shared_module(
            fake,
            lambda kind, event: events.append((kind, dict(event))),
        )
        kinds = [kind for kind, _event in events]
        self.assertLess(kinds.index("compiler_payload_terminal"), kinds.index("container"))
        self.assertLess(kinds.index("container"), kinds.index("module"))
        self.assertEqual(
            rebound.container.mode,
            "one_zero_final_program_alignment_completion",
        )
        self.assertIs(modules[0].loaded, rebound.shared_payload)
        self.assertEqual(rebound.shared_payload, device.reference_repaired_cubin())

    def test_fused_signature_counts_feature_and_logical_width_separately(self) -> None:
        ledger = _WorkLedger()
        tracker = device._CampaignTracker(ledger, 10)
        arguments: list[object] = [0] * 12
        arguments[2] = 5
        arguments[3] = 10
        arguments[7] = 7
        arguments[9] = 3
        arguments[11] = 64
        tracker.after_kernel("direct_selected_fold_tile", tuple(arguments))
        self.assertEqual(
            ledger.work,
            {
                "shared_direct_source_unranks": 35,
                "shared_direct_compatible_coefficient_pair_adds": (
                    7 * comb(6, 6) * 64
                ),
                "shared_direct_boundary_pair_copies": 21,
                "shared_direct_final_feature_pair_products": 448,
            },
        )
        self.assertNotEqual(
            ledger.work["shared_direct_compatible_coefficient_pair_adds"],
            7 * comb(6, 6) * 3,
        )

    def test_independent_work_rederivation_matches_adapter_and_rejects_25(self) -> None:
        for population in (10, 22):
            self.assertEqual(
                reader.expected_shared_campaign_work(population),
                device.expected_shared_campaign_work(population),
            )
        with self.assertRaises(ValueError):
            reader.expected_shared_campaign_work(25)
        with self.assertRaises(ValueError):
            device.expected_shared_campaign_work(25)

    def test_phase_ledger_partitions_a_full_valid_control_path(self) -> None:
        ticks = iter(range(100, 10_000, 10))
        ledger = device.SharedPhaseLedger(
            population=10,
            family=device._v4.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            device_terminal=lambda: 1,
            emit=None,
            deadline_ns=100_000,
            clock_ns=lambda: next(ticks),
        )
        ledger.start(repeat=0, tile=0)
        path = (
            "forward_source_and_offset",
            "shared_direct_fold_and_query",
            "forward_recurrence",
            "forward_signed_targets",
            "forward_fold_and_global_tree",
            "forward_capture_and_digest",
            "forward_release",
            "adjoint_covector_and_labels",
            "adjoint_recurrence_and_signed_sources",
            "direct_adjoint",
            "adjoint_recurrence_and_signed_sources",
            "adjoint_source_contract_and_global_tree",
            "adjoint_capture_digest_and_exact_stream",
            "mutations_and_lifecycle",
            "final_release",
        )
        for phase in path:
            ledger.switch(phase, repeat=0, tile=0)
        rows = ledger.finish()
        self.assertEqual({row.phase for row in rows}, set(device.PHASE_ORDER))
        self.assertEqual(
            sum(row.host_ns for row in rows),
            rows[-1].host_stop_ns - rows[0].host_start_ns,
        )
        self.assertTrue(
            all(left.host_stop_ns == right.host_start_ns for left, right in zip(rows, rows[1:]))
        )

    def test_phase_ledger_rejects_a_skipped_phase(self) -> None:
        ticks = iter((10, 20))
        ledger = device.SharedPhaseLedger(
            population=10,
            family=device._v4.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            device_terminal=lambda: 1,
            emit=None,
            deadline_ns=100,
            clock_ns=lambda: next(ticks),
        )
        ledger.start(repeat=0, tile=0)
        with self.assertRaises(ValueError):
            ledger.switch("forward_recurrence", repeat=0, tile=0)

    def test_raw_stream_reconstruction_is_exact_and_mutations_fail(self) -> None:
        events: list[tuple[str, dict[str, object]]] = []
        raw = bytes(range(256)) * 1000
        device._emit_raw_chunks(
            lambda kind, event: events.append((kind, dict(event))),
            kind="compiler_payload_chunk",
            stream_id="control",
            raw=raw,
        )
        indexed = [(index, event) for index, (_kind, event) in enumerate(events)]
        self.assertEqual(
            reader._reconstruct_stream(
                indexed, stream_id="control", terminal_position=len(indexed)
            ),
            raw,
        )
        broken = deepcopy(indexed)
        broken[0][1]["chunk_base64"] = broken[0][1]["chunk_base64"][:-4] + "AAAA"
        with self.assertRaises(ValueError):
            reader._reconstruct_stream(
                broken, stream_id="control", terminal_position=len(broken)
            )

    def test_independent_resource_derivation_and_mutation_control(self) -> None:
        loaded = b"sealed-cubin-control"
        text = (
            "Function direct_selected_queries_tile:\n REG:20 STACK:0 LOCAL:8\n"
            "Function direct_selected_fold_tile:\n REG:30 STACK:16 LOCAL:8\n"
            "Function direct_selected_adjoint_tile:\n REG:40 STACK:0 LOCAL:32\n"
        )
        direct = reader._parse_resources(text)
        driver = {
            name: {
                "local_size_bytes": 0,
                "registers": 10,
                "shared_size_bytes": 0,
                "maximum_threads_per_block": 1024,
            }
            for name in reader.DIRECT_KERNEL_NAMES
        }
        maxima = {
            name: {
                "registers": direct[name]["REG"],
                "stack_plus_local_backing_bytes": (
                    direct[name]["STACK"] + direct[name]["LOCAL"]
                ),
            }
            for name in reader.DIRECT_KERNEL_NAMES
        }
        residency = {
            "multiprocessor_count": 84,
            "maximum_threads_per_multiprocessor": 1536,
            "maximum_resident_threads": 129024,
            "backing_ceiling_bytes_per_thread": 4096,
            "maximum_resident_backing_bytes": 528482304,
            "frozen_device_reserve_bytes": 2000000000,
        }
        gates = {
            "register_ceiling": True,
            "local_and_stack_ceiling": True,
            "resident_thread_bound": True,
            "resident_backing_within_device_reserve": True,
        }
        event = {
            "schema_version": "legal-river-shared-direct-resource-v1",
            "tool_version": "Cuda compilation tools, release 13.3",
            "shared_cubin_sha256": sha256(loaded).hexdigest(),
            "shared_cubin_bytes": len(loaded),
            "direct": direct,
            "driver_direct": driver,
            "effective_maxima": maxima,
            "runtime_residency": residency,
            "gates": gates,
            "exact_spill_load_store_count": None,
        }
        commands = {
            "cuobjdump_version": {
                "status": "completed",
                "return_code": 0,
                "stdout": b"Cuda compilation tools, release 13.3",
                "stderr": b"",
            },
            "cuobjdump_resource_usage": {
                "status": "completed",
                "return_code": 0,
                "stdout": text.encode("ascii"),
                "stderr": b"",
            },
        }
        reader._validate_resource(event, commands, loaded=loaded)
        mutated = deepcopy(event)
        mutated["effective_maxima"]["direct_selected_fold_tile"]["registers"] += 1
        with self.assertRaises(ValueError):
            reader._validate_resource(mutated, commands, loaded=loaded)

    def test_every_child_terminal_type_is_honestly_typed(self) -> None:
        for terminal in sorted(reader.ALLOWED_TERMINALS - {"infrastructure_failure"}):
            event = {
                "schema_version": "legal-river-shared-direct-terminal-evidence-v1",
                "terminal": terminal,
                "passed": terminal == "completed_validation_pass",
                "reason": "synthetic typed terminal",
                "failed_population": None,
                "capacity_projection": None,
                "complete_25_numerical_value": None,
            }
            self.assertEqual(reader._validate_terminal_evidence(event)[0], terminal)
            violated = dict(event)
            violated["capacity_projection"] = [1, 1]
            with self.assertRaises(ValueError):
                reader._validate_terminal_evidence(violated)

    def test_minimal_infrastructure_journal_rebinds_and_distortions_fail(self) -> None:
        raw = _minimal_infrastructure_journal()
        rebound = reader.rebind_shared_direct_device_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "infrastructure_failure")
        self.assertFalse(rebound.passed)
        self.assertEqual(rebound.populations, ())
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_journal(
                raw[:-1], rebind_current_sources=False
            )
        corrupted = _rewrite(
            raw,
            lambda payloads: payloads[-1].__setitem__("capacity_projection", [1, 1]),
        )
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_journal(
                corrupted, rebind_current_sources=False
            )

    def test_commandless_cleanup_is_bound_to_an_early_failure(self) -> None:
        raw = _commandless_cleanup_journal()
        rebound = reader.rebind_shared_direct_device_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "resource_rejection")
        self.assertFalse(rebound.passed)

        def mutate_terminal(payloads) -> None:
            evidence = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "terminal_evidence"
            )
            evidence["terminal"] = "complete_ten_differential_rejection"
            payloads[-1]["terminal"] = "complete_ten_differential_rejection"

        impossible = _rewrite(raw, mutate_terminal)
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_journal(
                impossible, rebind_current_sources=False
            )

    def test_complete_synthetic_journal_rebinds_every_layer(self) -> None:
        raw = _complete_synthetic_journal()
        rebound = reader.rebind_shared_direct_device_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "completed_validation_pass")
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.container_mode, "complete_elf_without_edit")
        self.assertTrue(rebound.complete_ten_control_passed)
        self.assertEqual(rebound.populations, (10, 22))
        self.assertEqual(len(rebound.phases), 64)

        def mutate(payloads) -> None:
            population = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "population"
            )
            population["population_elapsed_host_ns"] = 1

        corrupted = _rewrite(raw, mutate)
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_journal(
                corrupted, rebind_current_sources=False
            )

        def overlap_families(payloads) -> None:
            phases = [
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "phase"
                and payload["event"]["population"] == 10
            ]
            first_family_stop = max(
                phase["host_stop_ns"]
                for phase in phases
                if phase["family"] == reader.FAMILIES[0]
            )
            first_second_family = next(
                phase
                for phase in phases
                if phase["family"] == reader.FAMILIES[1]
            )
            first_second_family["host_start_ns"] = first_family_stop - 1
            first_second_family["host_ns"] = (
                first_second_family["host_stop_ns"]
                - first_second_family["host_start_ns"]
            )
            population = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "population"
                and payload["event"]["population"] == 10
            )
            phase_name = first_second_family["phase"]
            population["phase_host_ns"][phase_name] += 1
            population["campaign_host_ns"] += 1

        overlapping = _rewrite(raw, overlap_families)
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_journal(
                overlapping, rebind_current_sources=False
            )

    def test_real_minus_b_no_cupy_handshake_crosses_transport(self) -> None:
        handshake = runner.run_no_cuda_bootstrap_handshake()
        self.assertEqual(handshake["runtime_name"], "__main__")
        self.assertFalse(handshake["cupy_imported"])


if __name__ == "__main__":
    unittest.main()
