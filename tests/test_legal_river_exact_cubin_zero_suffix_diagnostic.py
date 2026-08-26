from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

from pontius import legal_river_exact_cubin_zero_suffix_diagnostic as diagnostic
from pontius import legal_river_exact_cubin_zero_suffix_diagnostic_result as reader
from pontius import legal_river_exact_cubin_zero_suffix_diagnostic_runner as runner


_ROOT = Path(__file__).parents[1]
_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_PROGRAM = struct.Struct("<IIQQQQQQ")
_SECTION = struct.Struct("<IIQQQQIIQQ")
_RESULT = _ROOT / runner.RESULT_RELATIVE_PATH
_RESERVED = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


def _synthetic_elf() -> tuple[bytes, diagnostic.ZeroSuffixStructuralContract]:
    ident = b"\x7fELF\x02\x01\x01\x41\x08" + b"\x00" * 7
    e_shoff = 64
    e_shnum = 2
    e_phoff = e_shoff + e_shnum * _SECTION.size
    e_phnum = 2
    repaired_size = e_phoff + e_phnum * _PROGRAM.size
    header = (
        ident,
        2,
        190,
        1,
        0,
        e_phoff,
        e_shoff,
        0x6007802,
        _HEADER.size,
        _PROGRAM.size,
        e_phnum,
        _SECTION.size,
        e_shnum,
        1,
    )
    sections = (
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, 56, 8, 0, 0, 1, 0),
    )
    programs = (
        (6, 4, e_phoff, 0, 0, e_phnum * _PROGRAM.size, e_phnum * _PROGRAM.size, 8),
        (1, 5, 0, 0, 0, _HEADER.size, _HEADER.size, 8),
    )
    repaired = bytearray(repaired_size)
    repaired[: _HEADER.size] = _HEADER.pack(*header)
    for index, row in enumerate(sections):
        offset = e_shoff + index * _SECTION.size
        repaired[offset : offset + _SECTION.size] = _SECTION.pack(*row)
    for index, row in enumerate(programs):
        offset = e_phoff + index * _PROGRAM.size
        repaired[offset : offset + _PROGRAM.size] = _PROGRAM.pack(*row)
    original = bytes(repaired[:-1])
    final_partial = original[e_phoff + _PROGRAM.size :]
    contract = diagnostic.ZeroSuffixStructuralContract(
        original_sha256=sha256(original).hexdigest(),
        original_bytes=len(original),
        repaired_sha256=sha256(bytes(repaired)).hexdigest(),
        repaired_bytes=len(repaired),
        header=header,
        section_table_end=e_phoff,
        program_table_end=len(repaired),
        complete_program_headers=(programs[0],),
        final_first_seven=programs[1][:-1],
        final_alignment_low_seven=final_partial[-7:],
        repaired_final_program_header=programs[1],
        original_tail_32=original[-32:],
        repaired_tail_32=bytes(repaired[-32:]),
    )
    return original, contract


def _reidentity(
    original: bytes,
    contract: diagnostic.ZeroSuffixStructuralContract,
    **changes: object,
) -> diagnostic.ZeroSuffixStructuralContract:
    repaired = original + b"\x00"
    return replace(
        contract,
        original_sha256=sha256(original).hexdigest(),
        original_bytes=len(original),
        repaired_sha256=sha256(repaired).hexdigest(),
        repaired_bytes=len(repaired),
        program_table_end=len(repaired),
        original_tail_32=original[-32:],
        repaired_tail_32=repaired[-32:],
        **changes,
    )


def _resource_stdout(*, large: bool = False, omit_local: bool = False) -> bytes:
    rows: list[bytes] = []
    for index, name in enumerate(diagnostic.DIRECT_KERNEL_NAMES):
        values = f"REG:{9000 if large else 30 + index} STACK:{8000 if large else index}"
        if not omit_local or index != 1:
            values += f" LOCAL:{7000 if large else 2 * index}"
        rows.append(f"Function {name}:\n {values}\n".encode("ascii"))
    return b"".join(rows)


