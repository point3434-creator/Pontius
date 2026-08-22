from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-fresh-convex-retreat-replication-v2.json"
CONFIG = ROOT / "experiments/configs/h32-fresh-convex-retreat-replication-v2.json"
EXPECTED_SHA256 = "daaad3080637284d5413f156bad5df19256f8e7a36829026076ea38aeae1355e"
PREREGISTRATION_COMMIT = "2c353a93ca0fd9575e6c76fabbde893cc786a7c2"


class H32FreshConvexRetreatReplicationResultTests(unittest.TestCase):
    def test_label_blind_campaign_passes_exact_breadth_branch(self) -> None:
        raw = RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_SHA256)
        result = json.loads(raw)
        config = json.loads(CONFIG.read_text(encoding="utf-8"))

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "authorize_preregistered_latin_f_convex_retreat_confirmation",
        )
        self.assertEqual(result["environment"]["git"]["commit"], PREREGISTRATION_COMMIT)
        self.assertFalse(result["environment"]["git"]["dirty"])
        self.assertEqual(
            result["config_sha256"], hashlib.sha256(CONFIG.read_bytes()).hexdigest()
        )
        self.assertEqual(
            result["implementation_sha256"],
            config["expected_implementation_sha256"],
        )

        methodology = result["methodology"]
        self.assertEqual(
            methodology["campaign_events"],
            [
                "inputs_pinned",
                "all_candidates_frozen",
                "all_retreat_certificates_complete",
            ],
        )
        self.assertEqual(methodology["candidates_frozen_before_labels"], 6)
        self.assertEqual(methodology["adaptive_construction_oracles"], 6)
        self.assertEqual(methodology["final_retreat_strategy_labels"], 6)
        self.assertEqual(methodology["latin_f_strategy_quality_labels"], 0)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertFalse(methodology["cross_target_adaptation"])
        self.assertEqual(methodology["label_blind_reconstructed_targets"], 1)

        rows = result["target_rows"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(Counter(row["source"] for row in rows), Counter({row["source"]: 1 for row in rows}))
        self.assertEqual({row["observed_bettor"] for row in rows}, set(range(6)))
        self.assertEqual({row["acting_player"] for row in rows}, set(range(6)))
        self.assertEqual(Counter(row["range_family"] for row in rows), {"balanced": 3, "blocker_heavy": 3})
        self.assertEqual({row["round"] for row in rows}, {"latin_e"})

        values = []
        for row in rows:
            retreat = row["retreat"]
            certificate = retreat["exact_certificate"]
            values.append(retreat["exact_positive_value"])
            self.assertEqual(
                row["label_barrier"]["events"],
                [
                    "inputs_pinned",
                    "candidate_frozen",
                    "retreat_certificate_complete",
                ],
            )
            self.assertTrue(all(row["label_barrier"]["prelabel_checks"].values()))
            self.assertTrue(all(row["certificate_reconstruction"]["checks"].values()))
            self.assertTrue(row["certificate_reconstruction"]["excluded_from_live_ledger"])
            self.assertTrue(retreat["independently_certified"])
            self.assertTrue(retreat["shadow_accepted"])
            self.assertTrue(retreat["acceptance_predicate_passed"])
            self.assertGreater(retreat["exact_positive_value"], 0.001)
            self.assertTrue(certificate["cap_feasible"])
            self.assertEqual(certificate["maximum_cap_violation"], 0.0)
            self.assertGreaterEqual(
                certificate["minimum_cap_slack"],
                retreat["required_interior_slack"],
            )
            self.assertEqual(row["exact_oracles_executed"], 2)
            self.assertTrue(row["all_first_oracle_violators_accounted"])
            self.assertTrue(row["all_new_first_oracle_violators_cut"])
            self.assertLessEqual(
                row["maximum_resident_row_identity_error"],
                config["gates"]["maximum_resident_row_identity_error"],
            )
            self.assertLessEqual(
                row["maximum_resident_epigraph_residual"],
                config["gates"]["maximum_resident_epigraph_residual"],
            )
            self.assertTrue(row["ledger"]["fits_measured_street"])
            self.assertTrue(row["ledger"]["fits_effective_conservative_street"])
            self.assertAlmostEqual(
                math.fsum(row["ledger"]["components_ms"].values()),
                row["ledger"]["measured_live_ms"],
            )
            self.assertLessEqual(
                row["maximum_gpu_pool_total_bytes"],
                config["gates"]["maximum_gpu_pool_bytes"],
            )
            self.assertGreaterEqual(
                row["minimum_gpu_free_bytes"],
                config["gates"]["minimum_physical_free_bytes"],
            )
            self.assertEqual(row["payoff_span"], 30.0)
            self.assertEqual(row["raw_guard"], 3e-9)
            self.assertEqual(row["candidate_policies_emitted"], 0)
            self.assertEqual(
                row["actual_emitted_policy_sha256"],
                row["restricted_blueprint_policy_sha256"],
            )

        self.assertAlmostEqual(math.fsum(values), 0.06492851807154487)
        self.assertAlmostEqual(min(values), 0.001702021366485007)
        self.assertEqual([len(row["cut_rows"]) for row in rows], [2, 0, 2, 2, 3, 1])
        self.assertEqual(
            [len(row["resident_response_residual_rows"]) for row in rows],
            [0, 3, 0, 1, 0, 0],
        )
        corrected = rows[1]
        self.assertLessEqual(corrected["maximum_resident_row_identity_error"], 5e-16)
        self.assertAlmostEqual(
            corrected["maximum_resident_epigraph_residual"],
            corrected["maximum_master_primal_error"],
            delta=5e-16,
        )

        promotion = result["promotion"]
        self.assertEqual(promotion["material_target_count"], 6)
        self.assertEqual(
            set(promotion["material_range_families"]),
            {"balanced", "blocker_heavy"},
        )
        self.assertTrue(promotion["all_schedules_fit"])
        self.assertTrue(promotion["authorizes_latin_f_confirmation"])
        self.assertEqual(
            result["actual_emitted_policy"],
            "immutable_restricted_blueprint_only_on_all_targets",
        )
        self.assertEqual(
            result["strategy_quality_claim"],
            "six_target_label_blind_shadow_measurement_only",
        )
        self.assertIsNone(result["one_seat_global_optimality_claim"])
        self.assertIsNone(result["strategy_population_claim"])


if __name__ == "__main__":
    unittest.main()
