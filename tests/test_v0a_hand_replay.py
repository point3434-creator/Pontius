"""Slice-A contract tests for the blueprint-only v0a hand runtime (ADR-0485)."""

from __future__ import annotations

import sys
import unittest

from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from pontius.holdem_cards import OneSeatCardState
from pontius.legal_decision_spine_v2 import public_betting_state_sha256
from pontius.no_limit_betting import (
    CALL,
    FOLD,
    NoLimitBettingState,
    raise_to,
)
from pontius.v0a.clock import ClockInvalidError, ClockReversedError, MonotonicWitness
from pontius.v0a.model import (
    ActionEnvelope,
    ActionMailbox,
    DeliveryStatus,
    FailureCode,
    HandAction,
    HandStartedEvent,
    MailboxRejectionError,
    OpponentActionEvent,
    SelectionReason,
    ShowdownResultEvent,
    StreetRevealedEvent,
    TimingStatus,
)
from pontius.v0a.runtime import HandRuntime, select_blueprint_action

HAND = "hand-A"
STACKS = (200, 200, 200, 200, 200, 200)
NANOS = 1_000_000_000
WALL_NS = 15 * NANOS
CUTOFF_NS = 14 * NANOS


class ScriptedClock:
    """Deterministic frozen monotonic-ns source; tests advance it explicitly."""

    def __init__(self, start: int = 1_000) -> None:
        self.now = start
        self._fault: str | None = None
        self.reads = 0
        self._jump_at: dict[int, int] = {}
        self._fault_at: dict[int, str] = {}

    def jump_at(self, read_number: int, nanoseconds: int) -> None:
        """Schedule elapsed time at one exact observation."""

        self._jump_at[read_number] = nanoseconds

    def advance(self, delta_ns: int) -> None:
        self.now += delta_ns

    def fail_next(self, kind: str) -> None:
        self._fault = kind

    def fail_at(self, read_number: int, kind: str) -> None:
        self._fault_at[read_number] = kind

    def __call__(self) -> int:
        self.reads += 1
        self.now += self._jump_at.pop(self.reads, 0)
        scheduled = self._fault_at.pop(self.reads, None)
        if scheduled is not None:
            self._fault = scheduled
        if self._fault == "invalid":
            self._fault = None
            return True
        if self._fault == "reversed":
            self._fault = None
            self.now -= 7
            return self.now
        return self.now


class TickingClock:
    """Advances on every observation and records the exact read sequence."""

    def __init__(self, start: int = 1_000, step: int = 1_000_000) -> None:
        self.now = start
        self.step = step
        self.reads: list[int] = []

    def __call__(self) -> int:
        value = self.now
        self.reads.append(value)
        self.now += self.step
        return value


def decide_with_delay(
    *,
    blueprint,
    mailbox,
    clock,
    decision_jump_ns: int = 0,
):
    """Run one controlled decision with elapsed time injected at the clock.

    The controlled seat is the first preflop actor, so the hand-start dispatch
    itself produces the decision. Observation 8 falls inside decision work,
    between the response wall opening and the ready-to-emit checkpoint.
    """

    if decision_jump_ns:
        clock.jump_at(8, decision_jump_ns)
    runtime = HandRuntime(blueprint=blueprint, mailbox=mailbox, clock=clock)
    return runtime, runtime.dispatch(hand_started())


class DelayingMailbox:
    """Real mailbox plus a deterministic clock jump inside delivery."""

    def __init__(self, mailbox: ActionMailbox, clock: ScriptedClock, jump_ns: int):
        self._mailbox = mailbox
        self._clock = clock
        self._jump_ns = jump_ns

    def deliver(self, envelope):
        self._clock.advance(self._jump_ns)
        return self._mailbox.deliver(envelope)


class RejectingMailbox:
    def __init__(self, mailbox: ActionMailbox) -> None:
        self._mailbox = mailbox

    def deliver(self, envelope):
        raise MailboxRejectionError("scheduled rejection before acceptance")


class AmbiguousMailbox:
    def __init__(self, mailbox: ActionMailbox) -> None:
        self._mailbox = mailbox

    def deliver(self, envelope):
        self._mailbox.deliver(envelope)
        raise OSError("scheduled ambiguity after publication")


class ClockKillingMailbox:
    """Accept for real, then poison the witness before the closing observation."""

    def __init__(self, mailbox: ActionMailbox, clock: ScriptedClock, kind: str) -> None:
        self._mailbox = mailbox
        self._clock = clock
        self._kind = kind

    def deliver(self, envelope):
        receipt = self._mailbox.deliver(envelope)
        self._clock.fail_next(self._kind)
        return receipt


def hand_started(**overrides) -> HandStartedEvent:
    fields = {
        "hand_id": HAND,
        "event_index": 0,
        "button": 0,
        "controlled_seat": 3,
        "starting_stacks": STACKS,
        "small_blind": 1,
        "big_blind": 2,
        "private_cards": (0, 13),
    }
    fields.update(overrides)
    return HandStartedEvent(**fields)


def opponent(
    index: int,
    seat: int,
    action: HandAction,
    street: str = "preflop",
) -> OpponentActionEvent:
    return OpponentActionEvent(
        hand_id=HAND,
        event_index=index,
        street=street,
        seat=seat,
        action=action,
    )


def fold_action() -> HandAction:
    return HandAction(kind="fold", raise_to=None)


def call_action() -> HandAction:
    return HandAction(kind="call", raise_to=None)


def utg_context() -> tuple[OneSeatCardState, NoLimitBettingState]:
    betting = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=STACKS,
        small_blind=1,
        big_blind=2,
    )
    cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=(0, 13))
    return cards, betting


def utg_blueprint(action) -> ImmutableBlueprintActionSource:
    cards, betting = utg_context()
    key = BlueprintDecisionKey.from_state(
        cards=cards,
        betting=betting,
        decision=betting.legal_decision(),
    )
    return ImmutableBlueprintActionSource(
        source_id="v0a-test-blueprint",
        entries=(BlueprintActionEntry(key=key, action=action),),
    )


def empty_blueprint() -> ImmutableBlueprintActionSource:
    return ImmutableBlueprintActionSource(source_id="v0a-test-empty")


def new_runtime(blueprint, mailbox=None, clock=None):
    return HandRuntime(
        blueprint=blueprint,
        mailbox=ActionMailbox() if mailbox is None else mailbox,
        clock=ScriptedClock() if clock is None else clock,
    )


