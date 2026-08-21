from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.delta_certificate_contract import geometric_halving_scales
from pontius.h32_fresh_public_block_radius_audit import (
    certificate_binding_diagnostics,
    direction_information_keys,
    parse_h32_fresh_public_block_radius_config,
    summarize_direction_rows,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-public-block-radius-v1.json"


class H32FreshPublicBlockRadiusAuditTests(unittest.TestCase):
    def test_contract_rejects_target_direction_floor_parent_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_public_block_radius_config(config)
        self.assertEqual(parsed["local_blocker_target_seat"], 0)
        self.assertEqual(len(geometric_halving_scales(numerical_floor=parsed["numerical_floor"])), 34)

        mutated = json.loads(json.dumps(config))
        mutated["targets"][0]["target_belief_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_public_block_radius_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["directions"][2]["acting_seats"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_public_block_radius_config(mutated)

        mutated = dict(config)
        mutated["numerical_floor"] = 1e-9
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_public_block_radius_config(mutated)

        mutated = dict(config)
        mutated["expected_parent_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_public_block_radius_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["expected_scale_rows"] = 6
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_fresh_public_block_radius_config(mutated)

    def test_direction_keys_preserve_frozen_seat_and_block_order(self) -> None:
        blocks = [
            {"acting_seat": seat, "information_keys": [f"s{seat}-a", f"s{seat}-b"]}
            for seat in range(6)
        ]
        self.assertEqual(
            direction_information_keys(blocks, [1, 2]),
            ("s1-a", "s1-b", "s2-a", "s2-b"),
        )
        with self.assertRaisesRegex(ValueError, "cannot be resolved"):
            direction_information_keys(blocks, [6])

    def test_binding_diagnostics_match_verifier_stop_semantics(self) -> None:
        blueprint = {"deviation_gains": [1.0, 2.0], "nash_conv": 3.0}
        cap = {
            "stop_reason": "blueprint_cap",
            "stop_seat": 1,
            "partial_nash_conv": 2.0,
            "seat_rows": [{"deviation_gain": 2.25}],
        }
        self.assertAlmostEqual(
            certificate_binding_diagnostics(cap, blueprint, 0.1)["cap_excess"],
            0.15,
        )
        objective = {
            "stop_reason": "objective_lower_bound",
            "stop_seat": 1,
            "partial_nash_conv": 3.4,
            "seat_rows": [{"deviation_gain": 1.0}],
        }
        self.assertAlmostEqual(
            certificate_binding_diagnostics(objective, blueprint, 0.1)["objective_excess"],
            0.3,
        )

    def test_summary_reports_window_without_assuming_monotonicity(self) -> None:
        def row(index: int, scale: float, reason: str, value: float = 0.0) -> dict:
            return {
                "scale_index": index,
                "scale": scale,
                "positive_certified_value": value,
                "value_per_certificate_second": value,
                "certificate": {"complete": reason == "complete", "stop_reason": reason},
            }

        summary = summarize_direction_rows(
            [
                row(0, 1.0, "blueprint_cap"),
                row(1, 0.5, "complete", 0.2),
                row(2, 0.25, "objective_lower_bound"),
            ]
        )
        self.assertEqual(summary["classification"], "bounded_admissible_grid_window")
        self.assertEqual(summary["largest_complete_scale"], 0.5)
        self.assertEqual(summary["smallest_complete_scale"], 0.5)
        self.assertEqual(summary["stop_reason_transition_count"], 2)


if __name__ == "__main__":
    unittest.main()
