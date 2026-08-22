from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json"
CONFIG = ROOT / "experiments/configs/h32-latin-f-convex-retreat-confirmation-v1.json"
EXPECTED_SHA256 = "3bc21cee836f7327d967ef363ff367b7538d1992da052903dab21a1d6450a73b"
PREREGISTRATION_COMMIT = "9f623e65bb6cdb7da039fce1285ec5d9bb7c059d"


class H32LatinFConvexRetreatConfirmationResultTests(unittest.TestCase):
    def test_untouched_panel_confirms_breadth_with_two_interior_abstentions(self) -> None:
        raw = RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_SHA256)
        result = json.loads(raw)
        config = json.loads(CONFIG.read_text(encoding="utf-8"))

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration",
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
        self.assertEqual(methodology["fresh_latin_f_targets"], 6)
        self.assertEqual(methodology["final_retreat_strategy_labels"], 6)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertFalse(methodology["cross_target_adaptation"])

        rows = result["target_rows"]
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["round"] for row in rows}, {"latin_f"})
        self.assertEqual({row["observed_bettor"] for row in rows}, set(range(6)))
        self.assertEqual({row["acting_player"] for row in rows}, set(range(6)))
        self.assertEqual(
            Counter(row["range_family"] for row in rows),
            {"balanced": 3, "blocker_heavy": 3},
        )
        self.assertEqual(
            [row["retreat"]["shadow_accepted"] for row in rows],
            [True, True, True, True, False, False],
        )

        raw_values = []
        delivered_values = []
        for row in rows:
            retreat = row["retreat"]
            certificate = retreat["exact_certificate"]
            raw_values.append(retreat["exact_positive_value"])
            delivered_values.append(
                retreat["exact_positive_value"] if retreat["shadow_accepted"] else 0.0
            )
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
            self.assertTrue(retreat["independently_certified"])
            self.assertTrue(retreat["material_value"])
            self.assertGreater(retreat["exact_positive_value"], 0.001)
            self.assertTrue(certificate["cap_feasible"])
            self.assertEqual(certificate["maximum_cap_violation"], 0.0)
            self.assertTrue(row["ledger"]["fits_measured_street"])
            self.assertTrue(row["ledger"]["fits_effective_conservative_street"])
            self.assertAlmostEqual(
                math.fsum(row["ledger"]["components_ms"].values()),
                row["ledger"]["measured_live_ms"],
            )
            self.assertEqual(row["exact_oracles_executed"], 2)
            self.assertTrue(row["all_first_oracle_violators_accounted"])
            self.assertTrue(row["all_new_first_oracle_violators_cut"])
            self.assertEqual(row["candidate_policies_emitted"], 0)
            self.assertEqual(
                row["actual_emitted_policy_sha256"],
                row["restricted_blueprint_policy_sha256"],
            )

        for row in rows[:4]:
            self.assertTrue(row["retreat"]["interior_slack_passed"])
            self.assertGreaterEqual(
                row["retreat"]["exact_certificate"]["minimum_cap_slack"],
                row["retreat"]["required_interior_slack"],
            )
        for row in rows[4:]:
            self.assertFalse(row["retreat"]["interior_slack_passed"])
            self.assertLess(
                row["retreat"]["exact_certificate"]["minimum_cap_slack"],
                row["retreat"]["required_interior_slack"],
            )
            self.assertTrue(row["retreat"]["exact_certificate"]["cap_feasible"])

        self.assertAlmostEqual(math.fsum(raw_values), 0.05833345645895788)
        self.assertAlmostEqual(math.fsum(delivered_values), 0.045509775764524085)
        self.assertEqual([len(row["cut_rows"]) for row in rows], [1, 0, 3, 1, 1, 2])
        self.assertEqual(
            [len(row["resident_response_residual_rows"]) for row in rows],
            [0, 0, 0, 0, 0, 1],
        )

        confirmation = result["confirmation"]
        self.assertEqual(confirmation["material_target_count"], 4)
        self.assertEqual(
            set(confirmation["material_range_families"]),
            {"balanced", "blocker_heavy"},
        )
        self.assertTrue(confirmation["all_schedules_fit"])
        self.assertTrue(confirmation["confirms_latin_e_breadth"])
        self.assertAlmostEqual(
            result["latin_e_parent"]["pooled_delivered_exact_value"]
            + result["aggregate"]["pooled_delivered_exact_value"],
            0.11043829383606896,
        )
        self.assertEqual(
            result["actual_emitted_policy"],
            "immutable_restricted_blueprint_only_on_all_targets",
        )
        self.assertEqual(
            result["strategy_quality_claim"],
            "six_fresh_latin_f_shadow_confirmation_measurement_only",
        )
        self.assertIsNone(result["one_seat_global_optimality_claim"])
        self.assertIsNone(result["strategy_population_claim"])


if __name__ == "__main__":
    unittest.main()
