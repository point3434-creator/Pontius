from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius import h32_tier_b_opponent_batch_differential_v2 as v2


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-tier-b-opponent-batch-v2.json"


class H32TierBOpponentBatchDifferentialV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_successor_reuses_complete_v1_science(self) -> None:
        parsed = v2.parse_h32_tier_b_opponent_batch_v2_config(self.config)
        base = parsed["base"]
        self.assertEqual(base["candidate_family"], "regret_vertex_only")
        self.assertEqual(base["gates"]["expected_scalar_opponent_calls_per_arm"], 30)
        self.assertEqual(base["gates"]["expected_batch_calls_per_arm"], 6)
        self.assertEqual(len(base["timing_arm_schedule"]), 3)

    def test_source_schema_pins_top_level_pass_and_rejects_gates_alias(self) -> None:
        source = json.loads(v2.v1.science._SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(set(source), v2._SOURCE_SCHEMA)
        self.assertIn("passed", source)
        self.assertIn("gate_results", source)
        self.assertNotIn("gates", source)
        self.assertIsInstance(source["passed"], bool)

    def test_implementation_has_no_failed_schema_read_or_monkeypatch(self) -> None:
        source = v2._IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertNotIn('source_parent["gates"]', source)
        self.assertIn('source_parent["passed"]', source)
        self.assertNotIn("setattr(", source)
        self.assertNotIn("monkeypatch", source.lower())
        self.assertIn("v1._run_target", source)

    def test_config_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["correction_rule"] = "also_change_timing"
        with self.assertRaisesRegex(ValueError, "correction differs"):
            v2.parse_h32_tier_b_opponent_batch_v2_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_v1_rejection_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            v2.parse_h32_tier_b_opponent_batch_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
