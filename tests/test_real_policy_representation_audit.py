from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.real_policy_representation_audit import (
    _interpolate_seat,
    parse_real_policy_representation_config,
    _splice_seat,
    _structured_terminal_library,
)
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem
from pontius.showdown_value_rank_screen import _policies


def _game() -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for player in range(3):
        weights = {}
        for hand_index in range(2):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(1 + player + hand_index)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=12.0,
        stacks=(30.0,) * 3,
        bet_size=3.0,
        player_weights=tuple(ranges),
    )


class RealPolicyRepresentationAuditTests(unittest.TestCase):
    def test_frozen_config_parses_without_a_small_axis_speed_gate(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "real-policy-representation-audit-v1.json"
        )
        parsed = parse_real_policy_representation_config(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.assertEqual(parsed["rank_target_players"], (0, 3, 5))
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 512)
        self.assertNotIn("minimum_speedup", parsed["gates"])

    def test_seat_splice_and_interpolation_do_not_touch_other_seats(self) -> None:
        layout = PublicTreeTensorEvaluator(_game())
        policies = _policies(layout.information_schema(), 91)
        baseline = policies["hashed_dense"]
        donor = policies["hashed_pure"]
        spliced = _splice_seat(layout, baseline, donor, 1)
        interpolated = _interpolate_seat(layout, baseline, donor, 1, 0.25)
        for key in baseline:
            if "|p1|" in key:
                self.assertEqual(spliced[key], donor[key])
                for action in baseline[key]:
                    self.assertAlmostEqual(
                        interpolated[key][action],
                        0.75 * baseline[key][action] + 0.25 * donor[key][action],
                    )
                self.assertAlmostEqual(sum(interpolated[key].values()), 1.0)
            else:
                self.assertEqual(spliced[key], baseline[key])
                self.assertEqual(interpolated[key], baseline[key])

    def test_structured_terminal_library_matches_literal_dense_values(self) -> None:
        game = _game()
        layout = PublicTreeTensorEvaluator(game)
        dense, trains, bounds, summary = _structured_terminal_library(
            layout=layout,
            axes=layout.hands_by_player,
            board=game.board,
            player=1,
            pot=game.pot,
            bet_size=game.bet_size,
        )
        self.assertEqual(len(dense), 8)
        self.assertEqual(set(dense), set(trains))
        self.assertTrue(all(value == 0.0 for value in bounds.values()))
        self.assertLessEqual(summary["maximum_terminal_error"], 1e-12)
        for key in dense:
            self.assertLessEqual(
                abs(trains[key].to_dense() - dense[key]).max(), 1e-12
            )


if __name__ == "__main__":
    unittest.main()