class EventValueContractTests(unittest.TestCase):
    """Model-level exact validation from the frozen event table."""

    def test_rejects_malformed_event_values(self) -> None:
        cases = [
            ("bool index", lambda: hand_started(event_index=False)),
            ("nonzero start index", lambda: hand_started(event_index=1)),
            ("empty hand id", lambda: hand_started(hand_id="")),
            ("non ascii hand id", lambda: hand_started(hand_id="hand-é")),
            ("bool seat", lambda: hand_started(controlled_seat=True)),
            ("descending pair", lambda: hand_started(private_cards=(13, 0))),
            ("duplicate pair", lambda: hand_started(private_cards=(13, 13))),
            ("card out of range", lambda: hand_started(private_cards=(0, 52))),
            ("bool card", lambda: hand_started(private_cards=(True, 13))),
            ("five stacks", lambda: hand_started(starting_stacks=STACKS[:5])),
            ("float blind", lambda: hand_started(small_blind=1.0)),
            ("blind order", lambda: hand_started(small_blind=2, big_blind=2)),
            ("raise without amount", lambda: HandAction(kind="raise", raise_to=None)),
            ("check with amount", lambda: HandAction(kind="check", raise_to=4)),
            ("bool raise amount", lambda: HandAction(kind="raise", raise_to=True)),
            ("zero raise amount", lambda: HandAction(kind="raise", raise_to=0)),
            ("unknown kind", lambda: HandAction(kind="bet", raise_to=4)),
            ("negative index", lambda: opponent(-1, 4, fold_action())),
            ("bad street", lambda: opponent(1, 4, fold_action(), street="flop2")),
            (
                "flop reveals two cards",
                lambda: StreetRevealedEvent(
                    hand_id=HAND, event_index=5, street="flop", cards=(20, 21)
                ),
            ),
            (
                "turn reveals two cards",
                lambda: StreetRevealedEvent(
                    hand_id=HAND, event_index=6, street="turn", cards=(30, 31)
                ),
            ),
            (
                "duplicate reveal",
                lambda: StreetRevealedEvent(
                    hand_id=HAND, event_index=5, street="flop", cards=(20, 20, 21)
                ),
            ),
            (
                "five strengths",
                lambda: ShowdownResultEvent(
                    hand_id=HAND, event_index=9, strengths=(1, 2, 3, 4, 5)
                ),
            ),
            (
                "bool strength",
                lambda: ShowdownResultEvent(
                    hand_id=HAND,
                    event_index=9,
                    strengths=(True, 2, 3, 4, 5, 6),
                ),
            ),
        ]
        for label, build in cases:
            with self.subTest(label):
                with self.assertRaises((TypeError, ValueError)):
                    build()

    def test_events_cannot_carry_a_clock_timestamp(self) -> None:
        for build in (
            lambda: hand_started(timestamp_ns=5),
            lambda: OpponentActionEvent(
                hand_id=HAND,
                event_index=1,
                street="preflop",
                seat=4,
                action=fold_action(),
                timestamp_ns=5,
            ),
        ):
            with self.assertRaises(TypeError):
                build()

    def test_envelope_and_mailbox_accept_at_most_once(self) -> None:
        envelope = ActionEnvelope(
            hand_id=HAND,
            action_index=1,
            seat=3,
            street="preflop",
            action=call_action(),
        )
        mailbox = ActionMailbox()
        receipt = mailbox.deliver(envelope)
        self.assertEqual(receipt.hand_id, HAND)
        self.assertEqual(receipt.action_index, 1)
        with self.assertRaises(MailboxRejectionError):
            mailbox.deliver(envelope)


class WitnessContractTests(unittest.TestCase):
    """One validated monotonic witness; poisoned permanently on failure."""

    def test_witness_retains_last_returned_sample(self) -> None:
        clock = ScriptedClock(start=50)
        witness = MonotonicWitness(clock)
        self.assertEqual(witness(), 50)
        clock.advance(25)
        self.assertEqual(witness(), 75)
        self.assertEqual(witness.last_returned_ns, 75)
        self.assertEqual(witness(), 75)

    def test_witness_rejects_invalid_values_and_stays_failed(self) -> None:
        for fault, error in (("invalid", ClockInvalidError), ("reversed", ClockReversedError)):
            with self.subTest(fault):
                clock = ScriptedClock(start=100)
                witness = MonotonicWitness(clock)
                witness()
                clock.fail_next(fault)
                with self.assertRaises(error):
                    witness()
                self.assertEqual(witness.last_returned_ns, 100)
                with self.assertRaises(ClockInvalidError):
                    witness()


