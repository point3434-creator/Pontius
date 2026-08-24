from __future__ import annotations

import ast
import tempfile
import unittest
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_nonreplay_qualification as evidence_codec
import pontius.fresh_action_width_transfer_qualification as qualification
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    parse_journal_record_line,
    recover_journal_bytes,
    recover_journal_file,
)
from pontius.fresh_action_width_nonreplay_qualification import (
    QualificationEvidenceKind,
)
from pontius.fresh_action_width_qualification import (
    ActionWidthQualificationArm,
    build_adr0323_qualification_schedule,
)
from pontius.fresh_action_width_transfer_qualification import (
    ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    ADR0340_TRANSFER_QUALIFICATION_PROTOCOL,
    ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
    ADR0340_TRANSFER_QUALIFICATION_TARGET,
    ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT,
    TransferQualificationExecutionFailed,
    TransferQualificationExecutionPhase,
    TransferQualificationJournalPrefix,
    TransferQualificationJournalResult,
    TransferQualificationSchedule,
    TransferQualificationStopReason,
    bind_adr0340_transfer_target_panel,
    build_adr0340_transfer_qualification_schedule,
    rebind_adr0340_transfer_qualification_journal,
    rebind_adr0340_transfer_target_panel,
    synthetic_transfer_accepted_evidence,
    synthetic_transfer_rejected_evidence,
    verify_adr0339_transfer_source_and_pool,
    verify_adr0340_transfer_qualification_source_and_dependencies,
)
from pontius.fresh_action_width_transfer_qualification_seal import (
    ADR0340_SYNTHETIC_CONTROL_IDENTITIES,
    ADR0340_SYNTHETIC_TARGET_PANEL_SHA256,
    ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH as SEALED_PATH,
    ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256,
    ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST,
    ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT as SEALED_TASK_COUNT,
)
from pontius.fresh_action_width_transfer_structures_seal import (
    ADR0339_TRANSFER_POOL_SHA256,
)


def _synthetic_value_evidence(
    index: int,
    task: object,
    *,
    full_value: float = 10.0,
    width_two_value: float = 0.0,
):
    value = (
        full_value
        if task.arm is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE  # type: ignore[attr-defined]
        else width_two_value
    )
    return synthetic_transfer_accepted_evidence(
        task_index=index,
        task=task,  # type: ignore[arg-type]
        lower_chips=value,
        upper_chips=value,
    )


def _fully_rehash_with_semantic_corruption(raw: bytes) -> bytes:
    records = tuple(
        parse_journal_record_line(line) for line in raw.splitlines(keepends=True)
    )
    rebuilt: list[JournalRecordEnvelope] = []
    previous: str | None = None
    for record in records:
        payload = record.body.payload
        semantic_identity = record.body.semantic_identity_sha256
        if record.body.sequence == 1:
            core = {
                key: value
                for key, value in payload.items()
                if key != "evidence_sha256"
            }
            core["context_index"] = 95
            semantic_identity = sha256(canonical_journal_json_bytes(core)).hexdigest()
            payload = {**core, "evidence_sha256": semantic_identity}
        envelope = JournalRecordEnvelope(
            build_journal_record_body(
                protocol_sha256=record.body.protocol_sha256,
                campaign_sha256=record.body.campaign_sha256,
                kind=record.body.kind,
                sequence=record.body.sequence,
                previous_record_sha256=previous,
                semantic_identity_sha256=semantic_identity,
                payload=payload,
            )
        )
        rebuilt.append(envelope)
        previous = envelope.line_sha256
    return b"".join(record.line_bytes for record in rebuilt)


class FreshActionWidthTransferQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = verify_adr0339_transfer_source_and_pool()
        cls.schedule = build_adr0340_transfer_qualification_schedule()
        cls.source_sha256 = (
            verify_adr0340_transfer_qualification_source_and_dependencies()
        )
        cls.temporary = tempfile.TemporaryDirectory()
        cls.target_path = Path(cls.temporary.name) / "target.jsonl"
        campaign = qualification._campaign_sha256(
            schedule=cls.schedule,
            qualification_source_sha256=cls.source_sha256,
            synthetic=True,
        )
        cls.receipt_counts: list[int] = []

        def owner(index: int, task: object):
            recovery = recover_journal_file(
                cls.target_path,
                expected_protocol_sha256=(
                    ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256
                ),
                expected_campaign_sha256=campaign,
            )
            cls.receipt_counts.append(len(recovery.records))
            if recovery.invalid_suffix_bytes or len(recovery.records) != index + 1:
                raise AssertionError("next transfer arm observed a damaged prefix")
            return _synthetic_value_evidence(index, task)

        with cls._runtime():
            cls.target_result = qualification._execute_transfer_qualification(
                output_path=cls.target_path,
                pool=cls.pool,
                schedule=cls.schedule,
                qualification_source_sha256=cls.source_sha256,
                arm_owner=owner,
                synthetic=True,
            )
        if not isinstance(cls.target_result, TransferQualificationJournalResult):
            raise AssertionError("synthetic transfer target did not complete")
        cls.target_raw = cls.target_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    @classmethod
    @contextmanager
    def _runtime(cls):
        with (
            patch.object(
                qualification,
                "verify_adr0340_transfer_qualification_source_and_dependencies",
                return_value=cls.source_sha256,
            ),
            patch.object(
                qualification,
                "verify_adr0339_transfer_source_and_pool",
                return_value=cls.pool,
            ),
            patch.object(
                qualification,
                "build_adr0340_transfer_qualification_schedule",
                return_value=cls.schedule,
            ),
        ):
            yield

    def _run_control(self, name: str, owner: object):
        with tempfile.TemporaryDirectory() as directory, self._runtime():
            path = Path(directory) / f"{name}.jsonl"
            result = qualification._execute_transfer_qualification(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                qualification_source_sha256=self.source_sha256,
                arm_owner=owner,  # type: ignore[arg-type]
                synthetic=True,
            )
            raw = path.read_bytes()
        self.assertIsInstance(result, TransferQualificationJournalResult)
        assert isinstance(result, TransferQualificationJournalResult)
        return result, raw

    def assert_control_identity(
        self,
        name: str,
        result: TransferQualificationJournalResult,
        raw: bytes,
    ) -> None:
        self.assertEqual(
            ADR0340_SYNTHETIC_CONTROL_IDENTITIES[name],
            (
                result.journal_sha256,
                result.terminal_sha256,
                len(raw),
                len(result.evidences) + 2,
            ),
        )

    def test_source_protocol_schedule_path_and_import_boundary_are_exact(self) -> None:
        root = Path(qualification.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_transfer_qualification.py"],
            self.source_sha256,
        )
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
            sha256(
                canonical_journal_json_bytes(
                    dict(ADR0340_TRANSFER_QUALIFICATION_PROTOCOL)
                )
            ).hexdigest(),
        )
        self.assertEqual(ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256, self.schedule.digest)
        self.assertEqual(SEALED_TASK_COUNT, ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT)
        self.assertEqual(SEALED_PATH, ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH)
        with self.assertRaises(TypeError):
            ADR0340_TRANSFER_QUALIFICATION_PROTOCOL["target"] = 1  # type: ignore[index]

        source = Path(qualification.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        for forbidden in (
            "fresh_action_width_nonreplay_qualification_result",
            "fresh_action_width_nonreplay_greedy",
            "fresh_action_width_nonreplay_greedy_result",
            "fresh_action_width_nonreplay_teacher",
            "capacity",
            "preparation",
            "action_clock",
        ):
            self.assertFalse(any(forbidden in module for module in imported_modules))
        call_names = tuple(
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        )
        self.assertEqual(1, call_names.count("consume_certified_reduced_sizing_v2"))
        self.assertNotIn("run_and_retain_adr0331_nonreplay_qualification", source)
        prospective = root.parents[1] / ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
        # ADR-0341 permanently retained the once-prospective no-clobber path.
        self.assertTrue(prospective.is_file())
        attributes = (root.parents[1] / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(f"/{ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH} -text", attributes)

    def test_schedule_is_exact_pool_bound_full_then_width_two(self) -> None:
        self.assertEqual(ADR0339_TRANSFER_POOL_SHA256, self.schedule.pool_sha256)
        self.assertEqual(192, len(self.schedule.tasks))
        for context_index, context in enumerate(self.pool.contexts):
            full = self.schedule.tasks[2 * context_index]
            width_two = self.schedule.tasks[2 * context_index + 1]
            self.assertEqual(context_index, full.context_index)
            self.assertEqual(context_index, width_two.context_index)
            self.assertEqual(context.semantic_digest, full.context_semantic_digest)
            self.assertEqual(context.semantic_digest, width_two.context_semantic_digest)
            self.assertIs(
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                full.arm,
            )
            self.assertIs(
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
                width_two.arm,
            )
            self.assertEqual(
                context.complete_raise_to_totals,
                full.request.legal_raise_to_totals,
            )
            self.assertEqual(
                (
                    context.complete_raise_to_totals[0],
                    context.complete_raise_to_totals[-1],
                ),
                width_two.request.legal_raise_to_totals,
            )
        development = build_adr0323_qualification_schedule()
        with self.assertRaisesRegex(ValueError, "exact pool"):
            TransferQualificationSchedule(
                pool_sha256=self.schedule.pool_sha256,
                tasks=development.tasks,
            )

    def test_target_requires_receipts_and_binds_only_contexts(self) -> None:
        result = self.target_result
        self.assertEqual(TransferQualificationStopReason.TARGET_REACHED, result.stop_reason)
        self.assertEqual(32, len(result.evidences))
        self.assertEqual(16, len(result.outcomes))
        self.assertEqual(tuple(range(16)), result.qualified_indices)
        self.assertEqual(32, result.known_public_call_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertEqual(tuple(range(1, 33)), tuple(self.receipt_counts))
        self.assert_control_identity("target", result, self.target_raw)

        with self._runtime():
            rebound = rebind_adr0340_transfer_qualification_journal(
                self.target_raw,
                synthetic=True,
            )
            panel = rebind_adr0340_transfer_target_panel(
                self.target_raw,
                synthetic=True,
            )
        self.assertEqual(result, rebound)
        self.assertEqual(ADR0340_SYNTHETIC_TARGET_PANEL_SHA256, panel.digest)
        self.assertEqual(tuple(range(16)), panel.qualified_indices)
        self.assertEqual(
            tuple(context.semantic_digest for context in self.pool.contexts[:16]),
            panel.context_semantic_sha256s,
        )
        panel_text = panel.canonical_bytes.decode("ascii")
        for forbidden in ("regret", "lower", "upper", "policy", "value"):
            self.assertNotIn(forbidden, panel_text)

    def test_every_semantic_terminal_category_is_distinct_and_sealed(self) -> None:
        def rejected(index: int, task: object):
            if index == 1:
                return synthetic_transfer_rejected_evidence(
                    task_index=index,
                    task=task,  # type: ignore[arg-type]
                )
            return _synthetic_value_evidence(index, task)

        def unexpected(index: int, task: object):
            if index == 1:
                raise RuntimeError("synthetic transfer owner failure")
            return _synthetic_value_evidence(index, task)

        def ambiguous(index: int, task: object):
            return synthetic_transfer_accepted_evidence(
                task_index=index,
                task=task,  # type: ignore[arg-type]
                lower_chips=1.0,
                upper_chips=1.01,
            )

        def reversal(index: int, task: object):
            value = (
                0.0
                if task.arm is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE  # type: ignore[attr-defined]
                else 1.0
            )
            return synthetic_transfer_accepted_evidence(
                task_index=index,
                task=task,  # type: ignore[arg-type]
                lower_chips=value,
                upper_chips=value,
            )

        def exhausted(index: int, task: object):
            return synthetic_transfer_accepted_evidence(
                task_index=index,
                task=task,  # type: ignore[arg-type]
                lower_chips=0.0,
                upper_chips=0.0,
            )

        cases = (
            ("rejected", rejected, TransferQualificationStopReason.CONSUMER_REJECTED, 2),
            ("unexpected", unexpected, TransferQualificationStopReason.UNEXPECTED_EXCEPTION, 2),
            ("ambiguous", ambiguous, TransferQualificationStopReason.AMBIGUOUS, 2),
            ("reversal", reversal, TransferQualificationStopReason.NESTED_VALUE_REVERSAL, 2),
            ("exhausted", exhausted, TransferQualificationStopReason.POOL_EXHAUSTED, 192),
        )
        for name, owner, stop, evidence_count in cases:
            with self.subTest(name=name):
                result, raw = self._run_control(name, owner)
                self.assertEqual(stop, result.stop_reason)
                self.assertEqual(evidence_count, len(result.evidences))
                self.assert_control_identity(name, result, raw)
                if name == "unexpected":
                    self.assertFalse(result.invocation_count_complete)
                else:
                    self.assertTrue(result.invocation_count_complete)
                with self.assertRaisesRegex(ValueError, "exact target stop"):
                    bind_adr0340_transfer_target_panel(result)

    def test_prefixes_torn_suffixes_and_rehashed_semantic_corruption_fail_closed(self) -> None:
        lines = self.target_raw.splitlines(keepends=True)
        with self._runtime():
            for count in range(len(lines)):
                raw = b"".join(lines[:count])
                rebound = rebind_adr0340_transfer_qualification_journal(
                    raw,
                    synthetic=True,
                )
                self.assertIsInstance(rebound, TransferQualificationJournalPrefix)
                assert isinstance(rebound, TransferQualificationJournalPrefix)
                self.assertEqual(raw, rebound.recovery.raw_bytes)
                self.assertEqual(max(0, count - 1), len(rebound.evidences))
            self.assertEqual(
                self.target_result,
                rebind_adr0340_transfer_qualification_journal(
                    self.target_raw,
                    synthetic=True,
                ),
            )
            for line_index in (1, len(lines) // 2, len(lines) - 1):
                prior = b"".join(lines[:line_index])
                line = lines[line_index]
                raw = prior + line[: len(line) // 2]
                rebound = rebind_adr0340_transfer_qualification_journal(
                    raw,
                    synthetic=True,
                )
                self.assertIsInstance(rebound, TransferQualificationJournalPrefix)
                assert isinstance(rebound, TransferQualificationJournalPrefix)
                self.assertEqual(prior, rebound.recovery.verified_prefix_bytes)
                self.assertEqual(line[: len(line) // 2], rebound.recovery.invalid_suffix_bytes)

            corrupted = _fully_rehash_with_semantic_corruption(self.target_raw)
            generic = recover_journal_bytes(corrupted)
            self.assertTrue(generic.is_complete)
            self.assertEqual(34, len(generic.records))
            with self.assertRaisesRegex(ValueError, "scheduled task|metadata"):
                rebind_adr0340_transfer_qualification_journal(
                    corrupted,
                    synthetic=True,
                )
            with self.assertRaises(ValueError):
                rebind_adr0340_transfer_qualification_journal(
                    self.target_raw,
                    synthetic=False,
                )

    def test_invalid_owner_evidence_becomes_durable_unexpected_stop(self) -> None:
        def owner(index: int, task: object):
            if index == 0:
                return _synthetic_value_evidence(index, task)
            return synthetic_transfer_accepted_evidence(
                task_index=0,
                task=self.schedule.tasks[0],
                lower_chips=1.0,
                upper_chips=1.0,
            )

        result, _ = self._run_control("invalid-owner", owner)
        self.assertEqual(
            TransferQualificationStopReason.UNEXPECTED_EXCEPTION,
            result.stop_reason,
        )
        self.assertEqual(2, len(result.evidences))
        self.assertIs(QualificationEvidenceKind.UNEXPECTED_EXCEPTION, result.evidences[1].kind)
        self.assertFalse(result.invocation_count_complete)

    def test_observation_and_terminal_append_failures_preserve_receipts(self) -> None:
        original_append = qualification.DurableEvidenceJournalWriter.append
        with tempfile.TemporaryDirectory() as directory:
            observation_path = Path(directory) / "observation-failure.jsonl"

            def fail_second_observation(writer: object, **kwargs: object):
                if (
                    kwargs["kind"] is JournalRecordKind.OBSERVATION
                    and writer.next_sequence == 2  # type: ignore[attr-defined]
                ):
                    raise OSError("injected observation append failure")
                return original_append(writer, **kwargs)  # type: ignore[arg-type]

            with (
                self._runtime(),
                patch.object(
                    qualification.DurableEvidenceJournalWriter,
                    "append",
                    new=fail_second_observation,
                ),
            ):
                failure = qualification._execute_transfer_qualification(
                    output_path=observation_path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=_synthetic_value_evidence,
                    synthetic=True,
                )
            self.assertIsInstance(failure, TransferQualificationExecutionFailed)
            assert isinstance(failure, TransferQualificationExecutionFailed)
            self.assertEqual(
                TransferQualificationExecutionPhase.OBSERVATION_APPEND,
                failure.phase,
            )
            self.assertEqual(1, failure.failed_task_index)
            self.assertTrue(failure.unreceipted_arm_invocation)
            self.assertEqual(1, len(failure.durably_recorded_evidences))
            self.assertEqual(1, failure.known_public_call_count)
            self.assertFalse(failure.invocation_count_complete)
            assert failure.recovery is not None
            self.assertEqual(2, len(failure.recovery.records))

            terminal_path = Path(directory) / "terminal-failure.jsonl"

            def fail_terminal(writer: object, **kwargs: object):
                if kwargs["kind"] is JournalRecordKind.TERMINAL:
                    raise OSError("injected terminal append failure")
                return original_append(writer, **kwargs)  # type: ignore[arg-type]

            with (
                self._runtime(),
                patch.object(
                    qualification.DurableEvidenceJournalWriter,
                    "append",
                    new=fail_terminal,
                ),
            ):
                terminal_failure = qualification._execute_transfer_qualification(
                    output_path=terminal_path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=_synthetic_value_evidence,
                    synthetic=True,
                )
            self.assertIsInstance(
                terminal_failure,
                TransferQualificationExecutionFailed,
            )
            assert isinstance(terminal_failure, TransferQualificationExecutionFailed)
            self.assertEqual(
                TransferQualificationExecutionPhase.TERMINAL_APPEND,
                terminal_failure.phase,
            )
            self.assertFalse(terminal_failure.unreceipted_arm_invocation)
            self.assertEqual(32, len(terminal_failure.durably_recorded_evidences))
            self.assertEqual(32, terminal_failure.known_public_call_count)
            self.assertTrue(terminal_failure.invocation_count_complete)
            assert terminal_failure.recovery is not None
            self.assertEqual(33, len(terminal_failure.recovery.records))

    def test_no_clobber_precedes_any_owner_call(self) -> None:
        calls = 0

        def owner(index: int, task: object):
            nonlocal calls
            calls += 1
            return _synthetic_value_evidence(index, task)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.jsonl"
            original = b"do-not-clobber\n"
            path.write_bytes(original)
            with self.assertRaises(FileExistsError):
                qualification._execute_transfer_qualification(
                    output_path=path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=owner,
                    synthetic=True,
                )
            self.assertEqual(original, path.read_bytes())
        self.assertEqual(0, calls)

    def test_inherited_real_codec_still_requires_policy_and_dual_witnesses(self) -> None:
        task = self.schedule.tasks[0]
        synthetic = synthetic_transfer_accepted_evidence(
            task_index=0,
            task=task,
            lower_chips=1.0,
            upper_chips=1.0,
        )
        result = dict(synthetic.core["result"])  # type: ignore[arg-type]
        result["synthetic_result"] = False
        fabricated = evidence_codec._build_evidence(
            task_index=0,
            task=task,
            kind=QualificationEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=result,
        )
        with self.assertRaisesRegex(ValueError, "behavioral witness|dual certificate"):
            qualification._validate_evidence_against_task(
                fabricated,
                task=task,
                expect_synthetic=False,
            )

    def test_partial_interpretation_and_panel_type_fail_closed(self) -> None:
        self.assertEqual(
            "all-unchanged-conjuncts-or-reject-unrestricted-transfer",
            ADR0340_TRANSFER_QUALIFICATION_PROTOCOL[
                "partial_transfer_interpretation"
            ],
        )
        with self._runtime():
            prefix = rebind_adr0340_transfer_qualification_journal(
                self.target_raw.splitlines(keepends=True)[0],
                synthetic=True,
            )
        with self.assertRaises(TypeError):
            bind_adr0340_transfer_target_panel(prefix)  # type: ignore[arg-type]
        with self._runtime():
            panel = rebind_adr0340_transfer_target_panel(
                self.target_raw,
                synthetic=True,
            )
        with self.assertRaisesRegex(ValueError, "exact pool"):
            type(panel)(
                pool_sha256=panel.pool_sha256,
                schedule_sha256=panel.schedule_sha256,
                campaign_sha256=panel.campaign_sha256,
                journal_sha256=panel.journal_sha256,
                terminal_sha256=panel.terminal_sha256,
                qualified_indices=panel.qualified_indices,
                context_semantic_sha256s=(
                    self.pool.contexts[16].semantic_digest,
                    *panel.context_semantic_sha256s[1:],
                ),
                synthetic=True,
            )


if __name__ == "__main__":
    unittest.main()
