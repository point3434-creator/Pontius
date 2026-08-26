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

from pontius import legal_river_quotient_fixed_width_device_preflight_v2_result as parent_reader
from pontius import legal_river_quotient_fixed_width_device_preflight_v3_result as reader
from pontius import legal_river_quotient_fixed_width_device_preflight_v3_runner as runner
from pontius.legal_river_quotient_fixed_width_device_preflight_result import (
    assess_device_preflight_file as assess_v1_device_preflight_file,
)
from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius.legal_river_quotient_fixed_width_device_preflight_v2_outcome import (
    assess_device_preflight_v2_outcome_file,
)
from tests.test_legal_river_quotient_fixed_width_device_preflight import (
    synthetic_campaign,
)


ROOT = Path(__file__).parents[1]
LAUNCHER = ROOT / "run_legal_river_quotient_fixed_width_device_preflight_v3.py"
RUNNER = Path(runner.__file__)
READER = Path(reader.__file__)
CONTROLS = Path(__file__)
CONFIG = ROOT / runner.CONFIG_RELATIVE_PATH
V2_RESULT = ROOT / runner.CONSUMED_RESULT_RELATIVE_PATH


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


def child_environment(
    parent: dict[str, str], *, spool: Path, mode: str = runner._CAMPAIGN_CHILD
) -> dict[str, str]:
    environment = dict(parent)
    environment["PATH"] = (
        str(runner.RUNTIME_DIRECTORY) + os.pathsep + environment["PATH"]
    )
    environment.update(runner.STATIC_CHILD_VALUES)
    environment[runner._MODE_ENV] = mode
    environment[runner._SPOOL_ENV] = str(spool)
    return environment


def rewrite_journal(raw: bytes, transform) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.PROTOCOL_SHA256,
        expected_campaign_sha256=runner.CAMPAIGN_SHA256,
    )
    previous = None
    lines = []
    for envelope in recovery.records:
        payload = copy.deepcopy(envelope.body.payload)
        transform(envelope.body.kind.value, payload)
        semantic = sha256(canonical_journal_json_bytes(payload)).hexdigest()
        body = build_journal_record_body(
            protocol_sha256=runner.PROTOCOL_SHA256,
            campaign_sha256=runner.CAMPAIGN_SHA256,
            kind=envelope.body.kind,
            sequence=envelope.body.sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=semantic,
            payload=payload,
        )
        record = JournalRecordEnvelope(body=body)
        lines.append(record.line_bytes)
        previous = record.line_sha256
    return b"".join(lines)


class SplitRuntimeFixedWidthDeviceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.activated = runner._parent.activate_bound_host_environment()
        cls.runtime = runner.expected_child_runtime_evidence(
            cls.activated.environment
        )

    def test_config_parent_chain_and_consumed_result_rebind(self) -> None:
        raw = canonical_lf(CONFIG.read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), runner.CONFIG_SHA256)
        config = json.loads(raw)
        self.assertEqual(config["parent_commit"], "b326ac2ffc7dee1adfe68110c7e7d92c19af581b")
        self.assertEqual(
            config["child_runtime_environment"]["activated_projection_full_sha256"],
            runner.CHILD_FULL_ENVIRONMENT_SHA256,
        )
        self.assertEqual(
            sha256(V2_RESULT.read_bytes()).hexdigest(), runner.CONSUMED_RESULT_SHA256
        )
        for row in config["parent_chain"].values():
            path = ROOT / row["relative_path"]
            raw_parent = path.read_bytes()
            key = "raw_sha256" if "raw_sha256" in row else "canonical_lf_sha256"
            observed = sha256(
                raw_parent if key == "raw_sha256" else canonical_lf(raw_parent)
            ).hexdigest()
            self.assertEqual(observed, row[key])

    def test_runtime_files_and_independent_projection_match(self) -> None:
        rows = runner.verify_runtime_files()
        self.assertEqual(rows, tuple(self.runtime["required_runtime_files"]))
        child = dict(self.activated.environment)
        child["PATH"] = (
            str(runner.RUNTIME_DIRECTORY)
            + os.pathsep
            + self.activated.environment["PATH"]
        )
        full = sha256(
            json.dumps(child, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest()
        selected = {
            name: next(
                value
                for key, value in child.items()
                if key.casefold() == name.casefold()
            )
            for name in runner._parent.SELECTED_ENVIRONMENT_NAMES
        }
        selected_digest = sha256(
            json.dumps(selected, sort_keys=True, separators=(",", ":")).encode(
                "ascii"
            )
        ).hexdigest()
        self.assertEqual(full, runner.CHILD_FULL_ENVIRONMENT_SHA256)
        self.assertEqual(selected_digest, runner.CHILD_SELECTED_ENVIRONMENT_SHA256)

    def test_complete_child_environment_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spool = Path(directory).resolve()
            environment = child_environment(dict(self.activated.environment), spool=spool)
            validated = runner.validate_child_runtime_environment(environment)
        self.assertEqual(
            validated.runtime_evidence["child_full_environment_sha256"],
            runner.CHILD_FULL_ENVIRONMENT_SHA256,
        )
        self.assertEqual(
            validated.runtime_evidence["changed_parent_activated_keys"], ["PATH"]
        )
        self.assertEqual(
            validated.runtime_evidence["resolved_tools"],
            {
                "cl.exe": str(runner._parent.CL_PATH),
                "link.exe": str(runner._parent.LINK_PATH),
                "rc.exe": str(runner._parent.RC_PATH),
            },
        )

    def test_child_environment_mutations_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spool = Path(directory).resolve()
            base = child_environment(dict(self.activated.environment), spool=spool)
            mutations = []
            unknown = dict(base)
            unknown["UNLISTED_RUNTIME_KEY"] = "1"
            mutations.append(unknown)
            changed = dict(base)
            changed["INCLUDE"] += ";hostile"
            mutations.append(changed)
            duplicate = dict(base)
            duplicate["PATH"] = str(runner.RUNTIME_DIRECTORY) + os.pathsep + base["PATH"]
            mutations.append(duplicate)
            missing = dict(base)
            missing["PATH"] = self.activated.environment["PATH"]
            mutations.append(missing)
            shadow = dict(base)
            shadow["PATH"] = (
                str(runner.RUNTIME_DIRECTORY)
                + os.pathsep
                + r"C:\hostile"
                + os.pathsep
                + self.activated.environment["PATH"]
            )
            mutations.append(shadow)
            static = dict(base)
            static["PONTIUS_CUDA_DLL_SOURCE"] = "ambient"
            mutations.append(static)
            wrong_mode = dict(base)
            wrong_mode[runner._MODE_ENV] = "other"
            mutations.append(wrong_mode)
            for environment in mutations:
                with self.subTest(keys=len(environment)):
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        runner.validate_child_runtime_environment(environment)

    def test_runtime_file_manifest_mutations_reject(self) -> None:
        rows = list(runner.RUNTIME_FILES)
        name, path, size, digest = rows[0]
        rows[0] = (name, path, size + 1, digest)
        with self.assertRaisesRegex(ValueError, "runtime file identity differs"):
            runner.verify_runtime_files(tuple(rows))
        with self.assertRaisesRegex(ValueError, "runtime file domain differs"):
            runner.verify_runtime_files(tuple(rows[:-1]))
        rows = list(runner.RUNTIME_FILES)
        name, _, size, digest = rows[0]
        rows[0] = (name, runner.RUNTIME_DIRECTORY / "missing.dll", size, digest)
        with self.assertRaisesRegex(FileNotFoundError, "runtime file is absent"):
            runner.verify_runtime_files(tuple(rows))

    def test_external_root_probe_validates_child_without_science(self) -> None:
        challenge = bytes(range(32))
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
        environment["PATH"] = r"C:\hostile"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONNOUSERSITE"] = "1"
        environment[runner._MODE_ENV] = runner._SOURCE_SEAL_PROBE
        environment[runner._CHALLENGE_ENV] = challenge.hex()
        before = V2_RESULT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-B", str(LAUNCHER)],
                cwd=directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        evidence = json.loads(completed.stdout)
        self.assertEqual(evidence["challenge_sha256"], sha256(challenge).hexdigest())
        self.assertEqual(
            evidence["child"]["child_runtime_environment"][
                "child_full_environment_sha256"
            ],
            runner.CHILD_FULL_ENVIRONMENT_SHA256,
        )
        self.assertFalse(evidence["child"]["cupy_loaded"])
        self.assertFalse(evidence["child"]["scientific_source_loaded"])
        self.assertFalse(evidence["child"]["compiler_executed"])
        self.assertFalse(evidence["child"]["device_queried"])
        self.assertTrue(evidence["result_absent"])
        self.assertEqual(V2_RESULT.read_bytes(), before)
        self.assertFalse(runner.RESULT_PATH.exists())

    def test_source_probe_subprocess_inventory_contains_no_compiler(self) -> None:
        actual = subprocess.run
        with patch.object(runner.subprocess, "run", wraps=actual) as observed:
            evidence = runner.source_seal_probe(bytes(range(32)).hex())
        commands = [str(call.args[0]).casefold() for call in observed.call_args_list]
        self.assertFalse(any("nvcc.exe" in command for command in commands))
        self.assertFalse(any("cl.exe" in command for command in commands))
        self.assertFalse(evidence["compiler_executed"])
        self.assertFalse(evidence["cupy_scientific_imported"])
        self.assertFalse(evidence["device_queried"])

    def test_imports_are_science_result_and_consumed_artifact_nonmutating(self) -> None:
        v2_before = V2_RESULT.read_bytes()
        v3_before = runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None
        command = (
            "import hashlib,importlib,json,pathlib,sys; "
            f"v2=pathlib.Path({str(V2_RESULT)!r}); v3=pathlib.Path({str(runner.RESULT_PATH)!r}); "
            "b2=v2.read_bytes(); b3=v3.read_bytes() if v3.is_file() else None; "
            "[importlib.import_module(n) for n in ["
            "'pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner',"
            "'pontius.legal_river_quotient_fixed_width_device_preflight_v3_result']]; "
            "print(json.dumps({'v2':hashlib.sha256(v2.read_bytes()).hexdigest(),"
            "'v2_same':b2==v2.read_bytes(),'v3_same':b3==(v3.read_bytes() if v3.is_file() else None),"
            "'cupy':any(n=='cupy' or n.startswith('cupy.') for n in sys.modules),"
            "'science':'pontius.legal_river_quotient_fixed_width_device_preflight' in sys.modules}))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", command],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            check=True,
            capture_output=True,
            text=True,
        )
        evidence = json.loads(completed.stdout)
        self.assertEqual(evidence["v2"], runner.CONSUMED_RESULT_SHA256)
        self.assertTrue(evidence["v2_same"])
        self.assertTrue(evidence["v3_same"])
        self.assertFalse(evidence["cupy"])
        self.assertFalse(evidence["science"])
        self.assertEqual(V2_RESULT.read_bytes(), v2_before)
        self.assertEqual(
            runner.RESULT_PATH.read_bytes() if runner.RESULT_PATH.is_file() else None,
            v3_before,
        )

    def test_public_clock_precedes_activation_and_runtime_validation(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        segment = ast.get_source_segment(source, main)
        self.assertLess(
            segment.index("public_origin = perf_counter_ns()"),
            segment.index("activate_bound_host_environment()"),
        )
        self.assertLess(
            segment.index("public_origin = perf_counter_ns()"),
            segment.index("expected_child_runtime_evidence"),
        )
        origin = perf_counter_ns() - 1_000_000
        clock = runner._public_clock(origin)
        self.assertEqual(clock(), origin)
        self.assertGreater(clock(), origin)

    def test_engine_header_is_fresh_and_bindings_restore(self) -> None:
        original = {name: getattr(runner._engine, name) for name in runner._ENGINE_BINDING_NAMES}
        with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
            header = engine._header_payload(
                {"commit": "0" * 40, "dirty": False, "strict_status": True}
            )
            self.assertEqual(header["literal_worker_module"], runner.LITERAL_WORKER_MODULE)
            self.assertEqual(header["result_relative_path"], runner.RESULT_RELATIVE_PATH)
            self.assertEqual(header["child_runtime_environment"], self.runtime)
            self.assertEqual(
                header["predecessor"]["result_raw_sha256"],
                runner.CONSUMED_RESULT_SHA256,
            )
        self.assertEqual(
            {name: getattr(runner._engine, name) for name in original}, original
        )

    def test_zero_event_reader_branch_accepts_failure_and_rejects_success(self) -> None:
        def fail_before_event(_append_event):
            raise RuntimeError("synthetic pre-bootstrap failure")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "zero.jsonl"
            with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
                execution = engine.execute_owner_to_path(
                    output_path=path, campaign_executor=fail_before_event
                )
            raw = path.read_bytes()
        self.assertEqual(execution.event_count, 0)
        assessed = reader.assess_device_preflight_v3_bytes(raw)
        self.assertEqual(assessed.terminal, "infrastructure_failure")
        self.assertEqual(assessed.event_count, 0)

        def make_success(kind, payload):
            if kind == "terminal":
                payload["terminal"] = "completed_device_preflight"
                payload["passed"] = True

        with self.assertRaisesRegex(ValueError, "zero-event terminal differs"):
            reader.assess_device_preflight_v3_bytes(rewrite_journal(raw, make_success))
        for malformed in (raw[:-1], raw + b"{}\n"):
            with self.assertRaises(ValueError):
                reader.assess_device_preflight_v3_bytes(malformed)

        def one_nonbootstrap_event(append_event):
            append_event("not_bootstrap", {"synthetic": True})
            raise RuntimeError("synthetic one-event failure")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "one.jsonl"
            with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
                engine.execute_owner_to_path(
                    output_path=path, campaign_executor=one_nonbootstrap_event
                )
            one_raw = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "bootstrap differs"):
            reader.assess_device_preflight_v3_bytes(one_raw)

    def test_observed_synthetic_journal_reuses_scientific_reader(self) -> None:
        parent_constants = {
            name: getattr(parent_reader, name) for name in reader._PARENT_BINDING_NAMES
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.jsonl"
            with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
                execution = engine.execute_owner_to_path(
                    output_path=path, campaign_executor=synthetic_campaign
                )
            raw = path.read_bytes()
        self.assertEqual(execution.terminal["terminal"], "completed_device_preflight")
        assessed = reader.assess_device_preflight_v3_bytes(raw)
        self.assertTrue(assessed.passed)
        self.assertEqual(
            {name: getattr(parent_reader, name) for name in parent_constants},
            parent_constants,
        )

    def test_reader_projection_changes_only_two_header_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.jsonl"
            with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
                engine.execute_owner_to_path(
                    output_path=path, campaign_executor=synthetic_campaign
                )
            recovery = reader._validate_fresh_journal(path.read_bytes())
        projected = recover_journal_bytes(
            reader._parent_projection_bytes(recovery),
            expected_protocol_sha256=runner.PROTOCOL_SHA256,
            expected_campaign_sha256=runner.CAMPAIGN_SHA256,
        )
        original_payloads = [record.body.payload for record in recovery.records]
        projected_payloads = [record.body.payload for record in projected.records]
        expected = copy.deepcopy(original_payloads)
        expected[0].pop("child_runtime_environment")
        expected[0]["predecessor"] = {
            "result_relative_path": (
                "artifacts/work_preflight/"
                "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
            ),
            "result_raw_sha256": (
                "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
            ),
            "terminal": "compiler_rejection",
        }
        self.assertEqual(projected_payloads, expected)

    def test_zero_event_and_runtime_evidence_mutations_reject(self) -> None:
        def fail_before_event(_append_event):
            raise RuntimeError("synthetic pre-bootstrap failure")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "zero.jsonl"
            with runner.configured_engine(self.activated.evidence, self.runtime) as engine:
                engine.execute_owner_to_path(
                    output_path=path, campaign_executor=fail_before_event
                )
            raw = path.read_bytes()
        mutations = (
            lambda kind, payload: payload.update({"event_count": 1})
            if kind == "terminal"
            else None,
            lambda kind, payload: payload["child_runtime_environment"].update(
                {"path_prefix_occurrence_count": 2}
            )
            if kind == "header"
            else None,
            lambda kind, payload: payload["child_runtime_environment"].update(
                {"child_full_environment_sha256": "0" * 64}
            )
            if kind == "header"
            else None,
        )
        for transform in mutations:
            with self.subTest(transform=transform):
                with self.assertRaises(ValueError):
                    reader.assess_device_preflight_v3_bytes(
                        rewrite_journal(raw, transform)
                    )

    def test_consumed_v2_outcome_survives_all_wrappers(self) -> None:
        v1_before = asdict(assess_v1_device_preflight_file())
        before = asdict(assess_device_preflight_v2_outcome_file())
        with runner.configured_engine(self.activated.evidence, self.runtime):
            pass
        after = asdict(assess_device_preflight_v2_outcome_file())
        self.assertEqual(after, before)
        self.assertEqual(asdict(assess_v1_device_preflight_file()), v1_before)
        self.assertEqual(after["terminal"], "infrastructure_failure")
        self.assertEqual(after["event_count"], 0)

    def test_result_path_is_unfiltered_and_lifecycle_safe(self) -> None:
        relative = runner.RESULT_PATH.relative_to(ROOT).as_posix()
        attributes = subprocess.run(
            ["git", "check-attr", "text", "--", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(attributes, f"{relative}: text: unset")
        self.assertFalse(runner.RESULT_PATH.exists())


if __name__ == "__main__":
    unittest.main()
