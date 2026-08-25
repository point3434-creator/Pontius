from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_responder_raise_h4_factorized_affine_result import (
    ADR0359_ARTIFACT_BYTES,
    ADR0359_ARTIFACT_RELATIVE_PATH,
    ADR0359_ARTIFACT_SHA256,
    ADR0359_CONFIG_SHA256,
    ADR0359_INVOCATION_SOURCE_COMMIT,
    ADR0359_RESULT_PROTOCOL_SHA256,
    _canonical_hash,
    _load_json,
    _verify_config,
    _verify_record,
    verify_adr0359_legal_h4_factorized_affine_result_artifact,
)
from pontius.legal_responder_raise_h4_factorized_affine_result_seal import (
    ADR0359_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0359_RESULT_SOURCE_MANIFEST,
)


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / ADR0359_ARTIFACT_RELATIVE_PATH
OWNER = (
    ROOT
    / "src/pontius/legal_responder_raise_h4_factorized_affine_result.py"
)


def _rehash(integration: dict[str, object]) -> None:
    payload = dict(integration)
    payload.pop("integration_sha256")
    integration["integration_sha256"] = _canonical_hash(payload)


class LegalResponderRaiseH4FactorizedAffineResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verified = verify_adr0359_legal_h4_factorized_affine_result_artifact()
        cls.record = _load_json(ARTIFACT.read_bytes())
        cls.config = _verify_config()

    def test_exact_artifact_config_commit_and_protocol_are_bound(self) -> None:
        raw = ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0359_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0359_ARTIFACT_SHA256)
        self.assertEqual(self.verified.artifact_bytes, ADR0359_ARTIFACT_BYTES)
        self.assertEqual(
            self.verified.source_commit,
            ADR0359_INVOCATION_SOURCE_COMMIT,
        )
        self.assertEqual(self.verified.record["config_sha256"], ADR0359_CONFIG_SHA256)
        self.assertEqual(
            ADR0359_RESULT_PROTOCOL_SHA256,
            "8d78d45a45e9988950747e40d4ee04c3e71176bdde32ef39c275d54aecb7ebda",
        )
        canonical = OWNER.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(ADR0359_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            ADR0359_RESULT_SOURCE_MANIFEST[OWNER.name],
            hashlib.sha256(canonical).hexdigest(),
        )

    def test_complete_stored_result_rebinds_with_calibrated_observations(self) -> None:
        _verify_record(self.record, self.config)
        aggregate = self.verified.record["aggregate"]
        self.assertEqual(aggregate["sections"], 8)
        self.assertEqual(
            aggregate["mode_counts"],
            {
                "factorized_tie_aware_maximum_envelope": 4,
                "fail_closed_single_tape": 0,
                "v2_single_tape": 4,
            },
        )
        self.assertEqual(aggregate["fan_cells"], 12)
        self.assertEqual(aggregate["point_face_observations"], 28)
        self.assertEqual(aggregate["maximum_total_function_cardinality"], 2)
        self.assertEqual(aggregate["maximum_reachable_support_cardinality"], 2)
        self.assertEqual(aggregate["materialized_response_tapes"], 0)
        self.assertEqual(aggregate["subject_seconds"], 18.1520871000248)
        self.assertTrue(all(self.verified.record["gates"].values()))

    def test_fan_rows_and_compact_envelope_pieces_remain_distinct(self) -> None:
        aggregate = self.verified.record["aggregate"]
        self.assertEqual(aggregate["fan_cells"], 12)
        self.assertEqual(sum(aggregate["piece_counts"]), 10)
        root_responder = self.verified.record["directions"][2]["target_rows"][1]
        self.assertEqual(root_responder["integration"]["fan_counts"]["cells"], 2)
        self.assertEqual(len(root_responder["integration"]["pieces"]), 1)
        self.assertEqual(
            root_responder["integration"]["point_summary"][-1]["active_cell_rows"],
            2,
        )

    def test_authenticated_only_boundary_is_explicit(self) -> None:
        self.assertEqual(
            self.verified.authenticated_only_fields,
            (
                "non_source_point_factor_cardinality_and_active_face_fields",
                "non_quotient_fan_rows_and_individual_epigraph_residuals",
                "reproduced_section_sha256",
            ),
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
        self.assertFalse({"write_bytes", "write_text", "unlink"} & set(attributes))

    def test_rehashed_source_algebra_and_factor_mutations_fail_closed(self) -> None:
        algebra = deepcopy(self.record)
        integration = algebra["directions"][0]["target_rows"][0]["integration"]
        integration["source_face"]["deviation_gain"]["numerator"] += 1
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(algebra, self.config)

        factor = deepcopy(self.record)
        integration = factor["directions"][0]["target_rows"][0]["integration"]
        integration["source_face"]["factor_sha256"] = "0" * 64
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(factor, self.config)

    def test_rehashed_envelope_dispatch_and_endpoint_mutations_fail_closed(self) -> None:
        envelope = deepcopy(self.record)
        integration = envelope["directions"][0]["target_rows"][1]["integration"]
        integration["point_summary"][1]["deviation_gain"]["numerator"] += 1
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(envelope, self.config)

        dispatch = deepcopy(self.record)
        integration = dispatch["directions"][0]["target_rows"][0]["integration"]
        integration["mode"] = "v2_single_tape"
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(dispatch, self.config)

        endpoint = deepcopy(self.record)
        integration = endpoint["directions"][2]["target_rows"][1]["integration"]
        integration["point_summary"][-1]["active_cell_rows"] = 3
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(endpoint, self.config)

    def test_rehashed_parent_aggregate_and_gate_mutations_fail_closed(self) -> None:
        parent = deepcopy(self.record)
        integration = parent["directions"][0]["target_rows"][0]["integration"]
        integration["parent_section_sha256"] = "0" * 64
        integration["reproduced_section_sha256"] = "0" * 64
        _rehash(integration)
        with self.assertRaises(ValueError):
            _verify_record(parent, self.config)

        aggregate = deepcopy(self.record)
        aggregate["aggregate"]["fan_cells"] -= 1
        with self.assertRaises(ValueError):
            _verify_record(aggregate, self.config)

        gate = deepcopy(self.record)
        gate["gates"]["section_identity"] = False
        with self.assertRaises(ValueError):
            _verify_record(gate, self.config)

    def test_duplicate_keys_and_outer_byte_mutation_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            _load_json(b'{"duplicate":1,"duplicate":2}\n')

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "copy.json"
            record = deepcopy(self.record)
            record["analysis_seconds"] += 0.001
            path.write_text(
                json.dumps(record, allow_nan=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                verify_adr0359_legal_h4_factorized_affine_result_artifact(path)


if __name__ == "__main__":
    unittest.main()
