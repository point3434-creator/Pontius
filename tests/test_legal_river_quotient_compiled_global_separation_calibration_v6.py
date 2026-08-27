from __future__ import annotations

import ast
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v4_runner as v4_runner,
)
from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v6_result as reader,
)
from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v6_runner as successor,
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
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration_v6.py"
RUNNER = ROOT / (
    "src/pontius/"
    "legal_river_quotient_compiled_global_separation_calibration_v6_runner.py"
)
V5_ATTEMPT = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json"
)
V5_ATTEMPT_SHA256 = (
    "104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d"
)
V5_ATTEMPT_BYTES = (
    b'{"campaign_sha256":"c3b38c41fa199d0076a75912513fc5eb6b2d5e4dc806e224f861426b9bad6a0d",'
    b'"closed_v4_result_relative_path":"artifacts/work_preflight/legal_river_quotient_'
    b'compiled_global_separation_calibration_v4.jsonl","protocol_sha256":"8ae5b257549a7ffe'
    b'2807d9cf5f8b54574fa698f13b6b08f79c1a690d53cfc01d","rejected_v3_result_relative_'
    b'path":"artifacts/work_preflight/legal_river_quotient_compiled_global_separation_'
    b'calibration_v3.jsonl","result_relative_path":"artifacts/work_preflight/legal_river_'
    b'quotient_compiled_global_separation_calibration_v5.jsonl","schema_version":'
    b'"pontius-adr0469-public-attempt-v5-v1"}'
)


def _semantic(payload: dict[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _journal_bytes(
    header: dict[str, object],
    owner_terminal: dict[str, object],
    *,
    child_terminal: dict[str, object] | None = None,
) -> bytes:
    bootstrap = {
        "schema_version": "pontius-adr0457-bootstrap-v1",
        "literal_worker_module": successor.LITERAL_WORKER_MODULE,
        "python_no_bytecode": True,
        "child_runtime_environment": reader._v4._expected_child_runtime(),
        "cupy_loaded": False,
        "scientific_source_loaded": False,
        "parent_journal_present": True,
    }
    if child_terminal is None:
        child_terminal = {
            "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
            "terminal": "deferred_science_import_rejected",
            "passed": False,
            "reason": "synthetic v6 preauthorization control",
            "laboratory_elapsed_ns": 7,
            "candidate_selected": None,
            "topology_selected": None,
            "arithmetic_schedule_selected": None,
            "claims": dict(reader._REJECTED_CLAIMS),
            "executed_science_identity": None,
            "science_import_completed": False,
            "science_identity_validated": False,
            "science_execution_started": False,
        }
    observations = (
        ("bootstrap_handshake", bootstrap),
        ("terminal_evidence", child_terminal),
    )
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic-v6.jsonl"
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
            source_commit = header["source_seal_git"]["commit"]
            for index, (kind, event) in enumerate(observations):
                wrapper = {
                    "schema_version": "pontius-adr0457-owner-observation-v1",
                    "event_index": index,
                    "kind": kind,
                    "event": event,
                    "source_commit": source_commit,
                }
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=_semantic(wrapper),
                    payload=wrapper,
                )
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=_semantic(owner_terminal),
                payload=owner_terminal,
            )
        return path.read_bytes()


def _rechain(raw: bytes, record_index: int, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=successor.PROTOCOL_SHA256,
        expected_campaign_sha256=successor.CAMPAIGN_SHA256,
    )
    output = bytearray()
    previous = None
    for index, record in enumerate(recovery.records):
        payload = deepcopy(record.body.payload)
        if index == record_index:
            mutate(payload)
        semantic = sha256(canonical_journal_json_bytes(payload)).hexdigest()
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
    rebuilt = bytes(output)
    if rebuilt == raw:
        raise AssertionError("mutation did not change journal bytes")
    checked = recover_journal_bytes(
        rebuilt,
        expected_protocol_sha256=successor.PROTOCOL_SHA256,
        expected_campaign_sha256=successor.CAMPAIGN_SHA256,
    )
    if not checked.is_complete or len(checked.records) != len(recovery.records):
        raise AssertionError("mutation did not produce a complete re-chained journal")
    return rebuilt


def _at(payload: object, path: tuple[object, ...]):
    current = payload
    for name in path:
        current = current[name]  # type: ignore[index]
    return current


def _replace(payload: object, path: tuple[object, ...], value: object) -> None:
    current = payload
    for name in path[:-1]:
        current = current[name]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


def _mapping_paths(value: object, path: tuple[object, ...] = ()):
    if type(value) is dict:
        yield path
        for key, child in value.items():
            yield from _mapping_paths(child, (*path, key))
    elif type(value) is list:
        for index, child in enumerate(value):
            yield from _mapping_paths(child, (*path, index))


def _alias_paths(value: object, path: tuple[object, ...] = ()):
    if type(value) is dict:
        for key, child in value.items():
            yield from _alias_paths(child, (*path, key))
    elif type(value) is list:
        for index, child in enumerate(value):
            yield from _alias_paths(child, (*path, index))
    elif type(value) is bool or (type(value) is int and value in {0, 1}):
        yield path


class _TraceLock:
    def __init__(self, name: str, trace: list[str]) -> None:
        self.name = name
        self.trace = trace

    def __enter__(self):
        self.trace.append(f"enter:{self.name}")
        return self

    def __exit__(self, *_args) -> None:
        self.trace.append(f"exit:{self.name}")


