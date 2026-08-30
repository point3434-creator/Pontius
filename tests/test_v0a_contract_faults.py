"""Fault-schedule regressions for the r001 cold-review findings F1-F7.

Each test drives the real production path under a real failure schedule at
the public event boundary. None substitutes a helper double for a contract:
delays and faults are injected around real methods and real objects, which
then do their real work.
"""

from __future__ import annotations

import sys
import unittest

import pontius.v0a.runtime as runtime_module
from pontius.holdem_cards import OneSeatCardState
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    BlueprintSelection,
    ImmutableBlueprintActionSource,
    passive_blueprint_action,
)
from pontius.no_limit_betting import CALL, FOLD, NoLimitBettingState, raise_to
from pontius.v0a.clock import ClockInvalidError
from pontius.v0a.model import (
    ActionMailbox,
    DeliveryReceipt,
    DeliveryStatus,
    FailureCode,
    HandAction,
    HandStartedEvent,
    OpponentActionEvent,
    ShowdownResultEvent,
    StreetRevealedEvent,
    TimingStatus,
)
from pontius.v0a.runtime import HandRuntime

HAND = "fault-hand"
STACKS = (200,) * 6
NANOS = 1_000_000_000


class StepClock:
    """Deterministic witness source with an optional scheduled fault."""

    def __init__(self, start: int = 1_000, step: int = 1_000) -> None:
        self.now = start
        self.step = step
        self.reads = 0
        self._fault_at: int | None = None
        self._fault: Exception | None = None
        self._pending_jump = 0

    def fail_at(self, read_number: int, error: Exception) -> None:
        self._fault_at = read_number
        self._fault = error

    def jump(self, nanoseconds: int) -> None:
        self._pending_jump += nanoseconds

    def __call__(self) -> int:
        self.reads += 1
        if self._fault_at == self.reads:
            assert self._fault is not None
            raise self._fault
        value = self.now + self._pending_jump
        self._pending_jump = 0
        self.now = value + self.step
        return value


def started(**overrides) -> HandStartedEvent:
    fields = {
        "hand_id": HAND,
        "event_index": 0,
        "button": 0,
        "controlled_seat": 1,
        "starting_stacks": STACKS,
        "small_blind": 1,
        "big_blind": 2,
        "private_cards": (0, 13),
    }
    fields.update(overrides)
    return HandStartedEvent(**fields)


def opponent(index: int, seat: int, kind: str, street: str = "preflop", raise_to_amount=None):
    return OpponentActionEvent(
        hand_id=HAND,
        event_index=index,
        street=street,
        seat=seat,
        action=HandAction(kind=kind, raise_to=raise_to_amount),
    )


def empty_source() -> ImmutableBlueprintActionSource:
    return ImmutableBlueprintActionSource(source_id="fault-empty")


def drive_to_flop(runtime: HandRuntime) -> int:
    """Real preflop leaving the controlled small blind first to act postflop.

    Seats 3, 4, 5 and 0 fold; the controlled seat 1 completes the small blind
    (its own decision, inline); the big blind checks its option. Postflop the
    live seats are 1 and 2, and clockwise order puts the controlled seat first.
    """

    assert runtime.dispatch(started()).status in ("accepted", "decided")
    index = 1
    for seat in (3, 4, 5, 0):
        outcome = runtime.dispatch(opponent(index, seat, "fold"))
        index += 1
        if seat == 0:
            assert outcome.status == "decided", outcome
        else:
            assert outcome.status == "accepted", outcome
    outcome = runtime.dispatch(opponent(index, 2, "check"))
    assert outcome.status == "accepted", outcome
    return index + 1


