from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_canonical_affine_cache_replay import (
    parse_h32_canonical_affine_cache_replay_config,
)


class H32CanonicalAffineCacheReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "h32-canonical-affine-cache-replay-v1.json"
        )
        cls.config = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_frozen_repair_is_cache_only_and_scale_canonical(self) -> None:
        parsed = parse_h32_canonical_affine_cache_replay_config(self.config)
        self.assertEqual(parsed["bet_sizes"], (3.0, 6.0))
        self.assertEqual(parsed["expected_two_size_payoff_span"], 48.0)
        self.assertEqual(len(parsed["target_order"]), 4)
        self.assertEqual(parsed["gates"]["expected_shared_affine_bases"], 378)
        self.assertEqual(parsed["gates"]["expected_failed_parent_affine_bases"], 384)
        self.assertTrue(parsed["gates"]["require_zero_h32_steps"])
        self.assertTrue(parsed["gates"]["require_no_strategy_quality_evaluation"])

    def test_config_rejects_workload_source_and_gate_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["zero_step_rule"] = "run_again"
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_h32_canonical_affine_cache_replay_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_canonical_cache_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_canonical_affine_cache_replay_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["require_zero_h32_steps"] = False
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_canonical_affine_cache_replay_config(changed)


if __name__ == "__main__":
    unittest.main()