class EventOrderContractTests(unittest.TestCase):
    """Runtime-level fail-closed ordering from the frozen event table."""

    def start(self, controlled_seat: int = 5):
        clock = ScriptedClock()
        runtime = new_runtime(empty_blueprint(), clock=clock)
        outcome = runtime.dispatch(hand_started(controlled_seat=controlled_seat))
        self.assertIn(outcome.status, ("accepted", "decided"))
        return runtime

    def assert_failed(self, outcome, code: FailureCode) -> None:
        self.assertEqual(outcome.status, "failed")
        self.assertIsNotNone(outcome.failure)
        self.assertIs(outcome.failure.code, code)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.NOT_ATTEMPTED)
        self.assertIsNone(outcome.failure.delivered_action)

    def test_first_event_must_be_hand_started(self) -> None:
        runtime = new_runtime(empty_blueprint())
        outcome = runtime.dispatch(opponent(1, 3, fold_action()))
        self.assert_failed(outcome, FailureCode.EVENT_ORDER)

    def test_second_hand_started_is_rejected(self) -> None:
        runtime = self.start()
        outcome = runtime.dispatch(hand_started(controlled_seat=5))
        self.assert_failed(outcome, FailureCode.EVENT_ORDER)

    def test_wrong_hand_id_is_rejected(self) -> None:
        runtime = self.start()
        bad = OpponentActionEvent(
            hand_id="hand-B",
            event_index=1,
            street="preflop",
            seat=3,
            action=fold_action(),
        )
        self.assert_failed(runtime.dispatch(bad), FailureCode.EVENT_ORDER)

    def test_skipped_and_repeated_event_indices_are_rejected(self) -> None:
        runtime = self.start()
        self.assert_failed(
            runtime.dispatch(opponent(3, 3, fold_action())),
            FailureCode.EVENT_ORDER,
        )
        runtime = self.start()
        outcome = runtime.dispatch(opponent(1, 3, fold_action()))
        self.assertEqual(outcome.status, "accepted")
        self.assert_failed(
            runtime.dispatch(opponent(1, 4, fold_action())),
            FailureCode.EVENT_ORDER,
        )

    def test_wrong_actor_and_controlled_actor_are_rejected(self) -> None:
        runtime = self.start()
        self.assert_failed(
            runtime.dispatch(opponent(1, 4, fold_action())),
            FailureCode.EVENT_ORDER,
        )
        # An opponent event naming the controlled seat is rejected too. The
        # controlled seat is never pending between dispatches (its decision
        # runs inline), so this currently coincides with the wrong-actor
        # rejection; the guard is retained as defence in depth.
        runtime = self.start(controlled_seat=3)
        self.assert_failed(
            runtime.dispatch(opponent(1, 3, fold_action())),
            FailureCode.EVENT_ORDER,
        )

    def test_wrong_street_and_premature_reveal_are_rejected(self) -> None:
        runtime = self.start()
        self.assert_failed(
            runtime.dispatch(opponent(1, 3, fold_action(), street="flop")),
            FailureCode.EVENT_ORDER,
        )
        runtime = self.start()
        reveal = StreetRevealedEvent(
            hand_id=HAND, event_index=1, street="flop", cards=(20, 21, 22)
        )
        self.assert_failed(runtime.dispatch(reveal), FailureCode.EVENT_ORDER)

    def test_reveal_overlapping_known_cards_is_rejected(self) -> None:
        clock = ScriptedClock()
        runtime = new_runtime(empty_blueprint(), clock=clock)
        runtime.dispatch(hand_started(controlled_seat=2, private_cards=(20, 33)))
        for index, seat in ((1, 3), (2, 4), (3, 5), (4, 0)):
            folded = runtime.dispatch(opponent(index, seat, fold_action()))
            self.assertEqual(folded.status, "accepted")
        decided = runtime.dispatch(opponent(5, 1, call_action()))
        self.assertEqual(decided.status, "decided")
        reveal = StreetRevealedEvent(
            hand_id=HAND, event_index=6, street="flop", cards=(20, 21, 22)
        )
        self.assert_failed(runtime.dispatch(reveal), FailureCode.INVALID_EVENT)

    def test_showdown_before_terminal_is_rejected(self) -> None:
        runtime = self.start()
        event = ShowdownResultEvent(
            hand_id=HAND,
            event_index=1,
            strengths=(1, 1, 1, 1, 1, 1),
        )
        self.assert_failed(runtime.dispatch(event), FailureCode.EVENT_ORDER)

    def test_fold_terminal_accepts_no_showdown_and_settles_bare(self) -> None:
        runtime = self.start(controlled_seat=2)
        for index, seat in ((1, 3), (2, 4), (3, 5), (4, 0)):
            folded = runtime.dispatch(opponent(index, seat, fold_action()))
            self.assertEqual(folded.status, "accepted")
        outcome = runtime.dispatch(opponent(5, 1, fold_action()))
        self.assertEqual(outcome.status, "accepted")
        self.assertTrue(runtime.betting_terminal)
        event = ShowdownResultEvent(
            hand_id=HAND, event_index=6, strengths=(1, 1, 1, 1, 1, 1)
        )
        self.assert_failed(runtime.dispatch(event), FailureCode.EVENT_ORDER)
        runtime = self.start(controlled_seat=2)
        for index, seat in ((1, 3), (2, 4), (3, 5), (4, 0), (5, 1)):
            runtime.dispatch(opponent(index, seat, fold_action()))
        settlement = runtime.settle()
        self.assertEqual(settlement.final_stacks[2], 201)
        self.assertEqual(sum(settlement.final_stacks), sum(STACKS))

    def test_illegal_opponent_action_fails_closed(self) -> None:
        runtime = self.start()
        outcome = runtime.dispatch(opponent(1, 3, HandAction(kind="check", raise_to=None)))
        self.assert_failed(outcome, FailureCode.INVALID_EVENT)


class BlueprintOutcomeTests(unittest.TestCase):
    """The exact ADR-0485 outcome split for controlled decisions."""

    def decide_utg(self, blueprint, mailbox=None, clock=None):
        clock = ScriptedClock() if clock is None else clock
        mailbox = ActionMailbox() if mailbox is None else mailbox
        runtime = HandRuntime(blueprint=blueprint, mailbox=mailbox, clock=clock)
        outcome = runtime.dispatch(hand_started())
        return runtime, outcome

    def test_table_hit_emits_the_entry_action(self) -> None:
        mailbox = ActionMailbox()
        runtime, outcome = self.decide_utg(utg_blueprint(raise_to(6)), mailbox=mailbox)
        self.assertEqual(outcome.status, "decided")
        record = outcome.decision
        self.assertIs(record.selection_reason, SelectionReason.TABLE_HIT)
        self.assertEqual(record.selected_action, HandAction(kind="raise", raise_to=6))
        self.assertEqual(record.spine_reason, "no_candidate")
        self.assertIsNone(record.failure_reason)
        self.assertEqual(record.action_index, 1)
        self.assertEqual(record.street_action_index, 1)
        self.assertEqual(record.seat, 3)
        self.assertEqual(record.street, "preflop")
        self.assertEqual(len(mailbox.accepted), 1)

    def test_missing_match_selects_passive_default_call(self) -> None:
        mailbox = ActionMailbox()
        runtime, outcome = self.decide_utg(empty_blueprint(), mailbox=mailbox)
        self.assertEqual(outcome.status, "decided")
        record = outcome.decision
        self.assertIs(record.selection_reason, SelectionReason.PASSIVE_DEFAULT)
        self.assertEqual(record.selected_action, call_action())
        self.assertIsNone(record.failure_reason)

    def test_missing_match_selects_check_when_available(self) -> None:
        clock = ScriptedClock()
        mailbox = ActionMailbox()
        runtime = HandRuntime(blueprint=empty_blueprint(), mailbox=mailbox, clock=clock)
        runtime.dispatch(hand_started(controlled_seat=2))
        for index, seat in ((1, 3), (2, 4), (3, 5), (4, 0)):
            runtime.dispatch(opponent(index, seat, fold_action()))
        outcome = runtime.dispatch(opponent(5, 1, call_action()))
        self.assertEqual(outcome.status, "decided")
        self.assertEqual(outcome.decision.selected_action, HandAction(kind="check", raise_to=None))
        self.assertIs(outcome.decision.selection_reason, SelectionReason.PASSIVE_DEFAULT)

    def test_illegal_matching_entry_fails_typed_with_no_emission(self) -> None:
        mailbox = ActionMailbox()
        runtime, outcome = self.decide_utg(utg_blueprint(raise_to(1_000)), mailbox=mailbox)
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.INVALID_BLUEPRINT_ENTRY)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.NOT_ATTEMPTED)
        self.assertIsNone(outcome.failure.delivered_action)
        self.assertIsNone(outcome.decision)
        self.assertEqual(len(mailbox.accepted), 0)
        self.assertIs(outcome.failure.timing.status, TimingStatus.INTERRUPTED)

    def test_entry_for_another_state_is_a_miss_not_a_failure(self) -> None:
        cards, betting = utg_context()
        after_call = betting.apply_action(CALL)
        key = BlueprintDecisionKey.from_state(
            cards=OneSeatCardState.preflop(controlled_seat=4, private_hand=(1, 14)),
            betting=after_call,
            decision=after_call.legal_decision(),
        )
        blueprint = ImmutableBlueprintActionSource(
            source_id="v0a-other-state",
            entries=(BlueprintActionEntry(key=key, action=CALL),),
        )
        runtime, outcome = self.decide_utg(blueprint)
        self.assertEqual(outcome.status, "decided")
        self.assertIs(outcome.decision.selection_reason, SelectionReason.PASSIVE_DEFAULT)

    # The invalid-decision-context probe that lived here injected a ValueError
    # from a delegate the constructor no longer admits. A genuinely
    # inconsistent context is exercised directly against select_blueprint_action
    # in tests/test_v0a_contract_faults.py.

    def test_policy_selection_surface_is_exactly_four_inputs(self) -> None:
        import inspect

        import pontius.v0a.runtime as runtime_module
        for selector in (select_blueprint_action, runtime_module._select_admitted_blueprint_action):
            parameters = inspect.signature(selector).parameters
            self.assertEqual(tuple(parameters), ("source", "cards", "betting", "decision"))
        import pontius.v0a.model as model
        import pontius.v0a.clock as clockmod
        import pontius.v0a.runtime as runtimemod

        for module in (model, clockmod, runtimemod):
            source_text = inspect.getsource(module)
            self.assertNotIn("SixSeatHoldemDeal", source_text)
            self.assertNotIn("import pontius.river", source_text)
            self.assertNotIn("from pontius.river", source_text)
            self.assertNotIn("from .replay", source_text)


