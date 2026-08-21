from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_response_latency_bridge_audit import (
    _expected_stop,
    parse_h32_response_latency_bridge_config,
)


_CONFIG = Path(__file__).parents[1] / "experiments/configs/h32-response-latency-bridge-v1.json"


class H32ResponseLatencyBridgeTests(unittest.TestCase):
    def test_outcome_neutral_deadline_contract(self) -> None:
        parsed = parse_h32_response_latency_bridge_config(
            json.loads(_CONFIG.read_text(encoding="utf-8"))
        )
        self.assertEqual(parsed["candidate_id"], "search_current1")
        self.assertEqual(len(parsed["target_order"]), 12)
        self.assertEqual(parsed["seat_order"], (0, 1, 2, 3, 4, 5))
        self.assertEqual(parsed["decision_budget_ms"], 15000.0)
        self.assertIn("descriptive_sensitivity_only", parsed["deadline_interpretation"])
        gates = json.dumps(parsed["gates"], sort_keys=True).lower()
        self.assertNotIn("within_15s", gates)
        self.assertNotIn("minimum_improvement", gates)
        self.assertNotIn("expected_stop_seat", gates)

    def test_cap_precedes_objective_and_complete_is_explicit(self) -> None:
        common = {
            "blueprint_gains": (0.1, 0.1),
            "best_complete_nash_conv": 0.2,
            "raw_guard": 0.0,
            "seat_order": (0, 1),
        }
        self.assertEqual(
            _expected_stop(gains=(0.11, 0.11), **common),
            ("blueprint_cap", 0),
        )
        self.assertEqual(
            _expected_stop(gains=(0.1, 0.11), **common),
            ("blueprint_cap", 1),
        )
        self.assertEqual(
            _expected_stop(gains=(0.09, 0.09), **common),
            ("complete", -1),
        )
        self.assertEqual(
            _expected_stop(
                gains=(0.09, 0.09, 0.09),
                blueprint_gains=(0.1, 0.1, 0.1),
                best_complete_nash_conv=0.2,
                raw_guard=0.0,
                seat_order=(0, 1, 2),
            ),
            ("objective_lower_bound", 2),
        )

    def test_protocol_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutations = (
            lambda row: row.__setitem__("decision_budget_ms", 16000.0),
            lambda row: row["target_order"].reverse(),
            lambda row: row.__setitem__("seat_order", [5, 4, 3, 2, 1, 0]),
            lambda row: row.__setitem__(
                "unmeasured_emission_reserve_scenarios_ms", [0.0]
            ),
            lambda row: row["gates"].__setitem__(
                "maximum_response_certificate_ms", 61000.0
            ),
            lambda row: row.__setitem__("expected_teacher_result_sha256", "0" * 64),
        )
        for mutation in mutations:
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_response_latency_bridge_config(changed)


if __name__ == "__main__":
    unittest.main()
