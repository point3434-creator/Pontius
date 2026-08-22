from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h32-one-round-convex-master-v1.json"
_CONFIG = _ROOT / "experiments/configs/h32-one-round-convex-master-v1.json"
_EXPECTED_SHA256 = "6e09c69c5447b3313ae3db36f96eb9af81b779dd3e60b4851f7a6e8a3172d8ab"


class H32OneRoundConvexMasterResultTests(unittest.TestCase):
    def test_accepted_artifact_closes_the_frozen_one_round_branch(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "authorize_later_preregistered_one_seat_quality_trial",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "a5b1e98d7593a7f443ba722136d5743d8f882b4f",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])

        target = result["target"]
        self.assertTrue(target["path_single_visit"])
        self.assertEqual(target["behavioral_information_sets"], 512)
        self.assertEqual(target["policy_variables"], 1024)
        self.assertEqual(target["initial_gain_rows"], 6)
        self.assertEqual(target["cut_rounds"], 1)
        self.assertEqual(
            [row["target_player"] for row in target["cut_rows"]],
            [4, 5],
        )
        self.assertEqual(target["row_counts_by_player"], [1, 1, 1, 1, 2, 2])
        self.assertTrue(target["converged_after_frozen_round"])
        self.assertTrue(target["lower_bound_nondecreasing"])
        self.assertLessEqual(target["optimality_gap"], config["bound_tolerance"])
        self.assertLessEqual(
            target["final_oracle"]["maximum_epigraph_violation"],
            config["separation_tolerance"],
        )

        # The frozen runner accidentally used the looser separation tolerance
        # for its cap-feasible Boolean. Recheck the serialized exact maximum
        # against the distinct, preregistered envelope allowance so that the
        # accepted branch does not depend on that threshold conflation.
        self.assertLessEqual(
            target["final_oracle"]["maximum_cap_violation"],
            config["envelope_numerical_allowance"],
        )
        self.assertTrue(target["ledger"]["fits_measured_street"])
        self.assertTrue(target["ledger"]["fits_corrected_conservative_street"])
        self.assertEqual(target["candidate_policies_emitted"], 0)
        self.assertEqual(target["strategy_quality_labels_generated"], 0)
        self.assertIsNone(result["strategy_quality_claim"])


if __name__ == "__main__":
    unittest.main()
