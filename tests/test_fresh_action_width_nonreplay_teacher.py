from __future__ import annotations

import ast
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pontius.fresh_action_width_nonreplay_teacher as teacher
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_bytes,
    recover_journal_file,
)
from pontius.fresh_action_width_nonreplay import build_adr0331_nonreplay_pool
from pontius.fresh_action_width_nonreplay_teacher import (
    ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
    ADR0335_TEACHER_PROTOCOL,
    ADR0335_TEACHER_PROTOCOL_SHA256,
    ADR0335_TEACHER_SUBSET_COUNTS,
    ADR0335_TEACHER_TASK_COUNT,
    NonReplayTeacherEvidenceKind,
    NonReplayTeacherExecutionFailed,
    NonReplayTeacherExecutionPhase,
    NonReplayTeacherJournalPrefix,
    NonReplayTeacherJournalResult,
    NonReplayTeacherLaunchRejected,
    NonReplayTeacherStopReason,
    build_adr0334_nonreplay_exhaustive_teacher_schedule,
    rebind_adr0335_teacher_journal,
    run_and_retain_adr0334_nonreplay_exhaustive_teacher,
    synthetic_teacher_accepted_evidence,
    synthetic_teacher_rejected_evidence,
    verify_adr0335_teacher_source_and_dependencies,
)
from pontius.fresh_action_width_nonreplay_teacher_seal import (
    ADR0335_SYNTHETIC_COMPLETED_CONTROL,
    ADR0335_TEACHER_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0335_TEACHER_SCHEDULE_SHA256,
    ADR0335_TEACHER_SOURCE_MANIFEST,
    ADR0335_TEACHER_SUBSET_COUNTS as SEALED_SUBSET_COUNTS,
    ADR0335_TEACHER_TASK_COUNT as SEALED_TASK_COUNT,
)
from pontius.fresh_action_width_teacher import ExhaustiveTeacherArm


