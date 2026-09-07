"""Prepared lookup uses the real runtime, accounting, application and mailbox."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from pontius.blueprint_preparation.lookup import PreparedBlueprint
from pontius.holdem_cards import OneSeatCardState
from pontius.immutable_blueprint import (
    BlueprintActionEntry, BlueprintDecisionKey, ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import CALL, NoLimitBettingState, raise_to
from pontius.river import parse_cards
from pontius.v0a.clock import ClockInvalidError, ClockReversedError
from pontius.v0a.model import (
    DeliveryReceipt, FailureCode, HandAction, HandStartedEvent, OpponentActionEvent,
    StreetRevealedEvent,
)
from pontius.v0a.runtime import HandRuntime, select_blueprint_action


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


class Mailbox:
    def __init__(self):
        self.envelopes = []

    def deliver(self, envelope):
        self.envelopes.append(envelope)
        return DeliveryReceipt(envelope.hand_id, envelope.action_index)


def start(seat=3):
    return HandStartedEvent(
        hand_id='pontius-v0a-event-interface-v2-correctness-prepared', event_index=0,
        button=0, controlled_seat=seat, starting_stacks=(200,)*6, small_blind=1, big_blind=2,
        private_cards=tuple(sorted(parse_cards('As', 'Ah'))))


def table(action=CALL, hit=True):
    cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=start().private_cards)
    betting = NoLimitBettingState.six_max_100bb(button=0)
    key = BlueprintDecisionKey.from_state(cards=cards, betting=betting,
                                           decision=betting.legal_decision())
    entries = (BlueprintActionEntry(key, action),) if hit else ()
    return ImmutableBlueprintActionSource('prepared-runtime-control', entries)


class PreparedRuntimeTests(unittest.TestCase):
    def make_runtime(self, blueprint=None, strategy='blueprint-v1', clock=None, mailbox=None):
        return HandRuntime(blueprint=blueprint or table(), strategy=strategy,
            source_manifest_sha256='1'*64, clock=clock or Clock(), mailbox=mailbox or Mailbox())

    def test_no_hidden_preparation_before_start_and_one_preparation_across_actions(self):
        original = PreparedBlueprint.__init__
        prepared = []
        def observed(instance, source):
            original(instance, source)
            prepared.append(instance)
        with patch.object(PreparedBlueprint, '__init__', observed):
            source = table()
            runtime = self.make_runtime(source)
            self.assertIsNone(runtime._prepared_blueprint)
            self.assertEqual(runtime.blueprint_sha256, source.digest)
            self.assertEqual(prepared, [])
            first = start()
            self.assertEqual(runtime.dispatch(first).status, 'decided')
            for index, seat in enumerate((4, 5, 0, 1, 2), 1):
                result = runtime.dispatch(OpponentActionEvent(first.hand_id, index, 'preflop',
                    seat, HandAction('check' if seat == 2 else 'call', None)))
                self.assertEqual(result.status, 'accepted')
            self.assertEqual(runtime.dispatch(StreetRevealedEvent(first.hand_id, 6, 'flop',
                parse_cards('2c', '7d', '9s'))).status, 'accepted')
            runtime.dispatch(OpponentActionEvent(first.hand_id, 7, 'flop', 1,
                HandAction('check', None)))
            second = runtime.dispatch(OpponentActionEvent(first.hand_id, 8, 'flop', 2,
                HandAction('check', None)))
            self.assertEqual(second.status, 'decided')
            self.assertEqual(second.decision.selected_action.kind, 'check')
            self.assertEqual(len(prepared), 1)
            self.assertIs(runtime._prepared_blueprint, prepared[0])
            self.assertEqual(runtime.blueprint_sha256, source.digest)

    def test_preparation_elapsed_is_charged_with_no_new_bank_credit(self):
        original = PreparedBlueprint.__init__
        for seat in (0, 3):
            for strategy in ('blueprint-v1', 'baseline-rules-v1'):
                with self.subTest(seat=seat, strategy=strategy):
                    clock = Clock()
                    runtime = self.make_runtime(strategy=strategy, clock=clock)
                    def elapsed(instance, source):
                        original(instance, source)
                        clock.now = 2_000_000
                    with patch.object(PreparedBlueprint, '__init__', elapsed):
                        result = runtime.dispatch(start(seat))
                    self.assertEqual(result.status, 'accepted' if seat == 0 else 'decided')
                    self.assertTrue(runtime.accounting().complete)
                    if seat == 0:
                        self.assertEqual(runtime.accounting().preparation_compute_seconds, .002)
                    else:
                        timing = result.decision.timing
                        self.assertEqual(timing.elapsed_ns, 2_000_000)
                        self.assertEqual(timing.response_compute_seconds
                            + timing.response_uninstrumented_seconds, .002)
                        use = result.decision.preparation_use
                        self.assertEqual(use.producer_status, 'producer_absent')
                        self.assertEqual(use.artifact_sha256s, ())
                        self.assertEqual(use.credited_seconds, 0)

    def test_both_runtime_fallbacks_use_prepared_hits_and_misses(self):
        from pontius.decision_provider.model import DecisionProposal
        from pontius.decision_provider.providers import BaselineProvider
        original = PreparedBlueprint.action_for
        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
            for hit in (False, True):
                with self.subTest(strategy=strategy, hit=hit):
                    calls, mailbox = [], Mailbox()
                    def selected(instance, **context):
                        calls.append(instance)
                        return original(instance, **context)
                    def abstain(provider, observation):
                        return DecisionProposal(observation.decision_sha256, None, 'abstain')
                    runtime = self.make_runtime(table(raise_to(6), hit), strategy,
                                                mailbox=mailbox)
                    with patch.object(PreparedBlueprint, 'action_for', selected), \
                            patch.object(BaselineProvider, 'propose', abstain):
                        result = runtime.dispatch(start())
                    expected = HandAction('raise', 6) if hit else HandAction('call', None)
                    self.assertEqual(result.status, 'decided')
                    self.assertEqual(calls, [runtime._prepared_blueprint])
                    self.assertEqual(result.decision.selected_action, expected)
                    self.assertEqual(result.decision.applied_action, expected)
                    self.assertEqual(mailbox.envelopes[0].action, expected)
                    self.assertEqual(runtime.state.stacks[3], 194 if hit else 198)
                    if strategy == 'baseline-rules-v1':
                        self.assertEqual(result.decision.selection_origin, 'blueprint_fallback')

    def test_ordinary_preparation_failure_closes_and_never_publishes_a_cache(self):
        for paired in (False, True):
            with self.subTest(paired=paired):
                clock, mailbox = Clock(), Mailbox()
                runtime = self.make_runtime(clock=clock, mailbox=mailbox)
                def failing(instance, source):
                    clock.now = True if paired else 3_000_000
                    raise ValueError('controlled preparation failure')
                with patch.object(PreparedBlueprint, '__init__', failing):
                    result = runtime.dispatch(start())
                self.assertEqual(result.status, 'failed')
                self.assertEqual(result.failure.code, FailureCode.SOURCE_BINDING_MISMATCH)
                expected = (FailureCode.SOURCE_BINDING_MISMATCH,)
                if paired:
                    expected += (FailureCode.CLOCK_INVALID,)
                self.assertEqual(runtime.closure_failures, expected)
                self.assertIsNone(runtime._prepared_blueprint)
                self.assertIsNone(runtime._blueprint_digest)
                self.assertEqual(mailbox.envelopes, [])
                self.assertEqual(runtime.accounting().preparation_compute_seconds,
                                 None if paired else .003)

    def test_clock_preparation_failures_keep_their_type_and_cancellation_propagates(self):
        for error, code in ((ClockInvalidError, FailureCode.CLOCK_INVALID),
                            (ClockReversedError, FailureCode.CLOCK_REVERSED)):
            with self.subTest(error=error):
                runtime = self.make_runtime()
                with patch.object(PreparedBlueprint, '__init__', side_effect=error('scheduled')):
                    result = runtime.dispatch(start())
                self.assertEqual(result.failure.code, code)
                self.assertEqual(runtime.closure_failures, (code,))
                self.assertIsNone(runtime._prepared_blueprint)
        for error in (KeyboardInterrupt, SystemExit):
            mailbox = Mailbox()
            runtime = self.make_runtime(mailbox=mailbox)
            with patch.object(PreparedBlueprint, '__init__', side_effect=error), \
                    self.assertRaises(error):
                runtime.dispatch(start())
            self.assertIsNone(runtime._prepared_blueprint)
            self.assertEqual(mailbox.envelopes, [])

    def test_illegal_matching_entry_still_fails_before_application(self):
        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
            mailbox = Mailbox()
            runtime = self.make_runtime(table(raise_to(1)), strategy, mailbox=mailbox)
            result = runtime.dispatch(start())
            self.assertEqual(result.failure.code, FailureCode.INVALID_BLUEPRINT_ENTRY)
            self.assertEqual(runtime.state.stacks[3], 200)
            self.assertEqual(mailbox.envelopes, [])

    def test_prepared_lookup_keeps_exact_work_and_wall_edges(self):
        original = PreparedBlueprint.action_for
        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
            for elapsed in (13_999_999_999, 14_000_000_000, 14_000_000_001,
                            14_999_999_999, 15_000_000_000, 15_000_000_001):
                with self.subTest(strategy=strategy, elapsed=elapsed):
                    clock, mailbox = Clock(), Mailbox()
                    def delayed(instance, **context):
                        result = original(instance, **context)
                        clock.now = elapsed
                        return result
                    runtime = self.make_runtime(table(raise_to(6)), strategy, clock, mailbox)
                    with patch.object(PreparedBlueprint, 'action_for', delayed):
                        result = runtime.dispatch(start())
                    expected = (FailureCode.ACTION_DEADLINE_EXCEEDED if elapsed > 15_000_000_000
                        else FailureCode.WORK_CUTOFF_EXCEEDED if elapsed >= 14_000_000_000
                        else None)
                    self.assertEqual(result.failure.code if result.failure else None, expected)
                    self.assertEqual(result.decision.timing.elapsed_ns, elapsed)
                    self.assertEqual(len(mailbox.envelopes), 1)
                    self.assertEqual(result.decision.applied_action, mailbox.envelopes[0].action)
                    self.assertEqual(result.decision.delivered_action, mailbox.envelopes[0].action)

    def test_public_selector_retains_legacy_route(self):
        source = table(raise_to(6))
        cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=start().private_cards)
        betting = NoLimitBettingState.six_max_100bb(button=0)
        with patch.object(PreparedBlueprint, 'action_for', side_effect=AssertionError):
            result = select_blueprint_action(source, cards, betting, betting.legal_decision())
        self.assertEqual(result.action, raise_to(6))
        self.assertEqual(result.source_digest, source.digest)


if __name__ == '__main__':
    unittest.main()
