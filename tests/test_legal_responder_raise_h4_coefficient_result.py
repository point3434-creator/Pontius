from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import json
import tempfile
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

import pontius.legal_responder_raise_h4_coefficient_result as result_module
from pontius.legal_responder_raise_h4_coefficient_result import (
    ADR0347_ARTIFACT_BYTES,
    ADR0347_ARTIFACT_SHA256,
    ADR0347_CONFIG_SHA256,
    ADR0347_GAME_PROVENANCE_SHA256,
    ADR0347_GAME_STRUCTURAL_SHA256,
    ADR0347_INVOCATION_SOURCE_COMMIT,
    ADR0347_PUBLIC_SCHEMA_SHA256,
    ADR0347_RESULT_PROTOCOL_SHA256,
    ADR0347_ROOT_PUBLIC_STATE_SHA256,
    RetainedLegalH4CoefficientResult,
    verify_adr0347_legal_h4_coefficient_result_artifact,
    verify_adr0347_result_source_and_dependencies,
)
from pontius.legal_responder_raise_h4_coefficient_result_seal import (
    ADR0347_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0347_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT
    / "experiments/results/"
    / "legal-responder-raise-h4-coefficient-differential-v1.json"
)
_SOURCE = (
    _ROOT / "src/pontius/legal_responder_raise_h4_coefficient_result.py"
)


