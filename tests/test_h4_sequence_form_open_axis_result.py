from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h4-sequence-form-open-axis-v1.json"
_EXPECTED_SHA256 = "f646af38a3e08fa5f9d926c1ba445633d610d4f8e4d1c7be722a2f3e9e9aae02"


class H4SequenceFormOpenAxisResultTests(unittest.TestCase):
    def test_accepted_artifact_is_pinned_and_matches_the_frozen_branch(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)

        self.assertTrue(result["passed"])
        self.assertEqual(
            result["decision"],
            "authorize_external_axis_h32_row_extraction_preflight",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "a7d052327204e849745dd2b63b0c08e3c0e7c44b",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])
        self.assertTrue(all(result["gates"].values()))

        rows = {row["layout_id"]: row for row in result["layout_rows"]}
        repeated = rows["full_repeated_actor"]
        continuation = rows["post_bet_single_visit"]
        self.assertFalse(repeated["path_single_visit"])
        self.assertEqual(repeated["sequence_entries_per_row"], 256)
        self.assertTrue(continuation["path_single_visit"])
        self.assertEqual(continuation["sequence_entries_per_row"], 8)
        for row in rows.values():
            self.assertEqual(row["profile_passes"], 6)
            self.assertEqual(row["fixed_response_passes"], 5)
            self.assertLessEqual(row["maximum_profile_row_error"], 2e-11)
            self.assertLessEqual(row["maximum_fixed_response_row_error"], 2e-11)
            self.assertLessEqual(row["maximum_gain_row_error"], 2e-11)

        mutation = result["external_axis_mutation"]
        self.assertTrue(mutation["passed"])
        self.assertEqual(mutation["corrected_splice_errors"], 0)
        self.assertGreater(mutation["embedded_splice_mismatch_entries"], 0)


if __name__ == "__main__":
    unittest.main()
