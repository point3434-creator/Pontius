from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import ast
import copy
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_fixed_width_device_preflight as device
from pontius import legal_river_quotient_fixed_width_device_preflight_result as reader
from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
)


ROOT = Path(__file__).parents[1]
GIT = os.environ.get("PONTIUS_GIT") or shutil.which("git")
if GIT is None or not Path(GIT).is_absolute():
    raise RuntimeError("an absolute Git executable is required for these fixtures")
SOURCE = ROOT / "src/pontius/legal_river_quotient_fixed_width_device_preflight.py"
LIVE_CRLF_FIXTURE = b"left\r\nright"
FIXTURE_DEPENDENCIES = ("tests/test_legal_river_quotient_fixed_width_device_preflight.py",)
WORKER_MODULE = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"


def resource_streams() -> tuple[bytes, bytes, bytes]:
    ptxas_lines = []
    cubin_lines = []
    sass_lines = []
    for name in device.KERNEL_NAMES:
        ptxas_lines.extend(
            (
                f"ptxas info    : Compiling entry function '{name}' for 'sm_120'",
                f"ptxas info    : Function properties for {name}",
                "    0 bytes stack frame, 0 bytes spill stores, 0 bytes spill loads",
                "ptxas info    : Used 32 registers, 384 bytes cmem[0]",
            )
        )
        cubin_lines.extend((f"Function {name}:", " REG:32 STACK:0 LOCAL:0 SHARED:0"))
        sass_lines.extend((f".global {name}", " MOV R0, R0;"))
    return (
        ("\n".join(ptxas_lines) + "\n").encode("ascii"),
        ("\n".join(cubin_lines) + "\n").encode("ascii"),
        ("\n".join(sass_lines) + "\n").encode("ascii"),
    )


def command_evidence(
    argv: tuple[str, ...], stdout: bytes = b"", stderr: bytes = b""
) -> dict[str, object]:
    return device.BoundedCommand(
        argv=argv,
        return_code=0,
        stdout=stdout,
        stderr=stderr,
        elapsed_ns=1,
        status="completed",
    ).evidence()


def synthetic_output_digests(population: str, arm: str) -> object:
    if arm == device.POSITIONAL:
        return {
            name: sha256((population + arm + name).encode()).hexdigest()
            for name in reader.OUTPUT_NAMES
        }
    batches = (
        (tuple(range(9)),)
        if arm == device.RESIDENT_RRNS
        else ((0, 1, 2, 3, 8), (4, 5, 6, 7))
    )
    return {
        str(batch): {
            name: sha256((population + arm + str(batch) + name).encode()).hexdigest()
            for name in reader.OUTPUT_NAMES
        }
        for batch in batches
    }


def synthetic_rrns_fault_evidence(value: int = 720) -> dict[str, object]:
    def codeword(label: str, decoded: int, moduli: tuple[int, ...]) -> dict[str, object]:
        return {
            "label": label,
            "decoded_decimal": str(decoded),
            "residues": [decoded % modulus for modulus in moduli],
        }

    table_moduli = reader.TABLE_WORKING_MODULI + (reader.REDUNDANT_MODULUS,)
    scalar_moduli = reader.SCALAR_WORKING_MODULI + (reader.REDUNDANT_MODULUS,)
    return {
        "schema_version": "fixed-width-device-rrns-fault-evidence-v1",
        "changed_residue_delta": 1,
        "table_code": {
            "working_moduli": list(reader.TABLE_WORKING_MODULI),
            "redundant_modulus": reader.REDUNDANT_MODULUS,
            "absolute_bound_decimal": str(reader.TABLE_ABSOLUTE_BOUND),
            "codewords": [codeword("source_encoding_first", 11, table_moduli)],
        },
        "scalar_code": {
            "working_moduli": list(reader.SCALAR_WORKING_MODULI),
            "redundant_modulus": reader.REDUNDANT_MODULUS,
            "absolute_bound_decimal": str(reader.SCALAR_ABSOLUTE_BOUND),
            "codewords": [
                codeword(label, value, scalar_moduli)
                for label in ("forward_numerator", "adjoint_numerator", "reach")
            ],
        },
        "correlated_control": {
            **codeword("forward_numerator_plus_720", value + 720, scalar_moduli),
            "unbounded_authority_decimal": str(value),
        },
    }


