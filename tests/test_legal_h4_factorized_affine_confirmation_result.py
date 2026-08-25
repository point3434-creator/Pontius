from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_h4_factorized_affine_confirmation_result import (
    ADR0362_ARTIFACT_BYTES,
    ADR0362_ARTIFACT_RELATIVE_PATH,
    ADR0362_ARTIFACT_SHA256,
    ADR0362_CONFIG_SHA256,
    ADR0362_INVOCATION_SOURCE_COMMIT,
    ADR0362_RESULT_PROTOCOL_SHA256,
    _canonical_hash,
    _contains_outcome_key,
    _load_json,
    _row_growth_semantic_payload,
    _verify_config,
    _verify_record,
    verify_adr0362_legal_h4_factorized_affine_confirmation_artifact,
)
from pontius.legal_h4_factorized_affine_confirmation_result_seal import (
    ADR0362_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0362_RESULT_SOURCE_MANIFEST,
)


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / ADR0362_ARTIFACT_RELATIVE_PATH
OWNER = (
    ROOT
    / "src/pontius/legal_h4_factorized_affine_confirmation_result.py"
)
CONSUMED_RUNNER = ROOT / "src/pontius/legal_h4_factorized_affine_confirmation.py"


def _rehash_face(face: dict[str, object]) -> None:
    face["factor_sha256"] = _canonical_hash(
        {
            "information_sets": face["information_sets"],
            "reachable_support_cardinality": face["reachable_support_cardinality"],
            "total_function_cardinality": face["total_function_cardinality"],
        }
    )
    face["face_sha256"] = _canonical_hash(
        {key: value for key, value in face.items() if key != "face_sha256"}
    )


def _rehash_complete(complete: dict[str, object]) -> None:
    raw = complete["raw_section"]
    assert isinstance(raw, dict)
    fan = raw["fan"]
    assert isinstance(fan, dict)
    fan["fan_sha256"] = _canonical_hash(
        {key: value for key, value in fan.items() if key != "fan_sha256"}
    )
    raw["section_sha256"] = _canonical_hash(
        {key: value for key, value in raw.items() if key != "section_sha256"}
    )
    complete["complete_section_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in complete.items()
            if key != "complete_section_sha256"
        }
    )


class LegalH4FactorizedAffineConfirmationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verified = (
            verify_adr0362_legal_h4_factorized_affine_confirmation_artifact()
        )
        cls.record = _load_json(ARTIFACT.read_bytes())
        cls.config = _verify_config()

    def test_exact_bytes_config_commit_and_protocol_are_bound(self) -> None:
        raw = ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0362_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0362_ARTIFACT_SHA256)
        self.assertEqual(self.verified.artifact_bytes, 7_361_728)
        self.assertEqual(
            self.verified.source_commit,
            ADR0362_INVOCATION_SOURCE_COMMIT,
        )
        self.assertEqual(self.verified.record["config_sha256"], ADR0362_CONFIG_SHA256)
        self.assertEqual(
            ADR0362_RESULT_PROTOCOL_SHA256,
            "f4e2dc05ad8e8337f6c05853302af90866fdd0324c40d593a977434656f6c703",
        )
        canonical = OWNER.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(ADR0362_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            ADR0362_RESULT_SOURCE_MANIFEST[OWNER.name],
            hashlib.sha256(canonical).hexdigest(),
        )

    def test_recorded_rejection_and_scientific_rebind_remain_distinct(self) -> None:
        self.assertFalse(self.verified.recorded_passed)
        self.assertEqual(
            self.verified.recorded_decision,
            "reject_untouched_legal_h4_factorized_affine_confirmation",
        )
        self.assertTrue(self.verified.scientific_payload_rebound)
        self.assertTrue(self.verified.intended_zero_emission_predicate)
        self.assertTrue(self.verified.corrected_gate_vector["passed"])
        self.assertFalse(self.verified.record["gates"]["zero_actions_and_quality_rows"])
        self.assertEqual(self.verified.record["actions_emitted"], 0)
        self.assertEqual(self.verified.record["quality_rows_serialized"], 0)
        self.assertEqual(self.verified.record["strategy_labels_generated"], 0)
        self.assertIsNone(self.verified.record["strategy_quality_claim"])

    def test_complete_fresh_population_observations_rebind(self) -> None:
        _verify_record(self.record, self.config)
        self.assertEqual(self.record["section_count"], 32)
        self.assertEqual(
            self.record["observations"]["mode_counts"],
            {
                "factorized_tie_aware_maximum_envelope": 4,
                "v2_single_tape": 28,
            },
        )
        self.assertEqual(
            self.record["observations"]["maximum_total_function_cardinality"],
            2,
        )
        self.assertEqual(
            self.record["observations"]["maximum_reachable_support_cardinality"],
            2,
        )
        self.assertEqual(len(self.record["observations"]["piece_counts"]), 32)
        self.assertEqual(
            sum(
                target["section_subject_seconds"]
                for context in self.record["contexts"]
                for direction in context["directions"]
                for target in direction["targets"]
            ),
            self.record["subject_seconds"],
        )

    def test_result_owner_is_standard_library_and_read_only(self) -> None:
        tree = ast.parse(OWNER.read_text(encoding="utf-8"))
        imports = set()
        calls = []
        attributes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                calls.append(node.func.id if isinstance(node.func, ast.Name) else "")
            elif isinstance(node, ast.Attribute):
                attributes.append(node.attr)
        allowed_roots = {
            "__future__",
            "dataclasses",
            "fractions",
            "hashlib",
            "json",
            "math",
            "pathlib",
            "types",
            "typing",
        }
        self.assertTrue(all(name.split(".")[0] in allowed_roots for name in imports))
        self.assertNotIn("open", calls)
        self.assertFalse(
            {"write_bytes", "write_text", "unlink", "rename"}
            & set(attributes)
        )

    def test_rehashed_non_source_factor_mutation_fails_closed(self) -> None:
        changed = deepcopy(self.record)
        complete = changed["contexts"][0]["directions"][0]["targets"][0][
            "complete_evidence"
        ]
        face = complete["raw_section"]["samples"][1]["face"]
        factor = face["information_sets"][0]
        factor["maximum_slope_action"] = "not-an-active-action"
        _rehash_face(face)
        _rehash_complete(complete)
        with self.assertRaises(ValueError):
            _verify_record(changed, self.config)

    def test_rehashed_epigraph_and_piece_mutations_fail_closed(self) -> None:
        epigraph = deepcopy(self.record)
        complete = epigraph["contexts"][0]["directions"][0]["targets"][0][
            "complete_evidence"
        ]
        complete["epigraph_residual_matrix"][0]["rows"][0]["residual"][
            "numerator"
        ] += 1
        _rehash_complete(complete)
        with self.assertRaises(ValueError):
            _verify_record(epigraph, self.config)

        piece = deepcopy(self.record)
        complete = piece["contexts"][0]["directions"][0]["targets"][0][
            "complete_evidence"
        ]
        complete["pieces"][0]["intercept"]["numerator"] += 1
        _rehash_complete(complete)
        with self.assertRaises(ValueError):
            _verify_record(piece, self.config)

    def test_rehashed_row_growth_cap_mutation_fails_closed(self) -> None:
        changed = deepcopy(self.record)
        row_growth = changed["contexts"][0]["row_growth"]
        row_growth["caps_exact"][0]["numerator"] += 1
        row_growth["row_growth_semantic_sha256"] = _canonical_hash(
            _row_growth_semantic_payload(row_growth)
        )
        with self.assertRaises(ValueError):
            _verify_record(changed, self.config)

    def test_timing_is_excluded_but_science_is_included_in_row_growth_digest(self) -> None:
        row_growth = deepcopy(self.record["contexts"][0]["row_growth"])
        baseline = _canonical_hash(_row_growth_semantic_payload(row_growth))
        row_growth["iterations"][0]["master_solve_seconds"] += 10.0
        self.assertEqual(
            _canonical_hash(_row_growth_semantic_payload(row_growth)), baseline
        )
        row_growth["caps_exact"][0]["numerator"] += 1
        self.assertNotEqual(
            _canonical_hash(_row_growth_semantic_payload(row_growth)), baseline
        )

    def test_emission_gate_and_coordinate_mutations_fail_closed(self) -> None:
        emission = deepcopy(self.record)
        emission["actions_emitted"] = 1
        with self.assertRaises(ValueError):
            _verify_record(emission, self.config)

        gate = deepcopy(self.record)
        gate["gates"]["zero_actions_and_quality_rows"] = True
        gate["gates"]["passed"] = True
        gate["passed"] = True
        with self.assertRaises(ValueError):
            _verify_record(gate, self.config)

        coordinate = deepcopy(self.record)
        coordinate["contexts"][0]["directions"][1]["targets"][0][
            "direction_label"
        ] = coordinate["contexts"][0]["directions"][0]["label"]
        with self.assertRaises(ValueError):
            _verify_record(coordinate, self.config)

    def test_duplicate_keys_outer_byte_and_config_outcome_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            _load_json(b'{"duplicate":1,"duplicate":2}\n')
        self.assertTrue(_contains_outcome_key({"nested": [{"mode_counts": {}}]}))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "copy.json"
            changed = deepcopy(self.record)
            changed["campaign_seconds"] += 0.001
            path.write_text(
                json.dumps(changed, allow_nan=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                verify_adr0362_legal_h4_factorized_affine_confirmation_artifact(path)

    def test_mapping_literal_chain_is_a_single_named_consumed_tombstone(self) -> None:
        hits = []
        for path in sorted((ROOT / "src/pontius").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Compare)
                    and len(node.ops) > 1
                    and (
                        isinstance(node.left, (ast.Dict, ast.Set))
                        or any(
                            isinstance(item, (ast.Dict, ast.Set))
                            for item in node.comparators
                        )
                    )
                ):
                    hits.append((path.name, node.lineno, ast.unparse(node)))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], CONSUMED_RUNNER.name)
        self.assertIn("emissions ==", hits[0][2])
        self.assertIn("require_zero_actions_and_quality_rows", hits[0][2])


if __name__ == "__main__":
    unittest.main()
