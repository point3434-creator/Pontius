from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_one_seat_open_axis_preflight import (
    _parse_config,
    derive_cut_round_capacity,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-one-seat-open-axis-preflight-v1.json"


class H32OneSeatOpenAxisPreflightTests(unittest.TestCase):
    def test_frozen_config_prices_one_widest_seat_without_quality_labels(self) -> None:
        parsed = _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["acting_player"], 0)
        self.assertEqual(
            parsed["target"]["target_id"],
            "panel_2/balanced/checks_then_bet_seat1",
        )
        self.assertEqual(parsed["gates"]["expected_acting_public_nodes"], 16)
        self.assertEqual(parsed["gates"]["expected_profile_passes"], 6)
        self.assertEqual(parsed["gates"]["expected_fixed_response_passes"], 5)
        self.assertIn("zero_quality_values", parsed["strategy_label_policy"])

    def test_round_capacity_reserves_each_oracle_and_a_separate_final_proof(self) -> None:
        result = derive_cut_round_capacity(
            warm_step_ms=1000.0,
            initial_row_construction_ms=2000.0,
            source_response_oracle_ms=1000.0,
            response_row_construction_ms=1000.0,
            street_budget_ms=15000.0,
            response_oracle_safety_factor=1.25,
            row_round_safety_factor=1.25,
            minimum_final_certificate_reserve_ms=1250.0,
            master_reserve_per_round_ms=500.0,
            retreat_envelope_reserve_ms=50.0,
            emission_reserve_ms=1000.0,
        )
        self.assertEqual(result["response_oracle_and_final_certificate_reserve_ms"], 1250.0)
        self.assertEqual(result["new_response_rows_reserve_per_round_ms"], 1250.0)
        self.assertEqual(result["complete_cut_round_ms"], 3000.0)
        self.assertEqual(result["fixed_before_cut_rounds_ms"], 5300.0)
        self.assertEqual(result["conservative_complete_cut_rounds"], 3)
        self.assertEqual(result["one_round_complete_ledger_ms"], 8300.0)
        self.assertTrue(result["fits_one_complete_cut_round"])

    def test_capacity_miss_is_reported_without_hiding_fixed_final_proof(self) -> None:
        result = derive_cut_round_capacity(
            warm_step_ms=4000.0,
            initial_row_construction_ms=5000.0,
            source_response_oracle_ms=3000.0,
            response_row_construction_ms=2000.0,
            street_budget_ms=15000.0,
            response_oracle_safety_factor=1.25,
            row_round_safety_factor=1.25,
            minimum_final_certificate_reserve_ms=1250.0,
            master_reserve_per_round_ms=500.0,
            retreat_envelope_reserve_ms=50.0,
            emission_reserve_ms=1000.0,
        )
        self.assertEqual(result["response_oracle_and_final_certificate_reserve_ms"], 3750.0)
        self.assertEqual(result["fixed_before_cut_rounds_ms"], 13800.0)
        self.assertEqual(result["conservative_complete_cut_rounds"], 0)
        self.assertFalse(result["fits_one_complete_cut_round"])

    def test_invalid_safety_discount_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            derive_cut_round_capacity(
                warm_step_ms=1.0,
                initial_row_construction_ms=1.0,
                source_response_oracle_ms=1.0,
                response_row_construction_ms=1.0,
                street_budget_ms=15.0,
                response_oracle_safety_factor=0.99,
                row_round_safety_factor=1.0,
                minimum_final_certificate_reserve_ms=1.0,
                master_reserve_per_round_ms=1.0,
                retreat_envelope_reserve_ms=1.0,
                emission_reserve_ms=1.0,
            )


if __name__ == "__main__":
    unittest.main()
