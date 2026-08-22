from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "experiments/results/h32-retained-convex-closure-census-v2.json"
CHECKPOINT = (
    ROOT / "experiments/results/h32-retained-convex-closure-census-v2.partial.json"
)
EXPECTED_RESULT_SHA256 = (
    "e0ad1af41061fce837ac689fcc0507c105346c2a3b8b08756e86285c17a0f3e3"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "0b193021d3c0279bcf3be40c705ea38aa4142589a5d803a3a6e2cde0d1810be0"
)


class H32RetainedConvexClosureCensusV2ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result_bytes = RESULT.read_bytes()
        checkpoint_bytes = CHECKPOINT.read_bytes()
        cls.result = json.loads(result_bytes)
        cls.result_sha256 = hashlib.sha256(result_bytes).hexdigest()
        cls.checkpoint_sha256 = hashlib.sha256(checkpoint_bytes).hexdigest()

    def test_result_checkpoint_and_every_process_gate_are_sealed(self) -> None:
        self.assertEqual(self.result_sha256, EXPECTED_RESULT_SHA256)
        self.assertEqual(self.checkpoint_sha256, EXPECTED_CHECKPOINT_SHA256)
        self.assertEqual(
            self.result["partial_checkpoint_sha256"],
            EXPECTED_CHECKPOINT_SHA256,
        )
        self.assertTrue(self.result["passed"])
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(
            self.result["decision"],
            "closure_census_is_censored_or_stalled_retain_live_direction_"
            "fallback",
        )

    def test_all_42_outcomes_are_durable_and_labels_are_disclosed(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["targets_attempted"], 42)
        self.assertEqual(methodology["targets_completed"], 41)
        self.assertEqual(methodology["target_errors_censored"], 1)
        self.assertEqual(
            methodology["retrospective_optimizer_labels_from_completed_targets"],
            104,
        )
        self.assertEqual(methodology["fresh_post_fold_strategy_labels"], 0)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertEqual(len(self.result["target_outcomes"]), 42)
        self.assertEqual(
            [row["inventory_index"] for row in self.result["target_outcomes"]],
            list(range(42)),
        )

    def test_closure_distribution_rejects_universal_one_round(self) -> None:
        aggregate = self.result["aggregate"]
        self.assertEqual(aggregate["converged_targets"], 35)
        self.assertEqual(aggregate["one_round_closed_targets"], 18)
        self.assertEqual(aggregate["stalled_or_resource_censored_targets"], 6)
        self.assertEqual(aggregate["target_error_count"], 1)
        self.assertEqual(
            aggregate["rounds_to_closure_histogram"],
            {
                "0": 7,
                "1": 11,
                "2": 10,
                "3": 7,
                "censored:error:ArithmeticError": 1,
                "censored:no_new_facet_without_cap_or_bound_closure": 6,
            },
        )
        self.assertFalse(aggregate["universal_full_closure"])
        self.assertFalse(aggregate["universal_one_round_closure"])
        self.assertEqual(aggregate["maximum_rounds_to_closure"], 3)

    def test_current_decision_subgroup_closes_in_zero_or_one_round(self) -> None:
        current = [
            row for row in self.result["target_rows"] if row["panel"] == "post_call"
        ]
        self.assertEqual(len(current), 6)
        self.assertTrue(all(row["converged"] for row in current))
        self.assertEqual(
            Counter(int(row["rounds_to_closure"]) for row in current),
            Counter({0: 4, 1: 2}),
        )
        self.assertTrue(all(row["total_seconds"] < 10.0 for row in current))
        self.assertTrue(
            all(
                row["actual_emitted_policy_sha256"]
                == row["restricted_blueprint_policy_sha256"]
                for row in current
            )
        )

    def test_every_facet_closed_stall_is_exact_cap_infeasible(self) -> None:
        stalled = [row for row in self.result["target_rows"] if not row["converged"]]
        self.assertEqual(len(stalled), 6)
        for row in stalled:
            final = row["iterations"][-1]
            self.assertEqual(final["new_violating_players"], [])
            self.assertFalse(final["oracle"]["cap_feasible"])
            self.assertGreater(
                final["oracle"]["maximum_cap_violation"],
                2e-11,
            )
            self.assertGreater(row["optimality_gap"], 1e-8)
            self.assertEqual(
                row["stop_reason"],
                "no_new_facet_without_cap_or_bound_closure",
            )

    def test_known_master_failure_and_keystone_are_both_preserved(self) -> None:
        self.assertEqual(len(self.result["target_errors"]), 1)
        error = self.result["target_errors"][0]
        self.assertTrue(error["allowed_known_error"])
        self.assertEqual(error["error_type"], "ArithmeticError")
        self.assertEqual(
            error["error_message"],
            "behavioral master primal/dual verification failed",
        )
        replay = self.result["keystone_replay"]
        self.assertTrue(replay["discrete_identity"])
        self.assertEqual(replay["census_first_cut_players"], [4, 5])
        self.assertLessEqual(replay["maximum_absolute_error"], 2e-11)


if __name__ == "__main__":
    unittest.main()
