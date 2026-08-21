from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_affine_resident_cache_preflight import (
    parse_h32_affine_resident_cache_config,
)


class H32AffineResidentCachePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "h32-affine-resident-cache-preflight-v1.json"
        )
        cls.config = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_frozen_affine_workload_and_headroom_branch_are_exact(self) -> None:
        parsed = parse_h32_affine_resident_cache_config(self.config)
        self.assertEqual(parsed["bet_sizes"], (3.0, 6.0))
        self.assertEqual(parsed["expected_two_size_payoff_span"], 48.0)
        self.assertEqual(parsed["hands_per_player"], 32)
        self.assertEqual(len(parsed["target_order"]), 4)
        self.assertEqual(parsed["minimum_warm_noncache_reserve_bytes"], 5_184_456_164)
        self.assertEqual(parsed["gates"]["expected_shared_affine_bases"], 378)
        self.assertTrue(parsed["gates"]["require_conditional_single_widened_step"])
        self.assertTrue(parsed["gates"]["require_no_strategy_quality_evaluation"])

    def test_config_rejects_workload_source_and_gate_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["expected_two_size_payoff_span"] = 30.0
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_h32_affine_resident_cache_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_affine_contraction_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_affine_resident_cache_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_gpu_pool_bytes"] += 1
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_affine_resident_cache_config(changed)


if __name__ == "__main__":
    unittest.main()