class ActionClockContractTests(unittest.TestCase):
    """Outer-wall semantics: event-boundary start, edges, and equality."""

    def test_wall_starts_at_the_event_boundary(self) -> None:
        clock = ScriptedClock(start=5_000)
        runtime, outcome = decide_with_delay(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=ActionMailbox(),
            clock=clock,
            decision_jump_ns=3 * NANOS,
        )
        record = outcome.decision
        self.assertEqual(record.timing.wall_start_ns, 5_000)
        self.assertEqual(record.timing.elapsed_ns, 3 * NANOS)
        self.assertIs(record.timing.status, TimingStatus.COMPLETED)

    def test_a_late_started_wall_is_detectable(self) -> None:
        """Time spent in validation and transition work is inside the wall."""

        clock = TickingClock(start=1_000, step=1_000_000)
        runtime = HandRuntime(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=ActionMailbox(),
            clock=clock,
        )
        record = runtime.dispatch(hand_started()).decision
        timing = record.timing
        # The wall is pinned to the ledger's own event-arrival observation:
        # the second read of the dispatch (ledger construction, then boundary).
        self.assertEqual(timing.wall_start_ns, clock.reads[1])
        self.assertEqual(timing.emission_observed_ns, clock.reads[-1])
        self.assertEqual(timing.elapsed_ns, clock.reads[-1] - clock.reads[1])
        # Substantial pre-decision work is charged to the wall, so a wall
        # started at the decision instead of the event boundary is shorter.
        self.assertGreaterEqual(len(clock.reads), 10)
        self.assertGreaterEqual(timing.elapsed_ns, 9 * clock.step)

    def test_recorded_elapsed_matches_ledger_snapshot_exactly(self) -> None:
        clock = ScriptedClock(start=77)
        runtime, outcome = decide_with_delay(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=ActionMailbox(),
            clock=clock,
            decision_jump_ns=1_234_567_891,
        )
        record = outcome.decision
        timing = record.timing
        self.assertEqual(
            (timing.emission_observed_ns - timing.wall_start_ns) / NANOS,
            timing.elapsed_ns / NANOS,
        )
        self.assertEqual(timing.last_valid_observation_ns, timing.emission_observed_ns)
        self.assertEqual(timing.elapsed_ns, 1_234_567_891)
        self.assertGreaterEqual(timing.response_compute_seconds, 0.0)
        self.assertGreaterEqual(timing.response_uninstrumented_seconds, 0.0)

    def test_work_cutoff_edges_follow_the_ledger(self) -> None:
        for jump, crossed in (
            (CUTOFF_NS - 1, False),
            (CUTOFF_NS, True),
            (CUTOFF_NS + 1, True),
        ):
            with self.subTest(jump=jump):
                clock = ScriptedClock()
                mailbox = ActionMailbox()
                runtime, outcome = decide_with_delay(
                    blueprint=utg_blueprint(raise_to(6)),
                    mailbox=mailbox,
                    clock=clock,
                    decision_jump_ns=jump,
                )
                if not crossed:
                    self.assertEqual(outcome.status, "decided")
                    self.assertFalse(outcome.decision.timing.work_cutoff_crossed)
                    continue
                self.assertEqual(outcome.status, "failed")
                self.assertIs(outcome.failure.code, FailureCode.WORK_CUTOFF_EXCEEDED)
                self.assertIsNotNone(outcome.decision)
                record = outcome.decision
                self.assertTrue(record.timing.work_cutoff_crossed)
                self.assertFalse(record.timing.deadline_crossed)
                self.assertIs(record.failure_reason, FailureCode.WORK_CUTOFF_EXCEEDED)
                self.assertIs(outcome.failure.delivery_status, DeliveryStatus.ACCEPTED)
                self.assertEqual(outcome.failure.delivered_action, record.selected_action)
                self.assertEqual(len(mailbox.accepted), 1)

    def test_deadline_edges_follow_the_ledger(self) -> None:
        for jump, crossed in (
            (WALL_NS, False),
            (WALL_NS + 1, True),
        ):
            with self.subTest(jump=jump):
                clock = ScriptedClock()
                mailbox = ActionMailbox()
                runtime = HandRuntime(
                    blueprint=utg_blueprint(raise_to(6)),
                    mailbox=DelayingMailbox(mailbox, clock, jump),
                    clock=clock,
                )
                outcome = runtime.dispatch(hand_started())
                self.assertEqual(len(mailbox.accepted), 1)
                if not crossed:
                    self.assertEqual(outcome.status, "decided")
                    self.assertFalse(outcome.decision.timing.deadline_crossed)
                    continue
                self.assertEqual(outcome.status, "failed")
                self.assertIs(outcome.failure.code, FailureCode.ACTION_DEADLINE_EXCEEDED)
                record = outcome.decision
                self.assertTrue(record.timing.deadline_crossed)
                self.assertIs(record.failure_reason, FailureCode.ACTION_DEADLINE_EXCEEDED)
                self.assertIs(outcome.failure.delivery_status, DeliveryStatus.ACCEPTED)

    def test_reserve_between_cutoff_and_deadline_is_lawful_emission_time(self) -> None:
        clock = ScriptedClock()
        mailbox = ActionMailbox()
        runtime, outcome = decide_with_delay(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=DelayingMailbox(mailbox, clock, int(1.5 * NANOS)),
            clock=clock,
            decision_jump_ns=13 * NANOS,
        )
        self.assertEqual(outcome.status, "decided")
        timing = outcome.decision.timing
        self.assertFalse(timing.work_cutoff_crossed)
        self.assertFalse(timing.deadline_crossed)
        self.assertEqual(timing.elapsed_ns, 13 * NANOS + int(1.5 * NANOS))

    def test_cutoff_and_deadline_together_report_deadline_with_both_flags(self) -> None:
        clock = ScriptedClock()
        mailbox = ActionMailbox()
        runtime, outcome = decide_with_delay(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=DelayingMailbox(mailbox, clock, 2 * NANOS),
            clock=clock,
            decision_jump_ns=CUTOFF_NS + 5,
        )
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.ACTION_DEADLINE_EXCEEDED)
        record = outcome.decision
        self.assertTrue(record.timing.work_cutoff_crossed)
        self.assertTrue(record.timing.deadline_crossed)