class F1IngressWallTests(unittest.TestCase):
    """The response wall covers pre-decision adapter work on every path."""

    def test_reveal_path_charges_visible_card_construction(self) -> None:
        clock = StepClock()

        class DelayingCardState(OneSeatCardState):
            """Real card state; its transition costs measurable time."""

            __slots__ = ()

            def advance_to(self, street, revealed_cards):
                clock.jump(16 * NANOS)
                return OneSeatCardState.advance_to(self, street, revealed_cards)

        original = runtime_module.OneSeatCardState
        runtime_module.OneSeatCardState = DelayingCardState
        try:
            runtime = HandRuntime(
                blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
            )
            index = drive_to_flop(runtime)
            outcome = runtime.dispatch(
                StreetRevealedEvent(
                    hand_id=HAND, event_index=index, street="flop", cards=(20, 21, 22)
                )
            )
        finally:
            runtime_module.OneSeatCardState = original

        self.assertEqual(outcome.status, "failed", outcome)
        self.assertIs(outcome.failure.code, FailureCode.ACTION_DEADLINE_EXCEEDED)
        record = outcome.decision
        self.assertIsNotNone(record)
        self.assertGreaterEqual(record.timing.elapsed_ns, 16 * NANOS)
        self.assertTrue(record.timing.deadline_crossed)

    def test_opponent_path_charges_validation_and_transition(self) -> None:
        clock = StepClock(step=1_000_000)
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        runtime.dispatch(started())
        first_read_of_dispatch = clock.now
        outcome = runtime.dispatch(opponent(1, 3, "fold"))
        self.assertEqual(outcome.status, "accepted")
        # The boundary for this dispatch opened at its first observation, so a
        # later decision's wall cannot start before the event arrived.
        self.assertGreaterEqual(clock.now, first_read_of_dispatch)

    def test_wall_starts_at_the_event_not_after_validation(self) -> None:
        clock = StepClock(step=1_000_000)
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        runtime.dispatch(started())
        reads_before = clock.reads
        outcome = runtime.dispatch(opponent(1, 3, "fold"))
        self.assertEqual(outcome.status, "accepted")
        self.assertGreater(clock.reads, reads_before)


class F2ShowdownCompletionTests(unittest.TestCase):
    """An accepted showdown closes the hand irreversibly."""

    def play_to_showdown(self, runtime: HandRuntime) -> int:
        index = drive_to_flop(runtime)
        for street, cards in (("flop", (20, 21, 22)), ("turn", (30,)), ("river", (40,))):
            outcome = runtime.dispatch(
                StreetRevealedEvent(
                    hand_id=HAND, event_index=index, street=street, cards=cards
                )
            )
            # The controlled seat is first to act postflop, so the reveal
            # itself produces the decision.
            self.assertEqual(outcome.status, "decided", street)
            index += 1
            outcome = runtime.dispatch(opponent(index, 2, "check", street=street))
            self.assertEqual(outcome.status, "accepted", street)
            index += 1
        return index

    def test_a_second_showdown_vector_is_refused(self) -> None:
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=StepClock()
        )
        index = self.play_to_showdown(runtime)
        first = ShowdownResultEvent(
            hand_id=HAND, event_index=index, strengths=(None, 2, 9, None, None, None)
        )
        self.assertEqual(runtime.dispatch(first).status, "accepted")
        settled = runtime.settle()
        self.assertTrue(runtime.hand_complete)

        second = ShowdownResultEvent(
            hand_id=HAND, event_index=index + 1, strengths=(None, 9, 1, None, None, None)
        )
        outcome = runtime.dispatch(second)
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.EVENT_ORDER)
        self.assertEqual(runtime.settle().payouts, settled.payouts)

    def test_no_event_is_accepted_after_completion(self) -> None:
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=StepClock()
        )
        index = self.play_to_showdown(runtime)
        runtime.dispatch(
            ShowdownResultEvent(
                hand_id=HAND, event_index=index, strengths=(None, 2, 9, None, None, None)
            )
        )
        for event in (
            opponent(index + 1, 1, "check", street="river"),
            StreetRevealedEvent(
                hand_id=HAND, event_index=index + 1, street="river", cards=(41,)
            ),
            started(),
        ):
            with self.subTest(event.__class__.__name__):
                outcome = runtime.dispatch(event)
                self.assertEqual(outcome.status, "failed")
                self.assertIs(outcome.failure.code, FailureCode.EVENT_ORDER)


