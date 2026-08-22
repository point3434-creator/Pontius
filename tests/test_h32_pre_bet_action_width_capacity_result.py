from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
CHECKPOINT = (
    ROOT
    / "experiments/results/h32-pre-bet-action-width-capacity-v1.partial.json"
)
CONFIG = ROOT / "experiments/configs/h32-pre-bet-action-width-capacity-v1.json"
EXPECTED_RESULT_SHA256 = (
    "d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "a94e66fda42258cc4494cd3d026de7b9c97b8757da40f4e560e5ab5e232360e0"
)


class H32PreBetActionWidthCapacityResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result_bytes = RESULT.read_bytes()
        checkpoint_bytes = CHECKPOINT.read_bytes()
        cls.result = json.loads(result_bytes)
        cls.checkpoint = json.loads(checkpoint_bytes)
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.result_sha256 = hashlib.sha256(result_bytes).hexdigest()
        cls.checkpoint_sha256 = hashlib.sha256(checkpoint_bytes).hexdigest()

    def test_artifacts_seal_the_rejected_invocation(self) -> None:
        self.assertEqual(self.result_sha256, EXPECTED_RESULT_SHA256)
        self.assertEqual(self.checkpoint_sha256, EXPECTED_CHECKPOINT_SHA256)
        self.assertEqual(
            self.result["checkpoint_sha256"],
            EXPECTED_CHECKPOINT_SHA256,
        )
        self.assertFalse(self.result["passed"])
        self.assertEqual(
            {name for name, passed in self.result["gates"].items() if not passed},
            {"passed", "resource_caps"},
        )
        self.assertEqual(
            self.result["decision"],
            "reject_pre_bet_action_width_capacity_execution",
        )

    def test_checkpoint_contains_the_complete_frozen_matrix(self) -> None:
        self.assertEqual(self.checkpoint["phase"], "runtime")
        self.assertEqual(self.checkpoint["cache_targets_completed"], 36)
        self.assertEqual(self.checkpoint["runtime_targets_completed"], 36)
        self.assertEqual(len(self.checkpoint["cache_rows"]), 36)
        self.assertEqual(len(self.checkpoint["runtime_rows"]), 36)
        self.assertEqual(self.result["methodology"]["cache_arms"], 72)
        self.assertEqual(self.result["methodology"]["warm_steps"], 72)

    def test_outer_duration_is_the_only_resource_subgate_that_failed(self) -> None:
        gate = self.config["gates"]
        cache_arms = [
            arm
            for row in self.result["cache_rows"]
            for arm in row["arms"].values()
        ]
        runtime_arms = [
            arm
            for row in self.result["runtime_rows"]
            for arm in row["arms"].values()
        ]
        self.assertGreater(
            self.result["total_seconds"],
            self.config["maximum_campaign_seconds"],
        )
        self.assertTrue(
            all(
                arm["cache"]["device_cache_compile_ms"]
                <= gate["maximum_cache_compile_ms"]
                and arm["cache"]["pool_total_bytes"]
                <= gate["maximum_gpu_pool_bytes"]
                and arm["cache"]["physical_device_free_bytes"]
                >= gate["minimum_physical_free_bytes"]
                for arm in cache_arms
            )
        )
        self.assertTrue(
            all(
                arm["warm_step"]["wall_ms"] <= gate["maximum_warm_step_ms"]
                and arm["initial_row_ms"] <= gate["maximum_initial_row_ms"]
                for arm in runtime_arms
            )
        )

    def test_shared_topology_makes_widening_memory_safe_but_cold(self) -> None:
        paired = [
            (row["arms"]["one_size"]["cache"], row["arms"]["two_size"]["cache"])
            for row in self.result["cache_rows"]
        ]
        self.assertTrue(self.result["all_cache_safe_for_runtime"])
        self.assertEqual(
            self.result["aggregate"]["maximum_gpu_pool_total_bytes"],
            5_169_158_656,
        )
        self.assertEqual(
            self.result["aggregate"]["minimum_physical_free_bytes"],
            9_960_423_424,
        )
        self.assertTrue(
            all(
                two["persistent_numeric_bytes"] < one["persistent_numeric_bytes"]
                for one, two in paired
            )
        )
        self.assertTrue(
            all(
                two["raw_equivalent_automaton_numeric_bytes"]
                > one["raw_equivalent_automaton_numeric_bytes"]
                and two["total_logical_middle_rank"]
                > one["total_logical_middle_rank"]
                and two["stored_topology_middle_rank"]
                < one["stored_topology_middle_rank"]
                for one, two in paired
            )
        )
        cold_ratios = [
            two["cold_construction_ms"] / one["cold_construction_ms"]
            for one, two in paired
        ]
        self.assertAlmostEqual(statistics.median(cold_ratios), 6.277671662884783)

    def test_capacity_matrix_authorizes_no_widened_position(self) -> None:
        aggregate = self.result["aggregate"]
        self.assertEqual(aggregate["admitted_acting_players"], [])
        self.assertEqual(aggregate["admitted_position_count"], 0)
        self.assertEqual(aggregate["arm_fit_counts"], {"one_size": 9})
        self.assertTrue(
            all(not row["two_size_all_fit"] for row in self.result["position_rows"])
        )
        self.assertTrue(self.result["position_rows"][5]["one_size_all_fit"])
        two_size_proxies = [
            row["arms"]["two_size"]["capacity"]["complete_one_round_proxy_ms"]
            for row in self.result["runtime_rows"]
        ]
        self.assertAlmostEqual(min(two_size_proxies), 15_811.628899999778)
        self.assertAlmostEqual(max(two_size_proxies), 132_078.28460000455)

    def test_no_widened_strategy_label_or_policy_was_opened(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["master_candidate_endpoint_evaluations"], 0)
        self.assertEqual(methodology["retreat_or_certificate_evaluations"], 0)
        self.assertEqual(methodology["strategy_quality_rows_serialized"], 0)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertIsNone(self.result["strategy_population_claim"])
        self.assertEqual(
            self.result["actual_emitted_policy"],
            "immutable_one_size_blueprint_only",
        )


if __name__ == "__main__":
    unittest.main()
