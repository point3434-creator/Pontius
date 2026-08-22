from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h32-convex-replication-posterior-manifest-v1.json"
_EXPECTED_SHA256 = "502dce7e14fe4996e01697a7aa8839853c599fe700338eb39cb4bd04e06a49ba"


class H32ConvexReplicationPosteriorManifestResultTests(unittest.TestCase):
    def test_accepted_manifest_is_fresh_balanced_and_label_free(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "authorize_preregistered_fresh_convex_retreat_replication",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "a881bd5f2a4978771a1bd9892c15f104bffbea18",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])

        rows = result["target_rows"]
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            Counter(row["source"] for row in rows),
            Counter({row["source"]: 2 for row in rows}),
        )
        self.assertEqual(
            Counter(row["observed_bettor"] for row in rows),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertEqual(
            Counter(row["acting_player"] for row in rows),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertTrue(
            all(
                row["acting_player"] == (row["observed_bettor"] - 1) % 6
                for row in rows
            )
        )
        self.assertTrue(all(row["target_id_fresh_at_base_commit"] for row in rows))
        self.assertTrue(
            all(row["target_digest_fresh_at_base_commit"] for row in rows)
        )
        self.assertTrue(
            all(row["convex_acting_player_marginal_total_variation"] > 0.0 for row in rows)
        )
        self.assertEqual(result["aggregate"]["complete_source_bettor_combinations"], 36)
        self.assertEqual(result["methodology"]["new_warm_steps"], 0)
        self.assertEqual(result["methodology"]["convex_candidates"], 0)
        self.assertEqual(result["methodology"]["quality_evaluations"], 0)
        self.assertEqual(result["methodology"]["strategy_labels"], 0)
        self.assertIsNone(result["strategy_population_claim"])


if __name__ == "__main__":
    unittest.main()
