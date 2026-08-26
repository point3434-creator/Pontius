from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from pontius.legal_river_exact_cubin_inspector_diagnostic_result import (
    BinaryEvidence,
    CandidateEvidence,
    ExactCubinDiagnosticRebinding,
)
import pontius.legal_river_exact_cubin_inspector_selection as selection
from pontius.legal_river_exact_cubin_inspector_selection_seal import (
    ADR0408_SELECTOR_SOURCE_SHA256,
)
from pontius import legal_river_quotient_cuda_compensated_work_preflight as science


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / selection.CONFIG_RELATIVE_PATH
_SOURCE = _ROOT / "src/pontius/legal_river_exact_cubin_inspector_selection.py"
_RESULT = _ROOT / selection.RESULT_RELATIVE_PATH
_RESERVED = _ROOT / selection.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
_EMPTY_SHA = sha256(b"").hexdigest()
_IDENTITY = (
    b"cuobjdump: NVIDIA (R) fat binary listing tool\r\n"
    b"Copyright (c) 2005-2026 NVIDIA Corporation\r\n"
    b"Cuda compilation tools, release 13.3, V13.3.73\r\n"
    b"Build cuda_13.3.r13.3/compiler.38244171_0\r\n"
)
_VALID_RESOURCE = b"""Resource usage:
 Common:
  GLOBAL:56 CONSTANT[3]:28
 Function unrelated_kernel:
  REG:7 STACK:1 LOCAL:2
 Function direct_selected_queries_tile:
  REG:32 STACK:64 SHARED:0 LOCAL:128 CONSTANT[0]:16
 Function direct_selected_fold_tile:
  REG:64 STACK:1024 SHARED:0 LOCAL:256 CONSTANT[0]:16
 Function direct_selected_adjoint_tile:
  REG:48 STACK:128 SHARED:0 LOCAL:64 CONSTANT[0]:16
"""


def _binary(raw: bytes) -> BinaryEvidence:
    return BinaryEvidence(raw=raw, sha256=sha256(raw).hexdigest(), byte_count=len(raw))


def _candidate(
    candidate_id: str,
    *,
    return_code: int | None = 0,
    status: str = "completed",
    stdout: bytes = b"",
    stderr: bytes = b"",
) -> CandidateEvidence:
    return CandidateEvidence(
        candidate_id=candidate_id,
        return_code=return_code,
        status=status,
        stdout=_binary(stdout),
        stderr=_binary(stderr),
        elapsed_ns=17,
    )


def _candidates(
    *,
    identity_stdout: bytes = _IDENTITY,
    identity_code: int = 0,
    resource_stdout: bytes = _VALID_RESOURCE,
    resource_code: int = 0,
    nvdisasm_stdout: bytes = b"",
    nvdisasm_code: int = 1,
) -> tuple[CandidateEvidence, ...]:
    return (
        _candidate(
            "cuobjdump_version",
            return_code=identity_code,
            stdout=identity_stdout,
        ),
        _candidate(
            "cuobjdump_resource_usage",
            return_code=resource_code,
            stdout=resource_stdout,
        ),
        _candidate("cuobjdump_elf", return_code=1, stdout=b"support"),
        _candidate("nvdisasm_version", stdout=b"identity"),
        _candidate(
            "nvdisasm_default",
            return_code=nvdisasm_code,
            stdout=nvdisasm_stdout,
        ),
    )


def _driver_rows(registers: int = 40, local_bytes: int = 512) -> dict[str, dict[str, int]]:
    return {
        name: {
            "local_size_bytes": local_bytes,
            "maximum_threads_per_block": 1024,
            "registers": registers,
            "shared_size_bytes": 0,
        }
        for name in selection.DIRECT_KERNEL_NAMES
    }


