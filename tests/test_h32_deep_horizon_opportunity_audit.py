from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_deep_horizon_opportunity_audit import (
    material_depth_lift,
    parse_h32_deep_horizon_opportunity_config,
    purify_policy,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-opportunity-v1.json"


class H32DeepHorizonOpportunityAuditTests(unittest.TestCase):
    def test_contract_rejects_target_depth_direction_parent_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_deep_horizon_opportunity_config(config)
        self.assertEqual(len(parsed["targets"]), 2)
        self.assertEqual(parsed["checkpoints"], (8, 32, 64))
        self.assertEqual(
            parsed["endpoint_directions"],
            (
                "current8", "average8", "current32", "average32",
                "current64", "average64", "purified_average64",
            ),
        )

        mutated = json.loads(json.dumps(config))
        mutated["targets"].reverse()
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_deep_horizon_opportunity_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["checkpoints"] = [8, 16, 64]
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_deep_horizon_opportunity_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["endpoint_directions"].reverse()
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_deep_horizon_opportunity_config(mutated)

        mutated = dict(config)
        mutated["expected_parent_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_deep_horizon_opportunity_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["maximum_total_certificate_queries"] += 1
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_deep_horizon_opportunity_config(mutated)

    def test_purification_uses_first_maximum_probability_action(self) -> None:
        policy = {
            "k2": {"fold": 0.2, "call": 0.8},
            "k1": {"check": 0.5, "bet": 0.5},
        }
        self.assertEqual(
            purify_policy(policy),
            {
                "k1": {"check": 1.0, "bet": 0.0},
                "k2": {"fold": 0.0, "call": 1.0},
            },
        )

    def test_material_lift_requires_twofold_value_and_guard_margin(self) -> None:
        self.assertTrue(material_depth_lift(1.0, 2.1, raw_guard_total=0.1))
        self.assertFalse(material_depth_lift(1.0, 1.9, raw_guard_total=0.1))
        self.assertFalse(material_depth_lift(1.0, 2.0, raw_guard_total=1.0))
        self.assertTrue(material_depth_lift(0.0, 0.2, raw_guard_total=0.1))
        with self.assertRaises(ValueError):
            material_depth_lift(-1.0, 2.0, raw_guard_total=0.1)


if __name__ == "__main__":
    unittest.main()
