from __future__ import annotations
import copy, json
from pathlib import Path
import unittest
from pontius.h32_fresh_panel_target_transfer_audit_v2 import parse_h32_fresh_panel_target_transfer_v2_config

_CONFIG = Path(__file__).parents[1] / "experiments/configs/h32-fresh-panel-target-transfer-v2.json"

class CorrectedTargetTransferConfigTests(unittest.TestCase):
    def test_only_warm_identity_semantics_change(self) -> None:
        parsed = parse_h32_fresh_panel_target_transfer_v2_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["maximum_warm_start_probability_error"], 1e-12)
        self.assertEqual(parsed["maximum_warm_start_mean_total_variation"], 1e-13)
        self.assertFalse(parsed["require_warm_start_digest_identity"])
        self.assertEqual(parsed["base"]["search_iterations"], (1, 2))
        self.assertEqual(len(parsed["base"]["target_order"]), 12)
        self.assertNotIn("selection", json.dumps(parsed["base"]["gates"]).lower())
    def test_correction_source_and_tolerance_edits_fail(self) -> None:
        config=json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (lambda r:r.__setitem__("expected_failed_result_sha256", "0"*64), lambda r:r.__setitem__("maximum_warm_start_probability_error", 1e-11), lambda r:r.__setitem__("require_warm_start_digest_identity", True)):
            changed=copy.deepcopy(config); mutation(changed)
            with self.assertRaises(ValueError): parse_h32_fresh_panel_target_transfer_v2_config(changed)

if __name__ == "__main__": unittest.main()
