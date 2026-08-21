from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_retained_affine_selector_cascade_replay import (
    affine_tier_features,
    contaminated_tier_a_negative_control,
    derive_capacity,
    exact_random_value_floor,
    parse_h32_retained_affine_selector_cascade_config,
    score_feature_at_k,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v1.json"
)


def _affine_row(
    target_player: int,
    *,
    acting_player: int = 2,
    utility_slope: float = -0.1,
    br_slope: float = 0.02,
    gain_slope: float = 0.12,
) -> dict[str, float | int]:
    own = target_player == acting_player
    return {
        "target_player": target_player,
        "acting_player": acting_player,
        "profile_utility_slope": utility_slope,
        "best_response_value_slope": 0.0 if own else br_slope,
        "deviation_gain_intercept": 0.25,
        "deviation_gap_slope": -utility_slope if own else gain_slope,
        "selector_stable_scale": 0.75,
        "changed_public_nodes": 1,
        "affected_terminal_contractions": 0 if own else 2,
        "terminal_contraction_ms": 0.0 if own else 3.0,
        "reverse_evaluation_ms": 1.0,
        "wall_ms": 1.5 if own else 4.5,
    }


def _candidate(
    seat: int,
    family: str,
    feature: float,
    label: float,
) -> dict[str, object]:
    return {
        "acting_seat": seat,
        "public_history": f"history_{seat}",
        "direction_family": family,
        "features": {"score": feature},
        "label": label,
    }


class H32RetainedAffineSelectorCascadeReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_strata_feature_order_and_cardinalities_are_exact(self) -> None:
        parsed = parse_h32_retained_affine_selector_cascade_config(self.config)
        self.assertEqual(parsed["primary_candidate_set"], "regret_vertex_only")
        self.assertEqual(
            parsed["candidate_sets"]["regret_vertex_only"], ("regret_vertex",)
        )
        self.assertEqual(
            parsed["candidate_sets"]["soft_excluded"],
            ("regret_vertex", "best_response_vertex"),
        )
        self.assertEqual(parsed["diagnostic_k_ladders"]["all_families"][-1], 18)
        self.assertIn("tier_b_slope_predicted_value", parsed["feature_list"])
        self.assertEqual(parsed["gates"]["expected_candidate_rows"], 108)
        self.assertNotIn("minimum_value_capture", parsed["gates"])
        self.assertNotIn("require_prediction_passed", parsed["gates"])

    def test_tier_a_identity_and_five_opponent_charge_are_exact(self) -> None:
        rows = [_affine_row(seat) for seat in range(6)]
        result = affine_tier_features(
            rows,
            acting_seat=2,
            raw_guard=3e-9,
            numerical_allowance=2e-11,
        )
        self.assertEqual(result["identity"]["tier_a_identity_error"], 0.0)
        self.assertEqual(result["identity"]["own_best_response_value_slope"], 0.0)
        self.assertEqual(result["cost"]["opponent_br_conditioned_calls"], 5)
        self.assertEqual(result["cost"]["opponent_affected_terminal_terms"], 10)
        self.assertEqual(result["cost"]["opponent_terminal_contraction_ms"], 15.0)

        with self.assertRaisesRegex(ValueError, "one ordered row per seat"):
            affine_tier_features(
                rows[:-1],
                acting_seat=2,
                raw_guard=3e-9,
                numerical_allowance=2e-11,
            )
        contaminated_charge = [dict(row) for row in rows]
        contaminated_charge[2]["affected_terminal_contractions"] = 1
        with self.assertRaisesRegex(ValueError, "unexpectedly contracted"):
            affine_tier_features(
                contaminated_charge,
                acting_seat=2,
                raw_guard=3e-9,
                numerical_allowance=2e-11,
            )

    def test_impure_off_seat_direction_is_a_required_disagreement(self) -> None:
        control = contaminated_tier_a_negative_control()
        self.assertTrue(control["pure_scope_accepted"])
        self.assertTrue(control["impure_scope_rejected"])
        self.assertLessEqual(control["pure_identity_error"], 1e-15)
        self.assertGreater(control["impure_disagreement"], 0.0)
        self.assertTrue(control["passed"])

    def test_recall_scoring_and_random_floor_are_deterministic(self) -> None:
        rows = [
            _candidate(0, "regret_vertex", 3.0, 1.0),
            _candidate(1, "regret_vertex", 2.0, 4.0),
            _candidate(2, "regret_vertex", 1.0, 2.0),
        ]
        top1 = score_feature_at_k(rows, feature="score", k=1)
        top2 = score_feature_at_k(rows, feature="score", k=2)
        self.assertFalse(top1["canonical_best_recalled"])
        self.assertEqual(top1["value_capture_fraction"], 0.25)
        self.assertTrue(top2["canonical_best_recalled"])
        self.assertEqual(top2["value_capture_fraction"], 1.0)
        self.assertAlmostEqual(exact_random_value_floor([1.0, 4.0, 2.0], 1), 7 / 3)
        self.assertEqual(exact_random_value_floor([1.0, 4.0, 2.0], 3), 4.0)

    def test_capacity_is_label_blind_and_capped_by_library(self) -> None:
        rows = []
        for seat in range(6):
            rows.append(
                {
                    "timing": {
                        "endpoint_construction_ms": 2.0,
                        "envelope_ms": 1.0,
                    },
                    "tier": {
                        "cost": {
                            "acting_zero_contraction_wall_ms": 3.0,
                            "opponent_wall_ms": 100.0,
                        }
                    },
                }
            )
        capacity = derive_capacity(
            rows,
            search_step_ms=12000.0,
            street_budget_ms=15000.0,
            emission_reserve_ms=1000.0,
        )
        self.assertEqual(capacity["current_clock_feasible_k"], 6)
        self.assertTrue(capacity["current_library_limited"])
        self.assertNotIn("label", json.dumps(capacity))

    def test_config_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["primary_candidate_set"] = "all_families"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_retained_affine_selector_cascade_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_label_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_retained_affine_selector_cascade_config(changed)


if __name__ == "__main__":
    unittest.main()
