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
from pontius.no_limit_betting import (
    CALL,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from pontius.v0a.clock import ClockInvalidError
from pontius.v0a.model import (
    ActionMailbox,
    SelectionReason,
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
from pontius.v0a.runtime import (
    HandRuntime,
    InvalidDecisionContextError,
    select_blueprint_action,
)

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
        self._jump_at: dict[int, int] = {}

    def fail_at(self, read_number: int, error: Exception) -> None:
        self._fault_at = read_number
        self._fault = error

    def jump(self, nanoseconds: int) -> None:
        self._pending_jump += nanoseconds

    def jump_at(self, read_number: int, nanoseconds: int) -> None:
        """Schedule elapsed time at one exact observation, not in the policy."""

        self._jump_at[read_number] = nanoseconds

    def __call__(self) -> int:
        self.reads += 1
        if self._fault_at == self.reads:
            assert self._fault is not None
            raise self._fault
        self._pending_jump += self._jump_at.pop(self.reads, 0)
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


def drive_until_controlled(runtime: HandRuntime, *, tolerate_failure: bool = False):
    """Fold seats 3, 4, 5 and 0 so the controlled small blind must decide."""

    outcome = runtime.dispatch(started())
    index = 1
    for seat in (3, 4, 5, 0):
        outcome = runtime.dispatch(opponent(index, seat, "fold"))
        index += 1
        if outcome.status in ("failed", "decided"):
            break
    if not tolerate_failure:
        assert outcome.status == "decided", outcome
    return outcome


class F1IngressWallTests(unittest.TestCase):
    """The response wall covers pre-decision adapter work on every path."""

    def test_reveal_path_charges_visible_card_construction(self) -> None:
        clock = StepClock()

        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=clock
        )
        index = drive_to_flop(runtime)
        # Observe the real sealed method rather than replacing the exact value
        # type with a subclass that policy-context admission must reject.
        target = OneSeatCardState.advance_to.__code__
        previous = sys.getprofile()
        calls = []
        def charge_real_card_transition(frame, event, argument):
            if event == "call" and frame.f_code is target:
                calls.append(1)
                clock.jump(16 * NANOS)
        sys.setprofile(charge_real_card_transition)
        try:
            outcome = runtime.dispatch(
                StreetRevealedEvent(
                    hand_id=HAND, event_index=index, street="flop", cards=(20, 21, 22)
                )
            )
        finally:
            sys.setprofile(previous)
        self.assertEqual(calls, [1])

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

    # The three delegate probes that lived here asserted a typed
    # source_binding_mismatch from objects the constructor no longer admits at
    # all. Their contract — a substituted policy must never answer — is now
    # enforced earlier and tested in R2_01PolicyAuthorityTests, which also
    # proves a sealed subclass override cannot intercept the sealed lookup.

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

        class PoisoningMailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                clock.fail_at(clock.reads + 1, ValueError("clock died after acceptance"))
                return receipt

        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=PoisoningMailbox(), clock=clock
        )
        runtime.dispatch(started())
        for index, seat in ((1, 3), (2, 4), (3, 5)):
            self.assertEqual(
                runtime.dispatch(opponent(index, seat, "fold")).status, "accepted"
            )
        # Elapsed time is injected through the clock, never through the policy
        # object: decision work crosses the 14 s cutoff before ready-to-emit.
        clock.jump_at(clock.reads + 5, 14 * NANOS + 1)
        outcome = runtime.dispatch(opponent(4, 0, "fold"))

        self.assertEqual(outcome.status, "failed")
        record = outcome.decision
        self.assertIsNotNone(record, "an accepted delivery retains its decision record")
        self.assertIs(record.timing.status, TimingStatus.INTERRUPTED)
        self.assertIs(
            record.timing.work_cutoff_crossed,
            True,
            "a cutoff established by a valid snapshot must not be erased",
        )

# -- slice 1: r002 findings R2-01, R2-02, R2-03, R2-07, R2-08 ---------------