@contextmanager
def _isolated_lifecycle():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        paths = {
            "v3_result": root / "v3.jsonl",
            "v4_result": root / "v4.jsonl",
            "v4_attempt": root / "v4.attempt.json",
            "v4_pending": root / "v4.pending.json",
            "v4_consumed": root / "v4.consumed.json",
            "v4_aborted": root / "v4.aborted.json",
            "v5_result": root / "v5.jsonl",
            "v5_attempt": root / "v5.attempt.json",
            "v5_pending": root / "v5.pending.json",
            "v5_consumed": root / "v5.consumed.json",
            "v5_aborted": root / "v5.aborted.json",
            "v5_auth": root / "v5-auth.json",
            "v6_result": root / "v6.jsonl",
            "v6_attempt": root / "v6.attempt.json",
            "v6_pending": root / "v6.pending.json",
            "v6_consumed": root / "v6.consumed.json",
            "v6_aborted": root / "v6.aborted.json",
            "v6_auth": root / "v6-auth.json",
        }
        paths["v5_attempt"].write_bytes(V5_ATTEMPT_BYTES)
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(reader._v4, "REJECTED_V3_RESULT_PATH", paths["v3_result"])
            )
            for module in (successor, reader):
                bindings = {
                    "V4_RESULT_PATH": paths["v4_result"],
                    "V4_ATTEMPT_PATH": paths["v4_attempt"],
                    "V4_LAUNCH_PENDING_PATH": paths["v4_pending"],
                    "V4_LAUNCH_CONSUMED_PATH": paths["v4_consumed"],
                    "V4_LAUNCH_ABORTED_PATH": paths["v4_aborted"],
                    "V4_LAUNCH_PATHS": (
                        paths["v4_pending"],
                        paths["v4_consumed"],
                        paths["v4_aborted"],
                    ),
                    "V5_RESULT_PATH": paths["v5_result"],
                    "V5_ATTEMPT_PATH": paths["v5_attempt"],
                    "V5_LAUNCH_PENDING_PATH": paths["v5_pending"],
                    "V5_LAUNCH_CONSUMED_PATH": paths["v5_consumed"],
                    "V5_LAUNCH_ABORTED_PATH": paths["v5_aborted"],
                    "V5_LAUNCH_PATHS": (
                        paths["v5_pending"],
                        paths["v5_consumed"],
                        paths["v5_aborted"],
                    ),
                    "V5_AUTHORIZATION_PATH": paths["v5_auth"],
                    "V5_AUTHORIZATION_CONFIG_PATH": paths["v5_auth"],
                    "RESULT_PATH": paths["v6_result"],
                    "ATTEMPT_PATH": paths["v6_attempt"],
                    "LAUNCH_PENDING_PATH": paths["v6_pending"],
                    "LAUNCH_CONSUMED_PATH": paths["v6_consumed"],
                    "LAUNCH_ABORTED_PATH": paths["v6_aborted"],
                    "AUTHORIZATION_CONFIG_PATH": paths["v6_auth"],
                }
                for name, value in bindings.items():
                    if hasattr(module, name):
                        stack.enter_context(patch.object(module, name, value))
            yield paths