class F3BlueprintAuthorityTests(unittest.TestCase):
    """The bound immutable policy is the only one that may answer."""

    def context(self):
        betting = NoLimitBettingState.new_hand(
            button=0, starting_stacks=STACKS, small_blind=1, big_blind=2
        )
        for _ in range(4):
            betting = betting.apply_action(FOLD)
        betting = betting.apply_action(CALL)
        cards = OneSeatCardState.preflop(controlled_seat=2, private_hand=(0, 13))
        return cards, betting

    def test_a_source_switching_policies_mid_hand_is_refused(self) -> None:
        cards, betting = self.context()
        other = ImmutableBlueprintActionSource(source_id="a-different-policy")

        class SwitchingSource:
            def __init__(self, first) -> None:
                self._first = first
                self._calls = 0

            @property
            def digest(self) -> str:
                return self._first.digest

            def action_for(self, **kwargs):
                self._calls += 1
                return other.action_for(**kwargs)

        runtime = HandRuntime(
            blueprint=SwitchingSource(empty_source()),
            mailbox=ActionMailbox(),
            clock=StepClock(),
        )
        drive = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=StepClock()
        )
        del drive
        runtime.dispatch(started())
        index = 1
        outcome = None
        for seat in (3, 4, 5, 0):
            outcome = runtime.dispatch(opponent(index, seat, "fold"))
            index += 1
            if outcome.status == "failed":
                break
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.SOURCE_BINDING_MISMATCH)

    def test_a_fabricated_passive_default_is_refused(self) -> None:
        cards, betting = self.context()

        class FabricatingSource:
            digest = empty_source().digest

            def action_for(self, *, cards, betting, decision):
                key = BlueprintDecisionKey.from_state(
                    cards=cards, betting=betting, decision=decision
                )
                # Claims a miss but returns a non-passive legal action.
                return BlueprintSelection(
                    key=key,
                    action=raise_to(6),
                    table_hit=False,
                    source_digest=self.digest,
                )

        runtime = HandRuntime(
            blueprint=FabricatingSource(), mailbox=ActionMailbox(), clock=StepClock()
        )
        runtime.dispatch(started())
        index = 1
        outcome = None
        for seat in (3, 4, 5, 0):
            outcome = runtime.dispatch(opponent(index, seat, "fold"))
            index += 1
            if outcome.status == "failed":
                break
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.SOURCE_BINDING_MISMATCH)

    def test_a_foreign_decision_key_is_refused(self) -> None:
        class ForeignKeySource:
            digest = empty_source().digest

            def action_for(self, *, cards, betting, decision):
                foreign_cards = OneSeatCardState.preflop(
                    controlled_seat=cards.controlled_seat, private_hand=(4, 17)
                )
                key = BlueprintDecisionKey.from_state(
                    cards=foreign_cards, betting=betting, decision=decision
                )
                return BlueprintSelection(
                    key=key,
                    action=passive_blueprint_action(decision),
                    table_hit=False,
                    source_digest=self.digest,
                )

        runtime = HandRuntime(
            blueprint=ForeignKeySource(), mailbox=ActionMailbox(), clock=StepClock()
        )
        runtime.dispatch(started())
        index = 1
        outcome = None
        for seat in (3, 4, 5, 0):
            outcome = runtime.dispatch(opponent(index, seat, "fold"))
            index += 1
            if outcome.status == "failed":
                break
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.SOURCE_BINDING_MISMATCH)

    def test_the_real_source_still_answers_normally(self) -> None:
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=StepClock()
        )
        drive_to_flop(runtime)
        self.assertFalse(runtime.betting_terminal)


class F4ClockContainmentTests(unittest.TestCase):
    """Clock faults are typed failures that keep an established start."""

    def test_a_fault_at_ledger_construction_is_typed(self) -> None:
        clock = StepClock()
        clock.fail_at(1, ValueError("clock exploded"))
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        outcome = runtime.dispatch(started())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.CLOCK_INVALID)
        self.assertIsNone(outcome.failure.timing)

    def test_an_os_error_from_the_clock_is_normalized(self) -> None:
        clock = StepClock()
        clock.fail_at(2, OSError("no monotonic source"))
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        outcome = runtime.dispatch(started())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.CLOCK_INVALID)

    def test_a_fault_after_the_boundary_keeps_the_established_start(self) -> None:
        clock = StepClock()
        clock.fail_at(3, ValueError("clock exploded"))
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        outcome = runtime.dispatch(started())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.CLOCK_INVALID)
        timing = outcome.failure.timing
        self.assertIsNotNone(timing, "a valid boundary had already established the start")
        self.assertIs(timing.status, TimingStatus.INTERRUPTED)
        self.assertGreaterEqual(timing.last_valid_observation_ns, timing.wall_start_ns)

    def test_no_clock_error_escapes_dispatch(self) -> None:
        for read in range(1, 8):
            with self.subTest(read=read):
                clock = StepClock()
                clock.fail_at(read, ValueError("clock exploded"))
                runtime = HandRuntime(
                    blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
                )
                outcome = runtime.dispatch(started())
                self.assertIn(outcome.status, ("accepted", "decided", "failed"))


