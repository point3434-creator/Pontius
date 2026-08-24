from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pontius.certified_reduced_sizing_consumer_v2 as consumer
import pontius.fresh_action_width_nonreplay_teacher as teacher
import pontius.fresh_action_width_nonreplay_teacher_result as retained
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.fresh_action_width_nonreplay_teacher import (
    NonReplayTeacherEvidenceKind,
    NonReplayTeacherStopReason,
)
from pontius.fresh_action_width_nonreplay_teacher_result import (
    ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH,
    ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH,
    ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS,
    ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH,
    ADR0336_TEACHER_ARTIFACT_BYTES,
    ADR0336_TEACHER_ARTIFACT_SHA256,
    ADR0336_TEACHER_CONTEXT_RESULT_SHA256S,
    ADR0336_TEACHER_PUBLIC_CALL_COUNT,
    ADR0336_TEACHER_RECORD_COUNT,
    ADR0336_TEACHER_RESULT_PROTOCOL_SHA256,
    ADR0336_TEACHER_RESULT_SHA256,
    ADR0336_TEACHER_WIDTH_SUMMARY_SPECS,
    verify_adr0336_nonreplay_teacher_result_artifact,
)
from pontius.fresh_action_width_nonreplay_teacher_result_seal import (
    ADR0336_TEACHER_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0336_TEACHER_RESULT_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_structures import RaiseActionWidth


def _forbidden_call(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the retained result owner reached a value-owning path")


class FreshActionWidthNonReplayTeacherResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(retained.__file__).resolve().parents[2]
        cls.artifact_path = (
            cls.root
            / "experiments/results/"
            "fresh-action-width-nonreplay-exhaustive-teacher-v1.jsonl"
        )
        cls.raw = cls.artifact_path.read_bytes()
        with (
            patch.object(
                teacher,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_call,
            ),
            patch.object(
                consumer,
                "solve_certified_reduced_sizing_highs",
                side_effect=_forbidden_call,
            ),
            patch.object(
                teacher,
                "run_and_retain_adr0334_nonreplay_exhaustive_teacher",
                side_effect=_forbidden_call,
            ),
        ):
            cls.result = verify_adr0336_nonreplay_teacher_result_artifact()

    def test_source_protocol_artifact_and_binary_retention_are_exact(self) -> None:
        source_root = Path(retained.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(source_root / name)
            for name in ADR0336_TEACHER_RESULT_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0336_TEACHER_RESULT_SOURCE_MANIFEST), actual)
        self.assertEqual(
            SEALED_PROTOCOL_SHA256,
            ADR0336_TEACHER_RESULT_PROTOCOL_SHA256,
        )
        self.assertEqual(ADR0336_TEACHER_ARTIFACT_BYTES, len(self.raw))
        self.assertEqual(
            ADR0336_TEACHER_ARTIFACT_SHA256,
            hashlib.sha256(self.raw).hexdigest(),
        )
        self.assertEqual(ADR0336_TEACHER_RECORD_COUNT, self.raw.count(b"\n"))
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertFalse(self.raw.endswith(b"\n\n"))
        attributes = (self.root / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/results/"
            "fresh-action-width-nonreplay-exhaustive-teacher-v1.jsonl -text",
            attributes,
        )

    def test_solver_free_result_is_complete_accepted_and_exact(self) -> None:
        result = self.result
        self.assertEqual(ADR0336_TEACHER_RESULT_SHA256, result.digest)
        self.assertEqual(ADR0336_TEACHER_PUBLIC_CALL_COUNT, len(result.journal.evidences))
        self.assertEqual(
            ADR0336_TEACHER_PUBLIC_CALL_COUNT,
            result.journal.known_public_call_count,
        )
        self.assertTrue(result.journal.invocation_count_complete)
        self.assertFalse(result.journal.synthetic)
        self.assertIs(result.journal.stop_reason, NonReplayTeacherStopReason.COMPLETED)
        self.assertEqual(
            ADR0336_TEACHER_CONTEXT_RESULT_SHA256S,
            tuple(context.digest for context in result.journal.contexts),
        )
        self.assertTrue(
            all(
                evidence.kind is NonReplayTeacherEvidenceKind.ACCEPTED
                and evidence.public_call_count == 1
                and not evidence.synthetic
                for evidence in result.journal.evidences
            )
        )

    def test_population_knee_tail_and_plateau_map_are_exact(self) -> None:
        result = self.result
        self.assertEqual(
            ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH,
            result.median_lower_regret_knee.count,
        )
        self.assertEqual(
            ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH,
            result.first_all_contexts_zero_lower_width.count,
        )
        self.assertEqual(
            ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH,
            result.first_full_regret_gate_passing_width.count,
        )
        self.assertEqual(
            ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS,
            result.median_knee_positive_tail_context_positions,
        )
        self.assertEqual(
            ADR0336_TEACHER_WIDTH_SUMMARY_SPECS,
            tuple(retained._summary_spec(item) for item in result.width_summaries),
        )
        self.assertEqual(
            (16, 2, 0, 0, 0),
            tuple(
                len(item.certified_positive_lower_context_positions)
                for item in result.width_summaries
            ),
        )
        self.assertEqual(
            (16, 16, 2, 0, 0),
            tuple(
                len(item.unique_survivor_context_positions)
                for item in result.width_summaries
            ),
        )
        self.assertEqual(
            (False, True, True, True, True),
            tuple(item.full_regret_gate_pass for item in result.width_summaries),
        )
        self.assertTrue(result.width_summaries[0].maximum_full_regret_pass)
        self.assertFalse(result.width_summaries[0].mean_full_regret_pass)
        self.assertTrue(
            all(
                item.nondominated_cardinality_counts
                == item.equivalent_cardinality_counts
                for item in result.width_summaries
            )
        )

    def test_result_types_reject_crossed_knees_and_numeric_coincidences(self) -> None:
        with self.assertRaises(ValueError):
            replace(
                self.result,
                median_lower_regret_knee=RaiseActionWidth(4),
            )
        with self.assertRaises(ValueError):
            replace(
                self.result,
                first_all_contexts_zero_lower_width=RaiseActionWidth(3),
            )
        with self.assertRaises(ValueError):
            replace(
                self.result,
                first_full_regret_gate_passing_width=RaiseActionWidth(4),
            )
        with self.assertRaises((TypeError, ValueError)):
            replace(
                self.result.width_summaries[1],
                certified_positive_lower_context_positions=(False,),
            )
        with self.assertRaises(ValueError):
            replace(
                self.result.width_summaries[2],
                median_normalized_lower=1.0,
            )
        empty_reporting = replace(
            self.result.width_summaries[0],
            equivalent_cardinality_counts=((0, 16),),
        )
        self.assertEqual(((0, 16),), empty_reporting.equivalent_cardinality_counts)
        with self.assertRaises(ValueError):
            replace(
                self.result.width_summaries[0],
                nondominated_cardinality_counts=((0, 16),),
            )

    def test_byte_mutation_truncation_and_extension_fail_closed(self) -> None:
        variants = (
            self.raw[:-1],
            self.raw + b"\n",
            b"x" + self.raw[1:],
        )
        for index, raw in enumerate(variants):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "teacher.jsonl"
                path.write_bytes(raw)
                patches = ()
                if len(raw) == len(self.raw):
                    patches = (
                        patch.object(
                            retained,
                            "ADR0336_TEACHER_ARTIFACT_SHA256",
                            hashlib.sha256(raw).hexdigest(),
                        ),
                    )
                with self.assertRaises((TypeError, ValueError)):
                    if patches:
                        with patches[0]:
                            verify_adr0336_nonreplay_teacher_result_artifact(path)
                    else:
                        verify_adr0336_nonreplay_teacher_result_artifact(path)

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
            "consume_certified_reduced_sizing_v2",
            "run_and_retain_adr0334_nonreplay_exhaustive_teacher",
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