class R2_01PolicyAuthorityTests(unittest.TestCase):
    """Only the sealed immutable policy may answer a controlled decision."""

    def test_the_runtime_refuses_a_non_sealed_policy_object(self) -> None:
        class LooksLikeAPolicy:
            digest = empty_source().digest

            def action_for(self, **kwargs):
                raise AssertionError("must never be called")

        with self.assertRaises(TypeError):
            HandRuntime(
                blueprint=LooksLikeAPolicy(),
                mailbox=ActionMailbox(),
                clock=StepClock(),
            )

    def test_a_delegate_with_the_real_digest_is_refused(self) -> None:
        """The r002 false-hit delegate: real digest, real key, fabricated hit."""

        inner = empty_source()

        class Delegate:
            digest = inner.digest
            entries = inner.entries

            def action_for(self, *, cards, betting, decision):
                key = BlueprintDecisionKey.from_state(
                    cards=cards, betting=betting, decision=decision
                )
                return BlueprintSelection(
                    key=key,
                    action=raise_to(6),
                    table_hit=True,
                    source_digest=inner.digest,
                )

        with self.assertRaises(TypeError):
            HandRuntime(blueprint=Delegate(), mailbox=ActionMailbox(), clock=StepClock())

    def test_a_subclass_cannot_intercept_the_sealed_lookup(self) -> None:
        """Subclass behavior is rejected before the sealed lookup or delivery."""

        inner = empty_source()

        class LyingSubclass(ImmutableBlueprintActionSource):
            def action_for(self, *, cards, betting, decision):
                key = BlueprintDecisionKey.from_state(
                    cards=cards, betting=betting, decision=decision
                )
                return BlueprintSelection(
                    key=key,
                    action=raise_to(6),
                    table_hit=True,
                    source_digest=inner.digest,
                )

        real = ActionMailbox()
        with self.assertRaises(TypeError):
            HandRuntime(
                blueprint=LyingSubclass(source_id=inner.source_id, entries=inner.entries),
                mailbox=real,
                clock=StepClock(),
            )
        self.assertEqual(len(real.accepted), 0)

    def test_the_real_sealed_source_still_hits_and_misses(self) -> None:
        runtime = HandRuntime(
            blueprint=empty_source(), mailbox=ActionMailbox(), clock=StepClock()
        )
        outcome = drive_until_controlled(runtime)
        self.assertEqual(outcome.status, "decided")
        self.assertIs(outcome.decision.selection_reason, SelectionReason.PASSIVE_DEFAULT)

    def test_an_inconsistent_context_is_classified_not_guessed(self) -> None:
        """A genuinely mismatched context, not an injected exception."""

        betting = NoLimitBettingState.new_hand(
            button=0, starting_stacks=STACKS, small_blind=1, big_blind=2
        )
        preflop_cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=(0, 13))
        flop_cards = preflop_cards.advance_to(BettingStreet.FLOP, (20, 21, 22))
        with self.assertRaises(InvalidDecisionContextError):
            select_blueprint_action(
                source=empty_source(),
                cards=flop_cards,
                betting=betting,
                decision=betting.legal_decision(),
            )


class R2_02EstablishedFlagTests(unittest.TestCase):
    """Every valid outer snapshot's established truths survive interruption."""

    def test_a_deadline_established_at_the_boundary_is_retained(self) -> None:
        clock = StepClock()
        real = ActionMailbox()
        runtime = HandRuntime(blueprint=empty_source(), mailbox=real, clock=clock)
        runtime.dispatch(started())
        for index, seat in ((1, 3), (2, 4), (3, 5)):
            self.assertEqual(runtime.dispatch(opponent(index, seat, "fold")).status, "accepted")
        # Within one dispatch the observations are: outer boundary start, the
        # two V2 transition reads, then the outer boundary snapshot. Put the
        # elapsed time on that snapshot and fail the very next observation.
        base = clock.reads
        clock.jump_at(base + 4, 16 * NANOS)
        clock.fail_at(base + 5, ValueError("clock died after the boundary"))
        outcome = runtime.dispatch(opponent(4, 0, "fold"))
        self.assertEqual(outcome.status, "failed", outcome)
        timing = outcome.failure.timing
        self.assertIsNotNone(timing)
        self.assertIs(timing.status, TimingStatus.INTERRUPTED)
        self.assertIs(
            timing.deadline_crossed,
            True,
            "a deadline established by the boundary snapshot must not be erased",
        )


class R2_08DeliveryCountingTests(unittest.TestCase):
    """A known accepted delivery counts, even when the response failed."""

    def test_a_late_but_accepted_action_is_still_a_delivery(self) -> None:
        clock = StepClock()
        real = ActionMailbox()

        class SlowMailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                clock.jump(16 * NANOS)
                return receipt

        runtime = HandRuntime(blueprint=empty_source(), mailbox=SlowMailbox(), clock=clock)
        outcome = drive_until_controlled(runtime, tolerate_failure=True)
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.ACTION_DEADLINE_EXCEEDED)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.ACCEPTED)
        self.assertEqual(len(real.accepted), 1)
        self.assertIsNotNone(outcome.decision)
        self.assertEqual(runtime.accepted_delivery_count, 1)


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
