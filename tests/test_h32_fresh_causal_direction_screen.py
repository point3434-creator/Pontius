from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_fresh_causal_direction_screen import (
    build_best_response_vertex_candidate,
    direction_binding_constraint,
    parse_h32_fresh_causal_direction_screen_config,
    select_feature_block,
    vertex_probe_features,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-fresh-causal-direction-screen-v1.json"
)


class H32FreshCausalDirectionScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_screen_contract_is_exact(self) -> None:
        parsed = parse_h32_fresh_causal_direction_screen_config(self.config)
        self.assertEqual(len(parsed["targets"]), 6)
        self.assertEqual(parsed["local_blocker_target_seat"], 2)
        self.assertEqual(
            parsed["direction_families"],
            ("soft_dcfr", "regret_vertex", "best_response_vertex"),
        )
        self.assertEqual(parsed["vertex_probe_scale_index"], 16)
        self.assertEqual(
            parsed["opportunity_features"],
            (
                "regret_mass",
                "negative_minimum_action_gap",
                "vertex_probe_estimated_cap_radius",
                "vertex_probe_positive_value",
            ),
        )

    def test_config_rejects_target_probe_family_gate_and_source_mutations(self) -> None:
        mutations = []
        changed = copy.deepcopy(self.config)
        changed["targets"][0]["target_belief_sha256"] = "0" * 64
        mutations.append(changed)
        changed = copy.deepcopy(self.config)
        changed["vertex_probe_scale_index"] = 15
        mutations.append(changed)
        changed = copy.deepcopy(self.config)
        changed["direction_families"].reverse()
        mutations.append(changed)
        changed = copy.deepcopy(self.config)
        changed["gates"]["expected_direction_rows"] = 109
        mutations.append(changed)
        changed = copy.deepcopy(self.config)
        changed["expected_parent_result_sha256"] = "0" * 64
        mutations.append(changed)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_fresh_causal_direction_screen_config(mutation)

    def test_best_response_vertex_uses_frozen_actions(self) -> None:
        blueprint = {
            "k1": {"a": 0.25, "b": 0.75},
            "k2": {"a": 0.6, "b": 0.4},
            "k3": {"a": 1.0, "b": 0.0},
        }
        candidate = build_best_response_vertex_candidate(
            blueprint,
            {"k1": "a", "k2": "b", "k3": "a"},
            ["k1", "k2"],
        )
        self.assertEqual(candidate["k1"], {"a": 1.0, "b": 0.0})
        self.assertEqual(candidate["k2"], {"a": 0.0, "b": 1.0})
        self.assertEqual(candidate["k3"], blueprint["k3"])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            build_best_response_vertex_candidate(blueprint, {"k1": "a"}, ["k2"])
        with self.assertRaisesRegex(ValueError, "schema"):
            build_best_response_vertex_candidate(
                blueprint,
                {"k1": "missing"},
                ["k1"],
            )

    def test_probe_features_measure_cap_slope_and_censoring(self) -> None:
        blueprint = {
            "deviation_gains": [2.0, 4.0],
            "nash_conv": 6.0,
        }
        complete = {
            "scale_index": 2,
            "scale": 0.25,
            "positive_certified_value": 0.2,
            "construction_ms": 3.0,
            "certificate": {
                "complete": True,
                "stop_reason": "complete",
                "stop_seat": None,
                "wall_ms": 5.0,
                "seat_rows": [
                    {"target_player": 0, "deviation_gain": 2.5},
                    {"target_player": 1, "deviation_gain": 3.75},
                ],
                "quality": {"nash_conv": 5.8},
            },
        }
        features = vertex_probe_features(
            complete,
            blueprint,
            raw_guard=0.1,
            payoff_span=10.0,
        )
        self.assertAlmostEqual(features["maximum_positive_observed_gain_slope"], 2.0)
        self.assertAlmostEqual(features["estimated_cap_radius"], 0.05)
        self.assertAlmostEqual(features["objective_improvement_slope"], 0.8)
        self.assertFalse(features["cap_radius_censored"])

        stopped = copy.deepcopy(complete)
        stopped["certificate"]["complete"] = False
        stopped["certificate"]["stop_reason"] = "blueprint_cap"
        stopped["certificate"]["stop_seat"] = 0
        stopped["certificate"]["seat_rows"] = [
            {"target_player": 0, "deviation_gain": 2.5}
        ]
        stopped["certificate"]["quality"] = None
        features = vertex_probe_features(
            stopped,
            blueprint,
            raw_guard=0.1,
            payoff_span=10.0,
        )
        self.assertTrue(features["cap_radius_censored"])
        self.assertEqual(features["objective_improvement_slope"], 0.0)

    def test_binding_constraint_reads_the_immediately_larger_scale(self) -> None:
        search = {
            "largest_complete_scale_index": 2,
            "queried_rows": [
                {
                    "scale_index": 1,
                    "certificate": {"stop_reason": "blueprint_cap"},
                },
                {"scale_index": 2, "certificate": {"stop_reason": "complete"}},
            ],
        }
        self.assertEqual(direction_binding_constraint(search), "blueprint_cap")
        search["largest_complete_scale_index"] = 0
        self.assertEqual(
            direction_binding_constraint(search),
            "grid_endpoint_complete",
        )

    def test_feature_selector_uses_lowest_seat_tie_break(self) -> None:
        rows = [
            {
                "acting_seat": 3,
                "public_history": "z",
                "feature_scores": {"regret_mass": 2.0},
            },
            {
                "acting_seat": 1,
                "public_history": "a",
                "feature_scores": {"regret_mass": 2.0},
            },
        ]
        selected = select_feature_block(rows, feature="regret_mass")
        self.assertEqual(selected["acting_seat"], 1)


if __name__ == "__main__":
    unittest.main()
