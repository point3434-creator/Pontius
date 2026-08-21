from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_retained_affine_selector_cascade_replay_v2 import (
    _memory_snapshot_alias,
    parse_h32_retained_affine_selector_cascade_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v2.json"
)


class H32RetainedAffineSelectorCascadeReplayV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_complete_v1_scientific_protocol_is_reused(self) -> None:
        parsed = parse_h32_retained_affine_selector_cascade_v2_config(self.config)
        base = parsed["v1_base"]
        self.assertEqual(
            base["candidate_families"],
            ("soft_dcfr", "regret_vertex", "best_response_vertex"),
        )
        self.assertEqual(base["primary_candidate_set"], "regret_vertex_only")
        self.assertEqual(base["feature_list"][-1], "tier_b_slope_predicted_value")
        self.assertEqual(base["gates"]["expected_candidate_rows"], 108)
        self.assertEqual(base["gates"]["expected_affine_seat_rows"], 648)

    def test_alias_adds_only_the_expected_physical_free_view(self) -> None:
        source = {
            "gpu_pool_total_bytes": 123,
            "gpu_free_bytes": 456,
        }
        corrected = _memory_snapshot_alias(lambda _cp: source)(object())
        self.assertEqual(source, {"gpu_pool_total_bytes": 123, "gpu_free_bytes": 456})
        self.assertEqual(
            corrected,
            {
                "gpu_pool_total_bytes": 123,
                "gpu_free_bytes": 456,
                "gpu_physical_free_bytes": 456,
            },
        )

    def test_alias_rejects_any_other_memory_schema(self) -> None:
        corrected = _memory_snapshot_alias(
            lambda _cp: {
                "gpu_pool_total_bytes": 1,
                "gpu_free_bytes": 2,
                "another_field": 3,
            }
        )
        with self.assertRaisesRegex(ValueError, "wrong memory schema"):
            corrected(object())

    def test_config_and_source_mutations_are_rejected(self) -> None:
        changed = dict(self.config)
        changed["correction_scope"] = "change_features"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_retained_affine_selector_cascade_v2_config(changed)

        changed = dict(self.config)
        changed["expected_v1_implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_retained_affine_selector_cascade_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
