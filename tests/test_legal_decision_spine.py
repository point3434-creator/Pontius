from __future__ import annotations

import unittest

from pontius.legal_decision_spine import (
    ActionSelectionReason,
    LegalDecisionSpine,
)
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from pontius.street_deadline import StreetDeadlineLedger


class _FakeClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += round(seconds * 1_000_000_000)


def _passive_preflop() -> NoLimitBettingState:
    state = NoLimitBettingState.six_max_100bb(button=0)
    while not state.round_complete:
        decision = state.legal_decision()
        state = state.apply_action(CALL if decision.can_call else CHECK)
    return state


class LegalDecisionSpineTests(unittest.TestCase):
    def test_timely_legal_candidate_is_selected_over_blueprint_fallback(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpine.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=clock,
        )
        ticket = spine.open_controlled_decision()
        self.assertEqual(ticket.decision.acting_seat, 3)
        with spine.charge_compute():
            clock.advance(10.0)
        emitted = spine.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertEqual(emitted.selected, raise_to(4))
        self.assertFalse(emitted.used_fallback)
        self.assertEqual(emitted.reason, ActionSelectionReason.CANDIDATE)
        self.assertEqual(emitted.deadline.charged_compute_seconds, 10.0)
        self.assertEqual(spine.state.acting_seat, 4)

    def test_two_controlled_actions_share_charged_budget_while_idle_is_free(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpine.new_hand(
            button=0,
            controlled_seat=3,
            starting_stacks=(30, 30, 30, 30, 3, 30),
            small_blind=1,
            big_blind=2,
            clock_ns=clock,
        )
        spine.open_controlled_decision()
        with spine.charge_compute():
            clock.advance(8.0)
        spine.emit_controlled_action(candidate=CALL, fallback=FOLD)

        clock.advance(100.0)
        spine.observe_opponent_action(raise_to(3))
        for _ in range(4):
            spine.observe_opponent_action(CALL)
        self.assertEqual(spine.state.acting_seat, 3)

        ticket = spine.open_controlled_decision()
        self.assertEqual(ticket.deadline.charged_compute_seconds, 8.0)
        self.assertEqual(ticket.deadline.idle_wall_seconds, 100.0)
        with spine.charge_compute():
            clock.advance(5.0)
        emitted = spine.emit_controlled_action(candidate=CALL, fallback=FOLD)
        self.assertEqual(emitted.deadline.charged_compute_seconds, 13.0)
        self.assertEqual(emitted.deadline.action_observations, 2)

    def test_candidate_after_work_cutoff_uses_fallback(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpine.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=clock,
        )
        spine.open_controlled_decision()
        with spine.charge_compute():
            clock.advance(14.1)
        emitted = spine.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertEqual(emitted.selected, CALL)
        self.assertTrue(emitted.used_fallback)
        self.assertEqual(emitted.reason, ActionSelectionReason.WORK_BUDGET_EXHAUSTED)

    def test_crossed_street_deadline_still_fails_closed_to_fallback(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpine.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=clock,
        )
        spine.open_controlled_decision()
        with spine.charge_compute():
            clock.advance(15.1)
        emitted = spine.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertTrue(emitted.deadline.deadline_crossed)
        self.assertEqual(emitted.selected, CALL)
        self.assertEqual(emitted.reason, ActionSelectionReason.STREET_DEADLINE_CROSSED)

    def test_illegal_candidate_uses_legal_fallback_and_invalid_fallback_raises(self) -> None:
        spine = LegalDecisionSpine.six_max_100bb(button=0, controlled_seat=3)
        spine.open_controlled_decision()
        emitted = spine.emit_controlled_action(candidate=raise_to(3), fallback=CALL)
        self.assertEqual(emitted.reason, ActionSelectionReason.ILLEGAL_CANDIDATE)
        self.assertEqual(emitted.selected, CALL)

        second = LegalDecisionSpine.six_max_100bb(button=0, controlled_seat=3)
        second.open_controlled_decision()
        with self.assertRaisesRegex(ValueError, "check"):
            second.emit_controlled_action(candidate=CALL, fallback=CHECK)
        self.assertTrue(second.decision_open)
        self.assertFalse(second.deadline.charging)

    def test_opponent_idle_is_free_but_event_processing_has_a_charge_interval(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpine.six_max_100bb(
            button=0,
            controlled_seat=4,
            clock_ns=clock,
        )
        self.assertEqual(spine.deadline.charge_intervals, 1)
        clock.advance(40.0)
        spine.observe_opponent_action(CALL)
        self.assertEqual(spine.deadline.charged_compute_seconds, 0.0)
        self.assertEqual(spine.deadline.idle_wall_seconds, 40.0)
        self.assertEqual(spine.deadline.charge_intervals, 2)
        with self.assertRaisesRegex(ValueError, "controlled-seat"):
            spine.observe_opponent_action(CALL)

    def test_exact_street_transition_resets_the_same_ledger(self) -> None:
        clock = _FakeClock()
        state = _passive_preflop()
        ledger = StreetDeadlineLedger("preflop", clock_ns=clock)
        with ledger.charge():
            clock.advance(12.0)
        spine = LegalDecisionSpine(state, controlled_seat=1, ledger=ledger)
        advanced = spine.advance_street()
        self.assertEqual(advanced.street, BettingStreet.FLOP)
        self.assertEqual(len(spine.completed_street_deadlines), 1)
        completed = spine.completed_street_deadlines[0]
        self.assertEqual(completed.street, "preflop")
        self.assertEqual(completed.charged_compute_seconds, 12.0)
        self.assertEqual(completed.charge_intervals, 2)
        self.assertEqual(spine.deadline.street, "flop")
        self.assertEqual(spine.deadline.charged_compute_seconds, 0.0)
        self.assertEqual(spine.deadline.action_observations, 0)

    def test_terminal_action_finalizes_the_last_street_snapshot(self) -> None:
        spine = LegalDecisionSpine.six_max_100bb(button=0, controlled_seat=3)
        spine.open_controlled_decision()
        spine.emit_controlled_action(candidate=raise_to(20), fallback=CALL)
        for _ in range(5):
            spine.observe_opponent_action(FOLD)

        self.assertTrue(spine.state.is_terminal)
        self.assertEqual(len(spine.completed_street_deadlines), 1)
        self.assertEqual(spine.completed_street_deadlines[0].street, "preflop")
        with self.assertRaisesRegex(RuntimeError, "finalized"), spine.charge_compute():
            pass

    def test_all_in_runout_archives_all_four_streets_through_showdown(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(2,) * 6,
            small_blind=1,
            big_blind=2,
        )
        while not state.round_complete:
            state = state.apply_action(CALL)
        spine = LegalDecisionSpine(state, controlled_seat=0)

        for _ in range(4):
            spine.advance_street()

        self.assertEqual(spine.state.terminal_reason.value, "showdown")
        self.assertEqual(
            tuple(snapshot.street for snapshot in spine.completed_street_deadlines),
            ("preflop", "flop", "turn", "river"),
        )


if __name__ == "__main__":
    unittest.main()
