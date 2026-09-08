"""Finite literal controls; no engine or seeded-deal imports and no poker starts."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/evaluation/controls.json').read_bytes())
SPEC = importlib.util.spec_from_file_location(
    '_evaluation_contract_test', ROOT / 'tools/v0a_evaluation_contract.py')
C = None
if Path(SPEC.origin).exists():
    C = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(C)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def fixture(strategy='baseline-rules-v1', failed=False):
    """Bind literal schema examples; this is not a successful engine oracle."""
    version = '2' if strategy == 'baseline-rules-v1' else '1'
    binding = copy.deepcopy(FIXTURE['binding'])
    binding['strategy'] = strategy
    binding['session_id'] = ('pontius-v0a-table-session-v' + version
                             + '-correctness-eval-control-u001')
    report = copy.deepcopy(FIXTURE['report_v' + version])
    frames = copy.deepcopy(FIXTURE['frames_v' + version])
    if failed:
        report.update(status='failed', failure_reason='child_failed', completed_hands=0,
                      next_button=3, carried_stacks=[200] * 6)
        hand = report['hands'][0]['result']
        hand.update(status='failed', failure_reason='child_failed', child_exit_code=1,
                    settlement=None, applied_actions=[])
        frames = [frames[0], copy.deepcopy(FIXTURE['failed_event_v' + version])]
    return binding, report, frames


def observe(binding, report, frames, **kwargs):
    report['hands'][0]['result']['child_stdout_base64'] = base64.b64encode(
        b''.join(raw(frame) for frame in frames)).decode()
    return C.observe_trial(binding, raw(report), b'', kwargs.get('exit_code', 0),
                           kwargs.get('capture_complete', True))


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(C, 'new contract helper must exist')

    def test_request_literal_and_canonical_encoding(self):
        self.assertEqual(C.decode_request(raw(FIXTURE['request'])), FIXTURE['request'])
        self.assertEqual(C.encode(FIXTURE['request']), raw(FIXTURE['request']))

    def test_request_refuses_types_domains_and_budget(self):
        for key, values in {
            'deal_count': [True, 0, 5, 1.0], 'seat_start': [True, -1, 6],
            'initial_button': [False, -1, 6], 'trial_budget_ms': [True, 0, 3600001],
            'total_budget_ms': [False, 0, 86400001, 64999, 100000000],
            'seed': ['F' * 64, '0' * 63, 0], 'version': ['wrong'],
            'lineups': [[], [['passive'] * 4], [['passive'] * 6],
                       [['passive'] * 5] * 2, [['unknown'] * 5], [[True] * 5],
                       [[[[['passive']]]]], [['passive'] * 5] * 5],
        }.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    C.decode_request(raw(dict(FIXTURE['request'], **{key: value})))

    def test_request_refuses_raw_encoding_and_extra_fields(self):
        canonical = raw(FIXTURE['request'])
        cases = [canonical[:-1], b'\xef\xbb\xbf' + canonical,
                 canonical.replace(b'\n', b'\r\n'), b' ' + canonical,
                 canonical.replace(b'"deal_count":1', b'"deal_count":1,"deal_count":1'),
                 canonical.replace(b'"deal_count":1', b'"deal_count":NaN'),
                 canonical.replace(b'"deal_count":1', b'"deal_count":100000000'),
                 raw(dict(FIXTURE['request'], extra=None)), b' ' * 4097,
            canonical.replace(b'passive', br'pass\u0069ve')]
        for data in cases:
            with self.subTest(data=data[:60]), self.assertRaises(ValueError):
                C.decode_request(data)

    def test_literal_matrix_seats_buttons_order_cards_and_hashes(self):
        plan = C.build_matrix(FIXTURE['request'], FIXTURE['deals'], 'control')
        self.assertEqual([p['controlled_seat'] for p in plan['pairs']], [2, 3, 4, 5, 0, 1])
        self.assertEqual([p['button'] for p in plan['pairs']], [3] * 6)
        self.assertEqual(len(plan['pairs']), 6)
        self.assertEqual(len(plan['units']), 12)
        self.assertEqual([u['strategy'] for u in plan['units']],
                         ['baseline-rules-v1', 'blueprint-v1', 'blueprint-v1',
                          'baseline-rules-v1'] * 3)
        self.assertEqual([u['ordinal'] for u in plan['units']], list(range(1, 13)))
        for index, pair in enumerate(plan['pairs']):
            payload = json.loads(pair['input_bytes'])
            self.assertEqual(payload['hands'], FIXTURE['deals'])
            self.assertEqual(payload['starting_stacks'], [200] * 6)
            self.assertEqual(payload['small_blind'], 1)
            self.assertEqual(payload['big_blind'], 2)
            self.assertEqual(payload['opponents'].count(None), 1)
            self.assertIsNone(payload['opponents'][pair['controlled_seat']])
            self.assertEqual(pair['input_path'], 'pairs/p%03d.json' % index)
            for unit in plan['units'][2 * index:2 * index + 2]:
                self.assertEqual(unit['input_sha256'],
                                 hashlib.sha256(pair['input_bytes']).hexdigest())
                self.assertEqual(unit['input_path'], pair['input_path'])
                self.assertTrue(unit['session_id'].endswith('eval-control-u%03d' % unit['ordinal']))

    def test_matrix_lineup_placement_and_deal_blocks(self):
        lineup = ['fold_to_bet', 'min_raise_once', 'shove_once', 'passive', 'fold_to_bet']
        request = dict(FIXTURE['request'], deal_count=2, lineups=[['passive'] * 5, lineup])
        plan = C.build_matrix(request, FIXTURE['deals'] * 2, 'blocks')
        self.assertEqual(len(plan['pairs']), 24)
        self.assertEqual(len(plan['units']), 48)
        self.assertEqual([p['button'] for p in plan['pairs']], [3] * 12 + [4] * 12)
        self.assertEqual([p['lineup_index'] for p in plan['pairs']], [0]*6+[1]*6+[0]*6+[1]*6)
        self.assertEqual(json.loads(plan['pairs'][6]['input_bytes'])['opponents'],
                         ['passive', 'fold_to_bet', None, 'fold_to_bet',
                          'min_raise_once', 'shove_once'])

    def test_matrix_limits_and_bad_inputs(self):
        lineups = [[name] * 5 for name in (
            'passive', 'fold_to_bet', 'min_raise_once', 'shove_once')]
        plan = C.build_matrix(dict(FIXTURE['request'], deal_count=4, lineups=lineups),
                              FIXTURE['deals'] * 4, 'maximum')
        self.assertEqual((len(plan['pairs']), len(plan['units'])), (96, 192))
        for suffix in ('', 'a' * 17, 'bad/path', '\u00e9'):
            with self.assertRaises(ValueError):
                C.build_matrix(FIXTURE['request'], FIXTURE['deals'], suffix)
        for deals in ([], [{}], [dict(FIXTURE['deals'][0], board_runout=[0, 1, 2, 3, 4])]):
            with self.assertRaises(ValueError):
                C.build_matrix(FIXTURE['request'], deals, 'bad')

    def test_complete_versioned_reports_keep_execution_and_selection_separate(self):
        for strategy in ('baseline-rules-v1', 'blueprint-v1'):
            binding, report, frames = fixture(strategy)
            result = observe(binding, report, frames)
            self.assertEqual(result['state'], 'completed', result)
            self.assertTrue(result['observation_complete'])
            self.assertTrue(result['report_complete'])
            self.assertEqual(result['net_chips'], 4)
            self.assertEqual(result['applied_actions_by_kind'], {'check': 1})
            self.assertEqual(result['unattributed_applied_actions'], 0)
            self.assertEqual(result['action_failures'], [])
            if strategy == 'baseline-rules-v1':
                self.assertEqual(result['baseline_fallback_selections'], {'provider_error': 1})
                self.assertEqual(result['baseline_fallback_applied'], {'provider_error': 1})
                self.assertIsNone(result['legacy_choices'])
            else:
                self.assertEqual(result['legacy_choices'], {'passive_default': 1})
                self.assertIsNone(result['baseline_fallback_selections'])
            self.assertNotIn('private_hands', str(result))
            self.assertNotIn('board_runout', str(result))

    def test_delivery_rejected_preserved_separately_from_both_scopes(self):
        for strategy in ('baseline-rules-v1', 'blueprint-v1'):
            binding, report, frames = fixture(strategy, failed=True)
            result = observe(binding, report, frames, exit_code=1)
            self.assertEqual(result['state'], 'failed')
            self.assertFalse(result['observation_complete'])
            self.assertIsNone(result['net_chips'])
            self.assertEqual(result['hand_failure_codes'], ['child_failed'])
            self.assertEqual(result['session_failure_codes'], ['child_failed'])
            failure = result['action_failures']
            self.assertEqual(len(failure), 1, result)
            self.assertEqual(failure[0]['code'], 'delivery_rejected')
            self.assertEqual(failure[0]['standing'], 'unverified_prefix')
            self.assertEqual(failure[0]['sources'],
                             ['decision', 'failure']
                             if strategy == 'baseline-rules-v1' else ['failure'])
            self.assertEqual(result['work_cutoff_actions'], 0)
            self.assertEqual(result['action_deadline_actions'], 0)
            self.assertNotIn('delivery_rejected', result['capture_deficiencies'])

    def test_failure_duplicate_timing_coalesced_and_host_timeout_not_action_clock(self):
        binding, report, frames = fixture(failed=True)
        decision = frames[1]['decision']
        decision['failure_reason'] = 'action_deadline_exceeded'
        decision['timing'].update(interruption_reason='action_deadline_exceeded',
                                  work_cutoff_crossed=True, deadline_crossed=True)
        frames[1]['failure'].update(code=decision['failure_reason'],
                                    timing=copy.deepcopy(decision['timing']))
        frames.append(copy.deepcopy(frames[1]))
        result = observe(binding, report, frames, exit_code=1)
        self.assertEqual(len(result['action_failures']), 1)
        self.assertEqual(result['work_cutoff_actions'], 1)
        self.assertEqual(result['action_deadline_actions'], 1)
        binding, report, frames = fixture(failed=True)
        report['failure_reason'] = report['hands'][0]['result']['failure_reason'] = 'host_limit'
        result = observe(binding, report, frames[:1], exit_code=1)
        self.assertEqual(result['work_cutoff_actions'], 0)
        self.assertEqual(result['action_deadline_actions'], 0)

    def test_null_failure_identity_is_preserved_and_not_merged_across_frames(self):
        binding, report, frames = fixture('blueprint-v1', failed=True)
        frames[1]['failure'].update(hand_id=None, event_index=None, action_index=None)
        frames.append(copy.deepcopy(frames[1]))
        frames[-1]['event_index'] = 1
        result = observe(binding, report, frames, exit_code=1)
        self.assertEqual(len(result['action_failures']), 2)
        self.assertTrue(all(f['action_index'] is None for f in result['action_failures']))

    def test_conflicting_failure_copies_refuse_without_double_count(self):
        for mutation in ('code', 'delivery_status', 'timing', 'action_index'):
            binding, report, frames = fixture(failed=True)
            failure = frames[1]['failure']
            failure[mutation] = {'code': 'delivery_ambiguous', 'delivery_status': 'unknown',
                                 'timing': None, 'action_index': 2}[mutation]
            result = observe(binding, report, frames, exit_code=1)
            self.assertEqual(result['state'], 'refused', result)
            self.assertTrue(result['capture_deficiencies'])
            self.assertFalse(result['observation_complete'])
        binding, report, frames = fixture(failed=True)
        repeated = copy.deepcopy(frames[1])
        repeated['decision']['failure_reason'] = repeated['failure']['code'] = 'delivery_ambiguous'
        repeated['decision']['timing']['interruption_reason'] = 'delivery_ambiguous'
        repeated['failure']['timing']['interruption_reason'] = 'delivery_ambiguous'
        result = observe(binding, report, frames + [repeated], exit_code=1)
        self.assertEqual(result['state'], 'refused')
        self.assertEqual(len(result['action_failures']), 1)

    def test_missing_invalid_failure_and_malformed_tail_keep_honest_prefix(self):
        for bad in (None, {}, {'code': 'delivery_rejected'}):
            binding, report, frames = fixture('blueprint-v1', failed=True)
            frames[1]['failure'] = bad
            result = observe(binding, report, frames, exit_code=1)
            self.assertFalse(result['observation_complete'])
            self.assertEqual(result['action_failures'], [])
            self.assertTrue(result['capture_deficiencies'])
        binding, report, frames = fixture(failed=True)
        result = observe(binding, report, frames + [{'unknown': 0}], exit_code=1)
        self.assertEqual(len(result['action_failures']), 1)
        self.assertFalse(result['observation_complete'])
        self.assertTrue(result['capture_deficiencies'])
        report['hands'][0]['result']['child_stdout_base64'] = base64.b64encode(
            b''.join(raw(f) for f in frames) + b'{').decode()
        result = C.observe_trial(binding, raw(report), b'', 1, True)
        self.assertEqual(len(result['action_failures']), 1)
        self.assertIn('partial_frame', result['capture_deficiencies'])

    def test_missing_decision_retains_unattributed_applied_action(self):
        binding, report, frames = fixture()
        frames[2]['decision'] = None
        result = observe(binding, report, frames)
        self.assertEqual(result['applied_actions_by_kind'], {'check': 1})
        self.assertEqual(result['unattributed_applied_actions'], 1)
        self.assertFalse(result['observation_complete'])
        self.assertIsNone(result['net_chips'])

    def test_repeated_failure_merges_source_labels_and_failed_decision_attribution(self):
        binding, report, frames = fixture(failed=True)
        first = copy.deepcopy(frames[1])
        first['decision'] = None
        result = observe(binding, report, [frames[0], first, frames[1]], exit_code=1)
        self.assertEqual(len(result['action_failures']), 1)
        self.assertEqual(result['action_failures'][0]['sources'], ['decision', 'failure'])

    def test_failed_decision_can_attribute_observed_host_application(self):
        binding, report, frames = fixture(failed=True)
        report['hands'][0]['result']['applied_actions'] = copy.deepcopy(
            FIXTURE['report_v2']['hands'][0]['result']['applied_actions'])
        result = observe(binding, report, frames, exit_code=1)
        self.assertEqual(result['baseline_fallback_applied'], {'provider_error': 1})
        self.assertEqual(result['unattributed_applied_actions'], 0)
        self.assertFalse(result['observation_complete'])

    def test_complete_street_action_ordinals_and_action_cardinality(self):
        binding, report, frames = fixture()
        frames[2]['decision']['street_action_index'] = 2
        result = observe(binding, report, frames)
        self.assertNotEqual(result['state'], 'completed')
        self.assertIsNone(result['net_chips'])

    def test_failed_closing_frame_cannot_be_replaced_by_later_success(self):
        binding, report, frames = fixture()
        failed = copy.deepcopy(frames[-1])
        failed.update(status='failed', failure_reason='trace_write_failed')
        result = observe(binding, report, frames[:-1] + [failed, frames[-1]])
        self.assertNotEqual(result['state'], 'completed')
        self.assertIsNone(result['net_chips'])
        self.assertIn('extra_frame', result['capture_deficiencies'])

    def assert_prefix_preserved(self, before, after, conflict):
        self.assertEqual(after['state'], 'refused')
        self.assertIn(conflict, after['capture_deficiencies'])
        self.assertFalse(after['observation_complete'])
        self.assertIsNone(after['net_chips'])
        for key in ('action_failures', 'applied_actions_by_kind',
                    'baseline_fallback_selections', 'baseline_fallback_applied',
                    'legacy_choices', 'unattributed_applied_actions', 'work_cutoff_actions',
                    'action_deadline_actions', 'hand_failure_codes', 'session_failure_codes'):
            with self.subTest(metric=key):
                self.assertEqual(after[key], before[key])

    def test_fix01_late_failure_timing_conflict_preserves_exact_failure_prefix(self):
        binding, report, frames = fixture('blueprint-v1', failed=True)
        before = observe(binding, report, frames, exit_code=1)
        expected = dict(hand_id=frames[1]['failure']['hand_id'], event_index=0, action_index=1,
                        code='delivery_rejected', delivery_status='rejected', sources=['failure'],
                        standing='unverified_prefix')
        self.assertEqual(before['action_failures'], [expected])
        rejected = copy.deepcopy(frames[1])
        rejected['event_index'] = rejected['failure']['event_index'] = 1
        rejected['failure']['timing']['last_valid_observation_ns'] = 2
        after = observe(binding, report, frames + [rejected], exit_code=1)
        self.assert_prefix_preserved(before, after, 'conflicting_timing')
        self.assertEqual(after['action_failures'], [expected])

    def test_fix01_late_decision_timing_conflict_preserves_selections_and_attribution(self):
        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
            with self.subTest(strategy=strategy):
                binding, report, frames = fixture(strategy, failed=True)
                frames[1]['decision'] = None
                _, success, decided = fixture(strategy)
                report['hands'][0]['result']['applied_actions'] = copy.deepcopy(
                    success['hands'][0]['result']['applied_actions'])
                before = observe(binding, report, frames, exit_code=1)
                self.assertEqual(before['unattributed_applied_actions'], 1)
                self.assertEqual(before['legacy_choices'] if strategy == 'blueprint-v1'
                                 else before['baseline_fallback_selections'], {})
                decided[2]['event_index'] = decided[2]['decision']['event_index'] = 1
                after = observe(binding, report, frames + decided[1:3], exit_code=1)
                self.assert_prefix_preserved(before, after, 'conflicting_timing')

    def test_fix01_conflicting_decision_cannot_mutate_prior_failure_source_alias(self):
        binding, report, frames = fixture(failed=True)
        failure_only = copy.deepcopy(frames[1])
        failure_only['decision'] = None
        failure_only['event_index'] = failure_only['failure']['event_index'] = 1
        prefix = frames + [failure_only]
        before = observe(binding, report, prefix, exit_code=1)
        self.assertEqual([f['sources'] for f in before['action_failures']],
                         [['decision', 'failure'], ['failure']])
        rejected = copy.deepcopy(frames[1])
        rejected['event_index'] = rejected['failure']['event_index'] = 1
        rejected['decision']['event_index'] = 1
        after = observe(binding, report, prefix + [rejected], exit_code=1)
        self.assert_prefix_preserved(before, after, 'conflicting_decision')

    def test_bad_schema_identity_settlement_capture_and_type_refused(self):
        cases = [('outer_extra',), ('wrong_input',), ('child_manifest',), ('bad_table_hash',),
                 ('bool_exit',), ('bool_count',), ('float_stack',), ('chips',), ('next_button',),
                 ('wrong_provider',), ('wrong_config',), ('wrong_policy',), ('missing_close',),
                 ('extra_close',), ('action_ordinal',), ('wrong_seat',), ('invalid_timing',),
                 ('truncated',), ('cleanup',), ('decision_extra',), ('ready_extra',)]
        for (case,) in cases:
            binding, report, frames = fixture()
            hand = report['hands'][0]['result']
            if case == 'outer_extra': report['extra'] = None
            if case == 'wrong_input': report['input_sha256'] = 'f' * 64
            if case == 'child_manifest': frames[0]['source_manifest_sha256'] = 'f' * 64
            if case == 'bad_table_hash': hand['input_sha256'] = 'f' * 64
            if case == 'bool_exit': hand['child_exit_code'] = False
            if case == 'bool_count': report['completed_hands'] = True
            if case == 'float_stack': report['carried_stacks'][0] = 200.0
            if case == 'chips': hand['settlement']['final_stacks'][0] += 1
            if case == 'next_button': report['next_button'] = 3
            if case == 'wrong_provider': report['provider'] = 'blueprint-v1'
            if case == 'wrong_config': hand['config_sha256'] = 'f' * 64
            if case == 'wrong_policy': frames[2]['decision']['fallback_blueprint_sha256'] = 'f' * 64
            if case == 'missing_close': frames.pop()
            if case == 'extra_close': frames.append(copy.deepcopy(frames[-1]))
            if case == 'action_ordinal': hand['applied_actions'][0]['index'] = 1
            if case == 'wrong_seat': hand['applied_actions'][0]['seat'] = 1
            if case == 'invalid_timing': frames[2]['decision']['timing']['elapsed_ns'] = True
            if case == 'truncated': hand['capture_truncated'] = True
            if case == 'cleanup': binding['cleanup_complete'] = False
            if case == 'decision_extra': frames[2]['decision']['extra'] = None
            if case == 'ready_extra': frames[0]['extra'] = None
            with self.subTest(case=case):
                result = observe(binding, report, frames)
                self.assertNotEqual(result['state'], 'completed', result)
                self.assertIsNone(result['net_chips'])

    def test_invalid_outer_bytes_yield_unknown_metrics(self):
        binding, _, _ = fixture()
        for data in (b'', b'{', b'{}\n', b'{"x":1,"x":1}\n', b'[' * 17 + b']' * 17,
                     b'{"x":' + b'1' * 641 + b'}', b'x' * (4 * 1024 * 1024 + 1)):
            result = C.observe_trial(binding, data, b'', None, False)
            self.assertIsNone(result['net_chips'])
            self.assertIsNone(result['action_failures'])
            self.assertFalse(result['observation_complete'])

    def test_reducer_independent_arithmetic_and_no_survivor_denominator(self):
        plan = {'pairs': [{'pair_index': 0, 'lineup_index': 0, 'controlled_seat': 2},
                          {'pair_index': 1, 'lineup_index': 1, 'controlled_seat': 3}],
                'units': []}
        trials = []
        for ordinal, (pair, strategy, net) in enumerate([
                (0, 'baseline-rules-v1', 4), (0, 'blueprint-v1', 1),
                (1, 'blueprint-v1', 3), (1, 'baseline-rules-v1', -2)], 1):
            unit = dict(ordinal=ordinal, pair_index=pair, strategy=strategy)
            plan['units'].append(unit)
            trials.append(dict(unit, state='completed', report_complete=True,
                               observation_complete=True, net_chips=net, cleanup_complete=True))
        reduced = C.reduce_trials(plan, trials)
        self.assertEqual([p['delta_chips'] for p in reduced['pairs']], [3, -5])
        aggregate = reduced['aggregate']
        self.assertEqual([aggregate[k] for k in ('baseline_net_chips', 'blueprint_net_chips',
                         'delta_chips', 'mean_delta_numerator', 'mean_delta_denominator')],
                         [2, 4, -2, -2, 2])
        self.assertEqual([g['mean_delta_denominator'] for g in aggregate['by_lineup']], [1, 1])
        self.assertEqual([g['delta_chips'] for g in aggregate['by_seat']], [3, -5])
        for bad in (trials[:-1], trials + [trials[-1]],
                    trials[:-1] + [dict(trials[-1], state='failed')],
                    trials[:-1] + [dict(trials[-1], observation_complete=False)],
                    trials[:-1] + [dict(trials[-1], cleanup_complete=False)],
                    trials[:-1] + [dict(trials[-1], net_chips=True)]):
            with self.subTest(bad=bad):
                self.assertIsNone(C.reduce_trials(plan, bad)['aggregate'])

    def test_six_named_negative_source_mutants_fail_independent_oracles(self):
        # Fixed captured helper bytes only. Mutants confer no runtime/source acceptance.
        global C
        accepted = C
        source = (ROOT / 'tools/v0a_evaluation_contract.py').read_text(encoding='utf-8')
        matrix = self.test_literal_matrix_seats_buttons_order_cards_and_hashes
        failure = self.test_delivery_rejected_preserved_separately_from_both_scopes
        mutants = [
            ('rotate_button', "(request['initial_button'] + d) % 6",
             "(request['initial_button'] + d + r) % 6", matrix),
            ('drop_seat', 'for r in range(6):', 'for r in range(5):', matrix),
            ('wrong_denominator', 'mean_delta_denominator=len(rows)',
             'mean_delta_denominator=len(rows) + 1',
             self.test_reducer_independent_arithmetic_and_no_survivor_denominator),
            ('drop_action_cause', 'action_failures=failures,', 'action_failures=[],', failure),
            ('double_action_cause', 'action_failures=failures,',
             'action_failures=failures + failures,', failure),
            ('fold_action_into_hand_scope', "result['hand_failure_codes'] = causes(hand)",
             "result['hand_failure_codes'] = causes(hand) + ['delivery_rejected']", failure),
        ]
        try:
            for name, old, new, oracle in mutants:
                with self.subTest(mutant=name):
                    self.assertEqual(source.count(old), 1, 'mutation must bind one exact site')
                    C = importlib.util.module_from_spec(SPEC)
                    exec(compile(source.replace(old, new), SPEC.origin, 'exec'), C.__dict__)
                    with self.assertRaises(AssertionError):
                        oracle()
        finally:
            C = accepted


if __name__ == '__main__':
    unittest.main()
