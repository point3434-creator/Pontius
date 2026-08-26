from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter_ns
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_fixed_width_device_preflight_result as parent_reader
from pontius import legal_river_quotient_fixed_width_device_preflight_runner as parent_runner
from pontius import legal_river_quotient_fixed_width_device_preflight_v2_result as reader
from pontius import legal_river_quotient_fixed_width_device_preflight_v2_runner as runner
from pontius.legal_river_quotient_fixed_width_device_preflight import (
    independent_normalize_crlf_bytes,
    literal_escape_mutation_receipt,
    normalize_crlf_bytes,
)
from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from tests.test_legal_river_quotient_fixed_width_device_preflight import (
    synthetic_campaign,
)


ROOT = Path(__file__).parents[1]
LAUNCHER = ROOT / "run_legal_river_quotient_fixed_width_device_preflight_v2.py"
CONFIG = ROOT / runner.CONFIG_RELATIVE_PATH
SOURCE = ROOT / "src/pontius/legal_river_quotient_fixed_width_device_preflight.py"
RUNNER = Path(runner.__file__)
READER = Path(reader.__file__)
CONTROLS = Path(__file__)
OLD_RESULT = ROOT / runner.CONSUMED_RESULT_RELATIVE_PATH
OLD_RESULT_SHA256 = runner.CONSUMED_RESULT_SHA256


def canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index : index + 2] == bytes((13, 10)):
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def independent_activation() -> tuple[dict[str, str], str, str]:
    source = os.environ
    baseline = {}
    for required in runner.BASELINE_ENVIRONMENT_NAMES:
        matches = [value for name, value in source.items() if name.casefold() == required.casefold()]
        if len(matches) != 1:
            raise AssertionError(f"independent activation baseline differs: {required}")
        baseline[required] = matches[0]
    baseline["PATH"] = str(Path(baseline["SystemRoot"]) / "System32")
    command = (
        f'"{baseline["ComSpec"]}" /d /s /c '
        f'""{runner.VCVARS64_PATH}" >nul && set"'
    )
    completed = subprocess.run(
        command,
        env=baseline,
        check=False,
        capture_output=True,
        timeout=10.0,
    )
    if completed.returncode or completed.stderr:
        raise AssertionError("independent activation command failed")
    rows = {}
    for raw_line in reversed(completed.stdout.splitlines()):
        name, separator, value = raw_line.partition(b"=")
        if not separator:
            raise AssertionError("independent activation row differs")
        decoded_name = name.decode("utf-8", "strict")
        if any(existing.casefold() == decoded_name.casefold() for existing in rows):
            raise AssertionError("independent activation repeats a key")
        rows[decoded_name] = value.decode("utf-8", "strict")
    full = sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    selected = {
        name: next(value for key, value in rows.items() if key.casefold() == name.casefold())
        for name in runner.SELECTED_ENVIRONMENT_NAMES
    }
    selected_digest = sha256(
        json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return rows, full, selected_digest


def rewrite_journal(raw: bytes, transform) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.PROTOCOL_SHA256,
        expected_campaign_sha256=runner.CAMPAIGN_SHA256,
    )
    if not recovery.is_complete:
        raise AssertionError("mutation input journal is incomplete")
    previous = None
    output = []
    for index, envelope in enumerate(recovery.records):
        payload = copy.deepcopy(envelope.body.payload)
        transform(index, envelope.body.kind.value, payload)
        semantic = sha256(canonical_journal_json_bytes(payload)).hexdigest()
        body = build_journal_record_body(
            protocol_sha256=runner.PROTOCOL_SHA256,
            campaign_sha256=runner.CAMPAIGN_SHA256,
            kind=envelope.body.kind,
            sequence=index,
            previous_record_sha256=previous,
            semantic_identity_sha256=semantic,
            payload=payload,
        )
        record = JournalRecordEnvelope(body=body)
        output.append(record.line_bytes)
        previous = record.line_sha256
    return b"".join(output)


class MsvcBoundFixedWidthDeviceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.activated = runner.activate_bound_host_environment()

    def test_imports_are_tool_process_and_result_nonmutating(self) -> None:
        new_before = runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None
        old_before = OLD_RESULT.read_bytes()
        command = (
            "import hashlib, importlib, json, pathlib, sys; "
            f"new=pathlib.Path({str(runner.RESULT_PATH)!r}); old=pathlib.Path({str(OLD_RESULT)!r}); "
            "before_new=new.read_bytes() if new.is_file() else None; before_old=old.read_bytes(); "
            "mods=['pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner',"
            "'pontius.legal_river_quotient_fixed_width_device_preflight_v2_result']; "
            "[importlib.import_module(name) for name in mods]; "
            "after_new=new.read_bytes() if new.is_file() else None; after_old=old.read_bytes(); "
            "print(json.dumps({'cupy':any(name=='cupy' or name.startswith('cupy.') for name in sys.modules),"
            "'science':'pontius.legal_river_quotient_fixed_width_device_preflight' in sys.modules,"
            "'new_same':before_new==after_new,'old_same':before_old==after_old,"
            "'old_sha':hashlib.sha256(after_old).hexdigest()}))"
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
        self.assertEqual(
            evidence,
            {
                "cupy": False,
                "science": False,
                "new_same": True,
                "old_same": True,
                "old_sha": OLD_RESULT_SHA256,
            },
        )
        self.assertEqual(
            runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None,
            new_before,
        )
        self.assertEqual(OLD_RESULT.read_bytes(), old_before)

    def test_config_parents_and_scientific_source_rebind(self) -> None:
        config_raw = canonical_lf(CONFIG.read_bytes())
        self.assertEqual(sha256(config_raw).hexdigest(), runner.CONFIG_SHA256)
        config = json.loads(config_raw)
        self.assertEqual(config["parent_commit"], "bf90ce5b7f6bded402b96f411ff44757aaa5dd56")
        preregistration_commit = subprocess.run(
            ["git", "rev-parse", "b24eae3"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(runner.PREREGISTRATION_COMMIT, preregistration_commit)
        self.assertEqual(reader.PREREGISTRATION_COMMIT, preregistration_commit)
        for row in config["parent_chain"].values():
            path = ROOT / row["relative_path"]
            raw = path.read_bytes()
            key = "raw_sha256" if "raw_sha256" in row else "canonical_lf_sha256"
            observed = sha256(raw if key == "raw_sha256" else canonical_lf(raw)).hexdigest()
            self.assertEqual(observed, row[key])
        self.assertEqual(
            sha256(canonical_lf(SOURCE.read_bytes())).hexdigest(),
            "5b448e3a7d6607cb9392505e35f4428b0bec460caedca3c881b52a81145e1df1",
        )

    def test_new_source_identities_use_two_normalizers_and_exact_trigger_counts(self) -> None:
        for path in (LAUNCHER, RUNNER, READER, CONTROLS):
            raw = path.read_bytes()
            self.assertEqual(normalize_crlf_bytes(raw), independent_normalize_crlf_bytes(raw))
            receipt = literal_escape_mutation_receipt(
                path, expected_occurrences=0, require_armed=False
            )
            self.assertEqual(receipt.occurrence_count, 0)
            self.assertEqual(
                receipt.canonical_lf_sha256,
                receipt.forbidden_mutation_sha256,
            )

    def test_bound_host_files_and_two_activation_parsers_agree(self) -> None:
        file_rows = runner.verify_host_files()
        self.assertEqual(file_rows, tuple(self.activated.evidence["file_identities"]))
        independent, full, selected = independent_activation()
        self.assertEqual(full, runner.FULL_ENVIRONMENT_SHA256)
        self.assertEqual(selected, runner.SELECTED_ENVIRONMENT_SHA256)
        self.assertEqual(set(independent), set(runner.ACTIVATED_ENVIRONMENT_NAMES))
        self.assertEqual(self.activated.evidence["full_environment_sha256"], full)
        self.assertEqual(self.activated.evidence["selected_environment_sha256"], selected)

    def test_ambient_compiler_state_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "cl.exe"
            fake.write_bytes(b"not a compiler")
            ambient = dict(os.environ)
            ambient.update(
                {
                    "PATH": f"{directory};C:\\hostile",
                    "INCLUDE": "hostile-include",
                    "LIB": "hostile-lib",
                    "LIBPATH": "hostile-libpath",
                    "VSINSTALLDIR": "hostile-vs",
                    "NVCC_PREPEND_FLAGS": "--use_fast_math",
                }
            )
            activated = runner.activate_bound_host_environment(ambient)
        self.assertEqual(
            activated.evidence["full_environment_sha256"],
            runner.FULL_ENVIRONMENT_SHA256,
        )
        self.assertNotIn(directory.casefold(), activated.environment["PATH"].casefold())

    def test_host_file_and_environment_mutations_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mutated = Path(directory) / "cl.exe"
            mutated.write_bytes(b"mutation")
            rows = list(runner.HOST_FILES)
            role, _, size, digest = rows[3]
            rows[3] = (role, mutated, size, digest)
            with self.assertRaisesRegex(ValueError, "host file identity differs"):
                runner.verify_host_files(tuple(rows))
        files = tuple(self.activated.evidence["file_identities"])
        for name, value in (
            ("VSCMD_ARG_TGT_ARCH", "x86"),
            ("WindowsSDKVersion", "10.0.00000.0\\"),
            ("PATH", "C:\\hostile;" + self.activated.environment["PATH"]),
        ):
            mutated_environment = dict(self.activated.environment)
            mutated_environment[name] = value
            with self.assertRaisesRegex(ValueError, "environment identity differs"):
                runner._environment_evidence(
                    mutated_environment,
                    file_evidence=files,
                    activation_elapsed_ns=1,
                )

    def test_activation_executes_only_the_bound_batch_shell(self) -> None:
        actual_run = subprocess.run
        with patch.object(runner.subprocess, "run", wraps=actual_run) as observed:
            runner.activate_bound_host_environment()
        self.assertEqual(observed.call_count, 1)
        command = observed.call_args.args[0]
        self.assertIn(str(runner.VCVARS64_PATH), command)
        self.assertNotIn("nvcc.exe", command.casefold())
        self.assertNotIn("cl.exe", command.casefold())

    def test_external_root_probe_activates_without_compiler_or_result(self) -> None:
        challenge = bytes(range(32))
        old_before = OLD_RESULT.read_bytes()
        new_before = runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None
        environment = dict(os.environ)
        for name in (
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTHONSTARTUP",
            "INCLUDE",
            "LIB",
            "LIBPATH",
            "VSINSTALLDIR",
            "VCINSTALLDIR",
            "NVCC_PREPEND_FLAGS",
            "NVCC_APPEND_FLAGS",
        ):
            environment.pop(name, None)
        environment["PATH"] = "C:\\hostile"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONNOUSERSITE"] = "1"
        environment[runner._MODE_ENV] = runner._SOURCE_SEAL_PROBE
        environment[runner._CHALLENGE_ENV] = challenge.hex()
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-B", str(LAUNCHER)],
                cwd=directory,
                env=environment,
                timeout=10.0,
                check=True,
                capture_output=True,
                text=True,
            )
        evidence = json.loads(completed.stdout)
        self.assertEqual(evidence["challenge_sha256"], sha256(challenge).hexdigest())
        self.assertFalse(evidence["cupy_loaded"])
        self.assertFalse(evidence["scientific_source_loaded"])
        self.assertFalse(evidence["compiler_executed"])
        self.assertFalse(evidence["device_queried"])
        self.assertEqual(
            evidence["host_toolchain"]["full_environment_sha256"],
            runner.FULL_ENVIRONMENT_SHA256,
        )
        self.assertEqual(OLD_RESULT.read_bytes(), old_before)
        self.assertEqual(
            runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None,
            new_before,
        )

    def test_direct_source_probe_restores_the_callers_environment(self) -> None:
        before = dict(os.environ)
        evidence = runner.source_seal_probe(bytes(range(32)).hex())
        self.assertEqual(dict(os.environ), before)
        self.assertFalse(evidence["compiler_executed"])
        self.assertEqual(
            evidence["host_toolchain"]["full_environment_sha256"],
            runner.FULL_ENVIRONMENT_SHA256,
        )

    def test_public_clock_origin_precedes_activation_in_source(self) -> None:
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        source = ast.get_source_segment(RUNNER.read_text(encoding="utf-8"), main)
        self.assertLess(source.index("public_origin = perf_counter_ns()"), source.index("activate_bound_host_environment()"))
        self.assertIn("monotonic_ns=_public_clock(public_origin)", source)
        origin = perf_counter_ns() - 1_000_000
        clock = runner._public_clock(origin)
        self.assertEqual(clock(), origin)
        self.assertGreater(clock(), origin)

    def test_engine_configuration_is_fresh_and_restores_parent(self) -> None:
        original = {
            name: getattr(parent_runner, name)
            for name in runner._ORIGINAL_ENGINE_BINDINGS
        }
        with runner.configured_engine(self.activated.evidence) as engine:
            self.assertEqual(engine.RESULT_PATH, runner.RESULT_PATH)
            self.assertEqual(engine.PROTOCOL_SHA256, runner.PROTOCOL_SHA256)
            self.assertEqual(engine.LITERAL_WORKER_MODULE, runner.LITERAL_WORKER_MODULE)
            header = engine._header_payload(
                {"commit": "0" * 40, "dirty": False, "strict_status": True}
            )
            self.assertEqual(header["host_toolchain"], self.activated.evidence)
            self.assertEqual(header["predecessor"]["result_raw_sha256"], OLD_RESULT_SHA256)
        self.assertEqual(
            {name: getattr(parent_runner, name) for name in original},
            original,
        )

    def test_absolute_git_survives_environment_replacement(self) -> None:
        before = dict(os.environ)
        try:
            runner._replace_process_environment(self.activated.environment)
            commit = runner._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        finally:
            os.environ.clear()
            os.environ.update(before)
        self.assertRegex(commit, r"^[0-9a-f]{40}$")

    def test_synthetic_owner_reader_projection_and_parent_restoration(self) -> None:
        old_before = asdict(parent_reader.assess_device_preflight_file(OLD_RESULT))
        parent_constants = {
            name: getattr(parent_reader, name) for name in reader._PARENT_BINDING_NAMES
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-v2.jsonl"
            with runner.configured_engine(self.activated.evidence) as engine:
                execution = engine.execute_owner_to_path(
                    output_path=path,
                    campaign_executor=synthetic_campaign,
                )
            self.assertEqual(execution.terminal["terminal"], "completed_device_preflight")
            raw = path.read_bytes()
            assessed = reader.assess_device_preflight_v2_bytes(raw)
        self.assertTrue(assessed.passed)
        self.assertEqual(
            assessed.eligible_arms,
            (parent_reader.POSITIONAL, parent_reader.BATCHED_RRNS),
        )
        self.assertEqual(
            {name: getattr(parent_reader, name) for name in parent_constants},
            parent_constants,
        )
        self.assertEqual(asdict(parent_reader.assess_device_preflight_file(OLD_RESULT)), old_before)

    def test_reader_rejects_host_and_scientific_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-v2.jsonl"
            with runner.configured_engine(self.activated.evidence) as engine:
                engine.execute_owner_to_path(
                    output_path=path, campaign_executor=synthetic_campaign
                )
            raw = path.read_bytes()

        def host_mutation(index, kind, payload):
            if kind == "header":
                payload["host_toolchain"]["full_environment_sha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "host-toolchain evidence differs"):
            reader.assess_device_preflight_v2_bytes(rewrite_journal(raw, host_mutation))

        def science_mutation(index, kind, payload):
            if kind == "observation" and payload.get("kind") == "candidate_observation":
                payload["event"]["exact_verified"] = False

        with self.assertRaises(ValueError):
            reader.assess_device_preflight_v2_bytes(rewrite_journal(raw, science_mutation))

    def test_projection_changes_exactly_one_header_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-v2.jsonl"
            with runner.configured_engine(self.activated.evidence) as engine:
                engine.execute_owner_to_path(
                    output_path=path, campaign_executor=synthetic_campaign
                )
            raw = path.read_bytes()
        original = reader._validate_fresh_journal(raw)
        projected_raw = reader._parent_projection_bytes(original)
        projected = recover_journal_bytes(
            projected_raw,
            expected_protocol_sha256=runner.PROTOCOL_SHA256,
            expected_campaign_sha256=runner.CAMPAIGN_SHA256,
        )
        original_payloads = [record.body.payload for record in original.records]
        projected_payloads = [record.body.payload for record in projected.records]
        expected = copy.deepcopy(original_payloads)
        expected[0] = dict(expected[0])
        expected[0]["literal_worker_module"] = reader.PARENT_LITERAL_WORKER_MODULE
        self.assertEqual(projected_payloads, expected)

    def test_result_path_is_unfiltered_and_successor_absence_is_lifecycle_safe(self) -> None:
        attributes = subprocess.run(
            ["git", "check-attr", "text", "--", runner.RESULT_RELATIVE_PATH],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(
            attributes.strip().replace("\\", "/"),
            f"{runner.RESULT_RELATIVE_PATH}: text: unset",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prospective.jsonl"
            absent = parent_runner.source_seal_probe(bytes(range(32)).hex(), result_path=path)
            self.assertTrue(absent["result_absent"])
            retained_bytes = b'{"retained":true}\n'
            path.write_bytes(retained_bytes)
            retained = parent_runner.source_seal_probe(bytes(range(32)).hex(), result_path=path)
            self.assertFalse(retained["result_absent"])
            self.assertTrue(retained["result_unchanged"])
            self.assertEqual(path.read_bytes(), retained_bytes)


if __name__ == "__main__":
    unittest.main()
