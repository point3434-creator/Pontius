"""Behavioral checks for the bounded early-street game and frozen leaves."""

from itertools import combinations, permutations
import random
import unittest

from pontius.early_holdem import EarlyHoldemGame, canonical_flop, preflop_class
from pontius.game import TERMINAL_PLAYER
from pontius.holdem_cards import SixSeatHoldemDeal
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from pontius.river import make_hole, parse_cards


def flop_betting(stacks=(40,) * 6):
    betting = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=stacks,
        small_blind=1,
        big_blind=2,
    )
    while not betting.round_complete:
        betting = betting.apply_action(CHECK if betting.legal_decision().can_check else CALL)
    return betting.advance_street()


def deal_with_visible(hole, board, seed=0, actor=1):
    remaining = [card for card in range(52) if card not in (*hole, *board)]
    random.Random(seed).shuffle(remaining)
    hands = []
    for seat in range(6):
        hands.append(hole if seat == actor else tuple(remaining.pop() for _ in range(2)))
    runout = (*board, *(remaining.pop() for _ in range(5 - len(board))))
    return SixSeatHoldemDeal(tuple(hands), runout)


class EarlyHoldemTests(unittest.TestCase):
    def test_preflop_partition_has_exactly_169_classes(self):
        classes = {preflop_class(hand) for hand in combinations(range(52), 2)}
        self.assertEqual(len(classes), 169)
        self.assertEqual(preflop_class(make_hole("As", "Ah")), "AA")
        self.assertEqual(preflop_class(make_hole("As", "Ks")), "AKs")
        self.assertEqual(preflop_class(make_hole("As", "Kh")), "AKo")

    def test_flop_key_is_invariant_under_all_suit_permutations(self):
        game = EarlyHoldemGame()
        betting = flop_betting()
        deal = deal_with_visible(make_hole("As", "Ks"), parse_cards("Qs", "Jh", "2c"))
        expected = game.state_for(deal, betting).information_state_key(1)
        for permutation in permutations(range(4)):

            def mapped(card):
                return 4 * (card // 4) + permutation[card % 4]

            changed = SixSeatHoldemDeal(
                tuple(tuple(mapped(card) for card in hand) for hand in deal.private_hands),
                tuple(mapped(card) for card in deal.board_runout),
            )
            self.assertEqual(game.state_for(changed, betting).information_state_key(1), expected)
        self.assertNotEqual(
            canonical_flop(make_hole("As", "Ks"), parse_cards("Qs", "Jh", "2c")),
            canonical_flop(make_hole("As", "Kh"), parse_cards("Qs", "Jh", "2c")),
        )

    def test_unseen_hands_and_future_cards_do_not_change_early_policy_inputs(self):
        game = EarlyHoldemGame()
        for betting in (flop_betting(), game.sample_root(random.Random(0)).betting):
            actor = betting.acting_seat
            board = parse_cards("Qs", "Jh", "2c") if betting.street == BettingStreet.FLOP else ()
            states = [
                game.state_for(
                    deal_with_visible(make_hole("As", "Ks"), board, seed, actor), betting
                )
                for seed in range(10)
            ]
            self.assertEqual(len({state.information_state_key(actor) for state in states}), 1)
            self.assertEqual(len({state.legal_actions() for state in states}), 1)

    def test_public_history_stacks_position_and_configuration_distinguish_keys(self):
        game = EarlyHoldemGame()
        deal = deal_with_visible(make_hole("As", "Ks"), parse_cards("Qs", "Jh", "2c"))
        small = flop_betting()
        big = flop_betting((200,) * 6)
        self.assertNotEqual(
            game.state_for(deal, small).information_state_key(1),
            game.state_for(deal, big).information_state_key(1),
        )
        root = game.sample_root(random.Random(4))
        called = root.apply_action("call")
        self.assertNotEqual(
            root.information_state_key(root.current_player),
            called.information_state_key(called.current_player),
        )
        self.assertNotEqual(game.game_id, EarlyHoldemGame(continuation="showdown_betting").game_id)
        self.assertEqual(game.game_id, EarlyHoldemGame().game_id)

    def test_random_hands_have_legal_menus_and_conserve_chips_without_late_nodes(self):
        rng = random.Random(919)
        for continuation in ("check_call", "showdown_betting"):
            for stack in (20, 100, 200):
                game = EarlyHoldemGame(stack_bb=stack, continuation=continuation)
                for _ in range(15):
                    state = game.sample_root(rng)
                    self.assertEqual(
                        len(
                            set(
                                (
                                    *state.deal.board_runout,
                                    *(card for hand in state.deal.private_hands for card in hand),
                                )
                            )
                        ),
                        17,
                    )
                    nodes = 0
                    while state.current_player != TERMINAL_PLAYER:
                        self.assertIn(
                            state.betting.street, (BettingStreet.PREFLOP, BettingStreet.FLOP)
                        )
                        actions = state.legal_actions()
                        self.assertTrue(actions)
                        self.assertEqual(len(actions), len(set(actions)))
                        for action in actions:
                            self.assertIsInstance(action, str)
                            state.apply_action(action)  # Exact kernel rejects illegal actions.
                        state = state.apply_action(rng.choice(actions))
                        nodes += 1
                        self.assertLess(nodes, 50)
                    self.assertEqual(len(state.returns()), 6)
                    self.assertAlmostEqual(sum(state.returns()), 0.0)
                    self.assertTrue(all(-stack <= value <= 5 * stack for value in state.returns()))
                    self.assertEqual(state.legal_actions(), ())

    def test_short_all_in_is_available_and_raise_cap_is_enforced(self):
        game = EarlyHoldemGame(max_raises=1)
        root = game.sample_root(random.Random(2))
        betting = NoLimitBettingState.new_hand(
            button=0, starting_stacks=(40, 40, 40, 3, 40, 40), small_blind=1, big_blind=2
        )
        state = game.state_for(root.deal, betting)
        self.assertIn("raise-to-3", state.legal_actions())
        after = state.apply_action("raise-to-3")
        self.assertFalse(any(action.startswith("raise") for action in after.legal_actions()))
        with self.assertRaises(ValueError):
            after.apply_action("raise-to-6")
        with self.assertRaises(ValueError):
            state.returns()

    def test_non_checkdown_leaf_changes_terminal_payoffs(self):
        hole = make_hole("As", "Ah")
        deal = deal_with_visible(hole, parse_cards("Ac", "7s", "2h", "Kd", "3c"))
        betting = flop_betting()
        while not betting.round_complete:
            betting = betting.apply_action(CHECK)
        passive = EarlyHoldemGame().state_for(deal, betting)
        betting_leaf = EarlyHoldemGame(continuation="showdown_betting").state_for(deal, betting)
        self.assertEqual(passive.current_player, TERMINAL_PLAYER)
        self.assertEqual(betting_leaf.current_player, TERMINAL_PLAYER)
        self.assertNotEqual(passive.returns(), betting_leaf.returns())
        self.assertTrue(
            any(record.action.raise_to is not None for record in betting_leaf.betting.history)
        )

    def test_identical_current_ledgers_preserve_different_preflop_histories(self):
        game = EarlyHoldemGame()
        root = game.sample_root(random.Random(7))
        early_raise = root.betting.apply_action(raise_to(5))
        late_raise = root.betting.apply_action(CALL).apply_action(raise_to(5))
        flops = []
        for betting in (early_raise, late_raise):
            while not betting.round_complete:
                betting = betting.apply_action(
                    CHECK if betting.legal_decision().can_check else CALL
                )
            flops.append(game.state_for(root.deal, betting))
        self.assertEqual(flops[0].betting.stacks, flops[1].betting.stacks)
        self.assertEqual(flops[0].betting.pot, flops[1].betting.pot)
        self.assertEqual(flops[0].current_player, flops[1].current_player)
        self.assertNotEqual(flops[0].information_state_key(1), flops[1].information_state_key(1))

    def test_turn_continuation_never_observes_the_future_river(self):
        game = EarlyHoldemGame(continuation="showdown_betting")
        deal = deal_with_visible(make_hole("As", "Ah"), parse_cards("Ac", "7s", "2h", "Kd", "3c"))
        used = {*deal.board_runout, *(card for hand in deal.private_hands for card in hand)}
        alternatives = [card for card in range(52) if card not in used][:6]
        betting = flop_betting()
        while not betting.round_complete:
            betting = betting.apply_action(CHECK)
        turn_histories = []
        for river in (deal.board_runout[-1], *alternatives):
            changed = SixSeatHoldemDeal(deal.private_hands, (*deal.board_runout[:4], river))
            leaf = game.state_for(changed, betting)
            turn_histories.append(
                tuple(
                    record for record in leaf.betting.history if record.street == BettingStreet.TURN
                )
            )
        self.assertTrue(turn_histories[0])
        self.assertEqual(len(set(turn_histories)), 1)

    def test_board_royal_flush_splits_the_six_way_pot_exactly(self):
        deal = deal_with_visible(make_hole("2s", "2h"), parse_cards("Ac", "Kc", "Qc", "Jc", "Tc"))
        game = EarlyHoldemGame()
        state = game.state_for(deal, flop_betting())
        while state.current_player != TERMINAL_PLAYER:
            state = state.apply_action("check")
        self.assertEqual(state.returns(), (0.0,) * 6)

    def test_sampler_reproducibility_and_configuration_validation(self):
        game = EarlyHoldemGame()
        self.assertEqual(game.sample_root(random.Random(4)), game.sample_root(random.Random(4)))
        for kwargs in (
            {"stack_bb": 0},
            {"stack_bb": True},
            {"stack_bb": 20.5},
            {"max_raises": -1},
            {"max_raises": True},
            {"continuation": "solved"},
        ):
            with self.assertRaises(ValueError):
                EarlyHoldemGame(**kwargs)


if __name__ == "__main__":
    unittest.main()
