from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/one-seat-convex-keystone-v1.json"
_EXPECTED_SHA256 = "c9734813feddee76ddcbac7917544c7bf869dfbc76b8365233f04065985155fb"


class OneSeatConvexKeystoneResultTests(unittest.TestCase):
    def test_accepted_artifact_is_pinned_and_matches_the_frozen_branch(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)

        self.assertTrue(result["passed"])
        self.assertEqual(
            result["decision"],
            "authorize_h4_open_axis_cut_extraction_differential",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "2aa3cb97dc776ac456b39fc9fa752783b947f343",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])
        self.assertTrue(all(result["gates"].values()))

        rows = result["acting_seat_rows"]
        self.assertEqual([row["acting_player"] for row in rows], [0, 1])
        self.assertTrue(all(row["converged"] for row in rows))
        self.assertEqual([row["iterations"] for row in rows], [5, 3])
        self.assertEqual(
            [row["generated_response_rows_by_player"] for row in rows],
            [[1, 5], [3, 1]],
        )
        self.assertTrue(
            all(row["teacher_objective_error"] <= 1e-9 for row in rows)
        )
        self.assertTrue(all(row["optimality_gap"] <= 1e-9 for row in rows))
        self.assertTrue(
            all(row["exact_duplicate_response_hits"] == 0 for row in rows)
        )


if __name__ == "__main__":
    unittest.main()
