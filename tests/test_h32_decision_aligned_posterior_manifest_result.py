from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-decision-aligned-posterior-manifest-v1.json"
EXPECTED_SHA256 = "738bc251a66289ae6623255ddba85cee0f1b695ec1b9163768db3b28d340ea98"


class H32DecisionAlignedPosteriorManifestResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = RESULT.read_bytes()
        cls.result = json.loads(raw)
        cls.digest = hashlib.sha256(raw).hexdigest()

    def test_result_bytes_and_every_gate_are_sealed(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)
        self.assertTrue(self.result["passed"])
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(
            self.result["decision"],
            "authorize_preregistered_decision_aligned_live_shadow_trial",
        )

    def test_manifest_generated_no_strategy_label(self) -> None:
        methodology = self.result["methodology"]
        for field in (
            "new_warm_steps",
            "convex_candidates",
            "quality_evaluations",
            "certificates",
            "strategy_labels",
        ):
            self.assertEqual(methodology[field], 0)
        self.assertIsNone(self.result["strategy_population_claim"])

    def test_all_six_roots_are_current_decisions_with_downstream_geometry(self) -> None:
        rows = self.result["target_rows"]
        self.assertEqual(len(rows), 6)
        for field in ("observed_bettor", "observed_responder", "acting_player"):
            self.assertEqual(
                Counter(int(row[field]) for row in rows),
                Counter({seat: 1 for seat in range(6)}),
            )
        for row in rows:
            self.assertEqual(row["observed_responder"], (row["observed_bettor"] + 1) % 6)
            self.assertEqual(row["acting_player"], (row["observed_bettor"] + 2) % 6)
            self.assertEqual(row["root_current_player"], row["acting_player"])
            self.assertEqual(row["root_legal_actions"], ["fold", "call"])
            self.assertEqual(row["remaining_responders"], 4)
            self.assertEqual(row["downstream_responders_after_actor"], 3)
            self.assertEqual(row["continuation_public_nodes"], 31)
            self.assertEqual(row["acting_public_nodes"], 1)
            self.assertEqual(row["behavioral_information_sets"], 32)
            self.assertEqual(row["policy_variables"], 64)
            self.assertTrue(row["path_single_visit"])
            self.assertEqual(row["topology_mismatch_count"], 0)

    def test_identities_are_fresh_and_belief_shifts_are_nondegenerate(self) -> None:
        rows = self.result["target_rows"]
        self.assertEqual(len({row["target_belief_sha256"] for row in rows}), 6)
        for row in rows:
            self.assertTrue(row["target_id_fresh_at_base_commit"])
            self.assertTrue(row["target_digest_fresh_at_base_commit"])
            self.assertNotEqual(
                row["target_belief_sha256"],
                row["source_belief_sha256"],
            )
            self.assertGreater(row["observed_bettor_marginal_total_variation"], 0.0)
            self.assertGreater(
                row["observed_responder_marginal_total_variation"], 0.0
            )
            self.assertGreater(row["acting_player_marginal_total_variation"], 0.0)
            self.assertLessEqual(row["source_split_relative_error"], 1e-12)
            self.assertLessEqual(row["target_split_relative_error"], 1e-12)


if __name__ == "__main__":
    unittest.main()
