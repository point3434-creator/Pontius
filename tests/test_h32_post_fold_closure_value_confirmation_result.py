from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = (
    ROOT / "experiments/results/h32-post-fold-closure-value-confirmation-v1.json"
)
EXPECTED_SHA256 = "783c80b9b6029da962e34cf7be50a3bea331ec5f8b04fd7398e98924b951f8b1"


class H32PostFoldClosureValueConfirmationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = RESULT.read_bytes()
        cls.result = json.loads(raw)
        cls.digest = hashlib.sha256(raw).hexdigest()

    def test_result_bytes_and_process_gates_are_sealed(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)
        self.assertTrue(self.result["passed"])
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(
            self.result["decision"],
            "accept_execution_retain_direction_fallback_on_fresh_closure_failure",
        )

    def test_fresh_closure_fails_on_exactly_two_preregistered_rows(self) -> None:
        rows = self.result["target_rows"]
        failed = [
            row for row in rows if not row["endpoint_certificate"]["globally_closed"]
        ]
        self.assertEqual(self.result["closure"]["globally_closed_targets"], 4)
        self.assertFalse(self.result["closure"]["all_globally_closed"])
        self.assertEqual(
            [row["target_id"] for row in failed],
            [
                "panel_1/blocker_heavy/checks_then_bet_seat1_then_fold_seat2",
                "panel_3/balanced/checks_then_bet_seat4_then_fold_seat5",
            ],
        )
        self.assertEqual(
            [
                row["endpoint_certificate"]["exact_summary"][
                    "epigraph_violating_players"
                ]
                for row in failed
            ],
            [[0, 5], [2, 3]],
        )
        self.assertAlmostEqual(
            max(row["endpoint_certificate"]["optimality_gap"] for row in failed),
            0.000776346434034958,
        )

    def test_all_six_retreats_are_safe_positive_and_material(self) -> None:
        rows = self.result["target_rows"]
        self.assertTrue(self.result["aggregate"]["all_safe_positive"])
        self.assertEqual(self.result["aggregate"]["shadow_accepted_targets"], 6)
        self.assertEqual(self.result["aggregate"]["material_target_count"], 6)
        self.assertTrue(self.result["transfer"]["decision_aligned_value_transfers"])
        for row in rows:
            retreat = row["retreat"]
            self.assertTrue(retreat["independently_certified"])
            self.assertTrue(retreat["exact_certificate"]["cap_feasible"])
            self.assertTrue(retreat["interior_slack_passed"])
            self.assertTrue(retreat["shadow_accepted"])
            self.assertTrue(retreat["material_value"])
            self.assertGreater(retreat["exact_positive_value"], 0.001)
        self.assertAlmostEqual(
            self.result["aggregate"]["pooled_delivered_exact_value"],
            0.0471074700272206,
        )

    def test_oracle_accounting_and_complete_ledgers_pass(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["adaptive_construction_oracles"], 6)
        self.assertEqual(methodology["post_cut_endpoint_labels"], 5)
        self.assertEqual(methodology["final_retreat_labels"], 6)
        self.assertEqual(methodology["total_exact_oracles"], 17)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertLessEqual(
            self.result["closure"]["maximum_incremental_endpoint_oracle_ms"],
            1000.0,
        )
        self.assertAlmostEqual(
            self.result["aggregate"]["maximum_measured_live_ms"],
            5337.317399997846,
        )
        self.assertAlmostEqual(
            self.result["aggregate"]["maximum_effective_conservative_live_ms"],
            14967.615699994712,
        )
        self.assertTrue(
            all(row["ledger"]["fits_measured_street"] for row in self.result["target_rows"])
        )
        self.assertTrue(
            all(
                row["ledger"]["fits_effective_conservative_street"]
                for row in self.result["target_rows"]
            )
        )

    def test_claims_and_external_emission_remain_scoped(self) -> None:
        self.assertFalse(
            self.result["aggregate"]["fresh_closure_and_value_confirmed"]
        )
        self.assertIsNone(self.result["one_seat_global_optimality_claim"])
        self.assertIsNone(self.result["strategy_population_claim"])
        for row in self.result["target_rows"]:
            self.assertEqual(
                row["actual_emitted_policy_sha256"],
                row["restricted_blueprint_policy_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
