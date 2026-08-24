from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_responder_raise_h4_selector_fan_result import (
    ADR0351_ARTIFACT_BYTES,
    ADR0351_ARTIFACT_SHA256,
    ADR0351_CONFIG_SHA256,
    ADR0351_GAME_PROVENANCE_SHA256,
    ADR0351_GAME_STRUCTURAL_SHA256,
    ADR0351_INVOCATION_SOURCE_COMMIT,
    ADR0351_PUBLIC_SCHEMA_SHA256,
    ADR0351_RESULT_PROTOCOL_SHA256,
    ADR0351_ROOT_PUBLIC_STATE_SHA256,
    ADR0351_SOURCE_POLICY_SHA256,
    RetainedLegalH4SelectorFanResult,
    verify_adr0351_legal_h4_selector_fan_record,
    verify_adr0351_legal_h4_selector_fan_result_artifact,
    verify_adr0351_result_source_and_dependencies,
)
from pontius.legal_responder_raise_h4_selector_fan_result_seal import (
    ADR0351_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0351_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-selector-window-v1.json"
)
_SOURCE = (
    _ROOT / "src/pontius/legal_responder_raise_h4_selector_fan_result.py"
)


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


class LegalResponderRaiseH4SelectorFanResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        cls.result = verify_adr0351_legal_h4_selector_fan_result_artifact()

    def test_result_owner_source_protocol_and_inputs_are_sealed(self) -> None:
        self.assertEqual(ADR0351_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            verify_adr0351_result_source_and_dependencies(),
            ADR0351_RESULT_SOURCE_MANIFEST[
                "legal_responder_raise_h4_selector_fan_result.py"
            ],
        )

    def test_artifact_bytes_commit_and_fixture_identities_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0351_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0351_ARTIFACT_SHA256)
        self.assertEqual(self.result.source_commit, ADR0351_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(self.result.record["config_sha256"], ADR0351_CONFIG_SHA256)
        self.assertEqual(
            self.result.record["root_public_state_sha256"],
            ADR0351_ROOT_PUBLIC_STATE_SHA256,
        )
        self.assertEqual(
            self.result.record["public_schema_sha256"],
            ADR0351_PUBLIC_SCHEMA_SHA256,
        )
        self.assertEqual(
            self.result.record["game_structural_sha256"],
            ADR0351_GAME_STRUCTURAL_SHA256,
        )
        self.assertEqual(
            self.result.record["game_provenance_sha256"],
            ADR0351_GAME_PROVENANCE_SHA256,
        )
        self.assertEqual(
            self.result.record["source_policy_sha256"],
            ADR0351_SOURCE_POLICY_SHA256,
        )

    def test_map_is_retained_but_recorded_successor_authority_is_rejected(self) -> None:
        self.assertIsInstance(self.result, RetainedLegalH4SelectorFanResult)
        self.assertEqual(self.result.sections, 8)
        self.assertEqual(self.result.source_tie_sections, 4)
        self.assertEqual(self.result.recorded_source_tie_window_violations, 4)
        self.assertFalse(self.result.corrected_certificate_pass)
        self.assertFalse(self.result.successor_authorized)
        self.assertTrue(self.result.record["passed"])
        self.assertTrue(
            self.result.record["gates"]["conservative_total_tape_window"]
        )

    def test_all_acting_player_sections_are_reachable_full_measure_ties(self) -> None:
        for direction in self.result.record["directions"]:
            target = direction["target_rows"][0]
            self.assertEqual(
                _fraction(target["fan"]["measure"]["total"]["tie_unresolved"]),
                1,
            )
            self.assertEqual(
                _fraction(
                    target["fan"]["measure"]["reachable"]["tie_unresolved"]
                ),
                1,
            )
            self.assertEqual(target["schedule"][0]["reachable_state"], "tie_unresolved")
            self.assertTrue(target["schedule"][0]["exact_ties"])
            self.assertEqual(target["float_window"]["conservative_scale"], 1.0)

    def test_responder_fan_has_two_switching_and_two_endpoint_tie_sections(self) -> None:
        responders = [
            direction["target_rows"][1]
            for direction in self.result.record["directions"]
        ]
        self.assertEqual(
            [
                _fraction(row["fan"]["source_cell_upper"])
                for row in responders
            ],
            [Fraction(15, 19), Fraction(139, 163), Fraction(1), Fraction(1)],
        )
        self.assertEqual(
            [
                _fraction(row["fan"]["measure"]["total"]["switched"])
                for row in responders
            ],
            [Fraction(4, 19), Fraction(24, 163), Fraction(0), Fraction(0)],
        )
        self.assertEqual(
            sum(
                not point["identity_columns"]["total_identity"]
                and point["identity_columns"]["reachable_identity"]
                for row in responders
                for point in row["schedule"]
            ),
            2,
        )

    def test_exact_rows_form_the_maximum_gain_envelope(self) -> None:
        for direction in self.result.record["directions"]:
            for target in direction["target_rows"]:
                self.assertTrue(
                    all(row["active_row_identity"] for row in target["schedule"])
                )
                self.assertTrue(
                    all(
                        row["upper_envelope_identity"]
                        for row in target["schedule"]
                    )
                )
                self.assertTrue(
                    all(
                        row["envelope_role"]
                        == "lower_bound_row_under_maximum_upper_envelope"
                        for row in target["row_library"]
                    )
                )

    def test_recorded_walls_remain_infrastructure_only(self) -> None:
        self.assertEqual(self.result.record["aggregate"]["selector_calls"], 136)
        self.assertLess(self.result.selector_seconds, 60.0)
        self.assertLess(self.result.total_seconds, 120.0)
        self.assertIsNone(self.result.record["strategy_quality_claim"])
        self.assertEqual(self.result.record["quality_rows_serialized"], 0)

    def test_outer_byte_mutation_is_rejected(self) -> None:
        mutated = bytearray(_ARTIFACT.read_bytes())
        mutated[100] = ord("x") if mutated[100] != ord("x") else ord("y")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_bytes(mutated)
            with self.assertRaises(ValueError):
                verify_adr0351_legal_h4_selector_fan_result_artifact(path)

    def test_source_tie_semantic_mutation_is_rejected_without_outer_hash(self) -> None:
        mutated = deepcopy(self.record)
        source = mutated["directions"][0]["target_rows"][0]["schedule"][0]
        source["exact_ties"] = []
        source["total_state"] = "fixed"
        source["reachable_state"] = "fixed"
        with self.assertRaises(ValueError):
            verify_adr0351_legal_h4_selector_fan_record(mutated)

    def test_affine_row_semantic_mutation_is_rejected_without_outer_hash(self) -> None:
        mutated = deepcopy(self.record)
        row = mutated["directions"][0]["target_rows"][1]["row_library"][0]
        prior = _fraction(row["deviation_gain_row_slope"])
        changed = prior + Fraction(1, 1024)
        row["deviation_gain_row_slope"] = {
            "numerator": changed.numerator,
            "denominator": changed.denominator,
        }
        with self.assertRaises(ValueError):
            verify_adr0351_legal_h4_selector_fan_record(mutated)

    def test_total_reachable_identity_mutation_is_rejected(self) -> None:
        mutated = deepcopy(self.record)
        identity = mutated["directions"][2]["target_rows"][1]["schedule"][-1][
            "identity_columns"
        ]
        identity["total_entry_changes"] += 1
        with self.assertRaises(ValueError):
            verify_adr0351_legal_h4_selector_fan_record(mutated)

    def test_result_owner_has_no_runner_selector_game_action_or_write_import(self) -> None:
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
            {(1, "legal_responder_raise_h4_selector_fan_result_seal")},
        )
        self.assertTrue(
            {
                "evaluation",
                "exact_selector_fan",
                "exact_selector_window_oracle",
                "legal_responder_raise_h4_selector_window",
                "legal_river_continuation",
                "no_limit_betting",
                "selector_window",
                "selector_window_v2",
            }.isdisjoint({module for _, module in imports})
        )
        self.assertTrue(
            {
                "best_response",
                "open",
                "run_legal_responder_raise_h4_selector_window",
                "write_bytes",
                "write_text",
            }.isdisjoint(calls)
        )


if __name__ == "__main__":
    unittest.main()
