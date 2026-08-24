from __future__ import annotations

import ast
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_nonreplay_greedy as greedy
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius.fresh_action_width_greedy import (
    ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
)
from pontius.fresh_action_width_nonreplay import build_adr0331_nonreplay_pool
from pontius.fresh_action_width_nonreplay_greedy import (
    ADR0337_GREEDY_ARM_COUNT,
    ADR0337_GREEDY_CALL_COUNT,
    ADR0337_GREEDY_COMPLETED_RECORD_COUNT,
    ADR0337_GREEDY_PROTOCOL,
    ADR0337_GREEDY_PROTOCOL_SHA256,
    ADR0337_GREEDY_TRANSITION_COUNT,
    NonReplayGreedyEvidenceKind,
    NonReplayGreedyExecutionFailed,
    NonReplayGreedyExecutionPhase,
    NonReplayGreedyJournalPrefix,
    NonReplayGreedyJournalResult,
    NonReplayGreedyStopReason,
    build_adr0336_nonreplay_closed_finite_block_schedule,
    rebind_adr0337_greedy_journal,
    synthetic_greedy_accepted_evidence,
    synthetic_greedy_rejected_evidence,
    verify_adr0337_greedy_source_and_dependencies,
)
from pontius.fresh_action_width_nonreplay_greedy_seal import (
    ADR0337_GREEDY_ARM_COUNT as SEALED_ARM_COUNT,
    ADR0337_GREEDY_CALL_COUNT as SEALED_CALL_COUNT,
    ADR0337_GREEDY_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0337_GREEDY_SCHEDULE_SHA256,
    ADR0337_GREEDY_SOURCE_MANIFEST,
    ADR0337_GREEDY_TRANSITION_COUNT as SEALED_TRANSITION_COUNT,
    ADR0337_SYNTHETIC_COMPLETED_CONTROL,
)
from pontius.fresh_action_width_nonreplay_teacher_result import (
    verify_adr0336_nonreplay_teacher_result_artifact,
)


