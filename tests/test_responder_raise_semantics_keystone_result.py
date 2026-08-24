from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pontius.responder_raise_semantics_keystone_result import (
    ADR0345_ARTIFACT_BYTES,
    ADR0345_ARTIFACT_SHA256,
    ADR0345_CONFIG_SHA256,
    ADR0345_GAME_PROVENANCE_SHA256,
    ADR0345_GAME_STRUCTURAL_SHA256,
    ADR0345_INVOCATION_SOURCE_COMMIT,
    ADR0345_LOWER_BOUND_HEX,
    ADR0345_MAXIMUM_JENSEN_ERROR_HEX,
    ADR0345_MAXIMUM_REALIZATION_ERROR_HEX,
    ADR0345_OBJECTIVE_HEX,
    ADR0345_PUBLIC_SCHEMA_SHA256,
    ADR0345_RESULT_PROTOCOL_SHA256,
    ADR0345_ROOT_PUBLIC_STATE_SHA256,
    RetainedResponderRaiseSemanticsResult,
    verify_adr0345_responder_raise_semantics_result_artifact,
    verify_adr0345_result_source_and_dependencies,
)
from pontius.responder_raise_semantics_keystone_result_seal import (
    ADR0345_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0345_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT / "experiments/results/responder-raise-semantics-keystone-v1.json"
)
_SOURCE = _ROOT / "src/pontius/responder_raise_semantics_keystone_result.py"


class ResponderRaiseSemanticsKeystoneResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_adr0345_responder_raise_semantics_result_artifact()

    def test_result_owner_source_protocol_and_inputs_are_sealed(self) -> None:
        self.assertEqual(ADR0345_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            verify_adr0345_result_source_and_dependencies(),
            ADR0345_RESULT_SOURCE_MANIFEST[
                "responder_raise_semantics_keystone_result.py"
            ],
        )

    def test_retained_artifact_bytes_and_source_commit_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0345_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0345_ARTIFACT_SHA256)
        self.assertEqual(self.result.source_commit, ADR0345_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(
            self.result.record["config_sha256"], ADR0345_CONFIG_SHA256
        )
        self.assertEqual(
            self.result.record["game_structural_sha256"],
            ADR0345_GAME_STRUCTURAL_SHA256,
        )
        self.assertEqual(
            self.result.record["game_provenance_sha256"],
            ADR0345_GAME_PROVENANCE_SHA256,
        )

    def test_exact_legal_semantics_and_repeated_actor_witness_are_retained(self) -> None:
        result = self.result.record
        semantics = result["semantics"]
        self.assertEqual(
            result["root_public_state_sha256"], ADR0345_ROOT_PUBLIC_STATE_SHA256
        )
        self.assertEqual(
            semantics["public_schema_sha256"], ADR0345_PUBLIC_SCHEMA_SHA256
        )
        self.assertEqual(semantics["strategic_nodes"], 6)
        self.assertEqual(semantics["terminal_nodes"], 11)
        self.assertEqual(semantics["full_raise_branches"], 1)
        self.assertEqual(semantics["short_all_in_raise_branches"], 1)
        self.assertTrue(semantics["short_all_in_final_response_only"])
        self.assertEqual(semantics["maximum_terminal_oracle_error_chips"], 0.0)
        self.assertFalse(result["topology"]["path_single_visit"])
        self.assertEqual(result["topology"]["repeated_player"], 0)
        self.assertTrue(result["topology"]["behavioral_shortcut_rejected"])
        self.assertTrue(all(result["gates"].values()))

    def test_complete_teacher_generated_bounds_and_retreat_are_retained(self) -> None:
        self.assertEqual(self.result.objective.hex(), ADR0345_OBJECTIVE_HEX)
        self.assertEqual(self.result.lower_bound.hex(), ADR0345_LOWER_BOUND_HEX)
        self.assertEqual(self.result.upper_bound.hex(), ADR0345_OBJECTIVE_HEX)
        self.assertEqual(self.result.record["teacher"]["acting_pure_plans"], 16)
        self.assertEqual(
            self.result.record["teacher"]["response_pure_plans"], (0, 18)
        )
        self.assertEqual(
            float(
                self.result.record["maximum_realization_equivalence_error"]
            ).hex(),
            ADR0345_MAXIMUM_REALIZATION_ERROR_HEX,
        )
        self.assertEqual(
            float(self.result.record["retreat"]["maximum_jensen_error"]).hex(),
            ADR0345_MAXIMUM_JENSEN_ERROR_HEX,
        )
        self.assertLess(self.result.total_seconds, 60.0)
        self.assertEqual(self.result.record["strategy_labels_generated"], 0)
        self.assertIsNone(self.result.record["strategy_quality_claim"])

    def test_mutation_and_truncation_fail_before_semantic_publication(self) -> None:
        raw = _ARTIFACT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responder-raise.json"
            mutated = bytearray(raw)
            mutated[len(mutated) // 2] ^= 1
            path.write_bytes(mutated)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_adr0345_responder_raise_semantics_result_artifact(path)

            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError, "byte count"):
                verify_adr0345_responder_raise_semantics_result_artifact(path)

    def test_result_value_rejects_nonfinite_or_wrong_source_identity(self) -> None:
        with self.assertRaises(ValueError):
            RetainedResponderRaiseSemanticsResult(
                record=self.result.record,
                source_commit="0" * 40,
                total_seconds=self.result.total_seconds,
                objective=self.result.objective,
                lower_bound=self.result.lower_bound,
                upper_bound=self.result.upper_bound,
            )
        with self.assertRaises(ValueError):
            RetainedResponderRaiseSemanticsResult(
                record=self.result.record,
                source_commit=ADR0345_INVOCATION_SOURCE_COMMIT,
                total_seconds=float("nan"),
                objective=self.result.objective,
                lower_bound=self.result.lower_bound,
                upper_bound=self.result.upper_bound,
            )

    def test_result_owner_has_no_runner_solver_game_action_or_write_path(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
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
        self.assertFalse(
            any(
                name.endswith("responder_raise_semantics_keystone")
                or name.startswith("scipy")
                for name in imports
            )
        )
        self.assertNotIn("solve_one_seat_with_row_generation", called_names)
        self.assertNotIn("solve_one_seat_complete_normal_form_teacher", called_names)
        self.assertNotIn("apply_action", called_names | called_attributes)
        self.assertNotIn("linprog", called_names | called_attributes)
        self.assertNotIn("write_bytes", called_attributes)
        self.assertNotIn("write_text", called_attributes)

        with (
            patch.object(Path, "write_bytes", side_effect=AssertionError("write")),
            patch.object(Path, "write_text", side_effect=AssertionError("write")),
        ):
            rebound = verify_adr0345_responder_raise_semantics_result_artifact()
        self.assertIsInstance(rebound, RetainedResponderRaiseSemanticsResult)


if __name__ == "__main__":
    unittest.main()
