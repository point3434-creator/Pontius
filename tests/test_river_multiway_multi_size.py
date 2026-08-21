from __future__ import annotations

import hashlib
import unittest

from pontius.evaluation import Policy, collect_information_sets, evaluate_profile
from pontius.game import CHANCE_PLAYER
from pontius.multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from pontius.public_tree_tensor_cfr import PublicTreeTensorCFR
from pontius.river import CALL, CHECK, FOLD, make_hole, parse_cards
from pontius.river_multiway import MultiwayRiverDeal
from pontius.river_multiway_multi_size import MultiwayMultiSizeRiverHoldem


BOARD = parse_cards("2c", "7d", "9h", "Js", "Qc")
HANDS = (
    make_hole("As", "Ad"),
    make_hole("Ks", "Kd"),
    make_hole("Ts", "Td"),
    make_hole("8s", "8d"),
    make_hole("6s", "6d"),
    make_hole("4s", "4d"),
)


def _game(players: int = 3) -> MultiwayMultiSizeRiverHoldem:
    deal = MultiwayRiverDeal(HANDS[:players])
    return MultiwayMultiSizeRiverHoldem.from_joint_weights(
        board=BOARD,
        pot=12.0,
        stacks=(30.0,) * players,
        bet_sizes=(3.0, 6.0),
        joint_weights={deal: 1.0},
    )


def _hashed_policy(game: MultiwayMultiSizeRiverHoldem) -> Policy:
    result: Policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            weights = tuple(float(1 + digest[index] % 17) for index in range(len(actions)))
            total = sum(weights)
            result[key] = {
                action: weights[index] / total
                for index, action in enumerate(actions)
            }
    return result


class MultiwayMultiSizeRiverTests(unittest.TestCase):
    def test_sized_bets_preserve_cyclic_response_and_exact_payoffs(self) -> None:
        game = _game(3)
        deal = next(iter(game.joint_distribution()))
        state = game.initial_state()
        self.assertEqual(state.current_player, CHANCE_PLAYER)
        state = state.apply_action(deal)
        small, large = game.bet_actions
        self.assertEqual(state.legal_actions(), (CHECK, small, large))

        all_check = state.apply_action(CHECK).apply_action(CHECK).apply_action(CHECK)
        self.assertEqual(all_check.returns(), (8.0, -4.0, -4.0))

        all_fold = state.apply_action(large).apply_action(FOLD).apply_action(FOLD)
        self.assertEqual(all_fold.returns(), (8.0, -4.0, -4.0))

        called = state.apply_action(small).apply_action(CALL).apply_action(FOLD)
        self.assertEqual(called.returns(), (11.0, -7.0, -4.0))
        self.assertAlmostEqual(sum(called.returns()), 0.0, places=12)

        late = state.apply_action(CHECK).apply_action(large)
        self.assertEqual(late.current_player, 2)
        late = late.apply_action(FOLD)
        self.assertEqual(late.current_player, 0)

    def test_information_identity_remembers_exact_size_but_not_range(self) -> None:
        game = _game(3)
        deal = next(iter(game.joint_distribution()))
        root = game.initial_state().apply_action(deal)
        small, large = game.bet_actions
        small_key = root.apply_action(small).information_state_key(1)
        large_key = root.apply_action(large).information_state_key(1)
        self.assertNotEqual(small_key, large_key)
        self.assertIn(str(small), small_key)
        self.assertIn(str(large), large_key)

        same = game.with_joint_weights({deal: 2.0})
        self.assertEqual(game.structural_digest, same.structural_digest)
        self.assertEqual(
            root.information_state_key(0),
            same.initial_state().apply_action(deal).information_state_key(0),
        )

    def test_tensor_evaluator_matches_generic_profile_and_has_expected_tree(self) -> None:
        game = _game(3)
        policy = _hashed_policy(game)
        layout = MultiSizePublicTreeTensorEvaluator(game)
        tensor = layout.evaluate(policy).evaluation
        generic = evaluate_profile(game, policy)
        for left, right in zip(
            (
                *tensor.utilities,
                *tensor.best_response_values,
                *tensor.deviation_gains,
                tensor.nash_conv,
            ),
            (
                *generic.utilities,
                *generic.best_response_values,
                *generic.deviation_gains,
                generic.nash_conv,
            ),
            strict=True,
        ):
            self.assertAlmostEqual(left, right, places=11)
        self.assertEqual(layout.topology_mismatch_count(), 0)
        self.assertEqual(layout.public_node_count, 46)
        self.assertEqual(layout.terminal_node_count, 25)
        self.assertEqual(layout.unique_terminal_descriptor_count, 15)
        self.assertIsInstance(PublicTreeTensorCFR(layout, "dcfr"), PublicTreeTensorCFR)

    def test_six_seat_two_size_geometry_is_exact(self) -> None:
        layout = MultiSizePublicTreeTensorEvaluator(_game(6))
        self.assertEqual(layout.public_node_count, 763)
        self.assertEqual(layout.strategic_node_count, 378)
        self.assertEqual(layout.terminal_node_count, 385)
        self.assertEqual(layout.unique_terminal_descriptor_count, 127)
        self.assertEqual(len(layout.information_schema()), 378)
        self.assertTrue(layout.topology_summary()["children_are_topological"])

    def test_invalid_sizes_and_stacks_are_rejected(self) -> None:
        deal = MultiwayRiverDeal(HANDS[:3])
        common = {
            "board": BOARD,
            "pot": 12.0,
            "stacks": (30.0,) * 3,
            "joint_weights": {deal: 1.0},
        }
        with self.assertRaisesRegex(ValueError, "at least one"):
            MultiwayMultiSizeRiverHoldem.from_joint_weights(
                **common,
                bet_sizes=(),
            )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            MultiwayMultiSizeRiverHoldem.from_joint_weights(
                **common,
                bet_sizes=(6.0, 3.0),
            )
        with self.assertRaisesRegex(ValueError, "fit every"):
            MultiwayMultiSizeRiverHoldem.from_joint_weights(
                **{**common, "stacks": (5.0, 30.0, 30.0)},
                bet_sizes=(3.0, 6.0),
            )


if __name__ == "__main__":
    unittest.main()
