from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_compiled_global_separation_calibration_runner as parent
from pontius import legal_river_quotient_compiled_global_separation_calibration_v4_runner as successor
from pontius import legal_river_quotient_compiled_global_separation_calibration_v4_result as reader
from pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome import (
    assess_compiled_calibration_v2_outcome_file,
)
from pontius.durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / successor.RECOVERY_CONFIG_RELATIVE_PATH
AUTHORIZATION = ROOT / successor.AUTHORIZATION_CONFIG_RELATIVE_PATH
SOURCE_SEAL_ADR = (
    ROOT / "docs/decisions/ADR-0467-source-seal-the-deferred-science-import-successor.md"
)
AUTHORIZATION_ADR = (
    ROOT / "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md"
)
CLOSURE_ADR = (
    ROOT
    / "docs/decisions/ADR-0469-retain-the-deferred-import-authorization-gate-rejection.md"
)
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration_v4.py"


def _canonical_lf(raw: bytes) -> bytes:
    return raw.replace(bytes((13, 10)), bytes((10,)))


class _FakeScience:
    __name__ = successor.SCIENTIFIC_MODULE

    class CalibrationFailure(Exception):
        pass

    @staticmethod
    def execute_calibration(emit, *, laboratory_started_ns):
        del emit
        return {
            "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
            "terminal": "compiler_rejected",
            "passed": False,
            "reason": "synthetic deferred-import control",
            "laboratory_elapsed_ns": 7,
            "candidate_selected": None,
            "topology_selected": None,
            "arithmetic_schedule_selected": None,
            "claims": dict(parent.CLAIMS),
        }


def _semantic(payload) -> str:
    return sha256(canonical_journal_json_bytes(dict(payload))).hexdigest()


def _journal_bytes(
    observations,
    *,
    owner_passed: bool = False,
    header_payload=None,
    owner_terminal=None,
) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic-v4.jsonl"
        with DurableEvidenceJournalWriter.create(
            path=path,
            protocol_sha256=successor.PROTOCOL_SHA256,
            campaign_sha256=successor.CAMPAIGN_SHA256,
        ) as writer:
            header = (
                {"synthetic": True}
                if header_payload is None
                else dict(header_payload)
            )
            source_commit = header.get("source_seal_git", {}).get(
                "commit", "a" * 40
            )
            writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256=_semantic(header),
                payload=header,
            )
            for index, (kind, event) in enumerate(observations):
                wrapper = {
                    "schema_version": "pontius-adr0457-owner-observation-v1",
                    "event_index": index,
                    "kind": kind,
                    "event": dict(event),
                    "source_commit": source_commit,
                }
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=_semantic(wrapper),
                    payload=wrapper,
                )
            terminal = (
                {
                    "schema_version": "pontius-adr0457-owner-terminal-v1",
                    "terminal": (
                        "completed_reduced_compiled_calibration_production_base_absent"
                        if owner_passed
                        else "compiled_reduced_calibration_rejected"
                    ),
                    "passed": owner_passed,
                    "event_count": len(observations),
                }
                if owner_terminal is None
                else dict(owner_terminal)
            )
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=_semantic(terminal),
                payload=terminal,
            )
        return path.read_bytes()


def _rechain_journal(
    raw: bytes,
    *,
    payload_mutator=None,
    semantic_mutator=None,
) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=successor.PROTOCOL_SHA256,
        expected_campaign_sha256=successor.CAMPAIGN_SHA256,
    )
    output = bytearray()
    previous = None
    for index, record in enumerate(recovery.records):
        payload = dict(record.body.payload)
        if payload_mutator is not None:
            payload = dict(payload_mutator(index, payload))
        semantic = sha256(canonical_journal_json_bytes(payload)).hexdigest()
        if semantic_mutator is not None:
            semantic = str(semantic_mutator(index, semantic))
        body = build_journal_record_body(
            protocol_sha256=successor.PROTOCOL_SHA256,
            campaign_sha256=successor.CAMPAIGN_SHA256,
            kind=record.body.kind,
            sequence=index,
            previous_record_sha256=previous,
            semantic_identity_sha256=semantic,
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        output.extend(envelope.line_bytes)
        previous = envelope.line_sha256
    return bytes(output)


def _bootstrap_event() -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0457-bootstrap-v1",
        "literal_worker_module": successor.LITERAL_WORKER_MODULE,
        "python_no_bytecode": True,
        "child_runtime_environment": reader._expected_child_runtime(),
        "cupy_loaded": False,
        "scientific_source_loaded": False,
        "parent_journal_present": True,
    }


def _loader_rejection_event(*, imported: bool = False) -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
        "terminal": "deferred_science_import_rejected",
        "passed": False,
        "reason": "synthetic loader rejection",
        "laboratory_elapsed_ns": 7,
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "claims": dict(reader._REJECTED_CLAIMS),
        "executed_science_identity": None,
        "science_import_completed": imported,
        "science_identity_validated": False,
        "science_execution_started": False,
    }


