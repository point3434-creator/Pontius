from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = (
    ROOT / "experiments/results/h32-current-decision-combined-ledger-replay-v1.json"
)
EXPECTED_SHA256 = "2176807c6c9712931fa457e02fbd9165308bd406c7183f42092602d313639077"


class H32CurrentDecisionCombinedLedgerReplayResultTests(unittest.TestCase):
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
            "authorize_preregistered_post_fold_current_decision_closure_and_"
            "value_confirmation",
        )

    def test_replay_opened_no_label_and_emitted_no_candidate(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["gpu_work"], 0)
        self.assertEqual(methodology["new_optimizer_labels"], 0)
        self.assertEqual(methodology["new_strategy_labels"], 0)
        self.assertEqual(methodology["post_fold_strategy_labels"], 0)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertIsNone(self.result["strategy_population_claim"])

    def test_exact_incremental_work_and_safe_retreats_are_sealed(self) -> None:
        rows = self.result["target_rows"]
        self.assertEqual(len(rows), 6)
        self.assertEqual([row["cut_rounds"] for row in rows], [1, 0, 0, 1, 0, 0])
        self.assertEqual(
            [row["combined_exact_oracles"] for row in rows],
            [3, 2, 2, 3, 2, 2],
        )
        for row in rows:
            self.assertTrue(all(row["identity"].values()))
            self.assertTrue(row["globally_closed"])
            self.assertTrue(row["incremental_endpoint_oracle_within_ceiling"])
            certificate = row["safe_retreat_certificate"]
            self.assertTrue(certificate["independently_certified"])
            self.assertTrue(certificate["cap_feasible"])
            self.assertTrue(certificate["interior_slack_passed"])
            self.assertTrue(certificate["acceptance_predicate_passed"])
            self.assertTrue(certificate["shadow_accepted"])
            self.assertGreater(certificate["exact_positive_value"], 0.0)

    def test_measured_and_conservative_ledgers_fit_the_street(self) -> None:
        aggregate = self.result["aggregate"]
        self.assertAlmostEqual(
            aggregate["maximum_incremental_endpoint_oracle_ms"],
            844.2939999949886,
        )
        self.assertAlmostEqual(
            aggregate["maximum_measured_combined_ledger_ms"],
            5884.573300002376,
        )
        self.assertAlmostEqual(
            aggregate["maximum_conservative_combined_ledger_ms"],
            14967.615699994712,
        )
        self.assertAlmostEqual(
            aggregate["minimum_conservative_combined_headroom_ms"],
            32.384300005287514,
        )
        self.assertTrue(all(row["measured_fits"] for row in self.result["target_rows"]))
        self.assertTrue(
            all(row["conservative_fits"] for row in self.result["target_rows"])
        )


if __name__ == "__main__":
    unittest.main()
