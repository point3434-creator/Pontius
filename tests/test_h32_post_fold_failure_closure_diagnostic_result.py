from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RESULT = (
    ROOT / "experiments/results/h32-post-fold-failure-closure-diagnostic-v1.json"
)
CHECKPOINT = (
    ROOT
    / "experiments/results/h32-post-fold-failure-closure-diagnostic-v1.partial.json"
)
EXPECTED_RESULT_SHA256 = (
    "dc20dcfbaaa3b861af2976f91bd8d1ce43f6e327e7f765dc97c98b333ff56802"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "aa7df3ac4a9f31ec52ce5c64014584d13fa782a3f4a0593a12d4495f02bb3eb6"
)
RECORDED_CANONICAL_TEXT_SHA256 = (
    "ae90841ef4a1145e2fcfce0e5209c24c0fad02b6b3180d8eab2833c32c1ad9e4"
)


class H32PostFoldFailureClosureDiagnosticResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result_bytes = RESULT.read_bytes()
        cls.checkpoint_bytes = CHECKPOINT.read_bytes()
        cls.result = json.loads(cls.result_bytes)
        cls.checkpoint = json.loads(cls.checkpoint_bytes)

    def test_result_bytes_and_every_frozen_gate_are_sealed(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.result_bytes).hexdigest(),
            EXPECTED_RESULT_SHA256,
        )
        self.assertTrue(self.result["passed"])
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(
            self.result["decision"],
            "fresh_failures_require_deeper_or_censored_closure_keep_"
            "global_solver_off_clock",
        )

    def test_checkpoint_is_complete_and_hash_telemetry_defect_is_disclosed(self) -> None:
        actual = hashlib.sha256(self.checkpoint_bytes).hexdigest()
        canonical_text = CHECKPOINT.read_text(encoding="utf-8").encode("utf-8")
        self.assertEqual(actual, EXPECTED_CHECKPOINT_SHA256)
        self.assertEqual(
            hashlib.sha256(canonical_text).hexdigest(),
            RECORDED_CANONICAL_TEXT_SHA256,
        )
        self.assertEqual(
            self.result["checkpoint_sha256"],
            RECORDED_CANONICAL_TEXT_SHA256,
        )
        self.assertNotEqual(self.result["checkpoint_sha256"], actual)
        self.assertEqual(self.checkpoint["attempted_targets"], 2)
        self.assertEqual(len(self.checkpoint["outcomes"]), 2)

    def test_both_targets_close_but_not_at_a_common_second_round(self) -> None:
        self.assertEqual(self.result["aggregate"]["converged_targets"], 2)
        self.assertEqual(
            self.result["aggregate"]["rounds_to_closure_histogram"],
            {"2": 1, "3": 1},
        )
        self.assertFalse(self.result["aggregate"]["both_close_at_round_two"])
        self.assertEqual(
            [row["rounds_to_closure"] for row in self.result["target_rows"]],
            [3, 2],
        )
        self.assertTrue(all(row["converged"] for row in self.result["target_rows"]))

    def test_later_round_facets_and_costs_are_exactly_retained(self) -> None:
        blocker, balanced = self.result["target_rows"]
        self.assertEqual(
            [row["new_cut_players"] for row in blocker["marginal_rounds_after_failed_round_one"]],
            [[0, 5], [0, 5]],
        )
        self.assertEqual(
            [row["new_cut_players"] for row in balanced["marginal_rounds_after_failed_round_one"]],
            [[2, 3]],
        )
        self.assertAlmostEqual(
            blocker["marginal_rounds_after_failed_round_one"][0]["incremental_ms"],
            556.2685000040802,
        )
        self.assertAlmostEqual(
            blocker["marginal_rounds_after_failed_round_one"][1]["incremental_ms"],
            555.1053999952273,
        )
        self.assertAlmostEqual(
            balanced["marginal_rounds_after_failed_round_one"][0]["incremental_ms"],
            764.9595999828307,
        )
        self.assertLessEqual(
            max(
                row["maximum_absolute_error"]
                for row in self.result["reproduction_rows"]
            ),
            3.1e-15,
        )

    def test_labels_and_external_behavior_remain_retrospective(self) -> None:
        methodology = self.result["methodology"]
        self.assertEqual(methodology["retrospective_optimizer_labels"], 7)
        self.assertEqual(methodology["new_retreat_labels"], 0)
        self.assertEqual(methodology["candidate_policies_emitted"], 0)
        self.assertIsNone(self.result["strategy_population_claim"])
        self.assertEqual(
            self.result["actual_emitted_policy"],
            "immutable_restricted_blueprint_only",
        )


if __name__ == "__main__":
    unittest.main()
