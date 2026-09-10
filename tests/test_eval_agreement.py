"""Retained-envelope controls; fixtures construct observations, never transport success."""
import base64
import copy
import importlib.util
import json
import unittest

from pontius.eval_bridge import board_cards, hand_name, replay_root, root_key
from pontius.holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
from pontius.legal_decision_spine_v2 import public_betting_state_sha256
from pontius.no_limit_betting import (
    CALL, CHECK, FOLD, NoLimitBettingState, TerminalReason, raise_to,
)
from pontius.river import parse_cards
from pontius.v0a.model import visible_cards_sha256


def payload(action):
    return dict(kind=action.kind.value, raise_to=action.raise_to)


def fixture(*, stacks=4, action=CHECK, baseline=False):
    board = board_cards(('2c', '7d', '9h', 'Js', 'Qc'))
    hands = tuple(tuple(sorted(parse_cards(*cards.split()))) for cards in
                  ('5c 6c', 'Kh Kd', '3c 4d', '8c 8d', 'Tc Td', 'As Ad'))
    blueprint = ImmutableBlueprintActionSource('classifier-control', (
        BlueprintActionEntry(root_key(replay_root(), board, hands[2]), action),))
    deal = SixSeatHoldemDeal(hands, board)
    state = NoLimitBettingState.new_hand(button=0, starting_stacks=(stacks,) * 6,
                                         small_blind=1, big_blind=2)
    protocol = 'pontius-v0a-event-interface-v1'
    common = dict(protocol=protocol,
                  session_id=protocol + '-correctness-table-classifier-h01')
    frames = [dict(common, type='ready', source_commit='a' * 40,
                   source_manifest_sha256='b' * 64, blueprint_artifact_sha256='c' * 64,
                   blueprint_sha256=blueprint.digest, evidentiary=False)]
    events, actions = {}, []
    event_index, action_index, street_index = 0, 0, 0
    timing = dict(status='completed', interruption_reason=None, wall_start_ns=0,
                  last_valid_observation_ns=1, emission_observed_ns=1, elapsed_ns=1,
                  response_compute_seconds=0.0, response_uninstrumented_seconds=1e-9,
                  work_cutoff_crossed=False, deadline_crossed=False)
    sequence = [(3, FOLD), (4, FOLD), (5, FOLD), (0, FOLD), (1, CALL), (2, CHECK),
                None, (1, CHECK), (2, CHECK), None, (1, CHECK), (2, CHECK),
                None, (1, CHECK), (2, action)]
    if baseline:
        sequence = [(3, FOLD), (4, FOLD), (5, FOLD), (0, FOLD), (1, raise_to(4)), (2, FOLD)]
    if baseline == 'allin':
        sequence = sequence[:-1] + [(2, CALL), None, None, None]
    elif action != CHECK:
        sequence.append((1, CALL))
    for step in sequence:
        if step is None:
            state = state.advance_street()
            event_index += 1
            street_index = 0
            continue
        seat, selected = step
        before = state
        state = state.apply_action(selected)
        actions.append(dict(index=len(actions), seat=seat, street=before.street.value,
                            action=payload(selected), origin='bot' if seat == 2 else 'opponent'))
        if seat != 2:
            event_index += 1
            continue
        action_index += 1
        street_index += 1
        cards = OneSeatCardState(2, hands[2], before.street, deal.public_cards(before.street))
        record = dict(hand_id=common['session_id'], event_index=event_index,
                      action_index=action_index, street_action_index=street_index, seat=2,
                      street=before.street.value,
                      state_before_sha256=public_betting_state_sha256(before),
                      state_after_sha256=public_betting_state_sha256(state),
                      visible_cards_sha256=visible_cards_sha256(cards),
                      blueprint_sha256=blueprint.digest, selected_action=payload(selected),
                      selection_reason='table_hit' if before.street.value == 'river' and stacks == 4
                                       else 'passive_default',
                      spine_reason='no_candidate', timing=timing, failure_reason=None,
                      preparation_use=dict(producer_status='producer_absent',
                                           artifact_sha256s=[], credited_seconds=0))
        events[event_index] = record
    if not state.is_terminal:
        state = state.advance_street()
    # Real host event numbering includes showdown publication even after a terminal action.
    event_index += state.terminal_reason is not TerminalReason.FOLD
    strengths = deal.showdown_strengths(state.live_seats) if baseline is not True else None
    settled = state.settle(strengths)
    settlement = dict(payouts=list(settled.payouts), final_stacks=list(settled.final_stacks),
                      pots=[dict(amount=p.amount, seats=list(p.eligible_seats))
                            for p in settled.side_pots])
    for index in range(event_index + 1):
        decision = events.get(index)
        if decision:
            frames.append(dict(common, type='action', hand_id=common['session_id'],
                               action_index=decision['action_index'], seat=2,
                               street=decision['street'], action=decision['selected_action']))
        frames.append(dict(common, type='event_result', event_index=index,
                           status='decided' if decision else 'accepted',
                           decision=decision, failure=None))
    closure = dict(common, accounting_complete=True, failure_reason=None,
                   secondary_failures=[], evidentiary=False)
    frames.extend([dict(closure, type='hand_result', complete=True, settlement=settlement,
                        rank_source='not_required' if baseline is True else 'host_supplied',
                        preparation_compute_seconds=0.0, post_terminal_compute_seconds=0.0,
                        interrupted_response_count=0),
                   dict(closure, type='session_result', status='completed',
                        terminal_publication_compute_seconds=0.0,
                        accounting_scope='runtime_begin_to_final_publication')])
    hand = dict(version='pontius-v0a-table-session-hand-result-v1',
                session_id='pontius-v0a-table-host-v1-correctness-classifier-h01',
                source_commit='a' * 40, blueprint_artifact_sha256='c' * 64,
                status='completed', failure_reason=None, secondary_failures=[],
                capture_truncated=False, child_exit_code=0, settlement=settlement,
                blueprint_sha256=blueprint.digest, applied_actions=actions)
    report = dict(version='pontius-v0a-table-session-result-v1',
                  session_id='pontius-v0a-table-session-v1-correctness-classifier',
                  source_commit='a' * 40, blueprint_artifact_sha256='c' * 64,
                  blueprint_sha256=blueprint.digest, status='completed',
                  failure_reason=None, secondary_failures=[],
                  stop_reason=None, requested_hands=1, completed_hands=1,
                  hands=[dict(ordinal=1, button=0, starting_stacks=[stacks] * 6, result=hand)])
    retain(report, frames)
    return report, frames, dict(blueprint=blueprint, teacher_actions={hand_name(hands[2]): action},
                                board=board, private_hands=hands, stacks=stacks)


