from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pontius.certified_reduced_sizing_consumer_v2 as consumer
import pontius.fresh_action_width_nonreplay_greedy as greedy
import pontius.fresh_action_width_nonreplay_greedy_result as retained
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.fresh_action_width_nonreplay_greedy import (
    NonReplayGreedyEvidenceKind,
    NonReplayGreedyStopReason,
)
from pontius.fresh_action_width_nonreplay_greedy_result import (
    ADR0338_GREEDY_ARTIFACT_BYTES,
    ADR0338_GREEDY_ARTIFACT_SHA256,
    ADR0338_GREEDY_CONTEXT_RESULT_SHA256S,
    ADR0338_GREEDY_EVIDENCE_COUNT,
    ADR0338_GREEDY_PUBLIC_CALL_COUNT,
    ADR0338_GREEDY_RECORD_COUNT,
    ADR0338_GREEDY_RESULT_PROTOCOL,
    ADR0338_GREEDY_RESULT_PROTOCOL_SHA256,
    ADR0338_GREEDY_RESULT_SHA256,
    ADR0338_GREEDY_WIDTH_GATE_SHA256S,
    ADR0338_GREEDY_WIDTH_GATE_SPECS,
    ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX,
    ADR0338_MAX_CERTIFICATE_GAP_HEX,
    ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH,
    ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT,
    ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT,
    verify_adr0338_nonreplay_greedy_result_artifact,
)
from pontius.fresh_action_width_nonreplay_greedy_result_seal import (
    ADR0338_GREEDY_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0338_GREEDY_RESULT_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_structures import RaiseActionWidth


def _forbidden_call(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the retained greedy result reached a value-owning path")


class FreshActionWidthNonReplayGreedyResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(retained.__file__).resolve().parents[2]
        cls.artifact_path = (
            cls.root
            / "experiments/results/"
            "fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl"
        )
        cls.raw = cls.artifact_path.read_bytes()
        with (
            patch.object(
                greedy,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_call,
            ),
            patch.object(
                consumer,
                "solve_certified_reduced_sizing_highs",
                side_effect=_forbidden_call,
            ),
            patch.object(
                greedy,
                "run_and_retain_adr0336_nonreplay_closed_finite_block_greedy",
                side_effect=_forbidden_call,
            ),
        ):
            cls.result = verify_adr0338_nonreplay_greedy_result_artifact()

    def test_source_protocol_artifact_and_binary_retention_are_exact(self) -> None:
        source_root = Path(retained.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(source_root / name)
            for name in ADR0338_GREEDY_RESULT_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0338_GREEDY_RESULT_SOURCE_MANIFEST), actual)
        self.assertEqual(
            SEALED_PROTOCOL_SHA256,
            ADR0338_GREEDY_RESULT_PROTOCOL_SHA256,
        )
        self.assertEqual(ADR0338_GREEDY_ARTIFACT_BYTES, len(self.raw))
        self.assertEqual(
            ADR0338_GREEDY_ARTIFACT_SHA256,
            hashlib.sha256(self.raw).hexdigest(),
        )
        self.assertEqual(ADR0338_GREEDY_RECORD_COUNT, self.raw.count(b"\n"))
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertFalse(self.raw.endswith(b"\n\n"))
        attributes = (self.root / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/results/"
            "fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl -text",
            attributes,
        )

    def test_solver_free_result_is_complete_accepted_and_exact(self) -> None:
        result = self.result
        self.assertEqual(ADR0338_GREEDY_RESULT_SHA256, result.digest)
        self.assertEqual(ADR0338_GREEDY_EVIDENCE_COUNT, len(result.journal.evidences))
        self.assertEqual(
            ADR0338_GREEDY_PUBLIC_CALL_COUNT,
            result.journal.known_public_call_count,
        )
        self.assertTrue(result.journal.invocation_count_complete)
        self.assertFalse(result.journal.synthetic)
        self.assertIs(
            result.journal.stop_reason,
            NonReplayGreedyStopReason.COMPLETED_SELECTED,
        )
        self.assertIsNone(result.journal.partial_context)
        self.assertIsNone(result.journal.failure_stage)
        self.assertFalse(result.journal.failure_exception_chain)
        self.assertEqual(
            ADR0338_GREEDY_CONTEXT_RESULT_SHA256S,
            tuple(context.digest for context in result.journal.contexts),
        )
        self.assertTrue(
            all(
                evidence.kind is NonReplayGreedyEvidenceKind.ACCEPTED
                and evidence.public_call_count == 1
                and not evidence.synthetic
                for evidence in result.journal.evidences
            )
        )

    def test_width_three_selection_five_gates_and_menus_are_exact(self) -> None:
        result = self.result
        self.assertEqual(
            ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH,
            result.selected_development_raise_width.count,
        )
        self.assertEqual(
            result.selected_development_raise_width,
            result.journal.selected_raise_width,
        )
        self.assertEqual(
            ADR0338_GREEDY_WIDTH_GATE_SHA256S,
            tuple(gate.digest for gate in result.journal.width_gates),
        )
        self.assertEqual(
            ADR0338_GREEDY_WIDTH_GATE_SPECS,
            tuple(retained._gate_spec(gate) for gate in result.journal.width_gates),
        )
        self.assertEqual((True, True, True, True), tuple(
            gate.passes for gate in result.journal.width_gates
        ))
        self.assertEqual(
            ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT,
            result.selected_menu_totals_by_context,
        )
        self.assertEqual(
            ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT,
            result.selected_subset_indices_by_context,
        )
        self.assertEqual(
            tuple(row[1] for row in ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT),
            tuple(
                context.rounds[0].selected.transition.augmented.raise_to_totals
                for context in result.journal.contexts
            ),
        )

    def test_certificate_diagnostic_and_claim_boundary_are_exact(self) -> None:
        gaps = tuple(
            float.fromhex(evidence.core["result"]["certified_gap_hex"])
            for evidence in self.result.journal.evidences
        )
        position = max(range(len(gaps)), key=gaps.__getitem__)
        self.assertEqual(ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX, position)
        self.assertEqual(ADR0338_MAX_CERTIFICATE_GAP_HEX, gaps[position].hex())
        claim = ADR0338_GREEDY_RESULT_PROTOCOL["claim_boundary"]
        self.assertIn("development-width-only", claim)
        self.assertIn("no production-width", claim)
        self.assertIn("latency", claim)
        self.assertIn("six-player-response", claim)

    def test_result_types_reject_crossed_widths_and_numeric_coincidences(self) -> None:
        with self.assertRaises(ValueError):
            replace(
                self.result,
                selected_development_raise_width=RaiseActionWidth(4),
            )
        bad_menus = list(self.result.selected_menu_totals_by_context)
        bad_first = list(bad_menus[0])
        bad_first[1] = (False, 5, 8)
        bad_menus[0] = tuple(bad_first)
        with self.assertRaises((TypeError, ValueError)):
            replace(
                self.result,
                selected_menu_totals_by_context=tuple(bad_menus),
            )
        bad_subsets = list(self.result.selected_subset_indices_by_context)
        bad_subsets[0] = (False, 1, 0, 0)
        with self.assertRaises((TypeError, ValueError)):
            replace(
                self.result,
                selected_subset_indices_by_context=tuple(bad_subsets),
            )
        with self.assertRaises(ValueError):
            replace(
                self.result.journal.width_gates[0],
                aggregate_recovery_pass=False,
            )

    def test_byte_mutation_truncation_and_extension_fail_closed(self) -> None:
        variants = (
            self.raw[:-1],
            self.raw + b"\n",
            b"x" + self.raw[1:],
        )
        for index, raw in enumerate(variants):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "greedy.jsonl"
                path.write_bytes(raw)
                digest_patch = (
                    patch.object(
                        retained,
                        "ADR0338_GREEDY_ARTIFACT_SHA256",
                        hashlib.sha256(raw).hexdigest(),
                    )
                    if len(raw) == len(self.raw)
                    else None
                )
                with self.assertRaises((TypeError, ValueError)):
                    if digest_patch is None:
                        verify_adr0338_nonreplay_greedy_result_artifact(path)
                    else:
                        with digest_patch:
                            verify_adr0338_nonreplay_greedy_result_artifact(path)

    def test_result_owner_has_no_solver_campaign_write_or_action_path(self) -> None:
        source = Path(retained.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        forbidden_imports = {
            "DurableEvidenceJournalWriter",
            "LegalDecisionSpine",
            "PreparationBank",
            "consume_certified_reduced_sizing_v2",
            "run_and_retain_adr0336_nonreplay_closed_finite_block_greedy",
            "solve_certified_reduced_sizing_highs",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_names))
        forbidden_attributes = {"append", "open", "write_bytes", "write_text"}
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(forbidden_attributes.isdisjoint(called_attributes))


if __name__ == "__main__":
    unittest.main()
