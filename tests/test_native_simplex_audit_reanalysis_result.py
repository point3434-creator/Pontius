from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/native-simplex-audit-corrected-gate-v1.json"
_FILE_BYTES = 1_169
_FILE_SHA256 = "d8ce7c26d935768f8476c183950e96e5be2692fac5e821bf9b674d373ae665c1"
_ASSESSMENT_SHA256 = "f44d518bba0953c064cd04c3015c37ec8abf27a91a96afa9902caf16c8ffe038"
_ANALYZER_SHA256 = "0755546e6260708ffb4165ec50ebf4ff88c473354faeb7303e8b84e568fca1be"
_ARTIFACT_SHA256 = "1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a"
_FAILING_ROWS = (
    0,
    2,
    5,
    6,
    12,
    13,
    50,
    51,
    64,
    71,
    89,
    99,
    122,
    129,
    146,
    147,
    157,
    166,
    167,
    205,
    215,
)


class NativeSimplexAuditReanalysisResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = _RESULT.read_bytes()
        cls.payload = cls.raw[:-1]
        cls.decoded = json.loads(cls.payload)
        cls.fields = cls.decoded["fields"]

    def test_file_and_canonical_assessment_identities_are_exact(self) -> None:
        self.assertEqual(len(self.raw), _FILE_BYTES)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertFalse(self.payload.endswith(b"\n"))
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), _FILE_SHA256)
        self.assertEqual(
            hashlib.sha256(self.payload).hexdigest(),
            _ASSESSMENT_SHA256,
        )
        rebuilt = json.dumps(
            self.decoded,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        self.assertEqual(rebuilt, self.payload)

    def test_corrected_gate_passes_only_after_complete_unchanged_checks(self) -> None:
        self.assertEqual(
            self.decoded["dataclass"],
            "pontius.native_simplex_audit_reanalysis.CorrectedAuditGateAssessment",
        )
        self.assertEqual(self.fields["analyzer_source_sha256"], _ANALYZER_SHA256)
        self.assertEqual(self.fields["artifact_sha256"], _ARTIFACT_SHA256)
        self.assertEqual(self.fields["artifact_bytes"], 110_068_679)
        self.assertTrue(self.fields["complete_schedule"])
        self.assertEqual(self.fields["observation_count"], 2_655)
        self.assertEqual(self.fields["variant_count"], 885)
        self.assertEqual(self.fields["base_count"], 177)
        self.assertEqual(self.fields["highs_ds_verified_count"], 885)
        self.assertEqual(self.fields["highs_ipm_verified_count"], 885)
        self.assertEqual(self.fields["native_verified_count"], 849)
        self.assertEqual(self.fields["native_exception_count"], 36)
        self.assertEqual(self.fields["failures"], [])
        self.assertTrue(self.fields["highs_dual_simplex_eligible"])

    def test_known_regression_reproduces_nonexclusive_unique_maximum(self) -> None:
        self.assertTrue(self.fields["known_native_regression_reproduced"])
        evidence = self.fields["known_native_regression"]["fields"]
        self.assertEqual(tuple(evidence["failing_rows"]), _FAILING_ROWS)
        self.assertEqual(evidence["unique_maximum_rows"], [215])
        self.assertEqual(evidence["pivots"], 375)
        self.assertEqual(
            evidence["maximum_residual"],
            {"float_hex": "0x1.032cad8b12778p+2"},
        )
        self.assertEqual(
            evidence["verification_allowance"],
            {"float_hex": "0x1.68c6fa0b2f9a2p-25"},
        )


if __name__ == "__main__":
    unittest.main()
