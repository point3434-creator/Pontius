from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from pontius.exact_directional_face_oracle_seal import (
    ADR0354_CONTROL_MANIFEST,
    ADR0354_PARENT_DECISION_SHA256,
    ADR0354_PROTOCOL,
    ADR0354_PROTOCOL_SHA256,
    ADR0354_SOURCE_MANIFEST,
)


ROOT = Path(__file__).resolve().parents[1]


def _canonical_lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class ExactDirectionalFaceOracleSealTests(unittest.TestCase):
    def test_parent_and_complete_source_boundary_are_immutable(self) -> None:
        parent = (
            ROOT
            / "docs"
            / "decisions"
            / "ADR-0353-retain-the-legal-h4-tie-aware-bound-rejection.md"
        )
        self.assertEqual(
            _canonical_lf_sha256(parent),
            ADR0354_PARENT_DECISION_SHA256,
        )
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

    def test_protocol_identity_and_claim_boundary_are_immutable(self) -> None:
        payload = dict(ADR0354_PROTOCOL)
        actual = sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            ADR0354_PROTOCOL_SHA256,
            "cfd37e22b4e3e09321b20f6d6f3bef93f4b8fd35af6ecd13d2166ba3aee7dabf",
        )
        self.assertEqual(actual, ADR0354_PROTOCOL_SHA256)
        self.assertEqual(payload["face_tape_bound"], None)
        self.assertEqual(
            payload["face_instrument"],
            "two_independent_lexicographic_backward_passes",
        )
        self.assertEqual(payload["materialized_response_tapes"], 0)
        self.assertEqual(payload["maximum_fan_pieces_default"], 256)
        self.assertEqual(payload["maximum_tree_nodes_default"], 100_000)
        self.assertEqual(
            payload["cardinality_columns"],
            ("total_function", "reachable_support"),
        )
        self.assertIsInstance(payload["source_manifest"], tuple)
        self.assertIsInstance(payload["control_manifest"], tuple)
        self.assertEqual(
            payload["future_crossing_control"],
            "dominated_source_row_crosses_inside_section",
        )


if __name__ == "__main__":
    unittest.main()
