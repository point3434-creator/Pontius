import copy
import json
from pathlib import Path
import unittest

from pontius.h32_fresh_panel_action_width_warm_step_audit import (
    parse_h32_fresh_panel_action_width_warm_step_config,
)


_CONFIG = (
    Path(__file__).parents[1]
    / "experiments/configs/h32-fresh-panel-action-width-warm-step-v1.json"
)


class FreshPanelActionWidthWarmStepConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_all_targets_and_one_step_per_arm_are_frozen(self) -> None:
        parsed = parse_h32_fresh_panel_action_width_warm_step_config(self.config)
        self.assertEqual(len(parsed["target_order"]), 12)
        self.assertEqual(len(parsed["arm_order_by_target"]), 12)
        self.assertEqual(parsed["complete_steps_per_arm"], 1)
        self.assertIn("all_twelve_targets", parsed["scheduling_independence_rule"])
        self.assertEqual(parsed["gates"]["expected_steps"], 24)
        self.assertEqual(parsed["gates"]["expected_complete_quality_profiles"], 36)

    def test_outcome_order_and_gate_mutations_fail(self) -> None:
        changes = []
        changed = copy.deepcopy(self.config)
        changed["disclosed_prior_outcome"] = "use_adr0149_to_filter"
        changes.append(changed)
        changed = copy.deepcopy(self.config)
        changed["target_order"] = changed["target_order"][:-1]
        changes.append(changed)
        changed = copy.deepcopy(self.config)
        changed["complete_steps_per_arm"] = 2
        changes.append(changed)
        changed = copy.deepcopy(self.config)
        changed["gates"]["expected_steps"] = 12
        changes.append(changed)
        for config in changes:
            with self.assertRaises(ValueError):
                parse_h32_fresh_panel_action_width_warm_step_config(config)

    def test_source_hash_mutation_fails(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["expected_cache_result_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            parse_h32_fresh_panel_action_width_warm_step_config(changed)


if __name__ == "__main__":
    unittest.main()