class DeliveryFailureTests(unittest.TestCase):
    """Delivery and clock failures preserve exactly what is known."""

    def run_utg(self, mailbox, clock=None):
        clock = ScriptedClock() if clock is None else clock
        runtime = HandRuntime(
            blueprint=utg_blueprint(raise_to(6)), mailbox=mailbox, clock=clock
        )
        return runtime, runtime.dispatch(hand_started())

    def test_rejected_delivery_is_typed_and_never_retried(self) -> None:
        real = ActionMailbox()
        runtime, outcome = self.run_utg(RejectingMailbox(real))
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.DELIVERY_REJECTED)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.REJECTED)
        self.assertIsNone(outcome.failure.delivered_action)
        self.assertEqual(len(real.accepted), 0)
        self.assertIs(outcome.failure.timing.status, TimingStatus.INTERRUPTED)

    def test_ambiguous_delivery_is_unknown_and_never_retried(self) -> None:
        real = ActionMailbox()
        runtime, outcome = self.run_utg(AmbiguousMailbox(real))
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.DELIVERY_AMBIGUOUS)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.UNKNOWN)
        self.assertIsNone(outcome.failure.delivered_action)
        self.assertEqual(len(real.accepted), 1)

    def test_clock_failure_before_delivery_is_interrupted_without_emission(self) -> None:
        clock = ScriptedClock()
        clock.fail_at(9, "reversed")  # the ready-to-emit checkpoint
        mailbox = ActionMailbox()
        runtime = HandRuntime(
            blueprint=utg_blueprint(raise_to(6)), mailbox=mailbox, clock=clock
        )
        outcome = runtime.dispatch(hand_started())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.CLOCK_REVERSED)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.NOT_ATTEMPTED)
        self.assertEqual(len(mailbox.accepted), 0)
        timing = outcome.failure.timing
        self.assertIs(timing.status, TimingStatus.INTERRUPTED)
        self.assertIsNone(timing.emission_observed_ns)
        self.assertIsNone(timing.elapsed_ns)
        self.assertGreaterEqual(timing.last_valid_observation_ns, timing.wall_start_ns)

    def test_clock_failure_after_acceptance_keeps_the_full_decision(self) -> None:
        clock = ScriptedClock()
        real = ActionMailbox()
        runtime = HandRuntime(
            blueprint=utg_blueprint(raise_to(6)),
            mailbox=ClockKillingMailbox(real, clock, "invalid"),
            clock=clock,
        )
        outcome = runtime.dispatch(hand_started())
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.CLOCK_INVALID)
        self.assertIs(outcome.failure.delivery_status, DeliveryStatus.ACCEPTED)
        self.assertEqual(
            outcome.failure.delivered_action, HandAction(kind="raise", raise_to=6)
        )
        self.assertEqual(len(real.accepted), 1)
        record = outcome.decision
        self.assertIsNotNone(record)
        self.assertIs(record.timing.status, TimingStatus.INTERRUPTED)
        self.assertIsNone(record.timing.emission_observed_ns)
        self.assertIsNone(record.timing.work_cutoff_crossed)
        self.assertIsNone(record.timing.deadline_crossed)
        self.assertEqual(record.timing, outcome.failure.timing)


