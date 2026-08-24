from __future__ import annotations

import ast
import tempfile
import unittest
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_transfer_confirmation as confirmation
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    parse_journal_record_line,
    recover_journal_bytes,
)
from pontius.fresh_action_width_transfer_confirmation import (
    ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH,
    ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT,
    ADR0342_TRANSFER_CONFIRMATION_COMPLETED_RECORD_COUNT,
    ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT,
    ADR0342_TRANSFER_CONFIRMATION_PROTOCOL,
    ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
    ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH,
    ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT,
    TransferConfirmationArmEvidence,
    TransferConfirmationEvidenceKind,
    TransferConfirmationExecutionFailed,
    TransferConfirmationExecutionPhase,
    TransferConfirmationFailureStage,
    TransferConfirmationJournalPrefix,
    TransferConfirmationJournalResult,
    TransferConfirmationStopReason,
    build_adr0342_transfer_confirmation_schedule,
    rebind_adr0342_transfer_confirmation_journal,
    synthetic_transfer_confirmation_accepted_evidence,
    synthetic_transfer_confirmation_rejected_evidence,
    verify_adr0342_transfer_confirmation_source_and_dependencies,
)
from pontius.fresh_action_width_transfer_confirmation_seal import (
    ADR0342_SYNTHETIC_CONTROL_IDENTITIES,
    ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH as SEALED_PATH,
    ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT as SEALED_CALL_COUNT,
    ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256,
    ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_transfer_qualification import (
    build_adr0340_transfer_qualification_schedule,
)
from pontius.fresh_action_width_transfer_qualification_result import (
    ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
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
                key: value for key, value in payload.items() if key != "evidence_sha256"
            }
            core["candidate_position"] = 99
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


class FreshActionWidthTransferConfirmationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = confirmation.build_adr0339_transfer_pool()
        cls.schedule = build_adr0342_transfer_confirmation_schedule()
        cls.source_sha256 = ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST[
            "fresh_action_width_transfer_confirmation.py"
        ]
        cls.temporary = tempfile.TemporaryDirectory()
        root = Path(cls.temporary.name)

        cls.receipt_prefix_counts: list[int] = []
        cls.confirmed_path = root / "confirmed.jsonl"

        def confirmed_owner(slot, task, transition):
            cls.receipt_prefix_counts.append(
                cls.confirmed_path.read_bytes().count(b"\n")
            )
            prior = cls.schedule.prior_references[slot.panel_position]
            return synthetic_transfer_confirmation_accepted_evidence(
                slot=slot,
                task=task,
                transition=transition,
                lower_chips=prior.full_value.lower_chips,
                upper_chips=prior.full_value.upper_chips,
            )

        with cls._runtime():
            cls.confirmed = confirmation._execute_transfer_confirmation(
                output_path=cls.confirmed_path,
                pool=cls.pool,
                schedule=cls.schedule,
                confirmation_source_sha256=cls.source_sha256,
                arm_owner=confirmed_owner,
                synthetic=True,
            )
        if not isinstance(cls.confirmed, TransferConfirmationJournalResult):
            raise AssertionError("synthetic confirmed control did not terminate")
        cls.confirmed_raw = cls.confirmed_path.read_bytes()

        rejected_evidences = tuple(
            cls._accepted_for_mode(slot, task, transition, confirmed=False)
            for slot, task, transition in zip(
                cls.schedule.call_slots,
                cls.schedule.candidate_tasks,
                cls.schedule.transitions,
                strict=True,
            )
        )
        cls.rejected_path = root / "rejected.jsonl"
        cls.rejected = cls._write_direct_terminal(
            cls.rejected_path,
            rejected_evidences,
        )
        cls.rejected_raw = cls.rejected_path.read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    @classmethod
    def _accepted_for_mode(cls, slot, task, transition, *, confirmed: bool):
        prior = cls.schedule.prior_references[slot.panel_position]
        interval = prior.full_value if confirmed else prior.baseline.value
        return synthetic_transfer_confirmation_accepted_evidence(
            slot=slot,
            task=task,
            transition=transition,
            lower_chips=interval.lower_chips,
            upper_chips=interval.upper_chips,
        )

    @classmethod
    @contextmanager
    def _runtime(cls):
        with (
            patch.object(
                confirmation,
                "verify_adr0342_transfer_confirmation_source_and_dependencies",
                return_value=cls.source_sha256,
            ),
            patch.object(
                confirmation,
                "build_adr0342_transfer_confirmation_schedule",
                return_value=cls.schedule,
            ),
        ):
            yield

    @classmethod
    def _write_direct_terminal(
        cls,
        path: Path,
        evidences: tuple[TransferConfirmationArmEvidence, ...],
    ) -> TransferConfirmationJournalResult:
        campaign = confirmation._campaign_sha256(
            schedule=cls.schedule,
            confirmation_source_sha256=cls.source_sha256,
            synthetic=True,
        )
        writer = DurableEvidenceJournalWriter.create(
            path=path,
            protocol_sha256=ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
            campaign_sha256=campaign,
        )
        header = confirmation._header_payload(
            schedule=cls.schedule,
            confirmation_source_sha256=cls.source_sha256,
            campaign_sha256=campaign,
            synthetic=True,
        )
        writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header["header_sha256"],
            payload=header,
        )
        receipt = None
        for evidence in evidences:
            receipt = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
        if receipt is None:
            raise AssertionError("direct terminal requires evidence")
        state = confirmation._derive_confirmation_state(
            evidences,
            schedule=cls.schedule,
        )
        terminal = confirmation._terminal_payload(
            state=state,
            schedule=cls.schedule,
            confirmation_source_sha256=cls.source_sha256,
            campaign_sha256=campaign,
            final_observation_line_sha256=receipt.line_sha256,
            synthetic=True,
        )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=terminal["terminal_sha256"],
            payload=terminal,
        )
        writer.close()
        with cls._runtime():
            rebound = rebind_adr0342_transfer_confirmation_journal(
                path.read_bytes(),
                synthetic=True,
            )
        if not isinstance(rebound, TransferConfirmationJournalResult):
            raise AssertionError("direct synthetic terminal did not rebind")
        return rebound

    def test_source_protocol_schedule_path_and_call_site_are_exact(self) -> None:
        root = Path(confirmation.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST), actual)
        self.assertEqual(
            self.source_sha256,
            verify_adr0342_transfer_confirmation_source_and_dependencies(),
        )
        self.assertEqual(SEALED_PROTOCOL, ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256,
            sha256(
                canonical_journal_json_bytes(
                    dict(ADR0342_TRANSFER_CONFIRMATION_PROTOCOL)
                )
            ).hexdigest(),
        )
        self.assertEqual(SEALED_PATH, ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH)
        self.assertEqual(
            SEALED_CALL_COUNT,
            ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT,
        )
        self.assertEqual(
            ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256,
            self.schedule.digest,
        )
        with self.assertRaises(TypeError):
            ADR0342_TRANSFER_CONFIRMATION_PROTOCOL["raise_width"] = 4  # type: ignore[index]

        source = Path(confirmation.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        call_names = tuple(
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        )
        self.assertEqual(1, call_names.count("consume_certified_reduced_sizing_v2"))
        for forbidden in (
            "run_and_retain_adr0331_nonreplay_qualification",
            "run_and_retain_adr0336_nonreplay_closed_finite_block_greedy",
            "run_adr0323_closed_finite_block_greedy_development",
            "run_and_retain_adr0339_transfer_qualification",
        ):
            self.assertNotIn(forbidden, source)
        prospective = root.parents[1] / ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
        self.assertFalse(prospective.exists())
        attributes = (root.parents[1] / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            f"/{ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH} -text",
            attributes,
        )

    def test_schedule_reuses_32_prior_arms_and_opens_only_126_candidates(self) -> None:
        self.assertEqual(3, ADR0342_TRANSFER_CONFIRMATION_TARGET_WIDTH.count)
        self.assertEqual(32, ADR0342_TRANSFER_CONFIRMATION_PRIOR_ARM_COUNT)
        self.assertEqual(142, ADR0342_TRANSFER_CONFIRMATION_TASK_COUNT)
        self.assertEqual(126, len(self.schedule.call_slots))
        self.assertEqual(126, len(self.schedule.candidate_tasks))
        self.assertEqual(126, len(self.schedule.transitions))
        self.assertEqual(
            [9, 7, 9, 7, 7, 7, 7, 9, 9, 9, 9, 7, 7, 9, 9, 5],
            [len(self.schedule.call_slots_for_context(i)) for i in range(16)],
        )
        qualification_schedule = build_adr0340_transfer_qualification_schedule()
        for prior in self.schedule.prior_references:
            context = self.pool.contexts[prior.pool_index]
            full = qualification_schedule.tasks[2 * prior.pool_index]
            width_two = qualification_schedule.tasks[2 * prior.pool_index + 1]
            self.assertEqual(full.digest, prior.full_qualification_task_sha256)
            self.assertEqual(
                width_two.digest,
                prior.baseline_qualification_task_sha256,
            )
            self.assertEqual(width_two.request, prior.baseline_task.request)
            self.assertEqual(context.payoff_span_chips, prior.payoff_span_chips)
            self.assertNotEqual(context.betting.stacks[0], prior.payoff_span_chips)
            self.assertEqual(
                ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
                prior.qualification_journal_sha256,
            )
            self.assertEqual(
                ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
                prior.qualification_terminal_sha256,
            )
            self.assertEqual(
                ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
                prior.qualification_panel_sha256,
            )
            outgoing = self.schedule.transitions_for_context(prior.panel_position)
            self.assertEqual(context.complete_raise_to_totals[1:-1], tuple(
                item.proposed_raise_to_total for item in outgoing
            ))
            for transition in outgoing:
                self.assertEqual(
                    set(transition.incumbent.response_row_set.rows)
                    | set(transition.own_block.response_rows),
                    set(transition.augmented.response_row_set.rows),
                )

    def test_confirmed_and_rejected_are_distinct_honest_full_panel_results(self) -> None:
        self.assertEqual(
            TransferConfirmationStopReason.COMPLETED_CONFIRMED,
            self.confirmed.stop_reason,
        )
        self.assertIs(True, self.confirmed.unrestricted_transfer_confirmed)
        self.assertTrue(self.confirmed.gate and self.confirmed.gate.passes)
        self.assertEqual(126, self.confirmed.known_public_call_count)
        self.assertEqual(126, len(self.confirmed.evidences))
        self.assertEqual(16, len(self.confirmed.contexts))
        self.assertEqual(
            ADR0342_TRANSFER_CONFIRMATION_COMPLETED_RECORD_COUNT,
            self.confirmed_raw.count(b"\n"),
        )
        self.assertEqual(
            tuple(range(1, 127)),
            tuple(self.receipt_prefix_counts),
        )

        self.assertEqual(
            TransferConfirmationStopReason.COMPLETED_REJECTED,
            self.rejected.stop_reason,
        )
        self.assertIs(False, self.rejected.unrestricted_transfer_confirmed)
        self.assertFalse(self.rejected.gate and self.rejected.gate.passes)
        assert self.rejected.gate is not None
        self.assertFalse(self.rejected.gate.maximum_full_regret_pass)
        self.assertFalse(self.rejected.gate.mean_full_regret_pass)
        self.assertFalse(self.rejected.gate.aggregate_recovery_pass)
        self.assertTrue(self.rejected.gate.maximum_teacher_excess_pass)
        self.assertTrue(self.rejected.gate.mean_teacher_excess_pass)
        self.assertEqual(126, self.rejected.known_public_call_count)
        self.assertEqual(128, self.rejected_raw.count(b"\n"))

        for result in (self.confirmed, self.rejected):
            for context in result.contexts:
                self.assertEqual(0, context.selected_candidate_position)
                self.assertEqual(
                    tuple(range(len(context.candidates))),
                    context.teacher.nondominated_subset_indices,
                )
                self.assertEqual(
                    tuple(range(len(context.candidates))),
                    context.teacher.equivalent_subset_indices,
                )

    def test_synthetic_terminal_identities_are_source_sealed(self) -> None:
        self.assertEqual(
            ADR0342_SYNTHETIC_CONTROL_IDENTITIES["confirmed"],
            (
                self.confirmed.journal_sha256,
                self.confirmed.terminal_sha256,
                len(self.confirmed_raw),
                self.confirmed_raw.count(b"\n"),
            ),
        )
        self.assertEqual(
            ADR0342_SYNTHETIC_CONTROL_IDENTITIES["rejected"],
            (
                self.rejected.journal_sha256,
                self.rejected.terminal_sha256,
                len(self.rejected_raw),
                self.rejected_raw.count(b"\n"),
            ),
        )

    def test_prefix_torn_tail_wrong_mode_and_semantic_corruption_fail_closed(self) -> None:
        lines = self.confirmed_raw.splitlines(keepends=True)
        with self._runtime():
            for count in (0, 1, 2, len(lines) // 2, len(lines) - 1):
                raw = b"".join(lines[:count])
                rebound = rebind_adr0342_transfer_confirmation_journal(
                    raw,
                    synthetic=True,
                )
                self.assertIsInstance(rebound, TransferConfirmationJournalPrefix)
                assert isinstance(rebound, TransferConfirmationJournalPrefix)
                self.assertEqual(raw, rebound.recovery.raw_bytes)
            torn = b"".join(lines[:5]) + lines[5][: len(lines[5]) // 2]
            rebound = rebind_adr0342_transfer_confirmation_journal(
                torn,
                synthetic=True,
            )
            self.assertIsInstance(rebound, TransferConfirmationJournalPrefix)
            assert isinstance(rebound, TransferConfirmationJournalPrefix)
            self.assertTrue(rebound.recovery.invalid_suffix_bytes)
            with self.assertRaises(ValueError):
                rebind_adr0342_transfer_confirmation_journal(
                    self.confirmed_raw,
                    synthetic=False,
                )
            corrupted = _fully_rehash_with_semantic_corruption(self.confirmed_raw)
            self.assertTrue(recover_journal_bytes(corrupted).is_complete)
            with self.assertRaisesRegex(ValueError, "call slot|invocation|metadata"):
                rebind_adr0342_transfer_confirmation_journal(
                    corrupted,
                    synthetic=True,
                )

    def test_rejection_unexpected_and_numerical_stops_are_distinct(self) -> None:
        def run(name, owner):
            path = Path(self.temporary.name) / f"short-{name}.jsonl"
            with self._runtime():
                result = confirmation._execute_transfer_confirmation(
                    output_path=path,
                    pool=self.pool,
                    schedule=self.schedule,
                    confirmation_source_sha256=self.source_sha256,
                    arm_owner=owner,
                    synthetic=True,
                )
            self.assertIsInstance(result, TransferConfirmationJournalResult)
            assert isinstance(result, TransferConfirmationJournalResult)
            return result

        rejected = run(
            "rejected",
            lambda slot, task, transition: (
                synthetic_transfer_confirmation_rejected_evidence(
                    slot=slot,
                    task=task,
                    transition=transition,
                )
            ),
        )
        self.assertEqual(
            TransferConfirmationStopReason.CONSUMER_REJECTED,
            rejected.stop_reason,
        )
        self.assertEqual(1, rejected.known_public_call_count)
        self.assertTrue(rejected.invocation_count_complete)

        def raise_owner(*_):
            raise RuntimeError("synthetic unreceipted owner failure")

        unexpected = run("unexpected", raise_owner)
        self.assertEqual(
            TransferConfirmationStopReason.UNEXPECTED_EXCEPTION,
            unexpected.stop_reason,
        )
        self.assertEqual(0, unexpected.known_public_call_count)
        self.assertFalse(unexpected.invocation_count_complete)

        def excessive(slot, task, transition):
            prior = self.schedule.prior_references[slot.panel_position]
            return synthetic_transfer_confirmation_accepted_evidence(
                slot=slot,
                task=task,
                transition=transition,
                lower_chips=prior.full_value.upper_chips + 1.0,
                upper_chips=prior.full_value.upper_chips + 1.0,
            )

        numerical = run("numerical", excessive)
        self.assertEqual(
            TransferConfirmationStopReason.NUMERICAL_REJECTED,
            numerical.stop_reason,
        )
        self.assertEqual(
            TransferConfirmationFailureStage.CONTEXT_REDUCTION,
            numerical.failure_stage,
        )
        self.assertEqual(9, numerical.known_public_call_count)

    def test_observation_append_failure_and_no_clobber_preserve_authority(self) -> None:
        original_append = confirmation.DurableEvidenceJournalWriter.append
        path = Path(self.temporary.name) / "append-failure.jsonl"

        def fail_second_observation(writer, **kwargs):
            if (
                kwargs["kind"] is JournalRecordKind.OBSERVATION
                and writer.next_sequence == 2
            ):
                raise OSError("injected confirmation append failure")
            return original_append(writer, **kwargs)

        def owner(slot, task, transition):
            return self._accepted_for_mode(
                slot,
                task,
                transition,
                confirmed=True,
            )

        with (
            self._runtime(),
            patch.object(
                confirmation.DurableEvidenceJournalWriter,
                "append",
                new=fail_second_observation,
            ),
        ):
            failure = confirmation._execute_transfer_confirmation(
                output_path=path,
                pool=self.pool,
                schedule=self.schedule,
                confirmation_source_sha256=self.source_sha256,
                arm_owner=owner,
                synthetic=True,
            )
        self.assertIsInstance(failure, TransferConfirmationExecutionFailed)
        assert isinstance(failure, TransferConfirmationExecutionFailed)
        self.assertEqual(
            TransferConfirmationExecutionPhase.OBSERVATION_APPEND,
            failure.phase,
        )
        self.assertEqual(1, failure.failed_call_index)
        self.assertTrue(failure.unreceipted_arm_invocation)
        self.assertEqual(1, len(failure.durably_recorded_evidences))
        self.assertEqual(1, failure.known_public_call_count)
        self.assertFalse(failure.invocation_count_complete)

        existing = Path(self.temporary.name) / "existing.jsonl"
        original = b"never clobber\n"
        existing.write_bytes(original)
        calls = 0

        def counted_owner(*args):
            nonlocal calls
            calls += 1
            return owner(*args)

        with self.assertRaises(FileExistsError):
            confirmation._execute_transfer_confirmation(
                output_path=existing,
                pool=self.pool,
                schedule=self.schedule,
                confirmation_source_sha256=self.source_sha256,
                arm_owner=counted_owner,
                synthetic=True,
            )
        self.assertEqual(0, calls)
        self.assertEqual(original, existing.read_bytes())

    def test_fabricated_real_evidence_requires_policy_and_dual_rebinding(self) -> None:
        slot = self.schedule.call_slots[0]
        task = self.schedule.candidate_tasks[0]
        transition = self.schedule.transitions[0]
        synthetic = self._accepted_for_mode(
            slot,
            task,
            transition,
            confirmed=True,
        )
        result = dict(synthetic.core["result"])
        result["synthetic_result"] = False
        fabricated = confirmation._build_evidence(
            slot=slot,
            task=task,
            transition=transition,
            kind=TransferConfirmationEvidenceKind.ACCEPTED,
            synthetic=False,
            result_payload=result,
        )
        with self.assertRaisesRegex(ValueError, "behavioral witness|dual certificate"):
            confirmation._validate_evidence_against_invocation(
                fabricated,
                slot=slot,
                task=task,
                transition=transition,
                expect_synthetic=False,
            )


if __name__ == "__main__":
    unittest.main()