def synthetic_campaign(append_event):
    ptxas_raw, cubin_raw, sass_raw = resource_streams()
    ptxas = device.parse_ptxas_verbose(ptxas_raw)
    cubin_rows = device.parse_cuobjdump_resource_usage(cubin_raw)
    sass = device.parse_nvdisasm_local_sites(sass_raw)
    driver = {
        name: device.DriverResource(
            kernel=name,
            registers=32,
            local_bytes=0,
            shared_bytes=0,
            maximum_threads_per_block=1024,
        )
        for name in device.KERNEL_NAMES
    }
    effective = device.combine_resource_evidence(
        ptxas, cubin_rows, sass, driver, device_shared_limit_bytes=65_536
    )
    compiler_options = list(device.NVCC_OPTIONS)
    cubin = bytes((0x7F, 0x45, 0x4C, 0x46)) + b"synthetic-cubin"
    compile_argv = device.compile_argv(Path("synthetic.cu"), Path("synthetic.cubin"))
    append_event(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-fixed-width-device-bootstrap-v1",
            "literal_worker_module": WORKER_MODULE,
            "argv_count": 1,
            "python_no_bytecode": True,
            "cupy_loaded": False,
            "scientific_source_loaded": False,
            "parent_journal_present": True,
        },
    )
    append_event(
        "tool_identity_and_cuda_source_materialization",
        {
            "schema_version": "fixed-width-device-source-materialization-v1",
            "cuda_source_sha256": device.CUDA_SOURCE_SHA256,
            "cuda_source_bytes": len(device.CUDA_SOURCE.encode("utf-8")),
            "compiler_options": compiler_options,
        },
    )
    append_event(
        "tool_versions",
        {
            "schema_version": "fixed-width-device-tool-versions-v1",
            "commands": {
                "nvcc": command_evidence((str(device.NVCC_PATH), "--version"), b"release 13.3"),
                "cuobjdump": command_evidence((str(device.CUOBJDUMP_PATH), "--version"), b"V13.3"),
                "nvdisasm": command_evidence(
                    (str(device.NVDISASM_PATH), "--version"), b"release 13.3"
                ),
            },
        },
    )
    append_event(
        "compile",
        {
            "schema_version": "fixed-width-device-compile-v1",
            "command": command_evidence(compile_argv, ptxas_raw),
        },
    )
    append_event(
        "durable_cubin_capture",
        {
            "schema_version": "fixed-width-device-cubin-capture-v1",
            "cubin": device.encode_binary(cubin),
            "zero_suffix_or_repair_applied": False,
        },
    )
    for command_id, raw in (
        ("cuobjdump_resource_usage", cubin_raw),
        ("nvdisasm", sass_raw),
    ):
        append_event(
            "external_resource_command",
            {
                "schema_version": "fixed-width-device-resource-command-v1",
                "command_id": command_id,
                "command": command_evidence((command_id, "synthetic.cubin"), raw),
                "inspected_cubin_sha256": sha256(cubin).hexdigest(),
            },
        )
    runtime = {
        "device_name": "NVIDIA GeForce RTX 5080",
        "compute_capability": "120",
        "device_total_bytes": device.EXPECTED_DEVICE_TOTAL_BYTES,
        "multiprocessor_count": 84,
        "maximum_threads_per_multiprocessor": 1536,
        "maximum_shared_bytes_per_block": 65_536,
        "cuda_driver_version": 13030,
        "cuda_runtime_version": 13020,
        "cupy_version": "synthetic",
    }
    append_event(
        "live_hardware_identity",
        {
            "schema_version": "fixed-width-device-live-hardware-v1",
            "runtime": runtime,
        },
    )
    append_event(
        "module_load_and_resource_evidence",
        {
            "schema_version": "fixed-width-device-resource-evidence-v1",
            "cubin_sha256": sha256(cubin).hexdigest(),
            "runtime": runtime,
            "ptxas": {name: asdict(row) for name, row in ptxas.items()},
            "cuobjdump": {name: asdict(row) for name, row in cubin_rows.items()},
            "sass": {name: asdict(row) for name, row in sass.items()},
            "driver": {name: asdict(row) for name, row in driver.items()},
            "effective": {name: asdict(row) for name, row in effective.items()},
            "arm_streams": {
                "count": 3,
                "arms": list(device.ARMS),
                "one_persistent_nonblocking_stream_per_arm": True,
            },
        },
    )

    clock = 1000
    laboratory_rows = []
    authority_manifests = []

    def add_phase(name: str) -> dict[str, object]:
        nonlocal clock
        row = {"name": name, "start_ns": clock, "end_ns": clock + 1, "elapsed_ns": 1}
        clock += 1
        laboratory_rows.append(row)
        return row

    for name in device.GLOBAL_PHASE_NAMES[:6]:
        add_phase(name)
    observations = []
    timed = {population: {arm: 0 for arm in device.ARMS} for population in device.POPULATIONS}
    schedule = device._candidate_schedule()
    for population_index, population in enumerate(device.POPULATIONS):
        add_phase(device.GLOBAL_PHASE_NAMES[6 + population_index])
        input_sha256 = sha256(population.encode("ascii")).hexdigest()
        manifest = {
            "schema_version": "fixed-width-device-reduced-authority-manifest-v1",
            "population": population,
            "input_sha256": input_sha256,
            "geometry": dict(reader.EXPECTED_GEOMETRY[population]),
            "representation_digests": {
                arm: synthetic_output_digests(population, arm)
                for arm in device.ARMS
            },
            "scalar_values_decimal": {
                "forward_numerator": "720",
                "adjoint_numerator": "720",
                "reach": "720",
            },
            "conditional_value_bits": 0,
        }
        authority_manifests.append(manifest)
        append_event("reduced_population_authority", manifest)
        for schedule_index, (kind, arm, repeat, descending) in enumerate(schedule):
            names = device.phase_names_for_arm(arm)
            phase_rows = [add_phase(name) for name in names]
            total = len(names)
            if kind == "timed":
                timed[population][arm] += total
            event = {
                "schema_version": "fixed-width-device-candidate-run-v1",
                "arm": arm,
                "population": population,
                "traversal_order": "descending_colex" if descending else "ascending_colex",
                "input_sha256": input_sha256,
                "phase_partition": {"rows": phase_rows, "total_ns": total},
                "scalar_values_decimal": {
                    "forward_numerator": "720",
                    "adjoint_numerator": "720",
                    "reach": "720",
                },
                "conditional_value_bits": 0,
                "exact_verified": True,
                "schedule_kind": kind,
                "repeat_index": repeat,
                "arm_order_index": schedule_index,
            }
            if arm == device.POSITIONAL:
                event["output_digests"] = synthetic_output_digests(population, arm)
            else:
                event["batch_output_digests"] = synthetic_output_digests(
                    population, arm
                )
                event["single_changed_channel_controls"] = 32
                event["correlated_fault_boundary"] = "rrns_passed_unbounded_differential_rejected"
                event["rrns_fault_evidence"] = synthetic_rrns_fault_evidence()
            observations.append(event)
    add_phase(device.GLOBAL_PHASE_NAMES[-1])
    laboratory = {
        "schema_version": "fixed-width-device-laboratory-partition-v1",
        "rows": laboratory_rows,
        "total_ns": len(laboratory_rows),
        "exact_sum": True,
    }
    memory = device.symbolic_literal45_liveness()
    eligibility = {}
    for arm in device.ARMS:
        walls = {
            population: {
                "elapsed_ns": timed[population][arm],
                "ceiling_ns": device.PER_POPULATION_ARM_WALL_NS,
                "passed": True,
            }
            for population in device.POPULATIONS
        }
        memory_pass = bool(memory[arm]["liveness"]["eligible"])
        eligibility[arm] = {
            "resource_eligible": True,
            "symbolic_literal_45_memory_eligible": memory_pass,
            "complete_reduced_exactness": True,
            "RRNS_fault_contract": True,
            "compile_and_resource_wall": True,
            "laboratory_wall": True,
            "timed_population_walls": walls,
            "eligible": memory_pass,
        }
    append_event("symbolic_literal_45_memory_liveness", memory)
    for event in observations:
        append_event("candidate_observation", event)
    append_event("laboratory_partition", laboratory)
    append_event("candidate_eligibility", eligibility)
    terminal = {
        "schema_version": "legal-river-quotient-fixed-width-device-preflight-v1",
        "terminal": "completed_device_preflight",
        "passed": True,
        "cuda_source_sha256": device.CUDA_SOURCE_SHA256,
        "cubin_sha256": sha256(cubin).hexdigest(),
        "runtime": runtime,
        "compile_and_resource_elapsed_ns": 5,
        "resource_rows": {name: asdict(row) for name, row in effective.items()},
        "symbolic_literal_45_memory_liveness": memory,
        "candidate_observations": observations,
        "authority_manifests": authority_manifests,
        "observed_counts": {
            population: {
                arm: {
                    "warmup": 1,
                    "timed_ascending": 3,
                    "timed_descending": 3,
                }
                for arm in device.ARMS
            }
            for population in device.POPULATIONS
        },
        "laboratory_partition": laboratory,
        "eligibility": eligibility,
        "candidate_selected": None,
        "claims": dict(reader.SCIENTIFIC_CLAIMS),
    }
    append_event("terminal_evidence", terminal)
    return terminal