def _binary(raw: bytes) -> reader.BinaryEvidence:
    return reader.BinaryEvidence(raw=raw, sha256=sha256(raw).hexdigest(), byte_count=len(raw))


def _candidates(
    *,
    required_nonzero: bool = False,
    supporting_nonzero: bool = False,
    large_resources: bool = False,
    incomplete_resources: bool = False,
    status_at: tuple[int, str] | None = None,
) -> list[reader.CandidateEvidence]:
    rows = diagnostic.load_preregistered_config()["candidate_commands_in_order"]
    assert isinstance(rows, list)
    result: list[reader.CandidateEvidence] = []
    for index, row in enumerate(rows):
        assert isinstance(row, dict)
        candidate_id = str(row["candidate_id"])
        stdout = (
            diagnostic._CUOBJDUMP_VERSION_BYTES
            if candidate_id == "cuobjdump_version"
            else _resource_stdout(
                large=large_resources, omit_local=incomplete_resources
            )
            if candidate_id == "cuobjdump_resource_usage"
            else b"support"
        )
        return_code = 0
        if required_nonzero and candidate_id == "cuobjdump_elf":
            return_code = 1
        if supporting_nonzero and candidate_id == "nvdisasm_default":
            return_code = 1
        status = status_at[1] if status_at is not None and status_at[0] == index else "completed"
        result.append(
            reader.CandidateEvidence(
                candidate_id=candidate_id,
                status=status,
                return_code=return_code,
                stdout=_binary(stdout),
                stderr=_binary(b""),
                elapsed_ns=index + 1,
                required=bool(row["required_for_suffix_pass"]),
            )
        )
    return result


