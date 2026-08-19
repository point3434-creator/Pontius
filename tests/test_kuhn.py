from __future__ import annotations

import unittest

from pontius.game import CHANCE_PLAYER, TERMINAL_PLAYER
from pontius.kuhn import BET, CALL, CHECK, FOLD, KuhnPoker


class KuhnStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = KuhnPoker().initial_state()

    def test_chance_deals_all_six_ordered_hands(self) -> None:
        self.assertEqual(self.root.current_player, CHANCE_PLAYER)
        outcomes = self.root.chance_outcomes()
        self.assertEqual(len(outcomes), 6)
        self.assertAlmostEqual(sum(probability for _, probability in outcomes), 1.0)
        self.assertEqual(len({deal for deal, _ in outcomes}), 6)

    def test_check_check_showdown(self) -> None:
        state = self.root.apply_action((2, 0)).apply_action(CHECK).apply_action(CHECK)
        self.assertEqual(state.current_player, TERMINAL_PLAYER)
        self.assertEqual(state.returns(), (1.0, -1.0))

    def test_bet_call_showdown(self) -> None:
        state = self.root.apply_action((0, 2)).apply_action(BET).apply_action(CALL)
        self.assertEqual(state.returns(), (-2.0, 2.0))

    def test_bet_fold_and_check_bet_fold(self) -> None:
        first_bets = self.root.apply_action((0, 2)).apply_action(BET).apply_action(FOLD)
        second_bets = (
            self.root.apply_action((2, 0))
            .apply_action(CHECK)
            .apply_action(BET)
            .apply_action(FOLD)
        )
        self.assertEqual(first_bets.returns(), (1.0, -1.0))
        self.assertEqual(second_bets.returns(), (-1.0, 1.0))

    def test_information_set_hides_opponent_card(self) -> None:
        left = self.root.apply_action((1, 0))
        right = self.root.apply_action((1, 2))
        self.assertEqual(left.information_state_key(0), right.information_state_key(0))

    def test_illegal_action_is_rejected(self) -> None:
        state = self.root.apply_action((1, 2))
        with self.assertRaises(ValueError):
            state.apply_action(CALL)


if __name__ == "__main__":
    unittest.main()