def transformed_synthetic_campaign(transform):
    def campaign(append_event):
        def transformed_append(kind, payload):
            copied = copy.deepcopy(payload)
            transform(kind, copied)
            append_event(kind, copied)

        return synthetic_campaign(transformed_append)

    return campaign


def synthetic_journal(campaign_executor=synthetic_campaign, *, public_elapsed_ns=1_000_000):
    """Build reader input in memory; this fixture launches no process or device."""
    header = {
        "schema_version": "legal-river-fixed-width-device-owner-header-v1",
        "protocol_sha256": reader.PROTOCOL_SHA256,
        "campaign_sha256": reader.CAMPAIGN_SHA256,
        "config_sha256": reader.CONFIG_SHA256,
        "correction_config_sha256": reader.CORRECTION_CONFIG_SHA256,
        "preregistration_commit": device.PREREGISTRATION_COMMIT,
        "correction_commit": device.CORRECTION_COMMIT,
        "source_seal_git": {"commit": "0" * 40, "dirty": False, "strict_status": True},
        "dependency_hashes": {
            relative: sha256((ROOT / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for relative in FIXTURE_DEPENDENCIES
        },
        "result_relative_path": reader.RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": (
            "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
        ),
        "literal_worker_module": WORKER_MODULE,
        "scientific_module": "pontius.legal_river_quotient_fixed_width_device_preflight",
        "claims": dict(reader.HEADER_CLAIMS),
    }
    observations = []

    def append_event(kind, event):
        observations.append({
            "schema_version": "legal-river-fixed-width-device-owner-observation-v1",
            "event_index": len(observations),
            "kind": kind,
            "event": dict(event),
            "source_commit": "0" * 40,
        })

    try:
        evidence = campaign_executor(append_event)
        terminal_name = evidence["terminal"]
        reason = "retained first terminal from the frozen one-shot owner"
    except RuntimeError as error:
        terminal_name = "infrastructure_failure"
        reason = f"RuntimeError: {error}"
    laboratory_elapsed = next(
        (row["event"]["total_ns"] for row in observations if row["kind"] == "laboratory_partition"),
        None,
    )
    claims = dict(reader.HEADER_CLAIMS)
    claims["device_preflight_result"] = (
        True if terminal_name in {"completed_device_preflight", "completed_no_device_candidate"}
        else None
    )
    terminal = {
        "schema_version": "legal-river-fixed-width-device-owner-terminal-v1",
        "terminal": terminal_name,
        "passed": terminal_name == "completed_device_preflight",
        "reason": reason,
        "event_count": len(observations),
        "public_elapsed_ns": public_elapsed_ns,
        "public_wall_ns": reader.PUBLIC_WALL_NS,
        "laboratory_elapsed_ns": laboratory_elapsed,
        "laboratory_wall_ns": reader.LABORATORY_WALL_NS,
        "outside_laboratory_elapsed_ns": (
            None if laboratory_elapsed is None else public_elapsed_ns - laboratory_elapsed
        ),
        "outside_laboratory_wall_ns": reader.OUTSIDE_LABORATORY_WALL_NS,
        "claims": claims,
    }
    payloads = [(JournalRecordKind.HEADER, header)]
    payloads.extend((JournalRecordKind.OBSERVATION, row) for row in observations)
    payloads.append((JournalRecordKind.TERMINAL, terminal))
    previous = None
    lines = []
    for sequence, (kind, payload) in enumerate(payloads):
        body = build_journal_record_body(
            protocol_sha256=reader.PROTOCOL_SHA256,
            campaign_sha256=reader.CAMPAIGN_SHA256,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=sha256(canonical_journal_json_bytes(payload)).hexdigest(),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


class FixedWidthDeviceTests(unittest.TestCase):
    def setUp(self) -> None:
        # The reader still checks real dependency bytes, scoped to this synthetic fixture.
        self.enterContext(patch.object(reader, "DEPENDENCY_RELATIVE_PATHS", FIXTURE_DEPENDENCIES))

    def test_imports_are_cuda_process_and_result_free(self) -> None:
        command = (
            "import hashlib, importlib, json, pathlib, sys; "
            "p=pathlib.Path('artifacts/work_preflight/"
            "legal_river_quotient_fixed_width_device_preflight_v1.jsonl'); "
            "before=p.read_bytes() if p.is_file() else None; "
            "mods=['pontius.legal_river_quotient_fixed_width_device_preflight',"
            "'pontius.legal_river_quotient_fixed_width_device_preflight_result']; "
            "[importlib.import_module(x) for x in mods]; "
            "after=p.read_bytes() if p.is_file() else None; "
            "print(json.dumps({'cupy':any(x=='cupy' or x.startswith('cupy.') for x in sys.modules),"
            "'before':None if before is None else hashlib.sha256(before).hexdigest(),"
            "'after':None if after is None else hashlib.sha256(after).hexdigest(),"
            "'unchanged':before==after}))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", command],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            check=True,
            capture_output=True,
            text=True,
        )
        evidence = json.loads(completed.stdout)
        expected = (
            sha256(reader.RESULT_PATH.read_bytes()).hexdigest()
            if reader.RESULT_PATH.is_file()
            else None
        )
        self.assertEqual(
            evidence,
            {"cupy": False, "before": expected, "after": expected, "unchanged": True},
        )

    def test_configuration_phase_topology_is_corrected(self) -> None:
        config = device.load_preregistered_config()
        self.assertEqual(
            config["schema_version"], "legal-river-quotient-fixed-width-device-preflight-v1"
        )
        self.assertEqual(len(device.SINGLE_PASS_PHASE_NAMES), 12)
        self.assertEqual(len(device.BATCHED_PHASE_NAMES), 20)
        self.assertEqual(len(device._candidate_schedule()), 21)
        self.assertEqual(
            device.phase_names_for_arm(device.BATCHED_RRNS)[9],
            "first_batch_output_drain_and_workspace_reuse_boundary",
        )
        self.assertIn("scalar_output_transfer", device.BATCHED_PHASE_NAMES[17])
        attributes = subprocess.run(
            [GIT, "check-attr", "text", "--", device.RESULT_RELATIVE_PATH],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(
            attributes.strip().replace("\\", "/"),
            f"{device.RESULT_RELATIVE_PATH}: text: unset",
        )

    def test_normalizers_and_literal_escape_controls(self) -> None:
        expected = b"left" + bytes((10,)) + b"right"
        self.assertEqual(device.normalize_crlf_bytes(LIVE_CRLF_FIXTURE), expected)
        self.assertEqual(device.independent_normalize_crlf_bytes(LIVE_CRLF_FIXTURE), expected)
        with tempfile.TemporaryDirectory() as directory:
            armed_path = Path(directory) / "armed.py"
            armed_path.write_bytes(repr(LIVE_CRLF_FIXTURE).encode("ascii"))
            receipt = device.literal_escape_mutation_receipt(
                armed_path, expected_occurrences=1, require_armed=True
            )
            self.assertNotEqual(receipt.canonical_lf_sha256, receipt.forbidden_mutation_sha256)
            path = Path(directory) / "unarmed.bin"
            path.write_bytes(b"no trigger")
            with self.assertRaisesRegex(ValueError, "unarmed_literal_escape_mutation"):
                device.literal_escape_mutation_receipt(
                    path, expected_occurrences=0, require_armed=True
                )
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        independent = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "independent_normalize_crlf_bytes"
        )
        calls = [node for node in ast.walk(independent) if isinstance(node, ast.Call)]
        self.assertFalse(any(
            isinstance(call.func, ast.Name) and call.func.id == "normalize_crlf_bytes"
            for call in calls
        ))
        self.assertFalse(any(
            isinstance(call.func, ast.Attribute) and call.func.attr == "replace" for call in calls
        ))

    def test_cuda_source_and_compiler_inventory_are_literal(self) -> None:
        contract = device.cuda_source_contract()
        self.assertEqual(tuple(contract["kernel_names"]), device.KERNEL_NAMES)
        self.assertEqual(len(device.KERNEL_NAMES), 16)
        self.assertEqual(device.CUDA_SOURCE.count('extern "C" __global__ void'), 16)
        self.assertNotIn("inverse_720", device.CUDA_SOURCE.lower())
        self.assertNotIn("level_six", device.CUDA_SOURCE.lower())
        argv = device.compile_argv(Path("a.cu"), Path("a.cubin"))
        self.assertEqual(argv[1:9], device.NVCC_OPTIONS)
        self.assertEqual(argv[9], "--output-file")

    def test_rrns_drain_retains_residues_and_defers_authority_to_verification(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("drain_and_verify", source)
        first_drain = source.index("batch_output_digests[str(batch)] = drain_outputs(batch)")
        second_drain = source.index(
            "batch_output_digests[str(last_batch)] = drain_outputs(last_batch)"
        )
        differential = source.index("for batch in batches:", second_drain)
        table_fault = source.index("table_codeword = fixed.RRNSValue", differential)
        self.assertLess(first_drain, second_drain)
        self.assertLess(second_drain, differential)
        self.assertLess(differential, table_fault)
        self.assertIn("capture_scalar_residues(last_batch)", source[first_drain:second_drain])
        self.assertEqual(source.count("cp.cuda.Stream(non_blocking=True)"), 1)
        self.assertIn("streams = {arm: cp.cuda.Stream(non_blocking=True) for arm in ARMS}", source)
        self.assertIn("stream = context.streams[POSITIONAL]", source)
        self.assertIn("stream = context.streams[arm]", source)

    def test_resource_parsers_preserve_semantic_quantities_and_maxima(self) -> None:
        ptxas_raw, cubin_raw, sass_raw = resource_streams()
        ptxas = device.parse_ptxas_verbose(ptxas_raw)
        cubin = device.parse_cuobjdump_resource_usage(cubin_raw)
        sass = device.parse_nvdisasm_local_sites(sass_raw)
        driver = {
            name: device.DriverResource(name, 34, 19, 7, 1024)
            for name in device.KERNEL_NAMES
        }
        first = device.KERNEL_NAMES[0]
        ptxas[first] = replace(ptxas[first], registers=33, stack_frame_bytes=17)
        cubin[first] = replace(
            cubin[first], registers=35, stack_bytes=11, local_bytes=13, shared_bytes=5
        )
        combined = device.combine_resource_evidence(
            ptxas, cubin, sass, driver, device_shared_limit_bytes=8
        )
        self.assertEqual(combined[first].registers, 35)
        self.assertEqual(combined[first].backing_bytes, 24)
        self.assertEqual(combined[first].shared_bytes, 7)
        self.assertTrue(combined[first].eligible)
        spilled = dict(ptxas)
        spilled[first] = replace(
            spilled[first], spill_store_bytes=8, spill_load_bytes=16
        )
        spilled_combined = device.combine_resource_evidence(
            spilled, cubin, sass, driver, device_shared_limit_bytes=8
        )
        self.assertFalse(spilled_combined[first].eligible)
        self.assertEqual(spilled_combined[first].backing_bytes, 24)
        self.assertEqual(spilled_combined[first].spill_store_bytes, 8)
        local_sites = device.parse_nvdisasm_local_sites(
            sass_raw.replace(b" MOV R0, R0;", b" LDL R0, [R1];\n STL [R1], R0;", 1)
        )
        self.assertEqual(local_sites[first].local_load_sites, 1)
        self.assertEqual(local_sites[first].local_store_sites, 1)
        self.assertEqual(
            device.combine_resource_evidence(
                ptxas, cubin, local_sites, driver, device_shared_limit_bytes=8
            )[first].backing_bytes,
            24,
        )
        with self.assertRaises(ValueError):
            device.parse_ptxas_verbose(ptxas_raw.replace(b"Used 32 registers", b"Used 32 register"))
        with self.assertRaises(ValueError):
            device.parse_ptxas_verbose(
                ptxas_raw.replace(
                    b"0 bytes stack frame, 0 bytes spill stores, 0 bytes spill loads",
                    b"0 bytes stack frame",
                    1,
                )
            )
        duplicated = ptxas_raw + ptxas_raw
        with self.assertRaises(ValueError):
            device.parse_ptxas_verbose(duplicated)
        with self.assertRaises(ValueError):
            device.parse_cuobjdump_resource_usage(cubin_raw.replace(b" REG:32", b""))
        with self.assertRaises(ValueError):
            device.parse_cuobjdump_resource_usage(cubin_raw + cubin_raw)
        with self.assertRaises(ValueError):
            device.parse_nvdisasm_local_sites(
                sass_raw.replace(b".global positional_contract", b".weak positional_contract")
            )

    def test_binary_phase_wall_and_memory_boundaries_fail_closed(self) -> None:
        encoded = device.encode_binary(b"abc")
        self.assertEqual(device.decode_binary(encoded, maximum=3), b"abc")
        altered = dict(encoded)
        altered["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            device.decode_binary(altered, maximum=3)
        stamps = list(range(13))
        partition = device.phase_partition(device.SINGLE_PASS_PHASE_NAMES, stamps)
        self.assertEqual(partition.total_ns, 12)
        self.assertEqual(sum(row.elapsed_ns for row in partition.rows), 12)
        with self.assertRaises(ValueError):
            device.phase_partition(device.BATCHED_PHASE_NAMES, stamps)
        bad = list(range(21))
        bad[10] = bad[9] - 1
        with self.assertRaises(ValueError):
            device.phase_partition(device.BATCHED_PHASE_NAMES, bad)
        self.assertTrue(device.wall_passes(29_999_999_999, 30_000_000_000))
        self.assertTrue(device.wall_passes(30_000_000_000, 30_000_000_000))
        self.assertFalse(device.wall_passes(30_000_000_001, 30_000_000_000))
        exact = device.memory_liveness(
            (device.BufferLifetime(
                "x", "x", device.EXPECTED_DEVICE_TOTAL_BYTES - device.DEVICE_RESERVE_BYTES, 0, 1
            ),),
            boundary_count=2,
        )
        self.assertTrue(exact.eligible)
        over = device.memory_liveness(
            (device.BufferLifetime(
                "x", "x", device.EXPECTED_DEVICE_TOTAL_BYTES - device.DEVICE_RESERVE_BYTES + 1, 0, 1
            ),),
            boundary_count=2,
        )
        self.assertFalse(over.eligible)
        with self.assertRaises(ValueError):
            device.memory_liveness(
                (
                    device.BufferLifetime("a", "same", 1, 0, 2),
                    device.BufferLifetime("b", "same", 1, 1, 2),
                ),
                boundary_count=3,
            )

    def test_command_streams_are_concurrently_bounded_before_parse(self) -> None:
        completed = device.run_bounded_command(
            (sys.executable, "-B", "-c",
             "import sys;sys.stdout.write('x'*4096);sys.stderr.write('y'*4096)"),
            wall_ns=5_000_000_000,
            stdout_limit=128,
            stderr_limit=128,
            cwd=ROOT,
        )
        self.assertEqual(completed.status, "output_limit")
        self.assertIsNone(completed.return_code)
        self.assertLessEqual(len(completed.stdout), 129)
        self.assertLessEqual(len(completed.stderr), 129)

    def test_symbolic_hybrid_liveness_and_batched_reuse_are_exact(self) -> None:
        rows = device.symbolic_literal45_liveness()
        self.assertTrue(rows[device.POSITIONAL]["liveness"]["eligible"])
        self.assertFalse(rows[device.RESIDENT_RRNS]["liveness"]["eligible"])
        self.assertTrue(rows[device.BATCHED_RRNS]["liveness"]["eligible"])
        for arm in device.ARMS:
            self.assertFalse(rows[arm]["fixed_width_level_six_materialized"])
            self.assertEqual(rows[arm]["forward_workspace_levels"], [0, 1, 2, 3, 4, 5])
        batched = rows[device.BATCHED_RRNS]["buffers"]
        identities = [row["storage_identity"] for row in batched]
        self.assertGreater(identities.count("recurrence_workspace"), 1)

    def test_signed_schoolbook_matches_unbounded_boundary_and_random_oracle(self) -> None:
        values = (0, 1, -1, (1 << 63) - 1, -(1 << 63), (1 << 255) - 1, -(1 << 255))
        rng = random.Random(440)
        cases = list(values) + [rng.randrange(-(1 << 250), 1 << 250) for _ in range(200)]
        for left in cases:
            for right in values:
                words = device.signed_schoolbook_product_words(
                    left, right, left_limbs=5, right_limbs=5, output_limbs=8
                )
                self.assertEqual(device.words_to_signed_integer(words), left * right)
        with self.assertRaises(OverflowError):
            device.signed_schoolbook_product_words(
                1 << 319, 1, left_limbs=5, right_limbs=5, output_limbs=8
            )

    @unittest.skipUnless(hasattr(math, "fma"), "host pair arithmetic requires math.fma")
    def test_reduced_population_authorities_and_representation_bytes_rebind(self) -> None:
        for label, source_rows, query_rows in (("complete_10", 210, 210), ("signed_12", 924, 495)):
            # Historical source admission is outside this numerical fixture.
            with patch(
                "pontius.legal_river_quotient_consumer_capacity.verify_preregistered_dependencies"
            ):
                population = device.build_validation_population(label)
            self.assertEqual(len(population.authority.source_rows), source_rows)
            self.assertEqual(len(population.authority.forward_scaled_rows), query_rows)
            positional = device._representation_expectations(population, arm=device.POSITIONAL)
            first = device._representation_expectations(
                population, arm=device.BATCHED_RRNS, channel_indices=(0, 1, 2, 3, 8)
            )
            second = device._representation_expectations(
                population, arm=device.BATCHED_RRNS, channel_indices=(4, 5, 6, 7)
            )
            self.assertEqual(set(positional), set(first))
            self.assertEqual(set(first), set(second))
            self.assertTrue(all(len(first[name]) * 4 == len(second[name]) * 5 for name in first))
            manifest = device._reduced_authority_manifest(
                population,
                positional=positional,
                resident={tuple(range(9)): device._representation_expectations(
                    population,
                    arm=device.RESIDENT_RRNS,
                    channel_indices=tuple(range(9)),
                )},
                batched={
                    (0, 1, 2, 3, 8): first,
                    (4, 5, 6, 7): second,
                },
            )
            parsed = reader._parse_authority_manifest(manifest, population=label)
            self.assertEqual(parsed["input_sha256"], population.input_sha256)

    def test_reader_recomputes_exactness_faults_and_cubin_identity(self) -> None:
        def mutate_candidate_and_terminal(mutator):
            def transform(kind, payload):
                if kind == "candidate_observation" and (
                    payload["population"] == "complete_10"
                    and payload["arm"] == device.RESIDENT_RRNS
                    and payload["schedule_kind"] == "warmup"
                ):
                    mutator(payload)
                if kind == "terminal_evidence":
                    mutator(payload["candidate_observations"][1])

            return transform

        def wrong_digest(payload):
            key = str(tuple(range(9)))
            payload["batch_output_digests"][key]["source_encoding"] = "0" * 64

        def wrong_fault_codeword(payload):
            payload["rrns_fault_evidence"]["scalar_code"]["codewords"][0][
                "residues"
            ][0] += 1

        def wrong_inspected_cubin(kind, payload):
            if kind == "external_resource_command" and payload["command_id"] == (
                "cuobjdump_resource_usage"
            ):
                payload["inspected_cubin_sha256"] = "0" * 64

        cases = (
            ("authority digest", mutate_candidate_and_terminal(wrong_digest)),
            ("RRNS codeword", mutate_candidate_and_terminal(wrong_fault_codeword)),
            ("inspected cubin", wrong_inspected_cubin),
        )
        for label, transform in cases:
            with self.subTest(label=label):
                raw = synthetic_journal(transformed_synthetic_campaign(transform))
                with self.assertRaises(ValueError):
                    reader.assess_device_preflight_bytes(raw)

    def test_noncanonical_evidence_and_unknown_serializer_types_reject(self) -> None:
        with self.assertRaises(TypeError):
            device._serialize_dataclass_rows({"unknown": object()})
        with self.assertRaises(TypeError):
            canonical_journal_json_bytes({"unknown": object()})
        for value in (1, "01", "-0", "+1", "1.0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reader._decimal_integer(value, label="synthetic large integer")

    def test_synthetic_journal_and_independent_reader_agree(self) -> None:
        raw = synthetic_journal()
        assessed = reader.assess_device_preflight_bytes(raw)
        self.assertEqual(assessed.terminal, "completed_device_preflight")
        self.assertTrue(assessed.passed)
        self.assertEqual(assessed.eligible_arms, (device.POSITIONAL, device.BATCHED_RRNS))
        with self.assertRaises(ValueError):
            reader.assess_device_preflight_bytes(raw + b"torn")
        mutated = bytearray(raw)
        mutated[len(mutated) // 2] ^= 1
        with self.assertRaises(ValueError):
            reader.assess_device_preflight_bytes(bytes(mutated))

    def test_infrastructure_terminal_is_readable(self) -> None:
        def failing_campaign(append_event):
            append_event(
                "bootstrap_handshake",
                {
                    "schema_version": "legal-river-fixed-width-device-bootstrap-v1",
                    "cupy_loaded": False,
                    "scientific_source_loaded": False,
                    "parent_journal_present": True,
                    "python_no_bytecode": True,
                },
            )
            raise RuntimeError("synthetic transport failure")

        raw = synthetic_journal(failing_campaign, public_elapsed_ns=10)
        assessed = reader.assess_device_preflight_bytes(raw)
        self.assertEqual(assessed.terminal, "infrastructure_failure")
        self.assertFalse(assessed.passed)


if __name__ == "__main__":
    unittest.main()
