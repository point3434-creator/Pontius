from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius import legal_river_quotient_cuda_compensated_tiles as paired
from pontius import legal_river_quotient_cuda_compensated_work_preflight as v4
from pontius import legal_river_quotient_cuda_shared_direct_device as parent
from pontius import legal_river_quotient_cuda_shared_direct_device_v2_result as v2_reader
from pontius import legal_river_quotient_cuda_shared_direct_device_v3_result as reader
from pontius import legal_river_quotient_cuda_shared_direct_sample_plan as sample_plan
from tests import test_legal_river_quotient_cuda_shared_direct_device_v2 as v2_controls


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / sample_plan.CONFIG_RELATIVE_PATH
_V2_RESULT = _ROOT / reader.V2_RESULT_RELATIVE_PATH


def _semantic(payload) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _journal(records) -> bytes:
    previous = None
    lines: list[bytes] = []
    for sequence, (kind, payload) in enumerate(records):
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


def _v3_journal(parent_raw: bytes) -> bytes:
    recovery = recover_journal_bytes(
        parent_raw,
        expected_protocol_sha256=v2_reader.PROTOCOL_SHA256,
        expected_campaign_sha256=v2_reader.CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise AssertionError(recovery.failure.reason)
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    header = payloads[0]
    header.update(
        {
            "schema_version": "legal-river-shared-direct-owner-header-v3",
            "config_sha256": reader.CONFIG_SHA256,
            "preregistration_commit": reader.PREREGISTRATION_COMMIT,
            "dependency_hashes": {
                relative: "7" * 64
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


def _shape_execution(cards: int, rows: int) -> SimpleNamespace:
    boundary = len(v4.BOUNDARY_FEATURES)
    return SimpleNamespace(
        available_cards=cards,
        source_samples=SimpleNamespace(shape=(rows, boundary, 2)),
        query_samples=SimpleNamespace(shape=(rows, boundary, 2)),
        fold_samples=SimpleNamespace(shape=(rows, 2, 2)),
        adjoint_samples=SimpleNamespace(shape=(rows, boundary, 2)),
        direct_query_samples=SimpleNamespace(shape=(rows, boundary, 2)),
        direct_fold_samples=SimpleNamespace(shape=(rows, 2, 2)),
        direct_adjoint_samples=SimpleNamespace(shape=(rows, boundary, 2)),
    )


class SharedSamplePlanV3Tests(unittest.TestCase):

    def test_literal_plans_are_frozen_read_only_and_exact(self) -> None:
        self.assertIsInstance(
            sample_plan.CALIBRATION_SAMPLE_PLANS, MappingProxyType
        )
        for cards in (10, 22):
            plan = sample_plan.CALIBRATION_SAMPLE_PLANS[cards]
            self.assertIs(
                sample_plan.SAMPLE_PLAN_RESOLVER.plan(cards), plan
            )
            self.assertEqual(
                (plan.source_ranks, plan.query_records),
                v4.sample_rows(cards),
            )
            self.assertEqual(
                plan.boundary_features, tuple(v4.BOUNDARY_FEATURES)
            )
            with self.assertRaises(FrozenInstanceError):
                plan.available_cards = 25  # type: ignore[misc]

    def test_generated_execution_and_evidence_share_one_resolver(self) -> None:
        report = sample_plan.generated_binding_report()
        self.assertTrue(report["all_gates_pass"])
        generated = sample_plan.build_generated_population_runner(object())
        execution = generated.__globals__["_sample_rows"]
        evidence = sample_plan._PLAN_ERROR_EVIDENCE.__globals__["sample_rows"]
        self.assertIs(execution, sample_plan.SAMPLE_PLAN_RESOLVER)
        self.assertIs(evidence, sample_plan.SAMPLE_PLAN_RESOLVER)
        self.assertIs(execution, evidence)
        self.assertIsNot(execution, paired._sample_rows)
        self.assertIs(
            sample_plan._POPULATION_EVIDENCE.__globals__[
                "_plan_error_evidence"
            ],
            sample_plan._plan_error_evidence,
        )
        self.assertIs(
            sample_plan._RUN_SHARED_FAMILY.__globals__[
                "build_generated_population_runner"
            ],
            sample_plan.build_generated_population_runner,
        )
        self.assertIs(
            sample_plan._VALIDATION.__globals__["run_shared_family"],
            sample_plan.run_shared_family,
        )
        self.assertIs(
            sample_plan._VALIDATION.__globals__["_population_evidence"],
            sample_plan._population_evidence,
        )


    def test_historical_seven_row_helper_rejects_before_cupy(self) -> None:
        self.assertEqual(tuple(map(len, paired._sample_rows(10))), (7, 7))
        before = parent._CUPY_IMPORT_CALLS
        execution = _shape_execution(10, 7)
        with self.assertRaisesRegex(
            ValueError,
            r"default\.source shape differs: "
            r"actual=\(7, 8, 2\) expected=\(16, 8, 2\)",
        ):
            sample_plan._plan_error_evidence(
                10, execution, execution, object()
            )
        self.assertEqual(parent._CUPY_IMPORT_CALLS, before)
        self.assertNotIn("cupy", sys.modules)

    def test_rank_feature_and_shape_mutations_reject(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutations = []

        rank = deepcopy(config)
        ranks = rank["immutable_sample_plans"]["10"]["source_ranks"]
        ranks.insert(-1, 208)
        mutations.append(rank)

        feature = deepcopy(config)
        feature["immutable_sample_plans"]["boundary_features"].append(176)
        mutations.append(feature)

        shape = deepcopy(config)
        shape["immutable_sample_plans"]["22"]["query_pair_shape"] = [15, 8, 2]
        mutations.append(shape)

        for mutated in mutations:
            with self.subTest(mutated=mutated["immutable_sample_plans"]):
                before = parent._CUPY_IMPORT_CALLS
                with self.assertRaises(ValueError):
                    sample_plan.compile_sample_plans(mutated)
                self.assertEqual(parent._CUPY_IMPORT_CALLS, before)
                self.assertNotIn("cupy", sys.modules)

    def test_all_plan_shapes_are_literal_for_both_populations(self) -> None:
        for cards in (10, 22):
            plan = sample_plan.CALIBRATION_SAMPLE_PLANS[cards]
            self.assertEqual(plan.source_pair_shape, (16, 8, 2))
            self.assertEqual(plan.query_pair_shape, (16, 8, 2))
            self.assertEqual(plan.fold_pair_shape, (16, 2, 2))
            self.assertEqual(plan.adjoint_pair_shape, (16, 8, 2))


    def test_reader_is_cupy_owner_adapter_and_v2_artifact_free(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_shared_direct_device_v3_result; "
            "print(int('cupy' in sys.modules)); "
            "print(int(any(name.endswith('_runner') for name in sys.modules))); "
            "print(int('pontius.legal_river_quotient_cuda_shared_direct_sample_plan' "
            "in sys.modules)); "
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
        self.assertEqual(completed.stdout.splitlines(), ["0", "0", "0", "0"])


    def test_minimal_infrastructure_journal_transduces(self) -> None:
        raw = _v3_journal(
            v2_controls._v2_journal(
                v2_controls.v1_controls._minimal_infrastructure_journal()
            )
        )
        rebound = reader.rebind_shared_direct_device_v3_journal(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "infrastructure_failure")
        self.assertFalse(rebound.passed)
        self.assertEqual(rebound.populations, ())

    def test_complete_synthetic_science_transduces_without_event_edits(self) -> None:
        raw = _v3_journal(
            v2_controls._v2_journal(
                v2_controls.v1_controls._complete_synthetic_journal()
            )
        )
        rebound = reader.rebind_shared_direct_device_v3_journal(
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
        translated = recover_journal_bytes(
            reader._translated_journal(recovery.records),
            expected_protocol_sha256=v2_reader.PROTOCOL_SHA256,
            expected_campaign_sha256=v2_reader.CAMPAIGN_SHA256,
        )
        for v3_record, v2_record in zip(
            recovery.records[2:-1], translated.records[2:-1], strict=True
        ):
            self.assertEqual(
                v3_record.body.payload["event"],
                v2_record.body.payload["event"],
            )
        self.assertEqual(
            recovery.records[-1].body.payload,
            translated.records[-1].body.payload,
        )

    def test_lifecycle_allowlist_is_literal_and_complete(self) -> None:
        raw = _v3_journal(
            v2_controls._v2_journal(
                v2_controls.v1_controls._minimal_infrastructure_journal()
            )
        )
        rebound = reader.rebind_shared_direct_device_v3_journal(
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

    def test_lifecycle_and_science_mutations_fail_closed(self) -> None:
        raw = _v3_journal(
            v2_controls._v2_journal(
                v2_controls.v1_controls._complete_synthetic_journal()
            )
        )

        def bootstrap(payloads) -> None:
            payloads[1]["event"]["runtime_name"] = "pontius"

        def phase(payloads) -> None:
            event = next(
                payload["event"]
                for payload in payloads[1:-1]
                if payload.get("kind") == "phase"
            )
            event["host_ns"] += 1

        def outer(payloads) -> None:
            payloads[-1]["complete_25_numerical_value"] = 1

        for mutation in (bootstrap, phase, outer):
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(ValueError):
                    reader.rebind_shared_direct_device_v3_journal(
                        _rewrite(raw, mutation), rebind_current_sources=False
                    )

    def test_reader_never_reads_retained_v2_artifact(self) -> None:
        raw = _v3_journal(
            v2_controls._v2_journal(
                v2_controls.v1_controls._minimal_infrastructure_journal()
            )
        )
        original = Path.read_bytes
        opened: list[Path] = []

        def recording(path: Path) -> bytes:
            opened.append(path)
            return original(path)

        with patch.object(Path, "read_bytes", recording):
            reader.rebind_shared_direct_device_v3_journal(
                raw, rebind_current_sources=False
            )
        self.assertNotIn(_V2_RESULT, opened)


if __name__ == "__main__":
    unittest.main()
