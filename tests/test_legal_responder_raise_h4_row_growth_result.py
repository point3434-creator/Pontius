from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_responder_raise_h4_row_growth_result import (
    ADR0349_ARTIFACT_BYTES,
    ADR0349_ARTIFACT_SHA256,
    ADR0349_CONFIG_SHA256,
    ADR0349_FINAL_POLICY_SHA256,
    ADR0349_GAME_PROVENANCE_SHA256,
    ADR0349_GAME_STRUCTURAL_SHA256,
    ADR0349_INVOCATION_SOURCE_COMMIT,
    ADR0349_PUBLIC_SCHEMA_SHA256,
    ADR0349_RESULT_PROTOCOL_SHA256,
    ADR0349_ROOT_PUBLIC_STATE_SHA256,
    ADR0349_SOURCE_POLICY_SHA256,
    RetainedLegalH4RowGrowthResult,
    verify_adr0349_legal_h4_row_growth_record,
    verify_adr0349_legal_h4_row_growth_result_artifact,
    verify_adr0349_result_source_and_dependencies,
)
from pontius.legal_responder_raise_h4_row_growth_result_seal import (
    ADR0349_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0349_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT / "experiments/results/legal-responder-raise-h4-row-growth-v1.json"
)
_SOURCE = _ROOT / "src/pontius/legal_responder_raise_h4_row_growth_result.py"


