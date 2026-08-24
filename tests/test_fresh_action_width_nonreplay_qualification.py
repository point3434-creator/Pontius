from __future__ import annotations

import ast
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_nonreplay_qualification as qualification
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
    ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    ADR0331_QUALIFICATION_PROTOCOL,
    ADR0331_QUALIFICATION_PROTOCOL_SHA256,
    ADR0331_QUALIFICATION_TARGET,
    ADR0331_QUALIFICATION_TASK_COUNT,
    NonReplayQualificationStopReason,
    QualificationEvidenceKind,
    QualificationExecutionFailed,
    QualificationExecutionPhase,
    QualificationJournalPrefix,
    QualificationJournalResult,
    QualificationLaunchRejected,
    build_adr0331_nonreplay_qualification_schedule,
    rebind_adr0331_qualification_journal,
    run_and_retain_adr0331_nonreplay_qualification,
    synthetic_accepted_evidence,
    synthetic_rejected_evidence,
    verify_adr0332_nonreplay_source_and_pool,
    verify_adr0333_qualification_source_and_dependencies,
)
from pontius.fresh_action_width_nonreplay_qualification_seal import (
    ADR0331_QUALIFICATION_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0331_QUALIFICATION_SCHEDULE_SHA256,
    ADR0331_QUALIFICATION_SOURCE_MANIFEST,
    ADR0331_QUALIFICATION_TASK_COUNT as SEALED_TASK_COUNT,
    ADR0333_SYNTHETIC_CONTROL_IDENTITIES,
)
from pontius.fresh_action_width_qualification import (
    ADR0323_OPPORTUNITY_FLOOR,
    ActionWidthQualificationArm,
)