class RepeatedActionAndRecordTests(unittest.TestCase):
    """Fresh walls per controlled action; exact record bindings."""

    def test_two_controlled_actions_get_fresh_walls_and_indices(self) -> None:
        cards, betting = utg_context()
        first_key = BlueprintDecisionKey.from_state(
            cards=cards, betting=betting, decision=betting.legal_decision()
        )
        after = betting.apply_action(raise_to(6))
        after = after.apply_action(raise_to(18))
        for _ in range(4):
            after = after.apply_action(FOLD)
        second_key = BlueprintDecisionKey.from_state(
            cards=cards, betting=after, decision=after.legal_decision()
        )
        blueprint = ImmutableBlueprintActionSource(
            source_id="v0a-two-decisions",
            entries=(
                BlueprintActionEntry(key=first_key, action=raise_to(6)),
                BlueprintActionEntry(key=second_key, action=CALL),
            ),
        )
        clock = ScriptedClock(start=10_000)
        mailbox = ActionMailbox()
        runtime = HandRuntime(blueprint=blueprint, mailbox=mailbox, clock=clock)
        first = runtime.dispatch(hand_started())
        self.assertEqual(first.status, "decided")
        self.assertEqual(first.decision.action_index, 1)
        first_start = first.decision.timing.wall_start_ns

        clock.advance(50)
        second_events = (
            opponent(1, 4, HandAction(kind="raise", raise_to=18)),
            opponent(2, 5, fold_action()),
            opponent(3, 0, fold_action()),
            opponent(4, 1, fold_action()),
            opponent(5, 2, fold_action()),
        )
        outcomes = [runtime.dispatch(event) for event in second_events]
        final = outcomes[-1]
        self.assertEqual(final.status, "decided")
        record = final.decision
        self.assertEqual(record.action_index, 2)
        self.assertEqual(record.street_action_index, 2)
        self.assertEqual(record.selected_action, call_action())
        self.assertGreater(record.timing.wall_start_ns, first_start)
        self.assertEqual(record.event_index, 5)

    def test_decision_record_binds_states_policy_and_preparation(self) -> None:
        cards, betting = utg_context()
        blueprint = utg_blueprint(raise_to(6))
        clock = ScriptedClock()
        runtime = HandRuntime(blueprint=blueprint, mailbox=ActionMailbox(), clock=clock)
        record = runtime.dispatch(hand_started()).decision
        self.assertEqual(record.hand_id, HAND)
        self.assertEqual(record.event_index, 0)
        self.assertEqual(record.blueprint_sha256, blueprint.digest)
        self.assertEqual(record.state_before_sha256, public_betting_state_sha256(betting))
        after = betting.apply_action(raise_to(6))
        self.assertEqual(record.state_after_sha256, public_betting_state_sha256(after))
        self.assertEqual(len(record.visible_cards_sha256), 64)
        prep = record.preparation_use
        self.assertEqual(prep.producer_status, "producer_absent")
        self.assertEqual(prep.artifact_sha256s, ())
        self.assertEqual(prep.credited_seconds, 0)

    def test_showdown_settlement_matches_the_kernel(self) -> None:
        clock = ScriptedClock()
        runtime = HandRuntime(
            blueprint=empty_blueprint(), mailbox=ActionMailbox(), clock=clock
        )
        runtime.dispatch(hand_started(controlled_seat=2))
        script = [
            (1, 3, fold_action()),
            (2, 4, fold_action()),
            (3, 5, fold_action()),
            (4, 0, fold_action()),
            (5, 1, call_action()),
        ]
        for index, seat, action in script:
            outcome = runtime.dispatch(opponent(index, seat, action))
        self.assertEqual(outcome.status, "decided")
        streets = (("flop", (20, 21, 22)), ("turn", (30,)), ("river", (40,)))
        index = 6
        for street, cards in streets:
            reveal = StreetRevealedEvent(
                hand_id=HAND, event_index=index, street=street, cards=cards
            )
            outcome = runtime.dispatch(reveal)
            self.assertEqual(outcome.status, "accepted", street)
            index += 1
            follow = runtime.dispatch(
                opponent(index, 1, HandAction(kind="check", raise_to=None), street=street)
            )
            self.assertEqual(follow.status, "decided", street)
            index += 1
        strengths = (None, 5, 9, None, None, None)
        result = ShowdownResultEvent(hand_id=HAND, event_index=index, strengths=strengths)
        outcome = runtime.dispatch(result)
        self.assertEqual(outcome.status, "accepted")
        settlement = runtime.settle()
        self.assertEqual(settlement.payouts[2], 4)
        self.assertEqual(settlement.final_stacks[2], 202)
        self.assertEqual(settlement.final_stacks[1], 198)
        self.assertEqual(sum(settlement.final_stacks), sum(STACKS))
        self.assertTrue(runtime.hand_complete)


