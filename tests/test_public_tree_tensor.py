from __future__ import annotations

import hashlib
import unittest

from pontius.evaluation import (
    Policy,
    best_response,
    collect_information_sets,
    evaluate_profile,
)
from pontius.multiway_river_context import generate_multiway_river_contexts
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem


def _disjoint_game(players: int, hands_per_player: int) -> MultiwayRiverHoldem:
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


def _hashed_policy(
    game: MultiwayRiverHoldem,
    *,
    pure: bool,
) -> Policy:
    policy: Policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            if pure:
                selected = digest[0] % len(actions)
                policy[key] = {
                    action: float(index == selected)
                    for index, action in enumerate(actions)
                }
            else:
                policy[key] = {
                    action: float(1 + digest[index] % 19)
                    for index, action in enumerate(actions)
                }
    return policy


def _evaluation_values(result: object) -> tuple[float, ...]:
    return (
        *result.utilities,  # type: ignore[attr-defined]
        *result.best_response_values,  # type: ignore[attr-defined]
        *result.deviation_gains,  # type: ignore[attr-defined]
        result.nash_conv,  # type: ignore[attr-defined]
    )


class PublicTreeTensorTests(unittest.TestCase):
    def assert_matches(self, game: MultiwayRiverHoldem, policy: Policy) -> None:
        evaluator = PublicTreeTensorEvaluator(game)
        tensor = evaluator.evaluate(policy)
        ordinary = evaluate_profile(game, policy)
        self.assertLessEqual(
            max(
                abs(left - right)
                for left, right in zip(
                    _evaluation_values(tensor.evaluation),
                    _evaluation_values(ordinary),
                    strict=True,
                )
            ),
            1e-10,
        )
        expected_actions = tuple(
            best_response(game, policy, player)[1]
            for player in range(game.num_players)
        )
        self.assertEqual(tensor.best_response_actions, expected_actions)

    def test_uniform_dense_and_zero_reach_policies_match_exactly(self) -> None:
        game = _disjoint_game(3, 2)
        self.assert_matches(game, {})
        self.assert_matches(game, _hashed_policy(game, pure=False))
        self.assert_matches(game, _hashed_policy(game, pure=True))

    def test_two_through_six_players_match(self) -> None:
        for players in range(2, 7):
            with self.subTest(players=players):
                game = _disjoint_game(players, 1)
                self.assert_matches(game, _hashed_policy(game, pure=True))

    def test_blocker_and_correlated_supports_match(self) -> None:
        contexts = generate_multiway_river_contexts(
            groups=1,
            seed=20260819,
            hands_per_player=3,
            families=("blocker_stress", "correlated"),
            splits=("development",),
            pot_options=(12.0,),
            bet_to_pot_options=(0.25,),
            effective_stack_to_pot=2.5,
            weight_options=(1.0, 2.0, 4.0),
        )
        self.assertEqual(len(contexts), 2)
        for context in contexts:
            with self.subTest(family=context.family):
                self.assert_matches(
                    context.game,
                    _hashed_policy(context.game, pure=False),
                )

    def test_schema_topology_layout_and_memory_are_explicit(self) -> None:
        game = _disjoint_game(3, 2)
        evaluator = PublicTreeTensorEvaluator(game)
        expected_schema = {}
        for player in range(game.num_players):
            expected_schema.update(collect_information_sets(game, player))

        self.assertEqual(evaluator.information_schema(), dict(sorted(expected_schema.items())))
        self.assertEqual(evaluator.topology_mismatch_count(), 0)
        self.assertTrue(evaluator.numeric_tensors_are_float64_contiguous())
        self.assertTrue(evaluator.policy_tensors_are_float64_contiguous({}))
        topology = evaluator.topology_summary()
        self.assertEqual(topology["public_nodes"], 25)
        self.assertEqual(topology["terminal_public_nodes"], 13)
        self.assertTrue(topology["children_are_topological"])
        memory = evaluator.memory_summary()
        self.assertGreater(memory["persistent_numeric_bytes"], 0)
        self.assertGreater(memory["estimated_hot_scratch_bytes"], 0)
        self.assertLess(
            memory["public_topology_bytes"],
            memory["terminal_value_bytes"],
        )

    def test_invalid_policy_is_rejected_by_the_shared_validator(self) -> None:
        game = _disjoint_game(3, 1)
        evaluator = PublicTreeTensorEvaluator(game)
        key, actions = next(iter(evaluator.information_schema().items()))
        with self.assertRaisesRegex(ValueError, "negative probability"):
            evaluator.evaluate(
                {key: {actions[0]: -1.0, actions[1]: 2.0}}
            )


if __name__ == "__main__":
    unittest.main()