def _forbidden_consumer(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the source-only qualification may not invoke its consumer")


def _synthetic_value_evidence(
    index: int,
    task: object,
    *,
    full_value: float = 1.0,
    width_two_value: float = 0.0,
):
    arm = task.arm  # type: ignore[attr-defined]
    value = (
        full_value
        if arm is ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE
        else width_two_value
    )
    return synthetic_accepted_evidence(
        task_index=index,
        task=task,  # type: ignore[arg-type]
        lower_chips=value,
        upper_chips=value,
    )


def _fully_rehash_with_semantic_corruption(raw: bytes) -> bytes:
    records = tuple(
        parse_journal_record_line(line)
        for line in raw.splitlines(keepends=True)
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
            semantic_identity = sha256(
                canonical_journal_json_bytes(core)
            ).hexdigest()
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


class FreshActionWidthNonReplayQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = verify_adr0332_nonreplay_source_and_pool()
        cls.schedule = build_adr0331_nonreplay_qualification_schedule()
        cls.source_sha256 = verify_adr0333_qualification_source_and_dependencies()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.target_path = Path(cls.temporary.name) / "target.jsonl"
        cls.observed_receipted_prefix_counts: list[int] = []

        def owner(index: int, task: object):
            recovery = recover_journal_file(
                cls.target_path,
                expected_protocol_sha256=ADR0331_QUALIFICATION_PROTOCOL_SHA256,
            )
            cls.observed_receipted_prefix_counts.append(len(recovery.records))
            if recovery.failure is not None or recovery.invalid_suffix_bytes:
                raise AssertionError("next arm observed a damaged journal prefix")
            return _synthetic_value_evidence(index, task)

        cls.target_result = qualification._execute_qualification(
            output_path=cls.target_path,
            pool=cls.pool,
            schedule=cls.schedule,
            qualification_source_sha256=cls.source_sha256,
            arm_owner=owner,
            synthetic=True,
        )
        cls.target_raw = cls.target_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def assert_control_identity(
        self,
        name: str,
        result: QualificationJournalResult,
    ) -> None:
        self.assertEqual(
            ADR0333_SYNTHETIC_CONTROL_IDENTITIES[name],
            (
                result.journal_sha256,
                result.terminal_sha256,
                result.journal_byte_count,
                len(result.evidences) + 2,
            ),
        )

    def test_source_manifest_protocol_schedule_and_import_boundary_are_exact(self) -> None:
        root = Path(qualification.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0331_QUALIFICATION_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0331_QUALIFICATION_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_nonreplay_qualification.py"],
            verify_adr0333_qualification_source_and_dependencies(),
        )
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0331_QUALIFICATION_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0331_QUALIFICATION_PROTOCOL_SHA256,
            sha256(
                canonical_journal_json_bytes(dict(ADR0331_QUALIFICATION_PROTOCOL))
            ).hexdigest(),
        )
        self.assertEqual(ADR0331_QUALIFICATION_SCHEDULE_SHA256, self.schedule.digest)
        self.assertEqual(SEALED_TASK_COUNT, ADR0331_QUALIFICATION_TASK_COUNT)
        self.assertEqual(192, len(self.schedule.tasks))

        tree = ast.parse(Path(qualification.__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        consumer_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "consume_certified_reduced_sizing_v2"
            ):
                consumer_calls += 1
        forbidden_modules = {
            "fresh_action_width_greedy",
            "fresh_action_width_result",
            "fresh_action_width_teacher",
            "preparation_bank",
            "resolver",
            "strategy_bridge",
            "transfer",
        }
        self.assertTrue(imported.isdisjoint(forbidden_modules))
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("apply_action", attributes)
        self.assertEqual(1, consumer_calls)
        self.assertFalse(
            (
                Path(qualification.__file__).resolve().parents[2]
                / ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH
            ).exists()
        )
        with self.assertRaises(TypeError):
            ADR0331_QUALIFICATION_PROTOCOL["task_count"] = 1  # type: ignore[index]

    def test_schedule_is_complete_ordered_candidate_blind_and_consumer_free(self) -> None:
        with patch.object(
            qualification,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            schedule = build_adr0331_nonreplay_qualification_schedule()
        self.assertEqual(self.pool.digest, schedule.pool_sha256)
        self.assertEqual(ADR0331_QUALIFICATION_TASK_COUNT, len(schedule.tasks))
        for context_index, context in enumerate(self.pool.contexts):
            full, width_two = schedule.tasks[2 * context_index : 2 * context_index + 2]
            self.assertEqual(context_index, full.context_index)
            self.assertEqual(context_index, width_two.context_index)
            self.assertEqual(
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                full.arm,
            )
            self.assertEqual(
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
                width_two.arm,
            )
            self.assertEqual(context.complete_raise_to_totals, full.request.legal_raise_to_totals)
            self.assertEqual(
                (
                    context.complete_raise_to_totals[0],
                    context.complete_raise_to_totals[-1],
                ),
                width_two.request.legal_raise_to_totals,
            )

    def test_target_run_requires_a_durable_receipt_before_every_next_arm(self) -> None:
        result = self.target_result
        self.assertIsInstance(result, QualificationJournalResult)
        assert isinstance(result, QualificationJournalResult)
        self.assertEqual(NonReplayQualificationStopReason.TARGET_REACHED, result.stop_reason)
        self.assertEqual(2 * ADR0331_QUALIFICATION_TARGET, len(result.evidences))
        self.assertEqual(ADR0331_QUALIFICATION_TARGET, len(result.outcomes))
        self.assertEqual(tuple(range(ADR0331_QUALIFICATION_TARGET)), result.qualified_indices)
        self.assertEqual(32, result.known_public_call_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertEqual(list(range(1, 33)), self.observed_receipted_prefix_counts)
        recovery = recover_journal_bytes(self.target_raw)
        self.assertTrue(recovery.is_complete)
        self.assertEqual(34, len(recovery.records))
        self.assertEqual(JournalRecordKind.HEADER, recovery.records[0].body.kind)
        self.assertEqual(JournalRecordKind.TERMINAL, recovery.records[-1].body.kind)
        self.assert_control_identity("target", result)

    def test_distinct_rejection_unexpected_ambiguity_and_reversal_stops(self) -> None:
        cases: tuple[
            tuple[str, NonReplayQualificationStopReason, bool, int], ...
        ] = (
            ("rejected", NonReplayQualificationStopReason.CONSUMER_REJECTED, True, 2),
            (
                "unexpected",
                NonReplayQualificationStopReason.UNEXPECTED_EXCEPTION,
                False,
                1,
            ),
            ("ambiguous", NonReplayQualificationStopReason.AMBIGUOUS, True, 2),
            (
                "reversal",
                NonReplayQualificationStopReason.NESTED_VALUE_REVERSAL,
                True,
                2,
            ),
        )
        for mode, expected_stop, complete, expected_calls in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / f"{mode}.jsonl"

                def owner(index: int, task: object):
                    if mode == "rejected" and index == 1:
                        return synthetic_rejected_evidence(
                            task_index=index,
                            task=task,  # type: ignore[arg-type]
                        )
                    if mode == "unexpected" and index == 1:
                        raise RuntimeError("synthetic owner failure")
                    if mode == "ambiguous":
                        threshold = (
                            ADR0323_OPPORTUNITY_FLOOR.value
                            * self.pool.contexts[0].payoff_span_chips
                        )
                        value = threshold if index == 0 else 0.0
                    elif mode == "reversal":
                        value = 0.0 if index == 0 else 1.0
                    else:
                        return _synthetic_value_evidence(index, task)
                    return synthetic_accepted_evidence(
                        task_index=index,
                        task=task,  # type: ignore[arg-type]
                        lower_chips=value,
                        upper_chips=value,
                    )

                result = qualification._execute_qualification(
                    output_path=path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=owner,
                    synthetic=True,
                )
                self.assertIsInstance(result, QualificationJournalResult)
                assert isinstance(result, QualificationJournalResult)
                self.assertEqual(expected_stop, result.stop_reason)
                self.assertEqual(2, len(result.evidences))
                self.assertEqual(expected_calls, result.known_public_call_count)
                self.assertIs(complete, result.invocation_count_complete)
                self.assert_control_identity(mode, result)
                self.assertEqual(result, rebind_adr0331_qualification_journal(
                    path.read_bytes(), synthetic=True
                ))

    def test_pool_exhaustion_reduces_all_192_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exhausted.jsonl"

            def owner(index: int, task: object):
                return synthetic_accepted_evidence(
                    task_index=index,
                    task=task,  # type: ignore[arg-type]
                    lower_chips=0.0,
                    upper_chips=0.0,
                )

            result = qualification._execute_qualification(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                qualification_source_sha256=self.source_sha256,
                arm_owner=owner,
                synthetic=True,
            )
        self.assertIsInstance(result, QualificationJournalResult)
        assert isinstance(result, QualificationJournalResult)
        self.assertEqual(NonReplayQualificationStopReason.POOL_EXHAUSTED, result.stop_reason)
        self.assertEqual(192, len(result.evidences))
        self.assertEqual(96, len(result.outcomes))
        self.assertEqual((), result.qualified_indices)
        self.assertEqual(192, result.known_public_call_count)
        self.assert_control_identity("exhausted", result)

    def test_every_complete_prefix_and_representative_torn_tail_rebind_exactly(self) -> None:
        lines = self.target_raw.splitlines(keepends=True)
        with (
            patch.object(
                qualification,
                "verify_adr0333_qualification_source_and_dependencies",
                return_value=self.source_sha256,
            ),
            patch.object(
                qualification,
                "verify_adr0332_nonreplay_source_and_pool",
                return_value=self.pool,
            ),
            patch.object(
                qualification,
                "build_adr0331_nonreplay_qualification_schedule",
                return_value=self.schedule,
            ),
        ):
            for count in range(len(lines)):
                raw = b"".join(lines[:count])
                rebound = rebind_adr0331_qualification_journal(raw, synthetic=True)
                self.assertIsInstance(rebound, QualificationJournalPrefix)
                assert isinstance(rebound, QualificationJournalPrefix)
                self.assertEqual(raw, rebound.recovery.raw_bytes)
                self.assertEqual(max(0, count - 1), len(rebound.evidences))
            complete = rebind_adr0331_qualification_journal(
                self.target_raw,
                synthetic=True,
            )
            self.assertEqual(self.target_result, complete)

            for line_index in (1, len(lines) // 2, len(lines) - 1):
                prior = b"".join(lines[:line_index])
                line = lines[line_index]
                for cut in (1, len(line) // 2, len(line) - 1):
                    raw = prior + line[:cut]
                    rebound = rebind_adr0331_qualification_journal(
                        raw,
                        synthetic=True,
                    )
                    self.assertIsInstance(rebound, QualificationJournalPrefix)
                    assert isinstance(rebound, QualificationJournalPrefix)
                    self.assertEqual(prior, rebound.recovery.verified_prefix_bytes)
                    self.assertEqual(line[:cut], rebound.recovery.invalid_suffix_bytes)
                    self.assertEqual(raw, rebound.recovery.raw_bytes)

    def test_fully_rehashed_same_count_semantic_corruption_is_rejected(self) -> None:
        corrupted = _fully_rehash_with_semantic_corruption(self.target_raw)
        generic = recover_journal_bytes(corrupted)
        self.assertTrue(generic.is_complete)
        self.assertEqual(34, len(generic.records))
        with self.assertRaisesRegex(ValueError, "scheduled task|metadata"):
            rebind_adr0331_qualification_journal(corrupted, synthetic=True)

    def test_real_value_endpoint_requires_policy_and_dual_witnesses(self) -> None:
        task = self.schedule.tasks[0]
        synthetic = synthetic_accepted_evidence(
            task_index=0,
            task=task,
            lower_chips=1.0,
            upper_chips=1.0,
        )
        result = dict(synthetic.core["result"])  # type: ignore[arg-type]
        result["synthetic_result"] = False
        fabricated = qualification._build_evidence(
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

    def test_invalid_owner_evidence_becomes_durable_unexpected_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-owner.jsonl"

            def owner(index: int, task: object):
                if index == 0:
                    return _synthetic_value_evidence(index, task)
                return synthetic_accepted_evidence(
                    task_index=0,
                    task=self.schedule.tasks[0],
                    lower_chips=1.0,
                    upper_chips=1.0,
                )

            result = qualification._execute_qualification(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                qualification_source_sha256=self.source_sha256,
                arm_owner=owner,
                synthetic=True,
            )
        self.assertIsInstance(result, QualificationJournalResult)
        assert isinstance(result, QualificationJournalResult)
        self.assertEqual(
            NonReplayQualificationStopReason.UNEXPECTED_EXCEPTION,
            result.stop_reason,
        )
        self.assertEqual(QualificationEvidenceKind.UNEXPECTED_EXCEPTION, result.evidences[1].kind)
        self.assertFalse(result.invocation_count_complete)

    def test_observation_and_terminal_append_failures_preserve_receipted_evidence(self) -> None:
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

            with patch.object(
                qualification.DurableEvidenceJournalWriter,
                "append",
                new=fail_second_observation,
            ):
                observation_failure = qualification._execute_qualification(
                    output_path=observation_path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=_synthetic_value_evidence,
                    synthetic=True,
                )
            self.assertIsInstance(observation_failure, QualificationExecutionFailed)
            assert isinstance(observation_failure, QualificationExecutionFailed)
            self.assertEqual(
                QualificationExecutionPhase.OBSERVATION_APPEND,
                observation_failure.phase,
            )
            self.assertEqual(1, observation_failure.failed_task_index)
            self.assertTrue(observation_failure.unreceipted_arm_invocation)
            self.assertEqual(1, len(observation_failure.durably_recorded_evidences))
            self.assertEqual(1, observation_failure.known_public_call_count)
            self.assertFalse(observation_failure.invocation_count_complete)
            self.assertEqual(
                observation_path.read_bytes(),
                observation_failure.raw_journal_bytes,
            )
            assert observation_failure.recovery is not None
            self.assertEqual(2, len(observation_failure.recovery.records))

            terminal_path = Path(directory) / "terminal-failure.jsonl"

            def fail_terminal(writer: object, **kwargs: object):
                if kwargs["kind"] is JournalRecordKind.TERMINAL:
                    raise OSError("injected terminal append failure")
                return original_append(writer, **kwargs)  # type: ignore[arg-type]

            with patch.object(
                qualification.DurableEvidenceJournalWriter,
                "append",
                new=fail_terminal,
            ):
                terminal_failure = qualification._execute_qualification(
                    output_path=terminal_path,
                    pool=self.pool,
                    schedule=self.schedule,
                    qualification_source_sha256=self.source_sha256,
                    arm_owner=_synthetic_value_evidence,
                    synthetic=True,
                )
            self.assertIsInstance(terminal_failure, QualificationExecutionFailed)
            assert isinstance(terminal_failure, QualificationExecutionFailed)
            self.assertEqual(
                QualificationExecutionPhase.TERMINAL_APPEND,
                terminal_failure.phase,
            )
            self.assertFalse(terminal_failure.unreceipted_arm_invocation)
            self.assertEqual(32, len(terminal_failure.durably_recorded_evidences))
            self.assertEqual(32, terminal_failure.known_public_call_count)
            self.assertTrue(terminal_failure.invocation_count_complete)
            assert terminal_failure.recovery is not None
            self.assertEqual(33, len(terminal_failure.recovery.records))
            self.assertFalse(terminal_failure.recovery.is_complete)

    def test_public_runner_preflight_and_exclusive_create_fail_without_a_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prospective.jsonl"
            with (
                patch.object(qualification, "_artifact_path", return_value=path),
                patch.object(
                    qualification,
                    "verify_adr0333_qualification_source_and_dependencies",
                    side_effect=RuntimeError("source drift"),
                ),
                patch.object(
                    qualification,
                    "consume_certified_reduced_sizing_v2",
                    side_effect=_forbidden_consumer,
                ),
            ):
                rejected = run_and_retain_adr0331_nonreplay_qualification()
            self.assertIsInstance(rejected, QualificationLaunchRejected)
            self.assertFalse(path.exists())

            path.write_bytes(b"do-not-clobber")
            with (
                patch.object(qualification, "_artifact_path", return_value=path),
                patch.object(
                    qualification,
                    "verify_adr0333_qualification_source_and_dependencies",
                    return_value=self.source_sha256,
                ),
                patch.object(
                    qualification,
                    "verify_adr0332_nonreplay_source_and_pool",
                    return_value=self.pool,
                ),
                patch.object(
                    qualification,
                    "build_adr0331_nonreplay_qualification_schedule",
                    return_value=self.schedule,
                ),
                patch.object(
                    qualification,
                    "consume_certified_reduced_sizing_v2",
                    side_effect=_forbidden_consumer,
                ),
            ):
                collision = run_and_retain_adr0331_nonreplay_qualification()
            self.assertIsInstance(collision, QualificationLaunchRejected)
            self.assertEqual(b"do-not-clobber", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
