from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-decision-aligned-live-shadow-v1.json"
EXPECTED_SHA256 = "e926a64ca5d7ac55086607c3c697c51165777d888767f051359f19bb743b2d4f"


class H32DecisionAlignedLiveShadowResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = RESULT.read_bytes()
        cls.result = json.loads(raw)
        cls.digest = hashlib.sha256(raw).hexdigest()

    def test_result_bytes_process_and_decision_are_sealed(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)
        self.assertTrue(self.result["passed"])
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(
            self.result["decision"],
            "accept_decision_aligned_shadow_transfer_and_authorize_post_fold_preregistration",
        )

    def test_global_barrier_adapter_and_emission_contract_hold(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["candidates_frozen_before_labels"], 6)
        self.assertEqual(
            methodology["campaign_events"],
            [
                "inputs_pinned",
                "all_candidates_frozen",
                "all_retreat_certificates_complete",
            ],
        )
        self.assertTrue(methodology["setup_adapter_active_during_campaign"])
        self.assertTrue(methodology["setup_adapter_restored_after_campaign"])
        self.assertEqual(methodology["final_retreat_strategy_labels"], 6)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertFalse(methodology["cross_target_adaptation"])
        self.assertEqual(
            self.result["actual_emitted_policy"],
            "immutable_restricted_blueprint_only_on_all_targets",
        )

    def test_every_current_decision_is_exact_safe_accepted_and_inside_ledgers(self) -> None:
        rows = self.result["target_rows"]
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["root_current_player"], row["acting_player"])
            self.assertEqual(row["observed_response"], "call")
            self.assertEqual(row["acting_public_nodes"], 1)
            self.assertEqual(row["behavioral_information_sets"], 32)
            self.assertEqual(row["policy_variables"], 64)
            self.assertEqual(row["downstream_responders_after_actor"], 3)
            self.assertTrue(row["retreat"]["shadow_accepted"])
            self.assertTrue(row["retreat"]["exact_certificate"]["cap_feasible"])
            self.assertEqual(
                row["retreat"]["exact_certificate"]["maximum_cap_violation"],
                0.0,
            )
            self.assertGreaterEqual(
                row["retreat"]["exact_certificate"]["minimum_cap_slack"],
                row["retreat"]["required_interior_slack"],
            )
            self.assertTrue(row["retreat"]["interior_slack_passed"])
            self.assertTrue(row["ledger"]["fits_measured_street"])
            self.assertTrue(row["ledger"]["fits_effective_conservative_street"])
            self.assertEqual(row["exact_oracles_executed"], 2)
            self.assertLessEqual(row["cut_rounds"], 1)
            self.assertTrue(row["all_first_oracle_violators_accounted"])
            self.assertTrue(row["all_new_first_oracle_violators_cut"])
            self.assertEqual(
                row["actual_emitted_policy_sha256"],
                row["restricted_blueprint_policy_sha256"],
            )
            self.assertEqual(row["candidate_policies_emitted"], 0)

    def test_value_transfer_passes_at_the_frozen_threshold(self) -> None:
        transfer = self.result["transfer"]
        aggregate = self.result["aggregate"]
        self.assertTrue(transfer["decision_aligned_value_transfers"])
        self.assertEqual(transfer["material_target_count"], 4)
        self.assertEqual(
            set(transfer["material_range_families"]),
            {"balanced", "blocker_heavy"},
        )
        self.assertTrue(transfer["all_schedules_fit"])
        self.assertEqual(aggregate["shadow_accepted_targets"], 6)
        self.assertEqual(aggregate["material_target_count"], 4)
        self.assertAlmostEqual(
            aggregate["pooled_delivered_exact_value"],
            0.0510680060211276,
        )
        self.assertLessEqual(aggregate["maximum_measured_live_ms"], 15000.0)
        self.assertEqual(
            aggregate["maximum_effective_conservative_live_ms"],
            13967.615699994712,
        )

    def test_numerics_memory_and_claim_boundaries_hold(self) -> None:
        rows = self.result["target_rows"]
        self.assertLessEqual(
            max(row["maximum_initial_row_error"] for row in rows), 2e-11
        )
        self.assertLessEqual(max(row["maximum_cut_row_error"] for row in rows), 2e-11)
        self.assertLessEqual(
            max(row["maximum_profile_equivalence_error"] for row in rows), 2e-11
        )
        self.assertLessEqual(
            max(row["maximum_master_primal_error"] for row in rows), 1e-8
        )
        self.assertLessEqual(
            max(row["maximum_master_dual_error"] for row in rows), 1e-8
        )
        self.assertLessEqual(
            max(row["maximum_gpu_pool_total_bytes"] for row in rows),
            12_000_000_000,
        )
        self.assertGreaterEqual(
            min(row["minimum_gpu_free_bytes"] for row in rows),
            1_000_000_000,
        )
        self.assertIsNone(self.result["one_seat_global_optimality_claim"])
        self.assertIsNone(self.result["strategy_population_claim"])


if __name__ == "__main__":
    unittest.main()
