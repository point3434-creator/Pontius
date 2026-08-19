from __future__ import annotations

import unittest

from pontius.multiway_river_calibration import run_multiway_river_calibration


def config() -> dict[str, object]:
    return {
        "evidence_stage": "revealed_engineering_calibration",
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "hands_per_player": [1, 2],
        "range_weight_rule": "disjoint_linear_index",
        "solver": "dcfr",
        "candidate_iterations": 2,
        "timing_repeats": 1,
        "warmup_repeats": 1,
        "frozen_contract_sha256": (
            "b98ee2c73b7b3c93a686ecc5d783756990fbd06b7c911a2e8f52521368e358f4"
        ),
        "maximum_exact_error": 1e-10,
    }


class MultiwayRiverCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_multiway_river_calibration(config())

    def test_exactness_and_cubic_deal_gates_pass(self) -> None:
        self.assertTrue(self.result["gates"]["passed"])
        self.assertTrue(all(self.result["gates"]["results"].values()))
        self.assertEqual(
            [row["joint_deals"] for row in self.result["rows"]],
            [1, 8],
        )
        self.assertEqual(
            self.result["aggregate"]["best_response_action_mismatches"],
            0,
        )

    def test_tape_costs_are_separated_from_hot_evaluation(self) -> None:
        for row in self.result["rows"]:
            self.assertGreater(row["policy_tape_compile_median_ms"], 0.0)
            self.assertGreater(row["hot_dense_candidate_evaluation_median_ms"], 0.0)
            self.assertGreater(row["tape_runtime_bytes"], 0)

    def test_unknown_field_or_nonrevealed_stage_is_rejected(self) -> None:
        unknown = config()
        unknown["strategy_gate"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            run_multiway_river_calibration(unknown)

        hidden = config()
        hidden["evidence_stage"] = "preregistered_holdout"
        with self.assertRaisesRegex(ValueError, "explicitly revealed"):
            run_multiway_river_calibration(hidden)

        changed_contract = config()
        changed_contract["frozen_contract_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "contract SHA-256 changed"):
            run_multiway_river_calibration(changed_contract)


if __name__ == "__main__":
    unittest.main()
