from __future__ import annotations

import unittest
from hashlib import sha256

from pontius.action_clock import (
    ACTION_EMISSION_RESERVE_SECONDS,
    ACTION_RESPONSE_WALL_SECONDS,
    ActionClockLedger,
    ActionClockStop,
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


class ActionClockTests(unittest.TestCase):
    def test_each_controlled_action_gets_a_fresh_continuous_wall(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("flop", clock_ns=clock)

        first = ledger.begin_action(public_state_sha256=_digest("first"))
        self.assertEqual(first.remaining_seconds, ACTION_RESPONSE_WALL_SECONDS)
        clock.advance(2.0)
        with ledger.response_work():
            clock.advance(8.0)
        first_live = ledger.snapshot()
        self.assertEqual(first_live.action_wall_elapsed_seconds, 10.0)
        self.assertEqual(first_live.response_compute_seconds, 8.0)
        self.assertEqual(first_live.response_uninstrumented_seconds, 2.0)
        self.assertEqual(first_live.remaining_seconds, 5.0)
        self.assertEqual(first_live.work_remaining_seconds, 4.0)
        completed_first = ledger.finish_action()

        clock.advance(100.0)
        second = ledger.begin_action(public_state_sha256=_digest("second"))
        self.assertEqual(second.remaining_seconds, ACTION_RESPONSE_WALL_SECONDS)
        self.assertEqual(second.action_wall_elapsed_seconds, 0.0)
        self.assertEqual(second.action.hand_action_index, 2)
        self.assertEqual(second.action.street_action_index, 2)
        self.assertEqual(ledger.completed_actions, (completed_first,))

    def test_reserve_and_deadline_use_wall_not_instrumented_compute(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("turn", clock_ns=clock)
        clock.advance(1.0)
        ledger.begin_action(public_state_sha256=_digest("turn"))
        clock.advance(14.0)
        cutoff = ledger.snapshot()
        self.assertEqual(cutoff.response_compute_seconds, 0.0)
        self.assertEqual(cutoff.work_remaining_seconds, 0.0)
        self.assertEqual(
            cutoff.reserve_remaining_seconds,
            ACTION_EMISSION_RESERVE_SECONDS,
        )
        with self.assertRaises(ActionClockStop):
            ledger.require_work_time()

        clock.advance(1.1)
        crossed = ledger.snapshot()
        self.assertTrue(crossed.deadline_crossed)
        self.assertLess(crossed.remaining_seconds, 0.0)

    def test_turn_boundary_classifies_processing_without_starting_late(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("preflop", clock_ns=clock)
        boundary = ledger.start_transition_boundary()
        clock.advance(2.5)
        started = ledger.finish_transition_boundary(
            boundary,
            starts_controlled_action=True,
            controlled_action_public_state_sha256=_digest("boundary"),
        )
        self.assertEqual(started.action_wall_elapsed_seconds, 2.5)
        self.assertEqual(started.response_compute_seconds, 2.5)
        self.assertEqual(started.response_charge_intervals, 1)
        ledger.finish_action()

        boundary = ledger.start_transition_boundary()
        clock.advance(3.0)
        prepared = ledger.finish_transition_boundary(
            boundary,
            starts_controlled_action=False,
        )
        self.assertEqual(prepared.compute_seconds, 3.0)
        self.assertEqual(ledger.hand_preparation_compute_seconds, 3.0)

    def test_street_transition_archives_prior_actions_at_event_boundary(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("preflop", clock_ns=clock)
        ledger.begin_action(public_state_sha256=_digest("preflop"))
        with ledger.response_work():
            clock.advance(1.0)
        preflop_action = ledger.finish_action()
        clock.advance(20.0)

        boundary = ledger.start_transition_boundary()
        clock.advance(0.5)
        flop = ledger.finish_transition_boundary(
            boundary,
            starts_controlled_action=True,
            controlled_action_public_state_sha256=_digest("flop"),
            next_street="flop",
        )
        self.assertEqual(len(ledger.completed_streets), 1)
        archived = ledger.completed_streets[0]
        self.assertEqual(archived.street, "preflop")
        self.assertEqual(archived.actions, (preflop_action,))
        self.assertEqual(archived.street_wall_elapsed_seconds, 21.0)
        self.assertEqual(flop.action.street, "flop")
        self.assertEqual(flop.action.street_action_index, 1)
        self.assertEqual(flop.action_wall_elapsed_seconds, 0.5)

    def test_nested_stale_finalized_and_reversed_clock_paths_fail_closed(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("river", clock_ns=clock)
        ledger.start_preparation_work()
        with self.assertRaisesRegex(RuntimeError, "already"):
            ledger.start_preparation_work()
        with self.assertRaisesRegex(RuntimeError, "timing"):
            ledger.begin_action(public_state_sha256=_digest("blocked"))
        ledger.stop_preparation_work()

        boundary = ledger.start_transition_boundary()
        with self.assertRaisesRegex(RuntimeError, "pending"):
            ledger.start_transition_boundary()
        ledger.abort_transition_boundary(boundary)
        with self.assertRaisesRegex(ValueError, "stale"):
            ledger.abort_transition_boundary(boundary)

        clock.advance(1.0)
        ledger.begin_action(public_state_sha256=_digest("river"))
        clock.nanoseconds -= 1
        with self.assertRaisesRegex(RuntimeError, "backwards"):
            ledger.snapshot()
        clock.nanoseconds += 1
        ledger.finish_action()
        ledger.finalize()
        with self.assertRaisesRegex(RuntimeError, "finalized"):
            ledger.begin_action(public_state_sha256=_digest("finalized"))

    def test_contract_is_fixed_and_not_caller_configurable(self) -> None:
        self.assertEqual(ACTION_RESPONSE_WALL_SECONDS, 15.0)
        self.assertEqual(ACTION_EMISSION_RESERVE_SECONDS, 1.0)
        with self.assertRaises(TypeError):
            ActionClockLedger(  # type: ignore[call-arg]
                "river",
                maximum_seconds=30.0,
            )

    def test_action_state_identity_is_mandatory_and_boundary_owned(self) -> None:
        ledger = ActionClockLedger("flop", clock_ns=_FakeClock())
        with self.assertRaisesRegex(TypeError, "digest"):
            ledger.begin_action(public_state_sha256="not-a-digest")

        boundary = ledger.start_transition_boundary()
        with self.assertRaisesRegex(TypeError, "digest"):
            ledger.finish_transition_boundary(
                boundary,
                starts_controlled_action=True,
            )
        ledger.abort_transition_boundary(boundary)

        boundary = ledger.start_transition_boundary()
        with self.assertRaisesRegex(ValueError, "non-action"):
            ledger.finish_transition_boundary(
                boundary,
                starts_controlled_action=False,
                controlled_action_public_state_sha256=_digest("wrong-phase"),
            )
        ledger.abort_transition_boundary(boundary)


if __name__ == "__main__":
    unittest.main()