def _forbidden_consumer(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("source-only greedy validation may not invoke its consumer")


def _synthetic_success(slot: object, task: object, transition: object):
    value = 0.0 if task.raise_width.count == 2 else 100.0  # type: ignore[attr-defined]
    return synthetic_greedy_accepted_evidence(
        slot=slot,  # type: ignore[arg-type]
        task=task,  # type: ignore[arg-type]
        transition=transition,  # type: ignore[arg-type]
        lower_chips=value,
        upper_chips=value,
    )


class FreshActionWidthNonReplayGreedyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_sha256, cls.schedule = (
            greedy._preflight_adr0337_greedy_source_and_schedule()
        )
        cls.pool = build_adr0331_nonreplay_pool()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.completed_path = Path(cls.temporary.name) / "completed.jsonl"
        with (
            patch.object(
                greedy,
                "_preflight_adr0337_greedy_source_and_schedule",
                return_value=(cls.source_sha256, cls.schedule),
            ),
            patch.object(
                greedy,
                "build_adr0331_nonreplay_pool",
                return_value=cls.pool,
            ),
            patch.object(
                greedy,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_consumer,
            ),
        ):
            cls.completed_result = greedy._execute_greedy(
                output_path=cls.completed_path,
                pool=cls.pool,
                schedule=cls.schedule,
                greedy_source_sha256=cls.source_sha256,
                teacher_result=None,
                arm_owner=_synthetic_success,
                synthetic=True,
            )
        cls.completed_raw = cls.completed_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def _patched_rebind(self, raw: bytes):
        with (
            patch.object(
                greedy,
                "_preflight_adr0337_greedy_source_and_schedule",
                return_value=(self.source_sha256, self.schedule),
            ),
            patch.object(
                greedy,
                "build_adr0331_nonreplay_pool",
                return_value=self.pool,
            ),
            patch.object(
                greedy,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_consumer,
            ),
        ):
            return rebind_adr0337_greedy_journal(raw, synthetic=True)

    def _execute(self, owner: object, name: str):
        path = Path(self.temporary.name) / f"{name}.jsonl"
        with (
            patch.object(
                greedy,
                "_preflight_adr0337_greedy_source_and_schedule",
                return_value=(self.source_sha256, self.schedule),
            ),
            patch.object(
                greedy,
                "build_adr0331_nonreplay_pool",
                return_value=self.pool,
            ),
        ):
            result = greedy._execute_greedy(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                greedy_source_sha256=self.source_sha256,
                teacher_result=None,
                arm_owner=owner,  # type: ignore[arg-type]
                synthetic=True,
            )
        return result, path

    def test_source_protocol_schedule_and_closed_import_boundary_are_exact(self) -> None:
        root = Path(greedy.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0337_GREEDY_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0337_GREEDY_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_nonreplay_greedy.py"],
            verify_adr0337_greedy_source_and_dependencies(),
        )
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0337_GREEDY_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0337_GREEDY_PROTOCOL_SHA256,
            sha256(
                canonical_journal_json_bytes(dict(ADR0337_GREEDY_PROTOCOL))
            ).hexdigest(),
        )
        self.assertEqual(ADR0337_GREEDY_SCHEDULE_SHA256, self.schedule.digest)
        self.assertEqual(SEALED_ARM_COUNT, ADR0337_GREEDY_ARM_COUNT)
        self.assertEqual(SEALED_TRANSITION_COUNT, ADR0337_GREEDY_TRANSITION_COUNT)
        self.assertEqual(SEALED_CALL_COUNT, ADR0337_GREEDY_CALL_COUNT)

        tree = ast.parse(Path(greedy.__file__).read_text(encoding="utf-8"))
        forbidden = {
            "run_adr0323_closed_finite_block_greedy_development",
            "run_and_retain_adr0323_closed_finite_block_greedy_development",
            "_execute_adr0323_closed_finite_block_greedy_development",
        }
        names: set[str] = set()
        attributes: set[str] = set()
        consumer_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
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
        self.assertTrue(forbidden.isdisjoint(names | attributes))
        self.assertTrue(
            {"BettingAction", "PreparationBank", "Transfer"}.isdisjoint(names)
        )
        self.assertNotIn("apply_action", attributes)
        self.assertEqual(1, consumer_calls)
        with self.assertRaises(TypeError):
            ADR0337_GREEDY_PROTOCOL["call_count"] = 1  # type: ignore[index]

    def test_graph_call_slots_and_response_closure_are_exact_and_solver_free(self) -> None:
        with patch.object(
            greedy,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            schedule = build_adr0336_nonreplay_closed_finite_block_schedule()
        self.assertEqual(2_097, len(schedule.tasks))
        self.assertEqual(6_543, len(schedule.transitions))
        self.assertEqual(376, len(schedule.call_slots))
        self.assertEqual(
            {7: 4, 9: 7, 11: 5},
            dict(Counter(
                len(schedule.complete_raise_to_totals(position))
                for position in range(16)
            )),
        )
        self.assertEqual(
            tuple(range(376)),
            tuple(slot.call_index for slot in schedule.call_slots),
        )
        for task in schedule.tasks:
            self.assertEqual(
                2 * 4 * task.raise_width.count,
                len(task.response_row_set.rows),
            )
        for transition in schedule.transitions:
            incumbent_rows = {
                item.digest for item in transition.incumbent.response_row_set.rows
            }
            own_rows = {item.digest for item in transition.own_block.response_rows}
            augmented_rows = {
                item.digest for item in transition.augmented.response_row_set.rows
            }
            self.assertTrue(incumbent_rows.isdisjoint(own_rows))
            self.assertEqual(incumbent_rows | own_rows, augmented_rows)

    def test_complete_solver_free_journal_matches_sealed_control(self) -> None:
        result = self.completed_result
        self.assertIsInstance(result, NonReplayGreedyJournalResult)
        assert isinstance(result, NonReplayGreedyJournalResult)
        self.assertEqual(
            NonReplayGreedyStopReason.COMPLETED_SELECTED,
            result.stop_reason,
        )
        self.assertEqual(3, result.selected_raise_width.count)  # type: ignore[union-attr]
        self.assertEqual(376, len(result.evidences))
        self.assertEqual(16, len(result.contexts))
        self.assertEqual(376, result.known_public_call_count)
        self.assertTrue(result.invocation_count_complete)
        self.assertEqual(
            dict(ADR0337_SYNTHETIC_COMPLETED_CONTROL),
            {
                "all_five_gates_pass": all(item.passes for item in result.width_gates),
                "campaign_sha256": result.campaign_sha256,
                "context_count": len(result.contexts),
                "evidence_count": len(result.evidences),
                "journal_byte_count": result.journal_byte_count,
                "journal_sha256": result.journal_sha256,
                "public_call_count": result.known_public_call_count,
                "record_count": len(result.evidences) + 2,
                "selected_raise_width": result.selected_raise_width.count,  # type: ignore[union-attr]
                "terminal_sha256": result.terminal_sha256,
            },
        )
        recovery = recover_journal_bytes(self.completed_raw)
        self.assertTrue(recovery.is_complete)
        self.assertEqual(ADR0337_GREEDY_COMPLETED_RECORD_COUNT, len(recovery.records))
        self.assertIs(JournalRecordKind.HEADER, recovery.records[0].body.kind)
        self.assertIs(JournalRecordKind.TERMINAL, recovery.records[-1].body.kind)

    def test_ties_select_smaller_raise_and_all_five_nominal_gates_recompute(self) -> None:
        result = self.completed_result
        assert isinstance(result, NonReplayGreedyJournalResult)
        for context in result.contexts:
            for round_result in context.rounds:
                proposed = tuple(
                    item.transition.proposed_raise_to_total.chips
                    for item in round_result.candidates
                )
                self.assertEqual(min(proposed), round_result.selected.transition.proposed_raise_to_total.chips)
                self.assertTrue(all(
                    item.augmented.feasible_behavioral_lower_bound_chips
                    == round_result.selected.augmented.feasible_behavioral_lower_bound_chips
                    for item in round_result.candidates
                ))
        self.assertEqual(
            result.width_gates,
            tuple(
                greedy._build_width_gate_result(
                    raise_width=width,
                    contexts=result.contexts,
                )
                for width in greedy.ADR0323_RAISE_WIDTHS[1:]
            ),
        )
        gate_limits = (
            ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
            ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
            ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
            ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
            ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
        )
        self.assertEqual(5, len({type(item) for item in gate_limits}))
        self.assertTrue(all(item.passes for item in result.width_gates))

    def test_real_teacher_counterpart_rebind_is_exact_without_a_consumer(self) -> None:
        with patch.object(
            greedy,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            retained = verify_adr0336_nonreplay_teacher_result_artifact()
            for panel_position in (0, 9, 15):
                task = next(
                    item
                    for item in self.schedule.tasks_for_context(panel_position)
                    if item.raise_width.count == 3 and item.subset_index == 0
                )
                reference = greedy._teacher_reference_for_selected(
                    selected_task=task,
                    teacher_result=retained,
                    synthetic=False,
                )
                reference.verify_selected_task(task)
                self.assertEqual(
                    task.request.betting.pot + 2 * task.request.betting.stacks[0],
                    reference.payoff_span_chips,
                )

    def test_representative_prefix_and_torn_tail_preserve_exact_suffix(self) -> None:
        recovery = recover_journal_bytes(self.completed_raw)
        for record_count in (0, 1, 2, 19):
            raw = b"".join(
                record.line_bytes for record in recovery.records[:record_count]
            )
            rebound = self._patched_rebind(raw)
            self.assertIsInstance(rebound, NonReplayGreedyJournalPrefix)
            assert isinstance(rebound, NonReplayGreedyJournalPrefix)
            expected_evidence = max(0, record_count - 1)
            self.assertEqual(expected_evidence, len(rebound.evidences))
        prior = b"".join(record.line_bytes for record in recovery.records[:19])
        raw = prior + b'{"torn":'
        rebound = self._patched_rebind(raw)
        self.assertIsInstance(rebound, NonReplayGreedyJournalPrefix)
        assert isinstance(rebound, NonReplayGreedyJournalPrefix)
        self.assertEqual(prior, rebound.recovery.verified_prefix_bytes)
        self.assertEqual(b'{"torn":', rebound.recovery.invalid_suffix_bytes)

    def test_rejection_and_unexpected_exception_stop_without_a_next_call(self) -> None:
        calls: list[int] = []

        def rejecting_owner(slot: object, task: object, transition: object):
            calls.append(slot.call_index)  # type: ignore[attr-defined]
            if slot.call_index == 1:  # type: ignore[attr-defined]
                return synthetic_greedy_rejected_evidence(
                    slot=slot,  # type: ignore[arg-type]
                    task=task,  # type: ignore[arg-type]
                    transition=transition,  # type: ignore[arg-type]
                )
            return _synthetic_success(slot, task, transition)

        rejected, rejected_path = self._execute(rejecting_owner, "rejected")
        self.assertIsInstance(rejected, NonReplayGreedyJournalResult)
        assert isinstance(rejected, NonReplayGreedyJournalResult)
        self.assertEqual([0, 1], calls)
        self.assertEqual(
            NonReplayGreedyStopReason.CONSUMER_REJECTED,
            rejected.stop_reason,
        )
        self.assertEqual(2, rejected.known_public_call_count)
        self.assertEqual(4, len(recover_journal_bytes(rejected_path.read_bytes()).records))

        calls.clear()

        def exploding_owner(slot: object, task: object, transition: object):
            del task, transition
            calls.append(slot.call_index)  # type: ignore[attr-defined]
            raise RuntimeError("synthetic owner failure")

        unexpected, unexpected_path = self._execute(exploding_owner, "unexpected")
        self.assertIsInstance(unexpected, NonReplayGreedyJournalResult)
        assert isinstance(unexpected, NonReplayGreedyJournalResult)
        self.assertEqual([0], calls)
        self.assertEqual(
            NonReplayGreedyStopReason.UNEXPECTED_EXCEPTION,
            unexpected.stop_reason,
        )
        self.assertFalse(unexpected.invocation_count_complete)
        self.assertEqual(0, unexpected.known_public_call_count)
        self.assertEqual(3, len(recover_journal_bytes(unexpected_path.read_bytes()).records))

        calls.clear()

        def reversing_owner(slot: object, task: object, transition: object):
            calls.append(slot.call_index)  # type: ignore[attr-defined]
            value = 0.0 if task.raise_width.count == 2 else 200.0  # type: ignore[attr-defined]
            return synthetic_greedy_accepted_evidence(
                slot=slot,  # type: ignore[arg-type]
                task=task,  # type: ignore[arg-type]
                transition=transition,  # type: ignore[arg-type]
                lower_chips=value,
                upper_chips=value,
            )

        numerical, _ = self._execute(reversing_owner, "numerical")
        self.assertIsInstance(numerical, NonReplayGreedyJournalResult)
        assert isinstance(numerical, NonReplayGreedyJournalResult)
        self.assertEqual(list(range(6)), calls)
        self.assertEqual(
            NonReplayGreedyStopReason.NUMERICAL_REJECTED,
            numerical.stop_reason,
        )
        self.assertIs(
            greedy.NonReplayGreedyFailureStage.ROUND_REDUCTION,
            numerical.failure_stage,
        )
        self.assertTrue(numerical.failure_exception_chain)

    def test_receipt_authority_append_failure_and_same_count_drift_are_typed(self) -> None:
        observed_record_counts: list[int] = []

        def receipt_owner(slot: object, task: object, transition: object):
            recovery = recover_journal_bytes(receipt_path.read_bytes())
            observed_record_counts.append(len(recovery.records))
            if slot.call_index == 1:  # type: ignore[attr-defined]
                return synthetic_greedy_rejected_evidence(
                    slot=slot,  # type: ignore[arg-type]
                    task=task,  # type: ignore[arg-type]
                    transition=transition,  # type: ignore[arg-type]
                )
            return _synthetic_success(slot, task, transition)

        receipt_path = Path(self.temporary.name) / "receipt.jsonl"
        result, _ = self._execute(receipt_owner, "receipt")
        self.assertIsInstance(result, NonReplayGreedyJournalResult)
        self.assertEqual([1, 2], observed_record_counts)

        original_append = greedy.DurableEvidenceJournalWriter.append

        def failing_append(writer: object, **kwargs: object):
            if kwargs.get("kind") is JournalRecordKind.OBSERVATION:
                raise OSError("injected observation append failure")
            return original_append(writer, **kwargs)  # type: ignore[arg-type]

        with patch.object(
            greedy.DurableEvidenceJournalWriter,
            "append",
            new=failing_append,
        ):
            failure, _ = self._execute(_synthetic_success, "append-failure")
        self.assertIsInstance(failure, NonReplayGreedyExecutionFailed)
        assert isinstance(failure, NonReplayGreedyExecutionFailed)
        self.assertIs(
            NonReplayGreedyExecutionPhase.OBSERVATION_APPEND,
            failure.phase,
        )
        self.assertTrue(failure.unreceipted_arm_invocation)
        self.assertEqual((), failure.durably_recorded_evidences)

        slots = list(self.schedule.call_slots)
        slots[1], slots[2] = slots[2], slots[1]
        with self.assertRaises(ValueError):
            replace(self.schedule, call_slots=tuple(slots))


if __name__ == "__main__":
    unittest.main()