class ExactCubinInspectorSelectionTests(unittest.TestCase):
    def test_preregistered_config_source_seal_and_absence_boundary(self) -> None:
        raw = _CONFIG.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(sha256(raw).hexdigest(), selection.CONFIG_SHA256)
        config = json.loads(raw)
        self.assertTrue(
            config["selection_question"]["empty_selection_is_a_required_reachable_terminal"]
        )
        self.assertTrue(
            config["qualification_contract"][
                "candidate_qualification_does_not_depend_on_whether_a_resource_value_passes_a_ceiling"
            ]
        )
        self.assertEqual(selection.canonical_lf_sha256(_SOURCE), ADR0408_SELECTOR_SOURCE_SHA256)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_valid_resource_candidate_qualifies_with_componentwise_maxima(self) -> None:
        assessment = selection.assess_candidates(
            _candidates(),
            _driver_rows(),
            selector_source_sha256="1" * 64,
        )
        self.assertEqual(assessment.terminal, "qualified_inspector")
        self.assertEqual(assessment.selected_inspector, "cuobjdump_resource_usage")
        self.assertTrue(assessment.identity_contract_pass)
        self.assertIsNotNone(assessment.selected_resource_rows)
        self.assertIsNotNone(assessment.combined_direct_rows)
        assert assessment.combined_direct_rows is not None
        fold = assessment.combined_direct_rows["direct_selected_fold_tile"]
        self.assertEqual(fold["registers_max"], 64)
        self.assertEqual(fold["candidate_stack_plus_local_bytes"], 1280)
        self.assertEqual(fold["local_backing_max_bytes"], 1280)
        self.assertIsNone(assessment.resource_gate_result)
        self.assertNotIn("passed", selection.canonical_assessment_bytes(assessment).decode())

    def test_empty_selection_survives_version_pass_and_resource_failure(self) -> None:
        assessment = selection.assess_candidates(
            _candidates(resource_code=4_294_967_295, resource_stdout=b"not device code"),
            _driver_rows(),
            selector_source_sha256="2" * 64,
        )
        self.assertEqual(assessment.terminal, "no_qualified_inspector")
        self.assertTrue(assessment.identity_contract_pass)
        self.assertIsNone(assessment.selected_inspector)
        self.assertIsNone(assessment.selected_resource_rows)
        self.assertIsNone(assessment.combined_direct_rows)
        resource = assessment.candidate_assessments[1]
        self.assertIn("resource_return_code_nonzero", resource.reasons)

    def test_all_nonzero_and_real_return_code_shape_are_honest_empty_results(self) -> None:
        candidates = tuple(
            _candidate(candidate_id, return_code=index + 1, stdout=b"failure")
            for index, candidate_id in enumerate(selection.CANDIDATE_IDS)
        )
        all_nonzero = selection.assess_candidates(
            candidates,
            _driver_rows(),
            selector_source_sha256="3" * 64,
        )
        self.assertEqual(all_nonzero.terminal, "no_qualified_inspector")

        real_shape = _candidates(
            resource_code=4_294_967_295,
            resource_stdout=b"does not contain device code",
            nvdisasm_code=1,
        )
        retained_shape = selection.assess_candidates(
            real_shape,
            _driver_rows(),
            selector_source_sha256="4" * 64,
        )
        self.assertEqual(retained_shape.terminal, "no_qualified_inspector")

    def test_nvdisasm_register_metadata_and_elf_magic_cannot_select(self) -> None:
        candidates = _candidates(
            resource_code=1,
            resource_stdout=b"\x7fELF",
            nvdisasm_code=0,
            nvdisasm_stdout=(
                b'.sectioninfo @"SHI_REGISTERS=14"\n'
                b"direct_selected_queries_tile\n"
                b"direct_selected_fold_tile\n"
                b"direct_selected_adjoint_tile\n"
            ),
        )
        assessment = selection.assess_candidates(
            candidates,
            _driver_rows(),
            selector_source_sha256="5" * 64,
        )
        self.assertEqual(assessment.terminal, "no_qualified_inspector")
        self.assertEqual(
            assessment.candidate_assessments[4].qualification_status,
            "ineligible_support_only",
        )

    def test_resource_parser_matches_immutable_parser_and_fails_closed(self) -> None:
        selected = selection.parse_cuobjdump_resource_usage(_VALID_RESOURCE)
        inherited = science.parse_cuobjdump_resource_usage(_VALID_RESOURCE.decode("ascii"))
        expected = {
            name: {field: inherited[name][field] for field in ("REG", "STACK", "LOCAL")}
            for name in selection.DIRECT_KERNEL_NAMES
        }
        self.assertEqual(selected, expected)

        reordered = b"\n".join(_VALID_RESOURCE.splitlines()[::-1])
        reordered_selected = selection.parse_cuobjdump_resource_usage(reordered)
        reordered_inherited = science.parse_cuobjdump_resource_usage(
            reordered.decode("ascii")
        )
        self.assertEqual(
            reordered_selected,
            {
                name: {
                    field: reordered_inherited[name][field]
                    for field in ("REG", "STACK", "LOCAL")
                }
                for name in selection.DIRECT_KERNEL_NAMES
            },
        )
        self.assertNotEqual(reordered_selected, selected)
        for mutated in (
            _VALID_RESOURCE.replace(b"Function direct_selected_fold_tile:\n", b""),
            _VALID_RESOURCE.replace(
                b"Function direct_selected_fold_tile:",
                b"Function direct_selected_queries_tile:",
            ),
            _VALID_RESOURCE.replace(b" STACK:1024", b" SPILL:1024"),
            _VALID_RESOURCE + b"\xff",
        ):
            with self.assertRaises(ValueError):
                selection.parse_cuobjdump_resource_usage(mutated)

    def test_field_value_and_quantity_pairing_mutations_change_assessment(self) -> None:
        baseline = selection.assess_candidates(
            _candidates(), _driver_rows(), selector_source_sha256="6" * 64
        )
        changed_resource = _VALID_RESOURCE.replace(b"REG:64", b"REG:65")
        changed = selection.assess_candidates(
            _candidates(resource_stdout=changed_resource),
            _driver_rows(),
            selector_source_sha256="6" * 64,
        )
        self.assertNotEqual(
            selection.canonical_assessment_bytes(baseline),
            selection.canonical_assessment_bytes(changed),
        )
        assert changed.combined_direct_rows is not None
        self.assertEqual(
            changed.combined_direct_rows["direct_selected_fold_tile"]["registers_max"],
            65,
        )

    def test_ceiling_failures_do_not_change_instrument_qualification(self) -> None:
        resource = _VALID_RESOURCE.replace(b"REG:64", b"REG:999").replace(
            b"STACK:1024", b"STACK:5000"
        )
        assessment = selection.assess_candidates(
            _candidates(resource_stdout=resource),
            _driver_rows(),
            selector_source_sha256="7" * 64,
        )
        self.assertEqual(assessment.terminal, "qualified_inspector")
        assert assessment.combined_direct_rows is not None
        fold = assessment.combined_direct_rows["direct_selected_fold_tile"]
        self.assertGreater(fold["registers_max"], selection.REGISTER_CEILING)
        self.assertGreater(
            fold["local_backing_max_bytes"],
            selection.STACK_PLUS_LOCAL_CEILING_BYTES,
        )
        self.assertIsNone(assessment.resource_gate_result)

    def test_identity_candidate_order_and_stream_mutations_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            selection.assess_candidates(
                tuple(reversed(_candidates())),
                _driver_rows(),
                selector_source_sha256="8" * 64,
            )
        assessment = selection.assess_candidates(
            _candidates(identity_stdout=b"cuobjdump 13.3"),
            _driver_rows(),
            selector_source_sha256="8" * 64,
        )
        self.assertEqual(assessment.terminal, "no_qualified_inspector")
        self.assertFalse(assessment.identity_contract_pass)
        non_ascii = selection.assess_candidates(
            _candidates(identity_stdout=_IDENTITY + b"\xff"),
            _driver_rows(),
            selector_source_sha256="8" * 64,
        )
        self.assertFalse(non_ascii.identity_contract_pass)

    def test_synthetic_rebinding_identity_and_mutations(self) -> None:
        raw = b"one\ntwo\n"
        cubin = _binary(b"\x7fELFsynthetic")
        contract = selection.RetainedInputContract(
            artifact_sha256=sha256(raw).hexdigest(),
            artifact_bytes=len(raw),
            artifact_records=2,
            source_commit="a" * 40,
            terminal="capture_complete",
            event_count=10,
            cubin_sha256=cubin.sha256,
            cubin_bytes=cubin.byte_count,
            cubin_magic=b"\x7fELF",
        )
        rebinding = ExactCubinDiagnosticRebinding(
            terminal="capture_complete",
            passed=True,
            event_count=10,
            source_commit="a" * 40,
            cubin=cubin,
            driver_rows=_driver_rows(),
            candidates=_candidates(),
            cleanup={"temporary_cubin_removed": True},
            journal_byte_count=len(raw),
        )
        rows, candidates = selection.validate_rebinding_identity(
            rebinding, raw_artifact=raw, contract=contract
        )
        self.assertEqual(tuple(rows), selection.DIRECT_KERNEL_NAMES)
        self.assertEqual(tuple(c.candidate_id for c in candidates), selection.CANDIDATE_IDS)
        with self.assertRaises(ValueError):
            selection.validate_rebinding_identity(
                rebinding, raw_artifact=raw + b"x", contract=contract
            )
        with self.assertRaises(ValueError):
            selection.validate_rebinding_identity(
                replace(rebinding, source_commit="b" * 40),
                raw_artifact=raw,
                contract=contract,
            )
        with self.assertRaises(ValueError):
            selection.validate_rebinding_identity(
                replace(rebinding, candidates=tuple(reversed(_candidates()))),
                raw_artifact=raw,
                contract=contract,
            )

    def test_import_surface_is_device_process_network_and_write_free(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(
            {"cupy", "subprocess", "socket", "urllib", "requests", "tempfile"}.isdisjoint(
                imported
            )
        )
        self.assertNotIn("run_calibration_preflight", _SOURCE.read_text(encoding="utf-8"))

        command = [
            sys.executable,
            "-B",
            "-c",
            (
                "import json,sys; "
                "before=set(sys.modules); "
                "import pontius.legal_river_exact_cubin_inspector_selection; "
                "after=set(sys.modules); "
                "print(json.dumps(sorted((after-before)&{'cupy','subprocess','socket'})))"
            ),
        ]
        env = os_environ_with_pythonpath()
        completed = subprocess.run(
            command,
            cwd=_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(completed.stdout), [])
        self.assertFalse(_RESULT.exists())

    def test_result_writer_is_no_argument_exclusive_and_refuses_before_input_read(self) -> None:
        self.assertEqual(len(inspect.signature(selection.write_sealed_selection_result).parameters), 0)
        with tempfile.TemporaryDirectory() as directory:
            occupied = Path(directory) / "selection.json"
            occupied.write_bytes(b"owned")
            with mock.patch.object(selection, "_RESULT", occupied), mock.patch.object(
                selection, "_INPUT", Path(directory) / "must-not-be-read"
            ):
                with self.assertRaises(FileExistsError):
                    selection.select_sealed_adr0406_artifact()
            self.assertEqual(occupied.read_bytes(), b"owned")


def os_environ_with_pythonpath() -> dict[str, str]:
    import os

    env = dict(os.environ)
    current = env.get("PYTHONPATH", "")
    source = str(_ROOT / "src")
    env["PYTHONPATH"] = source if not current else source + os.pathsep + current
    return env


if __name__ == "__main__":
    unittest.main()