def _success_science_observations(materiality: bool):
    manifests = []
    authority_sha256 = sha256(
        json.dumps(manifests, sort_keys=True, separators=(",", ":")).encode(
            "ascii"
        )
    ).hexdigest()
    fixture = {
        "schema_version": "synthetic-fixture-authority-v1",
        "manifests": manifests,
        "authority_sha256": authority_sha256,
    }
    fit = {"synthetic_materiality": materiality}
    fit_sha256 = sha256(
        json.dumps(fit, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    terminal = {
        "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
        "terminal": "completed_reduced_compiled_calibration_production_base_absent",
        "passed": True,
        "laboratory_elapsed_ns": 7,
        "scientific_call_count": 2_880,
        "warmup_call_count": 480,
        "measured_call_count": 2_400,
        "differential_count": 2_880,
        "complete_positive_differential_count": 60,
        "authority_sha256": authority_sha256,
        "fit_projection_sha256": fit_sha256,
        "production_base_classification": "producer_absent",
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "claims": reader._expected_success_claims(materiality),
        "executed_science_identity": reader._expected_executed_science_identity(),
        "science_import_completed": True,
        "science_identity_validated": True,
        "science_execution_started": True,
    }
    return (
        ("bootstrap_handshake", _bootstrap_event()),
        ("fixture_authority", fixture),
        ("fit_projection", fit),
        ("terminal_evidence", terminal),
    )


class CompiledGlobalSeparationCalibrationV4Tests(unittest.TestCase):
    def test_config_closes_v3_and_freezes_deferred_import(self) -> None:
        self.assertEqual(
            sha256(_canonical_lf(CONFIG.read_bytes())).hexdigest(),
            successor.RECOVERY_CONFIG_SHA256,
        )
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["rejected_source_seal"]["public_invocation_count"], 0)
        self.assertFalse(config["rejected_source_seal"]["result_exists"])
        fresh = config["fresh_successor"]
        self.assertTrue(fresh["bootstrap_must_be_emitted_before_science_import"])
        self.assertTrue(fresh["top_level_v3_science_import_forbidden"])
        self.assertTrue(fresh["sys_modules_alias_forbidden"])
        self.assertTrue(fresh["executed_science_identity_required_in_terminal_evidence"])
        self.assertTrue(fresh["durable_attempt_marker_before_mutable_public_preconditions"])
        self.assertIsNone(config["claims"]["compiled_calibration_result"])

    def test_runner_has_no_module_scope_science_import_or_alias_path(self) -> None:
        path = Path(successor.__file__).resolve()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imports = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
        self.assertNotIn(
            "legal_river_quotient_compiled_global_separation_calibration",
            imports,
        )
        self.assertNotIn(
            "legal_river_quotient_compiled_global_separation_calibration_v3",
            imports,
        )
        forbidden_attribute_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_campaign_child_main"
        ]
        self.assertEqual(forbidden_attribute_calls, [])
        assignments_to_modules = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Attribute)
                and isinstance(target.value.value, ast.Name)
                and target.value.value.id == "sys"
                and target.value.attr == "modules"
                for target in node.targets
            )
        ]
        self.assertEqual(assignments_to_modules, [])

    def test_root_launcher_is_importable_without_an_installed_package(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-I",
                "-c",
                (
                    "import runpy,sys; "
                    f"runpy.run_path({str(LAUNCHER)!r}, run_name='__source_review__'); "
                    "assert not any(n == 'pontius' or n.startswith('pontius.') "
                    "for n in sys.modules)"
                ),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_root_launcher_rejects_extension_shadow_before_runner_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "synthetic.pyd").write_bytes(b"not an extension")
            program = (
                "import pathlib,runpy; "
                f"ns=runpy.run_path({str(LAUNCHER)!r}, run_name='__source_review__'); "
                "g=ns['_source_extension_collisions'].__globals__; "
                f"g['ROOT']=pathlib.Path({str(root)!r}); "
                f"g['SOURCE']=pathlib.Path({str(source)!r}); "
                "assert ns['_source_extension_collisions']()==('src/synthetic.pyd',)"
            )
            completed = subprocess.run(
                [sys.executable, "-B", "-I", "-c", program],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_loaded_science_repo_module_closure_is_fully_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONPYCACHEPREFIX"] = str(
                Path(directory) / "unused-pycache"
            )
            environment["PYTHONSAFEPATH"] = "1"
            program = (
                "import importlib,json,pathlib,sys; "
                "r=importlib.import_module('pontius.legal_river_quotient_compiled_"
                "global_separation_calibration_v4_runner'); "
                "r._load_sealed_science(); root=r.ROOT.resolve(); loaded=[]; "
                "[(loaded.append(str(pathlib.Path(m.__spec__.origin).resolve()."
                "relative_to(root)).replace('\\\\','/'))) "
                "for n,m in tuple(sys.modules.items()) "
                "if (n=='pontius' or n.startswith('pontius.')) "
                "and getattr(getattr(m,'__spec__',None),'origin',None) "
                "and str(m.__spec__.origin).endswith('.py')]; "
                "print(json.dumps({'missing':sorted(set(loaded)-set(r."
                "DEPENDENCY_RELATIVE_PATHS)),'cupy':any(n=='cupy' or "
                "n.startswith('cupy.') for n in sys.modules)}))"
            )
            completed = subprocess.run(
                [sys.executable, "-B", "-P", "-c", program],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"missing": [], "cupy": False})

    def test_source_provenance_rejects_non_source_and_external_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONPYCACHEPREFIX"] = str(
                Path(directory) / "unused-pycache"
            )
            environment["PYTHONSAFEPATH"] = "1"
            origins = [
                str(ROOT / "src" / "pontius" / "synthetic.pyd"),
                str(ROOT.parent / "external" / "synthetic.py"),
            ]
            program = (
                "import importlib,json,pathlib,sys,types; "
                "r=importlib.import_module('pontius.legal_river_quotient_compiled_"
                "global_separation_calibration_v4_runner'); "
                "p=pathlib.Path(sys.pycache_prefix).resolve(); out=[]; "
                f"origins={origins!r}; "
                "\nfor origin in origins:\n"
                " m=types.SimpleNamespace(__spec__=types.SimpleNamespace(origin=origin),"
                "__cached__=str(p/'synthetic.pyc')); "
                "sys.modules['pontius.synthetic_shadow']=m\n"
                " try:\n  r._require_repo_source_imports(p); out.append(False)\n"
                " except RuntimeError:\n  out.append(True)\n"
                " finally:\n  sys.modules.pop('pontius.synthetic_shadow',None)\n"
                "print(json.dumps(out))"
            )
            completed = subprocess.run(
                [sys.executable, "-B", "-P", "-c", program],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [True, True])

    def test_fresh_interpreter_probe_observes_real_import_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "unused-pycache"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONPYCACHEPREFIX"] = str(prefix)
            environment["PYTHONSAFEPATH"] = "1"
            environment[successor._MODE_ENV] = successor._SOURCE_PROBE
            environment[successor._CHALLENGE_ENV] = sha256(
                b"adr0466-probe"
            ).hexdigest()
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-P",
                    "-m",
                    successor.LITERAL_WORKER_MODULE,
                ],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["science_loaded_before_probe_import"])
        self.assertFalse(payload["parent_science_loaded_before_probe_import"])
        self.assertFalse(payload["cupy_loaded_before_probe_import"])
        self.assertTrue(payload["science_loaded_after_probe_import"])
        self.assertTrue(payload["loaded_module_is_exact"])
        self.assertTrue(payload["python_safe_path"])
        self.assertTrue(payload["fresh_pycache_prefix"])
        self.assertFalse(payload["repo_bytecode_loaded"])
        self.assertEqual(
            payload["executed_science_identity"],
            reader._expected_executed_science_identity(),
        )
        self.assertFalse(payload["compiler_executed"])
        self.assertFalse(payload["device_queried"])

    def test_header_launch_contract_is_source_derived_without_science_import(self) -> None:
        self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
        self.assertNotIn(successor.PARENT_SCIENTIFIC_MODULE, sys.modules)
        with patch.object(
            successor,
            "_load_sealed_science",
            side_effect=AssertionError("header path imported science"),
        ):
            identity = successor._launch_abi_identity()
        self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
        self.assertNotIn(successor.PARENT_SCIENTIFIC_MODULE, sys.modules)
        contract = identity["launch_arity_contract"]
        self.assertEqual(contract["kernel_count"], 28)
        self.assertEqual(
            successor._manifest_sha256(contract),
            successor.KERNEL_SIGNATURE_MANIFEST_SHA256,
        )
        self.assertEqual(
            identity["executed_science_identity"],
            reader._expected_executed_science_identity(),
        )

    def test_exact_campaign_helper_emits_bootstrap_before_loader(self) -> None:
        events = []
        loaded = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def loader():
            self.assertEqual([kind for kind, _ in events], ["bootstrap_handshake"])
            self.assertFalse(events[0][1]["scientific_source_loaded"])
            self.assertFalse(events[0][1]["cupy_loaded"])
            loaded.append(True)
            return _FakeScience, reader._expected_executed_science_identity()

        ticks = iter((100, 120))
        result = successor._execute_deferred_campaign(
            runtime={"schema_version": "synthetic-runtime"},
            emit=emit,
            module_loader=loader,
            monotonic_ns=lambda: next(ticks),
        )
        self.assertEqual(result, 0)
        self.assertEqual(loaded, [True])
        self.assertEqual(
            [kind for kind, _ in events],
            ["bootstrap_handshake", "terminal_evidence"],
        )
        self.assertEqual(
            events[-1][1]["executed_science_identity"],
            reader._expected_executed_science_identity(),
        )
        self.assertTrue(events[-1][1]["science_import_completed"])
        self.assertTrue(events[-1][1]["science_identity_validated"])
        self.assertTrue(events[-1][1]["science_execution_started"])

    def test_loader_failure_is_typed_before_science_execution(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def loader():
            raise RuntimeError("synthetic import failure")

        ticks = iter((100, 120))
        self.assertEqual(
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=loader,
                monotonic_ns=lambda: next(ticks),
            ),
            0,
        )
        terminal = events[-1][1]
        self.assertEqual(terminal["terminal"], "deferred_science_import_rejected")
        self.assertFalse(terminal["passed"])
        self.assertIsNone(terminal["executed_science_identity"])
        self.assertFalse(terminal["science_import_completed"])
        self.assertFalse(terminal["science_identity_validated"])
        self.assertFalse(terminal["science_execution_started"])

    def test_post_import_validation_failure_is_not_mislabeled(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def loader():
            raise successor.DeferredScienceLoadFailure(
                "synthetic seal mismatch",
                import_completed=True,
                identity_validated=False,
            )

        ticks = iter((100, 120))
        self.assertEqual(
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=loader,
                monotonic_ns=lambda: next(ticks),
            ),
            0,
        )
        terminal = events[-1][1]
        self.assertTrue(terminal["science_import_completed"])
        self.assertFalse(terminal["science_identity_validated"])
        self.assertFalse(terminal["science_execution_started"])
        self.assertIsNone(terminal["executed_science_identity"])

    def test_deferred_loader_failure_reason_respects_reader_bound(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def loader():
            raise successor.DeferredScienceLoadFailure(
                "x" * 5000,
                import_completed=True,
                identity_validated=False,
            )

        ticks = iter((100, 120))
        self.assertEqual(
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=loader,
                monotonic_ns=lambda: next(ticks),
            ),
            0,
        )
        terminal = events[-1][1]
        self.assertEqual(len(terminal["reason"]), 4096)
        self.assertEqual(
            terminal["reason"],
            ("DeferredScienceLoadFailure: " + "x" * 5000)[:4096],
        )
        self.assertTrue(terminal["science_import_completed"])
        self.assertFalse(terminal["science_identity_validated"])
        self.assertFalse(terminal["science_execution_started"])

    def test_final_source_rebind_precedes_the_only_terminal(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def validate_before_terminal():
            self.assertEqual(
                [kind for kind, _ in events],
                ["bootstrap_handshake"],
            )
            raise RuntimeError("synthetic final source drift")

        ticks = iter((100, 120))
        self.assertEqual(
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=lambda: (
                    _FakeScience,
                    reader._expected_executed_science_identity(),
                ),
                pre_terminal_validator=validate_before_terminal,
                monotonic_ns=lambda: next(ticks),
            ),
            0,
        )
        self.assertEqual(
            [kind for kind, _ in events],
            ["bootstrap_handshake", "terminal_evidence"],
        )
        terminal = events[-1][1]
        self.assertEqual(terminal["terminal"], "deferred_science_import_rejected")
        self.assertFalse(terminal["passed"])
        self.assertIn("synthetic final source drift", terminal["reason"])
        self.assertEqual(
            terminal["executed_science_identity"],
            reader._expected_executed_science_identity(),
        )
        self.assertTrue(terminal["science_import_completed"])
        self.assertTrue(terminal["science_identity_validated"])
        self.assertTrue(terminal["science_execution_started"])

    def test_final_rebind_failure_preserves_typed_import_stage(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        def loader():
            raise successor.DeferredScienceLoadFailure(
                "synthetic imported-source mismatch",
                import_completed=True,
                identity_validated=False,
            )

        def final_validator():
            raise RuntimeError("synthetic correlated Git drift")

        ticks = iter((100, 120))
        self.assertEqual(
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=loader,
                pre_terminal_validator=final_validator,
                monotonic_ns=lambda: next(ticks),
            ),
            0,
        )
        terminal = events[-1][1]
        self.assertEqual(terminal["terminal"], "deferred_science_import_rejected")
        self.assertIn("synthetic correlated Git drift", terminal["reason"])
        self.assertTrue(terminal["science_import_completed"])
        self.assertFalse(terminal["science_identity_validated"])
        self.assertFalse(terminal["science_execution_started"])
        self.assertIsNone(terminal["executed_science_identity"])

    def test_execution_dependency_preload_failure_is_not_identity_validated(self) -> None:
        science = object()
        with (
            patch.object(successor, "_EXECUTION_MODULES", ("synthetic.dependency",)),
            patch.object(
                successor.importlib,
                "import_module",
                side_effect=(science, RuntimeError("synthetic dependency failure")),
            ),
            patch.object(successor, "_validate_loaded_science", return_value={}),
        ):
            with self.assertRaises(successor.DeferredScienceLoadFailure) as caught:
                successor._load_sealed_science()
        self.assertTrue(caught.exception.import_completed)
        self.assertFalse(caught.exception.identity_validated)

    def test_postload_child_rebind_failure_is_truthfully_typed(self) -> None:
        events = []

        def emit(kind, event):
            events.append((kind, dict(event)))

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(
                successor,
                "_load_sealed_science",
                return_value=(object(), reader._expected_executed_science_identity()),
            ),
            patch.object(
                successor,
                "_require_repo_source_imports",
                side_effect=RuntimeError("synthetic postload provenance failure"),
            ),
        ):
            ticks = iter((100, 120))
            successor._execute_deferred_campaign(
                runtime={"schema_version": "synthetic-runtime"},
                emit=emit,
                module_loader=lambda: successor._load_and_validate_child_science(
                    token="1" * 64,
                    expected_pycache=Path(directory) / "unused-pycache",
                ),
                monotonic_ns=lambda: next(ticks),
            )
        terminal = events[-1][1]
        self.assertTrue(terminal["science_import_completed"])
        self.assertFalse(terminal["science_identity_validated"])
        self.assertFalse(terminal["science_execution_started"])
        self.assertIsNone(terminal["executed_science_identity"])

    def test_attempt_marker_is_exclusive_exact_and_status_typed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "delegated-attempt.json"

            def durable_write(candidate, payload):
                self.assertEqual(candidate, path)
                self.assertEqual(payload, successor._attempt_bytes())
                candidate.write_bytes(payload)

            with patch.object(
                successor,
                "_exclusive_durable_write",
                side_effect=durable_write,
            ) as durable:
                successor.claim_public_attempt(path)
            durable.assert_called_once()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attempt.json"
            successor.claim_public_attempt(path)
            self.assertEqual(path.read_bytes(), successor._attempt_bytes())
            with self.assertRaises(FileExistsError):
                successor.claim_public_attempt(path)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "concurrent-attempt.json"

            def claim():
                try:
                    successor.claim_public_attempt(path)
                    return True
                except FileExistsError:
                    return False

            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(lambda _: claim(), range(8)))
            self.assertEqual(outcomes.count(True), 1)
            self.assertEqual(outcomes.count(False), 7)
            self.assertEqual(path.read_bytes(), successor._attempt_bytes())
        self.assertEqual(
            successor._expected_status_entries(result_created=False),
            sorted(
                (
                    f"?? {successor.ATTEMPT_RELATIVE_PATH}".encode("utf-8"),
                    f"?? {successor.LAUNCH_PENDING_RELATIVE_PATH}".encode("utf-8"),
                )
            ),
        )
        self.assertEqual(
            successor._expected_status_entries(result_created=True),
            sorted(
                (
                    f"?? {successor.ATTEMPT_RELATIVE_PATH}".encode("utf-8"),
                    f"?? {successor.LAUNCH_PENDING_RELATIVE_PATH}".encode("utf-8"),
                    f"?? {successor.RESULT_RELATIVE_PATH}".encode("utf-8"),
                )
            ),
        )

    def test_child_launch_claim_is_one_use_and_terminal(self) -> None:
        token = "1" * 64
        commit = "2" * 40
        authorization = {"authorization_commit": commit}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pending = root / "pending.json"
            consumed = root / "consumed.json"
            aborted = root / "aborted.json"
            with (
                patch.object(successor, "LAUNCH_PENDING_PATH", pending),
                patch.object(successor, "LAUNCH_CONSUMED_PATH", consumed),
                patch.object(successor, "LAUNCH_ABORTED_PATH", aborted),
                patch.object(successor, "_authorization_identity", return_value=authorization),
            ):
                identity = successor.claim_child_launch(token, commit)
                self.assertEqual(
                    pending.read_bytes(),
                    successor._launch_marker_bytes(identity, state="pending"),
                )
                self.assertEqual(successor.consume_child_launch(token), identity)
                self.assertFalse(pending.exists())
                self.assertTrue(consumed.is_file())
                with self.assertRaises((FileExistsError, RuntimeError)):
                    successor.consume_child_launch(token)
                self.assertEqual(
                    successor.finalize_child_launch_after_owner(token), "consumed"
                )

    def test_interrupted_terminal_marker_cleanup_is_symmetric(self) -> None:
        token = "1" * 64
        commit = "2" * 40
        authorization = {"authorization_commit": commit}
        for state, transition_name in (
            ("consumed", "consume_child_launch"),
            ("aborted", "abort_child_launch"),
        ):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                pending = root / "pending.json"
                consumed = root / "consumed.json"
                aborted = root / "aborted.json"
                with (
                    patch.object(successor, "LAUNCH_PENDING_PATH", pending),
                    patch.object(successor, "LAUNCH_CONSUMED_PATH", consumed),
                    patch.object(successor, "LAUNCH_ABORTED_PATH", aborted),
                    patch.object(
                        successor,
                        "_authorization_identity",
                        return_value=authorization,
                    ),
                ):
                    identity = successor.claim_child_launch(token, commit)
                    terminal = consumed if state == "consumed" else aborted
                    real_unlink = successor._durable_unlink

                    def interrupted(path):
                        self.assertEqual(path, pending)
                        raise OSError("synthetic interruption after terminal write")

                    with patch.object(
                        successor, "_durable_unlink", side_effect=interrupted
                    ):
                        with self.assertRaisesRegex(OSError, "synthetic interruption"):
                            getattr(successor, transition_name)(token)
                    self.assertTrue(pending.is_file())
                    self.assertEqual(
                        terminal.read_bytes(),
                        successor._launch_marker_bytes(identity, state=state),
                    )
                    with patch.object(successor, "_durable_unlink", real_unlink):
                        self.assertEqual(
                            successor.finalize_child_launch_after_owner(token), state
                        )
                    self.assertFalse(pending.exists())
                    self.assertTrue(terminal.is_file())

    def test_strict_git_metadata_checks_exact_status_markers_and_tree_hashes(self) -> None:
        token = "5" * 64
        commit = "6" * 40
        authorization = {
            "schema_version": "pontius-adr0468-one-commit-authorization-v1",
            "authorization_commit": commit,
        }
        hashes = {relative: "7" * 64 for relative in successor.DEPENDENCY_RELATIVE_PATHS}
        state = {"result_created": False, "launch_state": "pending", "drift": False}

        def absolute_git(*arguments):
            if arguments == ("rev-parse", "HEAD"):
                return commit.encode("ascii") + b"\n"
            if arguments[:3] == ("ls-files", "--error-unmatch", "--"):
                return arguments[3].encode("utf-8") + b"\n"
            if arguments == ("status", "--porcelain=v1", "-z", "--untracked-files=all"):
                rows = successor._expected_status_entries(
                    result_created=state["result_created"],
                    launch_state=state["launch_state"],
                )
                return b"\0".join(rows) + b"\0"
            raise AssertionError(arguments)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "ATTEMPT_PATH": root / "attempt.json",
                "RESULT_PATH": root / "result.jsonl",
                "LAUNCH_PENDING_PATH": root / "pending.json",
                "LAUNCH_CONSUMED_PATH": root / "consumed.json",
                "LAUNCH_ABORTED_PATH": root / "aborted.json",
            }
            paths["ATTEMPT_PATH"].write_bytes(successor._attempt_bytes())
            launch = successor._launch_claim_identity(token, commit)
            paths["LAUNCH_PENDING_PATH"].write_bytes(
                successor._launch_marker_bytes(launch, state="pending")
            )

            def current_hashes():
                if state["drift"]:
                    return {**hashes, next(iter(hashes)): "8" * 64}
                return dict(hashes)

            with (
                patch.multiple(successor, **paths),
                patch.object(successor, "_authorization_identity", return_value=authorization),
                patch.object(successor._v2, "_absolute_git", side_effect=absolute_git),
                patch.object(successor, "_dependency_hashes_at_commit", return_value=hashes),
                patch.object(successor, "_current_dependency_hashes", side_effect=current_hashes),
            ):
                metadata = successor.strict_git_metadata(
                    result_created=False, launch_token=token
                )
                self.assertEqual(metadata["authorized_dependency_hashes"], hashes)
                state["drift"] = True
                with self.assertRaises(RuntimeError):
                    successor.strict_git_metadata(
                        result_created=False, launch_token=token
                    )
                state["drift"] = False
                paths["RESULT_PATH"].write_bytes(b"header")
                paths["LAUNCH_PENDING_PATH"].unlink()
                paths["LAUNCH_CONSUMED_PATH"].write_bytes(
                    successor._launch_marker_bytes(launch, state="consumed")
                )
                state.update(result_created=True, launch_state="consumed")
                successor.strict_git_metadata(
                    result_created=True,
                    launch_state="consumed",
                    launch_token=token,
                )

    def test_child_accepts_only_the_bound_header_only_journal(self) -> None:
        token = "9" * 64
        commit = "a" * 40
        launch = successor._launch_claim_identity(token, commit)
        header = {
            "source_seal_git": {
                "commit": commit,
                "authorization": {"authorization_commit": commit},
                "launch_claim": launch,
            },
            "deferred_science_import_authorization": {
                "authorization_commit": commit
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def write(path, *, with_observation=False):
                with DurableEvidenceJournalWriter.create(
                    path=path,
                    protocol_sha256=successor.PROTOCOL_SHA256,
                    campaign_sha256=successor.CAMPAIGN_SHA256,
                ) as writer:
                    writer.append(
                        kind=JournalRecordKind.HEADER,
                        semantic_identity_sha256=_semantic(header),
                        payload=header,
                    )
                    if with_observation:
                        observation = {"unexpected": True}
                        writer.append(
                            kind=JournalRecordKind.OBSERVATION,
                            semantic_identity_sha256=_semantic(observation),
                            payload=observation,
                        )

            exact = root / "header-only.jsonl"
            write(exact)
            with patch.object(successor, "RESULT_PATH", exact):
                successor._require_header_only_result(launch)
            extra = root / "extra.jsonl"
            write(extra, with_observation=True)
            with (
                patch.object(successor, "RESULT_PATH", extra),
                self.assertRaises(RuntimeError),
            ):
                successor._require_header_only_result(launch)

    def test_public_pre_writer_failure_consumes_the_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "ATTEMPT_PATH": root / "attempt.json",
                "RESULT_PATH": root / "result.jsonl",
                "REJECTED_V3_RESULT_PATH": root / "v3.jsonl",
                "LAUNCH_PENDING_PATH": root / "pending.json",
                "LAUNCH_CONSUMED_PATH": root / "consumed.json",
                "LAUNCH_ABORTED_PATH": root / "aborted.json",
            }
            with (
                patch.multiple(successor, **paths),
                patch.object(sys, "argv", ["synthetic-owner"]),
                patch.object(successor, "_require_public_source_loader"),
                patch.object(
                    successor,
                    "assess_compiled_calibration_v2_outcome_file",
                    side_effect=RuntimeError("synthetic pre-writer failure"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "synthetic pre-writer"):
                    successor.main()
                self.assertEqual(
                    paths["ATTEMPT_PATH"].read_bytes(), successor._attempt_bytes()
                )
                with self.assertRaises(FileExistsError):
                    successor.main()

    def test_reader_terminal_lifecycle_mutations_fail_closed(self) -> None:
        bootstrap = _bootstrap_event()
        rejection = _loader_rejection_event()
        raw = _journal_bytes(
            (("bootstrap_handshake", bootstrap), ("terminal_evidence", rejection))
        )
        self.assertEqual(
            reader._validate_executed_terminal_identity(raw), rejection
        )

        imported_rejection = _loader_rejection_event(imported=True)
        imported_raw = _journal_bytes(
            (
                ("bootstrap_handshake", bootstrap),
                ("terminal_evidence", imported_rejection),
            )
        )
        self.assertEqual(
            reader._validate_executed_terminal_identity(imported_raw),
            imported_rejection,
        )

        for observations in (
            (("terminal_evidence", rejection), ("bootstrap_handshake", bootstrap)),
            (("unknown", {"value": 1}),),
            (
                ("bootstrap_handshake", {**bootstrap, "cupy_loaded": True}),
                ("terminal_evidence", rejection),
            ),
            (
                ("bootstrap_handshake", bootstrap),
                ("terminal_evidence", {**rejection, "science_identity_validated": True}),
            ),
            (
                ("bootstrap_handshake", bootstrap),
                ("terminal_evidence", rejection),
                ("unknown", {"value": 1}),
            ),
        ):
            with self.subTest(observations=observations), self.assertRaises(ValueError):
                reader._validate_executed_terminal_identity(
                    _journal_bytes(observations)
                )

        prebootstrap = _journal_bytes(())
        self.assertIsNone(reader._validate_executed_terminal_identity(prebootstrap))
        interrupted = _journal_bytes((("bootstrap_handshake", bootstrap),))
        self.assertIsNone(reader._validate_executed_terminal_identity(interrupted))
        interrupted_after_event = _journal_bytes(
            (("bootstrap_handshake", bootstrap), ("calibration_cell", {"partial": True}))
        )
        self.assertIsNone(
            reader._validate_executed_terminal_identity(interrupted_after_event)
        )

        runtime_mutation = _bootstrap_event()
        runtime_mutation["child_runtime_environment"] = {
            **runtime_mutation["child_runtime_environment"],
            "unexpected": True,
        }
        with self.assertRaises(ValueError):
            reader._validate_executed_terminal_identity(
                _journal_bytes(
                    (
                        ("bootstrap_handshake", runtime_mutation),
                        ("terminal_evidence", rejection),
                    )
                )
            )
        terminal_mutation = {**rejection, "unexpected": True}
        with self.assertRaises(ValueError):
            reader._validate_executed_terminal_identity(
                _journal_bytes(
                    (
                        ("bootstrap_handshake", bootstrap),
                        ("terminal_evidence", terminal_mutation),
                    )
                )
            )
        fabricated = {
            **rejection,
            "terminal": "fabricated_rejection",
            "executed_science_identity": reader._expected_executed_science_identity(),
            "science_import_completed": True,
            "science_identity_validated": True,
            "science_execution_started": True,
        }
        with self.assertRaises(ValueError):
            reader._validate_executed_terminal_identity(
                _journal_bytes(
                    (
                        ("bootstrap_handshake", bootstrap),
                        ("terminal_evidence", fabricated),
                    )
                )
            )

    def test_reader_semantic_identity_is_recomputed_from_payload(self) -> None:
        raw = _journal_bytes(())
        baseline = recover_journal_bytes(
            raw,
            expected_protocol_sha256=successor.PROTOCOL_SHA256,
            expected_campaign_sha256=successor.CAMPAIGN_SHA256,
        )
        reader._validate_semantic_identities(baseline)
        mutated = _rechain_journal(
            raw,
            semantic_mutator=lambda index, value: "0" * 64 if index == 0 else value,
        )
        recovery = recover_journal_bytes(
            mutated,
            expected_protocol_sha256=successor.PROTOCOL_SHA256,
            expected_campaign_sha256=successor.CAMPAIGN_SHA256,
        )
        with self.assertRaises(ValueError):
            reader._validate_semantic_identities(recovery)

    def test_reader_binds_child_and_owner_terminal_sum(self) -> None:
        rejection = _loader_rejection_event()
        rejecting_observations = (
            ("bootstrap_handshake", _bootstrap_event()),
            ("terminal_evidence", rejection),
        )
        exact_owner = parent._terminal_payload(
            terminal="deferred_science_import_rejected",
            reason="synthetic exact rejection",
            event_count=2,
            public_elapsed_ns=20,
            laboratory_elapsed_ns=7,
        )
        raw = _journal_bytes(
            rejecting_observations, owner_terminal=exact_owner
        )
        child = reader._validate_executed_terminal_identity(raw)
        reader._validate_owner_terminal_binding(raw, child)
        for mutation in (
            {**exact_owner, "terminal": "compiled_reduced_calibration_rejected"},
            {**exact_owner, "reason": ""},
            {**exact_owner, "unexpected": True},
            {
                **exact_owner,
                "claims": {**exact_owner["claims"], "truncation_authorized": True},
            },
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                reader._validate_owner_terminal_binding(
                    _journal_bytes(
                        rejecting_observations, owner_terminal=mutation
                    ),
                    child,
                )

        success_observations = _success_science_observations(False)
        success_child = dict(success_observations[-1][1])
        public_wall = parent._terminal_payload(
            terminal="public_wall_rejected",
            reason="synthetic public wall",
            event_count=len(success_observations),
            public_elapsed_ns=reader.PUBLIC_WALL_NS + 1,
            laboratory_elapsed_ns=7,
        )
        raw = _journal_bytes(success_observations, owner_terminal=public_wall)
        reader._validate_owner_terminal_binding(raw, success_child)
        wrong_priority = {
            **public_wall,
            "terminal": "outside_laboratory_wall_rejected",
        }
        with self.assertRaises(ValueError):
            reader._validate_owner_terminal_binding(
                _journal_bytes(
                    success_observations, owner_terminal=wrong_priority
                ),
                success_child,
            )
        generic = parent._terminal_payload(
            terminal="compiled_reduced_calibration_rejected",
            reason="synthetic wrong generic terminal",
            event_count=len(success_observations),
            public_elapsed_ns=20,
            laboratory_elapsed_ns=7,
        )
        with self.assertRaises(ValueError):
            reader._validate_owner_terminal_binding(
                _journal_bytes(success_observations, owner_terminal=generic),
                success_child,
            )

    def test_reader_local_lifecycle_binds_attempt_launch_and_v3_absence(self) -> None:
        token = "3" * 64
        commit = "4" * 40
        launch = successor._launch_claim_identity(token, commit)
        raw = _journal_bytes(
            (),
            header_payload={
                "source_seal_git": {"launch_claim": launch},
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt = root / "attempt.json"
            pending = root / "pending.json"
            consumed = root / "consumed.json"
            aborted = root / "aborted.json"
            v3 = root / "v3.jsonl"
            attempt.write_bytes(reader._attempt_bytes())
            aborted.write_bytes(reader._launch_marker_bytes(launch, state="aborted"))
            patches = (
                patch.object(reader, "ATTEMPT_PATH", attempt),
                patch.object(reader, "LAUNCH_PENDING_PATH", pending),
                patch.object(reader, "LAUNCH_CONSUMED_PATH", consumed),
                patch.object(reader, "LAUNCH_ABORTED_PATH", aborted),
                patch.object(reader, "REJECTED_V3_RESULT_PATH", v3),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                reader._validate_local_lifecycle(raw)
                attempt.write_bytes(b"wrong")
                with self.assertRaises(ValueError):
                    reader._validate_local_lifecycle(raw)
                attempt.write_bytes(reader._attempt_bytes())
                v3.write_bytes(b"forbidden")
                with self.assertRaises(ValueError):
                    reader._validate_local_lifecycle(raw)
                v3.unlink()
                pending.write_bytes(reader._launch_marker_bytes(launch, state="pending"))
                with self.assertRaises(ValueError):
                    reader._validate_local_lifecycle(raw)
                pending.unlink()
                aborted.unlink()
                consumed.write_bytes(
                    reader._launch_marker_bytes(launch, state="consumed")
                )
                aborted.mkdir()
                with self.assertRaises(ValueError):
                    reader._validate_local_lifecycle(raw)

    def test_reader_file_api_is_exact_path_and_detects_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alternate = root / "alternate.jsonl"
            alternate.write_bytes(b"alternate")
            with self.assertRaises(ValueError):
                reader.assess_calibration_file(alternate)

            public = root / "public.jsonl"
            public.write_bytes(b"first")

            def replace(raw):
                self.assertEqual(raw, b"first")
                public.write_bytes(b"second")
                return object()

            with (
                patch.object(reader, "RESULT_PATH", public),
                patch.object(reader, "_validate_local_lifecycle"),
                patch.object(reader, "assess_calibration_bytes", side_effect=replace),
                self.assertRaisesRegex(ValueError, "changed during assessment"),
            ):
                reader.assess_calibration_file(public)

    def test_reader_success_claims_are_exact_and_materiality_bound(self) -> None:
        for materiality in (False, True):
            observations = _success_science_observations(materiality)
            event = dict(observations[-1][1])
            raw = _journal_bytes(observations, owner_passed=True)
            reader._validate_executed_terminal_identity(
                raw, expected_materiality=materiality
            )
            with self.assertRaises(ValueError):
                reader._validate_executed_terminal_identity(
                    raw, expected_materiality=not materiality
                )
            mutated = dict(event)
            mutated["claims"] = {**event["claims"], "truncation_authorized": True}
            mutated_observations = (*observations[:-1], ("terminal_evidence", mutated))
            with self.assertRaises(ValueError):
                reader._validate_executed_terminal_identity(
                    _journal_bytes(mutated_observations, owner_passed=True)
                )
    def test_manifest_is_recomputed_from_every_signature_row(self) -> None:
        signatures = {
            "alpha": ["left", "right"],
            "beta": ["value"],
        }
        baseline = reader._manifest_sha256(signatures)
        mutated = {name: list(values) for name, values in signatures.items()}
        mutated["alpha"][1] = "wrong"
        self.assertNotEqual(reader._manifest_sha256(mutated), baseline)
        with self.assertRaises(TypeError):
            reader._manifest_sha256({"alpha": "not-a-list"})

    def test_parent_bindings_restore_without_loading_science(self) -> None:
        self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
        self.assertNotIn(successor.PARENT_SCIENTIFIC_MODULE, sys.modules)
        original = {name: getattr(parent, name) for name in successor._PARENT_BINDINGS}
        with successor.configured_parent() as engine:
            self.assertEqual(engine.RESULT_PATH, successor.RESULT_PATH)
            self.assertEqual(engine.SCIENTIFIC_MODULE, successor.SCIENTIFIC_MODULE)
            self.assertIsNot(engine.strict_git_metadata, successor.strict_git_metadata)
            self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
            self.assertNotIn(successor.PARENT_SCIENTIFIC_MODULE, sys.modules)
        for name, value in original.items():
            self.assertIs(getattr(parent, name), value)

    def test_reader_runner_dependencies_and_lifecycle_are_independent(self) -> None:
        self.assertEqual(reader.DEPENDENCY_RELATIVE_PATHS, successor.DEPENDENCY_RELATIVE_PATHS)
        self.assertEqual(reader.AUTHORIZATION_COMMIT_PATHS, successor.AUTHORIZATION_COMMIT_PATHS)
        self.assertEqual(reader.PROTOCOL_SHA256, successor.PROTOCOL_SHA256)
        self.assertEqual(reader.CAMPAIGN_SHA256, successor.CAMPAIGN_SHA256)
        self.assertFalse(successor.REJECTED_V3_RESULT_PATH.exists())
        self.assertFalse(successor.RESULT_PATH.exists())
        self.assertFalse(successor.ATTEMPT_PATH.exists())
        self.assertTrue(LAUNCHER.is_file())
        self.assertIn(
            "docs/decisions/ADR-0467-source-seal-the-deferred-science-import-successor.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )

    def test_reader_projects_only_the_inherited_v1_result_contract(self) -> None:
        before = parent.RESULT_RELATIVE_PATH
        with reader._configured_parent_reader() as configured:
            self.assertEqual(configured.RESULT_RELATIVE_PATH, reader.RESULT_RELATIVE_PATH)
            configured.verify_independent_contract()
            self.assertEqual(configured.RESULT_RELATIVE_PATH, reader.RESULT_RELATIVE_PATH)
        self.assertEqual(parent.RESULT_RELATIVE_PATH, before)
        self.assertIn(
            "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )

    def test_authorization_is_absent_until_separate_gate(self) -> None:
        if CLOSURE_ADR.exists():
            with self.assertRaisesRegex(RuntimeError, "authorization commit differs"):
                successor._authorization_identity()
            self.assertFalse(successor.RESULT_PATH.exists())
            self.assertFalse(successor.ATTEMPT_PATH.exists())
            self.assertFalse(successor.LAUNCH_PENDING_PATH.exists())
            self.assertFalse(successor.LAUNCH_CONSUMED_PATH.exists())
            self.assertFalse(successor.LAUNCH_ABORTED_PATH.exists())
            return
        if AUTHORIZATION.exists() or AUTHORIZATION_ADR.exists():
            identity = successor._authorization_identity()
            self.assertTrue(identity["single_generation_only"])
            self.assertEqual(
                identity["source_seal_commit"],
                json.loads(AUTHORIZATION.read_text(encoding="utf-8"))[
                    "source_seal_commit"
                ],
            )
        else:
            with self.assertRaises(FileNotFoundError):
                successor._authorization_identity()

    def test_authorized_reader_subprocess_target_is_importable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join(
                (str(ROOT), str(ROOT / "src"))
            )
            environment["PYTHONPYCACHEPREFIX"] = str(
                Path(directory) / "unused-pycache"
            )
            environment["PYTHONSAFEPATH"] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-P",
                    "-c",
                    (
                        "import importlib; importlib.import_module("
                        "'tests.test_legal_river_quotient_compiled_global_"
                        "separation_calibration_v4')"
                    ),
                ],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_full_reader_journal_and_mutations_after_authorization(self) -> None:
        if CLOSURE_ADR.exists():
            with self.assertRaisesRegex(RuntimeError, "authorization commit differs"):
                successor._authorization_identity()
            self.assertFalse(successor.RESULT_PATH.exists())
            self.assertFalse(successor.ATTEMPT_PATH.exists())
            self.assertFalse(successor.LAUNCH_PENDING_PATH.exists())
            self.assertFalse(successor.LAUNCH_CONSUMED_PATH.exists())
            self.assertFalse(successor.LAUNCH_ABORTED_PATH.exists())
            return
        if not AUTHORIZATION.exists() or not AUTHORIZATION_ADR.exists():
            self.skipTest("the separate invocation authorization is not sealed yet")
        if os.environ.get("PONTIUS_ADR0467_AUTH_READER_CHILD") != "1":
            with tempfile.TemporaryDirectory() as directory:
                environment = dict(os.environ)
                environment["PYTHONPATH"] = os.pathsep.join(
                    (str(ROOT), str(ROOT / "src"))
                )
                environment["PYTHONPYCACHEPREFIX"] = str(
                    Path(directory) / "unused-pycache"
                )
                environment["PYTHONSAFEPATH"] = "1"
                environment["PONTIUS_ADR0467_AUTH_READER_CHILD"] = "1"
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-P",
                        "-m",
                        "unittest",
                        (
                            "tests.test_legal_river_quotient_compiled_global_"
                            "separation_calibration_v4."
                            "CompiledGlobalSeparationCalibrationV4Tests."
                            "test_full_reader_journal_and_mutations_after_authorization"
                        ),
                    ],
                    cwd=ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120.0,
                )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            return
        authorization = successor._authorization_identity()
        token = "b" * 64
        launch = successor._launch_claim_identity(
            token, str(authorization["authorization_commit"])
        )
        dependency_hashes = successor._current_dependency_hashes()
        git = {
            "commit": authorization["authorization_commit"],
            "dirty": False,
            "strict_status": True,
            "authorization": authorization,
            "attempt_marker_sha256": sha256(successor._attempt_bytes()).hexdigest(),
            "launch_claim": launch,
            "launch_marker_sha256": sha256(
                successor._launch_marker_bytes(launch, state="pending")
            ).hexdigest(),
            "authorized_dependency_hashes": dependency_hashes,
        }
        with successor.configured_parent(launch_token=token) as engine:
            header = engine._header_payload(git)
            owner_terminal = engine._terminal_payload(
                terminal="deferred_science_import_rejected",
                reason="synthetic authorized reader control",
                event_count=2,
                public_elapsed_ns=20,
                laboratory_elapsed_ns=7,
            )
        observations = (
            ("bootstrap_handshake", _bootstrap_event()),
            ("terminal_evidence", _loader_rejection_event()),
        )

        def encoded(candidate_header, candidate_observations=observations):
            return _journal_bytes(
                candidate_observations,
                header_payload=candidate_header,
                owner_terminal=owner_terminal,
            )

        raw = encoded(header)
        assessed = reader.assess_calibration_bytes(raw)
        self.assertFalse(assessed.passed)
        self.assertEqual(assessed.terminal, "deferred_science_import_rejected")

        mutated_header = deepcopy(header)
        signatures = mutated_header["launch_abi_recovery"]["launch_arity_contract"][
            "kernel_signatures"
        ]
        first_name = next(iter(signatures))
        signatures[first_name][0] = "mutated_parameter"
        with self.assertRaises(ValueError):
            reader.assess_calibration_bytes(encoded(mutated_header))

        mutated_header = deepcopy(header)
        mutated_header["source_seal_git"]["attempt_marker_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            reader.assess_calibration_bytes(encoded(mutated_header))

        wrong_terminal = _loader_rejection_event()
        wrong_terminal["executed_science_identity"] = {"module": "wrong"}
        wrong_terminal["science_import_completed"] = True
        wrong_terminal["science_identity_validated"] = True
        wrong_terminal["science_execution_started"] = True
        with self.assertRaises(ValueError):
            reader.assess_calibration_bytes(
                encoded(
                    header,
                    (
                        ("bootstrap_handshake", _bootstrap_event()),
                        ("terminal_evidence", wrong_terminal),
                    ),
                )
            )

    def test_authorization_surface_and_single_generation_are_not_self_declared(self) -> None:
        source = "a" * 40
        head = "b" * 40
        config = {
            "schema_version": "pontius-adr0468-one-commit-authorization-v1",
            "source_seal_commit": source,
            "authorization_commit_paths": list(successor.AUTHORIZATION_COMMIT_PATHS),
        }

        def absolute_git(*arguments):
            if arguments == ("rev-parse", "HEAD"):
                return head.encode("ascii") + b"\n"
            if arguments == ("rev-list", "--parents", "-n", "1", head):
                return f"{head} {source}\n".encode("ascii")
            if arguments[:4] == ("diff", "--name-only", "--no-renames", source):
                self.assertEqual(arguments[4], head)
                return ("\n".join(successor.AUTHORIZATION_COMMIT_PATHS) + "\n").encode()
            raise AssertionError(arguments)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authorization.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with (
                patch.object(successor, "AUTHORIZATION_CONFIG_PATH", path),
                patch.object(successor._v2, "_absolute_git", absolute_git),
            ):
                identity = successor._authorization_identity()
                self.assertEqual(identity["source_seal_commit"], source)
                self.assertEqual(identity["authorization_commit"], head)
            config["authorization_commit_paths"] = list(
                reversed(successor.AUTHORIZATION_COMMIT_PATHS)
            )
            path.write_text(json.dumps(config), encoding="utf-8")
            with (
                patch.object(successor, "AUTHORIZATION_CONFIG_PATH", path),
                patch.object(successor._v2, "_absolute_git", absolute_git),
                self.assertRaises(ValueError),
            ):
                successor._authorization_identity()
            config["authorization_commit_paths"] = list(
                successor.AUTHORIZATION_COMMIT_PATHS
            )
            config["authorization_commit_paths"].append(
                "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_runner.py"
            )
            path.write_text(json.dumps(config), encoding="utf-8")
            with (
                patch.object(successor, "AUTHORIZATION_CONFIG_PATH", path),
                patch.object(successor._v2, "_absolute_git", absolute_git),
                self.assertRaises(ValueError),
            ):
                successor._authorization_identity()

    def test_reader_authorization_config_schema_is_independent_and_exact(self) -> None:
        config = {
            "schema_version": "pontius-adr0468-one-commit-authorization-v1",
            "source_seal_commit": "a" * 40,
            "authorization_commit_paths": list(reader.AUTHORIZATION_COMMIT_PATHS),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authorization.json"

            def assess(value):
                path.write_text(json.dumps(value), encoding="utf-8")
                with patch.object(reader, "AUTHORIZATION_CONFIG_PATH", path):
                    return reader._authorization_config()

            loaded, _ = assess(config)
            self.assertEqual(dict(loaded), config)
            mutations = (
                {**config, "schema_version": "wrong"},
                {**config, "source_seal_commit": "A" * 40},
                {**config, "source_seal_commit": "a" * 39},
                {
                    **config,
                    "authorization_commit_paths": list(
                        reversed(reader.AUTHORIZATION_COMMIT_PATHS)
                    ),
                },
                {**config, "extra": True},
            )
            for mutation in mutations:
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    assess(mutation)
            path.write_text(
                '{"schema_version":"pontius-adr0468-one-commit-authorization-v1",'
                '"source_seal_commit":"' + "a" * 40 + '",'
                '"source_seal_commit":"' + "b" * 40 + '",'
                '"authorization_commit_paths":[]}',
                encoding="utf-8",
            )
            with (
                patch.object(reader, "AUTHORIZATION_CONFIG_PATH", path),
                self.assertRaises(ValueError),
            ):
                reader._authorization_config()

    def test_real_git_authorization_is_exactly_one_linear_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*arguments):
                completed = subprocess.run(
                    [str(successor._v2.GIT_PATH), *arguments],
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30.0,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                return completed.stdout.strip()

            git("init")
            git("config", "user.email", "pontius-control@example.invalid")
            git("config", "user.name", "Pontius Control")
            (root / "seed.txt").write_text("source seal\n", encoding="utf-8")
            git("add", "seed.txt")
            git("commit", "-m", "source seal")
            source = git("rev-parse", "HEAD")
            authorization_path = root / successor.AUTHORIZATION_CONFIG_RELATIVE_PATH
            for relative in successor.AUTHORIZATION_COMMIT_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative == successor.AUTHORIZATION_CONFIG_RELATIVE_PATH:
                    path.write_text(
                        json.dumps(
                            {
                                "schema_version": "pontius-adr0468-one-commit-authorization-v1",
                                "source_seal_commit": source,
                                "authorization_commit_paths": list(
                                    successor.AUTHORIZATION_COMMIT_PATHS
                                ),
                            }
                        ),
                        encoding="utf-8",
                    )
                else:
                    path.write_text(f"authorized {relative}\n", encoding="utf-8")
            git("add", *successor.AUTHORIZATION_COMMIT_PATHS)
            git("commit", "-m", "authorize")
            with (
                patch.object(successor._v2, "ROOT", root),
                patch.object(
                    successor, "AUTHORIZATION_CONFIG_PATH", authorization_path
                ),
            ):
                identity = successor._authorization_identity()
                self.assertEqual(identity["source_seal_commit"], source)
                self.assertEqual(identity["authorization_commit"], git("rev-parse", "HEAD"))
                (root / "later.txt").write_text("later\n", encoding="utf-8")
                git("add", "later.txt")
                git("commit", "-m", "later")
                with self.assertRaises(RuntimeError):
                    successor._authorization_identity()
    def test_retained_v2_outcome_is_unchanged(self) -> None:
        outcome = assess_compiled_calibration_v2_outcome_file()
        self.assertEqual(successor.CONSUMED_RESULT_PATH.stat().st_size, 3_299_268)
        self.assertEqual(
            sha256(successor.CONSUMED_RESULT_PATH.read_bytes()).hexdigest(),
            "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d",
        )
        self.assertEqual(outcome.scientific_call_count, 1)
        self.assertEqual(outcome.measured_call_count, 0)


if __name__ == "__main__":
    unittest.main()
