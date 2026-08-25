from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from pontius.exact_directional_face_oracle_seal import (
    ADR0354_CONTROL_MANIFEST,
    ADR0354_SOURCE_MANIFEST,
)
from pontius.factorized_tie_aware_affine_seal import (
    ADR0357_CONTROL_MANIFEST,
    ADR0357_PARENT_DECISION_SHA256,
    ADR0357_PROTOCOL,
    ADR0357_PROTOCOL_SHA256,
    ADR0357_SOURCE_MANIFEST,
)


ROOT = Path(__file__).resolve().parents[1]


def _canonical_lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(bytes((13, 10)), bytes((10,)))).hexdigest()


class FactorizedTieAwareAffineSealTests(unittest.TestCase):
    def test_parent_and_complete_successor_boundary_are_immutable(self) -> None:
        parent = (
            ROOT
            / "docs"
            / "decisions"
            / "ADR-0356-retain-and-rebind-the-legal-h4-directional-face-diagnostic.md"
        )
        self.assertEqual(_canonical_lf_sha256(parent), ADR0357_PARENT_DECISION_SHA256)
        for name, expected in ADR0357_SOURCE_MANIFEST.items():
            with self.subTest(source=name):
                self.assertEqual(
                    _canonical_lf_sha256(ROOT / "src" / "pontius" / name),
                    expected,
                )
        for name, expected in ADR0357_CONTROL_MANIFEST.items():
            with self.subTest(control=name):
                self.assertEqual(
                    _canonical_lf_sha256(ROOT / "tests" / name),
                    expected,
                )

    def test_historical_directional_face_boundary_remains_byte_valid(self) -> None:
        for name, expected in ADR0354_SOURCE_MANIFEST.items():
            with self.subTest(source=name):
                self.assertEqual(
                    _canonical_lf_sha256(ROOT / "src" / "pontius" / name),
                    expected,
                )
        for name, expected in ADR0354_CONTROL_MANIFEST.items():
            with self.subTest(control=name):
                self.assertEqual(
                    _canonical_lf_sha256(ROOT / "tests" / name),
                    expected,
                )

    def test_protocol_identity_and_semantic_types_are_immutable(self) -> None:
        payload = dict(ADR0357_PROTOCOL)
        actual = sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            ADR0357_PROTOCOL_SHA256,
            "8a5b053e1b792ae879f5d10cd8c7614ae69e33fe2033db0d0337388375e83d6a",
        )
        self.assertEqual(actual, ADR0357_PROTOCOL_SHA256)
        self.assertEqual(payload["face_materialization_bound"], None)
        self.assertEqual(payload["tape_cartesian_product"], "forbidden")
        self.assertEqual(
            payload["exact_source_tie_dispatch"],
            "factorized_tie_aware_maximum_envelope",
        )
        self.assertEqual(payload["singleton_dispatch"], "selector_window_v2")
        self.assertEqual(payload["certificate_identity_authority"], "total_function_only")
        self.assertEqual(payload["reachable_identity_role"], "reporting_only")
        self.assertEqual(payload["historical_tie_registry_mutated"], False)


if __name__ == "__main__":
    unittest.main()
