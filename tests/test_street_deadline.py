from __future__ import annotations

import unittest

from pontius.street_deadline import (
    ACTION_EMISSION_RESERVE_SECONDS,
    STREET_WALL_SECONDS,
    StreetDeadlineLedger,
    StreetDeadlineStop,
)


class _FakeClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += round(seconds * 1_000_000_000)


class StreetDeadlineTests(unittest.TestCase):
    def test_charged_work_accumulates_across_actions_but_opponent_idle_does_not(self) -> None:
        clock = _FakeClock()
        ledger = StreetDeadlineLedger("flop", clock_ns=clock)
        first = ledger.begin_action()
        self.assertEqual(first.charged_compute_seconds, 0.0)
        self.assertEqual(first.work_remaining_seconds, 14.0)

        with ledger.charge():
            clock.advance(10.0)
        clock.advance(30.0)
        second = ledger.begin_action()
        self.assertEqual(second.street_wall_elapsed_seconds, 40.0)
        self.assertEqual(second.charged_compute_seconds, 10.0)
        self.assertEqual(second.idle_wall_seconds, 30.0)
        self.assertEqual(second.remaining_seconds, 5.0)
        self.assertEqual(second.work_remaining_seconds, 4.0)
        self.assertEqual(second.reserve_remaining_seconds, 1.0)
        self.assertEqual(ledger.admitted_work_seconds(20.0), 4.0)
        self.assertEqual(second.action_observations, 2)
        self.assertEqual(second.charge_intervals, 1)

    def test_reserve_is_inside_fifteen_charged_seconds(self) -> None:
        clock = _FakeClock()
        ledger = StreetDeadlineLedger("turn", clock_ns=clock)
        ledger.start_charge()
        clock.advance(14.0)
        stopped = ledger.stop_charge()
        self.assertEqual(stopped.work_remaining_seconds, 0.0)
        self.assertEqual(stopped.reserve_remaining_seconds, 1.0)
        with self.assertRaises(StreetDeadlineStop):
            ledger.require_work_time()

        ledger.start_charge()
        clock.advance(1.1)
        crossed = ledger.stop_charge()
        self.assertTrue(crossed.deadline_crossed)
        self.assertLess(crossed.remaining_seconds, 0.0)

    def test_only_an_exact_next_street_transition_resets_charged_work(self) -> None:
        clock = _FakeClock()
        ledger = StreetDeadlineLedger("preflop", clock_ns=clock)
        with ledger.charge():
            clock.advance(12.0)
        clock.advance(50.0)
        with self.assertRaisesRegex(ValueError, "exactly one street"):
            ledger.transition_to("turn")
        with self.assertRaisesRegex(ValueError, "exactly one street"):
            ledger.transition_to("preflop")
        reset = ledger.transition_to("flop")
        self.assertEqual(len(ledger.completed_streets), 1)
        completed = ledger.completed_streets[0]
        self.assertEqual(completed.street, "preflop")
        self.assertEqual(completed.charged_compute_seconds, 12.0)
        self.assertEqual(completed.idle_wall_seconds, 50.0)
        self.assertEqual(reset.street_wall_elapsed_seconds, 0.0)
        self.assertEqual(reset.charged_compute_seconds, 0.0)
        self.assertEqual(reset.remaining_seconds, STREET_WALL_SECONDS)
        self.assertEqual(reset.work_remaining_seconds, 14.0)
        self.assertEqual(reset.action_observations, 0)
        self.assertEqual(reset.charge_intervals, 0)
        self.assertEqual(
            reset.action_emission_reserve_seconds,
            ACTION_EMISSION_RESERVE_SECONDS,
        )

    def test_transition_and_nested_charge_fail_closed(self) -> None:
        ledger = StreetDeadlineLedger("turn", clock_ns=_FakeClock())
        ledger.start_charge()
        with self.assertRaisesRegex(RuntimeError, "already"):
            ledger.start_charge()
        with self.assertRaisesRegex(RuntimeError, "stop charged"):
            ledger.transition_to("river")
        ledger.stop_charge()
        with self.assertRaisesRegex(RuntimeError, "not currently"):
            ledger.stop_charge()

    def test_context_manager_stops_charge_after_exception(self) -> None:
        clock = _FakeClock()
        ledger = StreetDeadlineLedger("river", clock_ns=clock)
        with self.assertRaisesRegex(RuntimeError, "probe"), ledger.charge():
            clock.advance(2.5)
            raise RuntimeError("probe")
        snapshot = ledger.snapshot()
        self.assertFalse(snapshot.charging)
        self.assertEqual(snapshot.charged_compute_seconds, 2.5)

    def test_terminal_finalization_freezes_and_closes_the_street(self) -> None:
        clock = _FakeClock()
        ledger = StreetDeadlineLedger("river", clock_ns=clock)
        with ledger.charge():
            clock.advance(9.0)
        clock.advance(30.0)
        final = ledger.finalize()
        self.assertTrue(ledger.finalized)
        self.assertEqual(ledger.completed_streets, (final,))
        self.assertEqual(final.charged_compute_seconds, 9.0)
        self.assertEqual(final.idle_wall_seconds, 30.0)

        clock.advance(100.0)
        self.assertEqual(ledger.snapshot(), final)
        self.assertEqual(ledger.admitted_work_seconds(1.0), 0.0)
        with self.assertRaisesRegex(RuntimeError, "finalized"):
            ledger.start_charge()
        with self.assertRaisesRegex(RuntimeError, "already finalized"):
            ledger.finalize()

    def test_contract_is_fixed_at_fifteen_seconds_not_caller_configurable(self) -> None:
        self.assertEqual(STREET_WALL_SECONDS, 15.0)
        self.assertEqual(ACTION_EMISSION_RESERVE_SECONDS, 1.0)
        with self.assertRaises(TypeError):
            StreetDeadlineLedger(  # type: ignore[call-arg]
                "river",
                maximum_seconds=0.25,
            )


if __name__ == "__main__":
    unittest.main()
