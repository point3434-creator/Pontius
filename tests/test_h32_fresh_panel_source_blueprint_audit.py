from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_fresh_board_panel_cache_preflight import _FROZEN_PANELS, _FROZEN_SOURCE_DIGESTS
from pontius.h32_fresh_panel_source_blueprint_audit import parse_h32_fresh_panel_source_blueprint_config


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-fresh-panel-source-blueprints-v1.json"


class H32FreshPanelSourceBlueprintConfigTests(unittest.TestCase):
    def test_source_only_schedule_is_frozen(self) -> None:
        parsed = parse_h32_fresh_panel_source_blueprint_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["panels"], tuple(dict(row) for row in _FROZEN_PANELS))
        self.assertEqual(parsed["source_belief_sha256_by_source"], _FROZEN_SOURCE_DIGESTS)
        self.assertEqual(parsed["final_iteration"], 64)
        self.assertEqual(parsed["checkpoint_iterations"], (1, 2, 4, 8, 16, 32, 64))
        self.assertEqual(parsed["full_state_iterations"], (64,))
        self.assertTrue(parsed["cold_start"])
        self.assertIn("uninterrupted", parsed["trajectory_rule"])
        self.assertIn("without_continuation", parsed["restart_rule"])
        self.assertIn("finish_all_six", parsed["quality_phase_rule"])
        self.assertIn("forbidden_zero_target", parsed["target_construction_rule"])
        self.assertNotIn("nash", json.dumps(parsed["gates"]).lower())

    def test_schedule_source_and_gate_mutations_are_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("expected_cache_result_sha256", "0" * 64),
            lambda row: row.__setitem__("final_iteration", 63),
            lambda row: row["source_order"].reverse(),
            lambda row: row["source_belief_sha256_by_source"].__setitem__("panel_1/balanced", "0" * 64),
            lambda row: row["gates"].__setitem__("maximum_training_step_ms", 61000.0),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_fresh_panel_source_blueprint_config(changed)


if __name__ == "__main__":
    unittest.main()
