import copy
import json
from pathlib import Path
import unittest

from pontius.h32_fresh_panel_action_width_warm_step_audit_v2 import (
    parse_h32_fresh_panel_action_width_warm_step_v2_config,
)


_CONFIG = Path(__file__).parents[1] / "experiments/configs/h32-fresh-panel-action-width-warm-step-v2.json"


class CorrectedFreshPanelActionWidthConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_only_post_work_aggregation_changes(self) -> None:
        parsed = parse_h32_fresh_panel_action_width_warm_step_v2_config(self.config)
        self.assertEqual(len(parsed["base"]["target_order"]), 12)
        self.assertEqual(parsed["base"]["complete_steps_per_arm"], 1)
        self.assertIn("post_work_aggregation_only", parsed["correction_scope"])
        self.assertIn("reuse_adr0150", parsed["outcome_policy"])

    def test_scope_outcome_and_source_mutations_fail(self) -> None:
        for field, value in (
            ("correction_scope", "change_quality_gate"),
            ("outcome_policy", "drop_failed_target"),
            ("expected_v1_implementation_sha256", "0" * 64),
        ):
            changed = copy.deepcopy(self.config)
            changed[field] = value
            with self.assertRaises(ValueError):
                parse_h32_fresh_panel_action_width_warm_step_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
