from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from pontius.fresh_action_width_transfer_confirmation import (
    TransferConfirmationEvidenceKind,
    TransferConfirmationStopReason,
)
from pontius.fresh_action_width_transfer_confirmation_result import (
    ADR0343_ACHIEVED_GAIN_LOWER_CHIPS_HEX,
    ADR0343_ACHIEVED_GAIN_UPPER_CHIPS_HEX,
    ADR0343_AGGREGATE_RECOVERY_LOWER_HEX,
    ADR0343_AGGREGATE_RECOVERY_UPPER_HEX,
    ADR0343_AVAILABLE_GAIN_LOWER_CHIPS_HEX,
    ADR0343_AVAILABLE_GAIN_UPPER_CHIPS_HEX,
    ADR0343_CONTEXT_CANDIDATE_COUNTS,
    ADR0343_CONTEXT_RESULT_SHA256S,
    ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS,
    ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS,
    ADR0343_MAX_CERTIFICATE_GAP_HEX,
    ADR0343_MAXIMUM_NORMALIZED_FULL_REGRET_UPPER_HEX,
    ADR0343_MAXIMUM_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
    ADR0343_MEAN_NORMALIZED_FULL_REGRET_LOWER_HEX,
    ADR0343_MEAN_NORMALIZED_FULL_REGRET_UPPER_HEX,
    ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_LOWER_HEX,
    ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
    ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES,
    ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256,
    ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256,
    ADR0343_TRANSFER_CONFIRMATION_CONTEXT_COUNT,
    ADR0343_TRANSFER_CONFIRMATION_EVIDENCE_COUNT,
    ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256,
    ADR0343_TRANSFER_CONFIRMATION_PUBLIC_CALL_COUNT,
    ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT,
    ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256,
    ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256,
    RetainedTransferConfirmationResult,
    verify_adr0343_transfer_confirmation_result_artifact,
    verify_adr0343_transfer_result_source_and_dependencies,
)
from pontius.fresh_action_width_transfer_confirmation_result_seal import (
    ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0343_TRANSFER_CONFIRMATION_RESULT_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_transfer_qualification_result import (
    ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT / "experiments/results/fresh-action-width-transfer-confirmation-v1.jsonl"
)
_SOURCE = (
    _ROOT / "src/pontius/fresh_action_width_transfer_confirmation_result.py"
)


def _forbidden(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("closed solver-bearing confirmation owner was reached")


class FreshActionWidthTransferConfirmationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_adr0343_transfer_confirmation_result_artifact()

    def test_source_closure_and_result_protocol_are_sealed(self) -> None:
        self.assertEqual(
            ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256,
            SEALED_PROTOCOL,
        )
        self.assertEqual(
            verify_adr0343_transfer_result_source_and_dependencies(),
            ADR0343_TRANSFER_CONFIRMATION_RESULT_SOURCE_MANIFEST[
                "fresh_action_width_transfer_confirmation_result.py"
            ],
        )

    def test_exact_journal_rebinds_without_runner_consumer_solver_or_writer(self) -> None:
        with (
            patch(
                "pontius.fresh_action_width_transfer_confirmation."
                "run_and_retain_adr0341_transfer_confirmation",
                side_effect=_forbidden,
            ),
            patch(
                "pontius.fresh_action_width_transfer_confirmation."
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden,
            ),
            patch(
                "pontius.fresh_action_width_transfer_confirmation."
                "DurableEvidenceJournalWriter",
                side_effect=_forbidden,
            ),
            patch("scipy.optimize.linprog", side_effect=_forbidden),
        ):
            result = verify_adr0343_transfer_confirmation_result_artifact()

        journal = result.journal
        self.assertEqual(
            journal.stop_reason,
            TransferConfirmationStopReason.COMPLETED_CONFIRMED,
        )
        self.assertIs(journal.unrestricted_transfer_confirmed, True)
        self.assertEqual(
            journal.campaign_sha256,
            ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256,
        )
        self.assertEqual(
            journal.terminal_sha256,
            ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256,
        )
        self.assertEqual(
            len(journal.evidences),
            ADR0343_TRANSFER_CONFIRMATION_EVIDENCE_COUNT,
        )
        self.assertEqual(
            len(journal.contexts),
            ADR0343_TRANSFER_CONFIRMATION_CONTEXT_COUNT,
        )
        self.assertEqual(
            journal.known_public_call_count,
            ADR0343_TRANSFER_CONFIRMATION_PUBLIC_CALL_COUNT,
        )
        self.assertTrue(journal.invocation_count_complete)
        self.assertFalse(journal.synthetic)
        self.assertIsNone(journal.failure_stage)
        self.assertFalse(journal.failure_exception_chain)
        self.assertTrue(
            all(
                evidence.kind is TransferConfirmationEvidenceKind.ACCEPTED
                and evidence.public_call_count == 1
                and evidence.invocation_count_complete
                and not evidence.synthetic
                for evidence in journal.evidences
            )
        )

    def test_retained_bytes_and_record_count_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256,
        )
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"), ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT)

    def test_all_five_transfer_conjuncts_pass_with_exact_diagnostics(self) -> None:
        gate = self.result.journal.gate
        self.assertIsNotNone(gate)
        assert gate is not None
        self.assertTrue(gate.passes)
        self.assertEqual(gate.digest, ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256)
        self.assertEqual(
            gate.maximum_normalized_full_regret_upper.hex(),
            ADR0343_MAXIMUM_NORMALIZED_FULL_REGRET_UPPER_HEX,
        )
        self.assertEqual(
            gate.mean_normalized_full_regret_lower.hex(),
            ADR0343_MEAN_NORMALIZED_FULL_REGRET_LOWER_HEX,
        )
        self.assertEqual(
            gate.mean_normalized_full_regret_upper.hex(),
            ADR0343_MEAN_NORMALIZED_FULL_REGRET_UPPER_HEX,
        )
        recovery = gate.aggregate_recovery
        self.assertEqual(recovery.lower.hex(), ADR0343_AGGREGATE_RECOVERY_LOWER_HEX)
        self.assertEqual(recovery.upper.hex(), ADR0343_AGGREGATE_RECOVERY_UPPER_HEX)
        self.assertEqual(
            recovery.achieved_gain_lower_chips.hex(),
            ADR0343_ACHIEVED_GAIN_LOWER_CHIPS_HEX,
        )
        self.assertEqual(
            recovery.achieved_gain_upper_chips.hex(),
            ADR0343_ACHIEVED_GAIN_UPPER_CHIPS_HEX,
        )
        self.assertEqual(
            recovery.available_gain_lower_chips.hex(),
            ADR0343_AVAILABLE_GAIN_LOWER_CHIPS_HEX,
        )
        self.assertEqual(
            recovery.available_gain_upper_chips.hex(),
            ADR0343_AVAILABLE_GAIN_UPPER_CHIPS_HEX,
        )
        self.assertEqual(
            gate.maximum_normalized_teacher_excess_upper.hex(),
            ADR0343_MAXIMUM_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
        )
        self.assertEqual(
            gate.mean_normalized_teacher_excess_lower.hex(),
            ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_LOWER_HEX,
        )
        self.assertEqual(
            gate.mean_normalized_teacher_excess_upper.hex(),
            ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
        )
        self.assertTrue(gate.maximum_full_regret_pass)
        self.assertTrue(gate.mean_full_regret_pass)
        self.assertTrue(gate.aggregate_recovery_pass)
        self.assertTrue(gate.maximum_teacher_excess_pass)
        self.assertTrue(gate.mean_teacher_excess_pass)
        self.assertEqual(
            self.result.maximum_certificate_gap_chips.hex(),
            ADR0343_MAX_CERTIFICATE_GAP_HEX,
        )

    def test_context_local_menus_and_teacher_winners_are_exact(self) -> None:
        contexts = self.result.journal.contexts
        self.assertEqual(
            tuple(item.pool_index for item in contexts),
            ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
        )
        self.assertEqual(
            tuple(item.digest for item in contexts),
            ADR0343_CONTEXT_RESULT_SHA256S,
        )
        self.assertEqual(
            tuple(len(item.candidates) for item in contexts),
            ADR0343_CONTEXT_CANDIDATE_COUNTS,
        )
        self.assertEqual(
            tuple(item.selected_candidate_position for item in contexts),
            ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS,
        )
        self.assertEqual(
            tuple(
                item.selected.transition.augmented.raise_to_totals for item in contexts
            ),
            ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS,
        )
        for item in contexts:
            selected = item.selected_candidate_position
            self.assertEqual(item.teacher.nondominated_subset_indices, (selected,))
            self.assertEqual(item.teacher.equivalent_subset_indices, (selected,))
            self.assertEqual(item.teacher.unique_best_subset_index, selected)

    def test_mutation_and_truncation_fail_before_semantic_publication(self) -> None:
        raw = _ARTIFACT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transfer-confirmation.jsonl"
            mutated = bytearray(raw)
            mutated[len(mutated) // 2] ^= 1
            path.write_bytes(mutated)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_adr0343_transfer_confirmation_result_artifact(path)

            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError, "byte count"):
                verify_adr0343_transfer_confirmation_result_artifact(path)

    def test_retained_result_rejects_invalid_gap_and_nonconfirmation(self) -> None:
        result = self.result
        with self.assertRaises(ValueError):
            RetainedTransferConfirmationResult(
                journal=result.journal,
                maximum_certificate_gap_chips=float("nan"),
            )
        with self.assertRaises(ValueError):
            replace(
                result.journal,
                stop_reason=TransferConfirmationStopReason.COMPLETED_REJECTED,
            )

    def test_result_owner_has_no_solver_campaign_action_or_write_path(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertNotIn(
            "run_and_retain_adr0341_transfer_confirmation",
            called_names,
        )
        self.assertNotIn("consume_certified_reduced_sizing_v2", called_names)
        self.assertNotIn("linprog", called_names | called_attributes)
        self.assertNotIn("apply_action", called_names | called_attributes)
        self.assertNotIn("write_bytes", called_attributes)
        self.assertNotIn("write_text", called_attributes)


if __name__ == "__main__":
    unittest.main()
