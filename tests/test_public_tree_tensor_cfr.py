from __future__ import annotations

import hashlib
import unittest

from pontius.cfr import TabularCFR
from pontius.evaluation import Policy
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.public_tree_tensor_cfr import PublicTreeTensorCFR
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem


def _disjoint_game(players: int = 3, hands_per_player: int = 2) -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for player in range(players):
        weights = {}
        for hand_index in range(hands_per_player):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(1 + player + hand_index)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=12.0,
        stacks=(30.0,) * players,
        bet_size=3.0,
        player_weights=tuple(ranges),
    )


def _dense_policy(schema: dict[str, tuple[str, ...]]) -> Policy:
    policy: Policy = {}
    for key, actions in schema.items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 17) for index in range(len(actions)))
        total = sum(weights)
        policy[key] = {
            action: weights[index] / total
            for index, action in enumerate(actions)
        }
    return policy


class PublicTreeTensorCFRTests(unittest.TestCase):
    def assert_policy_close(self, first: Policy, second: Policy, tolerance: float) -> None:
        self.assertEqual(first.keys(), second.keys())
        for key in first:
            self.assertEqual(first[key].keys(), second[key].keys())
            for action in first[key]:
                self.assertLessEqual(
                    abs(first[key][action] - second[key][action]),
                    tolerance,
                    msg=f"policy mismatch at {key!r}/{action!r}",
                )

    def assert_table_close(
        self,
        first: dict[str, dict[str, float]],
        second: dict[str, dict[str, float]],
        tolerance: float,
    ) -> None:
        self.assertEqual(first.keys(), second.keys())
        for key in first:
            self.assertEqual(first[key].keys(), second[key].keys())
            for action in first[key]:
                self.assertLessEqual(
                    abs(first[key][action] - second[key][action]),
                    tolerance,
                    msg=f"accumulator mismatch at {key!r}/{action!r}",
                )

    def test_warm_alternating_trajectory_matches_tabular_for_every_rule(self) -> None:
        game = _disjoint_game()
        layout = PublicTreeTensorEvaluator(game)
        schema = layout.information_schema()
        warm_policy = _dense_policy(schema)
        for variant in ("cfr", "lcfr", "cfr_plus", "dcfr"):
            with self.subTest(variant=variant):
                ordinary = TabularCFR(game, variant)
                ordinary.warm_start_from_schema(warm_policy, 3.25, schema)
                tensor = PublicTreeTensorCFR(layout, variant)
                tensor.warm_start(warm_policy, 3.25)
                for _ in range(3):
                    ordinary.step()
                    tensor.step()
                    expected_regrets = {
                        key: dict(data.regrets)
                        for key, data in sorted(ordinary.information_sets.items())
                    }
                    expected_sums = {
                        key: dict(data.strategy_sum)
                        for key, data in sorted(ordinary.information_sets.items())
                    }
                    self.assertEqual(tensor.iteration, ordinary.iteration)
                    self.assert_policy_close(
                        tensor.current_strategy(), ordinary.current_strategy(), 2e-12
                    )
                    self.assert_policy_close(
                        tensor.average_strategy(), ordinary.average_strategy(), 2e-12
                    )
                    self.assert_table_close(
                        tensor.regret_table(), expected_regrets, 2e-11
                    )
                    self.assert_table_close(
                        tensor.strategy_sum_table(), expected_sums, 2e-12
                    )

    def test_cold_start_and_callback_match_tabular(self) -> None:
        game = _disjoint_game(players=2)
        layout = PublicTreeTensorEvaluator(game)
        ordinary = TabularCFR(game, "dcfr")
        tensor = PublicTreeTensorCFR(layout, "dcfr")
        seen: list[int] = []
        ordinary.run(2)
        tensor.run(2, lambda solver: seen.append(solver.iteration))
        self.assertEqual(seen, [1, 2])
        self.assert_policy_close(
            tensor.current_strategy(), ordinary.current_strategy(), 2e-12
        )
        self.assert_policy_close(
            tensor.average_strategy(), ordinary.average_strategy(), 2e-12
        )

    def test_six_player_iteration_matches_tabular(self) -> None:
        game = _disjoint_game(players=6, hands_per_player=2)
        layout = PublicTreeTensorEvaluator(game)
        schema = layout.information_schema()
        warm_policy = _dense_policy(schema)
        ordinary = TabularCFR(game, "dcfr")
        ordinary.warm_start_from_schema(warm_policy, 1.0, schema)
        tensor = PublicTreeTensorCFR(layout, "dcfr")
        tensor.warm_start(warm_policy, 1.0)
        ordinary.step()
        tensor.step()
        self.assert_policy_close(
            tensor.current_strategy(), ordinary.current_strategy(), 3e-12
        )
        self.assert_policy_close(
            tensor.average_strategy(), ordinary.average_strategy(), 3e-12
        )
        self.assert_table_close(
            tensor.regret_table(),
            {
                key: dict(data.regrets)
                for key, data in sorted(ordinary.information_sets.items())
            },
            3e-11,
        )

    def test_state_validation_and_memory_are_explicit(self) -> None:
        layout = PublicTreeTensorEvaluator(_disjoint_game())
        solver = PublicTreeTensorCFR(layout, "dcfr")
        with self.assertRaisesRegex(ValueError, "positive"):
            solver.warm_start({}, 0.0)
        solver.warm_start({}, 1.0)
        with self.assertRaisesRegex(ValueError, "before"):
            solver.warm_start({}, 1.0)
        with self.assertRaisesRegex(ValueError, "negative"):
            solver.run(-1)
        memory = solver.memory_summary()
        self.assertGreater(memory["persistent_accumulator_bytes"], 0)
        self.assertGreater(memory["estimated_peak_step_scratch_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
