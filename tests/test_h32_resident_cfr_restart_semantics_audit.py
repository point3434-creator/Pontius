from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_resident_cfr_restart_semantics_audit import (
    parse_h32_resident_cfr_restart_semantics_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-resident-cfr-restart-semantics-audit-v1.json"
)


class H32ResidentCFRRestartSemanticsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_separates_restore_continuation_and_quality(self) -> None:
        parsed = parse_h32_resident_cfr_restart_semantics_config(self.config)
        self.assertEqual(
            parsed["continuation_arms"],
            ("uninterrupted", "restored_a", "restored_b"),
        )
        self.assertEqual(len(parsed["quality_policy_kinds"]), 4)
        self.assertTrue(
            parsed["gates"]["require_immediate_restore_state_digest_identity"]
        )
        self.assertEqual(
            parsed["gates"]["maximum_continuation_regret_error"],
            1e-10,
        )
        self.assertEqual(parsed["gates"]["maximum_quality_nash_conv_error"], 1e-10)

    def test_config_rejects_post_freeze_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_quality_nash_conv_error"] = 1e-8
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_resident_cfr_restart_semantics_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_parent_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_resident_cfr_restart_semantics_config(changed)


if __name__ == "__main__":
    unittest.main()
