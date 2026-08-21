from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_fresh_union_value_audit import (
    _positive_value,
    _safe_ratio,
    parse_h32_fresh_union_value_config,
    union_keys_by_seat,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-union-value-v1.json"


class H32FreshUnionValueAuditTests(unittest.TestCase):
    def test_contract_rejects_target_library_source_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_union_value_config(config)
        self.assertIn("before_any_seat4_target", parsed["evidence_stage"])

        mutated = json.loads(json.dumps(config))
        mutated["targets"][0]["target_belief_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_union_value_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["union_library"][0]["acting_seats"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_union_value_config(mutated)

        mutated = dict(config)
        mutated["expected_source_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_union_value_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["expected_post_ledger_atomic_labels"] = 6
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_fresh_union_value_config(mutated)

    def test_union_keys_are_seat_exact_and_fail_closed(self) -> None:
        manifest = [
            {"acting_seat": seat, "information_key": f"key-{seat}"}
            for seat in range(6)
        ]
        self.assertEqual(
            union_keys_by_seat(manifest, [0, 2, 5]),
            ("key-0", "key-2", "key-5"),
        )
        with self.assertRaisesRegex(ValueError, "cannot be resolved"):
            union_keys_by_seat(manifest, [0, 6])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            union_keys_by_seat(manifest + [manifest[0]], [0])

    def test_value_accounting_has_no_zero_denominator_escape(self) -> None:
        self.assertEqual(_positive_value(2.0, 1.5), 0.5)
        self.assertEqual(_positive_value(1.0, 1.5), 0.0)
        self.assertEqual(_safe_ratio(0.5, 2.0), 0.25)
        self.assertIsNone(_safe_ratio(1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
