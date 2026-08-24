from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_responder_raise_h4_tie_aware_affine_result import (
    ADR0353_ARTIFACT_BYTES,
    ADR0353_ARTIFACT_SHA256,
    ADR0353_CONFIG_SHA256,
    ADR0353_HISTORICAL_RUNNER_CONTROL_SHA256,
    ADR0353_IMPLEMENTATION_SHA256,
    ADR0353_INVOCATION_SOURCE_COMMIT,
    ADR0353_RESULT_PROTOCOL_SHA256,
    ADR0353_TOTAL_SECONDS,
    RetainedLegalH4TieAwareAffineRejection,
    verify_adr0353_legal_h4_tie_aware_affine_record,
    verify_adr0353_legal_h4_tie_aware_affine_result_artifact,
    verify_adr0353_result_source_and_dependencies,
)
from pontius.legal_responder_raise_h4_tie_aware_affine_result_seal import (
    ADR0353_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0353_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-tie-aware-affine-v1.json"
)
_SOURCE = (
    _ROOT / "src/pontius/legal_responder_raise_h4_tie_aware_affine_result.py"
)


class LegalResponderRaiseH4TieAwareAffineResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        cls.result = verify_adr0353_legal_h4_tie_aware_affine_result_artifact()

    def test_result_owner_source_protocol_and_inputs_are_sealed(self) -> None:
        self.assertEqual(ADR0353_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            verify_adr0353_result_source_and_dependencies(),
            ADR0353_RESULT_SOURCE_MANIFEST[
                "legal_responder_raise_h4_tie_aware_affine_result.py"
            ],
        )
        self.assertEqual(
            ADR0353_HISTORICAL_RUNNER_CONTROL_SHA256,
            "dd691d01b271dfabb599a68df338602286e304287f35b7ae6fc1fc0a8709d92e",
        )

    def test_artifact_bytes_commit_and_source_identities_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0353_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0353_ARTIFACT_SHA256)
        self.assertEqual(self.result.source_commit, ADR0353_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(self.result.record["config_sha256"], ADR0353_CONFIG_SHA256)
        self.assertEqual(
            self.result.record["implementation_sha256"],
            ADR0353_IMPLEMENTATION_SHA256,
        )

    def test_typed_bound_rejection_is_rebound_without_relaxation(self) -> None:
        self.assertIsInstance(
            self.result,
            RetainedLegalH4TieAwareAffineRejection,
        )
        self.assertFalse(self.result.record["passed"])
        self.assertFalse(self.result.successor_authorized)
        self.assertEqual(
            self.result.failure_classification,
            "frozen_active_tape_cartesian_bound_rejection",
        )
        self.assertEqual(
            dict(self.result.record["failure"]),
            {
                "message": "exact active-tape closure exceeds its frozen bound",
                "stage": "tie_aware_affine",
                "type": "RuntimeError",
            },
        )
        self.assertEqual(
            self.result.record["total_seconds"].hex(),
            ADR0353_TOTAL_SECONDS.hex(),
        )
        self.assertIsNone(self.result.record["strategy_quality_claim"])

    def test_outer_byte_mutation_is_rejected(self) -> None:
        mutated = bytearray(_ARTIFACT.read_bytes())
        mutated[100] = ord("x") if mutated[100] != ord("x") else ord("y")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_bytes(mutated)
            with self.assertRaises(ValueError):
                verify_adr0353_legal_h4_tie_aware_affine_result_artifact(path)

    def test_rehashed_failure_semantic_mutations_are_rejected(self) -> None:
        for key, value in (
            ("message", "exact affine-row library exceeds its frozen bound"),
            ("stage", "serialization"),
            ("type", "ArithmeticError"),
        ):
            with self.subTest(key=key):
                mutated = deepcopy(self.record)
                mutated["failure"][key] = value
                with self.assertRaises(ValueError):
                    verify_adr0353_legal_h4_tie_aware_affine_record(mutated)

    def test_rehashed_authority_and_timing_mutations_are_rejected(self) -> None:
        mutations = []
        for key, value in (
            ("passed", True),
            ("decision", "authorize_legal_h4_tie_aware_affine_integration"),
            ("strategy_quality_claim", "positive"),
            ("total_seconds", 120.0),
        ):
            mutated = deepcopy(self.record)
            mutated[key] = value
            mutations.append(mutated)
        mutated = deepcopy(self.record)
        mutated["environment"]["git"]["dirty"] = True
        mutations.append(mutated)
        for index, record in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    verify_adr0353_legal_h4_tie_aware_affine_record(record)

    def test_result_owner_has_no_runner_solver_game_action_or_write_import(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.add((node.level, node.module))
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        self.assertEqual(
            {item for item in imports if item[0] > 0},
            {(1, "legal_responder_raise_h4_tie_aware_affine_result_seal")},
        )
        self.assertTrue(
            {
                "legal_responder_raise_h4_tie_aware_affine",
                "exact_tie_aware_affine_envelope",
                "tie_aware_affine_adapter",
                "exact_sequence_form_br",
                "legal_river_continuation",
                "no_limit_betting",
            }.isdisjoint({module for _, module in imports})
        )
        self.assertTrue(
            {
                "best_response",
                "build_exact_tie_aware_affine_section",
                "main",
                "open",
                "run_and_retain",
                "write_bytes",
                "write_text",
            }.isdisjoint(calls)
        )


if __name__ == "__main__":
    unittest.main()
