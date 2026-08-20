from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.signed_clean_fringe_audit import parse_signed_clean_fringe_config


class SignedCleanFringeAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "signed-clean-fringe-audit-v1.json"
        )
        cls.config = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_frozen_config_and_target_customer_parse_exactly(self) -> None:
        parsed = parse_signed_clean_fringe_config(self.config)
        self.assertEqual(parsed["hands_per_player"], (4, 7))
        self.assertEqual(
            parsed["target_checkpoint_transitions"],
            ((4, 16), (16, 64)),
        )
        self.assertEqual(parsed["expected_candidate_rows"], 134)
        self.assertEqual(parsed["expected_target_customer_rows"], 24)

    def test_stage_hash_target_and_speed_gate_mutations_fail(self) -> None:
        mutations = []
        stage = deepcopy(self.config)
        stage["evidence_stage"] = "revealed"
        mutations.append(stage)
        source = deepcopy(self.config)
        source["expected_signed_clean_fringe_tt_sha256"] = "0" * 64
        mutations.append(source)
        target = deepcopy(self.config)
        target["target_checkpoint_transitions"] = [[1, 4], [4, 16]]
        mutations.append(target)
        speed = deepcopy(self.config)
        speed["gates"][
            "minimum_target_recompose_to_signed_optimized_certified_speedup"
        ] = 1.0
        mutations.append(speed)
        extra = deepcopy(self.config)
        extra["post_freeze_selector"] = "best_observed_arm"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_signed_clean_fringe_config(mutation)


if __name__ == "__main__":
    unittest.main()
