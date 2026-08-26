from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = (
    _ROOT / "experiments/results/legal-river-exact-cubin-inspector-selection-v1.json"
)
_FILE_BYTES = 3_164
_FILE_SHA256 = "ebc66a0d06a84eeb16d5c2d6adf6376227011ef3982c8fcdd09e97496c276d1f"
_CANONICAL_SHA256 = (
    "e5748ad72fd5182a2835c789ef32095a73d452db8c31f9e48dd48f3f229a311a"
)


class ExactCubinInspectorSelectionResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = _RESULT.read_bytes()
        cls.payload = cls.raw[:-1]
        cls.decoded = json.loads(cls.payload)
        cls.fields = cls.decoded["fields"]

    def test_file_and_canonical_payload_identities_are_exact(self) -> None:
        self.assertEqual(len(self.raw), _FILE_BYTES)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertFalse(self.payload.endswith(b"\n"))
        self.assertEqual(sha256(self.raw).hexdigest(), _FILE_SHA256)
        self.assertEqual(sha256(self.payload).hexdigest(), _CANONICAL_SHA256)
        rebuilt = json.dumps(
            self.decoded,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        self.assertEqual(rebuilt, self.payload)

    def test_selector_returns_honest_empty_selection(self) -> None:
        self.assertEqual(
            self.decoded["dataclass"],
            "pontius.legal_river_exact_cubin_inspector_selection.InspectorSelectionAssessment",
        )
        self.assertEqual(self.fields["terminal"], "no_qualified_inspector")
        self.assertTrue(self.fields["identity_contract_pass"])
        self.assertIsNone(self.fields["selected_inspector"])
        self.assertIsNone(self.fields["selected_resource_rows"])
        self.assertIsNone(self.fields["combined_direct_rows"])
        self.assertIsNone(self.fields["resource_gate_result"])
        self.assertIsNone(self.fields["calibration_result"])
        self.assertIsNone(self.fields["capacity_projection"])
        self.assertNotIn("passed", self.fields)

    def test_only_semantically_eligible_candidate_is_rejected_by_return_code(self) -> None:
        rows = self.fields["candidate_assessments"]
        self.assertEqual(
            [row["candidate_id"] for row in rows],
            [
                "cuobjdump_version",
                "cuobjdump_resource_usage",
                "cuobjdump_elf",
                "nvdisasm_version",
                "nvdisasm_default",
            ],
        )
        self.assertEqual(rows[0]["qualification_status"], "identity_support_pass")
        self.assertEqual(rows[1]["return_code"], 4_294_967_295)
        self.assertEqual(
            rows[1]["qualification_status"], "resource_candidate_rejected"
        )
        self.assertEqual(rows[1]["reasons"], ["resource_return_code_nonzero"])
        self.assertTrue(rows[1]["selectable"])
        for row in rows[2:]:
            self.assertFalse(row["selectable"])
            self.assertEqual(row["qualification_status"], "ineligible_support_only")


if __name__ == "__main__":
    unittest.main()
