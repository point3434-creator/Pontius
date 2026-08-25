from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_responder_raise_h4_directional_face_result import (
    ADR0356_ARTIFACT_BYTES,
    ADR0356_ARTIFACT_RELATIVE_PATH,
    ADR0356_ARTIFACT_SHA256,
    ADR0356_CONFIG_SHA256,
    ADR0356_INVOCATION_SOURCE_COMMIT,
    ADR0356_RESULT_PROTOCOL_SHA256,
    _canonical_hash,
    _load_json,
    _verify_config,
    _verify_record,
    verify_adr0356_legal_h4_directional_face_result_artifact,
)
from pontius.legal_responder_raise_h4_directional_face_result_seal import (
    ADR0356_RESULT_PROTOCOL_SHA256 as SEALED_PROTOCOL,
    ADR0356_RESULT_SOURCE_MANIFEST,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = _ROOT / ADR0356_ARTIFACT_RELATIVE_PATH
_OWNER = (
    _ROOT
    / "src/pontius/legal_responder_raise_h4_directional_face_result.py"
)


def _rehash_section(section: dict[str, object], *, fan: bool = False) -> None:
    if fan:
        fan_record = section["fan"]
        payload = dict(fan_record)
        payload.pop("fan_sha256")
        fan_record["fan_sha256"] = _canonical_hash(payload)
    payload = dict(section)
    payload.pop("section_sha256")
    section["section_sha256"] = _canonical_hash(payload)


class LegalResponderRaiseH4DirectionalFaceResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verified = verify_adr0356_legal_h4_directional_face_result_artifact()
        cls.record = _load_json(_ARTIFACT.read_bytes())
        cls.config = _verify_config()

    def test_source_protocol_and_artifact_are_sealed(self) -> None:
        canonical = _OWNER.read_bytes().replace(bytes([13, 10]), bytes([10]))
        self.assertEqual(ADR0356_RESULT_PROTOCOL_SHA256, SEALED_PROTOCOL)
        self.assertEqual(
            ADR0356_RESULT_SOURCE_MANIFEST[_OWNER.name],
            hashlib.sha256(canonical).hexdigest(),
        )
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0356_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0356_ARTIFACT_SHA256)
        self.assertEqual(self.verified.artifact_bytes, ADR0356_ARTIFACT_BYTES)
        self.assertEqual(self.verified.source_commit, ADR0356_INVOCATION_SOURCE_COMMIT)
        self.assertEqual(self.verified.record["config_sha256"], ADR0356_CONFIG_SHA256)

    def test_complete_result_rebinds_without_scientific_imports(self) -> None:
        _verify_record(self.record, self.config)
        aggregate = self.verified.record["aggregate"]
        self.assertEqual(aggregate["sections"], 8)
        self.assertEqual(aggregate["schedule_face_calls"], 136)
        self.assertEqual(aggregate["maximum_total_function_cardinality"], 104_976)
        self.assertEqual(aggregate["maximum_reachable_support_cardinality"], 2)
        self.assertEqual(aggregate["materialized_response_tapes"], 0)
        self.assertEqual(aggregate["total_logical_work_units"], 147_418)
        self.assertTrue(all(self.verified.record["gates"].values()))

    def test_result_owner_is_solver_free_and_read_only(self) -> None:
        tree = ast.parse(_OWNER.read_text(encoding="utf-8"))
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
        forbidden = (
            "cfr",
            "evaluation",
            "game",
            "oracle",
            "optimizer",
            "runner",
            "selector",
        )
        self.assertFalse(any(any(token in name for token in forbidden) for name in imports))
        self.assertNotIn("open", calls)
        self.assertFalse({"write_bytes", "write_text", "unlink"} & set(attributes))

    def test_fraction_factor_and_work_mutations_fail_closed(self) -> None:
        mutations = []
        gain = deepcopy(self.record)
        gain_face = gain["directions"][0]["target_rows"][0]["schedule"][0]["face"]
        gain_face["deviation_gain"]["numerator"] += 1
        mutations.append(gain)

        cardinality = deepcopy(self.record)
        card_face = cardinality["directions"][0]["target_rows"][0]["schedule"][0]["face"]
        card_face["total_function_cardinality"] += 1
        card_face["factor_sha256"] = _canonical_hash(
            {
                "total_function_cardinality": card_face["total_function_cardinality"],
                "reachable_support_cardinality": card_face[
                    "reachable_support_cardinality"
                ],
                "information_sets": card_face["information_sets"],
            }
        )
        mutations.append(cardinality)

        work = deepcopy(self.record)
        work_face = work["directions"][0]["target_rows"][0]["schedule"][0]["face"]
        work_face["work"]["lexicographic_passes"] = 1
        mutations.append(work)

        for mutation in mutations:
            with self.subTest():
                with self.assertRaises(ValueError):
                    _verify_record(mutation, self.config)

    def test_reachable_projection_and_tie_state_mutations_fail_closed(self) -> None:
        projection = deepcopy(self.record)
        section = projection["directions"][0]["target_rows"][0]["composed_section"]
        point = section["fan"]["points"][0]
        point["reachable_tape"] = []
        _rehash_section(section, fan=True)
        with self.assertRaises(ValueError):
            _verify_record(projection, self.config)

        state = deepcopy(self.record)
        section = state["directions"][0]["target_rows"][0]["composed_section"]
        section["fan"]["segments"][0]["total_state"] = "switched"
        _rehash_section(section, fan=True)
        with self.assertRaises(ValueError):
            _verify_record(state, self.config)

    def test_fan_geometry_and_envelope_mutations_fail_closed(self) -> None:
        geometry = deepcopy(self.record)
        section = geometry["directions"][0]["target_rows"][1]["composed_section"]
        section["fan"]["cells"][0]["upper"] = {
            "numerator": 1,
            "denominator": 100,
        }
        _rehash_section(section, fan=True)
        with self.assertRaises(ValueError):
            _verify_record(geometry, self.config)

        envelope = deepcopy(self.record)
        section = envelope["directions"][0]["target_rows"][0]["composed_section"]
        section["cell_gain_rows"][0]["intercept"]["numerator"] += 1
        _rehash_section(section)
        with self.assertRaises(ValueError):
            _verify_record(envelope, self.config)

    def test_aggregate_gate_and_duplicate_key_mutations_fail_closed(self) -> None:
        aggregate = deepcopy(self.record)
        aggregate["aggregate"]["maximum_total_function_cardinality"] -= 1
        with self.assertRaises(ValueError):
            _verify_record(aggregate, self.config)

        gate = deepcopy(self.record)
        gate["gates"]["passed"] = False
        with self.assertRaises(ValueError):
            _verify_record(gate, self.config)

        with self.assertRaises(ValueError):
            _load_json(b'{"duplicate":1,"duplicate":2}\n')

    def test_outer_byte_identity_rejects_even_semantically_valid_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "copy.json"
            record = deepcopy(self.record)
            record["analysis_seconds"] += 0.001
            path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_adr0356_legal_h4_directional_face_result_artifact(path)


if __name__ == "__main__":
    unittest.main()
