from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.open_mode_audit import parse_open_mode_audit_config


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "open-mode-factor-tt-audit-v1.json"


class OpenModeAuditTests(unittest.TestCase):
    def test_frozen_config_parses_and_every_gate_is_pinned(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_open_mode_audit_config(config)
        self.assertEqual(parsed["small_hands_per_player"], (4, 7))
        self.assertEqual(parsed["range_families"], ("balanced", "blocker_heavy"))
        self.assertEqual(parsed["gates"]["expected_small_infoset_rows"], 768)
        self.assertEqual(
            parsed["gates"]["maximum_wide_peak_numeric_bytes"],
            1_000_000_000,
        )

    def test_config_rejects_gate_relaxation_and_unknown_fields(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        relaxed = copy.deepcopy(config)
        relaxed["gates"]["maximum_action_numerator_error"] = 1e-7
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_open_mode_audit_config(relaxed)
        widened = copy.deepcopy(config)
        widened["unknown"] = True
        with self.assertRaisesRegex(ValueError, "fields"):
            parse_open_mode_audit_config(widened)


if __name__ == "__main__":
    unittest.main()
