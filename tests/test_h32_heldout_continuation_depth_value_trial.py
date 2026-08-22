from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from pontius.h32_heldout_continuation_depth_value_trial import (
    _parse_config,
    depth_promotion_decision,
)


class HeldoutContinuationDepthValueTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = Path("experiments/configs/h32-heldout-continuation-depth-value-v1.json")

    def test_promotion_requires_material_value_and_better_rate(self) -> None:
        self.assertTrue(depth_promotion_decision(
            one_value=1.0, two_value=1.3, one_ledger_ms=10.0,
            two_ledger_ms=12.0, materiality_floor=0.1,
        ))
        self.assertFalse(depth_promotion_decision(
            one_value=1.0, two_value=1.05, one_ledger_ms=10.0,
            two_ledger_ms=10.0, materiality_floor=0.1,
        ))
        self.assertFalse(depth_promotion_decision(
            one_value=1.0, two_value=1.2, one_ledger_ms=10.0,
            two_ledger_ms=20.0, materiality_floor=0.1,
        ))
        with self.assertRaises(ValueError):
            depth_promotion_decision(
                one_value=math.nan, two_value=1.0, one_ledger_ms=1.0,
                two_ledger_ms=1.0, materiality_floor=0.0,
            )

    def test_frozen_config_is_heldout_paired_and_stack_is_not_span(self) -> None:
        parsed = _parse_config(json.loads(self.path.read_text(encoding="utf-8")))
        self.assertEqual(parsed["depth_arms"], [1, 2])
        self.assertEqual(len(parsed["targets"]), 12)
        self.assertEqual({row["round"] for row in parsed["targets"]}, {"latin_c", "latin_d"})
        source = Path("src/pontius/h32_heldout_continuation_depth_value_trial.py").read_text(encoding="utf-8")
        self.assertIn("raw_guard(layout", source)
        self.assertIn("normalized_quality(", source)
        self.assertNotIn('payoff_span=parsed["stack"]', source)
        self.assertNotIn('acceptance_guard_normalized\"] * parsed[\"stack', source)

    def test_mutations_are_rejected(self) -> None:
        config = json.loads(self.path.read_text(encoding="utf-8"))
        for field, value in (
            ("promotion_rule", "inspect_labels"),
            ("depth_arms", [2, 1]),
            ("seat_order", [1, 0, 2, 3, 4, 5]),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                _parse_config({**config, field: value})


if __name__ == "__main__":
    unittest.main()