class PolicyAdmissionRegressionTests(unittest.TestCase):
    """Authority comes from owned exact facts, not caller equality or identity hooks."""

    def reject_at_both_boundaries(self, policy):
        from pontius.v0a.runtime import InvalidDecisionContextError
        mailbox = ActionMailbox()
        with self.subTest(boundary="runtime"):
            with self.assertRaises((TypeError, ValueError)):
                HandRuntime(blueprint=policy, mailbox=mailbox, clock=ScriptedClock())
            self.assertEqual(mailbox.accepted, {})
        cards, betting = utg_context()
        with self.subTest(boundary="public-selector"):
            caught = None
            try:
                select_blueprint_action(policy, cards, betting, betting.legal_decision())
            except BaseException as error:
                caught = type(error)
            self.assertIs(caught, InvalidDecisionContextError)

    def test_outer_policy_identity_and_lookup_hooks_cannot_supply_authority(self):
        honest = empty_blueprint()
        real = utg_blueprint(raise_to(6))
        class DigestPolicy(ImmutableBlueprintActionSource):
            @property
            def digest(self):
                return honest.digest
        class BytesPolicy(ImmutableBlueprintActionSource):
            def canonical_bytes(self):
                return honest.canonical_bytes()
        class LookupPolicy(ImmutableBlueprintActionSource):
            def action_for(self, **kwargs):
                raise AssertionError("caller lookup must not run")
        class Pretender:
            @property
            def __class__(self):
                return ImmutableBlueprintActionSource
        for kind in (DigestPolicy, BytesPolicy, LookupPolicy):
            with self.subTest(kind=kind.__name__):
                self.reject_at_both_boundaries(kind(source_id=real.source_id, entries=real.entries))
        with self.subTest(kind="class-property"):
            self.reject_at_both_boundaries(Pretender())

    def test_every_nested_policy_value_is_exact_before_hashing_or_matching(self):
        from dataclasses import fields, replace
        from pontius.no_limit_betting import BettingAction
        real = utg_blueprint(raise_to(6))
        entry = real.entries[0]
        class Key(BlueprintDecisionKey):
            def __eq__(self, other):
                return True
            __hash__ = BlueprintDecisionKey.__hash__
        class Entry(BlueprintActionEntry):
            pass
        class Action(BettingAction):
            pass
        class Integer(int):
            pass
        class Tuple(tuple):
            pass
        class Text(str):
            pass
        values = {field.name: getattr(entry.key, field.name)
                  for field in fields(BlueprintDecisionKey)}
        values["private_hand"] = (1, 14)  # a different visible key, nevertheless equal under Key
        wildcard = Key(**values)
        policies = (
            ImmutableBlueprintActionSource(
                real.source_id, (BlueprintActionEntry(wildcard, entry.action),)),
            ImmutableBlueprintActionSource(real.source_id, (Entry(entry.key, entry.action),)),
            ImmutableBlueprintActionSource(real.source_id, (BlueprintActionEntry(
                entry.key, Action(entry.action.kind, entry.action.raise_to)),)),
            ImmutableBlueprintActionSource(real.source_id, (BlueprintActionEntry(
                replace(entry.key, small_blind=Integer(entry.key.small_blind)), entry.action),)),
            ImmutableBlueprintActionSource(real.source_id, (BlueprintActionEntry(
                replace(entry.key, starting_stacks=Tuple(entry.key.starting_stacks)),
                entry.action),)),
            ImmutableBlueprintActionSource(real.source_id, Tuple(real.entries)),
            ImmutableBlueprintActionSource(Text(real.source_id), real.entries),
        )
        for index, policy in enumerate(policies):
            with self.subTest(graph=index):
                self.reject_at_both_boundaries(policy)


    def test_nonempty_history_values_obey_the_same_admission_boundary(self):
        from dataclasses import replace
        from pontius.no_limit_betting import BettingAction, BettingActionRecord
        from pontius.v0a.runtime import InvalidDecisionContextError
        _, start = utg_context()
        betting = start.apply_action(CALL)
        cards = OneSeatCardState.preflop(controlled_seat=4, private_hand=(1, 14))
        decision = betting.legal_decision()
        key = BlueprintDecisionKey.from_state(cards=cards, betting=betting, decision=decision)
        atom = key.public_history[0]
        class Text(str):
            pass
        class Tuple(tuple):
            pass
        class Action(BettingAction):
            pass
        class History(BettingActionRecord):
            pass
        bad_keys = (
            replace(key, public_history=((Text(atom[0]), *atom[1:]),)),
            replace(key, public_history=(Tuple(atom),)),
        )
        for index, supplied in enumerate(bad_keys):
            with self.subTest(policy_history=index):
                self.reject_at_both_boundaries(ImmutableBlueprintActionSource(
                    "history-policy", (BlueprintActionEntry(supplied, CALL),)
                ))
        record = betting.history[0]
        bad_histories = (
            Tuple(betting.history),
            (replace(record, action=Action(record.action.kind, record.action.raise_to)),),
            (History(record.street, record.seat, record.action, record.chips_committed,
                     record.full_raise, record.uncalled_return_seat,
                     record.uncalled_return_chips),),
        )
        for index, history in enumerate(bad_histories):
            with self.subTest(context_history=index):
                supplied = replace(betting, history=history)
                with self.assertRaises(InvalidDecisionContextError):
                    select_blueprint_action(empty_blueprint(), cards, supplied,
                                            supplied.legal_decision())

    def test_complete_legal_context_rejects_equal_but_wrongly_typed_fields(self):
        from dataclasses import replace
        from pontius.v0a.runtime import InvalidDecisionContextError
        cards, betting = utg_context()
        decision = betting.legal_decision()
        aliases = (
            replace(decision, street_contribution=False),
            replace(decision, current_bet=float(decision.current_bet)),
            replace(decision, raise_bounds=replace(decision.raise_bounds, all_in_only=0)),
        )
        for index, supplied in enumerate(aliases):
            with self.subTest(alias=index):
                with self.assertRaises(InvalidDecisionContextError):
                    select_blueprint_action(empty_blueprint(), cards, betting, supplied)


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1




class PolicyRefusalShapeTests(unittest.TestCase):
    def test_malformed_depth_is_refused_by_field_shape(self):
        from dataclasses import fields, replace
        from pontius.v0a.runtime import InvalidDecisionContextError
        cards, betting = utg_context()
        deep = 1
        for _ in range(2000):
            deep = (deep,)
        contexts = (betting, NoLimitBettingState.new_hand(
            button=0, starting_stacks=(2,) * 6, small_blind=1, big_blind=2))
        for state in contexts:
            decision = state.legal_decision()
            for field in fields(decision):
                with self.subTest(
                    field=field.name, raise_allowed=decision.raise_bounds is not None
                ):
                    bad = replace(decision, **{field.name: deep})
                    with self.assertRaises(InvalidDecisionContextError):
                        select_blueprint_action(empty_blueprint(), cards, state, bad)
            if decision.raise_bounds is not None:
                for field in fields(decision.raise_bounds):
                    with self.subTest(bounds=field.name):
                        bounds = replace(decision.raise_bounds, **{field.name: deep})
                        with self.assertRaises(InvalidDecisionContextError):
                            select_blueprint_action(empty_blueprint(), cards, state,
                                                    replace(decision, raise_bounds=bounds))
            result = select_blueprint_action(empty_blueprint(), cards, state, decision)
            self.assertEqual(result.action, CALL)


