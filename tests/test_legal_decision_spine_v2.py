from __future__ import annotations

import ast
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from pontius.action_clock import ActionClockLedger
from pontius.legal_decision_spine_v2 import (
    ActionSelectionReasonV2,
    LegalDecisionSpineV2,
    public_betting_state_sha256,
)
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)


class _FakeClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += round(seconds * 1_000_000_000)


def _digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


def _passive_preflop() -> NoLimitBettingState:
    state = NoLimitBettingState.six_max_100bb(button=0)
    while not state.round_complete:
        decision = state.legal_decision()
        state = state.apply_action(CALL if decision.can_call else CHECK)
    return state


class LegalDecisionSpineV2Tests(unittest.TestCase):
    def test_timely_candidate_uses_one_fresh_action_wall(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpineV2.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=clock,
        )
        ticket = spine.open_controlled_decision()
        self.assertEqual(ticket.decision.acting_seat, 3)
        self.assertEqual(
            ticket.deadline.action.public_state_sha256,
            public_betting_state_sha256(spine.state),
        )
        with spine.charge_compute():
            clock.advance(10.0)
        emitted = spine.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertEqual(emitted.selected, raise_to(4))
        self.assertFalse(emitted.used_fallback)
        self.assertEqual(emitted.reason, ActionSelectionReasonV2.CANDIDATE)
        self.assertEqual(emitted.deadline.action_wall_elapsed_seconds, 10.0)
        self.assertEqual(emitted.deadline.response_compute_seconds, 10.0)
        self.assertIsNone(spine.deadline)

    def test_two_same_street_actions_receive_independent_response_walls(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpineV2.new_hand(
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
        first = spine.emit_controlled_action(candidate=CALL, fallback=FOLD)
        self.assertEqual(first.deadline.action_wall_elapsed_seconds, 8.0)

        clock.advance(100.0)
        spine.observe_opponent_action(raise_to(3))
        for _ in range(4):
            spine.observe_opponent_action(CALL)
        self.assertEqual(spine.state.acting_seat, 3)
        second_ticket = spine.open_controlled_decision()
        self.assertEqual(second_ticket.deadline.action.street_action_index, 2)
        self.assertEqual(second_ticket.deadline.action_wall_elapsed_seconds, 0.0)
        self.assertEqual(second_ticket.deadline.remaining_seconds, 15.0)
        with spine.charge_compute():
            clock.advance(5.0)
        second = spine.emit_controlled_action(candidate=CALL, fallback=FOLD)
        self.assertEqual(second.deadline.action_wall_elapsed_seconds, 5.0)
        self.assertEqual(len(spine.completed_action_deadlines), 2)

    def test_same_street_preparation_hit_adds_quality_work_not_live_time(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpineV2.six_max_100bb(
            button=0,
            controlled_seat=4,
            clock_ns=clock,
        )
        target = spine.state.apply_action(CALL)
        semantic = _digest("same-street-semantic")
        source = _digest("same-street-source")
        artifact = b"same-street-preparation"
        spine.preparation_bank.start_preparation(
            target_public_state_sha256=public_betting_state_sha256(target),
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        clock.advance(4.0)
        spine.preparation_bank.seal_preparation(artifact)

        spine.observe_opponent_action(CALL)
        self.assertEqual(spine.state.acting_seat, 4)
        spine.claim_preparation(
            artifact_bytes=artifact,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        deadline = spine.deadline
        assert deadline is not None
        self.assertEqual(deadline.credited_preparation_seconds, 4.0)
        self.assertEqual(deadline.remaining_seconds, 15.0)

    def test_previous_street_preparation_can_match_first_to_act(self) -> None:
        clock = _FakeClock()
        state = _passive_preflop()
        timing = ActionClockLedger("preflop", clock_ns=clock)
        spine = LegalDecisionSpineV2(
            state,
            controlled_seat=1,
            action_clock=timing,
        )
        target = state.advance_street()
        semantic = _digest("flop-semantic")
        source = _digest("flop-source")
        artifact = b"future-flop-preparation"
        spine.preparation_bank.start_preparation(
            target_public_state_sha256=public_betting_state_sha256(target),
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        clock.advance(7.0)
        credit = spine.preparation_bank.seal_preparation(artifact)

        advanced = spine.advance_street()
        self.assertEqual(advanced.street, BettingStreet.FLOP)
        self.assertEqual(advanced.acting_seat, 1)
        self.assertEqual(credit.created_street, "preflop")
        spine.claim_preparation(
            artifact_bytes=artifact,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        deadline = spine.deadline
        assert deadline is not None
        self.assertEqual(deadline.action.street, "flop")
        self.assertEqual(deadline.credited_preparation_seconds, 7.0)
        self.assertEqual(deadline.work_remaining_seconds, 14.0)
        self.assertEqual(spine.completed_street_timings[0].street, "preflop")

    def test_uninstrumented_wall_triggers_cutoff_and_hard_fallback(self) -> None:
        clock = _FakeClock()
        spine = LegalDecisionSpineV2.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=clock,
        )
        spine.open_controlled_decision()
        clock.advance(14.1)
        emitted = spine.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertEqual(emitted.selected, CALL)
        self.assertEqual(
            emitted.reason,
            ActionSelectionReasonV2.WORK_BUDGET_EXHAUSTED,
        )
        self.assertGreaterEqual(emitted.deadline.response_uninstrumented_seconds, 14.1)

        crossed_clock = _FakeClock()
        crossed = LegalDecisionSpineV2.six_max_100bb(
            button=0,
            controlled_seat=3,
            clock_ns=crossed_clock,
        )
        crossed.open_controlled_decision()
        crossed_clock.advance(15.1)
        late = crossed.emit_controlled_action(candidate=raise_to(4), fallback=CALL)
        self.assertEqual(late.selected, CALL)
        self.assertEqual(
            late.reason,
            ActionSelectionReasonV2.ACTION_DEADLINE_CROSSED,
        )
        self.assertTrue(late.deadline.deadline_crossed)

    def test_illegal_candidate_and_fallback_paths_remain_exact(self) -> None:
        spine = LegalDecisionSpineV2.six_max_100bb(button=0, controlled_seat=3)
        spine.open_controlled_decision()
        emitted = spine.emit_controlled_action(candidate=raise_to(3), fallback=CALL)
        self.assertEqual(emitted.reason, ActionSelectionReasonV2.ILLEGAL_CANDIDATE)
        self.assertEqual(emitted.selected, CALL)

        second = LegalDecisionSpineV2.six_max_100bb(button=0, controlled_seat=3)
        second.open_controlled_decision()
        with self.assertRaisesRegex(ValueError, "check"):
            second.emit_controlled_action(candidate=CALL, fallback=CHECK)
        self.assertTrue(second.decision_open)
        self.assertIsNotNone(second.deadline)
        self.assertFalse(second.action_clock.charging)

    def test_all_in_runout_archives_every_street_and_terminal_timing(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(2,) * 6,
            small_blind=1,
            big_blind=2,
        )
        while not state.round_complete:
            state = state.apply_action(CALL)
        spine = LegalDecisionSpineV2(state, controlled_seat=0)

        for _ in range(4):
            spine.advance_street()

        self.assertEqual(spine.state.terminal_reason.value, "showdown")
        self.assertEqual(
            tuple(snapshot.street for snapshot in spine.completed_street_timings),
            ("preflop", "flop", "turn", "river"),
        )
        self.assertTrue(spine.action_clock.finalized)

    def test_public_state_digest_is_deterministic_complete_and_nominal(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        same = NoLimitBettingState.six_max_100bb(button=0)
        changed = state.apply_action(CALL)
        self.assertEqual(
            public_betting_state_sha256(state),
            public_betting_state_sha256(same),
        )
        self.assertNotEqual(
            public_betting_state_sha256(state),
            public_betting_state_sha256(changed),
        )
        with self.assertRaises(TypeError):
            public_betting_state_sha256("state")  # type: ignore[arg-type]

    def test_external_boundary_owns_first_and_later_actor_processing(self) -> None:
        first_clock = _FakeClock()
        original_new_hand = NoLimitBettingState.new_hand

        def delayed_new_hand(**kwargs: object) -> NoLimitBettingState:
            first_clock.advance(2.25)
            return original_new_hand(**kwargs)  # type: ignore[arg-type]

        with patch.object(
            NoLimitBettingState,
            "new_hand",
            side_effect=delayed_new_hand,
        ):
            first = LegalDecisionSpineV2.six_max_100bb(
                button=0,
                controlled_seat=3,
                clock_ns=first_clock,
            )
        first_deadline = first.deadline
        assert first_deadline is not None
        self.assertEqual(first_deadline.action_wall_elapsed_seconds, 2.25)
        self.assertEqual(first_deadline.response_compute_seconds, 2.25)

        later_clock = _FakeClock()

        def delayed_nonactor_hand(**kwargs: object) -> NoLimitBettingState:
            later_clock.advance(1.5)
            return original_new_hand(**kwargs)  # type: ignore[arg-type]

        with patch.object(
            NoLimitBettingState,
            "new_hand",
            side_effect=delayed_nonactor_hand,
        ):
            later = LegalDecisionSpineV2.six_max_100bb(
                button=0,
                controlled_seat=4,
                clock_ns=later_clock,
            )
        self.assertEqual(
            later.action_clock.hand_preparation_compute_seconds,
            1.5,
        )

        original_apply_action = NoLimitBettingState.apply_action

        def delayed_apply_action(
            state: NoLimitBettingState,
            action: object,
        ) -> NoLimitBettingState:
            later_clock.advance(3.0)
            return original_apply_action(state, action)  # type: ignore[arg-type]

        with patch.object(
            NoLimitBettingState,
            "apply_action",
            autospec=True,
            side_effect=delayed_apply_action,
        ):
            later.observe_opponent_action(CALL)
        later_deadline = later.deadline
        assert later_deadline is not None
        self.assertEqual(later_deadline.action_wall_elapsed_seconds, 3.0)
        self.assertEqual(later_deadline.response_compute_seconds, 3.0)

    def test_prebuilt_controlled_state_cannot_start_its_clock_late(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        with self.assertRaisesRegex(ValueError, "boundary-started"):
            LegalDecisionSpineV2(state, controlled_seat=3)

        timing = ActionClockLedger("preflop", clock_ns=_FakeClock())
        timing.begin_action(public_state_sha256=_digest("wrong-state"))
        with self.assertRaisesRegex(ValueError, "active action clock"):
            LegalDecisionSpineV2(
                state,
                controlled_seat=3,
                action_clock=timing,
            )

    def test_successor_imports_only_exact_betting_and_timing_dependencies(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "pontius"
        expected = {
            "action_clock.py": {"preparation_bank", "street_deadline"},
            "preparation_bank.py": {"action_clock", "street_deadline"},
            "legal_decision_spine_v2.py": {
                "action_clock",
                "no_limit_betting",
                "preparation_bank",
            },
        }
        for filename, allowed in expected.items():
            path = root / filename
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            local_imports = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is not None
            }
            with self.subTest(filename=filename):
                self.assertEqual(local_imports, allowed)


if __name__ == "__main__":
    unittest.main()
