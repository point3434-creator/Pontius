from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_resident_verifier_audit import (
    _PARENT,
    _parent_target,
    parse_h32_resident_verifier_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-verifier-audit-v1.json"


class H32ResidentVerifierAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_residency_customer_and_economics(self) -> None:
        parsed = parse_h32_resident_verifier_config(self.config)
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 384)
        self.assertEqual(
            parsed["cache_charge"],
            "one_complete_six_seat_cache_per_target",
        )
        self.assertEqual(parsed["fresh_target_seats"], (0, 3))
        self.assertEqual(
            parsed["gates"]["minimum_pooled_calibrated_speedup"],
            1.5,
        )
        self.assertEqual(parsed["gates"]["maximum_gpu_pool_bytes"], 12_000_000_000)

    def test_config_rejects_post_freeze_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["gates"]["minimum_pooled_calibrated_speedup"] = 1.0
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_resident_verifier_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_resident_contraction_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_resident_verifier_config(changed)

    def test_parent_target_lookup_covers_the_four_frozen_customers(self) -> None:
        parent = json.loads(_PARENT.read_text(encoding="utf-8"))
        rows = [
            _parent_target(parent, family=family, shift=shift)
            for family in ("balanced", "blocker_heavy")
            for shift in ("local_blocker_seat3_x2", "all_seat_strength_1_to2")
        ]
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            sum(row["economics"]["live_seat_evaluations"] for row in rows),
            133,
        )
        self.assertEqual(
            sum(row["economics"]["complete_candidate_rows"] for row in rows),
            13,
        )


if __name__ == "__main__":
    unittest.main()