def retain(report, frames):
    report['hands'][0]['result']['child_stdout_base64'] = base64.b64encode(
        b''.join(json.dumps(frame).encode() + b'\n' for frame in frames)).decode()


class AgreementTests(unittest.TestCase):
    def classify(self, report, args):
        self.assertIsNotNone(importlib.util.find_spec('pontius.eval_agreement'),
                             'retained-outcome classifier is absent')
        from pontius.eval_agreement import classify
        return classify(report, **args)

    def test_completed_exact_check_is_hit_and_settlement_is_replayed(self):
        report, frames, args = fixture()
        self.assertEqual(sum(row['type'] == 'event_result' for row in frames), 13)
        result = self.classify(report, args)
        self.assertEqual(result['classification'], 'hit')
        self.assertTrue(result['chip_eligible'])
        self.assertEqual(result['chips'], -2)
        self.assertTrue(result['agreement_eligible'])
        self.assertEqual(result['causes'], [])

    def test_outer_and_nested_failures_precede_decision(self):
        for where in ('outer', 'nested'):
            report, frames, args = fixture()
            failed = report if where == 'outer' else report['hands'][0]['result']
            failed['status'], failed['failure_reason'] = 'failed', 'transport_failed'
            result = self.classify(report, args)
            self.assertEqual(result['classification'], 'excluded')
            self.assertIsNone(result['chips'])
            self.assertIn('transport_failed', ' '.join(result['causes']))

    def test_missing_nested_result_is_excluded(self):
        report, _, args = fixture()
        report['hands'][0] = dict(status='completed', settlement={'payouts': [0] * 6})
        self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_bad_wire_and_truncation_are_excluded(self):
        for wire in ('!', base64.b64encode(b'{}').decode(),
                     base64.b64encode(b'{"type":"ready","type":"ready"}\n').decode(),
                     base64.b64encode(b'{"value":NaN}\n').decode()):
            report, _, args = fixture()
            report['hands'][0]['result']['child_stdout_base64'] = wire
            self.assertEqual(self.classify(report, args)['classification'], 'excluded')
        report, _, args = fixture()
        report['hands'][0]['result']['capture_truncated'] = True
        self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_child_failure_and_incomplete_closure_are_excluded(self):
        for change in ('event_failure', 'missing_closure', 'hand_incomplete',
                       'unaccounted', 'late_failure', 'missing_settlement'):
            report, frames, args = fixture()
            if change == 'event_failure':
                frames[1].update(status='failed', decision=None,
                                 failure=dict(code='transport_failed', timing=None))
            elif change == 'missing_closure':
                frames.pop()
            elif change == 'hand_incomplete':
                frames[-2]['complete'] = False
            elif change == 'unaccounted':
                frames[-1]['accounting_complete'] = False
            elif change == 'late_failure':
                frames[-1]['failure_reason'] = 'clock_invalid'
            else:
                report['hands'][0]['result']['settlement'] = None
            retain(report, frames)
            result = self.classify(report, args)
            self.assertEqual(result['classification'], 'excluded', change)
            self.assertFalse(result['chip_eligible'])

    def test_relabelled_check_and_nonpassive_prefix_are_disagreements(self):
        for street in ('river', 'preflop'):
            report, frames, args = fixture()
            decision = next(f['decision'] for f in frames if f['type'] == 'event_result'
                            and f['decision'] and f['decision']['street'] == street)
            decision['selection_reason'] = 'passive_default' if street == 'river' else 'table_hit'
            retain(report, frames)
            self.assertEqual(self.classify(report, args)['classification'], 'disagreement')

    def test_wrong_teacher_and_tampered_state_hash_do_not_hit(self):
        from pontius.no_limit_betting import raise_to
        for field in ('teacher', 'hash'):
            report, frames, args = fixture()
            if field == 'teacher':
                args['teacher_actions'] = {name: raise_to(2) for name in args['teacher_actions']}
            else:
                decision = next(f['decision'] for f in frames if f.get('decision'))
                decision['state_before_sha256'] = '0' * 64
                retain(report, frames)
            self.assertNotEqual(self.classify(report, args)['classification'], 'hit')

    def test_changed_stack_prefix_has_zero_hits(self):
        report, _, args = fixture(stacks=5)
        result = self.classify(report, args)
        self.assertEqual(result['classification'], 'unsupported')
        self.assertTrue(result['chip_eligible'])

    def test_baseline_fold_still_has_chips_without_river(self):
        report, _, args = fixture(baseline=True)
        result = self.classify(report, dict(args, strategy='baseline-rules-v1'))
        self.assertTrue(result['chip_eligible'])
        self.assertFalse(result['agreement_eligible'])
        self.assertEqual(result['chips'], -2)
        self.assertEqual(result['classification'], 'unsupported')

    def test_false_settlement_is_excluded(self):
        report, frames, args = fixture()
        report['hands'][0]['result']['settlement']['final_stacks'][2] += 1
        retain(report, frames)
        self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_summary_accounts_missing_and_rejects_overcount(self):
        self.classify(*[fixture()[i] for i in (0, 2)])
        from pontius.eval_agreement import summarize
        result = summarize([dict(classification='hit', chip_eligible=True,
                                 agreement_eligible=True)], scheduled=2)
        self.assertEqual(result['missing'], 1)
        self.assertFalse(result['complete'])
        with self.assertRaises(ValueError):
            summarize([dict(classification='hit')], scheduled=0)


    def test_missing_required_frame_and_decision_fields_are_excluded(self):
        for field in ('ready', 'decision', 'extra_v1_delivery'):
            report, frames, args = fixture()
            if field == 'ready':
                del frames[0]['source_manifest_sha256']
            else:
                record = next(frame['decision'] for frame in frames if frame.get('decision'))
                if field == 'decision':
                    del record['preparation_use']
                else:
                    record['delivery_status'] = 'accepted'
            retain(report, frames)
            self.assertEqual(self.classify(report, args)['classification'], 'excluded', field)

    def test_raise_table_hit_and_off_pool_default(self):
        for in_pool in (True, False):
            report, frames, args = fixture(action=raise_to(2) if in_pool else CHECK)
            if not in_pool:
                args['blueprint'] = ImmutableBlueprintActionSource('empty-control', ())
                args['teacher_actions'] = {}
                digest = args['blueprint'].digest
                frames[0]['blueprint_sha256'] = digest
                report['blueprint_sha256'] = report['hands'][0]['result']['blueprint_sha256'] = (
                    digest)
                for frame in frames:
                    if frame.get('decision'):
                        frame['decision'].update(blueprint_sha256=digest,
                                                 selection_reason='passive_default')
                retain(report, frames)
            result = self.classify(report, args)
            self.assertEqual(result['classification'], 'hit' if in_pool else 'unsupported', result)
            self.assertTrue(result['chip_eligible'])

    def test_zero_or_duplicate_river_never_hit(self):
        for duplicate in (False, True):
            report, frames, args = fixture()
            river = next(frame for frame in frames if frame.get('decision')
                         and frame['decision']['street'] == 'river')
            if duplicate:
                index = frames.index(river)
                frames.insert(index + 1, copy.deepcopy(frames[index - 1]))
                added = copy.deepcopy(river)
                frames.insert(index + 2, added)
                # Duplicate the decision in an extra, coherently framed event.
                for index, frame in enumerate(f for f in frames if f['type'] == 'event_result'):
                    frame['event_index'] = index
                    if frame['decision']:
                        frame['decision']['event_index'] = index
            else:
                frames.remove(frames[frames.index(river) - 1])
                river.update(status='accepted', decision=None)
            retain(report, frames)
            result = self.classify(report, args)
            self.assertNotEqual(result['classification'], 'hit')
            if not duplicate:
                self.assertTrue(result['chip_eligible'])
                self.assertIn('agreement:river_decision_count:0', result['causes'])

    def test_unknown_reason_and_in_pool_default_disagree(self):
        for reason in ('made_up', 'passive_default'):
            report, frames, args = fixture()
            if reason == 'passive_default':
                args['blueprint'] = ImmutableBlueprintActionSource('empty-control', ())
                frames[0]['blueprint_sha256'] = args['blueprint'].digest
                report['blueprint_sha256'] = report['hands'][0]['result']['blueprint_sha256'] = (
                    args['blueprint'].digest)
            for frame in frames:
                if frame.get('decision'):
                    frame['decision']['blueprint_sha256'] = args['blueprint'].digest
                    if frame['decision']['street'] == 'river':
                        frame['decision']['selection_reason'] = reason
            retain(report, frames)
            self.assertEqual(self.classify(report, args)['classification'], 'disagreement')

    def test_observed_counts_include_reason_relabels(self):
        report, frames, args = fixture(stacks=6)
        result = self.classify(report, args)
        self.assertEqual(result['observed_table_hits'], 0)
        self.assertEqual(result['river_records'], 1)
        report, frames, args = fixture()
        record = next(frame['decision'] for frame in frames if frame.get('decision'))
        record['selection_reason'] = 'table_hit'
        retain(report, frames)
        self.assertEqual(self.classify(report, args)['observed_table_hits'], 2)

    def test_completed_baseline_early_allin_still_has_chips(self):
        report, _, args = fixture(baseline='allin')
        result = self.classify(report, dict(args, strategy='baseline-rules-v1'))
        self.assertTrue(result['chip_eligible'], result)
        self.assertEqual(result['chips'], -4)

    def test_exponent_overflow_is_not_valid_retained_json(self):
        report, frames, args = fixture()
        raw = b''.join(json.dumps(frame).encode() + b'\n' for frame in frames)
        raw = raw.replace(b'"source_commit": "' + b'a' * 40 + b'"',
                          b'"source_commit": 1e9999')
        report['hands'][0]['result']['child_stdout_base64'] = base64.b64encode(raw).decode()
        self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_noninteger_settlement_cannot_compare_equal_to_kernel(self):
        report, frames, args = fixture()
        report['hands'][0]['result']['settlement']['payouts'][0] = False
        retain(report, frames)
        self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_nonnull_false_failure_and_missing_failure_field_are_excluded(self):
        for marker in (False, '', 'missing'):
            report, _, args = fixture()
            report['failure_reason'] = marker
            if marker == 'missing':
                del report['failure_reason']
            self.assertEqual(self.classify(report, args)['classification'], 'excluded')

    def test_retained_source_artifact_and_session_identities_cannot_be_swapped(self):
        for changed in ('ready_commit', 'hand_commit', 'outer_artifact',
                        'manifest_shape', 'child_id'):
            report, frames, args = fixture()
            if changed == 'ready_commit':
                frames[0]['source_commit'] = 'd' * 40
            elif changed == 'hand_commit':
                report['hands'][0]['result']['source_commit'] = 'd' * 40
            elif changed == 'outer_artifact':
                report['blueprint_artifact_sha256'] = 'd' * 64
            elif changed == 'manifest_shape':
                frames[0]['source_manifest_sha256'] = 'not-a-sha256'
            else:
                for frame in frames:
                    frame['session_id'] += '-other'
                    if 'hand_id' in frame:
                        frame['hand_id'] += '-other'
                    if frame.get('decision'):
                        frame['decision']['hand_id'] += '-other'
            retain(report, frames)
            self.assertEqual(self.classify(report, args)['classification'], 'excluded', changed)
