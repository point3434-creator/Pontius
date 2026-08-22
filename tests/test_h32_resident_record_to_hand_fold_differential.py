from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius import h32_resident_record_to_hand_fold_differential as fold


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-record-to-hand-fold-v1.json"


class H32ResidentRecordToHandFoldDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_scope_is_two_customer_and_four_cell(self) -> None:
        parsed = fold.parse_h32_resident_record_to_hand_fold_config(self.config)
        self.assertEqual(parsed["warm_step_arms"], ["host_fold", "device_fold"])
        self.assertEqual(
            parsed["tier_b_cells"],
            ["host_scalar", "host_batch", "device_scalar", "device_batch"],
        )
        self.assertEqual(len(parsed["warm_step_schedule"]), 3)
        self.assertEqual(len(parsed["tier_b_schedule"]), 3)
        self.assertEqual(parsed["base"]["gates"]["expected_targets"], 6)

    def test_global_device_choice_is_pooled_and_scalar_wins_exact_tie(self) -> None:
        rows = [
            {"cell": "device_scalar", "wall_ms": 10.0},
            {"cell": "device_scalar", "wall_ms": 20.0},
            {"cell": "device_scalar", "wall_ms": 30.0},
            {"cell": "device_batch", "wall_ms": 19.0},
            {"cell": "device_batch", "wall_ms": 20.0},
            {"cell": "device_batch", "wall_ms": 40.0},
        ]
        self.assertEqual(fold.choose_global_device_tier_cell(rows), "device_scalar")
        rows[-2]["wall_ms"] = 19.5
        self.assertEqual(fold.choose_global_device_tier_cell(rows), "device_batch")

    def test_labels_are_hash_bound_but_batch_result_is_not_deserialized(self) -> None:
        source = fold._IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertNotIn("_BATCH_RESULT.read_text", source)
        self.assertIn("strategy_labels_loaded\": 0", source)
        self.assertIn("source_parent[\"passed\"]", source)
        self.assertNotIn('source_parent["gates"]', source)

    def test_workload_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["minimum_material_speedup"] = 1.0
        with self.assertRaisesRegex(ValueError, "workload differs"):
            fold.parse_h32_resident_record_to_hand_fold_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_fold_implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            fold.parse_h32_resident_record_to_hand_fold_config(changed)

    def test_counter_profiler_cannot_enter_paired_timing(self) -> None:
        source = fold._IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertIn("hardware_counters_in_timed_process\": False", source)
        self.assertNotIn("ncu --", source)
        self.assertIn("_ncu_metadata", source)


if __name__ == "__main__":
    unittest.main()