class ExactZeroSuffixStructuralTests(unittest.TestCase):
    def test_exact_one_missing_zero_repairs_and_is_prefix_exact(self) -> None:
        original, contract = _synthetic_elf()
        evidence = diagnostic.reconstruct_exact_one_zero(original, contract)
        self.assertEqual(evidence.repaired, original + b"\x00")
        self.assertEqual(evidence.program_headers[-1][-1], 8)
        self.assertEqual(evidence.section_header_count, 2)

    def test_zero_two_extra_and_nonzero_suffix_cases_reject(self) -> None:
        original, contract = _synthetic_elf()
        for mutated in (original + b"\x00", original[:-1], original + b"x"):
            with self.subTest(size=len(mutated)):
                with self.assertRaises(diagnostic.StructuralRejection):
                    diagnostic.reconstruct_exact_one_zero(mutated, contract)
        nonzero_claim = replace(
            contract,
            repaired_sha256=sha256(original + b"\x01").hexdigest(),
        )
        with self.assertRaises(diagnostic.StructuralRejection):
            diagnostic.reconstruct_exact_one_zero(original, nonzero_claim)

    def test_wrong_partial_field_hash_tail_and_program_identity_reject(self) -> None:
        original, contract = _synthetic_elf()
        mutations = (
            replace(contract, final_first_seven=(*contract.final_first_seven[:-1], 65)),
            replace(contract, original_sha256="0" * 64),
            replace(contract, original_tail_32=b"x" * 32),
            replace(
                contract,
                complete_program_headers=(
                    (*contract.complete_program_headers[0][:-1], 16),
                ),
            ),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(diagnostic.StructuralRejection):
                    diagnostic.reconstruct_exact_one_zero(original, mutated)

    def test_section_bounds_and_name_table_controls_reject(self) -> None:
        original, contract = _synthetic_elf()
        header = contract.header
        e_shoff = int(header[6])
        section_one = list(_SECTION.unpack_from(original, e_shoff + _SECTION.size))
        for field, value in ((4, len(original) + 10), (1, 8)):
            mutated = bytearray(original)
            row = section_one.copy()
            row[field] = value
            mutated[e_shoff + _SECTION.size : e_shoff + 2 * _SECTION.size] = _SECTION.pack(
                *row
            )
            adjusted = _reidentity(bytes(mutated), contract)
            with self.subTest(field=field):
                with self.assertRaises(diagnostic.StructuralRejection):
                    diagnostic.reconstruct_exact_one_zero(bytes(mutated), adjusted)

    def test_program_memsz_and_alignment_controls_reject(self) -> None:
        original, contract = _synthetic_elf()
        e_phoff = int(contract.header[5])
        first = list(contract.complete_program_headers[0])
        for field, value in ((6, first[5] - 1), (7, 3), (2, len(original) + 50)):
            row = first.copy()
            row[field] = value
            mutated = bytearray(original)
            mutated[e_phoff : e_phoff + _PROGRAM.size] = _PROGRAM.pack(*row)
            adjusted = _reidentity(
                bytes(mutated), contract, complete_program_headers=(tuple(row),)
            )
            with self.subTest(field=field):
                with self.assertRaises(diagnostic.StructuralRejection):
                    diagnostic.reconstruct_exact_one_zero(bytes(mutated), adjusted)


class ExactZeroSuffixSemanticTests(unittest.TestCase):
    def test_payload_and_stream_limits_are_semantically_separate(self) -> None:
        with (
            mock.patch.object(diagnostic, "MAXIMUM_PAYLOAD_BYTES", 4),
            mock.patch.object(diagnostic, "MAXIMUM_STREAM_BYTES", 8),
        ):
            with self.assertRaisesRegex(ValueError, "repaired payload"):
                diagnostic.encode_payload(b"12345")
            self.assertEqual(diagnostic.encode_stream(b"12345")["byte_count"], 5)
        envelope = diagnostic.encode_stream(b"12345")
        with self.assertRaises(ValueError):
            reader.decode_binary(
                envelope, label="payload control", maximum_bytes=4
            )
        decoded = reader.decode_binary(
            envelope, label="stream control", maximum_bytes=8
        )
        self.assertEqual(decoded.raw, b"12345")

    def test_resource_parser_is_complete_exact_and_order_independent(self) -> None:
        expected = diagnostic.parse_cuobjdump_resource_usage(_resource_stdout())
        observed = reader.parse_cuobjdump_resource_usage(_resource_stdout())
        self.assertEqual(expected, observed)
        self.assertEqual(set(observed), set(diagnostic.DIRECT_KERNEL_NAMES))
        with self.assertRaises(ValueError):
            diagnostic.parse_cuobjdump_resource_usage(_resource_stdout(omit_local=True))
        with self.assertRaises(ValueError):
            reader.parse_cuobjdump_resource_usage(_resource_stdout(omit_local=True))

    def test_supporting_failure_does_not_decide_and_required_failure_does(self) -> None:
        terminal, resources, qualified = reader._derive_scientific_terminal(
            candidates=_candidates(supporting_nonzero=True),
            module_failure=False,
            module_rows=diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
            worker_failure=False,
        )
        self.assertEqual(terminal, "suffix_reconstruction_pass")
        self.assertIsNotNone(resources)
        self.assertEqual(qualified, diagnostic.QUALIFIED_INSTRUMENT)
        terminal, _, qualified = reader._derive_scientific_terminal(
            candidates=_candidates(required_nonzero=True),
            module_failure=False,
            module_rows=diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
            worker_failure=False,
        )
        self.assertEqual(terminal, "tool_rejection")
        self.assertIsNone(qualified)

    def test_ceiling_sized_rows_cannot_change_suffix_validity(self) -> None:
        terminal, resources, qualified = reader._derive_scientific_terminal(
            candidates=_candidates(large_resources=True),
            module_failure=False,
            module_rows=diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
            worker_failure=False,
        )
        self.assertEqual(terminal, "suffix_reconstruction_pass")
        self.assertGreater(resources[diagnostic.DIRECT_KERNEL_NAMES[0]]["REG"], 255)
        self.assertEqual(qualified, diagnostic.QUALIFIED_INSTRUMENT)

    def test_timeout_output_module_and_driver_failures_are_typed(self) -> None:
        cases = (
            (
                _candidates(status_at=(2, "timeout")),
                False,
                diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
                "candidate_timeout_rejection",
            ),
            (
                _candidates(status_at=(4, "output_limit")),
                False,
                diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
                "candidate_output_limit_rejection",
            ),
            (_candidates(), True, None, "module_load_rejection"),
            (
                _candidates(),
                False,
                {
                    **diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
                    diagnostic.DIRECT_KERNEL_NAMES[0]: {
                        **diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS[
                            diagnostic.DIRECT_KERNEL_NAMES[0]
                        ],
                        "registers": 39,
                    },
                },
                "driver_row_rejection",
            ),
        )
        for candidates, module_failure, rows, expected in cases:
            with self.subTest(expected=expected):
                terminal, _, _ = reader._derive_scientific_terminal(
                    candidates=candidates,
                    module_failure=module_failure,
                    module_rows=rows,
                    worker_failure=False,
                )
                self.assertEqual(terminal, expected)

    def test_temporary_module_hash_kernel_and_driver_mutations_reject(self) -> None:
        repaired = _binary(b"synthetic\x00")
        temporary = {
            "schema_version": "legal-river-zero-suffix-temporary-payload-v1",
            "temporary_path": r"C:\Temp\payload.cubin",
            "readback_sha256": repaired.sha256,
            "readback_bytes": repaired.byte_count,
            "matches_durable_repaired_payload": True,
        }
        self.assertEqual(reader._validate_temporary(temporary, repaired), temporary["temporary_path"])
        for key, value in (
            ("readback_sha256", "0" * 64),
            ("readback_bytes", repaired.byte_count + 1),
            ("matches_durable_repaired_payload", False),
        ):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    reader._validate_temporary({**temporary, key: value}, repaired)
        module = {
            "schema_version": "legal-river-zero-suffix-module-capture-v1",
            "repaired_payload_sha256": repaired.sha256,
            "repaired_payload_bytes": repaired.byte_count,
            "kernel_names": list(diagnostic.ALL_KERNEL_NAMES),
            "direct_driver_rows": diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS,
            "kernel_launch_count": 0,
        }
        self.assertEqual(reader._validate_module(module, repaired), diagnostic.ORIGINAL_DIRECT_DRIVER_ROWS)
        for key, value in (
            ("repaired_payload_sha256", "f" * 64),
            ("kernel_names", list(diagnostic.ALL_KERNEL_NAMES[:-1])),
            ("kernel_launch_count", 1),
        ):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    reader._validate_module({**module, key: value}, repaired)

    def test_candidate_order_and_same_temporary_path_are_mechanical(self) -> None:
        config_rows = diagnostic.load_preregistered_config()["candidate_commands_in_order"]
        assert isinstance(config_rows, list)
        expected = config_rows[1]
        assert isinstance(expected, dict)
        temporary = r"C:\Temp\one-exact.cubin"
        event = {
            "schema_version": "legal-river-zero-suffix-candidate-command-v1",
            "candidate_index": 1,
            "candidate_id": expected["candidate_id"],
            "uses_repaired_payload": expected["uses_repaired_payload"],
            "required_for_suffix_pass": expected["required_for_suffix_pass"],
            "argv": [
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe",
                "--dump-resource-usage",
                temporary,
            ],
            "status": "completed",
            "return_code": 0,
            "stdout": diagnostic.encode_stream(_resource_stdout()),
            "stderr": diagnostic.encode_stream(b""),
            "elapsed_ns": 1,
        }
        observed = reader._validate_candidate(
            event, expected, index=1, temporary_path=temporary
        )
        self.assertEqual(observed.candidate_id, "cuobjdump_resource_usage")
        for mutation in (
            {"candidate_index": 2},
            {"candidate_id": "cuobjdump_elf"},
            {"argv": [*event["argv"][:-1], r"C:\Temp\different.cubin"]},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    reader._validate_candidate(
                        {**event, **mutation}, expected, index=1, temporary_path=temporary
                    )

    def test_binary_envelope_mutations_reject_independently(self) -> None:
        envelope = diagnostic.encode_stream(b"\x00\xffbinary")
        self.assertEqual(
            reader.decode_binary(envelope, label="control", maximum_bytes=64).raw,
            b"\x00\xffbinary",
        )
        for key, value in (
            ("sha256", "0" * 64),
            ("byte_count", envelope["byte_count"] + 1),
            ("base64", str(envelope["base64"]) + "="),
        ):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    reader.decode_binary(
                        {**envelope, key: value}, label="control", maximum_bytes=64
                    )


class ExactZeroSuffixLifecycleTests(unittest.TestCase):
    def test_literal_device_free_protocol_child_is_complete(self) -> None:
        events: list[tuple[str, dict[str, object]]] = []
        terminal = runner.run_device_free_protocol_probe(
            lambda kind, event: events.append((kind, dict(event)))
        )
        self.assertEqual(terminal["terminal"], "suffix_reconstruction_pass")
        self.assertEqual(events[0][0], "bootstrap_handshake")
        self.assertFalse(events[0][1]["cupy_loaded"])
        self.assertFalse(events[0][1]["parent_reader_loaded"])
        self.assertEqual(sum(kind == "candidate_command" for kind, _ in events), 6)
        self.assertEqual(events[-1][0], "terminal_evidence")

    def test_silent_child_and_post_terminal_frame_fail_closed(self) -> None:
        with self.assertRaises(TimeoutError):
            runner.run_child_process(
                mode=runner._HANG_MODE,
                emit=lambda _kind, _event: None,
                wall_limit_ns=100_000_000,
            )
        with self.assertRaises(RuntimeError):
            runner.run_child_process(
                mode=runner._POST_TERMINAL_MODE,
                emit=lambda _kind, _event: None,
                wall_limit_ns=5_000_000_000,
            )

    def test_handshake_and_frame_identity_mutations_reject(self) -> None:
        challenge = "a" * 64
        handshake = {
            "schema_version": "legal-river-zero-suffix-handshake-v1",
            "challenge": challenge,
            "literal_worker_module": runner.LITERAL_WORKER_MODULE,
            "runtime_name": "__main__",
            "spec_name": runner.LITERAL_WORKER_MODULE,
            "python_no_bytecode": True,
            "cupy_loaded": False,
            "parent_reader_loaded": False,
        }
        reader._validate_handshake(handshake)
        for key, value in (("challenge", "b" * 63), ("cupy_loaded", True)):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    reader._validate_handshake({**handshake, key: value})
        frame = runner._frame("control", {"schema_version": "control-v1"})
        self.assertEqual(runner._strict_frame(frame)[0], "control")
        with self.assertRaises(ValueError):
            runner._strict_frame(frame.replace(b"\n", b"\r\n"))
        noncanonical = json.dumps(
            {"kind": "control", "event": {"schema_version": "control-v1"}},
            indent=1,
        ).encode() + b"\n"
        with self.assertRaises(ValueError):
            runner._strict_frame(noncanonical)

    def test_owner_is_exclusive_and_first_terminal_is_permanent(self) -> None:
        loaded = runner.load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "synthetic.jsonl"
            reserved = Path(directory) / "reserved.jsonl"

            def campaign(emit, _wall):
                terminal = diagnostic._terminal(
                    "diagnostic_failure", "synthetic owner control", candidate_count=0
                )
                emit("terminal_evidence", terminal)
                return terminal

            kwargs = {
                "output_path": output,
                "config_loader": lambda: loaded,
                "git_loader": lambda: {
                    "commit": "b" * 40,
                    "dirty": False,
                    "strict_status": True,
                },
                "hashes_loader": lambda: {"synthetic": "c" * 64},
                "retained_loader": lambda: {
                    "diagnostic": {},
                    "selection": {},
                },
                "campaign_executor": campaign,
                "reserved_path": reserved,
            }
            execution = runner.execute_owner_to_path(**kwargs)
            self.assertEqual(execution.terminal["terminal"], "diagnostic_failure")
            with self.assertRaises(FileExistsError):
                runner.execute_owner_to_path(**kwargs)

    def test_infrastructure_journal_rebinds_and_torn_replay_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "infrastructure.jsonl"

            def absent_config():
                raise RuntimeError("synthetic config failure")

            execution = runner.execute_owner_to_path(
                output_path=output,
                config_loader=absent_config,
                reserved_path=Path(directory) / "reserved.jsonl",
            )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            rebound = reader.rebind_zero_suffix_diagnostic_journal(output.read_bytes())
            self.assertEqual(rebound.terminal, "infrastructure_failure")
            raw = output.read_bytes()
            with self.assertRaises(ValueError):
                reader.rebind_zero_suffix_diagnostic_journal(raw[:-1])
            with self.assertRaises(ValueError):
                reader.rebind_zero_suffix_diagnostic_journal(raw + raw.splitlines(True)[-1])

    def test_journal_cap_rejects_before_unbounded_observation(self) -> None:
        loaded = runner.load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bounded.jsonl"

            def campaign(emit, _wall):
                emit("oversized", {"payload": "x" * 20_000})
                raise AssertionError("cap should reject before return")

            with mock.patch.object(runner, "MAXIMUM_ARTIFACT_BYTES", 12_000):
                execution = runner.execute_owner_to_path(
                    output_path=output,
                    config_loader=lambda: loaded,
                    git_loader=lambda: {
                        "commit": "d" * 40,
                        "dirty": False,
                        "strict_status": True,
                    },
                    hashes_loader=lambda: {"synthetic": "e" * 64},
                    retained_loader=lambda: {"diagnostic": {}, "selection": {}},
                    campaign_executor=campaign,
                    reserved_path=Path(directory) / "reserved.jsonl",
                )
            self.assertEqual(execution.terminal["terminal"], "infrastructure_failure")
            self.assertLess(output.stat().st_size, 12_000)


class ExactZeroSuffixSourceBoundaryTests(unittest.TestCase):
    def test_imports_are_device_free_and_result_paths_are_absent(self) -> None:
        self.assertNotIn("cupy", sys.modules)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())
        self.assertEqual(runner.load_public_config().sha256, diagnostic.CONFIG_SHA256)

    def test_reader_is_independent_and_source_has_no_compile_or_launch_call(self) -> None:
        reader_path = _ROOT / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py"
        reader_tree = ast.parse(reader_path.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(reader_tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(reader_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(any("cupy" in name for name in imported))
        self.assertFalse(any(name.endswith("zero_suffix_diagnostic") for name in imported))
        self.assertFalse(any(name.endswith("zero_suffix_diagnostic_runner") for name in imported))
        for relative in (
            "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py",
            "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_runner.py",
        ):
            tree = ast.parse((_ROOT / relative).read_text(encoding="utf-8"))
            calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
            names = {
                func.attr if isinstance(func, ast.Attribute) else func.id
                for func in calls
                if isinstance(func, (ast.Attribute, ast.Name))
            }
            self.assertFalse(
                names
                & {
                    "compile",
                    "compile_with_cache",
                    "RawKernel",
                    "RawModule",
                    "run_calibration_preflight",
                    "run_actual_context",
                }
            )
        source = (
            _ROOT / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("ConsumerPopulationFixture", source)
        self.assertNotIn("legal_river_quotient_cuda_consumer_v1.jsonl\"", source.split("def run_real_diagnostic", 1)[1])

    def test_frozen_config_and_consumed_inputs_rebind_exactly(self) -> None:
        config = (_ROOT / diagnostic.CONFIG_RELATIVE_PATH).read_bytes()
        self.assertEqual(
            sha256(config.replace(b"\r\n", b"\n")).hexdigest(), diagnostic.CONFIG_SHA256
        )
        facts = runner.retained_artifact_facts()
        self.assertEqual(facts["diagnostic"]["sha256"], diagnostic.PARENT_ARTIFACT_SHA256)
        self.assertEqual(facts["selection"]["sha256"], diagnostic.PARENT_SELECTION_SHA256)
        parent_reader = _ROOT / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py"
        self.assertEqual(
            diagnostic.canonical_lf_sha256(parent_reader),
            "ec7308b8adb8bd398844b60a2a149198262e53cfe9bd8256ba424e47bf87093b",
        )


if __name__ == "__main__":
    unittest.main()
