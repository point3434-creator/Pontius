from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h32-one-seat-open-axis-preflight-v1.json"
_EXPECTED_SHA256 = "1baa4ae297c5054dde63efbaed3b50729f6d56f6cf5778b9c2346ec4ec46214f"


class H32OneSeatOpenAxisResultTests(unittest.TestCase):
    def test_accepted_artifact_is_pinned_to_the_one_round_branch(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "authorize_label_free_h32_one_seat_master_prototype",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "fe26d7e338e22c5e55d2a495d651ffda73ee304c",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])

        target = result["target"]
        self.assertEqual(target["acting_public_nodes"], 16)
        self.assertEqual(target["entries_per_row"], 1024)
        self.assertEqual(target["profile_passes"], 6)
        self.assertEqual(target["fixed_response_passes"], 5)
        self.assertEqual(target["gain_rows"], 6)
        self.assertEqual(target["teacher_rows"], 96)
        self.assertLessEqual(target["maximum_profile_slope_error"], 2e-11)
        self.assertLessEqual(target["maximum_response_slope_error"], 2e-11)
        self.assertLessEqual(target["maximum_gain_slope_error"], 2e-11)
        self.assertEqual(len(set(target["gain_row_sha256"])), 6)
        self.assertEqual(len(set(target["exact_response_signatures"])), 5)

        capacity = target["capacity_before_teacher"]
        self.assertEqual(capacity["conservative_complete_cut_rounds"], 1)
        self.assertLessEqual(capacity["one_round_complete_ledger_ms"], 15000.0)
        self.assertTrue(
            capacity[
                "final_certificate_is_reserved_separately_from_every_cut_oracle"
            ]
        )
        self.assertEqual(target["quality_values_serialized"], 0)
        self.assertEqual(target["certificates_executed"], 0)
        self.assertEqual(target["strategy_labels_generated"], 0)
        self.assertIsNone(result["strategy_quality_claim"])


if __name__ == "__main__":
    unittest.main()
