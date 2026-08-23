from __future__ import annotations

import random
import unittest
from dataclasses import replace

from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    BettingActionKind,
    BettingActionRecord,
    BettingStreet,
    NoLimitBettingState,
    TerminalReason,
    raise_to,
)


def _passive_round(state: NoLimitBettingState) -> NoLimitBettingState:
    while not state.round_complete:
        decision = state.legal_decision()
        state = state.apply_action(CALL if decision.can_call else CHECK)
    return state


def _runout_with_checks(state: NoLimitBettingState) -> NoLimitBettingState:
    while not state.is_terminal:
        if state.round_complete:
            state = state.advance_street()
        else:
            state = state.apply_action(CHECK)
    return state


class NoLimitBettingActionTests(unittest.TestCase):
    def test_six_max_posts_blinds_and_opens_utg_with_exact_bounds(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        self.assertEqual(state.starting_stacks, (200,) * 6)
        self.assertEqual(state.stacks, (200, 199, 198, 200, 200, 200))
        self.assertEqual(state.street_contributions, (0, 1, 2, 0, 0, 0))
        self.assertEqual(state.pending_seats, (3, 4, 5, 0, 1, 2))
        self.assertEqual(state.pot, 3)

        decision = state.legal_decision()
        self.assertEqual(decision.acting_seat, 3)
        self.assertEqual(decision.to_call, 2)
        self.assertEqual(decision.call_amount, 2)
        self.assertEqual(
            decision.action_kinds,
            (
                BettingActionKind.FOLD,
                BettingActionKind.CALL,
                BettingActionKind.RAISE,
            ),
        )
        assert decision.raise_bounds is not None
        self.assertEqual(decision.raise_bounds.minimum_raise_to, 4)
        self.assertEqual(decision.raise_bounds.maximum_raise_to, 200)
        self.assertEqual(decision.raise_bounds.maximum_contestable_raise_to, 200)

    def test_full_raise_updates_minimum_increment_and_rejects_underraise(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        state = state.apply_action(raise_to(6))
        self.assertEqual(state.last_full_raise_size, 4)
        bounds = state.legal_decision().raise_bounds
        assert bounds is not None
        self.assertEqual(bounds.minimum_raise_to, 10)
        with self.assertRaisesRegex(ValueError, "outside the legal range"):
            state.apply_action(raise_to(9))
        state = state.apply_action(raise_to(10))
        self.assertEqual(state.last_full_raise_size, 4)
        state = state.apply_action(raise_to(20))
        self.assertEqual(state.last_full_raise_size, 10)

    def test_single_short_all_in_does_not_reopen_for_a_prior_caller(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(CALL)  # seat 3 calls 2
        short = state.legal_decision().raise_bounds
        assert short is not None
        self.assertTrue(short.all_in_only)
        self.assertEqual(short.minimum_raise_to, 3)
        state = state.apply_action(raise_to(3))  # seat 4 all-in, +1
        for _ in range(4):
            state = state.apply_action(CALL)
        decision = state.legal_decision()
        self.assertEqual(decision.acting_seat, 3)
        self.assertEqual(decision.to_call, 1)
        self.assertFalse(decision.can_raise)
        self.assertEqual(
            decision.action_kinds,
            (BettingActionKind.FOLD, BettingActionKind.CALL),
        )

    def test_cumulative_short_all_ins_reopen_by_a_full_increment(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(30, 30, 30, 30, 3, 4),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(CALL)  # seat 3 acted at 2
        state = state.apply_action(raise_to(3))  # seat 4 adds one
        state = state.apply_action(raise_to(4))  # seat 5 adds one
        for _ in range(3):
            state = state.apply_action(CALL)
        decision = state.legal_decision()
        self.assertEqual(decision.acting_seat, 3)
        self.assertEqual(decision.current_bet - 2, 2)
        self.assertTrue(decision.can_raise)
        assert decision.raise_bounds is not None
        self.assertEqual(decision.raise_bounds.minimum_raise_to, 6)

    def test_tda_cumulative_short_all_in_example_preserves_seat_specific_rights(self) -> None:
        # Scaled form of Poker TDA Rule 47 Example 1: A opens 100, B is all-in
        # 125, C calls, D is all-in 200, and E calls.  A faces a cumulative full
        # 100 and may raise; after A calls, C faces only 75 and may not.
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(500, 500, 127, 500, 202, 500),
            small_blind=1,
            big_blind=2,
        )
        state = _passive_round(state).advance_street()
        state = state.apply_action(raise_to(100))  # A, seat 1
        state = state.apply_action(raise_to(125))  # B, seat 2, short all-in
        state = state.apply_action(CALL)  # C, seat 3
        state = state.apply_action(raise_to(200))  # D, seat 4, short all-in
        state = state.apply_action(CALL)  # E, seat 5
        state = state.apply_action(FOLD)  # F, seat 0

        a_decision = state.legal_decision()
        self.assertEqual(a_decision.acting_seat, 1)
        self.assertTrue(a_decision.can_raise)
        assert a_decision.raise_bounds is not None
        self.assertEqual(a_decision.raise_bounds.minimum_raise_to, 300)
        state = state.apply_action(CALL)

        c_decision = state.legal_decision()
        self.assertEqual(c_decision.acting_seat, 3)
        self.assertEqual(c_decision.to_call, 75)
        self.assertFalse(c_decision.can_raise)

    def test_unacted_big_blind_may_raise_over_a_short_all_in(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(CALL)
        state = state.apply_action(raise_to(3))
        state = state.apply_action(FOLD)  # seat 5
        state = state.apply_action(FOLD)  # button
        state = state.apply_action(FOLD)  # small blind
        decision = state.legal_decision()
        self.assertEqual(decision.acting_seat, 2)
        self.assertTrue(decision.can_raise)
        assert decision.raise_bounds is not None
        self.assertEqual(decision.raise_bounds.minimum_raise_to, 5)

    def test_no_raise_is_offered_when_no_opponent_can_answer_more(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(2, 2, 2, 2, 2, 100),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(CALL)  # seat 3 all-in
        state = state.apply_action(CALL)  # seat 4 all-in
        decision = state.legal_decision()
        self.assertEqual(decision.acting_seat, 5)
        self.assertFalse(decision.can_raise)
        self.assertEqual(decision.action_kinds, (BettingActionKind.FOLD, BettingActionKind.CALL))

    def test_invalid_semantic_actions_fail_without_mutating_state(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        with self.assertRaisesRegex(ValueError, "check"):
            state.apply_action(CHECK)
        with self.assertRaisesRegex(ValueError, "outside"):
            state.apply_action(raise_to(3))
        with self.assertRaisesRegex(ValueError, "outside"):
            state.apply_action(raise_to(201))
        with self.assertRaisesRegex(TypeError, "BettingAction"):
            state.apply_action("call")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "integer"):
            raise_to(True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "kind"):
            BettingAction("raise", 4)  # type: ignore[arg-type]
        self.assertEqual(state.pot, 3)
        self.assertEqual(state.acting_seat, 3)


class NoLimitBettingPotAndStreetTests(unittest.TestCase):
    def test_uncalled_raise_is_returned_before_fold_settlement(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        state = state.apply_action(raise_to(20))
        for _ in range(5):
            state = state.apply_action(FOLD)
        self.assertEqual(state.terminal_reason, TerminalReason.FOLD)
        self.assertEqual(state.total_contributions, (0, 1, 2, 2, 0, 0))
        self.assertEqual(state.history[-1].uncalled_return_seat, 3)
        self.assertEqual(state.history[-1].uncalled_return_chips, 18)
        settlement = state.settle()
        self.assertEqual(settlement.payouts, (0, 0, 0, 5, 0, 0))
        self.assertEqual(settlement.net_returns, (0, -1, -2, 3, 0, 0))
        self.assertEqual(sum(settlement.final_stacks), 1200)

    def test_four_exact_all_in_layers_are_awarded_independently(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(10, 6, 4, 20, 20, 20),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(raise_to(10))
        for _ in range(5):
            state = state.apply_action(CALL)
        self.assertTrue(state.round_complete)
        self.assertEqual(state.total_contributions, (10, 6, 4, 10, 10, 10))

        state = state.advance_street()
        self.assertEqual(state.street, BettingStreet.FLOP)
        state = state.apply_action(raise_to(10))
        state = state.apply_action(CALL).apply_action(CALL)
        self.assertTrue(state.round_complete)
        self.assertEqual(state.total_contributions, (10, 6, 4, 20, 20, 20))
        while not state.is_terminal:
            state = state.advance_street()

        pots = state.side_pots()
        self.assertEqual(tuple(pot.amount for pot in pots), (24, 10, 16, 30))
        self.assertEqual(
            tuple(pot.eligible_seats for pot in pots),
            ((0, 1, 2, 3, 4, 5), (0, 1, 3, 4, 5), (0, 3, 4, 5), (3, 4, 5)),
        )
        settlement = state.settle((80, 90, 100, 70, 60, 50))
        self.assertEqual(settlement.payouts, (16, 10, 24, 30, 0, 0))
        self.assertEqual(settlement.net_returns, (6, 4, 20, 10, -20, -20))
        self.assertEqual(sum(settlement.net_returns), 0)

    def test_each_street_uses_postflop_order_and_resets_raise_state(self) -> None:
        state = _passive_round(NoLimitBettingState.six_max_100bb(button=0))
        self.assertEqual(state.street, BettingStreet.PREFLOP)
        self.assertTrue(state.round_complete)
        state = state.advance_street()
        self.assertEqual(state.street, BettingStreet.FLOP)
        self.assertEqual(state.pending_seats, (1, 2, 3, 4, 5, 0))
        self.assertEqual(state.street_contributions, (0,) * 6)
        self.assertEqual(state.last_full_raise_size, 2)
        self.assertEqual(state.acted_at_bet, (None,) * 6)

        observed: list[int] = []
        while not state.round_complete:
            assert state.acting_seat is not None
            observed.append(state.acting_seat)
            state = state.apply_action(CHECK)
        self.assertEqual(observed, [1, 2, 3, 4, 5, 0])
        state = state.advance_street()
        self.assertEqual(state.street, BettingStreet.TURN)
        state = _runout_with_checks(state)
        self.assertEqual(state.terminal_reason, TerminalReason.SHOWDOWN)

    def test_odd_chip_goes_to_first_tied_winner_left_of_button_per_pot(self) -> None:
        state = _passive_round(NoLimitBettingState.six_max_100bb(button=0))
        state = state.advance_street()
        state = state.apply_action(raise_to(3))  # seat 1
        state = state.apply_action(CALL)  # seat 2
        state = state.apply_action(CALL)  # seat 3
        state = state.apply_action(FOLD)  # seat 4
        state = state.apply_action(FOLD)  # seat 5
        state = state.apply_action(FOLD)  # button
        state = _runout_with_checks(state)
        settlement = state.settle((None, 10, 5, 10, None, None))
        self.assertEqual(tuple(pot.amount for pot in settlement.side_pots), (21,))
        self.assertEqual(len(settlement.side_pots[0].contribution_layers), 2)
        self.assertEqual(settlement.payouts, (0, 11, 0, 10, 0, 0))

    def test_folded_only_thresholds_do_not_award_multiple_odd_chips(self) -> None:
        # Three folded seats stopped at 1, 2, and 3 chips while all three live
        # seats reached 4.  The raw 6/5/4/3 contributor layers share the same
        # live claimant set, so this is one 18-chip pot, not four odd-chip
        # awards that would incorrectly pay the first tied winner 7/6/5.
        state = NoLimitBettingState(
            button=5,
            small_blind=1,
            big_blind=2,
            street=BettingStreet.RIVER,
            starting_stacks=(10,) * 6,
            stacks=(6, 6, 6, 9, 8, 7),
            total_contributions=(4, 4, 4, 1, 2, 3),
            street_contributions=(4, 4, 4, 1, 2, 3),
            folded=(False, False, False, True, True, True),
            pending_seats=(),
            last_full_raise_size=2,
            acted_at_bet=(4, 4, 4, 1, 2, 3),
            round_complete=True,
            terminal_reason=TerminalReason.SHOWDOWN,
        )
        self.assertEqual(tuple(layer.amount for layer in state.contribution_layers()), (6, 5, 4, 3))
        self.assertEqual(tuple(pot.amount for pot in state.side_pots()), (18,))
        settlement = state.settle((10, 10, 10, None, None, None))
        self.assertEqual(settlement.payouts, (6, 6, 6, 0, 0, 0))


class NoLimitBettingInvariantTests(unittest.TestCase):
    def test_frozen_state_rejects_mutable_vector_aliases(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            replace(state, stacks=list(state.stacks))  # type: ignore[arg-type]

    def test_history_rejects_boolean_seat_and_numerically_coincident_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "history seat"):
            BettingActionRecord(
                street=BettingStreet.PREFLOP,
                seat=True,  # type: ignore[arg-type]
                action=CALL,
                chips_committed=2,
                full_raise=False,
                uncalled_return_seat=None,
                uncalled_return_chips=0,
            )
        with self.assertRaisesRegex(TypeError, "full-raise flag"):
            BettingActionRecord(
                street=BettingStreet.PREFLOP,
                seat=3,
                action=CALL,
                chips_committed=2,
                full_raise=0,  # type: ignore[arg-type]
                uncalled_return_seat=None,
                uncalled_return_chips=0,
            )

    def test_seeded_random_legal_walks_preserve_chips_order_and_settlement(self) -> None:
        for seed in range(200):
            rng = random.Random(seed)
            starting = tuple(rng.randint(2, 50) for _ in range(SEAT_COUNT))
            state = NoLimitBettingState.new_hand(
                button=rng.randrange(SEAT_COUNT),
                starting_stacks=starting,
                small_blind=1,
                big_blind=2,
            )
            transitions = 0
            while not state.is_terminal:
                state.assert_invariants()
                self.assertEqual(sum(pot.amount for pot in state.side_pots()), state.pot)
                if state.round_complete:
                    state = state.advance_street()
                    transitions += 1
                    self.assertLessEqual(transitions, 4)
                    continue

                decision = state.legal_decision()
                choices = [FOLD, CALL] if decision.can_call else [CHECK]
                bounds = decision.raise_bounds
                if bounds is not None:
                    raise_amounts = {
                        bounds.minimum_raise_to,
                        bounds.maximum_raise_to,
                    }
                    if bounds.maximum_contestable_raise_to >= bounds.minimum_raise_to:
                        raise_amounts.add(bounds.maximum_contestable_raise_to)
                    choices.extend(raise_to(amount) for amount in raise_amounts)
                state = state.apply_action(rng.choice(choices))

            state.assert_invariants()
            strengths = None
            if state.terminal_reason is TerminalReason.SHOWDOWN:
                strengths = tuple(
                    rng.randrange(8) if seat in state.live_seats else None
                    for seat in range(SEAT_COUNT)
                )
            settlement = state.settle(strengths)
            self.assertEqual(sum(settlement.payouts), state.pot)
            self.assertEqual(sum(settlement.net_returns), 0)
            self.assertEqual(sum(settlement.final_stacks), sum(starting))


if __name__ == "__main__":
    unittest.main()
