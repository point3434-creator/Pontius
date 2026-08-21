from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.retrospective_atomic_value_capture import (
    _positive_reduction,
    _safe_ratio,
    parse_retrospective_atomic_value_capture_config,
)


_ROOT = Path(__file__).parents[1]


class RetrospectiveAtomicValueCaptureTests(unittest.TestCase):
    def test_contract_is_explicitly_post_hoc_and_hash_bound(self) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/retrospective-atomic-value-capture-v1.json").read_text(
                encoding="utf-8"
            )
        )
        parsed = parse_retrospective_atomic_value_capture_config(config)
        self.assertIn("not_preregistered", parsed["evidence_stage"])
        mutated = dict(config)
        mutated["expected_atomic_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_retrospective_atomic_value_capture_config(mutated)
        mutated = json.loads(json.dumps(config))
        mutated["gates"]["expected_atom_rows"] = 12
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_retrospective_atomic_value_capture_config(mutated)

    def test_value_and_fraction_accounting_are_fail_closed(self) -> None:
        self.assertEqual(_positive_reduction(2.0, 1.5), 0.5)
        self.assertEqual(_positive_reduction(1.0, 1.5), 0.0)
        self.assertEqual(_safe_ratio(0.5, 2.0), 0.25)
        self.assertIsNone(_safe_ratio(1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
