from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_resident_cfr_sustained_audit import (
    parse_h32_resident_cfr_sustained_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-resident-cfr-sustained-audit-v1.json"
)


class H32ResidentCFRSustainedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_sustained_teacher_and_restart_contract(self) -> None:
        parsed = parse_h32_resident_cfr_sustained_config(self.config)
        self.assertEqual(parsed["comparison_iterations"], (1, 2, 4, 8))
        self.assertEqual(parsed["final_iteration"], 8)
        self.assertEqual(parsed["restart_control"]["split_iteration"], 4)
        self.assertEqual(parsed["gates"]["maximum_restart_regret_error"], 0.0)
        self.assertTrue(parsed["gates"]["require_restart_state_digest_identity"])
        self.assertEqual(
            parsed["gates"]["minimum_each_target_eight_step_cache_charged_speedup"],
            1.5,
        )

    def test_config_rejects_post_freeze_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_teacher_regret_error"] = 1e-8
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_resident_cfr_sustained_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_resident_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_resident_cfr_sustained_config(changed)


if __name__ == "__main__":
    unittest.main()
