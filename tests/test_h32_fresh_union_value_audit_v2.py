from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_fresh_union_value_audit_v2 import (
    _target_outcome_signature,
    parse_h32_fresh_union_value_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-union-value-v2.json"


class H32FreshUnionValueAuditV2Tests(unittest.TestCase):
    def test_successor_changes_only_the_known_warm_start_gate(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_union_value_v2_config(config)
        self.assertEqual(parsed["maximum_warm_start_probability_error"], 1e-12)
        self.assertEqual(parsed["maximum_warm_start_mean_total_variation"], 1e-13)
        self.assertFalse(parsed["require_warm_start_digest_identity"])
        self.assertEqual(len(parsed["base"]["targets"]), 2)

        for field, value in (
            ("maximum_warm_start_probability_error", 1e-11),
            ("maximum_warm_start_mean_total_variation", 1e-12),
            ("require_warm_start_digest_identity", True),
        ):
            mutated = dict(config)
            mutated[field] = value
            with self.assertRaisesRegex(ValueError, "workload differs"):
                parse_h32_fresh_union_value_v2_config(mutated)

        mutated = dict(config)
        mutated["expected_failed_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_union_value_v2_config(mutated)

    def test_outcome_signature_excludes_timing_and_value(self) -> None:
        target = {
            "target": "target",
            "deadline_reason": "done",
            "shadow_selected_candidate_id": "union",
            "live_union_rows": [
                {
                    "candidate_id": "union",
                    "usable_before_emission_cutoff": True,
                    "positive_certified_value": 0.5,
                    "elapsed_completed_ms": 10.0,
                    "certificate": {
                        "complete": True,
                        "stop_reason": "complete",
                        "stop_seat": None,
                    },
                }
            ],
            "post_ledger_atomic_rows": [
                {
                    "acting_seat": 0,
                    "certificate": {
                        "complete": False,
                        "stop_reason": "blueprint_cap",
                        "stop_seat": 3,
                    },
                }
            ],
        }
        first = _target_outcome_signature(target)
        target["live_union_rows"][0]["positive_certified_value"] = 0.25
        target["live_union_rows"][0]["elapsed_completed_ms"] = 20.0
        self.assertEqual(first, _target_outcome_signature(target))


if __name__ == "__main__":
    unittest.main()
