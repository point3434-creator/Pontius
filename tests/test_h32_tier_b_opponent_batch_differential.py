from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from pontius.h32_tier_b_opponent_batch_differential import (
    affine_semantic_difference,
    complete_six_block_ledger,
    parse_h32_tier_b_opponent_batch_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-tier-b-opponent-batch-v1.json"
_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_tier_b_opponent_batch_differential.py"
)


def _row(**changes):
    values = {
        "profile_utility_intercept": 1.0,
        "profile_utility_slope": -0.2,
        "best_response_value_intercept": 1.1,
        "best_response_value_slope": 0.05,
        "deviation_gain_intercept": 0.1,
        "deviation_gap_slope": 0.25,
        "selector_stable_scale": 0.5,
        "target_player": 0,
        "acting_player": 1,
        "changed_public_node": 9,
        "first_switch_information_key": None,
        "first_switch_source_action": None,
        "first_switch_competing_action": None,
        "first_switch_hand_index": None,
        "selector_comparisons": 32,
        "exact_source_action_ties": 0,
        "changed_public_nodes": 1,
        "changed_opponent_public_nodes": 1,
        "affected_terminal_contractions": 2,
        "full_terminal_contractions": 10,
        "reused_terminal_numerators": 8,
    }
    values.update(changes)
    return SimpleNamespace(**values)


class H32TierBOpponentBatchDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_scope_charges_thirty_to_six_without_quality_gate(self) -> None:
        parsed = parse_h32_tier_b_opponent_batch_config(self.config)
        self.assertEqual(parsed["candidate_family"], "regret_vertex_only")
        self.assertEqual(parsed["gates"]["expected_opponent_rows_per_target"], 30)
        self.assertEqual(
            parsed["gates"]["expected_scalar_opponent_calls_per_arm"], 30
        )
        self.assertEqual(parsed["gates"]["expected_batch_calls_per_arm"], 6)
        self.assertEqual(len(parsed["timing_arm_schedule"]), 3)
        self.assertNotIn("minimum_speedup", parsed["gates"])
        self.assertNotIn("require_full_six_block_fit", parsed["gates"])

    def test_affine_comparison_separates_numeric_and_structural_failure(self) -> None:
        identical = affine_semantic_difference(_row(), _row())
        self.assertEqual(identical["maximum_numeric_error"], 0.0)
        self.assertTrue(identical["structural_identity"])

        changed = affine_semantic_difference(
            _row(),
            _row(deviation_gap_slope=0.250000001, changed_public_node=10),
        )
        self.assertAlmostEqual(changed["maximum_numeric_error"], 1e-9)
        self.assertFalse(changed["structural_identity"])
        self.assertEqual(changed["structural_mismatches"], ["changed_public_node"])

    def test_complete_ledger_charges_every_stage_and_reserve_once(self) -> None:
        passing = complete_six_block_ledger(
            search_step_ms=8000.0,
            endpoint_construction_ms=100.0,
            own_row_ms=50.0,
            batched_opponent_ms=2000.0,
            ranking_and_winner_envelope_ms=10.0,
            emission_reserve_ms=1000.0,
            street_budget_ms=15000.0,
        )
        self.assertEqual(passing["total_ms"], 11160.0)
        self.assertTrue(passing["full_six_block_set_fits"])

        failing = complete_six_block_ledger(
            search_step_ms=12000.0,
            endpoint_construction_ms=100.0,
            own_row_ms=50.0,
            batched_opponent_ms=2000.0,
            ranking_and_winner_envelope_ms=10.0,
            emission_reserve_ms=1000.0,
            street_budget_ms=15000.0,
        )
        self.assertFalse(failing["full_six_block_set_fits"])
        self.assertEqual(failing["headroom_ms"], -160.0)

    def test_config_source_or_batch_scope_mutation_is_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["batch_axis"] = "batch_everything"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_tier_b_opponent_batch_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_batch_implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_tier_b_opponent_batch_config(changed)

    def test_selector_result_is_hash_bound_but_never_deserialized(self) -> None:
        source = _IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertIn("expected_selector_result_sha256", source)
        self.assertNotIn("_SELECTOR_RESULT.read_text", source)
        self.assertNotIn("_LABEL_RESULT.read_text", source)
        self.assertIn('"strategy_labels_loaded": 0', source)


if __name__ == "__main__":
    unittest.main()
