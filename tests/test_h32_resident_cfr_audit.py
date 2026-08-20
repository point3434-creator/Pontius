from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_resident_cfr_audit import parse_h32_resident_cfr_config


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v1.json"


class H32ResidentCFRAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_customer_controls_and_charges(self) -> None:
        parsed = parse_h32_resident_cfr_config(self.config)
        self.assertEqual(parsed["trajectory_iterations"], (1, 2))
        self.assertEqual(parsed["small_control_hands_per_player"], 7)
        self.assertEqual(
            parsed["cache_charge"],
            "one_complete_six_seat_cache_per_target",
        )
        self.assertEqual(len(parsed["engine_order_by_target"]), 4)
        self.assertEqual(
            parsed["gates"]["minimum_each_target_two_step_cache_charged_speedup"],
            1.5,
        )

    def test_config_rejects_post_freeze_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["gates"]["minimum_each_target_two_step_cache_charged_speedup"] = 1.0
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_resident_cfr_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_resident_cfr_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_resident_cfr_config(changed)


if __name__ == "__main__":
    unittest.main()
