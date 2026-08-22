from collections import Counter
import unittest

from pontius.h32_action_conditioned_posterior_manifest import _TARGET_PLAN as OPENED
from pontius.h32_heldout_continuation_posterior_manifest import _TARGET_PLAN


class HeldoutContinuationPosteriorManifestTests(unittest.TestCase):
    def test_latin_cd_plan_is_balanced_and_disjoint(self) -> None:
        self.assertEqual(len(_TARGET_PLAN), 12)
        self.assertEqual(
            Counter(row["source"] for row in _TARGET_PLAN),
            Counter({row["source"]: 2 for row in _TARGET_PLAN}),
        )
        self.assertEqual(
            Counter(row["observed_bettor"] for row in _TARGET_PLAN),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertFalse(
            {row["target_id"] for row in _TARGET_PLAN}
            & {row["target_id"] for row in OPENED}
        )
        self.assertEqual({row["round"] for row in _TARGET_PLAN}, {"latin_c", "latin_d"})


if __name__ == "__main__":
    unittest.main()
