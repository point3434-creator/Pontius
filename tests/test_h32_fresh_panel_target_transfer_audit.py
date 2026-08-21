from __future__ import annotations
import copy, json
from pathlib import Path
import unittest
from pontius.h32_fresh_panel_target_transfer_audit import parse_h32_fresh_panel_target_transfer_config

_CONFIG = Path(__file__).parents[1] / "experiments/configs/h32-fresh-panel-target-transfer-v1.json"

class H32FreshPanelTargetTransferConfigTests(unittest.TestCase):
    def test_two_step_outcome_neutral_contract(self) -> None:
        parsed = parse_h32_fresh_panel_target_transfer_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["search_iterations"], (1, 2)); self.assertEqual(len(parsed["target_order"]), 12)
        self.assertEqual(len(parsed["candidate_order"]), 6); self.assertIn("never_reanchors", parsed["certificate_anchor_rule"])
        gates = json.dumps(parsed["gates"]).lower(); self.assertNotIn("minimum_improvement", gates); self.assertNotIn("expected_selection", gates)
    def test_source_target_schedule_and_gate_edits_fail(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (lambda r:r.__setitem__("expected_source_result_sha256", "0"*64), lambda r:r.__setitem__("search_iterations", [1,2,4]), lambda r:r["target_order"].reverse(), lambda r:r["gates"].__setitem__("maximum_training_step_ms", 61000.0)):
            changed=copy.deepcopy(config); mutation(changed)
            with self.assertRaises(ValueError): parse_h32_fresh_panel_target_transfer_config(changed)

if __name__ == "__main__": unittest.main()