def _forbidden_consumer(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the source-only teacher may not invoke its consumer")


def _completed_synthetic_evidence(index: int, task: object):
    value = (
        1.0
        if task.arm is ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE  # type: ignore[attr-defined]
        else 0.0
    )
    return synthetic_teacher_accepted_evidence(
        task_index=index,
        task=task,  # type: ignore[arg-type]
        lower_chips=value,
        upper_chips=value,
    )


class FreshActionWidthNonReplayTeacherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = build_adr0331_nonreplay_pool()
        cls.schedule = build_adr0334_nonreplay_exhaustive_teacher_schedule()
        cls.source_sha256 = verify_adr0335_teacher_source_and_dependencies()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.completed_path = Path(cls.temporary.name) / "completed.jsonl"
        cls.completed_result = teacher._execute_teacher(
            output_path=cls.completed_path,
            pool=cls.pool,
            schedule=cls.schedule,
            teacher_source_sha256=cls.source_sha256,
            arm_owner=_completed_synthetic_evidence,
            synthetic=True,
        )
        cls.completed_raw = cls.completed_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def _execute(self, owner: object, name: str):
        path = Path(self.temporary.name) / f"{name}.jsonl"
        with (
            patch.object(
                teacher,
                "verify_adr0335_teacher_source_and_dependencies",
                return_value=self.source_sha256,
            ),
            patch.object(
                teacher,
                "build_adr0331_nonreplay_pool",
                return_value=self.pool,
            ),
            patch.object(
                teacher,
                "build_adr0334_nonreplay_exhaustive_teacher_schedule",
                return_value=self.schedule,
            ),
        ):
            result = teacher._execute_teacher(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                teacher_source_sha256=self.source_sha256,
                arm_owner=owner,  # type: ignore[arg-type]
                synthetic=True,
            )
        return result, path

    def test_source_protocol_schedule_and_import_boundary_are_exact(self) -> None:
        root = Path(teacher.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0335_TEACHER_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0335_TEACHER_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_nonreplay_teacher.py"],
            verify_adr0335_teacher_source_and_dependencies(),
        )
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0335_TEACHER_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0335_TEACHER_PROTOCOL_SHA256,
            sha256(
                canonical_journal_json_bytes(dict(ADR0335_TEACHER_PROTOCOL))
            ).hexdigest(),
        )
        self.assertEqual(ADR0335_TEACHER_SCHEDULE_SHA256, self.schedule.digest)
        self.assertEqual(SEALED_SUBSET_COUNTS, ADR0335_TEACHER_SUBSET_COUNTS)
        self.assertEqual(SEALED_TASK_COUNT, ADR0335_TEACHER_TASK_COUNT)

        tree = ast.parse(Path(teacher.__file__).read_text(encoding="utf-8"))
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
        self.assertTrue(
            imported.isdisjoint(
                {
                    "fresh_action_width_greedy",
                    "preparation_bank",
                    "resolver",
                    "strategy_bridge",
                    "transfer",
                }
            )
        )
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("apply_action", attributes)
        self.assertEqual(1, consumer_calls)
        prospective = (
            Path(teacher.__file__).resolve().parents[2]
            / ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH
        )
        self.assertFalse(prospective.exists())
        with self.assertRaises(TypeError):
            ADR0335_TEACHER_PROTOCOL["task_count"] = 1  # type: ignore[index]

    def test_schedule_is_exact_ordered_panel_bound_and_consumer_free(self) -> None:
        with patch.object(
            teacher,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            schedule = build_adr0334_nonreplay_exhaustive_teacher_schedule()
        self.assertEqual(2_113, len(schedule.tasks))
        self.assertEqual(tuple(range(2_113)), tuple(t.ordinal for t in schedule.tasks))
        self.assertEqual(
            {7: 4, 9: 7, 11: 5},
            dict(Counter(
                len(task.request.legal_raise_to_totals)
                for task in schedule.tasks
                if task.arm is ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE
            )),
        )
        self.assertEqual(
            ADR0335_TEACHER_SUBSET_COUNTS,
            tuple(
                (
                    width,
                    sum(
                        task.raise_width is not None
                        and task.raise_width.count == width
                        for task in schedule.tasks
                    ),
                )
                for width in range(2, 7)
            ),
        )
        for panel_position in range(16):
            tasks = tuple(
                task
                for task in schedule.tasks
                if task.panel_position == panel_position
            )
            self.assertIs(
                ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE,
                tasks[0].arm,
            )
            self.assertTrue(all(
                task.arm is ExhaustiveTeacherArm.ANCHORED_SUBSET
                for task in tasks[1:]
            ))

    def test_complete_solver_free_journal_matches_sealed_control(self) -> None:
        result = self.completed_result
        self.assertIsInstance(result, NonReplayTeacherJournalResult)
        assert isinstance(result, NonReplayTeacherJournalResult)
        self.assertEqual(NonReplayTeacherStopReason.COMPLETED, result.stop_reason)
        self.assertEqual(2_113, len(result.evidences))
        self.assertEqual(16, len(result.contexts))
        self.assertEqual(2_113, result.known_public_call_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertEqual(
            dict(ADR0335_SYNTHETIC_COMPLETED_CONTROL),
            {
                "context_count": len(result.contexts),
                "journal_byte_count": result.journal_byte_count,
                "journal_sha256": result.journal_sha256,
                "public_call_count": result.known_public_call_count,
                "record_count": len(result.evidences) + 2,
                "terminal_sha256": result.terminal_sha256,
            },
        )
        recovery = recover_journal_bytes(self.completed_raw)
        self.assertTrue(recovery.is_complete)
        self.assertEqual(2_115, len(recovery.records))
        self.assertIs(JournalRecordKind.HEADER, recovery.records[0].body.kind)
        self.assertIs(JournalRecordKind.TERMINAL, recovery.records[-1].body.kind)

        first = result.contexts[0]
        self.assertEqual(5, len(first.widths))
        self.assertEqual(1.0, first.widths[0].full_minus_teacher_regret.signed_lower_chips)
        width_three = first.widths[1]
        self.assertEqual(
            tuple(range(len(width_three.subset_observations))),
            width_three.envelope.nondominated_subset_indices,
        )
        self.assertEqual(
            width_three.envelope.nondominated_subset_indices,
            width_three.envelope.equivalent_subset_indices,
        )
        self.assertIsNone(width_three.envelope.unique_best_subset_index)
        with self.assertRaisesRegex(ValueError, "call count drifted"):
            replace(result, known_public_call_count=0)
        with self.assertRaisesRegex(ValueError, "partial state"):
            replace(result, pending_full_evidence_sha256="0" * 64)

    def test_rejection_unexpected_and_nested_reversal_are_distinct_terminals(self) -> None:
        cases = (
            (
                "rejected",
                NonReplayTeacherStopReason.CONSUMER_REJECTED,
                True,
                1,
            ),
            (
                "unexpected",
                NonReplayTeacherStopReason.UNEXPECTED_EXCEPTION,
                False,
                1,
            ),
            (
                "reversal",
                NonReplayTeacherStopReason.NESTED_VALUE_REVERSAL,
                True,
                2,
            ),
        )
        for mode, expected_stop, complete, expected_calls in cases:
            with self.subTest(mode=mode):
                def owner(index: int, task: object):
                    if index == 0:
                        value = 0.0 if mode == "reversal" else 1.0
                        return synthetic_teacher_accepted_evidence(
                            task_index=index,
                            task=task,  # type: ignore[arg-type]
                            lower_chips=value,
                            upper_chips=value,
                        )
                    if mode == "rejected":
                        return synthetic_teacher_rejected_evidence(
                            task_index=index,
                            task=task,  # type: ignore[arg-type]
                        )
                    if mode == "unexpected":
                        raise RuntimeError("synthetic owner failure")
                    return synthetic_teacher_accepted_evidence(
                        task_index=index,
                        task=task,  # type: ignore[arg-type]
                        lower_chips=1.0,
                        upper_chips=1.0,
                    )

                result, path = self._execute(owner, mode)
                self.assertIsInstance(result, NonReplayTeacherJournalResult)
                assert isinstance(result, NonReplayTeacherJournalResult)
                self.assertEqual(expected_stop, result.stop_reason)
                self.assertEqual(2, len(result.evidences))
                self.assertEqual(expected_calls, result.known_public_call_count)
                self.assertIs(complete, result.invocation_count_complete)
                self.assertEqual(
                    result,
                    rebind_adr0335_teacher_journal(
                        path.read_bytes(), synthetic=True
                    ),
                )

    def test_structural_reduction_error_is_not_mislabeled_as_value_reversal(self) -> None:
        with patch.object(
            teacher,
            "_build_subset_observation",
            side_effect=ValueError("synthetic structural category error"),
        ):
            result, path = self._execute(
                _completed_synthetic_evidence,
                "structural-reduction-error",
            )
        self.assertIsInstance(result, NonReplayTeacherExecutionFailed)
        assert isinstance(result, NonReplayTeacherExecutionFailed)
        self.assertEqual(
            NonReplayTeacherExecutionPhase.SEMANTIC_REDUCTION,
            result.phase,
        )
        self.assertEqual(1, result.failed_task_index)
        self.assertFalse(result.unreceipted_arm_invocation)
        self.assertEqual(2, len(result.durably_recorded_evidences))
        self.assertEqual(2, result.known_public_call_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertIn(
            "synthetic structural category error",
            result.exception_chain[0]["message"],
        )
        assert result.recovery is not None
        self.assertFalse(result.recovery.is_complete)
        self.assertEqual(path.read_bytes(), result.raw_journal_bytes)

    def test_invalid_owner_evidence_becomes_durable_unexpected_evidence(self) -> None:
        def owner(index: int, task: object):
            if index == 0:
                return _completed_synthetic_evidence(index, task)
            return synthetic_teacher_accepted_evidence(
                task_index=0,
                task=self.schedule.tasks[0],
                lower_chips=1.0,
                upper_chips=1.0,
            )

        result, _ = self._execute(owner, "invalid-owner")
        self.assertIsInstance(result, NonReplayTeacherJournalResult)
        assert isinstance(result, NonReplayTeacherJournalResult)
        self.assertEqual(
            NonReplayTeacherStopReason.UNEXPECTED_EXCEPTION,
            result.stop_reason,
        )
        self.assertIs(
            NonReplayTeacherEvidenceKind.UNEXPECTED_EXCEPTION,
            result.evidences[1].kind,
        )
        self.assertFalse(result.invocation_count_complete)

    def test_real_value_endpoint_requires_policy_and_dual_witnesses(self) -> None:
        task = self.schedule.tasks[0]
        synthetic = synthetic_teacher_accepted_evidence(
            task_index=0,
            task=task,
            lower_chips=1.0,
            upper_chips=1.0,
        )
        result_payload = dict(synthetic.core["result"])  # type: ignore[arg-type]
        result_payload["synthetic_result"] = False
        fabricated = teacher._build_evidence(
            task_index=0,
            task=task,
            kind=NonReplayTeacherEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=result_payload,
        )
        with self.assertRaisesRegex(ValueError, "behavioral witness|dual certificate"):
            teacher._validate_evidence_against_task(
                fabricated,
                task=task,
                expect_synthetic=False,
            )

    def test_representative_prefixes_and_torn_tail_rebind_without_solving(self) -> None:
        lines = self.completed_raw.splitlines(keepends=True)
        with (
            patch.object(
                teacher,
                "verify_adr0335_teacher_source_and_dependencies",
                return_value=self.source_sha256,
            ),
            patch.object(
                teacher,
                "build_adr0331_nonreplay_pool",
                return_value=self.pool,
            ),
            patch.object(
                teacher,
                "build_adr0334_nonreplay_exhaustive_teacher_schedule",
                return_value=self.schedule,
            ),
            patch.object(
                teacher,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_consumer,
            ),
        ):
            for count in (0, 1, 2, len(lines) // 2, len(lines) - 1):
                raw = b"".join(lines[:count])
                rebound = rebind_adr0335_teacher_journal(raw, synthetic=True)
                self.assertIsInstance(rebound, NonReplayTeacherJournalPrefix)
                assert isinstance(rebound, NonReplayTeacherJournalPrefix)
                self.assertEqual(max(0, count - 1), len(rebound.evidences))
            prior = lines[0]
            torn = lines[1][: len(lines[1]) // 2]
            rebound = rebind_adr0335_teacher_journal(
                prior + torn,
                synthetic=True,
            )
            self.assertIsInstance(rebound, NonReplayTeacherJournalPrefix)
            assert isinstance(rebound, NonReplayTeacherJournalPrefix)
            self.assertEqual(prior, rebound.recovery.verified_prefix_bytes)
            self.assertEqual(torn, rebound.recovery.invalid_suffix_bytes)

    def test_receipt_precedes_the_next_arm_and_append_failure_is_phase_typed(self) -> None:
        observed_record_counts: list[int] = []

        def rejecting_owner(index: int, task: object):
            path = Path(self.temporary.name) / "receipt.jsonl"
            recovery = recover_journal_file(
                path,
                expected_protocol_sha256=ADR0335_TEACHER_PROTOCOL_SHA256,
            )
            observed_record_counts.append(len(recovery.records))
            if index == 1:
                return synthetic_teacher_rejected_evidence(
                    task_index=index,
                    task=task,  # type: ignore[arg-type]
                )
            return _completed_synthetic_evidence(index, task)

        result, _ = self._execute(rejecting_owner, "receipt")
        self.assertIsInstance(result, NonReplayTeacherJournalResult)
        self.assertEqual([1, 2], observed_record_counts)

        original_append = teacher.DurableEvidenceJournalWriter.append
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "append-failure.jsonl"

            def fail_second_observation(writer: object, **kwargs: object):
                if (
                    kwargs["kind"] is JournalRecordKind.OBSERVATION
                    and writer.next_sequence == 2  # type: ignore[attr-defined]
                ):
                    raise OSError("injected observation append failure")
                return original_append(writer, **kwargs)  # type: ignore[arg-type]

            with patch.object(
                teacher.DurableEvidenceJournalWriter,
                "append",
                new=fail_second_observation,
            ):
                failure = teacher._execute_teacher(
                    output_path=path,
                    pool=self.pool,
                    schedule=self.schedule,
                    teacher_source_sha256=self.source_sha256,
                    arm_owner=_completed_synthetic_evidence,
                    synthetic=True,
                )
        self.assertIsInstance(failure, NonReplayTeacherExecutionFailed)
        assert isinstance(failure, NonReplayTeacherExecutionFailed)
        self.assertEqual(
            NonReplayTeacherExecutionPhase.OBSERVATION_APPEND,
            failure.phase,
        )
        self.assertTrue(failure.unreceipted_arm_invocation)
        self.assertEqual(1, len(failure.durably_recorded_evidences))
        self.assertFalse(failure.invocation_count_complete)

    def test_public_runner_preflight_and_exclusive_create_never_call_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prospective.jsonl"
            with (
                patch.object(teacher, "_artifact_path", return_value=path),
                patch.object(
                    teacher,
                    "verify_adr0335_teacher_source_and_dependencies",
                    side_effect=RuntimeError("source drift"),
                ),
                patch.object(
                    teacher,
                    "consume_certified_reduced_sizing_v2",
                    side_effect=_forbidden_consumer,
                ),
            ):
                rejected = run_and_retain_adr0334_nonreplay_exhaustive_teacher()
            self.assertIsInstance(rejected, NonReplayTeacherLaunchRejected)
            self.assertFalse(path.exists())

            path.write_bytes(b"do-not-clobber")
            with (
                patch.object(teacher, "_artifact_path", return_value=path),
                patch.object(
                    teacher,
                    "verify_adr0335_teacher_source_and_dependencies",
                    return_value=self.source_sha256,
                ),
                patch.object(
                    teacher,
                    "verify_adr0334_nonreplay_qualification_result_artifact",
                    return_value=SimpleNamespace(
                        panel=SimpleNamespace(digest=self.schedule.panel_sha256)
                    ),
                ),
                patch.object(
                    teacher,
                    "build_adr0331_nonreplay_pool",
                    return_value=self.pool,
                ),
                patch.object(
                    teacher,
                    "build_adr0334_nonreplay_exhaustive_teacher_schedule",
                    return_value=self.schedule,
                ),
                patch.object(
                    teacher,
                    "consume_certified_reduced_sizing_v2",
                    side_effect=_forbidden_consumer,
                ),
            ):
                collision = run_and_retain_adr0334_nonreplay_exhaustive_teacher()
            self.assertIsInstance(collision, NonReplayTeacherLaunchRejected)
            self.assertEqual(b"do-not-clobber", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
