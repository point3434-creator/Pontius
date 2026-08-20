from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_candidate_availability_replay import (
    parse_h32_candidate_availability_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v1.json"


class H32CandidateAvailabilityReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_availability_is_nested_and_step_two_contains_interpolation(self) -> None:
        parsed = parse_h32_candidate_availability_config(self.config)
        self.assertEqual(parsed["stages"], (0, 1, 2, 4, 8))
        self.assertEqual(parsed["availability"]["search_current1"], 1)
        self.assertEqual(parsed["availability"]["interpolate_current1_to2_alpha050"], 2)
        self.assertEqual(parsed["availability"]["search_average8"], 8)
        self.assertEqual(
            tuple(
                sum(iteration <= stage for iteration in parsed["availability"].values())
                for stage in parsed["stages"]
            ),
            (2, 4, 9, 11, 13),
        )

    def test_config_rejects_cost_gate_and_source_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["availability"]["interpolate_current1_to2_alpha050"] = 1
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_h32_candidate_availability_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_replay_seconds"] = 10.0
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_h32_candidate_availability_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_fresh_transfer_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_h32_candidate_availability_config(changed)


if __name__ == "__main__":
    unittest.main()