def _canonical_bytes(record: object) -> bytes:
    return (
        json.dumps(record, allow_nan=False, indent=2, sort_keys=True) + "\n"
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
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class LegalResponderRaiseH4CoefficientResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_adr0347_legal_h4_coefficient_result_artifact()

    def test_result_owner_source_protocol_and_inputs_are_sealed(self) -> None:
        self.assertEqual(ADR0347_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            verify_adr0347_result_source_and_dependencies(),
            ADR0347_RESULT_SOURCE_MANIFEST[
                "legal_responder_raise_h4_coefficient_result.py"
            ],
        )

    def test_artifact_bytes_commit_and_public_identities_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0347_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0347_ARTIFACT_SHA256)
        self.assertEqual(self.result.source_commit, ADR0347_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(self.result.record["config_sha256"], ADR0347_CONFIG_SHA256)
        self.assertEqual(
            self.result.record["root_public_state_sha256"],
            ADR0347_ROOT_PUBLIC_STATE_SHA256,
        )
        self.assertEqual(
            self.result.record["public_schema_sha256"],
            ADR0347_PUBLIC_SCHEMA_SHA256,
        )
        self.assertEqual(
            self.result.record["game_structural_sha256"],
            ADR0347_GAME_STRUCTURAL_SHA256,
        )
        self.assertEqual(
            self.result.record["game_provenance_sha256"],
            ADR0347_GAME_PROVENANCE_SHA256,
        )

    def test_exact_h4_axis_rows_endpoints_and_gates_are_retained(self) -> None:
        record = self.result.record
        self.assertEqual(record["fixture"]["hand_counts"], (4, 4))
        self.assertEqual(record["fixture"]["joint_deals"], 16)
        self.assertEqual(record["fixture"]["terminal_paths"], 176)
        self.assertEqual(record["axis"]["information_sets"], 12)
        self.assertEqual(record["axis"]["sequence_variables"], 32)
        self.assertEqual(record["axis"]["final_response_variables"], 16)
        self.assertEqual(self.result.coefficient_rows, 6)
        self.assertEqual(self.result.coefficients_per_row, 32)
        self.assertFalse(record["topology"]["path_single_visit"])
        self.assertTrue(record["topology"]["behavioral_shortcut_rejected"])
        self.assertEqual(
            record["coverage_nonzero_final_histories"],
            ("raise-to-2", "raise-to-3"),
        )
        self.assertTrue(all(record["gates"].values()))

    def test_fraction_rebinding_preserves_zero_sum_and_gain_algebra(self) -> None:
        rows = {
            row["label"]: row
            for row in self.result.record["payoff_rows"]
            + self.result.record["gain_rows"]
        }
        profile0 = rows["profile_player0"]
        profile1 = rows["profile_player1"]
        acting_gain = rows["acting_gain"]
        response = rows["best_response_player1"]
        response_gain = rows["responder_gain"]
        for left, right in zip(
            profile0["coefficients"],
            profile1["coefficients"],
            strict=True,
        ):
            left_exact = Fraction(**left["exact"])
            right_exact = Fraction(**right["exact"])
            self.assertEqual(left_exact + right_exact, 0)
        for source, gain in zip(
            profile0["coefficients"],
            acting_gain["coefficients"],
            strict=True,
        ):
            self.assertEqual(Fraction(**gain["exact"]), -Fraction(**source["exact"]))
        for best, base, gain in zip(
            response["coefficients"],
            profile1["coefficients"],
            response_gain["coefficients"],
            strict=True,
        ):
            self.assertEqual(
                Fraction(**gain["exact"]),
                Fraction(**best["exact"]) - Fraction(**base["exact"]),
            )

    def test_byte_mutation_and_truncation_fail_before_publication(self) -> None:
        raw = _ARTIFACT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "h4-coefficients.json"
            mutated = bytearray(raw)
            mutated[len(mutated) // 2] ^= 1
            path.write_bytes(mutated)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_adr0347_legal_h4_coefficient_result_artifact(path)

            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError, "byte count"):
                verify_adr0347_legal_h4_coefficient_result_artifact(path)

    def test_fully_rehashed_gain_mutation_fails_exact_algebra(self) -> None:
        record = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        gain = record["gain_rows"][0]
        coefficient = gain["coefficients"][0]
        original = Fraction(**coefficient["exact"])
        mutated = original + Fraction(1, 8)
        coefficient["exact"] = {
            "numerator": mutated.numerator,
            "denominator": mutated.denominator,
        }
        coefficient["subject_hex"] = float(mutated).hex()
        gain["exact_row_sha256"] = _row_digest(gain)
        raw = _canonical_bytes(record)
        expected_rows = dict(result_module._ROW_SHA256S)
        expected_rows["acting_gain"] = gain["exact_row_sha256"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rehashed-h4-coefficients.json"
            path.write_bytes(raw)
            with (
                patch.object(result_module, "ADR0347_ARTIFACT_BYTES", len(raw)),
                patch.object(
                    result_module,
                    "ADR0347_ARTIFACT_SHA256",
                    hashlib.sha256(raw).hexdigest(),
                ),
                patch.object(
                    result_module,
                    "_ROW_SHA256S",
                    MappingProxyType(expected_rows),
                ),
                self.assertRaisesRegex(ValueError, "gain-row algebra"),
            ):
                verify_adr0347_legal_h4_coefficient_result_artifact(path)

    def test_result_value_rejects_wrong_identity_or_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            RetainedLegalH4CoefficientResult(
                record=self.result.record,
                source_commit="0" * 40,
                total_seconds=self.result.total_seconds,
                coefficient_rows=6,
                coefficients_per_row=32,
            )
        with self.assertRaises(ValueError):
            RetainedLegalH4CoefficientResult(
                record=self.result.record,
                source_commit=ADR0347_INVOCATION_SOURCE_COMMIT,
                total_seconds=self.result.total_seconds,
                coefficient_rows=5,
                coefficients_per_row=32,
            )

    def test_owner_has_no_runner_game_evaluator_solver_action_or_write_path(self) -> None:
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
        forbidden_import_fragments = (
            "legal_responder_raise_h4_coefficient_differential",
            "exact_sequence_form_coefficient_oracle",
            "legal_river_continuation",
            "one_seat_convex_generation",
            "evaluation",
            "scipy",
        )
        self.assertFalse(
            any(
                fragment in name
                for name in imports
                for fragment in forbidden_import_fragments
            )
        )
        self.assertTrue(
            {"best_response", "expected_utilities", "apply_action", "linprog"}
            .isdisjoint(called_names | called_attributes)
        )
        self.assertTrue(
            {"write_bytes", "write_text"}.isdisjoint(called_attributes)
        )
        with (
            patch.object(Path, "write_bytes", side_effect=AssertionError("write")),
            patch.object(Path, "write_text", side_effect=AssertionError("write")),
        ):
            rebound = verify_adr0347_legal_h4_coefficient_result_artifact()
        self.assertIsInstance(rebound, RetainedLegalH4CoefficientResult)


if __name__ == "__main__":
    unittest.main()
