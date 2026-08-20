from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_resident_cfr_audit_v2 import (
    parse_h32_resident_cfr_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v2.json"


class H32ResidentCFRV2AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_successor_changes_only_cross_run_identity_semantics(self) -> None:
        parsed = parse_h32_resident_cfr_v2_config(self.config)
        self.assertEqual(
            parsed["rerun_protocol"],
            "execute_immutable_v1_workload_and_all_v1_speed_gates",
        )
        self.assertEqual(
            parsed["gates"]["maximum_legacy_teacher_regret_error"],
            1e-12,
        )
        self.assertEqual(
            parsed["gates"]["minimum_each_target_two_step_cache_charged_speedup"],
            1.5,
        )

    def test_config_rejects_post_freeze_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_legacy_teacher_regret_error"] = 1e-9
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_resident_cfr_v2_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_v1_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_resident_cfr_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
