from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_candidate_availability_replay import (
    parse_h32_candidate_availability_config,
)
from pontius.h32_candidate_availability_replay_v2 import (
    _stage_count_sentinel,
    parse_h32_candidate_availability_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v2.json"
_V1 = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v1.json"


class H32CandidateAvailabilityReplayV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.v1 = parse_h32_candidate_availability_config(
            json.loads(_V1.read_text(encoding="utf-8"))
        )

    def test_correction_is_only_frozen_stage_count_sentinel(self) -> None:
        parsed = parse_h32_candidate_availability_v2_config(self.config)
        self.assertEqual(
            parsed["correction"],
            "supply_stage_count_sentinel_from_frozen_availability_only",
        )
        sentinel = _stage_count_sentinel(self.v1)
        self.assertEqual(
            tuple(len(row["available_candidate_ids"]) for row in sentinel["stage_rows"]),
            (2, 4, 9, 11, 13),
        )

    def test_correction_rejects_any_config_change(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["correction"] = "edit_v1"
        with self.assertRaisesRegex(ValueError, "correction config"):
            parse_h32_candidate_availability_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
