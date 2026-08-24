from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from pontius.fresh_action_width_nonreplay_qualification import (
    QualificationEvidenceKind,
)
from pontius.fresh_action_width_qualification import (
    ADR0323_OPPORTUNITY_FLOOR,
    ActionWidthQualificationClassification,
)
from pontius.fresh_action_width_transfer_qualification import (
    TransferQualificationStopReason,
)
from pontius.fresh_action_width_transfer_qualification_result import (
    ADR0341_MAX_CERTIFICATE_GAP_HEX,
    ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX,
    ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX,
    ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES,
    ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT,
    ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT,
    ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT,
    ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT,
    ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256,
    ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
    ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
    RetainedTransferQualificationResult,
    verify_adr0341_transfer_qualification_result_artifact,
    verify_adr0341_transfer_result_source_and_dependencies,
)
from pontius.fresh_action_width_transfer_qualification_result_seal import (
    ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_transfer_structures import (
    build_adr0339_transfer_pool,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT / "experiments/results/fresh-action-width-transfer-qualification-v1.jsonl"
)
_SOURCE = (
    _ROOT / "src/pontius/fresh_action_width_transfer_qualification_result.py"
)


def _forbidden(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("closed solver-bearing transfer owner was reached")


class FreshActionWidthTransferQualificationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_adr0341_transfer_qualification_result_artifact()

    def test_source_closure_and_result_protocol_are_sealed(self) -> None:
        self.assertEqual(
            ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256,
            SEALED_PROTOCOL,
        )
        self.assertEqual(
            verify_adr0341_transfer_result_source_and_dependencies(),
            ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST[
                "fresh_action_width_transfer_qualification_result.py"
            ],
        )

    def test_exact_journal_rebinds_without_runner_consumer_or_solver(self) -> None:
        with (
            patch(
                "pontius.fresh_action_width_transfer_qualification."
                "run_and_retain_adr0339_transfer_qualification",
                side_effect=_forbidden,
            ),
            patch(
                "pontius.fresh_action_width_transfer_qualification."
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden,
            ),
            patch("scipy.optimize.linprog", side_effect=_forbidden),
        ):
            result = verify_adr0341_transfer_qualification_result_artifact()

        self.assertEqual(
            result.journal.stop_reason,
            TransferQualificationStopReason.TARGET_REACHED,
        )
        self.assertEqual(
            result.journal.campaign_sha256,
            ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256,
        )
        self.assertEqual(
            result.journal.terminal_sha256,
            ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
        )
        self.assertEqual(
            len(result.journal.evidences),
            ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT,
        )
        self.assertEqual(
            len(result.journal.outcomes),
            ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT,
        )
        self.assertEqual(
            result.journal.known_public_call_count,
            ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT,
        )
        self.assertTrue(result.journal.invocation_count_complete)
        self.assertFalse(result.journal.synthetic)
        self.assertTrue(
            all(
                evidence.kind is QualificationEvidenceKind.ACCEPTED
                and evidence.public_call_count == 1
                and not evidence.synthetic
                for evidence in result.journal.evidences
            )
        )

    def test_retained_bytes_and_record_count_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
        )
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            raw.count(b"\n"),
            ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT,
        )

    def test_target_panel_and_classification_prefix_are_exact(self) -> None:
        result = self.result
        self.assertEqual(result.panel.digest, ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256)
        self.assertEqual(
            result.panel.qualified_indices,
            ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
        )
        self.assertEqual(
            result.panel.context_semantic_sha256s,
            ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S,
        )
        self.assertEqual(
            result.journal.qualified_indices,
            ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
        )
        counts = Counter(
            outcome.classification for outcome in result.journal.outcomes
        )
        self.assertEqual(
            counts,
            {
                ActionWidthQualificationClassification.QUALIFYING: 16,
                ActionWidthQualificationClassification.NONQUALIFYING: 31,
            },
        )
        self.assertEqual(
            tuple(outcome.context_index for outcome in result.journal.outcomes),
            tuple(range(47)),
        )

    def test_payoff_span_diagnostics_and_panel_diversity(self) -> None:
        result = self.result
        floor = ADR0323_OPPORTUNITY_FLOOR.value
        self.assertEqual(
            result.maximum_certificate_gap_chips.hex(),
            ADR0341_MAX_CERTIFICATE_GAP_HEX,
        )
        self.assertEqual(
            result.minimum_qualified_normalized_lower.hex(),
            ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX,
        )
        self.assertEqual(
            result.maximum_nonqualifying_normalized_upper.hex(),
            ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX,
        )
        self.assertGreater(result.minimum_qualified_normalized_lower, floor)
        self.assertLess(result.maximum_nonqualifying_normalized_upper, floor)

        pool = build_adr0339_transfer_pool()
        contexts = tuple(
            pool.contexts[index] for index in result.panel.qualified_indices
        )
        self.assertEqual({context.betting.pot for context in contexts}, {6, 10, 14, 20})
        self.assertEqual(
            {context.betting.stacks[0] for context in contexts},
            {8, 10, 12},
        )
        self.assertEqual(
            Counter(len(context.complete_raise_to_totals) for context in contexts),
            {7: 1, 9: 7, 11: 8},
        )
        self.assertEqual(len({context.showdown_signs for context in contexts}), 16)
        self.assertEqual(len({context.joint_probabilities for context in contexts}), 16)

    def test_panel_and_result_constructors_reject_cross_identity(self) -> None:
        result = self.result
        with self.assertRaises(ValueError):
            replace(
                result.panel,
                qualified_indices=(False, *result.panel.qualified_indices[1:]),
            )
        with self.assertRaises(ValueError):
            replace(
                result.panel,
                context_semantic_sha256s=(
                    result.panel.context_semantic_sha256s[0],
                    result.panel.context_semantic_sha256s[0],
                    *result.panel.context_semantic_sha256s[2:],
                ),
            )
        mismatched_panel = replace(result.panel, terminal_sha256="0" * 64)
        with self.assertRaises(ValueError):
            RetainedTransferQualificationResult(
                journal=result.journal,
                panel=mismatched_panel,
                maximum_certificate_gap_chips=result.maximum_certificate_gap_chips,
                minimum_qualified_normalized_lower=(
                    result.minimum_qualified_normalized_lower
                ),
                maximum_nonqualifying_normalized_upper=(
                    result.maximum_nonqualifying_normalized_upper
                ),
            )

    def test_mutation_and_truncation_fail_before_semantic_publication(self) -> None:
        raw = _ARTIFACT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transfer-qualification.jsonl"
            mutated = bytearray(raw)
            mutated[len(mutated) // 2] ^= 1
            path.write_bytes(mutated)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_adr0341_transfer_qualification_result_artifact(path)

            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError, "byte count"):
                verify_adr0341_transfer_qualification_result_artifact(path)

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
            "run_and_retain_adr0339_transfer_qualification",
            called_names,
        )
        self.assertNotIn("consume_certified_reduced_sizing_v2", called_names)
        self.assertNotIn("linprog", called_names | called_attributes)
        self.assertNotIn("apply_action", called_names | called_attributes)
        self.assertNotIn("write_bytes", called_attributes)
        self.assertNotIn("write_text", called_attributes)


if __name__ == "__main__":
    unittest.main()