@contextmanager
def _synthetic_preauthorization():
    source_seal = "a" * 40
    authorization_commit = "b" * 40
    with _isolated_lifecycle() as paths:
        auth_config = {
            "schema_version": successor.AUTHORIZATION_SCHEMA_VERSION,
            "source_seal_commit": source_seal,
            "authorization_commit_paths": list(successor.AUTHORIZATION_COMMIT_PATHS),
        }
        paths["v6_auth"].write_text(
            json.dumps(auth_config, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        config_hash = sha256(
            paths["v6_auth"].read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        authorization = {
            "schema_version": successor.AUTHORIZATION_SCHEMA_VERSION,
            "config_relative_path": successor.AUTHORIZATION_CONFIG_RELATIVE_PATH,
            "config_canonical_lf_sha256": config_hash,
            "source_seal_commit": source_seal,
            "authorization_commit": authorization_commit,
            "authorization_commit_paths": list(successor.AUTHORIZATION_COMMIT_PATHS),
            "single_generation_only": True,
        }
        dependency_hashes = successor._current_dependency_hashes()
        token = "c" * 64
        launch = successor._launch_claim_identity(token, authorization_commit)
        git = {
            "commit": authorization_commit,
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
        with patch.object(
            successor, "_authorization_identity", return_value=authorization
        ):
            with successor.configured_parent(launch_token=token) as engine:
                header = engine._header_payload(git)
                owner_terminal = engine._terminal_payload(
                    terminal="deferred_science_import_rejected",
                    reason="synthetic v6 preauthorization control",
                    event_count=2,
                    public_elapsed_ns=20,
                    laboratory_elapsed_ns=7,
                )
        raw = _journal_bytes(header, owner_terminal)
        with (
            patch.object(reader._v4, "_validate_authorization_git", return_value=None),
            patch.object(
                reader._v4,
                "_absolute_git",
                return_value=paths["v6_auth"].read_bytes(),
            ),
        ):
            yield raw, header, paths


class CompiledGlobalSeparationCalibrationV6Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertEqual(V5_ATTEMPT_BYTES, V5_ATTEMPT.read_bytes())
        status = V5_ATTEMPT.stat(follow_symlinks=False)
        self.assertTrue(stat.S_ISREG(status.st_mode))
        self.assertFalse(V5_ATTEMPT.is_symlink())
        self.assertFalse(
            getattr(status, "st_file_attributes", 0)
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
        self.assertEqual(len(V5_ATTEMPT_BYTES), 606)
        self.assertEqual(sha256(V5_ATTEMPT_BYTES).hexdigest(), V5_ATTEMPT_SHA256)
        self.assertEqual(V5_ATTEMPT, successor.V5_ATTEMPT_PATH)
        self.assertEqual(V5_ATTEMPT_BYTES, successor._retained_v5_attempt_bytes())

        absent = (
            ROOT
            / "artifacts/work_preflight/"
            "legal_river_quotient_compiled_global_separation_calibration_v3.jsonl",
            successor.V4_RESULT_PATH,
            successor.V4_ATTEMPT_PATH,
            successor.V4_LAUNCH_PENDING_PATH,
            successor.V4_LAUNCH_CONSUMED_PATH,
            successor.V4_LAUNCH_ABORTED_PATH,
            successor.V5_RESULT_PATH,
            successor.V5_LAUNCH_PENDING_PATH,
            successor.V5_LAUNCH_CONSUMED_PATH,
            successor.V5_LAUNCH_ABORTED_PATH,
            successor.V5_AUTHORIZATION_CONFIG_PATH,
            successor.RESULT_PATH,
            successor.ATTEMPT_PATH,
            successor.LAUNCH_PENDING_PATH,
            successor.LAUNCH_CONSUMED_PATH,
            successor.LAUNCH_ABORTED_PATH,
            successor.AUTHORIZATION_CONFIG_PATH,
        )
        for path in absent:
            self.assertFalse(os.path.lexists(path), path)

    def test_config_attempt_and_all_public_identities_are_fresh(self) -> None:
        self.assertEqual(
            sha256(CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            successor.RECOVERY_CONFIG_SHA256,
        )
        self.assertEqual(successor.RECOVERY_CONFIG_SHA256, reader.RECOVERY_CONFIG_SHA256)
        self.assertEqual(successor.DEPENDENCY_RELATIVE_PATHS, reader.DEPENDENCY_RELATIVE_PATHS)
        self.assertIn(successor.V5_ATTEMPT_RELATIVE_PATH, successor.DEPENDENCY_RELATIVE_PATHS)
        self.assertIn(successor.RECOVERY_CONFIG_RELATIVE_PATH, successor.DEPENDENCY_RELATIVE_PATHS)
        self.assertNotIn(
            successor.AUTHORIZATION_CONFIG_RELATIVE_PATH,
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertNotIn(
            "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-"
            "calibration-invocation.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertEqual(
            successor.AUTHORIZATION_COMMIT_PATHS,
            (
                "ARCHITECTURE.md",
                "RISK_REGISTER.md",
                "ROADMAP.md",
                "STATUS.md",
                "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-"
                "calibration-invocation.md",
                successor.AUTHORIZATION_CONFIG_RELATIVE_PATH,
            ),
        )
        self.assertNotEqual(successor.PROTOCOL_SHA256, v4_runner.PROTOCOL_SHA256)
        self.assertNotEqual(successor.CAMPAIGN_SHA256, v4_runner.CAMPAIGN_SHA256)
        self.assertNotEqual(successor.PROTOCOL_SHA256, successor.V5_PROTOCOL_SHA256)
        self.assertNotEqual(successor.CAMPAIGN_SHA256, successor.V5_CAMPAIGN_SHA256)
        self.assertEqual(
            successor.ATTEMPT_SCHEMA_VERSION,
            "pontius-adr0470-public-attempt-v6-v1",
        )
        self.assertEqual(
            successor.LAUNCH_SCHEMA_VERSION,
            "pontius-adr0471-one-use-child-launch-v6-v1",
        )
        self.assertEqual(successor._attempt_bytes(), reader._attempt_bytes())

    def test_fresh_process_source_probe_preserves_every_lifecycle(self) -> None:
        attempt_before = V5_ATTEMPT.read_bytes()
        challenge = sha256(b"adr0470-v6-source-probe").hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "unused-pycache"
            environment = dict(os.environ)
            for name in (
                *successor._LEGACY_ENV_NAMES,
                successor._MODE_ENV,
                successor._CHALLENGE_ENV,
                successor._SPOOL_ENV,
                successor._LAUNCH_TOKEN_ENV,
                successor._PUBLIC_PYCACHE_ENV,
            ):
                environment.pop(name, None)
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONPYCACHEPREFIX"] = str(prefix)
            environment["PYTHONSAFEPATH"] = "1"
            program = (
                "import json; "
                "from pontius import legal_river_quotient_compiled_global_"
                "separation_calibration_v6_runner as r; "
                f"print(json.dumps(r.source_seal_probe({challenge!r}),sort_keys=True))"
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
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["schema_version"],
            "pontius-adr0470-retained-attempt-source-probe-v6",
        )
        self.assertEqual(
            payload["retained_v5_attempt_recovery"],
            successor._retained_v5_attempt_recovery_identity(),
        )
        for name in (
            "v4_lifecycle_absent",
            "v5_attempt_retained_exactly",
            "v5_result_launch_authorization_absent",
            "v6_result_absent",
            "v6_attempt_absent",
            "v6_launch_markers_absent",
            "v6_authorization_absent",
            "python_safe_path",
            "fresh_pycache_prefix",
            "loaded_module_is_exact",
        ):
            self.assertIs(payload[name], True, name)
        for name in (
            "science_loaded_before_probe_import",
            "parent_science_loaded_before_probe_import",
            "cupy_loaded_before_probe_import",
            "repo_bytecode_loaded",
            "compiler_executed",
            "device_queried",
        ):
            self.assertIs(payload[name], False, name)
        self.assertIs(payload["science_loaded_after_probe_import"], True)
        self.assertEqual(V5_ATTEMPT.read_bytes(), attempt_before)
        for path in (
            successor.RESULT_PATH,
            successor.ATTEMPT_PATH,
            successor.LAUNCH_PENDING_PATH,
            successor.LAUNCH_CONSUMED_PATH,
            successor.LAUNCH_ABORTED_PATH,
            successor.AUTHORIZATION_CONFIG_PATH,
        ):
            self.assertFalse(os.path.lexists(path), path)
        attempt = json.loads(successor._attempt_bytes())
        self.assertEqual(
            attempt["retained_v5_attempt_relative_path"],
            successor.V5_ATTEMPT_RELATIVE_PATH,
        )
        self.assertEqual(attempt["retained_v5_attempt_bytes"], 606)
        self.assertEqual(attempt["retained_v5_attempt_raw_sha256"], V5_ATTEMPT_SHA256)
        self.assertEqual(successor.SCIENTIFIC_MODULE, v4_runner.SCIENTIFIC_MODULE)
        self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
        self.assertFalse(
            any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)
        )

        production_modules = (successor, reader)
        for module in production_modules:
            imported = {
                getattr(value, "__name__", "")
                for value in vars(module).values()
                if type(value).__name__ == "module"
            }
            self.assertFalse(
                any("compiled_global_separation_calibration_v5" in name for name in imported),
                imported,
            )
            self.assertFalse(hasattr(module, "_v5"))

    def test_writer_and_reader_bindings_are_complete_restore_and_lock_v4_first(self) -> None:
        with _isolated_lifecycle():
            writer_replacements = successor._v6_replacements()
            self.assertEqual(set(successor._V4_BINDINGS), set(writer_replacements))
            writer_before = {
                name: getattr(successor._v4, name) for name in successor._V4_BINDINGS
            }
            with successor._configured_v4() as engine:
                for name, value in writer_replacements.items():
                    self.assertIs(getattr(engine, name), value, name)
            for name, value in writer_before.items():
                self.assertIs(getattr(successor._v4, name), value, name)
            with self.assertRaisesRegex(RuntimeError, "synthetic writer context"):
                with successor._configured_v4():
                    raise RuntimeError("synthetic writer context")
            for name, value in writer_before.items():
                self.assertIs(getattr(successor._v4, name), value, name)

            reader_replacements = reader._replacements()
            self.assertEqual(set(reader._V4_BINDINGS), set(reader_replacements))
            reader_before = {
                name: getattr(reader._v4, name) for name in reader._V4_BINDINGS
            }
            with reader._configured_v4_reader() as inherited:
                for name, value in reader_replacements.items():
                    self.assertIs(getattr(inherited, name), value, name)
            for name, value in reader_before.items():
                self.assertIs(getattr(reader._v4, name), value, name)
            with self.assertRaisesRegex(RuntimeError, "synthetic reader context"):
                with reader._configured_v4_reader():
                    raise RuntimeError("synthetic reader context")
            for name, value in reader_before.items():
                self.assertIs(getattr(reader._v4, name), value, name)

            writer_trace: list[str] = []
            with (
                patch.object(
                    successor._v4,
                    "_BINDING_LOCK",
                    _TraceLock("v4", writer_trace),
                ),
                patch.object(
                    successor,
                    "_BINDING_LOCK",
                    _TraceLock("v6", writer_trace),
                ),
                successor._configured_v4(),
            ):
                pass
            self.assertEqual(
                writer_trace,
                ["enter:v4", "enter:v6", "exit:v6", "exit:v4"],
            )

            reader_trace: list[str] = []
            with (
                patch.object(reader._v4, "_LOCK", _TraceLock("v4", reader_trace)),
                patch.object(reader, "_LOCK", _TraceLock("v6", reader_trace)),
                reader._configured_v4_reader(),
            ):
                pass
            self.assertEqual(
                reader_trace,
                ["enter:v4", "enter:v6", "exit:v6", "exit:v4"],
            )

    def test_actual_layered_header_round_trips_and_matches_frozen_recovery_shape(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            self.assertEqual(len(header), 16)
            retained = header["retained_v5_attempt_recovery"]
            self.assertEqual(
                set(retained),
                {
                    "schema_version",
                    "config_relative_path",
                    "config_canonical_lf_sha256",
                    "retained_v5_attempt",
                    "closed_predecessors",
                    "fresh_v6",
                },
            )
            self.assertEqual(
                set(retained["retained_v5_attempt"]),
                {
                    "relative_path",
                    "bytes",
                    "raw_sha256",
                    "regular_file",
                    "symlink",
                    "reparse_point",
                },
            )
            self.assertEqual(
                set(retained["closed_predecessors"]),
                {
                    "rejected_v3_result_relative_path",
                    "rejected_v3_result_exists",
                    "v4_result_relative_path",
                    "v4_lifecycle_absent",
                    "v5_result_relative_path",
                    "v5_result_exists",
                    "v5_launch_marker_count",
                    "v5_authorization_relative_path",
                    "v5_authorization_exists",
                },
            )
            self.assertEqual(
                set(retained["fresh_v6"]),
                {
                    "result_relative_path",
                    "attempt_relative_path",
                    "launch_pending_relative_path",
                    "launch_consumed_relative_path",
                    "launch_aborted_relative_path",
                    "authorization_config_relative_path",
                    "authorization_schema_version",
                },
            )
            reader._validate_deferred_header(raw)
            assessed = reader.assess_calibration_bytes(raw)
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "deferred_science_import_rejected")

    def test_every_actual_header_mapping_domain_rejects_missing_and_extra_keys(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            paths = tuple(_mapping_paths(header))
            self.assertIn(("retained_v5_attempt_recovery",), paths)
            self.assertIn(
                ("retained_v5_attempt_recovery", "retained_v5_attempt"), paths
            )
            self.assertIn(
                ("retained_v5_attempt_recovery", "closed_predecessors"), paths
            )
            self.assertIn(("retained_v5_attempt_recovery", "fresh_v6"), paths)
            for path in paths:
                target = header if not path else _at(header, path)
                self.assertIs(type(target), dict)
                for key in tuple(target):
                    with self.subTest(operation="missing", path=path, key=key):

                        def mutate(payload, path=path, key=key):
                            current = payload if not path else _at(payload, path)
                            del current[key]

                        with self.assertRaises((TypeError, ValueError)):
                            reader._validate_deferred_header(_rechain(raw, 0, mutate))
                with self.subTest(operation="extra", path=path):

                    def mutate(payload, path=path):
                        current = payload if not path else _at(payload, path)
                        current["unexpected"] = "field"

                    with self.assertRaises((TypeError, ValueError)):
                        reader._validate_deferred_header(_rechain(raw, 0, mutate))

    def test_all_rejection_bool_int_aliases_are_rejected(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=successor.PROTOCOL_SHA256,
                expected_campaign_sha256=successor.CAMPAIGN_SHA256,
            )
            paths = [
                (index, path)
                for index, record in enumerate(recovery.records)
                for path in _alias_paths(record.body.payload)
            ]
            recovery_paths = [
                item
                for item in paths
                if item[0] == 0
                and item[1][:1] == ("retained_v5_attempt_recovery",)
            ]
            inherited_paths = [item for item in paths if item not in recovery_paths]
            self.assertEqual(len(inherited_paths), 38)
            self.assertEqual(len(paths), 46)
            for index, path in paths:
                original = _at(recovery.records[index].body.payload, path)
                replacement = int(original) if type(original) is bool else bool(original)
                self.assertEqual(replacement, original)
                self.assertIsNot(type(replacement), type(original))
                with self.subTest(record=index, path=path):

                    def mutate(payload, path=path, replacement=replacement):
                        _replace(payload, path, replacement)

                    with self.assertRaises((TypeError, ValueError)):
                        reader.assess_calibration_bytes(_rechain(raw, index, mutate))

    def test_all_started_science_bool_int_aliases_are_rejected(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=successor.PROTOCOL_SHA256,
                expected_campaign_sha256=successor.CAMPAIGN_SHA256,
            )
            owner_terminal = dict(recovery.records[-1].body.payload)
            owner_terminal.update(
                terminal="compiler_rejected",
                reason="synthetic started-science rejection",
            )
            child_terminal = {
                "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
                "terminal": "compiler_rejected",
                "passed": False,
                "reason": "synthetic started-science rejection",
                "laboratory_elapsed_ns": 7,
                "candidate_selected": None,
                "topology_selected": None,
                "arithmetic_schedule_selected": None,
                "claims": dict(reader._REJECTED_CLAIMS),
                "executed_science_identity": reader._v4._expected_executed_science_identity(),
                "science_import_completed": True,
                "science_identity_validated": True,
                "science_execution_started": True,
            }
            started = _journal_bytes(
                header,
                owner_terminal,
                child_terminal=child_terminal,
            )
            assessed = reader.assess_calibration_bytes(started)
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "compiler_rejected")
            started_recovery = recover_journal_bytes(
                started,
                expected_protocol_sha256=successor.PROTOCOL_SHA256,
                expected_campaign_sha256=successor.CAMPAIGN_SHA256,
            )
            paths = [
                (index, path)
                for index, record in enumerate(started_recovery.records)
                for path in _alias_paths(record.body.payload)
            ]
            recovery_paths = [
                item
                for item in paths
                if item[0] == 0
                and item[1][:1] == ("retained_v5_attempt_recovery",)
            ]
            self.assertEqual(len([item for item in paths if item not in recovery_paths]), 39)
            self.assertEqual(len(paths), 47)
            for index, path in paths:
                original = _at(started_recovery.records[index].body.payload, path)
                replacement = int(original) if type(original) is bool else bool(original)
                with self.subTest(record=index, path=path):

                    def mutate(payload, path=path, replacement=replacement):
                        _replace(payload, path, replacement)

                    with self.assertRaises((TypeError, ValueError)):
                        reader.assess_calibration_bytes(_rechain(started, index, mutate))

    def test_imported_but_unvalidated_science_rejection_is_truthful(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=successor.PROTOCOL_SHA256,
                expected_campaign_sha256=successor.CAMPAIGN_SHA256,
            )
            owner_terminal = dict(recovery.records[-1].body.payload)
            child_terminal = {
                "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
                "terminal": "deferred_science_import_rejected",
                "passed": False,
                "reason": "synthetic post-import identity rejection",
                "laboratory_elapsed_ns": 7,
                "candidate_selected": None,
                "topology_selected": None,
                "arithmetic_schedule_selected": None,
                "claims": dict(reader._REJECTED_CLAIMS),
                "executed_science_identity": None,
                "science_import_completed": True,
                "science_identity_validated": False,
                "science_execution_started": False,
            }
            imported = _journal_bytes(
                header,
                owner_terminal,
                child_terminal=child_terminal,
            )
            assessed = reader.assess_calibration_bytes(imported)
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "deferred_science_import_rejected")

    def test_every_inherited_success_equality_site_is_type_exact(self) -> None:
        base = reader._BASE_READER
        cases = {
            "arithmetic_admission": base._expected_arithmetic_admission(),
            "source_contract": {
                "full_codeword_reconstruction_call_sites": 1,
                "batched_admission_consumer_sites": 2,
                "timed_host_surface": {
                    "schema_version": "pontius-adr0458-timed-host-surface-v1",
                    "phase_callbacks": list(base.PHASE_CALLBACKS),
                    "host_prefix_authority_calls": 0,
                    "host_unbounded_scientific_comparisons": 0,
                    "nonterminal_device_to_host_scientific_transfers": 0,
                    "passed": True,
                },
            },
            "compile_resource_evidence": {
                "register_ceiling": 255,
                "spill_store_ceiling_bytes": 0,
                "spill_load_ceiling_bytes": 0,
            },
            "module_load_and_runtime": {"kernel_count": 28},
            "device_memory_admission": {
                "physical_RRNS_table_arena_allocations": 1,
                "RRNS_table_arena_channel_capacity": 5,
                "campaign": base._expected_liveness(base._campaign_memory_peak()),
            },
            "device_domain_prepared": {
                "cards": 10,
                "memory": {
                    "shared_five_channel_replay": base._expected_liveness(
                        base._domain_memory_peak(10)
                    )
                },
            },
            "calibration_cell": {
                "pass_index": 1,
                "phase_partition": {"primitive_total_ns": 0},
                "terminal": {
                    "found_positive": 1,
                    "globally_closed": 0,
                    "prefix_decision_keys": 1,
                },
                "differential": {
                    "complete_positive_output": {
                        "authority_coordinates_checked": 1,
                    }
                },
            },
            "fit_projection": {
                "fit_rows": [{"target_upper_ceiling_ns": 1, "target_work": 0}],
                "primitive_rows": [{"projected_primitive_upper_ns": 1}],
                "materiality_rows": [
                    {
                        "direct_upper_ns": 1,
                        "zeta_upper_ns": 0,
                        "zeta_at_most_half_direct": True,
                    }
                ],
            },
        }
        alias_count = 0
        for kind, event in cases.items():
            reader._validate_inherited_success_event_types(kind, event)
            for path in tuple(_alias_paths(event)):
                original = _at(event, path)
                replacement = int(original) if type(original) is bool else bool(original)
                mutated = deepcopy(event)
                _replace(mutated, path, replacement)
                with self.subTest(kind=kind, path=path), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    reader._validate_inherited_success_event_types(kind, mutated)
                alias_count += 1
        self.assertGreater(alias_count, 30)

        nonintegral = deepcopy(cases["module_load_and_runtime"])
        nonintegral["kernel_count"] = 28.0
        with self.assertRaises((TypeError, ValueError)):
            reader._validate_inherited_success_event_types(
                "module_load_and_runtime", nonintegral
            )

    def test_recovery_config_identities_cannot_cross_layers(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            crossings = (
                (
                    ("absolute_git_recovery", "config_relative_path"),
                    reader.DEFERRED_IMPORT_CONFIG_RELATIVE_PATH,
                ),
                (
                    ("launch_abi_recovery", "config_canonical_lf_sha256"),
                    reader.ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256,
                ),
                (
                    (
                        "retained_v5_attempt_recovery",
                        "config_relative_path",
                    ),
                    reader.HEADER_CONTRACT_CONFIG_RELATIVE_PATH,
                ),
                (
                    (
                        "retained_v5_attempt_recovery",
                        "config_canonical_lf_sha256",
                    ),
                    reader.DEFERRED_IMPORT_CONFIG_SHA256,
                ),
            )
            for path, replacement in crossings:
                with self.subTest(path=path):

                    def mutate(payload, path=path, replacement=replacement):
                        _replace(payload, path, replacement)

                    with self.assertRaises((TypeError, ValueError)):
                        reader._validate_deferred_header(_rechain(raw, 0, mutate))

    def test_authorization_parser_and_injected_git_proof_are_real_and_type_exact(self) -> None:
        source_seal = "a" * 40
        authorization_commit = "b" * 40
        with _isolated_lifecycle() as paths:
            config = {
                "schema_version": reader.AUTHORIZATION_SCHEMA_VERSION,
                "source_seal_commit": source_seal,
                "authorization_commit_paths": list(reader.AUTHORIZATION_COMMIT_PATHS),
            }
            raw = json.dumps(
                config, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            paths["v6_auth"].write_bytes(raw)
            parsed, config_hash = reader._authorization_config()
            self.assertEqual(parsed, config)

            blobs = {
                path: f"independent blob for {path}\n".encode("utf-8")
                for path in reader.DEPENDENCY_RELATIVE_PATHS
            }
            dependencies = {
                path: sha256(blob.replace(b"\r\n", b"\n")).hexdigest()
                for path, blob in blobs.items()
            }

            def absolute_git(*arguments: str) -> bytes:
                if arguments == (
                    "rev-list",
                    "--parents",
                    "-n",
                    "1",
                    authorization_commit,
                ):
                    return f"{authorization_commit} {source_seal}\n".encode("ascii")
                if arguments == (
                    "diff",
                    "--name-only",
                    "--no-renames",
                    source_seal,
                    authorization_commit,
                ):
                    return ("\n".join(reader.AUTHORIZATION_COMMIT_PATHS) + "\n").encode()
                if len(arguments) == 2 and arguments[0] == "show":
                    commit, relative = arguments[1].split(":", 1)
                    self.assertEqual(commit, authorization_commit)
                    if relative == reader.AUTHORIZATION_CONFIG_RELATIVE_PATH:
                        return raw
                    return blobs[relative]
                raise AssertionError(f"unexpected absolute Git call: {arguments!r}")

            with patch.object(
                successor._v4._v2,
                "_absolute_git",
                side_effect=absolute_git,
            ):
                writer_identity = successor._authorization_identity(
                    commit=authorization_commit
                )
            self.assertEqual(
                writer_identity,
                {
                    "schema_version": successor.AUTHORIZATION_SCHEMA_VERSION,
                    "config_relative_path": (
                        successor.AUTHORIZATION_CONFIG_RELATIVE_PATH
                    ),
                    "config_canonical_lf_sha256": config_hash,
                    "source_seal_commit": source_seal,
                    "authorization_commit": authorization_commit,
                    "authorization_commit_paths": list(
                        successor.AUTHORIZATION_COMMIT_PATHS
                    ),
                    "single_generation_only": True,
                },
            )

            def mismatched_authorization_blob(*arguments: str) -> bytes:
                if (
                    len(arguments) == 2
                    and arguments[0] == "show"
                    and arguments[1].endswith(
                        ":" + successor.AUTHORIZATION_CONFIG_RELATIVE_PATH
                    )
                ):
                    return b'{"different":"committed authorization"}\n'
                return absolute_git(*arguments)

            with (
                patch.object(
                    successor._v4._v2,
                    "_absolute_git",
                    side_effect=mismatched_authorization_blob,
                ),
                self.assertRaisesRegex(RuntimeError, "Git blob"),
            ):
                successor._authorization_identity(commit=authorization_commit)

            with patch.object(reader._v4, "_absolute_git", side_effect=absolute_git):
                reader._validate_v6_authorization_git(
                    authorization_commit,
                    source_seal,
                    dependencies,
                    config_hash,
                )
                mutated = dict(dependencies)
                mutated[next(iter(mutated))] = "0" * 64
                with self.assertRaisesRegex(ValueError, "authorization Git identity"):
                    reader._validate_v6_authorization_git(
                        authorization_commit,
                        source_seal,
                        mutated,
                        config_hash,
                    )

            with (
                patch.object(
                    reader._v4,
                    "_absolute_git",
                    side_effect=mismatched_authorization_blob,
                ),
                self.assertRaisesRegex(ValueError, "Git blob"),
            ):
                reader._validate_v6_authorization_git(
                    authorization_commit,
                    source_seal,
                    dependencies,
                    config_hash,
                )

            for mutation in (
                {**config, "schema_version": "wrong"},
                {**config, "source_seal_commit": True},
                {
                    **config,
                    "authorization_commit_paths": list(
                        reversed(config["authorization_commit_paths"])
                    ),
                },
                {**config, "extra": False},
            ):
                with self.subTest(mutation=mutation):
                    paths["v6_auth"].write_text(json.dumps(mutation), encoding="utf-8")
                    with self.assertRaises((TypeError, ValueError)):
                        reader._authorization_config()

    def test_live_authorization_ancestry_has_no_skipped_branch(self) -> None:
        if os.path.lexists(AUTHORIZATION):
            config, config_hash = reader._authorization_config()
            authorization_commit = (
                reader._v4._absolute_git("rev-parse", "HEAD")
                .decode("ascii")
                .strip()
            )
            dependencies = reader._v4._dependency_hashes_at_commit(
                authorization_commit
            )
            reader._validate_v6_authorization_git(
                authorization_commit,
                config["source_seal_commit"],
                dependencies,
                config_hash,
            )
        else:
            self.assertFalse(os.path.lexists(AUTHORIZATION))

    def test_every_wrapper_reader_and_probe_rechecks_retained_state_in_finally(self) -> None:
        with _synthetic_preauthorization() as (raw, _, paths):
            retained = paths["v5_attempt"]

            def corrupt(*_args, **_kwargs):
                retained.write_bytes(b"corrupt")
                raise RuntimeError("synthetic delegated failure")

            @contextmanager
            def corrupting_context(*_args, **_kwargs):
                retained.write_bytes(b"corrupt")
                raise RuntimeError("synthetic delegated failure")
                yield  # pragma: no cover

            runner_cases = (
                (
                    "configured_v4",
                    None,
                    lambda: successor._configured_v4(),
                    True,
                ),
                (
                    "configured_parent_bound",
                    "_INHERITED_CONFIGURED_PARENT",
                    lambda: successor._configured_parent_bound(launch_token="a" * 64),
                    True,
                ),
                (
                    "configured_parent",
                    "_INHERITED_CONFIGURED_PARENT",
                    lambda: successor.configured_parent(launch_token="a" * 64),
                    True,
                ),
                (
                    "strict_git_bound",
                    "_INHERITED_STRICT_GIT_METADATA",
                    lambda: successor._strict_git_metadata_bound(result_created=False),
                    False,
                ),
                (
                    "strict_git",
                    "_INHERITED_STRICT_GIT_METADATA",
                    lambda: successor.strict_git_metadata(result_created=False),
                    False,
                ),
                (
                    "source_probe",
                    "_INHERITED_SOURCE_SEAL_PROBE",
                    lambda: successor.source_seal_probe("a" * 64),
                    False,
                ),
                (
                    "dependency_hashes",
                    "_INHERITED_CURRENT_DEPENDENCY_HASHES",
                    successor._current_dependency_hashes,
                    False,
                ),
                (
                    "claim_attempt",
                    "_INHERITED_CLAIM_PUBLIC_ATTEMPT",
                    lambda: successor.claim_public_attempt(paths["v6_attempt"]),
                    False,
                ),
                (
                    "claim_launch",
                    "_INHERITED_CLAIM_CHILD_LAUNCH",
                    lambda: successor.claim_child_launch("a" * 64, "b" * 40),
                    False,
                ),
                (
                    "consume_launch",
                    "_INHERITED_CONSUME_CHILD_LAUNCH",
                    lambda: successor.consume_child_launch("a" * 64),
                    False,
                ),
                (
                    "abort_launch",
                    "_INHERITED_ABORT_CHILD_LAUNCH",
                    lambda: successor.abort_child_launch("a" * 64),
                    False,
                ),
                (
                    "finalize_launch",
                    "_INHERITED_FINALIZE_CHILD_LAUNCH",
                    lambda: successor.finalize_child_launch_after_owner("a" * 64),
                    False,
                ),
            )
            for name, attribute, invoke, is_context in runner_cases:
                with self.subTest(wrapper=name):
                    retained.write_bytes(V5_ATTEMPT_BYTES)
                    authorization_bytes = None
                    if name == "source_probe":
                        authorization_bytes = paths["v6_auth"].read_bytes()
                        paths["v6_auth"].unlink()
                    contexts = []
                    if attribute is not None:
                        replacement = corrupting_context if is_context else corrupt
                        contexts.append(
                            patch.object(successor, attribute, replacement)
                        )
                    try:
                        with ExitStack() as stack:
                            for item in contexts:
                                stack.enter_context(item)
                            with self.assertRaisesRegex(
                                ValueError, "retained v5 attempt bytes differ"
                            ):
                                if is_context:
                                    with invoke():
                                        if name == "configured_v4":
                                            retained.write_bytes(b"corrupt")
                                            raise RuntimeError(
                                                "synthetic delegated failure"
                                            )
                                else:
                                    invoke()
                    finally:
                        if authorization_bytes is not None:
                            paths["v6_auth"].write_bytes(authorization_bytes)

            retained.write_bytes(V5_ATTEMPT_BYTES)
            identity = successor._launch_claim_identity("a" * 64, "b" * 40)
            with (
                patch.object(successor._v4, "_launch_marker_bytes", side_effect=corrupt),
                self.assertRaisesRegex(ValueError, "retained v5 attempt bytes differ"),
            ):
                successor._launch_marker_bytes(identity, state="pending")

            reader_cases = (
                (
                    "assess_bytes",
                    "_INHERITED_ASSESS_BYTES",
                    lambda: reader.assess_calibration_bytes(raw),
                ),
                (
                    "validate_local",
                    "_INHERITED_VALIDATE_LOCAL_LIFECYCLE",
                    lambda: reader._validate_local_lifecycle(raw),
                ),
            )
            for name, attribute, invoke in reader_cases:
                with self.subTest(reader=name):
                    retained.write_bytes(V5_ATTEMPT_BYTES)
                    with (
                        patch.object(reader, attribute, side_effect=corrupt),
                        self.assertRaisesRegex(
                            ValueError, "retained v5 attempt bytes differ"
                        ),
                    ):
                        invoke()

            retained.write_bytes(V5_ATTEMPT_BYTES)
            paths["v6_result"].write_bytes(raw)
            with (
                patch.object(
                    reader,
                    "_INHERITED_VALIDATE_LOCAL_LIFECYCLE",
                    side_effect=corrupt,
                ),
                self.assertRaisesRegex(
                    ValueError, "retained v5 attempt bytes differ"
                ),
            ):
                reader.assess_calibration_file(paths["v6_result"])

    def test_real_lifecycle_transitions_use_only_temporary_paths(self) -> None:
        real_attempt = V5_ATTEMPT.read_bytes()
        token = "1" * 64
        commit = "2" * 40
        authorization = {"authorization_commit": commit}

        for requested in ("consumed", "aborted", "implicit_aborted"):
            with self.subTest(requested=requested), _isolated_lifecycle() as paths:
                successor.claim_public_attempt(paths["v6_attempt"])
                self.assertEqual(
                    paths["v6_attempt"].read_bytes(), successor._attempt_bytes()
                )
                with self.assertRaises(FileExistsError):
                    successor.claim_public_attempt(paths["v6_attempt"])

                with patch.object(
                    successor,
                    "_authorization_identity",
                    return_value=authorization,
                ):
                    identity = successor.claim_child_launch(token, commit)
                    self.assertEqual(
                        paths["v6_pending"].read_bytes(),
                        successor._launch_marker_bytes(identity, state="pending"),
                    )
                    if requested == "consumed":
                        transitioned = successor.consume_child_launch(token)
                        expected_state = "consumed"
                    elif requested == "aborted":
                        transitioned = successor.abort_child_launch(token)
                        expected_state = "aborted"
                    else:
                        transitioned = identity
                        expected_state = "aborted"
                    self.assertEqual(transitioned, identity)
                    self.assertEqual(
                        successor.finalize_child_launch_after_owner(token),
                        expected_state,
                    )

                terminal = paths[f"v6_{expected_state}"]
                self.assertFalse(os.path.lexists(paths["v6_pending"]))
                self.assertEqual(
                    terminal.read_bytes(),
                    successor._launch_marker_bytes(
                        identity, state=expected_state
                    ),
                )
                other = (
                    paths["v6_aborted"]
                    if expected_state == "consumed"
                    else paths["v6_consumed"]
                )
                self.assertFalse(os.path.lexists(other))

        self.assertEqual(V5_ATTEMPT.read_bytes(), real_attempt)
        for path in (
            successor.RESULT_PATH,
            successor.ATTEMPT_PATH,
            successor.LAUNCH_PENDING_PATH,
            successor.LAUNCH_CONSUMED_PATH,
            successor.LAUNCH_ABORTED_PATH,
            successor.AUTHORIZATION_CONFIG_PATH,
        ):
            self.assertFalse(os.path.lexists(path), path)

    def test_legacy_environment_names_reject_without_entering_owner(self) -> None:
        for name in successor._LEGACY_ENV_NAMES:
            with self.subTest(name=name), patch.dict(os.environ, {name: "poison"}):
                with self.assertRaisesRegex(ValueError, "legacy lifecycle names"):
                    successor._require_legacy_environment_absent()

    def test_runner_entry_guard_precedes_owner_without_invoking_main(self) -> None:
        attempt_before = V5_ATTEMPT.read_bytes()
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        main = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        first = main.body[0]
        self.assertIsInstance(first, ast.Expr)
        self.assertIsInstance(first.value, ast.Call)
        self.assertIsInstance(first.value.func, ast.Name)
        self.assertEqual(first.value.func.id, "_require_public_interpreter_state")

        successor._require_public_interpreter_state(
            argv=("runner",),
            dont_write_bytecode=True,
            safe_path=True,
        )
        for argv, dont_write_bytecode, safe_path in (
            (("runner", "extra"), True, True),
            (("runner",), False, True),
            (("runner",), True, False),
        ):
            with self.subTest(
                argv=argv,
                dont_write_bytecode=dont_write_bytecode,
                safe_path=safe_path,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "runner requires no arguments and Python -B -P",
                ):
                    successor._require_public_interpreter_state(
                        argv=argv,
                        dont_write_bytecode=dont_write_bytecode,
                        safe_path=safe_path,
                    )
        self.assertEqual(V5_ATTEMPT.read_bytes(), attempt_before)
        for path in (
            successor.RESULT_PATH,
            successor.ATTEMPT_PATH,
            successor.LAUNCH_PENDING_PATH,
            successor.LAUNCH_CONSUMED_PATH,
            successor.LAUNCH_ABORTED_PATH,
            successor.AUTHORIZATION_CONFIG_PATH,
        ):
            self.assertFalse(os.path.lexists(path), path)

    def test_launcher_unsafe_and_safe_source_imports_never_delegate(self) -> None:
        attempt_before = V5_ATTEMPT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            isolated = Path(directory)
            copied_launcher = isolated / "launcher.py"
            copied_launcher.write_bytes(LAUNCHER.read_bytes())
            poison_marker = isolated / "poison-fired"
            (isolated / "pathlib.py").write_text(
                "open('poison-fired', 'wb').write(b'fired')\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            for name in (
                "PYTHONPATH",
                "PYTHONSAFEPATH",
                successor._MODE_ENV,
                successor._CHALLENGE_ENV,
                successor._SPOOL_ENV,
                successor._LAUNCH_TOKEN_ENV,
                successor._PUBLIC_PYCACHE_ENV,
            ):
                environment.pop(name, None)
            poisoned = subprocess.run(
                [sys.executable, "-B", str(copied_launcher)],
                cwd=isolated,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
            self.assertNotEqual(poisoned.returncode, 0)
            self.assertEqual(
                poisoned.stderr.splitlines()[-1],
                "RuntimeError: v6 retained-attempt launcher requires Python -B -P",
            )
            self.assertFalse(poison_marker.exists())
            self.assertEqual(V5_ATTEMPT.read_bytes(), attempt_before)

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
        self.assertEqual(V5_ATTEMPT.read_bytes(), attempt_before)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "synthetic.pyd").write_bytes(b"shadow")
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
        self.assertEqual(V5_ATTEMPT.read_bytes(), attempt_before)


if __name__ == "__main__":
    unittest.main()
