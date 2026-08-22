import copy
import json
from pathlib import Path
import unittest

from pontius.h32_continuation_direction_capacity import (
    _parse_config,
    build_soft_regret_bisector_candidate,
    direction_capacity_decision,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-continuation-direction-capacity-v1.json"


class ContinuationDirectionCapacityTests(unittest.TestCase):
    def test_bisector_changes_only_selected_rows_at_exact_midpoint(self) -> None:
        blueprint = {
            "a": {"x": 0.8, "y": 0.2},
            "b": {"x": 0.4, "y": 0.6},
        }
        soft = {
            "a": {"x": 0.6, "y": 0.4},
            "b": {"x": 0.1, "y": 0.9},
        }
        vertex = {
            "a": {"x": 0.0, "y": 1.0},
            "b": {"x": 0.4, "y": 0.6},
        }
        result = build_soft_regret_bisector_candidate(
            blueprint, soft, vertex, ("a",)
        )
        self.assertEqual(result["a"], {"x": 0.3, "y": 0.7})
        self.assertEqual(result["b"], blueprint["b"])

    def test_capacity_requires_complete_distinct_baseline_first_expansion(self) -> None:
        common = {
            "baseline_candidate_ms": (100.0, 100.0),
            "bonus_candidate_ms": (100.0, 100.0),
            "warm_step_ms": 100.0,
            "street_budget_ms": 1000.0,
            "emission_reserve_ms": 100.0,
            "certificate_reserve_ms": 100.0,
            "envelope_reserve_ms": 0.0,
        }
        passed = direction_capacity_decision(**common, distinct_bonus_rows=2)
        self.assertTrue(passed["promote_bisector_family"])
        self.assertEqual(passed["baseline_complete_ledger_ms"], 500.0)
        self.assertEqual(passed["expanded_complete_ledger_ms"], 700.0)
        self.assertEqual(passed["expanded_capacity"]["profiled_cumulative_k"], 4)

        duplicate = direction_capacity_decision(**common, distinct_bonus_rows=1)
        self.assertFalse(duplicate["promote_bisector_family"])

        too_slow = direction_capacity_decision(
            **{**common, "street_budget_ms": 450.0}, distinct_bonus_rows=2
        )
        self.assertFalse(too_slow["promote_bisector_family"])

    def test_frozen_config_and_mutations(self) -> None:
        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["direction_families"], [
            "regret_vertex", "soft_regret_bisector"
        ])
        self.assertEqual(parsed["gates"]["expected_candidate_rows"], 744)
        self.assertEqual(parsed["certificate_reserve_ms"], 1250.0)

        for field, value in (
            ("candidate_order", "bisector_first"),
            ("certificate_reserve_ms", 0.0),
            ("strategy_label_policy", "serialize_labels"),
        ):
            mutated = copy.deepcopy(dict(parsed))
            mutated["targets"] = [dict(row) for row in parsed["targets"]]
            mutated[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                _parse_config(mutated)


if __name__ == "__main__":
    unittest.main()
