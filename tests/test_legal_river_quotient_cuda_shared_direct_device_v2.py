from __future__ import annotations

import ast
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

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius import legal_river_quotient_cuda_shared_direct_device_result as v1_reader
from pontius import legal_river_quotient_cuda_shared_direct_device_v2_result as reader
from pontius import legal_river_quotient_cuda_shared_direct_device_v2_runner as runner
from tests import test_legal_river_quotient_cuda_shared_direct_device as v1_controls


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / runner.CONFIG_RELATIVE_PATH
_LAUNCHER = _ROOT / runner.LAUNCHER_RELATIVE_PATH
_RESULT = _ROOT / runner.RESULT_RELATIVE_PATH
_V1_RESULT = _ROOT / runner.V1_RESULT_RELATIVE_PATH
_RESERVED = _ROOT / runner.RESERVED_ACTUAL_RESULT_RELATIVE_PATH


def _semantic(payload: dict[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _independent_canonical_lf(path: Path) -> str:
    source = path.read_bytes()
    normalized = bytearray()
    index = 0
    while index < len(source):
        if (
            source[index] == 13
            and index + 1 < len(source)
            and source[index + 1] == 10
        ):
            normalized.append(10)
            index += 2
        else:
            normalized.append(source[index])
            index += 1
    return sha256(bytes(normalized)).hexdigest()


def _journal(
    payloads: list[tuple[JournalRecordKind, dict[str, object]]]
) -> bytes:
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


def _v2_journal(parent_raw: bytes) -> bytes:
    recovery = recover_journal_bytes(
        parent_raw,
        expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
        expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    header = payloads[0]
    header.update(
        {
            "schema_version": "legal-river-shared-direct-owner-header-v2",
            "config_sha256": reader.CONFIG_SHA256,
            "preregistration_commit": reader.PREREGISTRATION_COMMIT,
            "dependency_hashes": {
                relative: "6" * 64
                for relative in reader.DEPENDENCY_RELATIVE_PATHS
            },
            "result_relative_path": reader.RESULT_RELATIVE_PATH,
        }
    )
    for payload in payloads[1:-1]:
        payload["config_sha256"] = reader.CONFIG_SHA256
        if payload.get("kind") == "bootstrap_handshake":
            event = payload["event"]
            event["literal_module"] = reader.LITERAL_WORKER_MODULE
            event["spec_name"] = reader.LITERAL_WORKER_MODULE
    return _journal(
        [
            (record.body.kind, payload)
            for record, payload in zip(
                recovery.records, payloads, strict=True
            )
        ]
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
            for record, payload in zip(
                recovery.records, payloads, strict=True
            )
        ]
    )


class LauncherSafeSharedDirectV2Tests(unittest.TestCase):
    def test_corrected_config_and_all_result_absences(self) -> None:
        self.assertEqual(
            runner.canonical_lf_sha256(_CONFIG), runner.CONFIG_SHA256
        )
        runner.verify_preregistered_contract()
        reader.verify_preregistered_contract()
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_V1_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_root_launcher_is_stdlib_first_and_no_argument(self) -> None:
        source = _LAUNCHER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(imports, {"os", "runpy", "sys"})
        self.assertIn("Path(__file__).resolve().parent", source)
        self.assertIn('os.environ.pop("PYTHONPATH", None)', source)
        self.assertIn("runpy.run_module(_RUNNER_MODULE", source)
        self.assertIn("len(sys.argv) != 1", source)

    def test_runner_never_imports_or_invokes_consumed_v1_runner(self) -> None:
        path = _ROOT / (
            "src/pontius/"
            "legal_river_quotient_cuda_shared_direct_device_v2_runner.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn(
            "pontius.legal_river_quotient_cuda_shared_direct_device_runner",
            imported,
        )
        self.assertNotIn(
            "from .legal_river_quotient_cuda_shared_direct_device_runner",
            source,
        )
        self.assertIn("[sys.executable, \"-B\", str(_LAUNCHER)]", source)

    def test_reader_is_cupy_owner_and_adapter_free(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device_v2_result; "
            "print(int('cupy' in sys.modules)); "
            "print(int(any(name.endswith('_v2_runner') for name in sys.modules))); "
            "print(int('pontius.legal_river_quotient_cuda_shared_direct_device' "
            "in sys.modules))"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = f"{_ROOT / 'src'}{os.pathsep}{_ROOT}"
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=15.0,
        )
        self.assertEqual(completed.stdout.splitlines(), ["0", "0", "0"])

    def test_scrubbed_external_cwd_probe_crosses_both_launchers(self) -> None:
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment["PYTHONNOUSERSITE"] = "1"
        environment["PONTIUS_ADR0422_PUBLIC_LAUNCHER_PROBE"] = "1"
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-B", str(_LAUNCHER)],
                cwd=directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
                timeout=15.0,
            )
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        probe = json.loads(completed.stdout)
        self.assertEqual(
            canonical_journal_json_bytes(probe) + b"\n",
            completed.stdout.encode("utf-8"),
        )
        self.assertEqual(probe["parent"], {
            key: value
            for key, value in probe["child"].items()
            if key not in {"schema_version", "challenge_sha256"}
        })
        self.assertFalse(probe["pythonpath_present"])
        self.assertFalse(probe["pythonhome_present"])
        self.assertFalse(probe["parent"]["cupy_imported"])
        self.assertFalse(probe["parent"]["science_adapter_imported"])
        self.assertEqual(
            probe["child_command"],
            [sys.executable, "-B", str(_LAUNCHER.resolve())],
        )
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_V1_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_real_root_launched_bootstrap_handshake_is_v1_shaped(self) -> None:
        event = runner.run_no_cuda_bootstrap_handshake()
        self.assertEqual(
            set(event),
            {
                "schema_version",
                "challenge_sha256",
                "literal_module",
                "spec_name",
                "runtime_name",
                "cupy_imported",
            },
        )
        self.assertEqual(event["literal_module"], runner.LITERAL_WORKER_MODULE)
        self.assertEqual(event["runtime_name"], "__main__")
        self.assertFalse(event["cupy_imported"])

    def test_dependency_inventories_are_identical_and_parent_complete(self) -> None:
        self.assertEqual(
            runner.DEPENDENCY_RELATIVE_PATHS,
            reader.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertTrue(
            set(v1_reader.DEPENDENCY_RELATIVE_PATHS)
            <= set(reader.DEPENDENCY_RELATIVE_PATHS)
        )
        self.assertIn(
            "docs/decisions/"
            "ADR-0423-correct-the-v2-reader-lifecycle-transduction-before-source.md",
            reader.DEPENDENCY_RELATIVE_PATHS,
        )

    def test_parent_hashes_rebind_exactly_from_the_corrected_config(self) -> None:
        runner.verify_preregistered_contract()
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        retained = config["retained_parent_contract"]
        for prefix in (
            "v1_config",
            "v1_source_seal_adr",
            "v1_failure_adr",
            "v1_adapter",
            "v1_runner",
            "v1_reader",
            "v1_controls",
        ):
            path = _ROOT / retained[f"{prefix}_relative_path"]
            digest = sha256(
                path.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            self.assertEqual(
                digest, retained[f"{prefix}_canonical_lf_sha256"]
            )

    def test_canonical_lf_helper_matches_independent_byte_loop(self) -> None:
        paths = {
            _CONFIG,
            _LAUNCHER,
            _ROOT
            / "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_runner.py",
            _ROOT
            / "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_result.py",
            Path(__file__),
        }
        paths.update(
            _ROOT / relative
            for relative in reader.DEPENDENCY_RELATIVE_PATHS
            if not relative.startswith("artifacts/")
        )
        for path in paths:
            self.assertEqual(
                runner.canonical_lf_sha256(path),
                _independent_canonical_lf(path),
                str(path),
            )

    def test_literal_escape_text_rewrite_reproduces_only_false_receipts(self) -> None:
        literal_token = bytes((92, 114, 92, 110))
        wrong_replacement = bytes((92, 110))
        expected = {
            "src/pontius/legal_river_quotient_cuda_shared_direct_device.py": (
                2,
                "a064c9485c3cc9f9a9e7dbbe03719070ae93c9672cc23895d22ff8638283c25b",
            ),
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_runner.py": (
                2,
                "dcf5f0166adcadf23123ace98dedf2bbf799abcd521ec585d5f143bdc2e7f3db",
            ),
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py": (
                3,
                "ce7f820ade6472990df88634fe2d2c9215b5ef97a255ab9caafa07edfc8912b9",
            ),
        }
        for relative, (count, false_digest) in expected.items():
            raw = (_ROOT / relative).read_bytes()
            self.assertEqual(raw.count(literal_token), count)
            self.assertEqual(
                sha256(
                    raw.replace(literal_token, wrong_replacement)
                ).hexdigest(),
                false_digest,
            )
            self.assertNotEqual(
                false_digest,
                _independent_canonical_lf(_ROOT / relative),
            )

    def test_minimal_infrastructure_journal_transduces(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "infrastructure_failure")
        self.assertFalse(rebound.passed)
        self.assertEqual(rebound.event_count, 1)
        self.assertEqual(rebound.populations, ())

    def test_lifecycle_allowlist_is_literal_and_complete(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(
            rebound.lifecycle_allowlist,
            (
                "journal.protocol_sha256",
                "journal.campaign_sha256",
                "header.schema_version",
                "header.config_sha256",
                "header.preregistration_commit",
                "header.dependency_hashes",
                "header.result_relative_path",
                "observations[*].config_sha256",
                "bootstrap.literal_module",
                "bootstrap.spec_name",
            ),
        )

    def test_current_dependency_closure_rebinds_without_results(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())

        def bind_current(payloads) -> None:
            payloads[0]["dependency_hashes"] = runner.dependency_hashes()

        rebound = reader.rebind_shared_direct_device_v2_journal(
            _rewrite(raw, bind_current), rebind_current_sources=True
        )
        self.assertEqual(rebound.terminal, "infrastructure_failure")
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_V1_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_complete_synthetic_science_transduces_without_payload_edits(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())
        rebound = reader.rebind_shared_direct_device_v2_journal(
            raw, rebind_current_sources=False
        )
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.populations, (10, 22))
        self.assertEqual(rebound.phase_count, 64)
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        self.assertIsNone(recovery.failure)
        translated = reader._translated_journal(recovery.records)
        parent = recover_journal_bytes(
            translated,
            expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
            expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
        )
        self.assertIsNone(parent.failure)
        for v2_record, v1_record in zip(
            recovery.records[2:-1], parent.records[2:-1], strict=True
        ):
            self.assertEqual(
                v2_record.body.payload["event"],
                v1_record.body.payload["event"],
            )
        self.assertEqual(
            recovery.records[-1].body.payload,
            parent.records[-1].body.payload,
        )

    def test_bootstrap_projection_changes_exactly_two_event_fields(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        translated = recover_journal_bytes(
            reader._translated_journal(recovery.records),
            expected_protocol_sha256=v1_reader.PROTOCOL_SHA256,
            expected_campaign_sha256=v1_reader.CAMPAIGN_SHA256,
        )
        before = recovery.records[1].body.payload["event"]
        after = translated.records[1].body.payload["event"]
        changed = {key for key in before if before[key] != after[key]}
        self.assertEqual(changed, {"literal_module", "spec_name"})

    def test_duplicate_bootstrap_is_rejected_before_parent_projection(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        recovery = recover_journal_bytes(
            raw,
            expected_protocol_sha256=reader.PROTOCOL_SHA256,
            expected_campaign_sha256=reader.CAMPAIGN_SHA256,
        )
        payloads = [
            deepcopy(record.body.payload) for record in recovery.records
        ]
        payloads.insert(2, deepcopy(payloads[1]))
        kinds = [
            JournalRecordKind.HEADER,
            JournalRecordKind.OBSERVATION,
            JournalRecordKind.OBSERVATION,
            JournalRecordKind.TERMINAL,
        ]
        duplicated = _journal(list(zip(kinds, payloads, strict=True)))
        with self.assertRaises(ValueError):
            reader.rebind_shared_direct_device_v2_journal(
                duplicated, rebind_current_sources=False
            )

    def test_lifecycle_mutations_fail_closed(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())

        def corrupt_bootstrap(payloads, field, value) -> None:
            event = payloads[1]["event"]
            event[field] = value

        for field, value in (
            ("challenge_sha256", "0"),
            ("runtime_name", "pontius"),
            ("cupy_imported", True),
            ("literal_module", "pontius.wrong"),
        ):
            broken = _rewrite(
                raw,
                lambda payloads, field=field, value=value: corrupt_bootstrap(
                    payloads, field, value
                ),
            )
            with self.assertRaises(ValueError):
                reader.rebind_shared_direct_device_v2_journal(
                    broken, rebind_current_sources=False
                )

    def test_post_bootstrap_and_outer_mutations_fail_closed(self) -> None:
        raw = _v2_journal(v1_controls._complete_synthetic_journal())

        def corrupt_runtime(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "runtime"
            )
            event["built_cuda_source_sha256"] = "0" * 64

        def corrupt_phase(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "phase"
            )
            event["host_ns"] += 1

        def corrupt_population(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "population"
            )
            event["gates"]["chip_units"] = False

        def corrupt_outer(payloads) -> None:
            payloads[-1]["capacity_projection"] = [1, 1]

        for mutation in (
            corrupt_runtime,
            corrupt_phase,
            corrupt_population,
            corrupt_outer,
        ):
            with self.assertRaises(ValueError):
                reader.rebind_shared_direct_device_v2_journal(
                    _rewrite(raw, mutation), rebind_current_sources=False
                )

    def test_reader_never_reads_absent_v1_result(self) -> None:
        raw = _v2_journal(v1_controls._minimal_infrastructure_journal())
        original = Path.read_bytes
        opened: list[Path] = []

        def recording(path: Path) -> bytes:
            opened.append(path)
            return original(path)

        with patch.object(Path, "read_bytes", recording):
            reader.rebind_shared_direct_device_v2_journal(
                raw, rebind_current_sources=False
            )
        self.assertNotIn(_V1_RESULT, opened)

    def test_public_launcher_rejects_arguments_without_results(self) -> None:
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-B", str(_LAUNCHER), "forbidden"],
            cwd=_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=15.0,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("accepts no arguments", completed.stderr)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_V1_RESULT.exists())
        self.assertFalse(_RESERVED.exists())


if __name__ == "__main__":
    unittest.main()