class F5F6DeliveryTests(unittest.TestCase):
    """Publication outcomes are established by acknowledgement, not exception class."""

    def drive_until_decision(self, mailbox, clock=None):
        runtime = HandRuntime(
            blueprint=empty_source(),
            mailbox=mailbox,
            clock=StepClock() if clock is None else clock,
        )
        runtime.dispatch(started())
        index = 1
        outcome = None
        for seat in (3, 4, 5, 0):
            outcome = runtime.dispatch(opponent(index, seat, "fold"))
            index += 1
            if outcome.status in ("failed", "decided"):
                return runtime, outcome
        return runtime, outcome

    def test_a_clock_fault_after_real_acceptance_is_unknown_not_unattempted(self) -> None:
        real = ActionMailbox()

        class ClockFaultingMailbox:
            def deliver(self, envelope):
                real.deliver(envelope)
                raise ClockInvalidError("clock died inside delivery")

        runtime, outcome = self.drive_until_decision(ClockFaultingMailbox())
        self.assertEqual(outcome.status, "failed")
        self.assertEqual(len(real.accepted), 1, "the real mailbox did accept")
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.UNKNOWN)
        self.assertIsNot(outcome.failure.delivery_status, DeliveryStatus.NOT_ATTEMPTED)

    def test_a_missing_acknowledgement_fails_closed(self) -> None:
        class SilentMailbox:
            def deliver(self, envelope):
                return None

        runtime, outcome = self.drive_until_decision(SilentMailbox())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.DELIVERY_AMBIGUOUS)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.UNKNOWN)
        self.assertIsNone(outcome.failure.delivered_action)

    def test_a_mismatched_acknowledgement_fails_closed(self) -> None:
        real = ActionMailbox()

        class WrongReceiptMailbox:
            def deliver(self, envelope):
                real.deliver(envelope)
                return DeliveryReceipt(hand_id="some-other-hand", action_index=99)

        runtime, outcome = self.drive_until_decision(WrongReceiptMailbox())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.DELIVERY_AMBIGUOUS)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.UNKNOWN)

    def test_a_matching_acknowledgement_succeeds(self) -> None:
        real = ActionMailbox()
        runtime, outcome = self.drive_until_decision(real)
        self.assertEqual(outcome.status, "decided")
        self.assertEqual(len(real.accepted), 1)


class F7RetainedViolationTests(unittest.TestCase):
    """An established cutoff or deadline survives a later clock failure."""

    def test_a_known_cutoff_is_retained_through_interruption(self) -> None:
        clock = StepClock()
        real = ActionMailbox()

        class SlowSource:
            def __init__(self, inner) -> None:
                self._inner = inner

            @property
            def digest(self) -> str:
                return self._inner.digest

            def action_for(self, **kwargs):
                clock.jump(14 * NANOS + 1)
                return self._inner.action_for(**kwargs)

        class PoisoningMailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                clock.fail_at(clock.reads + 1, ValueError("clock died after acceptance"))
                return receipt

        runtime = HandRuntime(
            blueprint=SlowSource(empty_source()),
            mailbox=PoisoningMailbox(),
            clock=clock,
        )
        runtime.dispatch(started())
        index = 1
        outcome = None
        for seat in (3, 4, 5, 0):
            outcome = runtime.dispatch(opponent(index, seat, "fold"))
            index += 1
            if outcome.status == "failed":
                break
        if outcome.status != "failed":
            outcome = runtime.dispatch(opponent(index, 1, "call"))

        self.assertEqual(outcome.status, "failed")
        record = outcome.decision
        self.assertIsNotNone(record, "an accepted delivery retains its decision record")
        self.assertIs(record.timing.status, TimingStatus.INTERRUPTED)
        self.assertIs(
            record.timing.work_cutoff_crossed,
            True,
            "a cutoff established by a valid snapshot must not be erased",
        )


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
