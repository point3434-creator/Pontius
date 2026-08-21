from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_multi_size_resident_cache_preflight import (
    parse_h32_multi_size_resident_cache_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-multi-size-resident-cache-preflight-v1.json"
)


class H32MultiSizeResidentCachePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_workload_and_headroom_branch_are_exact(self) -> None:
        parsed = parse_h32_multi_size_resident_cache_config(self.config)
        self.assertEqual(parsed["bet_sizes"], (3.0, 6.0))
        self.assertEqual(parsed["hands_per_player"], 32)
        self.assertEqual(len(parsed["target_order"]), 4)
        self.assertEqual(
            parsed["minimum_warm_noncache_reserve_bytes"],
            parsed["resident_lineage_maximum_pool_bytes"]
            - parsed["resident_lineage_largest_persistent_bytes"],
        )
        self.assertEqual(
            parsed["unsafe_branch"],
            "stop_before_any_h32_two_size_step_and_build_affine_shared_topology_cache",
        )
        self.assertTrue(parsed["gates"]["require_no_strategy_quality_evaluation"])

    def test_config_rejects_workload_source_and_gate_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["bet_sizes"] = [3.0, 9.0]
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_h32_multi_size_resident_cache_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_sized_resident_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_multi_size_resident_cache_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_gpu_pool_bytes"] = 13_000_000_000
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_multi_size_resident_cache_config(changed)


if __name__ == "__main__":
    unittest.main()