class ValueAdmissionRegressionTests(unittest.TestCase):
    """Admission precedes effects; acknowledgement never guesses acceptance."""

    @staticmethod
    def loose(record, **changes):
        from dataclasses import fields
        kind = type(record)
        unchecked = type("Unchecked" + kind.__name__, (kind,),
                         {"__post_init__": lambda self: None})
        values = {field.name: getattr(record, field.name) for field in fields(kind)}
        values.update(changes)
        return unchecked(**values)

    def before(self, kind):
        mailbox = ActionMailbox()
        runtime = new_runtime(empty_blueprint(), mailbox=mailbox)
        if kind == "start":
            return runtime, mailbox, hand_started()
        self.assertEqual(runtime.dispatch(hand_started(controlled_seat=2)).status, "accepted")
        if kind == "opponent":
            return runtime, mailbox, opponent(1, 3, fold_action())
        for index, seat in ((1, 3), (2, 4), (3, 5), (4, 0)):
            self.assertEqual(runtime.dispatch(opponent(index, seat, fold_action())).status,
                             "accepted")
        self.assertEqual(runtime.dispatch(opponent(5, 1, call_action())).status, "decided")
        reveal = StreetRevealedEvent(hand_id=HAND, event_index=6,
                                    street="flop", cards=(20, 21, 22))
        if kind == "reveal":
            return runtime, mailbox, reveal
        index = 6
        for street, cards in (("flop", (20, 21, 22)), ("turn", (30,)), ("river", (40,))):
            self.assertEqual(runtime.dispatch(StreetRevealedEvent(
                hand_id=HAND, event_index=index, street=street, cards=cards)).status, "accepted")
            index += 1
            self.assertEqual(runtime.dispatch(opponent(
                index, 1, HandAction(kind="check", raise_to=None), street)).status, "decided")
            index += 1
        return runtime, mailbox, ShowdownResultEvent(
            hand_id=HAND, event_index=index, strengths=(None, 5, 9, None, None, None))

    def assert_no_effect(self, runtime, mailbox, bad):
        before, deliveries = runtime.state, mailbox.accepted
        outcome = runtime.dispatch(bad)
        self.assertEqual(outcome.status, "failed")
        self.assertIs(outcome.failure.code, FailureCode.INVALID_EVENT)
        self.assertIsNone(outcome.failure.event_index)
        self.assertEqual(runtime.state, before)
        self.assertEqual(mailbox.accepted, deliveries)
        self.assertFalse(runtime.hand_complete)

    def test_all_event_variants_revalidate_before_any_effect(self):
        for kind in ("start", "opponent", "reveal", "showdown"):
            for changes in ({}, {"schema_version": "wrong"}, {"event_index": True},
                            {"event_index": 0.0}, {"hand_id": []}):
                with self.subTest(kind=kind, changes=changes):
                    runtime, mailbox, good = self.before(kind)
                    self.assert_no_effect(runtime, mailbox, self.loose(good, **changes))
        runtime, mailbox, good = self.before("opponent")
        # Exact outer event, normally constructed nested object skipping validation.
        nested = self.loose(HandAction(kind="raise", raise_to=6), kind="not-an-action")
        self.assert_no_effect(runtime, mailbox, OpponentActionEvent(
            hand_id=HAND, event_index=1, street="preflop", seat=3, action=nested))

    def test_showdown_strengths_are_immutable_and_comparable_before_completion(self):
        from dataclasses import replace
        for strengths in ([], [None, 5, 9, None, None, None],
                          (None, (), (9,), None, None, None)):
            with self.subTest(strengths=strengths):
                runtime, mailbox, good = self.before("showdown")
                self.assert_no_effect(runtime, mailbox, self.loose(good, strengths=strengths))
        for ranks in ((None, 5, (9,), None, None, None),
                      (None, None, 9, None, None, None), (1, 5, 9, None, None, None)):
            with self.subTest(context_strengths=ranks):
                runtime, mailbox, good = self.before("showdown")
                before = runtime.state
                outcome = runtime.dispatch(replace(good, strengths=ranks))
                self.assertEqual(outcome.status, "failed")
                self.assertIs(outcome.failure.code, FailureCode.INVALID_EVENT)
                self.assertEqual(runtime.state, before)
                self.assertFalse(runtime.hand_complete)
        for strengths in ((None, 5, 9, None, None, None),
                          (None, (5,), (9,), None, None, None)):
            runtime, mailbox, good = self.before("showdown")
            self.assertEqual(runtime.dispatch(replace(good, strengths=strengths)).status, "accepted")
            first = runtime.settle()
            self.assertEqual(first.payouts, (0, 0, 4, 0, 0, 0))
            self.assertEqual(runtime.settle(), first)

    def test_rejected_metadata_never_reads_unadmitted_objects(self):
        class Hostile:
            @property
            def event_index(self):
                raise AssertionError("unadmitted metadata consulted")
        for mode in ("fresh", "dead", "clock", "complete"):
            with self.subTest(mode=mode):
                clock = ScriptedClock()
                mailbox = ActionMailbox()
                runtime = new_runtime(empty_blueprint(), mailbox, clock)
                if mode == "dead":
                    runtime.dispatch(opponent(1, 3, fold_action()))
                if mode == "clock":
                    clock.fail_next("invalid")
                if mode == "complete":
                    runtime, mailbox, event = self.before("showdown")
                    self.assertEqual(runtime.dispatch(event).status, "accepted")
                before = mailbox.accepted
                outcome = runtime.dispatch(Hostile())
                self.assertEqual(outcome.status, "failed")
                self.assertIsNone(outcome.failure.event_index)
                self.assertEqual(mailbox.accepted, before)

    def test_invalid_envelopes_cannot_poison_later_valid_key(self):
        good = ActionEnvelope(hand_id=HAND, action_index=1, seat=3,
                              street="preflop", action=call_action())
        changes = ({}, {"action_index": True}, {"action_index": 1.0},
                   {"seat": True}, {"street": "wrong"}, {"hand_id": []},
                   {"action": self.loose(call_action(), kind="bad")})
        for change in changes:
            with self.subTest(change=change):
                mailbox = ActionMailbox()
                with self.assertRaises(MailboxRejectionError):
                    mailbox.deliver(self.loose(good, **change))
                self.assertEqual(mailbox.accepted, {})
                self.assertEqual(mailbox.deliver(good).action_index, 1)
                self.assertEqual(len(mailbox.accepted), 1)
                with self.assertRaises(MailboxRejectionError):
                    mailbox.deliver(good)
        nested = ActionEnvelope(hand_id=HAND, action_index=1, seat=3,
                                street="preflop", action=self.loose(call_action(), kind="bad"))
        mailbox = ActionMailbox()
        with self.assertRaises(MailboxRejectionError):
            mailbox.deliver(nested)
        self.assertEqual(mailbox.accepted, {})
        mailbox.deliver(good)

    def test_real_delivery_with_invalid_receipt_is_ambiguous_without_retry(self):
        from pontius.v0a.model import DeliveryReceipt
        for change in ({}, {"action_index": True}, {"action_index": 1.0}, {"hand_id": []}):
            with self.subTest(change=change):
                mailbox, attempts = ActionMailbox(), []
                loose = self.loose
                class Forward:
                    def deliver(self, envelope):
                        attempts.append(envelope)
                        receipt = mailbox.deliver(envelope)
                        return loose(receipt, **change)
                runtime = new_runtime(empty_blueprint(), Forward())
                outcome = runtime.dispatch(hand_started())
                self.assertEqual(outcome.status, "failed")
                self.assertIs(outcome.failure.code, FailureCode.DELIVERY_AMBIGUOUS)
                self.assertIs(outcome.failure.delivery_status, DeliveryStatus.UNKNOWN)
                self.assertEqual(runtime.accepted_delivery_count, 0)
                self.assertEqual(len(mailbox.accepted), 1)
                self.assertEqual(len(attempts), 1)
                runtime.dispatch(opponent(1, 4, call_action()))
                self.assertEqual(len(attempts), 1)



if __name__ == "__main__":
    sys.exit(main())