def _canonical_compact(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _row_digest(row: dict[str, object]) -> str:
    coefficients = row["coefficients"]
    assert isinstance(coefficients, list)
    payload = {
        "constant": row["constant_exact"],
        "coefficients": sorted(
            (
                {
                    "information_key": item["information_key"],
                    "action": item["action"],
                    "value": item["exact"],
                }
                for item in coefficients
            ),
            key=lambda item: (item["information_key"], item["action"]),
        ),
    }
    return hashlib.sha256(_canonical_compact(payload)).hexdigest()


class LegalResponderRaiseH4RowGrowthResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        cls.result = verify_adr0349_legal_h4_row_growth_result_artifact()

    def test_result_owner_source_protocol_and_inputs_are_sealed(self) -> None:
        self.assertEqual(ADR0349_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            verify_adr0349_result_source_and_dependencies(),
            ADR0349_RESULT_SOURCE_MANIFEST[
                "legal_responder_raise_h4_row_growth_result.py"
            ],
        )

    def test_artifact_bytes_commit_and_fixture_identities_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0349_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0349_ARTIFACT_SHA256)
        self.assertEqual(self.result.source_commit, ADR0349_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(self.result.record["config_sha256"], ADR0349_CONFIG_SHA256)
        self.assertEqual(
            self.result.record["root_public_state_sha256"],
            ADR0349_ROOT_PUBLIC_STATE_SHA256,
        )
        self.assertEqual(
            self.result.record["public_schema_sha256"],
            ADR0349_PUBLIC_SCHEMA_SHA256,
        )
        self.assertEqual(
            self.result.record["game_structural_sha256"],
            ADR0349_GAME_STRUCTURAL_SHA256,
        )
        self.assertEqual(
            self.result.record["game_provenance_sha256"],
            ADR0349_GAME_PROVENANCE_SHA256,
        )

    def test_clean_negative_row_growth_result_is_exactly_bounded(self) -> None:
        self.assertIsInstance(self.result, RetainedLegalH4RowGrowthResult)
        self.assertEqual(self.result.response_rows, 2)
        self.assertEqual(self.result.generated_rows, 0)
        self.assertEqual(self.result.iterations, 1)
        self.assertEqual(self.result.record["response_rows_by_player"], (1, 1))
        self.assertEqual(self.result.record["retained_row_bytes"], 21_691)
        self.assertEqual(
            self.result.record["source_policy_sha256"],
            ADR0349_SOURCE_POLICY_SHA256,
        )
        self.assertEqual(
            self.result.record["final_policy_sha256"],
            ADR0349_FINAL_POLICY_SHA256,
        )
        self.assertEqual(
            Fraction(
                self.result.record["final_exact_nash_conv"]["numerator"],
                self.result.record["final_exact_nash_conv"]["denominator"],
            ),
            Fraction(27, 64),
        )
        self.assertEqual(self.result.record["optimality_gap"].hex(), "0x1.0000000000000p-53")

    def test_candidate_changes_responder_tape_but_needs_no_cut(self) -> None:
        evaluations = self.result.record["evaluations"]
        baseline = evaluations[0]
        candidate = evaluations[1]
        self.assertEqual(
            baseline["response_signature_sha256s"][0],
            candidate["response_signature_sha256s"][0],
        )
        self.assertNotEqual(
            baseline["response_signature_sha256s"][1],
            candidate["response_signature_sha256s"][1],
        )
        self.assertEqual(
            Fraction(
                candidate["deviation_gains_exact"][1]["numerator"],
                candidate["deviation_gains_exact"][1]["denominator"],
            ),
            0,
        )
        iteration = self.result.record["iterations"][0]
        self.assertEqual(iteration["response_rows_added"], 0)
        self.assertEqual(iteration["added_targets"], ())
        self.assertTrue(iteration["exact_converged"])

    def test_rows_bytes_conditioning_and_oracle_work_are_rebound(self) -> None:
        rows = self.record["response_rows"]
        self.assertEqual([row["retained_bytes"] for row in rows], [10_889, 10_802])
        for row in rows:
            semantic = {key: value for key, value in row.items() if key != "retained_bytes"}
            self.assertEqual(len(_canonical_compact(semantic)), row["retained_bytes"])
            self.assertEqual(_row_digest(row), row["exact_row_sha256"])
            self.assertEqual(len(row["coefficients"]), 32)
            self.assertTrue(row["exact_float_identity"])
        for row in self.result.record["conditioning"]:
            self.assertEqual(row["production"], row["rebound"])
            self.assertEqual(row["rebound"]["effective_condition_number"], 1.0)
        accounting = self.result.record["oracle_accounting"]
        self.assertTrue(accounting["identity"])
        self.assertEqual(accounting["observed"], accounting["expected_from_call_graph"])
        self.assertEqual(accounting["observed"]["best_response_calls"], 5)

    def test_all_gates_pass_and_timing_stays_infrastructure_only(self) -> None:
        self.assertTrue(self.result.record["passed"])
        self.assertTrue(all(self.result.record["gates"].values()))
        timing = self.result.record["timing"]
        self.assertLess(timing["subject_generation_seconds"], 60.0)
        self.assertLess(timing["total_infrastructure_seconds"], 120.0)
        self.assertEqual(
            timing["subject_generation_seconds"]
            + timing["exact_audit_and_plumbing_seconds"],
            timing["total_infrastructure_seconds"],
        )
        self.assertIsNone(self.result.record["strategy_quality_claim"])
        self.assertEqual(self.result.record["quality_rows_serialized"], 0)

    def test_outer_byte_mutation_is_rejected(self) -> None:
        mutated = bytearray(_ARTIFACT.read_bytes())
        mutated[100] = ord("x") if mutated[100] != ord("x") else ord("y")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_bytes(mutated)
            with self.assertRaises(ValueError):
                verify_adr0349_legal_h4_row_growth_result_artifact(path)

    def test_fully_rehashed_row_semantic_mutation_is_rejected(self) -> None:
        mutated = deepcopy(self.record)
        row = mutated["response_rows"][0]
        coefficient = row["coefficients"][0]
        prior = Fraction(
            coefficient["exact"]["numerator"],
            coefficient["exact"]["denominator"],
        )
        changed = prior + Fraction(1, 1024)
        coefficient["exact"] = {
            "numerator": changed.numerator,
            "denominator": changed.denominator,
        }
        coefficient["subject_hex"] = float(changed).hex()
        row["exact_row_sha256"] = _row_digest(row)
        semantic = {key: value for key, value in row.items() if key != "retained_bytes"}
        row["retained_bytes"] = len(_canonical_compact(semantic))
        mutated["retained_row_bytes"] = sum(
            item["retained_bytes"] for item in mutated["response_rows"]
        )

        with self.assertRaises(ValueError):
            verify_adr0349_legal_h4_row_growth_record(mutated)

    def test_fully_rehashed_candidate_tape_mutation_is_rejected(self) -> None:
        mutated = deepcopy(self.record)
        signature = mutated["evaluations"][1]["response_signatures"][1]
        signature[0]["action"] += "-mutated"
        digest = hashlib.sha256(_canonical_compact(signature)).hexdigest()
        mutated["evaluations"][1]["response_signature_sha256s"][1] = digest
        mutated["iterations"][0]["response_signature_sha256s"][1] = digest

        with self.assertRaises(ValueError):
            verify_adr0349_legal_h4_row_growth_record(mutated)

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
            {(1, "legal_responder_raise_h4_row_growth_result_seal")},
        )
        self.assertTrue(
            {
                "one_seat_convex_generation",
                "one_seat_row_growth_audit",
                "legal_responder_raise_h4_row_growth",
                "evaluation",
                "legal_river_continuation",
                "no_limit_betting",
            }.isdisjoint({module for _, module in imports})
        )
        self.assertTrue(
            {
                "open",
                "write_bytes",
                "write_text",
                "solve_one_seat_with_row_generation",
                "best_response",
            }.isdisjoint(calls)
        )


if __name__ == "__main__":
    unittest.main()
