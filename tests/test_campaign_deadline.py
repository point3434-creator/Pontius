from __future__ import annotations

import unittest

from pontius.campaign_deadline import (
    CampaignDeadlineStop,
    MonotonicCampaignDeadline,
)


class _FakeMonotonicClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += int(seconds * 1_000_000_000)


class CampaignDeadlineTests(unittest.TestCase):
    def test_checkpoints_before_admission_and_stops_early(self) -> None:
        clock = _FakeMonotonicClock()
        deadline = MonotonicCampaignDeadline(10.0, clock_ns=clock)
        events = []

        def checkpoint() -> None:
            events.append("checkpoint")
            clock.advance(3.0)

        with self.assertRaises(CampaignDeadlineStop) as raised:
            deadline.checkpoint_before_unit(
                "runtime/target-2/two-size",
                8.0,
                checkpoint=checkpoint,
            )
        self.assertEqual(events, ["checkpoint"])
        self.assertEqual(raised.exception.reason, "insufficient_remaining_time")
        self.assertEqual(raised.exception.snapshot.elapsed_seconds, 3.0)
        self.assertEqual(raised.exception.snapshot.remaining_seconds, 7.0)
        self.assertFalse(raised.exception.snapshot.deadline_crossed)
        self.assertEqual(
            raised.exception.as_record()["deadline"]["clock"],
            "monotonic_ns",
        )

    def test_guards_completion_before_another_unit(self) -> None:
        clock = _FakeMonotonicClock()
        deadline = MonotonicCampaignDeadline(10.0, clock_ns=clock)
        checkpoints = []
        with (
            self.assertRaises(CampaignDeadlineStop) as raised,
            deadline.bounded_unit(
                "cache/target-1/one-size",
                9.0,
                checkpoint=lambda: checkpoints.append("saved"),
            ),
        ):
            clock.advance(10.5)
        self.assertEqual(checkpoints, ["saved"])
        self.assertEqual(raised.exception.reason, "deadline_crossed")
        self.assertEqual(raised.exception.unit_elapsed_seconds, 10.5)
        self.assertEqual(raised.exception.snapshot.remaining_seconds, -0.5)
        self.assertTrue(raised.exception.snapshot.deadline_crossed)

    def test_stops_when_a_unit_exceeds_its_frozen_bound(self) -> None:
        clock = _FakeMonotonicClock()
        deadline = MonotonicCampaignDeadline(100.0, clock_ns=clock)
        with (
            self.assertRaises(CampaignDeadlineStop) as raised,
            deadline.bounded_unit(
                "runtime/target-1/one-size",
                5.0,
                checkpoint=lambda: None,
            ),
        ):
            clock.advance(5.5)
        self.assertEqual(raised.exception.reason, "unit_bound_crossed")
        self.assertEqual(raised.exception.unit_elapsed_seconds, 5.5)
        self.assertFalse(raised.exception.snapshot.deadline_crossed)

    def test_admits_exact_bound_and_rejects_clock_rollback(self) -> None:
        clock = _FakeMonotonicClock()
        deadline = MonotonicCampaignDeadline(5.0, clock_ns=clock)
        admitted = deadline.checkpoint_before_unit(
            "target-1",
            5.0,
            checkpoint=lambda: None,
        )
        self.assertEqual(admitted.remaining_seconds, 5.0)
        clock.advance(1.0)
        self.assertEqual(deadline.snapshot().elapsed_seconds, 1.0)
        clock.nanoseconds = 0
        with self.assertRaisesRegex(RuntimeError, "moved backwards"):
            deadline.snapshot()

    def test_rejects_invalid_limits_clock_and_checkpoint(self) -> None:
        for value in (True, 0, -1, float("inf"), float("nan"), "10"):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                MonotonicCampaignDeadline(value)  # type: ignore[arg-type]
        with self.assertRaisesRegex(RuntimeError, "invalid value"):
            MonotonicCampaignDeadline(1.0, clock_ns=lambda: -1)
        deadline = MonotonicCampaignDeadline(1.0, clock_ns=lambda: 0)
        with self.assertRaises(TypeError):
            deadline.checkpoint_before_unit("x", 0.5, checkpoint=None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            deadline.checkpoint_before_unit("", 0.5, checkpoint=lambda: None)


if __name__ == "__main__":
    unittest.main()
