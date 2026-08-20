from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.real_policy import policy_digest
from pontius.real_policy_source import (
    parse_real_policy_source_config,
    solve_policy_geometry,
)
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem


def _game() -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for player in range(2):
        weights = {}
        for hand_index in range(2):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(1 + player + hand_index)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=12.0,
        stacks=(30.0, 30.0),
        bet_size=3.0,
        player_weights=tuple(ranges),
    )


class RealPolicySourceTests(unittest.TestCase):
    def test_frozen_config_parses_and_has_no_quality_gate(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "real-policy-source-v1.json"
        )
        parsed = parse_real_policy_source_config(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.assertEqual(parsed["checkpoint_ladders"][4], (0, 1, 4, 16, 64, 256))
        self.assertEqual(parsed["checkpoint_ladders"][7], (0, 1, 4, 16, 64))
        self.assertNotIn("maximum_nash_conv", parsed["gates"])

    def test_small_geometry_serializes_checkpoints_and_every_response(self) -> None:
        result = solve_policy_geometry(
            PublicTreeTensorEvaluator(_game()),
            geometry_id="test",
            checkpoints=(0, 1, 3),
            regret_mass=1.0,
            response_checkpoint=1,
            response_targets=(0, 1),
        )
        profiles = result["profiles"]
        self.assertEqual(len(profiles), 5)
        self.assertEqual(result["maximum_rederivation_policy_error"], 0.0)
        self.assertEqual(result["rederivation_digest_mismatches"], 0)
        self.assertLessEqual(result["maximum_best_response_target_value_error"], 1e-12)
        self.assertEqual(result["policy_schema_mismatches"], 0)
        self.assertEqual(len(result["consecutive_checkpoint_tv"]), 2)
        for profile in profiles:
            self.assertEqual(profile["policy_sha256"], policy_digest(profile["policy"]))

    def test_checkpoint_contract_is_strict(self) -> None:
        layout = PublicTreeTensorEvaluator(_game())
        with self.assertRaisesRegex(ValueError, "start at zero"):
            solve_policy_geometry(
                layout,
                geometry_id="bad",
                checkpoints=(1,),
                regret_mass=1.0,
                response_checkpoint=1,
                response_targets=(0,),
            )
        with self.assertRaisesRegex(ValueError, "present"):
            solve_policy_geometry(
                layout,
                geometry_id="bad",
                checkpoints=(0, 1),
                regret_mass=1.0,
                response_checkpoint=2,
                response_targets=(0,),
            )


if __name__ == "__main__":
    unittest.main()
