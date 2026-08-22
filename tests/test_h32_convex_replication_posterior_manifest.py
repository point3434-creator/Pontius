from __future__ import annotations

from collections import Counter
import unittest

from pontius.h32_action_conditioned_posterior_manifest import _TARGET_PLAN as OPENED
from pontius.h32_convex_replication_posterior_manifest import _TARGET_PLAN
from pontius.h32_heldout_continuation_posterior_manifest import (
    _TARGET_PLAN as HELDOUT,
)


class H32ConvexReplicationPosteriorManifestTests(unittest.TestCase):
    def test_latin_ef_plan_is_balanced_fresh_and_completes_square(self) -> None:
        self.assertEqual(len(_TARGET_PLAN), 12)
        self.assertEqual(
            Counter(row["source"] for row in _TARGET_PLAN),
            Counter({row["source"]: 2 for row in _TARGET_PLAN}),
        )
        self.assertEqual(
            Counter(row["observed_bettor"] for row in _TARGET_PLAN),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertEqual(
            Counter(row["acting_player"] for row in _TARGET_PLAN),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertTrue(
            all(
                row["acting_player"] == (row["observed_bettor"] - 1) % 6
                for row in _TARGET_PLAN
            )
        )
        prior_ids = {row["target_id"] for row in (*OPENED, *HELDOUT)}
        self.assertFalse({row["target_id"] for row in _TARGET_PLAN} & prior_ids)
        self.assertEqual({row["round"] for row in _TARGET_PLAN}, {"latin_e", "latin_f"})

        combinations = {
            (row["source"], row["observed_bettor"])
            for row in (*OPENED, *HELDOUT, *_TARGET_PLAN)
        }
        self.assertEqual(len(combinations), 36)

    def test_every_new_target_id_is_absent_from_frozen_prior_plans(self) -> None:
        prior_ids = {row["target_id"] for row in (*OPENED, *HELDOUT)}
        for row in _TARGET_PLAN:
            self.assertNotIn(row["target_id"], prior_ids)
            self.assertNotEqual(row["acting_player"], row["observed_bettor"])


if __name__ == "__main__":
    unittest.main()
