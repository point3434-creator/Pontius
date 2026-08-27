from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v4_runner as v4_runner,
)
from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v5_result as reader,
)
from pontius import (
    legal_river_quotient_compiled_global_separation_calibration_v5_runner as successor,
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
CONFIG = ROOT / successor.HEADER_CONTRACT_CONFIG_RELATIVE_PATH
AUTHORIZATION = ROOT / successor.AUTHORIZATION_CONFIG_RELATIVE_PATH
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration_v5.py"
CONSUMED_ATTEMPT_BYTES = 606
CONSUMED_ATTEMPT_SHA256 = (
    "104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d"
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
            "reason": "synthetic v5 preauthorization control",
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
        path = Path(directory) / "synthetic-v5.jsonl"
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
    for record in checked.records:
        expected = sha256(
            canonical_journal_json_bytes(dict(record.body.payload))
        ).hexdigest()
        if record.body.semantic_identity_sha256 != expected:
            raise AssertionError("mutation retained a stale semantic identity")
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


def _alias_paths(value: object, path: tuple[str, ...] = ()):
    if type(value) is dict:
        for key, child in value.items():
            yield from _alias_paths(child, (*path, key))
    elif type(value) is list:
        for index, child in enumerate(value):
            yield from _alias_paths(child, (*path, index))
    elif type(value) is bool or (type(value) is int and value in {0, 1}):
        yield path


@contextmanager
def _synthetic_preauthorization():
    source_seal = "a" * 40
    authorization_commit = "b" * 40
    with tempfile.TemporaryDirectory() as directory:
        auth_path = Path(directory) / "authorization.json"
        auth_config = {
            "schema_version": successor.AUTHORIZATION_SCHEMA_VERSION,
            "source_seal_commit": source_seal,
            "authorization_commit_paths": list(successor.AUTHORIZATION_COMMIT_PATHS),
        }
        auth_path.write_text(
            json.dumps(auth_config, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        config_hash = sha256(
            auth_path.read_bytes().replace(b"\r\n", b"\n")
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
                    reason="synthetic v5 preauthorization control",
                    event_count=2,
                    public_elapsed_ns=20,
                    laboratory_elapsed_ns=7,
                )
        raw = _journal_bytes(header, owner_terminal)
        with (
            patch.object(reader, "AUTHORIZATION_CONFIG_PATH", auth_path),
            patch.object(reader._v4, "_validate_authorization_git", return_value=None),
            patch.object(reader._v4, "_absolute_git", return_value=auth_path.read_bytes()),
        ):
            yield raw, header, auth_path


class CompiledGlobalSeparationCalibrationV5Tests(unittest.TestCase):
    def setUp(self) -> None:
        for path in (
            successor.V4_RESULT_PATH,
            successor.V4_ATTEMPT_PATH,
            successor.V4_LAUNCH_PENDING_PATH,
            successor.V4_LAUNCH_CONSUMED_PATH,
            successor.V4_LAUNCH_ABORTED_PATH,
            successor.RESULT_PATH,
            successor.LAUNCH_PENDING_PATH,
            successor.LAUNCH_CONSUMED_PATH,
            successor.LAUNCH_ABORTED_PATH,
        ):
            self.assertFalse(os.path.lexists(path), path)
        self.assertTrue(successor.ATTEMPT_PATH.is_file())
        attempt = successor.ATTEMPT_PATH.read_bytes()
        self.assertEqual(len(attempt), CONSUMED_ATTEMPT_BYTES)
        self.assertEqual(sha256(attempt).hexdigest(), CONSUMED_ATTEMPT_SHA256)
        self.assertEqual(attempt, successor._attempt_bytes())

    def test_config_and_all_public_identities_are_fresh(self) -> None:
        self.assertEqual(
            sha256(CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            successor.HEADER_CONTRACT_CONFIG_SHA256,
        )
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(config["fresh_successor"]["v4_permanently_closed_uninvoked"])
        self.assertEqual(
            successor.DEPENDENCY_RELATIVE_PATHS, reader.DEPENDENCY_RELATIVE_PATHS
        )
        self.assertNotIn(
            successor.AUTHORIZATION_CONFIG_RELATIVE_PATH,
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertNotIn(
            "docs/decisions/ADR-0471-authorize-one-corrected-deferred-import-"
            "calibration-invocation.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertNotEqual(successor.PROTOCOL_SHA256, v4_runner.PROTOCOL_SHA256)
        self.assertNotEqual(successor.CAMPAIGN_SHA256, v4_runner.CAMPAIGN_SHA256)
        self.assertNotEqual(successor.RESULT_RELATIVE_PATH, v4_runner.RESULT_RELATIVE_PATH)
        self.assertNotEqual(successor.ATTEMPT_RELATIVE_PATH, v4_runner.ATTEMPT_RELATIVE_PATH)
        self.assertNotEqual(successor._MODE_ENV, v4_runner._MODE_ENV)
        self.assertNotEqual(successor._CHALLENGE_ENV, v4_runner._CHALLENGE_ENV)
        self.assertNotEqual(successor._SPOOL_ENV, v4_runner._SPOOL_ENV)
        self.assertNotEqual(successor._LAUNCH_TOKEN_ENV, v4_runner._LAUNCH_TOKEN_ENV)
        self.assertNotEqual(successor._SOURCE_PROBE, v4_runner._SOURCE_PROBE)
        self.assertNotEqual(successor._CAMPAIGN_CHILD, v4_runner._CAMPAIGN_CHILD)
        self.assertNotEqual(successor._EVENT_PREFIX, v4_runner._EVENT_PREFIX)
        self.assertNotEqual(successor._ACK_PREFIX, v4_runner._ACK_PREFIX)
        self.assertNotEqual(
            successor._PUBLIC_PYCACHE_ENV, v4_runner._PUBLIC_PYCACHE_ENV
        )
        self.assertEqual(
            successor.AUTHORIZATION_SCHEMA_VERSION,
            "pontius-adr0471-one-commit-authorization-v1",
        )
        self.assertEqual(
            successor.ATTEMPT_SCHEMA_VERSION,
            "pontius-adr0469-public-attempt-v5-v1",
        )
        self.assertEqual(
            successor.LAUNCH_SCHEMA_VERSION,
            "pontius-adr0470-one-use-child-launch-v5-v1",
        )
        self.assertEqual(successor.SCIENTIFIC_MODULE, v4_runner.SCIENTIFIC_MODULE)
        self.assertNotIn(successor.SCIENTIFIC_MODULE, sys.modules)
        self.assertFalse(any(name == "cupy" or name.startswith("cupy.") for name in sys.modules))

    def test_writer_and_reader_bindings_restore_after_success_and_failure(self) -> None:
        writer_replacements = successor._v5_replacements()
        self.assertEqual(set(successor._V4_BINDINGS), set(writer_replacements))
        writer_before = {name: getattr(successor._v4, name) for name in successor._V4_BINDINGS}
        with successor._configured_v4() as engine:
            for name, value in writer_replacements.items():
                self.assertIs(getattr(engine, name), value)
        for name, value in writer_before.items():
            self.assertIs(getattr(successor._v4, name), value)
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with successor._configured_v4():
                raise RuntimeError("synthetic")
        for name, value in writer_before.items():
            self.assertIs(getattr(successor._v4, name), value)

        reader_replacements = reader._replacements()
        self.assertEqual(set(reader._V4_BINDINGS), set(reader_replacements))
        reader_before = {name: getattr(reader._v4, name) for name in reader._V4_BINDINGS}
        with reader._configured_v4_reader() as inherited:
            for name, value in reader_replacements.items():
                self.assertIs(getattr(inherited, name), value)
        for name, value in reader_before.items():
            self.assertIs(getattr(reader._v4, name), value)
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with reader._configured_v4_reader():
                raise RuntimeError("synthetic")
        for name, value in reader_before.items():
            self.assertIs(getattr(reader._v4, name), value)

    def test_closed_v4_lifecycle_rejects_before_and_after_delegation(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            with tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / "closed-v4-result.jsonl"
                with patch.object(reader, "V4_RESULT_PATH", marker):
                    marker.write_bytes(b"present-before-reader")
                    with self.assertRaisesRegex(FileExistsError, "closed v4 lifecycle"):
                        reader.assess_calibration_bytes(raw)
                    marker.unlink()

                    def inherited_assessment(_raw):
                        marker.write_bytes(b"appeared-during-reader")
                        return object()

                    with patch.object(
                        reader,
                        "_INHERITED_ASSESS_BYTES",
                        side_effect=inherited_assessment,
                    ):
                        with self.assertRaisesRegex(
                            FileExistsError, "closed v4 lifecycle"
                        ):
                            reader.assess_calibration_bytes(raw)
                    self.assertTrue(marker.is_file())
                    marker.unlink()

                    def failing_inherited_assessment(_raw):
                        marker.write_bytes(b"appeared-before-reader-exception")
                        raise RuntimeError("synthetic inherited failure")

                    with patch.object(
                        reader,
                        "_INHERITED_ASSESS_BYTES",
                        side_effect=failing_inherited_assessment,
                    ):
                        with self.assertRaisesRegex(
                            FileExistsError, "closed v4 lifecycle"
                        ):
                            reader.assess_calibration_bytes(raw)
                    self.assertTrue(marker.is_file())
                    marker.unlink()

                with patch.object(successor, "V4_RESULT_PATH", marker):
                    with self.assertRaisesRegex(FileExistsError, "closed v4 lifecycle"):
                        with successor.configured_parent(launch_token="f" * 64):
                            marker.write_bytes(b"appeared-during-writer")
                    self.assertTrue(marker.is_file())
                    marker.unlink()

                wrapper_cases = (
                    (
                        "_INHERITED_CLAIM_PUBLIC_ATTEMPT",
                        lambda: successor.claim_public_attempt(
                            Path(directory) / "synthetic-v5-attempt.json"
                        ),
                    ),
                    (
                        "_INHERITED_CLAIM_CHILD_LAUNCH",
                        lambda: successor.claim_child_launch("a" * 64, "b" * 40),
                    ),
                    (
                        "_INHERITED_CONSUME_CHILD_LAUNCH",
                        lambda: successor.consume_child_launch("a" * 64),
                    ),
                    (
                        "_INHERITED_ABORT_CHILD_LAUNCH",
                        lambda: successor.abort_child_launch("a" * 64),
                    ),
                    (
                        "_INHERITED_FINALIZE_CHILD_LAUNCH",
                        lambda: successor.finalize_child_launch_after_owner("a" * 64),
                    ),
                    (
                        "_strict_git_metadata_bound",
                        lambda: successor.strict_git_metadata(result_created=False),
                    ),
                    (
                        "_INHERITED_STRICT_GIT_METADATA",
                        lambda: successor._strict_git_metadata_bound(
                            result_created=False
                        ),
                    ),
                    (
                        "_INHERITED_SOURCE_SEAL_PROBE",
                        lambda: successor.source_seal_probe("d" * 64),
                    ),
                )
                for attribute, invoke in wrapper_cases:
                    with self.subTest(attribute=attribute):
                        def fail_after_v4_path(*_args, **_kwargs):
                            marker.write_bytes(b"appeared-before-wrapper-exception")
                            raise RuntimeError("synthetic delegated failure")

                        with (
                            patch.object(successor, "V4_RESULT_PATH", marker),
                            patch.object(
                                successor,
                                attribute,
                                side_effect=fail_after_v4_path,
                            ),
                            self.assertRaisesRegex(
                                FileExistsError, "closed v4 lifecycle"
                            ),
                        ):
                            invoke()
                        self.assertTrue(marker.is_file())
                        marker.unlink()

    def test_legacy_environment_names_reject_before_owner(self) -> None:
        for name in successor._LEGACY_ENV_NAMES:
            with self.subTest(name=name), patch.dict(os.environ, {name: "poison"}):
                with self.assertRaisesRegex(ValueError, "legacy lifecycle names"):
                    successor._require_legacy_environment_absent()

    def test_preauthorization_actual_layered_header_round_trip(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            self.assertEqual(len(header), 15)
            self.assertIn("absolute_git_recovery", header)
            reader._validate_deferred_header(raw)
            assessed = reader.assess_calibration_bytes(raw)
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "deferred_science_import_rejected")

    def test_absolute_git_domains_and_every_leaf_reject_when_mutated(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            mapping_paths = (
                (),
                ("absolute_git_recovery",),
                ("absolute_git_recovery", "absolute_git"),
                ("absolute_git_recovery", "predecessor"),
            )
            for path in mapping_paths:
                target = header if not path else _at(header, path)
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

    def test_every_additive_header_layer_has_an_exact_mapping_domain(self) -> None:
        with _synthetic_preauthorization() as (raw, header, _):
            mapping_paths = (
                ("launch_abi_recovery",),
                ("launch_abi_recovery", "predecessor"),
                ("launch_abi_recovery", "rejected_v3"),
                ("launch_abi_recovery", "executed_science_identity"),
                ("launch_abi_recovery", "launch_arity_contract"),
                ("deferred_science_import_authorization",),
                ("source_seal_git",),
                ("source_seal_git", "authorization"),
                ("source_seal_git", "launch_claim"),
            )
            for path in mapping_paths:
                target = _at(header, path)
                self.assertIs(type(target), dict)
                for key in tuple(target):
                    with self.subTest(operation="missing", path=path, key=key):
                        def mutate(payload, path=path, key=key):
                            del _at(payload, path)[key]
                        with self.assertRaises((TypeError, ValueError)):
                            reader._validate_deferred_header(_rechain(raw, 0, mutate))
                with self.subTest(operation="extra", path=path):
                    def mutate(payload, path=path):
                        _at(payload, path)["unexpected"] = "field"
                    with self.assertRaises((TypeError, ValueError)):
                        reader._validate_deferred_header(_rechain(raw, 0, mutate))

            absolute = header["absolute_git_recovery"]
            leaf_paths = tuple(
                path
                for path in (
                    ("schema_version",),
                    ("config_relative_path",),
                    ("config_canonical_lf_sha256",),
                    ("absolute_git", "path"),
                    ("absolute_git", "bytes"),
                    ("absolute_git", "sha256"),
                    ("absolute_git", "provenance"),
                    ("predecessor", "source_seal_commit"),
                    ("predecessor", "result_relative_path"),
                    ("predecessor", "result_exists"),
                    ("predecessor", "terminal"),
                    ("predecessor", "exception_type"),
                    ("predecessor", "exception_message"),
                    ("predecessor", "invocation_count"),
                    ("scientific_source_canonical_lf_sha256",),
                    ("literal_cuda_source_sha256",),
                )
            )
            for path in leaf_paths:
                original = _at(absolute, path)
                if type(original) is bool:
                    replacement = int(original)
                elif type(original) is int:
                    replacement = bool(original) if original in {0, 1} else original + 1
                else:
                    replacement = "mutated:" + original
                with self.subTest(path=path):
                    def mutate(payload, path=path, replacement=replacement):
                        _replace(
                            payload,
                            ("absolute_git_recovery", *path),
                            replacement,
                        )
                    with self.assertRaises((TypeError, ValueError)):
                        reader._validate_deferred_header(_rechain(raw, 0, mutate))

    def test_every_equality_preserving_bool_int_alias_rejects(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=successor.PROTOCOL_SHA256,
                expected_campaign_sha256=successor.CAMPAIGN_SHA256,
            )
            paths = []
            for index, record in enumerate(recovery.records):
                paths.extend((index, path) for path in _alias_paths(record.body.payload))
            self.assertEqual(len(paths), 38)
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

    def test_started_science_identity_bool_int_alias_rejects(self) -> None:
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

            def mutate(payload):
                path = (
                    "event",
                    "executed_science_identity",
                    "central_pre_driver_guard",
                )
                self.assertIs(_at(payload, path), True)
                _replace(payload, path, 1)

            with self.assertRaises((TypeError, ValueError)):
                reader.assess_calibration_bytes(_rechain(started, 2, mutate))

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
                "fit_rows": [
                    {"target_upper_ceiling_ns": 1, "target_work": 0}
                ],
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
                self.assertEqual(original, replacement)
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

    def test_imported_but_unvalidated_science_rejection_remains_truthful(self) -> None:
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

    def test_config_identities_cannot_cross_layers(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            crossings = (
                (
                    ("absolute_git_recovery", "config_relative_path"),
                    reader.DEFERRED_IMPORT_CONFIG_RELATIVE_PATH,
                ),
                (
                    ("absolute_git_recovery", "config_canonical_lf_sha256"),
                    reader.DEFERRED_IMPORT_CONFIG_SHA256,
                ),
                (
                    ("launch_abi_recovery", "config_relative_path"),
                    reader.ABSOLUTE_GIT_RECOVERY_CONFIG_RELATIVE_PATH,
                ),
                (
                    ("launch_abi_recovery", "config_canonical_lf_sha256"),
                    reader.ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256,
                ),
            )
            for path, replacement in crossings:
                with self.subTest(path=path):
                    def mutate(payload, path=path, replacement=replacement):
                        _replace(payload, path, replacement)
                    with self.assertRaises((TypeError, ValueError)):
                        reader._validate_deferred_header(_rechain(raw, 0, mutate))

    def test_direct_header_validation_binds_v5_git_authority(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            before = {
                "AUTHORIZATION_COMMIT_PATHS": reader._v4.AUTHORIZATION_COMMIT_PATHS,
                "DEPENDENCY_RELATIVE_PATHS": reader._v4.DEPENDENCY_RELATIVE_PATHS,
            }
            observed = []

            def validate(*_args):
                observed.append(
                    (
                        reader._v4.AUTHORIZATION_COMMIT_PATHS,
                        reader._v4.DEPENDENCY_RELATIVE_PATHS,
                    )
                )

            with patch.object(
                reader._v4, "_validate_authorization_git", side_effect=validate
            ):
                reader._validate_deferred_header(raw)
            self.assertEqual(
                observed,
                [(reader.AUTHORIZATION_COMMIT_PATHS, reader.DEPENDENCY_RELATIVE_PATHS)],
            )
            for name, value in before.items():
                self.assertIs(getattr(reader._v4, name), value)

            def reject(*_args):
                self.assertEqual(
                    reader._v4.AUTHORIZATION_COMMIT_PATHS,
                    reader.AUTHORIZATION_COMMIT_PATHS,
                )
                raise RuntimeError("synthetic Git validation failure")

            with patch.object(
                reader._v4, "_validate_authorization_git", side_effect=reject
            ):
                with self.assertRaisesRegex(RuntimeError, "synthetic Git"):
                    reader._validate_deferred_header(raw)
            for name, value in before.items():
                self.assertIs(getattr(reader._v4, name), value)

    def test_present_absolute_git_predecessor_rejects(self) -> None:
        with _synthetic_preauthorization() as (raw, _, _):
            with tempfile.TemporaryDirectory() as directory:
                present = Path(directory) / "predecessor.jsonl"
                present.write_bytes(b"present")
                with (
                    patch.object(reader, "ABSOLUTE_GIT_PREDECESSOR_RESULT_PATH", present),
                    self.assertRaisesRegex(ValueError, "predecessor result unexpectedly exists"),
                ):
                    reader._validate_deferred_header(raw)

    def test_authorization_config_parser_is_type_exact(self) -> None:
        base = {
            "schema_version": reader.AUTHORIZATION_SCHEMA_VERSION,
            "source_seal_commit": "a" * 40,
            "authorization_commit_paths": list(reader.AUTHORIZATION_COMMIT_PATHS),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auth.json"
            def assess(value):
                path.write_text(json.dumps(value), encoding="utf-8")
                with patch.object(reader, "AUTHORIZATION_CONFIG_PATH", path):
                    return reader._authorization_config()
            loaded, _ = assess(base)
            self.assertEqual(loaded, base)
            for mutation in (
                {**base, "schema_version": "wrong"},
                {**base, "source_seal_commit": True},
                {
                    **base,
                    "authorization_commit_paths": list(
                        reversed(base["authorization_commit_paths"])
                    ),
                },
                {**base, "extra": False},
            ):
                with self.subTest(mutation=mutation), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    assess(mutation)

    def test_root_launcher_is_source_only_and_extension_closed(self) -> None:
        attempt_before = successor.ATTEMPT_PATH.read_bytes()
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
            self.assertIn("Python -B -P", poisoned.stderr)
            self.assertFalse(poison_marker.exists())
            self.assertEqual(
                successor.ATTEMPT_PATH.read_bytes(), attempt_before
            )

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
        self.assertEqual(successor.ATTEMPT_PATH.read_bytes(), attempt_before)
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

    def test_consumed_v5_source_probe_fails_before_science(self) -> None:
        before_modules = set(sys.modules)
        with self.assertRaisesRegex(FileExistsError, "source-probe lifecycle"):
            successor.source_seal_probe("d" * 64)
        added = set(sys.modules) - before_modules
        self.assertNotIn(successor.SCIENTIFIC_MODULE, added)
        self.assertFalse(
            any(name == "cupy" or name.startswith("cupy.") for name in added)
        )
        self.assertEqual(
            successor.ATTEMPT_PATH.read_bytes(), successor._attempt_bytes()
        )

    def test_v5_authorization_remains_absent_after_consumed_attempt(self) -> None:
        self.assertFalse(os.path.lexists(AUTHORIZATION))
        with self.assertRaises(FileNotFoundError):
            successor._authorization_identity()


if __name__ == "__main__":
    unittest.main()
